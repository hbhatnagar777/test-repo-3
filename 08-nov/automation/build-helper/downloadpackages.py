# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Â©2017 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Setup file for the CVAutomationMask Python package."""

import os
import re
import ssl
import sys
import socket
import subprocess
import datetime
import pip

class DownloadPackages(object):
    """
    download .whl files specified in all_requirements.txt file
    
    """
    def __init__(self, pip_path,source_file, destination, log=None):
        """
        all requirement.txt as paramter
        
        """
        self.source_file = source_file
        self.pip_path = pip_path
        self.destination = destination
        self.log = log
       
    def generate_commnad(self):
        """
        
        """
        return r"pip3.8" + " download -r "+ self.source_file +" --dest " + self.destination+ " --no-deps --platform win_amd64" 
        
    def validate(self):
        """
        
        """
        count = 0
        if os.path.exists(self.source_file):
            with open(self.source_file, r'r') as fp:
                count = fp.readlines()
            
            file_count = next(os.walk(self.destination))[2]
            if len(file_count) >=len(count):
                return True
            else:
                raise Exception("raised exception as the download packages [%s] count mismatch [%s]"%(file_count, count))
            
    def execute_command(self):
        """ Executes command on the machine
    
        Args:
             command    (str)   -- Command to be executed on the machine
    
        """
        try:            
            #os.chdir(r"/")
            #retcode = os.system(self.generate_commnad())
            process = subprocess.Popen(
                self.generate_commnad(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.pip_path,
                shell=True
            )
    
            output, error = process.communicate()
    
            if output:
                #print("Command output: {%s}"%output.decode())
                self.log.info("Command output: {%s}"%output.decode())
    
            if error:
                if str(error).find('WARNING: You are using pip version') >=0:
                    pass
                else:
                    raise Exception("Error: {%s}"%error.decode())
                
            self.validate()
    
        except Exception as exp:
            self.log.info("Exception occurred: {%s}"%exp)
            raise Exception("Exception occurred in download pacakges: {%s}"%exp)
            #print("Exception occurred: {%s}"%exp)

#dp = DownloadPackages(r"/usr/local/bin", r"/root/Desktop/Proj1/Source/all_requirements.txt", r"/root/Desktop/dist/wheelfiles")
#dp.execute_command()




