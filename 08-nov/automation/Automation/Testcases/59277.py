""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

Input Example:
"testcases":    {     "59277": {   "ClientName": "",
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
from Web.AdminConsole.Helper.VirtualServerHelper import VMwareAdminConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Snap Backup, Backup copy, Mount/Unmount, Restore and Delete"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance Test of VMware Snap Backup and Restore"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tpath = None
        self.tstamp = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
        }
        self.child_job = """select childjobid from jmjobdatalink where parentjobId={a}"""

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
        self.vmware_obj = VMwareAdminConsole(self.instance, self.browser,
                                             self.commcell, self.csdb)
        self.vmware_obj.hypervisor = self.tcinputs['ClientName']
        self.vmware_obj.instance = self.tcinputs['InstanceName']
        self.vmware_obj.subclient = self.tcinputs['SubclientName']
        self.vmware_obj.subclient_obj = self.subclient
        self.vmware_obj.testcase_obj = self

    def run(self):
        """Main function for test case execution"""

        try:

            self.vmware_obj.generate_testdata = True
            self.vmware_obj.skip_testdata = False
            self.vmware_obj.backup_method = "Regular"
            decorative_log("*" * 10 + " VSA Snap Backup " + "*" * 10)
            if "skip_pre_backup_config" in self.tcinputs.keys():
                self.vmware_obj.run_pre_backup_config_checks = not self.tcinputs['skip_pre_backup_config']
            backup_jobid = self.vmware_obj.backup()
            parent_jobid = self.vmware_obj.backup_job
            child_jobid = self.vmware_obj.execute_query(self.child_job, {'a': parent_jobid})
            child_jobid = child_jobid[0][0]
            self.vmware_obj.mount_snap(parent_jobid)
            self.vmware_obj.unmount_snap(parent_jobid)

            self.vmware_obj.unconditional_overwrite = True
            self.vmware_obj.live_recovery = False

            if self.tcinputs.get('RedirectDatastore'):
                self.vmware_obj.redirect_datastore = self.tcinputs['RedirectDatastore']
            if self.tcinputs.get('Datastore'):
                self.vmware_obj.datastore = self.tcinputs['Datastore']
            if self.tcinputs.get('Replication Target'):
                self.vmware_obj.restore_client = self.tcinputs['Replication Target']

            try:
                decorative_log("*" * 10 + "In-place Full VM Restore" + "*" * 10)
                self.vmware_obj.full_vm_in_place = True
                self.vmware_obj.full_vm_restore()

                decorative_log("*" * 10 + "Running Backup Copy " + "*" * 10)
                bkpcpy_job = self.vmware_obj.backup_copy()
                job_details = self.vmware_obj.get_job_status(bkpcpy_job)
                self.vmware_obj.delete_snap_array(parent_jobid)

                self.vmware_obj.unconditional_overwrite = False
                self.vmware_obj.snap_restore = False
                decorative_log("*" * 10 + "Out-of-place Full VM Restore from Backup Copy" + "*" * 10)
                self.vmware_obj.full_vm_in_place = False
                self.vmware_obj.full_vm_restore()

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
                self.vmware_obj.post_restore_clean_up(source_vm = True , status= self.status)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        self.browser.close_silently(self.browser)
