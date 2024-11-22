# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------
"""
Test case to verify the UI options shown at subclient policies page in admin console.

It verifies
1.creation of subclient policy based on agent type and user input.
2.Editing of subclient policy options based on user input.
3.Editing of subclient options based on user input.
4.Deletion of subclient from the subclient policy.
5.Deletion of subclient policy.
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.subclient_policies_helper import SubclientPoliciesMain
from Web.AdminConsole.adminconsole import AdminConsole

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ basic acceptance test case for subclient policy configuration """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Admin console - Subclient policy Acceptance"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.subclient_policies_obj = None
        self.admin_console = None

        self.tcinputs = {
            'subclient_policy_name': None,
            'agent_type': None,
            'storage_policy_name': None,
            'associations': None,
            'new_subclient_policy_name': None,
            'new_associations': None,
            'new_storage_policy_name': None,
            'subclient_name': None,
            'new_subclient_name': None,
            'subclient_path': None,
            'new_subclient_path': None

        }

    def run(self):
        try:
            self.log.info("Started executing %s test case", self.id)
            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            driver = self.browser.driver

            self.log.info("Log into the command center")
            self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                     self.inputJSONnode["commcell"]["commcellPassword"])
            self.subclient_policies_obj = SubclientPoliciesMain(self.admin_console)

            self.subclient_policies_obj.subclient_policy_name = self.tcinputs['subclient_policy_name']
            self.subclient_policies_obj.agent_type = self.tcinputs['agent_type']
            self.subclient_policies_obj.storage_policy_name = self.tcinputs['storage_policy_name']
            self.subclient_policies_obj.associations = self.tcinputs['associations']

            self.subclient_policies_obj.add_subclient_policy()
            self.log.info("Subclient Policy was created successfully")

            self.subclient_policies_obj.new_subclient_policy_name = self.tcinputs['new_subclient_policy_name']
            self.subclient_policies_obj.new_associations = self.tcinputs['new_associations']
            self.subclient_policies_obj.subclient_name = self.tcinputs['subclient_name']
            self.subclient_policies_obj.new_subclient_name = self.tcinputs['new_subclient_name']
            self.subclient_policies_obj.subclient_path = self.tcinputs['subclient_path']
            self.subclient_policies_obj.new_subclient_path = self.tcinputs['new_subclient_path']
            self.subclient_policies_obj.new_storage_policy_name = self.tcinputs['new_storage_policy_name']

            self.subclient_policies_obj.edit_subclient_policy()
            self.log.info("Subclient Policy options were modified successfully")

            self.subclient_policies_obj.edit_subclient()
            self.log.info("Subclient Policy subclient options were modified successfully")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.subclient_policies_obj.delete_subclient()
            self.log.info("Subclient Policy subclient was deleted successfully")

            self.subclient_policies_obj.delete_subclient_policy()
            self.log.info("Test case execution is completed.")
            self.browser.close()
