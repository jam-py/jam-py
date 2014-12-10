#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from jam.client_classes import AdminTask

def main():
    try:
        url = sys.argv[1]
    except:
        url = None
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    client = AdminTask(url)
    client.run()

if __name__ == '__main__':
    main()
