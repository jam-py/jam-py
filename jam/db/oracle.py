import sys
import cx_Oracle
from werkzeug._compat import text_type, to_bytes, to_unicode

DATABASE = 'ORACLE'
NEED_DATABASE_NAME = True
NEED_LOGIN = True
NEED_PASSWORD = True
NEED_ENCODING = False
NEED_HOST = False
NEED_PORT = False
CAN_CHANGE_TYPE = False
CAN_CHANGE_SIZE = False
DDL_ROLLBACK = False
NEED_GENERATOR = True

FROM = '"%s" %s '
LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" %s'
FIELD_AS = 'AS'
LIKE = 'LIKE'
DESC = 'DESC NULLS LAST'

JAM_TYPES = TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, KEYS, FILE, IMAGE = range(1, 12)
FIELD_TYPES = {
    INTEGER: 'NUMBER',
    TEXT: 'VARCHAR2',
    FLOAT: 'DOUBLE PRECISION',
    CURRENCY: 'DOUBLE PRECISION',
    DATE: 'DATE',
    DATETIME: 'TIMESTAMP',
    BOOLEAN: 'NUMBER',
    LONGTEXT: 'CLOB',
    KEYS: 'CLOB',
    FILE: 'CLOB',
    IMAGE: 'CLOB'
}

def connect(database, user, password, host, port, encoding, server):
    if database and user and password:
        return cx_Oracle.connect(user=user, password=password, dsn=database)
    elif database:
        return cx_Oracle.connect(dsn=database)

get_lastrowid = None

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
    start = fields_clause
    end = ''.join([from_clause, where_clause, group_clause, order_clause])
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
                field = to_unicode(field, 'utf-8')
            fields.append(field)
        result.append(fields)
    return result

def cast_date(date_str):
    return "TO_DATE('" + date_str + "', 'YYYY-MM-DD')"

def cast_datetime(datetime_str):
    return "TO_DATE('" + date_str + "', 'YYYY-MM-DD  HH24:MI')"

def value_literal(index):
    return ':f%d' % index

def convert_like(field_name, val, data_type):
    if data_type in [INTEGER, FLOAT, CURRENCY]:
        return 'TO_CHAR(%s, 99999999999990.999999999999)' % field_name, val
    else:
        return field_name, val

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
        if field['primary_key']:
            primary_key = field['field_name']
        lines.append(line)
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
    return 'CREATE %s INDEX "%s" ON "%s" (%s)' % \
        (unique, index_name, table_name, fields)

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
    return 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field['field_name'])

def change_field_sql(table_name, old_field, new_field):
    result = []
    if FIELD_TYPES[old_field['data_type']] != FIELD_TYPES[new_field['data_type']] \
        or old_field['size'] != new_field['size']:
        raise Exception(u"Don't know how to change field's size or type of %s" % old_field['field_name'])
    if old_field['field_name'] != new_field['field_name']:
        sql = 'ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"' % \
            (table_name, old_field['field_name'], new_field['field_name'])
        result.append(sql)
    if old_field['default_value'] != new_field['default_value']:
        if new_field['default_value']:
            if new_field['data_type'] == TEXT:
                sql = 'ALTER TABLE "%s" MODIFY "%s" DEFAULT' % \
                    (table_name, new_field['field_name'])
                sql +=  " '%s'" % new_field['default_value']
            else:
                sql = 'ALTER TABLE "%s" MODIFY "%s" DEFAULT %s' % \
                    (table_name, new_field['field_name'], new_field['default_value'])
        else:
            sql = 'ALTER TABLE "%s" MODIFY "%s" DEFAULT %s' % \
                (table_name, new_field['field_name'], 'NULL')
        result.append(sql)
    return result

def param_literal():
    return '?'

def next_sequence_value_sql(gen_name):
    return 'SELECT "%s".NEXTVAL FROM DUAL' % gen_name

def restart_sequence_sql(gen_name, value):
    result = []
    result.append('DROP SEQUENCE "%s"' % gen_name)
    result.append('CREATE SEQUENCE "%s" START WITH %s' % (gen_name, value))
    return result

def identifier_case(name):
    return name.upper()

def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute('SELECT table_name FROM user_tables')
    result = cursor.fetchall()
    return [r[0] for r in result]

def get_table_info(connection, table_name, db_name):
    cursor = connection.cursor()
    sql = "SELECT COLUMN_NAME, DATA_TYPE, CHAR_LENGTH, DATA_DEFAULT FROM USER_TAB_COLUMNS WHERE TABLE_NAME='%s'" % table_name
    cursor.execute(sql)
    result = cursor.fetchall()
    fields = []
    for (field_name, data_type, size, default_value) in result:
        fields.append({
            'field_name': field_name,
            'data_type': data_type,
            'size': size,
            'default_value': default_value,
            'pk': False
        })
    return {'fields': fields, 'field_types': FIELD_TYPES}
