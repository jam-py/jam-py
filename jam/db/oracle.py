# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import cPickle
import cx_Oracle

NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = False
NEED_HOST = False
NEED_PORT = False
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False
UPPER_CASE = True
DDL_ROLLBACK = False
FROM = '"%s" %s '
LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" %s'
FIELD_AS = 'AS'
LIKE = 'LIKE'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB = range(1, 9)
FIELD_TYPES = {
    INTEGER: 'NUMBER',
    TEXT: 'VARCHAR2',
    FLOAT: 'DOUBLE PRECISION',
    CURRENCY: 'DOUBLE PRECISION',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'NUMBER',
    BLOB: 'BLOB'
}

def connect(database, user, password, host, port, encoding):
    if database and user and password:
        return cx_Oracle.connect(user=user, password=password, dsn=database)
    elif database:
        return cx_Oracle.connect(dsn=database)

def get_lastrowid(cursor):
    return None

def get_fields(query, fields, alias):
    sql = ''
    for field in fields:
        if field.master_field:
            pass
        elif field.calculated:
            sql += 'NULL AS "%s", ' % field.field_name
        else:
            sql += '%s."%s", ' % (alias, field.field_name)
    if query['__expanded']:
        for field in fields:
            if field.lookup_item:
                sql += '%s_LOOKUP, ' % field.field_name
    sql = sql[:-2]
    return set_case(sql)


def get_select(query, start, end, fields):
    offset = query['__offset']
    limit = query['__limit']
    result = 'SELECT %s FROM %s' % (start, end)
    if limit:
        flds = get_fields(query, fields, 'b')
        rnum = offset + 1
        rownum = offset + limit
        if offset == 0:
            rnum = 0
        result = "SELECT %s FROM (SELECT a.*, rownum rnum FROM (%s) a WHERE rownum <= %s) b WHERE rnum >= %s" % \
            (flds, result, rownum, rnum)
    return result

def process_sql_params(params, cursor):
    result = []
    for i, p in enumerate(params):
        if type(p) == tuple:
            value, data_type = p
            if data_type == BLOB:
                if type(value) == unicode:
                    value = value.encode('utf-8')
                blob = cursor.var(cx_Oracle.BLOB)
                blob.setvalue(0, value)
                value = blob
        else:
            value = p
        result.append(value)
    return result

def process_sql_result(rows):
    result = []
    for row in rows:
        fields = []
        for field in row:
            if isinstance(field, cx_Oracle.LOB):
                field = field.read()
            fields.append(field)
        result.append(fields)
    return result

def cast_date(date_str):
    return "TO_DATE('" + date_str + "', 'YYYY-MM-DD')"

def cast_datetime(datetime_str):
    return "TO_DATE('" + date_str + "', 'YYYY-MM-DD  HH24:MI')"

def value_literal(index):
    return ':f%d' % index

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
    return set_case('CREATE %s INDEX "%s" ON "%s" (%s)' % \
        (unique, index_name, table_name, fields))

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
    return set_case('ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field['field_name']))

def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception, u"Don't know how to change field's size or type of %s" % old_field['field_name']
    if old_field['field_name'] != new_field['field_name']:
        sql = set_case('ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name']))
        result.append(sql)
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = set_case('ALTER TABLE "%s" MODIFY "%s" DEFAULT' % \
                    (table_name, new_field['field_name']))
                sql +=  " '%s'" % new_field['default_value']
            else:
                sql = set_case('ALTER TABLE "%s" MODIFY "%s" DEFAULT %s' % \
                    (table_name, new_field['field_name'], new_field['default_value']))
        else:
            sql = set_case('ALTER TABLE "%s" MODIFY "%s" DEFAULT %s' % \
                (table_name, new_field['field_name'], 'NULL'))
        result.append(sql)
    return result

def set_case(string):
    return string.upper()

def param_literal():
    return '?'

def get_sequence_name(table_name):
    return set_case('%s_GEN' % table_name)

def next_sequence_value_sql(table_name):
    return set_case('SELECT %s.NEXTVAL FROM DUAL' % \
        get_sequence_name(table_name))

def restart_sequence_sql(table_name, value):
    result = []
    result.append(set_case('DROP SEQUENCE "%s_GEN"' % table_name))
    result.append(set_case('CREATE SEQUENCE "%s_GEN" START WITH %s' % (table_name, value)))
    return result


