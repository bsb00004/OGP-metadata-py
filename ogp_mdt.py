import argparse
import glob
import os.path
from src import mgmg2ogp,fgdc2ogp
parser = argparse.ArgumentParser()
parser.add_argument("workspace",help="indicate the path where the metadata to be converted is contained")
parser.add_argument("metadata_type",help="acceptable values are FGDC or MGMG")
args = parser.parse_args()
ws = args.workspace
md = args.metadata_type

if os.path.exists(ws) == False:
    print "Workspace does not seem to exist. Are you sure you entered it correctly?"
elif os.path.exists(ws) == True:
    if md.lower() == "mgmg":
        if ws[-1] == '\\':
            mgmg2ogp.MGMG(ws)   
        else:
            mgmg2ogp.MGMG(ws+'\\')
    
    if md.lower() == "fgdc":
        if ws[-1] == '\\':
            fgdc2ogp.FGDC(ws)   
        else:
            fgdc2ogp.FGDC(ws+'\\')
    else:
        print "Unsupported metadata type entered. Currently supported values are FGDC or MGMG"
