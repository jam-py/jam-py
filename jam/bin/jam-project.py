#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import distutils.core
import sqlite3
import jam
from jam.interface import select_language
from jam.client_classes import AdminTask

lang = select_language()
if lang:
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
    cursor.execute('UPDATE SYS_PARAMS SET F_LANGUAGE=%s' % lang)
    cursor.execute('UPDATE SYS_TASKS SET F_DB_TYPE=NULL, F_DB_NAME=NULL')
    con.commit()

    AdminTask().run()
