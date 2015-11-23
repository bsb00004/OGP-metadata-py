#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import argparse
import os, os.path
import fnmatch
import pdb
from src import md2ogp

METADATA_OPTIONS = ['mgmg','fgdc','arcgis','marc','iso','guess','eod','gdrs']

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path",help="indicate the path where the metadata to be converted is contained")
    parser.add_argument("output_path",help="indicate the path where the output should be sent, or 'same' if you want to output to the same path as the input")
    parser.add_argument("metadata_type",help="Metadata standard used for input XMLs. Acceptable values are FGDC, MGMG, ISO, EOD, MARC, GDRS or GUESS (which takes a guess)")
    parser.add_argument("-i","--indirect",action="store_true",help="If the links in the metadata do not directly return a binary file (e.g. a zip archive), set this option")
    parser.add_argument("-l","--log_only",action="store_true",help="If you just want the log written (i.e. no output XMLs). Useful for metadata cleanup.")
    parser.add_argument("-z","--zip", action="store_true", help="Output a zip file with the metadata files in it")
    parser.add_argument("-o","--overrides", help="provide JSON file of fields to override and the values to use instead")
    parser.add_argument("-s","--to_solr", action="store_true", help="if selected, will push straight to Solr")

    args = parser.parse_args()

    # set input_path, check if it's an absolute or relative path and make changes as needed
    ws = args.input_path
    if not os.path.isabs(ws):
        ws = os.path.abspath(os.path.relpath(ws,os.getcwd()))

    output = args.output_path

    if output.lower() != "same" and not os.path.isabs(output):
        output = os.path.abspath(os.path.relpath(output,os.getcwd()))
    elif output.lower() == "same":
        output = ws

    md = args.metadata_type.lower()

    if md not in METADATA_OPTIONS:
        sys.exit('Invalid metadata standard. Supported options are %s. Please try again.' % ( " ,".join(METADATA_OPTIONS)))

    if not os.path.exists(output):
        try:
            os.mkdir(output)
        except OSError:
            print "There's a problem with the output path: %s. Are you sure you entered it correctly?" % (output)

    if not os.path.exists(ws):
        print "Workspace %s does not seem to exist. Are you sure you entered it correctly?" % (ws)

    elif os.path.exists(ws):

        # instantiate base class to take in output path and metadata option
        ogp = md2ogp.baseOGP(output,md)

        if args.indirect:
            ogp.set_indirect_links()

        if args.log_only:
            ogp.logging_only()

        if args.zip:
            ogp.set_zip()

        if args.overrides:
            ogp.set_overrides(args.overrides)

        files = []

        if md == "gdrs":
            filter_phrase == "metadata.xml"
        else:
            filter_phrase == "*.xml"

        # assemble list of files to be processed
        for root, dirnames, filenames in os.walk(ws):

            #filters out certain XML file names
            for filename in fnmatch.filter(filenames, filter_phrase):
                files.append(unicode(os.path.join(root, filename), "utf-8"))

        print 'There are %s files to be processed.' % (len(files))

        if args.to_solr:
            ogp.set_solr()
            ogp.process_for_solr(files)

        else:
            ogp.process_list_of_files(files)


if __name__ == "__main__":
    sys.exit(main())
