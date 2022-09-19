import sys

from werkzeug.utils import cached_property

import jam
from .common import consts, error_message

class AbortException(Exception):
    pass

class AbstractItem(object):
    def __init__(self, task, owner, name='', caption=''):
        self.task = task
        self.owner = owner
        self.item_name = name
        self.items = []
        self.table_name = None
        self.ID = None
        self.js_filename = None
        self._events = []
        if owner:
            if not owner.find(name):
                owner.items.append(self)
                if not hasattr(owner, self.item_name):
                    setattr(owner, self.item_name, self)
        self.item_caption = caption
        if self != task:
            self.log = task.log
        self._loader = TracebackLoader(self)

    def task_locked(self):
        try:
            if self.task.ID:
                if self.master:
                    owner = self.master.owner
                else:
                    owner = self.owner
                if owner:
                    return self.task.app.task_locked()
        except:
            pass

    def __setattr__(self, name, value):
        if self.task_locked():
            raise Exception(self.task.language('server_tree_immutable') + \
                ' Item: "%s", Attribute: "%s"' % (self.item_name, name))
        super(AbstractItem, self).__setattr__(name, value)

    @property
    def session(self):
        try:
            return jam.context.session
        except:
            pass

    @property
    def environ(self):
        return jam.context.environ

    @property
    def user_info(self):
        if self.session:
            return self.session['user_info']

    def find(self, name):
        for item in self.items:
            if item.item_name == name:
                return item

    def item_by_ID(self, id_value):
        if self.ID == id_value:
            return self
        for item in self.items:
            result = item.item_by_ID(id_value)
            if result:
                return result

    def all(self, func):
        result = func(self);
        if not result is None:
            return result
        for item in self.items:
            result = item.all(func)
            if not result is None:
                return result

    def write_info(self, info, server):
        info['id'] = self.ID
        info['name'] = self.item_name
        info['caption'] = self.item_caption
        info['visible'] = self.visible
        info['type'] = self.item_type_id
        info['js_filename'] = self.js_filename

    def read_info(self, info):
        self.ID = info['id']
        self.item_name = info['name']
        self.item_caption = info['caption']
        self.visible = info['visible']
        self.item_type_id = info['type']
        self.js_filename = info['js_filename']

    def get_info(self, server=False):
        result = {}
        result['items'] = []
        self.write_info(result, server)
        for item in self.items:
            result['items'].append((item.item_type_id, item.get_info(server)))
        return result

    def get_child_class(self):
        pass

    def set_info(self, info):
        self.read_info(info)
        for item_type_id, item_info in info['items']:
            child = self.get_child_class()(self.task, self, item_info['name'])
            child.item_type_id = item_type_id
            child.set_info(item_info)

    def compile(self):
        self.task.compile_item(self)
        for item in self.items:
            item.compile()

    def bind_item(self):
        pass

    def bind_items(self):
        self.bind_item()
        for item in self.items:
            item.bind_items()
        self.item_type = consts.ITEM_TYPES[self.item_type_id - 1]

    def get_module_name(self):
        result = self.owner.get_module_name() + '.' + self.item_name
        return str(result)

    def store_handlers(self):
        result = {}
        for key, value in self.__dict__.items():
            if key[0:3] == 'on_':
                result[key] = self.__dict__[key]
        return result

    def clear_handlers(self):
        for key, value in self.__dict__.items():
            if key[0:3] == 'on_':
                self.__dict__[key] = None

    def load_handlers(self, handlers):
        for key, value in handlers.items():
            self.__dict__[key] = handlers[key]

    def get_master_field(self, fields, master_field):
        for field in fields:
            if field.ID == master_field:
                return field

    def abort(self, message=''):
        raise AbortException(message)

    def register(self, func):
        setattr(self, func.__name__, func)

    def load_code(self):
        return self.item_name

    def check_operation(self, operation):
        try:
            if not consts.SAFE_MODE:
                return True
            session = self.session
            app = self.task.app
            if self.task == app.admin:
                if session and session['user_info']['admin']:
                    return True
            elif session:
                role_id = session['user_info']['role_id']
                privileges = app.get_role_privileges(role_id)
                priv_dic = privileges.get(self.ID)
                if priv_dic:
                    return priv_dic[operation]
        except:
            return False

    def check_field_restricted(self, field_id, restriction, role_id=None):
        app = self.task.app
        if not consts.SAFE_MODE or self.task == app.admin:
            return False
        if role_id is None:
            if self.session:
                role_id = self.session['user_info']['role_id']
        if role_id:
            restrictions = app.get_role_field_restrictions(role_id)
            restrictions = restrictions.get(field_id)
            return restrictions and restrictions.get(restriction)

    def execute_query(self, cursor, query, params=None, arg_params=False):
        # ~ print(query)
        try:
            if params:
                if arg_params:
                    cursor.execute(query, *params)
                else:
                    cursor.execute(query, params)
            else:
                cursor.execute(query)
        except Exception as x:
            error = error_message(x)
            self.log.exception('Error: %s\n query: %s\n params: %s' % (error, query, params))
            raise

    def can_view(self):
        return self.check_operation('can_view')

    def round(self, value, dec):
        return consts.round(value, dec)

    def float_to_str(self, value):
        return consts.float_to_str(value)

    def cur_to_str(self, value):
        return consts.cur_to_str(value)

    def date_to_str(self, value):
        return consts.date_to_str(value)

    def datetime_to_str(self, value):
        return consts.datetime_to_str(value)

    def str_to_date(self, value):
        return consts.str_to_date(value)

    def str_to_datetime(self, value):
        return consts.str_to_datetime(value)

    def str_to_float(self, value):
        return consts.str_to_float(value)

    def str_to_cur(self, value):
        return consts.str_to_cur(value)


class AbstrGroup(AbstractItem):
    pass


class AbstrTask(AbstractItem):
    def __init__(self, owner, name, caption):
        AbstractItem.__init__(self, self, owner, name, caption)
        self.task = self
        self.item_type_id = consts.TASK_TYPE
        self.history_item = None
        self.log = None

    def task_locked(self):
        try:
            if self.ID:
                return self.app.task_locked()
        except:
            pass

    def write_info(self, info, server):
        super(AbstrTask, self).write_info(info, server)
        info['lookup_lists'] = self.lookup_lists
        if self.history_item:
            info['history_item'] = self.history_item.ID

    def set_info(self, info):
        super(AbstrTask, self).set_info(info)
        self.bind_items()

    def get_child_class(self):
        pass

    def item_by_name(self, item_name):
        for group in self.items:
            if group.item_name == item_name:
                return group
            else:
                for item in group.items:
                    if item.item_name == item_name:
                        return item

    def compile_all(self):
        for module in self.modules:
            del sys.modules[module]
        self.modules = []
        self.compile()

    def language(self, key):
        return consts.language(key)

class AbstrItem(AbstractItem):
    def __init__(self, task, owner, name, caption):
        AbstractItem.__init__(self, task, owner, name, caption)
        self.master = None
        if not isinstance(self, AbstrDetail):
            if self.owner and not hasattr(self.task, self.item_name):
                setattr(self.task, self.item_name, self)

    def write_info(self, info, server):
        role_id = 0
        if consts.SAFE_MODE and not server:
            if self.task != self.task.app.admin:
                role_id = self.session['user_info']['role_id']
        super(AbstrItem, self).write_info(info, server)
        if server:
            info['table_name'] = self.table_name
            info['fields'] = self.field_defs
        else:
            info['fields'] = self.get_field_defs(role_id)
        info['filters'] = self.get_filter_defs(role_id)
        info['reports'] = self.get_reports_info()
        info['default_order'] = self._order_by
        info['primary_key'] = self._primary_key
        info['deleted_flag'] = self._deleted_flag
        info['virtual_table'] = self.virtual_table
        info['master_field'] = self.master_field
        info['master_id'] = self._master_id
        info['master_rec_id'] = self._master_rec_id
        info['keep_history'] = self.keep_history
        info['edit_lock'] = self.edit_lock
        info['view_params'] = self._view_list
        info['edit_params'] = self._edit_list
        info['virtual_table'] = self.virtual_table

    def read_info(self, info):
        super(AbstrItem, self).read_info(info)
        self.create_fields(info['fields'])
        self.create_filters(info['filters'])
        self.reports = info['reports']
        self._order_by = info['default_order']
        self._primary_key = info['primary_key']
        self._deleted_flag = info['deleted_flag']
        self._virtual_table = info['virtual_table']
        self._master_id = info['master_id']
        self._master_rec_id = info['master_rec_id']
        self.keep_history = info['keep_history']
        self.edit_lock = info['edit_lock']
        self._view_list = info['view_params']
        self._edit_list = info['edit_params']
        self.table_name = info['table_name']

    def bind_item(self):
        self._prepare_dataset()

    def can_create(self):
        return self.check_operation('can_create')

    def can_edit(self):
        return self.check_operation('can_edit')

    def can_delete(self):
        return self.check_operation('can_delete')

class AbstrDetail(AbstrItem):

    def write_info(self, info, server):
        super(AbstrDetail, self).write_info(info, server)
        info['prototype_ID'] = self.prototype.ID
        info['master_applies'] = self.master_applies

    def read_info(self, info):
        super(AbstrDetail, self).read_info(info)
        self.owner.details.append(self)
        if not hasattr(self.owner.details, self.item_name):
            setattr(self.owner.details, self.item_name, self)
        self._prototype_id = info['prototype_ID']
        self.master_applies = info['master_applies']

    def bind_item(self):
        super(AbstrDetail, self).bind_item();
        if hasattr(self, '_prototype_id'):
            self.prototype = self.task.item_by_ID(self._prototype_id)
            self.init_fields()

class AbstrReport(AbstractItem):
    def __init__(self, task, owner, name, caption):
        AbstractItem.__init__(self, task, owner, name, caption)
        if not hasattr(self.task, self.item_name):
            setattr(self.task, self.item_name, self)

    def write_info(self, info, server):
        super(AbstrReport, self).write_info(info, server)
        info['fields'] = self.param_defs

    def read_info(self, info):
        super(AbstrReport, self).read_info(info)
        self.create_params(info['fields'])

    def param_by_name(self, name):
        for param in self.params:
            if param.param_name == name:
                return param

    def bind_item(self):
        self.prepare_params()

class TracebackLoader(object):
    def __init__(self, item):
        self.item = item

    def get_source(self, source):
        admin = self.item.task.app.admin
        sys_items = admin.sys_items.copy()
        sys_items.set_where(id=self.item.ID)
        sys_items.open(fields=['f_server_module'])
        return sys_items.f_server_module.value
