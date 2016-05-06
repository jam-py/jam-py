# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys

import common, db.db_modules as db_modules
from dataset import *

class SQL(object):

    def get_next_id(self, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        sql = db_module.next_sequence_value_sql(self.table_name)
        if sql:
            rec = self.task.execute_select_one(sql)
            if rec:
                if rec[0]:
                    return int(rec[0])

    def insert_sql(self, db_module):
        self._records[self.rec_no][self.deleted.bind_index] = 0
        sql = 'INSERT INTO "%s" (' % self.table_name
        row = []
        fields = ''
        values = ''
        for field in self.fields:
            if not (field.calculated or field.master_field):
                fields += '"%s", ' % field.field_name
                values +=  '%s, ' % db_module.param_literal()
                value = field.raw_value
#                value = db_module.store_value(value, field.data_type)
                row.append(value)
        fields = fields[:-2]
        values = values[:-2]
        sql = db_module.set_case('INSERT INTO "%s" (%s) VALUES ' % (self.table_name, fields)) + '(' + values + ')'
        return sql, row

    def update_sql(self, db_module):
        row = []
        command = db_module.set_case('UPDATE "%s" SET ' % self.table_name)
        fields = ''
        for field in self.fields:
            if not (field.calculated or field.master_field):
                fields += '"%s"=%s, ' % (db_module.set_case(field.field_name), db_module.param_literal())
                value = field.raw_value
                if field.field_name.lower() == 'deleted':
                    value = 0
#                value = db_module.store_value(value, field.data_type)
                row.append(value)
        fields = fields[:-2]
        id_field_name = 'id'
        if self.id_field_name:
            id_field_name = self.id_field_name
            id_value = self._field_by_name(id_field_name).value
        else:
            id_field_name = 'id'
            id_value = self.id.value
        where = db_module.set_case(' WHERE %s = %s' % (id_field_name, id_value))
        return command + fields + where, row

    def delete_sql(self, db_module):
        soft_delete = self.soft_delete
        if self.master:
            soft_delete = self.master.soft_delete
        if soft_delete:
            sql = 'UPDATE %s SET %s = 1 WHERE %s = %s' % (self.table_name, self.deleted.field_name, self.id.field_name, self.id.value)
        else:
            sql = 'DELETE FROM %s WHERE %s = %s' % (self.table_name, self.id.field_name, self.id.value)
        return db_module.set_case(sql)

    def apply_sql(self, priv=None, db_module=None):

        def get_sql(item, db_module):
            if item.master:
                item._records[item.rec_no][item.owner_id.bind_index] = item.owner.ID
                item._records[item.rec_no][item.owner_rec_id.bind_index] = item.owner.id.value
            if item.record_status == common.RECORD_INSERTED:
                if not item.master:
                    if priv and not priv['can_create']:
                        raise Exception, self.task.lang['cant_create'] % self.item_caption
                sql, param = item.insert_sql(db_module)
            elif item.record_status == common.RECORD_MODIFIED:
                if not item.master:
                    if priv and not priv['can_edit']:
                        raise Exception, self.task.lang['cant_edit'] % self.item_caption
                sql, param = item.update_sql(db_module)
            elif item.record_status == common.RECORD_DETAILS_MODIFIED:
                sql, param = '', None
            elif item.record_status == common.RECORD_DELETED:
                if not item.master:
                    if priv and not priv['can_delete']:
                        raise Exception, self.task.lang['cant_delete'] % self.item_caption
                sql = item.delete_sql(db_module)
                param = None
            else:
                raise Exception, u'apply_sql - invalid %s record_status %s, record: %s' % (item.item_name, item.record_status, item._records[item.rec_no])
            if item.master:
                owner_rec_id_index = item.fields.index(item.owner_rec_id)
            else:
                owner_rec_id_index = 0
            id_index = item.fields.index(item.id)
            info = {'ID': item.ID,
                'table_name': item.table_name,
                'status': item.record_status,
                'id': item.id.value,
                'id_index': id_index,
                'log_id': item.get_rec_info()[common.REC_CHANGE_ID],
                'owner_rec_id_index': owner_rec_id_index}
            return sql, param, info

        def delete_detail_sql(item, detail, db_module):
            if item.soft_delete:
                sql = 'UPDATE %s SET DELETED = 1 WHERE OWNER_ID = %s AND OWNER_REC_ID = %s' % (detail.table_name, item.ID, item.id.value)
            else:
                sql = 'DELETE FROM %s WHERE OWNER_ID = %s AND OWNER_REC_ID = %s' % (detail.table_name, item.ID, item.id.value)
            return db_module.set_case(sql), None, None

        def generate_sql(item, db_module, result):
            ID, sql = result
            for it in item:
                details = []
                sql.append((get_sql(it, db_module), details))
                for detail in item.details:
                    detail_sql = []
                    detail_result = (str(detail.ID), detail_sql)
                    details.append(detail_result)
                    if item.record_status == common.RECORD_DELETED:
                        detail_sql.append((delete_detail_sql(item, detail, db_module), []))
                    else:
                        generate_sql(detail, db_module, detail_result)

        if db_module is None:
            db_module = self.task.db_module
        result = (self.ID, [])
        generate_sql(self, db_module, result)
        return {'delta': result}


    def ref_table_alias(self, field):
        if field.master_field:
            return field.lookup_item.table_name + str(self._fields.index(field.master_field))
        else:
            return field.lookup_item.table_name + str(self._fields.index(field))

    def fields_clause(self, query, fields, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        funcs = query.get('__funcs')
        if funcs:
            functions = {}
            for key, value in funcs.iteritems():
                functions[key.upper()] = value
        sql = ''
        for field in fields:
            if field.master_field:
                pass
            elif field.calculated:
                sql += 'NULL AS "%s", ' % field.field_name
            else:
                field_sql = '"%s"."%s"' % (self.table_name, field.field_name)
                if funcs:
                    func = functions.get(field.field_name.upper())
                    if func:
                        field_sql = '%s(%s)' % (func, field_sql)
                sql += field_sql + ', '
        if query['__expanded']:
            for field in fields:
                if field.lookup_item:
                    field_sql = '"%s"."%s" AS "%s_LOOKUP"' % (self.ref_table_alias(field), field.lookup_field, field.field_name)
                    if funcs:
                        func = functions.get(field.field_name.upper())
                        if func:
                            field_sql = '%s("%s"."%s") AS "%s_LOOKUP"' % (func, self.ref_table_alias(field), field.lookup_field, field.field_name)
                    sql += field_sql + ', '
        sql = sql[:-2]
        return db_module.set_case(sql)

    def from_clause(self, query, fields, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        result = '"%s"' % self.table_name
        if query['__expanded']:
            for field in fields:
                if field.lookup_item and not field.master_field:
                    if field.lookup_item.id_field_name:
                        id_field_name = field.lookup_item.id_field_name
                    else:
                        id_field_name = 'id'
                    result = '(' + result
                    result += ' ' + db_module.LEFT_OUTER_JOIN + ' "%s" AS "%s"' % (field.lookup_item.table_name, self.ref_table_alias(field))
                    result += ' ON "%s"."%s"' % (self.table_name, field.field_name)
                    result += ' = "%s"."%s")'  % (self.ref_table_alias(field), id_field_name)
        return db_module.set_case(result)

    def where_clause(self, query, db_module=None):

        def get_filter_sign(filter_type, value=None):
            result = common.FILTER_SIGN[filter_type]
            if filter_type == common.FILTER_ISNULL:
                if value:
                    result = 'IS NULL'
                else:
                    result = 'IS NOT NULL'
            if (result == 'LIKE'):
                result = db_module.LIKE
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
            found = False
            for ch in value:
                if ch == "'":
                    ch = ch + ch
                elif ch in ['_', '%']:
                    ch = esc_char + ch
                    found = True
                result += ch
            return result, found

        def get_condition(field_name, filter_type, value):
            field = self._field_by_name(field_name)
            esc_char = '/'
            cond_field_name = db_module.set_case('"%s"."%s"' % (self.table_name, field_name))
            if type(value) == str:
                value = value.decode('utf-8')
            filter_sign = get_filter_sign(filter_type, value)
            cond_string = '%s %s %s'
            if filter_type in (common.FILTER_IN, common.FILTER_NOT_IN):
                lst = '('
                for it in value:
                    lst += convert_field_value(field, it) + ', '
                value = lst[:-2] + ')'
            elif filter_type == common.FILTER_RANGE:
                value = convert_field_value(field, value[0]) + ' AND ' + convert_field_value(field, value[1])
            elif filter_type == common.FILTER_ISNULL:
                value = ''
            else:
                value = convert_field_value(field, value, filter_type)
                if filter_type in [common.FILTER_CONTAINS, common.FILTER_STARTWITH, common.FILTER_ENDWITH]:
                    value, esc_found = escape_search(value, esc_char)
                    if field.lookup_item:
                        cond_field_name = db_module.set_case('"%s"."%s"' % (self.ref_table_alias(field), field.lookup_field))
                    if filter_type == common.FILTER_CONTAINS:
                        value = '%' + value + '%'
                    elif filter_type == common.FILTER_STARTWITH:
                        value = value + '%'
                    elif filter_type == common.FILTER_ENDWITH:
                        value = '%' + value
                    upper_function =  db_module.upper_function()
                    if upper_function:
                        cond_string = upper_function + '(%s) %s %s'
                        value = value.upper()
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
                    raise Exception, 'sql.py where_clause method: boolen field condition may give ambiguious results.'
            return sql

        def valid_filter(filter_type, value):
            if value is None:
                return False
            if filter_type in [common.FILTER_IN, common.FILTER_NOT_IN]:
                if type(value) in [tuple, list] and len(value) == 0:
                    return False
            return True

        if db_module is None:
            db_module = self.task.db_module
        result = ''
        conditions = []
        filters = query['__filters']
        deleted_in_filters = False
        if filters:
            for (field_name, filter_type, value) in filters:
                if valid_filter(filter_type, value):
                    if field_name == 'deleted':
                        deleted_in_filters = True
                    if filter_type == common.FILTER_CONTAINS_ALL:
                        values = value.split()
                        for val in values:
                            conditions.append(get_condition(field_name, common.FILTER_CONTAINS, val))
                    else:
                        conditions.append(get_condition(field_name, filter_type, value))
        if not deleted_in_filters:
            conditions.append(db_module.set_case('"%s"."deleted"=0' % self.table_name))
        for sql in conditions:
            result += sql + ' AND '
        result = result[:-5]
        if result:
            result = ' WHERE ' + result
        return result

    def group_clause(self, query, fields, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        group_fields = query.get('__group_by')
        result = ''
        if group_fields:
            for field_name in group_fields:
                field = self.field_by_name(field_name)
                result += '"%s"."%s", ' % (self.table_name, field_name)
                if field.lookup_item:
                    result += '"%s_LOOKUP", ' % field.field_name
            if result:
                result = result[:-2]
                result = ' GROUP BY ' + result
            return db_module.set_case(result)
        else:
            return ''

    def order_clause(self, query, db_module=None):
        result = ''
        if query.get('__funcs') and not query.get('__group_by'):
            return result
        if db_module is None:
            db_module = self.task.db_module
        order_list = query.get('__order', [])
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
        return db_module.set_case(result)

    def limit_clause_start(self, query, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        result = ''
        if query['__limit']:
            result = db_module.limit_start(query['__offset'], query['__limit'])
        if result:
            result += ' '
        return db_module.set_case(result)

    def limit_clause_end(self, query, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        result = ''
        if query['__limit']:
            result = db_module.limit_end(query['__offset'], query['__limit'])
        return ' ' + db_module.set_case(result)

    def get_select_statement(self, query, db_module=None):
        if db_module is None:
            db_module = self.task.db_module
        field_list = query['__fields']
        if len(field_list):
            fields = [self._field_by_name(field_name) for field_name in field_list]
        else:
            fields = self._fields
        sql = 'SELECT ' + \
            self.limit_clause_start(query, db_module) + \
            self.fields_clause(query, fields, db_module) + \
            ' FROM ' + \
            self.from_clause(query, fields, db_module) + \
            self.where_clause(query, db_module) + \
            self.group_clause(query, fields, db_module) + \
            self.order_clause(query, db_module) + \
            self.limit_clause_end(query, db_module)
        return sql

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
        db_module = db_modules.get_db_module(db_type)
        result = db_module.create_table_sql(table_name, fields, foreign_fields=None)
        for i, s in enumerate(result):
            result[i] = db_module.set_case(s)
            print result[i]
        return result

    def delete_table_sql(self, db_type):
        table_name = self.f_table_name.value
        db_module = db_modules.get_db_module(db_type)
        result = db_module.delete_table_sql(table_name)
        for i, s in enumerate(result):
            result[i] = db_module.set_case(s)
            print result[i]
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

        def recreate(comp):
            for key, (old_field, new_field) in comp.items():
                if old_field and new_field:
                    if old_field['field_name'] != new_field['field_name']:
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
            for key, (old_field, new_field) in comp.items():
                if old_field and not new_field and db_type != db_modules.SQLITE:
                    result.append(db_module.del_field_sql(table_name, old_field))
            for key, (old_field, new_field) in comp.items():
                if old_field and new_field and db_type != db_modules.SQLITE:
                    if (old_field['field_name'] != new_field['field_name']) or \
                        (db_module.FIELD_TYPES[old_field['data_type']] != db_module.FIELD_TYPES[new_field['data_type']]) or \
                        (old_field['size'] != new_field['size']):
                        result.append(db_module.change_field_sql(table_name, old_field, new_field))
            for key, (old_field, new_field) in comp.items():
                if not old_field and new_field:
                    result.append(db_module.add_field_sql(table_name, new_field))
        for i, s in enumerate(result):
            result[i] = db_module.set_case(s)
            print result[i]
        return result

    def create_index_sql(self, db_type, table_name, fields=None, new_fields=None):

        def new_field_name_by_id(id_value):
            for f in new_fields:
                if f['id'] == id_value:
                    return f['field_name']

        db_module = db_modules.get_db_module(db_type)
        index_name = self.f_index_name.value
        if self.f_foreign_index.value:
            key = self.f_foreign_field.display_text
            ref_id = self.task.sys_fields.field_by_id(self.f_foreign_field.value, 'f_object')
            ref = self.task.sys_items.field_by_id(ref_id, 'f_table_name')
            sql = db_module.create_foreign_index_sql(table_name, index_name, key, ref)
        else:
            index_desc = self.descending.value
            index_fields = self.f_fields.value
            desc = ''
            if index_desc:
                desc = 'DESC'
            fields = common.load_index_fields(index_fields)
            if new_fields:
                fields = [new_field_name_by_id(field[0]) for field in fields]
            else:
                fields = [self.task.sys_fields.field_by_id(field[0], 'f_field_name') for field in fields]
            if desc and db_type in (db_modules.SQLITE, db_modules.POSTGRESQL):
                fields = ['"%s" %s' % (field, desc) for field in fields]
                field_str = ', '.join(fields)
            else:
                field_str = '"' + '", "'.join(fields) + '"'
            sql = db_module.create_index_sql(index_name, table_name, field_str, desc)
        print db_module.set_case(sql)
        return db_module.set_case(sql)

    def delete_index_sql(self, db_type):
        db_module = db_modules.get_db_module(db_type)
        table_name = self.task.sys_items.field_by_id(self.owner_rec_id.value, 'f_table_name')
        index_name = self.f_index_name.value
        if self.f_foreign_index.value:
            sql = db_module.delete_foreign_index(table_name, index_name)
        else:
            sql = db_module.delete_index(table_name, index_name)
        print db_module.set_case(sql)
        return db_module.set_case(sql)
