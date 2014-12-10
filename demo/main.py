#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import jam.common
from jam.client_classes import ClientTask

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    jam.common.URL = None
    client = ClientTask()
    client.run()

if __name__ == '__main__':
    main()
