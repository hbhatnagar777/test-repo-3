# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper

# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG1'

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG1',
                                                   description='Test Group',
                                                   client_scope='Clients in this Commcell')

            # Get a preview of the clients that will be a part of this group
            preview_clients_list = smartclient_helper.preview_clients()

            rule_list = []
            self.log.info("""
                            ====================================================
                            Step1:
                            Creating Automatic Client Group with Client installed
                            ====================================================
                            """)
            self.log.info("Creating Rule for Client equal to Installed")
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')

            rule_list.append(rule1)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            # Get Generated clients list
            created_clients_list = smartclient_helper.get_clients_list(smartclient_helper.group_name)
            # Validation of Preview clients and Created group clients
            smartclient_helper.validate_clients_list(preview_clients_list, created_clients_list)

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            if smartclient_helper is not None:
                smartclient_helper.smart_client_cleanup()
