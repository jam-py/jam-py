# -*- coding: utf-8 -*-

import sqlite3

DATABASE = 'SQLITE'
NEED_DATABASE_NAME = True
NEED_LOGIN = False
NEED_PASSWORD = False
NEED_ENCODING = False
NEED_HOST = False
NEED_PORT = False
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = True
DDL_ROLLBACK = False
NEED_GENERATOR = False

FROM = '"%s" AS %s'
LEFT_OUTER_JOIN = 'OUTER LEFT JOIN "%s" AS %s'
FIELD_AS = 'AS'
LIKE = 'LIKE'

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

def get_select(query, start, end, fields):
    offset = query['__offset']
    limit = query['__limit']
    result = 'SELECT %s FROM %s' % (start, end)
    if limit:
        result += ' LIMIT %d, %d' % (offset, limit)
    return result

def process_sql_params(params, cursor):
    result = []
    for p in params:
        if type(p) == tuple:
            value, data_type = p
        else:
            value = p
        result.append(value)
    return result

def process_sql_result(rows):
    result = []
    for row in rows:
        result.append(list(row))
    return result

def cast_date(date_str):
    return "CAST('" + date_str + "' AS DATE)"

def cast_datetime(datetime_str):
    return "CAST('" + datetime_str + "' AS TIMESTAMP)"

def value_literal(index):
    return '?'

def upper_function():
    pass

def create_table_sql(table_name, fields, gen_name=None, foreign_fields=None):
    result = []
    primary_key = ''
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    for field in fields:
        sql += '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['primary_key']:
            primary_key = field['field_name']
            sql += ' PRIMARY KEY'
        if field['default_value']:
            if field['data_type'] == TEXT:
                sql += " DEFAULT '%s'" % field['default_value']
            else:
                sql += ' DEFAULT %s' % field['default_value']
        sql +=  ',\n'
    if foreign_fields:
        for field in foreign_fields:
            sql += 'FOREIGN KEY(%s) REFERENCES %s(%s),\n' % (field['key'], field['ref'], field['primary_key'])
    sql = sql[:-2]
    sql += ')\n'
    result.append(sql)
    return result

def delete_table_sql(table_name, gen_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (unique, index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref):
    return ''

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s"' % index_name

def delete_foreign_index(table_name, index_name):
    pass

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s' % \
        (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    if field['default_value']:
        if field['data_type'] == TEXT:
            sql += " DEFAULT '%s'" % field['default_value']
        else:
            sql += ' DEFAULT %s' % field['default_value']
    return result

def del_field_sql(table_name, field):
    return ''

def change_field_sql(table_name, old_field, new_field):
    return ''

def literal_case(string):
    return string.upper()

def get_sequence_name(table_name):
    return None

def next_sequence_value_sql(table_name):
    return None

def restart_sequence_sql(table_name, value):
    pass

def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    result = cursor.fetchall()
    return [r[1] for r in result]

def get_table_info(connection, table_name):
    cursor = connection.cursor()
    cursor.execute('PRAGMA table_info(%s)' % table_name)
    result = cursor.fetchall()
    fields = []
    for r in result:
        size = 0
        if r[2] == 'TEXT':
            size = 256
        fields.append({
            'field_name': r[1],
            'data_type': r[2],
            'size': size,
            'default_value': r[4],
            'pk': r[5]==1
        })
    cursor.execute('PRAGMA index_list(%s)' % table_name)
    result = cursor.fetchall()
    indexes = []
    for r in result:
        try:
            index_name = r[1]
            unique = r[2]
            cursor.execute('PRAGMA index_info(%s)' % index_name)
            info = cursor.fetchall()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='%s'" % index_name)
            sql = cursor.fetchall()
            flds = sql[0][0].split('(')[1].split(')')[0].split(',')
            defs = []
            for i in info:
                for field in flds:
                    f = i[2].upper()
                    field = field.upper()
                    if field.find(f) != -1:
                        a = field.split()
                        desc = False
                        if len(a) == 2 and a[1].strip() == 'DESC':
                            desc = True
                        f_name = a[0]
                        f_name = f_name.strip('"').strip("'")
#                        f_name = f_name.strip("'")
                        defs.append([f_name, desc])
            indexes.append({
                'index_name': index_name,
                'unique': unique,
                'fields': defs
            })
        except Exception, e:
            print e
            pass
    return {'fields': fields, 'indexes': indexes}



