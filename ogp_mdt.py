import argparse
import glob
from src import mgmg2ogp,fgdc2ogp
parser = argparse.ArgumentParser()
parser.add_argument("workspace",help="indicate the path where the metadata to be converted is contained")
parser.add_argument("metadata_type",help="acceptable values are FGDC or MGMG")
args = parser.parse_args()
ws = args.workspace
md = args.metadata_type

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
