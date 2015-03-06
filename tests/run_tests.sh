#! /bin/sh
echo "------FGDC TESTS------"
echo ""
python ../ogp-mdt.py ./fixtures/fgdc ../converted fgdc
echo ""
echo "------MGMG TESTS------"
python ../ogp-mdt.py ./fixtures/mgmg ../converted mgmg
echo ""
echo "------ISO TESTS-------"
python ../ogp-mdt.py ./fixtures/iso ../converted iso
echo ""
echo "------SOLR TESTS------"
python test_solr.py
