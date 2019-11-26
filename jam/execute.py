from __future__ import division

import sys, os
import json
import datetime
import traceback

from werkzeug._compat import string_types

from .common import consts, error_message, json_defaul_handler

def execute_select(cursor, db_module, command):
    # ~ print('')
    # ~ print(command)
    try:
        cursor.execute(command)
    except Exception as x:
        consts.app.log.exception(error_message(x))
        # ~ print('\nError: %s\n command: %s' % (str(x), command))
        raise
    return db_module.process_sql_result(cursor.fetchall())

def execute(cursor, command, params=None):
    # ~ print('')
    # ~ print(command)
    # ~ print(params)
    try:
        if params:
            cursor.execute(command, params)
        else:
            cursor.execute(command)
    except Exception as x:
        consts.app.log.exception(error_message(x))
        # ~ print('\nError: %s\n command: %s\n params: %s' % (str(x), command, params))
        raise

def execute_command(cursor, db_module, command, params=None, select=False):
    if select:
        result = execute_select(cursor, db_module, command)
    else:
        result = execute(cursor, command, params)
    return result

def process_delta(cursor, db_module, delta, master_rec_id, result):
    ID, sqls = delta
    result['ID'] = ID
    changes = []
    result['changes'] = changes
    for sql in sqls:
        (command, params, info, h_sql, h_params, h_del_details), details = sql
        if h_del_details:
            for d_select, d_sql, d_params in h_del_details:
                ids = execute_select(cursor, db_module, d_select)
                for i in ids:
                    d_params[1] = i[0]
                    execute(cursor, d_sql, db_module.process_sql_params(d_params, cursor))
        if info:
            rec_id = info.get('pk')
            inserted = info.get('inserted')
            if inserted:
                master_pk_index = info.get('master_pk_index')
                if master_pk_index:
                    params[master_pk_index] = master_rec_id
                pk_index = info.get('pk_index')
                gen_name = info.get('gen_name')
                if not rec_id and db_module.get_lastrowid is None and gen_name and \
                    not pk_index is None and pk_index >= 0:
                    next_sequence_value_sql = db_module.next_sequence_value_sql(gen_name)
                    if next_sequence_value_sql:
                        cursor.execute(next_sequence_value_sql)
                        rec = cursor.fetchone()
                        rec_id = rec[0]
                        params[pk_index] = rec_id
            if params:
                params = db_module.process_sql_params(params, cursor)
            if command:
                before = info.get('before_command')
                if before:
                    execute(cursor, before)
                execute(cursor, command, params)
                after = info.get('after_command')
                if after:
                    execute(cursor, after)
            if inserted and not rec_id and db_module.get_lastrowid:
                rec_id = db_module.get_lastrowid(cursor)
            result_details = []
            if rec_id:
                changes.append([info['log_id'], rec_id, result_details])
            for detail in details:
                result_detail = {}
                result_details.append(result_detail)
                process_delta(cursor, db_module, detail, rec_id, result_detail)
        elif command:
                execute(cursor, command, params)
        if h_sql:
            if not h_params[1]:
                h_params[1] = rec_id
            h_params = db_module.process_sql_params(h_params, cursor)
            execute(cursor, h_sql, h_params)

def execute_delta(cursor, db_module, command, params, delta_result):
    delta = command['delta']
    process_delta(cursor, db_module, delta, None, delta_result)

def execute_list(cursor, db_module, command, delta_result, params, select):
    res = None
    for com in command:
        command_type = type(com)
        if command_type in string_types:
            res = execute_command(cursor, db_module, com, params, select)
        elif command_type == list:
            res = execute_list(cursor, db_module, com, delta_result, params, select)
        elif command_type == tuple:
            res = execute_command(cursor, db_module, com[0], com[1], select)
        elif command_type == dict:
            res = execute_delta(cursor, db_module, com, params, delta_result)
        elif not com:
            pass
        else:
            raise Exception('server_classes execute_list: invalid argument - command: %s' % command)
    return res

def execute_sql_connection(connection, command, params, select, db_module, close_on_error=False, autocommit=True):
    delta_result = {}
    result = None
    error = None
    info = ''
    try:
        cursor = connection.cursor()
        command_type = type(command)
        if command_type in string_types:
            result = execute_command(cursor, db_module, command, params, select)
        elif command_type == dict:
            res = execute_delta(cursor, db_module, command, params, delta_result)
        elif command_type == list:
            result = execute_list(cursor, db_module, command, delta_result, params, select)
        else:
            result = execute_command(cursor, db_module, command, params, select)
        if autocommit:
            if select:
                connection.rollback()
            else:
                connection.commit()
        if delta_result:
            result = delta_result
    except Exception as x:
        try:
            if connection:
                connection.rollback()
                if close_on_error:
                    connection.close()
            error = str(x)
            if not error:
                error = 'SQL execution error'
            traceback.print_exc()
        finally:
            if close_on_error:
                connection = None
    finally:
        result = connection, (result, error)
    return result

def execute_sql(db_module, db_server, db_database, db_user, db_password,
    db_host, db_port, db_encoding, connection, command,
    params=None, select=False):

    if connection is None:
        try:
            connection = db_module.connect(db_database, db_user, db_password, db_host, db_port, db_encoding, db_server)
        except Exception as x:
            consts.app.log.exception(error_message(x))
            # ~ print(str(x))
            return  None, (None, str(x))
    return execute_sql_connection(connection, command, params, select, db_module, close_on_error=True)

def apply_sql(item, params=None, db_module=None): #depricated

    def get_user(item):
        user = None
        if item.session:
            try:
                user = item.session.get('user_info')['user_name']
            except:
                pass
        return user

    def insert_sql(item, db_module):
        info = {
            'gen_name': item.gen_name,
            'inserted': True
        }
        if item._deleted_flag:
            item._deleted_flag_field.data = 0
        row = []
        fields = []
        values = []
        index = 0
        pk = None
        if item._primary_key:
            pk = item._primary_key_field
        auto_pk = not db_module.get_lastrowid is None
        if auto_pk and pk and pk.data:
            if hasattr(db_module, 'set_identity_insert'):
                info['before_command'] = db_module.set_identity_insert(item.table_name, True)
                info['after_command'] = db_module.set_identity_insert(item.table_name, False)
        for field in item.fields:
            if not (field.master_field or (field == pk and auto_pk and not pk.data)):
                if field == pk:
                    info['pk_index'] = index
                elif item.master and field == item._master_rec_id_field:
                    info['master_pk_index'] = index
                index += 1
                fields.append('"%s"' % field.db_field_name)
                values.append('%s' % db_module.value_literal(index))
                value = (field.data, field.data_type)
                row.append(value)

        fields = ', '.join(fields)
        values = ', '.join(values)
        sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
            (item.table_name, fields, values)
        return sql, row, info

    def update_sql(item, db_module):
        row = []
        fields = []
        index = 0
        pk = item._primary_key_field
        command = 'UPDATE "%s" SET ' % item.table_name
        for field in item.fields:
            if not (field.master_field or field == pk):
                index += 1
                fields.append('"%s"=%s' % (field.db_field_name, db_module.value_literal(index)))
                value = (field.data, field.data_type)
                if field.field_name == item._deleted_flag:
                    value = (0, field.data_type)
                row.append(value)
        fields = ', '.join(fields)
        if item._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % item._primary_key_field.value
        else:
            id_literal = "%s" % item._primary_key_field.value
        where = ' WHERE "%s" = %s' % (item._primary_key_db_field_name, id_literal)
        return ''.join([command, fields, where]), row

    def delete_sql(item, db_module):
        soft_delete = item.soft_delete
        if item.master:
            soft_delete = item.master.soft_delete
        if item._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % item._primary_key_field.value
        else:
            id_literal = "%s" % item._primary_key_field.value
        if soft_delete:
            sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                (item.table_name, item._deleted_flag_db_field_name,
                item._primary_key_db_field_name, id_literal)
        else:
            sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                (item.table_name, item._primary_key_db_field_name, id_literal)
        return sql

    def get_sql(item, safe, db_module):
        info = {}
        if item.master:
            if item._master_id:
                item._master_id_field.data = item.master.ID
            item._master_rec_id_field.data = item.master._primary_key_field.value
        if item.record_status == consts.RECORD_INSERTED:
            if safe and not item.can_create():
                raise Exception(consts.language('cant_create') % item.item_caption)
            sql, param, info = insert_sql(item, db_module)
        elif item.record_status == consts.RECORD_MODIFIED:
            if safe and not item.can_edit():
                raise Exception(consts.language('cant_edit') % item.item_caption)
            sql, param = update_sql(item, db_module)
        elif item.record_status == consts.RECORD_DETAILS_MODIFIED:
            sql, param = '', None
        elif item.record_status == consts.RECORD_DELETED:
            if safe and not item.can_delete():
                raise Exception(consts.language('cant_delete') % item.item_caption)
            sql = delete_sql(item, db_module)
            param = None
        else:
            raise Exception('apply_sql - invalid %s record_status %s, record: %s' % \
                (item.item_name, item.record_status, item._dataset[item.rec_no]))
        if item._primary_key:
            info['pk'] = item._primary_key_field.value
        info['ID'] = item.ID
        info['log_id'] = item.get_rec_info()[consts.REC_LOG_REC]
        h_sql, h_params, h_del_details = get_history_sql(item, db_module)
        return sql, param, info, h_sql, h_params, h_del_details

    def delete_detail_sql(item, detail, db_module, result):
        ID, delete_sql = result
        h_sql = None
        h_params = None
        h_del_details = None
        if item._primary_key_field.data_type == consts.TEXT:
            id_literal = "'%s'" % item._primary_key_field.value
        else:
            id_literal = "%s" % item._primary_key_field.value
        if detail._master_id:
            if item.soft_delete:
                sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s AND "%s" = %s' % \
                    (detail.table_name, detail._deleted_flag_db_field_name, detail._master_id_db_field_name, \
                    item.ID, detail._master_rec_id_db_field_name, id_literal)
            else:
                sql = 'DELETE FROM "%s" WHERE "%s" = %s AND "%s" = %s' % \
                    (detail.table_name, detail._master_id_db_field_name, item.ID, \
                    detail._master_rec_id_db_field_name, id_literal)
        else:
            if item.soft_delete:
                sql = 'UPDATE "%s" SET "%s" = 1 WHERE "%s" = %s' % \
                    (detail.table_name, detail._deleted_flag_db_field_name, \
                    detail._master_rec_id_db_field_name, id_literal)
            else:
                sql = 'DELETE FROM "%s" WHERE "%s" = %s' % \
                    (detail.table_name, detail._master_rec_id_db_field_name, id_literal)
            h_sql, h_params, h_del_details = get_history_sql(detail, db_module)
        details = []
        if len(detail.details):
            item.update_deleted([detail])
            for it in detail:
                for d in detail.details:
                    d_sql = []
                    d_result = (str(d.ID), d_sql)
                    details.append(d_result)
                    detail.delete_detail_sql(d, db_module, d_result)
        delete_sql.append(((sql, None, {'ID': ID}, h_sql, h_params, h_del_details), details))

    def get_history_sql(item, db_module):
        h_sql = None
        h_params = None
        h_del_details = None
        if item.task.history_item and item.keep_history and item.record_status != consts.RECORD_DETAILS_MODIFIED:
            deleted_flag = item.task.history_item._deleted_flag
            user_info = None
            if item.session:
                user_info = item.session.get('user_info')
            h_fields = ['item_id', 'item_rec_id', 'operation', 'changes', 'user', 'date']
            table_name = item.task.history_item.table_name
            fields = []
            for f in h_fields:
                fields.append(item.task.history_item._field_by_name(f).db_field_name)
            h_fields = fields
            index = 0
            fields = []
            values = []
            index = 0
            for f in h_fields:
                index += 1
                fields.append('"%s"' % f)
                values.append('%s' % db_module.value_literal(index))
            fields = ', '.join(fields)
            values = ', '.join(values)
            h_sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
                (table_name, fields, values)
            changes = None
            user = None
            item_id = item.ID
            if item.master:
                item_id = item.prototype.ID
            if user_info:
                try:
                    user = user_info['user_name']
                except:
                    pass
            if item.record_status != consts.RECORD_DELETED:
                old_rec = item.get_rec_info()[consts.REC_OLD_REC]
                new_rec = item._dataset[item.rec_no]
                f_list = []
                for f in item.fields:
                    if not f.system_field():
                        new = new_rec[f.bind_index]
                        old = None
                        if old_rec:
                            old = old_rec[f.bind_index]
                        if old != new:
                            f_list.append([f.ID, new])
                changes_str = json.dumps(f_list, separators=(',',':'), default=json_defaul_handler)
                changes = ('%s%s' % ('0', changes_str), consts.LONGTEXT)
            elif not item.master and item.details:
                h_del_details = []
                for detail in item.details:
                    if detail.keep_history:
                        d_select = 'SELECT "%s" FROM "%s" WHERE "%s" = %s AND "%s" = %s' % \
                            (detail._primary_key_db_field_name, detail.table_name,
                            detail._master_id_db_field_name, item.ID,
                            detail._master_rec_id_db_field_name, item._primary_key_field.value)
                        d_sql = h_sql
                        d_params = [detail.prototype.ID, None, consts.RECORD_DELETED, None, user, datetime.datetime.now()]
                        h_del_details.append([d_select, d_sql, d_params])
            h_params = [item_id, item._primary_key_field.value, item.record_status, changes, user, datetime.datetime.now()]
        return h_sql, h_params, h_del_details

    def generate_sql(item, safe, db_module, result):
        ID, sql = result
        for it in item:
            details = []
            sql.append((get_sql(it, safe, db_module), details))
            for detail in item.details:
                detail_sql = []
                detail_result = (str(detail.ID), detail_sql)
                details.append(detail_result)
                if item.record_status == consts.RECORD_DELETED:
                    delete_detail_sql(item, detail, db_module, detail_result)
                else:
                    generate_sql(detail, safe, db_module, detail_result)

    safe = False
    if params:
        safe = params['__safe']
    if db_module is None:
        db_module = item.task.db_module
    result = (item.ID, [])
    generate_sql(item, safe, db_module, result)
    return {'delta': result}
