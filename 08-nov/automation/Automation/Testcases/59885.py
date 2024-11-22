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
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.VSAPages.replication_targets import ReplicationTargets
from Web.AdminConsole.AdminConsolePages.replication_groups import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.DRHelper import ReplicationMain
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.configure_vsa_replication_group import ConfigureVSAReplicationGroup


class TestCase(CVTestCase):
    """Class for performing failback operation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Kill Failback operation and validate status"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.navigator = None
        self.table = None
        self.tc_hvobj = None
        self.vm_group_obj = None
        self.config_rg = None
        self.replication_group_obj = None
        self.recovery_target_obj = None
        self.replication_group_name = None
        self.auto_subclient = None

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
        self.table = Table(self.admin_console)
        self.vm_group_obj = VMGroups(self.admin_console)
        self.config_rg = ConfigureVSAReplicationGroup(self.admin_console)
        self.replication_group_obj = ReplicationGroup(self.admin_console.driver)
        self.recovery_target_obj = ReplicationTargets(self.admin_console)
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)

    def run(self):
        """Main function for test case execution"""
        try:
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
                'replication_group_name': self.auto_subclient.subclient_name + '_del_rg',
                'vm_backupgroup': self.auto_subclient.subclient_name,
                'vms': self.auto_subclient.vm_list,
                'replication_target': self.auto_subclient.subclient_name + '_del_rt',
                'proxy': self.auto_subclient.browse_ma[0],
                'resource_group': vm.resource_group_name,
                'region': self.tcinputs['Region'],
                'storage_account': sa,
                'storage_copy': self.tcinputs['StorageCopy'],
                'dvdf': True
            }
            self.config_rg.configure_vsa_replication_group_azure(dict_vals)

            # checking if failover operation is done or not
            self.navigator.navigate_to_replication_groups()
            self.table.access_link(self.replication_group_name)
            sync_status = self.table.get_column_data(self.admin_console.props['header.failoverStatus'])
            for status in sync_status:
                if status.lower() not in ["failover complete", "failback failed"]:
                    self.replication_helper.do_unplanned_failover(self.replication_group_name)

            job_id = (self.replication_helper
                      .perform_failback(replication_group=self.replication_group_name,
                                        operation_level=self.replication_helper.Operationlevel.OVERVIEW))
            time.sleep(20)

            # killing the failback operation
            job_manager = JobManager(job_id, self._commcell)
            try:
                job_manager.modify_job(set_status='kill')
            except Exception as exp:
                self.log.info(exp)
                self.status = False
                raise Exception("Failed to kill the Job")

            # validating the vm status
            time.sleep(20)
            self.admin_console.refresh_page()
            failover_status = self.table.get_column_data(self.admin_console.props['header.failoverStatus'])
            failover_status = [status for status in failover_status if 'fail' in status.lower()]
            for status in failover_status:
                if status.lower() != "failback failed":
                    raise Exception("Failover status is not failback failed")

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

        finally:
            self.log.info("Deleting Replication Group")
            self.navigator.navigate_to_replication_groups()
            self.replication_group_obj.delete_group(self.auto_subclient.subclient_name + '_del_rg')
            self.navigator.navigate_to_replication_targets()
            self.recovery_target_obj.action_delete(self.auto_subclient.subclient_name + '_del_rt')

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
