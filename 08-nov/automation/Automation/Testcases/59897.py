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
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.DRHelper import ReplicationMain


class TestCase(CVTestCase):
    """Class for performing replication with static ip and snapshots deleted"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Performing replication from a backupjob with a static IP and Integrity " \
                    "snapshot deleted"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.replication_helper = None
        self.navigator = None
        self.vm_group_obj = None
        self.table = None
        self.auto_subclient = None
        self.nic = None

    def setup(self):
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
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.nic = self.tcinputs['NIC']
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)

    def run(self):
        """Main function for test case execution"""
        try:
            self.replication_helper.get_details_for_validation(self.tcinputs['ReplicationGroupName'])
            self.tc_hvobj = self.auto_subclient.auto_vsainstance._create_hypervisor_object()
            for vm_name in self.replication_helper.source_vms:
                if vm_name not in self.tc_hvobj.VMs:
                    self.tc_hvobj.VMs = vm_name
                vm = self.tc_hvobj.VMs[vm_name]
                vm.make_nic_static(self.nic)
                vm.add_nic(self.nic)
                vm.delete_snapshots()
                time.sleep(30)

            # doing replication from backup copy
            self.navigator.navigate_to_vm_groups()
            backup_jobid = self.vm_group_obj.action_backup_vm_groups(self.tcinputs["SubclientName"],
                                                                     Backup.BackupType.INCR)
            backup_job_manager = JobManager(backup_jobid, self.commcell)

            try:
                self.log.info("Getting status for the job %s", backup_jobid)
                job_details = backup_job_manager.wait_for_state(
                    expected_state=["completed", "completed w/ one or more errors"])
                if not job_details:
                    raise Exception("Backup job didnt complete. Please check the logs")
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
                try:
                    replication_job_id = active_jobs[1][0]
                except Exception as exp:
                    self.log.exception("Failed to get the replication job id")
                    raise exp
                rep_job_manager = JobManager(replication_job_id, self._commcell)
                try:
                    self.log.info("Getting status for the job %s", replication_job_id)
                    job_details = rep_job_manager.wait_for_state(expected_state=["completed",
                                                                                 "completed w/ one or more errors"])
                    if not job_details:
                        raise Exception("Replication job didnt complete. Please check the logs")
                except Exception as exp:
                    self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                    raise exp
            else:
                self.log.info("There is no replication job present for the given client")

            # validate the replication
            self.replication_helper.validate_replication(self.tcinputs["ReplicationGroupName"])

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

        finally:
            # removing the NIC
            for vm_name in self.replication_helper.source_vms:
                vm = self.tc_hvobj.VMs[vm_name]
                vm.remove_nic(self.nic)
                vm.make_nic_dynamic(self.nic)

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
