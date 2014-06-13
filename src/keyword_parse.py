def keywordParse(elementTree,KW_TYPE):
    """

    :param elementTree: Element tree passed in
    :param KW_TYPE: "themekey or placekey"
    :return:
    """
    try:
        kw = list(elementTree.iter(KW_TYPE))

        if len(kw) > 0:
            kw_str = [i.text for i in kw][0]
            return kw_str
        else:
            return 'None'
    except AttributeError as e:
        print "can't find keywords. Setting to UNKNOWN for now"
        return "UNKNOWN"
