import pysolr
import pdb

class SolrOGP(object):

	def __init__(self, url=None):

		# defaults to UMN OGP
		if url is None:
			url = "http://ec2-54-87-229-228.compute-1.amazonaws.com:8080/solr/collection1/"

		self.solr_url = url
		self.connectToSolr()

	def escapeQuery(self,raw_query):
		"""
		Escape single quotes in value. May or may not be worth a damn at the moment.
		"""
		return raw_query.replace("'","\'")

	def runQuery(self,query):
		"""
		Query the connected Solr index
		"""
		q = self.escapeQuery(query)
		return self.solr.search(q)

	def addToSolr(self,tree):
		"""
		Adds a document to Solr. Accepts an ElementTree as argument.
		"""
		d = self.treeToDict(tree)
		self.solr.add([d])

	def _buildDeleteQuery(self,list_of_layer_ids):
		return "LayerId:(" + " ".join(list_of_layer_ids) + ")"

	def deleteQuery(self,query):
		self.solr.delete(q=self.escapeQuery(query))

	def deleteFromSolr(self,list_of_layer_ids):
		"""
		Delete a list of LayerId values from Solr.
		"""

		query = self._buildDeleteQuery(list_of_layer_ids)
		self.solr.delete(q=query)

	def connectToSolr(self):
		"""
		Connects to Solr using the url provided when object was instantiated
		"""

		self.solr = pysolr.Solr(self.solr_url)

	def treeToDict(self,tree):
		"""
		Takes an ElementTree and returns a flat dictionary containing the OGP fields,
		suitable for ingesting to Solr via pysolr.
		"""

		fields = tree.findall("doc/field")

		d = dict()

		for f in fields:
			d[f.attrib['name']] = f.text

		return d

