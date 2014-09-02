#!/usr/bin/env python 
import sys
import argparse
import os, os.path
import fnmatch
from src import md2ogp

METADATA_OPTIONS = ['mgmg','fgdc','arcgis','marc']

try:
    from lxml import etree
    XML_LIB = "lxml" 
except ImportError:
    try:
        print "\nPython lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported.\n"
        from xml.etree import ElementTree as etree
        XML_LIB = "etree" 
    except ImportError:
        print "No xml lib found. Please install lxml lib to continue"

def processSingleFile():
    pass

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-m","--mgs", action="store_true", help="shortcut for MGS project")

    #TODO remove nargs from each of the following after MGS project complete
    parser.add_argument("workspace", nargs='?', help="indicate the path where the metadata to be converted is contained")
    parser.add_argument("output_path", nargs='?', help="indicate the path where the output should be sent")
    parser.add_argument("metadata_type", nargs='?', help="Metadata standard used for input XMLs. Acceptable values are FGDC, MGMG, or MARC")
    parser.add_argument("suffix", nargs='?', help="suffix to be appended to the end of each XML file name. Useful if you're expecting duplicate names. Defaults to 'OGP'")

    args = parser.parse_args()

    if args.suffix:
        suffix = args.suffix
    else:
        suffix = "OGP"

    # temporary MGS project shortcut... to be removed when done
    if args.mgs:
        mgs_record = raw_input("Please enter record number: ")
        ws = os.path.join("D:\drive\Map Library Projects\MGS\Records",
                          mgs_record,
                          "final_XMLs")
        output = os.path.join(ws,"OGP")
        md = "fgdc"


    else:

        # TODO remove when MGS project complete
        if (args.workspace is None) or (args.output_path is None) or (args.metadata_type is None):
            sys.exit('Missing arguments. Be sure to have a workspace path, output path, and metadata standard entered.')

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
        sys.exit('Invalid metadata standard. Supported options are %s. Please try again.' % ( " ,".join(METADATA_OPTIONS)))
    
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
            for filename in fnmatch.filter(filenames, '*[!aux][!_OGP][!template].xml'):
                files.append(os.path.join(root, filename))
                 
        # for each file, parse it into an ElementTree, then instantiate the appropriate metadata standard class
        for filename in files:

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
                doc = md2ogp.MGMGDocument(root,filename)

            elif md == "fgdc":
                doc = md2ogp.FGDCDocument(root,filename)

            elif md == "arcgis":
                doc = md2ogp.ArcGISDocument(root,filename)

            elif md == "marc":
                doc = md2ogp.MARCXMLDocument(root,filename)

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

            print 'Writing: ' + os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_" + suffix + ".xml")
            
            if XML_LIB == "lxml":
                OGPtree.write(os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_" + suffix + ".xml"), pretty_print=True)
            else:
                OGPtree.write(os.path.join(output, os.path.splitext(os.path.split(filename)[1])[0] + "_" + suffix + ".xml"))
                
if __name__ == "__main__":
    sys.exit(main())
