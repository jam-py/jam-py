import json
import datetime

from ..common import consts, error_message, json_defaul_handler
from ..common import to_bytes, to_str

class WhereCondition(object):
    def __init__(self, db):
        self.db = db
        self.queries = []
        self.params = []

    @property
    def next_literal(self):
        return self.db.value_literal(len(self.params) + 1)

    def add(self, query, param=None):
        self.queries.append(query)
        if not param is None:
            self.params.append(param)

    def add_or(self, query, param):
        self.queries.append(query)
        self.params += param

    @property
    def where_query(self):
        result = ' AND '.join(self.queries)
        if result:
            result = ' WHERE ' + result
        return result, self.params

    @property
    def or_query(self):
        result = ' OR '.join(self.queries)
        return '(%s)' % result, self.params


class AbstractDB(object):
    def __init__(self):
        self.db_type = None
        self.db_info = None
        self.DDL_ROLLBACK = False
        self.NEED_GENERATOR = False
        self.FROM = '"%s" AS %s'
        self.LIKE = 'LIKE'
        self.LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" AS %s'
        self.IS_DISTINCT_FROM = '%s IS DISTINCT FROM %s'
        self.FIELD_AS = 'AS'
        self.DESC_NULLS = None
        self.ASC_NULLS = None

    @property
    def params(self):
        return {
            'name': None,
            'dsn': False,
            'lib': [],
            'server': False,
            'database': True,
            'login': False,
            'password': False,
            'encoding': False,
            'host': False,
            'port': False,
            'ddl_rollback': self.DDL_ROLLBACK,
            'generator': self.NEED_GENERATOR,
            'import_support': True
        }
    @property
    def arg_params(self):
        return False

    def value_literal(self, index):
        return '?'

    def identifier_case(self, name):
        return name.upper()

    def convert_like(self, field_name, val, data_type):
        return 'UPPER(%s)' % field_name, val.upper()

    def next_sequence(self, table_name):
        pass

    def before_restart_sequence(self, gen_name):
        pass

    def restart_sequence(self, table_name, value):
        pass

    def process_query_params(self, params, cursor):
        result = []
        for p in params:
            if type(p) == tuple:
                value, data_type = p
            else:
                value = p
            result.append(value)
        return result

    def process_query_result(self, rows):
        return [list(row) for row in rows]

    def default_text(self, field_info):
        result = field_info.default_value
        if not result is None:
            if field_info.data_type in [consts.TEXT, consts.LONGTEXT, consts.FILE, consts.IMAGE]:
                if field_info.default_value:
                    result =  "'%s'" % result
                else:
                    result = None
            elif field_info.data_type == consts.BOOLEAN:
                if result == 'true':
                    result = '1'
                elif result == 'false':
                    result = '0'
                else:
                    result = None
            elif field_info.data_type in [consts.DATE, consts.DATETIME]:
                result = None
        return result

    def get_field_info(self, field_name, table_name, db_name=None):
        connection = self.connect(self.app.admin.task_db_info)
        try:
            fields_info = self.get_table_info(connection, table_name, db_name)
        finally:
            connection.close()
        for field in fields_info['fields']:
            if field['field_name'] == field_name:
                return field

    def before_insert(self, cursor, pk_field):
        pass

    def after_insert(self, cursor, pk_field):
        pass

    def returning(self, pk_field):
        return ''

    def insert_query(self, pk_field):
        return 'INSERT INTO "%s" (%s) VALUES (%s)'

    def db_field(self, field):
        if not field.master_field and not field.calculated:
            return True

    def insert_record(self, delta, cursor):
        if delta._deleted_flag:
            delta._deleted_flag_field.data = 0
        pk = delta._primary_key_field
        self.before_insert(cursor, pk)
        row = []
        fields = []
        values = []
        index = 0
        for field in delta.fields:
            if self.db_field(field) and not (field == pk and not pk.data):
                index += 1
                fields.append('"%s"' % field.db_field_name)
                values.append('%s' % self.value_literal(index))
                if field.data is None and not field.default_value is None:
                    field.data = field.get_default_value()
                value = (field.data, field.data_type)
                row.append(value)
        fields = ', '.join(fields)
        values = ', '.join(values)
        sql = self.insert_query(pk) % (delta.table_name, fields, values)
        row = self.process_query_params(row, cursor)
        delta.execute_query(cursor, sql, row, arg_params=self.arg_params)
        if pk:
            self.after_insert(cursor, pk)

    def check_record_version(self, delta, cursor):
        if delta.lock_active:
            if delta._record_version_field.value != delta._record_version_field.cur_value:
                raise Exception(consts.language('edit_record_modified'))
            if delta.change_log.record_status == consts.RECORD_DETAILS_MODIFIED:
                delta._record_version_field.value += 1
                delta.execute_query('UPDATE "%s" SET "%s"=COALESCE("%s", 0)+1 WHERE "%s"=%s' % \
                    (delta.table_name, delta._record_version_db_field_name,
                        delta._record_version_db_field_name, delta._primary_key_db_field_name,
                        delta._record_version_field.value))

    def update_record(self, delta, cursor):
        self.check_record_version(delta, cursor)
        row = []
        fields = []
        index = 0
        pk = delta._primary_key_field
        command = 'UPDATE "%s" SET ' % delta.table_name
        for field in delta.fields:
            prohibited, read_only = field.restrictions
            if self.db_field(field) and field != pk and not read_only:
                index += 1
                fields.append('"%s"=%s' % (field.db_field_name, self.value_literal(index)))
                if field.field_name == delta._record_version:
                    field.value += 1
                value = (field.data, field.data_type)
                if field.field_name == delta._deleted_flag:
                    value = (0, field.data_type)
                row.append(value)
        fields = ', '.join(fields)
        if delta._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % delta._primary_key_field.value
        else:
            id_literal = "%s" % delta._primary_key_field.value
        where = ' WHERE "%s" = %s' % (delta._primary_key_db_field_name, id_literal)
        sql = ''.join([command, fields, where])
        row = self.process_query_params(row, cursor)
        delta.execute_query(cursor, sql, row, arg_params=self.arg_params)

    def delete_record(self, delta, cursor):
        soft_delete = delta.soft_delete
        if delta.master:
            soft_delete = delta.owner.soft_delete
        if delta._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % delta._primary_key_field.value
        else:
            id_literal = "%s" % delta._primary_key_field.value
        if soft_delete:
            sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                (delta.table_name, delta._deleted_flag_db_field_name,
                delta._primary_key_db_field_name, id_literal)
        else:
            sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                (delta.table_name, delta._primary_key_db_field_name, id_literal)
        delta.execute_query(cursor, sql)

    def check_lookup_refs(self, delta, connection, cursor):
        if delta._lookup_refs:
            for item, fields in delta._lookup_refs.items():
                for field in fields:
                    copy = item.copy(filters=False, details=False, handlers=False)
                    field_name = field.field_name
                    copy.set_where({field_name: delta.id.value})
                    copy.set_fields([field.field_name])
                    copy.open(expanded=False, limit=1, connection=connection)
                    if copy.rec_count:
                        raise Exception(consts.language('cant_delete_used_record'))

    def get_user(self, delta):
        user = None
        if delta.session:
            try:
                user = delta.session.get('user_info')['user_name']
            except:
                pass
        return user

    def init_history(self, delta):
        if delta.task.history_item and delta.keep_history and delta.change_log.record_status != consts.RECORD_DETAILS_MODIFIED:
            delta.init_history()

    def save_history(self, delta, connection, cursor):
        if delta.task.history_item and delta.keep_history and delta.change_log.record_status != consts.RECORD_DETAILS_MODIFIED:
            changes = None
            user = self.get_user(delta)
            item_id = delta.ID
            if delta.master:
                item_id = delta.prototype.ID
            if delta.change_log.record_status != consts.RECORD_DELETED:
                f_list = []
                for f in delta.fields:
                    if self.db_field(f) and f.cur_data != f.data:
                        if not delta._record_version or f.field_name != delta._record_version:
                            f_list.append([f.ID, f.data])
                if f_list:
                    changes_str = json.dumps(f_list, separators=(',',':'), default=json_defaul_handler)
                    changes = ('%s%s' % ('0', changes_str), consts.LONGTEXT)
            if changes or delta.change_log.record_status == consts.RECORD_DELETED:
                params = [item_id, delta._primary_key_field.value, delta.change_log.record_status, changes, user, datetime.datetime.now()]
                params = self.process_query_params(params, cursor)
                delta.execute_query(cursor, delta.task.history_sql, params, arg_params=self.arg_params)

    def update_deleted_detail(self, delta, detail, cursor):
        fields = [detail._primary_key]
        detail.open(fields=fields, open_empty=True)
        if detail.master_field:
            sql = 'SELECT "%s" FROM "%s" WHERE "%s" = %s AND "%s" = 0' % \
                (detail._primary_key_db_field_name, detail.table_name,
                detail._master_field_db_field_name, delta._primary_key_field.value,
                detail._deleted_flag_db_field_name)
        else:
            sql = 'SELECT "%s" FROM "%s" WHERE "%s" = %s AND "%s" = %s AND "%s" = 0' % \
                (detail._primary_key_db_field_name, detail.table_name,
                detail._master_id_db_field_name, delta.ID,
                detail._master_rec_id_db_field_name, delta._primary_key_field.value,
                detail._deleted_flag_db_field_name)
        try:
            cursor.execute(sql)
            rows = self.process_query_result(cursor.fetchall())
        except Exception as x:
            delta.log.exception(error_message(x))
            raise Exception(x)
        detail._dataset = rows

    def delete_detail_records(self, delta, connection, cursor, detail):
        if delta._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % delta._primary_key_field.value
        else:
            id_literal = "%s" % delta._primary_key_field.value
        if detail._master_field:
            if delta.soft_delete:
                sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                    (detail.table_name, detail._deleted_flag_db_field_name, \
                    detail._master_field_db_field_name, id_literal)
            else:
                sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                    (detail.table_name, detail._master_field_db_field_name, id_literal)
        elif detail._master_id:
            if delta.soft_delete:
                sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s AND "%s" = %s' % \
                    (detail.table_name, detail._deleted_flag_db_field_name, detail._master_id_db_field_name, \
                    delta.ID, detail._master_rec_id_db_field_name, id_literal)
            else:
                sql = 'DELETE FROM "%s" WHERE "%s" = %s AND "%s" = %s' % \
                    (detail.table_name, detail._master_id_db_field_name, delta.ID, \
                    detail._master_rec_id_db_field_name, id_literal)
        elif detail._master_rec_id:
            if delta.soft_delete:
                sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                    (detail.table_name, detail._deleted_flag_db_field_name, \
                    detail._master_rec_id_db_field_name, id_literal)
            else:
                sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                    (detail.table_name, detail._master_rec_id_db_field_name, id_literal)
        if len(detail.details) or detail.keep_history:
            self.update_deleted_detail(delta, detail, cursor)
            if delta.task.history_item and detail.keep_history:
                for d in detail:
                    params = [detail.prototype.ID, d._primary_key_field.data,
                        consts.RECORD_DELETED, None, self.get_user(delta), datetime.datetime.now()]
                    delta.execute_query(cursor, delta.task.history_sql, \
                        self.process_query_params(params, cursor), arg_params=self.arg_params)
            if len(detail.details):
                for it in detail:
                    for d in detail.details:
                        self.delete_detail_records(detail, connection, cursor, d)
        delta.execute_query(cursor, sql)

    def process_record(self, delta, connection, cursor, safe):
        self.init_history(delta)
        if delta.master:
            if delta._master_field:
                delta._master_field_field.data = delta.master._primary_key_field.value
            elif delta._master_id:
                delta._master_id_field.data = delta.master.ID
                delta._master_rec_id_field.data = delta.master._primary_key_field.value
            elif delta._master_rec_id:
                delta._master_rec_id_field.data = delta.master._primary_key_field.value
        if delta.change_log.record_status == consts.RECORD_INSERTED:
            if safe and not delta.can_create():
                raise Exception(consts.language('cant_create') % delta.item_caption)
            self.insert_record(delta, cursor)
        elif delta.change_log.record_status == consts.RECORD_MODIFIED:
            if safe and not delta.can_edit():
                raise Exception(consts.language('cant_edit') % delta.item_caption)
            self.update_record(delta, cursor)
        elif delta.change_log.record_status == consts.RECORD_DETAILS_MODIFIED:
            self.check_record_version(delta, cursor)
        elif delta.change_log.record_status == consts.RECORD_DELETED:
            if safe and not delta.can_delete():
                raise Exception(consts.language('cant_delete') % delta.item_caption)
            self.check_lookup_refs(delta, connection, cursor)
            self.delete_record(delta, cursor)
        else:
            raise Exception('execute_delta - invalid %s record_status %s, record: %s' % \
                (delta.item_name, delta.change_log.record_status, delta._dataset[delta.rec_no]))
        self.save_history(delta, connection, cursor)

    def do_before_apply(self, delta, connection, params):
        item = delta._tree_item
        delta_params = item._get_delta_params(delta, params)
        if delta.task.on_before_apply_record:
            result = delta.task.on_before_apply_record(item, delta, delta_params, connection)
            if result == False:
                return result
        if item.on_before_apply_record:
            result = item.on_before_apply_record(item, delta, delta_params, connection)
            if result == False:
                return result

    def do_after_apply(self, delta, connection, params):
        item = delta._tree_item
        delta_params = item._get_delta_params(delta, params)
        if delta.task.on_after_apply_record:
            delta.task.on_after_apply_record(item, delta, delta_params, connection)
        if item.on_after_apply_record:
            item.on_after_apply_record(item, delta, delta_params, connection)

    def process_records(self, delta, connection, cursor, params, safe):
        for d in delta:
            res = self.do_before_apply(delta, connection, params)
            details = []
            if res != False and not d.virtual_table:
                self.process_record(d, connection, cursor, safe)
                for detail in d.details:
                    if d.change_log.record_status == consts.RECORD_DELETED:
                        self.delete_detail_records(d, connection, cursor, detail)
                    elif detail.master:
                        self.process_records(detail, connection, cursor, params, safe)
            self.do_after_apply(delta, connection, params)

    def process_changes(self, delta, connection, params=None):
        safe = delta.client_changes
        changes = []
        cursor = connection.cursor()
        self.process_records(delta, connection, cursor, params, safe)

    def table_alias(self, item):
        return '"%s"' % item.table_name

    def lookup_table_alias(self, item, field):
        if field.master_field:
            return '%s_%d' % (field.lookup_item.table_name, field.master_field.ID)
        else:
            return '%s_%d' % (field.lookup_item.table_name, field.ID)

    def lookup_table_alias1(self, item, field):
        return self.lookup_table_alias(item, field) + '_' + field.lookup_db_field

    def lookup_table_alias2(self, item, field):
        return self.lookup_table_alias1(item, field) + '_' + field.lookup_db_field1

    def field_alias(self, item, field):
        return '%s_%s' % (field.db_field_name, self.identifier_case('LOOKUP'))

    def lookup_field_sql(self, item, field):
        if field.lookup_item:
            if field.lookup_field2:
                field_sql = '%s."%s"' % (self.lookup_table_alias2(item, field), field.lookup_db_field2)
            elif field.lookup_field1:
                field_sql = '%s."%s"' % (self.lookup_table_alias1(item, field), field.lookup_db_field1)
            else:
                if field.lookup_field == field.lookup_item._primary_key:
                    field_sql = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                else:
                    field_sql = '%s."%s"' % (self.lookup_table_alias(item, field), field.lookup_db_field)
            return field_sql

    def calculated_sql(self, item, field):
        result = 'SELECT %s("%s") FROM "%s" WHERE %s.%s=%s' % \
            (field._calc_op, field._calc_field.db_field_name, field._calc_item.table_name,
            self.table_alias(item), field._calc_item._primary_key_db_field_name, field._calc_on_field.db_field_name)
        if field._calc_item._deleted_flag:
            result = '%s AND "%s"=0' % (result, field._calc_item._deleted_flag_db_field_name)
        result = '(%s) %s %s' % (result, self.FIELD_AS, self.identifier_case(field.field_name))
        return result

    def fields_clause(self, item, query, fields):
        summary = query.summary
        funcs = query.funcs
        if funcs:
            functions = {}
            for key, value in funcs.items():
                functions[key.upper()] = value
        sql = []
        for i, field in enumerate(fields):
            if query.client_request:
                prohibited, read_only = field.restrictions
                if prohibited:
                    print(field.field_name)
                    continue
            if i == 0 and summary:
                sql.append(self.identifier_case('count(*)'))
            elif field.master_field:
                pass
            elif field.calculated:
                pass
            else:
                field_sql = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                func = None
                if funcs:
                    func = functions.get(field.field_name.upper())
                    if func:
                        field_sql = '%s(%s) %s "%s"' % (func.upper(), field_sql, self.FIELD_AS, field.db_field_name)
                sql.append(field_sql)
        for i, field in enumerate(fields):
            if field.calculated:
                if query.expanded:
                    sql.append(self.calculated_sql(item, field))
        if query.expanded:
            for i, field in enumerate(fields):
                if i == 0 and summary:
                    continue
                field_sql = self.lookup_field_sql(item, field)
                field_alias = self.field_alias(item, field)
                if field_sql:
                    if funcs:
                        func = functions.get(field.field_name.upper())
                    if func:
                        field_sql = '%s(%s) %s "%s"' % (func.upper(), field_sql, self.FIELD_AS, field_alias)
                    else:
                        field_sql = '%s %s %s' % (field_sql, self.FIELD_AS, field_alias)
                    sql.append(field_sql)
        sql = ', '.join(sql)
        return sql

    def add_join(self, result, joins, item, field):
        alias = self.lookup_table_alias(item, field)
        cur_field = field
        if field.master_field:
            cur_field = field.master_field
        if not joins.get(alias):
            primary_key_field_name = field.lookup_item._primary_key_db_field_name
            result.append('%s ON %s."%s" = %s."%s"' % (
                self.LEFT_OUTER_JOIN % (field.lookup_item.table_name, self.lookup_table_alias(item, field)),
                self.table_alias(item),
                cur_field.db_field_name,
                self.lookup_table_alias(item, field),
                primary_key_field_name
            ))
            joins[alias] = True

    def add_join1(self, result, joins, item, field):
        alias = self.lookup_table_alias1(item, field)
        if not joins.get(alias):
            primary_key_field_name = field.lookup_item1._primary_key_db_field_name
            result.append('%s ON %s."%s" = %s."%s"' % (
                self.LEFT_OUTER_JOIN % (field.lookup_item1.table_name, self.lookup_table_alias1(item, field)),
                self.lookup_table_alias(item, field),
                field.lookup_db_field,
                self.lookup_table_alias1(item, field),
                primary_key_field_name
            ))
            joins[alias] = True

    def add_join2(self, result, joins, item, field):
        alias = self.lookup_table_alias2(item, field)
        if not joins.get(alias):
            primary_key_field_name = field.lookup_item2._primary_key_db_field_name
            result.append('%s ON %s."%s" = %s."%s"' % (
                self.LEFT_OUTER_JOIN % (field.lookup_item2.table_name, self.lookup_table_alias2(item, field)),
                self.lookup_table_alias1(item, field),
                field.lookup_db_field1,
                self.lookup_table_alias2(item, field),
                primary_key_field_name
            ))
            joins[alias] = True

    def from_clause(self, item, query, fields):
        result = []
        result.append(self.FROM % (item.table_name, self.table_alias(item)))
        fields = list(fields)
        filters = query.filters
        if filters:
            for f in filters:
                if type(f[0]) != list:
                    field_name, filter_type, value = f
                    if not value is None:
                        field = item._field_by_name(field_name)
                        if not field in fields:
                            fields.append(field)
        if query.expanded:
            joins = {}
            for field in fields:
                if field.lookup_item and field.data_type != consts.KEYS:
                    self.add_join(result, joins, item, field)
                if field.lookup_item1:
                    self.add_join1(result, joins, item, field)
                if field.lookup_item2:
                    self.add_join2(result, joins, item, field)
            filters = query.filters
        return ' '.join(result)

    def get_filter_sign(self, item, filter_type, value):
        result = consts.FILTER_SIGN[filter_type]
        if filter_type == consts.FILTER_ISNULL:
            if value:
                result = 'IS NULL'
            else:
                result = 'IS NOT NULL'
        if (result == 'LIKE'):
            result = self.LIKE
        return result

    def convert_field_value(self, field, value):
        data_type = field.data_type
        if isinstance(value, str):
            value = to_str(value)
        if data_type == consts.DATE:
            if isinstance(value, str):
                return datetime.datetime.strptime(value, '%Y-%m-%d')
        if data_type == consts.DATETIME:
            if isinstance(value, str):
                return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        if data_type == consts.BOOLEAN:
            if value:
                return '1'
            else:
                return '0'
        else:
            return value

    def escape_search(self, value, esc_char):
        result = ''
        found = False
        for ch in value:
            if ch == "'":
                ch = ch + ch
            elif ch in ['_', '%']:
                ch = esc_char + ch
                found = True
            result += ch
        return result, found

    def get_condition(self, item, conditions, field, filter_type, value):
        esc_char = '/'
        cond_field_name = '%s."%s"' % (self.table_alias(item), field.db_field_name)
        if filter_type > consts.FILTER_CONTAINS:
            if field.lookup_item:
                if field.lookup_item1:
                    cond_field_name = '%s."%s"' % (self.lookup_table_alias1(item, field), field.lookup_db_field1)
                else:
                    if field.data_type == consts.KEYS:
                        cond_field_name = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                    else:
                        cond_field_name = '%s."%s"' % (self.lookup_table_alias(item, field), field.lookup_db_field)
        if filter_type > consts.FILTER_CONTAINS_ALL:
            filter_type -= consts.FILTER_CONTAINS_ALL
        sql_literal = conditions.next_literal
        filter_sign = self.get_filter_sign(item, filter_type, value)
        if filter_type in (consts.FILTER_IN, consts.FILTER_NOT_IN):
            values = [to_str(v) for v in value if v is not None]
            sql_literal = '(%s)' % ', '.join(values)
            value = None
        elif filter_type == consts.FILTER_RANGE:
            param1 = self.convert_field_value(field, value[0])
            conditions.params.append(param1)
            sql_literal2 = conditions.next_literal
            param2 = self.convert_field_value(field, value[1])
            sql_literal = ' %s AND %s ' % (sql_literal, sql_literal2)
            value = param2
        elif filter_type == consts.FILTER_ISNULL:
            sql_literal = ''
            value = None
        elif filter_type in [consts.FILTER_CONTAINS, consts.FILTER_STARTWITH, consts.FILTER_ENDWITH]:
                value = self.convert_field_value(field, value)
                value, esc_found = self.escape_search(value, esc_char)
                if field.lookup_item:
                    if field.lookup_item1:
                        cond_field_name = '%s."%s"' % (self.lookup_table_alias1(item, field), field.lookup_db_field1)
                    else:
                        if field.data_type == consts.KEYS:
                            cond_field_name = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                        else:
                            cond_field_name = '%s."%s"' % (self.lookup_table_alias(item, field), field.lookup_db_field)
                if filter_type == consts.FILTER_CONTAINS:
                    value = '%' + value + '%'
                elif filter_type == consts.FILTER_STARTWITH:
                    value = value + '%'
                elif filter_type == consts.FILTER_ENDWITH:
                    value = '%' + value
                cond_field_name, value = self.convert_like(cond_field_name, value, field.data_type)
                if esc_found:
                    value = '' + value + "' ESCAPE '" + esc_char
                value = '%s' % value
        else:
            value = self.convert_field_value(field, value)
        sql = '%s %s %s' % (cond_field_name, filter_sign, sql_literal)
        if field.data_type == consts.BOOLEAN and value == 0 and filter_sign == '=':
            value = '1'
            sql = self.IS_DISTINCT_FROM % (cond_field_name, sql_literal)
        if filter_sign == '<>':
            sql = self.IS_DISTINCT_FROM % (cond_field_name, sql_literal)
        return sql, value

    def add_master_conditions(self, item, conditions, query):
        if query.master_field:
            conditions.add('%s."%s" = %s' % \
                (self.table_alias(item), item._master_field_db_field_name,
                conditions.next_literal), query.master_field)
        elif query.master_id:
            conditions.add('%s."%s" = %s' % \
                (self.table_alias(item), item._master_id_db_field_name,
                conditions.next_literal), query.master_id)
            conditions.add('%s."%s" = %s' % \
                (self.table_alias(item), item._master_rec_id_db_field_name,
                conditions.next_literal), query.master_rec_id)
        elif query.master_rec_id:
            conditions.add('%s."%s" = %s' % \
                (self.table_alias(item), item._master_rec_id_db_field_name,
                conditions.next_literal), query.master_rec_id)

    def where_clause(self, item, query, or_clause=False):
        conditions = WhereCondition(self)
        if or_clause:
            filters = query
        else:
            filters = query.filters
            if item.master:
                self.add_master_conditions(item, conditions, query)
        deleted_in_filters = False
        if filters:
            for f in filters:
                if type(f[0]) == list:
                    query, param = self.where_clause(item, f, True)
                    conditions.add_or(query, param)
                else:
                    field_name, filter_type, value = f
                    if not value is None:
                        field = item._field_by_name(field_name)
                        if field_name == item._deleted_flag:
                            deleted_in_filters = True
                        if filter_type == consts.FILTER_CONTAINS_ALL:
                            values = value.split()
                            for val in values:
                                query, param = self.get_condition(item, conditions, field, consts.FILTER_CONTAINS, val)
                                conditions.add(query, param)
                        elif filter_type in [consts.FILTER_IN, consts.FILTER_NOT_IN] and \
                            type(value) in [tuple, list] and len(value) == 0:
                            conditions.add('%s."%s" IN (NULL)' % (self.table_alias(item), item._primary_key_db_field_name))
                        else:
                            query, param = self.get_condition(item, conditions, field, filter_type, value)
                            conditions.add(query, param)
        if or_clause:
            return conditions.or_query
        else:
            if not deleted_in_filters and item._deleted_flag:
                conditions.add('%s."%s" = 0' % (self.table_alias(item), item._deleted_flag_db_field_name))
            return conditions.where_query

    def group_clause(self, item, query, fields):
        group_fields = query.group_by
        funcs = query.funcs
        if funcs:
            functions = {}
            for key, value in funcs.items():
                functions[key.upper()] = value
        result = ''
        if group_fields:
            for field_name in group_fields:
                field = item._field_by_name(field_name)
                use_lookup_field = (query.expanded and field.lookup_item and field.data_type != consts.KEYS)
                lookup_sql = self.lookup_field_sql(item, field)
                table_alias = self.table_alias(item)
                if use_lookup_field:
                    func = functions.get(field.field_name.upper())
                    if func:
                            result += '%s."%s", ' % (self.table_alias(item), field.db_field_name)
                    elif field.master_field:
                            result += '%s, ' % lookup_sql
                    elif field.lookup_field:
                        result += '%s, %s."%s", ' % (lookup_sql, table_alias, field.db_field_name)
                    else:
                            result += '%s, ' % lookup_sql
                else:
                    result += '%s."%s", ' % (table_alias, field.db_field_name)
            if result:
                result = result[:-2]
                result = ' GROUP BY ' + result
            return result
        else:
            return ''

    def order_clause(self, item, query):
        limit = query.limit
        if limit and not query.order and item._primary_key:
            query.order = [[item._primary_key, False]]
        if query.funcs and not query.group_by:
            return ''
        funcs = query.funcs
        functions = {}
        if funcs:
            for key, value in funcs.items():
                functions[key.upper()] = value
        order_list = query.order
        orders = []
        for order in order_list:
            field = item._field_by_name(order[0])
            if field:
                func = functions.get(field.field_name.upper())
                if not query.expanded and field.lookup_item1:
                   orders = []
                   break
                if query.expanded and field.lookup_item:
                    if field.data_type == consts.KEYS:
                        ord_str = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                    else:
                        if func:
                            ord_str = self.field_alias(item, field)
                        else:
                            ord_str = self.lookup_field_sql(item, field)
                elif field.calculated:
                    ord_str = self.identifier_case(field.field_name)
                else:
                    if func:
                        if self.db_type == consts.MSSQL and limit:
                            ord_str = '%s(%s."%s")' %  (func, self.table_alias(item), field.db_field_name)
                        else:
                            ord_str = '"%s"' % field.db_field_name
                    else:
                        ord_str = '%s."%s"' % (self.table_alias(item), field.db_field_name)
                if order[1]:
                    ord_str += ' DESC'
                    if self.DESC_NULLS:
                        ord_str += ' %s' % self.DESC_NULLS
                elif self.ASC_NULLS:
                    ord_str += ' ASC %s' % self.ASC_NULLS
                orders.append(ord_str)
        if orders:
             result = ' ORDER BY %s' % ', '.join(orders)
        else:
            result = ''
        return result

    def split_query(self, query):
        MAX_IN_LIST = 1000
        filters = query.filters
        filter_index = -1
        max_list = 0
        if filters:
            for i, f in enumerate(filters):
                if type(f[0]) != list: # not or filter
                    field_name, filter_type, value = f
                    if filter_type in [consts.FILTER_IN, consts.FILTER_NOT_IN]:
                        length = len(value)
                        if length > MAX_IN_LIST and length > max_list:
                            max_list = length
                            filter_index = i
        if filter_index != -1:
            lists = []
            value_list = filters[filter_index][2]
            while True:
                values = value_list[0:MAX_IN_LIST]
                if values:
                    lists.append(values)
                value_list = value_list[MAX_IN_LIST:]
                if not value_list:
                    break;
            return filter_index, lists

    def get_select_queries(self, item, query):
        result = []
        filter_in_info = self.split_query(query)
        if filter_in_info:
            filter_index, lists = filter_in_info
            for lst in lists:
                query.limit = None
                query.offset = None
                query.filters[filter_index][2] = lst
                result.append(self.get_select_query(item, query))
        else:
            result.append(self.get_select_query(item, query))
        return result

    def get_select_statement(self, item, query): # depricated
        return self.get_select_query(item, query)

    def get_select_query(self, item, query):
        try:
            field_list = query.fields
            if len(field_list):
                fields = [item._field_by_name(field_name) for field_name in field_list]
            else:
                fields = item._fields
            fields_clause = self.fields_clause(item, query, fields)
            from_clause = self.from_clause(item, query, fields)
            where_clause, params = self.where_clause(item, query)
            group_clause = self.group_clause(item, query, fields)
            order_clause = self.order_clause(item, query)
            sql = self.get_select(query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields)
            return sql, params
        except Exception as e:
            item.log.exception(error_message(e))
            raise

    def get_record_count_query(self, item, query):
        fields = []
        filters = query.filters
        if filters:
            for (field_name, filter_type, value) in filters:
                fields.append(item._field_by_name(field_name))
        where_sql, params = self.where_clause(item, query)
        sql = 'SELECT COUNT(*) FROM %s %s' % (self.from_clause(item, query, fields),
            where_sql)
        return sql, params

    def empty_table_query(self, item):
        return 'DELETE FROM %s' % item.table_name

