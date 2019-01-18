#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import distutils.core
import sqlite3
import jam
from base64 import b64encode

project_dir = os.getcwd()
jam_project_dir = os.path.join(os.path.dirname(jam.__file__), 'project')
distutils.dir_util.copy_tree(jam_project_dir, project_dir, preserve_mode=0)
os.chmod(os.path.join(project_dir, 'server.py'), 0o777)

dirs = ['js', 'reports', os.path.join('static', 'reports')]
for dir in dirs:
    path = os.path.join(project_dir, dir)
    if not os.path.isdir(path):
        os.makedirs(path)

key = b64encode(os.urandom(20)).decode('utf-8')

con = sqlite3.connect(os.path.join(project_dir, 'admin.sqlite'))
cursor = con.cursor()
cursor.execute("UPDATE SYS_PARAMS SET F_LANGUAGE=NULL, F_SECRET_KEY='%s'" % key)
cursor.execute("UPDATE SYS_TASKS SET F_NAME=NULL, F_ITEM_NAME=NULL, \
    F_MANUAL_UPDATE=NULL, F_DB_TYPE=NULL, F_ALIAS=NULL, F_LOGIN=NULL, \
    F_PASSWORD=NULL, F_HOST=NULL, F_PORT=NULL, F_ENCODING=NULL")
con.commit()
con.close()
