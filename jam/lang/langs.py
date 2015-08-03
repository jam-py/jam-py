# -*- coding: utf-8 -*-

ENG, RUS, FR = range(1, 4)
LANGUAGE = ('English', 'Russian', 'French')

def get_lang_dict(language):
    if language == ENG:
        import english as lang
    elif language == RUS:
        import russian as lang
    elif language == FR:
        import french as lang
    return lang.dictionary
