import os.path
import csv
import time
import json

class Logger(object):
    """
    Output log creation. Defaults to CSV, but can write as JSON as well
    """
    def __init__(self, output_location, output_format=None):
      
        if output_format is None:
            self.output_format = "csv"
        else:
            self.output_format = output_format

        self.output_location = output_location
        self._create_log()

    def _create_log():
        if self.output_format = "csv":
            self._create_csv()
        elif self.output_format = "json":
            self._create_json()
            

    def _create_csv(self):
        self.filename = '__ogp-mdt-log-' + str(time.time()).replace('.', '') + '.csv'
        self.csvfile = open(os.path.join(self.output_location, self.filename), mode='a')
        self.log = csv.writer(self.csvfile)

    def _create_json(self):
        self.log = {}

    def write(self, item, message):
        if self.output_format = "csv":
            self._write_csv(item,message)
        elif self.output_format = "json":
            self._create_json()


    def _write_csv(self, item, message):
        s = os.path.split(item)
        self.log.writerow([s[0], s[1], message])

    def _write_json(self, item, message):

    def close(self):
        self.csvfile.close()
