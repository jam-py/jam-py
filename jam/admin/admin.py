import os
import json
import sqlite3

from ..common import consts, error_message, file_read, file_write
from ..server_classes import AdminTask, Group
from .builder import on_created, init_task_attr
from jam.db.db_modules import SQLITE, get_db_module
import jam.langs as langs

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
    update_admin_fields(task)
    consts.read_settings()
    consts.MAINTENANCE = False
    consts.write_settings(['MAINTENANCE'])
    consts.read_language()
    on_created(task)

def create_admin(app):
    if os.path.exists(os.path.join(app.work_dir, '_admin.sqlite')):
        os.rename(os.path.join(app.work_dir, '_admin.sqlite'), \
            os.path.join(app.work_dir, 'admin.sqlite'))
    task = AdminTask(app, 'admin', 'Administrator', '', SQLITE,
        db_database=os.path.join(app.work_dir, 'admin.sqlite'))
    app.admin = task
    task.secret_key = read_secret_key(task)
    init_admin(task)
    return task

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
    db_module = task.task_db_module
    db_type = task.task_db_type
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
    db_type = task.task_db_type
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
