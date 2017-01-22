
ENG, RUS = range(1, 3)
LANGUAGE = ('English', 'Russian')

#~ ENG, RUS, HUN, POR = range(1, 5)
#~ LANGUAGE = ('English', 'Russian', 'Hungarian', 'Portuguese')

def get_lang_dict(language):
    if language == ENG:
        import english as lang
    elif language == RUS:
        import english as en_lang
        import russian as lang
        for key, value in en_lang.dictionary.iteritems():
            if not lang.dictionary.get(key):
                lang.dictionary[key] = value
    for key, value in lang.dictionary.iteritems():
        if value[0] == '[' and value[len(value) - 1] == ']':
            value = value[1:-1].split(', ')
            lang.dictionary[key] = [s.strip() for s in value]
    return lang.dictionary
