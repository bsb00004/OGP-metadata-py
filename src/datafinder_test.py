import json, urllib
import argparse
import os, os.path

parser = argparse.ArgumentParser()
parser.add_argument("ArcGISRest",help="indicate URL to the folder which contains ArcGISRestful map services")
parser.add_argument("output_path",help="indicate the path where the output should be sent")
args = parser.parse_args()

ArcGISRest = args.ArcGISRest
OUTPUT_FILE = args.output_path

if not os.path.isabs(OUTPUT_FILE):
    OUTPUT_FILE = os.path.abspath(os.path.relpath(OUTPUT_FILE,os.getcwd()))

OUTPUT_FILE = open(OUTPUT_FILE,"w")

u = urllib.urlopen("http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/?f=json")
j = json.loads(u.read())
services = j["services"]
names=[]
layers=[]
ldict={}
#
#The follow services don"t seem to be working at the moment
#
#only two layers, both of which are throwing AGS errors at the moment
#http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Environmental_Monitoring_Modeling/MapServer
#
#Transportation has a couple layers that seem to be causing trouble
#
#base
#http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Transportation/MapServer
#
#trouble layers
#http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Transportation/MapServer/29
#http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Transportation/MapServer/30
#
#
for service in services:
    try:
        serviceName = service["name"][service["name"].rfind("/")+1:]
        service_url = ArcGISRest+"/"+serviceName+"/"+service["type"]
        layers_url = service_url + "/layers?f=json"
        y = urllib.urlopen(layers_url)
        w = json.loads(y.read())
        for number,item in enumerate(w["layers"]):
            index = number
            #print "service: ",WorkspaceName,item["name"]
            currentLayerInfo ={}
            currentLayerInfo["layerId"] = str(item["id"])
            currentLayerInfo["ArcGISRest"] = str(service_url)
            ldict[item["name"]]= str(currentLayerInfo)
            #ldict[item["name"]]= "{\"layerId\":\""+str(item["id"])+"\",\"ArcGISRest\":\""+service_url+"\"}"
        #     names.append(item["name"])
        #     layers.append({item["name"]:{ "layerId":item["id"],
        #            #   "url": service_url+"/"+str(item["id"]),
        #                       #"WorkspaceName":WorkspaceName,
        #                       # I think we could get rid of tracking WorkspaceName since ArcGISRestful service is organized in Folder-MapServices-Layers.
        #                             "ArcGISRest":service_url,
        #                         "ServerType":service["type"]
        #                               }})
        # for layer in layers:
        #     ldict[layer.items()]='aaa'
    except ValueError:
        print service["name"]," is all messed up"


OUTPUT_FILE.write(json.dumps(ldict))
OUTPUT_FILE.close()
