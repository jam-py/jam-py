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

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, BLOB, KEYS = range(1, 10)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'TEXT',
    FLOAT: 'REAL',
    CURRENCY: 'REAL',
    DATE: 'TEXT',
    DATETIME: 'TEXT',
    BOOLEAN: 'INTEGER',
    BLOB: 'BLOB',
    KEYS: 'TEXT'
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
    return [list(row) for row in rows]

def cast_date(date_str):
    return "'%s'" % date_str

def cast_datetime(datetime_str):
    return "'%s'" % datetime_str

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

def get_sequence_name(table_name):
    return None

def next_sequence_value_sql(table_name):
    return None

def restart_sequence_sql(table_name, value):
    pass

def set_literal_case(name):
    return name.upper()

def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    result = cursor.fetchall()
    return [r[1] for r in result]

def get_table_info(connection, table_name, db_name):
    cursor = connection.cursor()
    cursor.execute('PRAGMA table_info(%s)' % table_name)
    result = cursor.fetchall()
    fields = []
    for r in result:
        fields.append({
            'field_name': r[1],
            'data_type': r[2],
            'size': 0,
            'default_value': r[4],
            'pk': r[5]==1
        })
    return {'fields': fields, 'field_types': FIELD_TYPES}



