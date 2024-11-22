# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the operations helpful for Threat analysis feature

ThreatAnalysisHelper: Class for performing threat analysis operations

ThreatAnalysisHelper
==============

    Functions:

    is_plan_associated()                 --  Checks if a TA plan is associated to the Index server
"""
from cvpysdk.index_server import IndexServer
from AutomationUtils import logger
import dynamicindex.utils.constants as cs
from Web.Common.exceptions import CVWebAutomationException


class ThreatAnalysisHelper:
    """
     This class contains all the Threat Analysis operations
    """

    def __init__(self,  admin_console=None, commcell=None, csdb=None):
        self.__admin_console = admin_console
        self.log = logger.get_log()
        self.commcell = commcell
        self.csdb = csdb

    def is_plan_associated(self, index_server_name, plan_name):
        """
        Check if a Threat analysis plan is associated
        """
        index_server_obj = IndexServer(self.commcell, index_server_name)
        self.log.info(f"Index server properties {index_server_obj.properties}")
        is_pseudo_client_id = index_server_obj.properties.get("indexServerClientId")
        self.log.info(f"Index server id {is_pseudo_client_id}")
        self.csdb.execute(
            f"SELECT NAME FROM APP_PLAN WHERE NAME = '{plan_name}'")
        if not [plans[0] for plans in self.csdb.fetch_all_rows() if plans[0] != '']:
            self.log.info("No threat scan plan is associated to the index server")
            return False
        else: 
            self.log.info(f"Plan found {self.csdb.fetch_all_rows()[0]}")
            return True



