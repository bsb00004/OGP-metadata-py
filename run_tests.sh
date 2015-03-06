#! /bin/sh
echo "------FGDC TESTS------"
echo ""
python ./ogp-mdt.py ./tests/fixtures/fgdc ./converted fgdc
echo ""
echo "------MGMG TESTS------"
python ./ogp-mdt.py ./tests/fixtures/mgmg ./converted mgmg
echo ""
echo "------ISO TESTS-------"
python ./ogp-mdt.py ./tests/fixtures/iso ./converted iso
echo ""
echo "------SOLR TESTS------"
python ./tests/test_solr.py
