import argparse
import glob
import os.path
from src import mgmg2ogp,fgdc2ogp
parser = argparse.ArgumentParser()
parser.add_argument("workspace",help="indicate the path where the metadata to be converted is contained")
parser.add_argument("metadata_type",help="acceptable values are FGDC or MGMG", choices=['MGMG','FGDC'])
parser.add_argument("--et", type=int,help="acceptable level of error which decides for any given XML file whether it will be included in the final output folder, or the error folder. Default value of 5000. Lower value means less tolerance (0 means any missing or incorrect OGP field will cause the file to be moved to error folder)")
args = parser.parse_args()
ws = args.workspace
md = args.metadata_type
et = args.et
if et == None:
    et = 5000
    

if os.path.exists(ws) == False:
    print "Workspace does not seem to exist. Are you sure you entered it correctly?"
elif os.path.exists(ws) == True:
    if md.lower() == "mgmg":
        if ws[-1] == '\\':
            mgmg2ogp.MGMG(ws, et)   
        else:
            mgmg2ogp.MGMG(ws+'\\', et)
    
    elif md.lower() == "fgdc":
        if ws[-1] == '\\':
            fgdc2ogp.FGDC(ws, et)   
        else:
            fgdc2ogp.FGDC(ws+'\\', et)
    else:
        print "Unsupported metadata type entered. Currently supported values are FGDC or MGMG"
