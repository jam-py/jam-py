from __future__ import division

import sys, os
import datetime
import traceback

import jam.common as common
import jam.db.db_modules as db_modules
from werkzeug._compat import string_types


def execute_select(cursor, db_module, command):
    #~ print('')
    #~ print(command)
    try:
        cursor.execute(command)
    except Exception as x:
        print('\nError: %s\n command: %s' % (str(x), command))
        raise
    return db_module.process_sql_result(cursor.fetchall())

def execute(cursor, command, params=None):
    #~ print('')
    #~ print(command)
    #~ print(params)
    try:
        if params:
            cursor.execute(command, params)
        else:
            cursor.execute(command)
    except Exception as x:
        print('\nError: %s\n command: %s\n params: %s' % (str(x), command, params))
        raise

def info_from_error(err):
    arr = str(err).split('\\n')
    error = '<br>'.join(arr)
    return '<div class="text-error">%s</div>' % error

def execute_dll(cursor, db_module, command, params, messages):
    try:
        result = None
        print('')
        print(command)
        if params:
            print(params)
            messages.append('<p>' + command + '<br>' + \
                json.dumps(params, default=common.json_defaul_handler) + '</p>')
        else:
            messages.append('<p>' + command + '</p>')
        result = execute(cursor, command, params)
    except Exception as x:
        error = '\nError: %s\n command: %s\n params: %s' % (str(x), command, params)
        print(error)
        messages.append(info_from_error(x))
        if db_module.DDL_ROLLBACK:
            raise

def execute_command(cursor, db_module, command, params=None, select=False, ddl=False, messages=None):
    if select:
        result = execute_select(cursor, db_module, command)
    elif ddl:
        result = execute_dll(cursor, db_module, command, params, messages)
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
                    d_params = db_module.process_sql_params(d_params, cursor)
                    execute(cursor, d_sql, d_params)
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

def execute_list(cursor, db_module, command, delta_result, params, select, ddl, messages):
    res = None
    for com in command:
        command_type = type(com)
        if command_type in string_types:
            res = execute_command(cursor, db_module, com, params, select, ddl, messages)
        elif command_type == dict:
            res = execute_delta(cursor, db_module, com, params, delta_result)
        elif command_type == list:
            res = execute_list(cursor, db_module, com, delta_result, params, select, ddl, messages)
        elif command_type == tuple:
            res = execute_command(cursor, db_module, com[0], com[1], select, ddl, messages)
        elif not com:
            pass
        else:
            raise Exception('server_classes execute_list: invalid argument - command: %s' % command)
    return res

def execute_sql_connection(connection, command, params, call_proc, select, ddl, db_module, close_on_error=False):
    delta_result = {}
    messages = []
    result = None
    error = None
    info = ''
    try:
        cursor = connection.cursor()
        if call_proc:
            try:
                cursor.callproc(command, params)
                result = cursor.fetchone()
            except Exception as x:
                print('\nError: %s in command: %s' % (str(x), command))
                raise
        else:
            command_type = type(command)
            if command_type in string_types:
                result = execute_command(cursor, db_module, command, params, select, ddl, messages)
            elif command_type == dict:
                res = execute_delta(cursor, db_module, command, params, delta_result)
            elif command_type == list:
                result = execute_list(cursor, db_module, command, delta_result, params, select, ddl, messages)
            else:
                result = execute_command(cursor, db_module, command, params, select, ddl, messages)
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
        if ddl:
            if error:
                messages.append(info_from_error(error))
            if messages:
                info = ''.join(messages)
            result = connection, (result, error, info)
        else:
            result = connection, (result, error)
    return result

def execute_sql(db_module, db_server, db_database, db_user, db_password,
    db_host, db_port, db_encoding, connection, command,
    params=None, call_proc=False, select=False, ddl=False):

    if connection is None:
        try:
            connection = db_module.connect(db_database, db_user, db_password, db_host, db_port, db_encoding, db_server)
        except Exception as x:
            print(str(x))
            if ddl:
                return  None, (None, str(x), info_from_error(x))
            else:
                return  None, (None, str(x))
    return execute_sql_connection(connection, command, params, call_proc, select, ddl, db_module, close_on_error=True)

def process_request(parentPID, name, queue, db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding, mod_count):
    con = None
    counter = 0
    last_date = datetime.datetime.now()
    db_module = db_modules.get_db_module(db_type)
    while True:
        if parentPID and hasattr(os, 'getppid') and os.getppid() != parentPID:
            break
        request = queue.get()
        if request:
            result_queue = request['queue']
            command = request['command']
            params = request['params']
            call_proc = request['call_proc']
            select = request['select']
            cur_mod_count = request['mod_count']
            date = datetime.datetime.now()
            hours = (date - last_date).total_seconds() // 3600
            if cur_mod_count != mod_count or counter > 1000 or hours >= 1:
                if con:
                    try:
                        con.rollback()
                        con.close()
                    except:
                        pass
                con = None
                mod_count = cur_mod_count
                counter = 0
            last_date = date
            con, result = execute_sql(db_module, db_server, db_database, db_user, db_password,
                db_host, db_port, db_encoding, con, command, params, call_proc, select)
            counter += 1
            result_queue.put(result)

