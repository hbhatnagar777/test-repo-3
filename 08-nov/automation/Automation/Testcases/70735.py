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
from Web.AdminConsole.Components.panel import Backup
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
        IBMi - Backup and restore validation of pre-defined subclient *HST log from command center.
        Step1, configure BackupSet and pre-defined Subclients for TC
        Step2: On client, Re-create the file QSYS/{0}
                and delete QSYS/{1} if exists
        Step3: Run a full backup for the subclient *HST log
                and verify if it completes without failures.
        step4: Check backup logs to confirm SAVOBJ was used.
        step5: Check scan logs to confirm regular scan was used.
        Step6: On client, Create a file QHST543661 with a member.
        Step7: Run an incremental job for the subclient
                and verify it completes without failures.
        Step8: Check backup logs to confirm SAVOBJ was used.
        step9: Check scan logs to confirm regular scan was used.
        Step10: OOP Restore QSYS/QHST54366 & QSYS/QHST543661
                objects  to library QHST<TESTCASE>
        Step11: Verify client restore logs if command RSTOBJ is used.
        Step12: check restored objects and cleanup created history file objects.
        Step13: cleanup restored library on IBMi client and delete components created on CS 
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Backup and restore validation of pre-defined subclient *HST log from command center."
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.client_machine = None
        self.destlib = None
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
        self.destpath = None
        self.qhst_path = None
        self.job_id = None
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
            self.subclient_name = "*HST log"
            self.plan_name = self.tcinputs['PlanName']
            self.destlib = "QHST{0}".format(self.id)
            self.hstobj = ["QHST{0}".format(self.id), "QHST{0}1".format(self.id)]
            self.qhst_path = ["/QSYS.LIB/QHST{0}.FILE".format(self.id),
                              "/QSYS.LIB/QHST{0}1.FILE".format(self.id)]

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
        """ Create a new backupset """
        self.navigate_to_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=self.backupset_name,
                                                 plan_name=self.plan_name)

    @test_step
    def generate_client_data(self, run_count=0):
        """ Generate data on IBMi client machine """
        if run_count == 0:
            for each in self.hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))
        self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(self.hstobj[run_count]))

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
            self.log.info("Job#{0} completed successfully".format(self.job_id))

    @test_step
    def update_predefined_subclient(self):
        """
            Update IBMi subclient properties
        """
        self.RfsSubclient.update_ibmi_subclient_details(subclient_name=self.subclient_name,
                                                        backupset_name=self.backupset_name,
                                                        plan_name=self.plan_name
                                                        )
        # self.RfsSubclient.update_ibmi_subclient_details(subclient_name=self.subclient_name,
        #                                                 backupset_name=self.backupset_name,
        #                                                 include_global_exclusions=True,
        #                                                 plan_name=self.plan_name,
        #                                                 content_filters=["/test"],
        #                                                 content_exceptions=["/test/test1"],
        #                                                 save_while_active="*LIB",
        #                                                 active_wait_time=300,
        #                                                 backup_spool_file=True
        #                                                 )

    @test_step
    def restore_and_compare(self):
        """ Restore IBMi data from subclient and compare """
        self.navigate_to_subclient_tab()
        self.client_machine.manage_library(operation='delete', object_name=self.destlib)
        self.job_id = self.RfsSubclient.ibmi_restore_subclient(backupset_name=self.backupset_name,
                                                               subclient_name=self.subclient_name,
                                                               destination_path=self.client_machine.lib_to_path(
                                                                   self.destlib),
                                                               unconditional_overwrite=True,
                                                               selected_files=self.qhst_path,
                                                               restore_spool_files=True
                                                               )
        self.wait_for_job_completion()
        for each in self.hstobj:
            self.client_machine.object_existence(library_name=self.destlib,
                                                 object_name='{0}'.format(each),
                                                 obj_type='*FILE')

    @test_step
    def verify_client_logs(self, run_count=0):
        """
        Verify client logs if correct paramemter are used
        """
        if run_count == 0:
            self.log.info("Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job_id,
                                        expectedvalue="[SAVOBJ]:[OBJ({0}".format(self.hstobj[0])
                                        )
            self.log.info("Check scan logs to confirm regular scan was used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=self.job_id,
                                        expectedvalue="We are not running Scanless Backup"
                                        )
        if run_count == 1:
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job_id,
                                        expectedvalue="[SAVOBJ]:[OBJ({0}".format(self.hstobj[1])
                                        )
            self.log.info("step9: Check scan logs to confirm regular scan was used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=self.job_id,
                                        expectedvalue="We are not running Scanless Backup"
                                        )

        if run_count == 2:
            self.log.info("Verify client restore logs if command RSTOBJ is used.")
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="OBJ(QHST{0}".format(self.id)
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job_id,
                                        expectedvalue="OBJ(QHST{0}1".format(self.id)
                                        )

    @test_step
    def cleanup(self):
        """
        Cleanup the data created on client and entries created on CS
        """
        for each in self.hstobj:
            self.client_machine.delete_file_object(library='QSYS', object_name="{0}".format(each))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)

        self.navigate_to_subclient_tab()
        self.RfsSubclient.delete_backup_set(self.backupset_name)

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
            self.verify_client_logs(2)
            self.cleanup()
            self.log.info("**QHST Log subclient backup & Restore validation is COMPLETED SUCCESSFULLY**")
            self.log.info("******TEST CASE COMPLETED SUCCESSFULLY AND PASSED******")

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.log.info("Logout from command center completed successfully")
