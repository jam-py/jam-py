# -*- coding: utf-8 -*-

ENG, RUS = range(1, 3)
LANGUAGE = ('English', 'Russian')

def get_lang_dict(language):
    if language == ENG:
        import english as lang
    elif language == RUS:
        import russian as lang
    return lang.dictionary
