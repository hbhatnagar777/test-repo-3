from selenium.webdriver.common.by import By
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
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.replication_targets import ReplicationTargets
from Web.AdminConsole.AdminConsolePages.replication_groups import ReplicationGroup
from Web.AdminConsole.VSAPages.configure_vsa_replication_group import ConfigureVSAReplicationGroup
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from cvpysdk.policies.storage_policies import StoragePolicies
from Web.AdminConsole.Helper.DRHelper import ReplicationMain


class TestCase(CVTestCase):
    """Class for performing replication from an aux copy"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Performing replication from an aux copy"
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
        self.config_rg = None
        self.replication_group_obj = None
        self.recovery_target_obj = None
        self.storage_policy = None
        self.aux_copy = None

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
        self.replication_group_obj = ReplicationGroup(self.admin_console.driver)
        self.recovery_target_obj = ReplicationTargets(self.admin_console)
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.config_rg = ConfigureVSAReplicationGroup(self.admin_console)
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)

    def run(self):
        """Main function for test case execution"""
        try:
            # creating a new replication group with aux storage
            self.navigator.navigate_to_vm_groups()
            self.vm_group_obj.select_vm_group(self.tcinputs['SubclientName'])
            self.admin_console.driver.find_element(By.XPATH, 
                '//*[@id="cv-content-page"]/cv-tab-nav/div/div[2]/div[3]/a').click()
            self.admin_console.driver.find_element(By.XPATH, '//*[@id="moreActions"]/li/a/span').click()

            vm = self.auto_subclient.hvobj.VMs[list(self.auto_subclient.hvobj.VMs)[0]]
            if not vm.managed_disk:
                uri = vm.vm_info['properties']['storageProfile']['osDisk']['vhd']['uri']
                sa = uri.split('//')[1].partition('.')[0]
            else:
                sa = self.tcinputs['StorageAccount']

            dict_vals = {
                'hypervisor': self.auto_subclient.auto_vsaclient.vsa_client_name,
                'replication_group_name': self.auto_subclient.subclient_name + '_temp_rg',
                'vm_backupgroup': self.auto_subclient.subclient_name,
                'vms': self.auto_subclient.vm_list,
                'replication_target': self.auto_subclient.subclient_name + '_temp_rt',
                'proxy': self.auto_subclient.browse_ma[0],
                'resource_group': vm.resource_group_name,
                'region': self.tcinputs['Region'],
                'storage_account': sa,
                'storage_copy': 'Secondary',
                'dvdf': False
            }
            self.config_rg.configure_vsa_replication_group_azure(dict_vals)

            # performing a backup job
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

            # performing an aux job
            self.navigator.navigate_to_vm_groups()
            self.table.access_link(self.tcinputs['SubclientName'])
            panel_info = PanelInfo(self.admin_console, self.admin_console.props['label.summary'])
            plan = panel_info.get_details()['Plan']
            if '\n' in plan:
                plan = plan.splitlines()[0]
            policies = StoragePolicies(self.commcell)
            self.storage_policy = policies.get(plan)
            if len(self.storage_policy.copies) > 1:
                if self.storage_policy.aux_copies:
                    self.aux_copy = self.storage_policy.aux_copies[0]
                    aux_job = self.storage_policy.run_aux_copy(self.aux_copy)
                    aux_job_manager = JobManager(aux_job.job_id, self.commcell)
                    try:
                        self.log.info("Getting status for the job %s", aux_job.job_id)
                        job_details = aux_job_manager.wait_for_state(
                            expected_state=["completed", "completed w/ one or more errors"])
                        if not job_details:
                            raise Exception("Aux job didnt complete. Please check the logs")
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
            self.replication_helper.validate_replication(self.auto_subclient.subclient_name + '_temp_rg')

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

        finally:
            self.log.info("Deleting Replication Group")
            self.navigator.navigate_to_replication_groups()
            self.replication_group_obj.delete_group(self.auto_subclient.subclient_name + '_temp_rg')
            self.navigator.navigate_to_replication_targets()
            self.recovery_target_obj.action_delete(self.auto_subclient.subclient_name + '_temp_rt')

    def tear_down(self):
        """Teardown function for this test case execution"""
        # deleting the replication group
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
