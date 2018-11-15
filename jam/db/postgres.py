import psycopg2
from werkzeug._compat import PY2, iteritems, text_type, to_bytes, to_unicode

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
DESC = 'DESC NULLS LAST'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, KEYS, FILE, IMAGE = range(1, 12)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'VARCHAR',
    FLOAT: 'NUMERIC',
    CURRENCY: 'NUMERIC',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'INTEGER',
    LONGTEXT: 'TEXT',
    KEYS: 'TEXT',
    FILE: 'TEXT',
    IMAGE: 'TEXT'
}

def connect(database, user, password, host, port, encoding, server):
    return psycopg2.connect(dbname=database, user=user, password=password, host=host, port=port)

get_lastrowid = None

def get_select(query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
    start = fields_clause
    end = ''.join([from_clause, where_clause, group_clause, order_clause])
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
        else:
            value = p
        result.append(value)
    return result

#~ def process_sql_result(rows):
    #~ return [list(row) for row in rows]

def process_sql_result(rows):
    result = []
    for row in rows:
        fields = []
        for field in row:
            if PY2:
                if type(field) == buffer:
                    field = str(field)
            else:
                if type(field) == memoryview:
                    field = to_unicode(to_bytes(field, 'utf-8'), 'utf-8')
            fields.append(field)
        result.append(fields)
    return result

def cast_date(date_str):
    return "CAST('" + date_str + "' AS DATE)"

def cast_datetime(datetime_str):
    return "CAST('" + datetime_str + "' AS TIMESTAMP)"

def value_literal(index):
    return '%s'

def convert_like(field_name, val, data_type):
    return '%s::text' % field_name, val.upper()

def create_table_sql(table_name, fields, gen_name=None, foreign_fields=None):
    result = []
    primary_key = ''
    seq_name = gen_name
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    lines = []
    for field in fields:
        line = '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['size'] != 0 and field['data_type'] == TEXT:
            line += '(%d)' % field['size']
        if field['primary_key']:
            primary_key = field['field_name']
            line += ' PRIMARY KEY DEFAULT NEXTVAL(\'"%s"\')' % seq_name
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                line += " DEFAULT '%s'" % field['default_value']
            else:
                line += ' DEFAULT %s' % field['default_value']
        lines.append(line)
    sql += ',\n'.join(lines)
    sql += ')\n'
    result.append(sql)
    if primary_key:
        result.insert(0, 'CREATE SEQUENCE "%s"' % seq_name)
        result.append('ALTER SEQUENCE "%s" OWNED BY "%s"."%s"' % (seq_name, table_name, primary_key))
    return result

def delete_table_sql(table_name, gen_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    result.append('DROP SEQUENCE IF EXISTS "%s"' % gen_name)
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
        raise Exception(u"Don't know how to change field's size or type of %s" % old_field['field_name'])
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

def next_sequence_value_sql(gen_name):
    return 'SELECT NEXTVAL(\'"%s"\')' % gen_name

def restart_sequence_sql(gen_name, value):
    return 'ALTER SEQUENCE "%s" RESTART WITH %d' % (gen_name, value)

def identifier_case(name):
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
    return {'fields': fields, 'field_types': FIELD_TYPES}

