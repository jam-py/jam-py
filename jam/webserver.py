#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.db_multiprocessing = True

import cPickle
import json
import traceback
try:
    import SimpleHTTPServer
except:
    import SimpleHTTPServer
try:
    import web
except:
    import jam.third_party.web as web

import common

urls = (
    '/api(.*)', 'Api',
    '/ext(.*)', 'Ext',
    '/upload(.*)', 'Upload',
    '/(.*)', 'Index',
)

web.config.debug = True
app = web.application(urls, globals(), autoreload=False)

class Request(object):
    def __init__(self):
        self.web_request = None

    def get_request(self):
        data = web.data()
        self.web_request = data[0] == '1'
        if self.web_request:
            result = json.loads(data[1:])
        else:
            result = cPickle.loads(data[1:].decode('zlib'))
        return result

    def prepare_response(self, r):
        if self.web_request:
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
        else:
            web.header('Content-encoding', 'deflate')
            return cPickle.dumps(r, 2).encode('zlib')


class Api(Request):
    def __init__(self):
        Request.__init__(self)

    def POST(self, name):
        r = {'result': None, 'error': None}
        q = self.get_request()
        try:
            method = q['method']
            if method == 'send_request':
                request = q['params'][0]
                user_id = q['params'][1]
                task_id = q['params'][2]
                item_id = q['params'][3]
                params = q['params'][4]
                r['result'] = web.server.process_request(web.ctx.env, request, user_id, task_id, item_id, params)
                if task_id == 0:
                    if request == 'exit' and r['result']:
                        sys.exit(0)
            else:
                r['result'] = None
        except Exception, e:
            print traceback.format_exc()
            r['error'] = e.message
        return self.prepare_response(r)

class Ext(Request):
    def __init__(self):
        Request.__init__(self)

    def get_request(self):
        data = web.data()
        self.web_request = True
        result = json.loads(data)
        return result

    def POST(self, name):
        r = {'result': None, 'error': None}
        q = self.get_request()
        try:
            request = name
            user_id = None
            task_id = None
            item_id = None
            params = q
            ext = True
            r['result'] = web.server.process_request(web.ctx.env, request, user_id, task_id, item_id, params, ext)
        except Exception, e:
            print traceback.format_exc()
            r['error'] = e.message
        return self.prepare_response(r)

class Upload:
    def POST(self, name):
        data = web.data()
        header = []
        header_str = ''
        length = 0
        string = ''
        for s in data:
            header_str += s
            if s == ';':
                if len(header) == 0:
                    length = int(string)
                header.append(int(string))
                if len(header) == 2 * (length + 1):
                    break;
                string = ''
            else:
                string += s
        start = len(header_str)
        path = os.path.join(os.getcwd(), os.path.normpath(data[start: start + header[1]]))
        if not os.path.exists(path):
            os.makedirs(path)
        start = start + header[1]
        for i in range(length):
            index = 2 * i + 2
            file_name = data[start: start + header[index]]
            start = start + header[index]
            index += 1
            content = data[start: start + header[index]]
            file_name = os.path.join(path, file_name)
            with open(file_name, 'wb') as f:
                f.write(content)
            start = start + header[index]

class Index:
    def GET(self, name):
        if not name:
            name = 'index.html'
        file_name = os.path.normpath(name)
        if file_name in ['index.html', 'admin.html']:
            web.server.check_task_client_modified(file_name)
        file_name = web.server.check_file_name(file_name)
        base, ext = os.path.splitext(file_name)
        content_type = common.mime_type_by_ext(ext)
        if file_name and os.path.isfile(file_name):
            with open(os.path.join(file_name), 'rb') as f:
                web.header('Content-Type', content_type)
#                web.header('Cache-Control', 'no-cache')
                return f.read()
        else:
            return ''

def run(server):
    me = common.SingleInstance()
    web.server = server
    server.app = app
    app.run()

