#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import signal
import time
import subprocess

app_server = None

def signal_handler(sigvalue, frame):
    global app_server
    app_server.stop(sigvalue)

def run():
    global app_server

    reload(sys)

    pid = os.getpid()
    signal.signal(signal.SIGINT, signal_handler)

    sys.setdefaultencoding('utf-8')
    import jam.webapp
    from jam.requests import server
    server.application_pid = pid
    app_server = server
    jam.webapp.run(server)

if __name__ == '__main__':
    run()
