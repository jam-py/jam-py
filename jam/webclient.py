# -*- coding: utf-8 -*-

import sys, os, time

import urllib2, cPickle

class Aws(object):
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers
        print self.url

    def __getattr__(self, name):
        obj = lambda *params: self._send(name, params)
        setattr(self, name, obj)
        return obj

    def _send(self, method, params):
        try:
            data = '0'+cPickle.dumps({'method': method, 'params': params}, 2).encode('zlib')
            if self.headers:
                req = urllib2.Request(url=self.url, data=data, headers=self.headers)
            else:
                req = urllib2.Request(url=self.url, data=data)
            a = urllib2.urlopen(req)
            r = cPickle.loads(a.read().decode('zlib'))
            return r['result'], r['error']
        except Exception, e:
            return None, str(e)
