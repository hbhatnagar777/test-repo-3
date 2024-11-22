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
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import ADTypes
from Web.AdminConsole.AD.ad import ADPage, ADClientsPage
from AutomationUtils import machine, constants
from Application.AD import adpowershell_helper
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for Verification of advance options and Link for AD GPO Restore
    Options to be Verified are Enforced, LinkEnabled and Status
    """

    def __init__(self):
        """Initialize the Testcase class Object"""
        super(TestCase, self).__init__()
        self.name = "Test to check GPO advance Restore"
        self.browser = None
        self.client = None
        self.gpo_name = None
        self.gpo_name2 = None
        self.ou1_name = None
        self.ou2_name = None
        self.domain = None
        self.app_type = None
        self.utils = TestCaseUtils(self)
        self.admin_console = None
        self.navigator = None
        self.driver = None
        self.navigator = None
        self.ad_page = None
        self.ad_clientpage = None
        self.host_machine = None
        self.ad_ps_helper = None
        self.server = None
        self.gpo_status = None
        self.original_enabled_value = None
        self.original_enforced_value = None
        self.original_gpo_status = None
        self.gpo2_id = None

    @TestStep()
    def restore_validate_result(self, link_restore_option):
        """
        function used to Restore and validate the result for GPOLink Advance Options
             Args:
                link_restore_option(str)     --advance option to select while Restore
            Returns:
                exception
        """
        try:
            self.navigator.navigate_to_activedirectory()
            self.ad_clientpage.entity_search(self.client)
            self.log.info("Starting the Restore")
            self.ad_page.restore(entity_names=self.gpo_name, entity_type="GPO",
                                 link_restore_option=link_restore_option)
            self.log.info("Restore Completed")

            # Getting the advance Gpo attributes value
            self.log.info("Getting the GPO Link and status value")
            att_result = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                                          op_type="GPLINKS_ATT", ou=self.ou1_name)
            prop_result = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                                           op_type="GPLINKS_PROP")
            new_enforce_value = None
            new_enabled_value = None
            new_gpo_status = None
            if len(att_result) > 0:
                new_enabled_value = att_result[0][0]
                new_enforce_value = att_result[0][1]
                new_gpo_status = prop_result[0][1]

            # Verifying for  the GPO advance option Restore
            self.log.info("Verifying for  the GPO advance option Restore")
            if (self.original_enabled_value == new_enabled_value
                    and self.original_enforced_value == new_enforce_value
                    and self.original_gpo_status == new_gpo_status):
                self.log.info("Advance GPO restore Successful")
            else:
                raise Exception("The Advance GPO Restore Verification "
                                " attributes not restored")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    @TestStep()
    def create_gpo(self):
        """
        Function is used to create the gpo

        """
        self.log.info(f"Creating GPO name: {self.gpo_name} ")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name, op_type="CREATE_GPO")

        self.log.info(f"Creating GPO name: {self.gpo_name2} ")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name2, op_type="CREATE_GPO")

    @TestStep()
    def create_gpo_link(self, gpo_name=None, ou_name=None):
        """
        function is used to link a gpo to an ou
        Args:
            gpo_name(str)     : name of the gpo
            ou_name           : name of an ou

        """
        self.log.info(f"Linking the {gpo_name} to {ou_name}")
        self.ad_ps_helper.gpo_operations(gpo_name=gpo_name,
                                         op_type="NEW_GPLINK",
                                         ou=ou_name)

    @TestStep()
    def do_backup(self):
        """
        Run the backup job

        """
        self.log.info("Backing up the GPO")
        self.ad_clientpage.entity_search(self.client)
        self.admin_console.wait_for_completion()
        self.ad_page.backup(backuptype='Incremental')
        self.log.info("Incremental Backup is completed")

    @TestStep()
    def modify_gpo_link(self):
        """
        Function modify the advance option attribute and status  of the gpo

        """
        self.log.info("Modifying the GPO Attributes value using powershell")
        new_enable_value = "No" if self.original_enabled_value == "True" else "Yes"
        new_enforced_value = "No" if self.original_enforced_value == "True" else "Yes"
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                         op_type="SET_STATUS",
                                         status=self.gpo_status)
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                         op_type="SET_ADLINKS",
                                         ou=self.ou1_name,
                                         link_enabled=new_enable_value,
                                         enforced=new_enforced_value)

    @TestStep()
    def get_gpo_attribute(self):
        """
        function is used to get the advance option attribute and status of the gpo

        """
        self.log.info("Getting the GPO Attributes value")
        att_result = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                                      op_type="GPLINKS_ATT",
                                                      ou=self.ou1_name)
        prop_result = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name,
                                                       op_type="GPLINKS_PROP")
        prop_result2 = self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name2,
                                                        op_type="GPLINKS_PROP")

        if len(att_result) > 0:
            self.original_enabled_value = att_result[0][0]
            self.original_enforced_value = att_result[0][1]
            self.original_gpo_status = prop_result[0][1]
            self.gpo2_id = prop_result2[0][0]
        self.log.info(f"Original enabled value is {self.original_enabled_value}")
        self.log.info(f"Original enforced value is {self.original_enforced_value}")
        self.log.info(f"Original status value is {self.original_gpo_status}")

    @TestStep()
    def delete_and_restore_gpo(self):
        """
         Function delete the gpo and perform the restore of the gpo
        """
        # Deleting the gpo link
        self.log.info(f"Deleting the gpo link of {self.gpo_name2} from {self.ou1_name} ou ")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name2,
                                         op_type="REMOVE_GPLINK",
                                         ou=self.ou1_name)

        # Linking the gpo to ou
        self.create_gpo_link(gpo_name=self.gpo_name2, ou_name=self.ou2_name)

        self.navigator.navigate_to_activedirectory()
        self.ad_clientpage.entity_search(self.client)
        self.log.info("Starting the Restore")
        self.ad_page.restore(entity_names=self.gpo_name2, entity_type="GPO",
                             link_restore_option="Revert all links to "
                                                 "their original state in backup")
        self.log.info("Restore Completed")

    @TestStep()
    def validate_delete_result(self):
        """
        Function to return OU Link id
        """
        self.log.info("Getting the ID of gpo linked to ou")
        ou1_link_id = self.ad_ps_helper.gpo_operations(op_type="GPLINK_ID", ou=self.ou1_name)
        ou2_link_id = self.ad_ps_helper.gpo_operations(op_type="GPLINK_ID", ou=self.ou2_name)
        self.log.info(f"OU 1 link id {ou1_link_id}")
        self.log.info(f"OU 2 link id {ou2_link_id}")
        # Checking if the Link get removed from ou
        for i in ou2_link_id:
            if i[0] == self.gpo2_id:
                raise Exception("The Advance GPO Restore Failed")
        self.log.info(f"Got expected results for OU 2")

        result_ou1 = False
        # Verify if the Link get Restored to ou
        for i in ou1_link_id:
            if i[0] == self.gpo2_id:
                result_ou1 = True
                break
        self.log.info(f"Got expected results for OU 1")
        if result_ou1:
            self.log.info("The gpo link restore successful")
        else:
            raise Exception("The Advance GPO Restore Failed")

    def setup(self):
        """setup function for the TestCase"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.log.info("Opening the browser")
        self.domain = self.tcinputs["Domain"]
        hostname = self.inputJSONnode['commcell']['webconsoleHostname']
        username = self.tcinputs['TenantUsername']
        password = self.tcinputs['TenantPassword']
        ad_user = self.tcinputs["ServerUsername"]
        ad_pass = self.tcinputs["ServerPassword"]
        self.gpo_name = 'Test' + str(int(time.time()))
        self.gpo_name2 = 'Testgpo' + str(int(time.time()))
        self.admin_console = AdminConsole(self.browser, hostname)
        self.server = self.tcinputs["ServerName"]
        self.app_type = ADTypes.ad
        self.log.info("Logging into the Command Center")
        self.admin_console.login(username, password)
        self.navigator = self.admin_console.navigator
        self.ad_page = ADPage(self.admin_console, self.commcell)
        self.ad_clientpage = ADClientsPage(self.admin_console)
        self.host_machine = machine.Machine(self.server, self.commcell)
        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.ad_page, self.server,
                                                             ad_username=ad_user,
                                                             ad_password=ad_pass,
                                                             domain_name=self.domain)
        self.client = self.tcinputs["Client"]
        self.ou1_name = self.tcinputs["Ou1Name"]
        self.ou2_name = self.tcinputs["Ou2Name"]
        self.gpo_status = self.tcinputs["GpoStatus"]

    def run(self):
        """Main function for Test Case Execution"""
        try:
            self.log.info("Navigating to Active Directory")
            self.navigator.navigate_to_activedirectory()

            self.create_gpo()

            self.create_gpo_link(gpo_name=self.gpo_name, ou_name=self.ou1_name)
            self.create_gpo_link(gpo_name=self.gpo_name2, ou_name=self.ou1_name)

            self.get_gpo_attribute()

            self.do_backup()

            self.modify_gpo_link()

            self.restore_validate_result(link_restore_option="Revert all links to "
                                                             "their original state in backup")

            self.log.info(f"Deleting the gpo{self.gpo_name}")
            self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name, op_type="DELETE")

            self.restore_validate_result(link_restore_option="Restore links from backup "
                                                             "and merge with existing links")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function for this Test Case"""
        self.log.info("Executing the Tear down function")
        if self.status == constants.PASSED:
            self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name, op_type="DELETE")
            self.ad_ps_helper.gpo_operations(gpo_name=self.gpo_name2, op_type="DELETE")
            self.log.info("Testcase completed successfully")
        else:
            self.log.info("Testcase failed")
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
