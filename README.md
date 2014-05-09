<h1>OGP-metadata-py</h1>
A simple Python (2.6+) script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG). or ArcGIS's proprietary metadata format

<h3>Usage</h3>
<b>ogp-mdt.py [workspace] [metadata_standard] {--et}</b>

<b>workspace</b> - The filesystem location of the data to be converted (currently assumes a completely flat organization of the data)  
<b>metadata_standard</b> - Either FGDC or MGMG (ARCGIS option in the works)  
<b><i>--et</i></b> - OPTIONAL - Error tolerance. Default value of 5000 (!), where 0 means any omitted or invalid OGP field will result in the file being relegated to the error folder and 10 means up to ten problem fields are tolerated (not a great idea, but depending on the state of your data, could be necessary, hence the default of 5000!). 


<h3>Notes</h3> 
If you want your output XML files to be pretty printed you'll need the [lxml](http://lxml.de/) module installed. See [this] (http://lxml.de/installation.html) page for installation directions. Otherwise the etree module will be used and you'll end up with a seemingly shapeless blob of XML output.

=======

