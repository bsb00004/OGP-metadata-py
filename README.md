<h1>OGP-metadata-py</h1>
A simple Python script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG). or ArcGIS's proprietary metadata format

Usable at the command line

<b>ogp-mdt.py <i>[workspace] [metadata_standard] {--et [0-10]}</i></b>

<b>workspace</b> - the filesystem location of the data to be converted (currently assumes a completely flat organization of the data)
<b>metadata_standard</b> - either FGDC or MGMG (ARCGIS option to be added soon)
<b><i>--et</i></b> - error tolerance, where 0 means any omitted or invalid OGP field will result in the file being relegated to the error folder and 10 means up to ten problem fields are tolerated (not a great idea, but depending on your data, a definite possibility)


===============

