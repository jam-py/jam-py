# -*- coding: utf-8 -*-

ENG, RUS ,HUN = range(1, 4)
LANGUAGE = ('English', 'Russian','Hungarian')

def get_lang_dict(language):
    if language == ENG:
        import english as lang
    elif language == RUS:
        import russian as lang
    elif language == HUN:
        import hungarian as lang
    return lang.dictionary
