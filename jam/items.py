import sys, os
import zipfile
import datetime, time
import inspect
import pickle
import json
import types

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
from sqlalchemy.pool import NullPool, QueuePool

from .filelock import FileLock

from .common import consts, error_message, json_defaul_handler, QueryData
from .common  import to_bytes
from .db.databases import get_database
from .tree import AbstrTask, AbstrGroup, AbstrItem, AbstrDetail, AbstrReport
from .dataset import Dataset, DBField, DBFilter, ParamReport, Param, DatasetException
from .admin.copy_db import copy_database
from .report import Report

class ServerDataset(Dataset):
    def __init__(self):
        Dataset.__init__(self)
        self.ID = None
        self.gen_name = None
        self._order_by = []
        self.values = None
        self.on_open = None
        self.on_before_open = None
        self.on_after_open = None
        self.on_apply = None
        self.on_before_apply_record = None
        self.on_after_apply_record = None
        self.on_count = None
        self.on_field_get_text = None

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
        result._record_version = self._record_version
        result._master_id = self._master_id
        result._master_rec_id = self._master_rec_id
        result._master_field = self._master_field
        result._master_field_db_field_name = self._master_field_db_field_name
        result._primary_key_db_field_name = self._primary_key_db_field_name
        result._deleted_flag_db_field_name = self._deleted_flag_db_field_name
        result._master_id_db_field_name = self._master_id_db_field_name
        result._master_rec_id_db_field_name = self._master_rec_id_db_field_name
        result._record_version_db_field_name = self._record_version_db_field_name
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

    def do_internal_open(self, params, connection):
        return self.select_records(params, connection)

    def do_apply(self, params=None, safe=False, connection=None):
        if not self.master:
            changes = {}
            if not params:
                params = {}
            if self.change_log and self.change_log.get_changes(changes):
                data, error = self.apply_changes((changes, params), safe, connection)
                if error:
                    raise Exception(error)
                else:
                    self.change_log.update(data)

    def add_detail(self, master, master_field):
        detail = Detail(self.task, self, master.item_name, master.item_caption,
            master.table_name, master_field=master_field)
        detail.prototype = master
        self.details.append(detail)
        detail.owner = self
        detail.init_fields()
        return detail

    def detail_by_name(self, caption):
        for table in self.details:
            if table.item_name == caption:
                return table

    def _execute_select(self, sql, params):
        db = self.task.db
        con = self.task.connect()
        cursor = con.cursor()
        return self.__execute_select(cursor, sql, params, db)

    def __execute_select(self, cursor, sql, params, db):
        try:
            if params:
                params = db.process_query_params(params, cursor)
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return db.process_query_result(cursor.fetchall())
        except Exception as x:
            self.log.exception('%s:\n%s' % (error_message(x), sql))
            print(sql)
            print(params)

    def execute_open(self, params, connection=None, db=None, query_data=None, ):
        rows = None
        error_mes = ''
        if not db:
            db = self.task.db
        if not query_data:
            query_data = QueryData(params)
        limit = query_data.limit
        offset = query_data.offset
        sqls = db.get_select_queries(self, query_data)
        if connection:
            con = connection
        else:
            con = self.task.connect()
        cursor = con.cursor()
        try:
            if len(sqls) == 1:
                rows = self.__execute_select(cursor, sqls[0][0], sqls[0][1], db)
            else:
                rows = []
                cut = False
                for sql in sqls:
                    rows += self.__execute_select(cursor, sql[0], sql[1], db)
                    if limit or offset:
                        if len(rows) >= offset + limit:
                            rows = rows[offset:offset + limit]
                            cut = True
                            break
                if (limit or offset) and not cut:
                    rows = rows[offset:offset + limit]
                if query_data.summary:
                    new_rows = [0 for r in rows[0]]
                    for row in rows:
                        for i, r in enumerate(row):
                            if not r is None:
                                new_rows[i] += r
                    rows = [new_rows]
        finally:
            if not connection:
                con.close()
        return rows, error_mes

    def init_open_dataset(self, query_data, dataset, result):
        if not dataset:
            if self.master:
                dataset = self.prototype.copy(filters=False, details=False, handlers=False)
            else:
                dataset = self.copy(filters=False, details=False, handlers=False)
            dataset.log_changes = False
            dataset.open(expanded=query_data.expanded, fields=query_data.fields, open_empty=True)
            dataset._dataset = result
            dataset.first();
        return dataset

    def select_records(self, params, connection=None, client_request=False):
        if client_request and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)

        query_data = QueryData(params)
        query_data.client_request = client_request

        result = None # on_open is depricated
        if self.task.on_open:
            result = self.task.on_open(self, params)
        if result is None and self.on_open:
            result = self.on_open(self, params)
        if result:
            return result

        error = None
        result = None
        exec_query = True
        if self.task.on_before_open:
            exec_query = self.task.on_before_open(self, query_data, params, connection)
        if exec_query != False and self.on_before_open:
            exec_query = self.on_before_open(self, query_data, params, connection)

        if exec_query != False:
            if self.virtual_table:
                result = []
            else:
                result, error = self.execute_open(params, connection, query_data=query_data)

        dataset = None
        if self.on_after_open:
            dataset = self.init_open_dataset(query_data, dataset, result)
            self.on_after_open(self, query_data, params, connection, dataset)
        elif self.task.on_after_open:
            dataset = self.init_open_dataset(query_data, dataset, result)
            self.task.on_after_open(self, query_data, params, connection, dataset)
        if dataset:
            result = dataset._dataset
        return result, error

    def apply_delta(self, delta, params, connection, db=None):
        if not db:
            db = self.task.db
        for d in delta:
            if not d.rec_deleted():
                d.check_record_valid()
        db.process_changes(delta, connection, params)
        return delta.change_log.prepare_updates()

    def set_apply_connection(self, delta, con):
        delta._apply_connection = con
        for d in delta.details:
            self.set_apply_connection(d, con)

    def _get_delta_params(self, delta, params_dict):
        return params_dict.get(str(delta.ID), {})

    def apply_changes(self, data, safe, connection=None):
        result = None
        result_data = None
        changes, params_dict = data
        delta = self.delta(changes, safe)
        delta_params = self._get_delta_params(delta, params_dict)
        if connection:
            con = connection
        else:
            con = self.task.connect()
        self.set_apply_connection(delta, con)
        try:
            if self.task.on_apply:
                result = self.task.on_apply(self, delta, delta_params, con)
            if result is None and self.on_apply:
                result = self.on_apply(self, delta, delta_params, con)
            if result is None:
                result = self.apply_delta(delta, params_dict, con)
            if not connection and con:
                con.commit()
        finally:
            self.set_apply_connection(delta, None)
            if not connection and con:
                con.close()
        return result, ''

    def update_deleted(self, details=None, connection=None): #depricated
        if self._is_delta:
            if details is None:
                details = self.details
            rec_no = self.rec_no
            try:
                for it in self:
                    if it.rec_deleted():
                        for detail in details:
                            fields = []
                            for field in detail.fields:
                                fields.append(field.field_name)
                            prototype = self.task.item_by_ID(detail.prototype.ID).copy()
                            where = {
                                prototype._master_id: self.ID,
                                prototype._master_rec_id: self._primary_key_field.value
                            }
                            prototype.open(fields=fields, expanded=detail.expanded, where=where, connection=connection)
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
                cursor.execute(self.task.db.empty_table_query(self))
                con.commit()
            except Exception as e:
                self.log.exception(error_message(e))
                con.rollback()
            finally:
                con.close()

    def get_next_id(self, db=None):
        if db is None:
            db = self.task.db
        sql = db.next_sequence(self.gen_name)
        if sql:
            rec = self.task.select(sql)
            if rec:
                if rec[0][0]:
                    return int(rec[0][0])

    def load_interface(self):
        self._view_list = []
        self._edit_list = []
        self._order_list = []
        self._reports_list = []
        value = self.f_info.value
        if value:
            if len(value) >= 4 and value[0:4] == 'json':
                lists = json.loads(value[4:])
            else:
                lists = pickle.loads(to_bytes(value, 'utf-8'))
            self._view_list = lists['view']
            self._edit_list = lists['edit']
            self._order_list = lists['order']
            if lists.get('reports'):
                self._reports_list = lists['reports']

    def store_interface(self, connection=None, apply_interface=True):
        handlers = self.store_handlers()
        self.clear_handlers()
        try:
            self.edit()
            dic = {'view': self._view_list,
                    'edit': self._edit_list,
                    'order': self._order_list,
                    'reports': self._reports_list}
            self.f_info.value = 'json' + json.dumps(dic, default=json_defaul_handler)
            self.post()
            if apply_interface:
                self.apply(connection)
        finally:
            handlers = self.load_handlers(handlers)

    def store_index_fields(self, f_list):
        return json.dumps(f_list)

    def load_index_fields(self, value):
        return json.loads(str(value))


class Group(AbstrGroup):
    def __init__(self, task, owner, name='', caption=''):
        AbstrGroup.__init__(self, task, owner, name, caption)
        self.ID = None

    def add_item(self, name, caption):
        result = Item(self.task, self, name, caption)
        return result

    def get_child_class(self):
        return Item

class ReportGroup(Group):
    def __init__(self, task, owner, name='', caption=''):
        Group.__init__(self, task, owner, name, caption)
        self.on_convert_report = None

    def add_report(self, name, caption):
        result = Report(self.task, self, name, caption)
        return result

    def get_child_class(self):
        return Report

class Item(AbstrItem, ServerDataset):
    def __init__(self, task, owner, name='', caption=''):
        item_type_id = consts.ITEM_TYPE
        AbstrItem.__init__(self, task, owner, name, caption)
        ServerDataset.__init__(self)
        self.reports = []

    def get_child_class(self):
        return Detail

    def get_reports_info(self):
        result = []
        for report in self.reports:
            result.append(report.ID)
        return result

    def get_select_statement(self, query, db=None): # depricated
        if db is None:
            db = self.task.db
        return db.get_select_statement(self, query)

    def order_clause(self, query, db=None): # depricated
        if db is None:
            db = self.task.db
        return db.order_clause(self, query)

    def where_clause(self, query, db=None): # depricated
        if db is None:
            db = self.task.db
        return db.where_clause(self, query)


class Report(AbstrReport, ParamReport, Report):
    def __init__(self, task, owner, name='', caption=''):
        AbstrReport.__init__(self, task, owner, name, caption)
        ParamReport.__init__(self)
        self.item_type_id = consts.REPORT_TYPE

        self.on_before_generate = None
        self.on_generate = None
        self.on_after_generate = None
        self.on_parsed = None
        self.on_before_save_report = None
        self.on_field_get_text = None
        self.on_convert_report = None

    def copy(self):
        result = self.__class__(self.task, None, self.item_name, self.item_caption);
        result.template = self.template
        result.on_before_generate = self.on_before_generate
        result.on_generate = self.on_generate
        result.on_after_generate = self.on_after_generate
        result.on_before_save_report = self.on_before_save_report
        result.on_parsed = self.on_parsed
        result.on_convert_report = self.owner.on_convert_report
        result.param_defs = self.param_defs
        for param_def in result.param_defs:
            param = Param(result, param_def)
            result.params.append(param)
        result.prepare_params()
        return  result

    def print_report(self, param_values, url, ext=None, safe=False):
        self.delete_reports()
        if safe and not self.can_view():
            raise Exception(consts.language('cant_view') % self.item_caption)
        copy = self.copy()
        copy.name = self.item_name
        copy.template_path = os.path.join(self.task.work_dir, 'reports', self.template)
        copy.url = url
        copy.dest_folder = os.path.join(self.task.work_dir, 'static', 'reports')
        copy.dest_url = os.path.join(url, 'static', 'reports')
        if not os.path.exists(copy.dest_folder):
            os.makedirs(copy.dest_folder)
        copy.on_convert = self.on_convert_report
        for i, param in enumerate(copy.params):
            param.data = param_values[i];
        copy.prepare_report(self.on_generate, ext='.' + ext)
        if url:
            return copy.report_url

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


class DBInfo(object):
    def __init__(self, dsn='', server = '', lib=None, database = '',
        user = '', password = '', host='', port='', encoding=''):
        self.dsn = dsn
        self.server = server
        self.lib = lib
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.encoding = encoding
        if not self.port:
            self.port = None
        else:
            self.port = int(port)
        if not self.encoding:
            self.encoding = None


class AbstractServerTask(AbstrTask):
    def __init__(self, app, name, caption):
        AbstrTask.__init__(self, None, None, None)
        self.app = app
        self.items = []
        self.lookup_lists = {}
        self.ID = None
        self.item_name = name
        self.item_caption = caption
        self.visible = True
        self.on_before_request = None
        self.on_after_request = None
        self.on_open = None
        self.on_before_open = None
        self.on_after_open = None
        self.on_apply = None
        self.on_before_apply_record = None
        self.on_after_apply_record = None
        self.on_count = None
        self.on_request = None
        self.on_upload = None
        self.work_dir = app.work_dir
        self.modules = []
        self.log = app.log
        self.consts = consts
        self.pool = None

    @property
    def version(self):
        return consts.VERSION

    def get_child_class(self):
        return Group

    def create_pool(self, con_pool_size=1, persist_con=True):
        if self.pool:
            self.pool.dispose()
        if persist_con:
            if self.db_type == consts.SQLITE:
                self.pool = NullPool(self.create_connection)
            else:
                self.pool = QueuePool(self.create_connection, \
                    pool_size=con_pool_size, max_overflow=con_pool_size*2, \
                    recycle=60*60)
        else:
            self.pool = NullPool(self.create_connection)

    def create_connection(self):
        return self.db.connect(self.db_info)

    def connect(self):
        return self.pool.connect()

    def __execute_query_list(self, cursor, query_list):
        for query in query_list:
            if query:
                if type(query) == list:
                    self.__execute_query_list(cursor, query)
                else:
                    if type(query) == tuple:
                        self.execute_query(cursor, query[0], query[1])
                    else:
                        self.execute_query(cursor, query)

    def execute(self, query, params=None, connection=None, db=None):
        # ~ print (query, params)
        error = None
        con = connection
        if not connection:
            con = self.connect()
        cursor = con.cursor()
        try:
            if type(query) == list:
                self.__execute_query_list(cursor, query)
            else:
                self.execute_query(cursor, query, params)
        except Exception as x:
            error = error_message(x)
        finally:
            if not connection:
                con.commit()
                con.close()
        return error

    def select(self, select_query, connection=None, db=None):
        result = None
        error = None
        con = connection
        if not connection:
            con = self.connect()
        cursor = con.cursor()
        try:
            self.execute_query(cursor, select_query)
            result = cursor.fetchall()
            result = [list(r) for r in result]
        except Exception as x:
            error = error_message(x)
        finally:
            if not connection:
                con.close()
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
        item_module.__dict__['task'] = self
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
            exec(comp_code, item_module.__dict__)

            item_module.__dict__['__loader__'] = item._loader
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                # ~ if hasattr(item, func_name) and func_name[:3] != 'on_':
                    # ~ item.log.warning('Module %s: method "%s" will override "%s" existing attribute. Please, rename the function.' % \
                        # ~ (item.module_name, func_name, item.item_name))
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
    def __init__(self, app, name, caption):
        AbstractServerTask.__init__(self, app, name, caption)
        self.on_created = None
        self.on_login = None
        self.on_logout = None
        self.on_ext_request = None
        self.init_dict = {}
        for key, value in self.__dict__.items():
            self.init_dict[key] = value

    @property
    def timeout(self):
        return consts.TIMEOUT

    def login(self, request, dic=None):
        if dic:
            return self.app.login(request, self, dic)
        else:
            return self.app.login(request, self, request.form)

    def logged_in(self, request):
        return self.app.check_session(request, self)

    def redirect(self, location, code=302, Response=None):
        return redirect(location, code, Response)

    def serve_page(self, file_path, dic=None):
        return self.app.serve_page(file_path, dic)

    def copy_database(self, dbtype, connection, limit = 1000):
        copy_database(self, dbtype, connection, limit)


class AdminTask(AbstractServerTask):
    def __init__(self, app, name, caption, db_type, db_database = ''):
        AbstractServerTask.__init__(self, app, name, caption)
        self.timeout = 43200
        self.db_type = db_type
        self.db_info = DBInfo(database=os.path.join(app.work_dir, db_database))
        self.db = get_database(app, db_type, self.db_info.lib)
        self.create_pool()

class Detail(AbstrDetail, ServerDataset):
    def __init__(self, task, owner, name='', caption='', table_name='', master_field=None):
        AbstrDetail.__init__(self, task, owner, name, caption)
        ServerDataset.__init__(self)
        self.item_type_id = consts.DETAIL_TYPE
        self.master_field = master_field
        self.master = owner

    def init_fields(self):
        self.field_defs = []
        for field_def in self.prototype.field_defs:
            self.field_defs.append(list(field_def))
        for field_def in self.field_defs:
            field = DBField(self, field_def)
            self._fields.append(field)
        self.edit_lock = self.prototype.edit_lock
        self._primary_key = self.prototype._primary_key
        self._deleted_flag = self.prototype._deleted_flag
        self._record_version = self.prototype._record_version
        self._master_id = self.prototype._master_id
        self._master_rec_id = self.prototype._master_rec_id
        self._virtual_table = self.prototype._virtual_table

    def do_internal_post(self):
        return {'success': True, 'id': None, 'message': '', 'detail_ids': None}

    def get_filters(self):
        return self.prototype.filters

    def get_reports_info(self):
        return []
