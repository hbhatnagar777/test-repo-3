
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""


from VirtualServer.VSAUtils import  OptionsHelper, VirtualServerUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
import time


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Live VM Recovery using v2 client from Snap"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Live Recovery from Snap backups"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.vm_level = True
        self.tpath = None
        self.tstamp = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "destination_host": None,
            "destination_datastore": None
        }

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
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)

    def run(self):
        """Main function for test case execution"""

        try:
           
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            decorative_log("*" * 10 + " Live Recovery " + "*" * 10)

            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.live_recovery = True
            self.vsa_obj.snap_restore = True

            if self.tcinputs.get('RedirectDatastore'):
                self.vsa_obj.redirect_datastore = self.tcinputs['RedirectDatastore']
            if self.tcinputs.get('DelayMigration'):
                self.vsa_obj.delay_migration = self.tcinputs['DelayMigration']

            try:
                decorative_log("*" * 10 + "Restoring the VM out-of-place" + "*" * 10)
                self.vsa_obj.full_vm_restore(self.vm_level)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            # Wait for 15 mins for snap to get unmounted before starting new job
            time.sleep(900)

            try:
                decorative_log("*" * 10 + "Restoring the VM In-place" + "*" * 10)
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.select_live_recovery_restore_type = True
                self.vsa_obj.full_vm_restore(self.vm_level)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)    

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.test_individual_status)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.browser.close_silently(self.browser)