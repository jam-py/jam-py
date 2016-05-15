# -*- coding: utf-8 -*-

import sys
import os
import json
import uuid
import traceback
from threading import Lock
import jam

sys.path.insert(1, os.path.join(os.path.dirname(jam.__file__), 'third_party'))

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware, peek_path_info, get_path_info

import common
import adm_server
from items import AbortException

class App(object):
    def __init__(self):
        self.admin = adm_server.task
        self.admin.app = self
        self.task = None
        self.task_lock = Lock()
        self.users = {}
        self.roles = None
        self._busy = 0
        self.pid = os.getpid()
        self.task_server_modified = False
        self.task_client_modified = True
        self.under_maintenance = False
        self.work_dir = self.admin.work_dir
        self.jam_dir = os.path.dirname(jam.__file__)
        self.jam_version = jam.version()
        self.static = {
            '/jam/': self.jam_dir,
            '/': self.work_dir
        }
        self.fileserver = SharedDataMiddleware(None, self.static, cache_timeout=0.1)
        self.url_map = Map([
            Rule('/', endpoint='root_file'),
            Rule('/<file_name>', endpoint='root_file'),
            Rule('/js/<file_name>', endpoint='file'),
            Rule('/css/<file_name>', endpoint='file'),
            Rule('/jam/js/<file_name>', endpoint='file'),
            Rule('/jam/js/ace/<file_name>', endpoint='file'),
            Rule('/jam/css/<file_name>', endpoint='file'),
            Rule('/jam/img/<file_name>', endpoint='file'),
            Rule('/api', endpoint='api'),
            Rule('/upload', endpoint='upload')
        ])

    def get_task(self):
        if self.task is None:
            with self.task_lock:
                if self.task is None:
                    adm_server.create_task(self)
        return self.task

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if endpoint in ['file', 'root_file']:
                return self.serve_file(environ, start_response, endpoint, **values)
            elif endpoint in ['api', 'upload']:
                response = getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            if peek_path_info(environ) == 'ext':
                response = self.on_ext(request)
            else:
                response = e
        return response(environ, start_response)

    def serve_index(self, environ, start_response):
        response = Response()
        response.headers['Content-Type'] = 'text/html'
        with open('index.html', 'r') as f:
            response.set_data(f.read())
        return response(environ, start_response)

    def serve_file(self, environ, start_response, endpoint, file_name=None):
        if endpoint == 'root_file':
            if not file_name:
                file_name = 'index.html'
                environ['PATH_INFO'] = environ['PATH_INFO'] + '/index.html'
            if file_name == 'index.html':
                self.check_task_client_modified()
                return self.serve_index(environ, start_response)
            elif file_name == 'admin.html':
                environ['PATH_INFO'] = os.path.join('jam', file_name)
        try:
            if file_name:
                base, ext = os.path.splitext(file_name)
            if common.SETTINGS['COMPRESSED_JS'] and ext and ext in ['.js', '.css']:
                try:
                    cur_path_info = environ['PATH_INFO']
                    min_file_name = base + '.min' + ext
                    environ['PATH_INFO'] = environ['PATH_INFO'].replace(file_name, min_file_name)
                    return self.fileserver(environ, start_response)
                except:
                    environ['PATH_INFO'] = cur_path_info
                    return self.fileserver(environ, start_response)
            else:
                return self.fileserver(environ, start_response)
        except Exception, e:
            return Response('')(environ, start_response)


    def create_post_response(self, request, result):
        response = Response()
        accepts_gzip = 0
        try:
            if request.environ.get("HTTP_ACCEPT_ENCODING").find("gzip") != -1:
                accepts_gzip = 1
        except:
            pass
        buff = json.dumps(result, default=common.json_defaul_handler)
        response.headers['Content-Type'] = 'application/json'
        if accepts_gzip:
            buff = common.compressBuf(buff)
            response.headers['Content-encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(buff))
        response.set_data(buff)
        return response

    def on_api(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            try:
                method, user_id, task_id, item_id, params, date = json.loads(request.get_data())
                r['result'] = self.process_request(request.environ, method, user_id, task_id, item_id, params)
            except AbortException, e:
                print traceback.format_exc()
                r['result'] = None, e.message
                r['error'] = e.message
            except Exception, e:
                print traceback.format_exc()
                if common.SETTINGS['DEBUGGING']:
                    raise
                r['result'] = None, e.message
                r['error'] = e.message
            return self.create_post_response(request, r)

    def process_request(self, env, method, user_uuid=None, task_id=None, item_id=None, params=None, ext=None):
        user_info = {}
        is_admin = task_id == 0
        if is_admin:
            task = self.admin
        else:
            task = self.get_task()
        if not task:
            return {'status': common.NO_PROJECT, 'data': None}
        elif self.under_maintenance:
            return {'status': common.UNDER_MAINTAINANCE, 'data': None}
        elif method == 'login':
            return {'status': common.RESPONSE, 'data': self.login(params[0], params[1], is_admin, env)}
        if ext:
            obj = task
        else:
            if self.admin.safe_mode:
                user_info = self.get_user_info(user_uuid, is_admin, env)
                if not user_info:
                    return {'status': common.NOT_LOGGED, 'data': common.NOT_LOGGED}
            obj = task
            if task:
                obj = task.item_by_ID(item_id)
        self._busy += 1
        try:
            data = None
            if task.on_request:
                data = task.on_request(task, user_info, env, method, obj, params, ext)
            if not data:
                data = self.get_response(is_admin, env, method, user_info, task_id, obj, params, ext)
        finally:
            self._busy -= 1
        return {'status': common.RESPONSE, 'data': data, 'version': task.version}

    def get_response(self, is_admin, env, method, user_info, task_id, item, params, ext):
        if ext:
            if item.on_ext_request:
                return item.on_ext_request(item, method, params, env)
        elif method == 'server_function':
            return self.server_func(item, params[0], params[1], env)
        elif method == 'open':
            if self.has_privilege(user_info, item, 'can_view'):
                return item.select_records(params, user_info, env)
            else:
                return [], item.task.lang['cant_view'] % item.item_caption
        elif method == 'get_record_count':
            return item.get_record_count(params, env)
        elif method == 'apply_changes':
            return item.apply_changes(params, self.find_privileges(user_info, item), user_info, env)
        elif method == 'print_report':
            url = None
            error = None
            if self.has_privilege(user_info, item, 'can_view'):
                url = item.print_report(*params)
            else:
                error = item.task.lang['cant_view'] % item.item_caption
            return url, error
        elif method == 'logout':
            return self.logout(params, is_admin, env)
        elif method == 'init_client':
            return self.init_client(user_info, is_admin)

    def get_privileges(self, role_id):
        if self.roles is None:
            self.roles = adm_server.get_roles()
        return self.roles[role_id]

    def server_func(self, obj, func_name, params, env):
        result = None
        error = ''
        func = getattr(obj, func_name)
        if func:
            if func_name[-4:] == '_env':
                params = list(params)
                params.append(env)
            result = func(obj, *params)
        else:
            raise Exception, 'item: %s no server function with name %s' % (obj.item_name, func_name)
        return result, error

    def check_task_server_modified(self):
        if self.task_server_modified:
            adm_server.reload_task()
            self.task_server_modified = False

    def check_task_client_modified(self):
        if self.task_client_modified:
            adm_server.update_events_code()
            self.task_client_modified = False

    def init_client(self, user_info, is_admin):
        if is_admin:
            task = self.admin
        else:
            task = self.task
            self.check_task_server_modified()
        if user_info:
            priv = self.get_privileges(user_info['role_id'])
        else:
            priv = None
        result = {
            'task': task.get_info(),
            'settings': self.admin.get_settings(),
            'language': self.admin.lang,
            'user_info': user_info,
            'privileges': priv
        }
        return result, ''

    def login(self, log, psw_hash, admin, env):
        privileges = None
        if not admin and self.task.on_login:
            user_uuid, user_info = self.task.on_login(self.task, env, admin, log, psw_hash)
        else:
            user_id, user_info = self.admin.login(log, psw_hash, admin)
            user_uuid = None
            if user_id:
                for key in self.users.iterkeys():
                    if self.users[key][0] == user_id:
                        del self.users[key]
                        break
                user_uuid = str(uuid.uuid4())
                self.users[user_uuid] = (user_id, user_info, common.now())
        return user_uuid, ''

    def get_user_info(self, user_uuid, admin, env):
        if not admin and self.task.on_get_user_info:
            return self.task.on_get_user_info(self.task, user_uuid, env)
        else:
            user = self.users.get(user_uuid)
            if user:
                user_info = user[1]
                if not admin or (admin and user_info['admin']):
                    return user_info

    def logout(self, user_uuid, admin, env):
        if not admin and self.task.on_logout:
            self.task.on_logout(self.task, user_uuid, env)
        else:
            user = self.users.get(user_uuid)
            if user:
                adm_server.logout(user[0])
                del user

    def find_privileges(self, user_info, item):
        if not self.admin.safe_mode or item.master or (item.task == self.admin) or (item == item.task):
            return {'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True}
        else:
            try:
                priv_dic = self.get_privileges(user_info['role_id'])[item.ID]
            except:
                priv_dic = None
            if priv_dic:
                return priv_dic
            else:
                return {'can_view': False, 'can_create': False, 'can_edit': False, 'can_delete': False}

    def has_privilege(self, user_info, item, priv_name):
        return self.find_privileges(user_info, item)[priv_name]

    def on_ext(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            method = get_path_info(request.environ)
            params = json.loads(request.get_data())
            user_id = None
            task_id = None
            item_id = None
            ext = True
            try:
                r['result'] = self.process_request(request.environ,
                    method, user_id, task_id, item_id, params, ext)
            except AbortException, e:
                print traceback.format_exc()
                r['result'] = None, e.message
                r['error'] = e.message
            except Exception, e:
                print traceback.format_exc()
                if common.SETTINGS['DEBUGGING']:
                    raise
                r['result'] = None, e.message
                r['error'] = e.message
            return self.create_post_response(request, r)

    def on_upload(self, request):

        def find_param(data):
            pos = data.find(';')
            return data[:pos], pos + 1

        def read_user_info(data):
            info_len, pos = find_param(data)
            info_len = int(info_len)
            user_info = data[pos:pos+info_len]
            task_ID, p = find_param(user_info)
            user_id = user_info[p:]
            pos = pos + info_len + 1
            return user_id, int(task_ID), pos

        if request.method == 'POST':
            try:
                data = request.get_data()
                header = []
                header_str = ''
                length = 0
                string = ''
                user_id, task_ID, pos = read_user_info(data)
                if self.admin.safe_mode:
                    user_info = self.get_user_info(user_id, task_ID == 0, request.environ)
                    if not user_info:
                        return Response()
                for s in data[pos:]:
                    header_str += s
                    if s == ';':
                        if len(header) == 0:
                            length = int(string)
                        header.append(int(string))
                        if len(header) == 2 * (length + 1):
                            break;
                        string = ''
                    else:
                        string += s
                start = len(header_str) + pos
                path = os.path.join(os.getcwd(), os.path.normpath(data[start: start + header[1]]))
                if not os.path.exists(path):
                    os.makedirs(path)
                start = start + header[1]
                for i in range(length):
                    index = 2 * i + 2
                    file_name = data[start: start + header[index]]
                    start = start + header[index]
                    index += 1
                    content = data[start: start + header[index]]
                    file_name = os.path.join(path, file_name)
                    with open(file_name, 'wb') as f:
                        f.write(content)
                    os.chmod(file_name, 0o666)
                    start = start + header[index]
            except:
                print traceback.format_exc()
            return Response()

    def stop(self, sigvalue):
        self.kill()

    def kill(self):
        import signal, subprocess
        if os.name == "nt":
            subprocess.Popen("taskkill /F /T /pid %i" % self.pid, shell=True)
        else :
            os.killpg(self.pid, signal.SIGKILL)
