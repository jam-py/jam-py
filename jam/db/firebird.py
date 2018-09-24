import sys
import fdb
from werkzeug._compat import text_type, to_bytes, to_unicode

DATABASE = 'FIREBIRD'
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
LIKE = 'LIKE'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, KEYS, FILE, IMAGE = range(1, 12)
FIELD_TYPES = {
    INTEGER: 'INTEGER',
    TEXT: 'VARCHAR',
    FLOAT: 'DOUBLE PRECISION',
    CURRENCY: 'DOUBLE PRECISION',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'INTEGER',
    LONGTEXT: 'BLOB',
    KEYS: 'BLOB',
    FILE: 'VARCHAR(522)',
    IMAGE: 'VARCHAR(522)'
}

def connect(database, user, password, host, port, encoding, server):
    if not encoding:
        encoding = None
    if not port:
        port = None
    else:
        port = int(port)
    return fdb.connect(database=database, user=user, password=password, charset=encoding, host=host, port=port)

get_lastrowid = None

def get_select(query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
    start = fields_clause
    end = ''.join([from_clause, where_clause, group_clause, order_clause])
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
            if data_type in [LONGTEXT, KEYS]:
                if type(value) == text_type:
                    value = to_bytes(value, 'utf-8')
        else:
            value = p
        result.append(value)
    return result

def process_sql_result(rows):
    result = []
    for row in rows:
        new_row = []
        for r in row:
            if isinstance(r, fdb.fbcore.BlobReader):
                r = to_unicode(r.read(), 'utf-8')
            new_row.append(r)
        result.append(new_row)
    return result

def cast_date(date_str):
    return "CAST('" + date_str + "' AS DATE)"

def cast_datetime(datetime_str):
    return "CAST('" + datetime_str + "' AS TIMESTAMP)"

def value_literal(index):
    return '?'

def convert_like(field_name, val, data_type):
    return 'UPPER(%s)' % field_name, val.upper()

def create_table_sql(table_name, fields, gen_name=None, foreign_fields=None):
    result = []
    primary_key = ''
    sql = 'CREATE TABLE "%s"\n(\n' % table_name
    lines = []
    for field in fields:
        line = '"%s" %s' % (field['field_name'], FIELD_TYPES[field['data_type']])
        if field['size'] != 0 and field['data_type'] == TEXT:
            line += '(%d)' % field['size']
        if field['default_value'] and not field['primary_key']:
            if field['data_type'] == TEXT:
                line += " DEFAULT '%s'" % field['default_value']
            else:
                line += ' DEFAULT %s' % field['default_value']
        lines.append(line)
        if field['primary_key']:
            primary_key = field['field_name']
    if primary_key:
        lines.append('CONSTRAINT %s_PR_INDEX PRIMARY KEY ("%s")\n' % \
            (table_name, primary_key))
    sql += ',\n'.join(lines)
    sql += ')\n'
    result.append(sql)
    if primary_key:
        result.append('CREATE SEQUENCE "%s"' % gen_name)
    return result

def delete_table_sql(table_name, gen_name):
    result = []
    result.append('DROP TABLE "%s"' % table_name)
    if gen_name:
        result.append('DROP SEQUENCE "%s"' % gen_name)
    return result

def create_index_sql(index_name, table_name, unique, fields, desc):
    return 'CREATE %s %s INDEX "%s" ON "%s" (%s)' % \
        (unique, desc, index_name, table_name, fields)

def create_foreign_index_sql(table_name, index_name, key, ref, primary_key):
    return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s")' % \
        (table_name, index_name, key, ref, primary_key)

def delete_index(table_name, index_name):
    return 'DROP INDEX "%s"' % index_name

def delete_foreign_index(table_name, index_name):
    return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

def add_field_sql(table_name, field):
    result = 'ALTER TABLE "%s" ADD "%s" %s'
    result = result % (table_name, field['field_name'], FIELD_TYPES[field['data_type']])
    if field['size']:
        result += '(%d)' % field['size']
    if field['default_value']:
        if field['data_type'] == TEXT:
            result += " DEFAULT '%s'" % field['default_value']
        else:
            result += ' DEFAULT %s' % field['default_value']
    return result

def del_field_sql(table_name, field):
    return 'ALTER TABLE "%s" DROP "%s"' % (table_name, field['field_name'])

def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception(u"Don't know how to change field's size or type of %s, table name %s" % (old_field['field_name'], table_name))
    if old_field['field_name'] != new_field['field_name']:
        sql = 'ALTER TABLE "%s" ALTER "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name'])
        result.append(sql)
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
            sql = 'ALTER TABLE "%s" ALTER "%s" DROP DEFAULT' % \
                (table_name, new_field['field_name'])
        result.append(sql)
    return result

def next_sequence_value_sql(gen_name):
    return 'SELECT NEXT VALUE FOR "%s" FROM RDB$DATABASE' % gen_name

def restart_sequence_sql(gen_name, value):
    return 'ALTER SEQUENCE %s RESTART WITH %d' % (gen_name, value)

def identifier_case(name):
    return name.upper()

def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT RDB$RELATION_NAME FROM RDB$RELATIONS
        WHERE (RDB$SYSTEM_FLAG <> 1 OR RDB$SYSTEM_FLAG IS NULL)
        AND RDB$VIEW_BLR IS NULL
    ''')
    result = cursor.fetchall()
    return [r[0] for r in result]

def get_table_info(connection, table_name, db_name):
    cursor = connection.cursor()
    sql = '''
       SELECT RF.RDB$FIELD_NAME AS COLUMN_NAME,
            CASE F.RDB$FIELD_TYPE
                WHEN 7 THEN 'SMALLINT'
                WHEN 8 THEN 'INTEGER'
                WHEN 10 THEN 'FLOAT'
                WHEN 12 THEN 'DATE'
                WHEN 13 THEN 'TIME'
                WHEN 14 THEN 'CHAR'
                WHEN 16 THEN 'BIGINT'
                WHEN 27 THEN 'DOUBLE PRECISION'
                WHEN 35 THEN 'TIMESTAMP'
                WHEN 37 THEN 'VARCHAR'
                WHEN 261 THEN 'BLOB'
            END AS DATA_TYPE,
            F.RDB$FIELD_LENGTH,
            F.RDB$DEFAULT_VALUE
        FROM RDB$FIELDS F
            JOIN RDB$RELATION_FIELDS RF ON RF.RDB$FIELD_SOURCE = F.RDB$FIELD_NAME
        WHERE RF.RDB$RELATION_NAME = '%s'
    '''
    cursor.execute(sql % table_name)
    result = cursor.fetchall()
    fields = []
    for (field_name, data_type, size, default_value) in result:
        data_type = data_type.strip()
        if not data_type in ['VARCHAR', 'CHAR']:
            size = 0
        fields.append({
            'field_name': field_name.strip(),
            'data_type': data_type,
            'size': size,
            'default_value': default_value,
            'pk': False
        })
    return {'fields': fields, 'field_types': FIELD_TYPES}
