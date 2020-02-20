import pyodbc

from .mssql_db import MSSqlDB

class MSSqlDB2(MSSqlDB):
    def __init__(self):
        MSSqlDB.__init__(self)

    #DRIVER={ODBC Driver 17 for SQL Server};SERVER=ANDREW-PC\SQLEXPRESS;DATABASE=demo;UID=sa;PWD=1111
    #DSN=SQL Server;DATABASE=demo;UID=sa;PWD=1111
    def connect(self, db_info):
        return pyodbc.connect(db_info.dns)

    def get_lastrowid(self, cursor):
        cursor.execute('SELECT @@IDENTITY')
        r = cursor.fetchone()
        return int(r[0])

    @property
    def arg_params(self):
        return True

db = MSSqlDB2()

