# OGP-metadata-py
A simple Python (2.6+) commandline tool for creating Open GeoPortal ingestible metadata from data with existing FGDC metadata, Minnesota Geospatial Metadata Guidelines (MGMG), MARC XML, or (coming soon) ArcGIS's proprietary metadata format.

-----------
### Installation Using Pip (recommended)

If you don't have Pip, [get Pip](https://pip.pypa.io/en/latest/installing.html)!

Either clone the repo or [download as a zip](https://github.com/krdyke/OGP-metadata-py/archive/master.zip). Once cloned/downloaded and extracted, run this from the root of the repo:

    pip install -r requirements.txt

N.B Tries to install lxml, so things could get a bit hairy. It definitely works on OS X Mavericks. For Windows users, you'll likely need to install a binary version separately (see [this](https://pypi.python.org/pypi/lxml)).


-----------

### Usage
    ogp-mdt.py [-h] input_path output_path metadata_standard [-i] [-l] [-z]


`-h` - Display usage information  


`input_path` - The base filesystem location of the data to be converted. By default, will recurse through all subfolders. Can be relative (eg. ./datasets/metadata) or absolute (eg. /home/user/workspace/datasets/metadata) path.


`output_path` - The filesystem location where you would like the output written into. If it doesn't exists, it will be created. Can be relative or absolute. If you want to use the same path as the input, set this to `same`.  


`metadata_standard` - Either `FGDC`, `MGMG`, `MARC`, `ISO`, or `GUESS` (`ARCGIS` option in the works). The `GUESS` option will try and figure out the metadata standard on its own. Generally speaking, it's best to have files that use a single standard and to pick that.


`-i` - Sets the location field to indicate external links. Added since by default Open Geoportal expects either a ZIP file or some other similar bit stream, and we needed to point at a PURL in our institutional repository. If set, the `location` field for the resulting Solr documents will set links to `externalDownload` rather than `download`, which triggers different behavior in the Open Geoportal interface.


`-l` - Log only output. This option if present will suppress the writing of the output XML files, but will process them and create the log just the same. This can be useful when "debugging" inputted metadata.

`-z` - output as zip file. By default the script will create the XMLs in the indicated output path. If you want them in a zip file in the same path use this flag.

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

-------

### Running "tests"

Not really tests in any strict sense, but at least a way to check that the different standards (and solr connecting) are working

    ./run_tests.sh




