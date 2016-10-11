# -*- coding: utf-8 -*-

import psycopg2

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = True
NEED_HOST = True
NEED_PORT = True
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False
UPPER_CASE = False
DDL_ROLLBACK = True
FROM = '"%s" as %s'
LEFT_OUTER_JOIN = 'left outer join "%s" as %s'
FIELD_AS = 'as'
LIKE = 'ilike'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB = range(1, 9)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'VARCHAR',
    FLOAT: 'NUMERIC',
    CURRENCY: 'NUMERIC',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'INTEGER',
    BLOB: 'BYTEA'
}

def connect(database, user, password, host, port, encoding):
    return psycopg2.connect(database=database, user=user, password=password, host=host, port=port)

def get_lastrowid(cursor):
    return None

def get_select(query, start, end, fields):
    offset = query['__offset']
    limit = query['__limit']
    result = 'select %s from %s' % (start, end)
    if limit:
        result += ' limit %d offset %d' % (limit, offset)
    return result

def process_sql_params(params, cursor):
    result = []
    for p in params:
        if type(p) == tuple:
            value, data_type = p
            if data_type == BLOB:
                if type(value) == unicode:
                    value = value.encode('utf-8')
                value = psycopg2.Binary(value)
        else:
            value = p
        result.append(value)
    return result

def process_sql_result(rows):
    result = []
    for row in rows:
        fields = []
        for field in row:
            if type(field) == buffer:
                field = str(field)
            fields.append(field)
        result.append(fields)
    return result

def cast_date(date_str):
    return "cast('" + date_str + "' as date)"

def cast_datetime(datetime_str):
    return "cast('" + datetime_str + "' as timestamp)"

def value_literal(index):
    return '%s'

def upper_function():
    pass

def create_table_sql(table_name, fields, foreign_fields=None):
    result = []
    primary_key = ''
    seq_name = '%s_id_seq' % table_name
    result.append(set_case('create sequence "%s"' % seq_name))
    sql = 'create table "%s"\n(\n' % set_case(table_name)
    for field in fields:
        if field['primary_key']:
            primary_key = set_case(field['field_name'])
            sql += set_case('"%s" %s primary key default nextval(\'"%s"\')' % \
                (field['field_name'], FIELD_TYPES[field['data_type']], seq_name))
        else:
            sql += set_case('"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']]))
        if field['size'] != 0 and field['data_type'] == TEXT:
            sql += '(%d)' % field['size']
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                sql += set_case(" default '%s'" % field['default_value'])
            else:
                sql += set_case(' default %s' % field['default_value'])
        sql +=  ',\n'
    sql = sql[:-2]
    sql += ')\n'
    result.append(sql)
    result.append(set_case('alter sequence "%s" owned by "%s"."%s"' % (seq_name, table_name, primary_key)))
    return result

def delete_table_sql(table_name):
    result = []
    result.append(set_case('drop table "%s"' % table_name))
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return set_case('create %s index "%s" on "%s" (%s)' % \
        (unique, index_name, table_name, fields))

def create_foreign_index_sql(table_name, index_name, key, ref, primary_key):
    return set_case('alter table %s add constraint %s foreign key (%s) references %s(%s) match simple' % \
        (table_name, index_name, key, ref, primary_key))

def delete_index(table_name, index_name):
    return set_case('drop index "%s"' % index_name)

def delete_foreign_index(table_name, index_name):
    return set_case('alter table %s drop constraint %s' % (table_name, index_name))

def add_field_sql(table_name, field):
    result = set_case('alter table "%s" add column "%s" %s' %
        (table_name, field['field_name'], FIELD_TYPES[field['data_type']]))
    if field['size']:
        result += '(%d)' % field['size']
    if field['default_value']:
        if field['data_type'] == TEXT:
            result += " default '%s'" % set_case(field['default_value'])
        else:
            result += ' default %s' % field['default_value']
    return result

def del_field_sql(table_name, field):
    return set_case('alter table "%s" drop column "%s"' % (table_name, field['field_name']))

def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception, u"Don't know how to change field's size or type of %s" % old_field['field_name']
    if old_field['field_name'] != new_field['field_name']:
        result.append(set_case('alter table "%s" rename column  "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name'])))
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = set_case('alter table "%s" alter "%s" set default' % \
                    (table_name, new_field['field_name']))
                sql +=  " '%s'" % new_field['default_value']
            else:
                sql = set_case('alter table "%s" alter "%s" set default %s' % \
                    (table_name, new_field['field_name'], new_field['default_value']))
        else:
            sql = set_case('alter table "%s" alter "%s" drop default' % \
                (table_name, new_field['field_name']))
        result.append(sql)
    return result


def set_case(string):
    return string.lower()

def get_sequence_name(table_name):
    return set_case('%s_id_seq' % table_name)

def next_sequence_value_sql(table_name):
    return set_case("select nextval('%s')" % get_sequence_name(table_name))

def restart_sequence_sql(table_name, value):
    return set_case('alter sequence %s restart with %d' % (get_sequence_name(table_name), value))

