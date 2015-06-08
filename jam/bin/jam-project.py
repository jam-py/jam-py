#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import distutils.core
import sqlite3
import jam

project_dir = os.getcwd()
jam_project_dir = os.path.join(os.path.dirname(jam.__file__), 'project')
distutils.dir_util.copy_tree(jam_project_dir, project_dir)
for file_name in os.listdir(project_dir):
    name, ext = os.path.splitext(file_name)
    if ext == '.py':
        os.chmod(file_name, 0o777)
reports_path = os.path.join(project_dir, 'static', 'reports')
if not os.path.isdir(reports_path):
    os.makedirs(reports_path)

con = sqlite3.connect(os.path.join(project_dir, 'admin.sqlite'))
cursor = con.cursor()
cursor.execute('UPDATE SYS_PARAMS SET F_LANGUAGE=NULL')
cursor.execute('UPDATE SYS_TASKS SET F_NAME=NULL, F_ITEM_NAME=NULL, \
    F_MANUAL_UPDATE=NULL, F_DB_TYPE=NULL, F_ALIAS=NULL, F_LOGIN=NULL, \
    F_PASSWORD=NULL, F_HOST=NULL, F_PORT=NULL, F_ENCODING=NULL')
con.commit()
con.close()
