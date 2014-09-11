"""
create simple logger class to output results both to text file and display
"""
import os.path,csv,time

class Logger(object):
    def __init__(self,OUTPUT_LOCATION):
        self.filename = '__ogp-mdt-log-' + str(time.time()).replace('.','') + '.csv'
        self.csvfile = open(os.path.join(OUTPUT_LOCATION, self.filename), mode='a')
        self.log = csv.writer(self.csvfile)

    def write(self, filename,message):
        s = os.path.split(filename)
        self.log.writerow([s[0],s[1],message])

    def close(self):
        self.csvfile.close()

