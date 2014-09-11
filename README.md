# OGP-metadata-py
A simple Python (2.6+) script for creating OpenGeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG), MARC XML, or (coming soon) ArcGIS's proprietary metadata format

### Usage
`ogp-mdt.py [-h] input_path output_path metadata_standard`


`-h` - Display usage information  


`input_path` - The base filesystem location of the data to be converted. By default, will recurse through all subfolders. Can be relative (eg. ./datasets/metadata) or absolute (eg. /home/user/workspace/datasets/metadata) path.


`output_path` - The filesystem location where you would like the output written into. If it doesn't exists, it will be created. Can be relative or absolute.  


`metadata_standard` - Either `FGDC`, `MGMG`, `MARC`, or `GUESS` (`ARCGIS` option in the works). The `GUESS` option will try and figure out the metadata standard on its own. Generally speaking, it's best to have files that use a single standard and to pick that.


### Notes
If you want your output XML files to be pretty printed you'll need the [lxml](http://lxml.de/) module installed. See [this] (http://lxml.de/installation.html) page for installation directions. Otherwise the etree module will be used and you'll end up with a seemingly shapeless blob of XML output.
Note line 52 in ogp-mdt.py, which filters out certain names for input files. You may want to change/remove those [!...] options to just take in all XMLs in your input path.
A log file is produced in the output_path. Its name will look like `__ogp-mdt-log-<some numbers>.csv`. It has three columns, the first being the path to the input file.
The second field is the name of the inputted XML file, and the third field is the issue discovered with the field.

=======

