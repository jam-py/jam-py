import pymssql

from .mssql_db import MSSqlDB

class MSSqlDB1(MSSqlDB):
    def __init__(self):
        MSSqlDB.__init__(self)

    def connect(self, db_info):
        if db_info.encoding:
            return pymssql.connect(server=db_info.server, database=db_info.database,
                user=db_info.user, password=db_info.password, host=db_info.host,
                port=db_info.port, charset=db_info.encoding, autocommit=True)
        else:
            return pymssql.connect(server=db_info.server, database=db_info.database,
                user=db_info.user, password=db_info.password, host=db_info.host,
                port=db_info.port, autocommit=True)

    def get_lastrowid(self, cursor):
        return cursor.lastrowid

    def value_literal(self, index):
        return '%s'

db = MSSqlDB1()
