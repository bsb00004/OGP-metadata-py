"""
create simple logger class to output results both to text file and display
"""
import os.path
import csv
import time


class Logger(object):

    def __init__(self, output_location="/var/www/ogp-md/tmp/logs"):
        self.filename = '__ogp-mdt-log-' + str(time.time()).replace('.', '') + '.csv'
        self.csvfile = open(os.path.join(output_location, self.filename), mode='a')
        self.log = csv.writer(self.csvfile)

    def write(self, filename, message):
        s = os.path.split(filename)
        self.log.writerow([s[0], s[1], message])

    def close(self):
        self.csvfile.close()
