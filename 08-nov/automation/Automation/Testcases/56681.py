# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Backup and restore of Azure VM from admin console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Backup and restore of Azure VM from admin console"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.vsa_obj = None


    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
   
        self.vsa_obj.network_interface = self.tcinputs.get('network_interface', None)
        self.vsa_obj.storage_account = self.tcinputs.get('storage_account', None)
        self.vsa_obj.resource_group = self.tcinputs.get('resource_group', None)
        self.vsa_obj.region = self.tcinputs.get('region', None)    
        self.vsa_obj.unconditional_overwrite = True

    def run(self):
        """Main function for test case execution"""
        try:
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()
            self.vsa_obj.full_vm_restore()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
