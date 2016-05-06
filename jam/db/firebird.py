# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import cPickle
import fdb

NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = True
NEED_HOST = True
NEED_PORT = True
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB = range(1, 9)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'VARCHAR',
    FLOAT: 'DOUBLE PRECISION',
    CURRENCY: 'DOUBLE PRECISION',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'INTEGER',
    BLOB: 'BLOB'
}

def connect(database, user, password, host, port, encoding):
    if not encoding:
        encoding = None
    if not port:
        port = None
    else:
        port = int(port)
    return fdb.connect(database=database, user=user, password=password, charset=encoding, host=host, port=port)

def get_lastrowid(cursor):
    return None

LEFT_OUTER_JOIN = 'LEFT OUTER JOIN'
LIKE = 'LIKE'

def limit_start(offset, limit):
    return 'FIRST %d SKIP %d' % (limit, offset)

def limit_end(offset, limit):
    return ''

def upper_function():
    return 'UPPER'

def create_table_sql(table_name, fields, foreign_fields=None):
    result = []
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    for field in fields:
        sql += '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['size'] != 0 and field['data_type'] == TEXT:
            sql += '(%d)' % field['size']
        sql +=  ',\n'
    sql += 'CONSTRAINT %s_PR_INDEX PRIMARY KEY ("ID")\n' % table_name
    sql += ')\n'
    result.append(sql)
    result.append('CREATE SEQUENCE "%s_GEN"' % table_name)
    return result

def delete_table_sql(table_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    result.append('DROP SEQUENCE "%s_GEN"' % table_name)
    return result

def create_index_sql(index_name, table_name, fields, desc):
    return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (desc, index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref):
    return 'ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(ID)' % \
        (table_name, index_name, key, ref)

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s"' % index_name

def delete_foreign_index(table_name, index_name):
    return 'ALTER TABLE %s DROP CONSTRAINT %s' % (table_name, index_name)

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD "%s" %s'
    result = result % (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    if field['size']:
        result += '(%d)' % field['size']
    return result

def del_field_sql(table_name, field):
    return 'ALTER TABLE "%s" DROP "%s"' % (table_name, field['field_name'])

def change_field_sql(table_name, old_field, new_field):
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception, u"Don't know how to change field's size or type of %s" % old_field['field_name']
    result = 'ALTER TABLE "%s" ALTER "%s" TO "%s"' % (table_name, old_field['field_name'], new_field['field_name'])
    return result

def set_case(string):
    return string.upper()

def param_literal():
    return '?'

def get_sequence_name(table_name):
    return '%s_GEN' % table_name

def next_sequence_value_sql(table_name):
    return set_case('SELECT NEXT VALUE FOR "%s" FROM RDB$DATABASE' % get_sequence_name(table_name))

def restart_sequence_sql(table_name, value):
    return set_case('ALTER SEQUENCE %s RESTART WITH %d' % (get_sequence_name(table_name), value))


