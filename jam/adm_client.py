# -*- coding: utf-8 -*-

import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
except:
    print("GTK Not Availible")
    sys.exit(1)

import jam.interface
from jam.dataset import DBField
from jam.client_classes import ClientItem, ClientGroup, ClientTask
from jam.editors import FieldEditor, ItemEditor, ReportEditor, JavascriptEditor
from jam.common import *

###############################################################################
#                                 task events                                 #
###############################################################################

def refresh_tree(select_id=None):

    def filter_tree(item):
        if item.has_children.value:
            return True

    def expand_tasks():
        tasks = task.sys_items.copy()
        tasks.filters.type_id.value = [TASK_TYPE]
        tasks.open()
        for t in tasks:
            path = task.tree.get_path_by_id(t.id.value)
            task.tree.expand_to_path(path)

    task.server_update_has_children()
    task.tree_items.on_filter_record = filter_tree
    task.tree_items.filtered = True
    task.tree_items.details_active = False
    task.tree_items.open()
    task.tree.refresh()
    task.tree.expand_root()
    expand_tasks()


def on_main_form_show(task):

    def init_project(task):
        items = task.sys_items.copy(handlers=False)
        items.open()
        items.locate('type_id', TASK_TYPE)
        items.edit()
        items.f_name.required = False
        items.f_item_name.required = False
        items.f_name.value = None
        items.f_item_name.value = None
        items.post()
        items.f_name.required = True
        items.f_item_name.required = True
        items.set_edit_fields(['f_name', 'f_item_name'])
        items.edit_record(task.main_form.window)

    def show_params(widget):
        task.sys_params.set_edit_fields(['f_safe_mode', 'f_debugging', 'f_log_file', 'f_con_pool_size'])
        task.sys_params.edit_record(widget)

    def show_locale_params(widget):
        fields = ('f_decimal_point', 'f_mon_decimal_point', 'f_mon_thousands_sep', 'f_currency_symbol',
            'f_frac_digits', 'f_p_cs_precedes', 'f_n_cs_precedes', 'f_p_sep_by_space',
            'f_n_sep_by_space', 'f_positive_sign', 'f_negative_sign',
            'f_p_sign_posn', 'f_n_sign_posn', 'f_d_fmt', 'f_d_t_fmt')
        task.sys_params.set_edit_fields(fields)
        task.sys_params.edit_record(widget)

    def export_task(widget):
        import datetime
        data = task.server_export_task(task.sys_tasks.task_id.value)
        file_name = '%s_%s.zip' % (task.task_name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        file_name = jam.interface.save_file(file_name)
        if file_name:
            fh = open(file_name, 'w')
            fh.write(data)
            fh.close()

    def import_task(widget):
        file_name = jam.interface.open_file()
        fh = open(file_name, 'r')
        data = fh.read()
        fh.close()
        error = task.server_import_task(task.sys_tasks.task_id.value, data)
        if error:
            task.warning(error)
        else:
            if task.url:
                task.warning('Successful update. Sever will be stoped. You need to restart server.')
                task.send_request('exit')
                sys.exit()
            else:
                refresh_tree()
                task.warning('Successful update');

    def print_code(widget):
        file_name = task.server_print_code(task.sys_tasks.task_id.value, task.url)
        task.open_file(file_name)

    def edit_database(widget):
        tasks_field_changed(task.sys_tasks.f_db_type, None)
        task.sys_tasks.f_manual_update.edit_visible = True
        task.sys_tasks.edit_record(widget)

    def stop_and_exit(widget):
        task.send_request('exit')
        sys.exit()

    def create_params_btn():

        def add_button(caption, handler):
            btn = gtk.Button(caption)
            btn.connect("clicked", handler)
            btns_box.pack_start(btn, False, False)

        def add_divider():
            label = gtk.Label('')
            btns_box.pack_start(label, False, False)

        hbox = gtk.HBox()
        vbox = gtk.VBox()
        btns_box = gtk.VBox()
        hbox.pack_start(vbox)
        hbox.pack_start(btns_box, False, False)
        add_button(task.lang['project_params'], show_params)
        add_button(task.lang['project_locale'], show_locale_params)
        add_divider()
        add_button(task.lang['db'], edit_database)
        add_divider()
        add_button(task.lang['export'], export_task)
        add_button(task.lang['import'], import_task)
        add_divider()
        add_button(task.lang['print'], print_code)
        if task.url:
            add_divider()
            add_button(task.lang['stop_server'], stop_and_exit)
        task.content.add(hbox)
        task.content.show_all()

    def find_task_name():
        items = task.sys_items.copy()
        items.set_where(type_id=TASK_TYPE)
        items.open()
        task.task_name = items.f_item_name.value
        task.task_caption = items.f_name.value

    def item_selected(cur_id):
        task.selected_node_id = cur_id
        task.selected_node_type_id = items.field_by_id(cur_id, 'type_id')
        if task.selected_node_type_id in (ROOT_TYPE, None):
            container = task.content
            for child in container:
                container.remove(child)
                child.destroy()
            create_params_btn()
        elif task.selected_node_type_id == USERS_TYPE:
            task.sys_users.view(win.window)
        elif task.selected_node_type_id == ROLES_TYPE:
            task.sys_roles.view(win.window)
        else:
            items.filters.parent.value = cur_id
            items.view(win.window)

    task.new_project = False
    task.sys_tasks.open()
    if not task.sys_tasks.f_db_type.value:
        task.new_project = True
        init_project(task)
        return

    task.buttons = [] #Right panel buttons

    win = task.main_form

    rect = win.window.get_allocation()
    screen_width = gtk.gdk.screen_width()
    screen_height = gtk.gdk.screen_height()
    width = rect.width
    height = rect.height
    if width > screen_width:
        width = screen_width
    if height > screen_height - 60:
        height = screen_height - 60
    win.window.resize(width, height)

    body = win.body
    vbox = gtk.VBox()

    hpaned = gtk.HPaned()
    task.hpaned = hpaned

    task.tree_items = task.sys_items.copy()
    task.tree = jam.interface.DBTree(task.tree_items, 'id', 'f_name', 'parent', 0)
    refresh_tree()

    task.content = gtk.Alignment(xscale=1.0, yscale=1.0)
    hpaned.add1(task.tree)
    hpaned.add2(task.content)
    hpaned.set_position(250)

    vbox.pack_start(hpaned, True, True)
    body.add(vbox)
    win.window.show_all()

    find_task_name()

    items = task.sys_items
    items.open()

    item_selected(0)
    task.tree.on_select = item_selected
    task.sys_params.open()
    task.main_form.window.set_title(task.lang['admin'] + ' - ' + task.task_caption)
task.on_before_show_main_form = on_main_form_show

def get_fields_list(item):
    item = item.task.sys_items
    table = item.task.tables.sys_fields
    fields = table.copy()
    if item.table_id.value == 0:
        fields.filters.owner_rec_id.value = [item.id.value, item.parent.value]
    else:
        fields.filters.owner_rec_id.value = [item.table_id.value, item.field_by_id(item.table_id.value, 'parent')]
    fields.open()
    source_list = []
    for f in fields:
        source_list.append((f.id.value, f.f_field_name.value))
    return source_list

def get_reports_list(item):
    items = item.task.sys_items.copy(handlers=False)
    items.filters.type_id.value = [REPORTS_TYPE]
    items.filters.task_id.value = item.task_id.value
    items.open()
    parent = items.id.value
    items.clear_filters()
    items.filters.parent.value = parent
    items.open()
    source_list = []
    for it in items:
        source_list.append((it.id.value, it.f_name.value))
    return source_list


def on_data_show_view_form(item):

    source_def = [{'caption': '', 'type': int},
            {'caption': item.task.lang['caption_name'], 'type': str},
            ]

    view_dest_def = [
            {'caption': '', 'type': int},
            {'caption': item.task.lang['caption_name'], 'type': str, },
            {'caption': item.task.lang['caption_word_wrap'], 'type': bool},
            {'caption': item.task.lang['caption_expand'], 'type': bool},
            {'caption': item.task.lang['caption_edit'], 'type': bool},
            ]

    order_dest_def = [
            {'caption': '', 'type': int},
            {'caption': item.task.lang['caption_name'], 'type': str, },
            {'caption': item.task.lang['caption_descening'], 'type': bool},
            ]

    edit_dest_def = source_def
    tables_dest_def = source_def

    def edit_client_module(widget):
        module_name = item.task.server_get_module_name(item.id.value, CLIENT_MODULE)
        item.edit()
        ItemEditor(widget, item, module_name, task.selected_node_type_id, CLIENT_MODULE)

    def edit_web_client_module(widget):
        module_name = item.task.server_get_module_name(item.id.value, WEB_CLIENT_MODULE)
        item.edit()
        JavascriptEditor(widget, item, task.selected_node_type_id, module_name)

    def edit_server_module(widget):
        module_name = item.task.server_get_module_name(item.id.value, SERVER_MODULE)
        item.edit()
        ItemEditor(widget, item, module_name, task.selected_node_type_id, SERVER_MODULE)

    def edit_report_module(widget):
        if item.f_filter_template.value:
            ReportEditor(widget, item, item.f_filter_template.value)

    def edit_task(widget):
        tasks_field_changed(item.task.sys_tasks.f_db_type, None)
        item.task.sys_tasks.f_manual_update.edit_visible = True
        item.task.sys_tasks.edit_record(widget)

    def view_setup(widget):

        def save_view(dest_list):
            item._view_list = dest_list
            store_interface(item)

        load_interface(item)
        editor = FieldEditor(item, widget, u'%s - %s' % (item.f_name.value, item.task.lang['viewing'].lower()),
            source_def, get_fields_list(item) , view_dest_def, item._view_list, save_view)
        editor.show()

    def edit_setup(widget):

        def save_edit(dest_list):
            item._edit_list = dest_list
            store_interface(item)

        load_interface(item)
        editor = FieldEditor(item, widget, u'%s - %s' % (item.f_name.value, item.task.lang['editing'].lower()),
            source_def, get_fields_list(item), edit_dest_def, item._edit_list, save_edit)
        editor.show()

    def reports_setup(widget):

        def save_reports(dest_list):
            item._reports_list = dest_list
            store_interface(item)

        load_interface(item)
        editor = FieldEditor(item, widget, u'%s - %s' % (item.f_name.value, item.task.lang['reports'].lower()),
            source_def, get_reports_list(item) , edit_dest_def, item._reports_list, save_reports)
        editor.show()

    def filters_setup(widget):
        item.task.sys_filters.filters.owner_rec_id.value = item.id.value
        item.task.sys_filters.open()
        item.task.sys_filters.view(widget)

    def indices_setup(widget):
        item.task.sys_indices.filters.owner_rec_id.value = item.id.value
        item.task.sys_indices.filters.foreign_index.value = False
        item.task.sys_indices.open()
        item.task.sys_indices.view(widget)

    def foreign_keys_setup(widget):
        item.task.sys_indices.filters.owner_rec_id.value = item.id.value
        item.task.sys_indices.filters.foreign_index.value = True
        item.task.sys_indices.open()
        item.task.sys_indices.view(widget)

    def report_params_setup(widget):
        item.task.sys_report_params.filters.owner_rec_id.value = item.id.value
        item.task.sys_report_params.open()
        item.task.sys_report_params.view(widget)

    def order_setup(widget):

        def save_order(dest_list):
            item._order_list = dest_list
            store_interface(item)

        load_interface(item)
        editor = FieldEditor(item, widget, u'%s - %s' % (item.f_name.value, item.task.lang['order'].lower()),
            source_def, get_fields_list(item), order_dest_def, item._order_list, save_order)
        editor.show()

    def tables_setup(widget):

        def save_tables(dest_list):

            def get_table_info(table_id):
                items = item.copy()
                items.filters.id.value = table_id
                items.open()
                return items.f_name.value, items.f_item_name.value, items.f_table_name.value, \
                    items.f_view_template.value, items.f_edit_template.value, items.f_filter_template.value

            items = item.copy(handlers=False)
            items.filters.parent.value = item.id.value
            items.open()
            while not items.eof():
                cur_row = [row for row in dest_list if row[0] == items.table_id.value]
                if len(cur_row) == 1:
                    dest_list.remove(cur_row[0])
                    items.next()
                else:
                    items.delete()

            for row in dest_list:
                table_id = row[0]
                name, obj_name, table_name, view_template, edit_template, filter_template = get_table_info(table_id)
                items.append()
                items.task_id.value = item.task_id.value
                items.type_id.value = DETAIL_TYPE
                items.table_id.value = table_id
                items.parent.value = item.id.value
                items.f_name.value = name
                items.f_item_name.value = obj_name
                items.f_table_name.value = table_name
                items.f_view_template.value = view_template
                items.f_edit_template.value = edit_template
                items.f_filter_template.value = filter_template
                items.f_visible.value = True
                items.f_info.value = ''
                items.post()
                table = item.task.sys_items.copy()
                table.filters.id.value = table_id
                table.open()
                load_interface(table)
                items._view_list = table._view_list
                items._edit_list = table._edit_list
                items._order_list = table._order_list
                items._reports_list = []
                store_interface(items)
            refresh_tree(items.id.value)
            items.apply()

        source_list = []
        tables = item.copy(handlers=False)
        tables.filters.task_id.value = item.task_id.value
        tables.filters.type_id.value = [TABLE_TYPE]
        tables.open()
        for rec in tables:
            source_list.append((rec.id.value, rec.f_item_name.value))
        dest_list = []
        items = item.copy(handlers=False)
        items.filters.parent.value = item.id.value
        items.open()
        for it in items:
            dest_list.append([it.table_id.value])
        editor = FieldEditor(item, widget, u'%s - %s' % (item.f_name.value, item.task.lang['details'].lower()),
            source_def, source_list , tables_dest_def, dest_list, save_tables, can_move=False)
        editor.show()

    def add_button(caption, handler):
        btn = gtk.Button(caption)
        btn.connect("clicked", handler)
        item.view_form.btns_vbox.pack_start(btn, False, False)
        item.task.buttons.append(btn)
        btn.show()

    def add_divider():
        label = gtk.Label('')
        item.view_form.btns_vbox.pack_start(label, False, False)
        label.show()

    def move_item_up(widget):
        grid.move_up()
        items_save_indexes(item, grid)

    def move_item_down(widget):
        grid.move_down()
        items_save_indexes(item, grid)

    def items_save_indexes(item, grid):
        rec = item.rec_no
        for it in item:
            cur_iter = grid.find_rec_iter()
            it.edit()
            it.f_index.value = grid.path_by_iter(cur_iter)
            it.post()
        item.apply()
        item.rec_no = rec

    if item in (item.task.sys_users, item.task.sys_roles, item.task.sys_items):
        container = item.task.content
        for child in container:
            container.remove(child)
            child.destroy()
        body = item.view_form.body
        item.view_form.window.remove(body)
        container.add(body)
        item.view_form.window.destroy()
        item.view_form.window = None

    if item == item.task.sys_items:
        dic = {
            "on_select_button_clicked" : item.set_lookup_field_value,
            "on_edit_button_clicked" : item.edit_record,
            "on_delete_button_clicked" : item.delete_record,
            "on_new_button_clicked" : item.insert_record,
            "on_up_button_clicked": move_item_up,
            "on_down_button_clicked": move_item_down,
            }
        item.view_form.builder.connect_signals(dic)
        item.f_view_template.field_caption = item.task.lang['view_template']
        item.f_edit_template.field_caption = item.task.lang['edit_template']
        if task.selected_node_type_id == TASKS_TYPE:
            grid = jam.interface.DBGrid(item, ['f_name', 'f_item_name', 'f_view_template', 'f_visible'])
        elif task.selected_node_type_id == TASK_TYPE:
            grid = jam.interface.DBGrid(item, ['id', 'f_name', 'f_item_name', 'f_edit_template',
                'f_view_template', 'f_filter_template'])
        elif task.selected_node_type_id == REPORTS_TYPE:
            item.f_view_template.field_caption = item.task.lang['template']
            item.f_edit_template.field_caption = item.task.lang['params_template']
            grid = jam.interface.DBGrid(item, ['id', 'f_name', 'f_item_name',
                'f_view_template', 'f_edit_template', 'f_visible'])
        elif not (task.selected_node_type_id in (USERS_TYPE, ROLES_TYPE)):
            grid = jam.interface.DBGrid(item)
        else:
            grid = jam.interface.DBGrid(item)
        item.view_form.grid_container.add(grid)
        if item.view_form.select_button:
            item.view_form.select_button.set_visible(False)
        grid.show_all()
        parent = item.filters.parent.value
        parent_type_id = item.field_by_id(parent, 'type_id')
        item.view_form.up_down_hbox.set_visible(not parent_type_id in [TASKS_TYPE, TASK_TYPE])
        item.view_form.delete_button.set_visible(not parent_type_id in [TASKS_TYPE, TASK_TYPE])
        item.view_form.new_button.set_visible(not parent_type_id in [TASKS_TYPE, TASK_TYPE])
        item.view_form.edit_button.set_visible(parent_type_id != TASKS_TYPE)
        item.view_form.delete_button.set_label(item.task.lang['delete'])
        item.view_form.new_button.set_label(item.task.lang['new'])
        item.view_form.edit_button.set_label(item.task.lang['edit'])
        item.view_form.select_button.set_label(item.task.lang['select'])
        add_button(task.lang['client_module'], edit_client_module)
        add_button(task.lang['web_client_module'], edit_web_client_module)
        add_button(task.lang['server_module'], edit_server_module)
        add_divider()
        if parent_type_id == TASKS_TYPE:
            pass
            #~ add_button(task.lang['db'], edit_task)
            #~ add_divider()
            #~ add_button(task.lang['print'], print_code)
            #~ add_divider()
            #~ add_button(task.lang['export'], export_task)
            #~ add_button(task.lang['import'], import_task)
        elif parent_type_id == TASK_TYPE:
            pass
        elif parent_type_id == REPORTS_TYPE:
            add_button(task.lang['report_params'], report_params_setup)
        elif parent_type_id in (CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE):
            add_button(task.lang['viewing'], view_setup)
            add_button(task.lang['editing'], edit_setup)
            add_divider()
            add_button(task.lang['order'], order_setup)
        else:
            add_button(task.lang['viewing'], view_setup)
            add_button(task.lang['editing'], edit_setup)
            add_button(task.lang['filters'], filters_setup)
            add_divider()
            add_button(task.lang['details'], tables_setup)
            add_divider()
            add_button(task.lang['order'], order_setup)
            if parent_type_id in (CATALOGS_TYPE, JOURNALS_TYPE, TABLES_TYPE):
                add_button(task.lang['indices'], indices_setup)
                add_button(u'Foreign keys', foreign_keys_setup)
                add_divider()
                add_button(task.lang['reports'], reports_setup)
task.on_before_show_view_form = on_data_show_view_form

def on_task_after_show_view_form(item):
    item.open()
task.on_after_show_view_form = on_task_after_show_view_form

def on_task_after_show_edit_form(item):
    for detail in item.details:
        if item.details_active:
            detail.update_controls(common.UPDATE_OPEN)
        else:
            if not detail.disabled:
                detail.open()
task.on_after_show_edit_form = on_task_after_show_edit_form

def edit_form_close_query(item):
    if item.modified:
        res = item.yes_no_cancel(item.task.lang['save_changes'])
        if res == 1:
            if not item.apply_record():
                return True
        elif res == 0:
            item.cancel_edit()
        else:
            return True
    else:
        item.cancel_edit()
task.on_edit_form_close_query = edit_form_close_query

def create_task(widget, it):
    ts = task.sys_tasks
    if it.f_name.value and it.f_item_name.value and ts.f_db_type.value:
        success, message = task.server_create_task(it.f_name.value,
            it.f_item_name.value, ts.f_db_type.value, ts.f_alias.value,
            ts.f_login.value, ts.f_password.value, ts.f_host.value,
            ts.f_port.value, ts.f_encoding.value)
    else:
        success, message = False, task.lang['fill_task_attrubutes']
    if success:
        if it.apply_record():
            ts.post()
            ts.apply()
            on_main_form_show(task)
    else:
        it.warning(message)

def on_data_show_edit_form(item):
    if item.task.new_project:
        item.edit_form.window.set_title('New project')
        item.on_field_validate = items_validate_name
        item.create_entries(item.edit_form.fields_container, ['f_name', 'f_item_name'],
            sel_from_view_form=False, sel_from_dropdown_box=True)
        item.task.sys_tasks.edit()
        item.task.sys_tasks.create_entries(item.edit_form.tables_container,
            sel_from_view_form=False, sel_from_dropdown_box=True)
        dic = {
            "on_ok_button_clicked" : (create_task, item),
            "on_cancel_button_clicked" : item.cancel_edit
            }
        item.edit_form.builder.connect_signals(dic)
    else:
        dic = {
            "on_ok_button_clicked" : item.apply_record,
            "on_cancel_button_clicked" : item.cancel_edit
            }
        item.edit_form.builder.connect_signals(dic)
        if item == item.task.sys_items:
            if not (item.is_new() or item.task.sys_tasks.f_manual_update.value):
                item.f_table_name.read_only = True
            item.f_view_template.field_caption = item.task.lang['view_template']
            item.f_edit_template.field_caption = item.task.lang['edit_template']
            item.f_filter_template.field_caption = item.task.lang['filter_template']
            if task.selected_node_type_id == TASKS_TYPE:
                item.create_entries(item.edit_form.fields_container, ['f_name', 'f_item_name', 'f_view_template', 'f_visible'],
                    sel_from_view_form=False, sel_from_dropdown_box=True)
            elif task.selected_node_type_id == REPORTS_TYPE:
                item.f_view_template.field_caption = item.task.lang['template']
                item.f_edit_template.field_caption = item.task.lang['params_template']
                item.create_entries(item.edit_form.fields_container, ['f_name', 'f_item_name',
                    'f_view_template', 'f_edit_template', 'f_visible'],
                    sel_from_view_form=False, sel_from_dropdown_box=True)
            elif item.type_id.value == REPORTS_TYPE:
                item.f_edit_template.field_caption = item.task.lang['params_template']
                item.create_entries(item.edit_form.fields_container, ['f_name', 'f_item_name',
                    'f_edit_template', 'f_visible'],
                    sel_from_view_form=False, sel_from_dropdown_box=True)
            else:
                item.f_view_template.field_caption = item.task.lang['view_template']
                item.f_soft_delete.edit_visible = False
                if (item.table_id.value == 0) and not (item.id.value == item.task_id.value):
                    item.edit_form.window.set_default_size(1024, 800)
                    jam.interface.update_window_size(item.edit_form.window)
                    item.f_soft_delete.edit_visible = True
                    if item.type_id.value != REPORTS_TYPE:
                        item.create_table_grid(item.edit_form.tables_container, item.details.sys_fields)
                if task.selected_node_type_id == TASK_TYPE:
                    item.f_soft_delete.edit_visible = False
                    item.f_visible.edit_visible = False
                    item.f_table_name.edit_visible = False
                item.create_entries(item.edit_form.fields_container, #col_count=2,
                    sel_from_view_form=False, sel_from_dropdown_box=True)
        else:
            item.create_entries(item.edit_form.fields_container,
                sel_from_view_form=False, sel_from_dropdown_box=True)
    try:
        item.edit_form.ok_button.set_label(item.task.lang['ok'])
        item.edit_form.cancel_button.set_label(item.task.lang['cancel'])
        item.error_label = item.edit_form.errorLabel
    except:
        pass
task.on_before_show_edit_form = on_data_show_edit_form

###############################################################################
#                            sys_items events                                 #
###############################################################################

def items_append(item):
    item.f_visible.value = True
    item.f_soft_delete.value = True
    parent_type_id = task.selected_node_type_id
    item.parent.value = item.task.selected_node_id
    item.table_id.value = 0
    item.f_index.value = item.record_count()
    parent_task_id = item.field_by_id(item.task.selected_node_id, 'task_id')
    if parent_type_id == TASKS_TYPE:
        item.type_id.value = TASK_TYPE
    else:
        item.task_id.value = parent_task_id
    if parent_type_id == CATALOGS_TYPE:
        item.type_id.value = CATALOG_TYPE
    elif parent_type_id == JOURNALS_TYPE:
        item.type_id.value = JOURNAL_TYPE
    elif parent_type_id == TABLES_TYPE:
        item.type_id.value = TABLE_TYPE
    elif parent_type_id == REPORTS_TYPE:
        item.type_id.value = REPORT_TYPE
    elif parent_type_id in (CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE, REPORT_TYPE):
        item.type_id.value = DETAIL_TYPE
task.sys_items.on_after_append = items_append

def items_validate_name(field):
    item = field.owner
    if field.field_name == 'f_item_name':
        if not valid_identifier(field.value):
            return item.task.lang['invalid_name']
        if item.type_id.value != DETAIL_TYPE:
            items = item.copy(details=False, handlers=False)
            if item.task_id.value:
                items.filters.task_id.value = item.task_id.value;
            items.open()
            for it in items:
                if it.id.value != item.id.value and it.type_id.value != DETAIL_TYPE:
                    if it.f_item_name.value == field.value:
                        return 'There is an item with this name'
        test_task = ClientTask()
        if hasattr(test_task, field.value):
            return 'There is a task attribute with this name.'
        test_group = ClientGroup(None)
        if hasattr(test_group, field.value):
            return 'There is a group item attribute with this name.'
task.sys_items.on_field_validate = items_validate_name

def update_task_buttons(item):
    for btn in item.task.buttons:
        btn.set_sensitive(item.record_count())

def items_after_open(item):
    update_task_buttons(item)
task.sys_items.on_after_open = items_after_open

def items_before_delete(item):
    if item.type_id.value in (CATALOGS_TYPE, JOURNALS_TYPE, TABLES_TYPE):
        mess = item.task.lang['cant_delete_group']
        item.warning(mess)
        return False

    if item.id.value:
        details = item.task.sys_items.copy()
        details.filters.table_id.value = item.id.value
        details.open()
        used = []
        for d in details:
            used.append((item.task.sys_items.field_by_id(d.parent.value, 'f_item_name'), d.f_item_name.value))
        if len(used) != 0:
            names = ',\n'.join([item.task.lang['detail_mess'] % use for use in used])
            mess = item.task.lang['item_used_in_items'] % (item.f_item_name.value, names)
            item.warning(mess)
            return False

        fields = item.task.tables.sys_fields.copy()
        fields.open()
        used = []
        for f in fields:
            if f.f_object.value == item.id.value:
                used.append((item.task.sys_items.field_by_id(f.owner_rec_id.value, 'f_item_name'), f.f_field_name.value))
        if len(used) != 0:
            names = ',\n'.join([item.task.lang['field_mess'] % use for use in used])
            mess = item.task.lang['item_used_in_fields'] % (item.f_item_name.value, names)
            item.warning(mess)
            return False

        params = item.task.sys_report_params.copy()
        params.open()
        used = []
        for p in params:
            if p.f_object.value == item.id.value:
                 used.append((item.task.sys_items.field_by_id(p.owner_rec_id.value, 'f_item_name'), p.f_param_name.value))
        if len(used) != 0:
            names = ',\n'.join([item.task.lang['param_mess'] % use for use in used])
            mess = item.task.lang['item_used_in_params'] % (item.f_item_name.value, names)
            item.warning(mess)
            return False

        details = item.task.sys_items.copy()
        details.set_filters(parent=item.id.value)
        details.open()
        if details.record_count():
            mess = "Can't delete item: item contains details"
            item.warning(mess)
            return False
task.sys_items.on_before_delete = items_before_delete

def items_after_apply(item):
    if item.type_id.value in (CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE):
        item.refresh_record()
    update_task_buttons(item)
task.sys_items.on_after_apply = items_after_apply

def items_after_delete(item):
    update_task_buttons(item)
task.sys_items.on_after_delete = items_after_delete

def sys_items_field_changed(field, lookup_item):
    item = field.owner
    if item.is_new() and item.type_id.value in (CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE, REPORT_TYPE):
        if field.field_name == 'f_item_name' and item.type_id.value in (CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE):
            task_name = item.field_by_id(field.owner.task_id.value, 'f_item_name')
            item.f_table_name.value = task_name + '_' + field.value
        if field.field_name == 'f_name':
            if not item.f_item_name.value:
                try:
                    caption = field.text.replace(' ', '_').lower()
                    if valid_identifier(caption):
                        item.f_item_name.value = caption
                except:
                    pass
task.sys_items.on_field_changed = sys_items_field_changed

def items_after_scroll(item):
    if item.type_id.value == TASK_TYPE:
        item.task.sys_tasks.set_filters(task_id=item.id.value)
        item.task.sys_tasks.open()
task.sys_items.on_after_scroll = items_after_scroll


###############################################################################
#                              item_fields events                             #
###############################################################################

def fields_validate(field):
    item = field.owner
    if field.field_name == 'f_field_name':
        if not valid_identifier(field.value):
            return item.task.lang['invalid_field_name']
        clone = item.clone()
        for c in clone:
            if item.rec_no != c.rec_no:
                if field.value == c.f_field_name.value:
                    return 'There is a field with this name'
        test_item = ClientItem(task)
        if hasattr(test_item, field.value):
            return 'There is an item attribute with this name.'
        #~ test_field = DBField()
        #~ if field.value in test_field.__dict__.keys():
            #~ return 'There is a field attribute with this name.'
    if field.field_name == 'f_data_type':
        if item.f_data_type.value == 0:
            return item.task.lang['type_is_required']
task.sys_items.details.sys_fields.on_field_validate = fields_validate

def item_fields_field_changed(field, lookup_item):
    item = field.owner
    if field.field_name == 'f_name':
        if item.field_by_name('f_field_name'):
            if not item.f_field_name.value:
                try:
                    caption = field.text.replace(' ', '_').lower()
                    if valid_identifier(caption):
                        item.f_field_name.value = caption
                except:
                    pass
        elif item.field_by_name('f_param_name'):
            if not item.f_param_name.value:
                try:
                    caption = field.text.replace(' ', '_').lower()
                    if valid_identifier(caption):
                        item.f_param_name.value = caption
                except:
                    pass
    elif field == item.f_object:
        item.f_object_field.value = None
        if item.f_object.value:
            item.f_data_type.value = INTEGER
            item.f_data_type.read_only = True
        else:
            if item.is_new() or item.task.sys_tasks.f_manual_update.value:
                item.f_data_type.value = None
                item.f_data_type.read_only = False
    elif field == item.f_data_type:
        if item.f_data_type.value == TEXT:
            item.f_size.value = 10
        else:
            item.f_size.value = None
    if field in (item.f_data_type, item.f_object):
        item.f_alignment.value = get_alignment(item.f_data_type.value, item.f_object.value)
task.sys_items.details.sys_fields.on_field_changed = item_fields_field_changed

def item_fields_before_delete(item):

    def check_is_system_field(item):
        if item.f_field_name.value in SYSTEM_FIELDS:
            mess = item.task.lang['field_is_system']
            item.warning(mess)
            return False
        return True

    def check_is_used(item):
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
            names = ',\n'.join([u'%s - %s' % use for use in used])
            mess = item.task.lang['field_used_in_fields'] % \
                (item.f_field_name.value, names)
            item.warning(mess)
            return False
        return True

    def check_in_index(item):
        field_id = item.id.value
        indices = item.task.sys_indices
        indices.filters.owner_rec_id.value = item.owner.id.value
        indices.open()
        ind_list = []
        for ind in indices:
            if ind.f_foreign_index.value:
                if ind.f_foreign_field.value == field_id:
                    ind_list.append(ind.f_index_name.value)
            else:
                field_list = cPickle.loads(str(ind.f_fields.value))
                for fld in field_list:
                    if fld[0] == field_id:
                        ind_list.append(ind.f_index_name.value)
        if len(ind_list):
            names = ',\n'.join(ind_list)
            mess = item.task.lang['field_used_in_indices'] % \
                (item.f_field_name.value, names)
            item.warning(mess)
            return False
        return True

    def check_in_filter(item):
        field_id = item.id.value
        filters = item.task.sys_filters
        filters.filters.owner_rec_id.value = item.owner.id.value
        filters.open()
        filters_list = []
        for fltr in filters:
            if fltr.f_field.value == field_id:
                filters_list.append(fltr.f_filter_name.value)
        if len(filters_list):
            names = ',\n'.join(filters_list)
            mess = item.task.lang['field_used_in_filters'] % \
                (item.f_field_name.value, names)
            item.warning(mess)
            return False
        return True

    if not item.owner.item_state == STATE_DELETE:
        if not check_is_system_field(item) or \
            not check_is_used(item) or \
            not check_in_index(item) or \
            not check_in_filter(item):
            return False
task.sys_items.details.sys_fields.on_before_delete = item_fields_before_delete

def fields_after_append(item):
    item.task_id.value = item.master.task_id.value
    item.f_data_type.read_only = False
task.sys_items.details.sys_fields.on_after_append = fields_after_append

def fields_before_post(item):
    if item.f_object.value:
        if not item.f_object_field.value:
            item.warning(item.task.lang['object_field_required'])
            return False
#            raise Exception, item.task.lang['object_field_required']
    if item.f_data_type.value != TEXT:
        item.f_size.value = None
task.sys_items.details.sys_fields.on_before_post = fields_before_post

def on_field_lookup_item_show(field, lookup_item):
    item = field.owner
    if field == item.f_object:
        if item.owner == item.task.sys_items:
            lookup_item.filters.not_id.value = item.owner.id.value
            if item.owner.type_id.value == TASK_TYPE:
                lookup_item.filters.task_id.value = item.owner.id.value
            else:
                lookup_item.filters.task_id.value = item.owner.task_id.value
        lookup_item.set_order_by('f_item_name')
        lookup_item.filters.type_id.value = [CATALOG_TYPE, JOURNAL_TYPE, TABLE_TYPE]
        lookup_item.filters.table_id.value = 0
    elif field.field_name == 'f_master_field' and item.f_object.value:
        id_value = item.owner.id.value
        parent = item.task.sys_items.field_by_id(id_value, 'parent')
        lookup_item.filters.owner_rec_id.value = [id_value, parent]
        lookup_item.filters.not_id.value = item.id.value
        lookup_item.filters.object.value = item.f_object.value
        lookup_item.filters.master_field_is_null.value = True
    if field.field_name == 'f_object_field':
        if item.f_object.value:
            id_value = item.f_object.value
            parent = item.task.sys_items.field_by_id(id_value, 'parent')
            lookup_item.filters.owner_rec_id.value = [id_value, parent]
        else:
            lookup_item.filters.owner_rec_id.value = [-1]
task.sys_items.details.sys_fields.on_field_lookup_item_show = on_field_lookup_item_show

def fields_before_edit(item):
    item.read_only = item.f_field_name.value in SYSTEM_FIELDS
task.sys_items.details.sys_fields.on_before_edit = fields_before_edit

def fields_after_scroll(item):
    item.read_only = False
task.sys_items.details.sys_fields.on_after_scroll = fields_after_scroll

def fields_on_before_show_edit_form(item):

    def check_in_foreign_index():
        result = False
        if item.owner.id.value and item.id.value:
            indices = item.task.sys_indices
            indices.set_where(owner_rec_id=item.owner.id.value)
            indices.open()
            for ind in indices:
                if ind.f_foreign_index.value:
                    if ind.f_foreign_field.value == item.id.value:
                        result = True
        return result

    item.f_data_type.read_only = False
    item.f_size.read_only = False
    item.f_object.read_only = False
    item.f_object_field.read_only = False
    item.f_master_field.read_only = False
    if not item.is_new() and not item.task.sys_tasks.f_manual_update.value:
        item.f_data_type.read_only = True
        item.f_size.read_only = True
        item.f_object.read_only = True
        if item.f_data_type.value != INTEGER or not item.f_object.value:
            item.f_object_field.read_only = True
            item.f_master_field.read_only = True
    if check_in_foreign_index():
        item.f_object.read_only = True


task.sys_items.details.sys_fields.on_before_show_edit_form = fields_on_before_show_edit_form

###############################################################################
#                              filters events                                 #
###############################################################################


def filters_append(item):
    item.task_id.value = item.task.sys_items.task_id.value
    item.owner_id.value = 0
    item.f_visible.value = True
    item.f_index.value = item.record_count()
    item.f_type.value = FILTER_EQ
task.sys_filters.on_after_append = filters_append

def filters_before_post(item):
    item.owner_rec_id.value = item.task.sys_items.id.value
    item.owner.value = item.task.sys_items.ID
task.sys_filters.on_before_post = filters_before_post

def filters_field_changed(field, lookup_item):
    item = field.owner
    if field == item.f_field:
        fields = item.task.sys_fields.copy()
        fields.filters.id.value = field.value
        fields.open()
        item.f_name.value = fields.f_name.value
        item.f_filter_name.value = fields.f_field_name.value
task.sys_filters.on_field_changed = filters_field_changed

def on_filters_lookup_item_show(field, lookup_item):
    item = field.owner
    if field == item.f_field:
        item_id = item.task.sys_items.id.value
        item_parent = item.task.sys_items.field_by_id(item_id, 'parent')
        lookup_item.filters.owner_rec_id.value = [item_id, item_parent]
        lookup_item.filters.master_field_is_null.value = True
task.sys_filters.on_field_lookup_item_show = on_filters_lookup_item_show

def sys_filters_show_view_form(item):

    def move_filter_up(widget):
        item.grid.move_up()

    def move_filter_down(widget):
        item.grid.move_down()

    dic = {
        "on_buttonEdit_clicked": item.edit_record,
        "on_buttonDel_clicked": item.delete_record,
        "on_buttonNew_clicked": item.append_record,
        "on_up_button_clicked": move_filter_up,
        "on_down_button_clicked": move_filter_down,
        }
    item.view_form.builder.connect_signals(dic)
    grid = jam.interface.DBGrid(item)
    item.view_form.grid_container.add(grid)
    item.view_form.window.set_default_size(650, 400)
    item.grid = grid
    grid.show_all()
    item.view_form.delete_button.set_label(item.task.lang['delete'])
    item.view_form.new_button.set_label(item.task.lang['new'])
    item.view_form.edit_button.set_label(item.task.lang['edit'])
task.sys_filters.on_before_show_view_form = sys_filters_show_view_form

def filters_destroy_view_form(item):
    for it in item:
        cur_iter = item.grid.find_rec_iter()
        it.edit()
        it.f_index.value = item.grid.path_by_iter(cur_iter)
        it.post()
    item.apply()
task.sys_filters.on_view_form_close_query = filters_destroy_view_form

###############################################################################
#                            sys_users events                                 #
###############################################################################

def sys_users_show_view_form(item):
    def empty(widget):
        pass

    item.view_form.up_down_hbox.set_visible(False)
    item.view_form.delete_button.set_label(item.task.lang['delete'])
    item.view_form.new_button.set_label(item.task.lang['new'])
    item.view_form.edit_button.set_label(item.task.lang['edit'])
    item.view_form.select_button.set_label(item.task.lang['select'])
    dic = {
        "on_select_button_clicked" : item.set_lookup_field_value,
        "on_edit_button_clicked" : item.edit_record,
        "on_delete_button_clicked" : item.delete_record,
        "on_new_button_clicked" : item.insert_record,
        "on_up_button_clicked": empty,
        "on_down_button_clicked": empty,
        }
    item.view_form.builder.connect_signals(dic)
    grid = jam.interface.DBGrid(item)
    item.view_form.grid_container.add(grid)
    if item.view_form.select_button:
        item.view_form.select_button.set_visible(False)
    grid.show_all()
task.sys_users.on_before_show_view_form = sys_users_show_view_form

###############################################################################
#                            sys_roles events                                 #
###############################################################################

def roles_before_scroll(item):
    if item.item_state in (STATE_INSERT, STATE_EDIT):
        item.post()
        item.apply()
task.sys_roles.on_before_scroll = roles_before_scroll

def roles_after_scroll(item):
    if item.item_state == STATE_BROWSE:
        item.edit()
task.sys_roles.on_after_scroll = roles_after_scroll

def role_privileges_field_changed(field, lookup_item):
    item = field.owner
    item.post()
    item.owner.post()
    if item.id.value:
        item.record_status = RECORD_MODIFIED
    else:
        item.record_status = RECORD_INSERTED
    item.owner.apply()
    item.owner.edit()
task.sys_roles.details.sys_privileges.on_field_changed = role_privileges_field_changed

def sys_roles_show_view_form(item):

    def select_all_clicked(widget, value=True):
        if item.item_state == STATE_BROWSE:
            item.edit()
        detail = item.details.sys_privileges
        rec_no = detail.rec_no
        detail.on_field_changed = None
        detail.disable_controls
        for d in detail:
            d.edit()
            d.f_can_create.value = value
            d.f_can_view.value = value
            d.f_can_edit.value = value
            d.f_can_delete.value = value
            if d.id.value:
                d.record_status = RECORD_MODIFIED
            else:
                d.record_status = RECORD_INSERTED
            d.post()
        detail.on_field_changed = role_privileges_field_changed
        detail.rec_no = rec_no
        detail.enable_controls
        if item.item_state in (STATE_INSERT, STATE_EDIT):
            item.post()
            item.apply()
            item.edit()

    def del_role(widget):
        if item.item_state in (STATE_INSERT, STATE_EDIT):
            item.post()
            item.apply()
        item.delete_record(widget)

    def append_role(widget):
        if item.item_state in (STATE_INSERT, STATE_EDIT):
            item.post()
            item.apply()
        item.append_record(widget)

    def unselect_all_clicked(widget):
        select_all_clicked(widget, value=False)

    dic = {
        "on_delete_button_clicked" : del_role,
        "on_new_button_clicked" : append_role,
        "on_select_all_clicked" : select_all_clicked,
        "on_unselect_all_clicked" : unselect_all_clicked,
        }

    item.view_form.builder.connect_signals(dic)
    grid = jam.interface.DBGrid(item)
    item.view_form.delete_button.set_label(item.task.lang['delete'])
    item.view_form.new_button.set_label(item.task.lang['new'])
    item.view_form.select_all_button.set_label(item.task.lang['select_all'])
    item.view_form.unselect_all_button.set_label(item.task.lang['unselect_all'])
    item.view_form.grid_container.add(grid)
    item.create_table_grids(item.view_form.tables_container, create_buttons=False, dblclick_edit=False)
    grid.show_all()
    item.details_active = True
task.sys_roles.on_before_show_view_form = sys_roles_show_view_form

###############################################################################
#                            sys_tasks events                                 #
###############################################################################

def tasks_field_changed(field, lookup_item):
    if field == field.owner.f_db_type:
        if field.owner.is_changing():
            field.owner.f_alias.value = None
            field.owner.f_login.value = None
            field.owner.f_password.value = None
            field.owner.f_encoding.value = None
            field.owner.f_host.value = None
            field.owner.f_port.value = None
        field.owner.f_login.read_only = field.value == SQLITE
        field.owner.f_password.read_only = field.value == SQLITE
        field.owner.f_encoding.read_only = field.value in (SQLITE, POSTGRESQL, MYSQL)
        field.owner.f_host.read_only = field.value == SQLITE
        field.owner.f_port.read_only = field.value in (SQLITE, FIREBIRD, MYSQL)
task.sys_tasks.on_field_changed = tasks_field_changed

def tasks_before_post(item):
    check_result = task.server_check_connection(item.f_db_type.value, item.f_alias.value,
        item.f_login.value, item.f_password.value, item.f_host.value,
        item.f_port.value, item.f_encoding.value)
    if not check_result[0]:
        mess = task.lang['can_not_connect'] + ': ' + check_result[1]
        item.warning(mess)
        item.abort()
task.sys_tasks.on_before_post = tasks_before_post

###############################################################################
#                            sys_indices events                               #
###############################################################################

def indices_after_append(item):
    task_name = item.task.sys_items.field_by_id(item.task.sys_items.task_id.value, 'f_item_name').upper()
    sys_item_name = item.task.sys_items.f_item_name.value.upper()
    if not item.filters.foreign_index.value:
        item.f_index_name.value = '%s_%s_IDX' % (task_name, sys_item_name)
    item.task_id.value = item.task.sys_items.task_id.value
    item.owner_rec_id.value = item.task.sys_items.id.value
    item.f_foreign_index.value = item.filters.foreign_index.value
task.sys_indices.on_after_append = indices_after_append

def on_indices_lookup_item_show(field, lookup_item):

    def filter_record(item):
        if item.f_object.value:
            soft_delete = item.task.sys_items.field_by_id(item.f_object.value, 'f_soft_delete')
            if not soft_delete:
                clone = field.owner.clone()
                for c in clone:
                    if c.f_foreign_field.value == item.id.value:
                        return False
                return True

    lookup_item.on_filter_record = filter_record
    lookup_item.filtered = True
task.sys_indices.on_field_lookup_item_show = on_indices_lookup_item_show

def on_indices_field_changed(field, lookup_item):
    if field.field_name == 'f_foreign_field':
        field.owner.f_index_name.value = 'FK_%s_%s' % \
            (field.owner.task.sys_items.f_table_name.value.upper(), field.display_text.upper())
task.sys_indices.on_field_changed = on_indices_field_changed

def sys_indices_show_view_form(item):

    source_def = [{'caption': '', 'type': int},
            {'caption': item.task.lang['caption_name'], 'type': str},
            ]

    def edit_index(widget, new):

        def save_index(dest_list):
            if new:
                if not item.f_index_name.value:
                    mess = item.task.lang['index_name_required']
                    item.warning(mess)
                    raise Exception, mess
                if len(dest_list) == 0:
                    mess = item.task.lang['index_fields_required']
                    item.warning(mess)
                    raise Exception, mess
                item.f_fields.value = cPickle.dumps(dest_list)
                item.post()
                try:
                    item.apply()
                except Exception, e:
                    item.warning(e.message)
            else:
                item.read_only = False
                item.cancel()

        def cancel_action():
            item.read_only = False
            item.cancel()

        index_list = []
        if new:
            item.append()
            item.read_only = False
        else:
            if item.record_count() > 0:
                item.edit()
                item.read_only = True
                index_list = cPickle.loads(str(item.f_fields.value))
            else:
                return

        editor = FieldEditor(item, widget, u'',
            source_def, get_fields_list(item), source_def, index_list, save_index, cancel_action, read_only=not new)
        item.create_entries(editor.builder.get_object('fields_container'),
            sel_from_view_form=False, sel_from_dropdown_box=True)
        editor.show()

    def edit_record(widget):
        edit_index(widget, False)

    def insert_record(widget):
        edit_index(widget, True)

    if item.filters.foreign_index.value:
        item.view_form.window.set_title(u'Foreign keys')
        item.f_index_name.field_caption = u'Foreign key'
        item.set_view_fields(['f_foreign_field', 'f_index_name' ])
        item.set_edit_fields(['f_foreign_field', 'f_index_name' ])
        item.f_foreign_field.required = True
        item.f_index_name.required = True
        dic = {
            "on_new_button_clicked" : item.insert_record,
            "on_edit_button_clicked" : item.edit_record,
            "on_delete_button_clicked" : item.delete_record,
            }
    else:
        item.view_form.window.set_title(u'Indices')
        item.f_index_name.field_caption = u'Index'
        item.set_view_fields(['f_index_name', 'descending'])
        item.set_edit_fields(['f_index_name', 'descending'])
        item.f_foreign_field.required = False
        dic = {
            "on_new_button_clicked" : insert_record,
            "on_edit_button_clicked" : edit_record,
            "on_delete_button_clicked" : item.delete_record,
            }
    item.view_form.edit_button.set_label(task.lang['viewing'])
    item.view_form.builder.connect_signals(dic)
    if not item.filters.foreign_index.value:
        grid = jam.interface.DBGrid(item, on_dblclick=edit_record)
    else:
        grid = jam.interface.DBGrid(item)
    item.view_form.grid_container.add(grid)
    item.view_form.window.set_default_size(600, 400)
    item.grid = grid
    grid.show_all()
task.sys_indices.on_before_show_view_form = sys_indices_show_view_form

def validate_index(field):
    item = field.owner
    if field.field_name == 'f_index_name':
        clone = item.clone()
        for c in clone:
            if item.rec_no != c.rec_no:
                if field.value == c.f_index_name.value:
                    return 'There is index with this name';
task.sys_indices.on_field_validate = validate_index


###############################################################################
#                          report params events                               #
###############################################################################

def params_append(item):
    item.task_id.value = item.task_id.value
    item.f_data_type.read_only = False
    item.f_visible.value = True
task.sys_report_params.on_after_append = params_append

task.sys_report_params.on_before_show_view_form = sys_filters_show_view_form
task.sys_report_params.on_view_form_close_query = filters_destroy_view_form
task.sys_report_params.on_field_validate = fields_validate
task.sys_report_params.on_field_changed = item_fields_field_changed
task.sys_report_params.on_field_lookup_item_show = on_field_lookup_item_show
task.sys_report_params.on_before_post = filters_before_post
