# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: Replication with Auto proxy

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        "replication_group": "Group_1"
}
"""

from cvpysdk.drorchestration import replication_groups
from DROrchestration import PlannedFailover
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from cvpysdk.drorchestration.drjob import DRJob


class TestCase(CVTestCase):
    """Replication with Auto Proxy Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Replication with Auto proxy"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "replication_group": None
        }

        self.utils = None
        self.group_name = None
        self.admin_console = None
        self.replication_group = None
        self.group_details = None
        self.client = None
        self.recovery_target = None
        self.target_details = None
        self.replication_helper = None
        self.planned_failover = None
        self.proxies_destination = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""

        self.utils = TestCaseUtils(self)
        self.group_name = self.tcinputs['replication_group']

        Replication_group = self.commcell.replication_groups.get(self.group_name)
        self.client = Replication_group.source_client
        self.recovery_target = Replication_group.recovery_target

        self.target_details = self.commcell.recovery_targets.get(self.recovery_target)
        self.planned_failover = PlannedFailover(self.commcell, self.group_name)
        self.proxies_destination = self.planned_failover.destination_auto_instance.proxy_list

    @test_step
    def check_recovery_target_proxy(self):
        """check recovery target proxy as automatic
        Note : Proxy list will be '' if automatic is selected
        """
        check_proxy = self.target_details.access_node
        expected_proxy = ''
        self.log.info("Validate recovery target proxy as automatic")
        ReplicationHelper.assert_comparison(check_proxy, expected_proxy)
        self.log.info("Successfully validate recovery target proxy as automatic")

    @test_step
    def proxy_check_planned_failover(self, retain_blob=True):
        """check failover replication proxy"""
        self.login()
        dr_jobid = self.replication_helper.perform_planned_failover(self.group_name, retain_blob,
                                                                    operation_level=self.replication_helper.Operationlevel.GROUP)
        self.logout()
        job_obj = self.commcell.job_controller.get(dr_jobid)
        self.log.info("waiting for planned failover job to complete")
        job_obj.wait_for_completion()
        self.log.info("planned failover at group level completed")

        """last synced job : Planned failover"""
        dr_job = DRJob(self.commcell, dr_jobid)
        for source in dr_job.get_phases():
            rep_job = 0
            phases = dr_job.get_phases().get(source, [])
            for phase in phases:
                if phase.get('phase_name').name == 'REPLICATION' and phase.get('job_id'):
                    rep_job = phase.get('job_id')
                    break
            if rep_job:
                rep_job_obj = self.commcell.job_controller.get(rep_job)
                get_vm_list = rep_job_obj.get_vm_list()
                for vmlist in get_vm_list:
                    access_node = vmlist['Agent']
                    vmname = vmlist['vmName']
                    self.log.info("Verifying proxy used in replication for VM "f'{vmname}'" is in destination hypervisor")
                    ReplicationHelper.assert_includes(access_node, self.proxies_destination)
                    self.log.info("successfully verified proxy for VM "f'{vmname}'" present in destination hypervisor")

    @test_step
    def proxy_check_failback(self):
        """check failback replication proxy"""
        self.login()
        dr_jobid = self.replication_helper.perform_failback(replication_group=self.group_name,
                                                            operation_level=self.replication_helper.Operationlevel.GROUP)
        self.logout()
        job_obj = self.commcell.job_controller.get(dr_jobid)
        self.log.info("waiting for failback job to complete")
        job_obj.wait_for_completion()
        self.log.info("failback at group level completed")

        """last Backup job : failback"""
        dr_job = DRJob(self.commcell, dr_jobid)
        for source in dr_job.get_phases():
            bkp_job = 0
            phases = dr_job.get_phases().get(source, [])
            for phase in phases:
                if phase.get('phase_name').name == 'BACKUP' and phase.get('job_id'):
                    bkp_job = phase.get('job_id')
                    break
            if bkp_job:
                bkp_job_obj = self.commcell.job_controller.get(bkp_job)
                get_vm_list = bkp_job_obj.get_vm_list()
                for vmlist in get_vm_list:
                    access_node = vmlist['Agent']
                    vmname = vmlist['vmName']
                    self.log.info("Verifying proxy used for Backup of DR VM "f'{vmname}'" is in destination hypervisor")
                    ReplicationHelper.assert_includes(access_node, self.proxies_destination)
                    self.log.info("successfully verified backup proxy of DR VM "f'{vmname}'" present in destination hypervisor")

    def run(self):
        """Runs the testcase in order"""
        try:
            self.check_recovery_target_proxy()
            self.proxy_check_planned_failover()
            self.proxy_check_failback()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
