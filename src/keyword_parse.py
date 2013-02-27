def keywordParse(FGDCtree,KW_TYPE):
    try:
        kw = list(FGDCtree.iter(KW_TYPE))
        kw_text = []
        if len(kw_text) > 1:
            keywords = ', '
            print 'keywords are : ', keywords.join(kw_text).rstrip(", ")
            return keywords.join(kw_text).rstrip(", ")
        if len(kw_text) == 1:
            return kw_text[0]
        else:
            return 'None'
    except AttributeError as e:
        print "can't find keywords. Setting to UNKNOWN for now"
        return "UNKNOWN"
