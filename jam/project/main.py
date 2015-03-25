#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from jam.client_classes import ClientTask

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    client = ClientTask()
    client.run()

if __name__ == '__main__':
    main()
