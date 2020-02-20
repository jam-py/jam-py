import psycopg2
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

from ..common import consts
from .db import AbstractDB

class PostgresDB(AbstractDB):
    def __init__(self):
        AbstractDB.__init__(self)
        self.db_type = consts.POSTGRESQL
        self.DDL_ROLLBACK = True
        self.LIKE = 'ILIKE'
        self.DESC_NULLS = 'NULLS LAST'
        self.ASC_NULLS = 'NULLS FIRST'
        self.FIELD_TYPES = {
            consts.INTEGER: 'INTEGER',
            consts.TEXT: 'VARCHAR',
            consts.FLOAT: 'NUMERIC',
            consts.CURRENCY: 'NUMERIC',
            consts.DATE: 'DATE',
            consts.DATETIME: 'TIMESTAMP',
            consts.BOOLEAN: 'INTEGER',
            consts.LONGTEXT: 'TEXT',
            consts.KEYS: 'TEXT',
            consts.FILE: 'TEXT',
            consts.IMAGE: 'TEXT'
        }

    def get_params(self, lib):
        params = self.params
        params['name'] = 'POSTGRESQL'
        params['login'] = True
        params['password'] = True
        params['encoding'] = True
        params['host'] = True
        params['port'] = True
        return params

    def connect(self, db_info):
        return psycopg2.connect(dbname=db_info.database, user=db_info.user,
            password=db_info.password, host=db_info.host, port=db_info.port,
            client_encoding=db_info.encoding)

    def get_select(self, query, fields_clause, from_clause, where_clause, group_clause, order_clause, fields):
        start = fields_clause
        end = ''.join([from_clause, where_clause, group_clause, order_clause])
        offset = query['__offset']
        limit = query['__limit']
        result = 'SELECT %s FROM %s' % (start, end)
        if limit:
            result += ' LIMIT %d OFFSET %d' % (limit, offset)
        return result

    def value_literal(self, index):
        return '%s'

    def convert_like(self, field_name, val, data_type):
        return '%s::text' % field_name, val.upper()

    def create_table(self, table_name, fields, gen_name=None, foreign_fields=None):
        result = []
        primary_key = ''
        seq_name = gen_name
        sql = 'CREATE TABLE "%s"\n(\n' % table_name
        lines = []
        for field in fields:
            field_type = self.FIELD_TYPES[field.data_type]
            if field.primary_key:
                primary_key = field.field_name
                field_type = 'SERIAL PRIMARY KEY'# + field_type
            line = '"%s" %s' % (field.field_name, field_type)
            if field.size != 0 and field.data_type == consts.TEXT:
                line += '(%d)' % field.size
            default_value = self.default_value(field)
            if default_value and not field.primary_key:
                if default_value:
                    line += ' DEFAULT %s' % default_value
            lines.append(line)
        sql += ',\n'.join(lines)
        sql += ')\n'
        result.append(sql)
        return result

    def drop_table(self, table_name, gen_name):
        result = []
        result.append('DROP TABLE "%s"' % table_name)
        if gen_name:
            result.append('DROP SEQUENCE IF EXISTS "%s"' % gen_name)
        return result

    def create_index(self, index_name, table_name, unique, fields, desc):
        return 'CREATE %s INDEX "%s" ON "%s" (%s)' % (unique, index_name, table_name, fields)

    def create_foreign_index(self, table_name, index_name, key, ref, primary_key):
        return 'ALTER TABLE "%s" ADD CONSTRAINT "%s" FOREIGN KEY ("%s") REFERENCES "%s"("%s") MATCH SIMPLE' % \
            (table_name, index_name, key, ref, primary_key)

    def drop_foreign_index(self, table_name, index_name):
        return 'ALTER TABLE "%s" DROP CONSTRAINT "%s"' % (table_name, index_name)

    def add_field(self, table_name, field):
        result = 'ALTER TABLE "%s" ADD COLUMN "%s" %s' % \
            (table_name, field.field_name, self.FIELD_TYPES[field.data_type])
        if field.size:
            result += '(%d)' % field.size
        default_value = self.default_value(field)
        if default_value and not field.primary_key:
            if default_value:
                line += ' DEFAULT %s' % default_value
        return result

    def del_field(self, table_name, field):
        return 'ALTER TABLE "%s" DROP COLUMN "%s"' % (table_name, field.field_name)

    def change_field(self, table_name, old_field, new_field):
        result = []
        if self.FIELD_TYPES[old_field.data_type] != self.FIELD_TYPES[new_field.data_type] \
            or old_field.size != new_field.size:
            raise Exception("Changing field size or type is prohibited: field %s, table name %s" % \
                (old_field.field_name, table_name))
        if old_field.field_name != new_field.field_name:
            result.append('ALTER TABLE "%s" RENAME COLUMN  "%s" TO "%s"' % \
                (table_name, old_field.field_name, new_field.field_name))
        if old_field.default_value != new_field.default_value:
            default_value = self.default_value(new_field)
            if default_value:
                sql = 'ALTER TABLE "%s" ALTER "%s" SET DEFAULT %s' % \
                    (table_name, new_field.field_name, default_value)
            else:
                sql = 'ALTER TABLE "%s" alter "%s" DROP DEFAULT' % \
                    (table_name, new_field.field_name)
            result.append(sql)
        return result

    def insert_query(self, pk_field):
        return 'INSERT INTO "%s" (%s) VALUES (%s) RETURNING ' + pk_field.db_field_name

    def before_insert(self, cursor, pk_field):
        if pk_field and pk_field.owner.gen_name and not pk_field.data:
            cursor.execute(self.next_sequence(pk_field.owner.gen_name))
            rows = cursor.fetchall()
            pk_field.data = rows[0][0]

    def after_insert(self, cursor, pk_field):
        if pk_field and not pk_field.owner.gen_name and not pk_field.data:
            pk_field.data = cursor.fetchone()[0]

    def next_sequence(self, gen_name):
        return 'SELECT NEXTVAL(\'"%s"\')' % gen_name

    def restart_sequence(self, gen_name, value):
        return 'ALTER SEQUENCE "%s" RESTART WITH %d' % (gen_name, value)

    def identifier_case(self, name):
        return name.lower()

    def get_table_names(self, connection):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'")
        result = cursor.fetchall()
        return [r[1] for r in result]

    def get_table_info(self, connection, table_name, db_name):
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
        return {'fields': fields, 'field_types': self.FIELD_TYPES}

db = PostgresDB()
