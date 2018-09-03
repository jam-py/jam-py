import os
import sqlite3
import json
import datetime
from werkzeug._compat import iteritems, to_bytes, to_unicode
import jam

LANG_FIELDS = ['id', 'f_name', 'f_language', 'f_country', 'f_abr', 'f_rtl']
LOCALE_FIELDS = [
    'f_decimal_point', 'f_mon_decimal_point',
    'f_mon_thousands_sep', 'f_currency_symbol', 'f_frac_digits', 'f_p_cs_precedes',
    'f_n_cs_precedes', 'f_p_sep_by_space', 'f_n_sep_by_space', 'f_positive_sign',
    'f_negative_sign', 'f_p_sign_posn', 'f_n_sign_posn', 'f_d_fmt', 'f_d_t_fmt'
    ]

FIELDS = LANG_FIELDS + LOCALE_FIELDS

def langs_path():
    return os.path.join(os.path.dirname(jam.__file__), 'langs.sqlite')

def lang_con():
    return sqlite3.connect(langs_path())

def execute(sql, params=None):
    result = None
    con = lang_con()
    try:
        cursor = con.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        if sql.find('SELECT') != -1 or sql.find('select') != -1:
            result = cursor.fetchall()
            con.rollback()
        else:
            con.commit()
    except Exception as e:
        print(sql)
        raise Exception(e)
    finally:
        con.close()
    return result

def fill_table(cursor, table_name):
    if table_name == 'JAM_LANGUAGES':
        for name, abr, rtl in languages:
            cursor.execute("INSERT INTO JAM_LANGUAGES (F_NAME, F_ABR, F_RTL, DELETED) values (?, ?, ?, ?)", (name, abr, rtl, 0))
    if table_name == 'JAM_COUNTRIES':
        for name, abr in countries:
            cursor.execute("INSERT INTO JAM_COUNTRIES (F_NAME, F_ABR, DELETED) values (?, ?, ?)", (name, abr, 0))

def check_table(table_name):
    con = lang_con()
    try:
        cursor = con.cursor()
        sql = 'SELECT name FROM sqlite_master WHERE type="table" AND UPPER(name)="%s"' % table_name
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            if table_name == 'JAM_LANGUAGES':
                sql = 'CREATE TABLE %s (ID INTEGER PRIMARY KEY, F_NAME TEXT, F_ABR TEXT, F_RTL INTEGER, DELETED INTEGER)' % table_name
            if table_name == 'JAM_COUNTRIES':
                sql = 'CREATE TABLE %s (ID INTEGER PRIMARY KEY, F_NAME TEXT, F_ABR TEXT, DELETED INTEGER)' % table_name
            cursor.execute(sql)
            fill_table(cursor, table_name)
        con.commit()
    finally:
        con.close()

def init_tables(cursor):
    cursor.execute('DROP TABLE IF EXISTS SYS_LANGUAGES')
    cursor.execute('DROP TABLE IF EXISTS SYS_COUNTRIES')
    cursor.execute('ATTACH DATABASE "%s" AS LANGS' % langs_path())
    cursor.execute("SELECT sql FROM LANGS.sqlite_master WHERE type='table' AND name='JAM_LANGUAGES'")
    cursor.execute(cursor.fetchone()[0].replace('JAM_LANGUAGES', 'SYS_LANGUAGES'))
    cursor.execute('INSERT INTO SYS_LANGUAGES SELECT * FROM LANGS.JAM_LANGUAGES')
    cursor.execute("SELECT sql FROM LANGS.sqlite_master WHERE type='table' AND name='JAM_COUNTRIES'")
    cursor.execute(cursor.fetchone()[0].replace('JAM_COUNTRIES', 'SYS_COUNTRIES'))
    cursor.execute('INSERT INTO SYS_COUNTRIES SELECT * FROM LANGS.JAM_COUNTRIES')

def update_langs(task):
    con = sqlite3.connect(os.path.join(task.work_dir, 'admin.sqlite'))
    try:
        #~ check_table('JAM_LANGUAGES')
        #~ check_table('JAM_COUNTRIES')
        cursor = con.cursor()
        init_tables(cursor)
        cursor.execute('SELECT F_NAME FROM SYS_LANGS')
        langs = cursor.fetchall()
        langs_list = []
        for l in langs:
            langs_list.append(l[0])
        res = execute('SELECT %s FROM JAM_LANGS ORDER BY ID' % ', '.join(FIELDS))
        #~ index = FIELDS.index('f_d_fmt')
        for r in res:
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
                result[field] = to_unicode(loc[setting], 'utf-8')
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

def get_lang_dict(language):
    res = execute('''
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
    con = sqlite3.connect(os.path.join(task.work_dir, 'admin.sqlite'))
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

def get_lang_translation(lang1, lang2):
    res = execute('''
        SELECT K.ID, K.F_KEYWORD, V1.F_VALUE, V2.F_VALUE
        FROM JAM_LANG_KEYS AS K
        LEFT OUTER JOIN JAM_LANG_VALUES AS V1 ON (K.ID = V1.F_KEY AND V1.F_LANG = %s)
        LEFT OUTER JOIN JAM_LANG_VALUES AS V2 ON (K.ID = V2.F_KEY AND V2.F_LANG = %s)
    ''' % (lang1, lang2))
    return res

def add_lang(item, lang_id, language, country, name, abr, rtl, copy_lang):
    con = lang_con()
    try:
        cursor = con.cursor()
        locale = init_locale()
        fields = []
        values = []
        field_values = []
        for key, value in iteritems(locale):
            fields.append(key)
            values.append('?')
            field_values.append(to_unicode(value, 'utf-8'))
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
        langs = item.copy()
        langs.set_where(id=lang_id)
        langs.open()
        if langs.record_count():
            langs.edit()
            for key, value in iteritems(locale):
                langs.field_by_name(key).value = to_unicode(value, 'utf-8')
            langs.post()
            langs.apply()
    finally:
        con.close()

def save_lang_field(item, lang_id, field_name, value):
    execute('UPDATE JAM_LANGS SET %s=? WHERE ID=%s' % (field_name, lang_id), (value,))
    con = sqlite3.connect(os.path.join(item.task.work_dir, 'admin.sqlite'))
    try:
        cursor = con.cursor()
        cursor.execute('UPDATE SYS_LANGS SET %s=? WHERE ID=%s' % (field_name, lang_id), (value,))
        con.commit()
    finally:
        con.close()
    if item.task.language == lang_id:
        item.task.update_lang(lang_id)

def save_lang_translation(item, lang_id, key_id, value):
    res = execute('SELECT ID FROM JAM_LANG_VALUES WHERE F_LANG=%s AND F_KEY=%s' % (lang_id, key_id))
    if len(res):
        execute('UPDATE JAM_LANG_VALUES SET F_VALUE=? WHERE ID=%s' % (res[0][0]), (value,))
    else:
        execute('INSERT INTO JAM_LANG_VALUES (F_LANG, F_KEY, F_VALUE) VALUES (?, ?, ?)', (lang_id, key_id, value))
    item.task.update_lang(lang_id)

def add_key(key):
    result = ''
    con = lang_con()
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

def del_key(key_id):
    result = False
    con = lang_con()
    try:
        cursor = con.cursor()
        cursor.execute("DELETE FROM JAM_LANG_VALUES WHERE F_KEY=%s" % key_id)
        cursor.execute("DELETE FROM JAM_LANG_KEYS WHERE ID=%s" % key_id)
        con.commit()
        result = True
    finally:
        con.close()
    return result

def get_dict(language):
    res =  execute('''
            SELECT JAM_LANG_KEYS.F_KEYWORD, F_VALUE
            FROM JAM_LANG_VALUES LEFT OUTER JOIN JAM_LANG_KEYS ON JAM_LANG_KEYS.ID = JAM_LANG_VALUES.F_KEY
            WHERE F_LANG = %s
        ''' % language)
    result = {}
    for key, value in res:
        result[key] = value
    return result

def export_lang(work_dir, lang_id, host):
    names = FIELDS[1:]
    lang = execute('SELECT %s FROM JAM_LANGS WHERE ID=%s' % (', '.join(names), lang_id))
    if len(lang):
        language = {}
        for i in range(len(lang[0])):
            language[names[i]] = lang[0][i]

        translation = get_dict(lang_id)
        content = json.dumps({'language': language, 'translation': translation})

        name = language['f_name'].replace(' ', '_')
        file_name = '%s_%s.lang' % (name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        return {'file_name': file_name, 'content': content}

def import_lang(task, file_path):
    error = ''
    try:
        with open(file_path, 'r') as f:
            content = to_unicode(f.read(), 'utf-8')
        content = json.loads(content)
        language = content['language']
        translation = content['translation']

        con = lang_con()
        try:
            cursor = con.cursor()
            cursor.execute('SELECT ID FROM JAM_LANGS WHERE F_LANGUAGE=%s AND F_COUNTRY=%s' % (language['f_language'], language['f_country']))
            res = cursor.fetchall()
            if len(res):
                lang_id = res[0][0]
                fields = []
                field_values = []
                for key, value in iteritems(language):
                    fields.append('%s=?' % key)
                    field_values.append(value)
                fields = ',' .join(fields)
                cursor.execute("UPDATE JAM_LANGS SET %s WHERE ID=%s" % (fields, lang_id), field_values)

                sys_con = sqlite3.connect(os.path.join(task.work_dir, 'admin.sqlite'))
                try:
                    sys_cursor = sys_con.cursor()
                    sys_cursor.execute("UPDATE SYS_LANGS SET %s WHERE ID=%s" % (fields, lang_id), field_values)
                    sys_con.commit()
                finally:
                    sys_con.close()

                #~ try:
                #~ except:
                    #~ pass
            else:
                fields = []
                values = []
                field_values = []
                for key, value in iteritems(language):
                    fields.append(key)
                    field_values.append(value)
                    values.append('?')
                fields = ','.join(fields)
                values = ','.join(values)
                cursor.execute('INSERT INTO JAM_LANGS (%s) VALUES (%s)' % (fields, values), field_values)
                cursor.execute('SELECT ID FROM JAM_LANGS WHERE F_LANGUAGE=%s AND F_COUNTRY=%s' % (language['f_language'], language['f_country']))
                res = cursor.fetchall()
                lang_id = res[0][0]
            if lang_id:
                cursor.execute('SELECT ID, F_KEYWORD FROM JAM_LANG_KEYS')
                res = cursor.fetchall()
                keys = {}
                for r in res:
                    keys[r[1]] = r[0]
                recs = []
                for keyword, value in iteritems(translation):
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
    except Exception as e:
        print(e)
        error = 'Can not import language'
    update_langs(task)

languages = [
    ["Abkhazian", "ab", False],
    ["Afar", "aa", False],
    ["Afrikaans", "af", False],
    ["Akan", "ak", False],
    ["Albanian", "sq", False],
    ["Amharic", "am", False],
    ["Arabic", "ar", True],
    ["Aragonese", "an", False],
    ["Armenian", "hy", False],
    ["Assamese", "as", False],
    ["Avaric", "av", False],
    ["Avestan", "ae", False],
    ["Aymara", "ay", False],
    ["Azerbaijani", "az", False],
    ["Bambara", "bm", False],
    ["Bashkir", "ba", False],
    ["Basque", "eu", False],
    ["Belarusian", "be", False],
    ["Bengali (Bangla)", "bn", False],
    ["Bihari", "bh", False],
    ["Bislama", "bi", False],
    ["Bosnian", "bs", False],
    ["Breton", "br", False],
    ["Bulgarian", "bg", False],
    ["Burmese", "my", False],
    ["Catalan", "ca", False],
    ["Chamorro", "ch", False],
    ["Chechen", "ce", False],
    ["Chichewa, Chewa, Nyanja", "ny", False],
    ["Chinese", "zh", False],
    ["Chinese (Simplified)", "zh-Hans", False],
    ["Chinese (Traditional)", "zh-Hant", False],
    ["Chuvash", "cv", False],
    ["Cornish", "kw", False],
    ["Corsican", "co", False],
    ["Cree", "cr", False],
    ["Croatian", "hr", False],
    ["Czech", "cs", False],
    ["Danish", "da", False],
    ["Divehi, Dhivehi, Maldivian", "dv", False],
    ["Dutch", "nl", False],
    ["Dzongkha", "dz", False],
    ["English", "en", False],
    ["Esperanto", "eo", False],
    ["Estonian", "et", False],
    ["Ewe", "ee", False],
    ["Faroese", "fo", False],
    ["Fijian", "fj", False],
    ["Finnish", "fi", False],
    ["French", "fr", False],
    ["Fula, Fulah, Pulaar, Pular", "ff", False],
    ["Galician", "gl", False],
    ["Gaelic (Scottish)", "gd", False],
    ["Gaelic (Manx)", "gv", False],
    ["Georgian", "ka", False],
    ["German", "de", False],
    ["Greek", "el", False],
    ["Greenlandic", "kl", False],
    ["Guarani", "gn", False],
    ["Gujarati", "gu", False],
    ["Haitian Creole", "ht", False],
    ["Hausa", "ha", False],
    ["Hebrew", "he", True],
    ["Herero", "hz", False],
    ["Hindi", "hi", False],
    ["Hiri Motu", "ho", False],
    ["Hungarian", "hu", False],
    ["Icelandic", "is", False],
    ["Ido", "io", False],
    ["Igbo", "ig", False],
    ["Indonesian", "id, in", False],
    ["Interlingua", "ia", False],
    ["Interlingue", "ie", False],
    ["Inuktitut", "iu", False],
    ["Inupiak", "ik", False],
    ["Irish", "ga", False],
    ["Italian", "it", False],
    ["Japanese", "ja", False],
    ["Javanese", "jv", False],
    ["Kalaallisut, Greenlandic", "kl", False],
    ["Kannada", "kn", False],
    ["Kanuri", "kr", False],
    ["Kashmiri", "ks", False],
    ["Kazakh", "kk", False],
    ["Khmer", "km", False],
    ["Kikuyu", "ki", False],
    ["Kinyarwanda (Rwanda)", "rw", False],
    ["Kirundi", "rn", False],
    ["Kyrgyz", "ky", False],
    ["Komi", "kv", False],
    ["Kongo", "kg", False],
    ["Korean", "ko", False],
    ["Kurdish", "ku", False],
    ["Kwanyama", "kj", False],
    ["Lao", "lo", False],
    ["Latin", "la", False],
    ["Latvian (Lettish)", "lv", False],
    ["Limburgish ( Limburger)", "li", False],
    ["Lingala", "ln", False],
    ["Lithuanian", "lt", False],
    ["Luga-Katanga", "lu", False],
    ["Luganda, Ganda", "lg", False],
    ["Luxembourgish", "lb", False],
    ["Manx", "gv", False],
    ["Macedonian", "mk", False],
    ["Malagasy", "mg", False],
    ["Malay", "ms", False],
    ["Malayalam", "ml", False],
    ["Maltese", "mt", False],
    ["Maori", "mi", False],
    ["Marathi", "mr", False],
    ["Marshallese", "mh", False],
    ["Moldavian", "mo", False],
    ["Mongolian", "mn", False],
    ["Nauru", "na", False],
    ["Navajo", "nv", False],
    ["Ndonga", "ng", False],
    ["Northern Ndebele", "nd", False],
    ["Nepali", "ne", False],
    ["Norwegian", "no", False],
    ["Norwegian bokmal", "nb", False],
    ["Norwegian nynorsk", "nn", False],
    ["Nuosu", "ii", False],
    ["Occitan", "oc", False],
    ["Ojibwe", "oj", False],
    ["Old Church Slavonic, Old Bulgarian", "cu", False],
    ["Oriya", "or", False],
    ["Oromo (Afaan Oromo)", "om", False],
    ["Ossetian", "os", False],
    ["Pali", "pi", False],
    ["Pashto, Pushto", "ps", False],
    ["Persian (Farsi)", "fa", False],
    ["Polish", "pl", False],
    ["Portuguese", "pt", False],
    ["Punjabi (Eastern)", "pa", False],
    ["Quechua", "qu", False],
    ["Romansh", "rm", False],
    ["Romanian", "ro", False],
    ["Russian", "ru", False],
    ["Sami", "se", False],
    ["Samoan", "sm", False],
    ["Sango", "sg", False],
    ["Sanskrit", "sa", False],
    ["Serbian", "sr", False],
    ["Serbo-Croatian", "sh", False],
    ["Sesotho", "st", False],
    ["Setswana", "tn", False],
    ["Shona", "sn", False],
    ["Sichuan Yi", "ii", False],
    ["Sindhi", "sd", False],
    ["Sinhalese", "si", False],
    ["Siswati", "ss", False],
    ["Slovak", "sk", False],
    ["Slovenian", "sl", False],
    ["Somali", "so", False],
    ["Southern Ndebele", "nr", False],
    ["Spanish", "es", False],
    ["Sundanese", "su", False],
    ["Swahili (Kiswahili)", "sw", False],
    ["Swati", "ss", False],
    ["Swedish", "sv", False],
    ["Tagalog", "tl", False],
    ["Tahitian", "ty", False],
    ["Tajik", "tg", False],
    ["Tamil", "ta", False],
    ["Tatar", "tt", False],
    ["Telugu", "te", False],
    ["Thai", "th", False],
    ["Tibetan", "bo", False],
    ["Tigrinya", "ti", False],
    ["Tonga", "to", False],
    ["Tsonga", "ts", False],
    ["Turkish", "tr", False],
    ["Turkmen", "tk", False],
    ["Twi", "tw", False],
    ["Uyghur", "ug", False],
    ["Ukrainian", "uk", False],
    ["Urdu", "ur", False],
    ["Uzbek", "uz", False],
    ["Venda", "ve", False],
    ["Vietnamese", "vi", False],
    ["Volapuk", "vo", False],
    ["Wallon", "wa", False],
    ["Welsh", "cy", False],
    ["Wolof", "wo", False],
    ["Western Frisian", "fy", False],
    ["Xhosa", "xh", False],
    ["Yiddish", "yi, ji", True],
    ["Yoruba", "yo", False],
    ["Zhuang, Chuang", "za", False],
    ["Zulu", "zu", False]
]

countries = [
    ["AFGHANISTAN", "AF"],
    ["ALBANIA", "AL"],
    ["ALGERIA", "DZ"],
    ["AMERICAN SAMOA", "AS"],
    ["ANDORRA", "AD"],
    ["ANGOLA", "AO"],
    ["ANTARCTICA", "AQ"],
    ["ANTIGUA AND BARBUDA", "AG"],
    ["ARGENTINA", "AR"],
    ["ARMENIA", "AM"],
    ["ARUBA", "AW"],
    ["AUSTRALIA", "AU"],
    ["AUSTRIA", "AT"],
    ["AZERBAIJAN", "AZ"],
    ["BAHAMAS", "BS"],
    ["BAHRAIN", "BH"],
    ["BANGLADESH", "BD"],
    ["BARBADOS", "BB"],
    ["BELARUS", "BY"],
    ["BELGIUM", "BE"],
    ["BELIZE", "BZ"],
    ["BENIN", "BJ"],
    ["BERMUDA", "BM"],
    ["BHUTAN", "BT"],
    ["BOLIVIA", "BO"],
    ["BOSNIA AND HERZEGOVINA", "BA"],
    ["BOTSWANA", "BW"],
    ["BOUVET ISLAND", "BV"],
    ["BRAZIL", "BR"],
    ["BRITISH INDIAN OCEAN TERRITORY", "IO"],
    ["BRUNEI DARUSSALAM", "BN"],
    ["BULGARIA", "BG"],
    ["BURKINA FASO", "BF"],
    ["BURUNDI", "BI"],
    ["CAMBODIA", "KH"],
    ["CAMEROON", "CM"],
    ["CANADA", "CA"],
    ["CAPE VERDE", "CV"],
    ["CAYMAN ISLANDS", "KY"],
    ["CENTRAL AFRICAN REPUBLIC", "CF"],
    ["CHAD", "TD"],
    ["CHILE", "CL"],
    ["CHINA", "CN"],
    ["CHRISTMAS ISLAND", "CX"],
    ["COCOS (KEELING) ISLANDS", "CC"],
    ["COLOMBIA", "CO"],
    ["COMOROS", "KM"],
    ["CONGO", "CG"],
    ["CONGO, THE DEMOCRATIC REPUBLIC OF THE", "CD"],
    ["COOK ISLANDS", "CK"],
    ["COSTA RICA", "CR"],
    ["COTE D'IVOIRE", "CI"],
    ["CROATIA", "HR"],
    ["CUBA", "CU"],
    ["CYPRUS", "CY"],
    ["CZECH REPUBLIC", "CZ"],
    ["DENMARK", "DK"],
    ["DJIBOUTI", "DJ"],
    ["DOMINICA", "DM"],
    ["DOMINICAN REPUBLIC", "DO"],
    ["ECUADOR", "EC"],
    ["EGYPT", "EG"],
    ["EL SALVADOR", "SV"],
    ["EQUATORIAL GUINEA", "GQ"],
    ["ERITREA", "ER"],
    ["ESTONIA", "EE"],
    ["ETHIOPIA", "ET"],
    ["FALKLAND ISLANDS (MALVINAS)", "FK"],
    ["FAROE ISLANDS", "FO"],
    ["FIJI", "FJ"],
    ["FINLAND", "FI"],
    ["FRANCE", "FR"],
    ["FRENCH GUIANA", "GF"],
    ["FRENCH POLYNESIA", "PF"],
    ["FRENCH SOUTHERN TERRITORIES", "TF"],
    ["GABON", "GA"],
    ["GAMBIA", "GM"],
    ["GEORGIA", "GE"],
    ["GERMANY", "DE"],
    ["GHANA", "GH"],
    ["GIBRALTAR", "GI"],
    ["GREECE", "GR"],
    ["GREENLAND", "GL"],
    ["GRENADA", "GD"],
    ["GUADELOUPE", "GP"],
    ["GUAM", "GU"],
    ["GUATEMALA", "GT"],
    ["GUINEA", "GN"],
    ["GUINEA-BISSAU", "GW"],
    ["GUYANA", "GY"],
    ["HAITI", "HT"],
    ["HEARD ISLAND AND MCDONALD ISLANDS", "HM"],
    ["HONDURAS", "HN"],
    ["HONG KONG", "HK"],
    ["HUNGARY", "HU"],
    ["ICELAND", "IS"],
    ["INDIA", "IN"],
    ["INDONESIA", "ID"],
    ["IRAN, ISLAMIC REPUBLIC OF", "IR"],
    ["IRAQ", "IQ"],
    ["IRELAND", "IE"],
    ["ISRAEL", "IL"],
    ["ITALY", "IT"],
    ["JAMAICA", "JM"],
    ["JAPAN", "JP"],
    ["JORDAN", "JO"],
    ["KAZAKHSTAN", "KZ"],
    ["KENYA", "KE"],
    ["KIRIBATI", "KI"],
    ["KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF", "KP"],
    ["KOREA, REPUBLIC OF", "KR"],
    ["KUWAIT", "KW"],
    ["KYRGYZSTAN", "KG"],
    ["LAO PEOPLE'S DEMOCRATIC REPUBLIC(LAOS)", "LA"],
    ["LATVIA", "LV"],
    ["LEBANON", "LB"],
    ["LESOTHO", "LS"],
    ["LIBERIA", "LR"],
    ["LIBYAN ARAB JAMAHIRIYA", "LY"],
    ["LIECHTENSTEIN", "LI"],
    ["LITHUANIA", "LT"],
    ["LUXEMBOURG", "LU"],
    ["MACAO", "MO"],
    ["MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF", "MK"],
    ["MADAGASCAR", "MG"],
    ["MALAWI", "MW"],
    ["MALAYSIA", "MY"],
    ["MALDIVES", "MV"],
    ["MALI", "ML"],
    ["MALTA", "MT"],
    ["MARSHALL ISLANDS", "MH"],
    ["MARTINIQUE", "MQ"],
    ["MAURITANIA", "MR"],
    ["MAURITIUS", "MU"],
    ["MAYOTTE", "YT"],
    ["MEXICO", "MX"],
    ["MICRONESIA, FEDERATED STATES OF", "FM"],
    ["MOLDOVA, REPUBLIC OF", "MD"],
    ["MONACO", "MC"],
    ["MONGOLIA", "MN"],
    ["MONTENEGRO", "ME"],
    ["MONTSERRAT", "MS"],
    ["MOROCCO", "MA"],
    ["MOZAMBIQUE", "MZ"],
    ["MYANMAR", "MM"],
    ["NAMIBIA", "NA"],
    ["NAURU", "NR"],
    ["NEPAL", "NP"],
    ["NETHERLANDS", "NL"],
    ["NETHERLANDS ANTILLES", "AN"],
    ["NEW CALEDONIA", "NC"],
    ["NEW ZEALAND", "NZ"],
    ["NICARAGUA", "NI"],
    ["NIGER", "NE"],
    ["NIGERIA", "NG"],
    ["NIUE", "NU"],
    ["NORFOLK ISLAND", "NF"],
    ["NORTHERN MARIANA ISLANDS", "MP"],
    ["NORWAY", "NO"],
    ["OMAN", "OM"],
    ["PAKISTAN", "PK"],
    ["PALAU", "PW"],
    ["PALESTINIAN TERRITORY, OCCUPIED", "PS"],
    ["PANAMA", "PA"],
    ["PAPUA NEW GUINEA", "PG"],
    ["PARAGUAY", "PY"],
    ["PERU", "PE"],
    ["PHILIPPINES", "PH"],
    ["PITCAIRN", "PN"],
    ["POLAND", "PL"],
    ["PORTUGAL", "PT"],
    ["PUERTO RICO", "PR"],
    ["QATAR", "QA"],
    ["REUNION", "RE"],
    ["ROMANIA", "RO"],
    ["RUSSIAN FEDERATION", "RU"],
    ["RWANDA", "RW"],
    ["SAINT HELENA", "SH"],
    ["SAINT KITTS AND NEVIS", "KN"],
    ["SAINT LUCIA", "LC"],
    ["SAINT PIERRE AND MIQUELON", "PM"],
    ["SAINT VINCENT AND THE GRENADINES", "VC"],
    ["SAMOA", "WS"],
    ["SAN MARINO", "SM"],
    ["SAO TOME AND PRINCIPE", "ST"],
    ["SAUDI ARABIA", "SA"],
    ["SENEGAL", "SN"],
    ["SERBIA", "RS"],
    ["SEYCHELLES", "SC"],
    ["SIERRA LEONE", "SL"],
    ["SINGAPORE", "SG"],
    ["SLOVAKIA", "SK"],
    ["SLOVENIA", "SI"],
    ["SOLOMON ISLANDS", "SB"],
    ["SOMALIA", "SO"],
    ["SOUTH AFRICA", "ZA"],
    ["SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS", "GS"],
    ["SPAIN", "ES"],
    ["SRI LANKA", "LK"],
    ["SUDAN", "SD"],
    ["SURINAME", "SR"],
    ["SVALBARD AND JAN MAYEN", "SJ"],
    ["SWAZILAND", "SZ"],
    ["SWEDEN", "SE"],
    ["SWITZERLAND", "CH"],
    ["SYRIAN ARAB REPUBLIC", "SY"],
    ["TAIWAN", "TW"],
    ["TAJIKISTAN", "TJ"],
    ["TANZANIA, UNITED REPUBLIC OF", "TZ"],
    ["THAILAND", "TH"],
    ["TIMOR-LESTE", "TL"],
    ["TOGO", "TG"],
    ["TOKELAU", "TK"],
    ["TONGA", "TO"],
    ["TRINIDAD AND TOBAGO", "TT"],
    ["TUNISIA", "TN"],
    ["TURKEY", "TR"],
    ["TURKMENISTAN", "TM"],
    ["TURKS AND CAICOS ISLANDS", "TC"],
    ["TUVALU", "TV"],
    ["UGANDA", "UG"],
    ["UKRAINE", "UA"],
    ["UNITED ARAB EMIRATES", "AE"],
    ["UNITED KINGDOM", "GB"],
    ["UNITED STATES", "US"],
    ["UNITED STATES MINOR OUTLYING ISLANDS", "UM"],
    ["URUGUAY", "UY"],
    ["UZBEKISTAN", "UZ"],
    ["VANUATU", "VU"],
    ["VENEZUELA", "VE"],
    ["VIET NAM", "VN"],
    ["VIRGIN ISLANDS, BRITISH", "VG"],
    ["VIRGIN ISLANDS, U.S.", "VI"],
    ["WALLIS AND FUTUNA", "WF"],
    ["WESTERN SAHARA", "EH"],
    ["YEMEN", "YE"],
    ["ZAMBIA", "ZM"],
    ["ZIMBABWE", "ZW"]
]
