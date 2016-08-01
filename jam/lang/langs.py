# -*- coding: utf-8 -*-

ENG, RUS, HUN, POR = range(1, 5)
LANGUAGE = ('English', 'Russian', 'Hungarian', 'Portuguese')

def get_lang_dict(language):
    if language == ENG:
        import english as lang
    elif language == RUS:
        import russian as lang
    elif language == HUN:
        import hungarian as lang
    elif language == POR:
        import portuguese as lang
    return lang.dictionary
