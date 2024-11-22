# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies Zeal trial installation and then setting up from Zeal replication group by setting up all entities
And then finally deleting it

Sample JSON: {
            "ClientName": "<hyperv hypervisor name>", # HyperV Hypervisor must be registered on the CS from which testcase is running
            "trial_vm_name": "trial_vm", # The name of the VM on the hyperV which is used to install Zeal trial on
            "hypervisor_name": "vcenter1", # Vmware Hypervisor must be registered on the CS from which testcase is running.
                                     This is the hypervisor registered on the trial CS
            "source_vm": "vm1", # The source VM for the replication group
            "destination_host": "esxhost1", # The ESX host used to set as the destination in recovery target
            "datastore": "ds1", # The datastore on which the destination VM resides
            "destination_network": "network 1", # The network switch the destination VM must be connected to
}

**Note** - Set the below 3 Registry keys under path specified and restart the machine before running this test case.

    Reg Key path: HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon

    Registries(REG_SZ)

        1. DefaultUserName: username (default user name which you want the machine to be logged in to)

        2. DefaultPassword: password (password for default user)

        3. AutoAdminLogon: 1

    PSEXEC is used for installation on the remote machine, it should be activated before run

    Requires trials.txt file for testcase execution if not case is skipped

"""
from time import sleep

from cvpysdk.commcell import Commcell
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from CVTrials.trial_helper import TrialHelper
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerHelper
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from VirtualServer.VSAUtils.VirtualServerUtils import validate_ip
from VirtualServer.VSAUtils.VMHelpers.HyperVVM import HyperVVM
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.Setup.registration import ZealRegistration
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.virtualization_replication import SOURCE_HYPERVISOR_VMWARE, ConfigureVMWareVM
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for installing commvault trial software package"""
    _AGENT_NAME = 'virtual server'
    _VMWARE_INSTANCE_NAME = 'vmware'
    _HYPERV_INSTANCE_NAME = 'hyper-v'
    _BACKUPSET_NAME = 'defaultBackupSet'
    GROUP_NAME = 'OemGroup'
    TARGET_NAME = 'OemTarget'
    CORE_STORAGE_NAME = 'storage_zeal'
    STORAGE_NAME = 'OemStorage'

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "OEM 118 Zeal Brand Testing"
        self.utils = None
        self.helper = None
        self.install = None
        self.trial_file = None
        self.contents = None
        self.controller_machine = None
        self.machine = None

        self.config = None
        self.tcinputs = {
            "ClientName": None,
            "trial_vm_name": None,
            "hypervisor_name": None,
            "source_vm": None,
            "destination_host": None,
            "datastore": None,
            "destination_network": None,
        }
        self.agent = None
        self.instance = None
        self.trial_vm_name = None
        self.hypervisor_name = None
        self.source_vm = None
        self.destination_host = None
        self.datastore = None
        self.destination_network = None

        self._hypervisor_instance = None
        self._vmware_instance = None
        self._trial_vm = None

        self.trial_commcell = None
        self.trial_csdb = None
        self.trial_client = None
        self.trial_agent = None
        self.trial_instance = None
        self.trial_backupset = None
        self.trial_subclient = None
        self._source_subclient = None

        self.browser = None
        self.admin_console = None
        self.registration = None
        self.getting_started = None
        self.replication_helper = None

    @property
    def hypervisor_instance(self):
        """Returns the hypervisor instance for the hyperv"""
        try:
            hasattr(self, 'agent')
        except:
            self.agent = self.client.agents.get(self._AGENT_NAME)
            self.instance = self.agent.instances.get(self._HYPERV_INSTANCE_NAME)
        if not self._hypervisor_instance:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            self._hypervisor_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent,
                                                                              self.instance)
        return self._hypervisor_instance

    @property
    def vmware_hypervisor(self):
        """Returns the hypervisor object for the vmware hypervisor to be registered on trial machine"""
        if not self._vmware_instance:
            client = self.commcell.clients.get(self.hypervisor_name)
            agent = client.agents.get(self._AGENT_NAME)
            instance = agent.instances.get(self._VMWARE_INSTANCE_NAME)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, client)
            self._vmware_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, agent,
                                                                          instance)
        return self._vmware_instance

    @property
    def trial_vm(self):
        """Returns the trial VM"""
        if not self._trial_vm:
            self._trial_vm = HyperVVM(self.hypervisor_instance.hvobj, self.trial_vm_name)
        self._trial_vm.power_on()
        for _ in range(15):
            if self._trial_vm.ip and validate_ip(self._trial_vm.ip):
                break
            self.log.info('Waiting for VM to have a pingable IP')
            self._trial_vm.update_vm_info(os_info=True)
        return self._trial_vm

    @property
    def backup_job_id(self):
        """Returns the backup job ID of the replication group configured on trial CS"""
        if not self.trial_subclient:
            self.trial_commcell = Commcell(self.trial_vm.ip, self.config.Install.cs_machine_username,
                                           self.config.Install.cs_machine_password)
            self.trial_csdb = CommServDatabase(self.trial_commcell)
            self.trial_client = self.trial_commcell.clients.get(self.vmware_hypervisor.auto_vsaclient.vsa_client_name)
            self.trial_agent = self.trial_client.agents.get(self._AGENT_NAME)
            self.trial_instance = self.trial_agent.instances.get(self._VMWARE_INSTANCE_NAME)
            self.trial_backupset = self.trial_instance.backupsets.get(self._BACKUPSET_NAME)
            self.trial_subclient = self.trial_backupset.subclients.get(self.GROUP_NAME)
        try:
            return self.trial_subclient.find_latest_job().job_id
        except:
            return None

    @property
    def source_subclient(self):
        """Returns the VSA Auto source subclient after initialising all the testcase objects"""
        if not self._source_subclient:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.trial_commcell, self.trial_csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.trial_client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.trial_agent,
                                                                  self.trial_instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.trial_backupset)
            self._source_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.trial_subclient)
        return self._source_subclient

    @property
    def sp_version(self):
        """Returns the SP version for the CS to be used for automation"""
        return self.commcell.version.split('.')[1]

    def init_browser(self):
        """Gets the pre-existing browser or creates a new one if closed"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=self.trial_vm.ip)
        self.registration = ZealRegistration(self.admin_console)

    def login(self):
        """Logs in to the admin console of the trial CS"""
        if not hasattr(self.browser, '_driver'):
            self.init_browser()
        self.admin_console.login(self.config.Install.cs_machine_username,
                                 self.config.Install.cs_machine_password)
        self.getting_started = GettingStarted(self.admin_console)

    def init_dr_helpers(self):
        """
            Initialises the DR helper after group creation is successful
            This class is not made along with login due to localization fetching bug
        """
        self.replication_helper = ReplicationHelper(self.trial_commcell, self.admin_console)

    def logout(self):
        """Logs out of the admin console of the trial CS and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # To create a machine class object for the local machine
        self.trial_vm_name = self.tcinputs['trial_vm_name']
        self.hypervisor_name = self.tcinputs['hypervisor_name']
        self.source_vm = self.tcinputs['source_vm']
        self.destination_host = self.tcinputs['destination_host']
        self.datastore = self.tcinputs['datastore']
        self.destination_network = self.tcinputs['destination_network']

        try:
            self.utils = TestCaseUtils(self)
            self.controller_machine = Machine()
            self.config = get_config()

            self.helper = TrialHelper(self)

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception)

    def install_trial(self):
        """Installs the trial software to the VM"""
        # To Revert the VM to the fresh snap
        self.trial_vm.revert_snap()
        self.trial_vm.wait_for_vm_to_boot()

        input_json = {
            "IsBootstrapper": True,
            "IsToDownload": False,
            "IsBootStrapMode": True,
            "SelectedOS": [
                "WinX64"
            ],
            "CreateSelfExtracting": True,
            "create_commcell": True,
            "CommserveName": self.trial_vm_name,
        }

        # To install the commvault trial package
        sp_version = ''.join([subver.zfill(2) for subver in self.commcell.version.split('.')[1:] if subver != '0'])
        self.helper.interactive_install_trial_package(
            software_path=self.controller_machine.join_path(constants.AUTOMATION_BIN_PATH,
                                                            f"Zeal_Media_11_{sp_version}.exe"),
            input_json=input_json,
            machine=self.trial_vm.machine,
        )

    @test_step
    def register_zeal(self):
        """Registers the user in the Zeal registration"""
        self.init_browser()
        self.admin_console.goto_adminconsole()
        self.registration.fill_user_details(self.config.Install.cs_machine_username,
                                            self.config.Install.cs_machine_password)

    @test_step
    def core_setup(self):
        """Sets up the core entities like storages, hypervisors, access nodes etc"""
        self.helper.admin_console = self.admin_console
        self.helper.configure_core_setup(self.CORE_STORAGE_NAME,
                                         path='C:\\storage',
                                         partition_path='C:\\ddb')
        self.getting_started.access_tab('Disaster recovery')
        self.getting_started.access_panel('Replication')
        vmware_configure = ReplicationGroup(self.admin_console).configure_vmware()
        vmware_configure.create_new_hypervisor(SOURCE_HYPERVISOR_VMWARE,
                                               self.vmware_hypervisor.hvobj.server_host_name,
                                               self.vmware_hypervisor.auto_vsaclient.vsa_client_name,
                                               self.vmware_hypervisor.user_name,
                                               self.vmware_hypervisor.password,
                                               [self.trial_vm_name.lower()])

        vmware_configure.content.set_name(self.GROUP_NAME)
        (vmware_configure.content._hypervisor_details.select_vm_from_browse_tree
         ({self.vmware_hypervisor.auto_vsaclient.vsa_client_name: [self.source_vm]}))
        vmware_configure.next()

        target_configure = vmware_configure.create_new_target(self.TARGET_NAME)
        target_configure.set_destination_host(self.destination_host)
        target_configure.select_datastore(self.datastore)
        target_configure.select_destination_network(self.destination_network)
        target_configure.save()

        vmware_configure.target.select_recovery_target(self.TARGET_NAME)
        vmware_configure.target.unconditionally_overwrite_vm(True)
        vmware_configure.next()

        vmware_configure.create_new_storage(self.STORAGE_NAME,
                                            self.trial_vm_name.lower(),
                                            'C:\\storage2',
                                            ddb_path='C:\\ddb2')
        vmware_configure.storage_cache.select_storage(self.STORAGE_NAME)
        vmware_configure.next()

        vmware_configure.next()
        vmware_configure.finish()

    @test_step
    def verify_group_creation(self):
        """Verifies that the replication group creation passed with correct values
        in replication groups listing page"""
        self.replication_helper.verify_replication_group_exists(self.GROUP_NAME,
                                                                self.vmware_hypervisor.auto_vsaclient.vsa_client_name,
                                                                self.TARGET_NAME)

    def verify_backup_job_completion(self):
        """Waits for backup job to complete and then verify its details"""
        for _ in range(15):
            if self.backup_job_id:
                break
            self.log.info('Waiting to 1 minute to let the job trigger')
            sleep(60)
        else:
            raise CVTestStepFailure(f"No backup job triggered for replication group [{self.GROUP_NAME}]")
        self.log.info('Waiting for backup job %s to finish', self.backup_job_id)
        job_obj = self.trial_commcell.job_controller.get(self.backup_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    def verify_replication_job_completion(self):
        """Waits for replication job to complete and then verify its details"""
        self.log.info("Waiting 2 minutes to let live sync update")
        sleep(120)
        live_sync_utils = LiveSyncUtils(self.source_subclient,
                                        ReplicationGroup.get_schedule_name_by_replication_group(self.GROUP_NAME))
        job_obj = live_sync_utils.get_recent_replication_job(self.backup_job_id)
        self.log.info("Waiting for replication job id %s to finish", job_obj.job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    @test_step
    def verify_group_deletion(self):
        """Verify replication group, vm group and schedules are deleted"""
        self.replication_helper.delete_replication_group(self.GROUP_NAME, [self.source_vm])
        self.replication_helper.verify_group_deletion(self.GROUP_NAME)

    def run(self):
        """Main function for test case execution"""
        try:
            # self.install_trial()
            self.trial_vm.revert_snap(f'{self.sp_version}')
            self.register_zeal()
            self.login()
            self.core_setup()
            self.init_dr_helpers()
            self.verify_group_creation()

            self.logout()
            self.verify_backup_job_completion()
            self.verify_replication_job_completion()

            self.login()
            self.verify_group_deletion()
        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Cleans up the testcase"""
        self.logout()
