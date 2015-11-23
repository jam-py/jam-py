# -*- coding: utf-8 -*-

import sqlite3

NEED_DATABASE_NAME = True
NEED_LOGIN = False
NEED_PASSWORD = False
NEED_ENCODING = False
NEED_HOST = False
NEED_PORT = False
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = True

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB = range(1, 9)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'TEXT',
    FLOAT: 'REAL',
    CURRENCY: 'REAL',
    DATE: 'TEXT',
    DATETIME: 'TEXT',
    BOOLEAN: 'INTEGER',
    BLOB: 'BLOB'
}

def sqlite_lower(value_):
    try:
        return value_.lower()
    except:
        pass

def sqlite_upper(value_):
    try:
        return value_.upper()
    except:
        pass

def connect(database, user, password, host, port, encoding):
    connection = sqlite3.connect(database)
    connection.create_function("LOWER", 1, sqlite_lower)
    connection.create_function("UPPER", 1, sqlite_upper)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return connection

def get_lastrowid(cursor):
    return cursor.lastrowid

LEFT_OUTER_JOIN = 'OUTER LEFT JOIN'
LIKE = 'LIKE'

def limit_start(offset, limit):
    return ''

def limit_end(offset, limit):
    return 'LIMIT %d, %d' % (offset, limit)

def upper_function():
    pass

def create_table_sql(table_name, fields, foreign_fields=None):
    result = []
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    for field in fields:
        sql += '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['field_name'].upper() == u'ID':
            sql += ' PRIMARY KEY'
        sql +=  ',\n'
    if foreign_fields:
        for field in foreign_fields:
            sql += 'FOREIGN KEY(%s) REFERENCES %s(ID),\n' % (field['key'], field['ref'])
    sql = sql[:-2]
    sql += ')\n'
    result.append(sql)
    return result

def delete_table_sql(table_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    return result

def create_index_sql(index_name, table_name, fields, desc):
    return 'CREATE INDEX "%s" ON "%s" (%s)' % (index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref):
    return ''

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s"' % index_name

def delete_foreign_index(table_name, index_name):
    pass

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s'
    result = result % (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    return result

def del_field_sql(table_name, field):
    return ''

def change_field_sql(table_name, old_field, new_field):
    return ''

def set_case(string):
    return string.upper()

def param_literal():
    return '?'

def get_sequence_name(table_name):
    return None

def next_sequence_value_sql(table_name):
    return None

def restart_sequence_sql(table_name, value):
    pass



