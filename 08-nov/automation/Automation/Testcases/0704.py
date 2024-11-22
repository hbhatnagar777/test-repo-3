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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from VirtualServer.VSAUtils.VirtualServerUtils import create_adminconsole_object, decorative_log
from VirtualServer.VSAUtils import VirtualServerUtils as VS_Utils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Reports.utils import TestCaseUtils
from Web.Common.page_object import formatted_error_summary, handle_testcase_exception
from AutomationUtils.machine import Machine



class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "TEST_CASE_NAME"
        # self.tcinputs = {
        #     "INPUT_1": None,
        #     "INPUT_2": None
        # }
        self.browser = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.project_id = self.tcinputs.get('ProjectID')
        self.vsa_obj.network = self.tcinputs.get('network')
        self.vsa_obj.subnet = self.tcinputs.get('subnet')
        self.vsa_obj.zone_name = self.tcinputs.get('Zone')
        # self.vsa_obj.custom_metadata = self.tcinputs.get('cvCustomMetadata', {})
        # self.vsa_obj.service_account_email = self.tcinputs.get('service_account')
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)
        self.vsa_obj.hvobj = self.vsa_obj._create_hypervisor_object()[0]
        # self.vsa_obj.get_all_vms()
        # self.vsa_obj.auto_vsa_subclient = VS_Utils.subclient_initialize(self)
        
        

    def backup(self):
        try:
            self.vsa_obj.backup_type = "INCREMENTAL"
            self.vsa_obj.backup()
        except Exception as e:
            self.log.info("Backup failed with error: {0}".format(e))
        
    def run(self):
        """Run function of this test case"""
        # self.backup()

        try:
            self.vsa_obj.vsa_discovery()
            self.vsa_obj.full_vm_in_place = True
            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.full_vm_restore()
        except Exception as e:
            formatted_error_summary(e)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up()

        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
        
