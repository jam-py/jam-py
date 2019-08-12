import os
import json
import datetime
from threading import Lock
from operator import itemgetter
from esprima import parseScript, nodes

from werkzeug._compat import iteritems, iterkeys, to_unicode, to_bytes, text_type, string_types

from jam.common import consts
from jam.dataset import FIELD_NAME, FIELD_CAPTION, FIELD_LOOKUP_VALUES

from jam.common import consts, error_message, file_read, file_write
from jam.db.db_modules import SQLITE, FIREBIRD, DB_TYPE, get_db_module
from jam.server_classes import AdminTask, Group
from jam.dataset import LOOKUP_ITEM, LOOKUP_FIELD, FIELD_ALIGNMENT
from jam.events import get_events
from jam.execute import execute_sql
from jam.admin.export_metadata import export_task
import jam.langs as langs

LOOKUP_LISTS = {
        'f_theme': consts.THEMES,
        'f_db_type': DB_TYPE,
        'f_data_type': consts.FIELD_TYPES,
        'f_alignment': consts.ALIGNMENT,
        'f_type': consts.FILTER_STRING,
        'label_size': ['xSmall', 'Small', 'Medium', 'Large', 'xLarge'],
        'group_type': consts.GROUP_TYPES,

    }
    
def get_value_list(str_list):
    result = []
    for i, s in enumerate(str_list):
        result.append([i + 1, s])
    return result

def init_items(item):
    if hasattr(item, 'field_defs'):
        item.soft_delete = False
        item._primary_key_db_field_name = item._primary_key.upper()
        item._deleted_flag_db_field_name = item._deleted_flag.upper()
        # item._record_version_db_field_name = item._record_version.upper()
        if item.master:
            item._master_id_db_field_name = item._master_id.upper()
            item._master_rec_id_db_field_name = item._master_rec_id.upper()
        for field_def in item.field_defs:
            field_def[FIELD_CAPTION] = item.task.language(field_def[FIELD_CAPTION])
            lookup_list = LOOKUP_LISTS.get(field_def[FIELD_NAME])
            if lookup_list:
                field_def[FIELD_LOOKUP_VALUES] = get_value_list(lookup_list)

def save_caption_keys(task):

    def save_keys(item):
        if hasattr(item, 'field_defs'):
            item.__caption_keys = {}
            for field_def in item.field_defs:
                item.__caption_keys[field_def[FIELD_NAME]] = field_def[FIELD_CAPTION]

    task.all(save_keys)

def restore_caption_keys(task):

    def restore_keys(item):
        if hasattr(item, 'field_defs'):
            for field_def in item.field_defs:
                field_def[FIELD_CAPTION] = item.__caption_keys[field_def[FIELD_NAME]] 

    task.all(restore_keys)

def change_language(task):
    
    def change_fields_lang(item):
        if hasattr(item, 'field_defs'):
            for field_def in item.field_defs:
                field_def[FIELD_CAPTION] = item.task.language(field_def[FIELD_CAPTION])
    
    restore_caption_keys(task)
    consts.read_language()
    task.all(change_fields_lang)

def init_task_attr(task):
    tasks = task.sys_tasks.copy()
    tasks.open()
    task.task_db_type = tasks.f_db_type.value
    task.task_db_server = tasks.f_server.value
    task.task_db_database = tasks.f_alias.value
    task.task_db_user = tasks.f_login.value
    task.task_db_password = tasks.f_password.value
    task.task_db_host = tasks.f_host.value
    task.task_db_port = tasks.f_port.value
    task.task_db_encoding = tasks.f_encoding.value
    task.task_db_module = get_db_module(task.task_db_type)

def on_created(task):
    save_caption_keys(task)
    task.all(init_items)
    consts.read_settings()
    consts.MAINTENANCE = False
    consts.write_settings(['MAINTENANCE'])
    task.task_con_pool_size = consts.CON_POOL_SIZE
    if task.task_con_pool_size < 1:
        task.task_con_pool_size = 3
    try:
        task.task_persist_con = consts.PERSIST_CON
    except:
        task.task_persist_con = True
    task.ignore_change_ip = consts.IGNORE_CHANGE_IP
    task.ignore_change_uuid = True
    task.item_caption = task.language('admin')
    register_events(task)
    task.fields_id_lock = Lock()
    init_fields_next_id(task)
    init_task_attr(task)

def execute_db(task, task_id, sql, params=None):
    if task_id == 0:
        result_set, error = task.execute(sql, params)
        return error
    else:
        connection = None
        connection, (result_set, error) = execute_sql(task.task_db_module,
            task.task_db_server, task.task_db_database, task.task_db_user,
            task.task_db_password, task.task_db_host, task.task_db_port,
            task.task_db_encoding, connection, sql, params)
        if connection:
            connection.rollback()
            connection.close()
        return error

def get_privileges(task, role_id):
    result = {}
    privliges = task.sys_privileges.copy()
    privliges.set_where(owner_rec_id=role_id)
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

def login_user(task, log, password, taskin, ip=None, session_uuid=None):
    user_id = None
    user_info = {}
    if consts.SAFE_MODE:
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

###############################################################################
#                                 task                                        #
###############################################################################

def server_check_connection(task, db_type, database, user, password, host, port, encoding, server):
    error = ''
    if db_type:
        try:
            db_module = get_db_module(db_type)
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
    items.set_where(type_id=consts.TASK_TYPE)
    items.open()
    items.edit()
    items.f_name.value = f_name
    items.f_item_name.value = f_item_name
    items.post()
    items.apply()
    # ~ task.app.task = None

def server_set_project_langage(task, lang):
    consts.LANGUAGE = lang
    consts.read_language()
    consts.write_settings()
    consts.read_settings()
    change_language(task)
    # ~ create_items(task)

    items = task.sys_items.copy()
    items.open()
    for it in items:
        it.edit()
        try:
            it.f_name.value = task.language(it.f_item_name.value)
        except Exception as e:
            task.log.exception(error_message(e))
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

def server_update_has_children(task):
    has_children = {}
    items = task.sys_items.copy(handlers=False)
    items.open()
    for it in items:
        has_children[it.parent.value] = True
        if it.type_id.value in (consts.ROOT_TYPE,
            consts.USERS_TYPE, consts.ROLES_TYPE,
            consts.TASKS_TYPE, consts.ITEMS_TYPE,
            consts.TABLES_TYPE, consts.REPORTS_TYPE):
            has_children[it.id.value] = True
    for it in items:
        if not has_children.get(it.id.value):
            has_children[it.id.value] = False
        if it.has_children.value != has_children.get(it.id.value):
            it.edit()
            it.has_children.value = has_children.get(it.id.value)
            it.post()
    items.apply()

def server_export_task(task, url=None):
    return export_task(task, url)

def server_import_task(task, file_name, from_client=False):
    return task.app.import_md(file_name, from_client)

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
            if module_type == consts.WEB_CLIENT_MODULE:
                text = it.f_web_client_module.value
            elif module_type == consts.SERVER_MODULE:
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
    result = {'client': find_in_type('', consts.WEB_CLIENT_MODULE),
        'server': find_in_type('', consts.SERVER_MODULE)}
    return result

def server_web_print_code(task, task_id):

    def add_detail_code(item, module_type):
        for child in children:
            if child.table_id.value == item.id.value:
                add_code(child, module_type)

    def add_code(item, module_type):
        if module_type == consts.WEB_CLIENT_MODULE:
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
            add_code(items, consts.WEB_CLIENT_MODULE)
            add_code(items, consts.SERVER_MODULE)
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
        if it.type_id.value == consts.DETAIL_TYPE:
            parent, type_id, name, parent_external = name_dict.get(it.parent.value)
            external = parent_external
        return external

    def update_task(item):
        js_filename = js_filenames.get(item.ID, '')
        item.js_filename = js_filename

    def get_js_file_name(js_path):
        return js_path + '.js'

    single_file = consts.SINGLE_FILE_JS
    name_dict = {}
    js_filenames = {}

    it = task.sys_items.copy(handlers=False, details=False)
    it.set_where(type_id=consts.TASK_TYPE)
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
                    if consts.COMPRESSED_JS:
                        minify(file_name)
            js_filenames[it.id.value] = cur_js_filename
    if single_file:
        it.first()
        js_file_name = get_js_file_name(it.f_item_name.value)
        js_filenames[it.id.value] = js_file_name
        script = script_start + script_common + script_end
        file_name = os.path.join(to_unicode(os.getcwd(), 'utf-8'), 'js', js_file_name)
        file_write(file_name, script)
        if consts.COMPRESSED_JS:
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
    if type_id in [consts.ITEM_TYPE, consts.TABLE_TYPE, consts.DETAIL_TYPE]:
        fields = task.sys_fields.copy()
        if table_id:
            parent_id = task.sys_items.field_by_id(table_id, 'parent')
        fields.set_where(owner_rec_id__in=[item_id, parent_id])
        fields.open()
        for f in fields:
            if f.f_field_name.value.lower() != 'deleted':
                result[f.f_field_name.value] = None
    return result

def server_get_task_dict(task):

    def get_children(items, id_value, type_id, dict, key, parent_id, item_fields):
        childs = {}
        if type_id in (consts.TASK_TYPE, consts.ITEMS_TYPE,
            consts.TABLES_TYPE, consts.REPORTS_TYPE):
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
    it.set_where(type_id=consts.TASK_TYPE)
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
    get_children(items, task_id, consts.TASK_TYPE, result, 'task', None, item_fields)
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
    result['module'] = get_funcs_info(code, is_server)
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
    module_type = consts.WEB_CLIENT_MODULE
    if is_server:
        module_type = consts.SERVER_MODULE
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
                task.log.exception(error)
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
                task.log.exception(error)
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
                module_info = get_funcs_info(code, is_server)
            else:
                error = task.language('item_with_id_not found') % item_id
        except Exception as e:
            error = error_message(e)
            task.log.exception(error)
        if is_server:
            set_server_modified(task)
        else:
            set_client_modified(task)
    return {'error': error, 'line': line, 'module_info': module_info}

def set_server_modified(task):
    if task.item_name == 'admin':
        task.app.server_modified = True
    
def set_client_modified(task):
    if task.item_name == 'admin':
        task.app.client_modified = True
    
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
    result = {}
    error = ''
    if file_name == 'project.css':
        file_name = os.path.join('css', 'project.css')
    file_name = os.path.normpath(file_name)
    try:
        file_write(file_name, code)
    except Exception as e:
        error = error_message(e)
        task.log.exception(error_message(e))
    result['error'] = error
    if file_name == 'index.html':
        change_theme(task)
    return result

def server_get_db_options(task, db_type):
    error = ''
    try:
        result = {}
        db_module = get_db_module(db_type)
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
    items.set_where(type_id=consts.TASK_TYPE)
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
    elif type_id == consts.DETAIL_TYPE:
        items.set_where(parent=parent_id)
        items.open()
        for it in items:
            if it.task_id.value and it.id.value != item_id and it.f_item_name.value.upper() == name.upper():
                result = 'There is an item with this name'
                break
    else:
        items = task.sys_items.copy(handlers=False, details=False)
        items.set_where(type_id__ne=consts.DETAIL_TYPE)
        items.open()
        for it in items:
            if it.task_id.value and it.id.value != item_id and it.f_item_name.value.upper() == name.upper():
                result = 'There is an item with this name'
                break
    return result

def server_create_task(task):
    init_task_attr(task)
    fields = task.sys_fields.copy(handlers=False)
    fields.open()
    for f in fields:
        if f.f_db_field_name.value:
            f.edit()
            f.f_db_field_name.value = task.task_db_module.identifier_case(f.f_db_field_name.value)
            f.post()
    fields.apply()
    task.app.create_task()

def get_lookup_list(task, list_id):
    lists = task.sys_lookup_lists.copy()
    lists.set_where(id=list_id)
    lists.open()
    return json.loads(lists.f_lookup_values_text.value)

def change_theme(task):
    rlist = []
    prefix = ''
    theme = consts.THEME_FILE[consts.THEME]
    for t in consts.THEME_FILE:
        if t and t != theme:
            rlist.append((t, theme))
    if consts.SMALL_FONT:
        rlist.append(('jam.css', 'jam12.css'))
    else:
        rlist.append(('jam12.css', 'jam.css'))
    file_name = os.path.join(task.work_dir, 'index.html')
    content = file_read(file_name)
    for r1, r2 in rlist:
        content = content.replace(prefix + r1, prefix + r2)
    file_write(file_name, content)

def server_lang_modified(task):
    consts.read_language()
    change_language(task)

def do_on_apply_param_changes(item, delta, params):
    task = item.task
    language = consts.LANGUAGE
    debugging = consts.DEBUGGING
    # single_file_js = consts.SINGLE_FILE_JS
    # compressed_js = consts.COMPRESSED_JS
    theme = consts.THEME
    small_font = consts.SMALL_FONT

    if item.item_name == 'sys_params':
        delta.edit()
        delta.f_params_version.value = consts.PARAMS_VERSION + 1
        delta.post()

    sql = delta.apply_sql()
    result = item.task.execute(sql)

    consts.read_settings()
    task.app.save_build_id()

    # if compressed_js != consts.COMPRESSED_JS:
    #     set_client_modified(task)
    # if single_file_js != consts.SINGLE_FILE_JS:
    #     set_client_modified(task)
    #     set_server_modified(task)

    if language != consts.LANGUAGE:
        server_lang_modified(task)
    if theme != consts.THEME or small_font != consts.SMALL_FONT:
        change_theme(task)

    task.ignore_change_ip = consts.IGNORE_CHANGE_IP
    set_client_modified(task)
    set_server_modified(task)
    return result

def init_fields_next_id(task):
    con = task.connect()
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
    connection = task.task_db_module.connect(task.task_db_database, task.task_db_user,
        task.task_db_password, task.task_db_host, task.task_db_port,
        task.task_db_encoding, task.task_db_server)
    try:
        tables = task.task_db_module.get_table_names(connection)
        tables = [t.strip() for t in tables]
        ex_tables = task.select('SELECT F_TABLE_NAME FROM SYS_ITEMS')
        ex_tables = [t[0].upper() for t in ex_tables if t[0]]
        result = [t for t in tables if not t.upper() in ex_tables]
        result.sort()
    except Exception as x:
        task.log.exception(error_message(x))
        result = []
    finally:
        connection.close()
    return result

def server_import_table(task, table_name):
    connection = task.task_db_module.connect(task.task_db_database, task.task_db_user,
        task.task_db_password, task.task_db_host, task.task_db_port,
        task.task_db_encoding, task.task_db_server)
    try:
        result = task.task_db_module.get_table_info(connection, table_name, task.task_db_database)
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
    return task.task_db_module.identifier_case(name)

def get_new_table_name(task, var_name):
    db_module = task.task_db_module
    copy = task.sys_items.copy(handlers=False, details=False)
    copy.set_where(type_id=consts.TASK_TYPE)
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
        items.set_where(type_id=consts.TASK_TYPE)
        items.open(fields = ['id', 'type_id', 'f_item_name'])
        task_id = items.id.value
        task_name = items.f_item_name.value

        items = task.sys_items.copy()
        items.open(open_empty=True, fields = ['id', 'parent', 'task_id', \
            'type_id', 'f_name', 'f_item_name', 'f_table_name', \
            'f_gen_name', 'f_primary_key'])

        sys_group = None
        params = task.sys_params.copy()
        params.open(fields=['id', 'f_sys_group', 'f_history_item', 'f_lock_item'])

        sys_group = params.f_sys_group.value
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
            items.type_id.value = consts.ITEMS_TYPE
            items.f_name.value = task.language('system_group')
            items.f_item_name.value = check_item_name('system')
            items.f_index.value = '999999'
            items.post()
            items.apply()
            params.edit()
            params.f_sys_group.value = items.id.value
            params.post()
            params.apply()
            sys_group = items.id.value
        sys_group_name = items.f_name.value

        if field_name == 'f_history_item':
            name = 'History'
            item_name = check_item_name('history')
            fields = consts.HISTORY_FIELDS
            index_fields = consts.HISTORY_INDEX_FIELDS
            param_field = 'f_history_item'
            table_name, gen_name = get_new_table_name(task, item_name)
            gen_name = None
            sys_id = 1
        elif field_name == 'f_lock_item':
            name = 'Locks'
            item_name = check_item_name('locks')
            fields = consts.LOCKS_FIELDS
            index_fields = consts.LOCKS_INDEX_FIELDS
            param_field = 'f_lock_item'
            table_name, gen_name = get_new_table_name(task, item_name)
            sys_id = 2
        items.open(open_empty=True)
        items.append()
        items.parent.value = sys_group
        items.task_id.value = task_id
        items.type_id.value = consts.ITEM_TYPE
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

        params.edit()
        params.field_by_name(param_field).value = items.id.value
        params.post()
        params.apply()
    except Exception as e:
        error = 'While creating an item the following error was raised: %s' % e
        task.log.exception(error)
    if not error:
        result = 'The %s item has been created in the %s group. The Application builder will be reloaded.' % \
            (sys_item_name, sys_group_name)
        set_server_modified(task)
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
    db_module = task.task_db_module
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
    db_module = task.task_db_module
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

def get_table_fields(item, fields, delta_fields=None):

    def field_dict(field):
        if not field.f_master_field.value:
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
            if not field.f_master_field.value:
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
    parent_fields.set_where(owner_rec_id=fields.owner.parent.value)
    parent_fields.open()
    result = field_info(parent_fields) + field_info(fields)
    if delta_fields:
        for field in delta_fields:
            if not field.f_master_field.value:
                if field.record_status == consts.RECORD_INSERTED:
                    dic = field_dict(field)
                    if dic:
                        result.append(dic)
                if field.record_status == consts.RECORD_DELETED:
                    field_info = find_field(result, field.id.value)
                    if field_info:
                        result.remove(field_info)
                elif field.record_status == consts.RECORD_MODIFIED:
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
            elif field.f_master_field.value and field.record_status == consts.RECORD_MODIFIED:
                field_info = find_field(result, field.id.value)
                if field_info and not field_info['master_field']:
                    result.remove(field_info)
    return result

def item_children(task, item_id):
    items = task.sys_items.copy()
    items.set_where(parent=item_id)
    items.open()
    return items

def get_system_fields(item):
    result = []
    atts = ['f_primary_key', 'f_deleted_flag', 'f_record_version', 'f_master_id', 'f_master_rec_id']
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
    if type_id in (consts.ITEM_TYPE, consts.TABLE_TYPE) and \
        delta.details.sys_fields.record_count():
        item = task.sys_items.copy()
        item.set_where(id=item_id)
        item.open()
        system_fields = get_system_fields(item)

        fields = task.sys_fields.copy()
        fields.set_where(owner_rec_id__in=[item_id, item.parent.value])
        fields.open()
        item.load_interface()
        if delta.record_status == consts.RECORD_INSERTED:
            for field in fields:
                if field.owner_rec_id.value == item.parent.value:
                    if not field.f_field_name.value in system_fields:
                        if type(item._view_list) is list:
                            item._view_list.append([field.id.value, False, False, False])
                        if type(item._edit_list) is list:
                            item._edit_list.append([field.id.value])

        for d in delta.details.sys_fields:
            if d.record_status in [consts.RECORD_INSERTED, consts.RECORD_DELETED]:
                field_name = d.f_field_name.value
                if fields.locate('f_field_name', field_name):
                    if d.record_status == consts.RECORD_INSERTED:
                        if not field_name in system_fields:
                            if type(item._view_list) is list:
                                item._view_list.append([fields.id.value, False, False, False])
                            if type(item._edit_list) is list:
                                item._edit_list.append([fields.id.value])
                    elif d.record_status == consts.RECORD_DELETED:
                        if type(item._view_list) is list:
                            item._view_list = delete_id_from_list(item._view_list, fields.id.value)
                        if type(item._edit_list) is list:
                            item._edit_list = delete_id_from_list(item._edit_list, fields.id.value)
                        item._order_list = delete_id_from_list(item._order_list, fields.id.value)
        item.store_interface()

def change_item_sql(item, old_fields, new_fields):
    return item.change_table_sql(item.task.task_db_type, old_fields, new_fields)

def update_table(delta):
    if delta.f_virtual_table.value or \
        delta.type_id.value in (consts.ITEMS_TYPE, consts.TABLES_TYPE, consts.REPORTS_TYPE):
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
        if delta.type_id.value in (consts.ITEM_TYPE, consts.TABLE_TYPE):
            db_type = item.task.task_db_type
            fields = new_fields
            if not fields:
                fields = get_table_fields(delta, delta.details.sys_fields)
            sql = delta.create_table_sql(db_type, delta.f_table_name.value, \
                fields, delta.f_gen_name.value, foreign_fields=foreign_fields)
            return sql

def items_execute_insert(item, delta, manual_update):
    sql = items_insert_sql(item, delta, manual_update)
    if sql:
        error = execute_db(item.task, delta.task_id.value, sql)
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
        if delta.type_id.value in (consts.ITEMS_TYPE, consts.TABLES_TYPE,
            consts.ITEM_TYPE, consts.TABLE_TYPE) and \
            delta.details.sys_fields.record_count():
            it = item.copy()
            it.set_where(id=delta.id.value)
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
        error = execute_db(item.task, delta.task_id.value, sql)
        if error:
            raise Exception(item.task.language('error_modifying_table') % error)
    sql = delta.apply_sql()
    result = item.task.execute(sql)
    update_interface(delta, delta.type_id.value, delta.id.value)
    return result

def items_delete_sql(item, delta, manual_update=False):
    if update_table(delta) and not manual_update:
        if delta.type_id.value in (consts.ITEM_TYPE, consts.TABLE_TYPE):
            sql = delta.delete_table_sql(item.task.task_db_type)
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
        error = execute_db(item.task, delta.task_id.value, sql)
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
    set_server_modified(item.task)
    roles_changed(item)
    return result

def do_on_apply_changes(item, delta, params):
    sql = delta.apply_sql()
    result = item.task.execute(sql)
    set_server_modified(item.task)
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
    details.set_where(table_id=id_value)
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
    details.set_where(parent=id_value)
    details.open()
    if details.record_count():
        mess = "Can't delete item: item contains details"
        return mess

def server_load_interface(item, id_value):
    item = item.copy()
    item.set_where(id=id_value)
    item.open(fields=['id', 'f_info'])
    item.load_interface()
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
    item.store_interface()
    set_server_modified(item.task)

def create_detail_index(task, table_id):
    items = task.sys_items.copy()
    items.set_where(type_id=consts.TASK_TYPE)
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
            field_list = i.load_index_fields(i.f_fields_list.value)
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
        items.type_id.value = consts.DETAIL_TYPE
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
        table.load_interface()
        items._view_list = table._view_list
        items._edit_list = table._edit_list
        items._order_list = table._order_list
        items._reports_list = []
        items.store_interface()
        items.apply()
        init_priviliges(items, items.id.value)
        try:
            create_detail_index(items.task, table_id)
        except Exception as e:
            item.log.exception(error_message(e))
    set_server_modified(item.task)

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

    item.load_interface()
    item._view_list = convert_details(item._view_list, 'view_detail', detail_list)
    item._edit_list = convert_details(item._edit_list, 'edit_details', detail_list)
    item.store_interface()

###############################################################################
#                                 sys_fields                                  #
###############################################################################

def server_can_delete_field(item, id_value):
    item = item.copy()
    item.set_where(id=id_value)
    item.open()

    item_type_id = item.task.sys_items.field_by_id(item.owner_rec_id.value, 'type_id')
    if item_type_id in (consts.ITEMS_TYPE, consts.TABLES_TYPE):
        if not server_group_is_empty(item, item.owner_rec_id.value):
            mess = "Can't delete the field: the group contains items."
            return mess

    field_id = item.id.value
    fields = item.task.sys_fields.copy()
    fields.set_where(task_id=item.task_id.value)
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
    indices.set_where(owner_rec_id=item.owner_rec_id.value)
    indices.open()
    ind_list = []
    for ind in indices:
        if ind.f_foreign_index.value:
            if ind.f_foreign_field.value == field_id:
                ind_list.append(ind.f_index_name.value)
        else:
            field_list = ind.load_index_fields(ind.f_fields_list.value)
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
    filters.set_where(owner_rec_id=item.owner_rec_id.value)
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
    items.set_where(id=delta.owner_rec_id.value)
    items.open()
    it_fields = items.details.sys_fields
    it_fields.open()
    fields = get_table_fields(items, it_fields)
    new_fields = list(fields)
    return items.recreate_table_sql(SQLITE, fields, new_fields, delta)

def indices_insert_sql(item, delta, table_name=None, new_fields=None, manual_update=False, foreign_key_dict=None):
    if not manual_update and update_index(delta):
        if not table_name:
            table_name = delta.task.sys_items.field_by_id(delta.owner_rec_id.value, 'f_table_name')
        db_type = item.task.task_db_type
        if db_type == SQLITE and delta.f_foreign_index.value:
            if not new_fields:
                return change_foreign_index(delta)
        else:
            return delta.create_index_sql(db_type, table_name, new_fields=new_fields, foreign_key_dict=foreign_key_dict)

def indices_execute_insert(item, delta, manual_update):
    sql = indices_insert_sql(item, delta, manual_update=manual_update)
    if sql:
        error = execute_db(item.task, delta.task_id.value, sql)
        if error:
            raise Exception(item.task.language('error_creating_index') % (delta.f_index_name.value.upper(), error))
    sql = delta.apply_sql()
    return item.task.execute(sql)

def indices_delete_sql(item, delta, manual_update=False):
    if not manual_update and update_index(delta):
        db_type = item.task.task_db_type
        if db_type == SQLITE and delta.f_foreign_index.value:
            return change_foreign_index(delta)
        else:
            return delta.delete_index_sql(db_type)

def indices_execute_delete(item, delta, manual_update):
    sql = indices_delete_sql(item, delta, manual_update)
    if sql:
        error = execute_db(item.task, delta.task_id.value, sql)
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
    return item.store_index_fields(dest_list)

def server_load_index_fields(item, value):
    return item.load_index_fields(value)

###############################################################################
#                                  sys_roles                                  #
###############################################################################

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
#                               sys_lookup_lists                              #
###############################################################################

def lookup_lists_apply_changes(item, delta, params):
    set_server_modified(item.task)

###############################################################################
#                                  sys_langs                                  #
###############################################################################

def add_lang(item, lang_id, language, country, name, abr, rtl, copy_lang):
    langs.add_lang(item.task, lang_id, language, country, name, abr, rtl, copy_lang)

def save_lang_field(item, lang_id, field_name, value):
    langs.save_lang_field(item.task, lang_id, field_name, value)

def get_lang_translation(item, lang1, lang2):
    return langs.get_translation(item.task, lang1, lang2)

def save_lang_translation(item, lang_id, key_id, value):
    langs.save_translation(item.task, lang_id, key_id, value)

def add_key(item, key):
    return langs.add_key(item.task, key)

def del_key(item, key_id):
    return langs.del_key(item.task, key_id)

def export_lang(item, lang_id, host):
    return langs.export_lang(item.task, lang_id, host)

def import_lang(item, file_path):
    return langs.import_lang(item.task, os.path.join(item.task.work_dir, file_path))

def get_alignment(data_type, item=None, lookup_values=None):
    if (data_type == consts.INTEGER) or (data_type == consts.FLOAT) or (data_type == consts.CURRENCY):
        result = consts.ALIGN_RIGHT
    elif (data_type == consts.DATE) or (data_type == consts.DATETIME):
        result = consts.ALIGN_CENTER
    else:
        result = consts.ALIGN_LEFT
    if item or lookup_values:
        result = consts.ALIGN_LEFT
    return result

def remove_comments(text, is_server, comment_sign):
    result = []
    if text:
        comment = False
        for line in text.splitlines(True):
            if comment:
                pos = line.find('*/')
                if pos != -1:
                    comment = False
                    line = pos * ' ' + '*/' + line[pos + 2:]
                else:
                    line = ' ' * len(line)
            else:
                pos = line.find(comment_sign)
                if pos != -1:
                    line = line[0:pos] + comment_sign + (len(line) - len(line[0:pos] + comment_sign) - 1) * ' ' + '\n'
                if not is_server:
                    pos = line.find('/*')
                    if pos != -1:
                        end = line.find('*/', pos + 2)
                        if end != -1:
                            line = line[0:pos] + '/*' + ' ' * (end - pos - 2) + line[end:]
                        else:
                            comment = True
                            line = line[0:pos+2] + ' ' * (len(line) - (pos + 2))
            result.append(line)
        result = ''.join(result)
    return result

def get_funcs_info(text, is_server):

    def check_line(line, comment_sign, func_literal):
        func_name = ''
        trimed_line = line.strip()
        if len(trimed_line) > 0:
            if not (trimed_line[:len(comment_sign)] == comment_sign):
                for fl in func_literal:
                    indent = line.find(fl)
                    if indent >= 0:
                        def_end = line.find('(')
                        if def_end == -1 and is_server and fl == 'class':
                            def_end = line.find(':')
                        if def_end > indent:
                            func_name = line[indent+len(fl):def_end].strip()
                            if func_name:
                                return (indent, func_name)

    def add_child_funcs(i, parent_indent, parent_dic, parent_key):
        dic = {}
        parent_dic[parent_key] = dic
        if i < len(funcs_list):
            cur_indent = funcs_list[i][0]
        else:
            return
        cur_indent = -1
        child_indent = -1
        while i < len(funcs_list):
            (indent, func_name) = funcs_list[i]
            if cur_indent == -1:
                cur_indent = indent
            if indent == cur_indent:
                dic[func_name] = None
                cur_func_name = func_name
            elif indent > cur_indent:
                if child_indent == -1:
                    child_indent = indent
                if not indent > child_indent:
                    i = add_child_funcs(i, indent, dic, cur_func_name)
            elif indent < cur_indent:
                return i - 1
            i += 1
        return i

    funcs = {}
    funcs['result'] = {}
    if text:
        if is_server:
            comment_sign = '#'
            func_literal = ['def', 'class']
        else:
            comment_sign = '//'
            func_literal = ['function']
        text = remove_comments(text, is_server, comment_sign)
        lines = text.splitlines()
        funcs_list = []
        for i, line in enumerate(lines):
            res = check_line(line, comment_sign, func_literal)
            if res:
                funcs_list.append(res)
        add_child_funcs(0, -1, funcs, 'result')
    return funcs['result']

def prepare_files(task):
    from shutil import rmtree, copy

    folder = os.path.join(task.work_dir, 'jam_files')
    if os.path.exists(folder):
        rmtree(folder)
    os.makedirs(folder)

    builder_file = os.path.join(folder, 'builder.html')
    copy(os.path.join(task.work_dir, 'index.html'), builder_file)
    f = file_read(builder_file)
    f = f.replace('css/project.css', 'jam/css/admin.css')
    f = f.replace('task.load(', 'task.ID = 0; task.load(')
    file_write(builder_file, f)

    css_folder = os.path.join(folder, 'css')
    os.makedirs(css_folder)
    copy(os.path.join(task.work_dir, 'css', 'project.css'), os.path.join(css_folder, 'admin.css'))

    admin_folder = os.path.join(folder, 'admin')
    os.makedirs(admin_folder)

    update_events_code(task.app.admin)

    app_items = task.app.admin.sys_items.copy(handlers=False)
    app_items.set_where(type_id=consts.TASK_TYPE)
    app_items.open(fields=['f_server_module'])
    file_write(os.path.join(admin_folder, 'builder.py'), app_items.f_server_module.value)

    js_folder = os.path.join(folder, 'js')
    os.makedirs(js_folder)
    js_file = os.path.join(js_folder, 'admin.js')
    copy(os.path.join(task.work_dir, 'js', task.item_name + '.js'), js_file)
    f = file_read(js_file)
    f = f.replace('events1 ', 'events0 ')
    f = f.replace('Events1', 'Events0')
    file_write(js_file, f)

    restore_caption_keys(task)
    try:
        info = task.get_info(True)
        info['name'] = 'admin'
        info['id'] = 0
        info['js_filename'] = 'admin.js'
        info = json.dumps(info)
        file_write(os.path.join(admin_folder, 'builder_structure.info'), info)
    finally:
        change_language(task)
    return True

def register_events(task):
    task.register(server_check_connection)
    task.register(server_set_task_name)
    task.register(server_set_project_langage)
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
    task.register(server_lang_modified)
    task.register(get_new_table_name)
    task.register(create_system_item)
    task.register(create_detail_index)
    task.register(prepare_files)
    task.sys_params.on_apply = do_on_apply_param_changes
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
    task.sys_roles.sys_privileges.on_open = privileges_table_get_select
    task.sys_privileges.on_open = privileges_open
    task.sys_roles.register(roles_changed)
    task.sys_lookup_lists.on_apply = lookup_lists_apply_changes
    task.sys_langs.register(get_lang_translation)
    task.sys_langs.register(save_lang_field)
    task.sys_langs.register(save_lang_translation)
    task.sys_langs.register(add_lang)
    task.sys_langs.register(add_key)
    task.sys_langs.register(del_key)
    task.sys_langs.register(export_lang)
    task.sys_langs.register(import_lang)
