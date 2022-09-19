import datetime

from ..common import to_bytes, to_str
from ..common import consts, error_message, QueryData
from ..db.databases import get_database

def copy_database(task, dbtype, connection, limit = 1000):

    def convert_sql(item, sql, db):
        new_case = item.task.db.identifier_case
        old_case = db.identifier_case
        if old_case('a') != new_case('a'):
            if new_case(item.table_name) == item.table_name:
                sql = sql.replace(item.table_name, old_case(item.table_name))
        return sql

    def drop_indexes():
        con = task.connect()
        try:
            cursor = con.cursor()
            from jam.admin.admin import drop_indexes_sql
            sqls = drop_indexes_sql(task.app.admin)
            for s in sqls:
                try:
                    cursor.execute(s)
                    con.commit()
                except Exception as e:
                    con.rollback()
                    pass
        finally:
            con.close()

    def restore_indexes():
        con = task.connect()
        try:
            cursor = con.cursor()
            from jam.admin.admin import restore_indexes_sql
            sqls = restore_indexes_sql(task.app.admin)
            for s in sqls:
                try:
                    cursor.execute(s)
                    con.commit()
                except Exception as e:
                    con.rollback()
                    pass
        finally:
            con.close()

    def get_rows(item, db, connection, loaded, limit):
        cursor = connection.cursor()
        order_by = []
        if item._primary_key_db_field_name:
            order_by = [item._primary_key_db_field_name]
        elif item == item.task.history_item:
            order_by = [item.item_id.db_field_name, item.item_rec_id.db_field_name]
        params = {'__expanded': False, '__offset': loaded, '__limit': limit,
            '__fields': [], '__filters': [], '__order': order_by}
        sql, params = db.get_select_statement(item, QueryData(params))
        sql = convert_sql(item, sql, db)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [list(row) for row in rows]

    def copy_sql(item):
        fields = []
        values = []
        index = 0
        for field in item.fields:
            if not field.master_field and not field.calculated:
                index += 1
                fields.append('"%s"' % field.db_field_name)
                values.append('%s' % task.db.value_literal(index))
        fields = ', '.join(fields)
        values = ', '.join(values)
        return 'INSERT INTO "%s" (%s) VALUES (%s)' % (item.table_name, fields, values)

    def copy_rows(item, db, con, sql, rows):
        error = None
        for i, r in enumerate(rows):
            j = 0
            for field in item.fields:
                if not field.master_field and not field.calculated:
                    if not r[j] is None:
                        if field.data_type == consts.INTEGER:
                            r[j] = int(r[j])
                        elif field.data_type in (consts.FLOAT, consts.CURRENCY):
                            r[j] = float(r[j])
                        elif field.data_type == consts.BOOLEAN:
                            if r[j]:
                                r[j] = 1
                            else:
                                r[j] = 0
                        elif field.data_type == consts.DATE and type(r[j]) == str:
                            r[j] = consts.convert_date(r[j])
                        elif field.data_type == consts.DATETIME and type(r[j]) == str:
                            r[j] = consts.convert_date_time(r[j])
                        elif field.data_type in [consts.LONGTEXT, consts.KEYS]:
                            if task.db.db_type == consts.FIREBIRD:
                                if type(r[j]) == str:
                                    r[j] = to_bytes(r[j], 'utf-8')
                            elif db.db_type == consts.FIREBIRD:
                                if type(r[j]) == bytes:
                                    r[j] = to_str(r[j], 'utf-8')
                    j += 1
        cursor = con.cursor()
        try:
            if hasattr(db, 'set_identity_insert'):
                if item._primary_key:
                    cursor.execute(db.set_identity_insert(item.table_name, True))
                new_rows = []
                for r in rows:
                    new_rows.append(tuple(r))
                rows = new_rows
            if hasattr(cursor, 'executemany'):
                cursor.executemany(sql, rows)
            else:
                for r in rows:
                    cursor.execute(sql, r)
            con.commit()
            if hasattr(db, 'set_identity_insert'):
                if item._primary_key:
                    cursor.execute(db.set_identity_insert(item.table_name, False))
        except Exception as e:
            task.log.exception(error_message(e))
            con.rollback()
        return error

    def count_records(item, db, con):
        params = {'__expanded': False, '__offset': 0, '__limit': 0, '__filters': [], '__fields': []}
        sql, params = db.get_record_count_query(item, QueryData(params))
        if db != item.task.db:
            sql = convert_sql(item, sql, db)
        cursor = con.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        return result[0][0]

    with task.lock('$copying database'):
        task.log.info('copying started')
        task.log.info('copying started')
        source_con = None
        con = task.connect()
        db = get_database(task.app, dbtype, None)
        task.log.info('copying droping indexes')
        drop_indexes()
        if hasattr(task.db, 'set_foreign_keys'):
            task.execute(task.db.set_foreign_keys(False))
        try:
            for group in task.items:
                for it in group.items:
                    if it.item_type != 'report':
                        item = it.copy(handlers=False, filters=False, details=False)
                        if item.table_name and not item.virtual_table:
                            rec_count = count_records(item, task.db, con)
                            record_count = count_records(item, db, connection)
                            loaded = 0
                            task.log.info('copying table %s records: %s' % (item.item_name, record_count))
                            if record_count and rec_count != record_count:
                                task.execute('DELETE FROM "%s"' % item.table_name)
                                sql = copy_sql(item)
                                while True:
                                    now = datetime.datetime.now()
                                    rows = get_rows(item, db, connection, loaded, limit)
                                    copy_rows(item, task.db, con, sql, rows)
                                    records = len(rows)
                                    loaded += records
                                    task.log.info('copying table %s: %d%%' % (item.item_name, int(loaded * 100 / record_count)))
                                    if records == 0 or records < limit:
                                        break
                                gen_name = item.gen_name
                                if task.db.db_type == consts.POSTGRESQL:
                                    if not gen_name and item._primary_key_db_field_name:
                                        gen_name = '%s_%s_%s' % (item.table_name, item._primary_key_db_field_name, 'seq')
                                if gen_name:
                                    cursor = con.cursor()
                                    cursor.execute('SELECT MAX("%s") FROM "%s"' % (item._primary_key_db_field_name, item.table_name))
                                    res = cursor.fetchall()
                                    max_pk = res[0][0]
                                    sql = task.db.before_restart_sequence(gen_name)
                                    if sql:
                                        cursor.execute(sql)
                                    sql = task.db.restart_sequence(gen_name, max_pk + 1)
                                    cursor.execute(sql)
                                    con.commit()
        except Exception as e:
            task.log.exception(error_message(e))
        finally:
            task.log.info('copying restoring indexes')
            restore_indexes()
            if hasattr(task.db, 'set_foreign_keys'):
                task.execute(task.db.set_foreign_keys(True))
        task.log.info('copying finished')

