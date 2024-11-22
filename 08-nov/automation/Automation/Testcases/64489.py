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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AD.ad import ADClientsPage, ADPage
from Web.AdminConsole.Hub.constants import ADTypes
from AutomationUtils import machine
from AutomationUtils import constants
from Web.Common.page_object import TestStep
from Application.AD import adpowershell_helper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic AD GPO acceptance Test:
    Basic Validation for Metallic GPO backup and restore
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_AD_GPO_Basic_Acceptance"
        self.browser = None
        self.adminconsole = None
        self.navigator = None
        self.app_type = None
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.adpage = None
        self.gpo = None
        self.attribute = None
        self.adclientspage = None
        self.subclient = None
        self.host_machine = None
        self.driver = None
        self.ad_ps_helper = None
        self.server = None
        self.client = None
        self.gpo_directory = None

    @TestStep()
    def perform_backup(self, backuptype):
        """Performs backup for the client
        Args:
            backuptype(str) : backup type
        """
        self.log.info(f"Navigating to active directory")
        self.navigator.navigate_to_activedirectory()
        self.log.info(f"Backing up the GPO for the subclient {self.subclient}")
        self.adclientspage.select_client(self.client)
        self.adminconsole.wait_for_completion()
        self.adpage.backup(backuptype=backuptype)
        self.log.info(f"{backuptype} Backup is completed")

    @TestStep()
    def set_gpo_prop(self, value):
        """Sets the GPO property
        Args:
            value(int) : Value of the property to be set
        """
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, op_type="SET_PROP",
                                         attr_name=self.attribute, value=int(value))

    @TestStep()
    def create_gpo(self):
        """Creates the GPO"""
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, op_type="CREATE_GPO")

    @TestStep()
    def perform_restore(self):
        """Performs restore for the GPO"""
        self.log.info(f"Navigating to active directory")
        self.navigator.navigate_to_activedirectory()
        self.adclientspage.switch_to_app()
        self.adclientspage.select_client(self.client)
        self.log.info("Starting to restore the GPO")
        self.adpage.restore(entity_names=self.gpo, entity_type="GPO")
        self.log.info("Restore completed successfully")

    @TestStep()
    def get_gpo_property_value(self):
        """Fetches the GPO property value
        Returns:
            result(int) : Returns the property value
        """
        result = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, op_type="GET_PROP", attr_name=self.attribute)
        return result

    @TestStep()
    def delete_gpo(self):
        """Deletes the GPO"""
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, op_type="DELETE")

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.domain = self.tcinputs['Domain']
        self.browser.open()
        self.log.info("Opening the browser")
        username = self.inputJSONnode['commcell']['commcellUsername']
        password = self.inputJSONnode['commcell']['commcellPassword']
        ad_user = self.tcinputs['ServerUsername']
        ad_pass = self.tcinputs['ServerPassword']
        self.gpo = self.tcinputs['GPOName']
        self.attribute = self.tcinputs['AttributeName']
        self.subclient = self.tcinputs['subclient']
        self.adminconsole = AdminConsole(self.browser,
                                         self.inputJSONnode['commcell']['webconsoleHostname'])
        self.server = self.tcinputs['ServerName']
        self.app_type = ADTypes.ad
        self.adminconsole.login(username, password)

        self.log.info("Logging in to Command Center")
        self.driver = self.browser.driver
        self.navigator = self.adminconsole.navigator
        self.adpage = ADPage(self.adminconsole, self.commcell)
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.host_machine = machine.Machine(self.server, self.commcell)
        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.adpage, self.server,
                                                             ad_username=ad_user, ad_password=ad_pass)
        self.client = self.tcinputs['ClientName']
        self.gpo_directory = self.tcinputs['GPODirectory']

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_gpo()
            original_value = 900
            self.set_gpo_prop(900)

            self.perform_backup(backuptype="Full")

            self.set_gpo_prop(1000)

            self.perform_restore()

            result_after_modification = self.get_gpo_property_value()

            if original_value == result_after_modification:
                self.log.info(f'GPO property restored successfully')
            else:
                raise Exception('GPO property is not overwritten.')

            self.set_gpo_prop(1500)

            self.perform_backup(backuptype="Incremental")

            result_after_backup = self.get_gpo_property_value()
            self.log.info(f"Value is {result_after_backup}")

            self.delete_gpo()

            self.perform_restore()

            result_after_restore = self.get_gpo_property_value()
            self.log.info(f"{result_after_restore}")

            if result_after_backup == result_after_restore:
                self.log.info(f'Incremental backup verified')
            else:
                raise Exception('GPO is not restored properly.')

            # Verify the sys vol folder is getting restored
            file_exists = self.host_machine.check_directory_exists(self.gpo_directory)
            if file_exists:
                self.log.info(f'Sys vol folder restored successfully.')
            else:
                raise Exception('Sys vol folder is not restored.')

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Tear down process")
        if self.status == constants.PASSED:
            self.log.info("Testcase completed successfully")
            self.delete_gpo()
        else:
            self.log.info("Testcase failed")
        AdminConsole.logout_silently(self.adminconsole)
        Browser.close_silently(self.browser)


