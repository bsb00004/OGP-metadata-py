# OGP-metadata-py
A simple Python (2.6+) script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG), MARC XML, or (coming soon) ArcGIS's proprietary metadata format

### Usage
`ogp-mdt.py [-h] [workspace] [output_path] [metadata_standard] [suffix]`  


`-h` - Display usage information  


`workspace` - The base filesystem location of the data to be converted. By default, will recurse through all subfolders. Can be relative (eg. ./datasets/metadata) or absolute (eg. /home/user/workspace/datasets/metadata) path.


`output_path` - The filesystem location where you would like the output written into. If it doesn't exists, it will be created. Can be relative or absolute.  


`metadata_standard` - Either `FGDC`, `MGMG`, or `MARC` (`ARCGIS` option in the works)   


`suffix` - 

### Notes
If you want your output XML files to be pretty printed you'll need the [lxml](http://lxml.de/) module installed. See [this] (http://lxml.de/installation.html) page for installation directions. Otherwise the etree module will be used and you'll end up with a seemingly shapeless blob of XML output.

=======

