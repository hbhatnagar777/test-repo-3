# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              - initialize TestCase class
    verify_client_existence()				- Check if IBMi client entity present
    create_user_defined_backupset()			- Create a new backupset
    create_user_defined_subclient()			- Create a new Subclient
    delete_user_defined_backupset()			- Delete the specified backpset if exists
    generate_client_data_lfs()				- Generate LFS data on IBMi client machine
    generate_client_data()					- Generate data on IBMi client machine
    backup_job()							- Run a filesystem backup job
    validate_sc_defaults()					- Verify the client logs
    wait_for_job_completion()				- wait for job completion
    restore_compare()						- Restore IBMi data from subclient and compare
    delete_subclient_if_exists()			- Delete the specified subclient if exists
    cleanup()								- Perform cleanup on client machine and items created in CS
    navigate_to_subclient_tab()             - Navigate to Subclient tab of the IBMi client
    run()                                   - run function of this test case

Input Example:

    "testCases":
            {
                "59224":
                        {
                            "AgentName": "File System",
                            "PlanName":"Test-Auto",
                            "AgentName": "File System",
                            "ClientName": "Existing-client",
                            "HostName": "IBMi-host-name",
                            "TestPath": "/QSYS.LIB",
                            "UserName": <client_user>,
                            "Password": <client_password>
                        }
            }

"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsAgent
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi-CC-Validate IBMi subclient creation with SWA(*LIB) & backup and restore"
        self.helper = None
        self.browser = None
        self.display_name = None
        self.fsAgent = None
        self.fsSubclient = None
        self.backup_type = None
        self.subclient_name = None
        self.admin_console = None
        self.backupset_name = None
        self.srcdir = None
        self.destdir = None
        self.client_machine = None
        self.sub_client_details = None
        self.file_servers = None
        self.config = get_config()
        self.delimiter = None
        self.hostname = None
        self.username = None
        self.password = None
        self.navigator = None
        self.RfsSubclient = None
        self.Rfile_servers = None
        self.step = ""
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None,
            "UserName": None,
            "Password": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.file_servers = FileServers(self.admin_console)
            self.Rfile_servers = FileServers(self.admin_console)
            self.fsAgent = FsAgent(self.admin_console)
            self.fsSubclient = Subclient(self.admin_console)
            self.RfsSubclient = Subclient(self.admin_console)
            self.backup_type = Backup(self.admin_console)
            self.display_name = self.commcell.clients.get(self.tcinputs['ClientName']).display_name
            self.backupset_name = "a_{0}".format(self.id)
            self.subclient_name = "subclient_{0}".format(self.id)
            self.srcdir = "/AUT{0}".format(self.id)
            self.destdir = "/RST{0}".format(self.id)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def verify_client_existence(self):
        """Check if IBMi client entity present"""
        self.Rfile_servers.navigate_to_file_server_tab()
        if not self.file_servers.is_client_exists(server_name=self.display_name):
            raise CVTestStepFailure("IBMi client [{0}] does not exists.".format(self.display_name))
        self.Rfile_servers.access_server(self.display_name)

    @test_step
    def create_user_defined_backupset(self):
        """ Create a new backupset """
        self.navigate_to_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=self.backupset_name,
                                                 plan_name=self.tcinputs['PlanName'])

    @test_step
    def create_user_defined_subclient(self):
        """ Create a new Subclient """
        # self.navigate_to_subclient_tab()
        self.delete_subclient_if_exists()
        content = [self.client_machine.lib_to_path('TC{0}'.format(self.id)),
                   self.srcdir]

        self.RfsSubclient.add_ibmi_subclient(subclient_name=self.subclient_name,
                                             backupset_name=self.backupset_name,
                                             plan_name=self.tcinputs['PlanName'],
                                             content_paths=content,
                                             content_filters=["/tmp1", "/tmp2"],
                                             content_exceptions=["/tmp1/abc", "/tmp2/abcd"],
                                             save_while_active="*LIB"
                                             )

    @test_step
    def delete_user_defined_backupset(self):
        """ Delete the specified backpset if exists """
        self.navigate_to_subclient_tab()
        status = self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name)
        self.log.info("backupset existance is {0}".format(status))
        if status:
            self.RfsSubclient.delete_backup_set(self.backupset_name)

    @test_step
    def generate_client_data_lfs(self):
        """ Generate LFS data on IBMi client machine """
        self.client_machine.populate_lib_with_data(library_name='TC{0}'.format(self.id), tc_id=self.id)

    @test_step
    def generate_client_data(self, backup_level="full"):
        """ Generate data on IBMi client machine
            Args:
                backup_level(string)        -   Backup level to generate data
        """
        if "full" in backup_level:
            self.client_machine.populate_ifs_data(directory_name=self.srcdir,
                                                  tc_id=self.id,
                                                  count=5,
                                                  prefix="F",
                                                  delete=True)
        elif "incr" in backup_level:
            self.client_machine.populate_ifs_data(directory_name=self.srcdir,
                                                  tc_id=self.id,
                                                  count=2,
                                                  prefix="I",
                                                  delete=False)
        elif "diff" in backup_level:
            self.client_machine.populate_ifs_data(directory_name=self.srcdir,
                                                  tc_id=self.id,
                                                  count=2,
                                                  prefix="D",
                                                  delete=False)
        else:
            raise CVTestStepFailure("Backup level %s is not valid", backup_level)

    @test_step
    def backup_job(self, backup_level):
        """ Run IBMi filesystem backup job """
        # self.navigate_to_subclient_tab()
        jobid = self.RfsSubclient.backup_subclient(subclient_name=self.subclient_name,
                                                   backupset_name=self.backupset_name,
                                                   backup_type=backup_level)
        self.wait_for_job_completion(jobid)
        return jobid

    @test_step
    def validate_sc_defaults(self, jobid):
        """ Verify the client logs """
        self.helper.verify_sc_defaults(jobid)

    @test_step
    def wait_for_job_completion(self, job_id):
        """ wait for job completion"""
        job_obj = self.commcell.job_controller.get(job_id)
        job_status = job_obj.wait_for_completion()
        self.log.info(job_status)
        if job_status == 'False':
            raise CVTestStepFailure("Job %s didn't complete successfully", job_id)
        else:
            self.log.info("Job#{0} completed successfully".format(job_id))

    @test_step
    def restore_compare(self, level="full"):
        """ Restore IBMi data from subclient and compare """
        # self.navigate_to_subclient_tab()
        self.client_machine.remove_directory(directory_name=self.destdir)
        self.client_machine.create_directory(directory_name=self.destdir)
        files_to_restore = ["{0}/F{1}0.txt".format(self.srcdir, self.id),
                            "{0}/F{1}1.txt".format(self.srcdir, self.id),
                            "{0}/F{1}2.txt".format(self.srcdir, self.id),
                            "{0}/F{1}3.txt".format(self.srcdir, self.id),
                            "{0}/F{1}4.txt".format(self.srcdir, self.id)]
        if "incr" in level:
            files_to_restore.append("{0}/I{1}0.txt".format(self.srcdir, self.id))
            files_to_restore.append("{0}/I{1}1.txt".format(self.srcdir, self.id))

        job_id = self.RfsSubclient.ibmi_restore_subclient(backupset_name=self.backupset_name,
                                                          subclient_name=self.subclient_name,
                                                          destination_path=self.destdir,
                                                          unconditional_overwrite=True,
                                                          selected_files=files_to_restore,
                                                          restore_spool_files=True
                                                          )
        self.wait_for_job_completion(job_id=job_id)
        self.helper.compare_ibmi_data(source_path="{0}/*".format(self.srcdir),
                                      destination_path="{0}/*".format(self.destdir))

    @test_step
    def delete_subclient_if_exists(self):
        """ Delete the specified subclient if exists """
        # self.navigate_to_subclient_tab()
        self.RfsSubclient.delete_subclient(subclient_name=self.subclient_name,
                                           backupset_name=self.backupset_name)

    @test_step
    def cleanup(self):
        """ Perform cleanup on client machine and items created in CS"""
        self.client_machine.remove_directory(self.destdir)
        self.client_machine.remove_directory(self.srcdir)
        self.client_machine.manage_library(operation='delete', object_name='TC{0}'.format(self.id))
        self.navigate_to_subclient_tab()
        self.RfsSubclient.delete_subclient(subclient_name=self.subclient_name,
                                           backupset_name=self.backupset_name)
        self.RfsSubclient.delete_backup_set(self.backupset_name)

    @test_step
    def navigate_to_subclient_tab(self):
        """Navigates to the subclient page for IBMi clients"""
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.display_name)
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    def run(self):
        try:
            self.verify_client_existence()
            self.navigate_to_subclient_tab()
            self.delete_user_defined_backupset()
            self.create_user_defined_backupset()
            # self.delete_subclient_if_exists()  
            self.create_user_defined_subclient()
            self.generate_client_data()
            self.generate_client_data_lfs()
            self.validate_sc_defaults(self.backup_job(self.backup_type.BackupType.FULL))
            self.restore_compare(level="full")
            self.generate_client_data("incr")
            self.navigate_to_subclient_tab()
            self.backup_job(self.backup_type.BackupType.INCR)
            self.restore_compare(level="incr")
            self.cleanup()
            self.log.info("**IBMi - BACKUPSET MANAGEMENT, SUBCLIENT MANAGEMENT, BACKUP OPERATION,  "
                          "RESTORE OPERATION FROM COMMAND CENTER HAS COMPLETED SUCCESSFULLY**")
            self.log.info("******TEST CASE COMPLETED SUCCESSFULLY AND PASSED******")

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.log.info("Logout from command center completed successfully")
