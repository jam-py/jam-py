import  os
import json
import shutil

from ..common import consts, ProjectError, ProjectNotCompleted
from ..items import DBInfo, Task, Group, ReportGroup
from ..db.databases import get_database

def create_task(app):
    result = None
    adm = app.admin
    it = adm.sys_items.copy()
    it.set_where(type_id=consts.TASK_TYPE)
    it.open()
    if adm.task_db_type:
        result = Task(app, it.f_item_name.value, it.f_name.value)
        result.ID = it.id.value
        load_task(result, app)
    else:
        raise ProjectNotCompleted()
    return result

def reload_task(app):
    if app.task:
        if app.task.pool is None:
            app.task.create_pool()
        load_task(app.task, app, first_build=False)

def create_fields(item, owner_id, item_dict):
    fields = item_dict['sys_fields']['item']
    fields_dict = item_dict['sys_fields']['rec_dict']
    recs = fields_dict.get(owner_id)
    if recs:
        for r in recs:
            fields.rec_no = r
            if fields.owner_rec_id.value == owner_id:
                field = item.add_field(fields.id.value,
                    fields.f_field_name.value,
                    fields.f_name.value,
                    fields.f_data_type.value,
                    size=fields.f_size.value,
                    required=fields.f_required.value,
                    lookup_item=fields.f_object.value,
                    lookup_field=fields.f_object_field.value,
                    read_only=fields.f_read_only.value,
                    default=fields.f_default.value,
                    default_value=fields.f_default_value.data,
                    master_field=fields.f_master_field.value,
                    alignment=fields.f_alignment.value,
                    lookup_values=fields.f_lookup_values.value,
                    enable_typeahead=fields.f_enable_typehead.value,
                    field_help=fields.f_help.value,
                    field_placeholder=fields.f_placeholder.value,
                    lookup_field1=fields.f_object_field1.value,
                    lookup_field2=fields.f_object_field2.value,
                    db_field_name=fields.f_db_field_name.value,
                    field_mask=fields.f_mask.value,
                    image_edit_width=fields.f_image_edit_width.value,
                    image_edit_height=fields.f_image_edit_height.value,
                    image_view_width=fields.f_image_view_width.value,
                    image_view_height=fields.f_image_view_height.value,
                    image_placeholder=fields.f_image_placeholder.value,
                    image_camera=fields.f_image_camera.value,
                    file_download_btn=fields.f_file_download_btn.value,
                    file_open_btn=fields.f_file_open_btn.value,
                    file_accept=fields.f_file_accept.value,
                    calc_item =fields.f_calc_item.value,
                    calc_lookup_field =fields.f_calc_lookup_field.value,
                    calc_field =fields.f_calc_field.value,
                    calc_op =fields.f_calc_op.display_text,
                    textarea = fields.f_textarea.value,
                    do_not_sanitize = fields.f_do_not_sanitize.value
                )

def create_filters(item, owner_id, item_dict):
    filters = item_dict['sys_filters']['item']
    filters_dict = item_dict['sys_filters']['rec_dict']
    recs = filters_dict.get(owner_id)
    if recs:
        for r in recs:
            filters.rec_no = r
            if filters.owner_rec_id.value == owner_id:
                item.add_filter(
                    filters.f_filter_name.value,
                    filters.f_name.value,
                    filters.f_field.value,
                    filters.f_type.value,
                    filters.f_multi_select_all.value,
                    filters.f_data_type.value,
                    filters.f_visible.value,
                    filters.f_help.value,
                    filters.f_placeholder.value,
                    filters.id.value,
                )

def create_params(item, owner_id, item_dict):
    params = item_dict['sys_report_params']['item']
    params_dict = item_dict['sys_report_params']['rec_dict']
    recs = params_dict.get(owner_id)
    if recs:
        for r in recs:
            params.rec_no = r
            if params.owner_rec_id.value == owner_id:
                item.add_param(
                    params.f_name.value,
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

def create_items(group, item_dict):
    items = item_dict['sys_items']['item']
    items_dict = item_dict['sys_items']['rec_dict']
    recs = items_dict.get(group.ID)
    if recs:
        for r in recs:
            items.rec_no = r
            if group.item_type_id == consts.REPORTS_TYPE:
                add_item = group.add_report
            else:
                add_item = group.add_item
            item = add_item(items.f_item_name.value, items.f_name.value)
            if item:
                item.ID = items.id.value
                item.item_type_id = items.type_id.value
                item.visible = items.f_visible.value
                item.js_filename = items.f_js_filename.value
                item.server_code = items.f_server_module.value
                if group.item_type_id == consts.REPORTS_TYPE:
                    item.template = items.f_view_template.value
                    item.select_all = items.f_select_all.value
                    create_params(item, items.id.value, item_dict)
                    item.rep_ids = []
                else:
                    item.table_name = items.f_table_name.value
                    item.gen_name = items.f_gen_name.value
                    item.soft_delete = items.f_soft_delete.value
                    item.edit_lock = items.f_edit_lock.value
                    item._virtual_table = items.f_virtual_table.value
                    item.keep_history = items.f_keep_history.value
                    item._primary_key = items.f_primary_key.value
                    item._deleted_flag = items.f_deleted_flag.value
                    item._master_id = items.f_master_id.value
                    item._master_rec_id = items.f_master_rec_id.value
                    item._record_version = items.f_record_version.value
                    item._sys_id = items.sys_id.value
                    item._copy_of = items.f_copy_of.value
                    items.load_interface()
                    item._view_list = items._view_list
                    item._edit_list = items._edit_list
                    create_fields(item, items.id.value, item_dict)
                    item._order_by = items._order_list
                    item.rep_ids = items._reports_list
                    create_filters(item, group.ID, item_dict)
                    create_filters(item, items.id.value, item_dict)

def create_groups(task, item_dict):
    items = item_dict['sys_items']['item']
    groups = []
    for rec in items:
        if rec.id.value == task.ID:
            task.table_name = rec.f_table_name.value
            task.js_filename = rec.f_js_filename.value
            items.load_interface()
            task.server_code = rec.f_server_module.value
        if rec.parent.value == task.ID:
            const_class = Group
            if rec.type_id.value == consts.REPORTS_TYPE:
                const_class = ReportGroup
            group = const_class(
                task,
                task,
                rec.f_item_name.value,
                rec.f_name.value,
            )
            group.ID = rec.id.value
            group.item_type_id = rec.type_id.value
            group.js_filename = rec.f_js_filename.value
            group.visible = rec.f_visible.value
            group.server_code = rec.f_server_module.value
            groups.append(group)
    for group in groups:
         create_items(group, item_dict)

def create_detail(master, prototype, it):
    detail = master.add_detail(prototype, it.f_master_field.value)
    detail.item_name = it.f_item_name.value
    detail.ID = it.id.value
    detail.item_type_id = it.type_id.value
    detail.table_name = it.f_table_name.value
    detail.gen_name = prototype.gen_name
    detail.master_applies = it.f_master_applies.value
    detail.visible = it.f_visible.value
    detail.keep_history = prototype.keep_history
    detail.js_filename = it.f_js_filename.value
    detail.master_field = it.f_master_field.value
    if detail.master_field:
        detail.server_code = prototype.server_code
    else:
        detail.server_code = it.f_server_module.value
    it.load_interface()
    detail._view_list = it._view_list
    detail._edit_list = it._edit_list
    detail._order_by = it._order_list
    return detail

def create_details(task, item_dict):
    items = item_dict['sys_items']['item']
    details = {}
    for it in items:
        if it.table_id.value:
            master = task.item_by_ID(it.parent.value)
            prototype = task.item_by_ID(it.table_id.value)
            if master and prototype:
                detail = create_detail(master, prototype, it)
                details[prototype.ID] = detail

    while True:
        left_details = {}
        for it in items:
            if it.table_id.value:
                detail = details.get(it.parent.value)
                if detail:
                    master = detail
                    prototype = task.item_by_ID(it.table_id.value)
                    detail = create_detail(master, prototype, it)
                    details[prototype.ID] = detail
                    left_details[prototype.ID] = detail
        details = left_details
        if not details:
            break

def add_reports(item):
    item.reports = []
    for rep_id in item.rep_ids:
        report = item.task.item_by_ID(rep_id[0])
        if report:
            item.reports.append(report)

def process_reports(task):
    for group in task.items:
        for item in group.items:
            add_reports(item)

def process_lookup_lists(task, admin):
    lists = admin.sys_lookup_lists.copy()
    lists.open(order_by=['f_name'])
    for l in lists:
        text = l.f_lookup_values_text.value
        task.lookup_lists[l.id.value] = json.loads(l.f_lookup_values_text.value)

def fill_dict(item, parent_field_name):
    result = {}
    parent_field = item.field_by_name(parent_field_name)
    for i in item:
        d = result.get(parent_field.value)
        if d is None:
            d = []
            result[parent_field.value] = d
        d.append(i.rec_no)
    return result

def fill_rec_dicts(admin):
    result = {}
    items = [
        ['sys_items', 'f_index', 'parent'],
        ['sys_fields', 'id', 'owner_rec_id'],
        ['sys_filters', 'f_index', 'owner_rec_id'],
        ['sys_report_params', 'f_index', 'owner_rec_id']
    ]
    for item_name, order_by, parent_field_name in items:
        item = admin.item_by_name(item_name)
        copy = item.copy(handlers=False, details=False)
        copy.open(order_by=[order_by])
        result[item_name] = {}
        result[item_name]['item'] = copy
        result[item_name]['rec_dict'] = fill_dict(copy, parent_field_name)
    return result

def load_tree(admin, task):
    item_dict = fill_rec_dicts(admin)
    create_groups(task, item_dict)
    create_details(task, item_dict)
    process_reports(task)
    process_lookup_lists(task, admin)

def remove_attr(task):
    for key in list(task.__dict__.keys()):
        try:
            value = task.init_dict[key]
            if hasattr(task.__dict__[key], '__call__'):
                task.__dict__[key] = value
        except:
            del task.__dict__[key]

def history_on_apply(item, delta, params):
    raise Exception('Changing of history is not allowed.')

def history_sql(task):
    h_fields = ['item_id', 'item_rec_id', 'operation', 'changes', 'user', 'date']
    table_name = task.task.history_item.table_name
    fields = []
    for f in h_fields:
        fields.append(task.history_item._field_by_name(f).db_field_name)
    h_fields = fields
    index = 0
    fields = []
    values = []
    index = 0
    for f in h_fields:
        index += 1
        fields.append('"%s"' % f)
        values.append('%s' % task.db.value_literal(index))
    fields = ', '.join(fields)
    values = ', '.join(values)
    sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % \
        (table_name, fields, values)
    return sql


def load_task(task, app, first_build=True, after_import=False):
    try:
        admin = app.admin

        remove_attr(task)
        task.items = []
        load_tree(admin, task)

        task.bind_items()
        task.compile_all()

        task.db_type = admin.task_db_type
        task.db_info = admin.task_db_info
        if task.db_type == consts.SQLITE:
            task.db_info.database = os.path.join(app.work_dir, task.db_info.database)
        task.db = get_database(app, task.db_type, task.db_info.lib)

        task.create_pool(admin.task_con_pool_size, admin.task_persist_con)

        params = admin.sys_params.copy()
        params.open(fields=['f_history_item', 'f_lock_item'])
        task.history_item = None
        if params.f_history_item.value:
            task.history_item = task.item_by_ID(params.f_history_item.value)
            task.history_item.on_apply = history_on_apply
            task.history_sql = history_sql(task)
        if params.f_lock_item.value:
            task.lock_item = task.item_by_ID(params.f_lock_item.value)

        task.first_build = first_build
        task.after_import = after_import
        task.safe_mode = consts.SAFE_MODE
        if task.on_created:
            task.on_created(task)

        internal_path = os.path.join(admin.work_dir, 'static', 'internal')
        if os.path.exists(internal_path):
            try:
                shutil.rmtree(internal_path)
            except:
                pass
    except Exception as e:
        task.log.exception(consts.lang['project_error'])
        raise ProjectError()
