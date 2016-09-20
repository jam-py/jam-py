# -*- coding: utf-8 -*-

SQLITE, FIREBIRD, POSTGRESQL, MYSQL, ORACLE = range(1, 6)
DB_TYPE = ('Sqlite', 'FireBird', 'PostgreSQL', 'MySQL', 'Oracle')

def get_db_module(db_type):
    db = None
    if db_type == SQLITE:
        import sqlite as db
    elif db_type == FIREBIRD:
        import firebird as db
    elif db_type == POSTGRESQL:
        import postgres as db
    elif db_type == MYSQL:
        import mysql as db
    elif db_type == ORACLE:
        import oracle as db
    return db
