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
from datatype_parse import dataTypeParseMGMG
try:
    from lxml import etree as et
except ImportError:
    try:
        print "Python lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported"
        from xml.etree import ElementTree as et
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"


    
def MGMG(workspace,error_tolerance):
    """
    Set workspace (where datasets to be processed are located) below
    """
    ws = workspace
    max_errors = error_tolerance
    
    
    #Set output location for OGP metadata and log file, then instantiate Logger
    output_random = random.randint(0,100000000)
    if os.path.exists(ws+"output" + str(output_random) + "\\"):
        OUTPUT_LOCATION = ws+"output" + str(output_random) + "\\"
    else:
        os.mkdir(ws+"output" + str(output_random) + "\\")
        OUTPUT_LOCATION =ws+"output" + str(output_random) + "\\"

    if os.path.exists(ws+"error"+ str(output_random) + "\\"):
        ERROR_LOCATION = ws+"error"+ str(output_random) + "\\"
    else:
        os.mkdir(ws+"error"+ str(output_random) + "\\")
        ERROR_LOCATION = ws+"error"+ str(output_random) + "\\"
    print 'output location: ', OUTPUT_LOCATION
    print 'error location: ', ERROR_LOCATION

    d=datetime.today()
    LOG_NAME = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"

    sys.stdout = Logger(OUTPUT_LOCATION,LOG_NAME)


    files = glob.glob(ws+'*[!aux].xml')

    fields = ['LayerId', 'Name', 'CollectionId', 'Institution', 'InstitutionSort',
              'Access', 'DataType', 'DataTypeSort', 'Availability', 'LayerDisplayName',
              'LayerDisplayNameSort', 'Publisher', 'PublisherSort', 'Originator',
              'OriginatorSort', 'ThemeKeywords', 'PlaceKeywords', 'Abstract', 'MaxY',
              'MinY', 'MinX', 'MaxX', 'ContentDate','Location','WorkspaceName']
    
    #Set UTC timezone for ContentDate field
    
    utc = pytz.utc
    
    #List of layers and their respective URLs from Datafinder.org
    
    df_lyrs_file = open("G:\\GoogleDrive\\Google Drive\\GitHub\\OGP-metadata-py\\tests\\datafinder_layers.json",'r')
    df_lyrs = json.loads(df_lyrs_file.read())


   
    #start the clock! obviously not at all necessary 
   
    start = clock()

    for i in files:
        print 'full file path is ', i
        error_counter = 0
        FGDCtree= et.ElementTree()
        root = FGDCtree.parse(i)

        #layerID equals filename sans extension 
        LAYERID = i[i.rfind('\\')+1:i.rfind(".")]
        #print 'layerid is ', LAYERID
        
        try:
            if df_lyrs.has_key(LAYERID):
                NAME = unicode(df_lyrs[LAYERID]["name"])
            else:
                NAME = LAYERID
        except AttributeError as e:
            print "Name field doesn't exist! Setting to UNKNOWN for now"
            NAME = "UNKNOWN"
            error_counter += 1
        
        try:
            if df_lyrs.has_key(LAYERID):
                WORKSPACENAME = unicode(df_lyrs[LAYERID]["WorkspaceName"])
        except AttributeError as e:
            print 'Workspace name error: ',e
            error_counter += 1
        DATATYPE = dataTypeParseMGMG(root)
        if DATATYPE == "Undefined":
            error_counter += 1
        DATATYPESORT = DATATYPE

        #create string representation of MGMG md to be appended at end of OGP md
        MGMG_TEXT = et.tostring(root)



        COLLECTIONID = "initial collection"
        
        INSTITUTION = "University of Minnesota"
        INSTITUTIONSORT = "University of Minnesota"
        
        #to avoid authentication complications, for now we'll just set access field to public
        ACCESS= "Public"
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

        THEMEKEYWORDS = keywordParse(FGDCtree,"themekey")
        PLACEKEYWORDS = keywordParse(FGDCtree,"placekey")
        
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
                print 'Invalid West Bounding Coordinate of:',MINX
                error_counter += 1
            
        except AttributeError as e:
            print "West Bounding Coordinate not found!"
            error_counter += 1
            
        try:
            MINY = root.find("idinfo/spdom/bounding/southbc").text
            try:
                MINYf = float(MINY)
            except (TypeError, ValueError):
                print 'Invalid South Bounding Coordinate of:',MINY
                error_counter += 1
        except AttributeError as e:
            print "South Bounding Coordinate not found!"
            error_counter += 1
            
        try:
            MAXX = root.find("idinfo/spdom/bounding/eastbc").text
            try:
                MAXXf = float(MAXX)
            except (TypeError, ValueError):
                print 'Invalid East Bounding Coordinate of:',MAXX
                error_counter += 1
        except AttributeError as e:
            print "East Bounding Coordinate not found!"
            error_counter += 1
            
        try:
            MAXY = root.find("idinfo/spdom/bounding/northbc").text
            try:
                MAXYf = float(MAXY)
            except (TypeError, ValueError):
                print 'Invalid North Bounding Coordinate of:',MAXY
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
                ARCGISREST = df_lyrs[LAYERID]["ArcGISRest"]             
                SERVERTYPE = df_lyrs[LAYERID]["ServerType"]
                #print 'Found',LAYERID,' so removing it from df_lyrs'
                df_lyrs.pop(LAYERID) 
                if root.find("idinfo/citation/citeinfo/onlink") is not None:
                    DOWNLOAD_URL = root.find("idinfo/citation/citeinfo/onlink").text
                    LOCATION = json.dumps({
                        'ArcGISRest': ARCGISREST,
                        'download' : DOWNLOAD_URL,
                        'ServerType': SERVERTYPE
                        })
                else:
                    LOCATION = json.dumps({
                        'ArcGISRest': ARCGISREST,
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
            error_counter += 1
        print 'number of errors: ', error_counter  
        
        #Put it all together to make the OGP metadata xml file
        
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
        
        #TODO eventually change OGP code base to recognize MgmgText as a
        #field and parse the metadata accordingly    
        #mgmg_text = et.SubElement(doc,"field",name="MgmgText")
        mgmg_text = et.SubElement(doc,"field",name="FgdcText")
        mgmg_text.text = '<?xml version="1.0"?>'+MGMG_TEXT

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
        print 'Done. See log file for information'


    else:
        secs = str(math.ceil(end-start))
        print str(len(files)) + " datasets processed in " + secs + " seconds"
        print 'Done. See log file for information'


