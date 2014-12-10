#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from os.path import exists

from jam.interface import select_language, question, YES
import jam.common

adm_file = 'admin.py'
adm_code = \
'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from jam.client_classes import AdminTask

def main(url=None):
    client = AdminTask(url)
    client.run()

if __name__ == '__main__':
    try:
        url = sys.argv[1]
    except:
        url = None
    main(url)
'''

main_file = 'main.py'
main_code = \
'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jam.common

def main():
    from jam.client_classes import ClientTask

    client = ClientTask()
    client.run()

if __name__ == '__main__':
    jam.common.URL = None
    main()
'''

server_file = 'server.py'
server_code = \
'''!/usr/bin/env python
# -*- coding: utf-8 -*-


if __name__ == '__main__':
    import jam.webserver
    from jam.server import get_request
    jam.webserver.run(get_request)
'''

client_file = 'client.py'
client_code = \
'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from jam.client_classes import ClientTask

def main(url):
    client = ClientTask(url)
    client.run()

if __name__ == '__main__':
    try:
        url = sys.argv[1]
    except:
        url = '127.0.0.1:8080'
    main(url)
'''

def create_file(file_name, code):
    with open(file_name, 'w') as f:
        f.write(code)
    os.chmod(file_name, 0o777)

def create_adm_db():
    for group in adm.items:
        for item in group.items:
            sql = item.create_table_sql(adm.db_type, item.table_name)
            adm.execute(sql)

def del_if_exists(file_name):
    if exists(file_name):
        os.remove(file_name)

if exists(adm_file) or exists(main_file) or \
    exists(server_file) or exists(client_file):
    if question(None, u'There are project files in the directory. They will be overwritten. Continue anyway?') == YES:
        del_if_exists('admin.sqlite')
        del_if_exists(adm_file)
        del_if_exists(main_file)
        del_if_exists(server_file)
        del_if_exists(client_file)
    else:
        sys.exit(0)

lang = select_language()
if lang:
    jam.common.new_project_language = lang
    import jam.adm_server
    adm = jam.adm_server.task

    create_file(adm_file, adm_code)
    create_file(main_file, main_code)
    create_file(server_file, server_code)
    create_file(client_file, client_code)
    create_adm_db()

    reload(jam.adm_server)
    import admin
    admin.main()
