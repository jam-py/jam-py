#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from jam.client_classes import ClientTask

class TestTask(unittest.TestCase):

    task = None

    @classmethod
    def setUpClass(cls):
        cls.task = ClientTask()
        cls.task.load()
        cls.task.server_empty_tables()

    def test_task_name(self):
        self.assertEqual(self.task.item_name, 'test')

if __name__ == '__main__':
    unittest.main()
