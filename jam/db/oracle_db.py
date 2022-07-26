import cx_Oracle
from werkzeug._compat import text_type, to_bytes, to_unicode

from ..common import consts
from .db import AbstractDB

class OracleDB(AbstractDB):
    def __init__(self):
        AbstractDB.__init__(self)
        self.db_type = consts.ORACLE
        self.NEED_PASSWORD = True
        self.NEED_GENERATOR = True
        self.FROM = '"%s" %s '
        self.LEFT_OUTER_JOIN = 'LEFT OUTER JOIN "%s" %s'
        self.DESC = 'DESC NULLS LAST'
        self.IS_DISTINCT_FROM = 'DECODE(%s, %s, 0, 1) <> 0'
        self.FIELD_TYPES = {
            consts.INTEGER: 'NUMBER',
            consts.TEXT: 'VARCHAR2',
            consts.FLOAT: 'DOUBLE PRECISION',
            consts.CURRENCY: 'DOUBLE PRECISION',
            consts.DATE: 'DATE',
            consts.DATETIME: 'TIMESTAMP',
            consts.BOOLEAN: 'NUMBER',
            consts.LONGTEXT: 'CLOB',
            consts.KEYS: 'CLOB',
            consts.FILE: 'VARCHAR2(256)',
            consts.IMAGE: 'VARCHAR2(512)'
        }

    def get_params(self, lib):
        params = self.params
        params['name'] = 'ORACLE'
        params['dsn'] = True
        params['login'] = True
        params['password'] = True
        return params

    def connect(self, db_info):
        if db_info.dsn:
            return cx_Oracle.connect(dsn=db_info.dsn)
        else:
            return cx_Oracle.connect(user=db_info.user, password=db_info.password, dsn=db_info.database)

    def get_fields(self, query, fields, alias):
        sql = ''
        for field in fields:
            if field.master_field:
                pass
            else:
                sql += '%s."%s", ' % (alias, field.db_field_name)
        if query.expanded:
            for field in fields:
                if field.lookup_item:
                    sql += '%s_LOOKUP, ' % field.db_field_name
        sql = sql[:-2]
        return sql

    def get_select(self, query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
        start = fields_clause
        end = ''.join([from_clause, where_clause, group_clause, order_clause])
        offset = query.offset
        limit = query.limit
        result = 'SELECT %s FROM %s' % (start, end)
        if limit:
            flds = self.get_fields(query, fields, 'b')
            rnum = offset + 1
            rownum = offset + limit
            if offset == 0:
                rnum = 0
            result = "SELECT %s FROM (SELECT a.*, rownum rnum FROM (%s) a WHERE rownum <= %s) b WHERE rnum >= %s" % \
                (flds, result, rownum, rnum)
        return result

    def process_query_result(self, rows):
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

    def value_literal(self, index):
        return ':%d' % index

    def convert_like(self, field_name, val, data_type):
        if data_type in [consts.INTEGER, consts.FLOAT, consts.CURRENCY]:
            return 'TO_CHAR(%s, 99999999999990.999999999999)' % field_name, val
        else:
            return field_name, val

    def create_table(self, table_name, fields, gen_name=None, foreign_fields=None):
        result = []
        primary_key = ''
        sql = 'CREATE TABLE "%s"\n(\n' % table_name
        lines = []
        for field in fields:
            line = '"%s" %s' % (field.field_name, self.FIELD_TYPES[field.data_type])
            if field.size != 0 and field.data_type == consts.TEXT:
                line += '(%d)' % field.size
            if field.primary_key:
                primary_key = field.field_name
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

    def drop_table(self, table_name, gen_name):
        result = []
        result.append('DROP TABLE "%s"' % table_name)
        if gen_name:
            result.append('DROP SEQUENCE "%s"' % gen_name)
        return result

    def add_field(self, table_name, field):
        default_text = self.default_text(field)
        line = 'ALTER TABLE "%s" ADD "%s" %s' % \
            (table_name, field.field_name, self.FIELD_TYPES[field.data_type])
        if field.size:
            line += '(%d)' % field.size
        if not default_text is None:
            line += ' DEFAULT %s' % default_text
        return line

    def del_field(self, table_name, field):
        return 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field.field_name)

    def change_field(self, table_name, old_field, new_field):
        result = []
        default_text = self.default_text(new_field)
        field_info = self.get_field_info(old_field.field_name, table_name)
        if old_field.field_name != new_field.field_name:
            line = 'ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"' % \
                (table_name, old_field.field_name, new_field.field_name)
            result.append(line)
        if old_field.not_null != new_field.not_null or old_field.size != new_field.size:
            line = 'ALTER TABLE "%s" MODIFY "%s" %s' % \
                (table_name, new_field.field_name, field_info['data_type'])
            size = field_info['size']
            if size and field_info['data_type'].upper() in ['CHAR', 'NCHAR', 'VARCHAR2', 'VARCHAR', 'NVARCHAR2']:
                if new_field.size > size:
                    size = new_field.size
                line += '(%d)' % size
            if old_field.default_value != new_field.default_value:
                if not default_text is None:
                    line += ' DEFAULT %s' % default_text
                else:
                    line += ' DEFAULT NULL'
            result.append(line)
        return result

    def create_index(self, index_name, table_name, unique, fields, desc):
        return 'CREATE %s INDEX "%s" ON "%s" (%s)' % \
            (unique, index_name, table_name, fields)

    def create_foreign_index(self, table_name, index_name, key, ref, primary_key):
        return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s")' % \
            (table_name, index_name, key, ref, primary_key)

    def drop_index(self, table_name, index_name):
        return 'DROP INDEX "%s"' % index_name

    def drop_foreign_index(self, table_name, index_name):
        return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

    def before_insert(self, cursor, pk_field):
        if pk_field and not pk_field.data:
            cursor.execute(self.next_sequence(pk_field.owner.gen_name))
            rows = cursor.fetchall()
            pk_field.data = rows[0][0]

    def next_sequence(self, gen_name):
        return 'SELECT "%s".NEXTVAL FROM DUAL' % gen_name

    def before_restart_sequence(self, gen_name):
        return 'DROP SEQUENCE "%s"' % gen_name

    def restart_sequence(self, gen_name, value):
        return 'CREATE SEQUENCE "%s" START WITH %s' % (gen_name, value)

    def identifier_case(self, name):
        return name.upper()

    def get_table_names(self, connection):
        cursor = connection.cursor()
        cursor.execute('SELECT table_name FROM user_tables')
        result = cursor.fetchall()
        return [r[0] for r in result]

    def get_table_info(self, connection, table_name, db_name):
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
        return {'fields': fields, 'field_types': self.FIELD_TYPES}

db = OracleDB()
