#!/usr/bin/env python 
import sys
import argparse
import os, os.path
import fnmatch 
from datetime import datetime
#from src import mgmg2ogp,fgdc2ogp,logger
from src import mgmg2ogp,logger

try:
    from lxml import etree 
except ImportError:
    try:
        print "Python lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported"
        from xml.etree import ElementTree as etree
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("workspace",help="indicate the path where the metadata to be converted is contained")
    parser.add_argument("output_path",help="indicate the path where the output should be sent")
    parser.add_argument("metadata_type",help="Metadata standard used for input XMLs. Acceptable values are FGDC or MGMG", choices=['MGMG','FGDC'])
    parser.add_argument("--et", type=int,help="acceptable level of error which decides for any given XML file whether it will be included in the final output folder," +
                                              " or the error folder. Default value of 5000. Lower value means less tolerance (0 means any missing or incorrect OGP field" +
                                              " will cause the file to be moved to error folder)")
    args = parser.parse_args()
   
    ws = args.workspace
    output = args.output_path

    if not os.path.isabs(ws):
        ws = os.path.abspath(os.path.relpath(ws,os.getcwd()))

    if not os.path.isabs(output):
        output = os.path.abspath(os.path.relpath(output,os.getcwd()))
    
    md = args.metadata_type
    et = args.et

    if et == None:
        et = 5000    

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

        # for each file, parse it into an ElementTree, then  instantiate the appropraite metadata standard class
        for filename in files:

            tree = etree.ElementTree()
            root = tree.parse(filename)

            if md.lower() == "mgmg":
                doc = mgmg2ogp.MGMGDocument(root,filename)

            elif md.lower() == "fgdc":
                doc = mgmg2ogp.FGDCDocument(root,filename)

            elif md.lower() == "arcgis":
                doc = mgmg2ogp.ArcGISDocument(root,filename)

if __name__ == "__main__":
    sys.exit(main())
