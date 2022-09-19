import os
import sqlite3
import json
import datetime
from shutil import copyfile

import jam

LANG_FIELDS = ['id', 'f_name', 'f_language', 'f_country', 'f_abr', 'f_rtl']
LOCALE_FIELDS = [
    'f_decimal_point', 'f_mon_decimal_point',
    'f_mon_thousands_sep', 'f_currency_symbol', 'f_frac_digits', 'f_p_cs_precedes',
    'f_n_cs_precedes', 'f_p_sep_by_space', 'f_n_sep_by_space', 'f_positive_sign',
    'f_negative_sign', 'f_p_sign_posn', 'f_n_sign_posn', 'f_d_fmt', 'f_d_t_fmt'
    ]

FIELDS = LANG_FIELDS + LOCALE_FIELDS

def lang_con(task):
    return sqlite3.connect(os.path.join(task.work_dir, 'langs.sqlite'))

def execute(task, sql, params=None):
    result = None
    con = lang_con(task)
    try:
        cursor = con.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        con.commit()
    except Exception as e:
        print(sql)
        raise Exception(e)
    finally:
        con.close()

def select(task, sql):
    result = None
    con = lang_con(task)
    try:
        cursor = con.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        con.rollback()
    except Exception as e:
        print(sql)
        raise Exception(e)
    finally:
        con.close()
    return result

def copy_table(cursor, name):
    cursor.execute('DROP TABLE IF EXISTS SYS_%s' % name)
    cursor.execute("SELECT sql FROM LANGS.sqlite_master WHERE type='table' AND name='JAM_%s'" % name)
    sql = cursor.fetchone()[0]
    cursor.execute(sql.replace('JAM_%s' % name, 'SYS_%s' % name))
    cursor.execute('INSERT INTO SYS_%s SELECT * FROM LANGS.JAM_%s' % (name, name))

def update_langs(task):
    with task.lock('$langs'):
        con = task.create_connection()
        try:
            cursor = con.cursor()
            try:
                cursor.execute('ALTER TABLE SYS_PARAMS ADD COLUMN F_JAM_VERSION TEXT')
            except:
                pass
            cursor.execute('SELECT F_JAM_VERSION, F_LANGUAGE FROM SYS_PARAMS')
            res = cursor.fetchall()
            version = res[0][0]
            language = res[0][1]
            langs_path = os.path.join(task.work_dir, 'langs.sqlite')
            if version != task.app.jam_version or not os.path.exists(langs_path):
                # ~ task.log.info('Version changed!')
                copyfile(os.path.join(os.path.dirname(jam.__file__), 'langs.sqlite'), langs_path)
                os.chmod(os.path.join(task.work_dir, 'langs.sqlite'), 0o666)
                cursor.execute('SELECT ID, F_NAME FROM SYS_LANGS')
                langs = cursor.fetchall()
                langs_list = []
                langs_dict = {}
                for l in langs:
                    langs_list.append(l[1])
                    langs_dict[l[1]] = l[0]
                res = select(task, 'SELECT %s FROM JAM_LANGS ORDER BY ID' % ', '.join(FIELDS))
                for r in res:
                    if langs_dict.get(r[1]):
                        del langs_dict[r[1]]
                    if not r[1] in langs_list:
                        fields = ['DELETED']
                        values = ['?']
                        field_values = [0]
                        for i, value in enumerate(r):
                            if i > 0:
                                fields.append(FIELDS[i])
                                values.append('?')
                                field_values.append(value)
                        sql = "INSERT INTO SYS_LANGS (%s) VALUES (%s)" % (','.join(fields), ','.join(values))
                        cursor.execute(sql, (field_values))
                del_langs = list(langs_dict.values())
                if len(del_langs):
                    if language in del_langs:
                        language = 1
                    sql = "DELETE FROM SYS_LANGS WHERE ID IN (%s)" % ','.join([str(d) for d in del_langs])
                    cursor.execute(sql)
                if language is None:
                    language = 'NULL'
                cursor.execute("UPDATE SYS_PARAMS SET F_JAM_VERSION='%s', F_LANGUAGE=%s" % (task.app.jam_version, language))
                con.commit()
        finally:
            con.close()

def init_locale():
    import locale
    result = {}
    try:
        locale.setlocale(locale.LC_ALL, '')
        loc = locale.localeconv()
        for field in LOCALE_FIELDS:
            setting = field[2:]
            try:
                result[field] = jam.common.to_str(loc[setting], 'utf-8')
            except:
                result[field] = jam.common.DEFAULT_LOCALE[setting.upper()]
    except:
        pass
    try:
        result['f_d_fmt'] = locale.nl_langinfo(locale.D_FMT)
    except:
        result['f_d_fmt'] = '%Y-%m-%d'
    result['f_d_t_fmt'] = '%s %s' % (result['f_d_fmt'], '%H:%M')
    return result

def get_lang_dict(task, language):
    res = select(task, '''
        SELECT K.F_KEYWORD,
            CASE WHEN TRIM(V1.F_VALUE) <> ''
                THEN V1.F_VALUE
                ELSE V2.F_VALUE
            END
        FROM JAM_LANG_KEYS AS K
        LEFT OUTER JOIN JAM_LANG_VALUES AS V1 ON (K.ID = V1.F_KEY AND V1.F_LANG = %s)
        LEFT OUTER JOIN JAM_LANG_VALUES AS V2 ON (K.ID = V2.F_KEY AND V2.F_LANG = %s)
    ''' % (language, 1))
    result = {}
    for key, value in res:
        result[key] = value
    return result

def get_locale_dict(task, language):
    result = {}
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute('SELECT %s FROM SYS_LANGS WHERE ID=%s' % (', '.join(LOCALE_FIELDS), language))
        res = cursor.fetchall()
        if len(res):
            for i, field in enumerate(LOCALE_FIELDS):
                result[field[2:].upper()] = res[0][i]
        else:
            raise Exception('Language with id %s is not found' % language)
        con.rollback()
    except:
        result = jam.common.DEFAULT_LOCALE
    finally:
        con.close()
    return result

def get_translation(task, lang1, lang2):
    res = select(task, '''
        SELECT K.ID, K.F_KEYWORD, V1.F_VALUE, V2.F_VALUE
        FROM JAM_LANG_KEYS AS K
        LEFT OUTER JOIN JAM_LANG_VALUES AS V1 ON (K.ID = V1.F_KEY AND V1.F_LANG = %s)
        LEFT OUTER JOIN JAM_LANG_VALUES AS V2 ON (K.ID = V2.F_KEY AND V2.F_LANG = %s)
    ''' % (lang1, lang2))
    return res

def add_lang(task, lang_id, language, country, name, abr, rtl, copy_lang):
    con = lang_con(task)
    try:
        cursor = con.cursor()
        locale = init_locale()
        fields = []
        values = []
        field_values = []
        for key, value in locale.items():
            fields.append(key)
            values.append('?')
            field_values.append(jam.common.to_str(value, 'utf-8'))
        cursor.execute("INSERT INTO JAM_LANGS (ID, F_LANGUAGE, F_COUNTRY, F_NAME, F_ABR, F_RTL, %s) VALUES (?,?,?,?,?,?,%s)" % (','.join(fields), ','.join(values)),
            ([lang_id, language, country, name, abr, rtl] + field_values))
        if copy_lang:
            cursor.execute('''
                SELECT JAM_LANG_KEYS.ID, F_VALUE
                FROM JAM_LANG_VALUES LEFT OUTER JOIN JAM_LANG_KEYS ON JAM_LANG_KEYS.ID = JAM_LANG_VALUES.F_KEY
                WHERE F_LANG = %s
            ''' % copy_lang)
            res = cursor.fetchall()
            recs = []
            for key_id, value in res:
                recs.append((key_id, lang_id, value))
            cursor.executemany("INSERT INTO JAM_LANG_VALUES(F_KEY, F_LANG, F_VALUE) VALUES (?,?,?)", recs)
        con.commit()
        langs = task.sys_langs.copy()
        langs.set_where(id=lang_id)
        langs.open()
        if langs.record_count():
            langs.edit()
            for key, value in locale.items():
                langs.field_by_name(key).value = jam.common.to_str(value, 'utf-8')
            langs.post()
            langs.apply()
    finally:
        con.close()

def save_lang_field(task, lang_id, field_name, value):
    execute(task, 'UPDATE JAM_LANGS SET %s=? WHERE ID=%s' % (field_name, lang_id), (value,))
    con = task.create_connection()
    try:
        cursor = con.cursor()
        cursor.execute('UPDATE SYS_LANGS SET %s=? WHERE ID=%s' % (field_name, lang_id), (value,))
        con.commit()
    finally:
        con.close()
    if task.language == lang_id:
        task.update_lang(lang_id)

def save_translation(task, lang_id, key_id, value):
    res = select(task, 'SELECT ID FROM JAM_LANG_VALUES WHERE F_LANG=%s AND F_KEY=%s' % (lang_id, key_id))
    if len(res):
        execute(task, 'UPDATE JAM_LANG_VALUES SET F_VALUE=? WHERE ID=%s' % (res[0][0]), (value,))
    else:
        execute(task, 'INSERT INTO JAM_LANG_VALUES (F_LANG, F_KEY, F_VALUE) VALUES (?, ?, ?)', (lang_id, key_id, value))

def add_key(task, key):
    result = ''
    con = lang_con(task)
    try:
        cursor = con.cursor()
        cursor.execute("SELECT ID FROM JAM_LANG_KEYS WHERE F_KEYWORD='%s'" % key)
        res = cursor.fetchall()
        if len(res):
            result = 'Keyword exists'
        else:
            cursor.execute('INSERT INTO JAM_LANG_KEYS (F_KEYWORD) VALUES (?)', (key,))
        con.commit()
    finally:
        con.close()
    return result

def del_key(task, key_id):
    result = False
    con = lang_con(task)
    try:
        cursor = con.cursor()
        cursor.execute("DELETE FROM JAM_LANG_VALUES WHERE F_KEY=%s" % key_id)
        cursor.execute("DELETE FROM JAM_LANG_KEYS WHERE ID=%s" % key_id)
        con.commit()
        result = True
    finally:
        con.close()
    return result

def get_dict(task, language):
    res =  select(task, '''
            SELECT JAM_LANG_KEYS.F_KEYWORD, F_VALUE
            FROM JAM_LANG_VALUES LEFT OUTER JOIN JAM_LANG_KEYS ON JAM_LANG_KEYS.ID = JAM_LANG_VALUES.F_KEY
            WHERE F_LANG = %s
        ''' % language)
    result = {}
    for key, value in res:
        result[key] = value
    return result

def export_lang(task, lang_id, host):
    names = FIELDS[1:]
    lang = select(task, 'SELECT %s FROM JAM_LANGS WHERE ID=%s' % (', '.join(names), lang_id))
    if len(lang):
        language = {}
        for i in range(len(lang[0])):
            language[names[i]] = lang[0][i]

        translation = get_dict(task, lang_id)
        content = json.dumps({'language': language, 'translation': translation})

        name = language['f_name'].replace(' ', '_')
        file_name = '%s_%s.lang' % (name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        return {'file_name': file_name, 'content': content}

def import_lang(task, file_path):
    error = ''
    try:
        with open(file_path, 'r') as f:
            content = jam.common.to_str(f.read(), 'utf-8')
        content = json.loads(content)
        language = content['language']
        translation = content['translation']

        con = lang_con(task)
        sys_con = task.create_connection()
        try:
            cursor = con.cursor()
            cursor.execute('SELECT ID FROM JAM_LANGS WHERE F_LANGUAGE=%s AND F_COUNTRY=%s' % (language['f_language'], language['f_country']))
            res = cursor.fetchall()
            if len(res):
                lang_id = res[0][0]
                fields = []
                field_values = []
                for key, value in language.items():
                    fields.append('%s=?' % key)
                    field_values.append(value)
                fields = ',' .join(fields)
                cursor.execute("UPDATE JAM_LANGS SET %s WHERE ID=%s" % (fields, lang_id), field_values)

                sys_cursor = sys_con.cursor()
                sys_cursor.execute("UPDATE SYS_LANGS SET %s WHERE ID=%s" % (fields, lang_id), field_values)
                sys_con.commit()
            else:
                fields = []
                values = []
                field_values = []
                for key, value in language.items():
                    fields.append(key)
                    field_values.append(value)
                    values.append('?')
                cursor.execute('INSERT INTO JAM_LANGS (%s) VALUES (%s)' % (','.join(fields), ','.join(values)), field_values)
                cursor.execute('SELECT ID FROM JAM_LANGS WHERE F_LANGUAGE=%s AND F_COUNTRY=%s' % (language['f_language'], language['f_country']))
                res = cursor.fetchall()
                lang_id = res[0][0]
                fields.append('DELETED')
                values.append('?')
                field_values.append(0)
                sys_cursor = sys_con.cursor()
                sys_cursor.execute('INSERT INTO SYS_LANGS (%s) VALUES (%s)' % (','.join(fields), ','.join(values)), field_values)
                sys_con.commit()
            if lang_id:
                cursor.execute('SELECT ID, F_KEYWORD FROM JAM_LANG_KEYS')
                res = cursor.fetchall()
                keys = {}
                for r in res:
                    keys[r[1]] = r[0]
                recs = []
                for keyword, value in translation.items():
                    key_id = keys.get(keyword)
                    if key_id:
                        cursor.execute('SELECT ID FROM JAM_LANG_VALUES WHERE F_LANG=%s AND F_KEY=%s' % (lang_id, key_id))
                        res = cursor.fetchall()
                        if len(res):
                            cursor.execute('UPDATE JAM_LANG_VALUES SET F_VALUE=? WHERE ID=%s' % (res[0][0]), (value,))
                        else:
                            cursor.execute('INSERT INTO JAM_LANG_VALUES (F_LANG, F_KEY, F_VALUE) VALUES (?, ?, ?)', (lang_id, key_id, value))
            con.commit()
        finally:
            con.close()
            sys_con.close()
    except Exception as e:
        print(e)
        error = 'Can not import language'
