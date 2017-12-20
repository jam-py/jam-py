# -*- coding: utf-8 -*-

def run(app):
    import sys
    from werkzeug.serving import run_simple

    host = '0.0.0.0'
    try:
        port = int(sys.argv[1])
    except:
        port = 8080
    run_simple(host, port, app, threaded=True, use_debugger=True)
