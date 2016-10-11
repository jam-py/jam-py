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
UPPER_CASE = True
DDL_ROLLBACK = True
FROM = '"%s" AS %s'
LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" AS %s'
FIELD_AS = 'AS'
LIKE = 'LIKE'

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

def get_select(query, start, end, fields):
    offset = query['__offset']
    limit = query['__limit']
    page = ''
    if limit:
        page = 'FIRST %d SKIP %d' % (limit, offset)
    return 'SELECT %s %s FROM %s' % (page, start, end)

def process_sql_params(params, cursor):
    result = []
    for p in params:
        if type(p) == tuple:
            value, data_type = p
            if data_type == BLOB and type(value) == unicode:
                value = value.encode('utf-8')
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
    return 'UPPER'

def create_table_sql(table_name, fields, foreign_fields=None):
    result = []
    primary_key = ''
    sql = set_case('CREATE TABLE "%s"\n(\n' % table_name)
    for field in fields:
        sql += set_case('"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']]))
        if field['size'] != 0 and field['data_type'] == TEXT:
            sql += '(%d)' % field['size']
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                sql += " DEFAULT '%s'" % field['default_value']
            else:
                sql += ' DEFAULT %s' % field['default_value']
        sql +=  ',\n'
        if field['primary_key']:
            primary_key = set_case(field['field_name'])
    sql += set_case('CONSTRAINT %s_PR_INDEX PRIMARY KEY ("%s")\n' % \
        (table_name, primary_key))
    sql += ')\n'
    result.append(sql)
    result.append(set_case('CREATE SEQUENCE "%s_GEN"' % table_name))
    return result

def delete_table_sql(table_name):
    result = []
    result.append(set_case('DROP TABLE "%s"' % table_name))
    result.append(set_case('DROP SEQUENCE "%s_GEN"' % table_name))
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return set_case('CREATE %s %s INDEX "%s" ON "%s" (%s)' % \
        (unique, desc, index_name, table_name, fields))

def create_foreign_index_sql(table_name, index_name, key, ref, primary_key):
    return set_case('ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(%s)' % \
        (table_name, index_name, key, ref, primary_key))

def delete_index(table_name, index_name):
    return set_case('DROP INDEX "%s"' % index_name)

def delete_foreign_index(table_name, index_name):
    return set_case('ALTER TABLE %s DROP CONSTRAINT %s' % (table_name, index_name))

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD "%s" %s'
    result = set_case(result % (table_name, field['field_name'], FIELD_TYPES[field['data_type']]))
    if field['size']:
        result += '(%d)' % field['size']
    if field['default_value']:
        if field['data_type'] == TEXT:
            result += " DEFAULT '%s'" % field['default_value']
        else:
            result += ' DEFAULT %s' % field['default_value']
    return result

def del_field_sql(table_name, field):
    return set_case('ALTER TABLE "%s" DROP "%s"' % (table_name, field['field_name']))

def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception, u"Don't know how to change field's size or type of %s" % old_field['field_name']
    if old_field['field_name'] != new_field['field_name']:
        sql = set_case('ALTER TABLE "%s" ALTER "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name']))
        result.append(sql)
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = set_case('ALTER TABLE "%s" ALTER "%s" SET DEFAULT' % \
                    (table_name, new_field['field_name']))
                sql +=  " '%s'" % new_field['default_value']
            else:
                sql = set_case('ALTER TABLE "%s" ALTER "%s" SET DEFAULT %s' % \
                    (table_name, new_field['field_name'], new_field['default_value']))
        else:
            sql = set_case('ALTER TABLE "%s" ALTER "%s" DROP DEFAULT' % \
                (table_name, new_field['field_name']))
        result.append(sql)
    return result

def set_case(string):
    return string.upper()

def get_sequence_name(table_name):
    return set_case('%s_GEN' % table_name)

def next_sequence_value_sql(table_name):
    return set_case('SELECT NEXT VALUE FOR "%s" FROM RDB$DATABASE' % \
        get_sequence_name(table_name))

def restart_sequence_sql(table_name, value):
    return set_case('ALTER SEQUENCE %s RESTART WITH %d' % \
        (get_sequence_name(table_name), value))


