import sys
import os
import datetime, time
import xml.dom.minidom
import json
import pickle
import locale
import decimal
import zipfile
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from werkzeug._compat import to_unicode, to_bytes

DEFAULT_SETTINGS = {
    'LANGUAGE': 1,
    'SAFE_MODE': False,
    'DEBUGGING': False,
    'VERSION': '',
    'CON_POOL_SIZE': 4,
    'MP_POOL': False,
    'PERSIST_CON': False,
    'SINGLE_FILE_JS': False,
    'DYNAMIC_JS': False,
    'COMPRESSED_JS': False,
    'TIMEOUT': 0,
    'IGNORE_CHANGE_IP': True,
    'DELETE_REPORTS_AFTER': 0,
    'THEME': 1,
    'SMALL_FONT': False,
    'FULL_WIDTH': False,
    'FORMS_IN_TABS': True,
    'MAX_CONTENT_LENGTH': 0
}

DEFAULT_LOCALE = {
    'DECIMAL_POINT': '.',
    'MON_DECIMAL_POINT': '.',
    'MON_THOUSANDS_SEP': '',
    'CURRENCY_SYMBOL': '',
    'FRAC_DIGITS': 2,
    'P_CS_PRECEDES': False,
    'N_CS_PRECEDES': False,
    'P_SEP_BY_SPACE': True,
    'N_SEP_BY_SPACE': True,
    'POSITIVE_SIGN': '',
    'NEGATIVE_SIGN': '-',
    'P_SIGN_POSN': 1,
    'N_SIGN_POSN': 1,
    'D_FMT': '%Y-%m-%d',
    'D_T_FMT': '%Y-%m-%d %H:%M'
}

SETTINGS = {}
LOCALE = {}

THEMES = ('Bootstrap', 'Cerulean', 'Amelia', 'Flatly', 'Journal',
    'Slate', 'United', 'Cosmo', 'Readable', 'Spacelab')
THEME_FILE = ('', 'bootstrap.css', 'bootstrap-cerulean.css',
    'bootstrap-amelia.css', 'bootstrap-flatly.css', 'bootstrap-journal.css',
    'bootstrap-slate.css', 'bootstrap-united.css', 'bootstrap-cosmo.css',
    'bootstrap-readable.css', 'bootstrap-spacelab.css')


RESPONSE, NOT_LOGGED, UNDER_MAINTAINANCE, NO_PROJECT = range(1, 5)

ROOT_TYPE, USERS_TYPE, ROLES_TYPE, TASKS_TYPE, TASK_TYPE, \
    ITEMS_TYPE, JOURNALS_TYPE, TABLES_TYPE, REPORTS_TYPE, \
    ITEM_TYPE, JOURNAL_TYPE, TABLE_TYPE, REPORT_TYPE, DETAIL_TYPE = range(1, 15)
ITEM_TYPES = ["root", "users", "roles", "tasks", "task",
        "items", "items", "details", "reports",
        "item", "item", "detail_item", "report", "detail"]

GROUP_TYPES = ["Item group", "Detail group", "Report group"]

TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, KEYS, FILE, IMAGE = range(1, 12)
FIELD_TYPES = ('TEXT', 'INTEGER', 'FLOAT', 'CURRENCY', 'DATE', 'DATETIME', 'BOOLEAN', 'LONGTEXT', 'KEYS', 'FILE', 'IMAGE')
FIELD_TYPE_NAMES = ('', 'text', 'integer', 'float', 'currency', 'date', 'datetime', 'boolean', 'longtext', 'keys', 'file', 'image')
ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = 1, 2, 3
ALIGNMENT = ('ALIGN_LEFT', 'ALIGN_CENTER', 'ALIGN_RIGHT')
ITEM_FIELD, FILTER_FIELD, PARAM_FIELD = range(1, 4)

FILTER_EQ, FILTER_NE, FILTER_LT, FILTER_LE, FILTER_GT, FILTER_GE, FILTER_IN, FILTER_NOT_IN, \
FILTER_RANGE, FILTER_ISNULL, FILTER_EXACT, FILTER_CONTAINS, FILTER_STARTWITH, FILTER_ENDWITH, \
FILTER_CONTAINS_ALL = range(1, 16)
FILTER_STR = ('eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in', 'not_in', \
'range', 'isnull', 'exact', 'contains', 'startwith', 'endwith', \
'contains_all')
FILTER_SIGN = ('', '=', '<>', '<', '<=', '>', '>=', 'IN', 'NOT IN',
    'BETWEEN', 'ISNULL', '=', 'LIKE', 'LIKE', 'LIKE', 'CONTAINS_ALL')
FILTER_STRING = ('EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'IN', 'NOT IN',
    'RANGE', 'ISNULL', 'EXACT', 'CONTAINS', 'STARTWITH', 'ENDWITH', 'CONTAINS_ALL')
REC_STATUS, REC_CONTROLS_INFO, REC_CHANGE_ID = range(3)

ORDER_ASC, ORDER_DESC = range(2)
STATE_INACTIVE, STATE_BROWSE, STATE_INSERT, STATE_EDIT, STATE_DELETE = range(5)
UPDATE_OPEN, UPDATE_DELETE, UPDATE_CANCEL, UPDATE_APPEND, UPDATE_INSERT, UPDATE_SCROLLED, UPDATE_RESTORE, UPDATE_REFRESH = range(8)
RECORD_UNCHANGED, RECORD_INSERTED, RECORD_MODIFIED, RECORD_DELETED, RECORD_DETAILS_MODIFIED = None, 1, 2, 3, 4
EDITOR_TAB_SIZE = 4
ITEM_PARAM_INDENT = '__$_item_$__'
FIELD_PARAM_INDENT = '__$_field_$__'
FILTER_PARAM_INDENT = '__$_filter_$__'

CLIENT_MODULE, WEB_CLIENT_MODULE, SERVER_MODULE = range(3)
TAB_FUNCS, TAB_EVENTS, TAB_TASK, TAB_FIELDS = range(4)
editor_tabs = ("Module", "Events", "Task", "Fields")

HISTORY_FIELDS = [
    ['item_id', INTEGER, None],
    ['item_rec_id', INTEGER, None],
    ['operation', INTEGER, None],
    ['changes', LONGTEXT, None],
    ['user', TEXT, 30],
    ['date', DATETIME, None]
]
HISTORY_INDEX_FIELDS = ['item_id', 'item_rec_id']

LOCKS_FIELDS = [
    ['id', INTEGER, None],
    ['item_id', INTEGER, None],
    ['item_rec_id', INTEGER, None],
    ['user', TEXT, 30],
    ['date', DATETIME, None]
]
LOCKS_INDEX_FIELDS = ['item_id', 'item_rec_id']

SQL_KEYWORDS = ['DATE', 'DAY', 'MONTH']

def error_message(e):
    try:
        return str(e)
    except:
        return unicode(e)

def get_alignment(data_type, item=None, lookup_values=None):
    if (data_type == INTEGER) or (data_type == FLOAT) or (data_type == CURRENCY):
        result = ALIGN_RIGHT
    elif (data_type == DATE) or (data_type == DATETIME):
        result = ALIGN_CENTER
    else:
        result = ALIGN_LEFT
    if item or lookup_values:
        result = ALIGN_LEFT
    return result

def float_to_str(val):
    return str(val).replace('.', DECIMAL_POINT)

def str_to_float(val):
    val = val.replace(DECIMAL_POINT, '.')
    return float(val)

def cur_to_str(value):

    def transform_digits(val):
        if not val[0].isdigit():
            val = val[1:]
        point = val.find('.')
        dec = ''
        digits = val
        if point >= 0:
            dec = val[point + 1:]
            digits = val[:point]
        result = ''
        count = 0
        lenth = len(digits)
        for i in range(lenth):
            d = digits[lenth - i - 1]
            result = d + result
            count += 1
            if count % 3 == 0 and (i != lenth - 1):
                result = MON_THOUSANDS_SEP + result
        if dec:
            result = result + MON_DECIMAL_POINT + dec
        return result

    if value is None:
        value = 0
    format_str = '%.' + str(FRAC_DIGITS) + 'f'
    result = format_str % value
    result = transform_digits(result)
    if value < 0:
        if N_SIGN_POSN == 3:
            result = NEGATIVE_SIGN + result
        elif N_SIGN_POSN == 4:
            result = result + NEGATIVE_SIGN
    else:
        if P_SIGN_POSN == 3:
            result = POSITIVE_SIGN + result
        elif P_SIGN_POSN == 4:
            result = result + POSITIVE_SIGN
    if CURRENCY_SYMBOL:
        if value < 0:
            if N_CS_PRECEDES:
                if N_SEP_BY_SPACE:
                    result = CURRENCY_SYMBOL + ' ' + result
                else:
                    result = CURRENCY_SYMBOL + result
            else:
                if N_SEP_BY_SPACE:
                    result = result + ' ' + CURRENCY_SYMBOL
                else:
                    result = result + CURRENCY_SYMBOL
        else:
            if P_CS_PRECEDES:
                if P_SEP_BY_SPACE:
                    result = CURRENCY_SYMBOL + ' ' + result
                else:
                    result = CURRENCY_SYMBOL + result
            else:
                if P_SEP_BY_SPACE:
                    result = result + ' ' + CURRENCY_SYMBOL
                else:
                    result = result + CURRENCY_SYMBOL
    if value < 0:
        if N_SIGN_POSN == 0 and NEGATIVE_SIGN:
            result = NEGATIVE_SIGN + '(' + result + ')'
        elif N_SIGN_POSN == 1:
            result = NEGATIVE_SIGN + result
        elif N_SIGN_POSN == 2:
            result = result + NEGATIVE_SIGN
    else:
        if P_SIGN_POSN == 0 and POSITIVE_SIGN:
            result = POSITIVE_SIGN + '(' + result + ')'
        elif P_SIGN_POSN == 1:
            result = POSITIVE_SIGN + result
        elif P_SIGN_POSN == 2:
            result = result + POSITIVE_SIGN
    return result

def currency_to_str(val):
    return cur_to_str(val)

def str_to_currency(val):
    result = val.strip()
    if MON_THOUSANDS_SEP:
        result = result.replace(MON_THOUSANDS_SEP, '')
    if CURRENCY_SYMBOL:
        result = result.replace(CURRENCY_SYMBOL, '')
    if POSITIVE_SIGN:
        result = result.replace(POSITIVE_SIGN, '')
    if NEGATIVE_SIGN and result.find(NEGATIVE_SIGN) != -1:
        result = result.replace(NEGATIVE_SIGN, '')
        result = '-' + result
    result = result.replace(MON_DECIMAL_POINT, '.').strip()
    result = float(result)
    return result

def date_to_str(date):
    return date.strftime(D_FMT)

def str_to_date(date_str):
    time_tuple = time.strptime(date_str, D_FMT)
    return datetime.date(time_tuple.tm_year, time_tuple.tm_mon, time_tuple.tm_mday)

def datetime_to_str(date):
    return date.strftime(D_T_FMT)

def str_to_datetime(date_str):
    time_tuple = time.strptime(date_str, D_T_FMT)
    return datetime.datetime(time_tuple.tm_year, time_tuple.tm_mon,
        time_tuple.tm_mday, time_tuple.tm_hour, time_tuple.tm_min, time_tuple.tm_sec)

def load_interface(item):
    item._view_list = []
    item._edit_list = []
    item._order_list = []
    item._reports_list = []
    value = item.f_info.value
    if value:
        if len(value) >= 4 and value[0:4] == 'json':
            lists = json.loads(value[4:])
        else:
            lists = pickle.loads(to_bytes(value, 'utf-8'))
        item._view_list = lists['view']
        item._edit_list = lists['edit']
        item._order_list = lists['order']
        if lists.get('reports'):
            item._reports_list = lists['reports']

def store_interface(item):
    handlers = item.store_handlers()
    item.clear_handlers()
    try:
        item.edit()
        dic = {'view': item._view_list,
                'edit': item._edit_list,
                'order': item._order_list,
                'reports': item._reports_list}
        item.f_info.value = 'json' + json.dumps(dic, default=json_defaul_handler)
        #~ item.f_info.value = to_unicode(pickle.dumps(dic, protocol=0), 'utf-8')
        item.post()
        item.apply()
    finally:
        handlers = item.load_handlers(handlers)

def store_index_fields(f_list):
    return json.dumps(f_list)

def load_index_fields(value):
    return json.loads(str(value))

def valid_identifier(name):
    if name[0].isdigit():
        return False
    try:
        while vars().get(name):
            name += '1'
        vars()[name] = 1
        eval(name)
        return True
    except:
        return False

def remove_comments(text, is_server, comment_sign):
    result = []
    if text:
        comment = False
        for line in text.splitlines(True):
            if comment:
                pos = line.find('*/')
                if pos != -1:
                    comment = False
                    line = pos * ' ' + '*/' + line[pos + 2:]
                else:
                    line = ' ' * len(line)
            else:
                pos = line.find(comment_sign)
                if pos != -1:
                    line = line[0:pos] + comment_sign + (len(line) - len(line[0:pos] + comment_sign) - 1) * ' ' + '\n'
                if not is_server:
                    pos = line.find('/*')
                    if pos != -1:
                        end = line.find('*/', pos + 2)
                        if end != -1:
                            line = line[0:pos] + '/*' + ' ' * (end - pos - 2) + line[end:]
                        else:
                            comment = True
                            line = line[0:pos+2] + ' ' * (len(line) - (pos + 2))
            result.append(line)
        result = ''.join(result)
    return result

def get_funcs_info(text, is_server):

    def check_line(line, comment_sign, func_literal):
        func_name = ''
        trimed_line = line.strip()
        if len(trimed_line) > 0:
            if not (trimed_line[:len(comment_sign)] == comment_sign):
                indent = line.find(func_literal)
                if indent >= 0:
                    def_end = line.find('(')
                    if def_end > indent:
                        func_name = line[indent+len(func_literal):def_end].strip()
                        if func_name:
                            return (indent, func_name)

    def add_child_funcs(i, parent_indent, parent_dic, parent_key):
        dic = {}
        parent_dic[parent_key] = dic
        if i < len(funcs_list):
            cur_indent = funcs_list[i][0]
        else:
            return
        cur_indent = -1
        child_indent = -1
        while i < len(funcs_list):
            (indent, func_name) = funcs_list[i]
            if cur_indent == -1:
                cur_indent = indent
            if indent == cur_indent:
                dic[func_name] = None
                cur_func_name = func_name
            elif indent > cur_indent:
                if child_indent == -1:
                    child_indent = indent
                if not indent > child_indent:
                    i = add_child_funcs(i, indent, dic, cur_func_name)
            elif indent < cur_indent:
                return i - 1
            i += 1
        return i

    funcs = {}
    funcs['result'] = {}
    if text:
        if is_server:
            comment_sign = '#'
            func_literal = 'def'
        else:
            comment_sign = '//'
            func_literal = 'function'
        text = remove_comments(text, is_server, comment_sign)
        lines = text.splitlines()
        funcs_list = []
        for i, line in enumerate(lines):
            res = check_line(line, comment_sign, func_literal)
            if res:
                funcs_list.append(res)
        add_child_funcs(0, -1, funcs, 'result')
    return funcs['result']

class cached_property(property):

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

class SingleInstance(object):
    def __init__(self, port=None):
        import sqlite3
        file_name =  os.path.basename(sys.modules['__main__'].__file__)
        self.pid_file = '%s.pid' % file_name
        if port:
            self.pid_file = '%s_%s.pid' % (file_name, port)
        self.con = sqlite3.connect(self.pid_file, timeout=0.1, isolation_level='EXCLUSIVE')
        self.cur = self.con.cursor()
        try:
            self.cur.execute('PRAGMA journal_mode = MEMORY;')
            self.cur.execute('PRAGMA synchronous = OFF;')
            self.cur.execute('CREATE TABLE IF NOT EXISTS PID (ID INTEGER NOT NULL)')
            self.con.commit()
            self.cur.execute('INSERT INTO PID (ID) VALUES (?)', (1,))
        except sqlite3.OperationalError as e:
            if e.args[0].lower().find('database is locked') != -1:
                self.con.close()
                if port:
                    print('%s port %s: another instance is already running, quitting' % (file_name, port))
                else:
                    print('%s: another instance is already running, quitting' % file_name)
                sys.exit(-1)

    def close(self):
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

def json_defaul_handler(obj):
    result = obj
    if hasattr(obj, 'isoformat'):
        result = obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        result = float(obj)
    return result

def zip_dir(dir, zip_file, exclude_dirs=[], exclude_ext=[], recursive=True):
    folder = os.path.join(os.getcwd(), dir)
    if os.path.exists(folder):
        if recursive:
            for dirpath, dirnames, filenames in os.walk(folder):
                head, tail = os.path.split(dirpath)
                if not tail in exclude_dirs:
                    for file_name in filenames:
                        name, ext = os.path.splitext(file_name)
                        if not ext in exclude_ext:
                            file_path = os.path.join(dirpath, file_name)
                            arcname = os.path.relpath(os.path.join(dir, file_path))
                            zip_file.write(file_path, arcname)
        else:
            for file_name in os.listdir(folder):
                name, ext = os.path.splitext(file_name)
                if not ext in exclude_ext:
                    file_path = os.path.join(folder, file_name)
                    arcname = os.path.relpath(os.path.join(dir, file_path))
                    zip_file.write(file_path, arcname)

def compressBuf(buf):
    zbuf = StringIO()
    zfile = gzip.GzipFile(mode = 'wb',  fileobj = zbuf, compresslevel = 9)
    zfile.write(buf.encode())
    zfile.close()
    return zbuf.getvalue()

def profileit(func):
    import cProfile

    def wrapper(*args, **kwargs):
        datafn = func.__name__ + ".profile" # Name the data file sensibly
        prof = cProfile.Profile()
        retval = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(datafn)
        return retval

    return wrapper

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%s  %s' %  (method.__name__, te-ts))
        return result

    return timed

