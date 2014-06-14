# OGP-metadata-py
A simple Python (2.6+) script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG). or ArcGIS's proprietary metadata format

### Usage
`ogp-mdt.py [-h] [workspace] [output_path] [metadata_standard] {--et}`  
`-h` - Display usage information  
`workspace` - The base filesystem location of the data to be converted. By default, will recurse through all subfolders. Can be relative (eg. ./datasets/metadata) or absolute (eg. /home/user/workspace/datasets/metadata) path  
`output_path` - The filesystem location where you would like the output written into. If it doesn't exists, it will be created  
`metadata_standard` - Either `FGDC` or `MGMG` (`ARCGIS` option in the works)   
`--et` - OPTIONAL - Error tolerance. Default value of 5000 (!), where 0 means any omitted or invalid OGP field will result in the file being relegated to the error folder and 10 means up to ten problem fields are tolerated (not a great idea, but depending on the state of your data, could be necessary, hence the default of 5000!). 


### Notes
If you want your output XML files to be pretty printed you'll need the [lxml](http://lxml.de/) module installed. See [this] (http://lxml.de/installation.html) page for installation directions. Otherwise the etree module will be used and you'll end up with a seemingly shapeless blob of XML output.
I haven't tested on a Windows machine recently, so your mileage may vary.

=======

