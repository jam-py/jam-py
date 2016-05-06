# -*- coding: utf-8 -*-

def run(app):
    import sys, os
    from werkzeug.serving import run_simple

    host = '0.0.0.0'
    try:
        port = sys.argv[1]
    except:
        port = '8080'
    static = {
        '/static':  os.path.join(app.work_dir, 'static')
    }
    run_simple(host, port, app, threaded=True, static_files=static,
        use_debugger=True)
