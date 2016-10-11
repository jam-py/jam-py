# -*- coding: utf-8 -*-

import os
import json
import hashlib
import datetime
import time
import zipfile
import shutil
import traceback
import sqlite3
from threading import Lock

from jsparser import parse, SyntaxError_

import common
import db.db_modules as db_modules
from server_classes import *
import lang.langs as langs
from events import get_events

def read_language(task):
    result = None
    sql = 'SELECT F_LANGUAGE FROM SYS_PARAMS'
    db_module = db_modules.get_db_module(task.db_type)
    connection, (rec, error) = execute_sql(db_module,
        task.db_database, task.db_user, task.db_password,
        task.db_host, task.db_port, task.db_encoding,
        None, sql, select=True)
    if rec:
        result = rec[0][0]
    if not result:
        result = 1
    return result

def read_setting(task):
    sql = 'SELECT '
    keys = common.DEFAULT_SETTINGS.keys()
    for key in keys:
        sql += 'F_%s, ' % key
    sql = sql[:-2]
    sql += ' FROM SYS_PARAMS'
    db_module = db_modules.get_db_module(task.db_type)
    connection, (rec, error) = execute_sql(db_module,
        task.db_database, task.db_user, task.db_password,
        task.db_host, task.db_port, task.db_encoding,
        None, sql, select=True)
    rec = rec[0]
    common.SETTINGS = {}
    for i, key in enumerate(keys):
        setting_type = type(common.DEFAULT_SETTINGS[key])
        try:
            if rec[i] is None:
                common.SETTINGS[key] = common.DEFAULT_SETTINGS[key]
            else:
                common.SETTINGS[key] = setting_type(rec[i])
        except:
            common.SETTINGS[key] = common.DEFAULT_SETTINGS[key]
    for key in common.SETTINGS.keys():
        common.__dict__[key] = common.SETTINGS[key]

def get_value_list(str_list, order=False):

    def getKey(item):
        return item[1]

    result = []
    for i, s in enumerate(str_list):
        result.append([i + 1, s])
    if order:
        result = sorted(result, key=getKey)
    return result

def write_setting(task):
    sql = 'UPDATE SYS_PARAMS SET '
    params = []
    keys = common.DEFAULT_SETTINGS.keys()
    for key in keys:
        value = common.SETTINGS[key]
        setting_type = type(common.DEFAULT_SETTINGS[key])
        if setting_type == bool:
            if value:
                value = 1
            else:
                value = 0
        if setting_type == str:
            sql += 'F_%s="%s", ' % (key, value)
        else:
            sql += 'F_%s=%s, ' % (key, value)
    sql = sql[:-2]
    db_module = db_modules.get_db_module(task.db_type)
    connection, (rec, error) = execute_sql(db_module, \
        task.db_database, task.db_user, task.db_password,
        task.db_host, task.db_port, task.db_encoding, None, sql)

def create_items(task):
    task.items = []
    task.sys_catalogs = Group(task, 'catalogs', task.lang['catalogs'])
    task.sys_tables = Group(task, 'tables', task.lang['tables'], visible=False)

    task.sys_params = task.sys_catalogs.add_catalog('sys_params', u'', 'SYS_PARAMS')

    task.sys_params.add_field(1, 'id', u'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_params.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_params.add_field(3, 'f_safe_mode', task.lang['safe_mode'], common.BOOLEAN)
    task.sys_params.add_field(4, 'f_debugging', 'Debugging', common.BOOLEAN, edit_visible=False)
    task.sys_params.add_field(5, 'f_log_file', u'Log file', common.TEXT, size = 30)
    task.sys_params.add_field(6, 'f_con_pool_size', u'Connection pool size', common.INTEGER, required=True)
    task.sys_params.add_field(7, 'f_decimal_point', u'Decimal point', common.TEXT, size = 1)
    task.sys_params.add_field(8, 'f_mon_decimal_point', u'Monetory decimal point', common.TEXT, size = 1)
    task.sys_params.add_field(9, 'f_mon_thousands_sep', u'Monetory thousands separator', common.TEXT, size = 3)
    task.sys_params.add_field(10, 'f_currency_symbol', u'Currency symbol', common.TEXT, size = 10)
    task.sys_params.add_field(11, 'f_frac_digits', u'Number of fractional digits', common.INTEGER)
    task.sys_params.add_field(12, 'f_p_cs_precedes', u'Currency symbol precedes the value (positive values)', common.BOOLEAN)
    task.sys_params.add_field(13, 'f_n_cs_precedes', u'Currency symbol precedes the value (negative values)', common.BOOLEAN)
    task.sys_params.add_field(14, 'f_p_sep_by_space', u'Currency symbol is separated by a space (positive values)', common.BOOLEAN)
    task.sys_params.add_field(15, 'f_n_sep_by_space', u'Currency symbol is separated by a space (negative values)', common.BOOLEAN)
    task.sys_params.add_field(16, 'f_positive_sign', u'Symbol for a positive monetary value', common.TEXT, size = 1)
    task.sys_params.add_field(17, 'f_negative_sign', u'Symbol for a negative monetary value', common.TEXT, size = 1)
    task.sys_params.add_field(18, 'f_p_sign_posn', u'The position of the sign (positive values)', common.INTEGER)
    task.sys_params.add_field(19, 'f_n_sign_posn', u'The position of the sign (negative values)', common.INTEGER)
    task.sys_params.add_field(20, 'f_d_fmt', u'Date format string', common.TEXT, size = 30)
    task.sys_params.add_field(21, 'f_d_t_fmt', u'Date and time format string', common.TEXT, size = 30)
    task.sys_params.add_field(22, 'f_language', task.lang['language'], common.INTEGER, required=True,
        lookup_values=get_value_list(langs.LANGUAGE, True), edit_visible=False)
    task.sys_params.add_field(23, 'f_author', task.lang['author'], common.TEXT, size = 30, edit_visible=False)
    task.sys_params.add_field(24, 'f_version', u'Version', common.TEXT, size = 15)
    task.sys_params.add_field(25, 'f_mp_pool', u'Multiprocessing connection pool', common.BOOLEAN)
    task.sys_params.add_field(26, 'f_persist_con', u'Persistent connection', common.BOOLEAN)
    task.sys_params.add_field(27, 'f_single_file_js', u'All JS modules in a single file', common.BOOLEAN)
    task.sys_params.add_field(28, 'f_dynamic_js', u'Dynamic JS modules loading', common.BOOLEAN)
    task.sys_params.add_field(29, 'f_compressed_js', u'Compressed JS, CSS files', common.BOOLEAN)
    task.sys_params.add_field(30, 'f_field_id_gen', u'f_field_id_gen', common.INTEGER)

    task.sys_items = task.sys_catalogs.add_catalog('sys_items', u'Items', 'SYS_ITEMS')
    task.sys_fields = task.sys_tables.add_table('sys_fields', task.lang['fields'], 'SYS_FIELDS')

    task.sys_items.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_items.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(3, 'parent', u'Parent id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(4, 'task_id', u'Task id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(5, 'type_id', u'Type id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(6, 'table_id', u'Table id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(7, 'has_children', u'Has_children', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_items.add_field(8, 'f_index', u'Index', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(9, 'f_name', task.lang['caption'], common.TEXT, required=True, size=256)
    task.sys_items.add_field(10, 'f_item_name', task.lang['name'], common.TEXT, required=True, size=256)
    task.sys_items.add_field(11, 'f_table_name', task.lang['table_name'], common.TEXT, size=256)
    task.sys_items.add_field(12, 'f_view_template', task.lang['view_template'], common.TEXT, size=256)
    task.sys_items.add_field(13, 'f_visible', task.lang['visible'], common.BOOLEAN)
    task.sys_items.add_field(14, 'f_soft_delete', u'Soft delete', common.BOOLEAN)
    task.sys_items.add_field(15, 'f_client_module', task.lang['client_module'], common.BLOB, visible=False, edit_visible=False)
    task.sys_items.add_field(16, 'f_web_client_module', u'Web_client_module', common.BLOB, visible=False, edit_visible=False)
    task.sys_items.add_field(17, 'f_server_module', task.lang['server_module'], common.BLOB, visible=False, edit_visible=False)
    task.sys_items.add_field(18, 'f_info', u'Info', common.BLOB, visible=False, edit_visible=False)
    task.sys_items.add_field(19, 'f_virtual_table', u'Virtual table', common.BOOLEAN)
    task.sys_items.add_field(20, 'f_js_external', u'External js module', common.BOOLEAN)
    task.sys_items.add_field(21, 'f_js_filename', u'js_file_name', common.TEXT, size=1024)
    task.sys_items.add_field(22, 'f_primary_key', u'Primary key field', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(23, 'f_deleted_flag', u'Deleted flag field', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(24, 'f_master_id', u'Master ID field', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(25, 'f_master_rec_id', u'Master record id field', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(26, 'f_js_funcs', 'f_js_funcs', common.BLOB, visible=False, edit_visible=False)

    task.sys_items.add_filter('id', u'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('not_id', u'ID', 'id', common.FILTER_NE, visible=False)
    task.sys_items.add_filter('parent', u'Parent', 'parent', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('task_id', u'Task', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('type_id', u'Type', 'type_id', common.FILTER_IN, visible=False)
    task.sys_items.add_filter('table_id', u'Type', 'table_id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('type_id_gt', u'Type', 'type_id', common.FILTER_GT, visible=False)

    task.sys_tasks = task.sys_catalogs.add_catalog('sys_tasks', u'', 'SYS_TASKS')
    task.sys_tasks.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(3, 'task_id', u'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(4, 'f_name', task.lang['caption'], common.TEXT, required=True, size=256, edit_visible=False)
    task.sys_tasks.add_field(5, 'f_item_name', task.lang['name'], common.TEXT, required=True, size=256, edit_visible=False)
    task.sys_tasks.add_field(6, 'f_manual_update', u'DB manual mode', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_tasks.add_field(7, 'f_db_type', task.lang['db_type'], common.INTEGER, required=True, lookup_values=get_value_list(db_modules.DB_TYPE))
    task.sys_tasks.add_field(8, 'f_alias', task.lang['alias'], common.TEXT, required=True, size = 30)
    task.sys_tasks.add_field(9, 'f_login', task.lang['login'], common.TEXT, size = 30)
    task.sys_tasks.add_field(10, 'f_password', task.lang['password'], common.TEXT, size = 30)
    task.sys_tasks.add_field(11, 'f_host', u'Host', common.TEXT, size = 30)
    task.sys_tasks.add_field(12, 'f_port', u'Port', common.TEXT, size = 10)
    task.sys_tasks.add_field(13, 'f_encoding', u'Charset', common.TEXT, size = 30)

    task.sys_tasks.add_filter('task_id', u'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_lookup_lists = task.sys_catalogs.add_catalog('sys_lookup_lists', u'Lookup lists', 'SYS_LOOKUP_LISTS')

    task.sys_lookup_lists.add_field(1, 'id', u'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lookup_lists.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lookup_lists.add_field(3, 'f_name', task.lang['name'], common.TEXT, required=True, size=256)
    task.sys_lookup_lists.add_field(4, 'f_lookup_values_text', u'Text to store lookup_values',  common.BLOB)

    task.sys_field_lookups = task.sys_tables.add_table('sys_field_lookups', u'Lookup item', 'SYS_FIELD_LOOKUPS')

    task.sys_field_lookups.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_field_lookups.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_field_lookups.add_field(3, 'f_value', u'Value', common.INTEGER)
    task.sys_field_lookups.add_field(4, 'f_lookup', u'Lookup value', common.TEXT, size=612)

#    task.sys_fields = task.sys_tables.add_table('sys_fields', task.lang['fields'], 'SYS_FIELDS')

    task.sys_fields.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(2, 'deleted', u'Deleted', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(3, 'owner_id', u'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(4, 'owner_rec_id', u'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(5, 'task_id', u'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(6, 'f_name',         task.lang['caption'], common.TEXT, True, size=256)
    task.sys_fields.add_field(7, 'f_field_name',   task.lang['name'], common.TEXT, True, size=256)
    task.sys_fields.add_field(8, 'f_data_type',    task.lang['data_type'], common.INTEGER, True,  False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_fields.add_field(9, 'f_size',         task.lang['size'], common.INTEGER)
    task.sys_fields.add_field(10, 'f_object',       task.lang['object'], common.INTEGER, False, task.sys_items, 'f_item_name')
    task.sys_fields.add_field(11, 'f_object_field',   task.lang['object_field'], common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(12, 'f_master_field', task.lang['master_field'], common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(13, 'f_enable_typehead', u'Typeahead',  common.BOOLEAN)
    task.sys_fields.add_field(14, 'f_lookup_values', task.lang['lookup_values'], common.INTEGER, False, task.sys_lookup_lists, 'f_name')
    task.sys_fields.add_field(15, 'f_required',     task.lang['required'], common.BOOLEAN)
    task.sys_fields.add_field(16, 'f_calculated',   task.lang['calculated'], common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_fields.add_field(17, 'f_default',      task.lang['default'], common.BOOLEAN)
    task.sys_fields.add_field(18, 'f_read_only',    task.lang['read_only'], common.BOOLEAN)
    task.sys_fields.add_field(19, 'f_alignment',    task.lang['alignment'], common.INTEGER, lookup_values=get_value_list(common.ALIGNMENT))
    task.sys_fields.add_field(20, 'f_default_value', u'Default value', common.TEXT, False,  False, size =256)
    task.sys_fields.add_field(21, 'f_help',          u'Help', common.BLOB, visible=False)
    task.sys_fields.add_field(22, 'f_placeholder',   u'Placeholder', common.TEXT, visible=False, size=256)

    task.sys_fields.add_filter('id', u'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('owner_rec_id', u'Owner record ID', 'owner_rec_id', common.FILTER_IN, visible=False)
    task.sys_fields.add_filter('task_id', u'Task', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('not_id', u'not ID', 'id', common.FILTER_NE, visible=False)
    task.sys_fields.add_filter('object', u'Object ID', 'f_object', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('master_field_is_null', u'Master field', 'f_master_field', common.FILTER_ISNULL, visible=False)
    task.sys_fields.add_filter('master_field', u'Master field', 'f_master_field', common.FILTER_EQ, visible=False)

    task.item_fields = task.sys_items.add_detail(task.sys_fields)

    task.sys_report_params = task.sys_tables.add_table('sys_report_params', task.lang['report_params'], 'SYS_REPORT_PARAMS')

    task.sys_report_params.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(3, 'owner_id', u'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(4, 'owner_rec_id', u'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(5, 'task_id', u'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(6, 'f_index',        task.lang['index'],   common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(7, 'f_name',         task.lang['caption'],      common.TEXT, True, size = 30)
    task.sys_report_params.add_field(8, 'f_param_name',   task.lang['name'],          common.TEXT, True, size = 30)
    task.sys_report_params.add_field(9, 'f_data_type',    task.lang['data_type'],          common.INTEGER, True,  False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_report_params.add_field(10, 'f_size',         task.lang['size'],  common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(11, 'f_object',       task.lang['object'],       common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_report_params.add_field(12, 'f_object_field',   task.lang['object_field'],  common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(13, 'f_enable_typehead', u'Typeahead',  common.BOOLEAN)
    task.sys_report_params.add_field(14, 'f_lookup_values', task.lang['lookup_values'], common.INTEGER, False, task.sys_lookup_lists, 'f_name')
    task.sys_report_params.add_field(15, 'f_required',     task.lang['required'],        common.BOOLEAN)
    task.sys_report_params.add_field(16, 'f_visible',      task.lang['visible'],    common.BOOLEAN)
    task.sys_report_params.add_field(17, 'f_alignment',    task.lang['alignment'], common.INTEGER, lookup_values=get_value_list(common.ALIGNMENT))
    task.sys_report_params.add_field(18, 'f_master_field', task.lang['master_field'], common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(19, 'f_help',         u'Help', common.BLOB, visible=False)
    task.sys_report_params.add_field(20, 'f_placeholder',  u'Placeholder', common.TEXT, visible=False, size=256)

    task.sys_report_params.add_filter('owner_rec_id', u'Owner rec ID ', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_report_params.add_filter('task_id', u'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_indices = task.sys_tables.add_table('sys_indices', task.lang['indices'], 'SYS_INDICES')

    task.sys_indices.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(3, 'owner_id', u'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(4, 'owner_rec_id', u'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(5, 'task_id', u'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(6, 'f_index_name', task.lang['index_name'], common.TEXT, True, size = 100)
    task.sys_indices.add_field(7, 'descending', u'Descending', common.BOOLEAN)
    task.sys_indices.add_field(8, 'f_unique_index', u'Unique', common.BOOLEAN)
    task.sys_indices.add_field(9, 'f_foreign_index', u'Foreign Index', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_indices.add_field(10, 'f_foreign_field', u'Foreign Field', common.INTEGER, False, task.item_fields, 'f_field_name', visible=False, edit_visible=False)
    task.sys_indices.add_field(11, 'f_fields', task.lang['fields'], common.BLOB, visible=False, edit_visible=False)

    task.sys_indices.add_filter('id', u'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('owner_rec_id', u'Owner record ID', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('task_id', u'Task ID', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('foreign_index', u'Owner record ID', 'f_foreign_index', common.FILTER_EQ, visible=False)

    task.sys_filters = task.sys_tables.add_table('sys_filters', task.lang['filters'], 'SYS_FILTERS')

    task.sys_filters.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(3, 'owner_id', u'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(4, 'owner_rec_id', u'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(5, 'task_id', u'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(6, 'f_index',     task.lang['index'],   common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(7, 'f_field',     task.lang['field'],    common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_filters.add_field(8, 'f_name',      task.lang['caption'], common.TEXT, True)
    task.sys_filters.add_field(9, 'f_filter_name',  task.lang['name'],     common.TEXT, True)
    task.sys_filters.add_field(10, 'f_data_type', task.lang['data_type'], common.INTEGER, False,  visible=False, edit_visible=False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_filters.add_field(11, 'f_type',      task.lang['filter_type'], common.INTEGER, False, lookup_values=get_value_list(common.FILTER_STRING))
    task.sys_filters.add_field(12, 'f_visible',   task.lang['visible'],    common.BOOLEAN)
    task.sys_filters.add_field(13, 'f_help',      u'Help', common.BLOB, visible=False)
    task.sys_filters.add_field(14, 'f_placeholder', u'Placeholder', common.TEXT, visible=False, size=256)


    task.sys_filters.add_filter('owner_rec_id', u'Owner rec ID ', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_filters.add_filter('task_id', u'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_users = task.sys_catalogs.add_catalog('sys_users', task.lang['users'], 'SYS_USERS')
    task.sys_roles = task.sys_catalogs.add_catalog('sys_roles', task.lang['roles'], 'SYS_ROLES')

    task.sys_users.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_users.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_users.add_field(3, 'f_name', task.lang['name'], common.TEXT, required=True, size=30)
    task.sys_users.add_field(4, 'f_login', task.lang['login'], common.TEXT, required=True, size=30)
    task.sys_users.add_field(5, 'f_password', task.lang['password'], common.TEXT, required=True, size=30)
    task.sys_users.add_field(6, 'f_role', task.lang['role'], common.INTEGER, True, task.sys_roles, 'f_name')
    task.sys_users.add_field(7, 'f_info', task.lang['info'], common.TEXT, edit_visible=False, size=100)
    task.sys_users.add_field(8, 'f_admin', u'Admin', common.BOOLEAN)

    task.sys_roles.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_roles.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_roles.add_field(3, 'f_name', task.lang['roles'], common.TEXT, required=True, size=30)

    task.sys_roles.add_filter('id', u'ID', 'id', common.FILTER_EQ, visible=False)

    task.sys_privileges = task.sys_tables.add_table('sys_privileges', task.lang['privileges'], 'SYS_PRIVILEGES')

    task.sys_privileges.add_field(1, 'id', u'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(3, 'owner_id', u'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(4, 'owner_rec_id', u'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(5, 'item_id', task.lang['item'], common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_privileges.add_field(6, 'f_can_view', task.lang['can_view'], common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(7, 'f_can_create', task.lang['can_create'], common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(8, 'f_can_edit', task.lang['can_edit'], common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(9, 'f_can_delete', task.lang['can_delete'], common.BOOLEAN, editable=True)

    task.sys_privileges.add_filter('owner_rec_id', u'Owner record ID', 'owner_rec_id', common.FILTER_EQ, visible=False)

    task.role_privileges = task.sys_roles.add_detail(task.sys_privileges)

    task.sys_code_editor = task.sys_catalogs.add_catalog('sys_code_editor', u'Editor', '')

    task.sys_code_editor.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_code_editor.add_field(2, 'parent', u'parent', common.INTEGER)
    task.sys_code_editor.add_field(3, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_code_editor.add_field(4, 'name', task.lang['caption'], common.TEXT, size = 10000)

    task.sys_fields_editor = task.sys_catalogs.add_catalog('sys_fields_editor', u'Editor', '')

    task.sys_fields_editor.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_fields_editor.add_field(2, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields_editor.add_field(3, 'name', task.lang['caption'], common.TEXT, required=True, size = 256)
    task.sys_fields_editor.add_field(4, 'param1', u'param1', common.BOOLEAN)
    task.sys_fields_editor.add_field(5, 'param2', u'param2', common.BOOLEAN)
    task.sys_fields_editor.add_field(6, 'param3', u'param3', common.BOOLEAN)

    task.sys_search = task.sys_catalogs.add_catalog('sys_search', u'Find in task', '')

    task.sys_search.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_search.add_field(2, 'parent', u'parent', common.INTEGER)
    task.sys_search.add_field(3, 'deleted', u'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_search.add_field(4, 'find_text', task.lang['find'], common.TEXT, size = 1000)
    task.sys_search.add_field(5, 'case_sensitive', task.lang['case_sensitive'], common.BOOLEAN)
    task.sys_search.add_field(6, 'whole_words', task.lang['whole_words'], common.BOOLEAN)

    task.sys_new_group = task.sys_catalogs.add_catalog('sys_new_group', u'Select new group type', '')

    task.sys_new_group.add_field(1, 'group_type',  'Group type', common.INTEGER, required=True, lookup_values=get_value_list(common.GROUP_TYPES))

    task.sys_lang = task.sys_catalogs.add_catalog('sys_lang', u'Languages', '')

    task.sys_lang.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_lang.add_field(2, 'f_abr', u'', common.INTEGER, required=True, visible=False, edit_visible=False)
    task.sys_lang.add_field(3, 'f_name', u'language', common.TEXT, required=True, size = 20)
    task.sys_lang.add_field(4, 'f_decimal_point', u'Decimal point', common.TEXT, size = 1)
    task.sys_lang.add_field(5, 'f_mon_decimal_point', u'Monetory decimal point', common.TEXT, size = 1)
    task.sys_lang.add_field(6, 'f_mon_thousands_sep', u'Monetory thousands separator', common.TEXT, size = 3)
    task.sys_lang.add_field(7, 'f_currency_symbol', u'Currency symbol', common.TEXT, size = 10)
    task.sys_lang.add_field(8, 'f_frac_digits', u'Number of fractional digits', common.INTEGER)
    task.sys_lang.add_field(9, 'f_p_cs_precedes', u'Currency symbol precedes the value (positive values)', common.BOOLEAN)
    task.sys_lang.add_field(10, 'f_n_cs_precedes', u'Currency symbol precedes the value (negative values)', common.BOOLEAN)
    task.sys_lang.add_field(11, 'f_p_sep_by_space', u'Currency symbol is separated by a space (positive values)', common.BOOLEAN)
    task.sys_lang.add_field(12, 'f_n_sep_by_space', u'Currency symbol is separated by a space (negative values)', common.BOOLEAN)
    task.sys_lang.add_field(13, 'f_positive_sign', u'Symbol for a positive monetary value', common.TEXT, size = 1)
    task.sys_lang.add_field(14, 'f_negative_sign', u'Symbol for a negative monetary value', common.TEXT, size = 1)
    task.sys_lang.add_field(15, 'f_p_sign_posn', u'The position of the sign (positive values)', common.INTEGER)
    task.sys_lang.add_field(16, 'f_n_sign_posn', u'The position of the sign (negative values)', common.INTEGER)
    task.sys_lang.add_field(17, 'f_d_fmt', u'Date format string', common.TEXT, size = 30)
    task.sys_lang.add_field(18, 'f_d_t_fmt', u'Date and time format string', common.TEXT, size = 30)

    task.sys_lang_keys = task.sys_catalogs.add_catalog('sys_lang_keys', u'Language keys', '')

    task.sys_lang_keys.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_lang_keys.add_field(2, 'f_keyword', 'Keyword', common.TEXT, required=True, size = 128)

    task.sys_lang_values = task.sys_catalogs.add_catalog('sys_lang_values', u'Language values', '')

    task.sys_lang_values.add_field(1, 'id', u'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_lang_values.add_field(2, 'f_lang', u'Key', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_values.add_field(3, 'f_key', u'Key', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_values.add_field(4, 'f_value', u'value', common.TEXT, size = 1048)


    def init_item(item, id_value, *order_by):
        item.ID = id_value
        item.soft_delete = False
        item._primary_key = 'id'
        item._deleted_flag = 'deleted'
        item._master_id = ''
        item._master_rec_id = ''
        if item.master:
            item._master_id = 'owner_id'
            item._master_rec_id = 'owner_rec_id'
        if hasattr(item, '_fields'):
            for field in item._fields:
                field.alignment = common.get_alignment(field.data_type, field.lookup_item, field.lookup_values)
        if order_by:
            item.change_order(*order_by)

    init_item(task, 0)
    init_item(task.sys_users, 1, 'id')
    init_item(task.sys_roles, 2, 'id')
    init_item(task.sys_items, 3, 'type_id', 'f_index')
    init_item(task.sys_fields, 4, 'id')
    init_item(task.sys_filters, 5, 'f_index')
    init_item(task.item_fields, 6, 'f_field_name')#'id')
    init_item(task.sys_privileges, 7)
    init_item(task.role_privileges, 8)
    init_item(task.sys_tasks, 9)
    init_item(task.sys_indices, 10, 'id')
    init_item(task.sys_params, 11)
    init_item(task.sys_report_params, 12, 'f_index')
    init_item(task.sys_code_editor, 14)
    init_item(task.sys_fields_editor, 15)
    init_item(task.sys_search, 16)
    init_item(task.sys_field_lookups, 17)
    init_item(task.sys_lookup_lists, 18, 'f_name')
    init_item(task.sys_lang, 19)
    init_item(task.sys_lang_keys, 20)
    init_item(task.sys_lang_values, 21)
    init_item(task.sys_new_group, 22)

    task.sys_catalogs.ID = 101
    task.sys_tables.ID = 102

    for i in range(1, 16):
        try:
            item = task.item_by_ID(i)
            for field in item._fields:
                field_def = field.field_def
                field_def[FIELD_ALIGNMENT] = field.alignment
                if field.lookup_item:
                    field_def[LOOKUP_FIELD] = field.lookup_item._field_by_name(field.lookup_field).ID
                    field_def[LOOKUP_ITEM] = field.lookup_item.ID
            for filter in item.filters:
                if filter.field:
                    filter.filter_def[FILTER_FIELD_NAME] = filter.field.ID
        except:
            pass

def update_admin_fields(task):

    def update_system_fields(cursor, id_value, parent, type_id, name):
        print name
        cursor.execute("SELECT ID, F_FIELD_NAME FROM SYS_FIELDS WHERE OWNER_REC_ID IN (%d, %d)" % (id_value, parent))
        rows = cursor.fetchall()
        for (field_id, field_name) in rows:
            if field_name == 'id':
                cursor.execute("UPDATE SYS_ITEMS SET F_PRIMARY_KEY=%d WHERE ID=%d" % (field_id, id_value))
            elif field_name == 'deleted':
                cursor.execute("UPDATE SYS_ITEMS SET F_DELETED_FLAG=%d WHERE ID=%d" % (field_id, id_value))
                cursor.execute("UPDATE SYS_FIELDS SET f_data_type=%d WHERE ID=%d" % (common.INTEGER, field_id))
            elif field_name == 'owner_id':
                cursor.execute("UPDATE SYS_ITEMS SET F_MASTER_ID=%d WHERE ID=%d" % (field_id, id_value))
            elif field_name == 'owner_rec_id':
                cursor.execute("UPDATE SYS_ITEMS SET F_MASTER_REC_ID=%d WHERE ID=%d" % (field_id, id_value))

    def do_updates(con, field, item_name):
        if field.field_name.lower() == 'f_js_funcs':
            cursor = con.cursor()
            cursor.execute("SELECT ID, F_WEB_CLIENT_MODULE FROM SYS_ITEMS")
            rows = cursor.fetchall()
            for (id_value, code) in rows:
                if code:
                    js_funcs = parse_js(code.encode('utf-8'))
                    cursor.execute("UPDATE SYS_ITEMS SET F_JS_FUNCS='%s' WHERE ID=%d" % (js_funcs, id_value))
                else:
                    cursor.execute("UPDATE SYS_ITEMS SET F_JS_FUNCS=NULL WHERE ID=%d" % id_value)
            con.commit()
        if field.field_name.lower() == 'f_field_id_gen':
            cursor = con.cursor()
            cursor.execute("SELECT MAX(ID) FROM SYS_FIELDS")
            rows = cursor.fetchall()
            max_field_id = rows[0][0]
            print 'max_field_id', max_field_id
            cursor.execute("UPDATE SYS_PARAMS SET F_FIELD_ID_GEN = %d" % max_field_id)
            con.commit()
        if field.field_name.lower() == 'f_master_rec_id':
            cursor = con.cursor()
            cursor.execute("UPDATE SYS_ITEMS SET TYPE_ID = %d WHERE TYPE_ID=%d" % (common.ITEMS_TYPE, common.JOURNALS_TYPE))
            cursor.execute("UPDATE SYS_ITEMS SET TYPE_ID = %d WHERE TYPE_ID=%d" % (common.ITEM_TYPE, common.JOURNAL_TYPE))
            con.commit()
            cursor.execute("SELECT ID, PARENT, TYPE_ID, F_NAME FROM SYS_ITEMS WHERE TYPE_ID IN (%d, %d, %d, %d)" % \
                (common.ITEMS_TYPE, common.TABLES_TYPE, common.ITEM_TYPE, common.TABLE_TYPE))
            rows = cursor.fetchall()
            for (id_value, parent, type_id, name) in rows:
                update_system_fields(cursor, id_value, parent, type_id, name)
            con.commit()
            create_items(task)

    def get_item_fields(item, table_name):
        cursor.execute('PRAGMA table_info(%s)' % table_name)
        rows = cursor.fetchall()
        result = [str(row[1]).upper() for row in rows]
        return result

    def check_item_fields(item, table_name=None):
        if not table_name:
            table_name = item.table_name.upper()
        fields = get_item_fields(item, table_name)
        for field in item._fields:
            if not field.field_name.upper() in fields:
                sql = 'ALTER TABLE %s ADD COLUMN %s %s' % \
                    (table_name, field.field_name.upper(), \
                    task.db_module.FIELD_TYPES[field.data_type])
                print sql
                cursor.execute(sql)
                con.commit()
                do_updates(con, field, item.item_name)

    def check_table_exists(item, table_name=None):
        if not table_name:
            table_name = item.table_name.upper()
        sql = 'SELECT name FROM sqlite_master WHERE type="table" AND UPPER(name)="%s"' % table_name
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            sql = 'CREATE TABLE %s (ID INTEGER PRIMARY KEY)' % table_name
            cursor.execute(sql)
        return True

    con = task.create_connection()
    cursor = con.cursor()
    for group in task.items:
        for item in group.items:
            if item.table_name and not item.master:
                if check_table_exists(item):
                    check_item_fields(item)
    con.close()

    #~ con = sqlite3.connect('langs.sqlite')
    #~ cursor = con.cursor()
    #~ for group in task.items:
        #~ for item in group.items:
            #~ if item.item_name.find('sys_lang') != -1:
                #~ if check_table_exists(item, item.item_name.upper()):
                    #~ check_item_fields(item, item.item_name.upper())
    #~ con.close()


def create_admin(app):
    task = AdminTask(app, 'admin', u'Administrator', '', db_modules.SQLITE, db_database='admin.sqlite')

    task.language = read_language(task)
    create_items(task)
    update_admin_fields(task)
    task.fields_id_lock = Lock()

    read_setting(task)
    task.task_con_pool_size = common.SETTINGS['CON_POOL_SIZE']
    if task.task_con_pool_size < 1:
        task.task_con_pool_size = 3
    try:
        task.task_mp_pool = common.SETTINGS['MP_POOL']
        task.task_persist_con = common.SETTINGS['PERSIST_CON']
    except:
        task.task_mp_pool = 4
        task.task_persist_con = True
    task.safe_mode = common.SETTINGS['SAFE_MODE']
    task.language = common.SETTINGS['LANGUAGE']
    task.item_caption = task.lang['admin']
    register_defs(task)
    return task

def db_info(task):
    tasks = task.sys_tasks.copy()
    tasks.open()
    return tasks.f_db_type.value, str(tasks.f_alias.value), str(tasks.f_login.value), \
        str(tasks.f_password.value), tasks.f_host.value, \
        tasks.f_port.value, tasks.f_encoding.value

def execute(task, task_id, sql, params=None):
    if task_id == 0:
        result_set, error = task.execute(sql, params)
        return error
    else:
        connection = None
        db_type, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
        db_module = db_modules.get_db_module(db_type)
        connection, (result_set, error) = execute_sql(db_module, \
            db_database, db_user, db_password, db_host, db_port,
            db_encoding, connection, sql, params)
        if connection:
            connection.rollback()
            connection.close()
        return error

def execute_select(task_id, sql, params=None):
    return task.execute_select(sql)

def get_privileges(task, role_id):
    result = {}
    privliges = task.sys_privileges.copy()
    privliges.filters.owner_rec_id.value = role_id
    privliges.open()
    for p in privliges:
        result[p.item_id.value] = \
            {
            'can_view': p.f_can_view.value,
            'can_create': p.f_can_create.value,
            'can_edit': p.f_can_edit.value,
            'can_delete': p.f_can_delete.value
            }
    return result

def get_roles(task):
    result = {}
    roles = task.sys_roles.copy()
    roles.open()
    for r in roles:
        result[r.id.value] = get_privileges(task, r.id.value)
    return result

def login(task, log, psw_hash, admin):
    user_id = None
    user_info = {}
    users = task.sys_users.copy()
    users.open()
    if task.safe_mode:
        privileges = {}
        for u in users:
            if u.f_login.value.strip() == log.strip():
                if hashlib.md5(u.f_password.value).hexdigest() == psw_hash:
                    if not admin or u.f_admin.value == admin:
                        user_id = u.id.value
                        user_info = {
                            'user_id': u.id.value,
                            'role_id': u.f_role.value,
                            'role_name': u.f_role.display_text,
                            'user_name': u.f_name.value,
                            'admin': u.f_admin.value
                        }
    return user_info

def create_task(app):
    result = None
    task = app.admin
    it = task.sys_items.copy()
    it.filters.type_id.value = [common.TASK_TYPE]
    it.open()
    it_task = task.sys_tasks.copy()
    it_task.open()
    if it_task.f_db_type.value:
        result = Task(app, it.f_item_name.value, it.f_name.value,
            it.f_js_filename.value, it_task.f_db_type.value, it_task.f_alias.value,
            it_task.f_login.value, it_task.f_password.value, it_task.f_host.value,
            it_task.f_port.value, it_task.f_encoding.value, task.task_con_pool_size,
            task.task_mp_pool, task.task_persist_con
            )
        result.ID = it.id.value
        load_task(result, app)
    return result

###############################################################################
#                                   load task                                 #
###############################################################################

def reload_task(task):
    if task.app.task:
        task.app.under_maintenance = True
        try:
            while True:
                if task.app._busy > 1:
                    time.sleep(0.1)
                else:
                    break

            read_setting(task)
            load_task(task.app.task, task.app, first_build=False)
            task.app.task.mod_count += 1
        finally:
            task.app.under_maintenance = False


def load_task(target, app, first_build=True, after_import=False):

    def create_fields(item, parent_id):
        recs = fields_dict.get(parent_id)
        if recs:
            for r in recs:
                sys_fields.rec_no = r
                if sys_fields.owner_rec_id.value == parent_id:
                    view_index = -1
                    visible = False
                    word_wrap = False
                    expand = False
                    editable = False
                    for i, rec in enumerate(sys_items._view_list):
                        if sys_fields.id.value == rec[0]:
                            view_index = i
                            visible = True
                            word_wrap = rec[1]
                            expand = rec[2]
                            editable = rec[3]
                            break
                    edit_visible = False
                    edit_index = -1
                    for i, rec in enumerate(sys_items._edit_list):
                        if sys_fields.id.value == rec[0]:
                            edit_index = i
                            edit_visible = True
                            break
                    field = item.add_field(sys_fields.field_by_name('id').value,
                        sys_fields.f_field_name.value,
                        sys_fields.f_name.value,
                        sys_fields.f_data_type.value,
                        sys_fields.f_required.value,
                        sys_fields.f_object.value,
                        sys_fields.f_object_field.value,
                        visible,
                        view_index,
                        edit_visible,
                        edit_index,
                        sys_fields.f_read_only.value,
                        expand,
                        word_wrap,
                        sys_fields.f_size.value,
                        sys_fields.f_default_value.value,
                        sys_fields.f_default.value,
                        sys_fields.f_calculated.value,
                        editable,
                        sys_fields.f_master_field.value,
                        sys_fields.f_alignment.value,
                        sys_fields.f_lookup_values.value,
                        sys_fields.f_enable_typehead.value,
                        sys_fields.f_help.value,
                        sys_fields.f_placeholder.value
                        )

    def create_filters(item, parent_id):
        for rec in sys_filters:
            if sys_filters.owner_rec_id.value == parent_id:
                item.add_filter(
                    sys_filters.f_filter_name.value,
                    sys_filters.f_name.value,
                    sys_filters.f_field.value,
                    sys_filters.f_type.value,
                    sys_filters.f_data_type.value,
                    sys_filters.f_visible.value,
                    sys_filters.f_help.value,
                    sys_filters.f_placeholder.value
                    )

    def create_params(item, parent_id):
        for params in sys_params:
            if sys_params.owner_rec_id.value == parent_id:
                item.add_param(params.f_name.value,
                        params.f_param_name.value,
                        params.f_data_type.value,
                        params.f_object.value,
                        params.f_object_field.value,
                        params.f_required.value,
                        params.f_visible.value,
                        params.f_alignment.value,
                        params.f_enable_typehead.value,
                        params.f_lookup_values.value,
                        params.f_help.value,
                        params.f_placeholder.value
                        )

    def create_items(group, group_id, group_type_id):
        for rec in sys_items:
            if rec.parent.value == group_id:
                item = None
                add_item = None
                if group_type_id == common.ITEMS_TYPE:
                    add_item = group.add_catalog
                elif group_type_id == common.TABLES_TYPE:
                    add_item = group.add_table
                elif group_type_id == common.REPORTS_TYPE:
                    add_item = group.add_report
                if add_item:
                    item = add_item(rec.f_item_name.value,
                        rec.f_name.value,
                        rec.f_table_name.value,
                        rec.f_visible.value,
                        rec.f_view_template.value,
                        rec.f_js_filename.value,
                        rec.f_soft_delete.value)
                    if item:
                        item.ID = rec.id.value
                        item.virtual_table = rec.f_virtual_table.value
                        item.server_code = rec.f_server_module.value
                        item._primary_key = rec.f_primary_key.value
                        item._deleted_flag = rec.f_deleted_flag.value
                        item._master_id = rec.f_master_id.value
                        item._master_rec_id = rec.f_master_rec_id.value
                        if group_type_id != common.REPORTS_TYPE:
                            common.load_interface(sys_items)
                            create_fields(item, group_id)
                            create_fields(item, rec.id.value)
                            item._order_by = sys_items._order_list
                            item.rep_ids = sys_items._reports_list
                            create_filters(item, group_id)
                            create_filters(item, rec.id.value)
                        else:
                            create_params(item, rec.id.value)
                            item.rep_ids = []

    def create_groups(parent):
        groups = []
        for rec in sys_items:
            if rec.id.value == parent:
                target.table_name = rec.f_table_name.value
                target.template = rec.f_view_template.value
                target.js_filename = rec.f_js_filename.value
                common.load_interface(sys_items)
                target.server_code = rec.f_server_module.value
            if rec.parent.value == parent:
                group = Group(target, rec.f_item_name.value, rec.f_name.value, rec.f_view_template.value,
                    rec.f_js_filename.value, rec.f_visible.value, rec.type_id.value)
                group.ID = rec.id.value
                group.server_code = rec.f_server_module.value
                groups.append((group, rec.id.value, rec.type_id.value))
        for group in groups:
             create_items(*group)

    def create_details():
        for it in sys_items:
            if it.table_id.value:
                item = target.item_by_ID(it.parent.value)
                table = target.item_by_ID(it.table_id.value)
                if item and table:
                    detail = item.add_detail(table)
                    detail.ID = it.id.value
                    detail.visible = it.f_visible.value
                    detail.view_template = it.f_view_template.value
                    detail.js_filename = it.f_js_filename.value
                    detail.server_code = it.f_server_module.value
                    detail.item_type = common.ITEM_TYPES[detail.item_type_id - 1]
                    common.load_interface(sys_items)
                    detail._order_by = sys_items._order_list
                    for field in detail._fields:
                        field.view_index = -1
                        field.view_visible = False
                        field.word_wrap = False
                        field.expand = False
                        field.editable = False
                        for i, rec in enumerate(sys_items._view_list):
                            if field.ID == rec[0]:
                                field.view_index = i
                                field.view_visible = True
                                field.word_wrap = rec[1]
                                field.expand = rec[2]
                                field.editable = rec[3]
                                break
                        field.edit_visible = False
                        field.edit_index = -1
                        for i, rec in enumerate(sys_items._edit_list):
                            if field.ID == rec[0]:
                                field.edit_index = i
                                field.edit_visible = True
                                break
                        field.field_def[FIELD_VISIBLE] = field.view_visible
                        field.field_def[FIELD_VIEW_INDEX] = field.view_index
                        field.field_def[FIELD_EDIT_VISIBLE] = field.edit_visible
                        field.field_def[FIELD_EDIT_INDEX] = field.edit_index


    def process_reports():
        def add_reports(item):
            item.reports = []
            for rep_id in item.rep_ids:
                report = target.item_by_ID(rep_id[0])
                if report:
                    item.reports.append(report)

        for group in target.items:
            for item in group.items:
                add_reports(item)

    def process_lookup_lists():
        lists = task.sys_lookup_lists.copy()
        lists.open()
        for l in lists:
            text = l.f_lookup_values_text.value
            target.lookup_lists[l.id.value] = json.loads(l.f_lookup_values_text.value)

    def remove_attr(target):
        keys = target.__dict__.keys()
        for key in keys:
            try:
                value = target.init_dict[key]
                if hasattr(target.__dict__[key], '__call__'):
                    target.__dict__[key] = value
            except:
                del target.__dict__[key]

    task = app.admin
    remove_attr(target)
    target.items = []
    sys_fields = task.sys_fields.copy()
    sys_fields.open()
    fields_dict = {}
    for f in sys_fields:
        d = fields_dict.get(f.owner_rec_id.value, [])
        if not d:
            fields_dict[f.owner_rec_id.value] = d
        d.append(f.rec_no)
    sys_filters = task.sys_filters.copy()
    sys_filters.open()
    sys_params = task.sys_report_params.copy()
    sys_params.open()
    sys_items = task.sys_items.copy()
    sys_items.details_active = False
    sys_items.open()
    create_groups(target.ID)
    create_details()
    process_reports()
    process_lookup_lists()
    target.bind_items()
    target.compile_all()
    target.language = task.language

    target.first_build = first_build
    target.after_import = after_import
    if target.on_created:
        target.on_created(target)

    internal_path = os.path.join(task.work_dir, 'static', '_internal')
    if os.path.exists(internal_path):
        try:
            shutil.rmtree(internal_path)
        except:
            pass

#
###############################################################################
#                                 task                                        #
###############################################################################

def server_check_connection(task, db_type, database, user, password, host, port, encoding):
    error = ''
    if db_type:
        db_module = db_modules.get_db_module(db_type)
        try:
            connection = db_module.connect(database, user, password, host, port, encoding)
            if connection:
                connection.close()
        except Exception, e:
            error = e.message
            if not error:
                error = str(e)
    return error

def server_set_task_name(task, f_name, f_item_name):
    tasks = task.sys_tasks.copy()
    tasks.open()

    items = task.sys_items.copy(handlers=False)
    items.set_where(type_id=common.TASK_TYPE)
    items.open()
    items.edit()
    items.f_name.value = f_name
    items.f_item_name.value = f_item_name
    items.post()
    items.apply()
    task.app.task = None

def server_set_project_langage(task, lang):
    common.SETTINGS['LANGUAGE'] = lang
    task.language = lang
    task.init_locale()
    write_setting(task)
    read_setting(task)
    create_items(task)

    items = task.sys_items.copy()
    items.open()
    for it in items:
        it.edit()
        try:
            it.f_name.value = task.lang[it.f_item_name.value]
        except Exception, e:
            print traceback.format_exc()
        it.post()
    it.apply()

    file_name = 'index.html'
    with open(file_name, 'r') as f:
        data = f.read().decode('utf-8')
    start = data.find('__$_')
    label_list = []
    while start > -1:
        end = data.find('_$__', start)
        if end != -1:
            search = data[start:end+4]
            replace = data[start +4:end]
            label_list.append((search, replace))
        start = data.find('__$_', end)
    for search, replace in label_list:
        try:
            data = data.replace(search, task.lang[replace])
        except:
            pass
    with open(file_name, 'w') as f:
        f.write(data.encode('utf-8'))

    register_defs(task)

def server_update_has_children(task):
    has_children = {}
    items = task.sys_items.copy(handlers=False)
    items.open()
    for it in items:
        has_children[it.parent.value] = True
        if it.type_id.value in (common.ROOT_TYPE, common.USERS_TYPE, common.ROLES_TYPE,
            common.TASKS_TYPE, common.ITEMS_TYPE,
            common.TABLES_TYPE, common.REPORTS_TYPE):
            has_children[it.id.value] = True
    for it in items:
        if not has_children.get(it.id.value):
            has_children[it.id.value] = False
        if it.has_children.value != has_children.get(it.id.value):
            it.edit()
            it.has_children.value = has_children.get(it.id.value)
            it.post()
    items.apply()

def server_export_task(task, task_id, url=None):

    def add_item(item):
        table = item.copy(handlers=False)
        table.open()
        fields = []
        for field in table.fields:
            fields.append(field.field_name)
        result[item.item_name] = {'fields': fields, 'records': table.dataset}

    result = {}
    add_item(task.sys_items)
    add_item(task.sys_fields)
    add_item(task.sys_indices)
    add_item(task.sys_filters)
    add_item(task.sys_report_params)
    add_item(task.sys_roles)
    add_item(task.sys_params)
    add_item(task.sys_privileges)
    add_item(task.sys_lookup_lists)

    task_file = 'task.dat'
    file_name = 'task.zip'
    zip_file_name = os.path.join(task.work_dir, file_name)
    try:
        with open(task_file, 'w') as f:
            json.dump(result, f)
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(task_file)
            zip_file.write('index.html')
            common.zip_dir('js', zip_file)
            common.zip_dir('css', zip_file)
            common.zip_dir(os.path.join('static', 'img'), zip_file)
            common.zip_dir(os.path.join('static', 'js'), zip_file)
            common.zip_dir(os.path.join('static', 'css'), zip_file)
            common.zip_dir('utils', zip_file, exclude_ext=['.pyc'])
            common.zip_dir('reports', zip_file, exclude_ext=['.xml', '.ods#'])
        if url:
            items = task.sys_items.copy()
            items.set_where(id=task_id)
            items.open()
            result_path = os.path.join(task.work_dir, 'static', '_internal')
            if not os.path.exists(result_path):
                os.makedirs(result_path)
            result_file = '%s_%s_%s_%s.zip' % (items.f_item_name.value, common.SETTINGS['VERSION'],
                task.app.jam_version, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.rename(file_name, os.path.join(result_path, result_file))
            result = '%s/static/_internal/%s' % (url, result_file)
        else:
            with open(file_name, 'r') as f:
                result = f.read()
    finally:
        if os.path.exists(task_file):
            os.remove(task_file)
        if os.path.exists(file_name):
            os.remove(file_name)
    return result

def server_import_task(task, task_id, file_name, from_client=False):

    def refresh_old_item(item):
        item = item.copy(handlers=False)
        item.open(expanded=False)
        old_dict[item.item_name] = item

    def get_dataset(item, data_lists):
        ns = []
        ds = []
        dl = data_lists.get(item.item_name)
        if dl:
            field_names = data_lists[item.item_name]['fields']
            dataset = data_lists[item.item_name]['records']
            for d in dataset:
                ds.append([])
            for i, f in enumerate(field_names):
                if item.field_by_name(f):
                    ns.append(f)
                    for j, d in enumerate(dataset):
                        ds[j].append(dataset[j][i])
        else:
            for f in item.fields:
                ns.append(f.field_name)
        return ns, ds

    def get_items(dir):
        file_name = os.path.join(dir, 'task.dat')
        with open(file_name, 'r' ) as f:
            data = f.read()
        data_lists = json.loads(data)
        new_items = {}
        old_items = {}
        items = [task.sys_items, task.sys_fields, task.sys_indices, task.sys_filters, \
            task.sys_report_params, task.sys_roles, task.sys_params, task.sys_privileges, \
            task.sys_lookup_lists]
        for item in items:
            task.execute('DELETE FROM "%s" WHERE "DELETED" = 1' % item.table_name)
            old_item = item.copy(handlers=False)
            old_item.soft_delete = False
            old_item.open(expanded=False)
            field_names, dataset = get_dataset(old_item, data_lists)
            new_item = item.copy(handlers=False)
            new_item.open(expanded=False, fields=field_names)
            new_item._dataset = dataset
            new_items[item.item_name] = new_item
            old_items[item.item_name] = old_item
        os.remove(file_name)
        return new_items, old_items

    def can_copy_field(field):
        if field.owner.item_name == 'sys_params':
            if field.field_name in ['f_safe_mode', 'f_debugging']:
                return False
        return True

    def copy_record(old, new):
        for old_field in old.fields:
            if can_copy_field(old_field):
                new_field = new.field_by_name(old_field.field_name)
                if new_field:
                    old_field.value = new_field.raw_value

    def compare_items(old, new, owner_id=None):
        result = {}
        for it in old:
            result[it.id.value] = [True, False]
        for it in new:
            if not owner_id or owner_id == it.owner_rec_id.value:
                info = result.get(it.id.value)
                if info:
                    info[1] = True
                else:
                    result[it.id.value] = [False, True]
        return result

    def check_items():
        errors = []
        new = new_dict['sys_items']
        old = old_dict['sys_items']
        compare = compare_items(old, new)
        for it in old:
            o, n = compare[old.id.value]
            if o and n:
                new.locate('id', old.id.value)
                if old.type_id.value != new.type_id.value:
                    errors.append('Items with ID %s (<b>%s</b>, <b>%s</b>) have different type values' % \
                    (old.id.value, old.f_item_name.value, new.f_item_name.value))
                elif old.f_table_name.value and old.f_table_name.value.upper() != new.f_table_name.value.upper():
                    errors.append('Items with ID %s (<b>%s</b>, <b>%s</b>) have different database tables (<b>%s</b>, <b>%s</b>)' % \
                    (old.id.value, old.f_item_name.value, new.f_item_name.value, old.f_table_name.value, new.f_table_name.value))
        error = ",<br>".join(errors)
        if error:
            error = '<div class="text-error">%s</div>' % error
        return error

    def update_item(item_name, detail_name=None, options=['update', 'insert', 'delete'], owner=None):

        new = new_dict[item_name]
        if owner:
            old = owner.detail_by_name(item_name)
            old.open(expanded=False)
        else:
            old = old_dict[item_name]
        owner_id = None
        if owner:
            owner_id = owner.id.value

        compare = compare_items(old, new, owner_id)

        if 'delete' in options:
            old.first()
            while not old.eof():
                if not owner_id or owner_id == old.owner_rec_id.value:
                    o, n = compare[old.id.value]
                    if o and not n:
                        old.delete()
                    else:
                        old.next()
                else:
                    old.next()

        if 'update' in options:
            for it in old:
                if not owner_id or owner_id == it.owner_rec_id.value:
                    o, n = compare[old.id.value]
                    if o and n and new.locate('id', old.id.value):
                        old.edit()
                        copy_record(old, new)
                        if detail_name:
                            update_item(detail_name, owner=old)
                        old.post()

        if 'insert' in options:
            for it in new:
                if not owner_id or owner_id == it.owner_rec_id.value:
                    o, n = compare[new.id.value]
                    if not o and n:
                        old.append()
                        copy_record(old, new)
                        if detail_name:
                            update_item(detail_name, owner=old)
                        old.post()

        return old

    def get_delta(item_name, detail_name=None, options=['update', 'insert', 'delete']):
        item = update_item(item_name, detail_name, options)
        return item.delta()

    def get_new_fields(item_id):
        result = []
        new_items = new_dict['sys_items']
        if new_items.locate('id', item_id):
            parent_id = new_items.parent.value
        new_fields = new_dict['sys_fields']
        for field in new_fields:
            if field.owner_rec_id.value in [item_id, parent_id]:
                if not (field.f_calculated.value or field.f_master_field.value):
                    dic = {}
                    dic['id'] = field.id.value
                    dic['field_name'] = field.f_field_name.value
                    dic['data_type'] = field.f_data_type.value
                    dic['size'] = field.f_size.value
                    dic['default_value'] = field.f_default_value.value
                    dic['primary_key'] = field.id.value == new_items.f_primary_key.value
                    result.append(dic)
        return result

    def get_table_name(item_id):
        new_items = new_dict['sys_items']
        if new_items.locate('id', item_id):
            if not new_items.f_virtual_table.value:
                return new_items.f_table_name.value

    def copy_tmp_files(zip_file_name):
        dir = os.path.join(os.getcwd(), 'tmp-' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        if os.path.exists(dir):
            shutil.rmtree(dir)
        os.makedirs(dir)
        with zipfile.ZipFile(zip_file_name) as z:
            z.extractall(dir)
        return dir

    def delete_tmp_files(dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    def copy_files(dir):
        from distutils import dir_util
        dir_util.copy_tree(dir, os.getcwd())

    def get_foreign_key_dict(ind):
        dic = None
        if ind.f_foreign_index.value:
            dic = {}
            fields = new_dict['sys_fields']
            fields.locate('id', ind.f_foreign_field.value)
            dic['key'] = fields.f_field_name.value
            ref_id = fields.f_object.value
            items = new_dict['sys_items']
            items.locate('id', ref_id)
            dic['ref'] = items.f_table_name.value
            primary_key = items.f_primary_key.value
            fields.locate('id', primary_key)
            dic['primary_key'] = fields.f_field_name.value
        return dic

    def analize(dir, db_type):
        try:
            error = ''

            db_sql = []
            adm_sql = []
            deltas = {}

            delta = get_delta('sys_indices', options=['delete'])
            for d in delta:
                table_name = get_table_name(d.owner_rec_id.value)
                if table_name:
                    db_sql.append(indices_delete_sql(task.sys_indices, d))
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_items', 'sys_fields')
            for d in delta:
                if d.rec_inserted():
                    db_sql.append(items_insert_sql(task.sys_items, d))
                elif d.rec_modified():
                    db_sql.append(items_update_sql(task.sys_items, d))
                elif d.rec_deleted():
                    db_sql.append(items_delete_sql(task.sys_items, d))

            refresh_old_item(old_dict['sys_items'])
            delta = get_delta('sys_items')
            adm_sql.append(delta.apply_sql())

            refresh_old_item(old_dict['sys_fields'])
            delta = get_delta('sys_fields')
            adm_sql.append(delta.apply_sql())

            refresh_old_item(old_dict['sys_indices'])
            delta = get_delta('sys_indices', options=['update', 'insert'])
            for d in delta:
                table_name = get_table_name(d.owner_rec_id.value)
                if table_name:
                    if d.rec_inserted():
                        db_sql.append(indices_insert_sql(task.sys_indices, d, table_name,
                            get_new_fields(d.owner_rec_id.value),
                            foreign_key_dict=get_foreign_key_dict(d)))
                    elif d.rec_deleted():
                        db_sql.append(indices_delete_sql(task.sys_indices, d))
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_filters')
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_report_params')
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_roles')
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_params')
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_privileges')
            adm_sql.append(delta.apply_sql())

            delta = get_delta('sys_lookup_lists')
            adm_sql.append(delta.apply_sql())

        except Exception, e:
            error = traceback.format_exc()
            print u'Import error: %s' % error
        return error, db_sql, adm_sql

    def reload_utils():
        utils_folder = os.path.join(task.work_dir, 'utils')
        if os.path.exists(utils_folder):
            for dirpath, dirnames, filenames in os.walk(utils_folder):
                for file_name in filenames:
                    name, ext = os.path.splitext(file_name)
                    if ext == '.py':
                        relpath = os.path.join(os.path.relpath(dirpath, task.work_dir), name)
                        module_name = '.'.join(relpath.split(os.sep))
                        module = sys.modules.get(module_name)
                        if module:
                            try:
                                reload(module)
                            except Exception, e:
                                print module_name, e

    error = ''
    task._import_message = ''

    def show_progress(string):
        print string
        task._import_message += '<h5>' + string + '</h5>'

    def show_info(info):
        task._import_message += '<div style="margin-left: 30px;">' + info + '</div>'

    db_type = get_db_type(task)
    if db_type == db_modules.SQLITE:
        return False, error, '<h5>Import is not supported for SQlite database.</h5>'
    task.app.under_maintenance = True
    try:
        request_count = 0
        if from_client:
            request_count = 1
        file_name = os.path.join(os.getcwd(), os.path.normpath(file_name))
        show_progress(u'Import: reading data')
        dir = copy_tmp_files(file_name)
        new_dict, old_dict = get_items(dir)
        success = False
        show_progress(u'Import: checking data integrity')
        error = check_items()
        info = ''
        if error:
            show_info(error)
        else:
            show_progress(u'Import: analyzing changes')
            error, db_sql, adm_sql = analize(dir, db_type)
            if error:
                show_info(error)
        if not error:
            success = True
            show_progress(u'Import: waiting for connections to close')
            while True:
                i = 0
                if task.app._busy > request_count:
                    time.sleep(0.1)
                    i += 1
                    if i > 3000:
                        break
                else:
                    break
            if len(db_sql):
                show_progress(u'Import: applying changes to the database')
                connection = None
                db_type, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
                db_module = db_modules.get_db_module(db_type)
                connection, (result_set, error, info) = execute_sql(db_module, \
                    db_database, db_user, db_password, db_host, db_port,
                    db_encoding, connection, db_sql, ddl=True)
                show_info(info)
                if db_module.DDL_ROLLBACK:
                    if error:
                        success = False
                    #~ else:
                        #~ connection.commit()
                if connection:
                    connection.close()
            if success:
                show_progress(u'Import: applying changes to admin.sqlite')
                result, error = task.execute(adm_sql)
                if error:
                    success = False
            if success:
                show_progress(u'Import: copying files')
                copy_files(dir)
            if success:
                read_setting(task)
                if task.app.task:
                    reload_utils()
                    read_setting(task)
                    load_task(task.app.task, task.app, first_build=False, after_import=True)
                    task.app.roles = None
                    task.app.task.mod_count += 1
                    update_events_code(task)
    except Exception, e:
        error = str(e)
        if os.name != 'nt':
            print u'Import error traceback:', traceback.format_exc()
        print u'Import error:', error
    finally:
        show_progress(u'Import: deleteing tmp files')
        try:
            delete_tmp_files(dir)
        except:
            pass
        try:
            os.remove(file_name)
        except:
            pass
        task.app.under_maintenance = False
    return success, error, task._import_message

def get_module_names_dict(task, task_id):

    def find_module_name(dic, id_value):
        lst = dic[id_value]
        if id_value != task_id:
            parent = lst[0]
        else:
            parent = 0
        if parent:
            plst = dic[parent]
            if not plst[2]:
                plst[2] = find_module_name(dic, parent)
            lst[2] = plst[2] + '.' + lst[1]
        else:
            lst[2] = lst[1]
        return lst[2]

    items = task.sys_items.copy(handlers=False)
    items.set_where(task_id=task_id)
    items.set_order_by('id')
    items.open()
    d = {}
    for item in items:
        d[item.id.value] = [item.parent.value, item.f_item_name.value, '']
    result = {}
    for item in items:
        result[item.id.value] = find_module_name(d, item.id.value)
    return result


def server_find_in_task(task, task_id, search_text, case_sencitive, whole_words):

    try:
        search_text = search_text.decode("utf-8")
    except:
        pass
    if not case_sencitive:
        search_text = search_text.upper()

    def is_whole_word(line, pos, search_text):
        if pos > 0:
            ch = line[pos - 1]
            if ch.isalpha() or ch == '_':
                return False
        if pos + len(search_text) < len(line):
            ch = line[pos + len(search_text)]
            if ch.isalpha() or ch == '_':
                return False
        return True

    def find_in_text(text, search_text, module_name):
        result = []
        if text:
            lines = text.splitlines()
            for i, l in enumerate(lines):
                line = l
                if not case_sencitive:
                    line = l.upper()
                pos = line.find(search_text)
                if pos > -1:
                    if whole_words and not is_whole_word(line, pos, search_text):
                        continue
                    result.append((module_name, i + 1, l.strip()))
        return result

    def find_in_type(header, module_type):
        search = ''
        result = []
        for it in items:
            if module_type == common.CLIENT_MODULE:
                text = it.f_client_module.value
            elif module_type == common.WEB_CLIENT_MODULE:
                text = it.f_web_client_module.value
            elif module_type == common.SERVER_MODULE:
                text = it.f_server_module.value
            result += find_in_text(text, search_text, names_dict[it.id.value])
        for line in result:
            search += '%s:%s: %s\n' % line
        if header:
            search = header + '\n' + search
        return search + '\n'

    names_dict = get_module_names_dict(task, task_id)
    items = task.sys_items.copy(handlers=False)
    items.set_where(task_id=task_id)
    items.open(fields=['id', 'f_item_name', 'f_web_client_module', 'f_server_module'])
    result = {'client': find_in_type('', common.WEB_CLIENT_MODULE),
        'server': find_in_type('', common.SERVER_MODULE)}
    return result

def server_web_print_code(task, task_id):

    def add_detail_code(item, module_type):
        for child in children:
            if child.table_id.value == item.id.value:
                add_code(child, module_type)

    def add_code(item, module_type):
        if module_type == common.WEB_CLIENT_MODULE:
            name = 'client'
            code = item.f_web_client_module.value
        else:
            name = 'server'
            code = item.f_server_module.value
        if code and len(code):
            result[name].append([names_dict[item.id.value], code])
        add_detail_code(item, module_type)

    result = {}

    names_dict = get_module_names_dict(task, task_id)
    children = task.sys_items.copy()
    children.set_where(table_id__gt=0)
    children.open()
    items = task.sys_items.copy()
    items.set_where(task_id=task_id)
    items.open()
    items.locate('id', task_id)
    result['task'] = items.f_name.value
    result['client'] = []
    result['server'] = []
    for it in items:
        if not it.table_id.value:
            add_code(items, common.WEB_CLIENT_MODULE)
            add_code(items, common.SERVER_MODULE)
    return result

def server_load_report_module(task, module_name):
    file_name = os.path.join(task.work_dir, 'reports', module_name)
    with open(file_name) as f:
        result = f.read()
    return result

def server_store_report_module(task, text, module_name):
    file_name = os.path.join(task.work_dir, 'reports', module_name)
    with open(file_name, 'wb') as f:
        f.write(text)

def update_events_code(task):

    def process_events(code, js_funcs, ID, path):
        script = ''
        if code:
            script += str('\nfunction Events%s() { // %s \n\n' % (ID, path))
            code = '\t' + code.replace('\n', '\n\t')
            code = code.replace('    ', '\t')
            script += code
            if js_funcs:
                script += js_funcs
            else:
                script += '\n'
            script += '}\n\n'
            script += 'task.events.events%s = new Events%s();\n' % (ID, ID)
        return script

    def get_js_path(it):

        def get_parent_name(id_value, l):
            tp = name_dict.get(id_value)
            if tp:
                parent, type_id, name, external = tp
                l.insert(0, name)
                get_parent_name(parent, l)
        l = []
        l.append(it.f_item_name.value)
        get_parent_name(it.parent.value, l)
        return '.'.join(l)

    def get_external(it):
        external = it.f_js_external.value
        if it.type_id.value == common.DETAIL_TYPE:
            parent, type_id, name, parent_external = name_dict.get(it.parent.value)
            external = parent_external
        return external

    def update_task(item):
        js_filename = js_filenames.get(item.ID, '')
        item.js_filename = js_filename

    single_file = common.SETTINGS['SINGLE_FILE_JS']
    name_dict = {}
    js_filenames = {}

    it = task.sys_items.copy(handlers=False, details=False)
    it.set_where(type_id=common.TASK_TYPE)
    it.set_order_by('type_id')
    it.open()
    task_id = it.task_id.value
    it.set_where(task_id=task_id)
    it.open(fields=['id', 'parent', 'type_id', 'f_name', 'f_item_name', 'f_js_filename', 'f_js_external', 'f_web_client_module', 'f_js_funcs'])
    script_start = '(function($, task) {\n"use strict";\n'
    script_end = '\n})(jQuery, task)'
    script_common = ''
    for it in it:
        js_path = get_js_path(it)
        js_filename = js_path + '.js'
        file_name = os.path.join(os.getcwd().decode('utf-8'), 'js', js_filename)
        if os.path.exists(file_name):
            os.remove(file_name)
        min_file_name = get_minified_name(file_name)
        if os.path.exists(min_file_name):
            os.remove(min_file_name)
        name_dict[it.id.value] = [it.parent.value, it.type_id.value, it.f_item_name.value, it.f_js_external.value]
        code = it.f_web_client_module.value
        js_funcs = it.f_js_funcs.value
        cur_js_filename = ''
        if code:
            code = code.strip().encode('utf-8')
            js_funcs = js_funcs.encode('utf-8')
            if code:
                script = process_events(code, js_funcs, it.id.value, js_path)
                external = get_external(it)
                if single_file and not external:
                    script_common += script
                else:
                    script = script_start + script + script_end
                    cur_js_filename = js_filename
                    with open(file_name, 'w') as f:
                        f.write(script)
                    if common.SETTINGS['COMPRESSED_JS']:
                        minify(file_name)
            js_filenames[it.id.value] = cur_js_filename
    if single_file:
        it.first()
        js_file_name = it.f_item_name.value + '.js'
        js_filenames[it.id.value] = js_file_name
        script = script_start + script_common + script_end
        file_name = os.path.join(os.getcwd().decode('utf-8'), 'js', js_file_name)
        with open(file_name, 'w') as f:
            f.write(script)
        if common.SETTINGS['COMPRESSED_JS']:
            minify(file_name)
    sql = []
    for key,value in js_filenames.iteritems():
        sql.append("UPDATE %s SET F_JS_FILENAME = '%s' WHERE ID = %s" % (it.table_name, value, key))
    it.task.execute(sql)
    if it.task.app.task:
        it.task.app.task.all(update_task)

def get_minified_name(file_name):
    result = file_name
    head, tail = os.path.split(file_name)
    name, ext = os.path.splitext(tail)
    if (ext in ['.js', '.css']):
        result = os.path.join(head, '%s.min%s' % (name, ext))
    return result

def minify(file_name):
    min_file_name = get_minified_name(file_name)
    from slimit import minify

    with open(file_name, 'r') as f:
        text = f.read()
    text = text.replace('.delete(', '["delete"](')
    new_text = minify(text, mangle=True, mangle_toplevel=True)
    with open(min_file_name, 'w') as f:
        f.write(new_text)

def get_field_dict(task, item_id, parent_id, type_id, table_id):
    result = {}
    if type_id in [common.ITEM_TYPE, common.TABLE_TYPE, common.DETAIL_TYPE]:
        fields = task.sys_fields.copy()
        if table_id:
            fields.filters.owner_rec_id.value = [table_id, task.sys_items.field_by_id(table_id, 'parent')]
        else:
            fields.filters.owner_rec_id.value = [item_id, parent_id]
        fields.open()
        for f in fields:
            if f.f_field_name.value.lower() != 'deleted':
                result[f.f_field_name.value] = None
    return result

def get_task_dict(task, task_id):

    def get_children(items, id_value, type_id, dict, key, parent_id=None):
        childs = {}
        if type_id in (common.TASK_TYPE, common.ITEMS_TYPE,
            common.TABLES_TYPE, common.REPORTS_TYPE):
            for it in items:
                if it.parent.value == id_value:
                        clone = items.clone()
                        get_children(clone, it.id.value, it.type_id.value, childs, it.f_item_name.value, it.parent.value)
        else:
            fields = []
            f = f_dict.get(id_value)
            if f:
                fields += f
            f = f_dict.get(parent_id)
            if f:
                fields += f
            for f in fields:
                childs[f] = None
        dict[key] = childs

    result = {}
    f_dict = {}
    items = task.sys_items.copy()
    items.details_active = False
    items.open(['id', 'type_id', 'parent', 'f_item_name'])

    fields = task.sys_fields.copy()
    fields.open(['owner_rec_id', 'f_field_name'])
    for f in fields:
        if f.f_field_name.value.lower() != 'deleted':
            d = f_dict.get(f.owner_rec_id.value, [])
            if not d:
                f_dict[f.owner_rec_id.value] = d
            d.append(f.f_field_name.value)

    params = task.sys_report_params.copy()
    params.open(['owner_rec_id', 'f_param_name'])
    for f in params:
        d = f_dict.get(f.owner_rec_id.value, [])
        if not d:
            f_dict[f.owner_rec_id.value] = d
        d.append(f.f_param_name.value)

    get_children(items, task_id, common.TASK_TYPE, result, 'task')
    return result['task']

def server_item_info(task, item_id, is_server, doc_type):
    result = {}
    items = task.sys_items.copy()
    items.set_where(id=item_id)
    items.open()
    type_id = items.type_id.value
    parent_id = items.parent.value
    task_id = items.task_id.value
    table_id = items.table_id.value
    item_name = items.f_item_name.value
    if table_id:
        parent = task.sys_items.copy()
        parent.set_where(id=parent_id)
        parent.open()
        item_name = parent.f_item_name.value + '.' + item_name
    module_type = common.WEB_CLIENT_MODULE
    code = items.f_web_client_module.value
    if is_server:
        module_type = common.SERVER_MODULE
        code = items.f_server_module.value
    item_name = item_name + ' - ' + doc_type

    result[common.editor_tabs[common.TAB_FIELDS]] = get_field_dict(task, item_id, parent_id, type_id, table_id)
    result[common.editor_tabs[common.TAB_TASK]] = get_task_dict(task, task_id)
    result[common.editor_tabs[common.TAB_EVENTS]] = get_events(type_id, is_server)
    result[common.editor_tabs[common.TAB_FUNCS]] = common.get_funcs_info(code, module_type)
    result['module_name'] = item_name
    result['code'] = code
    return result

def parse_js(code):
    script = ''
    code = code.replace('.delete(', '["delete"](')
    n = parse(code)
    for key in n:
        if key.type == 'FUNCTION':
            script += '\tthis.%s = %s;\n' % (key.name, key.name)
    if script:
        script = '\n' + script
    return script

def server_save_edit(task, item_id, text, is_server):
    code = text
    text = text.encode('utf-8')
    line = None
    error = ''
    module_info = None
    module_type = common.WEB_CLIENT_MODULE
    if is_server:
        module_type = common.SERVER_MODULE
    try:
        if is_server:
            compile(text, 'check_item_code', "exec")
        else:
            text = text.replace('.delete(', '["delete"](')
            js_funcs = parse_js(text)
    except SyntaxError_, e:
        try:
            err_str = e.args[0]
            pos = err_str.find('\nNone:')
            error = err_str[:pos]
            error = 'invalid syntax'
            try:
                line = int(err_str[pos+len('\nNone:'):])
            except:
                pass
            if line:
                error += ' - line %s' % line
        except:
            error = e.message
    except Exception, e:
        try:
            line = e.args[1][1]
            col = e.args[1][2]
            if line and col:
                error = ' %s - line %d col %d' % (e.args[0], line, col)
            elif line:
                error = ' %s - line %d col %d' % (e.args[0], line)
            else:
                error = e.args[0]
        except:
            error = e.message
    if not error:
        try:
            item = task.sys_items.copy()
            item.set_where(id=item_id)
            item.open(['id', 'f_server_module', 'f_web_client_module', 'f_js_funcs'])
            if item.record_count() == 1:
                item.edit()
                if is_server:
                    item.f_server_module.value = code
                else:
                    item.f_web_client_module.value = code
                    item.f_js_funcs.value = js_funcs
                item.post()
                item.apply()
                module_info = common.get_funcs_info(code, module_type)
            else:
                error = u'item with id %s not found' % item_id
        except Exception, e:
            error = e.message
        if is_server:
            task.app.task_server_modified = True
        else:
            task.app.task_client_modified = True
    return error, line, module_info

def get_templates(text):
    result = {}
    all = []
    views = []
    edits = []
    filters = []
    params = []
    start = 0
    while True:
        index = text.find('class=', start)
        if index == -1:
            break
        else:
            start_char = text[index + 6: index + 7]
            sub_str = text[index + 7:]
            class_str = ''
            for ch in sub_str:
                if ch == start_char:
                    break
                else:
                    class_str += ch
            if class_str.find('-view') > 0:
                views.append(class_str)
            elif class_str.find('-edit') > 0:
                edits.append(class_str)
            elif class_str.find('-filter') > 0:
                filters.append(class_str)
            elif class_str.find('-param') > 0:
                params.append(class_str)
            start = index + 6 + len(class_str)
    all = views + edits + filters + params
    for one in all:
        if not one in ['icon-edit', 'icon-filter']:
            result[one] = None
    return result

def server_get_file_info(task, item_id, file_name):
    result = {}
    file_path = file_name
    if file_name == 'project.css':
        file_path = os.path.join('css', 'project.css')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            result['code'] = f.read()
        if file_name == 'index.html':
            result['Templates'] = get_templates(result['code'])
    return result

def server_save_file(task, file_name, code):
    code = code.encode('utf-8')
    result = {}
    error = ''
    if file_name == 'project.css':
        file_name = os.path.join('css', 'project.css')
    file_name = os.path.normpath(file_name)
    try:
        with open(file_name, 'w') as f:
            f.write(code)
        if file_name == 'index.html':
            result['Templates'] = get_templates(code)
    except Exception, e:
        print traceback.format_exc()
        error = e.message
    result['error'] = error
    return result

def server_get_db_options(task, db_type):
    result = {}
    db_module = db_modules.get_db_module(db_type)
    result['NEED_DATABASE_NAME'] = db_module.NEED_DATABASE_NAME
    result['NEED_LOGIN'] = db_module.NEED_LOGIN
    result['NEED_PASSWORD'] = db_module.NEED_PASSWORD
    result['NEED_ENCODING'] = db_module.NEED_ENCODING
    result['NEED_HOST'] = db_module.NEED_HOST
    result['NEED_PORT'] = db_module.NEED_PORT
    result['CAN_CHANGE_TYPE'] = db_module.CAN_CHANGE_TYPE
    result['CAN_CHANGE_SIZE'] = db_module.CAN_CHANGE_SIZE
    result['UPPER_CASE'] = db_module.UPPER_CASE
    return result

def server_get_task_info(task):
    items = task.sys_items.copy()
    items.set_where(type_id=common.TASK_TYPE)
    items.open(fields=['f_item_name', 'f_name'])
    task_name = items.f_item_name.value;
    task_caption = items.f_name.value;
    params = task.sys_params.copy()
    params.open()
    task_version = params.f_version.value
    return task_name, task_caption, task_version, task.app.started

def server_can_delete_lookup_list(task, list_id):
    fields = task.sys_fields.copy()
    fields.set_where(f_lookup_values=list_id)
    fields.open()
    used = []
    for f in fields:
        used.append((task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'), f.f_field_name.value))
    if len(used) != 0:
        names = ',<br>'.join([task.lang['field_mess'] % use for use in used])
        mess = u'Lookup list is used in <br> %s' % names
        return mess

def server_create_task(task):
    task.create_task()

def do_on_apply_sys_changes(item, delta, params, priv, user_info, env):
    task = item.task
    debugging = common.SETTINGS['DEBUGGING']
    safe_mode = common.SETTINGS['SAFE_MODE']
    single_file_js = common.SETTINGS['SINGLE_FILE_JS']
    compressed_js = common.SETTINGS['COMPRESSED_JS']

    sql = delta.apply_sql()
    result = item.task.execute(sql)

    read_setting(task)
    if compressed_js != common.SETTINGS['COMPRESSED_JS']:
        task.app.task_client_modified = True
    if single_file_js != common.SETTINGS['SINGLE_FILE_JS']:
        task.app.task_client_modified = True
        task.app.task_server_modified = True

    if safe_mode != common.SETTINGS['SAFE_MODE']:
        task.safe_mode = common.SETTINGS['SAFE_MODE']
        task.app.users = {}
    return result

def get_fields_next_id(task):
    with task.fields_id_lock:
        params = task.sys_params.copy()
        params.open()
        cur_id = params.f_field_id_gen.value + 1
        params.edit()
        params.f_field_id_gen.value = cur_id
        params.post()
        params.apply()
        return cur_id

def clear_docs_on_logout(task, user):
    try:
        if user:
            docs = []
            for i, (c_item_ID, c_item_id, c_doc_type, c_user) in enumerate(list(task.edited_docs)):
                if not (c_user and c_user["user_id"] and c_user["user_id"] == user["user_id"]):
                    docs.append(task.edited_docs[i])
        else:
            docs = []
        task.edited_docs = docs
    except Exception, e:
        print e

def find_edited_doc(task, item_ID, item_id, doc_type, user):
    for i, (c_item_ID, c_item_id, c_doc_type, c_user) in enumerate(list(task.edited_docs)):
        if c_item_ID == item_ID and c_item_id == item_id and c_doc_type == doc_type:
            return task.edited_docs[i]

def check_doc_edited(task, item_ID, item_id, doc_type, user):
    doc = find_edited_doc(task, item_ID, item_id, doc_type, user)
    return doc

def set_edited(task, item_ID, item_id, doc_type, user):
    clear_edited(task, item_ID, item_id, doc_type, user)
    doc = [item_ID, item_id, doc_type, user]
    task.edited_docs.append(doc)
    return doc

def clear_edited(task, item_ID, item_id, doc_type, user):
    doc = find_edited_doc(task, item_ID, item_id, doc_type, user)
    if doc:
        task.edited_docs.remove(doc)

###############################################################################
#                                  sys_items                                  #
###############################################################################

def get_db_type(task):
    tasks = task.sys_tasks.copy()
    tasks.open()
    return tasks.f_db_type.value

def get_table_fields(item, fields, delta_fields=None):

    def field_dict(field):
        if not (field.f_calculated.value or field.f_master_field.value):
            dic = {}
            dic['id'] = field.id.value
            dic['field_name'] = field.f_field_name.value
            dic['data_type'] = field.f_data_type.value
            dic['size'] = field.f_size.value
            dic['default_value'] = field.f_default_value.value
            dic['master_field'] = field.f_master_field.value
            dic['primary_key'] = field.id.value == item.f_primary_key.value
            return dic

    def field_info(fields):
        result = []
        for field in fields:
            if not (field.f_calculated.value or field.f_master_field.value):
                dic = field_dict(field)
                if dic:
                    result.append(dic)
        return result

    def find_field(fields_info, field_id):
        for field in fields_info:
            if field['id'] == field_id:
                return field

    task = item.task
    result = []
    parent_fields = task.sys_fields.copy()
    parent_fields.filters.owner_rec_id.value = [fields.owner.parent.value]
    parent_fields.open()
    result = field_info(parent_fields) + field_info(fields)
    if delta_fields:
        for field in delta_fields:
            if not (field.f_calculated.value or field.f_master_field.value):
                if field.record_status == common.RECORD_INSERTED:
                    dic = field_dict(field)
                    if dic:
                        result.append(dic)
                if field.record_status == common.RECORD_DELETED:
                    field_info = find_field(result, field.id.value)
                    if field_info:
                        result.remove(field_info)
                elif field.record_status == common.RECORD_MODIFIED:
                    field_info = find_field(result, field.id.value)
                    if field_info:
                        field_info['id'] = field.id.value
                        field_info['field_name'] = field.f_field_name.value
                        field_info['data_type'] = field.f_data_type.value
                        field_info['size'] = field.f_size.value
                        field_info['default_value'] = field.f_default_value.value
                    else:
                        dic = field_dict(field)
                        if dic:
                            result.append(dic)
            elif field.f_master_field.value and field.record_status == common.RECORD_MODIFIED:
                field_info = find_field(result, field.id.value)
                if field_info and not field_info['master_field']:
                    result.remove(field_info)
    return result

def item_children(task, item_id):
    items = task.sys_items.copy()
    items.filters.parent.value = item_id
    items.open()
    return items

def get_system_fields(item):
    result = []
    atts = ['f_primary_key', 'f_deleted_flag', 'f_master_id', 'f_master_rec_id']
    for at in atts:
        field = item.field_by_name(at)
        if field.value:
            result.append(field.value)
    if result:
        fields = item.task.sys_fields.copy()
        fields.set_where(id__in=result)
        fields.open()
        result = []
        for f in fields:
            result.append(f.f_field_name.value)
    return result

def update_interface(delta, type_id, item_id):

    def delete_id_from_list(id_list, id_value):
        return [id_it for id_it in id_list if id_it[0] != id_value]

    task = delta.task
    if type_id in (common.ITEM_TYPE, common.TABLE_TYPE) and \
        delta.details.sys_fields.record_count():
        item = task.sys_items.copy()
        item.filters.id.value = item_id
        item.open()
        system_fields = get_system_fields(item)

        fields = task.sys_fields.copy()
        fields.filters.owner_rec_id.value = [item_id, item.parent.value]
        fields.open()
        common.load_interface(item)
        if delta.record_status == common.RECORD_INSERTED:
            for field in fields:
                if field.owner_rec_id.value == item.parent.value:
                    if not field.f_field_name.value in system_fields:
                        item._view_list.append([field.id.value, False, False, False])
                        item._edit_list.append([field.id.value])

        for d in delta.details.sys_fields:
            if d.record_status in [common.RECORD_INSERTED, common.RECORD_DELETED]:
                field_name = d.f_field_name.value
                if fields.locate('f_field_name', field_name):
                    if d.record_status == common.RECORD_INSERTED:
                        if not field_name in system_fields:
                            item._view_list.append([fields.id.value, False, False, False])
                            item._edit_list.append([fields.id.value])
                    elif d.record_status == common.RECORD_DELETED:
                        item._view_list = delete_id_from_list(item._view_list, fields.id.value)
                        item._edit_list = delete_id_from_list(item._edit_list, fields.id.value)
                        item._order_list = delete_id_from_list(item._order_list, fields.id.value)
        common.store_interface(item)

def change_item_sql(item, old_fields, new_fields):
    db_type = get_db_type(item.task)
    return item.change_table_sql(db_type, old_fields, new_fields)

def update_table(delta):
    if delta.f_virtual_table.value or \
        delta.type_id.value in (common.ITEMS_TYPE, common.TABLES_TYPE, common.REPORTS_TYPE):
        return False
    else:
        return True

def init_priviliges(item, item_id):
    priv = item.task.sys_privileges.copy(handlers=False)
    priv.open(open_empty=True)
    roles = item.task.sys_roles.copy(handlers=False)
    roles.open()
    for r in roles:
        priv.append()
        priv.owner_id.value = r.ID
        priv.owner_rec_id.value = r.id.value
        priv.item_id.value = item_id
        priv.f_can_view.value = True
        priv.f_can_create.value = True
        priv.f_can_edit.value = True
        priv.f_can_delete.value = True
        priv.post()
    priv.apply()

def items_insert_sql(item, delta, manual_update=False, foreign_fields=None):
    if update_table(delta) and not manual_update:
        if delta.type_id.value in (common.ITEM_TYPE, common.TABLE_TYPE):
            db_type = get_db_type(item.task)
            sql = delta.create_table_sql(db_type, delta.f_table_name.value, \
                get_table_fields(delta, delta.details.sys_fields), foreign_fields=foreign_fields)
            return sql

def items_execute_insert(item, delta, manual_update):
    sql = items_insert_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception, u'Error while creating table: %s' % (error)
    sql = delta.apply_sql()
    result = item.task.execute(sql)
    exec_result = result[0]
    result_id = exec_result['changes'][0]['rec_id']
    init_priviliges(item, result_id)
    update_interface(delta, delta.type_id.value, result_id)
    return result

def items_update_sql(item, delta, manual_update=False):
    if update_table(delta) and not manual_update:
        if delta.type_id.value in (common.ITEMS_TYPE, common.TABLES_TYPE,
            common.ITEM_TYPE, common.TABLE_TYPE) and \
            delta.details.sys_fields.record_count():
            it = item.copy()
            it.filters.id.value = delta.id.value
            it.open()
            it_fields = it.details.sys_fields
            it_fields.open()
            old_fields = get_table_fields(delta, it_fields)
            new_fields = get_table_fields(delta, it_fields, delta.details.sys_fields)
            sql = change_item_sql(delta, old_fields, new_fields)
            return sql

def items_execute_update(item, delta, manual_update):
    sql = items_update_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception, u'Error while modifying table: %s' % error
    sql = delta.apply_sql()
    result = item.task.execute(sql)
    update_interface(delta, delta.type_id.value, delta.id.value)
    return result

def items_delete_sql(item, delta, manual_update=False):
    if update_table(delta) and not manual_update:
        if delta.type_id.value in (common.ITEM_TYPE, common.TABLE_TYPE):
            db_type = get_db_type(item.task)
            sql = delta.delete_table_sql(db_type)
            return sql

def items_execute_delete(item, delta, manual_update):
    sql = items_delete_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception, u'Error while deleting table %s: %s' % (delta.table_name.upper(), error)
    commands = []
    sql = delta.apply_sql()
    commands.append(sql)
    for it in (item.task.sys_filters, item.task.sys_indices, item.task.sys_report_params):
        commands.append('DELETE FROM %s WHERE OWNER_REC_ID = %s' % (it.table_name.upper(), delta.id.value))
    result = item.task.execute(commands)
    return result

def items_apply_changes(item, delta, params, priv, user_info, env):
    manual_update = params['manual_update']
    for f in delta.sys_fields:
        if not f.id.value:
            raise Exception, u'Field %s id value is not set' % (f.field_name)
    if delta.rec_inserted():
        result = items_execute_insert(item, delta, manual_update)
    elif delta.rec_modified():
        result = items_execute_update(item, delta, manual_update)
    elif delta.rec_deleted():
        result = items_execute_delete(item, delta, manual_update)
    item.task.app.task_server_modified = True
    return result

def do_on_apply_changes(item, delta, params, priv, user_info, env):
    sql = delta.apply_sql()
    result = item.task.execute(sql)
    item.task.app.task_server_modified = True
    return result

def server_group_is_empty(item, id_value):
    item = item.task.sys_items.copy()
    item.set_where(parent=id_value)
    item.open()
    return item.record_count() == 0

def server_can_delete(item, id_value):
    item = item.copy()
    item.set_where(id=id_value)
    item.open()
    details = item.task.sys_items.copy()
    details.filters.table_id.value = id_value
    details.open()
    used = []
    for d in details:
        used.append((item.task.sys_items.field_by_id(d.parent.value, 'f_item_name'), d.f_item_name.value))
    if len(used) != 0:
        names = ',<br>'.join([item.task.lang['detail_mess'] % use for use in used])
        mess = item.task.lang['item_used_in_items'] % (item.f_item_name.value, names)
        return mess

    fields = item.task.sys_fields.copy()
    fields.open()
    used = []
    for f in fields:
        if f.f_object.value == id_value:
            used.append((item.task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'), f.f_field_name.value))
    if len(used) != 0:
        names = ',<br>'.join([item.task.lang['field_mess'] % use for use in used])
        mess = item.task.lang['item_used_in_fields'] % (item.f_item_name.value, names)
        return mess

    params = item.task.sys_report_params.copy()
    params.open()
    used = []
    for p in params:
        if p.f_object.value == id_value:
             used.append((item.task.sys_items.field_by_id(p.owner_rec_id.value, 'f_item_name'), p.f_param_name.value))
    if len(used) != 0:
        names = ',<br>'.join([item.task.lang['param_mess'] % use for use in used])
        mess = item.task.lang['item_used_in_params'] % (item.f_item_name.value, names)
        return mess

    details = item.task.sys_items.copy()
    details.set_filters(parent=id_value)
    details.open()
    if details.record_count():
        mess = "Can't delete item: item contains details"
        return mess

def server_load_interface(item, id_value):
    item = item.copy()
    item.set_where(id=id_value)
    item.open(fields=['id', 'f_info'])
    common.load_interface(item)
    return {
        'view_list': item._view_list,
        'edit_list': item._edit_list,
        'order_list': item._order_list,
        'reports_list': item._reports_list
    }

def server_store_interface(item, id_value, info):
    item = item.copy()
    item.set_where(id=id_value)
    item.open(fields=['id', 'f_info'])
    item._view_list = info['view_list']
    item._edit_list = info['edit_list']
    item._order_list = info['order_list']
    item._reports_list = info['reports_list']
    common.store_interface(item)
    item.task.app.task_server_modified = True

def server_update_details(item, item_id, dest_list):

    def get_table_info(table_id):
        items = item.copy()
        items.set_where(id=table_id)
        items.open()
        return items.f_name.value, items.f_item_name.value, items.f_table_name.value

    items = item.copy(handlers=False)
    items.set_where(parent=item_id)
    items.open()
    while not items.eof():
        cur_row = [row for row in dest_list if row[0] == items.table_id.value]
        if len(cur_row) == 1:
            dest_list.remove(cur_row[0])
            items.next()
        else:
            items.delete()

    item = item.copy(handlers=False)
    item.set_where(id=item_id)
    item.open()
    for row in dest_list:
        table_id = row[0]
        name, obj_name, table_name = get_table_info(table_id)
        items.append()
        items.task_id.value = item.task_id.value
        items.type_id.value = common.DETAIL_TYPE
        items.table_id.value = table_id
        items.parent.value = item.id.value
        items.f_name.value = name
        items.f_item_name.value = obj_name
        items.f_table_name.value = table_name
        items.f_visible.value = True
        items.f_info.value = ''
        items.post()
        table = item.task.sys_items.copy()
        table.set_where(id=table_id)
        table.open()
        common.load_interface(table)
        items._view_list = table._view_list
        items._edit_list = table._edit_list
        items._order_list = table._order_list
        items._reports_list = []
        common.store_interface(items)
    items.apply()
    item.task.app.task_server_modified = True


###############################################################################
#                                 sys_fields                                  #
###############################################################################

def server_can_delete_field(item, id_value):
    item = item.copy()
    item.set_where(id=id_value)
    item.open()

    item_type_id = item.task.sys_items.field_by_id(item.owner_rec_id.value, 'type_id')
    if item_type_id in (common.ITEMS_TYPE, common.TABLES_TYPE):
        if not server_group_is_empty(item, item.owner_rec_id.value):
            mess = "Can't delete the field: the group contains items."
            return mess

    field_id = item.id.value
    fields = item.task.sys_fields.copy()
    fields.set_filters(task_id=item.task_id.value)
    fields.open()
    used = []
    for f in fields:
        if f.f_object_field.value == field_id:
            used.append((item.task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'),
                f.f_field_name.value))
    if len(used) != 0:
        names = ',<br>'.join([u'<p>%s - %s</p>' % use for use in used])
        mess = item.task.lang['field_used_in_fields'] % \
            (item.f_field_name.value, names)
        return mess

    field_id = item.id.value
    indices = item.task.sys_indices.copy()
    indices.filters.owner_rec_id.value = item.owner_rec_id.value
    indices.open()
    ind_list = []
    for ind in indices:
        if ind.f_foreign_index.value:
            if ind.f_foreign_field.value == field_id:
                ind_list.append(ind.f_index_name.value)
        else:
            field_list = common.load_index_fields(ind.f_fields.value)
            for fld in field_list:
                if fld[0] == field_id:
                    ind_list.append(ind.f_index_name.value)
    if len(ind_list):
        names = ',<br>'.join(ind_list)
        mess = item.task.lang['field_used_in_indices'] % \
            (item.f_field_name.value, names)
        return mess

    field_id = item.id.value
    filters = item.task.sys_filters.copy()
    filters.filters.owner_rec_id.value = item.owner_rec_id.value
    filters.open()
    filters_list = []
    for fltr in filters:
        if fltr.f_field.value == field_id:
            filters_list.append(fltr.f_filter_name.value)
    if len(filters_list):
        names = ',<br>'.join(filters_list)
        mess = item.task.lang['field_used_in_filters'] % \
            (item.f_field_name.value, names)
        return mess

###############################################################################
#                                 sys_indices                                 #
###############################################################################

def update_index(delta):
    it = delta.task.sys_items.copy()
    it.set_where(id=delta.owner_rec_id.value)
    it.open()
    if it.record_count():
        return not it.f_virtual_table.value
    else:
        return True

def change_foreign_index(delta):
    items = delta.task.sys_items.copy()
    items.filters.id.value = delta.owner_rec_id.value
    items.open()
    it_fields = items.details.sys_fields
    it_fields.open()
    fields = get_table_fields(items, it_fields)
    new_fields = list(fields)
    return items.recreate_table_sql(db_modules.SQLITE, fields, new_fields, delta)

def indices_insert_sql(item, delta, table_name=None, new_fields=None, manual_update=False, foreign_key_dict=None):
    if not manual_update and update_index(delta):
        if not table_name:
            table_name = delta.task.sys_items.field_by_id(delta.owner_rec_id.value, 'f_table_name')
        db_type = get_db_type(item.task)
        if db_type == db_modules.SQLITE and delta.f_foreign_index.value:
            if not new_fields:
                return change_foreign_index(delta)
        else:
            return delta.create_index_sql(db_type, table_name, new_fields=new_fields, foreign_key_dict=foreign_key_dict)

def indices_execute_insert(item, delta, manual_update):
    sql = indices_insert_sql(item, delta, manual_update=manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception, u'Error while creating index %s: %s' % (delta.f_index_name.value.upper(), error)
    sql = delta.apply_sql()
    return item.task.execute(sql)

def indices_delete_sql(item, delta, manual_update=False):
    if not manual_update and update_index(delta):
        db_type = get_db_type(item.task)
        if db_type == db_modules.SQLITE and delta.f_foreign_index.value:
            return change_foreign_index(delta)
        else:
            return delta.delete_index_sql(db_type)

def indices_execute_delete(item, delta, manual_update):
    sql = indices_delete_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception, u'Error while deleting index %s' % error
    sql = delta.apply_sql()
    return item.task.execute(sql)

def indices_apply_changes(item, delta, params, priv, user_info, env):
    manual_update = params['manual_update']
    table_name = item.task.sys_items.field_by_id(delta.owner_rec_id.value, 'f_table_name')
    if table_name:
        if delta.rec_inserted():
            result = indices_execute_insert(item, delta, manual_update)
        elif delta.rec_deleted():
            result = indices_execute_delete(item, delta, manual_update)
        return result

def server_dump_index_fields(item, dest_list):
    return common.store_index_fields(dest_list)

def server_load_index_fields(item, value):
    return common.load_index_fields(value)

###############################################################################
#                                  sys_roles                                  #
###############################################################################

def privileges_table_get_select(item, query, user_info, enviroment):
    owner_id = query['__master_id']
    owner_rec_id = query['__master_rec_id']
    result_sql =  \
        """
        SELECT "SYS_PRIVILEGES"."ID", "SYS_PRIVILEGES"."DELETED", "SYS_PRIVILEGES"."OWNER_ID",
        "SYS_PRIVILEGES"."OWNER_REC_ID",
        "SYS_ITEMS"."ID",
        "SYS_PRIVILEGES"."F_CAN_VIEW",
        "SYS_PRIVILEGES"."F_CAN_CREATE",
        "SYS_PRIVILEGES"."F_CAN_EDIT",
        "SYS_PRIVILEGES"."F_CAN_DELETE",
        "SYS_ITEMS"."F_NAME" AS "ITEM_ID_LOOKUP"
        FROM (SYS_ITEMS LEFT JOIN  "SYS_PRIVILEGES" ON "SYS_PRIVILEGES"."ITEM_ID" = "SYS_ITEMS"."ID" AND
            "SYS_PRIVILEGES"."DELETED" = 0 and SYS_PRIVILEGES.OWNER_ID = %s AND SYS_PRIVILEGES.OWNER_REC_ID = %s)
        WHERE "SYS_ITEMS"."DELETED" = 0 AND "SYS_ITEMS"."TYPE_ID" IN (10, 11, 12, 13) AND "SYS_ITEMS"."TABLE_ID" = 0
        ORDER BY "SYS_ITEMS"."TYPE_ID", "ITEM_ID_LOOKUP"
        """
    result_sql = result_sql % (owner_id, owner_rec_id)

    error_mes = ''
    try:
        rows = item.task.execute_select(result_sql)
    except Exception, e:
        error_mes = e.message
    return rows, error_mes

def roles_changed(item):
    item.task.app.roles = None

def privileges_open(item, params, user_info, enviroment):
    item_id = params['item_id']
    result_sql =  \
    """
    SELECT p.ID,
    p.DELETED,
    %s AS OWNER_ID,
    r.ID AS OWNER_REC_ID,
    %s AS ITEM_ID,
    p."F_CAN_VIEW",
    p."F_CAN_CREATE",
    p."F_CAN_EDIT",
    p."F_CAN_DELETE",
    r."F_NAME" AS "ITEM_ID_LOOKUP"
    FROM (SYS_ROLES AS r LEFT JOIN  "SYS_PRIVILEGES" AS p ON p."OWNER_REC_ID" = r."ID" AND
        p."DELETED" = 0 AND ITEM_ID = %s)
    WHERE r."DELETED" = 0
    ORDER BY "ITEM_ID_LOOKUP"
    """
    result_sql = result_sql % (item.task.sys_roles.ID, item_id, item_id)

    error_mes = ''
    try:
        rows = item.task.execute_select(result_sql)
    except Exception, e:
        error_mes = e.message
    return rows, error_mes


def register_defs(task):
    task.register(server_check_connection)
    task.register(server_set_task_name)
    task.register(server_set_project_langage)
    task.register(server_update_has_children)
    task.register(server_export_task)
    task.register(server_import_task)
    task.register(server_find_in_task)
    task.register(server_web_print_code)
    task.register(server_load_report_module)
    task.register(server_store_report_module)
    task.register(server_item_info)
    task.register(server_save_edit)
    task.register(server_get_file_info)
    task.register(server_save_file)
    task.register(get_fields_next_id)
    task.register(server_get_db_options)
    task.register(server_create_task)
    task.register(server_get_task_info)
    task.register(server_can_delete_lookup_list)
    task.register(clear_edited)
    task.register(set_edited)
    task.register(check_doc_edited)
    task.sys_params.on_apply = do_on_apply_sys_changes
    task.sys_tasks.on_apply = do_on_apply_sys_changes
    task.sys_items.register(server_can_delete)
    task.sys_items.register(server_group_is_empty)
    task.sys_items.register(server_load_interface)
    task.sys_items.register(server_store_interface)
    task.sys_items.register(server_update_details)
    task.sys_items.on_apply = items_apply_changes
    task.sys_fields.register(server_can_delete_field)
    task.sys_filters.on_apply = do_on_apply_changes
    task.sys_report_params.on_apply = do_on_apply_changes
    task.sys_indices.on_apply = indices_apply_changes
    task.sys_indices.register(server_dump_index_fields)
    task.sys_indices.register(server_load_index_fields)
    task.role_privileges.on_open = privileges_table_get_select
    task.sys_privileges.on_open = privileges_open
    task.sys_roles.register(roles_changed)
