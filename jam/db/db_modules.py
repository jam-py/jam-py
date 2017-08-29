
SQLITE, FIREBIRD, POSTGRESQL, MYSQL, ORACLE = range(1, 6)
DB_TYPE = ('Sqlite', 'FireBird', 'PostgreSQL', 'MySQL', 'Oracle')

def get_db_module(db_type):
    db = None
    if db_type == SQLITE:
        import jam.db.sqlite as db
    elif db_type == FIREBIRD:
        import jam.db.firebird as db
    elif db_type == POSTGRESQL:
        import jam.db.postgres as db
    elif db_type == MYSQL:
        import jam.db.mysql as db
    elif db_type == ORACLE:
        import jam.db.oracle as db
    return db
