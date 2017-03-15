# -*- coding: utf-8 -*-

import psycopg2

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

DATABASE = 'POSTGRESQL'
NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = True
NEED_HOST = True
NEED_PORT = True
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False
DDL_ROLLBACK = True
NEED_GENERATOR = True

FROM = '"%s" AS %s'
LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" AS %s'
FIELD_AS = 'AS'
LIKE = 'ILIKE'

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
    result = 'SELECT %s FROM %s' % (start, end)
    if limit:
        result += ' LIMIT %d OFFSET %d' % (limit, offset)
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
    return "CAST('" + date_str + "' AS DATE)"

def cast_datetime(datetime_str):
    return "CAST('" + datetime_str + "' AS TIMESTAMP)"

def value_literal(index):
    return '%s'

def upper_function():
    pass

def create_table_sql(table_name, fields, gen_name=None, foreign_fields=None):
    result = []
    primary_key = ''
    seq_name = gen_name
    result.append('CREATE SEQUENCE "%s"' % seq_name)
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    for field in fields:
        if field['primary_key']:
            primary_key = field['field_name']
            sql += '"%s" %s PRIMARY KEY DEFAULT NEXTVAL(\'"%s"\')' % \
                (field['field_name'], FIELD_TYPES[field['data_type']], seq_name)
        else:
            sql += '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['size'] != 0 and field['data_type'] == TEXT:
            sql += '(%d)' % field['size']
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                sql += " DEFAULT '%s'" % field['default_value']
            else:
                sql += ' DEFAULT %s' % field['default_value']
        sql +=  ',\n'
    sql = sql[:-2]
    sql += ')\n'
    result.append(sql)
    result.append('ALTER SEQUENCE "%s" OWNED BY "%s"."%s"' % (seq_name, table_name, primary_key))
    return result

def delete_table_sql(table_name, gen_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return 'CREATE %s INDEX "%s" ON "%s" (%s)' % \
        (unique, index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref, primary_key):
    return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s") MATCH SIMPLE' % \
        (table_name, index_name, key, ref, primary_key)

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s"' % index_name

def delete_foreign_index(table_name, index_name):
    return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s' % \
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
        raise Exception, u"Don't know how to change field's size or type of %s" % old_field['field_name']
    if old_field['field_name'] != new_field['field_name']:
        result.append('ALTER TABLE "%s" RENAME COLUMN  "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name']))
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = 'ALTER TABLE "%s" ALTER "%s" SET DEFAULT' % \
                    (table_name, new_field['field_name'])
                sql +=  " '%s'" % new_field['default_value']
            else:
                sql = 'ALTER TABLE "%s" ALTER "%s" SET DEFAULT %s' % \
                    (table_name, new_field['field_name'], new_field['default_value'])
        else:
            sql = 'ALTER TABLE "%s" alter "%s" DROP DEFAULT' % \
                (table_name, new_field['field_name'])
        result.append(sql)
    return result

def get_sequence_name(table_name):
    return '%s_ID_SEQ' % table_name

def next_sequence_value_sql(gen_name):
    return "SELECT NEXTVAL('%s')" % gen_name

def restart_sequence_sql(gen_name, value):
    return 'ALTER SEQUENCE "%s" RESTART WITH %d' % (gen_name, value)

def set_literal_case(name):
    return name.lower()

def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'")
    result = cursor.fetchall()
    return [r[1] for r in result]

def get_table_info(connection, table_name, db_name):
    cursor = connection.cursor()
    sql = "select column_name, data_type, character_maximum_length, column_default from information_schema.columns where table_name='%s'" % table_name
    cursor.execute(sql)
    result = cursor.fetchall()
    fields = []
    for column_name, data_type, character_maximum_length, column_default in result:
        try:
            if data_type == 'character varying':
                data_type = 'varchar'
            size = 0
            if character_maximum_length:
                size = character_maximum_length
            default_value = None
            if column_default:
                default_value = column_default.split('::')[0]
                if default_value.find('nextval') != -1:
                    default_value = None
        except:
            pass
        pk = False
        fields.append({
            'field_name': column_name,
            'data_type': data_type.upper(),
            'size': size,
            'default_value': column_default,
            'pk': pk
        })
    sql = "SELECT indexname FROM pg_indexes WHERE tablename = '%s'" % table_name
    cursor.execute(sql)
    result = cursor.fetchall()
    indexes = {}
    for indexname in result:
        indexname = indexname[0]
        sql = """
            SELECT i.indisunique AS IS_UNIQUE,
                   i.indisprimary AS IS_PRIMARY,
                   ci.relname AS INDEX_NAME,
                   (i.keys).n AS ORDINAL_POSITION,
                   pg_catalog.pg_get_indexdef(ci.oid, (i.keys).n, false) AS COLUMN_NAME,
                   CASE am.amcanorder
                     WHEN true THEN CASE i.indoption[(i.keys).n - 1] & 1
                       WHEN 1 THEN TRUE
                       ELSE FALSE
                     END
                     ELSE FALSE
                   END AS DESC
            FROM pg_catalog.pg_class ct
              JOIN pg_catalog.pg_namespace n ON (ct.relnamespace = n.oid)
              JOIN (SELECT i.indexrelid, i.indrelid, i.indoption,
                      i.indisunique, i.indisprimary, i.indisclustered, i.indpred,
                      i.indexprs,
                      information_schema._pg_expandarray(i.indkey) AS keys
                    FROM pg_catalog.pg_index i) i
                ON (ct.oid = i.indrelid)
              JOIN pg_catalog.pg_class ci ON (ci.oid = i.indexrelid)
              JOIN pg_catalog.pg_am am ON (ci.relam = am.oid)
            AND ct.relname = '%s' and ci.relname = '%s'
            ORDER BY ORDINAL_POSITION
        """
        cursor.execute(sql % (str(table_name), str(indexname)))
        result = cursor.fetchall()
        for is_unique, is_primary, index_name, ordinal_position, column_name, desc in result:
            if not is_primary:
                column_name = column_name.strip('"').strip("'")
                index = indexes.get(index_name)
                if not index:
                    index = {
                        'index_name': index_name,
                        'unique': is_unique,
                        'fields': []
                    }
                    indexes[index_name] = index
                index['fields'].append([column_name, desc])
    ind = []
    indexes.values()
    for key, value in indexes.iteritems():
        ind.append(value)
    return {'fields': fields, 'indexes': ind}

