import sys
import json
import traceback
import zlib
import base64

import jam.common as common
import jam.db.db_modules as db_modules
from jam.dataset import *
from werkzeug._compat import iteritems, text_type, string_types, to_bytes, to_unicode

class SQL(object):

    def get_next_id(self, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        sql = db_module.next_sequence_value_sql(self.gen_name)
        if sql:
            rec = self.task.select(sql)
            if rec:
                if rec[0][0]:
                    return int(rec[0][0])

    def insert_sql(self, db_module):
        info = {
            'gen_name': self.gen_name,
            'inserted': True
        }
        if self._deleted_flag:
            self._deleted_flag_field.set_data(0)
        row = []
        fields = []
        values = []
        index = 0
        pk = None
        if self._primary_key:
            pk = self._primary_key_field
        auto_pk = not db_module.get_lastrowid is None
        if auto_pk and pk and pk.raw_value:
            if hasattr(db_module, 'set_identity_insert'):
                info['before_command'] = db_module.set_identity_insert(self.table_name, True)
                info['after_command'] = db_module.set_identity_insert(self.table_name, False)
        for field in self.fields:
            if not (field.calculated or field.master_field or (field == pk and auto_pk and not pk.raw_value)):
                if field == pk:
                    info['pk_index'] = index
                elif self.master and field == self._master_rec_id_field:
                    info['master_pk_index'] = index
                index += 1
                fields.append('"%s"' % field.db_field_name)
                values.append('%s' % db_module.value_literal(index))
                value = (field.raw_value, field.data_type)
                row.append(value)

        fields = ', '.join(fields)
        values = ', '.join(values)
        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
            (self.table_name, fields, values)
        return sql, row, info

    def update_sql(self, db_module):
        row = []
        fields = []
        index = 0
        pk = self._primary_key_field
        command = 'UPDATE "%s" SET ' % self.table_name
        for field in self.fields:
            if not (field.calculated or field.master_field or field == pk):
                index += 1
                fields.append('"%s"=%s' % (field.db_field_name, db_module.value_literal(index)))
                value = (field.raw_value, field.data_type)
                if field.field_name == self._deleted_flag:
                    value = (0, field.data_type)
                row.append(value)
        fields = ', '.join(fields)
        if self._primary_key_field.data_type == common.TEXT:
            id_literal = "'%s'" % self._primary_key_field.value
        else:
            id_literal = "%s" % self._primary_key_field.value
        where = ' WHERE "%s" = %s' % (self._primary_key_db_field_name, id_literal)
        return ''.join([command, fields, where]), row

    def delete_sql(self, db_module):
        soft_delete = self.soft_delete
        if self.master:
            soft_delete = self.master.soft_delete
        if self._primary_key_field.data_type == common.TEXT:
            id_literal = "'%s'" % self._primary_key_field.value
        else:
            id_literal = "%s" % self._primary_key_field.value
        if soft_delete:
            sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                (self.table_name, self._deleted_flag_db_field_name,
                self._primary_key_db_field_name, id_literal)
        else:
            sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                (self.table_name, self._primary_key_db_field_name, id_literal)
        return sql

    def apply_sql(self, safe=False, db_module=None):

        def get_sql(item, safe, db_module):
            info = {}
            if item.master:
                if item._master_id:
                    item._master_id_field.set_data(item.master.ID)
                item._master_rec_id_field.set_data(item.master._primary_key_field.value)
            if item.record_status == common.RECORD_INSERTED:
                if safe and not self.can_create():
                    raise Exception(self.task.language('cant_create') % self.item_caption)
                sql, param, info = item.insert_sql(db_module)
            elif item.record_status == common.RECORD_MODIFIED:
                if safe and not self.can_edit():
                    raise Exception(self.task.language('cant_edit') % self.item_caption)
                sql, param = item.update_sql(db_module)
            elif item.record_status == common.RECORD_DETAILS_MODIFIED:
                sql, param = '', None
            elif item.record_status == common.RECORD_DELETED:
                if safe and not self.can_delete():
                    raise Exception(self.task.language('cant_delete') % self.item_caption)
                sql = item.delete_sql(db_module)
                param = None
            else:
                raise Exception('apply_sql - invalid %s record_status %s, record: %s' % \
                    (item.item_name, item.record_status, item._dataset[item.rec_no]))
            if item._primary_key:
                info['pk'] = item._primary_key_field.value
            info['ID'] = item.ID
            info['log_id'] = item.get_rec_info()[common.REC_CHANGE_ID]
            h_sql, h_params, h_del_details = get_history_sql(item, db_module)
            return sql, param, info, h_sql, h_params, h_del_details

        def delete_detail_sql(item, detail, db_module):
            h_sql = None
            h_params = None
            h_del_details = None
            if self._primary_key_field.data_type == common.TEXT:
                id_literal = "'%s'" % self._primary_key_field.value
            else:
                id_literal = "%s" % self._primary_key_field.value
            if detail._master_id:
                if item.soft_delete:
                    sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s AND "%s" = %s' % \
                        (detail.table_name, detail._deleted_flag_db_field_name, detail._master_id_db_field_name, \
                        item.ID, detail._master_rec_id_db_field_name, id_literal)
                else:
                    sql = 'DELETE FROM "%s" WHERE "%s" = %s AND "%s" = %s' % \
                        (detail.table_name, detail._master_id_db_field_name, item.ID, \
                        detail._master_rec_id_db_field_name, id_literal)
            else:
                if item.soft_delete:
                    sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                        (detail.table_name, detail._deleted_flag_db_field_name, \
                        detail._master_rec_id_db_field_name, id_literal)
                else:
                    sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                        (detail.table_name, detail._master_rec_id_db_field_name, id_literal)
                h_sql, h_params, h_del_details = get_history_sql(detail, db_module)
            return sql, None, None, h_sql, h_params, h_del_details

        def get_history_sql(item, db_module):
            h_sql = None
            h_params = None
            h_del_details = None
            if item.task.history_item and item.keep_history and item.record_status != common.RECORD_DETAILS_MODIFIED:
                deleted_flag = item.task.history_item._deleted_flag
                user_info = None
                if item.session:
                    user_info = item.session.get('user_info')
                #~ try:
                    #~ h_sql = item.task.__history_sql
                #~ except:
                h_fields = ['item_id', 'item_rec_id', 'operation', 'changes', 'user', 'date']
                table_name = item.task.history_item.table_name
                fields = []
                for f in h_fields:
                    fields.append(item.task.history_item._field_by_name(f).db_field_name)
                h_fields = fields
                index = 0
                fields = []
                values = []
                index = 0
                for f in h_fields:
                    index += 1
                    fields.append('"%s"' % f)
                    values.append('%s' % db_module.value_literal(index))
                fields = ', '.join(fields)
                values = ', '.join(values)
                h_sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                    (table_name, fields, values)
                #~ item.task.__history_sql = h_sql
                changes = None
                user = None
                item_id = item.ID
                if item.master:
                    item_id = item.prototype.ID
                if user_info:
                    try:
                        user = user_info['user_name']
                    except:
                        pass
                if item.record_status != common.RECORD_DELETED:
                    old_rec = item.get_rec_info()[3]
                    new_rec = item._dataset[item.rec_no]
                    f_list = []
                    for f in item.fields:
                        if not f.system_field():
                            new = new_rec[f.bind_index]
                            old = None
                            if old_rec:
                                old = old_rec[f.bind_index]
                            if old != new:
                                f_list.append([f.ID, new])
                    changes_str = json.dumps(f_list, separators=(',',':'), default=common.json_defaul_handler)
                    changes = ('%s%s' % ('0', changes_str), common.LONGTEXT)
                elif not item.master and item.details:
                    h_del_details = []
                    for detail in item.details:
                        if detail.keep_history:
                            d_select = 'SELECT "%s" FROM "%s" WHERE "%s" = %s AND "%s" = %s' % \
                                (detail._primary_key_db_field_name, detail.table_name,
                                detail._master_id_db_field_name, item.ID,
                                detail._master_rec_id_db_field_name, item._primary_key_field.value)
                            d_sql = h_sql
                            d_params = [detail.prototype.ID, None, common.RECORD_DELETED, None, user, datetime.datetime.now()]
                            h_del_details.append([d_select, d_sql, d_params])
                h_params = [item_id, item._primary_key_field.value, item.record_status, changes, user, datetime.datetime.now()]
            return h_sql, h_params, h_del_details

        def generate_sql(item, safe, db_module, result):
            ID, sql = result
            for it in item:
                details = []
                sql.append((get_sql(it, safe, db_module), details))
                for detail in item.details:
                    detail_sql = []
                    detail_result = (str(detail.ID), detail_sql)
                    details.append(detail_result)
                    if item.record_status == common.RECORD_DELETED:
                        detail_sql.append((delete_detail_sql(item, detail, db_module), []))
                    else:
                        generate_sql(detail, safe, db_module, detail_result)

        if db_module is None:
            db_module = self.task.db_module
        result = (self.ID, [])
        generate_sql(self, safe, db_module, result)
        return {'delta': result}

    def table_alias(self):
        return '"%s"' % self.table_name

    def lookup_table_alias(self, field):
        if field.master_field:
            return '%s_%d' % (field.lookup_item.table_name, field.master_field.ID)
        else:
            return '%s_%d' % (field.lookup_item.table_name, field.ID)

    def lookup_table_alias1(self, field):
        return self.lookup_table_alias(field) + '_' + field.lookup_db_field

    def lookup_table_alias2(self, field):
        return self.lookup_table_alias1(field) + '_' + field.lookup_db_field1

    def field_alias(self, field, db_module):
        return '%s_%s' % (field.db_field_name, db_module.identifier_case('LOOKUP'))

    def lookup_field_sql(self, field, db_module):
        if field.lookup_item:
            if field.lookup_field2:
                field_sql = '%s."%s"' % (self.lookup_table_alias2(field), field.lookup_db_field2)
            elif field.lookup_field1:
                field_sql = '%s."%s"' % (self.lookup_table_alias1(field), field.lookup_db_field1)
            else:
                if field.data_type == common.KEYS:
                    field_sql = 'NULL'
                else:
                    field_sql = '%s."%s"' % (self.lookup_table_alias(field), field.lookup_db_field)
            return field_sql

    def fields_clause(self, query, fields, db_module=None):
        summary = query.get('__summary')
        if db_module is None:
            db_module = self.task.db_module
        funcs = query.get('__funcs')
        if funcs:
            functions = {}
            for key, value in iteritems(funcs):
                functions[key.upper()] = value
        sql = []
        for i, field in enumerate(fields):
            if i == 0 and summary:
                sql.append(db_module.identifier_case('count(*)'))
            elif field.master_field:
                pass
            elif field.calculated:
                sql.append('NULL %s "%s"' % (db_module.FIELD_AS, field.db_field_name))
            else:
                field_sql = '%s."%s"' % (self.table_alias(), field.db_field_name)
                func = None
                if funcs:
                    func = functions.get(field.field_name.upper())
                if func:
                    field_sql = '%s(%s) %s "%s"' % (func.upper(), field_sql, db_module.FIELD_AS, field.db_field_name)
                sql.append(field_sql)
        if query['__expanded']:
            for i, field in enumerate(fields):
                if i == 0 and summary:
                    continue
                field_sql = self.lookup_field_sql(field, db_module)
                field_alias = self.field_alias(field, db_module)
                if field_sql:
                    if funcs:
                        func = functions.get(field.field_name.upper())
                    if func:
                        field_sql = '%s(%s) %s "%s"' % (func.upper(), field_sql, db_module.FIELD_AS, field_alias)
                    else:
                        field_sql = '%s %s %s' % (field_sql, db_module.FIELD_AS, field_alias)
                    sql.append(field_sql)
        sql = ', '.join(sql)
        return sql

    def from_clause(self, query, fields, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        result = []
        result.append(db_module.FROM % (self.table_name, self.table_alias()))
        if query['__expanded']:
            joins = {}
            for field in fields:
                if field.lookup_item and field.data_type != common.KEYS:
                    alias = self.lookup_table_alias(field)
                    cur_field = field
                    if field.master_field:
                        cur_field = field.master_field
                    if not joins.get(alias):
                        primary_key_field_name = field.lookup_item._primary_key_db_field_name
                        result.append('%s ON %s."%s" = %s."%s"' % (
                            db_module.LEFT_OUTER_JOIN % (field.lookup_item.table_name, self.lookup_table_alias(field)),
                            self.table_alias(),
                            cur_field.db_field_name,
                            self.lookup_table_alias(field),
                            primary_key_field_name
                        ))
                        joins[alias] = True
                if field.lookup_item1:
                    alias = self.lookup_table_alias1(field)
                    if not joins.get(alias):
                        primary_key_field_name = field.lookup_item1._primary_key_db_field_name
                        result.append('%s ON %s."%s" = %s."%s"' % (
                            db_module.LEFT_OUTER_JOIN % (field.lookup_item1.table_name, self.lookup_table_alias1(field)),
                            self.lookup_table_alias(field),
                            field.lookup_db_field,
                            self.lookup_table_alias1(field),
                            primary_key_field_name
                        ))
                        joins[alias] = True
                if field.lookup_item2:
                    alias = self.lookup_table_alias2(field)
                    if not joins.get(alias):
                        primary_key_field_name = field.lookup_item2._primary_key_db_field_name
                        result.append('%s ON %s."%s" = %s."%s"' % (
                            db_module.LEFT_OUTER_JOIN % (field.lookup_item2.table_name, self.lookup_table_alias2(field)),
                            self.lookup_table_alias1(field),
                            field.lookup_db_field1,
                            self.lookup_table_alias2(field),
                            primary_key_field_name
                        ))
                        joins[alias] = True
        return ' '.join(result)

    def _get_filter_sign(self, filter_type, value, db_module):
        result = common.FILTER_SIGN[filter_type]
        if filter_type == common.FILTER_ISNULL:
            if value:
                result = 'IS NULL'
            else:
                result = 'IS NOT NULL'
        if (result == 'LIKE'):
            result = db_module.LIKE
        return result

    def _convert_field_value(self, field, value, filter_type, db_module):
        data_type = field.data_type
        if filter_type and filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
            if data_type == common.FLOAT:
                value = common.str_to_float(value)
            elif data_type == common.CURRENCY:
                value = common.str_to_currency(value)
            if type(value) == float:
                if int(value) == value:
                    value = str(int(value)) + '.'
                else:
                    value = str(value)
            return value
        else:
            if data_type == common.DATE:
                if type(value) in string_types:
                    result = value
                else:
                    result = value.strftime('%Y-%m-%d')
                return db_module.cast_date(result)
            elif data_type == common.DATETIME:
                if type(value) in string_types:
                    result = value
                else:
                    result = value.strftime('%Y-%m-%d %H:%M')
                result = db_module.cast_datetime(result)
                return result
            elif data_type == common.INTEGER:
                if type(value) == int or type(value) in string_types and value.isdigit():
                    return str(value)
                else:
                    return "'" + value + "'"
            elif data_type == common.BOOLEAN:
                if value:
                    return '1'
                else:
                    return '0'
            elif data_type == common.TEXT:
                #~ return "'" + str(value) + "'"
                return "'" + to_unicode(value) + "'"
            elif data_type in (common.FLOAT, common.CURRENCY):
                return str(float(value))
            else:
                return value

    def _escape_search(self, value, esc_char):
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

    def _get_condition(self, field, filter_type, value, db_module):
        esc_char = '/'
        cond_field_name = '%s."%s"' % (self.table_alias(), field.db_field_name)
        if type(value) == str:
            value = to_unicode(value, 'utf-8')
        filter_sign = self._get_filter_sign(filter_type, value, db_module)
        cond_string = '%s %s %s'
        if filter_type in (common.FILTER_IN, common.FILTER_NOT_IN):
            values = [self._convert_field_value(field, v, filter_type, db_module) for v in value if v is not None]
            value = '(%s)' % ', '.join(values)
        elif filter_type == common.FILTER_RANGE:
            value = self._convert_field_value(field, value[0], filter_type, db_module) + \
                ' AND ' + self._convert_field_value(field, value[1], filter_type, db_module)
        elif filter_type == common.FILTER_ISNULL:
            value = ''
        else:
            value = self._convert_field_value(field, value, filter_type, db_module)
            if filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
                value, esc_found = self._escape_search(value, esc_char)
                if field.lookup_item:
                    if field.lookup_item1:
                        cond_field_name = '%s."%s"' % (self.lookup_table_alias1(field), field.lookup_db_field1)
                    else:
                        if field.data_type == common.KEYS:
                            cond_field_name = '%s."%s"' % (self.table_alias(), field.db_field_name)
                        else:
                            cond_field_name = '%s."%s"' % (self.lookup_table_alias(field), field.lookup_db_field)

                if filter_type == common.FILTER_CONTAINS:
                    value = '%' + value + '%'
                elif filter_type == common.FILTER_STARTWITH:
                    value = value + '%'
                elif filter_type == common.FILTER_ENDWITH:
                    value = '%' + value
                cond_field_name, value = db_module.convert_like(cond_field_name, value, field.data_type)
                if esc_found:
                    value = "'" + value + "' ESCAPE '" + esc_char + "'"
                else:
                    value = "'" + value + "'"
        sql = cond_string % (cond_field_name, filter_sign, value)
        if field.data_type == common.BOOLEAN and value == '0':
            if filter_sign == '=':
                sql = '(' + sql + ' OR %s IS NULL)' % cond_field_name
            elif filter_sign == '<>':
                sql = '(' + sql + ' AND %s IS NOT NULL)' % cond_field_name
            else:
                raise Exception('sql.py where_clause method: boolen field condition may give ambiguious results.')
        return sql

    def where_clause(self, query, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        conditions = []
        filters = query['__filters']
        deleted_in_filters = False
        if filters:
            for f in filters:
                field_name, filter_type, value = f
                if not value is None:
                    field = self._field_by_name(field_name)
                    if field_name == self._deleted_flag:
                        deleted_in_filters = True
                    if filter_type == common.FILTER_CONTAINS_ALL:
                        values = value.split()
                        for val in values:
                            conditions.append(self._get_condition(field, common.FILTER_CONTAINS, val, db_module))
                    elif filter_type in [common.FILTER_IN, common.FILTER_NOT_IN] and \
                        type(value) in [tuple, list] and len(value) == 0:
                        conditions.append('%s."%s" IN (NULL)' % (self.table_alias(), self._primary_key_db_field_name))
                    else:
                        conditions.append(self._get_condition(field, filter_type, value, db_module))
        if not deleted_in_filters and self._deleted_flag:
            conditions.append('%s."%s"=0' % (self.table_alias(), self._deleted_flag_db_field_name))
        result = ' AND '.join(conditions)
        if result:
            result = ' WHERE ' + result
        return result

    def group_clause(self, query, fields, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        group_fields = query.get('__group_by')
        funcs = query.get('__funcs')
        if funcs:
            functions = {}
            for key, value in iteritems(funcs):
                functions[key.upper()] = value
        result = ''
        if group_fields:
            for field_name in group_fields:
                field = self._field_by_name(field_name)
                if query['__expanded'] and field.lookup_item and field.data_type != common.KEYS:
                    func = functions.get(field.field_name.upper())
                    if func:
                        result += '%s."%s", ' % (self.table_alias(), field.db_field_name)
                    else:
                        result += '%s, %s."%s", ' % (self.lookup_field_sql(field, db_module), self.table_alias(), field.db_field_name)
                else:
                    result += '%s."%s", ' % (self.table_alias(), field.db_field_name)
            if result:
                result = result[:-2]
                result = ' GROUP BY ' + result
            return result
        else:
            return ''

    def order_clause(self, query, db_module=None):
        limit = query.get('__limit')
        if limit and not query.get('__order') and self._primary_key:
            query['__order'] = [[self._primary_key, False]]
        if query.get('__funcs') and not query.get('__group_by'):
            return ''
        funcs = query.get('__funcs')
        functions = {}
        if funcs:
            for key, value in iteritems(funcs):
                functions[key.upper()] = value
        if db_module is None:
            db_module = self.task.db_module
        order_list = query.get('__order', [])
        orders = []
        for order in order_list:
            field = self._field_by_name(order[0])
            if field:
                if not query['__expanded'] and field.lookup_item1:
                   orders = []
                   break
                if query['__expanded'] and field.lookup_item:
                    if field.data_type == common.KEYS:
                        ord_str = '%s."%s"' % (self.table_alias(), field.db_field_name)
                    else:
                        ord_str = self.lookup_field_sql(field, db_module)
                else:
                    func = functions.get(field.field_name.upper())
                    if func:
                        if db_module.DATABASE == 'MSSQL' and limit:
                            ord_str = '%s(%s."%s")' %  (func, self.table_alias(), field.db_field_name)
                        else:
                            ord_str = '"%s"' % field.db_field_name
                    else:
                        ord_str = '%s."%s"' % (self.table_alias(), field.db_field_name)
                if order[1]:
                    if hasattr(db_module, 'DESC'):
                        ord_str += ' ' + db_module.DESC
                    else:
                        ord_str += ' DESC'
                orders.append(ord_str)
        if orders:
             result = ' ORDER BY %s' % ', '.join(orders)
        else:
            result = ''
        return result

    def split_query(self, query):
        MAX_IN_LIST = 1000
        filters = query['__filters']
        filter_index = -1
        max_list = 0
        if filters:
            for i, f in enumerate(filters):
                field_name, filter_type, value = f
                if filter_type in [common.FILTER_IN, common.FILTER_NOT_IN]:
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

    def get_select_queries(self, query, db_module=None):
        result = []
        filter_in_info = self.split_query(query)
        if filter_in_info:
            filter_index, lists = filter_in_info
            for lst in lists:
                query['__limit'] = None
                query['__offset'] = None
                query['__filters'][filter_index][2] = lst
                result.append(self.get_select_query(query, db_module))
        else:
            result.append(self.get_select_query(query, db_module))
        return result

    def get_select_statement(self, query, db_module=None): # depricated
        return self.get_select_query(query, db_module)

    def get_select_query(self, query, db_module=None):
        try:
            if db_module is None:
                db_module = self.task.db_module
            field_list = query['__fields']
            if len(field_list):
                fields = [self._field_by_name(field_name) for field_name in field_list]
            else:
                fields = self._fields
            fields_clause = self.fields_clause(query, fields, db_module)
            from_clause = self.from_clause(query, fields, db_module)
            where_clause = self.where_clause(query, db_module)
            group_clause = self.group_clause(query, fields, db_module)
            order_clause = self.order_clause(query, db_module)
            sql = db_module.get_select(query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields)
            return sql
        except Exception as e:
            traceback.print_exc()
            raise

    def get_record_count_queries(self, query, db_module=None):
        result = []
        filter_in_info = self.split_query(query)
        if filter_in_info:
            filter_index, lists = filter_in_info
            for lst in lists:
                query['__filters'][filter_index][2] = lst
                result.append(self.get_record_count_query(query, db_module))
        else:
            result.append(self.get_record_count_query(query, db_module))
        return result

    def get_record_count_query(self, query, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        fields = []
        filters = query['__filters']
        if filters:
            for (field_name, filter_type, value) in filters:
                fields.append(self._field_by_name(field_name))
        sql = 'SELECT COUNT(*) FROM %s %s' % (self.from_clause(query, fields, db_module),
            self.where_clause(query, db_module))
        return sql

    def create_table_sql(self, db_type, table_name, fields=None, gen_name=None, foreign_fields=None):
        if not fields:
            fields = []
            for field in self.fields:
                if not (field.calculated or field.master_field):
                    dic = {}
                    dic['id'] = field.ID
                    dic['field_name'] = field.db_field_name
                    dic['data_type'] = field.data_type
                    dic['size'] = field.field_size
                    dic['default_value'] = ''#field.f_default_value.value
                    dic['primary_key'] = field.id.value == item.f_primary_key.value
                    fields.append(dic)
        result = []
        db_module = db_modules.get_db_module(db_type)
        result = db_module.create_table_sql(table_name, fields, gen_name, foreign_fields)
        for i, s in enumerate(result):
            print(result[i])
        return result

    def delete_table_sql(self, db_type):
        db_module = db_modules.get_db_module(db_type)
        gen_name = None
        if self.f_primary_key.value:
            gen_name = self.f_gen_name.value
        result = db_module.delete_table_sql(self.f_table_name.value, gen_name)
        for i, s in enumerate(result):
            print(result[i])
        return result

    def recreate_table_sql(self, db_type, old_fields, new_fields, fk_delta=None):

        def foreign_key_dict(ind):
            fields = ind.task.sys_fields.copy()
            fields.set_where(id=ind.f_foreign_field.value)
            fields.open()
            dic = {}
            dic['key'] = fields.f_db_field_name.value
            ref_id = fields.f_object.value
            items = self.task.sys_items.copy()
            items.set_where(id=ref_id)
            items.open()
            dic['ref'] = items.f_table_name.value
            primary_key = items.f_primary_key.value
            fields.set_where(id=primary_key)
            fields.open()
            dic['primary_key'] = fields.f_db_field_name.value
            return dic

        def get_foreign_fields():
            indices = self.task.sys_indices.copy()
            indices.filters.owner_rec_id.value = self.id.value
            indices.open()
            del_id = None
            if fk_delta and (fk_delta.rec_modified() or fk_delta.rec_deleted()):
                del_id = fk_delta.id.value
            result = []
            for ind in indices:
                if ind.f_foreign_index.value:
                    if not del_id or ind.id.value != del_id:
                        result.append(foreign_key_dict(ind))
            if fk_delta and (fk_delta.rec_inserted() or fk_delta.rec_modified()):
                result.append(foreign_key_dict(fk_delta))
            return result

        def create_indices_sql(db_type):
            indices = self.task.sys_indices.copy()
            indices.filters.owner_rec_id.value = self.id.value
            indices.open()
            result = []
            for ind in indices:
                if not ind.f_foreign_index.value:
                    result.append(ind.create_index_sql(db_type, self.f_table_name.value, new_fields=new_fields))
            return result

        def find_field(fields, id_value):
            found = False
            for f in fields:
                if f['id'] == id_value:
                    found = True
                    break
            return found

        def prepare_fields():
            for f in list(new_fields):
                if not find_field(old_fields, f['id']):
                    new_fields.remove(f)
            for f in list(old_fields):
                if not find_field(new_fields, f['id']):
                    old_fields.remove(f)

        table_name = self.f_table_name.value
        result = []
        result.append('PRAGMA foreign_keys=off')
        result.append('ALTER TABLE "%s" RENAME TO Temp' % table_name)
        foreign_fields = get_foreign_fields()
        create_sql = self.create_table_sql(db_type, table_name, new_fields, foreign_fields=foreign_fields)
        for sql in create_sql:
            result.append(sql)
        prepare_fields()
        old_field_list = ['"%s"' % field['field_name'] for field in old_fields]
        new_field_list = ['"%s"' % field['field_name'] for field in new_fields]
        result.append('INSERT INTO "%s" (%s) SELECT %s FROM Temp' % (table_name, ', '.join(new_field_list), ', '.join(old_field_list)))
        result.append('DROP TABLE Temp')
        result.append('PRAGMA foreign_keys=on')
        ind_sql = create_indices_sql(db_type)
        for sql in ind_sql:
            result.append(sql)
        return result

    def change_table_sql(self, db_type, old_fields, new_fields):

        def recreate(comp):
            for key, (old_field, new_field) in iteritems(comp):
                if old_field and new_field:
                    if old_field['field_name'] != new_field['field_name']:
                        return True
                    elif old_field['default_value'] != new_field['default_value']:
                        return True
                elif old_field and not new_field:
                    return True

        db_module = db_modules.get_db_module(db_type)
        table_name = self.f_table_name.value
        result = []
        comp = {}
        for field in old_fields:
            comp[field['id']] = [field, None]
        for field in new_fields:
            if comp.get(field['id']):
                comp[field['id']][1] = field
            else:
                if field['id']:
                    comp[field['id']] = [None, field]
                else:
                    comp[field['field_name']] = [None, field]
        if db_type == db_modules.SQLITE and recreate(comp):
            result += self.recreate_table_sql(db_type, old_fields, new_fields)
        else:
            for key, (old_field, new_field) in iteritems(comp):
                if old_field and not new_field and db_type != db_modules.SQLITE:
                    result.append(db_module.del_field_sql(table_name, old_field))
            for key, (old_field, new_field) in iteritems(comp):
                if old_field and new_field and db_type != db_modules.SQLITE:
                    if (old_field['field_name'] != new_field['field_name']) or \
                        (db_module.FIELD_TYPES[old_field['data_type']] != db_module.FIELD_TYPES[new_field['data_type']]) or \
                        (old_field['default_value'] != new_field['default_value']) or \
                        (old_field['size'] != new_field['size']):
                        sql = db_module.change_field_sql(table_name, old_field, new_field)
                        if type(sql) in (list, tuple):
                            result += sql
                        else:
                            result.append()
            for key, (old_field, new_field) in iteritems(comp):
                if not old_field and new_field:
                    result.append(db_module.add_field_sql(table_name, new_field))
        for i, s in enumerate(result):
            print(result[i])
        return result

    def create_index_sql(self, db_type, table_name, fields=None, new_fields=None, foreign_key_dict=None):

        def new_field_name_by_id(id_value):
            for f in new_fields:
                if f['id'] == id_value:
                    return f['field_name']

        db_module = db_modules.get_db_module(db_type)
        index_name = self.f_index_name.value
        if self.f_foreign_index.value:
            if foreign_key_dict:
                key = foreign_key_dict['key']
                ref = foreign_key_dict['ref']
                primary_key = foreign_key_dict['primary_key']
            else:
                fields = self.task.sys_fields.copy()
                fields.set_where(id=self.f_foreign_field.value)
                fields.open()
                key = fields.f_db_field_name.value
                ref_id = fields.f_object.value
                items = self.task.sys_items.copy()
                items.set_where(id=ref_id)
                items.open()
                ref = items.f_table_name.value
                primary_key = items.f_primary_key.value
                fields.set_where(id=primary_key)
                fields.open()
                primary_key = fields.f_db_field_name.value
            sql = db_module.create_foreign_index_sql(table_name, index_name, key, ref, primary_key)
        else:
            index_fields = self.f_fields_list.value
            desc = ''
            if self.descending.value:
                desc = 'DESC'
            unique = ''
            if self.f_unique_index.value:
                unique = 'UNIQUE'
            fields = common.load_index_fields(index_fields)
            if db_type == db_modules.FIREBIRD:
                if new_fields:
                    field_defs = [new_field_name_by_id(field[0]) for field in fields]
                else:
                    field_defs = [self.task.sys_fields.field_by_id(field[0], 'f_db_field_name') for field in fields]
                field_str = '"' + '", "'.join(field_defs) + '"'
            else:
                field_defs = []
                for field in fields:
                    if new_fields:
                        field_name = new_field_name_by_id(field[0])
                    else:
                        field_name = self.task.sys_fields.field_by_id(field[0], 'f_db_field_name')
                    d = ''
                    if field[1]:
                        d = 'DESC'
                    field_defs.append('"%s" %s' % (field_name, d))
                field_str = ', '.join(field_defs)
            sql = db_module.create_index_sql(index_name, table_name, unique, field_str, desc)
        #~ print(sql)
        return sql

    def delete_index_sql(self, db_type, table_name=None):
        db_module = db_modules.get_db_module(db_type)
        if not table_name:
            table_name = self.task.sys_items.field_by_id(self.owner_rec_id.value, 'f_table_name')
        index_name = self.f_index_name.value
        if self.f_foreign_index.value:
            sql = db_module.delete_foreign_index(table_name, index_name)
        else:
            sql = db_module.delete_index(table_name, index_name)
        #~ print(sql)
        return sql
