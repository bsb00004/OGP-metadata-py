from time import clock
from datetime import datetime
import os, math, sys
import pytz
import urllib
import StringIO
import glob
import json

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement

"""
create simple logger class to output results both to text file and display
"""
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(OUTPUT_LOCATION+LOG_NAME, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  



"""
Set workspace (where datasets to be processed are located) below
"""
ws = u"D:\\Workspace\\ogp_metadata\\mgmg_test\\"

"""
Set output location for OGP metadata and log file, then instantiate Logger
"""
OUTPUT_LOCATION = ws+"output\\"

d=datetime.today()
#LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"
#orig_stdout = sys.__stdout__
#sys.stdout = Logger()


files = glob.glob(ws+'*[!aux].xml')

fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
          'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
          'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
          'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
          'MinY', 'MinX', 'MaxX', 'ContentDate','Location']


"""
Set UTC timezone for ContentDate field
"""
utc = pytz.utc

"""
List of layers and their respective URLs from Datafinder.org
"""
df_lyrs_file = open(r'D:\Workspace\ogp_metadata\scripts_etc\datafinder_layers.json','r')
df_lyrs = json.loads(df_lyrs_file.read())

"""
Helper functions for parsing
"""

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
    
def dataTypeParseFGDC(root):
    try:
        if root.findtext("*//geoform").lower() == "scanned paper map":
            return "Paper Map"
        elif root.findtext("*//direct").lower() == "raster":
            return "Raster"
        elif (root.findtext("*//direct").lower() == "g-polygon" or root.findtext("*//direct").lower() == "polygon" or root.findtext("*//direct").lower() == "chain"):
            return "Polygon"
    except AttributeError as e:
        print "Can't determine data type, setting to UNKNOWN for now"
        return "UKNOWN"

def dataTypeParseMGMG(root):

    # There does not seem to be a separate listing for paper maps in the MN
    # standards. Instead the detailed abstract seems to have replaced original
    # form type fields...

    try:
        if root.findtext("*//direct").lower() == "raster":
            return "Raster"
        elif root.findtext("*//direct").lower() =="vector":       
            if "area" in root.findtext("*//mgmg3obj").lower() or "polygon" in root.findtext("*//mgmg3obj").lower() or "region" in root.findtext("*//mgmg3obj").lower() or "TIN" in root.findtext("*//mgmg3obj").lower():
                return "Polygon"
            elif "line" in root.findtext("*//mgmg3obj").lower() or "network" in root.findtext("*//mgmg3obj").lower() or "route-section" in root.findtext("*//mgmg3obj").lower():
                return "Line"
            elif "node" in root.findtext("*//mgmg3obj").lower() or "point" in root.findtext("*//mgmg3obj").lower():
                return "Point"
            
    except AttributeError as e:
        print "Can't determine data type, setting to Undefined for now"
        return "Undefined"
   
################
##MGMG to OGP##
################

    
def MGMG():
    """
    start the clock! obviously not at all necessary 
    """
    start = clock()
    download_ctr=0
    ags_ctr=0
    for i in files:
        download_ags = 0
        print 'full file path is ', i
        FGDCtree=ElementTree()
        root = FGDCtree.parse(i)

        #layerID equals filename sans extension 
        LAYERID = i[i.rfind('\\')+1:i.rfind(".")]
        print 'layerid is ', LAYERID
             
        DATATYPE = dataTypeParseMGMG(root)
        DATATYPESORT = DATATYPE

        #create string representation of MGMG md to be appended at end of OGP md
        FGDC_TEXT = ET.tostring(root)



        #name equals FGDC title field
        #NAME = root.find("idinfo/citation/citeinfo/title").text
        try:
            NAME = root.findtext("idinfo/citation/citeinfo/title")
        except AttributeError as e:
            print "Name field doesn't exist! Setting to UNKNOWN for now"
            NAME = "UNKNOWN"
            
        COLLECTIONID = "initial collection"
        
        INSTITUTION = "University of Minnesota"
        INSTITUTIONSORT = "University of Minnesota"
        
        try:
            ACCESS = root.find("idinfo/accconst").text
        except AttributeError as e:
            print "Access field doesn't exist! Setting to UNKNOWN for now"        
            ACCESS = "UNKNOWN"

        AVAILABILITY = "Online"

        LAYERDISPLAYNAME = NAME
        LAYERDISPLAYNAMESORT = NAME
        try:
            PUBLISHER = root.findtext("idinfo/citation/citeinfo/pubinfo/publish")
        except AttributeError as e:
            print "Publisher field doesn't exist! Setting to UNKNOWN for now"
            PUBLISHER = "UNKNOWN"
        finally:
            PUBLISHERSORT = PUBLISHER
        
        try:
            ORIGINATOR = root.find("idinfo/citation/citeinfo/origin").text
        except AttributeError as e:
            print "Originator field doesn't exist! Setting to UNKNOWN for now"
            ORIGINATOR = "UNKNOWN"
        finally:
            ORIGINATORSORT = ORIGINATOR
            
        #Combine multiple Keyword elements into a string rep

        THEMEKEYWORDS= keywordParse(FGDCtree,"themekey")
        PLACEKEYWORDS = keywordParse(FGDCtree,"placekey")
        
        try:
            ABSTRACT = root.find("idinfo/descript/abstract").text
        except AttributeError as e:
            print "No abstract found. Setting to UNKNOWN for now"
            ABSTRACT = "UNKNOWN"
        
        try:
            MINX=root.find("idinfo/spdom/bounding/westbc").text
            MINY=root.find("idinfo/spdom/bounding/southbc").text
            MAXX=root.find("idinfo/spdom/bounding/eastbc").text
            MAXY=root.find("idinfo/spdom/bounding/northbc").text

        except AttributeError as e:
            print "extent information not found!"
        
        #SRSPROJECTIONCODE=
        try:
            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                if len(dateText) != 8:
                    raise AttributeError
                else:
                    #print dateText
                    year = int(dateText[0:4])
                    month = int(dateText[4:6])
                    day = int(dateText[6:])
                    date = datetime(year,month,day)
                    CONTENTDATE = date.isoformat() + "Z"
       
        except AttributeError as e:
            print "No content date found! setting to UNKNOWN for now"
            CONTENTDATE = "UNKNOWN"

        except TypeError as e:
            print "|-|-|-| No content date found! setting to UNKNOWN for now"
            CONTENTDATE = "UNKNOWN"
            
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
                SERVICE_URL = df_lyrs[LAYERID]
                print 'Found',LAYERID,' so removing it from df_lyrs'
                df_lyrs.pop(LAYERID)
                ags_ctr += 1
                download_ags += 1
            else:
                pass
                SERVICE_URL = 'UNKNOWN'
            if root.find("idinfo/citation/citeinfo/onlink") is not None:
                DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                download_ctr +=1
            else:
                pass
                DOWNLOAD_URL = 'UNKNOWN'
            LOCATION = json.dumps({'ArcGIS93Rest': SERVICE_URL, 'download' : DOWNLOAD_URL})
            print LOCATION
        except:
            print 'LOCATION error'
          
        """
        Put it all together to make the OGP metadata xml file
        """
        OGPtree = ElementTree()
        OGProot = Element("add",allowDups="false")
        doc = SubElement(OGProot,"doc")
        OGPtree._setroot(OGProot)
        try:
            for field in fields:
                fieldEle = SubElement(doc,"field",name=field)
                fieldEle.text = locals()[field.upper()]
        except KeyError as e:
            print "Nonexistant key: ", field 
        fgdc_text=SubElement(doc,"field",name="FgdcText")
        fgdc_text.text = '<?xml version="1.0"?>'+FGDC_TEXT
        
        if os.path.exists(OUTPUT_LOCATION + LAYERID + "_OGP.xml"):
            existsPrompt =raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
            if existsPrompt == 'Y':
                OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml")
                print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"
            else:
                pass
        else:
            print download_ags
            if download_ags ==1:
                OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml")
                print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"
            else:
                pass


        print "Next!\n"

    end = clock()
    
    if (end-start) > 60:
        mins = str(math.ceil((end - start) / 60))
        secs = str(math.ceil((end - start) % 60))
        print str(len(files)) + " datasets processed in " + mins + " minutes and " + secs + " seconds"
        print 'Done. See log file for information'
        print 'ags ctr: ', ags_ctr
        print 'download ctr: ', download_ctr
        #sys.stdout=orig_stdout
    else:
        secs = str(math.ceil(end-start))
        print str(len(files)) + " datasets processed in " + secs + " seconds"
        print 'Done. See log file for information'
        print 'ags ctr: ', ags_ctr
        print 'download ctr: ', download_ctr
        #sys.stdout=sys.__stdout__

MGMG()
