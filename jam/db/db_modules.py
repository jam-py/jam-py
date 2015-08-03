# -*- coding: utf-8 -*-

SQLITE, FIREBIRD, POSTGRESQL, MYSQL = range(1, 5)
DB_TYPE = ('Sqlite', 'FireBird', 'PostgreSQL', 'MySQL')

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
    return db
