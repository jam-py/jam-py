import mysql.connector

from .mysql_db import MySQLDB

class MySQLDB2(MySQLDB):
    def __init__(self):
        MySQLDB.__init__(self)

    def connect(self, db_info):
        args = {
            'db': db_info.database,
            'user': db_info.user,
            'passwd': db_info.password,
            'host': db_info.host,
        }
        if db_info.port:
            args['port'] = db_info.port
        if db_info.encoding:
            args['charset'] = db_info.encoding
            args['use_unicode'] = True
        connection = mysql.connector.connect(**args)
        cursor = connection.cursor()
        cursor.execute("SET SESSION SQL_MODE=ANSI_QUOTES")
        connection.autocommit = False
        return connection

db = MySQLDB2()
