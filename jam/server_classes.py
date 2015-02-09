# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys, os
if not hasattr(sys, 'db_multiprocessing'):
    sys.db_multiprocessing = False

import Queue
import multiprocessing
#from multiprocessing.managers import BaseManager
import zipfile
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape
import datetime, time
import traceback
import inspect

import common
from items import *
from dataset import *
from sql import *

class ServerField(DBField):
    def __init__(self, owner, field_kind, field_name, caption, data_type, required = False,
            item = None, object_field = None, visible = True, index=0,
            edit_visible = True, edit_index = 0, read_only = False,
            expand = False, word_wrap = False, size = 0, default = False, calculated = False,
            editable = False, master_field = None, value_list=None):
        DBField.__init__(self)
        self.owner = owner
        self.field_kind = field_kind
        self.field_name = field_name
        self.field_caption = caption
        self.field_size = size
        self.is_default = default
        self.data_type = data_type
        self.required = required
        self.lookup_field = None
        self.lookup_item = None
        self.master_field = None
        if item:
            self.lookup_item = item
            self.lookup_field = object_field
        if master_field:
            self.master_field = master_field
            self.lookup_field = object_field
        self.view_visible = visible
        self.view_index = index
        self.edit_visible = edit_visible
        self.edit_index = edit_index
        self.read_only = read_only
        self.expand = expand
        self.word_wrap = word_wrap
        self.calculated = calculated
        self.editable = editable
        self.value_list = value_list

    def copy(self, owner):
        result = ServerField(owner, self.field_kind, self.field_name, self.field_caption, self.data_type)
        result.set_info(self.get_info())
        result.lookup_item = self.lookup_item
        return result

class ServerFilterField(DBField):
    def __init__(self, fltr, field):
        DBField.__init__(self)
        self.owner = field.owner
        self.filter = fltr
        self.lookup_item = None
        info = field.get_info()
        self.set_info(field.get_info())

    def do_before_changed(self, new_value, new_lookup_value):
        pass

    def get_row(self):
        return self.owner._filter_row

    def check_reqired(self, value):
        return True

    def set_modified(self, value):
        pass

    def set_record_status(self, value):
        pass

class ServerFilter(DBFilter):
    def __init__(self, owner, name, caption, field_name, filter_type = common.FILTER_EQ, data_type = None, visible = True):
        DBFilter.__init__(self)
        self.owner = owner
        self.filter_name = name
        self.filter_caption = caption
        self.field_name = None
        self.field_ID = None
        if type(field_name) == int:
            self.field_name = owner._field_by_ID(field_name).field_name
        else:
            self.field_name = field_name
        self.filter_type = filter_type
        self.data_type = data_type;
        self.visible = visible
        self.list = []
        if self.field_name:
            field = self.owner._field_by_name(self.field_name)
            self.field = ServerFilterField(self, field)
            setattr(self, self.field_name, self.field)

    def copy(self, owner):
        result = ServerFilter(owner, self.filter_name, self.filter_caption, self.field_name, self.filter_type, self.visible)
        return result


class ServerDataset(Dataset, SQL):
    def __init__(self, table_name='', view_template='', edit_template='', filter_template='', soft_delete=True):
        Dataset.__init__(self)
        self.ID = None
        self.table_name = table_name
        self.view_template = view_template
        self.edit_template = edit_template
        self.filter_template = filter_template
        self.filter_template = filter_template
        self._order_by = []
        self.on_get_next_id = None
        self.values = None
        self.on_select = None
        self.on_apply = None
        self.on_record_count = None
        self.on_get_field_text = None
        self.id_field_name = None
        self.deleted_field_name = None
        self.soft_delete = soft_delete

    def copy(self, filters=True, details=True, handlers=True):
        result = super(ServerDataset, self).copy(filters, details, handlers)
        result.table_name = self.table_name
        result._order_by = self._order_by
        result.id_field_name = self.id_field_name
        result.deleted_field_name = self.deleted_field_name
        result.soft_delete = self.soft_delete
        return result

    def get_event(self, caption):
        return getattr(caption)

    def add_field(self, field_kind, field_name, caption, data_type, required = False,
        item = None, object_field = None,
        visible = True, index=0, edit_visible = True, edit_index = 0, read_only = False, expand = False,
        word_wrap = False, size = 0, default = False, calculated = False, editable = False, master_field = None, value_list=None):
        field = ServerField(self, field_kind, field_name, caption, data_type, required, item, object_field, visible,
            index, edit_visible, edit_index, read_only, expand, word_wrap, size, default, calculated, editable, master_field, value_list)
        self._fields.append(field)
        return field

    def add_filter(self, name, caption, field_name, filter_type = common.FILTER_EQ, data_type = None, visible = True):
        fltr = ServerFilter(self, name, caption, field_name, filter_type, data_type, visible)
        self.filters.append(fltr)
        fltr.owner = self
        setattr(self.filters, name, fltr)
        return fltr

    def __getattr__(self, name):
        if self.detail_by_name(name):
            obj = self.detail_by_name(name)
            setattr(self, name, obj)
            return obj
        else:
            raise AttributeError(self.item_name + ' attribute: ' + name)

    def do_internal_open(self, params):
        return self.select_records(params)

    def do_apply(self, params=None):
        result = True
        if not self.master and self.log_changes:
            changes = {}
            self.change_log.get_changes(changes)
            if changes['data']:
                data = self.apply_changes((changes, params),
                    {'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True})
                if data:
                    if data['error']:
                        raise Exception, data['error']
                    else:
                        self.change_log.update(data['result'])
        return result

    def get_details(self):
        return self.details

    def get_fields_info(self):
        result = []
        for field in self._fields:
            result.append(field.get_info())
        return result

    def get_filters_info(self):
        result = []
        for fltr in self.filters:
            result.append(fltr.get_info())
        return result

    def get_details_info(self):
        result = []
        for detail in self.details:
            result.append(detail.get_info())
        return result

    #~ def get_reports_info(self):
        #~ result = []
        #~ for report in self.reports:
            #~ result.append(report.ID)
        #~ return result

    def add_detail(self, table):
        detail = ServerDetail(self, table.item_name, table.item_caption, table.table_name)
        self.details.append(detail)
        detail.owner = self
        detail.init_fields()
        return detail

    def detail_by_name(self, caption):
        for table in self.details:
            if table.item_name == caption:
                return table

    def do_on_loaded(self):
        self._filter_row = []
        for i, fltr in enumerate(self.filters):
            self._filter_row.append(None)
            fltr.field.bind_index = i

    def get_view_template(self):
        if self.view_template:
            return self.view_template
        elif self.owner:
            return self.owner.get_view_template()

    def get_view_ui(self):
        return common.ui_to_string(os.path.join(self.task.get_ui_path(), 'ui', self.get_view_template()))

    def get_edit_template(self):
        if self.edit_template:
            return self.edit_template
        elif self.owner:
            return self.owner.get_edit_template()

    def get_edit_ui(self):
        return common.ui_to_string(os.path.join(self.task.get_ui_path(), 'ui', self.get_edit_template()))

    def get_filter_template(self):
        if self.filter_template:
            return self.filter_template
        elif self.owner:
            return self.owner.get_filter_template()

    def get_filter_ui(self):
        if self.owner.filter_template:
            return common.ui_to_string(os.path.join(self.task.get_ui_path(), 'ui', self.get_filter_template()))

    def change_order(self, *fields):
        self._order_by = []
        for field in fields:
            field_name = field
            desc = False
            if field[0] == '-':
                desc = True
                field_name = field[1:]
            try:
                fld = self._field_by_name(field_name)
            except:
                raise RuntimeError('%s: change_order method arument error - %s' % (self.item_name, field))
            self._order_by.append([fld.ID, desc])
        return self

    def get_record_count(self, params, user_info=None, enviroment=None):
        result = 0;
        if self.on_record_count:
            result, error_mes = self.on_record_count(self, params, user_info, enviroment)
        else:
            error_mes = ''
            result = 0
            sql = self.get_record_count_query(params)
            try:
                rows = self.task.execute_select(sql)
                result = rows[0][0]
            except Exception, e:
                error_mes = e.message
        return result, error_mes

    def select_records(self, params, user_info=None, enviroment=None):
        if self.on_select:
            rows, error_mes = self.on_select(self, params, user_info, enviroment)
        else:
            sql = self.get_select_statement(params)
            error_mes = ''
            rows = []
            try:
                rows = self.task.execute_select(sql)
            except Exception, e:
                error_mes = e.message
        return rows, error_mes

    def apply_changes(self, data, privileges, user_info=None, enviroment=None):
        error = None
        try:
            changes, params = data
            if not params:
                params = {}
            delta = self.delta(changes)
            if self.on_apply:
                result, error = self.on_apply(self, delta, params, privileges, user_info, enviroment)
            else:
                sql = delta.apply_sql(privileges)
                result, error = self.task.execute(sql)
        except Exception, e:
            error = e.message
            if not error:
                error = '%s: apply_changes error' % self.item_name
            print traceback.format_exc()
        if error:
            return {'error': error, 'result': None}
        else:
            return {'error': error, 'result': result}


    def field_by_id(self, id_value, field_name):
        return self.get_field_by_id((id_value, field_name))

    def get_field_by_id(self, params):
        id_value, field_name = params
        if isinstance(field_name, tuple) or isinstance(field_name, list):
            field_names = field_name
        else:
            field_names = [field_name]
        field_types = [self._field_by_name(field_name).data_type for field_name in field_names]
        fields_str = ', '.join(['"%s"."%s"' % (self.table_name.upper(), field_name.upper()) for field_name in field_names])
        sql = 'SELECT %s FROM "%s" WHERE ID = %s AND DELETED = 0' % (fields_str, self.table_name.upper(), id_value)
        rec = self.task.execute_select_one(sql)
        if rec:
            rec = list(rec)
            for i, val in enumerate(rec):
                if val is None:
                    if field_types[i] == common.TEXT:
                        rec[i] = ''
                    elif field_types[i] in [common.INTEGER, common.FLOAT, common.CURRENCY]:
                        rec[i] = 0
            if len(field_names) == 1:
                return rec[0]
            else:
                return rec

class ServerAbstractItem(object):
    def __init__(self):
        self.reports = []

    def init_reports(self):
        pass

    def get_reports_info(self):
        result = []
        for report in self.reports:
            result.append(report.ID)
        return result

    def register(self, func):
        setattr(self, func.__name__, func)


class ServerItem(Item, ServerAbstractItem, ServerDataset):
    def __init__(self, owner, name, caption, visible = True,
            table_name='', view_template='', edit_template='', filter_template='', soft_delete=True):
        Item.__init__(self, owner, name, caption, visible)
        ServerAbstractItem.__init__(self)
        ServerDataset.__init__(self, table_name, view_template, edit_template, filter_template, soft_delete)
        self.item_type_id = None

class ServerParam(DBField):
    def __init__(self, caption='', name='', data_type=common.INTEGER, item=None, lookup_field=None, required=True, visible=True, alignment=0):
        DBField.__init__(self)
        self.field_caption = caption
        self.param_caption = caption
        self.field_name = name
        self.param_name = name
        self.lookup_item = item
        self.lookup_field = lookup_field
        self.data_type = data_type
        if self.data_type == common.TEXT:
            self.field_size = 1000
        else:
            self.field_size = 0
        self.required = required
        self.alignment = alignment
        self.edit_visible = visible
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

    def do_before_changed(self, new_value, new_lookup_value):
        pass

    def do_on_change_lookup_field(self, lookup_value=None, slave_field_values=None):
        pass

    def raw_display_text(self):
        result = ''
        if self.lookup_item:
            result = self.lookup_text
        else:
            result = self.text
        return result

    def copy(self, owner):
        result = ServerParam(self.param_caption, self.field_name, self.data_type,
            self.lookup_item, self.lookup_field, self.required,
            self.edit_visible, self.alignment)
        result.set_info(self.get_info())
        result.owner = owner
        return result


class ServerReport(Report, ServerAbstractItem):
    def __init__(self, owner, name='', caption='', visible = True,
            table_name='', view_template='', edit_template='', filter_template=''):
        ServerAbstractItem.__init__(self)
        Report.__init__(self, owner, name, caption, visible)
        self.params = []
        self.template = view_template
        self.band_tags = []
        self.bands = {}
        self.header = None
        self.footer = None
        self.on_before_generate_report = None
        self.on_generate_report = None
        self.on_report_generated = None
        self.on_before_save_report = None

    def copy(self):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible,
            self.table_name, self.template, '', '');
        result.on_before_generate_report = self.on_before_generate_report
        result.on_generate_report = self.on_generate_report
        result.on_report_generated = self.on_report_generated
        result.on_before_save_report = self.on_before_save_report
        for param in self.params:
            new_param = param.copy(result)
            new_param.lookup_item = param.lookup_item
            result.params.append(new_param)
        for param in result.params:
            if param.master_field:
                param.master_field = result.get_master_field(params, param.master_field)
        return  result

    def add_param(self, caption='', name='', data_type=common.INTEGER, obj=None, obj_field=None, required=True, visible=True, value=None):
        self.params.append(ServerParam(caption, name, data_type, obj, obj_field, required, visible, value))

    def get_params_info(self):
        result = []
        for param in self.params:
            result.append(param.get_info())
        return result

    def get_edit_template(self):
        if self.edit_template:
            return self.edit_template
        elif self.owner:
            return self.owner.get_edit_template()

    def get_edit_ui(self):
        return common.ui_to_string(os.path.join(self.task.get_ui_path(), 'ui', self.get_edit_template()))

    def print_report(self, param_values, url, ext=None):
        copy_report = self.copy();
        return copy_report.generate(param_values, url, ext);

    def generate(self, param_values, url, ext):
        self.extension = ext
        self.url = url
        for i, param in enumerate(self.params):
            param.value = param_values[i]
        if self.on_before_generate_report:
            self.on_before_generate_report(self)
        if self.template:
            if not len(self.bands):
                self.parse_template()
            self.content_name = os.path.join(self.task.work_dir, 'reports', 'content%s.xml' % time.time())
            self.content = open(self.content_name, 'wb')
            try:
                file_name = self.item_caption + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.ods'
                file_name = escape(file_name, {':': '-', '/': '_', '\\': '_'})
                self.report_filename = os.path.abspath(os.path.join(self.task.work_dir, 'static', 'reports', file_name))
                static_dir = os.path.dirname(self.report_filename)
                if not os.path.exists(static_dir):
                    os.makedirs(static_dir)
                if self.header:
                    self.content.write(self.header)
                if self.on_generate_report:
                    self.on_generate_report(self)
                if self.footer:
                    self.content.write(self.footer)
                self.save()
            finally:
                if not self.content.closed:
                    self.content.close()
                os.remove(self.content_name)
            if ext and (ext != 'ods'):
                converted = False
                if self.owner.on_convert_report:
                    try:
                        self.owner.on_convert_report(self)
                        converted = True
                    except:
                        pass
                if not converted:
                    # OpenOffice must be running in server mode
                    # soffice --headless --accept="socket,host=127.0.0.1,port=2002;urp;"
                    ext_file_name = self.report_filename.replace('.ods', '.' + ext)
                    try:
                        from third_party.DocumentConverter import DocumentConverter
                        converter = DocumentConverter()
                        converter.convert(self.report_filename, ext_file_name)
                        converted = True
                    except:
                        pass
                if not converted:
                    try:
                        from subprocess import Popen, STDOUT, PIPE
                        convertion = Popen(['soffice', '--headless', '--convert-to', ext,
                            self.report_filename, '--outdir', os.path.join(self.task.work_dir, 'static', 'reports') ],
                            stderr=STDOUT,stdout = PIPE)#, shell=True)
                        out, err = convertion.communicate()
                        converted = True
                    except:
                        pass
                converted_file = self.report_filename.replace('.ods', '.' + ext)
                if converted and os.path.exists(converted_file):
                    self.delete_report(self.report_filename)
                    file_name = file_name.replace('.ods', '.' + ext)
        else:
            if self.on_generate_report:
                self.on_generate_report(self)

        self.report_filename = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
        self.report_url = self.report_filename
        if self.url:
            self.report_url = '%s/static/reports/%s' % (self.url, file_name)
        if self.on_report_generated:
            self.on_report_generated(self)
        return self.report_url

    def delete_report(self, file_name):
        report_name = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
        os.remove(report_name)

    def parse_template(self):
        self.template_name = os.path.join(self.task.work_dir, 'reports', self.template)
        z = zipfile.ZipFile(self.template_name, 'r')
        try:
            data = unicode(z.read('content.xml'), 'utf-8')
        finally:
            z.close()

        self.band_tags = []
        self.bands = {}
        repeated_rows = None
        if data:
            dom = parseString(data)
            try:
                tables = dom.getElementsByTagName('table:table')
                if len(tables) > 0:
                    table = tables[0]
                    for child in table.childNodes:
                        if child.nodeName == 'table:table-row':
                            repeated = child.getAttribute('table:number-rows-repeated')
                            if repeated and repeated.isdigit():
                                repeated_rows = repeated
                            for row_child in child.childNodes:
                                if row_child.nodeName == 'table:table-cell':
                                    text = row_child.getElementsByTagName('text:p')
                                    if text.length > 0:
                                        self.band_tags.append(text[0].childNodes[0].nodeValue)
                                    break

                assert len(self.band_tags) > 0, u'No bands in report template'
                positions = []
                start = 0
                for tag in self.band_tags:
                    text = str('>%s<' % tag)
                    i = data.find(text)
                    i = data.rfind('<table:table-row', start, i)
                    positions.append(i)
                    start = i
                if repeated_rows and int(repeated_rows) > 1000:
                    i = data.find(repeated_rows)
                    i = data.rfind('<table:table-row', start, i)
                    self.band_tags.append('$$$end_of_report')
                    positions.append(i)
                self.header = data[0:positions[0]]
                for i, tag in enumerate(self.band_tags):
                    start = positions[i]
                    try:
                        end = positions[i + 1]
                    except:
                        end = data.find('</table:table>', start)
                    self.bands[tag] = data[start: end].replace(str(tag), '')
                self.footer = data[end:len(data)]
            finally:
                dom.unlink()
                del(dom)

    def print_band(self, band, dic=None, update_band_text=None):
        text = self.bands[band]
        if dic:
            d = dic.copy()
            for key, value in d.items():
                if type(value) in (str, unicode):
                    d[key] = escape(value)
            try:
                cell_start = 0
                cell_start_tag = '<table:table-cell'
                cell_type_tag = 'office:value-type="string"'
                calcext_type_tag = 'calcext:value-type="string"'
                start_tag = '<text:p>'
                end_tag = '</text:p>'
                while True:
                    cell_start = text.find(cell_start_tag, cell_start)
                    if cell_start == -1:
                        break
                    else:
                        start = text.find(start_tag, cell_start)
                        if start != -1:
                            end = text.find(end_tag, start + len(start_tag))
                            if end != -1:
                                text_start = start+len(start_tag)
                                text_end = end
                                cell_text = text[text_start:text_end]
                                cell_text_start = cell_text.find('%(', 0)
                                if cell_text_start != -1:
                                    end = cell_text.find(')s', cell_text_start + 2)
                                    if end != -1:
                                        end += 2
                                        val = cell_text[cell_text_start:end]
                                        key = val[2:-2]
                                        value = d.get(key)
                                        if not value is None:
                                            val = val % d
                                            if type(value) == float:
                                                val = val.replace('.', common.DECIMAL_POINT)
                                        else:
                                            if not key in d.keys():
                                                print 'Report: "%s" band: "%s" key "%s" not found in the dictionary' % (self.item_name, band, key)
                                        cell_text = cell_text[:cell_text_start] + val + cell_text[end:]
                                        text = text[:text_start] + cell_text + text[text_end:]
                                        if type(value) in (int, float):
                                            start_text = text[cell_start:start]
                                            office_value = str(value)
                                            start_text = start_text.replace(cell_type_tag, 'office:value-type="float" office:value="%s"' % office_value)
                                            start_text = start_text.replace(calcext_type_tag, 'calcext:value-type="float"')
                                            text = text[:cell_start] + start_text + text[start:]
                        cell_start += 1
                if update_band_text:
                    text = update_band_text(text)
            except Exception, e:
                print traceback.format_exc()
                print ('Report: "%s" band: "%s" error: "%s"') % (self.item_name, band, e)
        self.content.write(text.encode('utf-8'))

    def save(self):
        self.content.close()
        z = None
        self.zip_file = None
        try:
            self.zip_file = zipfile.ZipFile(self.report_filename, 'w', zipfile.ZIP_DEFLATED)
            z = zipfile.ZipFile(self.template_name, 'r')
            if self.on_before_save_report:
                self.on_before_save_report(self)
            for file_name in z.namelist():
                data = z.read(file_name)
                if file_name == 'content.xml':
                    self.zip_file.write(self.content_name, file_name)
                else:
                    self.zip_file.writestr(file_name, data)
        finally:
            if z:
                z.close()
            if self.zip_file:
                self.zip_file.close()
#            os.remove(self.content_name)

    def cur_to_str(self, value):
        return common.cur_to_str(value)

    def date_to_str(self, value):
        return common.date_to_str(value)

    def datetime_to_str(self, value):
        return common.datetime_to_str(value)



delta_result = None

def execute_sql(db_type, db_database, db_user, db_password,
    db_host, db_port, db_encoding, connection, command,
    params=None, result_set=None, call_proc=False, commit=True):

    def execute_command(cursor, command, params=None):
        try:
            #~ print ''
            #~ print command, params

            result = None
            if params:
                cursor.execute(command, params)
            else:
                cursor.execute(command)
            if result_set == 'ONE':
                result = cursor.fetchone()
            elif result_set == 'ALL':
                result = cursor.fetchall()
            return result
        except Exception, x:
            print '\nError: %s\n command: %s\n params: %s' % (str(x), command, params)
            raise

    def get_next_id(cursor, sql):
        cursor.execute(sql)
        rec = cursor.fetchone()
        return int(rec[0])

    def execute_delta(cursor, command):

        def process_delta(delta, master_rec_id, result):
            ID, sqls = delta
            result['ID'] = ID
            changes = []
            result['changes'] = changes
            for sql in sqls:
                (command, params, info), details = sql
                if info:
                    rec_id = info['id']
                    if rec_id:
                        if info['change_id_sql'] and info['next_id_sql']:
                            next_id = get_next_id(cursor, info['next_id_sql'])
                            if next_id < rec_id:
                                cursor.execute(info['change_id_sql'])
                    else:
                        if info['next_id_sql']:
                            rec_id = get_next_id(cursor, info['next_id_sql'])
                            params[info['id_index']] = rec_id
                    if info['status'] == common.RECORD_INSERTED and info['owner_rec_id_index']:
                        params[info['owner_rec_id_index']] = master_rec_id
                    if command:
                        execute_command(cursor, command, params)
                    if db_type == common.SQLITE and not info['status'] == common.RECORD_DELETED and not rec_id:
                        rec_id = cursor.lastrowid
                    result_details = []
                    if rec_id:
                        changes.append({'log_id': info['log_id'], 'rec_id': rec_id, 'details': result_details})
                    for detail in details:
                        result_detail = {}
                        result_details.append(result_detail)
                        process_delta(detail, rec_id, result_detail)
                else:
                    if command:
                        execute_command(cursor, command, params)

        global delta_result
        delta = command['delta']
        delta_result = {}
        process_delta(delta, None, delta_result)

    def execute_list(cursor, command):
        res = None
        if command:
            for com in command:
                if com:
                    if isinstance(com, unicode) or isinstance(com, str):
                        res = execute_command(cursor, com)
                    elif isinstance(com, list):
                        res = execute_list(cursor, com)
                    elif isinstance(com, dict):
                        res = execute_delta(cursor, com)
                    elif isinstance(com, tuple):
                        res = execute_command(cursor, com[0], com[1])
                    else:
                        raise Exception, 'server_classes execute_list: invalid argument - command: %s' % command
            return res

    def execute(connection):
        global delta_result
        result = None
        error = None
        try:
            cursor = connection.cursor()
            if call_proc:
                try:
                    cursor.callproc(command, params)
                    result = cursor.fetchone()
                except Exception, x:
                    print '\nError: %s in command: %s' % (str(x), command)
                    raise
            else:
                if isinstance(command, str) or isinstance(command, unicode):
                    result = execute_command(cursor, command, params)
                elif isinstance(command, dict):
                    res = execute_delta(cursor, command)
                elif isinstance(command, list):
                    result = execute_list(cursor, command)
                elif isinstance(command, tuple):
                    result = execute_command(cursor, command[0], command[1])
            if commit:
                connection.commit()
            if delta_result:
                result = delta_result
        except Exception, x:
            try:
                if connection:
                    connection.rollback()
                    connection.close()
                error = str(x)
                if not error:
                    error = 'Execute error'
                print traceback.format_exc()
            finally:
                connection = None
        return connection, (result, error)

    global delta_result
    delta_result = None
    if not db_host:
        db_host = 'localhost'
    if db_type == common.POSTGRESQL:
        if connection is None:
            import psycopg2
            connection = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host, port=db_port)
        return execute(connection)
    elif db_type == common.MYSQL:
        if connection is None:
            import MySQLdb
            connection = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_database)
            cursor = connection.cursor()
            cursor.execute("SET SESSION SQL_MODE=ANSI_QUOTES;")
        return execute(connection)
    elif db_type == common.FIREBIRD:
        if connection is None:
            import fdb
            connection = fdb.connect(host=db_host, database=db_database, user=db_user, password=db_password, charset=db_encoding)
        return execute(connection)
    elif db_type == common.SQLITE:
        if connection is None:
            import sqlite3
            connection = sqlite3.connect(db_database)
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
        return execute(connection)

def process_request(name, queue, db_type, db_database, db_user, db_password, db_host, db_port, db_encoding):
    con = None
    while True:
        request = queue.get()
        if request:
#            print name, 'process id:', os.getpid()
            result_queue = request['queue']
            command = request['command']
            params = request['params']
            result_set = request['result_set']
            call_proc = request['call_proc']
            commit = request['commit']
            if command == 'QUIT':
                if con:
                    con.commit()
                    con.close()
                result_queue.put('QUIT')
                break
            else:
                con, result = execute_sql(db_type, db_database, db_user, db_password,
                    db_host, db_port, db_encoding, con, command, params, result_set, call_proc, commit)
                result_queue.put(result)

class AbstractServerTask(Task, ServerAbstractItem):
    def __init__(self, name, caption, template, edit_template, db_type, db_database = '',
            db_user = '', db_password = '', host='', port='', encoding='', con_pool_size=1):
        Task.__init__(self, None, None, None, None)
        self.items = []
        self.ID = None
        self.item_name = name
        self.item_caption = caption
        self.template = template
        self.db_type = db_type
        self.db_database = db_database
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = host
        self.db_port = port
        self.db_encoding = encoding
        self.work_dir = os.getcwd()
        self.con_pool_size = 0
        self.processes = []
        if sys.db_multiprocessing and con_pool_size:
            self.queue = multiprocessing.Queue()
            self.manager = multiprocessing.Manager()
            self.con_pool_size = con_pool_size
            self.create_connection_pool()
        else:
            self.connection = None

    def create_connection_pool(self):
        if self.con_pool_size:
            for i in range(self.con_pool_size):
                p = multiprocessing.Process(target=process_request, args=(self.item_name,
                    self.queue, self.db_type, self.db_database, self.db_user,
                    self.db_password, self.db_host, self.db_port,
                    self.db_encoding))
                self.processes.append(p)
                p.daemon = True
                p.start()

    def release_connection_pool(self):
        if self.con_pool_size:
            for i in range(self.con_pool_size):
                self.execute('QUIT')
            for p in self.processes:
                p.join()
            self.processes = []

    def execute(self, command, params=None, result_set=None, call_proc=False, commit=True):
        if self.con_pool_size:
            result_queue = self.manager.Queue()
            request = {}
            request['queue'] = result_queue
            request['command'] = command
            request['command'] = command
            request['params'] = params
            request['result_set'] = result_set
            request['call_proc'] = call_proc
            request['commit'] = commit
            self.queue.put(request)
            result = result_queue.get()
            return result
        else:
            result = execute_sql(self.db_type, self.db_database, self.db_user,
                self.db_password, self.db_host, self.db_port,
                self.db_encoding, self.connection, command, params, result_set, call_proc, commit)
            self.connection = result[0]
            return result[1]


    def callproc(self, command, params=None):
        result_set, error = self.execute(command, params, call_proc=True)
        if not error:
            return result_set

    def execute_select(self, command, params=None):
        result, error = self.execute(command, params, result_set='ALL', commit=False)
        if error:
            raise Exception, error
        else:
            return result


    def execute_select_one(self, command, params=None):
        result, error = self.execute(command, params, result_set='ONE', commit=False)
        if error:
            raise Exception, error
        else:
            return result

    def get_module_name(self):
        return str(self.item_name + '_' + 'server')

    def compile_item(self, item):
        item.module_name = None
        code = item.server_code
        item.module_name = item.get_module_name()
        item_module = type(sys)(item.module_name)
        item_module.__dict__['this'] = item
        sys.modules[item.module_name] = item_module
        if item.owner:
            sys.modules[item.owner.get_module_name()].__dict__[item.module_name] = item_module
        if code:
            try:
                code = code.encode('utf-8')
            except:
                pass
            try:
                comp_code = compile(code, item.module_name, "exec")
            except Exception, e:
                print e
            exec comp_code in item_module.__dict__
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                setattr(item, func_name, func)
        del code

    def login(self, params):
        return 1

    def __getattr__(self, name):
        if self.item_by_name(name):
            return self.item_by_name(name)
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def add_item(self, item):
        self.items.append(item)
        item.owner = self
        return item

    def find_item(self, g_index, i_index):
        return self.items[g_index].items[i_index]

    def get_ui_file(self, file_name):
        return common.ui_to_string(os.path.join(self.get_ui_path(), 'ui', file_name))

    def get_ui(self):
        if self.template:
            return common.ui_to_string(os.path.join(self.get_ui_path(), 'ui', self.template))

    def copy_database_data(self, db_type, db_database=None, db_user=None, db_password=None,
        db_host=None, db_port=None, db_encoding=None):
        connection = None
        limit = 1024
        for group in self.items:
            for item in group.items:
                if item.item_type != 'report':
                    self.execute('DELETE FROM %s' % item.table_name)
                    item.open(expanded=False, open_empty=True)
                    params = {'__fields': [], '__filters': [], '__expanded': False, '__loaded': 0, '__limit': 0}
                    sql = item.get_record_count_query(params, db_type)
                    connection, (result, error) = \
                    execute_sql(db_type, db_database, db_user, db_password,
                        db_host, db_port, db_encoding, connection, sql, None, 'ALL')
                    record_count = result[0][0]
                    loaded = 0
                    while True:
                        params['__loaded'] = loaded
                        params['__limit'] = limit
                        sql = item.get_select_statement(params, db_type)
                        connection, (result, error) = \
                        execute_sql(db_type, db_database, db_user, db_password,
                            db_host, db_port, db_encoding, connection, sql, None, 'ALL')
                        if not error:
                            for i, r in enumerate(result):
                                item.append()
                                j = 0
                                for field in item.fields:
                                    if not field.master_field:
                                        field.value = r[j]
                                        j += 1
                                item.post()
                            item.apply()
                        else:
                            raise Exception, error
                        loaded = len(result)
                        loaded += loaded
                        print 'coping table %s: %d%%' % (item.item_name, int(loaded * 100 / record_count))
                        if loaded == 0 or loaded < limit:
                            break


class ServerTask(AbstractServerTask):
    def __init__(self, name, caption, template, edit_template,
        db_type, db_database = '', db_user = '', db_password = '',
        host='', port='', encoding='', con_pool_size=4):
        AbstractServerTask.__init__(self, name, caption, template, edit_template,
            db_type, db_database, db_user, db_password,
            host, port, encoding, con_pool_size)
        self.on_created = None
        self.on_login = None
        self.on_get_user_info = None
        self.on_logout = None

    def get_ui_path(self):
        filepath = os.getcwd()
        return filepath.decode('utf-8')

    def find_user(self, login, password_hash=None):
        return self.admin.find_user(login, password_hash);

class AdminServerTask(AbstractServerTask):
    def __init__(self, name, caption, template, edit_template,
        db_type, db_database = '', db_user = '', db_password = '',
        host='', port='', encoding=''):
        AbstractServerTask.__init__(self, name, caption, template, edit_template,
            db_type, db_database, db_user, db_password, host, port, encoding, 1)
        filepath, filename = os.path.split(__file__)
        self.cur_path = filepath

    def get_ui_path(self):
        return self.cur_path.decode('utf-8')


class ServerGroup(Group, ServerAbstractItem):
    def __init__(self, owner, name, caption, view_template = None, edit_template = None, filter_template = None, visible = True, item_type_id=0):
        ServerAbstractItem.__init__(self)
        Group.__init__(self, owner, name, caption, True, item_type_id)
        self.ID = None
        self.view_template = view_template
        self.edit_template = edit_template
        self.filter_template = filter_template
        if item_type_id == common.REPORTS_TYPE:
            self.on_convert_report = None

    def __getattr__(self, name):
        if self.find(name):
            return self.find(name)
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def get_view_template(self):
        return self.view_template

    def get_edit_template(self):
        return self.edit_template

    def get_filter_template(self):
        return self.filter_template

    def add_ref(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.CATALOG_TYPE
        return result

    def add_journal(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.JOURNAL_TYPE
        return result

    def add_table(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.TABLE_TYPE
        return result

    def add_report(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerReport(self, name, caption, visible, table_name, view_template, edit_template, filter_template)
        result.item_type_id = common.REPORT_TYPE
        return result


class ServerDetail(ServerAbstractItem, Detail, ServerDataset):
    def __init__(self, owner, name, caption, table_name):
        ServerAbstractItem.__init__(self)
        Detail.__init__(self, owner, name, caption, True)
        ServerDataset.__init__(self, table_name)
        self.prototype = self.task.item_by_name(self.item_name)
        self.master = owner

    def init_fields(self):
        for field in self.prototype._fields:
            self._fields.append(field.copy(self))

    def get_gen_name(self, db_type):
        return self.prototype.get_gen_name(db_type)

    def do_internal_post(self):
        return {'success': True, 'id': None, 'message': '', 'detail_ids': None}

    def where_clause(self, query, db_type):
        owner_id = query['__owner_id']
        owner_rec_id = query['__owner_rec_id']
        if type(owner_id) == int and type(owner_rec_id) == int:
            result = super(ServerDetail, self).where_clause(query, db_type)
            clause = '"%s"."OWNER_ID"=%s AND "%s"."OWNER_REC_ID"=%s' % \
            (self.table_name.upper(), str(owner_id), self.table_name.upper(), str(owner_rec_id))
            if result:
                result += ' AND ' + clause
            else:
                result = ' WHERE ' + clause
            return self.set_case(db_type, result)
        else:
            raise Exception, 'Invalid request parameter'

    def get_filters(self):
        return self.prototype.filters

    #~ def get_reports_info(self):
        #~ return []
