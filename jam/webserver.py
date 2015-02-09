#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.db_multiprocessing = True

import web
import cPickle
import json
import traceback
from random import randint
import common

urls = (
    '/api(.*)', 'Api',
    '/(.*)', 'Index',
)

web.config.debug = True
app = web.application(urls, globals(), autoreload=False)

class Api:
    def POST(self, name):
        r = {'result': None, 'error': None}
        data = web.data()
        sender_type = data[0]
        data = data[1:]
        if sender_type == '0': #python client
            q = cPickle.loads(data.decode('zlib'))
        elif sender_type == '1': #web client
            q = json.loads(data)

        try:
            method = q['method']
            if method == 'send_request':
                request = q['params'][0]
                user_id = q['params'][1]
                task_id = q['params'][2]
                item_id = q['params'][3]
                params = q['params'][4]
                r['result'] = web.get_request(web.ctx.env, request, user_id, task_id, item_id, params, sender_type == '1')
                if task_id == 0:
                    if request == 'exit' and r['result']:
                        sys.exit(0)
            else:
                r['result'] = None
        except Exception, e:
            print traceback.format_exc()
            r['error'] = e.message

        if sender_type == '0': #python client
            web.header('Content-encoding', 'deflate')
            return cPickle.dumps(r, 2).encode('zlib')
        elif sender_type == '1': #web client
            accepts_gzip = 0
            try:
                if web.ctx.env.get("HTTP_ACCEPT_ENCODING").find("gzip") != -1:
                    accepts_gzip = 1
            except:
                pass
            buff = json.dumps(r, default=common.json_defaul_handler)
            web.header('Content-Type', 'application/json')
            if accepts_gzip:
                buff = common.compressBuf(buff)
                web.header('Content-encoding', 'gzip')
                web.header('Content-Length', str(len(buff)))
                return buff
            else:
                return buff

class Index:
    def GET(self, name):
        content_types = {'js': 'application/javascript', 'css': 'text/css', 'img': 'image/png'}
        path_list = name.split('/')
        file_name = name
        content_type = 'text/html'
        if name:
            if len(path_list) == 2:
                d, f = path_list
                if d in ['css', 'js', 'img']:
                    content_type = content_types[path_list[0]]
                    file_name = os.path.join(*path_list)
        else:
            file_name = 'index.html'
        if file_name and os.path.isfile(file_name):
            with open(os.path.join(file_name), 'rb') as f:
                web.header('Content-Type', content_type)
                web.header('Cache-Control', 'no-cache')
                return f.read()
        else:
            return ''

def run(get_request):
    me = common.SingleInstance()
    web.get_request = get_request
    app.run()

