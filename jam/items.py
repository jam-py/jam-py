import sys
import logging

import jam
import jam.lang.langs as langs
import jam.common as common

class AbortException(Exception):
    pass

class DebugException(Exception):
    pass

class AbstractItem(object):
    def __init__(self, owner, name='', caption='', visible = True, item_type_id=0, js_filename=''):
        self.owner = owner
        self.item_name = name
        self.items = []
        self.ID = None
        self._events = []
        self.master = None
        self.js_filename = js_filename
        if owner:
            if not owner.find(name):
                owner.items.append(self)
                if not hasattr(owner, self.item_name):
                    setattr(owner, self.item_name, self)
            self.task = owner.task
        self.item_caption = caption
        self.visible = visible
        self.item_type_id = item_type_id
        self._loader = TracebackLoader(self)

    @property
    def session(self):
        if hasattr(jam.context, 'session'):
            return jam.context.session

    @property
    def environ(self):
        if hasattr(jam.context, 'environ'):
            return jam.context.environ

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
        func(self);
        for item in self.items:
            item.all(func)

    def write_info(self, info):
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

    def get_info(self):
        result = {}
        result['items'] = []
        self.write_info(result)
        for item in self.items:
            result['items'].append((item.item_type_id, item.get_info()))
        return result

    def get_child_class(self, item_type_id):
        pass

    def set_info(self, info):
        self.read_info(info)
        for item_type_id, item_info in info['items']:
            child = self.get_child_class(item_type_id)(self)
            child.item_type_id = item_type_id
            child.set_info(item_info)

    def bind_item(self):
        pass

    def bind_items(self):
        self.bind_item()
        for item in self.items:
            item.bind_items()
        self.item_type = common.ITEM_TYPES[self.item_type_id - 1]

    def get_module_name(self):
        result = self.owner.get_module_name() + '.' + self.item_name
        return str(result)

    def store_handlers(self):
        result = {}
        for key, value in self.__dict__.iteritems():
            if key[0:3] == 'on_':
                result[key] = self.__dict__[key]
        return result

    def clear_handlers(self):
        for key, value in self.__dict__.iteritems():
            if key[0:3] == 'on_':
                self.__dict__[key] = None

    def load_handlers(self, handlers):
        for key, value in handlers.iteritems():
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

class AbstrGroup(AbstractItem):
    pass


class AbstrTask(AbstractItem):
    def __init__(self, owner, name, caption, visible = True, item_type_id=0, js_filename=''):
        AbstractItem.__init__(self, owner, name, caption, visible, item_type_id, js_filename)
        self.task = self
        self.__language = None
        self.item_type_id = common.TASK_TYPE
        self.history_item = None
        self.log = None

    def write_info(self, info):
        super(AbstrTask, self).write_info(info)
        info['lookup_lists'] = self.lookup_lists
        if self.history_item:
            info['history_item'] = self.history_item.ID

    def set_info(self, info):
        super(AbstrTask, self).set_info(info)
        self.bind_items()

    def item_by_name(self, item_name):
        for group in self.items:
            if group.item_name == item_name:
                return group
            else:
                for item in group.items:
                    if item.item_name == item_name:
                        return item

    def compile_item(self, item):
        pass

    def compile_all(self):
        for module in self.modules:
            del sys.modules[module]
        self.modules = []
        self.compile_item(self)
        for group in self.items:
            self.compile_item(group)
        for group in self.items:
            for item in group.items:
                self.compile_item(item)
        for group in self.items:
            for item in group.items:
                if group.item_type_id != common.REPORTS_TYPE:
                    for detail in item.details:
                        self.compile_item(detail)

    def get_language(self):
        return self.__language

    def set_language(self, value):
        self.__language = value
        self.lang = langs.get_lang_dict(value)
        common.SETTINGS['LANGUAGE'] = value

    language = property (get_language, set_language)

    def get_settings(self):
        return common.SETTINGS

    def init_locale(self):
        import locale
        result = {}
        try:
            locale.setlocale(locale.LC_ALL, '')
            loc = locale.localeconv()
            for setting in common.LOCALE_SETTINGS:
                try:
                    common.SETTINGS[setting] = loc['setting'.lower()]
                except:
                    common.SETTINGS[setting] = common.DEFAULT_SETTINGS[setting]
        except:
            pass
        try:
            common.SETTINGS['D_FMT'] = locale.nl_langinfo(locale.D_FMT)
        except:
            common.SETTINGS['D_FMT'] = '%Y-%m-%d'
        common.SETTINGS['D_T_FMT'] = '%s %s' % (common.D_FMT, '%H:%M')

class AbstrItem(AbstractItem):
    def __init__(self, owner, name, caption, visible = True, item_type_id=0, js_filename=''):
        AbstractItem.__init__(self, owner, name, caption, visible, item_type_id, js_filename)
        if not hasattr(self.task, self.item_name):
            setattr(self.task, self.item_name, self)

    def write_info(self, info):
        super(AbstrItem, self).write_info(info)
        info['fields'] = self.field_defs
        info['filters'] = self.filter_defs
        info['reports'] = self.get_reports_info()
        info['default_order'] = self._order_by
        info['primary_key'] = self._primary_key
        info['deleted_flag'] = self._deleted_flag
        info['master_id'] = self._master_id
        info['master_rec_id'] = self._master_rec_id
        info['keep_history'] = self.keep_history

    def read_info(self, info):
        super(AbstrItem, self).read_info(info)
        self.create_fields(info['fields'])
        self.create_filters(info['filters'])
        self.reports = info['reports']
        self._order_by = info['default_order']

    def bind_item(self):
        self.prepare_fields()
        self.prepare_filters()

    def check_operation(self, operation):
        try:
            app = self.task.app
            if not app.admin.safe_mode or self.master or self.task == app.admin:
                return True
            else:
                session = self.session
                if session:
                    role_id = session['user_info']['role_id']
                    privileges = self.task.app.get_privileges(role_id)
                    priv_dic = privileges.get(self.ID)
                    if priv_dic:
                        return priv_dic[operation]
        except:
            return False

    def can_view(self):
        return self.check_operation('can_view')

    def can_create(self):
        return self.check_operation('can_create')

    def can_edit(self):
        return self.check_operation('can_edit')

    def can_delete(self):
        return self.check_operation('can_delete')


class AbstrDetail(AbstrItem):

    def write_info(self, info):
        super(AbstrDetail, self).write_info(info)
        info['prototype_ID'] = self.prototype.ID

    def read_info(self, info):
        super(AbstrDetail, self).read_info(info)
        self.owner.details.append(self)
        if not hasattr(self.owner.details, self.item_name):
            setattr(self.owner.details, self.item_name, self)


class AbstrReport(AbstractItem):
    def __init__(self, owner, name, caption, visible = True, item_type_id=0, js_filename=''):
        AbstractItem.__init__(self, owner, name, caption, visible, item_type_id, js_filename)
        if not hasattr(self.task, self.item_name):
            setattr(self.task, self.item_name, self)

    def write_info(self, info):
        super(AbstrReport, self).write_info(info)
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
