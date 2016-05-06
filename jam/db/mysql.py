# -*- coding: utf-8 -*-

import MySQLdb

NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = True
NEED_HOST = True
NEED_PORT = True
CAN_CHANGE_TYPE = True
CAN_CHANGE_SIZE = True

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB = range(1, 9)
FIELD_TYPES = {
    INTEGER: 'INT',
    TEXT: 'VARCHAR',
    FLOAT: 'DOUBLE',
    CURRENCY: 'DOUBLE',
    DATE: 'DATE',
    DATETIME: 'DATETIME',
    BOOLEAN: 'INT',
    BLOB: 'BLOB'
}

def connect(database, user, password, host, port, encoding):
    charset = None
    use_unicode = None
    if encoding:
        charset = encoding
        use_unicode = True
    if port:
        connection = MySQLdb.connect(db=database, user=user, passwd=password, host=host,
            port=int(port), charset=charset, use_unicode=use_unicode)
    else:
        connection = MySQLdb.connect(db=database, user=user, passwd=password, host=host,
            charset=charset, use_unicode=use_unicode)
    connection.autocommit(False)
    cursor = connection.cursor()
    cursor.execute("SET SESSION SQL_MODE=ANSI_QUOTES")
    return connection

def get_lastrowid(cursor):
    return cursor.lastrowid

LEFT_OUTER_JOIN = 'LEFT OUTER JOIN'
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
        if field['size'] != 0 and field['data_type'] == TEXT:
            sql += '(%d)' % field['size']
        if field['field_name'].upper() == u'ID':
            sql += ' NOT NULL AUTO_INCREMENT'
        sql +=  ',\n'
    sql += 'PRIMARY KEY("ID")'
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
    return 'ALTER TABLE %s ADD FOREIGN KEY (%s) REFERENCES %s(ID)' % \
        (table_name, index_name, key, ref)

def delete_index(table_name, index_name):
    return 'DROP INDEX %s ON %s' % (index_name, table_name)

def delete_foreign_index(table_name, index_name):
    return 'ALTER TABLE %s DROP FOREIGN KEY %s' % (table_name, index_name)

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD "%s" %s'
    result = result % (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    if field['size']:
        result += '(%d)' % field['size']
    return result

def del_field_sql(table_name, field):
    return 'ALTER TABLE "%s" DROP "%s"' % (table_name, field['field_name'])

def change_field_sql(table_name, old_field, new_field):
    result = 'ALTER TABLE "%s" CHANGE  "%s" "%s" %s' % (table_name, old_field['field_name'], new_field['field_name'], FIELD_TYPES[new_field['data_type']])
    if old_field['size'] and old_field['size'] != new_field['size']:
        result += '(%d)' % new_field['size']
    return result

def set_case(string):
    return string.upper()

def param_literal():
    return '%s'

def quotes():
    return '`'

def get_sequence_name(table_name):
    return None

def next_sequence_value_sql(table_name):
    return None

def restart_sequence_sql(table_name, value):
    pass
