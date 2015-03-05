__author__ = 'dykex005'
import md2ogp
import json
import ogp2solr
import pdb
from lxml import etree

manifest = json.load(open("manifest.json"))
datasets = manifest["dsDetails"]
docs = []
solr = ogp2solr.SolrOGP()
for dataset_id in datasets:
    print datasets[dataset_id]["dsBaseName"]
    doc = md2ogp.GDRSDocument(datasets[dataset_id], dataset_id.replace("{","").replace("}",""), None, None)
    ogp_tree = md2ogp.write_ogp_tree(doc)
    docs.append(ogp_tree)

solr.add_to_solr_bulk(docs)
import pip
with open("requirements.txt", "w") as f:
    for dist in pip.get_installed_distributions():
        req = dist.as_requirement()
        f.write(str(req) + "\n")




