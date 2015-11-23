#!/usr/bin/env python
# -*- coding: utf-8 -*-


if __name__ == '__main__':
    import sys
    reload(sys)

    sys.setdefaultencoding('utf-8')
    import jam.webapp
    from jam.requests import server
    jam.webapp.run(server)
