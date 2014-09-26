# OGP-metadata-py
A simple Python (2.6+) commandline tool for creating Open GeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG), MARC XML, or (coming soon) ArcGIS's proprietary metadata format.

-----------

### Usage
    ogp-mdt.py [-h] input_path output_path metadata_standard [-i] [-l]


`-h` - Display usage information  


`input_path` - The base filesystem location of the data to be converted. By default, will recurse through all subfolders. Can be relative (eg. ./datasets/metadata) or absolute (eg. /home/user/workspace/datasets/metadata) path.


`output_path` - The filesystem location where you would like the output written into. If it doesn't exists, it will be created. Can be relative or absolute. If you want to use the same path as the input, set this to `same`.  


`metadata_standard` - Either `FGDC`, `MGMG`, `MARC`, or `GUESS` (`ARCGIS` option in the works). The `GUESS` option will try and figure out the metadata standard on its own. Generally speaking, it's best to have files that use a single standard and to pick that.


`-i` - Sets the location field to indicate indirect links. Added since by default Open Geoportal expects either a ZIP file or some other similar bit stream, and we needed to point at a PURL in our institutional repository. Relies on some custom code in the Minnesota OGP instance to do anything.


`-l` - Log only output. This option if present will suppress the writing of the output XML files, but will process them and create the log just the same. This can be useful when "debugging" inputted metadata.

-------

### Examples


    ogp-mdt.py ~/some/metadata ~/output_folder FGDC
Takes a folder containing FGDC metadata (`~/some/metadata`), processes all the files, and outputs OGP formatted XMLs into `~/output_folder`.

-------

    ogp-mdt.py C:\metadata\ same GUESS -l
Takes a folder of XML using indeterminate/mixed metadata standards and outputs just the log file documenting any errors with the process into the same folder (`C:\metadata\`).

-------

	ogp-mdt.py -h
Get the usage information.


-------

### Notes

- If you want your output XML files to be pretty printed you'll need the [lxml](http://lxml.de/) module installed. See [this](http://lxml.de/installation.html) page for installation directions. Otherwise the standard library version of etree module will be used.

- A log file is produced in the output_path. Its name will look like `__ogp-mdt-log-<some numbers>.csv`. It has three columns, the first being the path to the input file. The second field is the name of the inputted XML file, and the third field is the issue discovered with the field. If you append `-l` at the end of the command you'll just get this log file. 


