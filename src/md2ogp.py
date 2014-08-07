from time import clock
import os, math, sys
import glob
import json
import random
from logger import Logger
import ast
import pdb
from datetime import datetime

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
            'Access': "Public",
            'Availability': "Online",
            'Institution': "Minnesota",
            'CollectionId': "initial collection",

            # the rest are associated with a method
            'DataType': self.data_type,
            'ThemeKeywords': self.theme_keywords,
            'ThemeKeywordsSort': self.theme_keywords,
            'PlaceKeywords': self.place_keywords,
            'PlaceKeywordsSort': self.place_keywords,
            'Publisher': self.publisher,
            'LayerId': self.layer_id,
            'Location': self.location,
            'Name': self.name,
            'LayerDisplayName': self.layer_display_name,
            'ContentDate': self.content_date,
            'Abstract': self.abstract,
            'MinX': self.min_x,
            'MaxX': self.max_x,
            'MinY': self.min_y,
            'MaxY': self.max_y,
            'CenterX': self.center_x,
            'CenterY': self.center_y
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
        import arcpy
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
                if root.findtext("*//geoform").lower() == "scanned paper map":
                    return "Paper Map"
            if root.find("*//direct") is not None:
                direct = root.findtext("*//direct").lower()
                if direct == "raster":
                    return "Raster"
                elif (
                    direct == "g-polygon" or 
                    direct == "polygon" or 
                    direct == "chain"
                    ):
                    return "Polygon"
                elif (direct == "point"):
                    return "Point"
            if root.find("*//sdtstype") is not None:
                sdtstype = root.findtext("*//sdtstype").lower()
                if ("composite" in sdtstype or
                    "point" in sdtstype
                    ):
                    return "Point"
                elif sdtstype == "string":
                    return "Line"
                elif (sdtstype == "g-polygon" or
                      sdtstype == "polygon" or
                      sdtstype == "chain"):
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

    def content_date(self):
        root = self.root
        try:

            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                return self._parse_content_date(dateText)
            elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text
                return self._parse_content_date(dateText)
            else:
                return "UNKOWN"

        except (AttributeError,TypeError):
            print "No content date found! setting to UNKNOWN for now"
            return "UNKNOWN"

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
            return str(float(self.min_x())+(float(self.max_x())-float(self.min_x())))
        except ValueError:
            return "UNKNOWN"

    def center_y(self):
        try:
            return str(float(self.min_y())+(float(self.max_y())-float(self.min_y())))
        except ValueError:
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

    def location(self):
        #TODO refactor this mess
        pass
        """
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

#TODO make this actually work
#adapted from https://github.com/gravesm/marcingest/blob/master/marcingest/field_handlers.py
class MARCXMLDocument(MetadataDocument):
    def __init__(self,root,file_name):
        super(MARCXMLDocument,self).__init__()

    def datatype(record):
        xpath = XPATHS['876_k']
        mapping = {
            "MAP": "Paper Map",
            "CDROM": "CD-ROM",
            "DVDROM": "DVD-ROM",
        }
        for datatype in xpath(record):
            if datatype.text in ("MAP", "CDROM", "DVDROM"):
                return mapping[datatype.text]
        return "Unknown"

    def theme_keywords(record):
        return _keywords(record, XPATHS['650_a'])

    def theme_keywords_concat(record):
        return " ".join(theme_keywords(record))

    def place_keywords(record):
        return _keywords(record, XPATHS['650_z'])

    def place_keywords_concat(record):
        return " ".join(place_keywords(record))

    def publisher(record):
        xpath = XPATHS['260_b']
        publisher = xpath(record)
        if publisher:
            return publisher[0].text.rstrip(",")

    def layer_id(record):
        xpath = XPATHS['001']
        return "MIT.{0}".format(xpath(record)[0].text)

    def location(record):
        xpath = XPATHS['001']
        return '{{"libRecord": "http://library.mit.edu/item/{0}"}}'.format(xpath(record)[0].text)

    def name(record):
        xpath = XPATHS['001']
        return xpath(record)[0].text

    def layer_display_name(record):
        xpath = XPATHS['245']
        return " ".join(xpath(record))

    def content_date(record):
        xpath = XPATHS['008']
        date = xpath(record)[0].text[7:11]
        try:
            date = int(date)
            return datetime.date(date, 1, 1)
        except ValueError:
            pass

    def abstract(record):
        xpath = XPATHS['500_a']
        return " ".join(xpath(record))

    def min_x(record):
        xpath = XPATHS['034_d']
        coord = xpath(record)
        if coord:
            return _convert_coord(coord[0])

    def min_y(record):
        xpath = XPATHS['034_g']
        coord = xpath(record)
        if coord:
            return _convert_coord(coord[0])

    def max_x(record):
        xpath = XPATHS['034_e']
        coord = xpath(record)
        if coord:
            return _convert_coord(coord[0])

    def max_y(record):
        xpath = XPATHS['034_f']
        coord = xpath(record)
        if coord:
            return _convert_coord(coord[0])

    def center_x(record):
        west = min_x(record)
        east = max_x(record)
        if west is not None and east is not None:
            return west + abs(east - west) / 2

    def center_y(record):
        south = min_y(record)
        north = max_y(record)
        if south is not None and north is not None:
            return south + abs(north - south) / 2

    def half_height(record):
        north = max_y(record)
        south = min_y(record)
        if north is not None and south is not None:
            return abs(north - south) / 2

    def half_width(record):
        east = max_x(record)
        west = min_x(record)
        if east is not None and west is not None:
            return abs(east - west) / 2

    def _convert_coord(coordinate):
        parts = _COORD_REGEX.search(coordinate)
        if parts is None:
            return
        decimal = float(parts.group(2)) + float(parts.group(4) or 0) / 60 + float(parts.group(6) or 0) / 3600
        if parts.group(1) and parts.group(1) in "WSws-":
            decimal = -decimal
        return decimal

    def _keywords(record, xpath):
        keywords = set()
        for keyword in xpath(record):
            keywords.add(keyword.text.rstrip(":;,. "))
        return list(keywords)

