# -*- coding: utf-8 -*-

import sys
import logging

import lang.langs as langs
import common

ITEM_INFO = ITEM_ID, ITEM_NAME, ITEM_CAPTION, ITEM_VISIBLE, ITEM_TYPE, \
    ITEM_ITEMS, ITEM_FIELDS, ITEM_FILTERS, ITEM_CLIENT_CODE, ITEM_REPORTS = range(10)

class AbstractItem(object):
    def __init__(self, owner, name='', caption='', visible = True, item_type_id=0):
        self.owner = owner
        self.item_name = name
        self.items = []
        self.ID = None
        self.client_code = None
        self._events = []
        if owner:
            if not owner.find(name):
                owner.items.append(self)
            self.task = owner.task
        self.item_caption = caption
        self.visible = visible
        self.item_type_id = item_type_id

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

    def write_info(self, info, web=None):
        info[ITEM_ID] = self.ID
        info[ITEM_NAME] = self.item_name
        info[ITEM_CAPTION] = self.item_caption
        info[ITEM_VISIBLE] = self.visible
        info[ITEM_TYPE] = self.item_type_id
        if not web:
            info[ITEM_CLIENT_CODE] = self.client_code

    def read_info(self, info):
        self.ID = info[ITEM_ID]
        self.item_name = info[ITEM_NAME]
        self.item_caption = info[ITEM_CAPTION]
        self.visible = info[ITEM_VISIBLE]
        self.item_type_id = info[ITEM_TYPE]
        self.item_type = common.ITEM_TYPES[self.item_type_id - 1]
        self.client_code = info[ITEM_CLIENT_CODE]

    def get_info(self, web=None):
        result = [None for i in range(len(ITEM_INFO))]
        result[ITEM_ITEMS] = []
        self.write_info(result, web)
        for item in self.items:
            result[ITEM_ITEMS].append((item.item_type_id, item.get_info(web)))
        return result

    def get_child_class(self, item_type_id):
        pass

    def set_info(self, info):
        self.read_info(info)
        for item_type_id, item_info in info[ITEM_ITEMS]:
            child = self.get_child_class(item_type_id)(self)
            child.item_type_id = item_type_id
            child.set_info(item_info)

    def bind_item(self):
        pass

    def bind_items(self):
        self.bind_item()
        for item in self.items:
            item.bind_items()

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


class Group(AbstractItem):
    pass


class Task(AbstractItem):
    def __init__(self, owner, name, caption, visible = True, item_type_id=0):
        AbstractItem.__init__(self, owner, name, caption, visible, item_type_id)
        self.task = self
        self.__language = None
        self.item_type_id = common.TASK_TYPE
        self.log = None

    def set_info(self, info):
        super(Task, self).set_info(info)
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
        common.SETTINGS['LAGUAGE'] = value

    language = property (get_language, set_language)

    def get_lang(self):
        return self.lang

    def write_setting(self, connsection):
        pass

    def get_settings(self):
        return common.SETTINGS

    def set_settings(self, value):
        common.SETTINGS = value
        for key in common.SETTINGS.keys():
            common.__dict__[key] = common.SETTINGS[key]
        self.language = common.SETTINGS['LANGUAGE']
        if common.SETTINGS['LOG_FILE'].strip():
            sys.stdout = open(common.SETTINGS['LOG_FILE'].strip(), 'a')
            sys.stderr = open(common.SETTINGS['LOG_FILE'].strip(), 'a')

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
            common.SETTINGS['D_T_FMT'] = '%s %s' % (common.D_FMT, '%H:%M')
        except:
            common.D_FMT = '%x'
            common.D_T_FMT = '%X'

class Item(AbstractItem):

    def write_info(self, info, web=None):
        super(Item, self).write_info(info, web)
        info[ITEM_FIELDS] = self.get_fields_info()
        info[ITEM_FILTERS] = self.get_filters_info()
        info[ITEM_REPORTS] = self.get_reports_info()

    def read_info(self, info):
        super(Item, self).read_info(info)
        self.create_fields(info[ITEM_FIELDS])
        self.create_filters(info[ITEM_FILTERS])
        self.reports = info[ITEM_REPORTS]

    def bind_item(self):
        self.prepare_fields()
        self.prepare_filters()
        self.init_reports()
        self.fields = list(self._fields)

    def prepare_fields(self):
        for field in self._fields:
            if field.lookup_item:
                field.lookup_item = self.task.item_by_ID(field.lookup_item)
            if field.master_field:
                field.master_field = self.get_master_field(self._fields, field.master_field)
            if field.lookup_field and type(field.lookup_field) == int:
                field.lookup_field = field.lookup_item._field_by_ID(field.lookup_field).field_name

    def prepare_filters(self):
        for fltr in self.filters:
            setattr(self.filters, fltr.filter_name, fltr)
            if fltr.field.lookup_item and type(fltr.field.lookup_item) == int:
                fltr.field.lookup_item = self.task.item_by_ID(fltr.field.lookup_item)
        self._filter_row = []
        for i, fltr in enumerate(self.filters):
            self._filter_row.append(None)
            fltr.field.bind_index = i
        length = len(self.filters)
        i = 0
        for fltr in self.filters:
            if fltr.field.lookup_item:
                self._filter_row.append(None)
                fltr.field.lookup_index = length + i
                i += 1

class Detail(Item):

    def read_info(self, info):
        super(Detail, self).read_info(info)
        self.owner.details.append(self)

class Report(AbstractItem):

    def __getattr__(self, name):
        if self.param_by_name(name):
            obj = self.param_by_name(name)
            if obj:
                setattr(self, name, obj)
                return obj

    def write_info(self, info, web=None):
        super(Report, self).write_info(info, web)
        info[ITEM_FIELDS] = self.get_params_info()

    def read_info(self, info):
        super(Report, self).read_info(info)
        self.create_params(info[ITEM_FIELDS])

    def param_by_name(self, name):
        for param in self.params:
            if param.param_name == name:
                return param

    def bind_item(self):
        self.prepare_params()

    def prepare_params(self):
        for param in self.params:
            if param.lookup_item and type(param.lookup_item) == int:
                param.lookup_item = self.task.item_by_ID(param.lookup_item)
            if param.lookup_field and type(param.lookup_field) == int:
                param.lookup_field = param.lookup_item._field_by_ID(param.lookup_field).field_name
