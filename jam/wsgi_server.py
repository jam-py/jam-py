# -*- coding: utf-8 -*-

def run(app):
    import sys, os
    from werkzeug.serving import run_simple

    host = '0.0.0.0'
    try:
        port = sys.argv[1]
    except:
        port = '8080'
    run_simple(host, port, app, threaded=True, use_debugger=True)
