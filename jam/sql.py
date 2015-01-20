# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import cPickle

import common
from dataset import *

class SQL(object):

    def data_type_name(self, db_type, data_type):
        if db_type == common.POSTGRESQL:
            if data_type == common.INTEGER:
                return 'INTEGER'
            elif data_type == common.TEXT:
                return 'VARCHAR'
            elif data_type == common.FLOAT:
                return 'NUMERIC'
            elif data_type == common.CURRENCY:
                return 'NUMERIC'
            elif data_type == common.DATE:
                return 'DATE'
            elif data_type == common.DATETIME:
                return 'TIMESTAMP'
            elif data_type == common.BOOLEAN:
                return 'INTEGER'
            elif data_type == common.BLOB:
                return 'BYTEA'
        elif db_type == common.MYSQL:
            if data_type == common.INTEGER:
                return 'INT'
            elif data_type == common.TEXT:
                return 'VARCHAR'
            elif data_type == common.FLOAT:
                return 'DOUBLE'
            elif data_type == common.CURRENCY:
                return 'DOUBLE'
            elif data_type == common.DATE:
                return 'DATE'
            elif data_type == common.DATETIME:
                return 'DATETIME'
            elif data_type == common.BOOLEAN:
                return 'INT'
            elif data_type == common.BLOB:
                return 'BLOB'
        elif db_type == common.FIREBIRD:
            if data_type == common.INTEGER:
                return 'INTEGER'
            elif data_type == common.TEXT:
                return 'VARCHAR'
            elif data_type == common.FLOAT:
                return 'DOUBLE PRECISION'
            elif data_type == common.CURRENCY:
                return 'DOUBLE PRECISION'
            elif data_type == common.DATE:
                return 'DATE'
            elif data_type == common.DATETIME:
                return 'TIMESTAMP'
            elif data_type == common.BOOLEAN:
                return 'INTEGER'
            elif data_type == common.BLOB:
                return 'BLOB'
        elif db_type == common.SQLITE:
            if data_type == common.INTEGER:
                return 'INTEGER'
            elif data_type == common.TEXT:
                return 'TEXT'
            elif data_type == common.FLOAT:
                return 'REAL'
            elif data_type == common.CURRENCY:
                return 'REAL'
            elif data_type == common.DATE:
                return 'TEXT'
            elif data_type == common.DATETIME:
                return 'TEXT'
            elif data_type == common.BOOLEAN:
                return 'INTEGER'
            elif data_type == common.BLOB:
                return 'BLOB'

    def set_case(self, db_type, string):
        if db_type == common.POSTGRESQL:
            return string.lower()
        elif db_type == common.MYSQL:
            return string.upper()
        elif db_type == common.FIREBIRD:
            return string.upper()
        elif db_type == common.SQLITE:
            return string.upper()

    def param_literal(self, db_type):
        if db_type == common.POSTGRESQL:
            return '%s'
        elif db_type == common.MYSQL:
            return '%s'
        elif db_type == common.FIREBIRD:
            return '?'
        elif db_type == common.SQLITE:
            return '?'

    def quotes(self, db_type):
        if db_type == common.MYSQL:
            return '`'
        else:
            return '"'

    def get_gen_name(self, db_type=None):
        if db_type == common.POSTGRESQL:
            return '%s_id_seq' % self.table_name.lower()
        elif db_type == common.FIREBIRD:
            return '%s_GEN' % self.table_name.upper()

    def next_id_sql(self, db_type):
        result = None
        if db_type is None:
            db_type = self.task.db_type
        if db_type == common.POSTGRESQL:
            result = "select nextval('%s')" % self.get_gen_name(db_type)
        elif db_type == common.FIREBIRD:
            result = 'SELECT NEXT VALUE FOR "%s" FROM RDB$DATABASE' % self.get_gen_name(db_type)
        return result

    def change_id_sql(self, value, db_type):
        result = None
        if db_type is None:
            db_type = self.task.db_type
        if db_type == common.POSTGRESQL:
            result = 'ALTER SEQUENCE %s RESTART WITH %d' % (self.get_gen_name(db_type), value)
        elif db_type == common.FIREBIRD:
            result = 'ALTER SEQUENCE %s RESTART WITH %d' % (self.get_gen_name(db_type), value);
        return result

    def get_next_id(self, db_type=None):
        if self.on_get_next_id:
            return self.on_get_next_id(self)
        else:
            sql = self.next_id_sql(db_type)
            if sql:
                rec = self.task.execute_select_one(sql)
                if rec:
                    if rec[0]:
                        return int(rec[0])

    def insert_sql(self, db_type):
        self._records[self.rec_no][self.deleted.bind_index] = 0
        sql = 'INSERT INTO "%s" (' % self.table_name
        row = []
        fields = ''
        values = ''
        for field in self.fields:
            if not (field.calculated or field.master_field):
                fields += '"%s", ' % field.field_name
                values +=  '%s, ' % self.param_literal(db_type)
                row.append(field.raw_value)
        fields = fields[:-2]
        values = values[:-2]
        sql = self.set_case(db_type, 'INSERT INTO "%s" (%s) VALUES ' % (self.table_name, fields)) + '(' + values + ')'
        return sql, row

    def update_sql(self, db_type):
        row = []
        command = self.set_case(db_type, 'UPDATE "%s" SET ' % self.table_name)
        fields = ''
        for field in self.fields:
            if not (field.calculated or field.master_field):
                fields += '"%s"=%s, ' % (self.set_case(db_type, field.field_name), self.param_literal(db_type))
                value = field.get_raw_value()
                if field.field_name.lower() == 'deleted':
                    value = 0
                row.append(value)
        fields = fields[:-2]
        id_field_name = 'id'
        if self.id_field_name:
            id_field_name = self.id_field_name
            id_value = self._field_by_name(id_field_name).value
        else:
            id_field_name = 'id'
            id_value = self.id.value
        where = self.set_case(db_type, ' WHERE %s = %s' % (id_field_name, id_value))
        return command + fields + where, row

    def delete_sql(self, db_type):
        soft_delete = self.soft_delete
        if self.master:
            soft_delete = self.master.soft_delete
        if soft_delete:
            sql = 'UPDATE %s SET %s = 1 WHERE %s = %s' % (self.table_name, self.deleted.field_name, self.id.field_name, self.id.value)
        else:
            sql = 'DELETE FROM %s WHERE %s = %s' % (self.table_name, self.id.field_name, self.id.value)
        return self.set_case(db_type, sql)

    def apply_sql(self, priv=None, db_type=None):

        def get_sql(item, db_type):
            next_id_sql = ''
            change_id_sql = ''
            if item.master:
                item._records[item.rec_no][item.owner_id.bind_index] = item.owner.ID
                item._records[item.rec_no][item.owner_rec_id.bind_index] = item.owner.id.value
            if item.record_status == common.RECORD_INSERTED:
                if not item.master:
                    if priv and not priv['can_create']:
                        raise Exception, self.task.lang['cant_create'] % self.item_caption
                sql, param = item.insert_sql(db_type)
                if item.id.value:
                    change_id_sql = item.change_id_sql(item.id.value, db_type)
            elif item.record_status == common.RECORD_MODIFIED:
                if not item.master:
                    if priv and not priv['can_edit']:
                        raise Exception, self.task.lang['cant_edit'] % self.item_caption
                sql, param = item.update_sql(db_type)
            elif item.record_status == common.RECORD_DETAILS_MODIFIED:
                sql, param = '', None
            elif item.record_status == common.RECORD_DELETED:
                if not item.master:
                    if priv and not priv['can_delete']:
                        raise Exception, self.task.lang['cant_delete'] % self.item_caption
                sql = item.delete_sql(db_type)
                param = None
            else:
                raise Exception, u'apply_sql - invalid %s record_status %s, record: %s' % (item.item_name, item.record_status, item._records[item.rec_no])
            if item.master:
                owner_rec_id_index = item.fields.index(item.owner_rec_id)
            else:
                owner_rec_id_index = 0
            id_index = item.fields.index(item.id)
#            if not item.id.value:
            next_id_sql = item.next_id_sql(db_type)
            info = {'ID': item.ID,
                'status': item.record_status,
                'id': item.id.value,
                'id_index': id_index,
                'next_id_sql': next_id_sql,
                'change_id_sql': change_id_sql,
                'log_id': item.get_rec_info()[common.REC_CHANGE_ID],
                'owner_rec_id_index': owner_rec_id_index}
            return sql, param, info

        def delete_detail_sql(item, detail, db_type):
            if item.soft_delete:
                sql = 'UPDATE %s SET DELETED = 1 WHERE OWNER_ID = %s AND OWNER_REC_ID = %s' % (detail.table_name, item.ID, item.id.value)
            else:
                sql = 'DELETE FROM %s WHERE OWNER_ID = %s AND OWNER_REC_ID = %s' % (detail.table_name, item.ID, item.id.value)
            return self.set_case(db_type, sql), None, None

        def generate_sql(item, db_type, result):
            ID, sql = result
            for it in item:
                details = []
                sql.append((get_sql(it, db_type), details))
                for detail in item.details:
                    detail_sql = []
                    detail_result = (str(detail.ID), detail_sql)
                    details.append(detail_result)
                    if item.record_status == common.RECORD_DELETED:
                        detail_sql.append((delete_detail_sql(item, detail, db_type), []));
                    else:
                        generate_sql(detail, db_type, detail_result)

        if db_type is None:
            db_type = self.task.db_type
        result = (self.ID, [])
        generate_sql(self, db_type, result)
        return {'delta': result}


    def ref_table_alias(self, field):
        if field.master_field:
            return field.lookup_item.table_name + str(self._fields.index(field.master_field))
        else:
            return field.lookup_item.table_name + str(self._fields.index(field))

    def fields_clause(self, query, fields, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        sql = ''
        for field in fields:
            if field.master_field:
                pass
            elif field.calculated:
                sql += 'NULL AS "%s", ' % field.field_name
            else:
                sql += '"%s"."%s", ' % (self.table_name, field.field_name)
        if query['__expanded']:
            for field in fields:
                if field.lookup_item:
                    sql += '"%s"."%s" AS "%s_LOOKUP", ' % (self.ref_table_alias(field), field.lookup_field, field.field_name)
        sql = sql[:-2]
        return self.set_case(db_type, sql)

    def from_clause(self, query, fields, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        result = '"%s"' % self.table_name
        if query['__expanded']:
            for field in fields:
                if field.lookup_item and not field.master_field:
                    if field.lookup_item.id_field_name:
                        id_field_name = field.lookup_item.id_field_name
                    else:
                        id_field_name = 'id'
                    result = '(' + result
                    if db_type == common.SQLITE:
                        result += ' OUTER LEFT JOIN "%s" AS "%s"' % (field.lookup_item.table_name, self.ref_table_alias(field))
                    elif db_type in [common.POSTGRESQL, common.MYSQL, common.FIREBIRD]:
                        result += ' LEFT OUTER JOIN  "%s" AS "%s"' % (field.lookup_item.table_name, self.ref_table_alias(field))
                    result += ' ON "%s"."%s"' % (self.table_name, field.field_name)
                    result += ' = "%s"."%s")'  % (self.ref_table_alias(field), id_field_name)
        return self.set_case(db_type, result)

    def where_clause(self, query, db_type=None):

        def get_filter_sign(filter_type, value=None):
            result = common.FILTER_SIGN[filter_type]
            if filter_type == common.FILTER_ISNULL:
                if value:
                    result = 'IS NULL'
                else:
                    result = 'IS NOT NULL'
            if (result == 'LIKE') and (db_type == common.POSTGRESQL):
                result = 'ILIKE'
            return result

        def convert_field_value(field, value, filter_type=None):
            data_type = field.data_type
            if data_type == common.DATE:
                if type(value) in (str, unicode):
                    return "'" + value + "'"
                else:
                    return "'" + value.strftime('%Y-%m-%d') + "'"
            elif data_type == common.DATETIME:
                if type(value) in (str, unicode):
                    result = value
                else:
                    result = value.strftime('%Y-%m-%d %H:%M')
                result = "cast('" + result + "' AS TIMESTAMP)"
                return result
            elif data_type == common.INTEGER:
                if type(value) == int or value.isdigit():
                    return str(value)
                else:
                    if filter_type and filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
                        return value
                    else:
                        return "'" + value + "'"
            elif data_type == common.BOOLEAN:
                if value:
                    return '1'
                else:
                    return '0'
            elif data_type == common.TEXT:
                if filter_type and filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
                    return value
                else:
                    return "'" + value + "'"
            elif data_type in (common.FLOAT, common.CURRENCY):
                value = float(value)
                return str(value)
            else:
                return value

        def escape_search(value, esc_char):
            result = ''
            for ch in value:
                if ch == "'":
                    ch = ch + ch
                elif ch in ['_', '%']:
                    ch = esc_char + ch
                result += ch
            return result

        def get_condition(field_name, filter_type, value):
            field = self._field_by_name(field_name)
            esc_char = ' '
            cond_field_name = self.set_case(db_type, '"%s"."%s"' % (self.table_name, field_name))
            if type(value) == str:
                value = value.decode('utf-8')
            filter_sign = get_filter_sign(filter_type, value)
            cond_string = '%s %s %s'
            if filter_type in (common.FILTER_IN, common.FILTER_NOT_IN):
                lst = '('
                for it in value:
                    lst += convert_field_value(field, it) + ', '
                value = lst[:-2] + ')'
            elif filter_type == common.FILTER_ISNULL:
                value = ''
            else:
                value = convert_field_value(field, value, filter_type)
                if filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
                    value = escape_search(value, esc_char)
                    if field.lookup_item:
                        cond_field_name = self.set_case(db_type, '"%s"."%s"' % (self.ref_table_alias(field), field.lookup_field))
                    if filter_type == common.FILTER_CONTAINS:
                        value = '%' + value + '%'
                    elif filter_type == common.FILTER_STARTWITH:
                        value = value + '%'
                    elif filter_type == common.FILTER_ENDWITH:
                        value = '%' + value
                    if db_type == common.FIREBIRD:
                        cond_string = 'UPPER(%s) %s %s'
                        value = value.upper()
                    value = "'" + value + "' ESCAPE '" + esc_char + "'"
            sql = cond_string % (cond_field_name, filter_sign, value)
            if field.data_type == common.BOOLEAN and value == '0':
                if filter_sign == '=':
                    sql = '(' + sql + ' OR %s IS NULL)' % cond_field_name
                elif filter_sign == '<>':
                    sql = '(' + sql + ' AND %s IS NOT NULL)' % cond_field_name
                else:
                    raise Exception, 'sql.py where_clause method: boolen field condition may give ambiguious results.'
            return sql

        if db_type is None:
            db_type = self.task.db_type
        result = ''
        conditions = []
        filters = query['__filters']
        deleted_in_filters = False
        if filters:
            for (field_name, filter_type, value) in filters:
                if not value is None:
                    if field_name == 'deleted':
                        deleted_in_filters = True
                    if filter_type == common.FILTER_SEARCH:
                        values = value.split()
                        for val in values:
                            conditions.append(get_condition(field_name, common.FILTER_CONTAINS, val))
                    else:
                        conditions.append(get_condition(field_name, filter_type, value))
        if not deleted_in_filters:
            conditions.append(self.set_case(db_type, '"%s"."deleted"=0' % self.table_name))
        for sql in conditions:
            result += sql + ' AND '
        result = result[:-5]
        if result:
            result = ' WHERE ' + result
        return result

    def order_clause(self, query, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        result = ''
        order_list = query.get('__order')
        if order_list:
            order_list = query['__order']
        else:
            order_list = self._order_by
        for order in order_list:
            field = self._field_by_ID(order[0])
            if field:
                if query['__expanded'] and field.lookup_item:
                    result += '"%s_LOOKUP"' % field.field_name
                else:
                    result += '"%s"."%s"' % (self.table_name, field.field_name)
                if order[1]:
                    result += ' DESC'
                result += ', '
        if result:
            result = result[:-2]
            result = ' ORDER BY ' + result
        return self.set_case(db_type, result)

    def limit_clause_end(self, query, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        if (db_type == common.SQLITE) and query['__limit']:
            result = ' LIMIT %d, %d' % (query['__loaded'], query['__limit'])
        elif (db_type == common.POSTGRESQL or db_type == common.MYSQL) and query['__limit']:
            result = ' LIMIT %d OFFSET %d' % (query['__limit'], query['__loaded'])
        else:
            result = ''
        return self.set_case(db_type, result)

    def limit_clause_start(self, query, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        if (db_type == common.FIREBIRD) and query['__limit']:
            result = 'FIRST %d SKIP %d ' % (query['__limit'], query['__loaded'])
        else:
            result = ''
        return self.set_case(db_type, result)

    def get_select_statement(self, query, db_type=None):

        if db_type is None:
            db_type = self.task.db_type
        field_list = query['__fields']
        if len(field_list):
            fields = [self._field_by_name(field_name) for field_name in field_list]
        else:
            fields = self._fields
        sql = 'SELECT ' + \
            self.limit_clause_start(query, db_type) + \
            self.fields_clause(query, fields, db_type) + \
            ' FROM ' + \
            self.from_clause(query, fields, db_type) + \
            self.where_clause(query, db_type) + \
            self.order_clause(query, db_type) + \
            self.limit_clause_end(query, db_type)
        return sql

    def get_record_count_query(self, query, db_type=None):
        if db_type is None:
            db_type = self.task.db_type
        fields = []
        filters = query['__filters']
        if filters:
            for (field_name, filter_type, value) in filters:
                fields.append(self._field_by_name(field_name))
        sql = 'SELECT COUNT(*) FROM %s %s' % (self.from_clause(query, fields, db_type),
            self.where_clause(query, db_type));
        return sql

    def create_table_sql(self, db_type, table_name, fields=None, foreign_fields=None):
        if not fields:
            fields = []
            for field in self.fields:
                if not (field.calculated or field.master_field):
                    dic = {}
                    dic['id'] = field.ID
                    dic['field_name'] = field.field_name
                    dic['data_type'] = field.data_type
                    dic['size'] = field.field_size
                    fields.append(dic)
        result = []
        if db_type == common.POSTGRESQL:
            seq_name = '%s_id_seq' % table_name
            result.append('CREATE SEQUENCE "%s"' % seq_name)
            sql = 'CREATE TABLE "%s"\n(\n' % table_name
            for field in fields:
                if field['field_name'].lower() == 'id':
                    sql += '"ID" %s PRIMARY KEY DEFAULT nextval(\'"%s"\')' % \
                    (self.data_type_name(db_type, field['data_type']),
                    seq_name)
                else:
                    sql += '"%s" %s' % (field['field_name'], self.data_type_name(db_type, field['data_type']))
                if field['size'] != 0 and field['data_type'] == common.TEXT:
                    sql += '(%d)' % field['size']
                sql +=  ',\n'
            sql = sql[:-2]
            sql += ')\n'
            result.append(sql)
            result.append('ALTER SEQUENCE "%s" OWNED BY "%s"."ID"' % (seq_name, table_name))
        elif db_type == common.MYSQL:
            sql = 'CREATE TABLE `%s`\n(\n' % table_name
            for field in fields:
                sql += '`%s` %s' % (field['field_name'], self.data_type_name(db_type, field['data_type']))
                if field['size'] != 0 and field['data_type'] == common.TEXT:
                    sql += '(%d)' % field['size']
                if field['field_name'].upper() == u'ID':
                    sql += ' NOT NULL AUTO_INCREMENT'
                sql +=  ',\n'
            sql += "PRIMARY KEY(`ID`)"
            sql += ')\n'
            result.append(sql)
        elif db_type == common.FIREBIRD:
            sql = 'CREATE TABLE "%s"\n(\n' % table_name
            for field in fields:
                sql += '"%s" %s' % (field['field_name'], self.data_type_name(db_type, field['data_type']))
                if field['size'] != 0 and field['data_type'] == common.TEXT:
                    sql += '(%d)' % field['size']
                sql +=  ',\n'
            sql += 'CONSTRAINT %s_PR_INDEX PRIMARY KEY ("ID")\n' % table_name
            sql += ')\n'
            result.append(sql)
            result.append('CREATE SEQUENCE "%s_GEN"' % table_name)
        elif db_type == common.SQLITE:
            sql = 'CREATE TABLE "%s"\n(\n' % table_name
            for field in fields:
                sql += '"%s" %s' % (field['field_name'], self.data_type_name(db_type, field['data_type']))
                if field['field_name'].upper() == u'ID':
                    sql += ' PRIMARY KEY'
                sql +=  ',\n'
            if foreign_fields:
                for field in foreign_fields:
                    sql += 'FOREIGN KEY(%s) REFERENCES %s(ID),\n' % (field['key'], field['ref'])
            sql = sql[:-2]
            sql += ')\n'
            result.append(sql)
        for i, s in enumerate(result):
            result[i] = self.set_case(db_type, s)
        return result

    def delete_table_sql(self, db_type):
        table_name = self.f_table_name.value
        result = []
        result.append('DROP TABLE "%s"' % table_name)
        if db_type == common.FIREBIRD:
            result.append('DROP SEQUENCE "%s_GEN"' % table_name)
        for i, s in enumerate(result):
            result[i] = self.set_case(db_type, s)
        return result

    def recreate_table_sql(self, db_type, old_fields, new_fields, fk_delta=None):

        def foreign_key_dict(ind):
            dic = {}
            dic['key'] = ind.f_foreign_field.display_text
            ref_id = self.task.sys_fields.field_by_id(ind.f_foreign_field.value, 'f_object')
            dic['ref'] = self.task.sys_items.field_by_id(ref_id, 'f_table_name')
            return dic

        def get_foreign_fields():
            indices = self.task.sys_indices.copy()
            indices.filters.owner_rec_id.value = self.id.value
            indices.open()
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
        result.append('ALTER TABLE "%s" RENAME TO Temp' % table_name)
        foreign_fields = get_foreign_fields()
        create_sql = self.create_table_sql(db_type, table_name, new_fields, foreign_fields)
        for sql in create_sql:
            result.append(sql)
        prepare_fields()
        old_field_list = ['"%s"' % field['field_name'] for field in old_fields]
        new_field_list = ['"%s"' % field['field_name'] for field in new_fields]
        result.append('INSERT INTO "%s" (%s) SELECT %s FROM Temp' % (table_name, ', '.join(new_field_list), ', '.join(old_field_list)))
        result.append('DROP TABLE Temp')
        ind_sql = create_indices_sql(db_type)
        for sql in ind_sql:
            result.append(sql)
        return result

    def change_table_sql(self, db_type, old_fields, new_fields):

        def add_field_sql(db_type, table_name, field):
            if db_type == common.POSTGRESQL:
                result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s'
            elif db_type == common.FIREBIRD:
                result = 'ALTER TABLE "%s" ADD "%s" %s'
            elif db_type == common.SQLITE:
                result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s'
            result = result % (table_name.upper(), field['field_name'].upper(), self.data_type_name(db_type, field['data_type']))
            if db_type in (common.FIREBIRD, common.POSTGRESQL) and field['size']:
                result += '(%d)' % field['size']
            return result

        def del_field_sql(db_type, table_name, field):
            if db_type == common.POSTGRESQL:
                result = 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name.upper(), field['field_name'].upper())
            elif db_type == common.FIREBIRD:
                result = 'ALTER TABLE "%s" DROP "%s"' % (table_name.upper(), field['field_name'].upper())
            return result

        def change_field_sql(db_type, table_name, old_field, new_field):
            if db_type == common.POSTGRESQL:
                if self.data_type_name(db_type, old_field['data_type']) != self.data_type_name(db_type, new_field['data_type']) \
                    or old_field['size'] != new_field['size']:
                    raise Exception, u"Don't know how to change field's size or type"
                result = 'ALTER TABLE "%s" RENAME COLUMN  "%s" TO "%s"' % (table_name.upper(), old_field['field_name'].upper(), new_field['field_name'].upper())
            if db_type == common.FIREBIRD:
                if self.data_type_name(db_type, old_field['data_type']) != self.data_type_name(db_type, new_field['data_type']) \
                    or old_field['size'] != new_field['size']:
                    raise Exception, u"Don't know how to change field's size or type %s" % old_field['field_name']
                result = 'ALTER TABLE "%s" ALTER "%s" TO "%s"' % (table_name.upper(), old_field['field_name'].upper(), new_field['field_name'].upper())
            return result

        def recreate(comp):
            for key, (old_field, new_field) in comp.items():
                if old_field and new_field:
                    if old_field['field_name'] != new_field['field_name']:
                        return True
                elif old_field and not new_field:
                    return True

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
        if db_type == common.SQLITE and recreate(comp):
            result += self.recreate_table_sql(db_type, old_fields, new_fields)
        else:
            for key, (old_field, new_field) in comp.items():
                if old_field and not new_field and db_type != common.SQLITE:
                    result.append(del_field_sql(db_type, table_name, old_field))
            for key, (old_field, new_field) in comp.items():
                if old_field and new_field and db_type != common.SQLITE:
                    if (old_field['field_name'] != new_field['field_name']) or \
                        (self.data_type_name(db_type, old_field['data_type']) != self.data_type_name(db_type, new_field['data_type'])) or \
                        (old_field['size'] != new_field['size']):
                        result.append(change_field_sql(db_type, table_name, old_field, new_field))
            for key, (old_field, new_field) in comp.items():
                if not old_field and new_field:
                    result.append(add_field_sql(db_type, table_name, new_field))
        for s in result:
            print 111, s
        for i, s in enumerate(result):
            result[i] = self.set_case(db_type, s)
        return result

    def create_index_sql(self, db_type, table_name, fields=None, new_fields=None):

        def new_field_name_by_id(id_value):
            for f in new_fields:
                if f['id'] == id_value:
                    return f['field_name']

        index_name = self.f_index_name.value
        if self.f_foreign_index.value:
            key = self.f_foreign_field.display_text
            ref_id = self.task.sys_fields.field_by_id(self.f_foreign_field.value, 'f_object')
            ref = self.task.sys_items.field_by_id(ref_id, 'f_table_name')
            if db_type == common.POSTGRESQL:
                sql = 'ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(ID) MATCH SIMPLE' % \
                    (table_name, index_name, key, ref)
            elif db_type == common.FIREBIRD:
                sql = 'ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(ID)' % \
                    (table_name, index_name, key, ref)
            elif db_type == common.SQLITE:
                return '' # Doesn't support SQLITE
                #~ sql = 'CREATE INDEX "%s" ON "%s" (%s)' % \
                    #~ (index_name, table_name, field_str)
        else:
            index_desc = self.descending.value
            index_fields = self.f_fields.value
            desc = ''
            if index_desc:
                desc = 'DESC'
            fields = cPickle.loads(str(index_fields))
            if new_fields:
                fields = [new_field_name_by_id(field[0]) for field in fields]
            else:
                fields = [self.task.sys_fields.field_by_id(field[0], 'f_field_name') for field in fields]
            if desc and db_type in (common.SQLITE, common.POSTGRESQL):
                fields = ['"%s" %s' % (field, desc) for field in fields]
                field_str = ', '.join(fields)
            else:
                field_str = '"' + '", "'.join(fields) + '"'
            if db_type == common.POSTGRESQL:
                sql = 'CREATE INDEX "%s" ON "%s" (%s)' % \
                    (index_name, table_name, field_str)
            elif db_type == common.FIREBIRD:
                sql = 'CREATE %s INDEX "%s" ON "%s" (%s)' % \
                    (desc, index_name, table_name, field_str)
            elif db_type == common.SQLITE:
                sql = 'CREATE INDEX "%s" ON "%s" (%s)' % \
                    (index_name, table_name, field_str)
        print self.set_case(db_type, sql)
        return self.set_case(db_type, sql)

    def delete_index_sql(self, db_type):
        if self.f_foreign_index.value:
            if db_type in [common.POSTGRESQL, common.FIREBIRD]:
                table_name = self.task.sys_items.field_by_id(self.owner_rec_id.value, 'f_table_name')
                sql = 'ALTER TABLE %s DROP CONSTRAINT %s' % (table_name, self.f_index_name.value)
                print self.set_case(db_type, sql)
                return self.set_case(db_type, sql)
        else:
            sql = 'DROP INDEX "%s"' % self.f_index_name.value
            print self.set_case(db_type, sql)
            return self.set_case(db_type, sql)
