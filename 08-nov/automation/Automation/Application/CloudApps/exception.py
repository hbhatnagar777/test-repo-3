# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for handling all the exceptions for the Cloud Apps Automation package.

EXCEPTION_DICT:
    A python dictionary for holding all the exception messages for a specific event or class.

    Any exceptions to be raised from the Automation in a module should be added to this dictionary.

    where,

        -   the key is the module name or the class name where the exception is raised

        -   the value is a dictionary:

            -   key is a unique ID to identify the exception message

            -   value is the exception message

|

CVCloudException:
    Class inheriting the "Exception" Base class for raising
    a specific exception for the Cloud Apps Automation package.

    The user should create an instance of the CVCloudException class:

        **CVCloudException(exception_module, exception_id, exception_message)**

        where,

            -   exception_module:   the module in which the exception is being raised

                -   key in the EXCEPTION_DICT

            -   exception_id:       unique ID which identifies the message for the Exception

            -   exception_message:  additional message to the exception

                -   only applicable if the user wishes to provide an additional message to the
                    exception along with the message already present as the value for the
                    exception_module - exception_id pair

    Example:

        **raise CVCloudException('GMail', '102')**

        will raise the exception as:

            CVCloudException: Exception while inserting message into user mailbox

        and, **raise CVCloudException('GMail', '108', 'Please check the value')**

        will raise:

            CVCloudException: Invalid mail insertion type provided.

            Valid values:

            APPEND

            IMPORT

            Please check the value

        where the user given message is appended to the original message joined by new line

"""

# Common dictionary for all exceptions among the Cloud Connector automation

EXCEPTION_DICT = {
    'CloudConnector': {
        '101': 'Empty values in input json file.'
    },
    'CvOperation': {
        '100': 'Error while creating commcell object of CVPySDK',
        '101': 'Job did not complete successfully',
        '102': 'Job was killed',
        '103': 'Job failed',
        '104': 'Backup level converted from intended one.',
        '301': 'Subclient content empty',
        '401': 'CVPYSDK Exception',
        '501': '',
        '601': 'No cloud apps client could be found on Commcell',
        '602': 'Invalid cloud apps instance type returned by get cloudapps API',
        '603': 'client info not returned in response json',
        '604': 'Exception while fetching instance from CS',
        '701': 'Exception while making request to get cloudapps subclient',
        '801': 'User account not found during browse',
        '901': 'Exception while browsing GMail label',
        '902': 'Number of mails are not matching in GMail label',
        '903': 'Label got from browse could not be found in Google Dict',
        '904': 'Empty label dict found. Please check whether label dict json got saved.',
        '905': 'User discovery is not matching with subclient discovery',
        '906': 'Exception during discovery verification',
        '907': 'Error in getting number of failed items',
        '908': 'Error in getting backup items'
    },

    'GMail': {
        '101': 'Subclient content list is empty',
        '102': 'Exception while inserting message into user mailbox',
        '103': 'Exception while creating MIME object',
        '104': 'Message properties are not matching.',
        '105': 'Email id is not present in restore dict',
        '106': 'Message property comparison failed. Please check log for details',
        '107': 'Invalid value provided for Google response format. Valid formats are [raw, full].',
        '108': 'Invalid mail insertion type provided. Valid values are [APPEND, IMPORT].',
        '109': 'Invalid message property dict for delete messages',
        '201': 'Exception while deleting messages from user mailbox',
        '301': 'Number of mails are not matching before backup and after restore.',
        '401': 'Invalid Job list provided',
        '501': ''
    },

    'GDrive': {
        '101': 'Exception while creating files in user GDrive',
        '102': 'Exception while deleting files from GDrive',
        '103': 'Incorrect file operation type. Valid values are delete, download',
        '104': 'Checksum did not match after file restore to GDrive.',
        '105': 'Exception while file operation',
        '106': 'Number of documents are not matching after restore.',
        '107': 'Error while deleting folder on GDrive.',
        '108': 'Error while downloading files on GDrive',
        '109': 'Error while file property comparison',
        '110': 'Error in get_file_properties',
        '111': 'Error in delete_files operation',
        '112': 'Error in download single file operation',
        '113': 'Error during get folder id from Gdrive',
        '114': 'Restore to disk files mismatch',
        '115': 'Google docs file mismatch after restore'
    },

    'GAdmin': {
        '101': 'No user found on Google Directory.',
        '102': 'Exception while fetching user list from Google'
    },

    'GAuth': {
        '101': 'Service account key file name is invalid. Please check file name or path.',
        '102': ('Exception while building google service object.'
                'Service Name or version may be incorrect or credentials can not be refreshed.')
    },

    'OneDriveAuth': {
        '101': 'Exception occurred during backend client authentication. '
               'Please check logs'
    },

    'Wiki': {
        '101': 'Error in wiki API response',
        '102': 'Exception while making HTTP request',
        '103': 'Exception while creating message from wiki',
        '104': ('Invalid content type provided to _set_params method of wiki. '
                'Content type should be "subject" or "body"'),
        '105': 'Exception occurred during creating documents',
        '106': 'Invalid ca_type provided for create_docx. Valid values are "gmail" or "gdrive"'
    },

    'DbOperations': {
        '101': 'Invalid data type passed to save_into_table method',
        '102': 'Invalid table type. Valid values are "labels", "messages"'
    },

    'SQLiteOperations': {
        '101': 'Failed to get the data from local db'
    },

    'OneDrive': {
        '101': 'Error in discovering users on Azure AD',
        '102': 'Method not supported',
        '103': 'Error while creating folder on OneDrive',
        '104': 'Excpetion while get file properties',
        '105': 'Automation folder ID not found on OneDrive. '
               'Please check whether folder exists on OneDrive',
        '106': 'Invalid input response dict',
        '107': '',
        '108': 'Number of restored documents is different than the number of backed up documents.',
        '109': 'File comparison failed after restore',
        '110': 'Maximum retries for Graph API request exceeded. This is Graph API server error',
        '111': 'Restore to disk files mismatch',
        '112': 'Error in Finalize phase'
    }
}


class CVCloudException(Exception):
    """Exception class for raising exception specific to a module."""

    def __init__(self, exception_module, exception_id, exception_message=""):
        """Initialize the SDKException class instance for the exception.

            Args:

                exception_module (str)   --  name of the module where the exception was raised

                exception_id (str)       --  id of the exception specific to the exception_module

                exception_message (str)  --  additional message about the exception

            Returns:

                object - instance of the SDKException class of type Exception

        """
        self.exception_module = str(exception_module)
        self.exception_id = str(exception_id)
        self.exception_message = EXCEPTION_DICT[exception_module][exception_id]

        if exception_message:
            if self.exception_message:
                self.exception_message = '\n'.join(
                    [self.exception_message, exception_message])
            else:
                self.exception_message = exception_message

        Exception.__init__(self, self.exception_message)
