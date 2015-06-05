#!/usr/bin/env python
# -*- coding: utf-8 -*-


if __name__ == '__main__':
    import sys
    reload(sys)

    sys.setdefaultencoding('utf-8')
    import jam.webserver
    from jam.server import server
    jam.webserver.run(server)
