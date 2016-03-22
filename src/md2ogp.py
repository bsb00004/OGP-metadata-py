# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import os.path
import time
from datetime import datetime
import json
from logger import Logger
import ogp2solr
import dateutil.parser
import sys
import urllib2
import re
import codecs
import zipfile
import pdb
import glob
try:
    import zlib
    mode = zipfile.ZIP_DEFLATED
except ImportError:
    mode = zipfile.ZIP_STORED

try:
    from lxml import etree
except ImportError:
    try:
        print("\n\nPython lib lxml not found. Using xml.etree instead. Note that pretty printing with xml.etree is not supported.\n\n")
        from xml.etree import ElementTree as etree
    except ImportError:
        print("No xml lib found. Please install lxml lib to continue")


def parse_data_type_FGDC(root):
    try:
        if root.find("*//geoform") is not None:
            geoform = root.findtext("*//geoform").lower()
            if ("scanned" in geoform or
                "paper" in geoform or
                "scanned paper map" in geoform
            ):
                return "Paper Map"

        if root.find("*//direct") is not None:
            direct = root.findtext("*//direct").lower()
            if "raster" in direct:
                return "Raster"
            elif (
                "g-polygon" in direct or
                "polygon" in direct or
                "chain" in direct
            ):
                return "Polygon"
            elif "point" in direct:
                return "Point"

        if root.find("*//sdtstype") is not None:
            sdtstype = root.findtext("*//sdtstype").lower()
            if ("composite" in sdtstype or
                "point" in sdtstype
            ):
                return "Point"
            elif "string" in sdtstype:
                return "Line"
            elif ("g-polygon" in sdtstype or
                  "polygon" in sdtstype or
                  "chain" in sdtstype
            ):
                return "Polygon"

    except AttributeError as e:
        return "Undefined"


def parse_data_type_MGMG(root):
    try:
        if root.findtext("*//direct").lower() == "raster":
            return "Raster"
        if root.findtext("*//direct").lower() == "point":
            return "Point"
        if root.findtext("*//direct").lower() == "vector":
            mgmg3obj = root.find("*//mgmg3obj")

            if mgmg3obj is not None:

                mgmg3obj = mgmg3obj.text.lower()
                if (
                    "area" in mgmg3obj or
                    "polygon" in mgmg3obj or
                    "region" in mgmg3obj or
                    "TIN" in mgmg3obj
                ):
                    return "Polygon"

                elif (
                    "line" in mgmg3obj or
                    "network" in mgmg3obj or
                    "route-section" in mgmg3obj or
                    "arc" in mgmg3obj
                ):
                    return "Line"
                elif (
                    "node" in mgmg3obj or
                    "point" in mgmg3obj or
                    "label" in mgmg3obj
                ):
                    return "Point"

        if root.find("*//sdtstype") is not None:
            sdtstype = root.findtext("*//sdtstype").lower()
            if ("composite" in sdtstype or
                "point" in sdtstype
            ):
                return "Point"
            elif "string" in sdtstype:
                return "Line"
            elif ("g-polygon" in sdtstype or
                  "polygon" in sdtstype or
                  "chain" in sdtstype
            ):
                return "Polygon"

        else:
            return "Undefined"

    except AttributeError as e:
        print("Can't determine data type, setting to Undefined for now")

        return "Undefined"


def _build_base_ogp_tree():
    # build empty etree to house output doc
    ogp_root = etree.Element("add", allowDups="false")
    return ogp_root


def _process_field_handlers(doc):
    root_element = _build_base_ogp_tree()
    doc_element = etree.SubElement(root_element, "doc")
    for field in doc.field_handlers:
        try:
            field_ele = etree.SubElement(doc_element, "field", name=field)

            if hasattr(doc.field_handlers[field], '__call__'):
                field_ele.text = doc.field_handlers[field].__call__()
            else:

                field_ele.text = doc.field_handlers[field]

        except (KeyError, ValueError) as e:
            print("Nonexistent key: ", field)
            print(e)
    return root_element


def write_ogp_tree(doc):
    return _process_field_handlers(doc)


class baseOGP(object):
    def __init__(self, output_path, md):

        self.output_path = output_path.rstrip('/')
        self.log = self.create_log()
        self.md = md.lower()
        self.indirect_links = False
        self.logging_only = False
        self.zip= False
        self.to_solr = False
        self.zip_file = self.init_zip()
        self.overrides = {}




    def set_overrides(self,f):

        if not os.path.isfile(f):
            sys.exit("Override file does not seem to exist")

        self.overrides = json.load(open(f))

    def init_zip(self):

        if self.zip:
            d = datetime.now()
            ds = d.strftime('%m%d%Y_%H%M')
            zip_file_name = os.path.join(self.output_path,
                self.output_path.split(os.path.sep)[-1] + "_" + ds + "_OGP.zip")
            return zipfile.ZipFile(zip_file_name, 'a', mode)

        else:
            return None

    def add_to_zip(self,tree,name):
        self.zip_file.writestr(
            os.path.split(name)[1]+"_OGP.xml", etree.tostring(tree)
            )

    def set_indirect_links(self):
        self.indirect_links = True

    def set_zip(self):
        self.zip = True
        self.zip_file = self.initZip()

    def set_logging_only(self):
        self.logging_only = True

    def create_log(self):
        return Logger(self.output_path)

    def process_for_solr(self,listoffiles):
        trees = []
        for f in listoffiles:
            trees.append(self.process_file(f))
        self.solr.add_to_solr_bulk(trees)

    def set_solr(self, url="http://54.235.211.28:8080/solr/collection1/"):
        self.to_solr = True
        self.solr = ogp2solr.SolrOGP(url)


    def process_list_of_files(self, listoffiles):

        if not os.path.exists(self.output_path):
            try:
                os.mkdir(self.output_path)
            except OSError:
                print("There's a problem with the output path: {path}. Are you sure you entered it correctly?".format(path=self.output_path))


        for f in listoffiles:
            self.process_file(f)

        # when done, close the log file and zip
        self.log.close()

        if self.zip:
            self.zip_file.close()


    def check_for_BOM(self,filename):
        with open(filename, "r") as opened_file:
            contents = opened_file.read()
            if contents[:3] == codecs.BOM_UTF8:
                print "found BOM in {name}".format(name=filename)
                return contents[3:]
            else:
                return False


    def remove_BOM(self, filename, new_contents):
        write_file = open(filename, "w")
        write_file.write(new_contents)
        write_file.close()


    def process_file(self, filename):

        print('Starting file:', filename)

        # parse the current XML into an etree
        tree = etree.ElementTree()

        try:
            root = tree.parse(filename, etree.XMLParser(encoding="utf-8"))
        except Exception as e:
            pdb.set_trace()
            bom_contents = self.check_for_BOM(filename)
            if bom_contents:
                self.remove_BOM(filename, bom_contents)
                root = tree.parse(filename, etree.XMLParser(encoding="utf-8"))
            else:
                raise e

        # grab the full text of the current XML for later use
        fullText = etree.tostring(root)

        doc = False

        if self.md == "mgmg":
            doc = MGMGDocument(root, filename, self.log, self.indirect_links)

        elif self.md == "fgdc":
            doc = FGDCDocument(root, filename, self.log, self.indirect_links)

        elif self.md == "arcgis":
            doc = ArcGISDocument(root, filename, self.log, self.indirect_links)

        elif self.md == "iso":
            doc = ISODocument(root, filename, self.log, self.indirect_links)

        elif self.md == "eod":
            doc = EsriOpenDataISODocument(root, filename, self.log, self.indirect_links)

        elif self.md == "marc":
            doc = MARCXMLDocument(root, filename, self.log, self.indirect_links)

        elif self.md == "gdrs":
            doc = GDRSDocument(root, filename, self.log, self.indirect_links)

        elif self.md == "guess":

            if root.find("metainfo/metstdn") is not None:
                if "Minnesota" in root.find("metainfo/metstdn").text:
                    doc = MGMGDocument(root, filename, self.log, self.indirect_links)
                elif "FGDC" in root.find("metainfo/metstdn").text:
                    doc = FGDCDocument(root, filename, self.log, self.indirect_links)
            elif root.find("collection/record") is not None:
                doc = MARCXMLDocument(root, filename, self.log, self.indirect_links)
            elif "_Metadata" in root.tag:
                doc = ISODocument(root, filename, self.log, self.indirect_links)
            else:
                self.log.write(filename, 'metadata standard undecipherable')

        if doc:
            root_element = _build_base_ogp_tree()
            doc_element = etree.SubElement(root_element, "doc")

            for field in doc.field_handlers:
                try:
                    fieldEle = etree.SubElement(doc_element, "field", name=field)

                    if self.overrides.has_key(field):
                        fieldEle.text = self.overrides[field]
                    elif hasattr(doc.field_handlers[field], '__call__'):
                        fieldEle.text = doc.field_handlers[field].__call__()
                    else:
                        fieldEle.text = doc.field_handlers[field]

                except KeyError as e:
                    print("Nonexistant key: ", field)

            fullTextElement = etree.SubElement(doc_element, "field", name="FgdcText")
            fullTextElement.text = fullText

            if not self.logging_only:

                new_tree = etree.ElementTree(root_element)

                if self.md == "gdrs":
                    resultName = os.path.join(self.output_path, filename.split(os.path.sep)[-2] +".xml")
                else:
                    resultName = os.path.join(self.output_path,
                        os.path.splitext(os.path.split(filename)[1])[0] + "_OGP.xml")

                # check for duplicate names (since w're looking across records with similar dataset content)
                # and add an _ to the end to avoid overwriting
                if os.path.exists(resultName):
                    resultName = os.path.splitext(resultName)[0] + "_" + os.path.splitext(resultName)[1]

                if self.zip:
                    print('Writing: ' + resultName)
                    self.add_to_zip(new_tree,filename)
                elif self.to_solr:
                    return new_tree
                elif "lxml" in etree.__name__:
                    print('Writing: ' + resultName)
                    new_tree.write(resultName, pretty_print=True)
                else:
                    print('Writing: ' + resultName)
                    new_tree.write(resultName)




class MetadataDocument(object):
    """
    Base class for metadata documents. This is where OGP fields that are handled the same
    across standards are implemented.
    """

    def __init__(self, root, file_name, log, indirect_links):
        self.log = log
        self.root = root
        self.file_name = file_name
        self.indirect_links = indirect_links

        """
        For docs without a specified bounding box, will use the below,
        by default set to state of MN
        """
        self.DEFAULT_BBOX = {
            "min_x": "-97.5",
            "max_x": "-89",
            "min_y": "43",
            "max_y": "49.5"
        }

        # create a dictionary containing the OGP field names as keys, mapping
        # the corresponding class method (or hardcoded string) as value
        self.field_handlers = {

            # hardcoded values first
            "Access": "Public",
            "Availability": "Online",
            "Institution": "Minnesota",
            "InstitutionSort": "Minnesota",
            "CollectionId": "initial collection",
            "WorkspaceName": "edu.umn",


            # the rest are associated with a method
            "Publisher": self.publisher,
            "PublisherSort": self.publisher,
            "Originator": self.originator,
            "OriginatorSort": self.originator,
            "DataType": self.data_type,
            "ThemeKeywords": self.theme_keywords,
            "PlaceKeywords": self.place_keywords,
            "LayerId": self.layer_id,
            "Location": self.location,
            "Name": self.name,
            "LayerDisplayName": self.layer_display_name,
            "LayerDisplayNameSort": self.layer_display_name,
            "ContentDate": self.content_date,
            "Abstract": self.abstract,
            "MinX": self.min_x,
            "MaxX": self.max_x,
            "MinY": self.min_y,
            "MaxY": self.max_y,
            "CenterX": self.center_x,
            "CenterY": self.center_y
        }

    # field methods
    def _file_name_sans_extension(self):
        file_name = os.path.basename(self.file_name)
        file_name = "".join(file_name.split(".")[:-1])
        return file_name

    def layer_id(self):
        return self._file_name_sans_extension() + str(time.time()).replace('.', '')

    def name(self):
        return self._file_name_sans_extension()

    def data_type(self):
        # see standard specific sub-class implementation
        pass

    def theme_keywords(self):
        # see standard specific sub-class implementation
        pass

    def place_keywords(self):
        # see standard specific sub-class implementation
        pass

    def publisher(self):
        # see standard specific sub-class implementation
        pass

    def originator(self):
        # see standard specific sub-class implementation
        pass

    def layer_display_name(self):
        # see standard specific sub-class implementation
        pass

    def _location_check_indirect(self,d,loc):

        if self.indirect_links:
            d['externalDownload'] = loc
        else:
            d['download'] = loc
        return d

    def location(self):
        # see standard specific sub-class implementation
        pass

    def content_date(self):
        # see standard specific sub-class implementation
        pass

    def abstract(self):
        # see standard specific sub-class implementation
        pass

    def min_x(self):
        # see standard specific sub-class implementation
        pass

    def min_y(self):
        # see standard specific sub-class implementation
        pass

    def max_x(self):
        # see standard specific sub-class implementation
        pass

    def max_y(self):
        # see standard specific sub-class implementation
        pass

    def center_x(self):
        # see standard specific sub-class implementation
        pass

    def center_y(self):
        # see standard specific sub-class implementation
        pass


class ISODocument(MetadataDocument):
    def __init__(self, root, filename, log, indirect_links):
        super(ISODocument, self).__init__(root, filename, log, indirect_links)

        self.NSMAP = {
           "srv":"http://www.isotc211.org/2005/srv",
           "gco":"http://www.isotc211.org/2005/gco",
           "xlink":"http://www.w3.org/1999/xlink",
           "gts":"http://www.isotc211.org/2005/gts",
           "xsi":"http://www.w3.org/2001/XMLSchema-instance",
           "gml":"http://www.opengis.net/gml",
           "gmd":"http://www.isotc211.org/2005/gmd"
        }




# _______         _______..  ______         __
# |   ____|       /       |  |   _  \       |  |
# |  |__         |   (----`  |  |_)  |      |  |
# |   __|         \   \      |      /       |  |
# |  |____    .----)   |     |  |\  \----.  |  |
# |_______|   |_______/      | _| `._____|  |__|

class EsriOpenDataISODocument(ISODocument):
    """
    Handle a particular instance of ISO document created by another script that parses
    Esri Open Data sites' data.json files
    """
    def __init__(self, root, filename, log, indirect_links):
        super(EsriOpenDataISODocument, self).__init__(root, filename, log, indirect_links)


        self.PATHS = {
            "title"              : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString",
            "pubdate"            : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:DateTime",
            "onlink"             : "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL",
            "origin"             : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString",
            "publish"            : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString",
            "westbc"             : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/gco:Decimal",
            "eastbc"             : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/gco:Decimal",
            "northbc"            : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/gco:Decimal",
            "southbc"            : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/gco:Decimal",
            "themekey"           : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode",
            "placekey"           : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:type/gmd:MD_KeywordTypeCode[@codeListValue='place']",
            "abstract"           : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString",
            "accconst"           : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString",
            "useconst"           : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_Constraints/gmd:useLimitation/gco:CharacterString",
            "formname"           : "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString",
            "id"                 : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString",
            "distribution_links" : "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:protocol/gco:CharacterString",
            "vector_datatype"    : "gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode",
            "spatialrep"         : "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode"
        }

    def data_type(self):

        #TODO check for vector/raster first using spatialrep

        spatial_rep_code = self.root.find(self.PATHS["spatialrep"], self.NSMAP).get("codeListValue")

        if spatial_rep_code == "vector":

            code = self.root.find(self.PATHS["vector_datatype"], self.NSMAP).get("codeListValue")
            if code == "point":
                return "Point"
            elif code == "curve":
                return "Line"
            elif code == "surface" or code == "complex":
                return "Polygon"

        elif spatial_rep_code == "grid":
            return "Raster"

    def layer_id(self):
        print self.root.find(self.PATHS["id"], self.NSMAP).text.split("/")[-1]
        return self.root.find(self.PATHS["id"], self.NSMAP).text.split("/")[-1]

    def theme_keywords(self):
        keywords =  self.root.findall(self.PATHS["themekey"], self.NSMAP)
        keywords_list = [k.text for k in keywords if k is not None]

        if not keywords_list:
            return ""
        elif len(keywords_list) == 1:
            return keywords_list[0]
        elif len(keywords_list) > 1:
            print keywords_list
            return ", ".join(keywords_list)


    def place_keywords(self):
        keywords =  self.root.find(self.PATHS["placekey"], self.NSMAP).getparent().getparent().findall("gmd:keyword", self.NSMAP)
        keywords_string = [k.find("gco:CharacterString", self.NSMAP).text for k in keywords]
        if keywords_string[0]:
            return ", ".join(keywords_string)
        return ""

    def publisher(self):
        return self.root.findtext(self.PATHS["publish"], "UNKNOWN", self.NSMAP)


    def originator(self):
        return self.root.findtext(self.PATHS["origin"], "UNKNOWN", self.NSMAP)

    def layer_display_name(self):
        return self.root.findtext(self.PATHS["title"], "UNKNOWN", self.NSMAP)

    def _location_check_indirect(self,d,loc):

        if self.indirect_links:
            d['externalDownload'] = loc
        else:
            d['download'] = loc
        return d

    def _location_get_protocols(self):
        """
        returns a dict of protocols (keys) and matching URLs (values)
        """

        link_protocols = self.root.findall(self.PATHS["distribution_links"], self.NSMAP)
        d = {}

        for protocol in link_protocols:
            d[protocol.text] = protocol.getparent().getparent().findtext("gmd:linkage/gmd:URL", "UNKNOWN", self.NSMAP)

        return d

    def _location_build(self, protocols):
        """
        creates an OGP specific dict from a dict of protocol/urls
        """
        loc = {}

        # protocols identified in Cat-Interop table
        # see https://github.com/OSGeo/Cat-Interop/blob/master/LinkPropertyLookupTable.csv
        for p in protocols:
            url = protocols[p]

            if url != "":
                if p == "ESRI:ArcGIS":

                    if url.find("FeatureServer") is -1:
                        loc["ArcGISRest"] = url[:url.rfind("/")]
                        loc["layerId"] = url[url.rfind("/") + 1:]
                    else:
                        loc["esrifeatureservice"] = url + "/"
                    #loc["layerId"] = url[url.rfind("/") + 1:]

                #TODO uncomment when we can handle 202s from EOD appropriately
                elif p == "download":
                    loc["download"] = url

                # indicates an indirect link
                #elif p == "WWW:LINK":
                #    loc["externalDownload"] = url

        return loc

    def location(self):
        protocols = self._location_get_protocols()
        loc = self._location_build(protocols)
        return json.dumps(loc)

    def content_date(self):
        return self.root.findtext(self.PATHS["pubdate"], "1919-08-01T00:00:00Z", self.NSMAP)

    def abstract(self):
        return self.root.findtext(self.PATHS["abstract"],"UNKNOWN", self.NSMAP)

    def min_x(self):
        return self.root.findtext(self.PATHS["westbc"], "UNKNOWN", self.NSMAP)

    def min_y(self):
        return self.root.findtext(self.PATHS["southbc"], "UNKNOWN", self.NSMAP)

    def max_x(self):

        return self.root.findtext(self.PATHS["eastbc"], "UNKNOWN", self.NSMAP)

    def max_y(self):
        return self.root.findtext(self.PATHS["northbc"], "UNKNOWN", self.NSMAP)

    def center_x(self):

        spread = abs(float(self.max_x()) - float(self.min_x())) / 2
        return unicode(float(self.max_x()) - spread)

    def center_y(self):
        spread = abs(float(self.max_y()) - float(self.min_y())) / 2
        return unicode(float(self.max_y()) - spread)


class ArcGISDocument(MetadataDocument):
    """
    Unimplemented. Inherits from MetadataDocument
    """

    def __init__(self, root, filename, log, indirect_links):
        super(ArcGISDocument, self).__init__(root, filename, log, indirect_links)



#  _______     _______    _______      ______
# |   ____|   /  _____|  |       \    /      |
# |  |__     |  |  __    |  .--.  |  |  ,----'
# |   __|    |  | |_ |   |  |  |  |  |  |
# |  |       |  |__| |   |  '--'  |  |  `----.
# |__|        \______|   |_______/    \______|

class FGDCDocument(MetadataDocument):
    """
    inherits from MetadataDocument
    """

    def __init__(self, root, filename, log, indirect_links):
        super(FGDCDocument, self).__init__(root, filename, log, indirect_links)

    def publisher(self):
        publisher = self.root.findtext("idinfo/citation/citeinfo/pubinfo/publish", "UNKNOWN")
        return publisher

    def layer_id(self):
        layer_id = self.root.find("idinfo/citation/citeinfo/title").get("catid")

        if layer_id is not None:
            return layer_id
        else:
            self.log.write(self.file_name, 'No catid found in title, using file name for now')
            return self.file_name.split(os.path.sep)[-1].replace(".xml","")


    def layer_display_name(self):
        disp_name = self.root.findtext("idinfo/citation/citeinfo/title", "UNKNOWN")
        #disp_name = disp_name + " (" + self.name() + ")"
        return disp_name.replace("_"," ").title()

    def abstract(self):
        abstract = self.root.findtext("idinfo/descript/abstract", "UNKNOWN")
        return abstract

    def originator(self):
        originator = self.root.findtext("idinfo/citation/citeinfo/origin", "UNKNOWN")
        return originator

    def data_type(self):
        root = self.root
        try:
            if root.find("*//geoform") is not None:
                geoform = root.findtext("*//geoform").lower()
                if ("scanned" in geoform or
                    "paper" in geoform or
                    "scanned paper map" in geoform
                ):
                    return "Paper Map"

            if root.find("*//direct") is not None:
                direct = root.findtext("*//direct").lower()
                if "raster" in direct:
                    return "Raster"
                elif (
                    "g-polygon" in direct or
                    "polygon" in direct or
                    "chain" in direct
                ):
                    return "Polygon"
                elif "point" in direct:
                    return "Point"

            if root.find("*//sdtstype") is not None:
                sdtstype = root.findtext("*//sdtstype").lower()
                if ("composite" in sdtstype or
                    "point" in sdtstype
                ):
                    return "Point"
                elif "string" in sdtstype:
                    return "Line"
                elif ("g-polygon" in sdtstype or
                      "polygon" in sdtstype or
                      "chain" in sdtstype
                ):
                    return "Polygon"

        except AttributeError as e:
            self.log.write(self.file_name, 'can\'t find data type')
            return "Undefined"

    def theme_keywords(self):
        try:
            kw = list(self.root.iter("themekey"))

            if len(kw) > 0:
                kw_str = [i.text for i in kw][0]
                return kw_str
            else:
                return 'None'
        except AttributeError as e:
            self.log.write(self.file_name, 'can\'t find keywords')
            return "UNKNOWN"

    def place_keywords(self):
        try:
            kw = list(self.root.iter("placekey"))

            if len(kw) > 0:
                kw_str = [i.text for i in kw][0]
                return kw_str
            else:
                return 'None'
        except AttributeError as e:
            print("can't find keywords. Setting to UNKNOWN for now")
            self.log.write(self.file_name, 'can\'t find keywords')
            return "UNKNOWN"

    def _parse_content_date(self, date_text):
        try:
            if self._try_parse_int(date_text) is not None:
                if len(date_text) == 4:
                    year = int(date_text)

                    # we'll just use Jan 1 as the default for year only entries
                    date = datetime(year, 1, 1)

                    #now format it ISO style
                    return date.isoformat() + "Z"
                elif len(date_text) == 8:
                    year = int(date_text[0:4])
                    month = int(date_text[4:6])
                    day = int(date_text[6:])
                    date = datetime(year, month, day)
                    return date.isoformat() + "Z"
            else:
                self.log.write(self.file_name, 'can\'t parse date with text: "' + date_text + '"')
        except ValueError as e:
            return "UNKNOWN"

    def _try_parse_int(self, s, base=10, val=None):
        try:
            return int(s, base)
        except ValueError:
            return val

    def content_date(self):
        root = self.root
        try:
            if root.find("idinfo/timeperd/timeinfo/sngdate/caldate") is not None:
                date_text = root.find("idinfo/timeperd/timeinfo/sngdate/caldate").text
            elif root.find("idinfo/timeperd/timeinfo/rngdates/begdate") is not None:
                date_text = root.find("idinfo/timeperd/timeinfo/rngdates/begdate").text
            elif root.find("idinfo/citation/citeinfo/pubdate") is not None:
                date_text = root.find("idinfo/citation/citeinfo/pubdate").text
            else:
                date_text = False

            if date_text:
                return self._parse_content_date(date_text)
            else:
                self.log.write(self.file_name, 'can\'t find date')
                return "1919-08-01T00:00:00Z"

        except (AttributeError, TypeError) as e:
            print(e)
            print("No content date found! setting to 1919-08-01T00:00:00Z for now")
            self.log.write(self.file_name, 'can\'t find date')
            return "1919-08-01T00:00:00Z"

    def _parse_coord(self, coord):
        try:
            coord = float(coord)
            return unicode(coord)
        except (ValueError, TypeError):
            self.log.write(self.file_name, 'can\'t parse coordinate: "' + coord + '"')
            return "0"

    def min_x(self):
        coord = self.root.findtext("idinfo/spdom/bounding/westbc", "UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        self.log.write(self.file_name, 'min_x issues')
        return "0"

    def min_y(self):
        coord = self.root.findtext("idinfo/spdom/bounding/southbc", "UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        self.log.write(self.file_name, 'min_y issues')
        return "0"

    def max_x(self):
        coord = self.root.findtext("idinfo/spdom/bounding/eastbc", "UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        self.log.write(self.file_name, 'max_x issues')
        return "0"

    def max_y(self):
        coord = self.root.findtext("idinfo/spdom/bounding/northbc", "UNKNOWN")
        if coord is not "UNKNOWN":
            return self._parse_coord(coord)
        self.log.write(self.file_name, 'max_y issues')
        return "0"

    def center_x(self):
        try:
            min_x = float(self.min_x())
            max_x = float(self.max_x())
            center_x = min_x + (abs(max_x - min_x) / 2)
            return unicode(center_x)
        except ValueError:
            self.log.write(self.file_name, 'center_x issues')
            return "0"

    def center_y(self):
        try:
            min_y = float(self.min_y())
            max_y = float(self.max_y())
            center_x = min_y + (abs(max_y - min_y) / 2)
            return unicode(center_x)
        except ValueError:
            self.log.write(self.file_name, 'center_y issues')
            return "0"


    def location(self):
        loc = self.root.findtext("idinfo/citation/citeinfo/onlink", "UNKNOWN")

        if loc != "UNKNOWN":
            locDict = {}
            locDict = self._location_check_indirect(locDict, loc)
            return json.dumps(locDict)
        else:
            self.log.write(self.file_name, 'can\'t find onlink.')
            return "UNKNOWN"


# .___  ___.     _______    .___  ___.     _______
# |   \/   |    /  _____|   |   \/   |    /  _____|
# |  \  /  |   |  |  __     |  \  /  |   |  |  __
# |  |\/|  |   |  | |_ |    |  |\/|  |   |  | |_ |
# |  |  |  |   |  |__| |    |  |  |  |   |  |__| |
# |__|  |__|    \______|    |__|  |__|    \______|

class MGMGDocument(FGDCDocument):
    """
    Inherits from FGDCDocument
    """

    def __init__(self, root, filename, log, indirect_links):
        super(MGMGDocument, self).__init__(root, filename, log, indirect_links)

    def data_type(self):
        root = self.root
        try:
            if root.findtext("*//direct").lower() == "raster":
                return "Raster"
            if root.findtext("*//direct").lower() == "point":
                return "Point"
            if root.findtext("*//direct").lower() == "vector":
                mgmg3obj = root.find("*//mgmg3obj")

                if mgmg3obj is not None:

                    mgmg3obj = mgmg3obj.text.lower()
                    if (
                        "area" in mgmg3obj or
                        "polygon" in mgmg3obj or
                        "region" in mgmg3obj or
                        "TIN" in mgmg3obj
                    ):
                        return "Polygon"

                    elif (
                        "line" in mgmg3obj or
                        "network" in mgmg3obj or
                        "route-section" in mgmg3obj or
                        "arc" in mgmg3obj
                    ):
                        return "Line"
                    elif (
                        "node" in mgmg3obj or
                        "point" in mgmg3obj or
                        "label" in mgmg3obj
                    ):
                        return "Point"

            if root.find("*//sdtstype") is not None:
                sdtstype = root.findtext("*//sdtstype").lower()

                if sdtstype:
                    if ("composite" in sdtstype or
                        "point" in sdtstype
                    ):
                        return "Point"
                    elif "string" in sdtstype:
                        return "Line"
                    elif ("g-polygon" in sdtstype or
                          "polygon" in sdtstype or
                          "chain" in sdtstype
                    ):
                        return "Polygon"

            else:
                self.log.write(self.file_name, 'data type issues')
                return "Undefined"

        except AttributeError as e:
            print("Can't determine data type, setting to Undefined for now")
            self.log.write(self.file_name, 'data type issues')
            return "Undefined"


    def location(self):
        loc = self.root.findtext("idinfo/citation/citeinfo/onlink", "UNKNOWN")

        if loc != "UNKNOWN":
            locDict = {}

            """
            #datafinder.org specific stuff
            try:
                if df.has_key(os.path.split(self.file_name)[1]):
                    f = df[os.path.split(self.file_name)[1]]
                    locDict['ArcGISRest'] = f['ArcGISRest']
                    locDict['layerId'] = f['layerId']
            except KeyError:
                pass
            """

            #end datafinder specific

            locDict = self._location_check_indirect(locDict, loc)
            return json.dumps(locDict)

        else:
            self.log.write(self.file_name, 'can\'t find onlink, or else it\'s goofy somehow')
            return "UNKNOWN"

#   ______    _______     ______           _____.
#  /  _____|  |       \   |   _  \        /      |
# |  |  __    |  .--.  |  |  |_)  |      |   (---`
# |  | |_ |   |  |  |  |  |      /        \   \
# |  |__| |   |  '--'  |  |  |\  \--.  .--)   |
#  \______|   |_______/   | _| `.___|  |_____/
#
class GDRSDocument(MGMGDocument):
    def __init__(self, root, filename, log, indirect_links):
        super(GDRSDocument, self).__init__(root, filename, log, indirect_links)
        self.filename = filename
        self.root = root
        self._geospatial_commons_root_url = "https://gisdata.mn.gov/dataset/"
        self._gdrs_root_url = "ftp://ftp.gisdata.mn.gov/pub/gdrs/data/pub/"
        self.field_handlers["Access"] = "Public"
        self._get_resource_xml()
        self._data_resource_paths = {
            "sub_resources" : "dataSubResources/dataSubResource",
            "topic_categories":"topicCategories/topicCategory"
        }

        #taken from https://gisdata.mn.gov/content/?q=publisher_codes
        self._gdrs_publisher_codes = {
            "us_mn_co_dakota":"Dakota County",
            "us_mn_co_carver":"Carver County",
            "us_mn_co_lake":"Lake County",
            "us_mn_state_metrogis":"Metro GIS",
            "us_mn_state_metc":"Metropolitan Council",
            "us_mn_state_bwsr":"Minnesota Board of Water and Soil Resources (BWSR)",
            "us_mn_state_mda":"Minnesota Department of Agriculture",
            "us_mn_state_mde":"Minnesota Department of Education",
            "us_mn_state_health":"Minnesota Department of Health",
            "us_mn_state_dnr":"Minnesota Department of Natural Resources",
            "us_mn_state_mdor":"Minnesota Department of Revenue",
            "us_mn_state_dot":"Minnesota Department of Transportation",
            "edu_umn_mngs":"Minnesota Geological Survey",
            "us_mn_state_mngeo":"Minnesota Geospatial Information Office",
            "us_mn_state_pca":"Minnesota Pollution Control Agency",
            "edu_umn":"University of Minnesota, Twin Cities"
        }

    def layer_id(self):
        return self._get_resource_name()

    def _get_layer_file(self):
        path_to_lyr = os.path.join(os.path.split(self.filename)[0], "*.lyr")
        lyr_list = glob.glob(path_to_lyr)
        if len(lyr_list) > 0:
            lyr_file = lyr_list[0]
            return lyr_file
        return None

    def _get_subresources(self):
        return self._data_resource_tree.findall(self._data_resource_paths["sub_resources"])

    def _get_subresource_type(self, sub_resource):
        return sub_resource.findtext("subResourceType", None)

    def _get_dataset_url_for_publisher(self):
        if self._get_resource_publisher_id() in ["us_mn_co_dakota", "us_mn_state_metc", "us_mn_state_metrogis"]:
            return self._get_resource_name()
        else:
            return self._get_resource_basename()

    def _build_geocommons_url(self):
        return self._geospatial_commons_root_url + self._get_dataset_url_for_publisher().replace("_","-")

    def _build_download_url(self):
        name = self._get_resource_basename()
        pub = self._get_resource_publisher_id()
        return self._gdrs_root_url + pub + "/" + name + "/"

    def _get_resource_basename(self):
        return self._data_resource_tree.findtext("baseName", None)

    def _get_resource_publisher_id(self):
        return self._data_resource_tree.findtext("publisherID", None)

    def _get_resource_name(self):
        name = self._get_resource_basename()
        pub = self._get_resource_publisher_id()
        if name and pub:
            return pub + "_" + name
        return None

    def _get_resource_xml(self):
        path_to_data_resource_xml = os.path.join(os.path.split(self.filename)[0], "dataResource.xml")
        if os.path.exists(path_to_data_resource_xml):
            self._data_resource_tree = etree.parse(path_to_data_resource_xml)

    def _get_topic_categories(self):
        tc = self._data_resource_tree.findall(self._data_resource_paths["topic_categories"])
        if len(tc) > 1:
            return '"' + ", ".join([i.text for i in tc]) + '"'
        else:
            return tc[0].text

    def name(self):
        return self._get_resource_name()

    def _check_metadata_standard(self):
        root_tag = self.root.tag
        if root_tag == "metadata":
            if "Minnesota" in self.root.find("metainfo/metstdn").text:
                return "mgmg"
            elif "FGDC" in self.root.find("metainfo/metstdn").text:
                return "fgdc"
        elif root_tag.find("MD_Metadata") != -1 or root_tag.find("MI_Metadata") != -1:
            return "iso"

    def data_type(self):
        metadata_standard = self._check_metadata_standard()
        if metadata_standard == "mgmg":
            return parse_data_type_MGMG(self.root)
        elif metadata_standard == "fgdc":
            return parse_data_type_FGDC(self.root)

    def theme_keywords(self):
        return self._get_topic_categories()

    def _get_publisher_name(self, publisher_id):
        return self._gdrs_publisher_codes[publisher_id]

    def publisher(self):
        pub_id = self._get_resource_publisher_id()
        pub = self._get_publisher_name(pub_id)
        return pub

    def _get_subresource_urls(self, resource):
        return resource.findall("subResourceAccess/subResourceURL")

    def _build_download_url(self):
        name = self._get_resource_basename()
        pub = self._get_resource_publisher_id()
        return self._gdrs_root_url + pub + "/" + name + "/"

    def location(self):
        loc = {}
        resources = self._get_subresources()
        for resource in resources:
            external_count = 0
            resource_type = self._get_subresource_type(resource)

            if resource_type:

                if resource_type == "shp" or resource_type == "fgdb":
                    url = self._build_download_url() + "shp_" + self._get_resource_basename() + ".zip"
                    loc["download"] = url

                elif resource_type == "external":
                    url_elements = self._get_subresource_urls(resource)
                    desc = resource.findtext("subResourceName", None)
                    if desc and "download" in desc.lower():
                        loc["externalDownload"] = url_elements[0].text

                elif resource_type == "ags_mapserver":
                    url = self._get_subresource_urls(resource)[0].text
                    self.log.write(self.file_name, url)
                    lyr_file = self._get_layer_file()

                    if lyr_file:
                        self.log.write(self.file_name, "I have a layer file!")
                        import arcpy
                        lyr = arcpy.mapping.Layer(lyr_file)

                        if lyr.isGroupLayer:
                            some_visible = False

                            for index, ly in enumerate(arcpy.mapping.ListLayers(lyr)):

                                if ly.visible:
                                    some_visible = True
                                    ind = index -1

                                    if ind >= 0:
                                        lyr_number = str(ind)

                                        #map service
                                        if url.find("MapServer") is not -1:
                                            loc["ArcGISRest"] = url
                                            loc["layerId"] = lyr_number
                                        #feature service
                                        elif url.find("FeatureServer") is not -1:
                                            if url.endswith("/"):
                                                url = url + lyr_number
                                            else:
                                                url = url + "/" + lyr_number
                                            loc["esrifeatureservice"] = url + "/"

                            if not some_visible:
                                loc["externalDownload"] = self._build_geocommons_url()

                        elif lyr.isServiceLayer:
                            if lyr.serviceProperties["URL"].find("MapServer") is not -1:
                                loc["ArcGISRest"] = lyr.serviceProperties["URL"]

                    else:
                        #if there's no layer file, we'll just check if it's a MapServer
                        if url.find("MapServer") is not -1:
                            loc["ArcGISRest"] = url

        if len(loc.items()) == 0:
            #if all else fails, default to pointing to the geospatial commons address
            loc["externalDownload"] = self._build_geocommons_url()

        self.log.write(self.file_name, json.dumps(loc))
        return json.dumps(loc)

# .___  ___.      ___      .______        ______
# |   \/   |     /   \     |   _  \      /      |
# |  \  /  |    /  ^  \    |  |_)  |    |  ,----'
# |  |\/|  |   /  /_\  \   |      /     |  |
# |  |  |  |  /  _____  \  |  |\  \----.|  `----.
# |__|  |__| /__/     \__\ | _| `._____| \______|

# from https://github.com/gravesm/marcingest
class MARCXMLDocument(MetadataDocument):
    def __init__(self, root, file_name, log, indirect_links):
        import re

        super(MARCXMLDocument, self).__init__(root, file_name, log, indirect_links)
        MARC = "http://www.loc.gov/MARC21/slim"
        MARCNS = "{{{0}}}".format(MARC)
        NSMAP = {
            "marc": MARC,
        }

        _XPATHS = {
            "001": "/collection/record/controlfield[@tag='001']",
            "008": "/collection/record/controlfield[@tag='008']/text()",
            "034_d": "/collection/record/datafield[@tag='034']/subfield[@code='d']/text()",
            "034_e": "/collection/record/datafield[@tag='034']/subfield[@code='e']/text()",
            "034_f": "/collection/record/datafield[@tag='034']/subfield[@code='f']/text()",
            "034_g": "/collection/record/datafield[@tag='034']/subfield[@code='g']/text()",
            "245": "/collection/record/datafield[@tag='245']/subfield[@code='a']/text()",
            "260_b": "/collection/record/datafield[@tag='260']/subfield[@code='b']",
            "500_a": "/collection/record/datafield[@tag='500']/subfield[@code='a']/text()",
            "650_a": "/collection/record/datafield[@tag='650']/subfield[@code='a']",
            "650_z": "/collection/record/datafield[@tag='650']/subfield[@code='z']",
            "876_k": "/collection/record/datafield[@tag='876']/subfield[@code='k']",
        }

        self.XPATHS = dict((k, etree.XPath(v)) for k, v in _XPATHS.items())
        self._COORD_REGEX = re.compile("^([NSEW+-])?(\d{3}(\.\d*)?)(\d{2}(\.\d*)?)?(\d{2}(\.\d*)?)?",
                                       re.IGNORECASE)

    def datatype(self):
        xpath = self.XPATHS['876_k']
        mapping = {
            "MAP": "Paper Map",
            "CDROM": "CD-ROM",
            "DVDROM": "DVD-ROM",
        }
        for datatype in xpath(self.root):
            if datatype.text in ("MAP", "CDROM", "DVDROM"):
                return mapping[datatype.text]
        return "Unknown"

    def theme_keywords(self):
        return " ".join(self._keywords(self.XPATHS['650_a']))

    def place_keywords(self):
        return " ".join(self._keywords(self.XPATHS['650_z']))

    def publisher(self):
        xpath = self.XPATHS['260_b']
        publisher = xpath(self.root)
        if publisher:
            return publisher[0].text.rstrip(",")

    def name(self):
        xpath = self.XPATHS['001']
        return xpath(self.root)[0].text

    def layer_display_name(self):
        xpath = self.XPATHS['245']
        return " ".join(xpath(self.root))

    def content_date(self):
        xpath = self.XPATHS['008']

        date = xpath(self.root)[0][7:11]

        try:
            date = datetime(int(date), 1, 1)
            return date.isoformat() + "Z"
        except ValueError:
            pass

    def abstract(self):
        xpath = self.XPATHS['500_a']
        return " ".join(xpath(self.root))

    def min_x(self):
        xpath = self.XPATHS['034_d']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def min_y(self):
        xpath = self.XPATHS['034_g']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def max_x(self):
        xpath = self.XPATHS['034_e']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def max_y(self):
        xpath = self.XPATHS['034_f']
        coord = xpath(self.root)
        if coord:
            return unicode(self._convert_coord(coord[0]))

    def center_x(self):
        west = float(self.min_x())
        east = float(self.max_x())
        if west is not None and east is not None:
            return unicode(west + abs(east - west) / 2)

    def center_y(self):
        south = float(self.min_y())
        north = float(self.max_y())
        if south is not None and north is not None:
            return unicode(south + abs(north - south) / 2)

    def half_height(self):
        north = float(self.max_y())
        south = float(self.min_y())
        if north is not None and south is not None:
            return unicode(abs(north - south) / 2)

    def half_width(self):
        east = float(self.max_x())
        west = float(self.min_x())
        if east is not None and west is not None:
            return unicode(abs(east - west) / 2)

    def _convert_coord(self, coordinate):
        parts = self._COORD_REGEX.search(coordinate)
        if parts is None:
            return
        decimal = float(parts.group(2)) + float(parts.group(4) or 0) / 60 + float(parts.group(6) or 0) / 3600
        if parts.group(1) and parts.group(1) in "WSws-":
            decimal = -decimal
        return decimal

    def _keywords(self, xpath):
        keywords = set()
        for keyword in xpath(self.root):
            keywords.add(keyword.text.rstrip(":;,. "))
        return list(keywords)
