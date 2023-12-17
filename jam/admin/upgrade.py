import os
from xml.dom.minidom import parse

def version7_upgrade(task):

    def field_by_id(id_value):
        sys_fields.rec_no = field_dict.get(id_value)
        return sys_fields

    def replace_in_field(field, field_dict):
        new_value = field_dict.get(field.value)
        if not new_value is None:
            field.value = new_value

    def replace_fields_in_list(l, field_dict):
        if l:
            for i, id_value in enumerate(l):
                new_id_field = field_dict.get(id_value)
                if not new_id_field is None:
                    l[i] = new_id_field
        return l

    def replace_fields_in_lists(lists, field_dict):
        if lists:
            for i, l in enumerate(lists):
                new_id_field = field_dict.get(l[0])
                if not new_id_field is None:
                    lists[i][0] = new_id_field
        return lists

    def upgrade_details(item, field_dict):
        items_rec_no = sys_items.rec_no
        recs = details_dict.get(item.id.value)
        if recs:
            for rec in recs:
                sys_items.rec_no = rec
                upgrade_interface(sys_items, field_dict)
        sys_items.rec_no = items_rec_no

    def upgrade_interface(item, field_dict):
        item.load_interface()
        if type(item._view_list) is list:
            item._view_list = replace_fields_in_lists(item._view_list, field_dict)
        else:
            form_options = item._view_list['0'][1];
            if form_options.get('search_field'):
                form_options['search_field'] = replace_fields_in_list(form_options['search_field'], field_dict)
            table_options = item._view_list['0'][3];
            if table_options.get('summary_fields'):
                table_options['summary_fields'] = replace_fields_in_list(table_options['summary_fields'], field_dict)
            if table_options.get('sort_fields'):
                table_options['sort_fields'] = replace_fields_in_list(table_options['sort_fields'], field_dict)
            if table_options.get('edit_fields'):
                table_options['edit_fields'] = replace_fields_in_list(table_options['edit_fields'], field_dict)
            table_fields = item._view_list['0'][4];
            table_fields = replace_fields_in_lists(table_fields, field_dict)
        if type(item._edit_list) is list:
            item._edit_list = replace_fields_in_lists(item._edit_list, field_dict)
        else:
            form_tabs = item._edit_list['0'][3];
            for tab in form_tabs:
                bands = tab[1];
                for band in bands:
                    fields = band[1]
                    fields = replace_fields_in_lists(fields, field_dict)
        item._order_list = replace_fields_in_lists(item._order_list, field_dict)
        item.store_interface(apply_interface=False)

    def upgrade_indices(item, field_dict):
        recs = indices_dict.get(item.id.value)
        if recs:
            for rec in recs:
                sys_indices.rec_no = rec
                field_str = sys_indices.f_fields_list.value
                if field_str:
                    field_list = sys_indices.load_index_fields(field_str)
                    field_list = replace_fields_in_lists(field_list, field_dict)
                    sys_indices.edit()
                    sys_indices.f_fields_list.value = sys_indices.store_index_fields(field_list)
                    sys_indices.post()

    def upgrade_filters(item, field_dict):
        recs = filters_dict.get(item.id.value)
        if recs:
            for rec in recs:
                sys_filters.rec_no = rec
                new_field_id = field_dict.get(sys_filters.f_field.value)
                if not new_field_id is None:
                    sys_filters.edit()
                    sys_filters.f_field.value = new_field_id
                    sys_filters.post()

    sys_params = task.sys_params.copy(handlers=False)
    sys_params.open()
    if sys_params.f_upgraded_to.value >= 7:
        return

    con = task.connect()

    lang = sys_params.f_language.value
    sys_params.edit()
    sys_params.f_upgraded_to.value = 7
    if not lang:
        sys_params.f_language.data = 1
    sys_params.post()
    sys_params.f_language.data = lang
    sys_params.apply(connection=con)

    sys_fields = task.sys_fields.copy(handlers=False)
    sys_fields.open()
    field_dict = {}
    field_item_dict = {}
    for f in sys_fields:
        field_dict[f.id.value] = sys_fields.rec_no
        field_item_dict[f.id.value] = f.owner_rec_id.value
    new_sys_fields = task.sys_fields.copy(handlers=False)
    new_sys_fields.open(open_empty=True)

    sys_indices = task.sys_indices.copy(handlers=False)
    sys_indices.open()
    indices_dict = {}
    for i in sys_indices:
        if indices_dict.get(i.owner_rec_id.value) is None:
            indices_dict[i.owner_rec_id.value] = []
        indices_dict[i.owner_rec_id.value].append(i.rec_no)

    sys_filters = task.sys_filters.copy(handlers=False)
    sys_filters.open()
    filters_dict = {}
    for f in sys_filters:
        if filters_dict.get(f.owner_rec_id.value) is None:
            filters_dict[f.owner_rec_id.value] = []
        filters_dict[f.owner_rec_id.value].append(f.rec_no)

    sys_items = task.sys_items.copy(handlers=False, details=False)
    sys_items.set_order_by(['id'])
    sys_items.open()
    details_dict = {}
    for i in sys_items:
        if details_dict.get(i.parent.value) is None:
            details_dict[i.parent.value] = []
        details_dict[i.parent.value].append(i.rec_no)
    upgrade_field_names = ['f_primary_key', 'f_deleted_flag', 'f_master_id', 'f_master_rec_id']
    upgrade_fields = []
    for field_name in upgrade_field_names:
        field = sys_items.field_by_name(field_name)
        if field:
            upgrade_fields.append(field)
    cur_field_id = 10000
    item_field_dict = {}
    for item in sys_items:
        if item.parent.value and item.table_id.value == 0 and item.type_id.value >= 10: # and item.f_table_name.value:
            pk_value = item.f_primary_key.value
            if pk_value:
                field_rec = field_by_id(pk_value)
                if item.id.value != field_rec.owner_rec_id.value:
                    field_pk_dict = {}
                    for f in upgrade_fields:
                        if f.value:
                            field_rec = field_by_id(f.value)
                            new_sys_fields.append()
                            for field in new_sys_fields.fields:
                                field.value = field_rec.field_by_name(field.field_name).data
                            new_sys_fields.owner_rec_id.value = item.id.value
                            old_pk = new_sys_fields._primary_key_field.data
                            new_pk = cur_field_id
                            new_sys_fields._primary_key_field.data = new_pk
                            new_sys_fields.post()
                            field_pk_dict[old_pk] = new_pk
                            cur_field_id += 1
                            item.edit()
                            f.value = new_pk
                            item.post()
                    item_field_dict[item.id.value] = field_pk_dict
                    upgrade_interface(item, field_pk_dict)
                    upgrade_filters(item, field_pk_dict)
                    upgrade_indices(item, field_pk_dict)
                    upgrade_details(item, field_pk_dict)
    if item_field_dict:
        for field in sys_fields:
            if field.f_object.value:
                field.edit()
                value = field.f_object_field.value
                field_pk_dict = item_field_dict[field.f_object.value]
                replace_in_field(field.f_object_field, field_pk_dict)
                replace_in_field(field.f_master_field, field_pk_dict)
                value1 = field.f_object_field1.value
                if value1:
                    rec_no = sys_fields.rec_no
                    sys_fields.rec_no = field_dict[value]
                    object1 = sys_fields.f_object.value
                    sys_fields.rec_no = rec_no
                    field_pk_dict = item_field_dict[object1]
                    replace_in_field(field.f_object_field1, field_pk_dict)
                    value2 = field.f_object_field2.value
                    if value2:
                        rec_no = sys_fields.rec_no
                        sys_fields.rec_no = field_dict[value1]
                        object2 = sys_fields.f_object.value
                        sys_fields.rec_no = rec_no
                        field_pk_dict = item_field_dict[object2]
                        replace_in_field(field.f_object_field2, field_pk_dict)
                field.post()
        report_params = task.sys_report_params.copy(handlers=False)
        report_params.open()
        for param in report_params:
            if param.f_object.value:
                param.edit()
                field_pk_dict = item_field_dict[param.f_object.value]
                replace_in_field(param.f_object_field, field_pk_dict)
                param.post()

        report_params.apply(connection=con)
        new_sys_fields.apply(connection=con)
        sys_fields.apply(connection=con)
        sys_indices.apply(connection=con)
        sys_filters.apply(connection=con)
        sys_items.apply(connection=con)

    sys_items = task.sys_items.copy(handlers=False, details=False)
    sys_items.set_where(type_id=5)
    sys_items.open(fields=['id', 'f_web_client_module'])
    code = sys_items.f_web_client_module.value
    code = code.replace('if (item.master) {', 'if (item.master || item.master_field) {')
    code = code.replace('if (!item.master &&', 'if (!(item.master || item.master_field) &&')
    code = code.replace("hasClass('modal')", "hasClass('modal-form')")
    sys_items.edit()
    sys_items.f_web_client_module.value = code
    sys_items.post()
    sys_items.apply(connection=con)

    sys_items = task.sys_items.copy(handlers=False, details=False)
    sys_items.open(fields=['id', 'table_id', 'f_master_applies'])
    for i in sys_items:
        if i.table_id.value:
            i.edit()
            i.f_master_applies.value = True
            i.post()
    sys_items.apply(connection=con)

    if os.path.exists('register.html'):
        sys_items.set_where(type_id=5)
        sys_items.open(fields=['id', 'f_server_module'])
        code = sys_items.f_server_module.value
        if code.find('def on_request(task, request):') == -1:
            code = code + """
def on_request(task, request):
    parts = request.path.strip('/').split('/')
    if parts[0] == 'register.html':
        return task.serve_page('register.html')
        """
            sys_items.edit()
            sys_items.f_server_module.value = code
            sys_items.post()
            sys_items.apply(connection=con)

    con.commit()
