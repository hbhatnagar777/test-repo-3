# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Verify if backups run with valid/invalid credentials

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and is executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.page_object import handle_testcase_exception, TestStep



class TestCase(CVTestCase):
    """Initiates test case."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.file_servers = None
        self.browser = None
        self.admin_console = None
        self.utils = None
        self.fssubclient_obj = None
        self.helper = None
        self.subclient_obj = None
        self.navigator = None
        self.cleanup_run = None
        self.subclient_name = None
        self.jobs = None
        self.rtable = None
        self.name = "Setting Pre/Post commands from command center"
        self.step = None
        self.tcinputs = {
            "ClientName": None,
            "BackupsetName": None,
            "PreScanProcess": None,
            "PostScanProcess": None,
            "PreBackupProcess": None,
            "PostBackupProcess": None,
        }

    def setup(self):
        """ Testcase objects are initializes in this method"""
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.subclient_name = "Test_" + str(self.id)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.log.info("Step1. Logging into browser")
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                    password=self.inputJSONnode['commcell']['commcellPassword'])
        self.fssubclient_obj = FsSubclient(self.admin_console)
        self.subclient_obj = FsSubclientDetails(self.admin_console)
        self.file_servers = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.rtable = Rtable(self.admin_console)
        self.jobs = Jobs(self.admin_console)
        
    def vaildate_pre_post(self,commands):
        """ Validates Pre Post Commands set on subclient
                Args:
                    commands   list(commands): list of commands to be set.
                Raises:
                    Exception :
                     -- if fails to validate the commands. It compares the given commands_from_input with value 
                        stored returned from cvpsdk layer
         """
        if commands:
            pre_scan_process = self.tcinputs[commands[0]]
            post_scan_process = self.tcinputs[commands[1]]  
            pre_backup_process = self.tcinputs[commands[2]]
            post_backup_process = self.tcinputs[commands[3]]
            commands_from_inputs = {"pre_scan_command": pre_scan_process,
                                        "post_scan_command": post_scan_process,
                                        "pre_backup_command": pre_backup_process,
                                        "post_backup_command": post_backup_process}
        else:
            commands_from_inputs = {"pre_scan_command": '', "post_scan_command": '', "pre_backup_command": '',
                                    "post_backup_command": ''}

        self.helper.validate_pre_post_commands(commands_from_inputs)

    def clear_pre_post_commands(self):
        """Clears all the Pre Post commands set on subclient"""
        self.navigate_to_server()
        self.fssubclient_obj.access_subclient(self.tcinputs['BackupsetName'], self.subclient_name)
        self.subclient_obj.clear_pre_post_commands(input_id="preBackupCommand")
        self.subclient_obj.clear_pre_post_commands(input_id="postBackupCommand")
        self.subclient_obj.clear_pre_post_commands(input_id="preScanCommand")
        self.subclient_obj.clear_pre_post_commands(input_id="postScanCommand")
        self.subclient.refresh()
        self.subclient.refresh()

    def set_pre_post_commands(self,commands):
        """Sets the Pre Post commands set on subclient"""
        self.navigate_to_server()
        self.fssubclient_obj.access_subclient(self.tcinputs['BackupsetName'], self.subclient_name)
        pre_scan_process = self.tcinputs[commands[0]]
        post_scan_process = self.tcinputs[commands[1]]  
        pre_backup_process = self.tcinputs[commands[2]]
        post_backup_process = self.tcinputs[commands[3]]
        self.subclient_obj.set_pre_backup_command(pre_backup_process)
        self.subclient_obj.set_post_backup_command(post_backup_process)
        self.subclient_obj.set_pre_post_advanced(pre_scan_process=pre_scan_process,
                                                     post_scan_process=post_scan_process)
        self.subclient.refresh()

    def navigate_to_server(self):
        """Navigates to the specific server used in testcase"""
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client.display_name)
        

    def run(self):

        try:
            self.navigate_to_server()
            if not self.fssubclient_obj.is_subclient_exists(self.subclient_name):
                #Adding backup data as dummy because with latest SP30 changes, plans can be defined without content
                #Also the content here doenst matter as this testcase doenst perform any backups
                #It just checks if pre-post commands are set on DB
                self.log.info("Creating subclient as Subclient doesnt exist")
                self.fssubclient_obj.add_fs_subclient(self.tcinputs['BackupsetName'],
                                                      self.subclient_name, self.tcinputs['PlanName'],
                                                      backup_data = ['C:\\dummy']
                                                      )
            self.log.info("Step2.Setting Pre/Post Scan and Backup Command")
            self.set_pre_post_commands(["PreScanProcess","PostScanProcess","PreBackupProcess","PostBackupProcess"])
            self.log.info("Step3.Validating if Pre/Post Scan and Backup Command is set")
            self.vaildate_pre_post(["PreScanProcess","PostScanProcess","PreBackupProcess","PostBackupProcess"])
            self.log.info("Step4.Setting different Pre/Post Scan and Backup Command")
            self.set_pre_post_commands(["PostScanProcess","PreScanProcess","PostBackupProcess","PreBackupProcess"])
            self.log.info("Step5.Validating if Pre/Post Scan and Backup Command is set")
            self.vaildate_pre_post(["PostScanProcess","PreScanProcess","PostBackupProcess","PreBackupProcess"])
            self.log.info("Step6.Clearing Pre/Post Scan and Backup Command")
            self.clear_pre_post_commands()
            self.log.info("Step7.Validating if Clearing Pre/Post Scan and Backup Command is honoured")
            self.vaildate_pre_post([])
    
        except Exception as exception:
           handle_testcase_exception(self,exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)