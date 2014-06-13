from time import clock
from datetime import datetime
import os, math, sys
import pytz
import urllib
import StringIO
import glob
import json
import random
from logger import Logger
from keyword_parse import keywordParse
from datatype_parse import dataTypeParse
import ast

try:
    from lxml import etree as et
except ImportError:
    try:
        print "Python lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported"
        from xml.etree import ElementTree as et
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"


class OgpXML(object):
    @property
    def layerId(self):
        return self._LayerId

    @layerId.setter
    def x(self, value):
        self._x = value

    @x.deleter
    def x(self):
        del self._x

class ArcGISDocument(MetadataDocument):
    """
    Inherits from MetadataDocument
    """
    def __init__(self):
        import arcpy
        MetadataDocument.__init__(self,root,file_name)

class MGMGDocument(FGDCDocument):
    """
    Inherits from FGDCDocument
    """
    def __init__(self,root,file_name):
        FGDCDocument.__init__(self,root,file_name)

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

class FGDCDocument(MetadataDocument):
    """
    inherits from MetadataDocument
    """
    def __init__(self,root,file_name):
        MetadataDocument.__init__(self,root,file_name)

    def publisher(self):
        publisher = self.root.findtext("idinfo/citation/citeinfo/pubinfo/publish","UNKNOWN")
        return publisher

    def layer_display_name(self):
        disp_name = self.root.findtext("idinfo/citation/citeinfo/title","UNKNOWN")
        return disp_name

    def abstract(self):
        return self.root.findtext("idinfo/descript/abstract","UNKNOWN")

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

            elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text

            return self._parse_content_date(dateText)

        except (AttributeError,TypeError):
            print "No content date found! setting to UNKNOWN for now"
            return "UNKNOWN"


#TODO make this actually work
#adapted from https://github.com/gravesm/marcingest/blob/master/marcingest/field_handlers.py
class MARCXMLDocument(MetadataDocument):
    def __init__(self,root,file_name):
        MetadataDocument.__init__(self,root,file_name)

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

    def area(record):
        west = min_x(record)
        east = max_x(record)
        south = min_y(record)
        north = max_y(record)
        if all(v is not None for v in (west, east, south, north)):
            return abs(east - west) * abs(north - south)

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

class MetadataDocument(object):
    """
    Base class for metadata documents. This is where OGP fields that are handled the same
    across standards are implemented.
    """

    def __init__(self,root,file_name):
        self.root = root
        self.file_name = file_name
        self.field_handlers = {
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
            'CenterY': self.center_y,
            'Area': self.area,
            'HalfWidth': self.half_width,
            'HalfHeight': self.half_height,
            'Access': "Public",
            'Availability': "Online",
            'Institution': "Minnesota",
            'WorkspaceName': self.workspace_name,
            'CollectionId': "initial collection"
        }



    # field handlers

    def layer_id(self, doc):
        file_name = os.path.basename(self.file_name)
        file_name = file_name[0:file_name.rfind('.')]
        return file_name

    def name(self):
        file_name = os.path.basename(self.file_name)
        file_name = file_name[0:file_name.rfind('.')]
        return file_name

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

    def parseXMLs(self):

        for i in self.files:
            print i
            tree = et.ElementTree()
            root = tree.parse(i)
            currentDoc = self.ogpXML()
            currentDoc.layerId = self.setLayerId(doc)
            currentDoc.Name = self.setName(doc)
            currentDoc.DataType = self.setDataType(doc)


def MGMG(workspace, output_path, error_tolerance):
    """
    Set workspace (where datasets to be processed are located) below
    """
    ws = workspace
    max_errors = error_tolerance

    # Set output location for OGP metadata and log file, then instantiate Logger

    error_path = output_path

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    OUTPUT_LOCATION = output_path

    if not os.path.exists(error_path):
        os.mkdir(error_path)

    ERROR_LOCATION = error_path

    print 'output location: ', OUTPUT_LOCATION

    d = datetime.today()
    LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"

    sys.stdout = Logger(OUTPUT_LOCATION, LOG_NAME)

    files = glob.glob(os.path.join(ws, '*[!aux].xml'))

    fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
              'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
              'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
              'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
              'MinY', 'MinX', 'MaxX', 'ContentDate', 'Location', 'WorkspaceName']

    #Set UTC timezone for ContentDate field

    utc = pytz.utc

    #List of layers and their respective URLs from Datafinder.org

    df_lyrs_file = open(os.path.abspath(os.path.relpath("tests/datafinder_layers.json", os.getcwd())), 'r')
    df_lyrs = json.loads(df_lyrs_file.read())



    #start the clock! 
    start = clock()

    for i in files:
        print 'full file path is ', i
        error_counter = 0
        FGDCtree = et.ElementTree()
        root = FGDCtree.parse(i)

        #layerID equals filename sans extension
        file_name = os.path.basename(i)
        file_name = file_name[0:file_name.rfind('.')]
        LAYERID = file_name

        #print 'layerid is ', LAYERID

        try:
            NAME = LAYERID
        except AttributeError as e:
            print "Name field doesn't exist! Setting to UNKNOWN for now"
            NAME = "UNKNOWN"
            error_counter += 1

        #Workspacename does not make sense here, unless we want to document the "Folder" of ArcGIS Services.
        # try:
        #     if df_lyrs.has_key(LAYERID):
        #         WORKSPACENAME = unicode(df_lyrs[LAYERID]["WorkspaceName"])
        # except AttributeError as e:
        #     print 'Workspace name error: ',e
        #     error_counter += 1

        DATATYPE = dataTypeParse(root, "MGMG")
        if DATATYPE == "Undefined":
            error_counter += 1
        DATATYPESORT = DATATYPE

        #create string representation of MGMG md to be appended at end of OGP md
        MGMG_TEXT = et.tostring(root)

        COLLECTIONID = "initial collection"

        INSTITUTION = "Minnesota"
        INSTITUTIONSORT = "Minnesota"

        #to avoid authentication complications, for now we'll just set access field to public
        ACCESS = "Public"
        #        try:
        #            ACCESS = root.find("idinfo/accconst").text
        #        except AttributeError as e:
        #            print "Access Constraints field doesn't exist! Setting to UNKNOWN for now"
        #            ACCESS = "UNKNOWN"

        AVAILABILITY = "Online"

        #set Display Name equal to title element    
        try:
            LAYERDISPLAYNAME = root.findtext("idinfo/citation/citeinfo/title")

        except AttributeError:
            print 'No Title element found...'
            LAYERDISPLAYNAME = "UNKNOWN"
            error_counter += 1

        LAYERDISPLAYNAMESORT = LAYERDISPLAYNAME

        try:
            PUBLISHER = root.findtext("idinfo/citation/citeinfo/pubinfo/publish")
        except AttributeError as e:
            print "Publisher field doesn't exist! Setting to UNKNOWN for now"
            PUBLISHER = "UNKNOWN"
            error_counter += 1
        finally:
            PUBLISHERSORT = PUBLISHER

        try:
            ORIGINATOR = root.find("idinfo/citation/citeinfo/origin").text
        except AttributeError as e:
            print "Originator field doesn't exist! Setting to UNKNOWN for now"
            ORIGINATOR = "UNKNOWN"
            error_counter += 1
        finally:
            ORIGINATORSORT = ORIGINATOR

        #Combine multiple Keyword elements into a string rep

        THEMEKEYWORDS = keywordParse(FGDCtree, "themekey")
        PLACEKEYWORDS = keywordParse(FGDCtree, "placekey")

        try:
            ABSTRACT = root.find("idinfo/descript/abstract").text
        except AttributeError as e:
            print "No abstract found. Setting to UNKNOWN for now"
            ABSTRACT = "UNKNOWN"

        try:
            MINX = root.find("idinfo/spdom/bounding/westbc").text
            try:
                MINXf = float(MINX)
            except (TypeError, ValueError):
                print 'Invalid West Bounding Coordinate of:', MINX
                error_counter += 1

        except AttributeError as e:
            print "West Bounding Coordinate not found!"
            error_counter += 1

        try:
            MINY = root.find("idinfo/spdom/bounding/southbc").text
            try:
                MINYf = float(MINY)
            except (TypeError, ValueError):
                print 'Invalid South Bounding Coordinate of:', MINY
                error_counter += 1
        except AttributeError as e:
            print "South Bounding Coordinate not found!"
            error_counter += 1

        try:
            MAXX = root.find("idinfo/spdom/bounding/eastbc").text
            try:
                MAXXf = float(MAXX)
            except (TypeError, ValueError):
                print 'Invalid East Bounding Coordinate of:', MAXX
                error_counter += 1
        except AttributeError as e:
            print "East Bounding Coordinate not found!"
            error_counter += 1

        try:
            MAXY = root.find("idinfo/spdom/bounding/northbc").text
            try:
                MAXYf = float(MAXY)
            except (TypeError, ValueError):
                print 'Invalid North Bounding Coordinate of:', MAXY
                error_counter += 1
        except AttributeError as e:
            print "North Bounding Coordinate not found!"
            error_counter += 1

        try:
            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                if len(dateText) == 4:
                    #if the length is 4, we'll assume it's referring to the year.
                    year = int(dateText)
                    #we'll take January 1st as the fill in month/day for ISO format
                    date = datetime(year, 1, 1)
                    CONTENTDATE = date.isoformat() + "Z"
                elif len(dateText) == 8:
                    year = int(dateText[0:4])
                    month = int(dateText[4:6])
                    day = int(dateText[6:])
                    date = datetime(year, month, day)
                    CONTENTDATE = date.isoformat() + "Z"

        except AttributeError as e:
            print "No content date found! setting to UNKNOWN for now"
            CONTENTDATE = "UNKNOWN"
            error_counter += 1

        except TypeError as e:
            print "|-|-|-| No content date found! setting to UNKNOWN for now"
            CONTENTDATE = "UNKNOWN"
            error_counter += 1

            # location is too specific at the moment

            ##        #base URL for all images
            ##        REST_URL_BASE = "http://lib-geo1.lib.umn.edu:6080/arcgis/rest/services/OGP/mosaic_ogp_4/ImageServer/exportImage?"
            ##
            ##        #parameters to pass to URL, in the form of a dictionary
            ##        DOWNLOAD_URL_PARAMS = {}
            ##        DOWNLOAD_URL_PARAMS['bbox'] = MINX+','+MINY+','+MAXX+','+MAXY
            ##        DOWNLOAD_URL_PARAMS['bboxSR'] = '4269'
            ##        DOWNLOAD_URL_PARAMS['imageSR'] = '26915'
            ##        DOWNLOAD_URL_PARAMS['format'] = 'tiff'
            ##        DOWNLOAD_URL_PARAMS['pixelType'] = 'U8'
            ##        DOWNLOAD_URL_PARAMS['size'] = '3000,3000'
            ##        DOWNLOAD_URL_PARAMS['restrictUTurns'] = 'esriNoDataMatchAny'
            ##        DOWNLOAD_URL_PARAMS['interpolation'] = 'RSP_BilinearInterpolation'
            ##        cursor = arcpy.SearchCursor(u"\\mosaic245.gdb\\mosaic_ogp_1","name = '"+ LAYERID+"'")
            ##        raster_ID = cursor.next().OBJECTID
            ##        DOWNLOAD_URL_PARAMS['mosaicRule'] ={}
            ##        DOWNLOAD_URL_PARAMS['mosaicRule']['mosaicMethod'] = 'esriMosaicLockRaster'
            ##        DOWNLOAD_URL_PARAMS['mosaicRule']['lockRasterIds'] = [raster_ID]
            ##        DOWNLOAD_URL_PARAMS['f']='image'
            ##
            ##        DOWNLOAD_URL = REST_URL_BASE + urllib.urlencode(DOWNLOAD_URL_PARAMS)
            ##
            ##        REST_URL= REST_URL_BASE + urllib.urlencode({'mosaicRule': DOWNLOAD_URL_PARAMS['mosaicRule']})

            ##        LOCATION = '{"ArcGIS93Rest" : "' + REST_URL + '", "tilecache" : "None", "download" : "' + DOWNLOAD_URL + '", "wfs" : "None"}'
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
        print 'number of errors: ', error_counter

        #Put it all together to make the OGP metadata xml file

        OGPtree = et.ElementTree()
        OGProot = et.Element("add", allowDups="false")
        doc = et.SubElement(OGProot, "doc")
        OGPtree._setroot(OGProot)
        try:
            for field in fields:
                fieldEle = et.SubElement(doc, "field", name=field)
                fieldEle.text = locals()[field.upper()]
        except KeyError as e:
            print "Nonexistant key: ", field
            error_counter += 1

        #TODO eventually change OGP code base to recognize MgmgText as a
        #field and parse the metadata accordingly    
        #mgmg_text = et.SubElement(doc,"field",name="MgmgText")
        mgmg_text = et.SubElement(doc, "field", name="FgdcText")
        mgmg_text.text = '<?xml version="1.0"?>' + MGMG_TEXT

        #check to see which etree module was used. If lxml was used
        #then we can pretty print the results. Otherwise we need to
        #remove the pretty print kwarg
        if et.__name__[0] == "l":
            if error_counter <= max_errors:
                if os.path.exists(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")):
                    existsPrompt = raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml"), pretty_print=True)
                        print "Output file: " + os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")
                    else:
                        pass
                else:
                    OGPtree.write(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml"), pretty_print=True)
                    print "Output file: " + os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")
            else:
                print 'File exceeded error tolerance of ', max_errors, ', so into the error folder it goes'
                if os.path.exists(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")):
                    existsPrompt = raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml"), pretty_print=True)
                        print "Output file: " + os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")
                    else:
                        pass
                else:
                    OGPtree.write(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml"), pretty_print=True)

                    print "Output file: " + os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")
        else:
            if error_counter <= max_errors:
                if os.path.exists(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")):
                    existsPrompt = raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml"))
                        print "Output file: " + os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")
                    else:
                        pass
                else:
                    OGPtree.write(os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml"))
                    print "Output file: " + os.path.join(OUTPUT_LOCATION, LAYERID + "_OGP.xml")
            else:
                print 'File exceeded error tolerance of ', max_errors, ', so into the error folder it goes'
                if os.path.exists(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")):
                    existsPrompt = raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml"))
                        print "Output file: " + os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")
                    else:
                        pass
                else:
                    OGPtree.write(os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml"))

                    print "Output file: " + os.path.join(ERROR_LOCATION, LAYERID + "_OGP.xml")

        print "\n"

    end = clock()

    if (end - start) > 60:
        mins = str(math.ceil((end - start) / 60))
        secs = str(math.ceil((end - start) % 60))
        print str(len(files)) + " datasets processed in " + mins + " minutes and " + secs + " seconds"
        print 'Done. See log file for information'


    else:
        secs = str(math.ceil(end - start))
        print str(len(files)) + " datasets processed in " + secs + " seconds"
        print 'Done. See log file for information'


