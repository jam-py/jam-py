import os
import sqlite3
from werkzeug._compat import iteritems
import jam

def get_langs():
    con = sqlite3.connect(os.path.join(os.path.dirname(jam.__file__), 'langs.sqlite'))
    cursor = con.cursor()
    cursor.execute('SELECT ID, F_NAME FROM JAM_LANG')
    result = cursor.fetchall()
    con.close()
    return result

def get_dict(language):
    con = sqlite3.connect(os.path.join(os.path.dirname(jam.__file__), 'langs.sqlite'))
    cursor = con.cursor()
    cursor.execute('''
        SELECT JAM_LANG_KEYS.F_KEYWORD, F_VALUE
        FROM JAM_LANG_VALUES LEFT OUTER JOIN JAM_LANG_KEYS ON JAM_LANG_KEYS.ID = JAM_LANG_VALUES.F_KEY
        WHERE F_LANG = %s
    ''' % language)
    res = cursor.fetchall()
    con.close()
    result = {}
    for key, value in res:
        result[key] = value
    return result

def get_lang_dict(language):
    if language == 1:
        lang = get_dict(language)
    else:
        en_lang = get_dict(1)
        lang = get_dict(language)
        for key, value in iteritems(en_lang):
            if not lang.get(key):
                lang[key] = value
    for key, value in iteritems(lang):
        if value[0] == '[' and value[len(value) - 1] == ']':
            value = value[1:-1].split(', ')
            lang[key] = [s.strip() for s in value]
    return lang
