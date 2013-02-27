"""
create simple logger class to output results both to text file and display
"""
import sys
class Logger():
    def __init__(self,OUTPUT_LOCATION,LOG_NAME):
        self.terminal = sys.stdout
        self.log = open(OUTPUT_LOCATION+LOG_NAME, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  
