
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
This test case will verify if the System protected files can be restored to a different location and in place restore is disabled

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  install dummyservice, take backup and uinstall the dummyservice, then initialize the browser object

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Components.table import Rtable
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import RestorePanel
from selenium.webdriver.common.by import By
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "command center Navigation"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "Subclient": None,
            "StoragePolicyName": None,
            "NetworkSharePath": None,
            "ShareUsername": None,
            "SharePassword": None,
            "RestorePath": None
        }

    def setup(self):
        """
        Steps:
        Create a backupset and set the storage policy.
        Copy the dummy service files from the specified network share to the client machine.
        Install the readfiles service by executing the batch script for installation.
        Trigger an incremental system state backup.
        Uninstall the readfile service.
        Initialize browser and admin console objects
        """
        self.helper = FSHelper(self)
        FSHelper.populate_tc_inputs(self, mandatory=False)        
        self.machine = Machine(self.tcinputs["ClientName"], self.commcell)

        self.log.info("Step 1. Create a backupset and set the storage policy")
        self.backupset_name = "Test_71043"
        self.helper.create_backupset(self.backupset_name, delete=False)
        self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
        self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'])

        self.log.info("Step 2. Copy the dummy service files from the specified network share to the client machine")

        if self.machine.check_directory_exists(self.tcinputs["RestorePath"]):
            self.machine.remove_directory(self.tcinputs["RestorePath"])


        self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\",
                                                    self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'])
        self.log.info("Step 3.Install the readfiles service by executing the batch script for installation")
        output = self.client_machine.execute_command(r"C:\dummyservice\readfilesservice.bat")

        time.sleep(60)
        reg_val = self.client_machine.get_registry_value(
            win_key=r'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\readfilesService', value='DisplayName'
        )
        if reg_val == "readfilesService":
            self.log.info("Readfile service installed succesfully")
        else:
            raise CVTestStepFailure("Error while installing Readfile service")

        self.log.info("Step 4. Trigger an incremental system state backup.")
        self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

        self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\",
                                                    self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'])

        self.log.info("Step 5. Uninstall the readfile service")
        self.client_machine.execute_command(r"C:\dummyservice\readfilesservice_uninstall.bat")

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.admin_console.navigator.navigate_to_file_servers()
        self.browse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.wizard = Wizard(self.admin_console)
        self.restorepanel = RestorePanel(self.admin_console)

    def run(self):

        try:
        
            self.rtable.access_action_item(self.tcinputs["ClientName"], "Restore")

            self.skip_backupset_selection = False

            try:
                self.admin_console.driver.find_element(By.XPATH, '//*[@id="fsBrowseForAgents"]/div[1]/div[2]/div/div/div/h1') # If there is only one backupset and subclient with system state backup then it will directly open browse page
                self.log.info("Bakcup content page found")
                self.skip_backupset_selection = True
            except Exception as e:
                self.log.info("Bakcup content page not found, going to select backupset")


            if not self.skip_backupset_selection:
                self.restorepanel.select_backupset_and_subclient(self.backupset_name, self.tcinputs["Subclient"])
                self.restorepanel.submit()

            try:
                self.browse.select_action_dropdown_value("Show system protected files")
                raise CVTestStepFailure("Show system protected files key found")
            except Exception as e:
                if "Show system protected files key found" in str(e):
                    raise CVTestStepFailure("Show system protected files key found")
                self.log.info("Show system protected files key not found")
                self.admin_console.click_by_xpath('//*[@id="action-list"]/div')
                    

            self.browse.navigate_path("[System State]\Components\System Protected Files")

            self.browse.select_action_dropdown_value("Show system protected files")

            self.browse.navigate_path("C\\dummyservice")
            self.browse.select_files(select_all=True)
            self.browse.submit_for_restore()

            try:
                self.wizard.select_checkbox(checkbox_id="restoreToFolder")
                raise CVTestStepFailure("In place restore is enabled")
            except Exception as e:
                if "Restore to folder is enabled" in str(e):
                    raise CVTestStepFailure("In place restore is enabled")
                self.log.info("Restore to original folder is disabled.")

            self.dialog.fill_text_in_field(element_id="destinationPathdestinationPathInput", text=self.tcinputs["RestorePath"])
            self.dialog.select_checkbox(checkbox_id="unconditionalOverwrite")
            self.dialog.click_submit()
            restore_job = self.admin_console.get_jobid_from_popup()
            self.job_obj = self.commcell.job_controller.get(restore_job)
            self.job_obj.wait_for_completion()

            
            if self.machine.check_file_exists(self.tcinputs["RestorePath"] + "\\readfilesservice.exe"):
                self.log.info("File restored successfully")
            else:
                raise CVTestStepFailure("Cannot find the restored file in the distination path.")
            
        except Exception as e:
            handle_testcase_exception(self, e)

    def tear_down(self):
        """
        Remove the restored files and close the browser
        """

        if self.machine.check_directory_exists(self.tcinputs["RestorePath"]):
            self.machine.remove_directory(self.tcinputs["RestorePath"])

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)


