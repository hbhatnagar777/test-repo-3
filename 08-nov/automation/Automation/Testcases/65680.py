# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()               --  initialize TestCase class.

    _cleanup()               --  To perform cleanup operation before setting the environment and after testcase completion.

    setup()                  --  setup function of this test case.

    create_cloud_storage()   -- To create a new cloud storage.

    run()                    --  run function of this test case.

    create_plan()            --  create a new plan/storage policy.

    navigate_to_subclient()  --  navigate to subclient page.

    create_subclient()       --  create subclient for the given backupset. 

    wait_for_job_completion() -- wait for job to complete. 

    restore()                --  perform restore opertation for the given subclient. 

    generate_backup_data()   --  create backup data on content path for backup jobs. 

    backup_job()             --  run backup job on the subclient. 

    

Design Steps:
1. Ensure feature is enabled on the setup ref doc link Enabling Library Creation for HPE StoreOnce Catalyst Library.
2. Configure a new storage pool and with this storage pool add new HPE catalyst store.
3. Associate a plan to this storage.
4. protect a workload, run multiple backup jobs
5. run a restore

Sample Input:
"65680": {
        "backupset": "backupsetName",
        "ClientName": "client name",
        "MediaAgentName": "media agent name",
        "AgentName": "File System",
        "StoreName": "HPE Store Name",
        "Username": "HPE Store Username",
        "Password": "HPE Store Password",
        "Host": "HPE Host"
    }

"""
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.panel import Backup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "HPE Catalyst Storage - Basic acceptace CC case."
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plans = None
        self.file_server = None
        self.fs_sub_client = None
        self.storage_helper = None
        self.MediaAgentName = None
        self.storage_name = None
        self.CLOUD_STORAGE_TYPE = None

        self.client_machine = None
        self.backupset_name = None 
        self.subclient_name = None
        self.plan_name = None
        self.backupset = None

        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None,
            "StoreName": None,
            "Username": None,
            "Password": None,
            "Host": None
        }

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.log.info(f"Username - {self.inputJSONnode['commcell']['commcellUsername']} , Pasword: {self.inputJSONnode['commcell']['commcellPassword']}")
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def cleanup(self):
        """ To perform cleanup operation """

        try:
            # Deleting content Data. 
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            # Deleting restore folder. 
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            
            # Deleting the backupset and subclient. 
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)
            
            # delete the plan created. 
            if self.plans.is_plan_exists(self.plan_name):
                self.plans.delete_plan(self.plan_name)

            # delete storage and the library. 
            self.log.info('Check for storage %s', self.storage_name)
            if self.storage_helper.has_cloud_storage(self.storage_name):
                # To delete cloud storage if exists
                self.log.info('Deletes storage %s', self.storage_name)
                self.storage_helper.delete_cloud_storage(self.storage_name)

        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.utils = TestCaseUtils(self)
        self.mmhelper = MMHelper(self)
        self.init_tc()
        self.CLOUD_STORAGE_TYPE = 'HPE Catalyst Storage'
        self.backupset_name = f'CC-HPE-Auto-BackUpSet-{self.id}'
        self.storage_helper = StorageMain(self.admin_console)
        self.option_selector = OptionsSelector(self.commcell)
        self.navigator = self.admin_console.navigator
        self.file_server = FileServers(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.plans = Plans(self.admin_console)
        self.MediaAgentName = self.tcinputs.get('MediaAgentName')
        self.storage_name = f'{self.id}_HPE_Cloud_Storage_{self.MediaAgentName}'
        self.subclient_name = f'{self.id}_Subclient_{self.MediaAgentName}'
        self.plan_name = f"{self.id}_storage_plan_{self.MediaAgentName}"

        # creating content path - 
        self.client_machine = self.option_selector.get_machine_object(
            self.tcinputs.get("ClientName")
        )
        # get client drive 
        client_drive = self.option_selector.get_drive(
            self.client_machine, size=10*1024
        )

        self.content_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Testdata'
        )
        # creating restore destination. 
        self.restore_dest_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'RestoreData')

    @test_step
    def create_plan(self):
        """To create a new plan"""
        self.navigator.navigate_to_plan()
        self.plans.create_server_plan(
            self.plan_name, {'pri_storage': self.storage_name})
        self.log.info(f'Created Server Plan : {self.plan_name}')

    @test_step
    def create_cloud_storage(self):
        """ To create a new cloud storage"""

        self.log.info("Adding a new cloud storage: %s", self.storage_name)
        ma_name = self.commcell.clients.get(self.tcinputs.get('MediaAgentName')).display_name
        self.storage_helper.add_cloud_storage(
            cloud_storage_name=self.storage_name,
            media_agent=ma_name,
            cloud_type=self.CLOUD_STORAGE_TYPE,
            server_host=self.tcinputs.get("Host", ""),
            container=self.tcinputs.get("StoreName", ""),
            username=self.tcinputs.get("Username", ""),
            password=self.tcinputs.get("Password")
        )
        self.log.info('successfully created cloud storage: %s', self.storage_name)
        if not self.storage_helper.has_cloud_storage(self.storage_name):
            raise Exception('Created cloud storage is not being shown on web page')
    
    @test_step
    def navigate_to_subclient(self):
        """Navigates to the subclient page for both NAS and FS clients"""
        self.log.info("Navigating to subclient page.")
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.file_server.access_server(self.client.display_name)
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    @test_step
    def create_subclient(self):
        """ Creates new subclient
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        # Create backupset. 
        self.log.info(f"creating backupset : {self.backupset_name}")
        self.mmhelper.configure_backupset(self.backupset_name)
        
        # Create SubClient. 
        self.navigate_to_subclient()
        self.log.info("\nCREATING SUBCLIENT : %s", self.subclient_name)
        self.log.info(f"Parameters - {self.subclient_name}, {self.backupset_name}, {self.plan_name}, {self.content_path}")

        self.fs_sub_client.add_subclient(
            subclient_name=self.subclient_name,
            backupset_name=self.backupset_name,
            plan_name=self.plan_name,
            contentpaths=[self.content_path],
            define_own_content=True,
            remove_plan_content=False
        )
        self.log.info(f"Subclient: {self.subclient_name} created successfully!!!")
    
    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
    
    @test_step
    def restore(self):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info("\nSTARTING RESTORE FOR SUBCLIENT : %s PATH : %s", self.subclient_name, self.restore_dest_path)

        dest_client = self.client.display_name
        impersonate_user = None
        restore_job = self.fs_sub_client.restore_subclient(
            subclient_name=self.subclient_name,
            backupset_name=self.backupset_name,
            dest_client=dest_client,
            destination_path=self.restore_dest_path,
            impersonate_user=impersonate_user)
        
        self.wait_for_job_completion(restore_job)
        self.log.info("\n\n RESTORE SUCCESSFUL FOR SUBCLIENT : %s", self.subclient_name)

    def generate_backup_data(self):
        """
        Generates 500MB of uncompressable data
        Args:
            content_path    (str)   -- path where data is to be generated.
        """
        self.log.info(f"Creating 500 MB of data on {self.content_path}")
        self.option_selector.create_uncompressable_data(
            client=self.tcinputs.get("ClientName"),
            path=self.content_path,
            size=0.5
        )

    @test_step
    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        self.log.info("\nSTARTING %s BACKUP FOR SUBCLIENT : %s", backup_type.value, self.subclient_name)
        if backup_type.value.upper() != 'SYNTHETIC_FULL':
            self.generate_backup_data()
        job = self.fs_sub_client.backup_subclient(subclient_name=self.subclient_name,
                                                  backupset_name=self.backupset_name,                                      
                                                  backup_type=backup_type)
        self.wait_for_job_completion(job)
        self.log.info("\n\nBACKUP SUCCESSFULL FOR SUBCLIENT : %s", self.subclient_name)

    def run(self):
        try:
            self.cleanup()
            self.create_cloud_storage()
            self.create_plan()
            self.create_subclient()
            self.backup_job(Backup.BackupType.FULL)
            self.backup_job(Backup.BackupType.INCR)
            self.backup_job(Backup.BackupType.INCR)
            self.backup_job(Backup.BackupType.SYNTH)
            self.navigate_to_subclient()
            self.restore()
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
