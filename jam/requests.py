#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import uuid
import traceback
import time
import subprocess
import signal
from threading import Lock

import jam
import common
import adm_server

class Server(object):
    def __init__(self):
        self.admin = adm_server.task
        self.admin.server = self
        self.task = None
        self.task_lock = Lock()
        self.users = {}
        self.roles = None
        self._busy = 0
        self.task_server_modified = False
        self.task_client_modified = True
        self.under_maintenance = False
        self.jam_dir = os.path.dirname(jam.__file__)
        self.jam_version = jam.version()
        self.application_pid = None

    def get_task(self):
        if self.task is None:
            with self.task_lock:
                if self.task is None:
                    self.task = adm_server.create_task(self)
        return self.task

    def stop(self, sigvalue):
        print sigvalue, self._busy
        #~ self.app.stop()
        #~ return
        self.kill()
        return
        if sigvalue == 2 and self._busy:
            self.under_maintenance = True
            print 'waiting for %s request(s) to be processed' % self._busy
            sys.stdout.flush()
            i = 0
            while True:
                if self._busy:
                    if i == 50:
                        user_input = raw_input('%s request(s) is(are) active. To kill processes press y, any other key to continue:' \
                            % self._busy)
                        if user_input == 'y':
                            break
                        else:
                            i = 0
                    time.sleep(0.1)
                else:
                    break
                i += 1
        self.kill()

    def kill(self):
        if os.name == "nt":
            subprocess.Popen("taskkill /F /T /pid %i" % self.application_pid, shell=True)
        else :
            os.killpg(self.application_pid, signal.SIGKILL)

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
            try:
                result = func(obj, *params)
            except Exception, e:
                print traceback.format_exc()
                error = e.message
                if not error:
                    error = '%s: server function error - %s' % (obj.item_name, func_name)
        else:
            error = 'item: %s no server function with name %s' % (obj.item_name, func_name)
        return {'error': error, 'result': result}

    def check_task_server_modified(self):
        if self.task_server_modified:
            adm_server.reload_task()
            self.task_server_modified = False

    def check_task_client_modified(self, file_name):
        if self.task_client_modified and file_name == 'index.html':
            adm_server.update_events_code()
            self.task_client_modified = False

    def check_file_name(self, file_name):
        result = os.path.normpath(file_name)
        if not common.SETTINGS['DEBUGGING']:
            result = adm_server.get_minified_name(result)
        base_name = os.path.basename(result)
        parts = result.split(os.sep)
        if parts[0] == 'jam':
            result = os.path.join(os.path.dirname(self.jam_dir), result)
        elif base_name == 'admin.html':
            result = os.path.join(self.jam_dir, base_name)
        if result != file_name and os.path.exists(result):
            return result
        else:
            return file_name

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
        return {
            'task': task.get_info(),
            'settings': self.admin.get_settings(),
            'language': self.admin.get_lang(),
            'user_info': user_info,
            'privileges': priv
        }

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
        return user_uuid

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

    def process_request(self, env, request, user_uuid=None, task_id=None, item_id=None, params=None, ext=None):
        #~ print ''
        #~ print 'process_request: ', request, user_uuid, task_id, item_id, params

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
        elif request == 'login':
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
                data = task.on_request(task, user_info, env, request, obj, params, ext)
            if not data:
                data = self.get_response(is_admin, env, request, user_info, task_id, obj, params, ext)
        finally:
            self._busy -= 1
        return {'status': common.RESPONSE, 'data': data, 'version': task.version}

    def get_response(self, is_admin, env, request, user_info, task_id, item, params, ext):
        if ext:
            if item.on_ext_request:
                return item.on_ext_request(item, request, params, env)
        elif request == 'server_function':
            return self.server_func(item, params[0], params[1], env)
        elif request == 'open':
            if self.has_privilege(user_info, item, 'can_view'):
                return item.select_records(params, user_info, env)
            else:
                return [], item.task.lang['cant_view'] % item.item_caption
        elif request == 'get_record_count':
            return item.get_record_count(params, env)
        elif request == 'apply_changes':
            return item.apply_changes(params, self.find_privileges(user_info, item), user_info, env)
        elif request == 'print_report':
            url = None
            error = None
            if self.has_privilege(user_info, item, 'can_view'):
                url = item.print_report(*params)
            else:
                error = item.task.lang['cant_view'] % item.item_caption
            return {'url': url, 'error': error}
        elif request == 'delete_report':
            return item.delete_report(params)
        elif request == 'logout':
            return self.logout(params, is_admin, env)
        elif request == 'init_client':
            return self.init_client(user_info, is_admin)
        elif request == 'exit' and task_id == 0:
            return True;

server = Server()
