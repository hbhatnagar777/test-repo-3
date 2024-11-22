# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module is use to handle all exception related to AD agent

Class:

    ADException
    This is an exception to generated more details when AD related exception was raised

        exception_module         (str)    the detail module can be found in EXCEPTION_MODULES

        exception_id            (int)    exception code

        exception_message        (str)    additional string or message from related module

Functions:
    errorlogging    : generate easier reading log based on exception


"""
__all__ = []

import json

class ADException(Exception):
    """ AD relaetd exception"""

    def __init__(self, exception_module, exception_id, exception_message=None):
        """initial AD exceptions"""
        self.module_name = exception_module
        self.error_id = str(exception_id)
        self.error_message = exception_message
        self.exceptions = self._load_exception()
        self.report = self.error_logging()

    def __repr__(self):
        """return error in string format """
        return self.error_logging()

    def _load_exception(self):
        """ load exception detials from json file"""
        with open("Application/Ad/exceptions.json", "r") as filehandle:
            except_modules = json.load(filehandle)
        if self.module_name in except_modules['modules']:
            exceptions_ = except_modules[self.module_name]['exceptions']
        return exceptions_

    def error_logging(self):
        """ create easy read error in log file and email notificaiton"""
        string = "\n"
        string += " "*40+f"Module is {self.module_name}, error code is {self.error_id}\n"
        string += " "*40+f"Error description is : {self.exceptions[self.error_id]}\n"
        string += " "*40+"Additional info:\n"+" "*40 +f"{self.error_message}\n"
        return string
