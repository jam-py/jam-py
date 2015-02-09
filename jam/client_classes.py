# -*- coding: utf-8 -*-

import sys, os
os.environ['LIBOVERLAY_SCROLLBAR'] = '0'

import hashlib
import inspect

import interface
import common
from items import *
from dataset import *

class ClientField(DBField, interface.FieldInterface):
    def __init__(self, owner, info):
        DBField.__init__(self)
        interface.FieldInterface.__init__(self)
        self.owner = owner
        if info:
            self.set_info(info)
        self.master_field_name = None

    def do_before_changed(self, new_value, new_lookup_value):
        self.show_error_mark(False)
        return super(ClientField, self).do_before_changed(new_value, new_lookup_value)

    def do_on_error(self, mess, err=None):
        self.show_error_mark(True)
        super(ClientField, self).do_on_error(mess, err)

    def update_controls(self, owner_updating=False):
        for control in self.controls:
            control.update()
        if not owner_updating:
            for control in self.owner.controls:
                control.update_field(self)

    def clear_value(self, widget = None):
        self.set_value(None)

    def show_invalid_mess(self, mess):
        self.owner.show_invalid_mess(mess)

class ClientFilterField(ClientField):
    def __init__(self, fltr, field):
        ClientField.__init__(self, field.owner, field.get_info())
        self.filter = fltr
        self.edit_visible = True

    def do_before_changed(self, new_value, new_lookup_value):
        self.show_error_mark(False)

    def get_row(self):
        return self.owner._filter_row

    def check_reqired(self, value):
        return True

    def update_controls(self):
        for control in self.controls:
            control.update()

    def set_modified(self, value):
        pass

    def set_record_status(self, value):
        pass

    def do_after_changed(self, lookup_item):
        if self.owner.on_filter_changed:
            self.owner.on_filter_changed(self.filter)
        self.update_controls()

    def set_read_only(self, value):
        self._read_only = value
        self.update_controls()

    def get_read_only(self):
        return self._read_only
    read_only = property (get_read_only, set_read_only)

    def check_reqired(self):
        return False

class ClientFilter(DBFilter):
    def __init__(self, owner, info):
        DBFilter.__init__(self)
        self.owner = owner
        self.set_info(info)
        field = self.owner._field_by_name(self.field_name)
        self.field = ClientFilterField(self, field)
        self.read_only = False
        self.list = None

    def set_read_only(self, value):
        self.field.read_only = value

    def get_read_only(self):
        return self.field.read_only

    read_only = property (get_read_only, set_read_only)

    def copy(self, owner):
        return ClientFilter(owner, self.get_info())


class ClientParam(ClientField):
    def __init__(self, info, owner):
        ClientField.__init__(self, None, info)
        self.param_name = self.field_name
        self.owner = owner
        self.edit_value = None
        self.param_lookup_value = None

    def system_field(self):
        return False

    def get_data(self):
        return self.edit_value

    def set_data(self, value):
        self.edit_value = value

    def get_lookup_data(self):
        return self.param_lookup_value

    def set_lookup_data(self, value):
        self.param_lookup_value = value

    def update_controls(self):
        for control in self.controls:
            control.update()

    def raw_display_text(self):
        result = ''
        if self.lookup_item:
            result = self.lookup_text
        else:
            result = self.text
        return result

    def show_invalid_mess(self, mess):
        if mess:
            print mess

    def do_before_changed(self, new_value, new_lookup_value):
        pass

    def do_after_changed(self, lookup_item):
        self.update_controls()

    def do_on_change_lookup_field(self, lookup_value=None, slave_field_values=None):
        self.set_lookup_value(lookup_value)


class ClientDataset(Dataset, interface.ItemInterface):
    def __init__(self):
        Dataset.__init__(self)
        interface.ItemInterface.__init__(self)
        self.reports = []
        self.on_update_controls = None

    def copy(self, filters=True, details=True, handlers=True):
        result = super(ClientDataset, self).copy(filters, details, handlers)
        return result

    def __getattr__(self, name):
        if name[0:7] == 'server_':
            obj = lambda *params: self.send_request(name, params)
            return obj
        elif self.detail_by_name(name):
            obj = self.detail_by_name(name)
            setattr(self, name, obj)
            return obj
        else:
            return super(ClientDataset, self).__getattr__(name)

    def send_request(self, command, params = None):
        return self.task.process_request(command, self.ID, params)

    def create_fields(self, fields_info):
        for info in fields_info:
            self._fields.append(ClientField(self, info))

    def init_fields(self):
        return list(self._fields)

    def init_reports(self):
        reports = []
        if not self.master:
            for rep_id in self.reports:
                reports.append(self.task.item_by_ID(rep_id))
        self.reports = reports

        return list(self._fields)

    def create_filters(self, filters_info):
        for info in filters_info:
            self.filters.append(ClientFilter(self, info))

    def do_internal_open(self, params):
        return self.send_request('open', params)

    def update_controls(self, state=None):
        if state is None:
            state = common.UPDATE_REFRESH
        if self.controls_enabled():
            for field in self.fields:
                field.update_controls(owner_updating=True)
            if self.on_update_controls:
                self.on_update_controls(self)
            for control in self.controls:
                control.update(state)

    def refresh_record(self):
        if self.id.value:
            fields = [field.field_name for field in self.fields if not (field.calculated or field.master_field)]
            values = self.field_by_id(self.id.value, fields)
            for i, field in enumerate(fields):
                self._records[self.rec_no][self.field_by_name(field).bind_index] = values[i]
        self.update_controls(common.UPDATE_SCROLLED)

    def do_apply(self, params=None):
        result = True
        if not self.master and self.log_changes:
            changes = {}
            self.change_log.get_changes(changes)
            if changes['data']:
                data = self.send_request('apply_changes', (changes, params))
                if data:
                    if data['error']:
#                        self.warning(data['error']);
                        raise Exception, data['error']
                    else:
                        self.change_log.update(data['result'])
        return result

    def field_by_id(self, id_value, field_name):
        return self.send_request('get_field_by_id', (id_value, field_name))


class ClientItem(Item, ClientDataset):
    def __init__(self, owner=None, name='', caption='', visible = True):
        Item.__init__(self, owner, name, caption, visible)
        ClientDataset.__init__(self)
        self.limit = 200

    def get_child_class(self, item_type_id):
        return ClientDetail


class ClientReport(Report, interface.ReportInterface):
    def __init__(self, owner, name='', caption='', visible = True):
        Report.__init__(self, owner, name, caption, visible)
        interface.ReportInterface.__init__(self)
        self.params = []

    def __getattr__(self, name):
        if name == 'edit_ui' :
            obj = self.send_request('get_edit_ui')
            setattr(self, name, obj)
            return obj
        else:
            return super(ClientReport, self).__getattr__(name)

    def create_params(self, params_info):
        for info in params_info:
            self.params.append(ClientParam(info, self))

    def send_request(self, command, params = None):
        return self.task.process_request(command, self.ID, params)

    def send_to_server(self):
        param_values = []
        for param in self.params:
            param_values.append(param.value)
        url = self.send_request('print_report', (param_values, self.task.url, self.extension))
        url_file = os.path.basename(url)
        if url:
            try:
                if self.task.url:
                    file_name, file_extension = os.path.splitext(url)
                    import urllib2, tempfile
                    data = urllib2.urlopen(url).read()
                    f, temp_file = tempfile.mkstemp(suffix=file_extension)
                    f = os.fdopen(f, 'wb')
                    f.write(data)
                    f.close()
                    url = temp_file
                    self.send_request('delete_report', url_file)
            except Exception, e:
                print e
                pass
        return url

    def show_report(self, url):
        self.task.open_file(url)

class AbstractClientTask(Task, interface.TaskInterface):
    def __init__(self, url=None, headers=None):
        Task.__init__(self, None, None, None, None)
        self.url = url
        self.headers = headers
        self.user_id = None
        self.user_info = None
        self.user_privileges = None
        self.ID = None
        self.on_before_show_main_form = None
        self.on_destroy_form = None
        self.on_login = None
        self.on_before_show_view_form = None
        self.on_before_show_edit_form = None
        self.on_before_show_filter_form = None
        self.on_before_show_params_form = None
        self.on_after_show_view_form = None
        self.on_after_show_edit_form = None
        self.on_after_show_filter_form = None
        self.on_after_show_params_form = None
        self.on_edit_keypressed = None
        self.on_view_keypressed = None
        self.on_edit_form_close_query = None
        self.on_view_form_close_query = None
        self.work_dir = os.getcwd()
        self._send_request = None
        self.crash_exit_file = '.edits.flt'
        self.tray_info = {}

    def get_child_class(self, item_type_id):
        if item_type_id == common.REPORTS_TYPE:
            return ClientReportGroup
        else:
            return ClientGroup

    def get_module_name(self):
        return str(self.item_name + '_' + 'client')

    def compile_item(self, item):
        item.module_name = None
        code = item.client_code
        item.module_name = item.get_module_name()
        item_module = type(sys)(item.module_name )
        item_module.__dict__['this'] = item
        item_module.__dict__.update(globals())
        if item.owner:
            sys.modules[item.owner.get_module_name()].__dict__[item.module_name] = item_module
        sys.modules[item.module_name] = item_module
        if code:
            code = code.encode()
            comp_code = compile(code, item.module_name, "exec")
            exec comp_code in item_module.__dict__
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                setattr(item, func_name, func)
        del code

    def __getattr__(self, name):
        if name == 'ui':
            obj = self.send_request('get_ui')
            setattr(self, name, obj)
            return obj
        elif self.item_by_name(name):
            obj = self.item_by_name(name)
            setattr(self, name, obj)
            return obj
        elif name[0:7] == 'server_':
            obj = lambda *params: self.send_request(name, params)
            return obj
        elif name == 'reports':
            obj = self.send_request('get_reports')
            setattr(self, name, obj)
            return obj
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def send_request(self, request, params=None):
        return self.process_request(request, self.ID, params)

    def process_request(self, request, item_id, params=None):

        def repeat_request():
            return self.process_request(request, item_id, params)

        if not self._send_request:
            common.URL = self.url
            common.HEADERS = self.headers
            if common.URL:
                from webclient import Aws
#                aws = Aws('http://%s/api' % common.URL, common.HEADERS)
                aws = Aws('%s/api' % common.URL, common.HEADERS)

                def _send_request(request, user_id, task_id, item_id, params=None):
                    r, e = aws.send_request(request, user_id, task_id, item_id, params)
                    if e:
                        print 'request error:', request + ' ' + e
                        if e.find(u'Errno 111') != -1:
                            from interface import error_dialog
                            error_dialog(u'Сервер не доступен.')
                        return None
                    else:
                        return r
            else:
                from server import get_request
                def _send_request(request, user_id, task_id, item_id, params=None):
                    return get_request(None, request, user_id, task_id, item_id, params)
            self._send_request = _send_request
        data = self._send_request(request, self.user_id, self.ID, item_id, params)
        if data:
            status = data['status']
            result = data['data']
            if status == common.UNDER_MAINTAINANCE:
                self.warning(self.lang['website_maintenance'])
                return
            if status == common.NOT_LOGGED and self.user_id:
                return self.login(repeat_request)
            return result

    def get_info(self):
        info = self.send_request('init_client')
        if info == common.NOT_LOGGED:
            return self.login(self.run)
        self.set_settings(info['settings'])
        self.user_info = info['user_info']
        self.user_privileges = info['privileges']
        return info['task']

    def login(self, func=None):
        log, psw = interface.login()
        psw_hash = hashlib.md5(psw).hexdigest()
        self.user_id = self.send_request('login', (log, psw_hash))
        if self.user_id:
            if func:
                return func()
        else:
            self.login(self.run)

    def get_ui_file(self, file_name):
        return self.send_request('get_ui_file', params = file_name)

    def load(self):
        info = self.get_info()
        if info:
            self.set_info(info)
            self.compile_all()
            return True

    def run(self):
        if self.load():
            self.show()

    def show(self):
        self.main_form = interface.MainWindow(self, self.ui)
        if self.on_before_show_main_form:
            self.on_before_show_main_form(self)
        self.main_form.show()

    def logout(self):
        if self.user_id:
            self.send_request('logout', self.user_id)
            self.user_id = None
            self.items = []

    def has_privilege(self, item, priv_name):
        if not self.user_privileges or item.master:
            return True
        else:
            if not self.user_privileges:
                return False
            try:
                priv_dic = self.user_privileges[item.ID]
            except:
                priv_dic = None
            if priv_dic:
                return priv_dic[priv_name]
            else:
                return False

    def open_file(self, url):
        import subprocess
        if os.name == "posix":
            subprocess.Popen(["xdg-open", url])
        else:
            try:
                os.startfile(url)
            except:
                pass

    def do_on_destroy_form(self):
        self.logout()
        if self.on_destroy_form:
            self.on_destroy_form(self)


class AdminTask(AbstractClientTask):
    def __init__(self, url=None, headers=None):
        AbstractClientTask.__init__(self, url, headers)
        self.ID = 0

    def has_privilege(self, item, priv_name):
        return True

    def compile_all(self):
        module_name = 'adm_client'
        module = type(sys)(module_name)
        module.__dict__['task'] = self
        (filepath, filename) = os.path.split(__file__)
        with open(os.path.join(filepath, module_name + '.py'), 'r') as f:
            code = f.read()
        comp_code = compile(code, module_name, "exec")
        sys.modules[module_name] = module
        exec comp_code in module.__dict__


class ClientTask(AbstractClientTask):
    def __init__(self, url=None, headers=None):
        AbstractClientTask.__init__(self, url, headers)


class ClientGroup(Group):
    def __init__(self, owner, name='', caption='', visible=True):
        Group.__init__(self, owner, name, caption, visible)
        self.on_before_show_view_form = None
        self.on_before_show_edit_form = None
        self.on_before_show_filter_form = None
        self.on_after_show_view_form = None
        self.on_after_show_edit_form = None
        self.on_after_show_filter_form = None
        self.on_edit_form_close_query = None
        self.on_view_form_close_query = None
        self.on_edit_keypressed = None
        self.on_view_keypressed = None

    def __getattr__(self, name):
        if self.find(name):
            return self.find(name)
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def get_child_class(self, item_type_id):
        return ClientItem

class ClientReportGroup(Group):
    def __init__(self, owner, name='', caption='', visible=True):
        Group.__init__(self, owner, name, caption, visible)
        self.on_before_show_params_form = None
        self.on_before_print_report = None
        self.on_print_report = None

    def __getattr__(self, name):
        if self.find(name):
            return self.find(name)
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def get_child_class(self, item_type_id):
        return ClientReport

class ClientDetail(Detail, ClientDataset):
    def __init__(self, owner, name='', caption='', visible=True):
        Detail.__init__(self, owner, name, caption, True)
        ClientDataset.__init__(self)
        self.master = owner

    def get_child_class(self, item_type_id):
        return ClientDetail

    def send_request(self, command, params = None):
        return self.task.process_request(command, self.ID, params)

    def do_internal_post(self):
        return {'success': True, 'id': None, 'message': '', 'detail_ids': None}

    def create_edit_form(self, parent):
        self.edit_form = interface.ItemWindow(self, self.edit_ui, parent)
        self.edit_form.window.connect('delete-event', self.check_edit)
        self.edit_form.window.connect("key-press-event", self.edit_keypressed)
        if self.task.on_before_show_edit_form:
            self.task.on_before_show_edit_form(self)
        if self.on_before_show_edit_form:
            self.on_before_show_edit_form(self)
        for detail in self.details:
            if self.details_active:
                detail.update_controls(common.UPDATE_OPEN)
            else:
                detail.open()
        self.edit_form.show()
        if self.on_after_show_edit_form:
            self.on_after_show_edit_form(self)




