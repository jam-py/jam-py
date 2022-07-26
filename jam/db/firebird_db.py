import fdb

from werkzeug._compat import text_type, to_bytes, to_unicode

from ..common import consts
from .db import AbstractDB

class FirebirdDB(AbstractDB):
    def __init__(self):
        AbstractDB.__init__(self)
        self.db_type = consts.FIREBIRD
        self.DDL_ROLLBACK = True
        self.NEED_GENERATOR = True
        self.FIELD_TYPES = {
            consts.INTEGER: 'INTEGER',
            consts.TEXT: 'VARCHAR',
            consts.FLOAT: 'DOUBLE PRECISION',
            consts.CURRENCY: 'DOUBLE PRECISION',
            consts.DATE: 'DATE',
            consts.DATETIME: 'TIMESTAMP',
            consts.BOOLEAN: 'INTEGER',
            consts.LONGTEXT: 'BLOB',
            consts.KEYS: 'BLOB',
            consts.FILE: 'VARCHAR(512)',
            consts.IMAGE: 'VARCHAR(256)'
        }

    def get_params(self, lib):
        params = self.params
        params['name'] = 'FIREBIRD'
        params['login'] = True
        params['password'] = True
        params['encoding'] = True
        params['host'] = True
        params['port'] = True
        return params

    def connect(self, db_info):
        if not db_info.database:
            raise Exception('Must supply database')
        return fdb.connect(database=db_info.database, user=db_info.user,
            password=db_info.password, charset=db_info.encoding,
            host=db_info.host, port=db_info.port)

    def get_select(self, query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
        start = fields_clause
        end = ''.join([from_clause, where_clause, group_clause, order_clause])
        offset = query.offset
        limit = query.limit
        page = ''
        if limit:
            page = 'FIRST %d SKIP %d' % (limit, offset)
        return 'SELECT %s %s FROM %s' % (page, start, end)

    def process_query_params(self, params, cursor):
        result = []
        for p in params:
            if type(p) == tuple:
                value, data_type = p
                if data_type in [consts.LONGTEXT, consts.KEYS]:
                    if type(value) == text_type:
                        value = to_bytes(value, 'utf-8')
            else:
                value = p
            result.append(value)
        return result

    def process_query_result(self, rows):
        result = []
        for row in rows:
            new_row = []
            for r in row:
                if isinstance(r, fdb.fbcore.BlobReader):
                    r = to_unicode(r.read(), 'utf-8')
                elif type(r) == bytes:
                    r = to_unicode(r, 'utf-8')
                new_row.append(r)
            result.append(new_row)
        return result

    def create_table(self, table_name, fields, gen_name=None, foreign_fields=None):
        result = []
        primary_key = ''
        sql = 'CREATE TABLE "%s"\n(\n' % table_name
        lines = []
        for field in fields:
            default_text = self.default_text(field)
            line = '"%s" %s' % (field.field_name, self.FIELD_TYPES[field.data_type])
            if field.size != 0 and field.data_type == consts.TEXT:
                line += '(%d)' % field.size
            if not default_text is None:
                line += ' DEFAULT %s' % default_text
            lines.append(line)
            if field.primary_key:
                primary_key = field.field_name
        if primary_key:
            lines.append('CONSTRAINT %s_PR_INDEX PRIMARY KEY ("%s")\n' % \
                (table_name, primary_key))
        sql += ',\n'.join(lines)
        sql += ')\n'
        result.append(sql)
        if primary_key:
            result.append('CREATE SEQUENCE "%s"' % gen_name)
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
        return 'ALTER TABLE "%s" DROP "%s"' % (table_name, field.field_name)

    def change_field(self, table_name, old_field, new_field):
        result = []
        field_info = self.get_field_info(old_field.field_name, table_name)
        if old_field.field_name != new_field.field_name:
            line = 'ALTER TABLE "%s" ALTER "%s" TO "%s"' % \
                (table_name, old_field.field_name, new_field.field_name)
            result.append(line)
        if old_field.size != new_field.size:
            if field_info['data_type'].upper() in ['CHAR', 'VARCHAR', 'NCHAR'] and \
                field_info['size'] < new_field.size:
                line = 'ALTER TABLE "%s" ALTER "%s" TYPE %s(%d) ' % \
                    (table_name, new_field.field_name, field_info['data_type'], new_field.size)
                result.append(line)
        if old_field.default_value != new_field.default_value:
            default_text = self.default_text(new_field)
            if default_text is None:
                line = 'DROP DEFAULT'
            else:
                line = 'SET DEFAULT %s' % default_text
            result.append(line)
        return result

    def drop_table(self, table_name, gen_name):
        result = ['DROP TABLE "%s"' % table_name]
        if gen_name:
            result.append('DROP SEQUENCE "%s"' % gen_name)
        return result

    def create_index(self, index_name, table_name, unique, fields, desc):
        return 'CREATE %s %s INDEX "%s" ON "%s" (%s)' % \
            (unique, desc, index_name, table_name, fields)

    def drop_index(self, table_name, index_name):
        return 'DROP INDEX "%s"' % index_name

    def create_foreign_index(self, table_name, index_name, key, ref, primary_key):
        return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s")' % \
            (table_name, index_name, key, ref, primary_key)

    def drop_foreign_index(self, table_name, index_name):
        return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

    def before_insert(self, cursor, pk_field):
        if pk_field and not pk_field.data:
            cursor.execute(self.next_sequence(pk_field.owner.gen_name))
            rows = cursor.fetchall()
            pk_field.data = rows[0][0]

    def next_sequence(self, gen_name):
        return 'SELECT NEXT VALUE FOR "%s" FROM RDB$DATABASE' % gen_name

    def restart_sequence(self, gen_name, value):
        return 'ALTER SEQUENCE %s RESTART WITH %d' % (gen_name, value)

    def get_table_names(self, connection):
        cursor = connection.cursor()
        cursor.execute('''
            SELECT RDB$RELATION_NAME FROM RDB$RELATIONS
            WHERE (RDB$SYSTEM_FLAG <> 1 OR RDB$SYSTEM_FLAG IS NULL)
            AND RDB$VIEW_BLR IS NULL
        ''')
        result = cursor.fetchall()
        return [r[0] for r in result]

    def get_table_info(self, connection, table_name, db_name):
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
                'pk': False,
            })
        return {'fields': fields, 'field_types': self.FIELD_TYPES}

db = FirebirdDB()
