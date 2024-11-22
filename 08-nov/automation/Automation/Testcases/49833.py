# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):
    """Class for executing database related operations through Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL related query operations on Commserver and external databases"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True
        self.tcinputs = {
            'RemoteSQLServer': None,
            'RemoteSQLServerInstance': None,
            'RemoteSQLDBUser': None,
            'RemoteSQLDBPassword': None,
            }

        # Inherited class attributes
        self._workflow = None
        self._test_req = ("""Test case input requirements not met.
                     Input 1. Remote SQL server instance name
                     Input 2. Remote SQL server DB name
                     Input 3. Remote SQL DB user name
                     Input 4. Remote SQL DB user password""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_db_operations")

        if not all(self.tcinputs.get(key) for key in ('RemoteSQLServer',
                                                      'RemoteSQLServerInstance',
                                                      'RemoteSQLDBUser',
                                                      'RemoteSQLDBPassword')):
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:

            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_DB_SERVER': self.tcinputs['RemoteSQLServer'],
                    'INP_DB_SERVER_INSTANCE': self.tcinputs['RemoteSQLServerInstance'],
                    'INP_DB_USER': self.tcinputs['RemoteSQLDBUser'],
                    'INP_DB_PASSWORD': self.tcinputs['RemoteSQLDBPassword']
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
