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
from datatype_parse import *
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
import arcpy

#########################
##ArcGIS to FGDC to OGP##
#########################

def ARCGIS(workspace): 
    """
    Set workspace (where datasets to be processed are located) below
    """
    arcpy.env.workspace = workspace
    ws = arcpy.env.workspace
    print 'ws: ',ws
    """
    Get ArcGIS Install Location
    """
    ARCGIS_INSTALL_LOCATION = arcpy.GetInstallInfo()['InstallDir']

    """
    Get location of XSL Translator to go from ArcGIS to FGDC
    """
    FGDC_XSL_FILE = ARCGIS_INSTALL_LOCATION + "Metadata\\Translator\\Transforms\\ArcGIS2FGDC.xsl"


    """
    Set output location for OGP metadata and log file, then instantiate Logger
    """
    if os.path.exists(ws+"\\output\\"):
        OUTPUT_LOCATION = ws+"\\output\\"
    else:
        os.mkdir(ws+"\\output\\")
        OUTPUT_LOCATION = ws+"\\output\\"
    print 'output location: ',OUTPUT_LOCATION
    d=datetime.today()
    LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"
    sys.stdout = Logger(OUTPUT_LOCATION,LOG_NAME)

    files = arcpy.ListFiles()
    datasets = arcpy.ListDatasets()
    fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
              'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
              'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
              'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
              'MinY', 'MinX', 'MaxX', 'CenterX', 'CenterY', 'HalfWidth', 'HalfHeight',
              'Area', 'ContentDate','Location']

    if os.path.exists(ws + "\\temp.xml"):
        print "removed temp xml file"
        os.remove(ws + "\\temp.xml")

    """
    Set UTC timezone for ContentDate field
    """
    utc = pytz.utc

    for i in datasets[:5]:
        """
        start the clock! obviously not at all necessary 
        """
        start = clock()

        """
         converting metadata from ArcGIS to FGDC using XSL transformation (super fast) and
         writing it to a temporary XML file that is then parsed and translated into
         final OGP format
        """
        print "======================================"
        print "Current item is " + i 
        print "======================================\n"
       
        print "Converting ArcGIS metadata into temporary FGDC XML file"
        
        XSLtrans = arcpy.XSLTransform_conversion(i,FGDC_XSL_FILE,"temp.xml")
        
        print XSLtrans.getMessages(),'\n'
        
        FGDCtree=ElementTree()
        root = FGDCtree.parse(ws + "\\temp.xml")
             
        DATATYPE = dataTypeParseFGDC(root)
        DATATYPESORT = DATATYPE

        #create string representation of FGDC md to be appended at end of OGP md
        FGDC_TEXT = ET.tostring(root)

        #layerID equals filename sans extension 
        LAYERID = i[:i.find(".")]

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
            #PUBLISHER = root.find("idinfo/citation/citeinfo/pubinfo/publish").text
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
        #try:
        if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
            dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
            year = int(dateText[0:4])
            month = int(dateText[4:6])
            day = int(dateText[6:8])
            date = datetime(year,month,day)
            CONTENTDATE = date.isoformat() + "Z"
        elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
            dateText = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text
            year = int(dateText[0:4])
            month = int(dateText[4:6])
            day = int(dateText[6:8])
            date = datetime(year,month,day)
            CONTENTDATE = date.isoformat() + "Z"
        #except AttributeError as e:
        #    print "No content date found! setting to UNKNOWN for now"
        #    CONTENTDATE = "UNKNOWN"


        """
        LOCATION
        <field name="Location">
        {
        "ArcGIS93Rest": ["(the url for the REST service)"],
        "tilecache": ["(the url for the tilecache, which I believe ArcGIS server does not have)"],
        "download": "(downloading URL for the layer)","wfs": "(WFS URL, if has one)"
        }
        </field>
        """
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
##        
##        LOCATION = '{"ArcGIS93Rest" : "' + REST_URL + '", "tilecache" : "None", "download" : "' + DOWNLOAD_URL + '", "wfs" : "None"}'

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
            OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml")
            print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"



        os.remove(ws+"\\temp.xml")

        print "Next!\n"

    end = clock()
    if (end-start) > 60:
        mins = str(math.ceil((end - start) / 60))
        secs = str(math.ceil((end - start) % 60))
        print str(len(datasets)) + " datasets processed in " + mins + " minutes and " + secs + " seconds"
    else:
        secs = str(math.ceil(end-start))
        print str(len(datasets)) + " datasets processed in " + secs + " seconds"
    sys.stdout=sys.__stdout__
    print 'Done. See log file for information'
    

