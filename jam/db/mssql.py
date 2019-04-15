import os
import sys
import pymssql

from werkzeug._compat import PY2, iteritems, text_type, to_bytes, to_unicode

DATABASE = 'MSSQL'
NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = True
NEED_HOST = True
NEED_PORT = True
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False
DDL_ROLLBACK = True
NEED_GENERATOR = False

FROM = '"%s" AS %s'
LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" AS %s'
FIELD_AS = 'AS'
LIKE = 'LIKE'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, KEYS, FILE, IMAGE = range(1, 12)
FIELD_TYPES = {
    INTEGER: 'INT',
    TEXT: 'NVARCHAR',
    FLOAT: 'FLOAT',
    CURRENCY: 'FLOAT',
    DATE: 'DATE',
    DATETIME: 'DATETIME',
    BOOLEAN: 'INT',
    LONGTEXT: 'NVARCHAR(MAX)',
    KEYS: 'NVARCHAR(MAX)',
    FILE: 'NVARCHAR(MAX)',
    IMAGE: 'NVARCHAR(MAX)'
}

def connect(database, user, password, host, port, encoding, server):
    if encoding:
        return pymssql.connect(server=server, database=database, user=user, password=password, host=host, port=port, charset=encoding)
    else:
        return pymssql.connect(server=server, database=database, user=user, password=password, host=host, port=port)

def get_lastrowid(cursor):
    return cursor.lastrowid

def get_fields(query, fields, alias):
    sql = ''
    for field in fields:
        if field.master_field:
            pass
        elif field.calculated:
            sql += 'NULL AS "%s", ' % field.db_field_name
        else:
            sql += '%s."%s", ' % (alias, field.db_field_name)
    if query['__expanded']:
        for field in fields:
            if field.lookup_item:
                sql += '%s_LOOKUP, ' % field.db_field_name
    sql = sql[:-2]
    return sql

def get_select(query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
    offset = query['__offset']
    limit = query['__limit']
    if limit:
        end = ''.join([from_clause, where_clause, group_clause])
        offset += 1
        limit += offset
        flds = get_fields(query, fields, 'b')
        result = "SELECT %s FROM (SELECT %s, ROW_NUMBER() OVER (%s) AS RowNum FROM %s) AS b WHERE RowNum >= %s AND RowNum < %s ORDER BY RowNum" % \
            (flds, fields_clause, order_clause, end, offset, limit)
    else:
        end = ''.join([from_clause, where_clause, group_clause, order_clause])
        result = 'SELECT %s FROM %s' % (fields_clause, end)
    return result

def process_sql_params(params, cursor):
    result = []
    for p in params:
        if type(p) == tuple:
            value, data_type = p
        else:
            value = p
        result.append(value)
    return tuple(result)


def process_sql_result(rows):
    return [list(row) for row in rows]

def cast_date(date_str):
    return "CAST('" + date_str + "' AS DATE)"

def cast_datetime(datetime_str):
    return "CAST('" + datetime_str + "' AS DATETIME)"

def value_literal(index):
    return '%s'

def convert_like(field_name, val, data_type):
    if data_type in [INTEGER, FLOAT, CURRENCY]:
        return 'CAST(CAST(%s AS DECIMAL(20, 10)) AS VARCHAR(20))' % field_name, val
    else:
        return field_name, val

def set_identity_insert(table_name, on):
    if on:
        suffix = 'ON'
    else:
        suffix = 'OFF'
    return 'SET IDENTITY_INSERT %s %s' % (table_name, suffix)

def create_table_sql(table_name, fields, gen_name=None, foreign_fields=None):
    result = []
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    lines = []
    primary_key = None
    for field in fields:
        line = '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['size'] != 0 and field['data_type'] == TEXT:
            line += '(%d)' % field['size']
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                line += " DEFAULT '%s'" % field['default_value']
            else:
                line += ' DEFAULT %s' % field['default_value']
        if field['primary_key']:
            line += ' NOT NULL IDENTITY(1, 1)'
            primary_key = field['field_name']
        lines.append(line)
    if primary_key:
        lines.append('CONSTRAINT PK_%s PRIMARY KEY("%s")' % (table_name, primary_key))
    sql += ',\n'.join(lines)
    sql += ')\n'
    result.append(sql)
    return result

def delete_table_sql(table_name, gen_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (unique, index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref, primary_key):
    return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s")' % \
           (table_name, index_name, key, ref, primary_key)

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s" ON "%s"' % (index_name, table_name)

def delete_foreign_index(table_name, index_name):
    return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD "%s" %s' % \
             (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    if field['size']:
        result += '(%d)' % field['size']
    if field['default_value']:
        if field['data_type'] == TEXT:
            result += " DEFAULT '%s'" % field['default_value']
        else:
            result += ' DEFAULT %s' % field['default_value']
    return result


def del_field_sql(table_name, field):
    return 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field['field_name'])


def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
            or old_field['size'] != new_field['size']:
        raise Exception(u"Don't know how to change field's size or type of %s" % old_field['field_name'])
    if old_field['field_name'] != new_field['field_name']:
        result.append('ALTER TABLE "%s" RENAME COLUMN  "%s" TO "%s"' %
                      (table_name, old_field['field_name'], new_field['field_name']))
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = 'ALTER TABLE "%s" ALTER "%s" SET DEFAULT' % \
                      (table_name, new_field['field_name'])
                sql += " '%s'" % new_field['default_value']
            else:
                sql = 'ALTER TABLE "%s" ALTER "%s" SET DEFAULT %s' % \
                      (table_name, new_field['field_name'], new_field['default_value'])
        else:
            sql = 'ALTER TABLE "%s" alter "%s" DROP DEFAULT' % \
                  (table_name, new_field['field_name'])
        result.append(sql)
    return result


def identifier_case(name):
    return name.upper()

def next_sequence_value_sql(gen_name):
    return ""


def restart_sequence_sql(gen_name, value):
    return ""

def get_table_names(connection):
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

def get_table_info(connection, table_name, db_name):
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
        #~ data_type = data.lower()
        #~ if data_type in ('char', 'varchar', 'nchar', 'nvarchar'):
            #~ data_type = nvarchar
        #~ if data_type in (text, ntext):
            #~ data_type = ntext
        #~ if data_type in (binary, varbinary, image):
            #~ data_type = image
        #~ if data_type in (bit, tinyint, smallint, int):
            #~ data_type = int
        #~ if data_type in (bigint, decimal, dec, numeric, float, real, smallmoney, money):
            #~ data_type = numeric
        #~ if data_type in (datetime, datetime2, smalldatetime, datetimeoffset, time):
            #~ data_type = datetime
        size = 0
        if character_maximum_length:
            size = character_maximum_length
        default_value = None
        if column_default:
            default_value = column_default[1 : -1]  ## !!! NOTE -- THIS SHOULD BE DEBUG
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
    return {'fields': fields, 'field_types': FIELD_TYPES}
