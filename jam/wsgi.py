import sys
import os
import json
import uuid
import traceback
import datetime
from threading import Lock
from types import MethodType
import mimetypes
import jam

sys.path.insert(1, os.path.join(os.path.dirname(jam.__file__), 'third_party'))

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware, peek_path_info, get_path_info
from werkzeug.local import Local, LocalManager
from werkzeug.http import parse_date, http_date
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.utils import cached_property

import jam.common as common
import jam.adm_server as adm_server
from jam.items import AbortException

SECRET_KEY = os.urandom(20)

class JamSecureCookie(SecureCookie):
    serialization_method = json

class JamRequest(Request):

    def session_key(self, task):
        return '%s_session_%s' % (task.item_name, self.environ['SERVER_PORT'])

    def get_session(self, task):
        if not hasattr(self, '_cookie'):
            key = self.session_key(task)
            self._cookie = JamSecureCookie.load_cookie(self, key=key, secret_key=SECRET_KEY)
        return self._cookie

    def save_session(self, response, task):
        key = self.session_key(task)
        session = self.get_session(task)
        session.save_cookie(response, key=key)

def create_application(from_file):
    if from_file:
        work_dir = os.path.dirname(os.path.abspath(from_file))
    else:
        work_dir = os.getcwd()
    os.chdir(work_dir)
    static_files = {
        '/static':  os.path.join(work_dir, 'static')
    }

    jam.context = Local()
    local_manager = LocalManager([jam.context])

    application = App(work_dir)
    application = SharedDataMiddleware(application, static_files)
    application = local_manager.make_middleware(application)
    return application

class App():
    def __init__(self, work_dir):
        mimetypes.add_type('text/cache-manifest', '.appcache')
        self.started = datetime.datetime.now()
        self.work_dir = work_dir
        self._loading = False
        self._load_lock = Lock()
        self.admin = None
        self.task = None
        self.privileges = None
        self._busy = 0
        self.pid = os.getpid()
        self.task_server_modified = False
        self.task_client_modified = True
        self.under_maintenance = False
        self.jam_dir = os.path.dirname(jam.__file__)
        self.jam_version = jam.version()
        self.application_files = {
            '/': self.work_dir,
            '/jam/': self.jam_dir
        }
        self.fileserver = SharedDataMiddleware(None, self.application_files, cache_timeout=1)
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
        self.admin = self.create_admin()

    def create_admin(self):
        from adm_server import create_admin
        return create_admin(self)

    def get_task(self):
        if self.task:
            return self.task
        else:
            if not self._loading:
                self._loading = True
                try:
                    with self._load_lock:
                        self.task = self.admin.create_task()
                except:
                    traceback.print_exc()
                    raise
                finally:
                    self._loading = False
            return self.task

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        jam.context.environ = environ
        request = JamRequest(environ)
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if endpoint in ['file', 'root_file']:
                return self.serve_file(environ, start_response, endpoint, **values)
            elif endpoint in ['api', 'upload']:
                response = getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException as e:
            if peek_path_info(environ) == 'ext':
                response = self.on_ext(request)
            else:
                response = e
        return response(environ, start_response)

    def check_modified(self, file_path, environ):
        if environ.get('HTTP_IF_MODIFIED_SINCE'):
            date1 = parse_date(environ['HTTP_IF_MODIFIED_SINCE'])
            date2 = datetime.datetime.utcfromtimestamp(os.path.getmtime(file_path)).replace(microsecond=0)
            if date1 != date2:
                try:
                    os.utime(file_path, None)
                except:
                    pass

    def serve_file(self, environ, start_response, endpoint, file_name=None):
        if endpoint == 'root_file':
            if not file_name:
                file_name = 'index.html'
                environ['PATH_INFO'] = environ['PATH_INFO'] + '/index.html'
            if file_name == 'index.html':
                self.check_modified(file_name, environ)
                if self.get_task():
                    self.check_task_client_modified()
                    self.check_task_server_modified()
                else:
                    return Response(self.admin.lang['no_task'])(environ, start_response)
            elif file_name == 'admin.html':
                self.check_modified(os.path.join(self.jam_dir, file_name), environ)
                environ['PATH_INFO'] = os.path.join('jam', file_name)
        if file_name:
            base, ext = os.path.splitext(file_name)
        init_path_info = None
        if common.SETTINGS['COMPRESSED_JS'] and ext and ext in ['.js', '.css']:
            init_path_info = environ['PATH_INFO']
            min_file_name = base + '.min' + ext
            environ['PATH_INFO'] = environ['PATH_INFO'].replace(file_name, min_file_name)
        try:
            try:
                return self.fileserver(environ, start_response)
            except Exception as e:
                if init_path_info:
                    environ['PATH_INFO'] = init_path_info
                    return self.fileserver(environ, start_response)
                else:
                    raise
        except Exception as e:
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

    def create_session(self, cookie, task, user_info={}):
        session = {}
        session['uuid'] = str(uuid.uuid4())
        session['user_info'] = user_info
        cookie['info'] = session
        cookie.modified = True
        return cookie

    def connect(self, request, task):
        if self.check_session(request, task):
            return True

    def check_session(self, request, task):
        c = request.get_session(task)
        if not c.get('info') and not self.admin.safe_mode:
            c = self.create_session(c, task)
        session = c.get('info')
        if session:
            user_info = session['user_info']
            if bool(user_info) != self.admin.safe_mode:
                self.logout(request, task)
                return False
            jam.context.session = session
            return True

    def login(self, request, task, login, psw_hash):
        if self.task == task and self.task and self.task.on_login:
            user_info = self.task.on_login(self.task, login, psw_hash)
        else:
            user_info = adm_server.login(self.admin, login, psw_hash, self.admin == task)
        if user_info:
            cookie = request.get_session(task)
            self.create_session(cookie, task, user_info)
            return True

    def logout(self, request, task):
        cookie = cookie = request.get_session(task)
        cookie['info'] = None
        jam.context.session = None

    def on_api(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            try:
                method, task_id, item_id, params, date = json.loads(request.get_data())
                if task_id == 0:
                    task = self.admin
                else:
                    task = self.get_task()
                result = {'status': common.RESPONSE, 'data': None, 'version': task.version}
                if not task:
                    result['status'] = common.NO_PROJECT
                elif self.under_maintenance:
                    result['status'] = common.UNDER_MAINTAINANCE
                elif method == 'connect':
                    self.connect(request, task)
                    result['data'] = self.connect(request, task)
                elif method == 'login':
                    result['data'] = self.login(request, task, params[0], params[1])
                elif method == 'logout':
                    self.logout(request, task);
                    result['status'] = common.NOT_LOGGED
                    result['data'] = common.NOT_LOGGED
                else:
                    if not self.check_session(request, task):
                        result['status'] = common.NOT_LOGGED
                        result['data'] = common.NOT_LOGGED
                    else:
                        item = task
                        if task and item_id:
                            item = task.item_by_ID(item_id)
                        self._busy += 1
                        try:
                            data = None
                            if task.on_request:
                                data = task.on_request(task, method, params)
                            if not data:
                                data = self.get_response(item, method, params)
                        finally:
                            self._busy -= 1
                        result['data'] = data
                r ['result'] = result
            except AbortException as e:
                traceback.print_exc()
                r['result'] = {'data': [None, e.message]}
                r['error'] = e.message
            except Exception as e:
                traceback.print_exc()
                if common.SETTINGS['DEBUGGING'] and task_id != 0:
                    raise
                r['result'] = {'data': [None, e.message]}
                r['error'] = e.message
            response = self.create_post_response(request, r)
            request.save_session(response, task)
            return response

    def get_response(self, item, method, params):
        if method == 'open':
            return item.select_records(params, safe=True)
        elif method == 'get_record_count':
            return item.get_record_count(params, safe=True)
        elif method == 'apply_changes':
            return item.apply_changes(params, safe=True)
        elif method == 'print_report':
            return item.print_report(*params), ''
        elif method == 'server_function':
            return self.server_func(item, params[0], params[1])
        elif method == 'init_client':
            return self.init_client(item)

    def server_func(self, obj, func_name, params):
        result = None
        error = ''
        func = getattr(obj, func_name)
        if func:
            result = func(obj, *params)
        else:
            raise Exception('item: %s no server function with name %s' % (obj.item_name, func_name))
        return result, error

    def check_task_server_modified(self):
        if self.task_server_modified:
            self.admin.reload_task()
            self.task_server_modified = False

    def check_task_client_modified(self):
        if self.task_client_modified:
            self.admin.update_events_code()
            self.task_client_modified = False

    def get_privileges(self, role_id):
        if self.privileges is None:
            roles, privileges = adm_server.get_roles(self.admin)
            if self.task:
                self.task.roles = roles
            self.privileges = privileges
        return self.privileges[role_id]

    def init_client(self, task):
        session = jam.context.session
        priv = None
        user_info = {}
        if session:
            user_info = session['user_info']
            if user_info:
                priv = self.get_privileges(user_info['role_id'])
        result = {
            'task': task.get_info(),
            'settings': self.admin.get_settings(),
            'language': self.admin.lang,
            'user_info': user_info,
            'privileges': priv
        }
        return result, ''

    def on_ext(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            method = get_path_info(request.environ)
            params = json.loads(request.get_data())
            task = self.get_task()
            try:
                data = None
                if task.on_ext_request:
                    data = task.on_ext_request(task, method, params)
                r['result'] = {'status': common.RESPONSE, 'data': data, 'version': task.version}
            except AbortException as e:
                traceback.print_exc()
                r['result'] = {'data': [None, e.message]}
                r['error'] = e.message
            except Exception as e:
                traceback.print_exc()
                if common.SETTINGS['DEBUGGING'] and task_id != 0:
                    raise
                r['result'] = {'data': [None, e.message]}
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
            task_name = user_info[p:]
            pos = pos + info_len + 1
            return task_name, int(task_ID), pos

        if request.method == 'POST':
            try:
                data = request.get_data()
                header = []
                header_str = ''
                length = 0
                string = ''
                task_name, task_id, pos = read_user_info(data)
                if task_id == 0:
                    task = self.admin
                else:
                    task = self.get_task()
                if self.admin.safe_mode:
                    if not request.get_session(task).get('info'):
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
                traceback.print_exc()
            return Response()

    def get_client_ip(self, environ):
        x_forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = environ.get('REMOTE_ADDR')
        return ip

    def stop(self, sigvalue):
        self.kill()

    def kill(self):
        import signal, subprocess
        if os.name == "nt":
            subprocess.Popen("taskkill /F /T /pid %i" % self.pid, shell=True)
        else :
            os.killpg(self.pid, signal.SIGKILL)
