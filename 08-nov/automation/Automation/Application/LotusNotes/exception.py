# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for handling all the exceptions for the Notes Database Automation package.

__EXCEPTION_DICT__:
    A python dictionary for holding all the exception messages for a specific event or class.

    Any exceptions to be raised from the Automation in a module should be added to this dictionary.

    where,

        -   the key is the module name or the class name where the exception is raised

        -   the value is a dictionary:

            -   key is a unique ID to identify the exception message

            -   value is the exception message


TimeoutException:
    Class inheriting the "Exception" Base class for exceptions
    specific to timeout during browse


BrowseException:
    Class inheriting the "Exception" Base class for exceptions
    specific to browse failures


InvalidJobException:
    Class inheriting the "Exception" Base class for exceptions
    specific to triggering of invalid jobs


LNException:
    Class inheriting the "Exception" Base class for raising
    a specific exception for the Notes database Automation package.

    The user should create an instance of the LNException class:

        **LNException(exception_module, exception_id, exception_message)**

        where,

            -   exception_module:   the module in which the exception is being raised

                -   key in the __EXCEPTION_DICT__

            -   exception_id:       unique ID which identifies the message for the Exception

            -   exception_message:  additional message to the exception

                -   only applicable if the user wishes to provide an additional message to the
                    exception along with the message already present as the value for the
                    exception_module - exception_id pair

"""

# Common dictionary for all exceptions among the Notes Database automation

__EXCEPTION_DICT__ = {
    'TestScenario': {
        '101': 'Not all test scenarios passed'
    },

    'CVOperation': {
        '101': 'Browse failed',
        '102': 'Job not converted to Full',
        '103': 'Incremental backup without changing content should not back up anything',
        '104': 'Consecutive Incremental Job converted to FULL',
        '105': 'Restoring TR logs is not allowed',
        '106': 'New databases not found by the default subclient',
        '107': 'Schedule not set',
        '108': 'Job was not triggered by schedule',
        '109': 'Schedule has not triggered any job'

    },

    'DocProperties': {
        '101': 'Document properties are not the same',
        '102': 'Document properties are the same'
    },

    'DominoOperations': {
        '101': 'Please bring up Domino Server manually',
        '102': 'CVRestAPI not present on this domino server',
        '103': 'CVRestAPI not enabled on this domino server'
    }
}


class TimeoutException(Exception):
    """Exception class for exception specific to timeout during browse

    """
    pass


class BrowseException(Exception):
    """Exception class for exception specific to browse failures

    """
    pass


class InvalidJobException(Exception):
    """Exception class for exception specific to triggering of invalid jobs

    """
    pass


class LNException(Exception):
    """Exception class for raising exception specific to a module."""

    def __init__(self, exception_module, exception_id, exception_message=""):
        """Initialize the LNDBException class instance for the exception.

            Args:

                exception_module (str)   --  name of the module where the exception was raised

                exception_id (str)       --  id of the exception specific to the exception_module

                exception_message (str)  --  additional message about the exception

            Returns:

                object - instance of the SDKException class of type Exception

        """
        self.exception_module = str(exception_module)
        self.exception_id = str(exception_id)
        self.exception_message = __EXCEPTION_DICT__[
            exception_module][exception_id]

        if exception_message:
            if self.exception_message:
                self.exception_message = '\n'.join(
                    [self.exception_message, exception_message])
            else:
                self.exception_message = exception_message

        Exception.__init__(self, self.exception_message)
