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
from Web.AdminConsole.AD.ad import ADPage, ADClientsPage
from Web.AdminConsole.Hub.constants import ADTypes
from AutomationUtils import constants
from Web.Common.page_object import TestStep
from Application.AD import adpowershell_helper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic AD Compare acceptance Test:
    Basic Validation for Metallic AD Compare
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_AD_Compare_Basic_Acceptance"
        self.browser = None
        self.adminconsole = None
        self.navigator = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.app_type = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.adpage = None
        self.adclientspage = None
        self.subclient = None
        self.compare_name = None
        self.attribute = None
        self.entities = None
        self.client_name = None
        self.ad_ps_helper = None
        self.server = None
        self.gpo = None
        self.first_ou = None
        self.second_ou = None
        self.add_gpo = None
        self.modify_gpo = None
        self.delete_gpo = None
        self.new_user = None
        self.modify_user = None
        self.delete_user = None
        self.attribute_value = None
        self.modified_attribute_value = None
        self.source_time = None
        self.gpo_attribute_value = None
        self.gpo_modified_attribute_value = None

    @TestStep()
    def run_backup(self):
        """Performs backup for the AD client"""
        self.log.info("Navigating to Active Directory")
        self.navigator.navigate_to_activedirectory()
        self.log.info(f"Backing up the client {self.client}")
        self.adpage.backup(client=self.client, backuptype='Incremental')
        self.log.info(f"Incremental Backup is completed")

    @TestStep()
    def ps_operations_for_compare(self):
        """Performs powershell operations for compare"""
        self.log.info(f"Running the powershell script to create a user")
        self.ad_ps_helper.attribute_ops(entity_name=self.new_user,
                                        op_type="CREATE_USER")
        self.log.info(f"Running the powershell script to modify a user")
        self.ad_ps_helper.attribute_ops(entity_name=self.modify_user,
                                        attribute=self.attribute, op_type="SET_ATTRIBUTE",
                                        value=self.attribute_value)
        self.log.info(f"Running the powershell script to delete a user")
        self.ad_ps_helper.attribute_ops(entity_name=self.delete_user,
                                        op_type="DELETE_USER")
        self.log.info(f"Running the powershell script to create a gpo")
        self.ad_ps_helper.gpo_operations(gpo_name=self.add_gpo, op_type="CREATE_GPO")
        self.log.info(f"Running the powershell script to modify a gpo")
        self.ad_ps_helper.gpo_operations(gpo_name=self.modify_gpo, attr_name=self.attribute,
                                         value=self.gpo_attribute_value, op_type='SET_PROP')
        self.log.info(f"Running the powershell script to delete an existing gpo")
        self.ad_ps_helper.gpo_operations(gpo_name=self.delete_gpo, op_type='DELETE')
        self.log.info(f"Running the powershell script to add a gpo link")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=self.first_ou, op_type="NEW_GPLINK")
        self.log.info(f"Running the powershell script to delete a gpo link")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=self.second_ou, op_type="REMOVE_GPLINK")

    @TestStep()
    def run_compare_and_validate_report(self):
        """Launch the compare job for the entire domain and validate the results"""
        self.navigator.navigate_to_activedirectory()
        self.log.info("Launching the entire domain compare job")
        self.adpage.run_ad_compare_entire_domain(self.client, compare_name="ADCompare",
                                                 source_time=self.source_time)
        self.log.info("Compare job completed successfully")
        self.navigator.navigate_to_activedirectory()
        self.adpage.entity_search(self.client)
        self.adpage.validate_compare_report(compare_name=self.compare_name,
                                            entities=self.entities, attribute=self.attribute)

    @TestStep()
    def delete_compare(self):
        """Deletes the compare"""
        self.navigator.navigate_to_activedirectory()
        self.adpage.select_client(self.client)
        self.adpage.delete_compare(self.compare_name)

    @TestStep()
    def revert_ps_operations_for_next_compare(self):
        """Reverting powershell operations for the next compare case run"""
        self.log.info("Creating the deleted objects")
        self.ad_ps_helper.gpo_operations(gpo_name=self.delete_gpo, op_type="CREATE_GPO")
        self.ad_ps_helper.attribute_ops(entity_name=self.new_user, op_type="DELETE_USER")
        self.ad_ps_helper.attribute_ops(entity_name=self.modify_user,
                                        attribute=self.attribute, op_type="SET_ATTRIBUTE",
                                        value=self.modified_attribute_value)
        self.ad_ps_helper.attribute_ops(entity_name=self.delete_user,
                                        op_type="CREATE_USER")
        self.ad_ps_helper.gpo_operations(gpo_name=self.add_gpo, op_type="DELETE")
        self.ad_ps_helper.gpo_operations(gpo_name=self.modify_gpo, attr_name=self.attribute,
                                         value=self.gpo_modified_attribute_value, op_type='SET_PROP')
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=self.first_ou, op_type="REMOVE_GPLINK")
        self.ad_ps_helper.gpo_operations(gpo_name=self.gpo, ou=self.second_ou, op_type="NEW_GPLINK")

    def setup(self):
        """Setup function for the testcase"""
        self.browser = BrowserFactory().create_browser_object()
        self.domain = self.tcinputs['Domain']
        self.browser.open()
        self.log.info("Opening the browser")
        username = self.inputJSONnode['commcell']['commcellUsername']
        password = self.inputJSONnode['commcell']['commcellPassword']
        self.adminconsole = AdminConsole(self.browser,
                                         self.inputJSONnode['commcell']['webconsoleHostname'])
        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.adpage, self.server,
                                                             ad_username=username, ad_password=password)
        self.add_gpo = self.tcinputs['ADDGPOName']
        self.modify_gpo = self.tcinputs['MODIFYGPOName']
        self.delete_gpo = self.tcinputs['DELETEGPOName']
        self.adminconsole.login(username, password)
        self.log.info("Logging in to Command Center")
        self.navigator = self.adminconsole.navigator
        self.adpage = ADPage(self.adminconsole, self.commcell)
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.app_type = ADTypes.ad
        self.client = self.tcinputs['ClientName']
        self.first_ou = self.tcinputs['FirstOU']
        self.second_ou = self.tcinputs['SecondOU']
        self.attribute = self.tcinputs['AttributeName']
        self.subclient = self.tcinputs['Subclient']
        self.entities = self.tcinputs["ChangedEnitites"]
        self.new_user = self.tcinputs["NewUser"]
        self.modify_user = self.tcinputs["ModifyUser"]
        self.delete_user = self.tcinputs["DeleteUser"]
        self.attribute = self.tcinputs["ModifiedAttribute"]
        self.attribute_value = self.tcinputs["AttributeValue"]
        self.modified_attribute_value = self.tcinputs["ModifiedAttributeValue"]
        self.gpo_attribute_value = self.tcinputs["GPOAttributeValue"]
        self.gpo_modified_attribute_value = self.tcinputs["GPOModifiedAttributeValue"]
        self.source_time = {'year': self.tcinputs["Year"],
                            'month': self.tcinputs["Month"],
                            'day': self.tcinputs["Day"],
                            'time': self.tcinputs["Time"]
                            }

    def run(self):
        """Main function for test case execution"""
        try:
            self.run_backup()
            self.ps_operations_for_compare()
            self.run_compare_and_validate_report()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Tear down process")
        if self.status == constants.PASSED:
            self.log.info("Testcase completed successfully")
            self.delete_compare()
            self.revert_ps_operations_for_next_compare()
        else:
            self.log.info("Testcase failed")
        AdminConsole.logout_silently(self.adminconsole)
        Browser.close_silently(self.browser)




