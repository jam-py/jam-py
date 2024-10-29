import os
import sys

from ..common import consts
from .db import AbstractDB

class MSSqlDB(AbstractDB):
    def __init__(self):
        AbstractDB.__init__(self)
        self.db_type = consts.MSSQL
        self.DDL_ROLLBACK = True
        self.IS_DISTINCT_FROM = 'NOT EXISTS(SELECT %s INTERSECT SELECT %s)'
        self.FIELD_TYPES = {
            consts.INTEGER: 'INT',
            consts.TEXT: 'NVARCHAR',
            consts.FLOAT: 'FLOAT',
            consts.CURRENCY: 'FLOAT',
            consts.DATE: 'DATE',
            consts.DATETIME: 'DATETIME',
            consts.BOOLEAN: 'INT',
            consts.LONGTEXT: 'NVARCHAR(MAX)',
            consts.KEYS: 'NVARCHAR(MAX)',
            consts.FILE: 'NVARCHAR(512)',
            consts.IMAGE: 'NVARCHAR(256)'
        }

    def get_params(self, lib):
        params = self.params
        params['name'] = 'MSSQL'
        params['lib'] = ['pymssql', 'pyodbc']
        if lib == 2:
            params['dsn'] = True
            params['database'] = False
        else:
            params['server'] = True
            params['login'] = True
            params['password'] = True
            params['encoding'] = True
            params['host'] = True
            params['port'] = True
        return params

    def get_fields(self, query, fields, alias):
        sql = ''
        for field in fields:
            if field.master_field:
                pass
            else:
                sql += '%s."%s", ' % (alias, field.db_field_name)
        if query.expanded:
            for field in fields:
                if field.lookup_item:
                    sql += '%s_LOOKUP, ' % field.db_field_name
        sql = sql[:-2]
        return sql

    def get_select(self, query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
        offset = query.offset
        limit = query.limit
        if limit:
            end = ''.join([from_clause, where_clause, group_clause])
            offset += 1
            limit += offset
            flds = self.get_fields(query, fields, 'b')
            result = "SELECT %s FROM (SELECT %s, ROW_NUMBER() OVER (%s) AS RowNum FROM %s) AS b WHERE RowNum >= %s AND RowNum < %s ORDER BY RowNum" % \
                (flds, fields_clause, order_clause, end, offset, limit)
        else:
            end = ''.join([from_clause, where_clause, group_clause, order_clause])
            result = 'SELECT %s FROM %s' % (fields_clause, end)
        return result

    def process_query_params(self, params, cursor):
        result = []
        for p in params:
            if type(p) == tuple:
                value, data_type = p
            else:
                value = p
            result.append(value)
        return tuple(result)

    def convert_like(self, field_name, val, data_type):
        if data_type in [consts.INTEGER, consts.FLOAT, consts.CURRENCY]:
            return 'CAST(CAST(%s AS DECIMAL(20, 10)) AS VARCHAR(20))' % field_name, val
        else:
            return field_name, val

    def set_identity_insert(self, table_name, on):
        if on:
            suffix = 'ON'
        else:
            suffix = 'OFF'
        return 'SET IDENTITY_INSERT %s %s' % (table_name, suffix)

    def create_table(self, table_name, fields, gen_name=None, foreign_fields=None):
        result = []
        sql = 'CREATE TABLE "%s"\n(\n' % table_name
        lines = []
        primary_key = None
        for field in fields:
            default_text = self.default_text(field)
            line = '"%s" %s' % (field.field_name, self.FIELD_TYPES[field.data_type])
            if field.size != 0 and field.data_type == consts.TEXT:
                line += '(%d)' % field.size
            if not default_text is None:
##                line += ' CONSTRAINT "%s" DEFAULT %s' % (field.field_name + '_DEFAULT_CONSTRAINT', default_text)          ##fsu 2024.10.26
                line += ' CONSTRAINT "%s" DEFAULT %s' % ('DF_' + table_name + '_' + field.field_name, default_text)         ##fsu 2024.10.26
            if field.primary_key:
                line += ' IDENTITY(1, 1)'
                primary_key = field.field_name
            lines.append(line)
        if primary_key:
            lines.append('CONSTRAINT PK_%s PRIMARY KEY("%s")' % (table_name, primary_key))
        sql += ',\n'.join(lines)
        sql += ')\n'
        return sql

    def drop_table(self, table_name, gen_name):
        return 'DROP TABLE "%s"' % table_name

    def add_field(self, table_name, field):
        default_text = self.default_text(field)
        line = 'ALTER TABLE "%s" ADD "%s" %s' % \
                 (table_name, field.field_name, self.FIELD_TYPES[field.data_type])
        if field.size:
            line += '(%d)' % field.size
        if not default_text is None:
##            line += ' CONSTRAINT "%s" DEFAULT %s' % (field.field_name + '_DEFAULT_CONSTRAINT', default_value)                                                 ##fsu 2024.10.26
            line += ' CONSTRAINT "%s" DEFAULT %s FOR "%s"' % ('DF_' + table_name + '_' + field.field_name, default_text, field.field_name)                  ##fsu 2024.10.26
        print(line)
        return line

    def del_field(self, table_name, field):
        result = 'IF NOT (SELECT COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = \'%s\' AND COLUMN_NAME = \'%s\') IS NULL BEGIN ALTER TABLE "%s" DROP CONSTRAINT "%s" END ALTER TABLE "%s" DROP COLUMN "%s"' % \
            (table_name, field.field_name, table_name, 'DF_' + table_name + '_' + field.field_name, table_name, field.field_name)    ##fsu 2024.10.26
##        return 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field.field_name)                                                ##fsu 2024.10.26
##        print(result)                                                                                                              ##fsu 2024.10.26
        return result

    def change_field(self, table_name, old_field, new_field):
        if old_field.field_name != new_field.field_name:
            raise Exception("Changing field name is prohibited: field %s" % old_field.field_name)
        result = ''                                                                                                     ##fsu 2024.10.26
 ##        default_value = self.default_value(new_field)                                                                ##fsu 2024.10.26
        default_text = self.default_text(new_field)
        old_default_text = self.default_text(old_field)
        field_info = self.get_field_info(old_field.field_name, table_name)
        if old_field.size != new_field.size:
##            line = 'ALTER TABLE "%s" ALTER COLUMN "%s" %s' % \                                                        ##fsu 2024.10.26
            result += 'ALTER TABLE "%s" ALTER COLUMN "%s" %s' % \
                 (table_name, new_field.field_name, field_info['data_type'])                                            ##fsu 2024.10.26
            size = field_info['size']
            if size and size > 0 and field_info['data_type'].upper() in ['CHAR', 'VARCHAR', 'NVARCHAR']:
                if new_field.size > size:
                    size = new_field.size
##                line += '(%d)' % size                                                                                 ##fsu 2024.10.26
                result += '(%d)' % size
##            result.append(line)                                                                                       ##fsu 2024.10.26
        if old_field.default_value != new_field.default_value:
            if not old_default_text is None:
##                line = 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % \
##                    (table_name, field.field_name + '_DEFAULT_CONSTRAINT')                                            ##fsu 2024.10.26
                result += ' ALTER TABLE "%s" DROP CONSTRAINT "%s"' % \
                    (table_name, 'DF_' + table_name + '_' + old_field.field_name)                                       ##fsu 2024.10.26
            if not default_text is None:
##                line = 'ALTER TABLE "%s" ADD CONSTRAINT "%s" DEFAULT %s' % \
##                    (table_name, field.field_name + '_DEFAULT_CONSTRAINT', default_text)                              ##fsu 2024.10.26
                result += ' ALTER TABLE "%s" ADD CONSTRAINT "%s" DEFAULT %s FOR "%s"' % \
                    (table_name, 'DF_' + table_name + '_' + new_field.field_name, default_text, new_field.field_name)   ##fsu 2024.10.26
##        print(result)                                                                                                 ##fsu 2024.10.26
        return result

    def create_index(self, index_name, table_name, unique, fields, desc):
        return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (unique, index_name, table_name, fields)

    def create_foreign_index(self, table_name, index_name, key, ref, primary_key):
        return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s")' % \
               (table_name, index_name, key, ref, primary_key)

    def drop_index(self, table_name, index_name):
        return 'DROP INDEX "%s" ON "%s"' % (index_name, table_name)

    def drop_foreign_index(self, table_name, index_name):
        return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

    def before_insert(self, cursor, pk_field):
        if pk_field and pk_field.data:
            cursor.execute('SET IDENTITY_INSERT %s ON' % pk_field.owner.table_name)

    def after_insert(self, cursor, pk_field):
        if pk_field:
            if not pk_field.data:
                pk_field.data = self.get_lastrowid(cursor)
            else:
                cursor.execute('SET IDENTITY_INSERT %s OFF' % pk_field.owner.table_name)

    def get_table_names(self, connection):
        sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = SCHEMA_NAME()"
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            res = cursor.fetchall()
        except:
            pass
        result = []
        for r in res:
            result.append(r[0])
        return result

    def get_table_info(self, connection, table_name, db_name):
        cursor = connection.cursor()
        sql = '''
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                COLUMN_DEFAULT,
                COLUMNPROPERTY(object_id(TABLE_SCHEMA+'.'+TABLE_NAME), COLUMN_NAME, 'IsIdentity')
            FROM
                INFORMATION_SCHEMA.COLUMNS
            WHERE
              TABLE_NAME = '%s'
        '''
        cursor.execute(sql % (table_name))
        result = cursor.fetchall()
        fields = []
        for column_name, data_type, character_maximum_length, column_default, itent in result:
            size = 0
            if character_maximum_length:
                size = character_maximum_length
            default_value = None
            if column_default:
                default_value = column_default
            pk = False
            if itent == 1:
                pk = True
            fields.append({
                'field_name': column_name,
                'data_type': data_type.upper(),
                'size': size,
                'default_value': default_value,
                'pk': pk
            })
        return {'fields': fields, 'field_types': self.FIELD_TYPES}

db = MSSqlDB()
