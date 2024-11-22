""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

Input Example:
"testcases":    {     "58730": {   "ClientName": "",
                         "SubclientName": "",
                         "Replication Target": "",
                         "BackupsetName": "",
                         "AgentName": "Virtual Server",
                         "InstanceName": "",
                         "Host": "",
                         "MediaAgent": "",
                         "Datastore": "",
                         "SnapAutomationOutput": "",
                         "Network": "VM Network",
                         "Destination network": "Original network"
                         }
                }
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Snap Guest File Restore """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance Test of VMware Snap Guest File Restore"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tpath = None
        self.tstamp = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {"ClientName": None,
                         "InstanceName": None,
                         "SnapEngine": None,
                         "SubclientName": None
                         }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)

        decorative_log("Creating an object for Virtual Server helper")
        self.vmware_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                    self.commcell, self.csdb)
        self.vmware_obj.hypervisor = self.tcinputs['ClientName']
        self.vmware_obj.instance = self.tcinputs['InstanceName']
        self.vmware_obj.subclient = self.tcinputs['SubclientName']
        self.vmware_obj.subclient_obj = self.subclient

    def run(self):
        """Main function for test case execution"""

        try:

            self.vmware_obj.generate_testdata = True
            self.vmware_obj.skip_testdata = False
            self.vmware_obj.backup_method = "Regular"
            decorative_log("*" * 10 + " VSA Snap Backup " + "*" * 10)
            self.vmware_obj.backup()

            try:
                decorative_log("*" * 10 + "In-place Guest File Restore" + "*" * 10)
                self.vmware_obj.snap_restore = True
                self.vmware_obj.backup_method = "snap"
                self.vmware_obj.guest_files_restore(in_place=True)

                decorative_log("*" * 10 + "Running Backup Copy " + "*" * 10)
                bkpcopy_job = self.vmware_obj.storage_policy.run_backup_copy()
                bkpcopy_job = bkpcopy_job.job_id
                job_details = self.vmware_obj.get_job_status(bkpcopy_job)

                self.vmware_obj.copy_precedence = 'Primary'
                self.vmware_obj.snap_restore = False
                decorative_log("*" * 10 + "Out-of-place Guest File Restore" + "*" * 10)
                self.vmware_obj.guest_files_restore()

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

            if self.vmware_obj:
                self.vmware_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        self.browser.close_silently(self.browser)
