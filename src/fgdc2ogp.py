from time import clock
from datetime import datetime
import os, math, sys
import urllib
import StringIO
import glob
import json
from logger import Logger
from keyword_parse import keywordParse
from datatype_parse import dataTypeParse
try:
    from lxml import etree as et
except ImportError:
    try:
        print "Python lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported"
        from xml.etree import ElementTree as et
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue. Try 'pip install lxml' or see http://lxml.de/installation.html for more information"

def FGDC(workspace, output_path, error_tolerance):
    """
    Set workspace (where datasets to be processed are located) below
    """
    ws = workspace

    max_errors = error_tolerance
    
    """
    Set output location for OGP metadata and log file, then instantiate Logger
    """
    if os.path.exists(ws+"output\\"):
        OUTPUT_LOCATION = ws+"output\\"
    else:
        os.mkdir(ws+"output\\")
        OUTPUT_LOCATION = ws+"output\\"
    print 'output location: ',OUTPUT_LOCATION
    
    d=datetime.today()
    LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"
    
    sys.stdout = Logger(OUTPUT_LOCATION,LOG_NAME)

    files = glob.glob(ws+'*[!aux].xml')

    fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
          'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
          'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
          'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
          'MinY', 'MinX', 'MaxX', 'ContentDate']
  
    #start the clock! obviously not at all necessary 
      
    start = clock()

    for i in files:
        error_counter = 0
        FGDCtree = et.ElementTree()
        root = FGDCtree.parse(i)
             
        DATATYPE = dataTypeParse(root,"FGDC")
        DATATYPESORT = DATATYPE

        #create string representation of FGDC md to be appended at end of OGP md
        FGDC_TEXT = et.tostring(root)

        #layerID equals filename sans extension 
        LAYERID = i[i.rfind('\\')+1:i.rfind(".")]
        print 'layerid is ', LAYERID
        
        try:
            NAME = root.findtext("idinfo/citation/citeinfo/title")
        except AttributeError as e:
            print "Name field doesn't exist! Setting to UNKNOWN for now"
            NAME = "UNKNOWN"
            
        COLLECTIONID = "initial collection"
        
        INSTITUTION = "University of Minnesota"
        INSTITUTIONSORT = "University of Minnesota"
        
        #to avoid authentication complications, for now we'll just set access field to public
        ACCESS= "public"
        #try:
        #    ACCESS = root.find("idinfo/accconst").text
        #except AttributeError as e:
        #    print "Access Constraints field doesn't exist! Setting to UNKNOWN for now"        
        #    ACCESS = "UNKNOWN"
        AVAILABILITY = "Online"

        #set Display Name equal to title element   
        try:
            LAYERDISPLAYNAME = root.findtext("idinfo/citation/citeinfo/title")
 
        except AttributeError:
            print 'No Title element found...'
            LAYERDISPLAYNAME = "UNKNOWN"
        
        LAYERDISPLAYNAMESORT = LAYERDISPLAYNAME
        
                
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
            
        
        try:

            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
                if len(dateText) == 4:
                    #if it's just 4 digits, lets assume it's the year and convert it to integer
                    year = int(dateText)

                    #set month to January
                    month = 1

                    #set day to the 1st
                    day = 1

                    #put em all together
                    date = datetime(year,month,day)

                    #now format it ISO style
                    CONTENTDATE = date.isoformat() + "Z"
                elif len(dateText) == 8:
                    #print dateText
                    year = int(dateText[0:4])
                    month = int(dateText[4:6])
                    day = int(dateText[6:])
                    date = datetime(year,month,day)
                    CONTENTDATE = date.isoformat() + "Z"
            elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
                dateText = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text
                if len(dateText) == 4:
                    #if it's just 4 digits, lets assume it's the year
                    year = dateText

                    #set month to January
                    month = 1

                    #set day to the 1st
                    day = 1

                    #put em all together
                    date = datetime(year,month,day)

                    #now format it ISO style
                    CONTENTDATE = date.isoformat() + "Z"
                elif len(dateText) == 8:
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

        print CONTENTDATE

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
        
        OGPtree = et.ElementTree()
        OGProot = et.Element("add",allowDups="false")
        doc = et.SubElement(OGProot,"doc")
        OGPtree._setroot(OGProot)
        try:
            for field in fields:
                fieldEle = et.SubElement(doc,"field",name=field)
                fieldEle.text = locals()[field.upper()]
        except KeyError as e:
            print "Nonexistant key: ", field
            error_counter += 1
        

        fgdc_text = et.SubElement(doc,"field",name="FgdcText")
        fgdc_text.text = '<?xml version="1.0"?>'+FGDC_TEXT

        #check to see which etree module was used. If lxml was used
        #then we can pretty print the results. Otherwise we need to
        #remove the pretty print kwarg
        if et.__name__[0] == "l":
            if error_counter <= max_errors:
                if os.path.exists(OUTPUT_LOCATION + LAYERID + "_OGP.xml"):
                    existsPrompt =raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml",pretty_print=True)
                        print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"
                    else:
                        pass
                else:
                    OGPtree.write(OUTPUT_LOCATION + LAYERID + "_OGP.xml",pretty_print=True)
                    
                    print "Output file: " + OUTPUT_LOCATION + LAYERID + "_OGP.xml"
            else:
                print 'File exceeded error tolerance of ', max_errors,', so into the error folder it goes'
                if os.path.exists(ERROR_LOCATION + LAYERID + "_OGP.xml"):
                    existsPrompt =raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(ERROR_LOCATION + LAYERID + "_OGP.xml",pretty_print=True)
                        print "Output file: " + ERROR_LOCATION + LAYERID + "_OGP.xml"
                    else:
                        pass
                else:
                    OGPtree.write(ERROR_LOCATION + LAYERID + "_OGP.xml",pretty_print=True)
                    
                    print "Output file: " + ERROR_LOCATION + LAYERID + "_OGP.xml"
        else:
            if error_counter <= max_errors:
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
            else:
                print 'File exceeded error tolerance of ', max_errors,', so into the error folder it goes'
                if os.path.exists(ERROR_LOCATION + LAYERID + "_OGP.xml"):
                    existsPrompt =raw_input('OGP metadata already exists! Overwrite? (Y/N): ')
                    if existsPrompt == 'Y':
                        OGPtree.write(ERROR_LOCATION + LAYERID + "_OGP.xml")
                        print "Output file: " + ERROR_LOCATION + LAYERID + "_OGP.xml"
                    else:
                        pass
                else:
                    OGPtree.write(ERROR_LOCATION + LAYERID + "_OGP.xml")
                    
                    print "Output file: " + ERROR_LOCATION + LAYERID + "_OGP.xml"

        print "\n"
        
    end = clock()
    if (end-start) > 60:
        mins = str(math.ceil((end - start) / 60))
        secs = str(math.ceil((end - start) % 60))
        print str(len(files)) + " datasets processed in " + mins + " minutes and " + secs + " seconds"
    else:
        secs = str(math.ceil(end-start))
        print str(len(files)) + " datasets processed in " + secs + " seconds"
    sys.stdout=sys.__stdout__
    print 'Done. See log file for information'
    

