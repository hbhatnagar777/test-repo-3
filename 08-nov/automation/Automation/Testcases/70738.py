# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  Initialize TestCase class

    setup()                             --  Initial configuration for the test case

    navigate_to_client_subclient_tab()  --  Navigates to the subclient page for IBMi clients

    create_user_defined_backupset()	    --  Create a new backupset

    generate_client_data()              --  Generate data on IBMi client machine

    run_backup()                        --  Run IBMi filesystem backup job

    wait_for_job_completion()           --  wait for job completion

    update_predefined_subclient()       --  Update IBMi subclient properties

    restore_and_compare()               --  Restore IBMi data from subclient and compare

    verify_client_logs()                --  Verify client logs if correct paramemter are used

    cleanup()                           --  Perform cleanup on client machine and items created in CS

    run()                               --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()
    """Class for executing
        IBMi - Backup and restore validation of pre-defined subclient *ALLDLO from command center.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Backup and restore validation of pre-defined subclient *ALLDLO from command center."
        # Other attributes which will be initialized in
        self.client_machine = None
        self.browser = None
        self.admin_console = None
        self.display_name = None
        self.navigator = None
        self.subclient_name = None
        self.helper = None
        self.hostname = None
        self.username = None
        self.password = None
        self.RfsSubclient = None
        self.backupset_name = None
        self.Rfile_servers = None
        self.plan_name = None
        self.hstobj = None
        self.job_id = None
        self.usr_flr = None
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None,
            "VTLLibrary": None,
            "VTLPlanName": None
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
            self.Rfile_servers = FileServers(self.admin_console)
            self.RfsSubclient = Subclient(self.admin_console)
            self.display_name = self.commcell.clients.get(self.tcinputs['ClientName']).display_name
            self.backupset_name = "A_{0}".format(self.id)
            self.subclient_name = "*ALLDLO"
            self.plan_name = self.tcinputs['PlanName']
            self.usr_flr = ["A{0}".format(self.id), "A{0}1".format(self.id)]

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def navigate_to_subclient_tab(self):
        """Navigates to the subclient page for IBMi clients"""
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.display_name)
        self.admin_console.access_tab("Subclients")
        self.admin_console.wait_for_completion()

    @test_step
    def create_user_defined_backupset(self):
        """ Create a new backupset if it doesn't exist"""
        self.navigate_to_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=self.backupset_name,
                                                 plan_name=self.plan_name)

    @test_step
    def generate_client_data(self, run_count=0):
        """ Generate data on IBMi client machine """
        if run_count == 0:
            for each in self.usr_flr:
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))
            self.client_machine.populate_QDLS_data(folder_name=self.usr_flr[0], tc_id=self.id, count=5)
        else:
            self.client_machine.populate_QDLS_data(folder_name=self.usr_flr[0], tc_id="99999", count=2, delete=False)
            self.client_machine.populate_QDLS_data(folder_name=self.usr_flr[1], tc_id=self.id, count=5)

    @test_step
    def run_backup(self, backup_level):
        """ Run IBMi filesystem backup job """
        self.navigate_to_subclient_tab()
        self.job_id = self.RfsSubclient.backup_ibmi_subclient(subclient_name=self.subclient_name,
                                                              backupset_name=self.backupset_name,
                                                              backup_type=backup_level)
        self.wait_for_job_completion()

    @test_step
    def wait_for_job_completion(self):
        """ wait for job completion"""
        job_obj = self.commcell.job_controller.get(self.job_id)
        job_status = job_obj.wait_for_completion()
        self.log.info(job_status)
        if job_status == 'False':
            raise CVTestStepFailure("Job %s didn't complete successfully", self.job_id)
        else:
            self.log.info("------------------------------ JOB#{0} COMPLETED --------------------".
                          format(self.job_id))

    @test_step
    def update_predefined_subclient(self):
        """
            Update IBMi subclient properties
        """
        self.RfsSubclient.update_ibmi_subclient_details(subclient_name=self.subclient_name,
                                                        backupset_name=self.backupset_name,
                                                        plan_name=self.plan_name
                                                        )

    @test_step
    def restore_and_compare(self):
        """ Restore IBMi data from subclient and compare """
        for each in self.usr_flr:
            self.navigate_to_subclient_tab()
            src_path = "/QDLS/{0}".format(each)
            dest_path = "/QDLS/R{0}".format(each)
            self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))
            self.job_id = self.RfsSubclient.ibmi_restore_subclient(backupset_name=self.backupset_name,
                                                                   subclient_name=self.subclient_name,
                                                                   destination_path=dest_path,
                                                                   unconditional_overwrite=False,
                                                                   selected_files=[src_path]
                                                                   )
            self.wait_for_job_completion()
            self.log.info("------------------------------ RESTORE JOB#{0} COMPLETED -----------------".
                          format(self.job_id))
            self.helper.compare_ibmi_data(source_path=src_path,
                                          destination_path="{0}/{1}".format(dest_path, each))

            self.log.info("------------------------------ DATA COMPARISON COMPLETED --------------------")
            self.verify_client_logs(run_count=self.usr_flr.index(each)+2)
            self.log.info("------------------------------ RESTORE LOGS ARE VERIFIED ON IBMi ------------")

    @test_step
    def verify_client_logs(self, run_count=0):
        """
        Verify client logs if correct parameter are used
        """
        if run_count == 0:
            self.log.info("Check backup logs to confirm QDLS flag is set to true.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=self.job_id,
                                        expectedvalue="[Backup_ALLDLO_Enabled]"
                                        )

            self.log.info("Check scan logs to confirm regular scan is used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=self.job_id,
                                        expectedvalue="We are not running Scanless Backup"
                                        )
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job_id,
                                        expectedvalue="[SAVDLO]:[DLO(*FLRLVL) FLR('{0}".format(self.usr_flr[0])
                                        )
        if run_count == 1:
            self.log.info("Check backup logs to confirm QDLS flag is set to true.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=self.job_id,
                                        expectedvalue="[Backup_ALLDLO_Enabled]"
                                        )
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job_id,
                                        expectedvalue="[SAVDLO]:[DLO(*SEARCH) OWNER(*ALL) FLR('{0}".
                                        format(self.usr_flr[1])
                                        )

        if run_count == 2:
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="Restore type=3"
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="[DLO(*ALL) SAVFLR('{0}".format(self.usr_flr[0])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="RSTFLR('R{0}/{0}".format(self.usr_flr[0])
                                        )
        if run_count == 3:
            self.log.info("Verify client restore logs if command RSTLIB is used for full backup restore.")
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="Restore type=3"
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="[DLO(*ALL) SAVFLR('{0}".format(self.usr_flr[1])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="RSTFLR('R{0}/{0}".format(self.usr_flr[1])
                                        )

    @test_step
    def cleanup(self):
        """
        Cleanup the data created on client and entries created on CS
        """
        for each in self.usr_flr:
            self.client_machine.manage_folder(operation='delete', folder_name=each)
            self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))
        self.navigate_to_subclient_tab()
        # self.RfsSubclient.delete_backup_set(self.backupset_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_user_defined_backupset()
            self.update_predefined_subclient()
            self.generate_client_data(run_count=0)
            self.run_backup("FULL")
            self.verify_client_logs()
            self.generate_client_data(run_count=1)
            self.run_backup("INCREMENTAL")
            self.verify_client_logs(1)
            self.restore_and_compare()
            self.cleanup()
            self.log.info("*** *ALLDLO subclient backup & Restore validation is completed successfully **")
            self.log.info("******TEST CASE COMPLETED SUCCESSFULLY AND PASSED******")

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.log.info("Logout from command center completed successfully")