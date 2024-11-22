""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

Input Example:
"testcases":    {     "58742": {   "ClientName": "",
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
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSAVSClient, AutoVSACommcell


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Live Mount from Snap Backup """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance Test of VMware Live Mount from Snap Backup"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.vsa_obj = None
        self.admin_console = None
        self.tcinputs = {
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
            target = self.tcinputs['RecoveryTarget']
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup_method = "SNAP"
            if "skip_pre_backup_config" in self.tcinputs.keys():
                self.vsa_obj.run_pre_backup_config_checks = not self.tcinputs['skip_pre_backup_config']
            backup_jobid= self.vsa_obj.backup()
            parent_jobid = self.vsa_obj.backup_job

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

            self.vsa_obj.snap_restore = True
            vm_names, live_mount_jobs = self.vsa_obj.live_mount(target)

            AutoVSAVSClient_obj.live_mount_validation(None,
                                                      destination_hvobj,
                                                      live_mount_jobs,
                                                      vm_names,
                                                      rep_target_summary=self.vsa_obj.rep_target_dict,
                                                      source_hvobj=self.vsa_obj.hvobj)
            self.vsa_obj.delete_snap_array(parent_jobid)
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
            self.utils.handle_testcase_exception(exp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
