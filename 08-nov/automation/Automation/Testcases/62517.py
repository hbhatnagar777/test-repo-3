# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()         --  initialize TestCase class
    run_db_query()     --  runs database query
    setup()            --  setup function of this test case
    run()              --  run function of this test case.
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.client_id = None
        self.db_helper = None
        self.CCM_helper = None
        self.name = "CLIENTS MISSING FROM NAME MANAGEMENT WIZARD POST CCM"
        self.tcinputs = {
            "ClientName": None,
            "sqlInstanceName": None,
            "SqlUserName": None,
            "SqlPassword": None,
            "SourceCommcellHostname": None,
            "SourceCommcellUsername": None,
            "SourceCommcellPassword": None
        }

    def run_db_query(self, special_client_flag):
        """Function to run Database query"""
        query = "update APP_Client set specialClientFlags = {} where id = {}".format(special_client_flag,
                                                                                     self.client_id)
        self.db_helper.execute(query)

    def setup(self):
        """Setup function for this test case"""
        self.db_helper = MSSQL(self.tcinputs["sqlInstanceName"],
                               self.tcinputs["SqlUserName"],
                               self.tcinputs["SqlPassword"],
                               "CommServ")
        self.client_id = self.commcell.clients.get(self.tcinputs["ClientName"]).client_id

    def run(self):
        """Run function of this test case"""
        try:
            self.commcell.register_commcell(
                self.tcinputs["SourceCommcellHostname"],
                True,
                self.tcinputs["SourceCommcellUsername"],
                self.tcinputs["SourceCommcellPassword"],
            )
            self.log.info("Setting wrong value for specialClientsFlag in APP_Client Table")
            self.run_db_query(0)
            flag = True
            clients_list = self.commcell.name_change.get_clients_for_name_change_post_ccm()
            for client in clients_list:
                if self.tcinputs["ClientName"] == client.get("name", ""):
                    flag = False
            if not flag:
                self.log.info(
                    "{} client is not available for name change operation".format(self.tcinputs["ClientName"]))
            else:
                raise Exception

            self.log.info("Setting the correct value for specialClientsFlag in APP_Client Table")
            self.run_db_query(32)
            clients_list = self.commcell.name_change.get_clients_for_name_change_post_ccm()
            flag = False
            for client in clients_list:
                if self.tcinputs["ClientName"] == client.get("name", ""):
                    self.log.info(
                        "{} client is available for name change operation".format(self.tcinputs["ClientName"]))
                    flag = True
            if not flag:
                self.log.error(
                    "{} client is not available for name change operation".format(self.tcinputs["ClientName"]))
                raise Exception
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
