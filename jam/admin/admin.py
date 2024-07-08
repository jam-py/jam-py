import os
import json
import sqlite3

from ..common import consts, error_message, file_read, file_write
from ..items import AdminTask, Group
from jam.db.databases import get_database
import jam.langs as langs

# task in this module is admin (Application builder) task

class FieldInfo(object):
    def __init__(self, field, item):
        self.id = field.id.value
        self.field_name = field.f_db_field_name.value
        self.data_type = field.f_data_type.value
        self.size = field.f_size.value
        self.default_value = field.f_default_value.data
        self.master_field = field.f_master_field.value
        self.calc_item = field.f_calc_item.value
        self.primary_key = field.id.value == item.f_primary_key.value

def create_items(task):
    info = file_read(os.path.join(task.app.jam_dir, 'admin', 'builder_structure.info'))
    info = json.loads(info)
    task.set_info(info)

def read_secret_key(task):
    result = None
    con = task.connect()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT F_SECRET_KEY FROM SYS_PARAMS')
        rec = cursor.fetchall()
        result = rec[0][0]
    except:
        pass
    finally:
        con.close()
    if result is None:
        result = ''
    return result

def check_version(task):
    pass

def init_admin(task):
    check_version(task)
    langs.update_langs(task)
    create_items(task)
    update_admin_db(task)
    consts.read_settings()
    consts.MAINTENANCE = False
    consts.write_settings(['MAINTENANCE'])
    consts.read_language()
    from .builder import on_created
    on_created(task)
    from .upgrade import version7_upgrade
    version7_upgrade(task)

def create_admin(app):
    if os.path.exists(os.path.join(app.work_dir, '_admin.sqlite')):
        os.rename(os.path.join(app.work_dir, '_admin.sqlite'), \
            os.path.join(app.work_dir, 'admin.sqlite'))
    task = AdminTask(app, 'admin', 'Administrator', consts.SQLITE,
        db_database=os.path.join(app.work_dir, 'admin.sqlite'))
    app.admin = task
    task.secret_key = read_secret_key(task)
    init_admin(task)
    return task

def connect_task_db(task):
    return task.task_db_module.connect(task.task_db_info)

def valid_delta_type(delta):
    return not delta.f_virtual_table.value and \
        delta.type_id.value in (consts.ITEM_TYPE, consts.TABLE_TYPE)

def get_item_fields(item, fields, delta_fields=None):

    def field_info(field):
        if not field.f_master_field.value and not field.f_calc_item.value:
            return FieldInfo(field, item)

    def fields_info(fields):
        result = []
        for field in fields:
            info = field_info(field)
            if info:
                result.append(info)
        return result

    def find_field(fields_info, field_id):
        for field in fields_info:
            if field.id == field_id:
                return field

    task = item.task
    result = []
    result = fields_info(fields)
    if delta_fields:
        for field in delta_fields:
            if not field.f_master_field.value and not field.f_calc_item.value:
                if field.change_log.record_status == consts.RECORD_INSERTED:
                    info = field_info(field)
                    if info:
                        result.append(info)
                if field.change_log.record_status == consts.RECORD_DELETED:
                    info = find_field(result, field.id.value)
                    if info:
                        result.remove(info)
                elif field.change_log.record_status == consts.RECORD_MODIFIED:
                    info = find_field(result, field.id.value)
                    if info:
                        info.id = field.id.value
                        info.field_name = field.f_db_field_name.value
                        info.data_type = field.f_data_type.value
                        info.size = field.f_size.value
                        info.default_value = field.f_default_value.data
                    else:
                        info = field_info(field)
                        if info:
                            result.append(info)
            elif field.change_log.record_status == consts.RECORD_MODIFIED:
                info = find_field(result, field.id.value)
                if info and not info.master_field and not info.calc_item:
                    result.remove(info)
    return result

def recreate_table(delta, old_fields, new_fields, comp=None, fk_delta=None):

    def foreign_key_dict(ind):
        fields = ind.task.sys_fields.copy()
        fields.set_where(id=ind.f_foreign_field.value)
        fields.open()
        dic = {}
        dic['key'] = fields.f_db_field_name.value
        ref_id = fields.f_object.value
        items = delta.task.sys_items.copy()
        items.set_where(id=ref_id)
        items.open()
        dic['ref'] = items.f_table_name.value
        primary_key = items.f_primary_key.value
        fields.set_where(id=primary_key)
        fields.open()
        dic['primary_key'] = fields.f_db_field_name.value
        return dic

    def get_foreign_fields():
        indices = delta.task.sys_indices.copy()
        indices.set_where(owner_rec_id=delta.id.value)
        indices.open()
        del_id = None
        if fk_delta and (fk_delta.rec_modified() or fk_delta.rec_deleted()):
            del_id = fk_delta.id.value
        result = []
        for ind in indices:
            if ind.f_foreign_index.value:
                if not del_id or ind.id.value != del_id:
                    result.append(foreign_key_dict(ind))
        if fk_delta and (fk_delta.rec_inserted() or fk_delta.rec_modified()):
            result.append(foreign_key_dict(fk_delta))
        return result

    def create_indices_sql():
        indices = delta.task.sys_indices.copy()
        indices.set_where(owner_rec_id=delta.id.value)
        indices.open()
        result = []
        for ind in indices:
            if not ind.f_foreign_index.value:
                result.append(indices_insert_query(ind, delta.f_table_name.value, new_fields=new_fields))
        return result

    def find_field(fields, id_value):
        for f in fields:
            if f.id == id_value:
                return True

    def prepare_fields():
        for f in list(new_fields):
            if not find_field(old_fields, f.id):
                new_fields.remove(f)
        for f in list(old_fields):
            if not find_field(new_fields, f.id):
                old_fields.remove(f)

    connection = connect_task_db(delta.task)
    cursor = connection.cursor()
    db = delta.task.task_db_module
    table_name = delta.f_table_name.value
    result = []
    cursor.execute('PRAGMA foreign_keys=off')
    print('ALTER TABLE "%s" RENAME TO Temp' % table_name)
    cursor.execute('ALTER TABLE "%s" RENAME TO Temp' % table_name)
    try:
        foreign_fields = get_foreign_fields()
        sql = db.create_table(table_name, new_fields, foreign_fields=foreign_fields)
        cursor.execute(sql)
        prepare_fields()
        old_field_list = ['"%s"' % field.field_name for field in old_fields]
        print (old_field_list)
        new_field_list = ['"%s"' % field.field_name for field in new_fields]
        print (new_field_list)
        print ('INSERT INTO "%s" (%s) SELECT %s FROM Temp' % \
            (table_name, ', '.join(new_field_list), ', '.join(old_field_list)))
        cursor.execute('INSERT INTO "%s" (%s) SELECT %s FROM Temp' % \
            (table_name, ', '.join(new_field_list), ', '.join(old_field_list)))
    except Exception as e:
        delta.log.exception(error_message(e))
        cursor.execute('DROP TABLE IF EXISTS "%s"' % table_name)
        cursor.execute('ALTER TABLE Temp RENAME TO "%s"' % table_name)
        cursor.execute('PRAGMA foreign_keys=on')
        connection.commit()
        raise
    cursor.execute('DROP TABLE Temp')
    cursor.execute('PRAGMA foreign_keys=on')
    ind_sql = create_indices_sql()
    for sql in ind_sql:
        cursor.execute(sql)
    connection.commit()
    return result

def change_item_query(delta, old_fields, new_fields):

    def recreate(comp):
        for key, (old_field, new_field) in comp.items():
            if old_field and new_field:
                if old_field.field_name != new_field.field_name:
                    return True
                elif db.default_text(old_field) != db.default_text(new_field):
                    return True
            elif old_field and not new_field:
                return True

    db = delta.task.task_db_module
    table_name = delta.f_table_name.value
    result = []
    comp = {}
    for field in old_fields:
        comp[field.id] = [field, None]
    for field in new_fields:
        if comp.get(field.id):
            comp[field.id][1] = field
        else:
            if field.id:
                comp[field.id] = [None, field]
            else:
                comp[field.field_name] = [None, field]
    if db.db_type == consts.SQLITE and recreate(comp):
        recreate_table(delta, old_fields, new_fields, comp=comp)
        return
    else:
        for key, (old_field, new_field) in comp.items():
            if old_field and not new_field:
                result.append(db.del_field(table_name, old_field))
        for key, (old_field, new_field) in comp.items():
            if old_field and new_field:
                if (old_field.field_name != new_field.field_name) or \
                    (db.FIELD_TYPES[old_field.data_type] != db.FIELD_TYPES[new_field.data_type]) or \
                    (old_field.default_value != new_field.default_value) or \
                    (old_field.size != new_field.size):
                    sql = db.change_field(table_name, old_field, new_field)
                    if type(sql) in (list, tuple):
                        result += sql
                    else:
                        result.append(sql)
        for key, (old_field, new_field) in comp.items():
            if not old_field and new_field:
                result.append(db.add_field(table_name, new_field))
    return result

def insert_item_query(delta, manual_update=False, new_fields=None, foreign_fields=None):
    if not manual_update and valid_delta_type(delta):
        fields = new_fields
        if not fields:
            fields = get_item_fields(delta, delta.sys_fields)
        return delta.task.task_db_module.create_table(delta.f_table_name.value, \
        fields, delta.f_gen_name.value, foreign_fields)

def update_item_query(delta, manual_update=None):
    if not manual_update and valid_delta_type(delta) and delta.sys_fields.rec_count:
        item = delta.copy()
        item.set_where(id=delta.id.value)
        item.open()
        item.sys_fields.open()
        old_fields = get_item_fields(delta, item.sys_fields)
        new_fields = get_item_fields(delta, item.sys_fields, delta.sys_fields)
        return change_item_query(delta, old_fields, new_fields)

def delete_item_query(delta, manual_update=None):
    if not manual_update and valid_delta_type(delta):
        gen_name = None
        if delta.f_primary_key.value:
            gen_name = delta.f_gen_name.value
        return delta.task.task_db_module.drop_table(delta.f_table_name.value, gen_name)

def valid_indices_record(delta):
    items = delta.task.sys_items.copy()
    items.set_where(id=delta.owner_rec_id.value)
    items.open()
    if items.rec_count:
        return not items.f_virtual_table.value
    else:
        return True

def change_foreign_index(delta):
    items = delta.task.sys_items.copy()
    items.set_where(id=delta.owner_rec_id.value)
    items.open()
    it_fields = items.sys_fields
    it_fields.open()
    fields = get_item_fields(items, it_fields)
    new_fields = list(fields)
    recreate_table(items, fields, new_fields, fk_delta=delta)

def create_index(delta, table_name, fields=None, new_fields=None, foreign_key_dict=None):

    def new_field_name_by_id(id_value):
        for f in new_fields:
            if f.id == id_value:
                return f.field_name

    db = delta.task.task_db_module
    index_name = delta.f_index_name.value
    if delta.f_foreign_index.value:
        if foreign_key_dict:
            key = foreign_key_dict['key']
            ref = foreign_key_dict['ref']
            primary_key = foreign_key_dict['primary_key']
        else:
            fields = delta.task.sys_fields.copy()
            fields.set_where(id=delta.f_foreign_field.value)
            fields.open()
            key = fields.f_db_field_name.value
            ref_id = fields.f_object.value
            items = delta.task.sys_items.copy()
            items.set_where(id=ref_id)
            items.open()
            ref = items.f_table_name.value
            primary_key = items.f_primary_key.value
            fields.set_where(id=primary_key)
            fields.open()
            primary_key = fields.f_db_field_name.value
        sql = db.create_foreign_index(table_name, index_name, key, ref, primary_key)
    else:
        index_fields = delta.f_fields_list.value
        desc = ''
        if delta.descending.value:
            desc = 'DESC'
        unique = ''
        if delta.f_unique_index.value:
            unique = 'UNIQUE'
        fields = delta.load_index_fields(index_fields)
        if db.db_type == consts.FIREBIRD:
            if new_fields:
                field_defs = [new_field_name_by_id(field[0]) for field in fields]
            else:
                field_defs = [delta.task.sys_fields.field_by_id(field[0], 'f_db_field_name') for field in fields]
            field_str = '"' + '", "'.join(field_defs) + '"'
        else:
            field_defs = []
            for field in fields:
                if new_fields:
                    field_name = new_field_name_by_id(field[0])
                else:
                    field_name = delta.task.sys_fields.field_by_id(field[0], 'f_db_field_name')
                d = ''
                if field[1]:
                    d = 'DESC'
                field_defs.append('"%s" %s' % (field_name, d))
            field_str = ', '.join(field_defs)
        sql = db.create_index(index_name, table_name, unique, field_str, desc)
    return sql

def indices_insert_query(delta, table_name=None, new_fields=None, manual_update=False, foreign_key_dict=None):
    if not manual_update and valid_indices_record(delta):
        if not table_name:
            table_name = delta.task.sys_items.field_by_id(delta.owner_rec_id.value, 'f_table_name')
        if delta.task.task_db_module.db_type == consts.SQLITE and delta.f_foreign_index.value:
            if not new_fields:
                change_foreign_index(delta)
        else:
            return create_index(delta, table_name, new_fields=new_fields, foreign_key_dict=foreign_key_dict)

def indices_delete_query(delta, table_name=None, manual_update=False):
    if not manual_update and valid_indices_record(delta):
        if delta.task.task_db_module.db_type == consts.SQLITE and delta.f_foreign_index.value:
            change_foreign_index(delta)
        else:
            db = delta.task.task_db_module
            if not table_name:
                table_name = delta.task.sys_items.field_by_id(delta.owner_rec_id.value, 'f_table_name')
            index_name = delta.f_index_name.value
            if delta.f_foreign_index.value:
                return db.drop_foreign_index(table_name, index_name)
            else:
                return db.drop_index(table_name, index_name)

def update_admin_db(task):

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
                    task.db.FIELD_TYPES[field.data_type])
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

    con = task.connect()
    try:
        cursor = con.cursor()
        for group in task.items:
            for item in group.items:
                if item.table_name and not item.master:
                    if check_table_exists(item):
                        check_item_fields(item)
    finally:
        con.close()

def get_privileges(task):
    priv = {}
    r = task.sys_roles.copy()
    r.open()
    privliges = task.sys_privileges.copy()
    privliges.open()
    for r in r:
        priv[r.id.value] = {}
    for p in privliges:
        priv[p.owner_rec_id.value][p.item_id.data] = \
            {
                'can_view': p.f_can_view.value,
                'can_create': p.f_can_create.value,
                'can_edit': p.f_can_edit.value,
                'can_delete': p.f_can_delete.value
            }
    return priv

def get_field_restrictions(task):
    result = {}
    r = task.sys_roles.copy()
    r.open()
    field_restrictions = task.sys_field_privileges.copy()
    field_restrictions.open()
    for r in r:
        result[r.id.value] = {}
    for p in field_restrictions:
        result[p.owner_rec_id.value][p.field.data] = \
            {
                'prohibited': p.f_prohibited.value,
                'read_only': p.f_read_only.value
            }
    return result

def login_user(task, log, password, admin, ip=None, session_uuid=None):
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
    db = task.task_db_module
    indexes = task.sys_indices.copy(handlers=False)
    indexes.open()
    table_names = indexes_get_table_names(indexes)
    sqls = []
    for i in indexes:
        if not (i.f_foreign_index.value and db.db_type == consts.SQLITE):
            table_name = table_names.get(i.owner_rec_id.value)
            if table_name:
                sqls.append(indices_delete_query(i, table_name))
    return sqls

def restore_indexes_sql(task):
    db = task.task_db_module
    indexes = task.sys_indices.copy(handlers=False)
    indexes.open()
    table_names = indexes_get_table_names(indexes)
    sqls = []
    for i in indexes:
        if not (i.f_foreign_index.value and db.db_type == consts.SQLITE):
            table_name = table_names.get(i.owner_rec_id.value)
            if table_name:
                sqls.append(indices_insert_query(i, table_name))
    return sqls
