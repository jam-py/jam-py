import sys
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

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, Forbidden
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wsgi import get_path_info
from werkzeug.local import Local, LocalManager
from werkzeug.http import parse_date, http_date
from werkzeug.utils import cached_property, secure_filename, redirect
from .secure_cookie.cookie import SecureCookie

from .common import consts, error_message, file_read, file_write
from .common import consts, ProjectError, ProjectNotCompleted
from .common import json_defaul_handler, compressBuf
from .common import validate_image, valid_uploaded_file
from .common import to_str
from .admin.admin import create_admin, login_user, get_privileges, get_field_restrictions
from .admin.admin import user_valid_ip, user_valid_uuid
from .admin.builder import update_events_code
from .admin.import_metadata import import_metadata
from .tree import AbortException
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
        return '%s_session_%s' % (self.task.item_name, self.environ['SERVER_PORT'])

    @cached_property
    def client_cookie(self):
        return JamSecureCookie.load_cookie(self, key=self.session_key, secret_key=self.task.app.admin.secret_key)

    def save_client_cookie(self, response, task):
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
        self.work_dir = to_str(work_dir)
        self.state = consts.PROJECT_NONE
        self.__task = None
        self.privileges = None
        self.field_restrictions = None
        self.__is_locked = 0
        self.__loading = False
        self._busy = 0
        self.pid = os.getpid()
        self.jam_dir = to_str(os.path.realpath(os.path.dirname(jam.__file__)))
        self.jam_version = jam.version()
        self.application_files = {
            '/': self.work_dir,
            '/jam/': self.jam_dir
        }
        self.fileserver = SharedDataMiddleware(None, self.application_files, cache_timeout=1)
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
        result = self.__task
        if not result and not self.__loading:
            self.__loading = True
            try:
                result = create_task(self)
                update_events_code(self.admin, loading=True)
                consts.CLIENT_MODIFIED = False
                consts.SERVER_MODIFIED = False
                consts.write_settings()
                self.state = consts.RESPONSE
                result.__task_locked = True
            except ProjectNotCompleted:
                raise
            except:
                traceback.print_exc()
                raise ProjectError()
            finally:
                self.__loading = False
        else:
            time.sleep(1)
            result = self.__task
            if not result:
                result = self.create_task()
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

    @cached_property
    def production(self):
        return os.path.exists(os.path.join(self.work_dir, 'builder.html'))

    def __call__(self, environ, start_response):
        jam.context.environ = environ
        jam.context.session = None
        request = JamRequest(environ)
        if consts.MAX_CONTENT_LENGTH > 0:
            request.max_content_length = 1024 * 1024 * consts.MAX_CONTENT_LENGTH
        try:
            if not self.under_maintenance:
                if self.__task and self.task.on_request:
                    if not self.production:
                        self.check_project_modified()
                    response = self.task.on_request(self.task, request)
                    if response:
                        return response(environ, start_response)
                parts = request.path.strip('/').split('/')
                prefix = parts[0]
                suffix = parts[len(parts) - 1]
                if prefix == 'api':
                    return self.on_api(request)(environ, start_response)
                elif prefix == 'upload':
                    return self.on_upload(request)(environ, start_response)
                elif prefix == 'jam':
                    return self.on_jam_file(request, environ, suffix)(environ, start_response)
                elif prefix in ['js', 'css']:
                    return self.on_project_file(request, environ, suffix)(environ, start_response)
                elif prefix in ['builder.html', 'builder_login.html']:
                    return self.on_builder(request, prefix)(environ, start_response)
                elif prefix == 'ext':
                    return self.on_ext(request)(environ, start_response)
                elif prefix in ['static', 'favicon.ico', 'dummy.html']:
                    return Response('')(environ, start_response)
                elif not prefix or prefix in ['index.html', 'login.html']:
                    return self.on_index(request, prefix)(environ, start_response)
                elif prefix == 'logout':
                    if self.task.on_logout:
                        response = self.task.on_logout(self.task, request)
                        if response:
                            return response
                    response = self.logout(request)
                    return response(environ, start_response)
                else:
                    print(request.path)
                    raise NotFound()
        except ProjectNotCompleted as e:
            self.log.exception(error_message(e))
            return self.show_information(consts.lang['no_project'])(environ, start_response)
        except ProjectError as e:
            self.log.exception(error_message(e))
            return self.show_error(consts.lang['project_error'])(environ, start_response)
        except HTTPException as e:
            self.log.exception(error_message(e))
            return self.show_error(error_message(e))(environ, start_response)
            # ~ return e

    def serve_page(self, file_name, dic=None):
        path = os.path.join(self.work_dir, file_name)
        if os.path.exists(path):
            page = file_read(path)
            if dic:
                page = page % dic
            return Response(page, mimetype="text/html")
        else:
            raise NotFound()

    def show_information(self, message):
        return self.show_error(message, 'alert-info', 'Information')

    def show_error(self, message, error_class=None, error_type=None):
        if not error_class:
            error_class = 'alert-error'
        if not error_type:
            error_type = 'Error'
        path = os.path.join(self.jam_dir, 'html', 'error.html')
        return self.serve_page(path, {
            'error_class': error_class,
            'error_type': error_type,
            'message': message
        })

    def on_index(self, request, file_name):
        if file_name == 'login.html':
            login_params = {
                'title': self.task.item_name,
                'error': '',
                'form_title': consts.lang['log_in'],
                'login_text': consts.lang['login'],
                'password_text': consts.lang['password'],
                'login': '',
                'password': ''
            }
            login_path = os.path.join(self.work_dir, 'login.html')
            if not os.path.exists(login_path):
                login_path = os.path.join(self.jam_dir, 'html', 'login.html')
            if request.method == 'POST':
                response = self.login(request, self.task, request.form)
                if response:
                    return response
                else:
                    form = request.form.to_dict()
                    login_params['error'] = 'error-modal-border'
                    login_params['login'] = form['login']
                    login_params['password'] = form['password']
                    return self.serve_page(login_path, login_params)
            else:
                return self.serve_page(login_path, login_params)
        else:
            if self.check_session(request, self.task):
                file_name = 'index.html'
                request.environ['PATH_INFO'] = '/%s' % file_name
                path = os.path.join(self.work_dir, file_name)
                self.check_project_modified()
                return self.fileserver
            else:
                return redirect('/login.html')

    def on_builder(self, request, file_name):
        if file_name == 'builder.html':
            if os.path.exists(os.path.join(self.work_dir, file_name)):
                request.environ['PATH_INFO'] = '/%s' % file_name
                return self.fileserver
            if self.check_session(request, self.admin):
                request.environ['PATH_INFO'] = '/jam/html/%s' % file_name
                return self.fileserver
            else:
                return redirect('/builder_login.html')
        elif file_name == 'builder_login.html':
            login_params = {
                'title': 'Jam.py Application Builder',
                'error': '',
                'form_title': consts.lang['log_in'] + ' - Application Builder',
                'login_text': consts.lang['login'],
                'password_text': consts.lang['password'],
                'login': '',
                'password': ''
            }
            login_path = os.path.join(self.jam_dir, 'html', 'login.html')
            if request.method == 'POST':
                response = self.login(request, self.admin, request.form)
                if response:
                    return response
                else:
                    form = request.form.to_dict()
                    login_params['error'] = 'error-modal-border'
                    login_params['login'] = form['login']
                    login_params['password'] = form['password']
                    return self.serve_page(login_path, login_params)
            else:
                return self.serve_page(login_path, login_params)

    def serve_prog_file(self, request, environ, file_name):
        base, ext = os.path.splitext(file_name)
        if consts.COMPRESSED_JS and ext and ext in ['.js', '.css'] and file_name != 'project.css':
            min_file_name = base + '.min' + ext
            environ['PATH_INFO'] = environ['PATH_INFO'].replace(file_name, min_file_name)
        return self.fileserver

    def on_jam_file(self, request, environ, file_name):
        return self.serve_prog_file(request, environ, file_name)

    def on_project_file(self, request, environ, file_name):
        if self.check_session(request, self.task):
            return self.serve_prog_file(request, environ, file_name)
        else:
            raise Forbidden()

    def create_post_response(self, request, result):
        response = Response()
        response.headers['Content-Type'] = 'application/json'
        try:
            buff = json.dumps(result, default=json_defaul_handler)
        except Exception as e:
            self.log.exception('wsgi.py create_post_response error %s' % error_message(e))
            self.log.debug(result)
            raise
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            response.set_data(buff)
            return response
        buff = compressBuf(buff)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Content-Length'] = len(buff)
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
        request.task = task
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
        request.task = task
        ip = None
        session_uuid = None
        ip = self.get_client_address(request)
        session_uuid = str(uuid.uuid4())
        if self.admin == task or task.on_login is None:
            user_info = self.default_login(task, form_data['login'], form_data['password'], ip, session_uuid)
        elif task.on_login:
            try:
                user_info = task.on_login(task, form_data, {'ip': ip, 'session_uuid': session_uuid})
            except:
                user_info = None
                traceback.print_exc()
        if user_info:
            self.create_session(request, task, user_info, session_uuid)
            if self.admin == task:
                response = redirect('/builder.html')
            else:
                response = redirect('/')
            request.save_client_cookie(response, task)
            return response


    def logout(self, request, task=None):
        if task is None:
            task = self.task
        request.task = task
        response = None
        if self.admin == task:
            del request.client_cookie['info']
        else:
            response = redirect('/')
            del request.client_cookie['info']
            request.save_client_cookie(response, self.task)
        jam.context.session = None
        return response

    def get_role_privileges(self, role_id):
        if consts.SAFE_MODE:
            if self.privileges is None:
                self.privileges = get_privileges(self.admin)
            return self.privileges[role_id]

    def get_role_field_restrictions(self, role_id):
        if consts.SAFE_MODE:
            if self.field_restrictions is None:
                self.field_restrictions = get_field_restrictions(self.admin)
            return self.field_restrictions[role_id]
        else:
            return {}

    def init_client(self, task):
        session = jam.context.session
        priv = None
        user_info = {}
        if session:
            user_info = session['user_info']
            role_id = user_info.get('role_id')
            if role_id:
                priv = self.get_role_privileges(role_id)
        templates = ''
        templates_path = os.path.join(self.work_dir, 'templates.html')
        if not os.path.exists(templates_path):
            file_write(templates_path, '')
        if task != self.admin:
            templates = file_read(templates_path)
        result = {
            'task': task.get_info(),
            'templates': templates,
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
                success = False
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
                except:
                    self.log.exception('wsgi.py create_post_response error')
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

    @property
    def under_maintenance(self):
        return consts.MAINTENANCE

    @property
    def client_modified(self):
        return consts.CLIENT_MODIFIED

    @client_modified.setter
    def client_modified(self, value):
        consts.CLIENT_MODIFIED = value
        consts.MODIFICATION += 1
        consts.PARAMS_VERSION += 1
        consts.write_settings()
        self.save_build_id()

    @property
    def server_modified(self):
        return consts.SERVER_MODIFIED

    @server_modified.setter
    def server_modified(self, value):
        consts.SERVER_MODIFIED = value
        consts.MODIFICATION += 1
        consts.PARAMS_VERSION += 1
        consts.write_settings()
        self.save_build_id()

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
                    data = to_str(data, 'utf-8')
                method, task_id, item_id, params, modification = json.loads(data)
                if task_id == 0:
                    if self.production:
                        raise Exception('Server is in production mode.')
                    task = self.admin
                else:
                    task = self.task
                request.task = task
                self.check_build()
                result = {'status': consts.RESPONSE, 'data': None, 'modification': consts.MODIFICATION}
                if not self.check_session(request, task):
                    result['status'] = consts.PROJECT_NOT_LOGGED
                elif task_id and modification and modification != consts.MODIFICATION:
                    result['status'] = consts.PROJECT_MODIFIED
                elif self.under_maintenance:
                    result['status'] = consts.PROJECT_MAINTAINANCE
                elif method == 'logout':
                    self.logout(request, task)
                    result['status'] = consts.PROJECT_NOT_LOGGED
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
                self.log.exception(error_message(e))
                error = error_message(e)
                if consts.DEBUGGING and task_id != 0:
                    raise
                r['result'] = {'data': [None, error]}
                r['error'] = error
            response = self.create_post_response(request, r)
            request.save_client_cookie(response, task)
            return response

    def get_response(self, item, method, params):
        if method == 'open':
            return item.select_records(params, client_request=True)
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
                data = to_str(data, 'utf-8')
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
                            file_name = secure_filename(file_name)
                            file_name = file_name.replace('?', '')
                            base, ext = os.path.splitext(file_name)
                            date_suffix = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
                            file_name = ('%s_%s%s') % (base, date_suffix, ext)
                            if len(file_name) > 255:
                                base = base[:len(base) - (len(file_name) - 255)]
                                file_name = ('%s_%s%s') % (base, date_suffix, ext)
                            if task_id == 0:
                                path = os.path.join('static', 'builder')
                            else:
                                path = os.path.join('static', 'files')
                            if not r['error']:
                                dir_path = os.path.join(to_str(self.work_dir, 'utf-8'), path)
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
