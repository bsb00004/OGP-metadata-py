import pysolr

class SolrOGP(object):

	def __init__(self, url=None):

		# defaults to UMN OGP
		if url is None:
			url = "http://ec2-54-87-229-228.compute-1.amazonaws.com:8080/solr/collection1/"

		self.solr_url = url
		self.connectToSolr()

	def connectToSolr(self):
		self.solr = pysolr.Solr(self.solr_url)

	def treeToDict(tree):
		"""
		Takes an ElementTree and returns a flat dictionary containing the OGP fields,
		suitable for ingesting to Solr via pysolr.
		"""

		if "ElementTree" not in tree.__class__:
			print "invalid tree inputted to treeToDict"
			return ""

		fields = tree.findall("doc/field")

		d = dict()

		for f in fields:
			d[f.attrib['name']] = f.text

