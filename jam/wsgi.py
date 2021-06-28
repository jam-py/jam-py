import sys
import os
import json
import uuid
import traceback
import datetime, time
from types import MethodType
import mimetypes
import logging
import jam

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(jam.__file__), 'third_party')))

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wsgi import peek_path_info, get_path_info
from werkzeug.local import Local, LocalManager
from werkzeug.http import parse_date, http_date
from werkzeug.utils import cached_property, secure_filename
from werkzeug._compat import to_unicode, to_bytes
from werkzeug.secure_cookie.securecookie import SecureCookie

from .third_party.six import get_function_code

from .common import consts, error_message, file_write
from .common import consts, ProjectNotCompleted
from .common import json_defaul_handler, compressBuf
from .common import validate_image, valid_uploaded_file
from .admin.admin import create_admin, login_user, get_roles
from .admin.admin import user_valid_ip, user_valid_uuid
from .admin.builder import update_events_code
from .admin.import_metadata import import_metadata
from .items import AbortException
from .admin.task import create_task, reload_task

class JamSecureCookie(SecureCookie):
    serialization_method = json

    def save_cookie(
        self,
        response,
        key="session",
        expires=None,
        session_expires=None,
        max_age=None,
        path="/",
        domain=None,
        secure=None,
        httponly=False,
        force=False,
        samesite=None
    ):
        if force or self.should_save:
            data = self.serialize(session_expires or expires)
            response.set_cookie(
                key,
                data,
                expires=expires,
                max_age=max_age,
                path=path,
                domain=domain,
                secure=secure,
                httponly=httponly,
                samesite=samesite
            )


class JamRequest(Request):

    @cached_property
    def session_key(self):
        if self.task.app.admin == self.task:
            return '%s_session_%s' % (self.task.item_name, self.environ['SERVER_PORT'])
        else:
            return '%s_session' % (self.task.item_name)

    @cached_property
    def client_cookie(self):
        return JamSecureCookie.load_cookie(self, key=self.session_key, secret_key=self.task.app.admin.secret_key)

    def save_client_cookie(self, response, app, task):
        if task:
            cookie = self.client_cookie
            expires = None
            if consts.SAFE_MODE and task.timeout:
                expires = time.time() + task.timeout
                cookie.modified = True
            cookie.save_cookie(response, key=self.session_key, session_expires=expires, httponly=True, samesite='Lax')

def create_application(from_file=None, load_task=False, testing=False):
    if from_file:
        if os.path.isfile(from_file):
            work_dir = os.path.dirname(from_file)
        else:
            work_dir = from_file
    else:
        work_dir = os.getcwd()
    work_dir = os.path.realpath(work_dir)
    os.chdir(work_dir)
    static_files = {
        '/static':  os.path.join(work_dir, 'static')
    }

    jam.context = Local()
    local_manager = LocalManager([jam.context])

    application = App(work_dir, load_task)
    if not testing:
        application = SharedDataMiddleware(application, static_files)
        application = local_manager.make_middleware(application)
    return application

class JamLogger(object):
    def __init__(self, app):
        self.app = app

    @cached_property
    def log(self):
        logger = logging.getLogger('jam_app')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

    def debug(self, msg, *args, **kwargs):
        self.log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.log.exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log.critical(msg, *args, **kwargs)

class App(object):
    def __init__(self, work_dir, load_task):
        mimetypes.add_type('text/cache-manifest', '.appcache')
        self.started = datetime.datetime.now()
        self.work_dir = work_dir
        self.state = consts.PROJECT_NONE
        self.__task = None
        self.privileges = None
        self._busy = 0
        self.pid = os.getpid()
        self.jam_dir = os.path.realpath(os.path.dirname(jam.__file__))
        self.jam_version = jam.version()
        self.__is_locked = 0
        self.application_files = {
            '/': self.work_dir,
            '/jam/': self.jam_dir
        }
        self.fileserver = SharedDataMiddleware(None, self.application_files, cache_timeout=1)
        self.url_map = Map([
            Rule('/', endpoint='root_file'),
            Rule('/<file_name>.html', endpoint='root_file'),
            Rule('/js/<file_name>', endpoint='file'),
            Rule('/css/<file_name>', endpoint='file'),
            Rule('/jam/js/<file_name>', endpoint='file'),
            Rule('/jam/js/ace/<file_name>', endpoint='file'),
            Rule('/jam/css/<file_name>', endpoint='file'),
            Rule('/jam/css/themes/<file_name>', endpoint='file'),
            Rule('/jam/img/<file_name>', endpoint='file'),
            Rule('/api', endpoint='api'),
            Rule('/upload', endpoint='upload')
        ])
        consts.app = self
        self.log = JamLogger(self)
        create_admin(self)
        self.build_id_prefix = '$buildID'
        self.save_build_id()
        if load_task:
            with self.admin.lock('$creating_task'):
                self.__task = create_task(self)
        self.check_migration()

    def create_task(self):
        result = None
        if self.state != consts.PROJECT_LOADING:
            self.state = consts.PROJECT_LOADING
            try:
                result = create_task(self)
                update_events_code(self.admin)
                consts.CLIENT_MODIFIED = False
                consts.SERVER_MODIFIED = False
                consts.write_settings()
                self.state = consts.RESPONSE
                result.__task_locked = True
            except ProjectNotCompleted:
                self.state = consts.PROJECT_NO_PROJECT
            except:
                self.state = consts.PROJECT_ERROR
                traceback.print_exc()
        return result

    @property
    def task(self):
        if not self.__task:
            self.__task = self.create_task()
        return self.__task

    def task_locked(self):
        return self.__is_locked > 0

    @property
    def __task_locked(self):
        pass

    @__task_locked.setter
    def __task_locked(self, value):
        if value:
            self.__is_locked += 1
        else:
            self.__is_locked -= 1

    def __call__(self, environ, start_response):
        jam.context.environ = environ
        jam.context.session = None
        request = JamRequest(environ)
        if consts.MAX_CONTENT_LENGTH > 0:
            request.max_content_length = 1024 * 1024 * consts.MAX_CONTENT_LENGTH
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if endpoint in ['file', 'root_file']:
                result = self.serve_file(environ, start_response, endpoint, **values)
                return result
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
            if file_name:
                file_name += '.html'
            if not file_name:
                file_name = 'index.html'
                environ['PATH_INFO'] = '/index.html'
            elif file_name == 'admin.html':
                file_name = 'builder.html'
            if file_name == 'index.html':
                self.check_modified(file_name, environ)
                self.check_project_modified()
            elif file_name == 'builder.html':
                if os.path.exists(file_name):
                    self.check_modified(file_name, environ)
                else:
                    self.check_modified(os.path.join(to_unicode(self.jam_dir, 'utf-8'), file_name), environ)
                    environ['PATH_INFO'] = '/jam/builder.html'
        if file_name:
            base, ext = os.path.splitext(file_name)
        init_path_info = None
        if consts.COMPRESSED_JS and ext and ext in ['.js', '.css']:
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
        try:
            buff = json.dumps(result, default=json_defaul_handler)
        except:
            self.log.exception('wsgi.py create_post_response error')
            self.log.debug(result)
            raise
        response.headers['Content-Type'] = 'application/json'
        if accepts_gzip:
            buff = compressBuf(buff)
            response.headers['Content-encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(buff))
        response.set_data(buff)
        return response

    def get_client_address(self, request):
        try:
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
        except KeyError:
            return request.environ['REMOTE_ADDR']

    def create_session(self, request, task, user_info=None, session_uuid=None):
        if not user_info:
            user_info = {
                'user_id': None,
                'role_id': None,
                'role_name': '',
                'user_name': '',
                'admin': False
            }
        cookie = request.client_cookie
        session = {}
        session['ip'] = self.get_client_address(request)
        session['uuid'] = session_uuid
        session['user_info'] = user_info
        cookie['info'] = session
        cookie.modified = True
        return cookie

    def connect(self, request, task):
        if self.check_session(request, task):
            return consts.PROJECT_LOGGED

    def valid_session(self, task, session, request):
        if consts.SAFE_MODE:
            user_info = session['user_info']
            if not (user_info and user_info.get('user_id')):
                return False
            if not self.admin.ignore_change_ip and task != self.admin:
                ip = self.get_client_address(request)
                if not user_valid_ip(self.admin, user_info['user_id'], ip):
                    return False
            if not self.admin.ignore_change_uuid and task != self.admin:
                if not user_valid_uuid(self.admin, user_info['user_id'], session['uuid']):
                    return False
        return True

    def check_session(self, request, task):
        c = request.client_cookie
        if not c.get('info') and not consts.SAFE_MODE:
            c = self.create_session(request, task)
        session = c.get('info')
        if session:
            if not self.valid_session(task, session, request):
                self.logout(request, task)
                return False
            jam.context.session = session
            return True

    def default_login(self, task, login, password, ip, session_uuid):
        return login_user(self.admin, login, password, self.admin == task, ip, session_uuid)

    def login(self, request, task, form_data):
        time.sleep(0.3)
        ip = None
        session_uuid = None
        ip = self.get_client_address(request)
        session_uuid = str(uuid.uuid4())
        if self.admin == task or task.on_login is None:
            user_info = self.default_login(task, form_data['login'], form_data['password'], ip, session_uuid)
        elif task.on_login:
            try:
                try:
                    user_info = task.on_login(task, form_data, {'ip': ip, 'session_uuid': session_uuid})
                except:
                    # for compatibility with previous versions
                    if get_function_code(task.on_login).co_argcount == 5:
                        user_info = task.on_login(task, form_data['login'], form_data['password'], ip, session_uuid)
                    else:
                        raise

            except:
                user_info = None
                traceback.print_exc()
        if user_info:
            self.create_session(request, task, user_info, session_uuid)
            return True

    def logout(self, request, task):
        del request.client_cookie['info']
        jam.context.session = None

    def create_connection_pool(self):
        if self.task:
            self.__task_locked = False
            try:
                self.task.create_pool()
            finally:
                self.__task_locked = True

    def get_privileges(self, role_id):
        if self.privileges is None:
            roles, privileges = get_roles(self.admin)
            self.privileges = privileges
        try:
            result = self.privileges[role_id]
        except:
            result = {}
        return result

    def init_client(self, task):
        session = jam.context.session
        priv = None
        user_info = {}
        if session:
            user_info = session['user_info']
            role_id = user_info.get('role_id')
            if role_id:
                priv = self.get_privileges(role_id)
        result = {
            'task': task.get_info(),
            'settings': consts.settings,
            'locale': consts.locale,
            'language': consts.lang,
            'user_info': user_info,
            'privileges': priv
        }
        return result, ''

    def check_migration(self):
        path = os.path.join(self.work_dir, 'migration')
        files = []
        if os.path.exists(path):
            for file_name in os.listdir(path):
                files.append(os.path.join(self.work_dir, 'migration', file_name))
        files_len = len(files)
        if files_len:
            if files_len == 1:
                self.import_md(files[0], False)
            else:
                self.log.error('More than one file in migration folder')

    def import_metadata(self, task, task_id, file_name, from_client): #for compatibility with previous versions
        self.import_md(file_name, from_client)

    def import_md(self, file_name, from_client):
        if not self.under_maintenance:
            with self.admin.lock('$metadata_import'):
                consts.MAINTENANCE = True
                consts.PARAMS_VERSION += 1
                consts.write_settings()
                self.save_build_id()
                self.__task_locked = False
                try:
                    result = import_metadata(self.admin, file_name, from_client)
                    success, error, message = result
                    if success and self.task:
                        reload_task(self)
                        update_events_code(self.admin)
                        self.privileges = None
                finally:
                    self.__task_locked = True
                    consts.MAINTENANCE = False
                    consts.PARAMS_VERSION += 1
                    if success:
                        consts.BUILD_VERSION += 1
                        consts.MODIFICATION += 1
                    consts.write_settings()
                    self.save_build_id()
                return result

    def get_under_maintenance(self):
        return consts.MAINTENANCE

    under_maintenance = property(get_under_maintenance)

    def __get_client_modified(self):
        return consts.CLIENT_MODIFIED

    def __set_client_modified(self, value):
        consts.CLIENT_MODIFIED = value
        consts.MODIFICATION += 1
        consts.PARAMS_VERSION += 1
        consts.write_settings()
        self.save_build_id()

    client_modified = property(__get_client_modified, __set_client_modified)

    def __get_server_modified(self):
        return consts.SERVER_MODIFIED

    def __set_server_modified(self, value):
        consts.SERVER_MODIFIED = value
        consts.MODIFICATION += 1
        consts.PARAMS_VERSION += 1
        consts.write_settings()
        self.save_build_id()

    server_modified = property(__get_server_modified, __set_server_modified)

    def check_project_modified(self):
        if self.task:
            with self.admin.lock('$code_updating'):
                params = consts.read_params(['CLIENT_MODIFIED', 'SERVER_MODIFIED', 'MAINTENANCE'])
                if not params['MAINTENANCE'] and (params['CLIENT_MODIFIED'] or params['SERVER_MODIFIED']):
                    self.__task_locked = False
                    try:
                        if params['SERVER_MODIFIED']:
                            reload_task(self)
                            consts.BUILD_VERSION += 1
                        if params['CLIENT_MODIFIED']:
                            update_events_code(self.admin)
                        consts.CLIENT_MODIFIED = False
                        consts.SERVER_MODIFIED = False
                        consts.MODIFICATION += 1
                        consts.PARAMS_VERSION += 1
                        consts.write_settings()
                        self.save_build_id()
                    finally:
                        self.__task_locked = True

    @property
    def build_id(self):
        return '%s_%s_%s' % (self.build_id_prefix, consts.BUILD_VERSION, consts.PARAMS_VERSION)

    def save_build_id(self):
        with self.admin.lock('$save_build_id'):
            path = os.path.join(self.work_dir, 'locks')
            for file_name in os.listdir(path):
                if file_name.startswith(self.build_id_prefix):
                    os.remove(os.path.join(path, file_name))
            file_write(os.path.join(path, self.build_id), '')

    def check_build(self):
        path = os.path.join(self.work_dir, 'locks')
        if not os.path.exists(os.path.join(path, self.build_id)):
            with self.admin.lock('$build_checking'):
                cur_build_version = consts.BUILD_VERSION
                cur_params_version = consts.PARAMS_VERSION
                build_version = None
                params_version = None
                for file_name in os.listdir(path):
                    if file_name.startswith(self.build_id_prefix):
                        cur_build_id = file_name
                        arr = cur_build_id.split('_')
                        build_version = int(arr[1])
                        params_version = int(arr[2])
                        break
                if params_version != cur_params_version:
                    consts.read_settings()
                if build_version != cur_build_version:
                    self.__task_locked = False
                    try:
                        reload_task(self)
                    finally:
                        self.__task_locked = True
                    consts.read_settings()

    def on_api(self, request):
        error = ''
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            try:
                data = request.get_data()
                if type(data) != str:
                    data = to_unicode(data, 'utf-8')
                method, task_id, item_id, params, modification = json.loads(data)
                if task_id == 0:
                    task = self.admin
                else:
                    task = self.task
                    if not task:
                        task = self.task
                        if not task:
                            lang = consts.lang
                            result = {'status': None, 'data': {'error': lang['error'], \
                                'info': lang['info']}, 'modification': None}
                            result['status'] = self.state
                            if self.state == consts.PROJECT_LOADING:
                                result['data']['project_loading'] = lang['project_loading']
                            elif self.state == consts.PROJECT_NO_PROJECT:
                                result['data']['no_project'] = lang['no_project']
                            elif self.state == consts.PROJECT_ERROR:
                                result['data']['project_error'] = lang['project_error']
                            r ['result'] = result
                            return self.create_post_response(request, r)
                if not task:
                    result = {'status': consts.PROJECT_NO_PROJECT, 'data': None, 'modification': None}
                else:
                    request.task = task
                    self.check_build()
                    result = {'status': consts.RESPONSE, 'data': None, 'modification': consts.MODIFICATION}
                    if task_id and modification and modification != consts.MODIFICATION:
                        result['status'] = consts.PROJECT_MODIFIED
                    elif self.under_maintenance:
                        result['status'] = consts.PROJECT_MAINTAINANCE
                    elif method == 'connect':
                        self.connect(request, task)
                        result['data'] = self.connect(request, task)
                    elif method == 'login':
                        result['data'] = self.login(request, task, params[0])
                    elif method == 'logout':
                        self.logout(request, task)
                        result['status'] = consts.PROJECT_NOT_LOGGED
                        result['data'] = consts.PROJECT_NOT_LOGGED
                    else:
                        if not self.check_session(request, task):
                            result['status'] = consts.PROJECT_NOT_LOGGED
                            result['data'] = consts.PROJECT_NOT_LOGGED
                        else:
                            item = task
                            if task and item_id:
                                item = task.item_by_ID(item_id)
                            self._busy += 1
                            try:
                                data = self.get_response(item, method, params)
                            finally:
                                self._busy -= 1
                            result['data'] = data
                r ['result'] = result
            except AbortException as e:
                traceback.print_exc()
                error = error_message(e)
                r['result'] = {'data': [None, error]}
                r['error'] = error
            except Exception as e:
                traceback.print_exc()
                error = error_message(e)
                if consts.DEBUGGING and task_id != 0:
                    raise
                r['result'] = {'data': [None, error]}
                r['error'] = error
            response = self.create_post_response(request, r)
            request.save_client_cookie(response, self, task)
            return response

    def get_response(self, item, method, params):
        if method == 'open':
            return item.select_records(params, safe=True)
        elif method == 'apply':
            return item.apply_changes(params, safe=True)
        elif method == 'server':
            return self.server_func(item, params[0], params[1])
        elif method == 'print':
            return item.print_report(*params, safe=True), ''
        elif method == 'load':
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

    def on_ext(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            method = get_path_info(request.environ)
            data = request.get_data()
            if type(data) != str:
                data = to_unicode(data, 'utf-8')
            try:
                params = json.loads(data)
            except:
                params = None
            if self.task:
                try:
                    data = None
                    if self.under_maintenance:
                        status = consts.UNDER_MAINTAINANCE
                    elif self.task.on_ext_request:
                        status = consts.RESPONSE
                        self._busy += 1
                        try:
                            data = self.task.on_ext_request(self.task, method, params)
                        finally:
                            self._busy -= 1
                    else:
                        status = None
                    r['result'] = {'status': status, 'data': data, 'modification': consts.MODIFICATION}
                except AbortException as e:
                    traceback.print_exc()
                    r['result'] = {'data': [None, error_message(e)]}
                    r['error'] = error_message(e)
                except Exception as e:
                    traceback.print_exc()
                    r['result'] = {'data': [None, error_message(e)]}
                    r['error'] = error_message(e)
            else:
                r['result'] = {'status': self.state, 'data': None, 'modification': None}
            return self.create_post_response(request, r)

    def on_upload(self, request):
        if request.method == 'POST':
            r = {'result': None, 'error': None}
            task_id = int(request.form.get('task_id'))
            item_id = int(request.form.get('item_id'))
            field_id = int(request.form.get('field_id'))
            path = request.form.get('path')
            if task_id == 0:
                task = self.admin
            else:
                task = self.task
            if task:
                request.task = task
                result = {'status': consts.RESPONSE, 'data': None, 'modification': consts.MODIFICATION}
                r ['result'] = result
                if not self.check_session(request, task):
                    r['result']['status'] = consts.NOT_LOGGED
                    r['result']['data'] = consts.NOT_LOGGED
                else:
                    f = request.files.get('file')
                    file_name = request.form.get('file_name')
                    if f and file_name:
                        base, ext = os.path.splitext(file_name)
                        ext = ext.lower()
                        upload_result = None
                        if task.on_upload:
                             upload_result = task.on_upload(task, path, file_name, f)
                        if upload_result:
                            path, file_name = upload_result
                            r['result']['data'] = {'file_name': file_name, 'path': path}
                        else:
                            if item_id != -1 and field_id != -1:
                                item = task.item_by_ID(item_id)
                                field = item.field_by_ID(field_id)
                                if field.data_type == consts.IMAGE:
                                    if not valid_uploaded_file('image/*', ext):
                                        r['error'] = consts.lang['upload_not_allowed']
                                elif field.data_type == consts.FILE:
                                    if not valid_uploaded_file(field.field_file['accept'], ext):
                                        r['error'] = consts.lang['upload_not_allowed']
                                else:
                                    r['error'] = 'Operation prohibited'
                            else:
                                if not ext in consts.upload_file_ext:
                                    r['error'] = '%s - %s' % (request.form.get('file_name'), consts.lang['upload_not_allowed'])
                                    self.log.error(r['error'])
                            file_name = ('%s_%s%s') % (base, datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'), ext)
                            file_name = secure_filename(file_name)
                            file_name = file_name.replace('?', '')
                            if task_id == 0:
                                path = os.path.join('static', 'builder')
                            else:
                                path = os.path.join('static', 'files')
                            if not r['error']:
                                dir_path = os.path.join(to_unicode(self.work_dir, 'utf-8'), path)
                                if not os.path.exists(dir_path):
                                    os.makedirs(dir_path)
                                f.save(os.path.join(dir_path, file_name))
                                r['result']['data'] = {'file_name': file_name, 'path': path}
                    else:
                        r['error'] = 'File upload invalid parameters'
            else:
                r['result'] = {'status': self.state, 'data': None, 'modification': None}
            return self.create_post_response(request, r)

    def stop(self, sigvalue):
        self.kill()

    def kill(self):
        import signal, subprocess
        if os.name == "nt":
            subprocess.Popen("taskkill /F /T /pid %i" % self.pid, shell=True)
        else :
            os.killpg(self.pid, signal.SIGKILL)
