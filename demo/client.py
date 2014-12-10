#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from jam.client_classes import ClientTask

def main():
    try:
        url = sys.argv[1]
    except:
        url = 'http://127.0.0.1:8080'
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    client = ClientTask(url)
    client.run()

if __name__ == '__main__':
    main()
