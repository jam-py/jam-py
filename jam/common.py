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
from decimal import Decimal, ROUND_HALF_UP
import io
import imghdr
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from werkzeug._compat import iterkeys, iteritems, to_unicode, to_bytes, string_types
from werkzeug.utils import cached_property

from .langs import get_lang_dict, get_locale_dict

class ProjectNotCompleted(Exception):
    pass

class Consts(object):
    DEFAULT_SETTINGS = {
        'LANGUAGE': 1,
        'SAFE_MODE': False,
        'DEBUGGING': False,
        'JAM_VERSION': '',
        'VERSION': '',
        'CON_POOL_SIZE': 4,
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
        'MAX_CONTENT_LENGTH': 0,
        'IMPORT_DELAY': 0,
        'UPLOAD_FILE_EXT': '.txt, .csv',
        'MODIFICATION': 0,
        'MAINTENANCE': False,
        'CLIENT_MODIFIED': False,
        'SERVER_MODIFIED': False,
        'BUILD_VERSION': 0,
        'PARAMS_VERSION': 0
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
        'D_T_FMT': '%Y-%m-%d %H:%M:%S'
    }
    THEMES = ('Bootstrap', 'Cerulean', 'Amelia', 'Flatly', 'Journal',
        'Slate', 'United', 'Cosmo', 'Readable', 'Spacelab')
    THEME_FILE = ('', 'bootstrap.css', 'bootstrap-cerulean.css',
        'bootstrap-amelia.css', 'bootstrap-flatly.css', 'bootstrap-journal.css',
        'bootstrap-slate.css', 'bootstrap-united.css', 'bootstrap-cosmo.css',
        'bootstrap-readable.css', 'bootstrap-spacelab.css')
    PROJECT_NONE, PROJECT_NO_PROJECT, PROJECT_LOADING, PROJECT_ERROR, \
        PROJECT_NOT_LOGGED, PROJECT_LOGGED, PROJECT_MAINTAINANCE, \
        PROJECT_MODIFIED, RESPONSE = range(1, 10)
    ROOT_TYPE, USERS_TYPE, ROLES_TYPE, TASKS_TYPE, TASK_TYPE, \
        ITEMS_TYPE, JOURNALS_TYPE, TABLES_TYPE, REPORTS_TYPE, \
        ITEM_TYPE, JOURNAL_TYPE, TABLE_TYPE, REPORT_TYPE, DETAIL_TYPE = range(1, 15)
    ITEM_TYPES = ["root", "users", "roles", "tasks", "task",
            "items", "items", "details", "reports",
            "item", "item", "detail_item", "report", "detail"]
    GROUP_TYPES = ["Item group", "Detail group", "Report group"]
    TEXT, INTEGER, FLOAT, CURRENCY, DATE, DATETIME, BOOLEAN, LONGTEXT, \
        KEYS, FILE, IMAGE = range(1, 12)
    FIELD_TYPES = ('TEXT', 'INTEGER', 'FLOAT', 'CURRENCY', 'DATE',
        'DATETIME', 'BOOLEAN', 'LONGTEXT', 'KEYS', 'FILE', 'IMAGE')
    FIELD_TYPE_NAMES = ('', 'text', 'integer', 'float', 'currency', 'date',
        'datetime', 'boolean', 'longtext', 'keys', 'file', 'image')
    ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT = 1, 2, 3
    ALIGNMENT = ('ALIGN_LEFT', 'ALIGN_CENTER', 'ALIGN_RIGHT')
    ITEM_FIELD, FILTER_FIELD, PARAM_FIELD = range(1, 4)
    FILTER_EQ, FILTER_NE, FILTER_LT, FILTER_LE, FILTER_GT, FILTER_GE, \
        FILTER_IN, FILTER_NOT_IN, FILTER_RANGE, FILTER_ISNULL, \
        FILTER_EXACT, FILTER_CONTAINS, FILTER_STARTWITH, FILTER_ENDWITH, \
        FILTER_CONTAINS_ALL = range(1, 16)
    FILTER_STR = ('eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in', 'not_in',
        'range', 'isnull', 'exact', 'contains', 'startwith', 'endwith',
        'contains_all')
    FILTER_SIGN = ('', '=', '<>', '<', '<=', '>', '>=', 'IN', 'NOT IN',
        'BETWEEN', 'ISNULL', '=', 'LIKE', 'LIKE', 'LIKE', 'CONTAINS_ALL')
    FILTER_STRING = ('EQ', 'NE', 'LT', 'LE', 'GT', 'GE', 'IN', 'NOT IN',
        'RANGE', 'ISNULL', 'EXACT', 'CONTAINS', 'STARTWITH', 'ENDWITH',
        'CONTAINS_ALL')
    REC_STATUS, REC_CONTROLS_INFO, REC_CHANGE_ID, REC_OLD_REC = range(4)
    ORDER_ASC, ORDER_DESC = range(2)
    STATE_INACTIVE, STATE_BROWSE, STATE_INSERT, STATE_EDIT, STATE_DELETE = range(5)
    UPDATE_OPEN, UPDATE_DELETE, UPDATE_CANCEL, UPDATE_APPEND, \
        UPDATE_INSERT, UPDATE_SCROLLED, UPDATE_RESTORE, \
        UPDATE_REFRESH = range(8)
    RECORD_UNCHANGED, RECORD_INSERTED, RECORD_MODIFIED, RECORD_DELETED, \
        RECORD_DETAILS_MODIFIED = None, 1, 2, 3, 4
    WEB_CLIENT_MODULE, SERVER_MODULE = range(2)
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
        ['version', INTEGER, None]
    ]
    LOCKS_INDEX_FIELDS = ['item_id', 'item_rec_id']
    SQL_KEYWORDS = ['DATE', 'DAY', 'MONTH']
    VIDEO_EXT = ['.3g2', '.3gp', '.amv', '.asf', '.asx', '.avi', '.axv',
        '.dif', '.dl', '.drc', '.dv', '.f4a', '.f4b', '.f4p', '.f4v',
        '.fli', '.flv', '.gif', '.gifv', '.gl', '.lsf', '.lsx', '.m1v',
        '.m2ts', '.m2v', '.m4p', '.m4v', '.mkv', '.mng', '.mov',
        '.movie', '.mp2', '.mp4', '.mpa', '.mpe', '.mpeg', '.mpg',
        '.mpv', '.mts', '.mxf', '.mxu', '.nsv', '.ogg', '.ogv', '.qt',
        '.rm', '.rmvb', '.roq', '.svi', '.ts', '.viv', '.vob', '.webm',
        '.wm', '.wmv', '.wmx', '.wvx', '.yuv']
    AUDIO_EXT = ['.3gp', '.8svx', '.aa', '.aac', '.aax', '.act', '.aif',
        '.aifc', '.aiff', '.alac', '.amr', '.ape', '.au', '.awb', '.axa',
        '.cda', '.csd', '.dct', '.dss', '.dvf', '.flac', '.gsm',
        '.iklax', '.ivs', '.kar', '.m3u', '.m4a', '.m4b', '.m4p',
        '.mid', '.midi', '.mmf', '.mogg', '.mp2', '.mp3', '.mpc',
        '.mpega', '.mpga', '.msv', '.nmf', '.oga', '.ogg', '.opus',
        '.orc', '.pls', '.ra', '.ram', '.raw', '.rf64', '.rm', '.sco',
        '.sd2', '.sid', '.sln', '.snd', '.spx', '.tta', '.voc', '.vox',
        '.wav', '.wax', '.webm', '.wma', '.wv']
    IMAGE_EXT = ['.art', '.bmp', '.cdr', '.cdt', '.cpt', '.cr2', '.crw',
        '.djv', '.djvu', '.erf', '.gif', '.ico', '.ief', '.jng', '.jp2',
        '.jpe', '.jpeg', '.jpf', '.jpg', '.jpg2', '.jpm', '.jpx', '.nef',
        '.orf', '.pat', '.pbm', '.pcx', '.pgm', '.png', '.pnm', '.ppm',
        '.psd', '.ras', '.rgb', '.svg', '.svgz', '.tif', '.tiff',
        '.wbmp', '.xbm', '.xpm', '.xwd']

    def __init__(self):
        self.app = None
        self.locale = None
        self.lang = None

    @property
    def settings(self):
        result = {}
        keys = list(iterkeys(consts.DEFAULT_SETTINGS))
        for key in keys:
            result[key] = self.__dict__[key]
        return result

    def __getattr__(self, name):
        try:
            return self.locale[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        try:
             super(Consts, self).__setattr__(name, value)
        except KeyError:
            try:
                self.locale[name] = value
            except KeyError:
                raise AttributeError

    def read_language(self):
        self.lang = get_lang_dict(self.app.admin, self.LANGUAGE)
        self.locale = get_locale_dict(self.app.admin, self.LANGUAGE)

    def read_params(self, params):
        fields = []
        for key in params:
            fields.append('F_%s' % key)
        sql = 'SELECT %s FROM SYS_PARAMS' % ','.join(fields)
        con = self.app.admin.connect()
        try:
            cursor = con.cursor()
            cursor.execute(sql)
            rec = cursor.fetchall()
        finally:
            con.close()
        rec = rec[0]
        result = {}
        for i, key in enumerate(params):
            setting_type = type(self.DEFAULT_SETTINGS[key])
            try:
                if rec[i] is None:
                    value = self.DEFAULT_SETTINGS[key]
                else:
                    value = setting_type(rec[i])
            except:
                value = self.DEFAULT_SETTINGS[key]
            result[key] = value
        return result

    def read_settings(self, keys=None):
        if not keys:
            keys = list(iterkeys(self.DEFAULT_SETTINGS))
        params = self.read_params(keys)
        for key, value in iteritems(params):
            self.__dict__[key] = value
        if self.__dict__.get('upload_file_ext'):
            del self.__dict__['upload_file_ext']

    def write_params(self, params):
        sql = 'UPDATE SYS_PARAMS SET '
        fields = []
        for key in params:
            value = self.__dict__[key]
            setting_type = type(self.DEFAULT_SETTINGS[key])
            if setting_type == bool:
                if value:
                    value = 1
                else:
                    value = 0
            if setting_type in string_types:
                fields.append('F_%s="%s"' % (key, value))
            else:
                fields.append('F_%s=%s' % (key, value))
        sql = 'UPDATE SYS_PARAMS SET %s' % ','.join(fields)
        con = self.app.admin.connect()
        try:
            cursor = con.cursor()
            cursor.execute(sql)
            con.commit()
        except:
            con.rollback()
        finally:
            con.close()

    def write_settings(self, keys=None):
        if not keys:
            keys = list(iterkeys(self.DEFAULT_SETTINGS))
        self.write_params(keys)

    def language(self, key):
        return self.lang.get(key, key)

    @cached_property
    def upload_file_ext(self):
        arr = self.UPLOAD_FILE_EXT.split(',')
        result = []
        for r in arr:
            result.append(r.strip())
        return result

    def round(self, value, dec):
        precision = Decimal(10) ** (-dec)
        result = Decimal(str(value)).quantize(Decimal(precision), rounding=ROUND_HALF_UP)
        return float(result)

    def float_to_str(self, val):
        return str(val).replace('.', self.DECIMAL_POINT)

    def str_to_float(self, val):
        val = val.replace(self.DECIMAL_POINT, '.')
        return float(val)

    def cur_to_str(self, value):

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
                    result = self.MON_THOUSANDS_SEP + result
            if dec:
                result = result + self.MON_DECIMAL_POINT + dec
            return result

        if value is None:
            value = 0
        format_str = '%.' + str(self.FRAC_DIGITS) + 'f'
        result = format_str % value
        result = transform_digits(result)
        if value < 0:
            if self.N_SIGN_POSN == 3:
                result = self.NEGATIVE_SIGN + result
            elif self.N_SIGN_POSN == 4:
                result = result + self.NEGATIVE_SIGN
        else:
            if self.P_SIGN_POSN == 3:
                result = self.POSITIVE_SIGN + result
            elif self.P_SIGN_POSN == 4:
                result = result + self.POSITIVE_SIGN
        if self.CURRENCY_SYMBOL:
            if value < 0:
                if self.N_CS_PRECEDES:
                    if self.N_SEP_BY_SPACE:
                        result = self.CURRENCY_SYMBOL + ' ' + result
                    else:
                        result = self.CURRENCY_SYMBOL + result
                else:
                    if self.N_SEP_BY_SPACE:
                        result = result + ' ' + self.CURRENCY_SYMBOL
                    else:
                        result = result + self.CURRENCY_SYMBOL
            else:
                if self.P_CS_PRECEDES:
                    if self.P_SEP_BY_SPACE:
                        result = self.CURRENCY_SYMBOL + ' ' + result
                    else:
                        result = self.CURRENCY_SYMBOL + result
                else:
                    if self.P_SEP_BY_SPACE:
                        result = result + ' ' + self.CURRENCY_SYMBOL
                    else:
                        result = result + self.CURRENCY_SYMBOL
        if value < 0:
            if self.N_SIGN_POSN == 0 and self.NEGATIVE_SIGN:
                result = self.NEGATIVE_SIGN + '(' + result + ')'
            elif self.N_SIGN_POSN == 1:
                result = self.NEGATIVE_SIGN + result
            elif self.N_SIGN_POSN == 2:
                result = result + self.NEGATIVE_SIGN
        else:
            if self.P_SIGN_POSN == 0 and self.POSITIVE_SIGN:
                result = self.POSITIVE_SIGN + '(' + result + ')'
            elif self.P_SIGN_POSN == 1:
                result = self.POSITIVE_SIGN + result
            elif self.P_SIGN_POSN == 2:
                result = result + self.POSITIVE_SIGN
        return result

    def str_to_cur(self, val):
        result = val.strip()
        result = result.replace(' ', '')
        if len(self.MON_THOUSANDS_SEP):
            result = result.replace(self.MON_THOUSANDS_SEP, '')
        if self.CURRENCY_SYMBOL:
            result = result.replace(self.CURRENCY_SYMBOL, '')
        if self.POSITIVE_SIGN:
            result = result.replace(self.POSITIVE_SIGN, '')
        if self.N_SIGN_POSN == 0 or self.P_SIGN_POSN == 0:
            result = result.replace('(', '').replace(')', '')
        if self.NEGATIVE_SIGN and result.find(self.NEGATIVE_SIGN) != -1:
            result = result.replace(self.NEGATIVE_SIGN, '')
            result = '-' + result
        result = result.replace(self.MON_DECIMAL_POINT, '.').strip()
        result = float(result)
        return result

    def date_to_str(self, date):
        return date.strftime(self.D_FMT)

    def str_to_date(self, date_str):
        time_tuple = time.strptime(date_str, self.D_FMT)
        return datetime.date(time_tuple.tm_year, time_tuple.tm_mon, time_tuple.tm_mday)

    def datetime_to_str(self, date):
        return date.strftime(self.D_T_FMT)

    def str_to_datetime(self, date_str):
        time_tuple = time.strptime(date_str, self.D_T_FMT)
        return datetime.datetime(time_tuple.tm_year, time_tuple.tm_mon,
            time_tuple.tm_mday, time_tuple.tm_hour, time_tuple.tm_min, time_tuple.tm_sec)

    def convert_date(self, value):
        if type(value) in string_types:
            try:
                return datetime.datetime.strptime(value, '%Y-%m-%d').date()
            except:
                return self.convert_date_time(value).date()
        else:
            return value

    def convert_date_time(self, value):
        if type(value) in string_types:
            if value.find('T'):
                value = value.replace('T', ' ')
            try:
                return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            except:
                return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        else:
            return value


consts = Consts()

def error_message(e):
    try:
        return str(e)
    except:
        return unicode(e)

def json_defaul_handler(obj):
    result = obj
    if hasattr(obj, 'isoformat'):
        result = obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        result = float(obj)
    elif isinstance(obj, object):
        result = 'Object'
    return result

def compressBuf(buf):
    zbuf = StringIO()
    zfile = gzip.GzipFile(mode = 'wb',  fileobj = zbuf, compresslevel = 9)
    zfile.write(buf.encode())
    zfile.close()
    return zbuf.getvalue()

def file_read(filename):
    with open(filename, 'rb') as f:
        return to_unicode(f.read(), 'utf-8', errors='ignore')

def file_write(filename, data):
    with open(filename, 'wb') as f:
        f.write(to_bytes(data, 'utf-8', errors='ignore'))

def cur_to_str(value):
    return consts.cur_to_str(value)

def float_to_str(value):
    consts.float_to_str(value)

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

def valid_uploaded_file(accept, ext):
    if not accept:
        return True
    exts = get_ext_list(accept)
    if ext in exts:
        return True

def get_ext_list(accept):
    result = []
    l = accept.split(',')
    for t in l:
        t = t.strip()
        if t == 'image/*':
            result += consts.IMAGE_EXT
        elif t == 'audio/*':
            result += consts.AUDIO_EXT
        elif t == 'video/*':
            result += consts.VIDEO_EXT
        else:
            if t[0] != '.':
                raise Exception("File extension must start with '.'")
            result.append(t)
    return result
