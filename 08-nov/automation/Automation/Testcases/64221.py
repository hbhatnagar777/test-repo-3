"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()       --   setup function will create setup objects related to web adminconsole

	run()       --   run function of this test case calls Snaptemplate Class to execute
                            and Validate Below Operations.
                            cleanup,create entities,revert,multi snap mount, multi snap unmount, multi snap delete
    tear_down()   --  tear down function will cleanup

	add_client_subclient_enable_snapbackup() -- Method to create second client,subclient and enable snapbackup

	verify_backup() -- Method to perform backup for second client

	client_cleanup() -- Method to Perform cleanup operation for second client

Inputs:
    ClientName          --      name of the client for backup
    StoragePoolName     --      backup location for disk storage
    SnapEngine          --      snap engine to set at subclient
    SubclientContent    --      Data to be backed up

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate
from Web.AdminConsole.Components.panel import Backup, RDropDown
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.dropdown = None
        self.rtable = None
        self.arrays = None
        self.navigator = None
        self.machine = None
        self.source_test_data = None
        self.browser = None
        self.admin_console = None
        self.snap_template = None
        self.tcinputs = {
            "ClientName": None,
            "ClientName2": None,
            "StoragePoolName": None,
            "SnapEngine": None,
            "SubclientContent": None,
            "SubclientContent2": None
        }
        self.name = """CC Automation : Negative Case: For Multiple Mount, Multiple Unmount, Multiple Delete, Revert Operations
                    (we have Two different clients of subclients belongs to same array and engine say(ex: array: HPE Nimble Storage, engine:HPE nimble Snap Engine))"""

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.snap_template = SnapTemplate(self, self.admin_console)
        self.arrays = Arrays(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.dropdown = RDropDown(self.admin_console)
        self.rmodal_dialog = RModalDialog(self.admin_console)
        self.fs_rscdetails = Subclient(self.admin_console)
        self.fs_servers = FileServers(self.admin_console)

    def add_client_subclient_enable_snapbackup(self, clientname, subclient_content):
        """ Adding client, subclient, and enabling snap engine
           Args:
            clientname(str): clientname
            subclient_content(str): subbclient content
        """
        try:
            self.log.info("Adding a second subclient %s", self.snap_template.subclient_name)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(clientname)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab("Subclients")
            self.fs_rscdetails.add_subclient(subclient_name=self.snap_template.subclient_name,
                                             plan_name=self.snap_template.plan_name,
                                             backupset_name=self.snap_template.backupset_name,
                                             contentpaths=subclient_content.split(','),
                                             define_own_content=True)
            self.log.info("Created a new subclient %s", self.snap_template.subclient_name)
            self.fs_rscdetails.access_subclient(subclient_name=self.snap_template.subclient_name,
                                                backupset_name=self.snap_template.backupset_name)
            self.admin_console.wait_for_completion(600)
            self.fs_rscdetails.enable_snapshot_engine(enable_snapshot=True,
                                                      engine_name=self.tcinputs['SnapEngine'])
        except Exception as exp:
            raise CVTestStepFailure(f'Create entities failed with error : {exp}')

    def verify_backup(self, backup_type, clientname):
        """Verify Snapbackup for specific client
           Args:
            backup_type : backup type (ex: Full, Incremental and etc)
            clientname(str): clientname
        """
        try:
            self.log.info("*" * 20 + "Run Snap Backup for Second Subclient" + "*" * 20)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(clientname)
            self.admin_console.access_tab("Subclients")
            jobid = self.fs_rscdetails.backup_subclient(subclient_name=self.snap_template.subclient_name,
                                                        backupset_name=self.snap_template.backupset_name,
                                                        backup_type=backup_type)
            job_status = self.snap_template.wait_for_job_completion(jobid)
            if not job_status:
                exp = "{0} Snap Job ID {1} didn't succeed".format(backup_type, jobid)
                raise Exception(exp)
            return jobid
        except Exception as exp:
            raise CVTestStepFailure(f'Snapbackup operation failed : {exp}')

    def client_cleanup(self, clientname):
        """To perform cleanup operation for client
        Args:
            clientname(str) : clientname
        """
        try:
            self.log.info("*" * 20 + "Cleanup for Second Client" + "*" * 20)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(clientname)
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab("Subclients")
            if self.fs_rscdetails.is_subclient_exists(self.snap_template.subclient_name,
                                                      self.snap_template.backupset_name):
                self.fs_rscdetails.delete_subclient(subclient_name=self.snap_template.subclient_name,
                                                    backupset_name=self.snap_template.backupset_name)
                self.admin_console.wait_for_completion()
                if self.fs_rscdetails.is_subclient_exists(self.snap_template.subclient_name):
                    raise CVTestStepFailure('Subclient still exists. Please check manually.')
                else:
                    self.log.info("Subclient deleted successfully.")
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup entities failed with error : {exp}')

    def run(self):
        """Main function for test case execution"""
        try:
            self.client_cleanup(clientname=self.tcinputs['ClientName2'])
            self.snap_template.cleanup()
            self.snap_template.create_entities()
            self.source_test_data = self.snap_template.add_test_data()
            client1_full_jobid = self.snap_template.verify_backup(Backup.BackupType.FULL)
            self.add_client_subclient_enable_snapbackup(self.tcinputs["ClientName2"],
                                                        self.tcinputs["SubclientContent2"])
            client2_full_jobid = self.verify_backup(backup_type=Backup.BackupType.FULL,
                                                    clientname=self.tcinputs['ClientName2'])
            list_jobs = [client1_full_jobid, client2_full_jobid]
            self.snap_template.mount_snap(job_id=list_jobs, copy_name=self.snap_template.snap_primary)
            self.snap_template.unmount_snap(job_id=list_jobs, copy_name=self.snap_template.snap_primary)
            try:
                self.snap_template.delete_snap(job_id=list_jobs, copy_name=self.snap_template.snap_primary)
            except:
                self.log.info("Cannot delete volumes from different Clients, Arrays or Engines")
        except Exception as exp:
            handle_testcase_exception(self, exp)


    def tear_down(self):
        """To cleanup entities created during TC"""
        try:
            self.client_cleanup(clientname=self.tcinputs['ClientName2'])
            self.snap_template.cleanup()
            pass
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
