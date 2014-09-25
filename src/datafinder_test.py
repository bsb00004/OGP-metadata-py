import json, urllib
from bs4 import BeautifulSoup

def getAGSdetails():

    ArcGISRestURL = "http://gis2.metc.state.mn.us/ArcGIS/rest/services/MetroGIS"

    if ArcGISRestURL[-1] == '/':
        ArcGISRestURL = ArcGISRestURL[:-1]

    u = urllib.urlopen(ArcGISRestURL+"?f=json")
    j = json.loads(u.read())
    services = j["services"]
    ldict={}


    for service in services:
        try:
            serviceName = service["name"][service["name"].rfind("/")+1:]
            service_url = ArcGISRestURL+"/"+serviceName+"/"+service["type"]
            layers_url = service_url + "/layers?f=json"
            y = urllib.urlopen(layers_url)
            w = json.loads(y.read())

            for item in w["layers"]:

                currentLayerInfo = {}
                currentLayerInfo["layerId"] = unicode(item["id"])
                currentLayerInfo["ArcGISRest"] = unicode(service_url)

                # description contains a link to the metadata html file, which
                # makes it waaay easier to get this shit working!
                if item["description"]:
                    description_link = BeautifulSoup(item["description"])
                    desc_link = description_link.find('a')
                    desc_link = desc_link.attrs['href']
                    desc_link = desc_link[desc_link.rfind('/') + 1: desc_link.rfind('.')] + '.xml'
                    ldict[desc_link]= currentLayerInfo

        except ValueError:
            print service["name"]," is all messed up"

    print 'there are:', len(list(ldict.iterkeys())),'layers'

    return ldict
