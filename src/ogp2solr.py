# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from lib import pysolr
import json

class SolrOGP(object):

    def __init__(self, url="http://54.235.211.28:8080/solr/collection1/"):
        # defaults to UMN OGP
        self.solr_url = url
        self.solr = self._connect_to_solr()

    def escape_query(self, raw_query):
        """
        Escape single quotes in value. May or may not be worth a damn at the moment.
        """
        return raw_query.replace("'","\'")

    def run_query(self, query, **kwargs):
        """
        Query the connected Solr index
        """
        q = self.escape_query(query)
        return self.solr.search(q, **kwargs)

    def json_to_dict(self, json_doc):
        j = json.load(open(json_doc, "r"))
        return j

    def add_json_to_solr(self,json_doc):
        record_dict = self.json_to_dict(json_doc)
        self.add_dict_to_solr(record_dict)

    def add_dict_to_solr(self,record_dict):
        self.solr.add([record_dict])

    def add_to_solr(self, tree):
        """
        Adds a document to Solr. Accepts an ElementTree as argument.
        """
        d = self.tree_to_dict(tree)
        self.solr.add([d])

    def add_to_solr_bulk(self, list_of_trees):
        """
        Adds a bunch of records. Accepts a list of ElementTrees as argument
        """
        list_of_dicts = self.list_of_trees_to_dicts(list_of_trees)

        print "Adding/updating %s documents in Solr index" % (len(list_of_trees))

        self.solr.add(list_of_dicts)

    def _build_delete_query(self, list_of_layer_ids):
        return "LayerId:(" + " ".join(list_of_layer_ids) + ")"

    def delete_query(self,query, no_confirm=False):
        if not no_confirm:
            s = self.solr.search(self.escape_query(query), **{"rows":"0"})
            are_you_sure = raw_input("Are you sure you want to delete {num_recs} records from Solr? Y/N: ".format(num_recs=s.hits))
            if are_you_sure.lower() == "y":
                self.solr.delete(q=self.escape_query(query))
            else:
                print "Abandon ship!"
        else:
            self.solr.delete(q=self.escape_query(query))



    def delete_from_solr(self, list_of_layer_ids):
        """
        Delete a list of LayerId values from Solr.
        """

        query = self._build_delete_query(list_of_layer_ids)
        self.solr.delete(q=query)

    def _connect_to_solr(self):
        """
        Connects to Solr using the url provided when object was instantiated
        """

        return pysolr.Solr(self.solr_url)

    def list_of_trees_to_dicts(self,trees):
        list_of_dicts = []

        for tree in trees:
            d = self.tree_to_dict(tree)
            list_of_dicts.append(d)

        return list_of_dicts

    def tree_to_dict(self,tree):
        """
        Takes an ElementTree and returns a flat dictionary containing the OGP fields,
        suitable for ingesting to Solr via pysolr.
        """

        fields = tree.findall("doc/field")

        d = dict()

        for f in fields:
            d[f.attrib['name']] = f.text

        d['WorkspaceName'] = 'edu.umn'
        return d
