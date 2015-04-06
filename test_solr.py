
from src import ogp2solr
from lxml import etree

print "testing connecting to Solr"
s = ogp2solr.SolrOGP()
print "ok!!\n"

print "testing parse XML into etree"
tree = etree.parse("tests/sample_output/0_OGP.xml")
print "ok!!\n"

print "test adding to Solr"
s.add_to_solr(tree)
print "ok!!\n"

print "test run_query"
s.run_query('LayerId:n39c884b0139a0cc8ad0n7ffe')
print "ok!!\n"

print "test delete_from_solr"
s.delete_from_solr(['n39c884b0139a0cc8ad0n7ffe'])
print "ok!!\n"