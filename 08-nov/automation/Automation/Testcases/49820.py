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
from AutomationUtils.config import get_config

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing user related operations through Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Create/modify user/user group operations"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True

        # Inherited class attributes
        self._workflow = None


    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_user_administration")
        self._log = self._workflow.log

    def run(self):
        """Main function for test case execution"""

        try:
            # Start workflow execution
            for user_logic in ["UserCreateXML", "UserCreateCMD",
                               "UserCreateQcommand", "UserCreateDemoXML",
                               "UserCreateDemoCMD"]:

                self._log.info("Executing workflow test for with {}".
                               format(str(user_logic)))

                self._workflow.execute({'INP_USER_LOGIC': user_logic,
                                        'INP_USERPASSWORD': _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword})

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
