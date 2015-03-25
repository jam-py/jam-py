#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import unittest

if __name__ == '__main__':
    try:
        pattern = sys.argv[1]
    except:
        pattern = 'test*.py'
    testsuite = unittest.TestLoader().discover('python', pattern)
    unittest.TextTestRunner(verbosity=2).run(testsuite)
