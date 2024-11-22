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
    """Class for executing threading and windows operations through
    Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Utilize fork/join activities and psExec and ExecuteCommand \
                        activities to create directories in parallel"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True
        self.tcinputs = {
            'Client': None,
            'ClientSystemPassword': None,
            'ClientSystemUsername': None,
            }

        # Inherited class attributes
        self._workflow = None
        self._test_req = ("""Test case input requirements not met.
                     Input 1. Client name
                     Input 2. Client System Username
                     Input 3. Client system password

                     These inputs are required as the workflow validates psexec
                     activity which requires system credentials""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_utilities")

        if not all(self.tcinputs.get(key) for key in ('Client',
                                                      'ClientSystemPassword',
                                                      'ClientSystemUsername')):
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:

            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_DIR_CLIENT': self.tcinputs['Client'],
                    'INP_USERNAME_CLIENT': self.tcinputs['ClientSystemUsername'],
                    'INP_PASSWORD_CLIENT': self.tcinputs['ClientSystemPassword'],
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
