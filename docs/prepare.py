#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def process_html(file_name):
    result = []
    with open(file_name) as f:
        content = f.readlines()
    lines = []
    for i, line in enumerate(content):
        cur_line = line.strip()
        if cur_line == '<head>':
            lines.append('  <head>\n')
            lines.append('    <!-- Global Site Tag (gtag.js) - Google Analytics -->\n')
            lines.append('    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-106491578-1"></script>\n')
            lines.append('    <script>\n')
            lines.append('      window.dataLayer = window.dataLayer || [];\n')
            lines.append('      function gtag(){dataLayer.push(arguments)};\n')
            lines.append("      gtag('js', new Date());\n")
            lines.append('\n')
            lines.append("      gtag('config', 'UA-106491578-1');\n")
            lines.append('    </script>\n')
        elif cur_line == '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />':
            lines.append('    <meta charset="utf-8">\n')
#            lines.append('    <meta http-equiv="X-UA-Compatible" content="IE=edge">\n')
            lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1">\n')
            lines.append('    <meta name="ROBOTS" content="ALL" />\n')
#            lines.append('    <meta http-equiv="imagetoolbar" content="no" />\n')
#            lines.append('    <meta name="MSSmartTagsPreventParsing" content="true" />\n')
            lines.append('    <meta name="Copyright" content="Andrew Yushev" />\n')
            lines.append('    <meta name="keywords" content="Python, Javascript, Jam.py, framework, open-source"/>\n')
            lines.append('    <meta name="description" content="" />\n')
        else:
            if cur_line == '<div class="sphinxsidebarwrapper">':
                if content[i + 1].find('Table Of Contents') != -1:
                    content[i + 1] = '<h3>Contents</h3>\n'
            if cur_line == '<h3>This Page</h3>':
                for j in range(6):
                    content[i + j - 1] = ''
            if cur_line.find('<table') != -1 and cur_line.find('class="docutils"') != -1:
                content[i] = line.replace('class="docutils"', 'class="table-condensed table-bordered table-striped"')
            if cur_line == '''<script type="text/javascript">$('#searchbox').show(0);</script>''':
                content[i] = '';
            lines.append(content[i])
    for line in lines:
        if line:
            result.append(line)
    with open(file_name, 'w') as f:
        f.write(''.join(result))

def update_html(folder):
    count = 0
    for root, dirs, files in os.walk(folder):
        for name in files:
            n, ext = os.path.splitext(name)
            if ext == '.html':
                count += 1
                process_html(os.path.join(root, name))
    print 'total', count

if __name__ == '__main__':
    folder = os.path.join(os.getcwd(), '_build', 'html')
    update_html(folder)
