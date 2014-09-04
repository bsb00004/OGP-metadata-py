import os, os.path
from datetime import datetime
try:
    from lxml import etree
except ImportError:
    try:
        print "\nPython lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported.\n"
        from xml.etree import ElementTree as etree
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"

def processListofFiles(listoffiles,output,md):
    if type(listoffiles) == list:

        if os.path.exists(output) == False:
            try:
                os.mkdir(output)
            except OSError:
                print "There's a problem with the output path: %s. Are you sure you entered it correctly?" % (output)

        for f in listoffiles:
            processFile(f,output,md)

def processFile(filename,output,md):
    
    md = md.lower()

    # build empty etree to house output doc
    OGPtree = etree.ElementTree()
    OGProot = etree.Element("add", allowDups="false")
    docElement = etree.SubElement(OGProot, "doc")
    OGPtree._setroot(OGProot)
    
    # parse the current XML into an etree
    tree = etree.ElementTree()
    root = tree.parse(filename)

    # grab the full text of the current XML for later use
    fullText = etree.tostring(root)
     
    if md == "mgmg":
        doc = MGMGDocument(root,filename)

    elif md == "fgdc":
        doc = FGDCDocument(root,filename)

    elif md == "arcgis":
        doc = ArcGISDocument(root,filename)

    elif md == "marc":
        doc = MARCXMLDocument(root,filename)

    for field in doc.field_handlers:
        try:
            fieldEle = etree.SubElement(docElement, "field", name=field)
            if hasattr(doc.field_handlers[field], '__call__'):
                fieldEle.text = doc.field_handlers[field].__call__()
            else:
                fieldEle.text = doc.field_handlers[field]

        except KeyError as e:
            print "Nonexistant key: ", field
    
    fullTextElement = etree.SubElement(docElement, "field", name="FgdcText")
    fullTextElement.text = fullText

    resultName =  os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_OGP.xml")
    
    #check for duplicate names (since w're looking across records with similar dataset content)
    # and add an _ to the end to avoid overwriting
    if os.path.exists(resultName):
        resultName = os.path.splitext(resultName)[0] + "_" + os.path.splitext(resultName)[1]

    print 'Writing: ' + resultName
    
    if "lxml" in etree.__name__:
        OGPtree.write(resultName, pretty_print=True)
    else:
        OGPtree.write(resultName)
        



class MetadataDocument(object):
    """
    Base class for metadata documents. This is where OGP fields that are handled the same
    across standards are implemented.
    """

    def __init__(self,root,file_name):
        self.root = root
        self.file_name = file_name

        # create a dictionary containing the OGP field names as keys, mapping
        # the corresponding class method (or hardcoded string) as value
        self.field_handlers = {

            # hardcoded values first
            "Access": "Public",
            "Availability": "Online",
            "Institution": "Minnesota",
            "InstitutionSort": "Minnesota",
            "CollectionId": "initial collection", 

            # plug in a few fixed vals for MGS
            #"Publisher": self.publisher,
            "Publisher": "Minnesota Geological Survey",
            #"PublisherSort": self.publisher,
            "PublisherSort": "Minnesota Geological Survey",
            #"Originator": self.originator,
            "Originator": "Minnesota Geological Survey",
            #"OriginatorSort": self.originator,
            "OriginatorSort": "Minnesota Geological Survey",

            # the rest are associated with a method
            "DataType": self.data_type,
            "DataTypeSort": self.data_type,
            "ThemeKeywords": self.theme_keywords,
            "PlaceKeywords": self.place_keywords,
            "LayerId": self.layer_id,
            "Location": self.location,
            "Name": self.name,
            "LayerDisplayName": self.layer_display_name,
            "LayerDisplayNameSort": self.layer_display_name,
            "ContentDate": self.content_date,
            "Abstract": self.abstract,
            "MinX": self.min_x,
            "MaxX": self.max_x,
            "MinY": self.min_y,
            "MaxY": self.max_y,
            "CenterX": self.center_x,
            "CenterY": self.center_y
        }

    # field methods 
    def _file_name_sans_extension(self):
        file_name = os.path.basename(self.file_name)
        file_name = file_name[0:file_name.rfind('.')]
        return file_name

    def layer_id(self):
        return self._file_name_sans_extension()

    def name(self):
        return self._file_name_sans_extension()

    def data_type(self):
        # see standard specific sub-class implementation
        pass

    def theme_keywords(self):
        # see standard specific sub-class implementation
        pass

    def place_keywords(self):
        # see standard specific sub-class implementation
        pass

    def publisher(self):
        # see standard specific sub-class implementation
        pass

    def layer_display_name(self):
        # see standard specific sub-class implementation
        pass

    def location(self):
        # see standard specific sub-class implementation
        pass

    def content_date(self):
        # see standard specific sub-class implementation
        pass

    def abstract(self):
        # see standard specific sub-class implementation
        pass


class ArcGISDocument(MetadataDocument):
    """
    Unimplemented. Inherits from MetadataDocument
    """
    def __init__(self,root,filename):
        super(ArcGISDocument,self).__init__(root,filename)


class FGDCDocument(MetadataDocument):
    """
    inherits from MetadataDocument
    """
    def __init__(self,root,filename):
        super(FGDCDocument,self).__init__(root,filename)

    def publisher(self):
        publisher = self.root.findtext("idinfo/citation/citeinfo/pubinfo/publish","UNKNOWN")
        return publisher

    def layer_display_name(self):
        disp_name = self.root.findtext("idinfo/citation/citeinfo/title","UNKNOWN")
        disp_name = disp_name + " (" + self.name() + ")"
        return disp_name

    def abstract(self):
        abstract = self.root.findtext("idinfo/descript/abstract","UNKNOWN")
        return abstract

    def originator(self):
        originator = self.root.findtext("idinfo/citation/citeinfo/origin","UNKNOWN")
        return originator

    def data_type(self):
        root = self.root
        try:
            if root.find("*//geoform") is not None:
                geoform = root.findtext("*//geoform").lower()
                if ("scanned" in geoform or 
                    "paper" in geoform or 
                    "scanned paper map" in geoform):
                    return "Paper Map"
            if root.find("*//direct") is not None:
                direct = root.findtext("*//direct").lower()
                if "raster" in direct:
                    return "Raster"
                elif (
                    "g-polygon" in direct or 
                    "polygon" in direct or 
                    "chain" in direct
                    ):
                    return "Polygon"
                elif ("point" in direct):
                    return "Point"
            if root.find("*//sdtstype") is not None:
                sdtstype = root.findtext("*//sdtstype").lower()
                if ("composite" in sdtstype or
                    "point" in sdtstype
                    ):
                    return "Point"
                elif "string" in sdtstype:
                    return "Line"
                elif ("g-polygon" in sdtstype or
                      "polygon" in sdtstype or
                      "chain" in sdtstype):
                    return "Polygon"

        except AttributeError as e:
            print "Can't determine data type, setting to Undefined for now"
            return "Undefined"

    def theme_keywords(self):
        try:
            kw = list(self.root.iter("themekey"))

            if len(kw) > 0:
                kw_str = [i.text for i in kw][0]
                return kw_str
            else:
                return 'None'
        except AttributeError as e:
            print "can't find keywords. Setting to UNKNOWN for now"
            return "UNKNOWN"

    def place_keywords(self):
        try:
            kw = list(self.root.iter("placekey"))

            if len(kw) > 0:
                kw_str = [i.text for i in kw][0]
                return kw_str
            else:
                return 'None'
        except AttributeError as e:
            print "can't find keywords. Setting to UNKNOWN for now"
            return "UNKNOWN"

    def _parse_content_date(self,dateText):

        try:
            if len(dateText) == 4:
                #if it's just 4 digits, lets assume it's the year and convert it to integer
                year = int(dateText)

                #we'll just use Jan 1 as the default for year only entries
                date = datetime(year,1,1)

                #now format it ISO style
                return date.isoformat() + "Z"
            elif len(dateText) == 8:
                year = int(dateText[0:4])
                month = int(dateText[4:6])
                day = int(dateText[6:])
                date = datetime(year,month,day)
                return date.isoformat() + "Z"

        except ValueError as e:
            return "UNKNOWN"

    def content_date(self):
        root = self.root
        try:

            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                return self._parse_content_date(dateText)
            elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text
                return self._parse_content_date(dateText)
            elif root.find("idinfo/citation/citeinfo/pubdate") is not None:
                dateText = root.find("idinfo/citation/citeinfo/pubdate").text
                return self._parse_content_date(dateText)
            else:
                return "1919-08-01T00:00:00Z"

        except (AttributeError,TypeError):
            print "No content date found! setting to 1919-08-01T00:00:00Z for now"
            return "1919-08-01T00:00:00Z"

    def _parse_coord(self,coord):
        try:
            coord = float(coord)
            return unicode(coord)
        except (ValueError,TypeError):
            return "ERR_" + coord

    def min_x(self):
        coord = self.root.findtext("idinfo/spdom/bounding/westbc","UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        return coord

    def min_y(self):
        coord = self.root.findtext("idinfo/spdom/bounding/southbc","UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        return coord

    def max_x(self):
        coord = self.root.findtext("idinfo/spdom/bounding/eastbc","UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        return coord

    def max_y(self):
        coord = self.root.findtext("idinfo/spdom/bounding/northbc","UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        return coord

    def center_x(self):
        try:
            min_x = float(self.min_x())
            max_x = float(self.max_x())
            center_x = min_x + (abs(max_x-min_x)/2)
            return unicode(center_x)
        except ValueError:
            return "UNKNOWN"

    def center_y(self):
        try:
            min_y = float(self.min_y())
            max_y = float(self.max_y())
            center_x = min_y + (abs(max_y-min_y)/2)
            return unicode(center_x)
        except ValueError:
            return "UNKNOWN"

    def location(self):
        loc = self.root.findtext("idinfo/citation/citeinfo/onlink","UNKNOWN")

        if loc != "UNKNOWN":
            return '{\"download\": \"%s\"}' % (loc)
        else:
            return "UNKNOWN"

class MGMGDocument(FGDCDocument):
    """
    Inherits from FGDCDocument
    """
    def __init__(self,root,filename):
        super(MGMGDocument,self).__init__(root,filename)

    def data_type(self):
        root = self.root
        try:
            if root.findtext("*//direct").lower() == "raster":
                return "Raster"
            if root.findtext("*//direct").lower() == "point":
                return "Point"
            elif root.findtext("*//direct").lower() =="vector":
                mgmg3obj = root.findtext("*//mgmg3obj").lower()
                if (
                    "area" in mgmg3obj or 
                    "polygon" in mgmg3obj or 
                    "region" in mgmg3obj or 
                    "TIN" in mgmg3obj
                    ):
                    return "Polygon"

                elif ("line" in mgmg3obj or
                    "network" in mgmg3obj or
                    "route-section" in mgmg3obj or
                    "arc" in mgmg3obj
                    ):
                    return "Line"
                elif (
                    "node" in mgmg3obj or 
                    "point" in mgmg3obj or 
                    "label" in mgmg3obj
                    ):
                    return "Point"

        except AttributeError as e:
            print "Can't determine data type, setting to Undefined for now"
            return "Undefined"

    """
    def location(self):
        #TODO refactor this mess
        pass
        
        try:
            if df_lyrs.has_key(LAYERID):
                dictCurrentLayer = ast.literal_eval(df_lyrs[LAYERID])
                ARCGISREST = dictCurrentLayer["ArcGISRest"]
                NAME = dictCurrentLayer["layerId"]
                #print 'Found',LAYERID,' so removing it from df_lyrs'
                df_lyrs.pop(LAYERID)

                if root.find("idinfo/citation/citeinfo/onlink") is not None:
                    DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                    LOCATION = json.dumps({
                        #It is tricky to add layerId here since we might complicate the location field to contain json-in-json.
                        #Currently, we neglect layerId but use layerName, which is LAYERID, a.k.a NAME field in OGP metadata format to access layer.
                        'ArcGISRest': ARCGISREST + "/export",
                        'download': DOWNLOAD_URL,
                    })
                else:
                    LOCATION = json.dumps({
                        'ArcGISRest': ARCGISREST,
                    })
            else:
                if root.find("idinfo/citation/citeinfo/onlink") is not None:
                    DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                    LOCATION = json.dumps({
                        'download': DOWNLOAD_URL
                    })
        except AttributeError as e:
            print 'LOCATION error: ', e
            error_counter += 1
    """

class MARCXMLDocument(MetadataDocument):
    def __init__(self,root,file_name):
        from itertools import ifilter
        import re
        super(MARCXMLDocument,self).__init__(root,file_name)
        MARC = "http://www.loc.gov/MARC21/slim"
        MARCNS = "{{{0}}}".format(MARC)
        NSMAP = {
            "marc": MARC,
        }

        _XPATHS = {
            "001"  : "/collection/record/controlfield[@tag='001']",
            "008"  : "/collection/record/controlfield[@tag='008']/text()",
            "034_d": "/collection/record/datafield[@tag='034']/subfield[@code='d']/text()",
            "034_e": "/collection/record/datafield[@tag='034']/subfield[@code='e']/text()",
            "034_f": "/collection/record/datafield[@tag='034']/subfield[@code='f']/text()",
            "034_g": "/collection/record/datafield[@tag='034']/subfield[@code='g']/text()",
            "245"  : "/collection/record/datafield[@tag='245']/subfield[@code='a']/text()",
            "260_b": "/collection/record/datafield[@tag='260']/subfield[@code='b']",
            "500_a": "/collection/record/datafield[@tag='500']/subfield[@code='a']/text()",
            "650_a": "/collection/record/datafield[@tag='650']/subfield[@code='a']",
            "650_z": "/collection/record/datafield[@tag='650']/subfield[@code='z']",
            "876_k": "/collection/record/datafield[@tag='876']/subfield[@code='k']",
        }

        self.XPATHS = dict((k, etree.XPath(v)) for k,v in _XPATHS.items())    
        self._COORD_REGEX = re.compile("^([NSEW+-])?(\d{3}(\.\d*)?)(\d{2}(\.\d*)?)?(\d{2}(\.\d*)?)?",
                          re.IGNORECASE)

    def datatype(self):
        xpath = self.XPATHS['876_k']
        mapping = {
            "MAP": "Paper Map",
            "CDROM": "CD-ROM",
            "DVDROM": "DVD-ROM",
        }
        for datatype in xpath(self.root):
            if datatype.text in ("MAP", "CDROM", "DVDROM"):
                return mapping[datatype.text]
        return "Unknown"

    def theme_keywords(self):
        return " ".join(self._keywords(self.XPATHS['650_a']))

    def place_keywords(self):
        return " ".join(self._keywords(self.XPATHS['650_z']))

    def publisher(self):
        xpath = self.XPATHS['260_b']
        publisher = xpath(self.root)
        if publisher:
            return publisher[0].text.rstrip(",")

    def name(self):
        xpath = self.XPATHS['001']
        return xpath(self.root)[0].text

    def layer_display_name(self):
        xpath = self.XPATHS['245']
        return " ".join(xpath(self.root))

    def content_date(self):
        xpath = self.XPATHS['008']

        date = xpath(self.root)[0][7:11]

        try:
            date= datetime(int(date), 1, 1)
            return date.isoformat() + "Z"
        except ValueError:
            pass

    def abstract(self):
        xpath = self.XPATHS['500_a']
        return " ".join(xpath(self.root))

    def min_x(self):
        xpath = self.XPATHS['034_d']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def min_y(self):
        xpath = self.XPATHS['034_g']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def max_x(self):
        xpath = self.XPATHS['034_e']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def max_y(self):
        xpath = self.XPATHS['034_f']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def center_x(self):
        west = float(self.min_x())
        east = float(self.max_x())
        if west is not None and east is not None:
            return unicode(west + abs(east - west) / 2)

    def center_y(self):
        south = float(self.min_y())
        north = float(self.max_y())
        if south is not None and north is not None:
            return unicode(south + abs(north - south) / 2)

    def half_height(self):
        north = float(self.max_y())
        south = float(self.min_y())
        if north is not None and south is not None:
            return unicode(abs(north - south) / 2)

    def half_width(self):
        east = float(self.max_x())
        west = float(self.min_x())
        if east is not None and west is not None:
            return unicode(abs(east - west) / 2)

    def _convert_coord(self,coordinate):
        parts = self._COORD_REGEX.search(coordinate)
        if parts is None:
            return
        decimal = float(parts.group(2)) + float(parts.group(4) or 0) / 60 + float(parts.group(6) or 0) / 3600
        if parts.group(1) and parts.group(1) in "WSws-":
            decimal = -decimal
        return decimal

    def _keywords(self, xpath):
        keywords = set()
        for keyword in xpath(self.root):
            keywords.add(keyword.text.rstrip(":;,. "))
        return list(keywords)

