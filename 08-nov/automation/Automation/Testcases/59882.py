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
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import time
import os
import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.DRHelper import ReplicationMain
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.Components.table import Table
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for performing azure dr cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Suspend and resume failback backup and failback replication jobs "
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.navigator = None
        self.table = None
        self.replication_group_obj = None
        self.auto_subclient = None
        self.replication_group_name = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.close_popup()
        self.navigator = self.admin_console.navigator
        self.replication_group_obj = ReplicationGroup(self.admin_console)
        self.table = Table(self.admin_console)
        self.replication_group_name = self.tcinputs['ReplicationGroupName']

        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)

    def do_failback(self, replication_group_name):
        """
        Performs and Validates a Failback Operation on the selected replication group

        Args:
            replication_group_name   (string)   --   Name of the replication group

        """
        try:
            self.replication_helper.get_details_for_validation(replication_group_name)
            destination_client_name = self.replication_helper.rt_details['Destination hypervisor']
            self.destination_client = self.auto_subclient.auto_vsainstance._create_hypervisor_object(
                destination_client_name)

            self.log.info("generating testdata in controller machine")
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_folder_name = backup_options.backup_type
            self.auto_subclient.backup_folder_name = backup_options.backup_type
            if not self.auto_subclient.testdata_path:
                self.auto_subclient.testdata_path = VirtualServerUtils.get_testdata_path(
                    self.auto_subclient.controller_machine)
                self.auto_subclient.timestamp = os.path.basename(os.path.normpath(self.auto_subclient.testdata_path))
                self.auto_subclient.auto_vsaclient.timestamp = self.auto_subclient.timestamp
            testdata_size = backup_options.advance_options.get("testdata_size", random.randint(40000, 60000))
            generate = self.auto_subclient.controller_machine.generate_test_data(self.auto_subclient.testdata_path, 3,
                                                                                 5, testdata_size)

            self.log.info("copying testdata to the destination vms")
            if not generate:
                raise Exception(generate)
            for _vm in self.replication_helper.destination_vms:
                if _vm not in self.destination_client.VMs:
                    self.destination_client.VMs = _vm
                self.destination_client.VMs[_vm].update_vm_info('All', os_info=True, force_update=True)
                self.log.info("VM selected is {0}".format(_vm))
                if len(self.destination_client.VMs[_vm].disk_list) > 0:
                    for _drive in self.destination_client.VMs[_vm].drive_list.values():
                        self.log.info("Copying Testdata to Drive {0}".format(_drive))
                        self.destination_client.copy_test_data_to_each_volume(_vm, _drive, backup_folder_name,
                                                                              self.auto_subclient.testdata_path)
            self.auto_subclient.destination_client_hvobj = self.destination_client

            self.navigator.navigate_to_replication_groups()
            self.replication_group_obj.access_group(replication_group_name)

            # performing a failback job
            job_id = (self.replication_helper
                      .perform_failback(replication_group=replication_group_name,
                                        operation_level=self.replication_helper.Operationlevel.OVERVIEW))
            time.sleep(15)
            self.suspend_resume_operation(job_id)
            time.sleep(30)

            # to login back after the job
            self.admin_console.refresh_page()
            if self.admin_console.check_if_entity_exists("xpath", '//a[contains(text(),"here")]'):
                self.admin_console.select_hyperlink("here")

            self.auto_subclient.validate_dr(replication_group_name, failback=True)

        except Exception as exp:
            self.log.exception("Exception occurred while doing a failback validation: %s", str(exp))
            raise exp

    def suspend_resume_operation(self, failback_job_id):
        """
        Suspend and resumes the backup and replication jobs of a failback operation

        Args:
            failback_job_id   (int)   --   job id of the failback operation

        """
        failback_job_manager = JobManager(failback_job_id, self.commcell)

        # suspend and resume failback backup job
        backup_active_jobs = failback_job_manager.get_filtered_jobs(
            client=self.tcinputs["ClientName"],
            current_state=['waiting', 'pending', 'running', 'suspended'],
            expected_state=['waiting', 'pending', 'running', 'suspended'],
            job_filter='backup',
            lookup_time=0.3,
            time_limit=1)

        if backup_active_jobs[0]:
            try:
                backup_job_id = backup_active_jobs[1][0]
            except Exception as exp:
                self.log.exception("Failed to get the failback backup job id")
                raise exp

            backup_job_manager = JobManager(backup_job_id, self._commcell)

            try:
                backup_job_manager.modify_job(set_status='suspend')
            except Exception as exp:
                self.log.exception("Failed to suspend job")
                raise exp

            try:
                backup_job_manager.modify_job(set_status='resume')
            except Exception as exp:
                self.log.exception("Failed to resume job")
                raise exp

            try:
                self.log.info("Getting status for the job %s", backup_job_id)
                job_details = backup_job_manager.wait_for_state(expected_state=["completed",
                                                                                "completed w/ one or more errors"])
                if not job_details:
                    raise Exception("Failback backup job didnt complete. Please check the logs")
            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp
        else:
            self.log.info("There is no backup job present for the given client")

        # suspend and resume failback replication job
        replication_active_jobs = failback_job_manager.get_filtered_jobs(
            client=self.tcinputs["ClientName"],
            current_state=['waiting', 'pending', 'running', 'suspended'],
            expected_state=['waiting', 'pending', 'running', 'suspended'],
            job_filter='replication',
            lookup_time=0.3,
            time_limit=1)

        if replication_active_jobs[0]:
            try:
                replication_job_id = replication_active_jobs[1][0]
            except Exception as exp:
                self.log.exception("Failed to get the failback backup job id")
                raise exp

            replication_job_manager = JobManager(replication_job_id, self._commcell)

            try:
                replication_job_manager.modify_job(set_status='suspend')
            except Exception as exp:
                self.log.exception("Failed to suspend job")
                raise exp

            try:
                replication_job_manager.modify_job(set_status='resume')
            except Exception as exp:
                self.log.exception("Failed to resume job")
                raise exp
        else:
            self.log.info("There is no replication job present for the given client")

        # complete the failback job
        try:
            self.log.info("Getting status for the job %s", failback_job_id)
            job_details = failback_job_manager.wait_for_state(expected_state=["completed",
                                                                              "completed w/ one or more errors"])
            if not job_details:
                raise Exception("Replication job didnt complete. Please check the logs")
        except Exception as exp:
            self.log.exception("Exception occurred in getting the job status: %s", str(exp))
            raise exp

    def run(self):
        """Main function for test case execution"""
        try:
            # checking if failover operation is done or not
            self.navigator.navigate_to_replication_groups()
            self.table.access_link(self.replication_group_name)
            sync_status = self.table.get_column_data(self.admin_console.props['header.failoverStatus'])
            for status in sync_status:
                if status.lower() not in ["failover complete", "failback failed"]:
                    self.replication_helper.do_unplanned_failover(self.replication_group_name)

            # performing a failback operation
            self.do_failback(self.replication_group_name)

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
