import sys, os
try:
    import Queue as Queue
except ImportError:
    import queue as Queue
import multiprocessing
import threading
import zipfile
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape
import datetime, time
import traceback
import inspect
import json

import jam.common as common
import jam.db.db_modules as db_modules
from jam.items import *
from jam.dataset import *
from jam.sql import *
from jam.execute import process_request, execute_sql
from jam.third_party.six import exec_, print_
from werkzeug._compat import iteritems, iterkeys, text_type, string_types, to_bytes, to_unicode

class ServerDataset(Dataset, SQL):
    def __init__(self, table_name='', soft_delete=True):
        Dataset.__init__(self)
        self.ID = None
        self.table_name = table_name
        self.gen_name = None
        self._order_by = []
        self.values = None
        self.on_open = None
        self.on_apply = None
        self.on_count = None
        self.on_field_get_text = None
        self.soft_delete = soft_delete
        self.virtual_table = False

    def copy(self, filters=True, details=True, handlers=True):
        if self.master:
            raise DatasetException(u'A detail item can not be copied: %s' % self.item_name)
        result = self._copy(filters, details, handlers)
        return result

    def free(self):
        try:
            for d in self.details:
                d.__dict__ = {}
            for f in self.filters:
                f.field = None
                f.__dict__ = {}
            self.filters.__dict__ = {}
            self.__dict__ = {}
        except:
            pass

    def _copy(self, filters=True, details=True, handlers=True):
        result = super(ServerDataset, self)._copy(filters, details, handlers)
        result.table_name = self.table_name
        result.gen_name = self.gen_name
        result._order_by = self._order_by
        result.soft_delete = self.soft_delete
        result._primary_key = self._primary_key
        result._deleted_flag = self._deleted_flag
        result._master_id = self._master_id
        result._master_rec_id = self._master_rec_id
        result._primary_key_db_field_name = self._primary_key_db_field_name
        result._deleted_flag_db_field_name = self._deleted_flag_db_field_name
        result._master_id_db_field_name = self._master_id_db_field_name
        result._master_rec_id_db_field_name = self._master_rec_id_db_field_name
        return result

    def get_event(self, caption):
        return getattr(caption)

    def add_field(self, field_id, field_name, field_caption, data_type, required=False,
        item=None, object_field=None, visible=True, index=0, edit_visible=True, edit_index=0, read_only=False,
        expand=False, word_wrap=False, size=0, default_value=None, default=False, calculated=False, editable=False,
        master_field=None, alignment=None, lookup_values=None, enable_typeahead=False, field_help=None,
        field_placeholder=None, lookup_field1=None, lookup_field2=None, db_field_name=None, field_mask=None,
        image_edit_width=None, image_edit_height=None, image_view_width=None, image_view_height=None,
        image_placeholder=None, file_download_btn=None, file_open_btn=None, file_accept=None):

        if db_field_name == None:
            db_field_name = field_name.upper()

        field_def = self.add_field_def(field_id, field_name, field_caption, data_type, required, item, object_field,
            lookup_field1, lookup_field2, visible, index, edit_visible, edit_index, read_only, expand, word_wrap, size,
            default_value, default, calculated, editable, master_field, alignment, lookup_values, enable_typeahead,
            field_help, field_placeholder, field_mask, image_edit_width, image_edit_height, image_view_width, image_view_height,
            image_placeholder, file_download_btn, file_open_btn, file_accept, db_field_name)
        field = DBField(self, field_def)
        self._fields.append(field)
        return field

    def add_filter(self, name, caption, field_name, filter_type=common.FILTER_EQ,
        multi_select_all=None, data_type=None, visible=True, filter_help=None,
        filter_placeholder=None, filter_id = None):

        filter_def = self.add_filter_def(name, caption, field_name, filter_type,
            multi_select_all, data_type, visible, filter_help, filter_placeholder, filter_id)
        fltr = DBFilter(self, filter_def)
        self.filters.append(fltr)
        return fltr

    def do_internal_open(self, params):
        return self.select_records(params)

    def do_apply(self, params=None, safe=False):
        if not self.master and self.log_changes:
            changes = {}
            self.change_log.get_changes(changes)
            if changes['data']:
                data, error = self.apply_changes((changes, params), safe)
                if error:
                    raise Exception(error)
                else:
                    self.change_log.update(data)

    def add_detail(self, table):
        detail = Detail(self.task, self, table.item_name, table.item_caption, table.table_name)
        self.details.append(detail)
        detail.owner = self
        detail.init_fields()
        return detail

    def detail_by_name(self, caption):
        for table in self.details:
            if table.item_name == caption:
                return table

    def get_record_count(self, params, safe=False): #depricated
        if safe and not self.can_view():
            raise Exception(self.task.language('cant_view') % self.item_caption)
        result = None
        if self.task.on_count:
            result = self.task.on_count(self, params)
        if result is None and self.on_count:
            result = self.on_count(self, params)
        if result is None:
            error_mess = ''
            count = 0
            for sql in self.get_record_count_queries(params):
                rows = self.task.select(sql)
                count += rows[0][0]
            result = count, error_mess
        return result

    def execute_select(self, params):
        error_mes = ''
        limit = params['__limit']
        offset = params['__offset']
        sqls = self.get_select_queries(params)
        if len(sqls) == 1:
            rows = self.task.select(sqls[0])
        else:
            rows = []
            cut = False
            for sql in sqls:
                rows += self.task.select(sql)
                if limit or offset:
                    if len(rows) >= offset + limit:
                        rows = rows[offset:offset + limit]
                        cut = True
                        break
            if (limit or offset) and not cut:
                rows = rows[offset:offset + limit]
        result = rows, error_mes
        return result

    def select_records(self, params, safe=False):
        if safe and not self.can_view():
            raise Exception(self.task.language('cant_view') % self.item_caption)
        result = None
        if self.task.on_open:
            result = self.task.on_open(self, params)
        if result is None and self.on_open:
            result = self.on_open(self, params)
        if result is None:
            result = self.execute_select(params)
        return result

    def apply_delta(self, delta, safe=False):
        sql = delta.apply_sql(safe)
        return self.task.execute(sql)

    def apply_changes(self, data, safe):
        result = None
        changes, params = data
        if not params:
            params = {}
        delta = self.delta(changes)
        if self.task.on_apply:
            result = self.task.on_apply(self, delta, params)
        if result is None and self.on_apply:
            result = self.on_apply(self, delta, params)
        if result is None:
            result = self.apply_delta(delta, safe)
        return result

    def update_deleted(self):
        if self._is_delta and len(self.details):
            rec_no = self.rec_no
            try:
                for it in self:
                    if it.rec_deleted():
                        for detail in self.details:
                            fields = []
                            for field in detail.fields:
                                fields.append(field.field_name)
                            det = self.task.item_by_name(detail.item_name).copy()
                            where = {
                                det._master_id: self.ID,
                                det._master_rec_id: self._primary_key_field.value
                            }
                            det.open(fields=fields, expanded=detail.expanded, where=where)
                            if det.record_count():
                                it.edit()
                                for d in det:
                                    detail.append()
                                    for field in detail.fields:
                                        f = det.field_by_name(field.field_name)
                                        field.set_value(f.value, f.lookup_value)
                                    detail.post()
                                it.post()
                                for d in detail:
                                    d.record_status = common.RECORD_DELETED
            finally:
                self.rec_no = rec_no

    def field_by_id(self, id_value, field_name):
        return self.get_field_by_id((id_value, field_name))

    def get_field_by_id(self, params):
        id_value, fields = params
        if not (isinstance(fields, tuple) or isinstance(fields, list)):
            fields = [fields]
        copy = self.copy()
        copy.set_where(id=id_value)
        copy.open(fields=fields)
        if copy.record_count() == 1:
            result = []
            for field_name in fields:
                result.append(copy.field_by_name(field_name).value)
            if len(fields) == 1:
                return result[0]
            else:
                return result
        return

class Item(AbstrItem, ServerDataset):
    def __init__(self, task, owner, name, caption, visible = True,
            table_name='', view_template='', js_filename='', soft_delete=True):
        AbstrItem.__init__(self, task, owner, name, caption, visible, js_filename=js_filename)
        ServerDataset.__init__(self, table_name, soft_delete)
        self.item_type_id = None
        self.reports = []

    def get_reports_info(self):
        result = []
        for report in self.reports:
            result.append(report.ID)
        return result


class Param(DBField):
    def __init__(self, owner, param_def):
        DBField.__init__(self, owner, param_def)
        self.field_kind = common.PARAM_FIELD
        if self.data_type == common.TEXT:
            self.field_size = 1000
        else:
            self.field_size = 0
        self.param_name = self.field_name
        self.param_caption = self.field_caption
        self._value = None
        self._lookup_value = None
        setattr(owner, self.param_name, self)

    def system_field(self):
        return False

    def get_data(self):
        return self._value

    def set_data(self, value):
        self._value = value

    def get_lookup_data(self):
        return self._lookup_value

    def set_lookup_data(self, value):
        self._lookup_value = value

    def _do_before_changed(self):
        pass

    def _change_lookup_field(self, lookup_value=None, slave_field_values=None):
        pass

    def copy(self, owner):
        result = Param(owner, self.param_caption, self.field_name, self.data_type,
            self.lookup_item, self.lookup_field, self.required,
            self.edit_visible, self.alignment)
        return result


class Report(AbstrReport):
    def __init__(self, task, owner, name='', caption='', visible = True,
            table_name='', view_template='', js_filename=''):
        AbstrReport.__init__(self, task, owner, name, caption, visible, js_filename=js_filename)
        self.param_defs = []
        self.params = []
        self.template = view_template
        self.template_name = None
        self.template_content = {}
        self.ext = 'ods'

        self.on_before_generate = None
        self.on_generate = None
        self.on_after_generate = None
        self.on_parsed = None
        self.on_before_save_report = None

        self.on_before_append = None
        self.on_after_append = None
        self.on_before_edit = None
        self.on_after_edit = None
        self.on_before_open = None
        self.on_after_open = None
        self.on_before_post = None
        self.on_after_post = None
        self.on_before_delete = None
        self.on_after_delete = None
        self.on_before_cancel = None
        self.on_after_cancel = None
        self.on_before_apply = None
        self.on_after_apply = None
        self.on_before_scroll = None
        self.on_after_scroll = None
        self.on_filter_record = None
        self.on_field_changed = None
        self.on_filters_applied = None
        self.on_before_field_changed = None
        self.on_filter_value_changed = None
        self.on_field_validate = None
        self.on_field_get_text = None


    def add_param(self, caption='', name='', data_type=common.INTEGER,
            obj=None, obj_field=None, required=True, visible=True, alignment=None,
            multi_select=None, multi_select_all=None, enable_typeahead=None, lookup_values=None,
            param_help=None, param_placeholder=None):
        param_def = self.add_param_def(caption, name, data_type, obj,
            obj_field, required, visible, alignment, multi_select, multi_select_all,
            enable_typeahead, lookup_values, param_help, param_placeholder)
        param = Param(self, param_def)
        self.params.append(param)

    def add_param_def(self, param_caption='', param_name='', data_type=common.INTEGER,
            lookup_item=None, lookup_field=None, required=True, visible=True,
            alignment=0, multi_select=False, multi_select_all=False, enable_typeahead=False,
            lookup_values=None, param_help=None,
        param_placeholder=None):
        param_def = [None for i in range(len(FIELD_DEF))]
        param_def[FIELD_NAME] = param_name
        param_def[NAME] = param_caption
        param_def[FIELD_DATA_TYPE] = data_type
        param_def[REQUIRED] = required
        param_def[LOOKUP_ITEM] = lookup_item
        param_def[LOOKUP_FIELD] = lookup_field
        param_def[FIELD_EDIT_VISIBLE] = visible
        param_def[FIELD_ALIGNMENT] = alignment
        param_def[FIELD_MULTI_SELECT] = multi_select
        param_def[FIELD_MULTI_SELECT_ALL] = multi_select_all
        param_def[FIELD_ENABLE_TYPEAHEAD] = enable_typeahead
        param_def[FIELD_LOOKUP_VALUES] = lookup_values
        param_def[FIELD_HELP] = param_help
        param_def[FIELD_PLACEHOLDER] = param_placeholder
        self.param_defs.append(param_def)
        return param_def

    def prepare_params(self):
        for param in self.params:
            if param.lookup_item and type(param.lookup_item) == int:
                param.lookup_item = self.task.item_by_ID(param.lookup_item)
            if param.lookup_field and type(param.lookup_field) == int:
                param.lookup_field = param.lookup_item._field_by_ID(param.lookup_field).field_name
            if param.lookup_values and type(param.lookup_values) == int:
                try:
                    param.lookup_values = self.task.lookup_lists[param.lookup_values]
                except:
                    pass


    def copy(self):
        result = self.__class__(self.task, None, self.item_name, self.item_caption, self.visible,
            '', self.template, '');
        result.on_before_generate = self.on_before_generate
        result.on_generate = self.on_generate
        result.on_after_generate = self.on_after_generate
        result.on_before_save_report = self.on_before_save_report
        result.on_parsed = self.on_parsed
        result.on_convert_report = self.owner.on_convert_report
        result.param_defs = self.param_defs
        result.template_content = self.template_content.copy()
        result.template_name = self.template_name
        for param_def in result.param_defs:
            param = Param(result, param_def)
            result.params.append(param)
        result.prepare_params()
        return  result

    def free(self):
        for p in self.params:
            p.field = None
        self.__dict__ = {}

    def print_report(self, param_values, url, ext=None, safe=False):
        if safe and not self.can_view():
            raise Exception(self.task.language('cant_view') % self.item_caption)
        copy = self.copy()
        copy.ext = ext
        result = copy.generate(param_values, url, ext)
        copy.free()
        return result

    def generate_file_name(self, ext=None):
        if not ext:
            ext = 'ods'
        file_name = self.item_name + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.' + ext
        file_name = escape(file_name, {':': '-', '/': '_', '\\': '_'})
        return os.path.abspath(os.path.join(self.task.work_dir, 'static', 'reports', file_name))

    def generate(self, param_values, url, ext):
        self.extension = ext
        self.url = url
        template = self.template
        for i, param in enumerate(self.params):
            param.set_data(param_values[i]);
        if self.on_before_generate:
            self.on_before_generate(self)
        if template != self.template:
            self.template_content = None
        if self.template:
            if not self.template_content:
                self.parse_template()
            if self.on_parsed:
                self.on_parsed(self)
            self.content_name = os.path.join(self.task.work_dir, 'reports', 'content%s.xml' % time.time())
            self.content = open(self.content_name, 'wb')
            try:
                self.report_filename = self.generate_file_name()
                file_name = os.path.basename(self.report_filename)
                static_dir = os.path.dirname(self.report_filename)
                if not os.path.exists(static_dir):
                    os.makedirs(static_dir)
                self.content.write(self.template_content['header'])
                self.content.write(self.template_content['columns'])
                self.content.write(self.template_content['rows'])
                if self.on_generate:
                    self.on_generate(self)
                self.content.write(self.template_content['footer'])
                self.save()
            finally:
                try:
                    if not self.content.closed:
                        self.content.close()
                    if os.path.exists(self.content_name):
                        os.remove(self.content_name)
                except:
                    pass
            if ext and (ext != 'ods'):
                converted = False
                if self.on_convert_report:
                    try:
                        self.on_convert_report(self)
                        converted = True
                    except:
                        pass
                if not converted:
                    converted = self.task.convert_report(self, ext)
                converted_file = self.report_filename.replace('.ods', '.' + ext)
                if converted and os.path.exists(converted_file):
                    self.delete_report(self.report_filename)
                    file_name = file_name.replace('.ods', '.' + ext)
            self.report_filename = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
            self.report_url = self.report_filename
            if self.url:
                self.report_url = os.path.join(self.url, 'static', 'reports', file_name)
        else:
            if self.on_generate:
                self.on_generate(self)
        if self.on_after_generate:
            self.on_after_generate(self)
        return self.report_url

    def delete_report(self, file_name):
        report_name = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
        os.remove(report_name)

    def find(self, text, search, beg=None, end=None):
        return to_bytes(text, 'utf-8').find(to_bytes(search, 'utf-8'), beg, end)

    def rfind(self, text, search, beg=None, end=None):
        return to_bytes(text, 'utf-8').rfind(to_bytes(search, 'utf-8'), beg, end)

    def replace(self, text, find, replace):
        return to_bytes(text, 'utf-8').replace(to_bytes(find, 'utf-8'), to_bytes(replace, 'utf-8'))

    def parse_template(self):
        if not os.path.isabs(self.template):
            self.template_name = os.path.join(self.task.work_dir, 'reports', self.template)
        else:
            self.template_name = self.template
        z = zipfile.ZipFile(self.template_name, 'r')
        try:
            data = z.read('content.xml')
        finally:
            z.close()
        band_tags = []
        bands = {}
        colum_defs = []
        header = ''
        columns = ''
        rows = ''
        footer = ''
        repeated_rows = None
        if data:
            dom = parseString(data)
            try:
                tables = dom.getElementsByTagName('table:table')
                if len(tables) > 0:
                    table = tables[0]
                    for child in table.childNodes:
                        if child.nodeName == 'table:table-column':
                            repeated = child.getAttribute('table:number-columns-repeated')
                            if not repeated:
                                repeated = 1
                            colum_defs.append(['', repeated])
                        if child.nodeName == 'table:table-row':
                            repeated = child.getAttribute('table:number-rows-repeated')
                            if repeated and repeated.isdigit():
                                repeated_rows = to_bytes(repeated, 'utf-8')
                            for row_child in child.childNodes:
                                if row_child.nodeName == 'table:table-cell':
                                    text = row_child.getElementsByTagName('text:p')
                                    if text.length > 0:
                                        band_tags.append(text[0].childNodes[0].nodeValue)
                                    break
                start = 0
                columns_start = 0
                for col in colum_defs:
                    start = self.find(data, '<table:table-column', start)
                    if columns_start == 0:
                        columns_start = start
                    end = self.find(data, '/>', start)
                    col_text = data[start: end + 2]
                    columns = to_bytes('%s%s' % (columns, col_text), 'utf-8')
                    col[0] = data[start: end + 2]
                    start = end + 2
                columns_end = start
                header = data[0:columns_start]
                assert len(band_tags) > 0, 'No bands in the report template'
                positions = []
                start = 0
                for tag in band_tags:
                    text = '>%s<' % tag
                    i = self.find(data, text)
                    i = self.rfind(data, '<table:table-row', start, i)
                    positions.append(i)
                    start = i
                if repeated_rows and int(repeated_rows) > 1000:
                    i = self.find(data, repeated_rows)
                    i = self.rfind(data, '<table:table-row', start, i)
                    band_tags.append('$$$end_of_report')
                    positions.append(i)
                rows = data[columns_end:positions[0]]
                for i, tag in enumerate(band_tags):
                    start = positions[i]
                    try:
                        end = positions[i + 1]
                    except:
                        end = self.find(data, '</table:table>', start)
                    bands[tag] = self.replace(data[start: end], str(tag), '')
                footer = data[end:len(data)]
                self.template_content = {}
                self.template_content['bands'] = bands
                self.template_content['colum_defs'] = colum_defs
                self.template_content['header'] = header
                self.template_content['columns'] = columns
                self.template_content['rows'] = rows
                self.template_content['footer'] = footer
            finally:
                dom.unlink()
                del(dom)

    def hide_columns(self, col_list):

        def convert_str_to_int(string):
            s = string.upper()
            base = ord('A')
            mult = ord('Z') - base + 1
            result = s
            if type(s) == str:
                result = 0
                chars = []
                for i in range(len(s)):
                    chars.append(s[i])
                for i in range(len(chars) - 1, -1, -1):
                    result += (ord(chars[i]) - base + 1) * (mult ** (len(chars) - i - 1))
            return result

        def remove_repeated(col, repeated):
            result = col
            p = self.find(col, 'table:number-columns-repeated')
            if p != -1:
                r = self.find(col, str(repeated), p)
                if r != -1:
                    for i in range(r, 100):
                        if col[i] in ("'", '"'):
                            result = self.replace(col, col[p:i+1], '')
                            break
            return result

        if self.template_content:
            ints = []
            for i in col_list:
                ints.append(convert_str_to_int(i))
            colum_defs = self.template_content['colum_defs']
            columns = ''
            index = 1
            for col, repeated in colum_defs:
                repeated = int(repeated)
                if repeated > 1:
                    col = remove_repeated(col, repeated)
                for i in range(repeated):
                    cur_col = col
                    if index in ints:
                        cur_col = cur_col[0:-2] + ' table:visibility="collapse"/>'
                    columns += cur_col
                    index += 1
            self.template_content['colum_defs'] = colum_defs
            self.template_content['columns'] = columns

    def print_band(self, band, dic=None, update_band_text=None):
        text = self.template_content['bands'][band]
        if dic:
            d = dic.copy()
            for key, value in iteritems(d):
                if type(value) in string_types:
                    d[key] = escape(value)
            cell_start = 0
            cell_start_tag = to_bytes('<table:table-cell', 'utf-8')
            cell_type_tag = to_bytes('office:value-type="string"', 'utf-8')
            calcext_type_tag = to_bytes('calcext:value-type="string"', 'utf-8')
            start_tag = to_bytes('<text:p>', 'utf-8')
            end_tag = to_bytes('</text:p>', 'utf-8')
            while True:
                cell_start = self.find(text, cell_start_tag, cell_start)
                if cell_start == -1:
                    break
                else:
                    start = self.find(text, start_tag, cell_start)
                    if start != -1:
                        end = self.find(text, end_tag, start + len(start_tag))
                        if end != -1:
                            text_start = start + len(start_tag)
                            text_end = end
                            cell_text = text[text_start:text_end]
                            cell_text_start = self.find(cell_text, to_bytes('%(', 'utf-8'), 0)
                            if cell_text_start != -1:
                                end = self.find(cell_text, to_bytes(')s', 'utf-8'), cell_text_start + 2)
                                if end != -1:
                                    end += 2
                                    val = cell_text[cell_text_start:end]
                                    key = val[2:-2]
                                    value = d.get(to_unicode(key, 'utf-8'))
                                    if isinstance(value, DBField):
                                        raise Exception('Report: "%s" band: "%s" key "%s" a field object is passed. Specify the value attribute.' % \
                                            (self.item_name, band, key))
                                    elif not value is None:
                                        val = to_unicode(val, 'utf-8')
                                        val = val % d
                                        val = to_bytes(val, 'utf-8')
                                        if type(value) == float:
                                            val = self.replace(val, '.', common.DECIMAL_POINT)
                                    else:
                                        if not key in iterkeys(d):
                                            print('Report: "%s" band: "%s" key "%s" not found in the dictionary' % \
                                                (self.item_name, band, key))
                                    cell_text = to_bytes('%s%s%s', 'utf-8') % (cell_text[:cell_text_start], val, cell_text[end:])
                                    text = to_bytes('', 'utf-8').join([text[:text_start], cell_text, text[text_end:]])
                                    if type(value) in (int, float):
                                        start_text = text[cell_start:start]
                                        office_value = value
                                        start_text = self.replace(start_text, cell_type_tag, 'office:value-type="float" office:value="%s"' % office_value)
                                        start_text = self.replace(start_text, calcext_type_tag, 'calcext:value-type="float"')
                                        text = to_bytes('', 'utf-8').join([text[:cell_start], start_text, text[start:]])
                    cell_start += 1
            if update_band_text:
                text = update_band_text(text)
        self.content.write(text)

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

    def cur_to_str(self, value):
        return common.cur_to_str(value)

    def date_to_str(self, value):
        return common.date_to_str(value)

    def datetime_to_str(self, value):
        return common.datetime_to_str(value)

    def _set_modified(self, value):
        pass


class Consts(object):
    def __init__(self):
        self.TEXT = common.TEXT
        self.INTEGER = common.INTEGER
        self.FLOAT = common.FLOAT
        self.CURRENCY = common.CURRENCY
        self.DATE = common.DATE
        self.DATETIME = common.DATETIME
        self.BOOLEAN = common.BOOLEAN
        self.LONGTEXT = common.LONGTEXT

        self.ITEM_FIELD = common.ITEM_FIELD
        self.FILTER_FIELD = common.FILTER_FIELD
        self.PARAM_FIELD = common.PARAM_FIELD

        self.FILTER_EQ = common.FILTER_EQ
        self.FILTER_NE = common.FILTER_NE
        self.FILTER_LT = common.FILTER_LT
        self.FILTER_LE = common.FILTER_LE
        self.FILTER_GT = common.FILTER_GT
        self.FILTER_GE = common.FILTER_GE
        self.FILTER_IN = common.FILTER_IN
        self.FILTER_NOT_IN = common.FILTER_NOT_IN
        self.FILTER_RANGE = common.FILTER_RANGE
        self.FILTER_ISNULL = common.FILTER_ISNULL
        self.FILTER_EXACT = common.FILTER_EXACT
        self.FILTER_CONTAINS = common.FILTER_CONTAINS
        self.FILTER_STARTWITH = common.FILTER_STARTWITH
        self.FILTER_ENDWITH = common.FILTER_ENDWITH
        self.FILTER_CONTAINS_ALL = common.FILTER_CONTAINS_ALL

        self.ALIGN_LEFT = common.ALIGN_LEFT
        self.ALIGN_CENTER = common.ALIGN_CENTER
        self.ALIGN_RIGHT = common.ALIGN_RIGHT

        self.STATE_INACTIVE = common.STATE_INACTIVE
        self.STATE_BROWSE = common.STATE_BROWSE
        self.STATE_INSERT = common.STATE_INSERT
        self.STATE_EDIT = common.STATE_EDIT
        self.STATE_DELETE = common.STATE_DELETE

        self.RECORD_UNCHANGED = common.RECORD_UNCHANGED
        self.RECORD_INSERTED = common.RECORD_INSERTED
        self.RECORD_MODIFIED = common.RECORD_MODIFIED
        self.RECORD_DETAILS_MODIFIED = common.RECORD_DETAILS_MODIFIED
        self.RECORD_DELETED = common.RECORD_DELETED

class ConCounter(object):
    def __init__(self):
        self.val = 0


class AbstractServerTask(AbstrTask):
    def __init__(self, app, name, caption, js_filename, db_type, db_server = '',
        db_database = '', db_user = '', db_password = '', host='', port='',
        encoding='', con_pool_size=1, mp_pool=False, persist_con=False):
        AbstrTask.__init__(self, None, None, None, None)
        self.app = app
        self.consts = Consts()
        self.items = []
        self.lookup_lists = {}
        self.ID = None
        self.item_name = name
        self.item_caption = caption
        self.js_filename = js_filename
        self.db_type = db_type
        self.db_server = db_server
        self.db_database = db_database
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = host
        self.db_port = port
        self.db_encoding = encoding
        self.db_module = db_modules.get_db_module(self.db_type)
        self.on_before_request = None
        self.on_after_request = None
        self.on_open = None
        self.on_apply = None
        self.on_count = None
        self.work_dir = os.getcwd()
        self.con_pool_size = 0
        self.mod_count = 0
        self.modules = []
        self.conversion_lock = threading.Lock()
        self.con_pool_size = con_pool_size
        self.mp_pool = mp_pool
        self.persist_con = persist_con
        self.con_counter = ConCounter()
        #~ self.persist_con_busy = 0
        if self.mp_pool:
            if self.persist_con:
                self.create_connection_pool(1)
            self.create_mp_connection_pool(self.con_pool_size)
        else:
            self.create_connection_pool(self.con_pool_size)

    def get_version(self):
        return common.SETTINGS['VERSION']

    version = property (get_version)

    def create_connection_pool(self, con_count):
        self.queue = Queue.Queue()
        pid = None
        for i in range(con_count):
            p = threading.Thread(target=process_request, args=(pid, self.item_name,
                self.queue, self.db_type, self.db_server, self.db_database, self.db_user,
                self.db_password, self.db_host, self.db_port,
                self.db_encoding, self.mod_count))
            p.daemon = True
            p.start()

    def create_mp_connection_pool(self, con_count):
        self.mp_queue = multiprocessing.Queue()
        self.mp_manager = multiprocessing.Manager()
        pid = os.getpid()
        for i in range(con_count):
            p = multiprocessing.Process(target=process_request, args=(pid, self.item_name,
                self.mp_queue, self.db_type, self.db_server, self.db_database, self.db_user,
                self.db_password, self.db_host, self.db_port,
                self.db_encoding, self.mod_count))
            p.daemon = True
            p.start()

    def create_connection(self):
        return self.db_module.connect(self.db_database, self.db_user, \
            self.db_password, self.db_host, self.db_port, self.db_encoding, self.db_server)

    def send_to_pool(self, queue, result_queue, command, params=None, call_proc=False, select=False):
        request = {}
        request['queue'] = result_queue
        request['command'] = command
        request['params'] = params
        request['call_proc'] = call_proc
        request['select'] = select
        request['mod_count'] = self.mod_count
        queue.put(request)
        return  result_queue.get()

    def execute_in_pool(self, command, params=None, call_proc=False, select=False):
        result_queue = Queue.Queue()
        result = self.send_to_pool(self.queue, result_queue, command, params, call_proc, select)
        return result

    def execute_in_mp_poll(self, command, params=None, call_proc=False, select=False):
        result_queue = self.mp_manager.Queue()
        result = self.send_to_pool(self.mp_queue, result_queue, command, params, call_proc, select)
        return result

    def execute(self, command, params=None, call_proc=False, select=False):
        if self.mp_pool:
            if self.persist_con and not self.con_counter.val:
                self.con_counter.val += 1
                try:
                    result = self.execute_in_pool(command, params, call_proc, select)
                finally:
                    self.con_counter.val -= 1
            else:
                result = self.execute_in_mp_poll(command, params, call_proc, select)
        else:
            result = self.execute_in_pool(command, params, call_proc, select)
        return result

    def callproc(self, command, params=None):
        result_set, error = self.execute(command, params, call_proc=True)
        if not error:
            return result_set

    def select(self, command, params=None):
        result, error = self.execute(command, params, select=True)
        if error:
            raise Exception(error)
        else:
            return result

    def execute_select(self, command, params=None): #depricated
        return self.select(command, params=None)

    def get_module_name(self):
        return str(self.item_name)

    def compile_item(self, item):
        item.module_name = None
        code = item.server_code
        item.module_name = item.get_module_name()
        item_module = type(sys)(item.module_name)
        item_module.__dict__['this'] = item
        sys.modules[item.module_name] = item_module

        item.task.modules.append(item.module_name)
        if item.owner:
            sys.modules[item.owner.get_module_name()].__dict__[item.module_name] = item_module
        if code:
            try:
                code = to_bytes(code, 'utf-8')
            except Exception as e:
                print(e)
            comp_code = compile(code, item.module_name, "exec")
            exec_(comp_code, item_module.__dict__)

            item_module.__dict__['__loader__'] = item._loader
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                setattr(item, func_name, func)
        del code

    def add_item(self, item):
        self.items.append(item)
        item.owner = self
        return item

    def find_item(self, g_index, i_index):
        return self.items[g_index].items[i_index]

    def convert_report(self, report, ext):
        converted = False
        with self.conversion_lock:
            try:
                from subprocess import Popen, STDOUT, PIPE
                if os.name == "nt":
                    import _winreg
                    regpath = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\soffice.exe"
                    root = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, regpath)
                    s_office = _winreg.QueryValue(root, "")
                else:
                    s_office = "soffice"
                convertion = Popen([s_office, '--headless', '--convert-to', ext,
#                convertion = Popen([s_office, '--headless', '--convert-to', '--norestore', ext,
                    report.report_filename, '--outdir', os.path.join(self.work_dir, 'static', 'reports') ],
                    stderr=STDOUT,stdout=PIPE)#, shell=True)
                out, err = convertion.communicate()
                converted = True
            except Exception as e:
                print(e)
        return converted

class DebugException(Exception):
    pass

class Task(AbstractServerTask):
    def __init__(self, app, name, caption, js_filename,
        db_type, db_server = '', db_database = '', db_user = '', db_password = '',
        host='', port='', encoding='', con_pool_size=4, mp_pool=True,
        persist_con=True):
        AbstractServerTask.__init__(self, app, name, caption, js_filename,
            db_type, db_server, db_database, db_user, db_password,
            host, port, encoding, con_pool_size, mp_pool, persist_con)
        self.on_created = None
        self.on_login = None
        self.on_ext_request = None
        self.compress_history = True
        self.init_dict = {}
        for key, value in iteritems(self.__dict__):
            self.init_dict[key] = value

    def get_safe_mode(self):
        return self.app.admin.safe_mode

    safe_mode = property (get_safe_mode)

    def drop_indexes(self):
        from jam.adm_server import drop_indexes_sql
        sqls = drop_indexes_sql(self.app.admin)
        for s in sqls:
            try:
                self.execute(s)
            except:
                pass

    def restore_indexes(self):
        from jam.adm_server import restore_indexes_sql
        sqls = restore_indexes_sql(self.app.admin)
        for s in sqls:
            try:
                self.execute(s)
            except:
                pass

    def copy_database(self, dbtype, database=None, user=None, password=None,
        host=None, port=None, encoding=None, server=None, limit = 4096):

        def convert_sql(item, sql, db_module):
            new_case = item.task.db_module.identifier_case
            old_case = db_module.identifier_case
            if old_case('a') != new_case('a'):
                if new_case(item.table_name) == item.table_name:
                    sql = sql.replace(item.table_name, old_case(item.table_name))
                for field in item.fields:
                    if new_case(field.db_field_name) == field.db_field_name and \
                        not field.db_field_name.upper() in common.SQL_KEYWORDS:
                        field_name = '"%s"' % field.db_field_name
                        sql = sql.replace(field_name, old_case(field_name))
            return sql

        print('copying started')
        connection = None
        db_module = db_modules.get_db_module(dbtype)
        print('copying droping indexes')
        self.drop_indexes()
        if hasattr(self.db_module, 'set_foreign_keys'):
            self.execute(self.db_module.set_foreign_keys(False))
        try:
            for group in self.items:
                for it in group.items:
                    if it.item_type != 'report':
                        item = it.copy(handlers=False, filters=False, details=False)
                        if item.table_name and not item.virtual_table:
                            print('copying table %s' % item.item_name)
                            params = {'__expanded': False, '__offset': 0, '__limit': 0, '__filters': []}
                            rec_count, mess = item.get_record_count(params)
                            sql = item.get_record_count_query(params, db_module)
                            sql = convert_sql(item, sql, db_module)
                            connection, (result, error) = \
                            execute_sql(db_module, server, database, user, password,
                                host, port, encoding, connection, sql,
                                params=None, select=True)
                            record_count = result[0][0]
                            loaded = 0
                            max_id = 0
                            item.open(expanded=False, open_empty=True)
                            if record_count and rec_count != record_count:
                                self.execute('DELETE FROM "%s"' % item.table_name)
                                while True:
                                    params = {'__expanded': False, '__offset': loaded, '__limit': limit, '__fields': [], '__filters': []}
                                    sql = item.get_select_statement(params, db_module)
                                    sql = convert_sql(item, sql, db_module)
                                    connection, (result, error) = \
                                    execute_sql(db_module, server, database, user, password,
                                        host, port, encoding, connection, sql,
                                        params=None, select=True)
                                    if not error:
                                        for i, r in enumerate(result):
                                            item.append()
                                            j = 0
                                            for field in item.fields:
                                                if not field.master_field:
                                                    field.set_data(r[j])
                                                    j += 1
                                            if item._primary_key and item._primary_key_field.value > max_id:
                                                max_id = item._primary_key_field.value
                                            item.post()
                                        item.apply()
                                    else:
                                        raise Exception(error)
                                    records = len(result)
                                    loaded += records
                                    print('copying table %s: %d%%' % (item.item_name, int(loaded * 100 / record_count)))
                                    if records == 0 or records < limit:
                                        break
                                if item.gen_name:
                                    sql = self.db_module.restart_sequence_sql(item.gen_name, max_id + 1)
                                    self.execute(sql)
        finally:
            print('copying restoring indexes')
            self.restore_indexes()
            if hasattr(self.db_module, 'set_foreign_keys'):
                self.execute(self.db_module.set_foreign_keys(True))
        print('copying finished')


class AdminTask(AbstractServerTask):
    def __init__(self, app, name, caption, js_filename,
        db_type, db_server = '', db_database = '', db_user = '', db_password = '',
        host='', port='', encoding=''):
        AbstractServerTask.__init__(self, app, name, caption, js_filename,
            db_type, db_server, db_database, db_user, db_password, host, port, encoding, 2)
        filepath, filename = os.path.split(__file__)
        self.cur_path = filepath
        self.edited_docs = []

    def create_task(self):
        from jam.adm_server import create_task
        return create_task(self.app)

    def reload_task(self):
        from jam.adm_server import reload_task
        reload_task(self)

    def update_events_code(self):
        from jam.adm_server import update_events_code
        update_events_code(self)


class Group(AbstrGroup):
    def __init__(self, task, owner, name, caption, view_template=None, js_filename=None, visible=True, item_type_id=0):
        AbstrGroup.__init__(self, task, owner, name, caption, visible, item_type_id, js_filename)
        self.ID = None
        self.view_template = view_template
        self.js_filename = js_filename
        if item_type_id == common.REPORTS_TYPE:
            self.on_convert_report = None

    def add_catalog(self, name, caption, table_name, visible=True, view_template='', js_filename='', soft_delete=True):
        result = Item(self.task, self, name, caption, visible, table_name, view_template, js_filename, soft_delete)
        result.item_type_id = common.ITEM_TYPE
        return result

    def add_table(self, name, caption, table_name, visible=True, view_template='', js_filename='', soft_delete=True):
        result = Item(self.task, self, name, caption, visible, table_name, view_template, js_filename, soft_delete)
        result.item_type_id = common.TABLE_TYPE
        return result

    def add_report(self, name, caption, table_name, visible=True, view_template='', js_filename='', soft_delete=True):
        result = Report(self.task, self, name, caption, visible, table_name, view_template, js_filename)
        result.item_type_id = common.REPORT_TYPE
        return result


class Detail(AbstrDetail, ServerDataset):
    def __init__(self, task, owner, name, caption, table_name):
        AbstrDetail.__init__(self, task, owner, name, caption, True)
        ServerDataset.__init__(self, table_name)
        self.prototype = self.task.item_by_name(self.item_name)
        self.master = owner

    def init_fields(self):
        self.field_defs = []
        for field_def in self.prototype.field_defs:
            self.field_defs.append(list(field_def))
        for field_def in self.field_defs:
            field = DBField(self, field_def)
            self._fields.append(field)
        self._primary_key = self.prototype._primary_key
        self._deleted_flag = self.prototype._deleted_flag
        self._master_id = self.prototype._master_id
        self._master_rec_id = self.prototype._master_rec_id

    def do_internal_post(self):
        return {'success': True, 'id': None, 'message': '', 'detail_ids': None}

    def where_clause(self, query, db_module):
        master_id = query['__master_id']
        master_rec_id = query['__master_rec_id']
        if master_id and master_rec_id:
            result = super(Detail, self).where_clause(query, db_module)
            if self._master_id:
                clause = '%s."%s"=%s AND %s."%s"=%s' % \
                    (self.table_alias(), self._master_id_db_field_name, str(master_id),
                    self.table_alias(), self._master_rec_id_db_field_name, str(master_rec_id))
            else:
                clause = '%s."%s"=%s' % \
                    (self.table_alias(), self._master_rec_id_db_field_name, str(master_rec_id))
            if result:
                result += ' AND ' + clause
            else:
                result = ' WHERE ' + clause
            return result
        else:
            raise Exception('Invalid request parameter')

    def get_filters(self):
        return self.prototype.filters

    def get_reports_info(self):
        return []
