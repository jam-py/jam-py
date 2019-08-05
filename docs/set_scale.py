#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def process_file(file_name, delete_scale):
    result = []
    with open(file_name) as f:
        content = f.readlines()
    lines = []
    for i, line in enumerate(content):
        cur_line = line.strip()
        new_line = None
        if delete_scale:
            if cur_line.find(':scale:') != -1:
                continue
        else:
            if cur_line.startswith('.. image::'):
                new_line = '\t:scale: 70 %\n'
        lines.append(content[i])
        if new_line:
            lines.append(new_line)
    for line in lines:
        if line:
            result.append(line)
    with open(file_name, 'w') as f:
        f.write(''.join(result))

def update_file(folder, delete_scale=False):
    for root, dirs, files in os.walk(folder):
        for name in files:
            n, ext = os.path.splitext(name)
            if ext == '.txt':
                process_file(os.path.join(root, name), delete_scale)


folder = os.getcwd()
update_file(folder, True)
#update_file(folder)


