#!/usr/bin/env python 
import sys
import argparse
import os, os.path
import fnmatch 
from datetime import datetime
from src import md2ogp,logger

METADATA_OPTIONS = ['mgmg','fgdc','arcgis']

try:
    from lxml import etree
    XML_LIB = "lxml" 
except ImportError:
    try:
        print "Python lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported"
        from xml.etree import ElementTree as etree
        XML_LIB = "etree" 
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-m","--mgs", action="store_true", help="shortcut for MGS project")
    parser.add_argument("workspace", nargs='?', help="indicate the path where the metadata to be converted is contained")
    parser.add_argument("output_path", nargs='?', help="indicate the path where the output should be sent")
    parser.add_argument("metadata_type", nargs='?', help="Metadata standard used for input XMLs. Acceptable values are FGDC or MGMG")
    args = parser.parse_args()

    if args.mgs:
        mgs_record = raw_input("Please enter record number: ")
        ws = os.path.join("D:\drive\Map Library Projects\MGS\Records",
                          mgs_record,
                          "final_XMLs")
        output = os.path.join(ws,"OGP")
        md = "fgdc"


    else:

        # set workspace, check if it's an absolute or relative path and make changes as needed
        ws = args.workspace
        if not os.path.isabs(ws):
            ws = os.path.abspath(os.path.relpath(ws,os.getcwd()))

        # same for output path
        output = args.output_path
        if not os.path.isabs(output):
            output = os.path.abspath(os.path.relpath(output,os.getcwd()))

        md = args.metadata_type.lower()

    if md not in METADATA_OPTIONS:
        sys.exit('Invalid metadata standard. Supported options are "' + '", "'.join(METADATA_OPTIONS) + '". Please try again.')
    
    if os.path.exists(output) == False:
        try:
            os.mkdir(output)
        except OSError:
            print "There's a problem with the output path: %s. Are you sure you entered it correctly?" % (output)

    if os.path.exists(ws) == False:
        print "Workspace %s does not seem to exist. Are you sure you entered it correctly?" % (ws)

    elif os.path.exists(ws) == True:

        # assemble list of files to be processed
        files = []
        for root, dirnames, filenames in os.walk(ws):
            for filename in fnmatch.filter(filenames, '*[!aux].xml'):
                files.append(os.path.join(root, filename))
                 
        # initialize logger
        d = datetime.today()
        log_name = "OGP_MD_LOG_" + d.strftime("%y%m%d%M%S") + ".txt"
        sys.stdout = logger.Logger(output, log_name)

        # for each file, parse it into an ElementTree, then instantiate the appropriate metadata standard class
        for filename in files:

            OGPtree = etree.ElementTree()
            OGProot = etree.Element("add", allowDups="false")
            docElement = etree.SubElement(OGProot, "doc")
            OGPtree._setroot(OGProot)
            
            tree = etree.ElementTree()
            root = tree.parse(filename)

            if md == "mgmg":
                doc = md2ogp.MGMGDocument(root,filename)

            elif md == "fgdc":
                doc = md2ogp.FGDCDocument(root,filename)

            elif md == "arcgis":
                doc = md2ogp.ArcGISDocument(root,filename)

            for field in doc.field_handlers:
                try:
                    fieldEle = etree.SubElement(docElement, "field", name=field)
                    if hasattr(doc.field_handlers[field], '__call__'):
                        fieldEle.text = doc.field_handlers[field].__call__()
                    else:
                        fieldEle.text = doc.field_handlers[field]

                except KeyError as e:
                    print "Nonexistant key: ", field
                    error_counter += 1
            
            print 'Writing: ' + os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_OGP.xml")
            
            if XML_LIB == "lxml":
                OGPtree.write(os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_OGP.xml"), pretty_print=True)
            else:
                OGPtree.write(os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_OGP.xml"))
                
if __name__ == "__main__":
    sys.exit(main())
