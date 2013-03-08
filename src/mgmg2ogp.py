from time import clock
from datetime import datetime
import os, math, sys
import pytz
import urllib
import StringIO
import glob
import json
from logger import Logger
from keyword_parse import keywordParse
from datatype_parse import dataTypeParseMGMG
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement

    
def MGMG(workspace):
    """
    Set workspace (where datasets to be processed are located) below
    """
    ws = workspace

    
    #Set output location for OGP metadata and log file, then instantiate Logger
    
    OUTPUT_LOCATION = ws+"output\\"

    d=datetime.today()
    LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"

    sys.stdout = Logger(OUTPUT_LOCATION,LOG_NAME)


    files = glob.glob(ws+'*[!aux].xml')

    fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
              'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
              'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
              'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
              'MinY', 'MinX', 'MaxX', 'ContentDate','Location']


    
    #Set UTC timezone for ContentDate field
    
    utc = pytz.utc

    
    #List of layers and their respective URLs from Datafinder.org
    
    df_lyrs_file = open("G:\\Documents\\GitHub\\OGP-metadata-py\\tests\\datafinder_layers.json",'r')
    df_lyrs = json.loads(df_lyrs_file.read())


   
    #start the clock! obviously not at all necessary 
   
    start = clock()

    for i in files:
        download_ags = 0
        print 'full file path is ', i
        FGDCtree=ElementTree()
        root = FGDCtree.parse(i)

        #layerID equals filename sans extension 
        LAYERID = i[i.rfind('\\')+1:i.rfind(".")]
        print 'layerid is ', LAYERID
        
        try:
            if df_lyrs.has_key(LAYERID):
                NAME = unicode(df_lyrs[LAYERID]["name"])
            else:
                NAME = LAYERID
        except AttributeError as e:
            print "Name field doesn't exist! Setting to UNKNOWN for now"
            NAME = "UNKNOWN"
        
        try:
            if df_lyrs.has_key(LAYERID):
                WORKSPACENAME = unicode(df_lyrs[LAYERID]["WorkspaceName"])
        except AttributeError as e:
            print 'Workspace name error: ',e
            
        DATATYPE = dataTypeParseMGMG(root)
        DATATYPESORT = DATATYPE

        #create string representation of MGMG md to be appended at end of OGP md
        MGMG_TEXT = ET.tostring(root)



        COLLECTIONID = "initial collection"
        
        INSTITUTION = "University of Minnesota"
        INSTITUTIONSORT = "University of Minnesota"
        
        try:
            ACCESS = root.find("idinfo/accconst").text
        except AttributeError as e:
            print "Access Constraints field doesn't exist! Setting to UNKNOWN for now"        
            ACCESS = "UNKNOWN"

        AVAILABILITY = "Online"
        
        #set Display Name equal to title element
        
        try:
            LAYERDISPLAYNAME = root.findtext("idinfo/citation/citeinfo/title")
 
        except AttributeError:
            print 'No Title element found...'
            LAYERDISPLAYNAME = "UNKNOWN"
        
        LAYERDISPLAYNAMESORT = LAYERDISPLAYNAME
                #name equals FGDC title field

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

        THEMEKEYWORDS = keywordParse(FGDCtree,"themekey")
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
        
        
        try:
            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                if len(dateText) == 4:
                    #if the length is 4, we'll assume it's referring to the year.
                    year = int(dateText)
                    #we'll take January 1st as the fill in month/day for ISO format
                    date = datetime(year, 1,1)
                    CONTENTDATE = date.isoformat() + "Z"
                elif len(dateText) == 8:
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
                ARCGISREST = df_lyrs[LAYERID]["ArcGISRest"]
                print 'Found',LAYERID,' so removing it from df_lyrs'
                df_lyrs.pop(LAYERID)              
                SERVERTYPE = df_lyrs[LAYERID]["ServerType"]
                if root.find("idinfo/citation/citeinfo/onlink") is not None:
                    DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                    LOCATION = json.dumps({
                        'ArcGIS93Rest': ARCGISREST,
                        'download' : DOWNLOAD_URL,
                        'ServerType': SERVERTYPE
                        })
                else:
                    LOCATION = json.dumps({
                        'ArcGIS93Rest': ARCGISREST,
                        'ServerType': SERVERTYPE
                        })
            else:
                if root.find("idinfo/citation/citeinfo/onlink") is not None:
                    DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                    LOCATION = json.dumps({
                        'download' : DOWNLOAD_URL
                        })
        except AttributeError as e:
            print 'LOCATION error: ', e
          
        
        #Put it all together to make the OGP metadata xml file
        
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
        mgmg_text=SubElement(doc,"field",name="MgmgText")
        mgmg_text.text = '<?xml version="1.0"?>'+MGMG_TEXT
        
        if os.path.exists(OUTPUT_LOCATION + LAYERID + "_OGP.xml"):
            existsPrompt =raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
            if existsPrompt == 'Y':
                OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml")
                print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"
            else:
                pass
        else:
            OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml")
            print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"


        print "Next!\n"

    end = clock()

    if (end-start) > 60:
        mins = str(math.ceil((end - start) / 60))
        secs = str(math.ceil((end - start) % 60))
        print str(len(files)) + " datasets processed in " + mins + " minutes and " + secs + " seconds"
        print 'Done. See log file for information'


    else:
        secs = str(math.ceil(end-start))
        print str(len(files)) + " datasets processed in " + secs + " seconds"
        print 'Done. See log file for information'


