# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------

"""The core logic for running pylint goes in this module"""
import os
from collections import defaultdict
from os import remove
from pylint.lint import Run
from pylint.reporters.text import TextReporter




class PylintOutput:
    """Class for storing an instance of pylint output"""

    def __init__(self):
        self.output = list()
        self.error_code = defaultdict(list)
        self._message = dict()
        self.name = None
        self.path = None
        self.score = None
        self.label = None

    def __check_for_error_codes(self, line):
        """Makes note of index numbers of the list which are Errors"""
        self.error_code[line[0]].append(len(self.output) - 1)

    def write(self, line):
        """Writes the pylint output to this method"""
        self.output.append(line)
        self.__check_for_error_codes(line)

    def get_error_lines(self):
        """Returns the tuples of lines with Error Code 'E' """
        return tuple(map(lambda index: self.output[index], self.error_code['E']))

    def get_fatal_lines(self):
        """Returns the tuples of lines with Error Code 'F' """
        return tuple(map(lambda index: self.output[index], self.error_code['F']))

    def write_to_file(self):
        """Writes the pylint output to the file"""
        if os.path.exists(self.path):  # Although 'w' mode truncates and writes afresh, //devshare path holds stub
            remove(self.path)  # of the file in some cases which python thinks as a file and attempts file
        with open(self.path, 'w') as file:  # operations on it.
            file.write("".join(self.output))

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message
        del self._message['statement']


    def run(self, directory, file):
        """Runs pylint for the given file and stores the output in the given directory and returns pylint object
    
        Args:
            queue         (Queue):    Queue to contain Logs
    
            directory       (str):  Path of the pylint output
    
            file            (str):  File on which pylint has to be run
    
        Returns:
            PylintOutput (object)
    
        """
        pylint_output = PylintOutput()
        #queue.put(f"Executing pylint on file: {file}")
        rc_file = os.path.join(os.path.dirname(__file__), "pylint.xml")
        result = Run([file, f"--rcfile={rc_file}"], reporter=TextReporter(pylint_output), do_exit=False)
    
        pylint_output.name = list(result.linter.stats['by_module'].keys()).pop()
        pylint_output.message = list(result.linter.stats['by_module'].values()).pop()
        pylint_output.score = result.linter.stats.get('global_note', 0)
        pylint_output.path = os.path.join(directory, f"{pylint_output.name}.txt")
        if "cvpysdk/" in file or "Automation/" in file:
            pylint_output.label = file.rsplit("cvpysdk/", 1)[1] if "cvpysdk" in file else file.split("Automation/", 1)[1]
        else:
            pylint_output.label = file
            
    
        #queue.put(f"Writing file: '{pylint_output.name}' in the location {directory}")
        pylint_output.write_to_file()
        return pylint_output


#po = PylintOutput()
#po.path=r"/root/Desktop/pylint_out/pylintout.txt"
#po.run(r"/root/Desktop/pylint_out", r"/root/Desktop//Automation/CVAutomation.py")
