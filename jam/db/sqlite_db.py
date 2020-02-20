import sqlite3

from ..common import consts
from .db import AbstractDB

class SQLiteDB(AbstractDB):
    def __init__(self):
        AbstractDB.__init__(self)
        self.db_type = consts.SQLITE
        self.FIELD_TYPES = {
            consts.INTEGER: 'INTEGER',
            consts.TEXT: 'TEXT',
            consts.FLOAT: 'REAL',
            consts.CURRENCY: 'REAL',
            consts.DATE: 'TEXT',
            consts.DATETIME: 'TEXT',
            consts.BOOLEAN: 'INTEGER',
            consts.LONGTEXT: 'TEXT',
            consts.KEYS: 'TEXT',
            consts.FILE: 'TEXT',
            consts.IMAGE: 'TEXT'
        }

    def get_params(self, lib):
        params = self.params
        params['name'] = 'SQLITE'
        return params

    def sqlite_upper(self, value):
        try:
            return value.upper()
        except:
            return value

    def connect(self, db_info):
        if not db_info.database:
            raise Exception('Must supply database name')
        connection = sqlite3.connect(db_info.database)
        connection.create_function("UPPER", 1, self.sqlite_upper)
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        return connection

    def get_select(self, query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
        start = fields_clause
        end = ''.join([from_clause, where_clause, group_clause, order_clause])
        offset = query['__offset']
        limit = query['__limit']
        result = 'SELECT %s FROM %s' % (start, end)
        if limit:
            result += ' LIMIT %d, %d' % (offset, limit)
        return result

    def cast_date(self, date_str):
        return "'%s'" % date_str

    def cast_datetime(self, datetime_str):
        return "'%s'" % datetime_str

    def create_table(self, table_name, fields, gen_name=None, foreign_fields=None):
        primary_key = ''
        sql = 'CREATE TABLE "%s"\n(\n' % table_name
        lines = []
        for field in fields:
            line = '"%s" %s' % (field.field_name, self.FIELD_TYPES[field.data_type])
            if field.primary_key:
                primary_key = field.field_name
                line += ' PRIMARY KEY'
            default_value = self.default_value(field)
            if default_value and not field.primary_key:
                line += ' DEFAULT %s' % default_value
            lines.append(line)
        if foreign_fields:
            for field in foreign_fields:
                lines.append('FOREIGN KEY(%s) REFERENCES %s(%s)\n' % \
                    (field['key'], field['ref'], field['primary_key']))
        sql += ',\n'.join(lines)
        sql += '\n)'
        return sql

    def add_field(self, table_name, field):
        result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s' % \
            (table_name, field.field_name, self.FIELD_TYPES[field.data_type])
        default_value = self.default_value(field)
        if default_value:
            result += ' DEFAULT %s' % default_value
        return result

    def del_field(self, table_name, field):
        return ''

    def change_field(self, table_name, old_field, new_field):
        return ''

    def drop_table(self, table_name, gen_name):
        return 'DROP TABLE IF EXISTS "%s"' % table_name

    def set_foreign_keys(self, value):
        if value:
            return 'PRAGMA foreign_keys=on'
        else:
            return 'PRAGMA foreign_keys=off'

    def create_index(self, index_name, table_name, unique, fields, desc):
        return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (unique, index_name, table_name, fields)

    def drop_index(self, table_name, index_name):
        return 'DROP INDEX IF EXISTS "%s"' % index_name

    def after_insert(self, cursor, pk_field):
        if pk_field and not pk_field.data:
            pk_field.data = cursor.lastrowid

    def get_table_names(self, connection):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        result = cursor.fetchall()
        return [r[1] for r in result]

    def get_table_info(self, connection, table_name, db_name):
        cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(%s)' % table_name)
        result = cursor.fetchall()
        fields = []
        for r in result:
            fields.append({
                'field_name': r[1],
                'data_type': r[2],
                'size': 0,
                'default_value': r[4],
                'pk': r[5]==1
            })
        return {'fields': fields, 'FIELD_TYPES': self.FIELD_TYPES}


db = SQLiteDB()


