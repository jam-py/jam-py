import uuid
import threading
import datetime

import jam
import jam.adm_server as adm_server

class Session(object):
    def __init__(self, owner, user_info= None, env=None):
        self.owner = owner
        self.server = owner.server
        self.uuid = str(uuid.uuid4())
        self.date = datetime.datetime.now()
        self.user_id = None
        self.user_name = None
        self.role_id = None
        self.role_name = None
        self.safe_mode = self.server.admin.safe_mode
        self.client_ip = None
        self.admin = False
        if user_info:
            self.user_id = user_info['user_id']
            self.user_name = user_info['user_name']
            self.role_id = user_info['role_id']
            self.role_name = user_info['role_name']
            self.admin = user_info['admin']
        if env:
            self.client_ip = self.server.get_client_ip(env)

    def user_info(self):
        result = {}
        result['user_id'] = self.user_id
        result['user_name'] = self.user_name
        result['role_id'] = self.role_id
        result['role_name'] = self.role_name
        result['admin'] = self.admin
        return result

    def privileges(self):
        result = None
        if self.role_id:
            result = self.owner.get_privileges(self.role_id)
        return result

    def has_privilege(self, item, priv_name):
        return self.find_privileges(item)[priv_name]

    def find_privileges(self, item):
        if not self.server.admin.safe_mode or item.master or (item.task == self.server.admin) or (item == item.task):
            return {'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True}
        else:
            try:
                priv_dic = self.privileges()[item.ID]
            except:
                priv_dic = None
            if priv_dic:
                return priv_dic
            else:
                return {'can_view': False, 'can_create': False, 'can_edit': False, 'can_delete': False}

class Store(object):
    def __init__(self, owner):
        self.owner = owner
        self.lock = threading.Lock()
        self._store = {}

    def add(self, session):
        with self.lock:
            self._store[session.uuid] = session

    def remove(self, session_id):
        with self.lock:
            del self._store[session_id]

    def find(self, session_id):
        with self.lock:
            return self._store.get(session_id)

    def remove_user(self, user_id):
        with self.lock:
            keys = self._store.keys()
            for key in keys:
                s = self._store.get(key)
                if s and s.user_id == user_id:
                    del self._store[key]

    def check(self):
        pass

class Sessions(object):
    def __init__(self, server, timeout=24*60*60):
        self.server = server
        self.date = datetime.datetime.now()
        self.timeout = timeout
        self.admin_store = Store(self)
        self.task_store = Store(self)

    def connect(self, is_admin, session_id=None, env=None):
        session = self.check_session(is_admin, session_id, env)
        if session:
            return session.uuid

    def check_session(self, is_admin, session_id=None, env=None):
        result = self.find(is_admin, session_id)
        if result and result.safe_mode != self.server.admin.safe_mode:
            self.remove(is_admin, result.uuid)
            result = None
        if not result and not self.server.admin.safe_mode:
            result = self.add(is_admin, None, env)
        jam.context.session = result
        return result

    def add(self, is_admin, user_info= None, env=None):
        session = Session(self, user_info, env)
        if is_admin:
            self.admin_store.add(session)
        else:
            self.task_store.add(session)
        return session

    def remove(self, is_admin, session_id):
        if is_admin:
            self.admin_store.remove(session_id)
        else:
            self.task_store.remove(session_id)

    def find(self, is_admin, session_id):
        if is_admin:
            return self.admin_store.find(session_id)
        else:
            return self.task_store.find(session_id)

    def remove_user(self, is_admin, user_id):
        if is_admin:
            return self.admin_store.remove_user(user_id)
        else:
            return self.task_store.remove_user(user_id)

    def login(self, log, psw_hash, is_admin, env):
        mess = ''
        privileges = None
        if not is_admin and self.server.task and self.server.task.on_login:
            user_info = self.server.task.on_login(self.server.task, log, psw_hash, env)
        else:
            user_info = adm_server.login(self.server.admin, log, psw_hash, is_admin)
        session_id = None
        if user_info:
            self.remove_user(is_admin, user_info['user_id'])
            session_id = self.add(is_admin, user_info, env).uuid
        return session_id

    def logout(self, session_id, is_admin, env):
        self.remove(is_admin, session_id)
        return None

    def get_privileges(self, role_id):
        if self.server.privileges is None:
            roles, privileges = adm_server.get_roles(self.server.admin)
            if self.server.task:
                self.server.task.roles = roles
            self.server.privileges = privileges
        return self.server.privileges[role_id]
