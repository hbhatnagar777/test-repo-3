# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper functions for integrating both salesforce and commvault operations for Salesforce iDA

SalesforceHelper is the only class defined in this file

SalesforceHelper: Helper class to integrate salesforce and commvault operations. This class has 4 super classes:

    SalesforceBase: This class contains methods to handle config and testcase inputs

    CVConnector: This class contains methods to manage Salesforce organizations in a CommCell

    SalesforceConnector: This class contains methods to manage Salesforce API operations

    SyncDbConnector: This class contains methods to manage sync database operations

SalesforceHelper:
    __init__()                          --  initializes salesforce helper object
"""
from time import sleep
from .cv_connector import CvConnector
from .salesforce_connector import SalesforceConnector
from .sync_db_connector import SyncDbConnector


class SalesforceHelper(CvConnector, SalesforceConnector, SyncDbConnector):
    """Class for integrating salesforce and commvault operations"""

    def __init__(self, tcinputs=None, commcell=None):
        """
        Constructor for the class. Pass commcell object to use CvConnector object. If tcinputs is not passed, then
        inputs will be read from config file. The commcell object is required if any commvault API operations need to be
        performed, else it is optional. Check CVConnector class for what methods require this input.

        Args:
            commcell (cvpysdk.commcell.Commcell): commcell object
            tcinputs (dict): testcase inputs

        Returns:
            None:
        """
        super().__init__(tcinputs, commcell)
        sleep(60)
