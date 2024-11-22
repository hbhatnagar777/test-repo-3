# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Test case to verify if CvAppMgrAccessControlTest works for the given client

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Server import serverconstants
from Server.cvappmgr_helper import CvAppMgrAccessControlTest


class TestCase(CVTestCase):
    """Class for executing adding entities from global search test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Test case to verify if CvAppMgrAccessControlTest works for the given client"
        self.utils = TestCaseUtils(self)
        self.all_clients = None
        self.cvappmgr_access_control_test = None
        self.client_obj = None
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""

        self.all_clients = self.commcell.clients

    def run(self):
        """Main function for test case execution"""

        all_clients = self.tcinputs['clients'].split(',')
        is_infra_mapping = self.tcinputs['is_infra_client'].split(',')
        local_path = self.tcinputs['local_path']
        query_dict = serverconstants.QUERY_DICT

        for client in all_clients:
            self.client_obj = self.all_clients.get(client)
            is_infra_index = all_clients.index(client)
            self.cvappmgr_access_control_test = CvAppMgrAccessControlTest(self.client_obj,
                                                                          self.commcell,
                                                                          self.csdb)
            try:

                self.cvappmgr_access_control_test.copy_exe_to_remote_machine(local_path)
                self.cvappmgr_access_control_test.execute_all_queries(query_dict)
                self.cvappmgr_access_control_test.verify_access_for_all_rows(
                    infrastructure_client=eval(is_infra_mapping[is_infra_index]))

            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

            finally:
                self.cvappmgr_access_control_test.remove_exe_from_remote_machine()
