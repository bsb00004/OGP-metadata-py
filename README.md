<h1>OGP-metadata-py</h1>
A simple Python script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG). or ArcGIS's proprietary metadata format

Usable at the command line

<b>ogp-mdt.py [workspace] [metadata_standard] {--et [0-10]}</b>

<b>workspace</b> - The filesystem location of the data to be converted (currently assumes a completely flat organization of the data)  
<b>metadata_standard</b> - Either FGDC or MGMG (ARCGIS option to be added soon)  
<b><i>--et</i></b> - OPTIONAL - Error tolerance. Default value of 5, where 0 means any omitted or invalid OGP field will result in the file being relegated to the error folder and 10 means up to ten problem fields are tolerated (not a great idea, but depending on the state of your data, could be necessary!). 


===============

