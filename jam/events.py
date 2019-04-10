import jam.common as common

# Client events

task_client_events = \
    {
        'on_page_loaded': 'task',
        'on_view_form_created': 'item',
        'on_edit_form_created': 'item',
        'on_filter_form_created': 'item',
        'on_param_form_created': 'report',
        'on_view_form_shown': 'item',
        'on_edit_form_shown': 'item',
        'on_filter_form_shown': 'item',
        'on_param_form_shown': 'report',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_filter_form_close_query': 'item',
        'on_param_form_close_query': 'report',
        'on_view_form_closed': 'item',
        'on_edit_form_closed': 'item',
        'on_filter_form_closed': 'item',
        'on_param_form_closed': 'report',
        'on_view_form_keyup': 'item, event',
        'on_view_form_keydown': 'item, event',
        'on_edit_form_keyup': 'item, event',
        'on_edit_form_keydown': 'item, event',
        'on_before_print_report': 'report'
    }

group_client_events = \
    {
        'on_view_form_created': 'item',
        'on_edit_form_created': 'item',
        'on_filter_form_created': 'item',
        'on_view_form_shown': 'item',
        'on_edit_form_shown': 'item',
        'on_filter_form_shown': 'item',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_filter_form_close_query': 'item',
        'on_view_form_closed': 'item',
        'on_edit_form_closed': 'item',
        'on_filter_form_closed': 'item',
        'on_param_form_closed': 'report',
        'on_view_form_keyup': 'item, event',
        'on_view_form_keydown': 'item, event',
        'on_edit_form_keyup': 'item, event',
        'on_edit_form_keydown': 'item, event'
    }

reports_client_events = \
    {
        'on_param_form_created': 'report',
        'on_param_form_shown': 'report',
        'on_param_form_close_query': 'report',
        'on_param_form_closed': 'report',
        'on_open_report': 'report, url',
        'on_before_print_report': 'report'
    }

detail_client_events = \
    {
        'on_view_form_created': 'item',
        'on_edit_form_created': 'item',
        'on_filter_form_created': 'item',
        'on_view_form_shown': 'item',
        'on_edit_form_shown': 'item',
        'on_filter_form_shown': 'item',
        'on_view_form_close_query': 'item',
        'on_edit_form_close_query': 'item',
        'on_filter_form_close_query': 'item',
        'on_view_form_closed': 'item',
        'on_edit_form_closed': 'item',
        'on_filter_form_closed': 'item',
        'on_view_form_keyup': 'item, event',
        'on_view_form_keydown': 'item, event',
        'on_edit_form_keyup': 'item, event',
        'on_edit_form_keydown': 'item, event',
        'on_before_append': 'item',
        'on_after_append': 'item',
        'on_before_edit': 'item',
        'on_after_edit': 'item',
        'on_before_delete': 'item',
        'on_after_delete': 'item',
        'on_before_cancel': 'item',
        'on_after_cancel': 'item',
        'on_before_open': 'item, params',
        'on_after_open': 'item',
        'on_before_post': 'item',
        'on_after_post': 'item',
        'on_before_scroll': 'item',
        'on_after_scroll': 'item',
        'on_filter_record': 'item',
        'on_field_changed': 'field, lookup_item',
        'on_field_select_value': 'field, lookup_item',
        'on_before_field_changed': 'field',
        'on_filters_apply': 'item',
        'on_filters_applied': 'item',
        'on_filter_changed': 'filter',
        'on_filter_select_value': 'field, lookup_item',
        'on_field_validate': 'field',
        'on_field_get_text': 'field',
        'on_field_get_html': 'field'
    }

item_client_events = detail_client_events
item_client_events['on_before_apply'] = 'item, params'
item_client_events['on_after_apply'] = 'item'
item_client_events['on_detail_changed'] = 'item, detail'

report_client_events = \
    {
        'on_param_form_created': 'report',
        'on_param_form_shown': 'report',
        'on_param_form_close_query': 'report',
        'on_before_print_report': 'report',
        'on_open_report': 'report, url',
        'on_param_select_value': 'param, lookup_item'
    }

# Server events

task_server_events = \
    {
        'on_created': 'task',
        'on_login': 'task, form_data, info',
        'on_open': 'item, params',
        'on_apply': 'item, delta, params, connection',
        'on_ext_request': 'task, request, params'
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
        'on_open': 'item, params'
    }

item_server_events = detail_server_events
item_server_events['on_apply'] = 'item, delta, params, connection'

report_server_events = \
    {
        'on_before_generate': 'report',
        'on_generate': 'report',
        'on_after_generate': 'report',
        'on_parsed': 'report'
    }

def get_events(item_type_id, server):
    if server:
        if item_type_id == common.TASK_TYPE:
            return task_server_events
        elif item_type_id in [common.ITEMS_TYPE, common.TABLES_TYPE]:
            return group_server_events
        elif item_type_id == common.REPORTS_TYPE:
            return reports_server_events
        elif item_type_id in [common.ITEM_TYPE, common.TABLE_TYPE, common.DETAIL_TYPE]:
            return item_server_events
        elif item_type_id == common.REPORT_TYPE:
            return report_server_events
        elif item_type_id == common.DETAIL_TYPE:
            return detail_server_events
    else:
        if item_type_id == common.TASK_TYPE:
            return task_client_events
        elif item_type_id in [common.ITEMS_TYPE, common.TABLES_TYPE]:
            return group_client_events
        elif item_type_id == common.REPORTS_TYPE:
            return reports_client_events
        elif item_type_id in [common.ITEM_TYPE, common.TABLE_TYPE, common.DETAIL_TYPE]:
            return item_client_events
        elif item_type_id == common.REPORT_TYPE:
            return report_client_events
        elif item_type_id == common.DETAIL_TYPE:
            return detail_client_events


