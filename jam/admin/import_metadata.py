import sys
import os
import datetime
import time
import zipfile
import tempfile
import shutil
import json
import traceback

from ..common import consts, file_read, file_write, error_message
from ..db.databases import get_database
from .admin import connect_task_db, FieldInfo
from .admin import insert_item_query, update_item_query, delete_item_query
from .admin import indices_insert_query, indices_delete_query

from .export_metadata import metadata_items

def import_metadata(admin, file_name, from_client=False):
    imp = MetaDataImport(admin, file_name, from_client)
    return imp.import_metadata()

class MetaDataImport(object):
    def __init__(self, task, file_name, from_client):
        self.task = task
        self.file_name = os.path.join(task.work_dir, os.path.normpath(file_name))
        self.from_client = from_client
        self.client_log = ''
        self.server_log = ''
        self.success = True
        self.error = None
        self.tmpdir = None
        self.new_items = {}
        self.old_items = {}
        self.db_type = task.task_db_type
        self.new_db_type = None
        self.db_sql = None
        self.adm_sql = None
        self.db = task.task_db_module
        self.items_hidden_fields = ['f_gen_name']
        self.params_hidden_fields = [
                'f_safe_mode', 'f_debugging', 'f_modification',
                'f_client_modified', 'f_server_modified',
                'f_build_version', 'f_params_version',
                'f_maintenance', 'f_import_delay', 'f_production'
            ]

    def import_metadata(self):
        self.check_can_import()
        self.prepare_data()
        self.check_data_integrity()
        self.analize_data()
        self.wait_ready()
        self.import_databases()
        self.copy_files()
        self.update_logs()
        self.tidy_up()
        return self.success, self.error, self.client_log

    def check_can_import(self):
        if self.db_type == consts.SQLITE and not self.project_empty():
            self.success = False
            self.error = 'Metadata can not be imported into an existing SQLITE project'
            self.show_error(self.error)

    def update_indexes(self):
        if self.new_db_type == consts.FIREBIRD or self.db_type == consts.FIREBIRD:
            item = self.new_items['sys_indices']
            for it in item:
                if it.f_fields_list.value:
                    field_list = it.load_index_fields(it.f_fields_list.value)
                    desc = it.descending.value
                    if field_list:
                        it.edit()
                        if self.new_db_type == consts.FIREBIRD:
                            l = []
                            for f in field_list:
                                l.append([f[0], desc])
                            field_list = l
                        elif self.db_type == consts.FIREBIRD:
                            desc = field_list[0][1]
                        it.descending.value = desc
                        it.f_fields_list.value = it.store_index_fields(field_list)
                        it.post()

    def update_item_idents(self, item_name, field_names, case):
        item = self.new_items[item_name]
        fields = []
        for field_name in field_names:
            fields.append(item.field_by_name(field_name))
        item.log_changes = False
        for it in item:
            it.edit()
            for field in fields:
                field.value = case(field.value)
            it.post()

    def update_idents(self):
        case = get_database(self.task.app, self.db_type, self.task.task_db_info.lib).identifier_case
        self.update_item_idents('sys_items', ['f_table_name', 'f_gen_name'], case)
        self.update_item_idents('sys_fields', ['f_db_field_name'], case)
        self.update_item_idents('sys_indices', ['f_index_name'], case)
        self.update_indexes()

    def prepare_data(self):
        if self.success:
            self.show_progress(self.task.language('import_reading_data'))
            try:
                self.tmpdir =  tempfile.mkdtemp()
                with zipfile.ZipFile(self.file_name) as z:
                    z.extractall(self.tmpdir)
                    file_name = os.path.join(self.tmpdir, 'task.dat')
                    data = file_read(file_name)
                    data_lists = json.loads(data)
                    for item_name in metadata_items:
                        item = self.task.item_by_name(item_name)
                        self.task.execute('DELETE FROM "%s" WHERE "DELETED" = 1' % item.table_name)
                        old_item = item.copy(handlers=False)
                        old_item.soft_delete = False
                        old_item.open(expanded=False)
                        field_names, dataset = self.get_dataset(old_item, data_lists)
                        new_item = item.copy(handlers=False)
                        new_item.open(expanded=False, fields=field_names, open_empty=True)
                        new_item._dataset = dataset
                        self.new_items[item.item_name] = new_item
                        self.old_items[item.item_name] = old_item
                    os.remove(file_name)
                    self.new_db_type = data_lists.get('db_type')
                    if self.new_db_type != self.db_type:
                        self.update_idents()
            except Exception as e:
                self.task.log.exception(e)
                self.success = False
                self.show_error(e)

    def get_dataset(self, item, data_lists):
        ns = []
        ds = []
        dl = data_lists.get(item.item_name)
        if dl:
            field_names = data_lists[item.item_name]['fields']
            dataset = data_lists[item.item_name]['records']
            for d in dataset:
                ds.append([])
            for i, f in enumerate(field_names):
                if item.field_by_name(f):
                    ns.append(f)
                    for j, d in enumerate(dataset):
                        ds[j].append(dataset[j][i])
        else:
            for f in item.fields:
                ns.append(f.field_name)
        return ns, ds

    def check_data_integrity(self):
        if self.success:
            self.show_progress(self.task.language('import_checking_integrity'))
            errors = []
            new = self.new_items['sys_items']
            old = self.old_items['sys_items']
            compare = self.compare_items(old, new)
            for it in old:
                o, n = compare[old.id.value]
                if o and n:
                    new.locate('id', old.id.value)
                    if old.type_id.value != new.type_id.value:
                        errors.append('Items with ID %s (%s, %s) have different type values' % \
                        (old.id.value, old.f_item_name.value, new.f_item_name.value))
                    elif old.f_table_name.value and old.f_table_name.value.upper() != new.f_table_name.value.upper():
                        errors.append('Items with ID %s (%s, %s) have different database tables (%s, %s)' % \
                        (old.id.value, old.f_item_name.value, new.f_item_name.value, old.f_table_name.value, new.f_table_name.value))
            if len(errors):
                self.error = "\n".join(errors)
                self.success = False
                self.show_error(self.error)

    def compare_items(self, old, new, owner_id=None):
        result = {}
        for it in old:
            result[it.id.value] = [True, False]
        for it in new:
            if not owner_id or owner_id == it.owner_rec_id.value:
                info = result.get(it.id.value)
                if info:
                    info[1] = True
                else:
                    result[it.id.value] = [False, True]
        return result

    def record_sql(self, d):
        pk = d._primary_key_field
        fields = []
        row = []
        if d.rec_inserted():
            values = []
            for field in d.fields:
                fields.append(field.db_field_name)
                values.append('?')
                row.append(field.data)
            sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                (d.table_name, ', '.join(fields), ', '.join(values))
            return (sql, row)
        elif d.rec_modified():
            for field in d.fields:
                fields.append('%s=?' % field.db_field_name)
                row.append(field.data)
            sql = 'UPDATE "%s" SET %s WHERE %s = %s' % \
                (d.table_name, ', '.join(fields), pk.db_field_name, pk.value)
            return (sql, row)
        elif d.rec_deleted():
            result = []
            sql = 'DELETE FROM %s WHERE %s = %s' % \
                (d.table_name, pk.db_field_name, pk.value)
            result.append((sql, None))
            for dt in d.details:
                sql = 'DELETE FROM %s WHERE %s = %s' % \
                    (dt.table_name, dt._master_rec_id_db_field_name, pk.value)
                result.append((sql, None))
            return result

    def admin_sql(self, delta):
        result = []
        for dl in delta:
            result.append(self.record_sql(dl))
            for dt in dl.details:
                for d in dt:
                    result.append(self.record_sql(d))
        return result

    def analize_data(self):
        if self.success:
            self.show_progress(self.task.language('import_analyzing'))
            try:
                task = self.task
                db_sql = []
                adm_sql = []
                deltas = {}

                delta = self.get_delta('sys_indices', options=['delete'])
                for d in delta:
                    table_name = self.get_table_name(d.owner_rec_id.value)
                    if table_name:
                        db_sql.append(indices_delete_query(d))
                adm_sql.append(self.admin_sql(delta))

                delta = self.get_delta('sys_items', 'sys_fields')
                self.check_generator(task.sys_items, delta)
                for d in delta:
                    if d.rec_inserted():
                        db_sql.append(insert_item_query(d, new_fields=self.get_new_fields(d.id.value)))
                    elif d.rec_modified():
                        db_sql.append(update_item_query(d))
                    elif d.rec_deleted():
                        db_sql.append(delete_item_query(d))

                self.refresh_old_item('sys_items')
                delta = self.get_delta('sys_items')
                self.check_generator(task.sys_items, delta)
                adm_sql.append(self.admin_sql(delta))

                self.refresh_old_item('sys_fields')
                delta = self.get_delta('sys_fields')
                adm_sql.append(self.admin_sql(delta))

                self.refresh_old_item('sys_indices')
                delta = self.get_delta('sys_indices', options=['update', 'insert'])
                for d in delta:
                    table_name = self.get_table_name(d.owner_rec_id.value)
                    if table_name:
                        if d.rec_inserted():
                            db_sql.append(indices_insert_query(
                                d, table_name,
                                self.get_new_fields(d.owner_rec_id.value),
                                foreign_key_dict=self.get_foreign_key_dict(d)
                                )
                            )
                        elif d.rec_deleted():
                            db_sql.append(indices_delete_query(d))
                adm_sql.append(self.admin_sql(delta))

                for item_name in ['sys_filters', 'sys_report_params', 'sys_roles', 'sys_params',
                    'sys_privileges', 'sys_field_privileges', 'sys_lookup_lists']:
                    delta = self.get_delta(item_name)
                    adm_sql.append(self.admin_sql(delta))

                self.db_sql = self.sqls_to_list(db_sql)
                self.adm_sql = self.sqls_to_list(adm_sql)
            except Exception as e:
                self.task.log.exception(e)
                self.success = False
                self.show_error(e)

    def get_table_name(self, item_id):
        items = self.new_items['sys_items']
        if items.locate('id', item_id):
            if not items.f_virtual_table.value or not items.f_copy_of.value:
                return items.f_table_name.value

    def get_foreign_key_dict(self, ind):
        dic = None
        if ind.f_foreign_index.value:
            dic = {}
            fields = self.new_items['sys_fields']
            fields.locate('id', ind.f_foreign_field.value)
            dic['key'] = fields.f_db_field_name.value
            ref_id = fields.f_object.value
            items = self.new_items['sys_items']
            items.locate('id', ref_id)
            dic['ref'] = items.f_table_name.value
            primary_key = items.f_primary_key.value
            fields.locate('id', primary_key)
            dic['primary_key'] = fields.f_db_field_name.value
        return dic

    def get_new_fields(self, item_id):
        result = []
        items = self.new_items['sys_items']
        items.locate('id', item_id)
        new_fields = self.new_items['sys_fields']
        for field in new_fields:
            if field.owner_rec_id.value == item_id:
                if not field.f_master_field.value:
                    result.append(FieldInfo(field, items))
        return result

    def can_copy_field(self, field):
        if field.owner.item_name == 'sys_params':
            if field.field_name in self.params_hidden_fields:
                return False
        if field.owner.item_name == 'sys_items':
            if field.field_name in self.items_hidden_fields:
                return False
        return True

    def copy_record(self, old, new):
        for old_field in old.fields:
            if self.can_copy_field(old_field):
                new_field = new.field_by_name(old_field.field_name)
                if new_field:
                    old_field.value = new_field.raw_value

    def update_item(self, item_name, detail_name=None,
        options=['update', 'insert', 'delete'], owner=None):

        new = self.new_items[item_name]
        if owner:
            old = owner.detail_by_name(item_name)
            old.open(expanded=False)
        else:
            old = self.old_items[item_name]
        owner_id = None
        if owner:
            owner_id = owner.id.value

        compare = self.compare_items(old, new, owner_id)

        if 'delete' in options:
            old.first()
            while not old.eof():
                if not owner_id or owner_id == old.owner_rec_id.value:
                    o, n = compare[old.id.value]
                    if o and not n:
                        old.delete()
                    else:
                        old.next()
                else:
                    old.next()

        if 'update' in options:
            new_ids = {}
            for it in new:
                new_ids[new.id.value] = new.rec_no
            for it in old:
                if not owner_id or owner_id == it.owner_rec_id.value:
                    o, n = compare[old.id.value]
                    if o and n:
                        rec = new_ids.get(old.id.value)
                        if rec is not None:
                            new.rec_no = rec
                            old.edit()
                            self.copy_record(old, new)
                            if detail_name:
                                self.update_item(detail_name, owner=old)
                            old.post()

        if 'insert' in options:
            for it in new:
                if not owner_id or owner_id == it.owner_rec_id.value:
                    o, n = compare[new.id.value]
                    if not o and n:
                        old.append()
                        self.copy_record(old, new)
                        if detail_name:
                            self.update_item(detail_name, owner=old)
                        old.post()

        return old

    def get_delta(self, item_name, detail_name=None, options=['update', 'insert', 'delete']):
        item = self.update_item(item_name, detail_name, options)
        return item.delta()

    def check_generator(self, item, delta):
        for d in delta:
            module = get_database(self.task.app, self.db_type, self.task.task_db_info.lib)
            if d.rec_inserted() and module.NEED_GENERATOR and \
                d.f_primary_key.value and not d.f_gen_name.value and \
                not d.f_virtual_table.value and not d.f_copy_of.value:
                case = module.identifier_case
                d.edit()
                #d.f_gen_name.value = case('%s_SEQ' % d.f_table_name.value)
                d.f_gen_name.value = case('%s_%s_SEQ' % (d.f_primary_key.value, d.f_table_name.value))
                d.post()

    def refresh_old_item(self, item_name):
        item = self.task.item_by_name(item_name).copy(handlers=False)
        item.open(expanded=False)
        self.old_items[item_name] = item

    def wait_ready(self):
        if self.success:
            if self.from_client:
                self.show_progress(self.task.language('import_waiting_close'))
                request_count = int(self.from_client)
                if consts.IMPORT_DELAY:
                    time.sleep(consts.IMPORT_DELAY)
                else:
                    while True:
                        i = 0
                        if self.task.app._busy > request_count:
                            time.sleep(0.1)
                            i += 1
                            if i > 3000:
                                break
                        else:
                            break

    def import_databases(self):
        if self.success:
            self.show_progress(self.task.language('import_changing_db'))
            connection = self.execute_ddl()
            try:
                if self.success:
                    admin_name = os.path.join(self.task.work_dir, 'admin.sqlite')
                    tmp_admin_name = os.path.join(self.task.work_dir, '_admin.sqlite')
                    if self.db.DDL_ROLLBACK:
                        shutil.copy2(admin_name, tmp_admin_name)
                    self.show_progress(self.task.language('import_changing_admin'))
                    self.error = self.execute_adm()
                    if self.error:
                        self.success = False
                    if self.db.DDL_ROLLBACK:
                        if self.success:
                            connection.commit()
                            os.remove(tmp_admin_name)
                        else:
                            os.rename(tmp_admin_name, admin_name)
                            connection.rollback()
            finally:
                if connection:
                    connection.close();
            consts.read_settings()
            consts.read_language()

    def execute_ddl(self):
        task = self.task
        info = []
        error = None
        connection = None
        try:
            connection = connect_task_db(task)
            if self.db_sql:
                cursor = connection.cursor()
                for sql in self.db_sql:
                    try:
                        cursor.execute(sql)
                    except Exception as x:
                        self.task.log.exception('Error: %s query: %s' % (x, sql))
                        error = error_message(x)
                    info.append({'sql': sql, 'error': error})
                    if error and self.db.DDL_ROLLBACK:
                        break
                if self.db.DDL_ROLLBACK:
                    if error:
                        self.success = False
                else:
                    connection.commit()
        except Exception as x:
            error = str(x)
            self.task.log.exception('Error: %s' % error)
            info.append({'error': error})
            self.success = False
        self.show_info(info)
        return connection

    def execute_adm(self):
        task = self.task
        info = []
        error = None
        connection = None
        try:
            connection = task.connect()
            if self.adm_sql:
                cursor = connection.cursor()
                for sql, params in self.adm_sql:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
            connection.commit()
        except Exception as x:
            error = str(x)
            self.task.log.exception('Error: %s' % error)
            info.append({'error': error})
            self.show_info(info)
        return error

    def sqls_to_list(self, sqls, result=None):
        if result is None:
            result = []
        for sql in sqls:
            if sql:
                if type(sql) == list:
                    self.sqls_to_list(sql, result)
                else:
                    result.append(sql)
        return result

    def update_logs(self):
        if self.success:
            result = self.task.language('import_success')
            if self.error:
                result = self.task.language('import_errors')
        else:
            result = self.task.language('import_failed')
        self.task.log.info(result)

        self.server_log = '%s\n\n%s' % (result.upper(), self.server_log)
        log_dir = os.path.join(self.task.work_dir, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_name = os.path.join(log_dir, 'import_%s.log' % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        file_write(log_file_name, self.server_log)

        if self.success:
            message = '<h3 class="text-center">%s</h3>' % result
        else:
            message = '<h3 class="text-center text-error">%s</h3>' % result
        self.client_log = '%s<h4 class="text-info">%s</h4><div>%s</div>' % \
            (message, self.task.language('import_log'), self.client_log)

    def copy_files(self):
        if self.success:
            self.show_progress(self.task.language('import_copying'))
            shutil.copytree(self.tmpdir, self.task.work_dir,
                copy_function=shutil.copyfile, dirs_exist_ok=True)

    def tidy_up(self):
        self.show_progress(self.task.language('import_deleteing_files'))
        try:
            if self.tmpdir and os.path.exists(self.tmpdir):
                shutil.rmtree(self.tmpdir)
            if self.success or self.from_client:
                os.remove(self.file_name)
        except Exception as e:
            self.task.log.exception(e)
            self.show_error(e)

    def show_progress(self, string):
        self.task.log.info(string)
        self.client_log += '<h5>' + string + '</h5>'
        self.server_log += '\n%s\n' % string

    def show_info(self, errors):
        for info in errors:
            sql = info.get('sql')
            error = info.get('error')
            if sql:
                self.task.log.info(sql)
                if error:
                    self.client_log += '<div class="text-error" style="margin-bottom: 10px; margin-left: 20px;">' + sql + '</div>'
                else:
                    self.client_log += '<div style="margin-bottom: 10px; margin-left: 20px;">' + sql + '</div>'
                self.server_log += '\n%s' % sql
            if error:
                self.show_error(error)

    def show_error(self, error):
        mess = self.format_error(error_message(error))
        self.client_log += '<div class="text-error" style="margin-left: 40px;">' + mess + '</div>'
        self.server_log += '\n%s' % error

    def format_error(self, error):
        try:
            arr = str(error).split('\n')
            lines = []
            for line in arr:
                line = line.replace('\t', ' ')
                spaces = 0
                for ch in line:
                    if ch == ' ':
                        spaces += 1
                    else:
                        break
                if spaces:
                    line = '<span style="white-space: pre; margin-left: %spx">%s</span>' % (10 * (spaces - 1), line)
                else:
                    line = '<span style="white-space: pre;">%s</span>' % line
                lines.append(line)
            result = '<br>'.join(lines)
            return '<div class="text-error">%s</div>' % result
        except:
            return error

    def project_empty(self):
        items = self.task.sys_items.copy(handlers=False)
        items.open(fields=['id', 'f_table_name'])
        for i in items:
            if i.f_table_name.value:
                return False
        return True
