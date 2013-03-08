import json, urllib

BASE_URL= "http://gis2.metc.state.mn.us/ArcGIS/rest/services/"
ArcGISRest = "http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS"
OUTPUT_FILE = open("G:\\Documents\\GitHub\\OGP-metadata-py\\tests\\datafinder_layers.json","w")

u = urllib.urlopen("http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/?f=json")
j = json.loads(u.read())
services = j["services"]
layers=[]
names=[]

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
        WorkspaceName = service["name"][service["name"].rfind("/")+1:]
        service_url = BASE_URL+service["name"]+"/"+service["type"]
        layers_url = service_url + "/layers?f=json"
        y = urllib.urlopen(layers_url)
        w = json.loads(y.read())
        for number,item in enumerate(w["layers"]):
            index = number
            print "service: ",WorkspaceName,item["name"]
            names.append(item["name"])
            layers.append({item["name"]:{ "name":item["id"],
                   #   "url": service_url+"/"+str(item["id"]),
                              "WorkspaceName":WorkspaceName,
                                    "ArcGISRest":ArcGISRest,
                                "ServerType":service["type"]
                                      }})
    except ValueError:
        print service["name"]," is all messed up"

try:
    service_url = "http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Transportation/MapServer"
    layers_url = "http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS/Transportation/MapServer?f=json"
    WorkspaceName = "Transportation"
    y = urllib.urlopen(layers_url)
    w = json.loads(y.read())
    for number,item in enumerate(w["layers"]):
        index = number
        print "service: ",WorkspaceName,item["name"]
        names.append(item["name"])
        layers.append({item["name"]:{
            "name":item["id"],
            "WorkspaceName":WorkspaceName,
            "ArcGISRest":ArcGISRest,
            "ServerType":"MapServer"
            }})
    ldict={}
    for layer in layers:
        ldict = dict(ldict.items() + layer.items())
except ValueError:
    print "error"

OUTPUT_FILE.write(json.dumps(ldict))
OUTPUT_FILE.close()


