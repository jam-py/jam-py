import os
import json
import hashlib
import datetime
import time
import zipfile
import shutil
import traceback
import sqlite3
import zlib
import base64
from threading import Thread, Lock
from operator import itemgetter
from esprima import parseScript, nodes

import jam.common as common
from jam.common import error_message, file_read, file_write
import jam.db.db_modules as db_modules
from jam.server_classes import *
from jam.events import get_events
from jam.execute import execute_sql
import jam.langs as langs
from werkzeug._compat import iteritems, iterkeys, to_unicode, to_bytes, text_type, string_types

def read_language(task):
    result = None
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT F_LANGUAGE FROM SYS_PARAMS')
        rec = cursor.fetchall()
    finally:
        con.rollback()
        con.close()
    if rec:
        result = rec[0][0]
    if not result:
        result = 1
    return result

def read_setting(task):
    sql = 'SELECT '
    keys = list(iterkeys(common.DEFAULT_SETTINGS))
    for key in keys:
        sql += 'F_%s, ' % key
    sql = sql[:-2]
    sql += ' FROM SYS_PARAMS'
    result = None
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute(sql)
        rec = cursor.fetchall()
    finally:
        con.rollback()
        con.close()
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
    for key in iterkeys(common.SETTINGS):
        common.__dict__[key] = common.SETTINGS[key]

def write_setting(task):
    sql = 'UPDATE SYS_PARAMS SET '
    params = []
    for key in iterkeys(common.DEFAULT_SETTINGS):
        value = common.SETTINGS[key]
        setting_type = type(common.DEFAULT_SETTINGS[key])
        if setting_type == bool:
            if value:
                value = 1
            else:
                value = 0
        if setting_type in string_types:
            sql += 'F_%s="%s", ' % (key, value)
        else:
            sql += 'F_%s=%s, ' % (key, value)
    sql = sql[:-2]
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute(sql)
        con.commit()
    except:
        con.rollback()
    finally:
        con.close()

def get_value_list(str_list, order=False):

    def getKey(item):
        return item[1]

    result = []
    for i, s in enumerate(str_list):
        result.append([i + 1, s])
    if order:
        result = sorted(result, key=getKey)
    return result

def create_items(task):
    task.items = []
    task.sys_catalogs = Group(task, task, 'catalogs', task.language('catalogs'))
    task.sys_tables = Group(task, task, 'tables', task.language('details'), visible=False)

    task.sys_items = task.sys_catalogs.add_catalog('sys_items', 'Items', 'SYS_ITEMS')
    task.sys_fields = task.sys_tables.add_table('sys_fields', task.language('fields'), 'SYS_FIELDS')
    task.sys_params = task.sys_catalogs.add_catalog('sys_params', '', 'SYS_PARAMS')
    task.sys_langs = task.sys_catalogs.add_catalog('sys_langs', 'Languages', 'SYS_LANGS')

    task.sys_params.add_field(1, 'id', 'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_params.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_params.add_field(3, 'f_safe_mode', task.language('safe_mode'), common.BOOLEAN)
    task.sys_params.add_field(4, 'f_debugging', task.language('debugging'), common.BOOLEAN, edit_visible=False)
    task.sys_params.add_field(5, 'f_con_pool_size', task.language('con_pool_size'), common.INTEGER, required=False)
    task.sys_params.add_field(6, 'f_language', task.language('language'), common.INTEGER, True, task.sys_langs, 'f_name', enable_typeahead=True)
    task.sys_params.add_field(7, 'f_version', task.language('version'), common.TEXT, size = 256)
    task.sys_params.add_field(8, 'f_mp_pool', task.language('mp_pool'), common.BOOLEAN)
    task.sys_params.add_field(9, 'f_persist_con', task.language('persist_con'), common.BOOLEAN)
    task.sys_params.add_field(10, 'f_single_file_js', task.language('single_file_js'), common.BOOLEAN)
    task.sys_params.add_field(11, 'f_dynamic_js', task.language('dynamic_js'), common.BOOLEAN)
    task.sys_params.add_field(12, 'f_compressed_js', task.language('compressed_js'), common.BOOLEAN)
    task.sys_params.add_field(13, 'f_field_id_gen', 'f_field_id_gen', common.INTEGER)
    task.sys_params.add_field(14, 'f_timeout', task.language('session_timeout'), common.INTEGER)
    task.sys_params.add_field(15, 'f_delete_reports_after', task.language('delete_reports_after'), common.INTEGER)
    task.sys_params.add_field(16, 'f_ignore_change_ip', task.language('ignore_change_ip'), common.BOOLEAN)
    task.sys_params.add_field(17, 'f_history_item', task.language('history'), common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_params.add_field(18, 'f_lock_item', 'Lock item', common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_params.add_field(19, 'f_sys_group', task.language('system_group'), common.INTEGER)
    task.sys_params.add_field(20, 'f_theme', task.language('theme'), common.INTEGER, required=True, lookup_values=get_value_list(common.THEMES))
    task.sys_params.add_field(21, 'f_small_font', task.language('small_font'), common.BOOLEAN)
    task.sys_params.add_field(22, 'f_full_width', task.language('full_width'), common.BOOLEAN)
    task.sys_params.add_field(23, 'f_forms_in_tabs', task.language('forms_in_tabs'), common.BOOLEAN)
    task.sys_params.add_field(24, 'f_max_content_length', 'Max content length (MB)', common.INTEGER)
    task.sys_params.add_field(25, 'f_secret_key', 'Secret key', common.TEXT, size = 256)

    task.sys_items.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_items.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(3, 'parent', 'Parent id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(4, 'task_id', 'Task id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(5, 'type_id', 'Type id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(6, 'table_id', 'Table id', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(7, 'has_children', 'Has_children', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_items.add_field(8, 'f_index', 'Index', common.INTEGER, visible=False, edit_visible=False)
    task.sys_items.add_field(9, 'f_name', task.language('caption'), common.TEXT, required=True, size=256)
    task.sys_items.add_field(10, 'f_item_name', task.language('name'), common.TEXT, required=True, size=256)
    task.sys_items.add_field(11, 'f_table_name', task.language('table_name'), common.TEXT, size=256)
    task.sys_items.add_field(12, 'f_gen_name', task.language('gen_name'), common.TEXT, size=256)
    task.sys_items.add_field(13, 'f_view_template', task.language('report_template'), common.TEXT, size=256)
    task.sys_items.add_field(14, 'f_visible', task.language('visible'), common.BOOLEAN)
    task.sys_items.add_field(15, 'f_soft_delete', task.language('soft_delete'), common.BOOLEAN)
    task.sys_items.add_field(16, 'f_client_module', task.language('client_module'), common.LONGTEXT, visible=False, edit_visible=False)
    task.sys_items.add_field(17, 'f_web_client_module', task.language('client_module'), common.LONGTEXT, visible=False, edit_visible=False)
    task.sys_items.add_field(18, 'f_server_module', task.language('server_module'), common.LONGTEXT, visible=False, edit_visible=False)
    task.sys_items.add_field(19, 'f_info', 'Info', common.LONGTEXT, visible=False, edit_visible=False)
    task.sys_items.add_field(20, 'f_virtual_table', task.language('virtual_table'), common.BOOLEAN)
    task.sys_items.add_field(21, 'f_js_external', task.language('js_external'), common.BOOLEAN)
    task.sys_items.add_field(22, 'f_js_filename', 'js_file_name', common.TEXT, size=1024)
    task.sys_items.add_field(23, 'f_primary_key', task.language('primary_key'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(24, 'f_deleted_flag', task.language('deleted_flag'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(25, 'f_master_id', task.language('master_id'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(26, 'f_master_rec_id', task.language('master_rec_id'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_items.add_field(27, 'f_js_funcs', 'f_js_funcs', common.LONGTEXT, visible=False, edit_visible=False)
    task.sys_items.add_field(28, 'f_keep_history', task.language('history'), common.BOOLEAN)
    task.sys_items.add_field(29, 'f_edit_lock', task.language('edit_lock'), common.BOOLEAN)
    task.sys_items.add_field(30, 'sys_id', 'sys_id', common.INTEGER)
    task.sys_items.add_field(31, 'f_select_all', task.language('select_all'), common.BOOLEAN)

    task.sys_items.add_filter('id', 'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('not_id', 'ID', 'id', common.FILTER_NE, visible=False)
    task.sys_items.add_filter('parent', 'Parent', 'parent', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('task_id', 'Task', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('type_id', 'Type', 'type_id', common.FILTER_IN, visible=False)
    task.sys_items.add_filter('table_id', 'Type', 'table_id', common.FILTER_EQ, visible=False)
    task.sys_items.add_filter('type_id_gt', 'Type', 'type_id', common.FILTER_GT, visible=False)

    task.sys_tasks = task.sys_catalogs.add_catalog('sys_tasks', '', 'SYS_TASKS')
    task.sys_tasks.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(3, 'task_id', 'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_tasks.add_field(4, 'f_name', task.language('caption'), common.TEXT, required=True, size=256, edit_visible=False)
    task.sys_tasks.add_field(5, 'f_item_name', task.language('name'), common.TEXT, required=True, size=256, edit_visible=False)
    task.sys_tasks.add_field(6, 'f_manual_update', task.language('manual_update'), common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_tasks.add_field(7, 'f_db_type', task.language('db_type'), common.INTEGER, required=True, lookup_values=get_value_list(db_modules.DB_TYPE))
    task.sys_tasks.add_field(8, 'f_alias', task.language('db_name'), common.TEXT, required=True, size = 30)
    task.sys_tasks.add_field(9, 'f_login', task.language('login'), common.TEXT, size = 30)
    task.sys_tasks.add_field(10, 'f_password', task.language('password'), common.TEXT, size = 30)
    task.sys_tasks.add_field(11, 'f_host', task.language('host'), common.TEXT, size = 30)
    task.sys_tasks.add_field(12, 'f_port', task.language('port'), common.TEXT, size = 10)
    task.sys_tasks.add_field(13, 'f_encoding', task.language('encoding'), common.TEXT, size = 30)
    task.sys_tasks.add_field(14, 'f_server', 'Server', common.TEXT, size = 30)

    task.sys_tasks.add_filter('task_id', 'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_lookup_lists = task.sys_catalogs.add_catalog('sys_lookup_lists', 'Lookup lists', 'SYS_LOOKUP_LISTS')

    task.sys_lookup_lists.add_field(1, 'id', 'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lookup_lists.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lookup_lists.add_field(3, 'f_name', task.language('name'), common.TEXT, required=True, size=256)
    task.sys_lookup_lists.add_field(4, 'f_lookup_values_text', 'Text to store lookup_values',  common.LONGTEXT)

    task.sys_field_lookups = task.sys_tables.add_table('sys_field_lookups', 'Lookup item', 'SYS_FIELD_LOOKUPS')

    task.sys_field_lookups.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_field_lookups.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_field_lookups.add_field(3, 'f_value', task.language('value'), common.INTEGER)
    task.sys_field_lookups.add_field(4, 'f_lookup', task.language('lookup_value'), common.TEXT, size=612)

    task.sys_fields.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(2, 'deleted', 'Deleted', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(3, 'owner_id', 'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(4, 'owner_rec_id', 'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(5, 'task_id', 'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields.add_field(6, 'f_name',         task.language('caption'), common.TEXT, True, size=256)
    task.sys_fields.add_field(7, 'f_field_name',   task.language('name'), common.TEXT, True, size=256)
    task.sys_fields.add_field(8, 'f_db_field_name',   task.language('db_field_name'), common.TEXT, False, size=256)
    task.sys_fields.add_field(9, 'f_data_type',    task.language('data_type'), common.INTEGER, True,  False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_fields.add_field(10, 'f_size',         task.language('size'), common.INTEGER)
    task.sys_fields.add_field(11, 'f_object',       task.language('object'), common.INTEGER, False, task.sys_items, 'f_item_name')
    task.sys_fields.add_field(12, 'f_object_field',   task.language('object_field'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(13, 'f_object_field1',   task.language('object_field') + ' 2', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(14, 'f_object_field2',   task.language('object_field') + ' 3', common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(15, 'f_master_field', task.language('master_field'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_fields.add_field(16, 'f_multi_select', task.language('multi_select'),  common.BOOLEAN)
    task.sys_fields.add_field(17, 'f_multi_select_all', task.language('multi_select_all'),  common.BOOLEAN)
    task.sys_fields.add_field(18, 'f_enable_typehead', task.language('enable_typehead'),  common.BOOLEAN)
    task.sys_fields.add_field(19, 'f_lookup_values', task.language('lookup_values'), common.INTEGER, False, task.sys_lookup_lists, 'f_name')
    task.sys_fields.add_field(20, 'f_required',     task.language('required'), common.BOOLEAN)
    task.sys_fields.add_field(21, 'f_calculated',   task.language('calculated'), common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_fields.add_field(22, 'f_default',      task.language('default'), common.BOOLEAN)
    task.sys_fields.add_field(23, 'f_read_only',    task.language('read_only'), common.BOOLEAN)
    task.sys_fields.add_field(24, 'f_alignment',    task.language('alignment'), common.INTEGER, lookup_values=get_value_list(common.ALIGNMENT))
    task.sys_fields.add_field(25, 'f_default_value', task.language('default_value'), common.TEXT, False,  False, size=256)
    task.sys_fields.add_field(26, 'f_help',          task.language('help'), common.LONGTEXT, visible=False)
    task.sys_fields.add_field(27, 'f_placeholder',   task.language('placeholder'), common.TEXT, visible=False, size=256)
    task.sys_fields.add_field(28, 'f_mask',  'Mask', common.TEXT, visible=False, size=30)
    task.sys_fields.add_field(29, 'f_default_lookup_value', task.language('default_value'), common.INTEGER, lookup_values=[[0, '']])
    task.sys_fields.add_field(30, 'f_image_edit_width', 'Edit width', common.INTEGER)
    task.sys_fields.add_field(31, 'f_image_edit_height', 'Edit height', common.INTEGER)
    task.sys_fields.add_field(32, 'f_image_view_width', 'View width', common.INTEGER)
    task.sys_fields.add_field(33, 'f_image_view_height', 'View height', common.INTEGER)
    task.sys_fields.add_field(34, 'f_image_placeholder', 'Placeholder image', common.IMAGE, image_edit_width=230)
    task.sys_fields.add_field(35, 'f_image_camera', 'Capture from camera', common.BOOLEAN)
    task.sys_fields.add_field(36, 'f_file_download_btn', 'Download btn', common.BOOLEAN)
    task.sys_fields.add_field(37, 'f_file_open_btn', 'Open btn', common.BOOLEAN)
    task.sys_fields.add_field(38, 'f_file_accept', 'Accept', common.TEXT, size=512)


    task.sys_fields.add_filter('id', 'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('owner_rec_id', 'Owner record ID', 'owner_rec_id', common.FILTER_IN, visible=False)
    task.sys_fields.add_filter('task_id', 'Task', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('not_id', 'not ID', 'id', common.FILTER_NE, visible=False)
    task.sys_fields.add_filter('object', 'Object ID', 'f_object', common.FILTER_EQ, visible=False)
    task.sys_fields.add_filter('master_field_is_null', 'Master field', 'f_master_field', common.FILTER_ISNULL, visible=False)
    task.sys_fields.add_filter('master_field', 'Master field', 'f_master_field', common.FILTER_EQ, visible=False)

    task.item_fields = task.sys_items.add_detail(task.sys_fields)

    task.sys_report_params = task.sys_tables.add_table('sys_report_params', task.language('report_params'), 'SYS_REPORT_PARAMS')

    task.sys_report_params.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(3, 'owner_id', 'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(4, 'owner_rec_id', 'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(5, 'task_id', 'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(6, 'f_index',        task.language('index'),   common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(7, 'f_name',         task.language('caption'),      common.TEXT, True, size = 30)
    task.sys_report_params.add_field(8, 'f_param_name',   task.language('name'),          common.TEXT, True, size = 30)
    task.sys_report_params.add_field(9, 'f_data_type',    task.language('data_type'),          common.INTEGER, True,  False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_report_params.add_field(10, 'f_size',         task.language('size'),  common.INTEGER, visible=False, edit_visible=False)
    task.sys_report_params.add_field(11, 'f_object',       task.language('object'),       common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_report_params.add_field(12, 'f_object_field',   task.language('object_field'),  common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(13, 'f_object_field1',   task.language('object_field'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(14, 'f_object_field2',   task.language('object_field'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(15, 'f_multi_select', task.language('multi_select'),  common.BOOLEAN)
    task.sys_report_params.add_field(16, 'f_multi_select_all', task.language('multi_select_all'),  common.BOOLEAN)
    task.sys_report_params.add_field(17, 'f_enable_typehead', task.language('enable_typehead'),  common.BOOLEAN)
    task.sys_report_params.add_field(18, 'f_lookup_values', task.language('lookup_values'), common.INTEGER, False, task.sys_lookup_lists, 'f_name')
    task.sys_report_params.add_field(19, 'f_required',     task.language('required'),        common.BOOLEAN)
    task.sys_report_params.add_field(20, 'f_visible',      task.language('visible'),    common.BOOLEAN)
    task.sys_report_params.add_field(21, 'f_alignment',    task.language('alignment'), common.INTEGER, lookup_values=get_value_list(common.ALIGNMENT))
    task.sys_report_params.add_field(22, 'f_master_field', task.language('master_field'), common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_report_params.add_field(23, 'f_help',         task.language('help'), common.LONGTEXT, visible=False)
    task.sys_report_params.add_field(24, 'f_placeholder',  task.language('placeholder'), common.TEXT, visible=False, size=256)

    task.sys_report_params.add_filter('owner_rec_id', 'Owner rec ID ', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_report_params.add_filter('task_id', 'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_indices = task.sys_tables.add_table('sys_indices', task.language('indices'), 'SYS_INDICES')

    task.sys_indices.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(3, 'owner_id', 'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(4, 'owner_rec_id', 'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(5, 'task_id', 'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_indices.add_field(6, 'f_index_name', task.language('index_name'), common.TEXT, True, size = 100)
    task.sys_indices.add_field(7, 'descending', task.language('descending'), common.BOOLEAN)
    task.sys_indices.add_field(8, 'f_unique_index', task.language('unique_index'), common.BOOLEAN)
    task.sys_indices.add_field(9, 'f_foreign_index', task.language('foreign_index'), common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_indices.add_field(10, 'f_foreign_field', task.language('foreign_field'), common.INTEGER, False, task.sys_fields, 'f_field_name', visible=False, edit_visible=False)
    task.sys_indices.add_field(11, 'f_fields_list', task.language('fields'), common.TEXT, size = 100, visible=False, edit_visible=False)

    task.sys_indices.add_filter('id', 'ID', 'id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('owner_rec_id', 'Owner record ID', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('task_id', 'Task ID', 'task_id', common.FILTER_EQ, visible=False)
    task.sys_indices.add_filter('foreign_index', 'Owner record ID', 'f_foreign_index', common.FILTER_EQ, visible=False)

    task.sys_filters = task.sys_tables.add_table('sys_filters', task.language('filters'), 'SYS_FILTERS')

    task.sys_filters.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(3, 'owner_id', 'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(4, 'owner_rec_id', 'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(5, 'task_id', 'Task ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(6, 'f_index',     task.language('index'),   common.INTEGER, visible=False, edit_visible=False)
    task.sys_filters.add_field(7, 'f_field',     task.language('field'),    common.INTEGER, False, task.sys_fields, 'f_field_name')
    task.sys_filters.add_field(8, 'f_name',      task.language('caption'), common.TEXT, True)
    task.sys_filters.add_field(9, 'f_filter_name',  task.language('name'),     common.TEXT, True)
    task.sys_filters.add_field(10, 'f_data_type', task.language('data_type'), common.INTEGER, False,  visible=False, edit_visible=False, lookup_values=get_value_list(common.FIELD_TYPES))
    task.sys_filters.add_field(11, 'f_type',      task.language('filter_type'), common.INTEGER, False, lookup_values=get_value_list(common.FILTER_STRING))
    task.sys_filters.add_field(12, 'f_multi_select_all', task.language('multi_select_all'),  common.BOOLEAN, edit_visible=False)
    task.sys_filters.add_field(13, 'f_visible',   task.language('visible'),    common.BOOLEAN)
    task.sys_filters.add_field(14, 'f_help',      task.language('help'), common.LONGTEXT, visible=False)
    task.sys_filters.add_field(15, 'f_placeholder', task.language('placeholder'), common.TEXT, visible=False, size=256)


    task.sys_filters.add_filter('owner_rec_id', 'Owner rec ID ', 'owner_rec_id', common.FILTER_EQ, visible=False)
    task.sys_filters.add_filter('task_id', 'Task ID', 'task_id', common.FILTER_EQ, visible=False)

    task.sys_users = task.sys_catalogs.add_catalog('sys_users', task.language('users'), 'SYS_USERS')
    task.sys_roles = task.sys_catalogs.add_catalog('sys_roles', task.language('roles'), 'SYS_ROLES')

    task.sys_users.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_users.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_users.add_field(3, 'f_name', task.language('name'), common.TEXT, required=True, size=128)
    task.sys_users.add_field(4, 'f_login', task.language('login'), common.TEXT, required=True, size=128)
    task.sys_users.add_field(5, 'f_password', task.language('password'), common.TEXT, required=False, size=128)
    task.sys_users.add_field(6, 'f_role', task.language('role'), common.INTEGER, True, task.sys_roles, 'f_name')
    task.sys_users.add_field(7, 'f_info', task.language('info'), common.TEXT, edit_visible=False, size=128)
    task.sys_users.add_field(8, 'f_admin', task.language('admin'), common.BOOLEAN)
    task.sys_users.add_field(9, 'f_psw_hash', 'psw_hash', common.TEXT, edit_visible=False, size=10000)
    task.sys_users.add_field(10, 'f_ip', 'ip', common.TEXT, edit_visible=False, size=10000)
    task.sys_users.add_field(11, 'f_uuid', 'uuid', common.TEXT, edit_visible=False, size=10000)

    task.sys_roles.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_roles.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_roles.add_field(3, 'f_name', task.language('roles'), common.TEXT, required=True, size=30)

    task.sys_roles.add_filter('id', 'ID', 'id', common.FILTER_EQ, visible=False)

    task.sys_privileges = task.sys_tables.add_table('sys_privileges', task.language('privileges'), 'SYS_PRIVILEGES')

    task.sys_privileges.add_field(1, 'id', 'Record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(3, 'owner_id', 'Owner ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(4, 'owner_rec_id', 'Owner record ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_privileges.add_field(5, 'item_id', task.language('item'), common.INTEGER, False, task.sys_items, 'f_name')
    task.sys_privileges.add_field(6, 'owner_item', task.language('owner'), common.TEXT, size=128)
    task.sys_privileges.add_field(7, 'f_can_view', task.language('can_view'), common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(8, 'f_can_create', task.language('can_create'), common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(9, 'f_can_edit', task.language('can_edit'), common.BOOLEAN, editable=True)
    task.sys_privileges.add_field(10, 'f_can_delete', task.language('can_delete'), common.BOOLEAN, editable=True)

    task.sys_privileges.add_filter('owner_rec_id', 'Owner record ID', 'owner_rec_id', common.FILTER_EQ, visible=False)

    task.role_privileges = task.sys_roles.add_detail(task.sys_privileges)

    task.sys_code_editor = task.sys_catalogs.add_catalog('sys_code_editor', 'Editor', '')

    task.sys_code_editor.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_code_editor.add_field(2, 'parent', 'parent', common.INTEGER)
    task.sys_code_editor.add_field(3, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_code_editor.add_field(4, 'name', task.language('caption'), common.TEXT, size = 10000)

    task.sys_fields_editor = task.sys_catalogs.add_catalog('sys_fields_editor', 'Editor', '')

    task.sys_fields_editor.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_fields_editor.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_fields_editor.add_field(3, 'name', task.language('caption'), common.TEXT, size = 256)
    task.sys_fields_editor.add_field(4, 'param1', 'param1', common.BOOLEAN)
    task.sys_fields_editor.add_field(5, 'param2', 'param2', common.BOOLEAN)
    task.sys_fields_editor.add_field(6, 'param3', 'param3', common.TEXT, size = 6)
    task.sys_fields_editor.add_field(7, 'width', task.language('width'), common.INTEGER)
    task.sys_fields_editor.add_field(8, 'col_count', task.language('col_count'), common.INTEGER)
    task.sys_fields_editor.add_field(9, 'in_well', task.language('in_well'), common.BOOLEAN)
    task.sys_fields_editor.add_field(10, 'pagination', 'Pagination', common.BOOLEAN)
    task.sys_fields_editor.add_field(11, 'row_count', task.language('row_count'), common.INTEGER)
    task.sys_fields_editor.add_field(11, 'row_line_count', task.language('row_line_count'), common.INTEGER)
    task.sys_fields_editor.add_field(11, 'freeze_count', task.language('freeze_count'), common.INTEGER)
    task.sys_fields_editor.add_field(12, 'expand_selected_row', task.language('expand_selected_row'), common.INTEGER)
    task.sys_fields_editor.add_field(13, 'multiselect', task.language('multi_select'), common.BOOLEAN)
    task.sys_fields_editor.add_field(14, 'dblclick_edit', task.language('dblclick_edit'), common.BOOLEAN)
    task.sys_fields_editor.add_field(15, 'sort_fields', task.language('sort_fields'), common.KEYS, False, task.sys_fields, 'id')
    task.sys_fields_editor.add_field(16, 'edit_fields', task.language('edit_fields'), common.KEYS, False, task.sys_fields, 'id')
    task.sys_fields_editor.add_field(16, 'edit_fields', task.language('edit_fields'), common.KEYS, False, task.sys_fields, 'id')
    task.sys_fields_editor.add_field(17, 'summary_fields', task.language('summary_fields'), common.KEYS, False, task.sys_fields, 'id')
    task.sys_fields_editor.add_field(18, 'label_size', task.language('label_size'), common.INTEGER, lookup_values=get_value_list(['xSmall', 'Small', 'Medium', 'Large', 'xLarge']))
    task.sys_fields_editor.add_field(19, 'history_button', task.language('history'), common.BOOLEAN)
    task.sys_fields_editor.add_field(20, 'refresh_button', task.language('refresh_button'), common.BOOLEAN)
    task.sys_fields_editor.add_field(21, 'close_button', task.language('close_button'), common.BOOLEAN)
    task.sys_fields_editor.add_field(22, 'close_on_escape', task.language('close_on_escape'), common.BOOLEAN)
    task.sys_fields_editor.add_field(23, 'form_border', task.language('form_border'), common.BOOLEAN)
    task.sys_fields_editor.add_field(24, 'form_header', task.language('form_header'), common.BOOLEAN)
    task.sys_fields_editor.add_field(25, 'enable_search', task.language('enable_search'), common.BOOLEAN)
    task.sys_fields_editor.add_field(26, 'enable_filters', task.language('enable_filters'), common.BOOLEAN)
    task.sys_fields_editor.add_field(27, 'edit_details', task.language('edit_details'), common.KEYS, False, task.sys_items, 'id')
    task.sys_fields_editor.add_field(28, 'view_detail', task.language('view_detail'), common.KEYS, False, task.sys_items, 'id')
    task.sys_fields_editor.add_field(29, 'detail_height', 'Detail height', common.INTEGER, False)
    task.sys_fields_editor.add_field(30, 'buttons_on_top', 'Buttons on top', common.BOOLEAN)
    task.sys_fields_editor.add_field(31, 'height', 'Height', common.INTEGER, False)
    task.sys_fields_editor.add_field(32, 'modeless', task.language('modeless'), common.BOOLEAN)
    task.sys_fields_editor.add_field(33, 'search_field', task.language('default_search_field'), common.KEYS, False, task.sys_fields, 'id')

    task.sys_search = task.sys_catalogs.add_catalog('sys_search', task.language('find_in_task'), '')

    task.sys_search.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_search.add_field(2, 'parent', 'parent', common.INTEGER)
    task.sys_search.add_field(3, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_search.add_field(4, 'find_text', task.language('find'), common.TEXT, size = 1000)
    task.sys_search.add_field(5, 'case_sensitive', task.language('case_sensitive'), common.BOOLEAN)
    task.sys_search.add_field(6, 'whole_words', task.language('whole_words'), common.BOOLEAN)

    task.sys_new_group = task.sys_catalogs.add_catalog('sys_new_group', task.language('new_group_type'), '')

    task.sys_new_group.add_field(1, 'group_type',  'Group type', common.INTEGER, required=True, lookup_values=get_value_list(common.GROUP_TYPES))

    task.sys_languages = task.sys_catalogs.add_catalog('sys_languages', 'Languages', 'SYS_LANGUAGES')

    task.sys_languages.add_field(1, 'id', 'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_languages.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_languages.add_field(3, 'f_abr', 'ISO code', common.INTEGER, required=True)
    task.sys_languages.add_field(4, 'f_name', 'Language', common.TEXT, required=True, size=20)
    task.sys_languages.add_field(5, 'f_rtl', 'Right to left', common.BOOLEAN)

    task.sys_countries = task.sys_catalogs.add_catalog('sys_countries', 'Countries', 'SYS_COUNTRIES')

    task.sys_countries.add_field(1, 'id', 'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_countries.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_countries.add_field(3, 'f_abr', 'ISO code', common.INTEGER, required=True)
    task.sys_countries.add_field(4, 'f_name', 'Country', common.TEXT, required=True, size=20)

    task.sys_langs.add_field(1, 'id', 'ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_langs.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_langs.add_field(3, 'f_name', 'Language', common.TEXT, required=True, size=100)
    task.sys_langs.add_field(4, 'f_abr', 'ISO code', common.TEXT, visible=False, size=20)
    task.sys_langs.add_field(5, 'f_language', 'Language', common.INTEGER, True, task.sys_languages, 'f_name', visible=False, enable_typeahead=True)
    task.sys_langs.add_field(6, 'f_country', 'Country', common.INTEGER, True, task.sys_countries, 'f_name', visible=False, enable_typeahead=True)
    task.sys_langs.add_field(7, 'f_decimal_point', 'Decimal point', common.TEXT, size=1, visible=False, edit_visible=False)
    task.sys_langs.add_field(8, 'f_mon_decimal_point', 'Monetory decimal point', common.TEXT, size=1, visible=False, edit_visible=False)
    task.sys_langs.add_field(9, 'f_mon_thousands_sep', 'Monetory thousands separator', common.TEXT, size=3, visible=False, edit_visible=False)
    task.sys_langs.add_field(10, 'f_currency_symbol', 'Currency symbol', common.TEXT, size=10, visible=False, edit_visible=False)
    task.sys_langs.add_field(11, 'f_frac_digits', 'Number of fractional digits', common.INTEGER, visible=False, edit_visible=False)
    task.sys_langs.add_field(12, 'f_p_cs_precedes', 'Currency symbol precedes the value (positive values)', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_langs.add_field(13, 'f_n_cs_precedes', 'Currency symbol precedes the value (negative values)', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_langs.add_field(14, 'f_p_sep_by_space', 'Currency symbol is separated by a space (positive values)', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_langs.add_field(15, 'f_n_sep_by_space', 'Currency symbol is separated by a space (negative values)', common.BOOLEAN, visible=False, edit_visible=False)
    task.sys_langs.add_field(16, 'f_positive_sign', 'Symbol for a positive monetary value', common.TEXT, size=1, visible=False, edit_visible=False)
    task.sys_langs.add_field(17, 'f_negative_sign', 'Symbol for a negative monetary value', common.TEXT, size=1, visible=False, edit_visible=False)
    task.sys_langs.add_field(18, 'f_p_sign_posn', 'The position of the sign (positive values)', common.INTEGER, visible=False, edit_visible=False)
    task.sys_langs.add_field(19, 'f_n_sign_posn', 'The position of the sign (negative values)', common.INTEGER, visible=False, edit_visible=False)
    task.sys_langs.add_field(20, 'f_d_fmt', 'Date format string', common.TEXT, size=30, visible=False, edit_visible=False)
    task.sys_langs.add_field(21, 'f_d_t_fmt', 'Date and time format string', common.TEXT, size=30, visible=False, edit_visible=False)
    task.sys_langs.add_field(22, 'f_rtl', 'Right to left', common.BOOLEAN, visible=False)

    task.sys_lang_keys_values = task.sys_catalogs.add_catalog('sys_lang_keys_values', 'Language values', '')

    task.sys_lang_keys_values.add_field(1, 'id', 'ID', common.INTEGER, visible=True, edit_visible=False)
    task.sys_lang_keys_values.add_field(2, 'deleted', 'Deleted flag', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_keys_values.add_field(3, 'f_type', 'Key type', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_keys_values.add_field(3, 'f_lang', 'Language ID', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_keys_values.add_field(4, 'f_key', 'Key', common.INTEGER, visible=False, edit_visible=False)
    task.sys_lang_keys_values.add_field(5, 'f_value', 'Translation', common.TEXT, size=1048)
    task.sys_lang_keys_values.add_field(6, 'f_key_str', 'Key', common.TEXT, size=1048)
    task.sys_lang_keys_values.add_field(6, 'f_eng_str', 'English', common.TEXT, size=1048)


    def init_item(item, id_value):
        item.ID = id_value
        item.soft_delete = False
        item._primary_key = 'id'
        item._primary_key_db_field_name = 'ID'
        item._deleted_flag = 'deleted'
        item._deleted_flag_db_field_name = 'DELETED'
        item._master_id = ''
        item._master_id_db_field_name = ''
        item._master_rec_id = ''
        item._master_rec_id_db_field_name = ''
        if item.master:
            item._master_id = 'owner_id'
            item._master_id_db_field_name = 'OWNER_ID'
            item._master_rec_id = 'owner_rec_id'
            item._master_rec_id_db_field_name = 'OWNER_REC_ID'
        item._view_list = []
        item._edit_list = []
        if hasattr(item, '_fields'):
            for field in item._fields:
                field.alignment = common.get_alignment(field.data_type, field.lookup_item, field.lookup_values)
                if field.lookup_field:
                    field.lookup_db_field = field.lookup_field.upper()
                if field.view_visible:
                    item._view_list.append([field.ID])
                if field.edit_visible:
                    item._edit_list.append([field.ID])

    init_item(task, 0)
    init_item(task.sys_users, 1)
    init_item(task.sys_roles, 2)
    init_item(task.sys_items, 3)
    init_item(task.sys_fields, 4)
    init_item(task.sys_filters, 5)
    init_item(task.item_fields, 6)
    init_item(task.sys_privileges, 7)
    init_item(task.role_privileges, 8)
    init_item(task.sys_tasks, 9)
    init_item(task.sys_indices, 10)
    init_item(task.sys_params, 11)
    init_item(task.sys_report_params, 12)
    init_item(task.sys_code_editor, 14)
    init_item(task.sys_fields_editor, 15)
    init_item(task.sys_search, 16)
    init_item(task.sys_field_lookups, 17)
    init_item(task.sys_lookup_lists, 18)
    init_item(task.sys_new_group, 19)
    init_item(task.sys_languages, 20)
    init_item(task.sys_countries, 21)
    init_item(task.sys_langs, 22)
    init_item(task.sys_lang_keys_values, 23)

    task.sys_catalogs.ID = 101
    task.sys_tables.ID = 102

    for i in range(1, 23):
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

    def do_updates(con, field, item_name):
        if item_name == 'sys_privileges' and field.field_name.lower() == 'owner_item':
            cursor = con.cursor()
            cursor.execute("SELECT ID FROM SYS_ITEMS WHERE TABLE_ID > 0 AND DELETED = 0")
            details = cursor.fetchall()
            cursor.execute("SELECT ID FROM SYS_ROLES WHERE DELETED = 0")
            roles = cursor.fetchall()
            for d in details:
                for r in roles:
                    cursor.execute("""
                        INSERT INTO SYS_PRIVILEGES
                        (DELETED, OWNER_ID, OWNER_REC_ID, ITEM_ID, F_CAN_VIEW, F_CAN_CREATE, F_CAN_EDIT, F_CAN_DELETE)
                        values (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (0, 2, r[0], d[0], True, True, True, True))
            con.commit()

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
                print(sql)
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
    try:
        cursor = con.cursor()
        for group in task.items:
            for item in group.items:
                if item.table_name and not item.master:
                    if check_table_exists(item):
                        check_item_fields(item)
    finally:
        con.close()

def delete_reports(task):
    while True:
        if common.SETTINGS['DELETE_REPORTS_AFTER']:
            path = os.path.join(task.work_dir, 'static', 'reports')
            if os.path.isdir(path):
                for f in os.listdir(path):
                    file_name = os.path.join(path, f)
                    if os.path.isfile(file_name):
                        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
                        hours, sec = divmod(delta.total_seconds(), 3600)
                        if hours > common.SETTINGS['DELETE_REPORTS_AFTER']:
                            os.remove(file_name)
        time.sleep(1)

def init_delete_reports(task):
    t = threading.Thread(target=delete_reports, args=(task,))
    t.daemon = True
    t.start()

def read_secret_key(task):
    result = None
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT f_secret_key FROM SYS_PARAMS')
        rec = cursor.fetchall()
    finally:
        con.rollback()
        con.close()
    result = rec[0][0]
    if result is None:
        result = ''
    return result

def init_admin(task):
    langs.update_langs(task)
    task.set_language(read_language(task))
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
    task.secret_key = read_secret_key(task)
    task.safe_mode = common.SETTINGS['SAFE_MODE']
    task.max_content_length = common.SETTINGS['MAX_CONTENT_LENGTH']
    task.timeout = common.SETTINGS['TIMEOUT']
    task.ignore_change_ip = common.SETTINGS['IGNORE_CHANGE_IP']
    task.ignore_change_uuid = True
    task.set_language(common.SETTINGS['LANGUAGE'])
    task.item_caption = task.language('admin')
    register_events(task)
    init_fields_next_id(task)
    init_delete_reports(task)
    return task

def create_admin(app):
    task = AdminTask(app, 'admin', 'Administrator', '', db_modules.SQLITE, db_database='admin.sqlite')
    init_admin(task)
    return task

def db_info(task):
    tasks = task.sys_tasks.copy()
    tasks.open()
    return tasks.f_db_type.value, tasks.f_server.value, tasks.f_alias.value, tasks.f_login.value, \
        tasks.f_password.value, tasks.f_host.value, \
        tasks.f_port.value, tasks.f_encoding.value

def execute(task, task_id, sql, params=None):
    if task_id == 0:
        result_set, error = task.execute(sql, params)
        return error
    else:
        connection = None
        db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
        db_module = db_modules.get_db_module(db_type)
        connection, (result_set, error) = execute_sql(db_module, \
            db_server, db_database, db_user, db_password, db_host, db_port,
            db_encoding, connection, sql, params)
        if connection:
            connection.rollback()
            connection.close()
        return error

def execute_ddl(task, db_sql):
    connection = None
    success = True
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    connection, (result_set, error, info) = execute_sql(db_module, \
        db_server, db_database, db_user, db_password, db_host, db_port,
        db_encoding, connection, db_sql, ddl=True)
    if db_module.DDL_ROLLBACK:
        if error:
            success = False
    if connection:
        connection.close()
    return success, error, info

def execute_select(task_id, sql, params=None):
    return task.select(sql)

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
    privileges = {}
    roles = []
    r = task.sys_roles.copy()
    r.open()
    for r in r:
        privileges[r.id.value] = get_privileges(task, r.id.value)
        roles.append([r.id.value, r.f_name.value])
    return roles, privileges

def login(task, log, password, admin, ip=None, session_uuid=None):
    user_id = None
    user_info = {}
    if task.safe_mode:
        users = task.sys_users.copy()
        users.set_where(f_password=password)
        users.open()
        for u in users:
            if u.f_login.value.strip() == log.strip() and u.f_password.value == password:
                if not admin or u.f_admin.value == admin:
                    user_id = u.id.value
                    user_info = {
                        'user_id': u.id.value,
                        'role_id': u.f_role.value,
                        'role_name': u.f_role.display_text,
                        'user_name': u.f_name.value,
                        'admin': u.f_admin.value
                    }
                    if ip or session_uuid:
                        task.execute("UPDATE SYS_USERS SET F_IP='%s', F_UUID='%s' WHERE ID=%s" % (ip, session_uuid, u.id.value))
                    break
    return user_info

def user_valid_ip(task, user_id, ip):
    res = task.select("SELECT F_IP FROM SYS_USERS WHERE ID=%s" % user_id)
    if res and res[0][0] == ip:
        return True
    return False

def user_valid_uuid(task, user_id, session_uuid):
    res = task.select("SELECT F_UUID FROM SYS_USERS WHERE ID=%s" % user_id)
    if res and res[0][0] == session_uuid:
        return True
    return False

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
            it.f_js_filename.value, it_task.f_db_type.value, it_task.f_server.value,
            it_task.f_alias.value, it_task.f_login.value, it_task.f_password.value,
            it_task.f_host.value, it_task.f_port.value, it_task.f_encoding.value,
            task.task_con_pool_size, task.task_mp_pool, task.task_persist_con
            )
        result.ID = it.id.value
        load_task(result, app)
    else:
        raise common.ProjectNotCompleted()
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
                    edit_visible = False
                    edit_index = -1
                    field = item.add_field(sys_fields.id.value,
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
                        sys_fields.f_placeholder.value,
                        sys_fields.f_object_field1.value,
                        sys_fields.f_object_field2.value,
                        sys_fields.f_db_field_name.value,
                        sys_fields.f_mask.value,
                        sys_fields.f_image_edit_width.value,
                        sys_fields.f_image_edit_height.value,
                        sys_fields.f_image_view_width.value,
                        sys_fields.f_image_view_height.value,
                        sys_fields.f_image_placeholder.value,
                        sys_fields.f_image_camera.value,
                        sys_fields.f_file_download_btn.value,
                        sys_fields.f_file_open_btn.value,
                        sys_fields.f_file_accept.value
                        )

    def create_filters(item, parent_id):
        for rec in sys_filters:
            if sys_filters.owner_rec_id.value == parent_id:
                item.add_filter(
                    sys_filters.f_filter_name.value,
                    sys_filters.f_name.value,
                    sys_filters.f_field.value,
                    sys_filters.f_type.value,
                    sys_filters.f_multi_select_all.value,
                    sys_filters.f_data_type.value,
                    sys_filters.f_visible.value,
                    sys_filters.f_help.value,
                    sys_filters.f_placeholder.value,
                    sys_filters.id.value,
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
                        params.f_multi_select.value,
                        params.f_multi_select_all.value,
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
                        item.gen_name = rec.f_gen_name.value
                        item.virtual_table = rec.f_virtual_table.value
                        item.server_code = rec.f_server_module.value
                        item._keep_history = rec.f_keep_history.value
                        item.edit_lock = rec.f_edit_lock.value
                        item.select_all = rec.f_select_all.value
                        item._primary_key = rec.f_primary_key.value
                        item._deleted_flag = rec.f_deleted_flag.value
                        item._master_id = rec.f_master_id.value
                        item._master_rec_id = rec.f_master_rec_id.value
                        item._sys_id = rec.sys_id.value
                        if group_type_id != common.REPORTS_TYPE:
                            common.load_interface(sys_items)
                            item._view_list = sys_items._view_list
                            item._edit_list = sys_items._edit_list
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
                group = Group(target, target, rec.f_item_name.value, rec.f_name.value, rec.f_view_template.value,
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
                    detail.item_name = it.f_item_name.value
                    detail.ID = it.id.value
                    detail.gen_name = table.gen_name
                    detail.visible = it.f_visible.value
                    detail.view_template = it.f_view_template.value
                    detail.js_filename = it.f_js_filename.value
                    detail.server_code = it.f_server_module.value
                    detail.item_type = common.ITEM_TYPES[detail.item_type_id - 1]
                    common.load_interface(sys_items)
                    detail._view_list = sys_items._view_list
                    detail._edit_list = sys_items._edit_list
                    detail._order_by = sys_items._order_list

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
        lists.open(order_by=['f_name'])
        for l in lists:
            text = l.f_lookup_values_text.value
            target.lookup_lists[l.id.value] = json.loads(l.f_lookup_values_text.value)

    def remove_attr(target):
        for key in list(iterkeys(target.__dict__)):
            try:
                value = target.init_dict[key]
                if hasattr(target.__dict__[key], '__call__'):
                    target.__dict__[key] = value
            except:
                del target.__dict__[key]

    def history_on_apply(item, delta, params):
        raise Exception('Changing of history is not allowed.')

    target.pool.dispose()
    target.pool.recreate()
    task = app.admin
    remove_attr(target)
    target.items = []
    sys_fields = task.sys_fields.copy()
    sys_fields.open(order_by=['id'])
    fields_dict = {}
    for f in sys_fields:
        d = fields_dict.get(f.owner_rec_id.value, [])
        if not d:
            fields_dict[f.owner_rec_id.value] = d
        d.append(f.rec_no)
    sys_filters = task.sys_filters.copy()
    sys_filters.open(order_by=['f_index'])
    sys_params = task.sys_report_params.copy()
    sys_params.open(order_by=['f_index'])
    sys_items = task.sys_items.copy()
    sys_items.details_active = False
    sys_items.open(order_by=['f_index'])
    create_groups(target.ID)
    create_details()
    process_reports()
    process_lookup_lists()
    target.bind_items()
    target.compile_all()
    target.lang = task.lang
    target.locale = task.locale

    params = task.sys_params.copy()
    params.open(fields=['f_history_item', 'f_lock_item'])
    target.history_item = None
    if params.f_history_item.value:
        target.history_item = target.item_by_ID(params.f_history_item.value)
        target.history_item.on_apply = history_on_apply
    if params.f_lock_item.value:
        target.lock_item = target.item_by_ID(params.f_lock_item.value)

    target.first_build = first_build
    target.after_import = after_import
    if target.on_created:
        target.on_created(target)

    sys_fields.free()
    sys_filters.free()
    sys_params.free()
    sys_items.free()

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

def server_check_connection(task, db_type, database, user, password, host, port, encoding, server):
    error = ''
    if db_type:
        try:
            db_module = db_modules.get_db_module(db_type)
            connection = db_module.connect(database, user, password, host, port, encoding, server)
            if connection:
                connection.close()
        except Exception as e:
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
    task.set_language(lang)
    write_setting(task)
    read_setting(task)
    create_items(task)

    items = task.sys_items.copy()
    items.open()
    for it in items:
        it.edit()
        try:
            it.f_name.value = task.language(it.f_item_name.value)
        except Exception as e:
            traceback.print_exc()
        it.post()
    it.apply()

    file_name = 'index.html'
    data = file_read(file_name)
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
            data = data.replace(search, task.language(replace))
        except:
            pass
    file_write(file_name, data)
    register_events(task)

# ~ def server_change_secret_key(task):
    # ~ from base64 import b64encode
    # ~ result = False
    # ~ key = b64encode(os.urandom(20)).decode('utf-8')
    # ~ con = task.create_connection()
    # ~ try:
        # ~ cursor = con.cursor()
        # ~ cursor.execute("UPDATE SYS_PARAMS SET F_SECRET_KEY='%s'" % key)
        # ~ con.commit()
        # ~ task.secret_key = key
        # ~ task.app.task_server_modified = True
        # ~ result = True
    # ~ except:
        # ~ con.rollback()
    # ~ finally:
        # ~ con.close()
    # ~ return result

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
    result['db_type'] = get_db_type(task)
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
            common.zip_html(zip_file)
            common.zip_dir('js', zip_file)
            common.zip_dir('css', zip_file)
            common.zip_dir(os.path.join('static', 'img'), zip_file)
            common.zip_dir(os.path.join('static', 'js'), zip_file)
            common.zip_dir(os.path.join('static', 'css'), zip_file)
            common.zip_dir(os.path.join('static', 'fonts'), zip_file)
            common.zip_dir(os.path.join('static', 'builder'), zip_file)
            common.zip_dir('utils', zip_file, exclude_ext=['.pyc'])
            common.zip_dir('reports', zip_file, exclude_ext=['.xml', '.ods#'], recursive=True)
        if url:
            items = task.sys_items.copy()
            items.set_where(id=task_id)
            items.open()
            result_path = os.path.join(task.work_dir, 'static', '_internal')
            if not os.path.exists(result_path):
                os.makedirs(result_path)
            result_file = '%s_%s_%s_%s.zip' % (items.f_item_name.value, common.SETTINGS['VERSION'],
                task.app.jam_version, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.rename(to_unicode(file_name, 'utf-8'), os.path.join(to_unicode(result_path, 'utf-8'), to_unicode(result_file, 'utf-8')))
            result = '%s/static/_internal/%s' % (url, result_file)
        else:
            result = file_read(file_name)
    finally:
        if os.path.exists(task_file):
            os.remove(task_file)
        if os.path.exists(file_name):
            os.remove(file_name)
    return result

def server_import_task(task, task_id, file_name, from_client=False):
    return task.app.import_metadata(task, task_id, file_name, from_client)

def import_metadata(task, task_id, file_name, from_client=False):

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
        data = file_read(file_name)
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
            new_item.open(expanded=False, fields=field_names, open_empty=True)
            new_item._dataset = dataset
            new_items[item.item_name] = new_item
            old_items[item.item_name] = old_item
        os.remove(file_name)
        db_type = data_lists.get('db_type')
        if not db_type:
            db_type = get_db_type(task)
        return new_items, old_items, db_type

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
                    dic['field_name'] = field.f_db_field_name.value
                    dic['data_type'] = field.f_data_type.value
                    dic['size'] = field.f_size.value
                    dic['default_value'] = ''#field.f_default_value.value
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
            dic['key'] = fields.f_db_field_name.value
            ref_id = fields.f_object.value
            items = new_dict['sys_items']
            items.locate('id', ref_id)
            dic['ref'] = items.f_table_name.value
            primary_key = items.f_primary_key.value
            fields.locate('id', primary_key)
            dic['primary_key'] = fields.f_db_field_name.value
        return dic

    def check_generator(item, delta):
        db_type = get_db_type(item.task)
        db_module = db_modules.get_db_module(db_type)
        for d in delta:
            if d.rec_inserted() and db_module.NEED_GENERATOR and \
                d.f_primary_key.value and not d.f_gen_name.value:
                d.edit()
                d.f_gen_name.value = '%s_SEQ' % d.f_table_name.value
                d.post()

    def update_indexes(new_dict, new_db_type, old_db_type):
        if new_db_type == db_modules.FIREBIRD or old_db_type == db_modules.FIREBIRD:
            item = new_dict['sys_indices']
            for it in item:
                if it.f_fields_list.value:
                    field_list = common.load_index_fields(it.f_fields_list.value)
                    desc = it.descending.value
                    if field_list:
                        it.edit()
                        if new_db_type == db_modules.FIREBIRD:
                            l = []
                            for f in field_list:
                                l.append([f[0], desc])
                            field_list = l
                        elif old_db_type == db_modules.FIREBIRD:
                            desc = field_list[0][1]
                        it.descending.value = desc
                        it.f_fields_list.value = common.store_index_fields(field_list)
                        it.post()

    def update_item_idents(new_dict, item_name, field_names, old_case, new_case):
        item = new_dict[item_name]
        fields = []
        for field_name in field_names:
            fields.append(item.field_by_name(field_name))
        item.log_changes = False
        for it in item:
            it.edit()
            for field in fields:
                if new_case(field.value) == field.value and not field.value.upper() in common.SQL_KEYWORDS:
                    field.value = old_case(field.value)
            it.post()

    def update_idents(new_dict, new_db_type, old_db_type):
        new_case = db_modules.get_db_module(new_db_type).identifier_case
        old_case = db_modules.get_db_module(old_db_type).identifier_case
        if old_case('a') != new_case('a'):
            update_item_idents(new_dict, 'sys_items', ['f_table_name', 'f_gen_name'], old_case, new_case)
            update_item_idents(new_dict, 'sys_fields', ['f_db_field_name'], old_case, new_case)
            update_item_idents(new_dict, 'sys_indices', ['f_index_name'], old_case, new_case)
        update_indexes(new_dict, new_db_type, old_db_type)

    def get_fk_ind():
        fk = {}
        if db_type == db_modules.SQLITE:
            indexes = new_dict['sys_indices']
            for ind in indexes:
                if ind.f_foreign_index.value:
                    dic = get_foreign_key_dict(ind)
                    if not fk.get(ind.owner_rec_id.value):
                        fk[ind.owner_rec_id.value] = []
                    fk[ind.owner_rec_id.value].append(dic)
        return fk

    def analize(dir, db_type):
        try:
            fk_ind = get_fk_ind() # SQLITE only

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
            check_generator(task.sys_items, delta)
            for d in delta:
                if d.rec_inserted():
                    db_sql.append(items_insert_sql(task.sys_items, d,
                        new_fields=get_new_fields(d.id.value),
                        foreign_fields=fk_ind.get(d.id.value)))
                elif d.rec_modified():
                    db_sql.append(items_update_sql(task.sys_items, d))
                elif d.rec_deleted():
                    db_sql.append(items_delete_sql(task.sys_items, d))

            refresh_old_item(old_dict['sys_items'])
            delta = get_delta('sys_items')
            check_generator(task.sys_items, delta)
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

        except Exception as e:
            error = traceback.format_exc()
            print('Import error: %s' % error)
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
                            except Exception as e:
                                print('%s %s' % (module_name, e))

    def project_empty():
        items = task.sys_items.copy(handlers=False)
        items.set_where(task_id=task_id)
        items.open(fields=['id', 'f_table_name'])
        for i in items:
            if i.f_table_name.value:
                return False
        return True

    error = ''
    task.__import_message = ''

    def info_from_error(err):
        arr = str(err).split('\\n')
        error = '<br>'.join(arr)
        return '<div class="text-error">%s</div>' % error

    def show_progress(string):
        print(string)
        task.__import_message += '<h5>' + string + '</h5>'

    def show_info(info):
        task.__import_message += '<div style="margin-left: 30px;">' + info + '</div>'


    db_type = get_db_type(task)
    if db_type == db_modules.SQLITE and not project_empty():
        error = 'Metadata can not be imported into an existing SQLITE project'
        show_progress(error)
        return False, error, task.__import_message
    task.app.under_maintenance = True
    success = False
    try:
        request_count = 0
        if from_client:
            request_count = 1
        file_name = os.path.join(to_unicode(os.getcwd(), 'utf-8'), os.path.normpath(file_name))
        show_progress(task.language('import_reading_data'))
        dir = copy_tmp_files(file_name)
        new_dict, old_dict, new_db_type = get_items(dir)
        if new_db_type != db_type:
            update_idents(new_dict, new_db_type, db_type)
        show_progress(task.language('import_checking_integrity'))
        error = check_items()
        info = ''
        if error:
            show_info(error)
        else:
            show_progress(task.language('import_analyzing'))
            error, db_sql, adm_sql = analize(dir, db_type)
            if error:
                show_info(error)
        if not error:
            success = True
            show_progress(task.language('import_waiting_close'))
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
                show_progress(task.language('import_changing_db'))
                success, error, info = execute_ddl(task, db_sql)
                show_info(info)
            if success:
                show_progress(task.language('import_changing_admin'))
                result, error = task.execute(adm_sql)
                if error:
                    success = False
            if success:
                show_progress(task.language('import_copying'))
                copy_files(dir)
            if success:
                read_setting(task)
                reload_utils()
                read_setting(task)
                load_task(task.app.task, task.app, first_build=False, after_import=True)
                task.app.privileges = None
                task.app.task.mod_count += 1
                update_events_code(task)
    except Exception as e:
        try:
            success = False
            error = str(e)
            if os.name != 'nt':
                trb = info_from_error(error)
                error = trb
            print(error)
            show_info(error)
        except:
            pass
    finally:
        try:
            show_progress(task.language('import_deleteing_files'))
            delete_tmp_files(dir)
        except:
            pass
        try:
            os.remove(file_name)
        except:
            pass
        task.app.under_maintenance = False
    return success, error, task.__import_message

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
        result = sorted(result, key=itemgetter(0, 1, 2))
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

def update_events_code(task):

    def process_events(code, js_funcs, ID, path):
        script = ''
        if code:
            script += '\nfunction Events%s() { // %s \n\n' % (ID, path)
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

    def get_js_file_name(js_path):
        return js_path + '.js'

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
        js_filename = get_js_file_name(js_path)
        file_name = os.path.join(to_unicode(os.getcwd(), 'utf-8'), 'js', js_filename)
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
            code = code.strip()
            if code:
                script = process_events(code, js_funcs, it.id.value, js_path)
                external = get_external(it)
                if single_file and not external:
                    script_common += script
                else:
                    script = script_start + script + script_end
                    cur_js_filename = js_filename
                    file_write(file_name, script)
                    if common.SETTINGS['COMPRESSED_JS']:
                        minify(file_name)
            js_filenames[it.id.value] = cur_js_filename
    if single_file:
        it.first()
        js_file_name = get_js_file_name(it.f_item_name.value)
        js_filenames[it.id.value] = js_file_name
        script = script_start + script_common + script_end
        file_name = os.path.join(to_unicode(os.getcwd(), 'utf-8'), 'js', js_file_name)
        file_write(file_name, script)
        if common.SETTINGS['COMPRESSED_JS']:
            minify(file_name)
    sql = []
    for key, value in iteritems(js_filenames):
        sql.append("UPDATE %s SET F_JS_FILENAME = '%s' WHERE ID = %s" % (it.table_name, value, key))
    it.task.execute(sql)
    if it.task.app.task:
        it.task.app.task.all(update_task)
    try:
        from utils.js_code import update_js
        update_js(task)
    except:
        pass

def get_minified_name(file_name):
    result = file_name
    head, tail = os.path.split(file_name)
    name, ext = os.path.splitext(tail)
    if (ext in ['.js', '.css']):
        result = os.path.join(head, '%s.min%s' % (name, ext))
    return result

def minify(file_name):
    min_file_name = get_minified_name(file_name)
    from jam.third_party.jsmin import jsmin
    text = file_read(file_name)
    file_write(min_file_name, jsmin(text))

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

def server_get_task_dict(task):

    def get_children(items, id_value, type_id, dict, key, parent_id, item_fields):
        childs = {}
        if type_id in (common.TASK_TYPE, common.ITEMS_TYPE,
            common.TABLES_TYPE, common.REPORTS_TYPE):
            for it in items:
                if it.parent.value == id_value:
                    clone = items.clone()
                    get_children(clone, it.id.value, it.type_id.value, childs, it.f_item_name.value, it.parent.value, item_fields)
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
            item_fields[id_value] = childs
        dict[key] = childs

    it = task.sys_items.copy(handlers=False)
    it.set_where(type_id=common.TASK_TYPE)
    it.open()
    task_id = it.id.value

    result = {}
    f_dict = {}
    items = task.sys_items.copy(handlers=False)
    items.details_active = False
    items.open(fields=['id', 'type_id', 'parent', 'f_item_name'])

    fields = task.sys_fields.copy(handlers=False)
    fields.open(fields=['owner_rec_id', 'f_field_name'])
    for f in fields:
        if f.f_field_name.value.lower() != 'deleted':
            d = f_dict.get(f.owner_rec_id.value, [])
            if not d:
                f_dict[f.owner_rec_id.value] = d
            d.append(f.f_field_name.value)

    params = task.sys_report_params.copy(handlers=False)
    params.open(fields=['owner_rec_id', 'f_param_name'])
    for f in params:
        d = f_dict.get(f.owner_rec_id.value, [])
        if not d:
            f_dict[f.owner_rec_id.value] = d
        d.append(f.f_param_name.value)

    item_fields = {}
    get_children(items, task_id, common.TASK_TYPE, result, 'task', None, item_fields)
    return result['task'], item_fields

def server_item_info(task, item_id, is_server):
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
    tag = item_name.replace('.', '-')
    if is_server:
        code = items.f_server_module.value
        ext = 'py'
        doc_type = 'server'
        tag = tag + '-server'
    else:
        code = items.f_web_client_module.value
        ext = 'js'
        doc_type = 'client'
        tag = tag + '-client'
    if not code:
        code = ''
    result['fields'] = get_field_dict(task, item_id, parent_id, type_id, table_id)
    result['task'] = {} #server_get_task_dict(task)
    result['events'] = get_events(type_id, is_server)
    result['module'] = common.get_funcs_info(code, is_server)
    result['name'] = '%s.%s' % (item_name, ext)
    result['ext'] = ext
    result['doc'] = code
    result['doc_type'] = doc_type
    result['rec_id'] = item_id
    result['type'] = doc_type
    result['tag'] = tag
    return result

def parse_js(code):
    script = ''
    ast = parseScript(to_unicode(code, 'utf-8'))
    for e in ast.body:
        if isinstance(e, nodes.FunctionDeclaration):
            script += '\tthis.%s = %s;\n' % (e.id.name, e.id.name)
    if script:
        script = '\n' + script
    return script

def server_save_edit(task, item_id, text, is_server):
    code = text
    text = to_bytes(text, 'utf-8')
    line = None
    error = ''
    module_info = None
    module_type = common.WEB_CLIENT_MODULE
    if is_server:
        module_type = common.SERVER_MODULE
    if is_server:
        try:
            compile(text, 'check_item_code', "exec")
        except Exception as e:
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
                error = str(e).replace('check_item_code, ', '')
                traceback.print_exc()
    else:
        try:
            js_funcs = parse_js(text)
        except Exception as e:
            try:
                err_str = e.args[0]
                line, err = err_str.split(':')
                try:
                    line = int(line[5:])
                except:
                    pass
                error = err_str
            except:
                error = error_message(e)
                traceback.print_exc()
    if not error:
        try:
            item = task.sys_items.copy()
            item.set_where(id=item_id)
            item.open(fields=['id', 'f_server_module', 'f_web_client_module', 'f_js_funcs'])
            if item.record_count() == 1:
                item.edit()
                if is_server:
                    item.f_server_module.value = code
                else:
                    item.f_web_client_module.value = code
                    item.f_js_funcs.value = js_funcs
                item.post()
                item.apply()
                module_info = common.get_funcs_info(code, is_server)
            else:
                error = task.language('item_with_id_not found') % item_id
        except Exception as e:
            traceback.print_exc()
            error = error_message(e)
        if is_server:
            task.app.task_server_modified = True
        else:
            task.app.task_client_modified = True
    return {'error': error, 'line': line, 'module_info': module_info}

def server_file_info(task, file_name):
    result = {}
    file_path = file_name
    ext = 'html'
    if file_name == 'project.css':
        ext = 'css'
        file_path = os.path.join('css', 'project.css')
    if os.path.exists(file_path):
        result['doc'] = file_read(file_path)
    result['name'] = file_name
    result['ext'] = ext
    result['type'] = ''
    result['tag'] = file_name.replace('.', '-')
    return result

def server_save_file(task, file_name, code):
    #~ code = to_bytes(code, 'utf-8')
    result = {}
    error = ''
    if file_name == 'project.css':
        file_name = os.path.join('css', 'project.css')
    file_name = os.path.normpath(file_name)
    try:
        file_write(file_name, code)
    except Exception as e:
        traceback.print_exc()
        error = error_message(e)
    result['error'] = error
    if file_name == 'index.html':
        change_theme(task)
    return result

def server_get_db_options(task, db_type):
    error = ''
    try:
        result = {}
        db_module = db_modules.get_db_module(db_type)
        result['DATABASE'] = db_module.DATABASE
        result['NEED_DATABASE_NAME'] = db_module.NEED_DATABASE_NAME
        result['NEED_LOGIN'] = db_module.NEED_LOGIN
        result['NEED_PASSWORD'] = db_module.NEED_PASSWORD
        result['NEED_ENCODING'] = db_module.NEED_ENCODING
        result['NEED_HOST'] = db_module.NEED_HOST
        result['NEED_PORT'] = db_module.NEED_PORT
        result['CAN_CHANGE_TYPE'] = db_module.CAN_CHANGE_TYPE
        result['CAN_CHANGE_SIZE'] = db_module.CAN_CHANGE_SIZE
        result['NEED_GENERATOR'] = db_module.NEED_GENERATOR
        if hasattr(db_module, 'get_table_info'):
            result['IMPORT_SUPPORT'] = True
        return result, error
    except Exception as e:
        return None, str(e)

def server_get_task_info(task):
    items = task.sys_items.copy()
    items.set_where(type_id=common.TASK_TYPE)
    items.open(fields=['f_item_name', 'f_name'])
    task_name = items.f_item_name.value;
    task_caption = items.f_name.value;
    params = task.sys_params.copy()
    params.open()
    task_version = '%s / %s' % (params.f_version.value, task.app.jam_version)
    tasks = task.sys_tasks.copy()
    tasks.open()
    task_db = tasks.f_alias.value
    return task_name, task_caption, task_version, task_db, task.app.started

def server_can_delete_lookup_list(task, list_id):
    fields = task.sys_fields.copy()
    fields.set_where(f_lookup_values=list_id)
    fields.open()
    used = []
    for f in fields:
        used.append({'field1': task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'), 'field2': f.f_field_name.value})
    if len(used) != 0:
        names = ',<br>'.join([task.language('field_mess') % use for use in used])
        mess = task.language('lookup_list_is_used_in') % names
        return mess

def server_valid_item_name(task, item_id, parent_id, name, type_id):
    result = ''
    items = task.sys_items.copy(handlers=False, details=False)
    if name.upper() in ['SYSTEM', 'HISTORY']:
        items.set_where(id=item_id)
        items.open()
        if items.f_item_name.value.upper() != name.upper():
            result = task.language('reserved_word')
    elif type_id == common.DETAIL_TYPE:
        items.set_where(parent=parent_id)
        items.open()
        for it in items:
            if it.task_id.value and it.id.value != item_id and it.f_item_name.value.upper() == name.upper():
                result = 'There is an item with this name'
                break
    else:
        items = task.sys_items.copy(handlers=False, details=False)
        items.set_where(type_id__ne=common.DETAIL_TYPE)
        items.open()
        for it in items:
            if it.task_id.value and it.id.value != item_id and it.f_item_name.value.upper() == name.upper():
                result = 'There is an item with this name'
                break
    return result

def server_create_task(task):
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    fields = task.sys_fields.copy(handlers=False)
    fields.open()
    for f in fields:
        if f.f_db_field_name.value:
            f.edit()
            f.f_db_field_name.value = db_module.identifier_case(f.f_db_field_name.value)
            f.post()
    fields.apply()
    task.create_task()

def get_lookup_list(task, list_id):
    lists = task.sys_lookup_lists.copy()
    lists.set_where(id=list_id)
    lists.open()
    return json.loads(lists.f_lookup_values_text.value)

def change_theme(task):
    rlist = []
    #~ prefix = '/css/'
    prefix = ''
    theme = common.THEME_FILE[common.SETTINGS['THEME']]
    for t in common.THEME_FILE:
        if t and t != theme:
            rlist.append((t, theme))
    if common.SETTINGS['SMALL_FONT']:
        rlist.append(('jam.css', 'jam12.css'))
    else:
        rlist.append(('jam12.css', 'jam.css'))
    file_name = os.path.join(task.work_dir, 'index.html')
    content = file_read(file_name)
    for r1, r2 in rlist:
        content = content.replace(prefix + r1, prefix + r2)
    file_write(file_name, content)

def do_on_apply_param_changes(item, delta, params):
    task = item.task
    language = common.SETTINGS['LANGUAGE']
    debugging = common.SETTINGS['DEBUGGING']
    safe_mode = common.SETTINGS['SAFE_MODE']
    single_file_js = common.SETTINGS['SINGLE_FILE_JS']
    compressed_js = common.SETTINGS['COMPRESSED_JS']
    theme = common.SETTINGS['THEME']
    small_font = common.SETTINGS['SMALL_FONT']

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
    if language != common.SETTINGS['LANGUAGE']:
        task.set_language(common.SETTINGS['LANGUAGE'])
        init_admin(task)
    if theme != common.SETTINGS['THEME'] or small_font != common.SETTINGS['SMALL_FONT']:
        change_theme(task)

    task.timeout = common.SETTINGS['TIMEOUT']
    task.ignore_change_ip = common.SETTINGS['IGNORE_CHANGE_IP']
    return result

def init_fields_next_id(task):
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT MAX(ID) FROM SYS_FIELDS')
        res = cursor.fetchall()
        max_id = res[0][0]
        if not max_id:
            max_id = 0
        cursor.execute('UPDATE SYS_PARAMS SET F_FIELD_ID_GEN=%s' % max_id)
        con.commit()
    finally:
        con.close()

def get_fields_next_id(task, length=1):
    with task.fields_id_lock:
        params = task.sys_params.copy()
        params.open()
        cur_id = params.f_field_id_gen.value
        params.edit()
        params.f_field_id_gen.value = cur_id + length
        params.post()
        params.apply()
        return cur_id + 1

def server_get_table_names(task):
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    connection = db_module.connect(db_database, db_user, db_password, db_host, db_port, db_encoding, db_server)
    try:
        tables = db_module.get_table_names(connection)
        tables = [t.strip() for t in tables]
        ex_tables = task.select('SELECT F_TABLE_NAME FROM SYS_ITEMS')
        ex_tables = [t[0].upper() for t in ex_tables if t[0]]
        result = [t for t in tables if not t.upper() in ex_tables]
        result.sort()
    except:
        result = []
    finally:
        connection.close()
    return result

def server_import_table(task, table_name):
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    connection = db_module.connect(db_database, db_user, db_password, db_host, db_port, db_encoding, db_server)
    try:
        result = db_module.get_table_info(connection, table_name, db_database)
    finally:
        connection.close()
    return result

def server_get_primary_key_type(task, lookup_item_id):
    items = task.sys_items.copy()
    items.set_where(id=lookup_item_id)
    items.open()
    if items.record_count():
        primary_field_id = items.f_primary_key.value
        fields = task.sys_fields.copy()
        fields.set_where(id=primary_field_id)
        fields.set_fields('id', 'f_field_name', 'f_data_type', 'f_size')
        fields.open()
        if fields.record_count():
            return {'field_id': fields.id.value, 'field_name': fields.f_field_name.value,
            'data_type': fields.f_data_type.value, 'size': fields.f_size.value}
    return None, None

def server_set_literal_case(task, name):
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    return db_module.identifier_case(name)

def get_new_table_name(task, var_name):
    db_type, db_server, db_database, db_user, db_password, db_host, db_port, db_encoding = db_info(task)
    db_module = db_modules.get_db_module(db_type)
    copy = task.sys_items.copy(handlers=False, details=False)
    copy.set_where(type_id=common.TASK_TYPE)
    copy.open();
    if copy.record_count() == 1:
        name = copy.f_item_name.value + '_' + var_name;
        gen_name = ''
        if db_module.NEED_GENERATOR:
            gen_name = name + '_SEQ'
    return [db_module.identifier_case(name), db_module.identifier_case(gen_name)]

def create_system_item(task, field_name):

    def check_item_name(name):
        items = task.sys_items.copy()
        items.open(fields = ['id', 'f_item_name'])
        i = 1
        cur_name = name
        while True:
            if items.locate('f_item_name', cur_name):
                cur_name = name + str(i)
                i += 1
            else:
                break
        return cur_name

    error = ''
    result = ''
    try:
        items = task.sys_items.copy()
        items.set_where(type_id=common.TASK_TYPE)
        items.open(fields = ['id', 'type_id', 'f_item_name'])
        task_id = items.id.value
        task_name = items.f_item_name.value

        items = task.sys_items.copy()
        items.open(open_empty=True, fields = ['id', 'parent', 'task_id', \
            'type_id', 'f_name', 'f_item_name', 'f_table_name', \
            'f_gen_name', 'f_primary_key'])

        sys_group = None
        params = task.sys_params.copy()
        task.sys_params.open(fields=['id', 'f_sys_group', 'f_history_item', 'f_lock_item'])

        sys_group = task.sys_params.f_sys_group.value
        if sys_group:
            items.set_where(id=sys_group)
            items.open(fields = ['id', 'f_name', 'f_item_name'])
            if not items.record_count():
                sys_group = None
        else:
            items.open(open_empty=True)
            items.append()
            items.parent.value = task_id
            items.task_id.value = task_id
            items.type_id.value = common.ITEMS_TYPE
            items.f_name.value = task.language('system_group')
            items.f_item_name.value = check_item_name('system')
            items.f_index.value = '999999'
            items.post()
            items.apply()
            task.sys_params.edit()
            task.sys_params.f_sys_group.value = items.id.value
            task.sys_params.post()
            task.sys_params.apply()
            sys_group = items.id.value
        sys_group_name = items.f_name.value

        if field_name == 'f_history_item':
            name = 'History'
            item_name = check_item_name('history')
            fields = common.HISTORY_FIELDS
            index_fields = common.HISTORY_INDEX_FIELDS
            param_field = 'f_history_item'
            table_name, gen_name = get_new_table_name(task, item_name)
            gen_name = None
            sys_id = 1
        elif field_name == 'f_lock_item':
            name = 'Locks'
            item_name = check_item_name('locks')
            fields = common.LOCKS_FIELDS
            index_fields = common.LOCKS_INDEX_FIELDS
            param_field = 'f_lock_item'
            table_name, gen_name = get_new_table_name(task, item_name)
            sys_id = 2
        items.open(open_empty=True)
        items.append()
        items.parent.value = sys_group
        items.task_id.value = task_id
        items.type_id.value = common.ITEM_TYPE
        items.f_name.value = name
        items.f_item_name.value = item_name
        items.f_table_name.value = table_name
        if gen_name:
            items.f_gen_name.value = gen_name
        items.sys_id.value = sys_id
        items.sys_fields.open()
        for i, f in enumerate(fields):
            field_name, data_type, size = f
            items.sys_fields.append()
            items.sys_fields.id.value = get_fields_next_id(task)
            items.sys_fields.task_id.value = task_id
            items.sys_fields.f_name.value = field_name
            items.sys_fields.f_field_name.value = field_name
            items.sys_fields.f_db_field_name.value = server_set_literal_case(task, field_name)
            items.sys_fields.f_data_type.value = data_type
            items.sys_fields.f_size.value = size
            items.sys_fields.post()
            if field_name == 'id':
                items.f_primary_key.value = items.sys_fields.id.value
        items.post()
        items.on_apply = items_apply_changes
        items.apply(params={'manual_update': False})

        sys_item_name = items.f_name.value

        dest_list = []
        for field_name in index_fields:
            items.sys_fields.locate('f_field_name', field_name)
            dest_list.append([items.sys_fields.id.value, False])
        indexes = task.sys_indices.copy()
        indexes.open(open_empty=True)
        indexes.append()
        indexes.f_index_name.value = task_name.upper() + '_' + items.f_item_name.value.upper() + '_' + 'IDX';
        indexes.task_id.value = task_id
        indexes.owner_rec_id.value = items.id.value
        indexes.f_foreign_index.value = False
        indexes.f_fields_list.value = server_dump_index_fields(indexes, dest_list)
        indexes.post()
        indexes.on_apply = indices_apply_changes
        indexes.apply(params={'manual_update': False})

        task.sys_params.edit()
        task.sys_params.field_by_name(param_field).value = items.id.value
        task.sys_params.post()
        task.sys_params.apply()
    except Exception as e:
        traceback.print_exc()
        error = 'While creating an item the following error was raised: %s' % e
    if not error:
        result = 'The %s item has been created in the %s group. The Application builder will be reloaded.' % \
            (sys_item_name, sys_group_name)
    return result, error

def indexes_get_table_names(indexes):
    ids = []
    for i in indexes:
        ids.append(i.owner_rec_id.value)
    items = indexes.task.sys_items.copy(handlers=False)
    items.set_where(id__in=ids)
    items.open(fields=['id', 'f_table_name'])
    table_names = {}
    for i in items:
        table_names[i.id.value] = i.f_table_name.value
    return table_names

def drop_indexes_sql(task):
    db_type = get_db_type(task)
    db_module = db_modules.get_db_module(db_type)
    indexes = task.sys_indices.copy(handlers=False)
    indexes.open()
    table_names = indexes_get_table_names(indexes)
    sqls = []
    for i in indexes:
        if not (i.f_foreign_index.value and db_module.DATABASE == 'SQLITE'):
            table_name = table_names.get(i.owner_rec_id.value)
            if table_name:
                sqls.append(i.delete_index_sql(db_type, table_name))
    return sqls

def restore_indexes_sql(task):
    db_type = get_db_type(task)
    db_module = db_modules.get_db_module(db_type)
    indexes = task.sys_indices.copy(handlers=False)
    indexes.open()
    table_names = indexes_get_table_names(indexes)
    sqls = []
    for i in indexes:
        if not (i.f_foreign_index.value and db_module.DATABASE == 'SQLITE'):
            table_name = table_names.get(i.owner_rec_id.value)
            if table_name:
                sqls.append(i.create_index_sql(db_type, table_name))
    return sqls

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
            dic['field_name'] = field.f_db_field_name.value
            dic['data_type'] = field.f_data_type.value
            dic['size'] = field.f_size.value
            dic['default_value'] = ''#field.f_default_value.value
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
                        field_info['field_name'] = field.f_db_field_name.value
                        field_info['data_type'] = field.f_data_type.value
                        field_info['size'] = field.f_size.value
                        field_info['default_value'] = ''#field.f_default_value.value
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
                        if type(item._view_list) is list:
                            item._view_list.append([field.id.value, False, False, False])
                        if type(item._edit_list) is list:
                            item._edit_list.append([field.id.value])

        for d in delta.details.sys_fields:
            if d.record_status in [common.RECORD_INSERTED, common.RECORD_DELETED]:
                field_name = d.f_field_name.value
                if fields.locate('f_field_name', field_name):
                    if d.record_status == common.RECORD_INSERTED:
                        if not field_name in system_fields:
                            if type(item._view_list) is list:
                                item._view_list.append([fields.id.value, False, False, False])
                            if type(item._edit_list) is list:
                                item._edit_list.append([fields.id.value])
                    elif d.record_status == common.RECORD_DELETED:
                        if type(item._view_list) is list:
                            item._view_list = delete_id_from_list(item._view_list, fields.id.value)
                        if type(item._edit_list) is list:
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
    item.task.execute('DELETE FROM SYS_PRIVILEGES WHERE ITEM_ID = %s' % item_id)
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

def items_insert_sql(item, delta, manual_update=False, new_fields=None, foreign_fields=None):
    if update_table(delta) and not manual_update:
        if delta.type_id.value in (common.ITEM_TYPE, common.TABLE_TYPE):
            db_type = get_db_type(item.task)
            fields = new_fields
            if not fields:
                fields = get_table_fields(delta, delta.details.sys_fields)
            sql = delta.create_table_sql(db_type, delta.f_table_name.value, \
                fields, delta.f_gen_name.value, foreign_fields=foreign_fields)
            return sql

def items_execute_insert(item, delta, manual_update):
    sql = items_insert_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception(item.task.language('error_creating_table') % (error))
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
            raise Exception(item.task.language('error_modifying_table') % error)
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

def sys_item_deleted_sql(delta):
    result = []
    sys_params = delta.task.sys_params.copy()
    sys_params.open()
    if delta.id.value == sys_params.f_history_item.value:
        result.append('UPDATE SYS_PARAMS SET F_HISTORY_ITEM=NULL')
    if delta.id.value == sys_params.f_lock_item.value:
        result.append('UPDATE SYS_PARAMS SET F_LOCK_ITEM=NULL')
    if delta.id.value == sys_params.f_sys_group.value:
        result.append('UPDATE SYS_PARAMS SET F_SYS_GROUP=NULL')
    return result

def items_execute_delete(item, delta, manual_update):
    sql = items_delete_sql(item, delta, manual_update)
    if sql:
        error = execute(item.task, delta.task_id.value, sql)
        if error:
            raise Exception(item.task.language('error_deleting_table') % (delta.table_name.upper(), error))
    commands = []
    sql = delta.apply_sql()
    commands.append(sql)
    for it in (item.task.sys_filters, item.task.sys_indices, item.task.sys_report_params):
        commands.append('DELETE FROM %s WHERE OWNER_REC_ID = %s' % (it.table_name.upper(), delta.id.value))
    commands = commands + sys_item_deleted_sql(delta)
    result = item.task.execute(commands)
    return result

def items_apply_changes(item, delta, params):
    manual_update = params['manual_update']
    for f in delta.sys_fields:
        if not f.id.value:
            raise Exception(item.task.language('field_no_id') % (f.field_name))
    if delta.rec_inserted():
        result = items_execute_insert(item, delta, manual_update)
    elif delta.rec_modified():
        result = items_execute_update(item, delta, manual_update)
    elif delta.rec_deleted():
        result = items_execute_delete(item, delta, manual_update)
    item.task.app.task_server_modified = True
    roles_changed(item)
    return result

def do_on_apply_changes(item, delta, params):
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
        used.append({'item1': item.task.sys_items.field_by_id(d.parent.value, 'f_item_name'), 'item2': d.f_item_name.value})
    if len(used) != 0:
        names = ',<br>'.join(['<b>%(item1)s</b> - <b>%(item2)s</b>' % use for use in used])
        mess = item.task.language('item_used_in_items') % {'item': item.f_item_name.value, 'items': names}
        return mess

    fields = item.task.sys_fields.copy()
    fields.open()
    used = []
    for f in fields:
        if f.f_object.value == id_value:
            used.append({'field1': item.task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'), 'field2': f.f_field_name.value})
    if len(used) != 0:
        names = ',<br>'.join(['<b>%(field1)s</b> - <b>%(field2)s</b>' % use for use in used])
        mess = item.task.language('item_used_in_fields') % {'item': item.f_item_name.value, 'fields': names}
        return mess

    params = item.task.sys_report_params.copy()
    params.open()
    used = []
    for p in params:
        if p.f_object.value == id_value:
             used.append({'param1': item.task.sys_items.field_by_id(p.owner_rec_id.value, 'f_item_name'), 'param2': p.f_param_name.value})
    if len(used) != 0:
        names = ',<br>'.join(['<b>%(param1)s</b> - <b>%(param2)s</b>' % use for use in used])
        mess = item.task.language('item_used_in_params') % {'item': item.f_item_name.value, 'params': names}
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

def create_detail_index(task, table_id):
    items = task.sys_items.copy()
    items.set_where(type_id=common.TASK_TYPE)
    items.open(fields = ['id', 'type_id', 'f_item_name'])
    task_id = items.id.value
    task_name = items.f_item_name.value

    tables = task.sys_items.copy(handlers=False)
    tables.set_where(id=table_id)
    tables.open()

    if not tables.f_master_id.value:
        return

    found = False
    indexes = task.sys_indices.copy(handlers=False)
    indexes.set_where(owner_rec_id=table_id)
    indexes.open()
    for i in indexes:
        if not i.f_foreign_index.value:
            field_list = common.load_index_fields(i.f_fields_list.value)
            if len(field_list) >= 2 and \
                field_list[0][0] == tables.f_master_id.value and \
                field_list[1][0] == tables.f_master_rec_id.value:
                found = True
    if not found:
        dest_list = [[tables.f_master_id.value, False], [tables.f_master_rec_id.value, False]]
        indexes.append()
        index_name = task_name.upper() + '_' + tables.f_item_name.value.upper()
        if len(index_name) > 20:
            index_name = index_name[0:20]
        indexes.f_index_name.value = index_name + '_DETAIL_' + 'IDX';
        indexes.task_id.value = task_id
        indexes.owner_rec_id.value = table_id
        indexes.f_foreign_index.value = False
        indexes.f_fields_list.value = server_dump_index_fields(indexes, dest_list)
        indexes.post()
        indexes.on_apply = indices_apply_changes
        indexes.apply(params={'manual_update': False})

def server_update_details(item, item_id, dest_list):

    def get_table_info(table_id):
        items = item.copy()
        items.set_where(id=table_id)
        items.open()
        return items.f_name.value, items.f_item_name.value, items.f_table_name.value

    def convert_details(i_list, attr, detail_list):
        try:
            for media, options in iteritems(i_list):
                try:
                    new = []
                    details = options[1].get(attr)
                    if details:
                        for d in detail_list:
                            if d in details:
                                new.append(d)
                        options[1][attr] = new
                except:
                    pass
        except:
            pass
        return i_list

    detail_list = [d[0] for d in dest_list]

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
    items.apply()

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
        init_priviliges(items, items.id.value)
        try:
            create_detail_index(items.task, table_id)
        except Exception as e:
            traceback.print_exc()
    item.task.app.task_server_modified = True

    items.set_order_by(['f_index'])
    items.set_where(parent=item_id)
    items.open()
    for it in items:
        cur_row = [i for i, row in enumerate(detail_list) if row == items.table_id.value]
        if len(cur_row) == 1:
            it.edit()
            it.f_index.value = cur_row[0]
            it.post()
    items.apply()

    items.set_order_by(['f_index'])
    items.set_where(parent=item_id)
    items.open()
    detail_list = []
    for it in items:
        detail_list.append(it.id.value)

    common.load_interface(item)
    item._view_list = convert_details(item._view_list, 'view_detail', detail_list)
    item._edit_list = convert_details(item._edit_list, 'edit_details', detail_list)
    common.store_interface(item)

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
        names = ',<br>'.join(['<p>%s - %s</p>' % use for use in used])
        mess = item.task.language('field_used_in_fields') % \
            {'field': item.f_field_name.value, 'fields': names}
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
            field_list = common.load_index_fields(ind.f_fields_list.value)
            for fld in field_list:
                if fld[0] == field_id:
                    ind_list.append(ind.f_index_name.value)
    if len(ind_list):
        names = ',<br>'.join(ind_list)
        mess = item.task.language('field_used_in_indices') % \
            {'field': item.f_field_name.value, 'indexes': names}
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
        mess = item.task.language('field_used_in_filters') % \
            {'field': item.f_field_name.value, 'filters': names}
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
            raise Exception(item.task.language('error_creating_index') % (delta.f_index_name.value.upper(), error))
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
            raise Exception(item.task.language('error_deleting_index') % error)
    sql = delta.apply_sql()
    return item.task.execute(sql)

def indices_apply_changes(item, delta, params):
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

def users_on_apply(item, delta, params):
    for d in delta:
        d.edit()
        d.f_psw_hash.value = hashlib.md5(d.f_password.value.encode("utf8")).hexdigest()
        #~ d.f_psw_hash.value = hashlib.md5(d.f_password.value).hexdigest()
        d.post()

def privileges_table_get_select(item, query):
    owner_id = query['__master_id']
    owner_rec_id = query['__master_rec_id']
    result_sql =  \
        """
        SELECT P.ID, P.DELETED, P.OWNER_ID,
        P.OWNER_REC_ID,
        I.ID,
        O.F_NAME,
        P.F_CAN_VIEW,
        P.F_CAN_CREATE,
        P.F_CAN_EDIT,
        P.F_CAN_DELETE,
        I.F_NAME AS ITEM_ID_LOOKUP
        FROM (SYS_ITEMS AS I
            LEFT JOIN SYS_ITEMS AS O ON O.ID = I.PARENT
            LEFT JOIN SYS_PRIVILEGES AS P ON P.ITEM_ID = I.ID AND P.DELETED = 0 and P.OWNER_ID = %s AND P.OWNER_REC_ID = %s)
        WHERE I.DELETED = 0 AND I.TYPE_ID >= 10
        ORDER BY O.F_NAME
        """
    result_sql = result_sql % (owner_id, owner_rec_id)

    error_mes = ''
    try:
        rows = item.task.select(result_sql)
    except Exception as e:
        error_mes = error_message(e)
    return rows, error_mes

def roles_changed(item):
    item.task.app.privileges = None

def privileges_open(item, params):
    item_id = params['item_id']
    result_sql =  \
    """
    SELECT p.ID,
    p.DELETED,
    %s AS OWNER_ID,
    r.ID AS OWNER_REC_ID,
    %s AS ITEM_ID,
    "" AS OWNER_ITEM,
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
        rows = item.task.select(result_sql)
    except Exception as e:
        error_mes = error_message(e)
    return rows, error_mes


###############################################################################
#                                  sys_langs                                  #
###############################################################################

def add_lang(item, lang_id, language, country, name, abr, rtl, copy_lang):
    langs.add_lang(item.task, lang_id, language, country, name, abr, rtl, copy_lang)

def save_lang_field(item, lang_id, field_name, value):
    langs.save_lang_field(item.task, lang_id, field_name, value)

def get_lang_translation(item, lang1, lang2):
    return langs.get_lang_translation(item.task, lang1, lang2)

def save_lang_translation(item, lang_id, key_id, value):
    langs.save_lang_translation(item.task, lang_id, key_id, value)

def add_key(item, key):
    return langs.add_key(item.task, key)

def del_key(item, key_id):
    return langs.del_key(item.task, key_id)

def export_lang(item, lang_id, host):
    return langs.export_lang(item.task, lang_id, host)

def import_lang(item, file_path):
    return langs.import_lang(item.task, os.path.join(item.task.work_dir, file_path))

def register_events(task):
    task.register(server_check_connection)
    task.register(server_set_task_name)
    task.register(server_set_project_langage)
    # ~ task.register(server_change_secret_key)
    task.register(server_update_has_children)
    task.register(server_export_task)
    task.register(server_import_task)
    task.register(server_find_in_task)
    task.register(server_web_print_code)
    task.register(server_item_info)
    task.register(server_get_task_dict)
    task.register(server_save_edit)
    task.register(server_file_info)
    task.register(server_save_file)
    task.register(get_fields_next_id)
    task.register(get_lookup_list)
    task.register(server_get_db_options)
    task.register(server_create_task)
    task.register(server_get_table_names)
    task.register(server_import_table)
    task.register(server_get_task_info)
    task.register(server_can_delete_lookup_list)
    task.register(server_valid_item_name)
    task.register(server_get_primary_key_type)
    task.register(server_set_literal_case)
    task.register(get_new_table_name)
    task.register(create_system_item)
    task.register(create_detail_index)
    task.sys_params.on_apply = do_on_apply_param_changes
    task.sys_users.on_apply = users_on_apply
    task.sys_tasks.on_apply = do_on_apply_param_changes
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
    task.sys_langs.register(get_lang_translation)
    task.sys_langs.register(save_lang_field)
    task.sys_langs.register(save_lang_translation)
    task.sys_langs.register(add_lang)
    task.sys_langs.register(add_key)
    task.sys_langs.register(del_key)
    task.sys_langs.register(export_lang)
    task.sys_langs.register(import_lang)

