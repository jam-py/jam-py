# -*- coding:utf-8 -*-

import common

# Client events

task_client_events = \
    {
        'on_before_show_main_form': 'task',
        'on_before_show_view_form': 'item',
        'on_before_show_edit_form': 'item',
        'on_before_show_filter_form': 'item',
        'on_before_show_params_form': 'item',
        'on_after_show_view_form': 'item',
        'on_after_show_edit_form': 'item',
        'on_after_show_filter_form': 'item',
        'on_after_show_params_form': 'item',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_params_form_close_query': 'report',
        'on_view_keypressed': 'item, event',
        'on_edit_keypressed': 'item, event'
    }

group_client_events = \
    {
        'on_before_show_view_form': 'item',
        'on_before_show_edit_form': 'item',
        'on_before_show_filter_form': 'item',
        'on_after_show_view_form': 'item',
        'on_after_show_edit_form': 'item',
        'on_after_show_filter_form': 'item',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_view_keypressed': 'item, event',
        'on_edit_keypressed': 'item, event'
    }

reports_client_events = \
    {
        'on_before_show_params_form': 'report',
        'on_after_show_params_form': 'report',
        'on_params_form_close_query': 'report',
        'on_before_print_report': 'report'
    }

detail_client_events = \
    {
        'on_before_show_view_form': 'item',
        'on_before_show_edit_form': 'item',
        'on_before_show_filter_form': 'item',
        'on_after_show_view_form': 'item',
        'on_after_show_edit_form': 'item',
        'on_after_show_filter_form': 'item',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_view_keypressed': 'item, event',
        'on_edit_keypressed': 'item, event',
        'on_before_append': 'item',
        'on_after_append': 'item',
        'on_before_edit': 'item',
        'on_after_edit': 'item',
        'on_before_delete': 'item',
        'on_after_delete': 'item',
        'on_before_cancel': 'item',
        'on_after_cancel': 'item',
        'on_before_open': 'item',
        'on_after_open': 'item',
        'on_before_post': 'item',
        'on_after_post': 'item',
        'on_before_scroll': 'item',
        'on_after_scroll': 'item',
        'on_filter_record': 'item',
        'on_field_changed': 'field, lookup_item',
        'on_before_field_changed': 'field, new_value, new_lookup_value',
        'on_filter_changed': 'filter',
        'on_field_validate': 'field',
#        'on_get_field_value_list': 'field',
        'on_get_field_text': 'field',
        'on_field_lookup_item_show': 'field, lookup_item',
        'on_filter_lookup_item_show': 'filter, lookup_item'
    }

item_client_events = detail_client_events
item_client_events['on_before_apply'] = 'item'
item_client_events['on_after_apply'] = 'item'

report_client_events = \
    {
        'on_before_show_params_form': 'report',
        'on_after_show_params_form': 'report',
        'on_params_form_close_query': 'report',
        'on_before_print_report': 'report',
        'on_param_lookup_item_show': 'param, lookup_item'
    }

# Server events

task_server_events = \
    {
        'on_created': 'task',
        'on_login': 'task, env, admin, login, password_hash',
        'on_get_user_info': 'task, user_uuid, env',
        'on_logout': 'task, user_uuid, env'
    }

group_server_events = \
    {
    }

reports_server_events = \
    {
        'on_convert_report': 'report'
    }

detail_server_events = \
    {
        'on_select': 'item, params, user_info, enviroment',
        'on_record_count': 'item, params, user_info, enviroment',
        'on_get_field_text': 'field'

    }

item_server_events = detail_server_events
item_server_events['on_apply'] = 'item, delta, params, privileges, user_info, enviroment'

report_server_events = \
    {
        'on_before_generate_report': 'report',
        'on_generate_report': 'report',
        'on_report_generated': 'report',
        'on_before_save_report': 'report'
    }

def get_events(item_type_id, server):
    if server:
        if item_type_id == common.TASK_TYPE:
            return task_server_events
        elif item_type_id in [common.CATALOGS_TYPE, common.JOURNALS_TYPE, common.TABLES_TYPE]:
            return group_server_events
        elif item_type_id == common.REPORTS_TYPE:
            return reports_server_events
        elif item_type_id in [common.CATALOG_TYPE, common.JOURNAL_TYPE, common.TABLE_TYPE, common.DETAIL_TYPE]:
            return item_server_events
        elif item_type_id == common.REPORT_TYPE:
            return report_server_events
        elif item_type_id == common.DETAIL_TYPE:
            return detail_server_events
    else:
        if item_type_id == common.TASK_TYPE:
            return task_client_events
        elif item_type_id in [common.CATALOGS_TYPE, common.JOURNALS_TYPE, common.TABLES_TYPE]:
            return group_client_events
        elif item_type_id == common.REPORTS_TYPE:
            return reports_client_events
        elif item_type_id in [common.CATALOG_TYPE, common.JOURNAL_TYPE, common.TABLE_TYPE, common.DETAIL_TYPE]:
            return item_client_events
        elif item_type_id == common.REPORT_TYPE:
            return report_client_events
        elif item_type_id == common.DETAIL_TYPE:
            return detail_client_events


