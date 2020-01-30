
from ..common import consts

def get_database(db_type):
    db = None
    if db_type == consts.SQLITE:
        from .sqlite import db
    elif db_type == consts.POSTGRESQL:
        from .postgres import db
    elif db_type == consts.MYSQL:
        from .mysql import db
    elif db_type == consts.FIREBIRD:
        from .firebird import db
    elif db_type == consts.ORACLE:
        from .oracle import db
    elif db_type == consts.MSSQL:
        from .mssql import db
    return db
