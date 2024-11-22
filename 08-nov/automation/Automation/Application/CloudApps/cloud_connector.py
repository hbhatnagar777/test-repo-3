# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for setting input variables and creating objects of all other modules.
    This module is imported in any test case.
    You need to create an object of this module in the test case.

CloudConnector is the only class defined in this module.

CloudConnector: Class for initializing input variables and other module objects.

CloudConnector:
        __init__(testcase_object)   --  Initializes the input variables,
        logging and creates object from other modules

        __repr__()                  --  Representation string for the instance of
        CloudConnector class

Attributes
==========

        **db**  --  Returns the object of DbOperations class

        **cvoperations**    --  Returns the object of CvOperation class

        **auth**    --  Returns the object of GAuth class

        **one_drive_auth**  --  Returns the object of OneDriveAuth class

        **gadmin**  --  Returns the object of GAdmin class

        **gmail**   --  Returns the object of GMail class

        **gdrive**   --  Returns the object of GDrive class

        **one_drive**   --  Returns the object of OneDrive class

        **csdb**        --  Returns the object of CommServ Database Class

"""


from __future__ import unicode_literals

from .google import GAdmin, GMail, GDrive
from .one_drive import OneDrive
from .auth import GAuth, OneDriveAuth
from .operations import CvOperation
from .db import DbOperations, SQLiteOperations
from . import constants


class CloudConnector:
    """Class for initializing input variables and object creation from different modules"""

    def __init__(self, tc_object):
        """Initializes the input variables,logging and creates object from other modules.

                Args:

                    tc_object   --  Instance of testcase class

                Returns:

                    object  --  Instance of CloudConnector class

        """
        self.tc_object = tc_object
        self.log = self.tc_object.log
        self.log.info('logger initialized for cloud apps')
        self.tc_inputs = self.tc_object.tcinputs
        self.app_name = self.__class__.__name__

        self._db = DbOperations(self)
        self._cvoperations = CvOperation(self)
        self._sqlite = SQLiteOperations(self)

        if tc_object.instance.ca_instance_type in ['GMAIL', 'GDRIVE']:
            constants.KEY_FILE_PATH = self.tc_inputs['private_key_file_path']
            constants.CLIENT_EMAIL = self.tc_inputs['application_email_address']
            constants.ADMIN_EMAIL = self.tc_object.instance.google_admin_id
            self._auth = GAuth(self.log)
            self._gadmin = GAdmin(self)
            self._gmail = GMail(self)
            self._gdrive = GDrive(self)

        if tc_object.instance.ca_instance_type == 'ONEDRIVE':
            constants.CLIENT_ID = self.tc_inputs['application_id']
            constants.CLIENT_SECRET = self.tc_inputs['application_key_value']
            constants.TENANT = self.tc_inputs['azure_directory_id']
            self._one_drive_auth = OneDriveAuth(self.log, self.tc_inputs.get('cloudRegion', 1))
            self._one_drive = OneDrive(self)
            self.index_server = self.tc_inputs.get('IndexServer', '')

    def __repr__(self):
        """Representation string for the instance of CloudConnector class."""

        return 'CloudConnector class instance for Commcell'

    @property
    def dbo(self):
        """Returns the object of DbOperations class"""
        return self._db

    @property
    def csdb(self):
        """Returns the object of CommServ DB class"""
        return self.tc_object.csdb

    @property
    def cvoperations(self):
        """Returns the object of CvOperation class"""
        return self._cvoperations

    @property
    def auth(self):
        """Returns the object of GAuth class"""
        return self._auth

    @property
    def one_drive_auth(self):
        """Returns the object of OneDriveAuth class"""
        return self._one_drive_auth

    @property
    def gadmin(self):
        """Returns the object of GAdmin class"""
        return self._gadmin

    @property
    def gmail(self):
        """Returns the object of GMail class"""
        return self._gmail

    @property
    def gdrive(self):
        """Returns the object of GDrive class"""
        return self._gdrive

    @property
    def one_drive(self):
        """Returns the object of OneDrive class"""
        return self._one_drive

    @property
    def sqlite(self):
        """Returns the object of SQLiteOperations class"""
        return self._sqlite
