import sys, os
import zipfile
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape
import datetime, time
import inspect
import json
if os.name == "nt":
    try:
        from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
    except:
        from _winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE

from werkzeug._compat import iteritems, iterkeys, text_type, string_types, to_bytes, to_unicode
from werkzeug.security import generate_password_hash, check_password_hash

from .third_party.filelock import FileLock
from .third_party.sqlalchemy.pool import NullPool, QueuePool
from .third_party.six import exec_, print_, get_function_code

from .common import consts, error_message
from .db.db_modules import SQLITE, get_db_module
from .items import AbstrTask, AbstrGroup, AbstrItem, AbstrDetail, AbstrReport
from .dataset import Dataset, DBField, DBFilter, ParamReport, Param, DatasetException
from .sql import SQL
from .execute import execute_sql, execute_sql_connection

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

    def add_field(self, *args, **kwargs):
        field_def = self.add_field_def(*args, **kwargs)
        field = DBField(self, field_def)
        self._fields.append(field)
        return field

    def create_fields(self, info):
        for field_def in info:
            self.field_defs.append(field_def)
            field = DBField(self, field_def)
            self._fields.append(field)

    def add_filter(self, *args):
        filter_def = self.add_filter_def(*args)
        fltr = DBFilter(self, filter_def)
        self.filters.append(fltr)
        return fltr

    def create_filters(self, info):
        for filter_def in info:
            self.add_filter(*filter_def)

    def do_internal_open(self, params):
        return self.select_records(params)

    def do_apply(self, params=None, safe=False, connection=None):
        if not self.master and self.log_changes:
            changes = {}
            self.change_log.get_changes(changes)
            if changes['data']:
                data, error = self.apply_changes((changes, params), safe, connection)
                if error:
                    raise Exception(error)
                else:
                    self.change_log.update(data)

    def add_detail(self, table):
        detail = Detail(self.task, self, table.item_name, table.item_caption, table.table_name)
        detail.prototype = table
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
            raise Exception(consts.language('cant_view') % self.item_caption)
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

    def find_rec_version(self, params):
        item_id = params.get('__edit_record_id')
        if item_id and self.task.lock_item:
            locks = self.task.lock_item.copy()
            return self.get_version(locks, item_id)

    def get_version(self, locks, item_id):
        locks.set_where(item_id=self.ID, item_rec_id=item_id)
        locks.open()
        if locks.rec_count:
            return locks.version.value
        else:
            return 1

    def execute_open(self, params, connection=None, db_module=None):
        error_mes = ''
        limit = params['__limit']
        offset = params['__offset']
        sqls = self.get_select_queries(params, db_module)
        if len(sqls) == 1:
            rows = self.task.select(sqls[0], connection, db_module)
        else:
            rows = []
            cut = False
            for sql in sqls:
                rows += self.task.select(sql, connection, db_module)
                if limit or offset:
                    if len(rows) >= offset + limit:
                        rows = rows[offset:offset + limit]
                        cut = True
                        break
            if (limit or offset) and not cut:
                rows = rows[offset:offset + limit]
        return rows, error_mes

    def select_records(self, params, safe=False):
        if safe and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)
        result = None
        if self.task.on_open:
            result = self.task.on_open(self, params)
        if result is None and self.on_open:
            result = self.on_open(self, params)
        if result is None:
            result = self.execute_open(params)
        result = list(result)
        result.append(self.find_rec_version(params))
        return result

    def update_rec_version(self, delta, params, connection):
        version = params.get('__edit_record_version')
        if version and delta.rec_count == 1 and self.task.lock_item:
            item_id = delta._primary_key_field.value
            locks = self.task.lock_item.copy()
            new_version = self.get_version(locks, item_id)
            if new_version != version:
                raise Exception(consts.language('edit_record_modified'))
            locks.set_where(item_id=self.ID, item_rec_id=item_id)
            locks.open()
            if locks.rec_count:
                locks.edit()
            else:
                locks.append()
            locks.item_id.value = self.ID
            locks.item_rec_id.value = item_id
            locks.version.value = version + 1
            locks.post()
            locks.apply(connection)
            return locks.version.value

    def apply_delta(self, delta, params=None, connection=None, db_module=None):
        if not db_module:
            db_module = self.task.db_module
        sql = delta.apply_sql(params)
        return self.task.execute(sql, None, connection=connection, db_module=db_module, autocommit=False)

    def apply_changes(self, data, safe, connection=None):
        result = None
        changes, params = data
        if not params:
            params = {}
        params['__safe'] = safe
        delta = self.delta(changes)
        if connection:
            autocommit = False
        else:
            autocommit = True
            connection = self.task.connect()
        try:
            rec_version = self.update_rec_version(delta, params, connection)
            if self.task.on_apply:
                try:
                    result = self.task.on_apply(self, delta, params, connection)
                except:
                    # for compatibility with previous versions
                    if get_function_code(self.task.on_apply).co_argcount == 3:
                        result = self.task.on_apply(self, delta, params)
                    else:
                        raise
            if result is None and self.on_apply:
                try:
                    result = self.on_apply(self, delta, params, connection)
                except:
                    # for compatibility with previous versions
                    if get_function_code(self.on_apply).co_argcount == 3:
                        result = self.on_apply(self, delta, params)
                    else:
                        raise
            if result is None:
                result = self.apply_delta(delta, params, connection)
                if autocommit:
                    connection.commit()
            try:
                result[0]['__edit_record_version'] = rec_version
            except:
                pass
        finally:
            if connection and autocommit:
                connection.close()
        return result

    def update_deleted(self):
        if self._is_delta:
            rec_no = self.rec_no
            try:
                for it in self:
                    if it.rec_deleted():
                        for detail in self.details:
                            fields = []
                            for field in detail.fields:
                                fields.append(field.field_name)
                            prototype = self.task.item_by_ID(detail.prototype.ID).copy()
                            where = {
                                prototype._master_id: self.ID,
                                prototype._master_rec_id: self._primary_key_field.value
                            }
                            prototype.open(fields=fields, expanded=detail.expanded, where=where)
                            if prototype.record_count():
                                it.edit()
                                for p in prototype:
                                    detail.append()
                                    for field in detail.fields:
                                        f = p.field_by_name(field.field_name)
                                        field.set_value(f.value, f.lookup_value)
                                    detail.post()
                                it.post()
                                for d in detail:
                                    d.record_status = consts.RECORD_DELETED
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

    def empty(self):
        if not self.master and self.table_name:
            con = self.task.connect()
            try:
                cursor = con.cursor()
                cursor.execute(self.empty_table_sql())
                con.commit()
            except:
                con.rollback()
            finally:
                con.close()



class Group(AbstrGroup):
    def __init__(self, task, owner, name='', caption='', template=None, js_filename=None, visible=True, item_type_id=0):
        AbstrGroup.__init__(self, task, owner, name, caption, visible, item_type_id, js_filename)
        self.ID = None
        self.template = template
        self.js_filename = js_filename
        if item_type_id == consts.REPORTS_TYPE:
            self.on_convert_report = None

    def add_item(self, name, caption, table_name, visible=True, template='', js_filename='', soft_delete=True):
        result = Item(self.task, self, name, caption, visible, table_name, js_filename, soft_delete)
        result.item_type_id = consts.ITEM_TYPE
        return result

    def add_report(self, name, caption, table_name, visible=True, template='', js_filename='', soft_delete=True):
        result = Report(self.task, self, name, caption, visible, table_name, template, js_filename)
        result.item_type_id = consts.REPORT_TYPE
        return result

    def get_child_class(self):
        if self.item_type_id == consts.REPORTS_TYPE:
            return Report
        else:
            return Item

class Item(AbstrItem, ServerDataset):
    def __init__(self, task, owner, name='', caption='', visible = True, table_name='', js_filename='', soft_delete=True):
        AbstrItem.__init__(self, task, owner, name, caption, visible, js_filename)
        ServerDataset.__init__(self, table_name, soft_delete)
        self.item_type_id = None
        self.reports = []

    def get_child_class(self):
        return Detail

    def get_reports_info(self):
        result = []
        for report in self.reports:
            result.append(report.ID)
        return result

class Report(AbstrReport, ParamReport):
    def __init__(self, task, owner, name='', caption='', visible = True,
            table_name='', template='', js_filename=''):
        AbstrReport.__init__(self, task, owner, name, caption, visible, js_filename)
        ParamReport.__init__(self)
        self.template = template
        self.template_name = None
        self.template_content = {}
        self.ext = 'ods'

        self.on_before_generate = None
        self.on_generate = None
        self.on_after_generate = None
        self.on_parsed = None
        self.on_before_save_report = None
        self.on_field_get_text = None

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
        self.delete_reports()
        if safe and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)
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
            param.data = param_values[i];
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
                        self.log.exception(error_message(e))
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
                                            val = self.replace(val, '.', consts.DECIMAL_POINT)
                                    else:
                                        if not key in iterkeys(d):
                                            self.log.info('Report: "%s" band: "%s" key "%s" not found in the dictionary' % \
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

    def _set_modified(self, value):
        pass

    def delete_reports(self):
        task = self.task
        if consts.DELETE_REPORTS_AFTER:
            path = os.path.join(task.work_dir, 'static', 'reports')
            if os.path.isdir(path):
                for f in os.listdir(path):
                    file_name = os.path.join(path, f)
                    if os.path.isfile(file_name):
                        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
                        hours, sec = divmod(delta.total_seconds(), 3600)
                        if hours > consts.DELETE_REPORTS_AFTER:
                            os.remove(file_name)

    def cur_to_str(self, value):
        return consts.cur_to_str(value)

    def date_to_str(self, value):
        return consts.date_to_str(value)

    def datetime_to_str(self, value):
        return consts.datetime_to_str(value)


class AbstractServerTask(AbstrTask):
    def __init__(self, app, name, caption, js_filename, db_type, db_server = '',
        db_database = '', db_user = '', db_password = '', host='', port='',
        encoding='', con_pool_size=1, persist_con=True):
        AbstrTask.__init__(self, None, None, None, None)
        self.app = app
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
        self.db_module = get_db_module(self.db_type)
        self.on_before_request = None
        self.on_after_request = None
        self.on_open = None
        self.on_apply = None
        self.on_count = None
        self.work_dir = app.work_dir
        self.con_pool_size = 0
        self.modules = []
        self.con_pool_size = con_pool_size
        self.persist_con = persist_con
        self.create_pool()
        if self.db_type == SQLITE:
            self.db_database = os.path.join(self.work_dir, self.db_database)
        self.log = app.log
        self.consts = consts

    @property
    def version(self):
        return consts.VERSION

    def get_child_class(self):
        return Group

    def create_pool(self):
        if self.persist_con:
            if self.db_type == SQLITE:
                self.pool = NullPool(self.getconn)
            else:
                self.pool = QueuePool(self.getconn, pool_size=self.con_pool_size, \
                    max_overflow=self.con_pool_size*2, recycle=60*60)
        else:
            self.pool = NullPool(self.getconn)

    def create_connection(self):
        return self.db_module.connect(self.db_database, self.db_user, \
            self.db_password, self.db_host, self.db_port, self.db_encoding, self.db_server)

    def create_connection_ex(self, db_module, database, user=None, password=None, \
        host=None, port=None, encoding=None, server=None):
        return db_module.connect(database, user, password, host, port, encoding, server)

    def getconn(self):
        return self.create_connection()

    def connect(self):
        try:
            return self.pool.connect()
        except:
            if self.pool is None:
                self.app.create_connection_pool()
                return self.pool.connect()

    def pool_execute(self, command, params=None, select=False):
        con = self.connect()
        try:
            connection, result = execute_sql_connection(con, command, params, select, self.db_module)
        finally:
            con.close()
        return result

    def execute(self, command, params=None, connection=None, db_module=None, \
        select=False, autocommit=True):
        if connection:
            connection, result = execute_sql_connection(connection, command, \
                params, select, db_module, autocommit=autocommit)
        elif self.persist_con:
            result = self.pool_execute(command, params, select)
        else:
            result = self.pool_execute(command, params, select)
        return result

    def select(self, command, connection=None, db_module=None):
        result, error = self.execute(command, None, connection, db_module, select=True)
        if error:
            raise Exception(error)
        else:
            return result

    def execute_select(self, command): #depricated
        return self.select(command)

    def generate_password_hash(self, password, method='pbkdf2:sha256', salt_length=8):
        return generate_password_hash(password, method, salt_length)

    def check_password_hash(self, pwhash, password):
        return check_password_hash(pwhash, password)

    def get_module_name(self):
        return str(self.item_name)

    def lock(self, lock_name, timeout=-1):
        lock_file = os.path.join(self.work_dir, 'locks', lock_name + '.lock')
        locks_dir = os.path.dirname(lock_file)
        if not os.path.exists(locks_dir):
            os.makedirs(locks_dir)
        return FileLock(lock_file, timeout)

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
                self.log.exception(error_message(e))
            comp_code = compile(code, item.module_name, "exec")
            exec_(comp_code, item_module.__dict__)

            item_module.__dict__['__loader__'] = item._loader
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                setattr(item, func_name, func)
        del code

    def convert_report(self, report, ext):
        converted = False
        with self.task.lock('$report_conversion'):
            try:
                from subprocess import Popen, STDOUT, PIPE
                if os.name == "nt":
                    regpath = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\soffice.exe"
                    root = OpenKey(HKEY_LOCAL_MACHINE, regpath)
                    s_office = QueryValue(root, "")
                else:
                    s_office = "soffice"
                convertion = Popen([s_office, '--headless', '--convert-to', ext,
                    report.report_filename, '--outdir', os.path.join(self.work_dir, 'static', 'reports')],
                    stderr=STDOUT,stdout=PIPE)
                out, err = convertion.communicate()
                converted = True
            except Exception as e:
                self.log.exception(error_message(e))
        return converted

class Task(AbstractServerTask):
    def __init__(self, app, name, caption, js_filename,
        db_type, db_server = '', db_database = '', db_user = '', db_password = '',
        host='', port='', encoding='', con_pool_size=4, persist_con=True):
        AbstractServerTask.__init__(self, app, name, caption, js_filename,
            db_type, db_server, db_database, db_user, db_password,
            host, port, encoding, con_pool_size, persist_con)
        self.on_created = None
        self.on_login = None
        self.on_ext_request = None
        self.compress_history = True
        self.init_dict = {}
        for key, value in iteritems(self.__dict__):
            self.init_dict[key] = value

    @property
    def timeout(self):
        return consts.TIMEOUT

    def copy_database(self, dbtype, database=None, user=None, password=None,
        host=None, port=None, encoding=None, server=None, limit = 1000):

        def convert_sql(item, sql, db_module):
            new_case = item.task.db_module.identifier_case
            old_case = db_module.identifier_case
            if old_case('a') != new_case('a'):
                if new_case(item.table_name) == item.table_name:
                    sql = sql.replace(item.table_name, old_case(item.table_name))
                for field in item.fields:
                    if new_case(field.db_field_name) == field.db_field_name and \
                        not field.db_field_name.upper() in consts.SQL_KEYWORDS:
                        field_name = '"%s"' % field.db_field_name
                        sql = sql.replace(field_name, old_case(field_name))
            return sql

        def drop_indexes():
            con = self.connect()
            try:
                cursor = con.cursor()
                from jam.admin.admin import drop_indexes_sql
                sqls = drop_indexes_sql(self.app.admin)
                for s in sqls:
                    try:
                        cursor.execute(s)
                        con.commit()
                    except Exception as e:
                        con.rollback()
                        pass
            finally:
                con.close()

        def restore_indexes():
            con = self.connect()
            try:
                cursor = con.cursor()
                from jam.admin.admin import restore_indexes_sql
                sqls = restore_indexes_sql(self.app.admin)
                for s in sqls:
                    try:
                        cursor.execute(s)
                        con.commit()
                    except Exception as e:
                        con.rollback()
                        pass
            finally:
                con.close()

        def get_rows(item, db_module, con, loaded, limit):
            params = {'__expanded': False, '__offset': loaded, '__limit': limit, '__fields': [], '__filters': []}
            sql = item.get_select_statement(params, db_module)
            sql = convert_sql(item, sql, db_module)
            con, (rows, error) = execute_sql(db_module, server, database, user, password,
                host, port, encoding, con, sql, params=None, select=True)
            return rows

        def copy_sql(item):
            fields = []
            values = []
            index = 0
            for field in item.fields:
                if not field.master_field:
                    index += 1
                    fields.append('"%s"' % field.db_field_name)
                    values.append('%s' % self.db_module.value_literal(index))
            fields = ', '.join(fields)
            values = ', '.join(values)
            return 'INSERT INTO "%s" (%s) VALUES (%s)' % (item.table_name, fields, values)

        def copy_rows(item, db_module, con, sql, rows):
            error = None
            for i, r in enumerate(rows):
                j = 0
                for field in item.fields:
                    if not field.master_field:
                        if not r[j] is None:
                            if field.data_type == consts.INTEGER:
                                r[j] = int(r[j])
                            elif field.data_type in (consts.FLOAT, consts.CURRENCY):
                                r[j] = float(r[j])
                            elif field.data_type == consts.BOOLEAN:
                                if r[j]:
                                    r[j] = 1
                                else:
                                    r[j] = 0
                            elif field.data_type == consts.DATE and type(r[j]) == text_type:
                                r[j] = consts.convert_date(r[j])
                            elif field.data_type == consts.DATETIME and type(r[j]) == text_type:
                                r[j] = consts.convert_date_time(r[j])
                            elif field.data_type in [consts.LONGTEXT, consts.KEYS]:
                                if self.db_module.DATABASE == 'FIREBIRD':
                                    if type(r[j]) == text_type:
                                        r[j] = to_bytes(r[j], 'utf-8')
                                elif db_module.DATABASE == 'FIREBIRD':
                                    if type(r[j]) == bytes:
                                        r[j] = to_unicode(r[j], 'utf-8')
                        j += 1
            cursor = con.cursor()
            try:
                if hasattr(db_module, 'set_identity_insert'):
                    if item._primary_key:
                        cursor.execute(db_module.set_identity_insert(item.table_name, True))
                    new_rows = []
                    for r in rows:
                        new_rows.append(tuple(r))
                    rows = new_rows
                if hasattr(cursor, 'executemany'):
                    cursor.executemany(sql, rows)
                else:
                    for r in rows:
                        cursor.execute(sql, r)
                con.commit()
                if hasattr(db_module, 'set_identity_insert'):
                    if item._primary_key:
                        cursor.execute(db_module.set_identity_insert(item.table_name, False))
            except Exception as e:
                self.log.exception(error_message(e))
                con.rollback()
            return error

        with self.lock('$copying database'):
            self.log.info('copying started')
            self.log.info('copying started')
            source_con = None
            con = self.connect()
            db_module = get_db_module(dbtype)
            self.log.info('copying droping indexes')
            drop_indexes()
            if hasattr(self.db_module, 'set_foreign_keys'):
                self.execute(self.db_module.set_foreign_keys(False))
            try:
                for group in self.items:
                    for it in group.items:
                        if it.item_type != 'report':
                            item = it.copy(handlers=False, filters=False, details=False)
                            if item.table_name and not item.virtual_table:
                                params = {'__expanded': False, '__offset': 0, '__limit': 0, '__filters': []}
                                rec_count, mess = item.get_record_count(params)
                                sql = item.get_record_count_query(params, db_module)
                                sql = convert_sql(item, sql, db_module)
                                source_con, (result, error) = execute_sql(db_module, server, database, user, password,
                                    host, port, encoding, source_con, sql, params=None, select=True)
                                record_count = result[0][0]
                                loaded = 0
                                self.log.info('copying table %s records: %s' % (item.item_name, record_count))
                                if record_count and rec_count != record_count:
                                    self.execute('DELETE FROM "%s"' % item.table_name)
                                    sql = copy_sql(item)
                                    while True:
                                        now = datetime.datetime.now()
                                        rows = get_rows(item, db_module, source_con, loaded, limit)
                                        if not error:
                                            error = copy_rows(item, self.db_module, con, sql, rows)
                                            if error:
                                                raise Exception(error)
                                        else:
                                            raise Exception(error)
                                        records = len(rows)
                                        loaded += records
                                        self.log.info('copying table %s: %d%%' % (item.item_name, int(loaded * 100 / record_count)))
                                        if records == 0 or records < limit:
                                            break
                                    if item.gen_name:
                                        cursor = con.cursor()
                                        cursor.execute('SELECT MAX(%s) FROM %s' % (item._primary_key, item.table_name))
                                        res = cursor.fetchall()
                                        max_pk = res[0][0]
                                        sql = self.db_module.restart_sequence_sql(item.gen_name, max_pk + 1)
                                        cursor.execute(sql)
                                        con.commit()
            except Exception as e:
                self.log.exception(error_message(e))
            finally:
                self.log.info('copying restoring indexes')
                restore_indexes()
                if hasattr(self.db_module, 'set_foreign_keys'):
                    self.execute(self.db_module.set_foreign_keys(True))
            self.log.info('copying finished')


class AdminTask(AbstractServerTask):
    def __init__(self, app, name, caption, js_filename,
        db_type, db_server = '', db_database = '', db_user = '', db_password = '',
        host='', port='', encoding=''):
        AbstractServerTask.__init__(self, app, name, caption, js_filename,
            db_type, db_server, db_database, db_user, db_password, host, port, encoding)
        self.timeout = 43200

class Detail(AbstrDetail, ServerDataset):
    def __init__(self, task, owner, name='', caption='', table_name=''):
        AbstrDetail.__init__(self, task, owner, name, caption, True)
        ServerDataset.__init__(self, table_name)
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
