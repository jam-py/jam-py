from __future__ import division

import sys, os
import datetime
import traceback

from werkzeug._compat import string_types

from .common import consts, error_message

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
                changes.append({'log_id': info['log_id'], 'rec_id': rec_id, 'details': result_details})
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
        elif command_type == dict:
            res = execute_delta(cursor, db_module, com, params, delta_result)
        elif command_type == list:
            res = execute_list(cursor, db_module, com, delta_result, params, select)
        elif command_type == tuple:
            res = execute_command(cursor, db_module, com[0], com[1], select)
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

