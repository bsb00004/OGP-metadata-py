from src import ogp2solr
from lxml import etree

print "testing connecting to Solr"
s = ogp2solr.SolrOGP()
print "ok!!\n"

print "testing parse XML into etree"

tree = etree.parse("sample_output/0_OGP.xml")
print "ok!!\n"

print "test adding to Solr"
s.addToSolr(tree)
print "ok!!\n"

print "test runQuery"
s.runQuery('LayerId:n39c884b0139a0cc8ad0n7ffe')
print "ok!!\n"

print "test deleteFromSolr"
s.deleteFromSolr(['n39c884b0139a0cc8ad0n7ffe'])
print "ok!!\n"