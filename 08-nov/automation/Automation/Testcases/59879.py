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
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table


class TestCase(CVTestCase):
    """Class for performing azure dr cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Incremental backup, Kill replication job and check status"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.navigator = None
        self.vm_group_obj = None
        self.table = None

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
        self.vm_group_obj = VMGroups(self.admin_console)
        self.table = Table(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        # Kill replication job and check status
        try:
            self.navigator.navigate_to_vm_groups()
            backup_jobid = self.vm_group_obj.action_backup_vm_groups(self.tcinputs["SubclientName"],
                                                                     Backup.BackupType.INCR)
            backup_job_manager = JobManager(backup_jobid, self.commcell)

            try:
                self.log.info("Getting status for the job %s", backup_jobid)
                job_details = backup_job_manager.wait_for_state(
                    expected_state=["completed", "completed w/ one or more errors"])
                if not job_details:
                    raise Exception("Replication job didnt complete. Please check the logs")
            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp

            time.sleep(30)
            active_jobs = backup_job_manager.get_filtered_jobs(
                              client=self.tcinputs["ClientName"],
                              current_state=['waiting', 'pending', 'running', 'suspended'],
                              expected_state=['waiting', 'pending', 'running', 'suspended'],
                              job_filter='replication',
                              lookup_time=0.3,
                              time_limit=1)

            if active_jobs[0]:
                replication_job_id = active_jobs[1][0]
                rep_job_manager = JobManager(replication_job_id, self._commcell)
                try:
                    rep_job_manager.modify_job(set_status='kill')
                except Exception as exp:
                    self.log.info(exp)
                    self.status = False
                    raise Exception("Failed to kill the Job")
            else:
                self.log.info("There is no replication job present for the given client")

            time.sleep(20)
            self.navigator.navigate_to_replication_groups()
            self.table.access_link(self.tcinputs['ReplicationGroupName'])
            sync_status = self.table.get_column_data(self.admin_console.props['header.syncStatus'])
            sync_status = [status for status in sync_status if 'sync' in status.lower()]
            for status in sync_status:
                if status.lower() != "sync pending":
                    raise Exception("Sync status is not sync pending")

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
