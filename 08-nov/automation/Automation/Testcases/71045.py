import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.FSPages.RFsPages.RFs_bmr import VirtualizeMe
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from cvpysdk.recovery_targets import RecoveryTarget
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.exceptions import CVTestStepFailure
from cvpysdk.client import Client, Clients

class TestCase(CVTestCase):

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "VME to Vmware with Clone"
        self.browser = None
        self.admin_console = None

        self.tcinputs = {
            "ClientName": None,
            "recovery_target": None,
            "restore_vm_name": None,
            "clone_client": None,
            "client_name": None,
            "use_dhcp": None,
            "destination_host": None,
        }

    def initial_setup(self):

        self.fileserver = FileServers(self.admin_console)
        self.fs_details = FsSubclient(self.admin_console)
        self.fssubdeets = FsSubclientDetails(self.admin_console)
        self.RModalPanel = RModalPanel(self.admin_console)
        self.table = Table(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.virtualize = VirtualizeMe(self.admin_console)

    def restore_setup(self):
        """
        Method to perform checks on restore machine required for test case execution
        """
        self.recovery_target = RecoveryTarget(self.commcell, self.tcinputs["recovery_target"])
        self.hvobj = Hypervisor(auto_commcell=self.commcell, commcell=self.commcell,
                                server_host_name=[self.tcinputs["destination_host"]],
                                user_name=self.tcinputs["host_creds"]["username"],
                                password=self.tcinputs["host_creds"]["password"], instance_type="vmware",
                                host_machine=self.tcinputs["AccessNode"])
        self.hvm = self.hvobj.to_vm_object(self.tcinputs["restore_vm_name"])

    def login(self):
        """Logs in to command center"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

    def logout(self):
        """Logs out of from command center"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):

        """
        Method to setup test variables
        """
        self.helper = FSHelper(self)
        FSHelper.populate_tc_inputs(self, mandatory=False)

    def backup_cycle(self):
        """
        Method to run backup cycle for specified storage policy
        """
        backupset_name = "defaultBackupSet"
        self.helper.create_backupset(backupset_name, delete=False)
        self.helper.create_subclient("default", self.tcinputs["StoragePolicyName"], ["\\"])
        self.log.info("Run a full system state backup")
        self.helper.run_onetouch_backup(backup_type="FULL")
        self.log.info("Trigger an incremental system state job ")
        self.helper.run_onetouch_backup(backup_type="Incremental")
        self.log.info("Run a synthetic full backup")
        self.helper.run_onetouch_backup(backup_type="Synthetic_full")
        self.log.info("Trigger an incremental system state job ")
        self.helper.run_onetouch_backup(backup_type="Incremental")

    def _wait_for_completion(self,job_obj, timeout=30, **kwargs):
        """
            Waits till the job is not finished; i.e.; till the value of job.is_finished is not True.
            Kills the job and exits, if the job has been in Pending / Waiting state for more than
            the timeout value.
            In case of job failure job status and failure reason can be obtained
                using status and delay_reason property

            Args:
                timeout     (int)   --  minutes after which the job should be killed and exited,
                        if the job has been in Pending / Waiting state
                    default: 30

            Returns:
                bool    -   boolean specifying whether the job had finished or not
                    True    -   if the job had finished successfully

                    False   -   if the job was killed/failed

        """
        start_time = actual_start_time = time.time()
        pending_time = 0
        waiting_time = 0
        previous_status = None
        return_timeout = kwargs.get('return_timeout')

        status_list = ['pending', 'waiting']
        current_phase = ''
        while not job_obj.is_finished:
            time.sleep(30)
            try:
                progress_info = job_obj._get_job_details()["jobDetail"]["progressInfo"]
                if current_phase != progress_info["currentPhase"]:
                    current_phase = progress_info["currentPhase"]
                    self.log.info(f'Job completed {progress_info["percentComplete"]} %')
                    self.log.info(f'Current Phase: {current_phase}')
                    self.log.info(progress_info["reasonForJobDelay"])
            except Exception:
                pass

            if return_timeout and ((time.time() - actual_start_time) / 60) > return_timeout:
                return False

            # get the current status of the job
            status = job_obj.status
            status = status.lower() if status else job_obj.state.lower()

            # set the value of start time as current time
            # if the current status is pending / waiting but the previous status was not
            # also if the current status is pending / waiting and same as previous,
            # then don't update the value of start time
            if status in status_list and previous_status not in status_list:
                start_time = time.time()

            if status == 'pending':
                pending_time = (time.time() - start_time) / 60
            else:
                pending_time = 0

            if status == 'waiting':
                waiting_time = (time.time() - start_time) / 60
            else:
                waiting_time = 0

            if pending_time > timeout or waiting_time > timeout:
                job_obj.kill()
                break

            # set the value of previous status as the value of current status
            previous_status = status
        else:
            return job_obj._status.lower() not in ["failed", "killed", "failed to start"]

        return False

    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not self._wait_for_completion(job_obj):

            try:
                restore_vm = self.hvobj.to_vm_object(self.tcinputs["restore_vm_name"])
            except Exception:

                raise CVTestStepFailure(
                    "Failed to create VM object for restore: %s" % self.tcinputs["restore_vm_name"],
                    "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
                )
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

        self.log.info("Successfully finished %s job", jobid)
        return True

    def run_virtualize_me(self):
        """
        Method to run Virtualize Me from command center
        """

        try:
            self.admin_console.navigator.navigate_to_file_servers()
            self.rtable.access_action_item(self.tcinputs["ClientName"], "Virtualize Me")
            self.virtualize.recovery_point_configuration()
            self.virtualize.target_selection(recovery_target=self.tcinputs["recovery_target"],destination_vm_name=self.tcinputs["restore_vm_name"],overwrite_option=self.tcinputs["overwrite_option"])
            self.virtualize.commcell_configuration(operating_system="Linux", client_name=self.tcinputs["client_name"])
            self.virtualize.machine_configuration(operating_system="Linux",use_dhcp=self.tcinputs["use_dhcp"])
            job_id = self.virtualize.adv_recovery_options()
            self.wait_for_job_completion(job_id)

        except Exception as e:
            self.log.error(f"Error occurred during virtualize me")
            raise CVTestStepFailure(f"Error occurred during virtualize me {e}")

    def post_virtualize_me(self):
        """
        Method to perform post virtualize me tasks
        """

        time.sleep(600)

        self.hvm.wait_for_vm_to_boot()
        restore_machine_ip = self.hvm.ip
        self.log.info(f"IP of restored machine: {restore_machine_ip}")
        dest_client = Client(self.commcell, self.tcinputs["client_name"])
        if dest_client.readiness_details.is_ready():
            self.log.info("Destination client is ready")
        else:
            self.log.info("Destination client is not ready")
            raise CVTestStepFailure(
                "Destination client is not ready"
            )

    def run(self):
        """
        Main test case execution
        """

        self.backup_cycle()
        self.login()
        self.initial_setup()
        self.run_virtualize_me()
        self.restore_setup()
        self.post_virtualize_me()
        self.logout()


    def tear_down(self):
        """
        Method to perform teardown tasks
        """
        pass
        try:
            Clients(self.commcell).delete(self.tcinputs["client_name"])
            self.log.info("Destination client deleted")
        except Exception as e:
            self.log.info("Destination client not deleted")
            raise CVTestStepFailure("Destination client not deleted")

        try:
            self.hvm.delete_vm()
        except Exception:
            self.log.info("VM not deleted")
            raise CVTestStepFailure("VM not deleted")
