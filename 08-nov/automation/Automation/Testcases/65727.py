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
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AD.ad import ADClientsPage, ADPage
from Web.AdminConsole.Hub.constants import HubServices, ADTypes
from AutomationUtils import constants
from Application.AD import adpowershell_helper
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic AD GPO link acceptance Test:
    Basic Validation for Metallic GPO link backup and restore
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_AD_GPO_Link_Basic_Acceptance"
        self.browser = None
        self.adminconsole = None
        self.navigator = None
        self.service = None
        self.app_type = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.adpage = None
        self.adclientspage = None
        self.subclient = None
        self.__driver = None
        self.client_name = None
        self.ad_ps_helper = None
        self.server = None
        self.gpo = None
        self.first_ou = None
        self.second_ou = None
        self.first_ou_path = None
        self.second_ou_path = None

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
    def perform_restore(self, link_restore_option):
        """Performs restore for the GPO
        Args:
            link_restore_option(str) : Option to restore link
        """
        self.log.info(f"Navigating to active directory")
        self.navigator.navigate_to_activedirectory()
        self.adclientspage.switch_to_app()
        self.adclientspage.select_client(self.client)
        self.log.info("Starting to restore the GPO")
        self.adpage.restore(entity_names=self.gpo, entity_type="GPO", link_restore_option=link_restore_option)
        self.log.info("Restore completed successfully")

    @TestStep()
    def create_gplinks(self, ou_path):
        """Links the GPO to Organisational Unit
        Args:
            ou_path(str) : OU path to which GPO will be linked
        """
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=ou_path, op_type="NEW_GPLINK")

    @TestStep()
    def remove_gplinks(self, ou_path):
        """Deletes the GPO link from the Organisational Unit
        Args:
            ou_path(str) : OU path to which GPO will be removed from
        """
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=ou_path, op_type="REMOVE_GPLINK")

    @TestStep()
    def fetch_gplinks(self, ou_path):
        """Fetches the links associated to an Organisational Unit
        Args:
            ou_path(str) : OU path for fetching the links
        Returns:
            result(int) : The number of links associated to OU
        """
        result = self.ad_ps_helper.gpo_operations(ou=ou_path, op_type="GET_GPLINKS")
        return result

    @TestStep()
    def no_link_restore_verification(self):
        """Verifies the no link restore option"""
        no_link_count = self.fetch_gplinks(ou_path=self.first_ou_path)
        if no_link_count == 0:
            self.log.info(f"Do not restore any links verified")
        else:
            raise Exception("Do not restore any links is not verified")

    @TestStep()
    def merge_link_restore_verification(self):
        """Verifies the merge links restore option"""
        backup_merge_count = self.fetch_gplinks(ou_path=self.first_ou_path)
        self.log.info(f"Backed up link count is {backup_merge_count}")
        merge_count = self.fetch_gplinks(ou_path=self.second_ou_path)
        self.log.info(f"Merged but not backed up link count is {merge_count}")
        if backup_merge_count + merge_count == 2:
            self.log.info(f"Backup and merge links verified")
        else:
            raise Exception("Backup and merge links is not verified")

    @TestStep()
    def revert_link_restore_verification(self):
        """Verifies the revert links restore option"""
        backup_count = self.fetch_gplinks(ou_path=self.first_ou_path)
        self.log.info(f"Backed up link count is {backup_count}")
        without_backedup_count = self.fetch_gplinks(ou_path=self.second_ou_path)
        self.log.info(f"Without backed up link count is {without_backedup_count}")
        if backup_count == 1 and without_backedup_count == 0:
            self.log.info(f"Revert all links to original state is verified")
        else:
            raise Exception("Revert all links to original state is not verified")

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
        self.adminconsole = AdminConsole(self.browser,
                                         self.inputJSONnode['commcell']['webconsoleHostname'])
        self.gpo = self.tcinputs['GPOName']
        self.server = self.tcinputs['ServerName']
        self.adminconsole.login(username, password)
        self.log.info("Logging in to Command Center")
        self.__driver = self.adminconsole.driver
        self.navigator = self.adminconsole.navigator
        self.adpage = ADPage(self.adminconsole, self.commcell)
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.service = HubServices.ad
        self.app_type = ADTypes.ad
        self.client = self.tcinputs['ClientName']
        self.first_ou = self.tcinputs['FirstOU']
        self.second_ou = self.tcinputs['SecondOU']
        self.subclient = self.tcinputs['Subclient']
        self.first_ou_path = self.adpage.ou_path(self.first_ou, self.domain)
        self.second_ou_path = self.adpage.ou_path(self.second_ou, self.domain)
        self.log.info("Navigating to Active Directory")
        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.adpage, self.server,
                                                             ad_username=ad_user, ad_password=ad_pass,
                                                             domain_name=self.domain)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info(f"Deleting all the gpo links associated to both the OUs")
            self.remove_gplinks(self.first_ou_path)
            self.remove_gplinks(self.second_ou_path)

            self.log.info(f"Linking the GPO to {self.first_ou}")
            self.create_gplinks(self.first_ou_path)

            self.perform_backup(backuptype="Incremental")

            self.log.info(f"Deleting the link from {self.first_ou}")
            self.remove_gplinks(self.first_ou_path)

            self.perform_restore(link_restore_option="Do not restore any links from backup")

            self.no_link_restore_verification()

            self.log.info(f"Linking the GPO to {self.second_ou}")
            self.create_gplinks(self.second_ou_path)

            self.perform_restore(link_restore_option="Restore links from backup and merge with existing links")

            self.merge_link_restore_verification()

            self.perform_restore(link_restore_option="Revert all links to their original state in backup")

            self.revert_link_restore_verification()

            self.log.info(f"GPO links are verified successfully")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Tear down process")
        if self.status == constants.PASSED:
            self.log.info("Testcase completed successfully")

        else:
            self.log.info("Testcase failed")
        AdminConsole.logout_silently(self.adminconsole)
        Browser.close_silently(self.browser)
