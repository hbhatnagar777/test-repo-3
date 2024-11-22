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
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSAVSClient, AutoVSACommcell
from Web.Common.page_object import TestStep
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Automation of Live Mount with Passkey as Tenant admin for vm-ware from command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tcinputs = {}
        self.navigator = None
        self.company_details = None
        self.commcell_page = None
        self.tcinputs = {
            "RecoveryTarget": None,
            "Passkey": None,
            "TAUsername": None,
            "TAPassword": None
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.company_details = CompanyDetails(self.admin_console)
        self.commcell_page = Commcell(self.admin_console)

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)

        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)

    @test_step
    def setup_passkey(self, passkey):
        """
        Setup passkey at the company level for restores

        Args:
            passkey         (str): Passkey for restores

        Raises:
            Exception:
                If failed to setup passkey
        """
        self.navigator.navigate_to_commcell()
        self.commcell_page.enable_users_can_enable_passkey()

        self.admin_console.logout()

        # Login as Tenant Admin
        self.admin_console.login(self.tcinputs['TAUsername'], self.tcinputs['TAPassword'])

        self.navigator.navigate_to_company()
        self.company_details.enable_passkey_for_restores(passkey)

    def run(self):
        """Run function of this test case"""
        try:

            target = self.tcinputs['RecoveryTarget']

            self.setup_passkey(self.tcinputs['Passkey'])

            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            AutoVSACommcell_obj = AutoVSACommcell(self.commcell, self.csdb)
            client = self.commcell.clients.get(self.vsa_obj.hypervisor)
            AutoVSAVSClient_obj = AutoVSAVSClient(AutoVSACommcell_obj, client)
            self.vsa_obj.auto_vsa_client = AutoVSAVSClient_obj
            AutoVSAVSClient_obj.timestamp = self.vsa_obj.timestamp
            AutoVSAVSClient_obj.backup_folder_name = self.vsa_obj.backup_folder_name

            target_summary = self.vsa_obj.get_target_summary(target)
            target_client_DN = target_summary['Destination hypervisor']
            target_client = self.vsa_obj.get_client_name_from_display_name(target_client_DN)
            destination_hvobj = self.vsa_obj._create_hypervisor_object(target_client)[0]
            self.vsa_obj.rep_target_dict = target_summary
            self.vsa_obj.restore_destination_client = destination_hvobj
            self.vsa_obj.passkey = self.tcinputs['Passkey']

            vm_names, live_mount_jobs = self.vsa_obj.live_mount(target)

            AutoVSAVSClient_obj.live_mount_validation(None,
                                                      destination_hvobj,
                                                      live_mount_jobs,
                                                      vm_names,
                                                      rep_target_summary=self.vsa_obj.rep_target_dict,
                                                      source_hvobj=self.vsa_obj.hvobj)
        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
