# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify Licensing : Virtual Machine Replication License Usage in DR VM Category

Sample input:
"58824": {
            "ClientName": "hypervisor",
            "vm_names_to_backup": ["vm"],
            "recovery_target":"test-3",
            "storage_name" : "Storage1"
       }

"""
from time import sleep

from Server.Scheduler.schedulerhelper import SchedulerHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.DR.virtualization_replication import _Target

from Web.AdminConsole.Reports.Custom import viewer

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test case to verify Licensing : Virtual Machine Replication License Usage in DR VM
    Category"""
    test_step = TestStep()

    # strings repeatedly used, making them constants
    _SLA_STATUS = 'SLA status'
    _REPLICATION_GROUP = 'Replication group'
    _STATUS = 'Status'
    _GROUP_NAME = 'Group name'
    _SOURCE = 'Source'
    _DESTINATION = 'Destination'
    _TYPE = 'Type'
    _STATE = 'State'

    def setup(self):
        """Initialize required variables/inputs"""
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.vm_names_to_backup = self.tcinputs["vm_names_to_backup"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.storage_name = self.tcinputs["storage_name"]

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Licensing : Virtual Machine Replication License Usage in DR VM Category"
        self.vitualization_group_name = "Auto_vitualization_group_58824"
        self.source_hypervisor = None
        self.vm_names_to_backup = None
        self.recovery_target = None
        self.storage_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.replication_groups = None
        self.replication_details = None
        self.report_viewer = None
        self.manage_report = None

    def init_commandcenter(self):
        """Initialize browser and redirect to page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.replication_groups = ReplicationGroup(self.admin_console)
            self.replication_details = ReplicationDetails(self.admin_console)
            self.manage_report = ManageReport(self.admin_console)
            wc = WebConsoleAdapter(self.admin_console, self.browser)
            self.report_viewer = viewer.CustomReportViewer(self.admin_console)

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def configure_vitualization_group(self):
        """Create a vitualization replication group"""
        try:
            self.navigator.navigate_to_replication_groups()
            vitualization_grp = self.replication_groups.configure_vmware()
            vitualization_grp.add_default_group(self.vitualization_group_name,
                                                self.source_hypervisor,
                                                self.vm_names_to_backup,
                                                self.recovery_target,
                                                self.storage_name)
            self.log.info('Replication group created successfully')
        except Exception as err:
            raise CVTestStepFailure(err)

    @test_step
    def get_license_summary_data(self):
        """
        Getting DR VM license usage
        Returns: purchased and used license count
        """
        self.admin_console.navigator.navigate_to_reports()
        self.manage_report.access_report('License summary')
        self.admin_console.select_hyperlink('Recalculate')
        sleep(5)
        data_table = viewer.DataTable("Virtualization Licenses")
        self.report_viewer.associate_component(data_table)
        data = data_table.get_table_data()
        index = data['License'].index('DR VM')
        return data['Purchased'][index], data['Used'][index]

    @test_step
    def verify_vitualization_group_exists(self):
        """Verify vitualization replication group exists in Replication Groups page"""
        self.admin_console.refresh_page()
        if not self.replication_groups.has_group(self.vitualization_group_name):
            raise CVTestStepFailure(
                f"Replication group [{self.vitualization_group_name}] doesnt exist")
        self.log.info("Verified replication group[%s] created successfully!",
                      self.vitualization_group_name)

    @test_step
    def delete_vitualization_group(self):
        """Delete replication group"""
        self.navigator.navigate_to_replication_groups()
        if self.replication_groups.has_group(self.vitualization_group_name):
            self.replication_groups.delete_group(self.vitualization_group_name)
            self.log.info("Replication[%s] group deleted!", self.vitualization_group_name)
            return True
        else:
            self.log.info("Replication group [%s] does not exist!",
                          self.vitualization_group_name)
        return False

    def wait_for_sync(self):
        """Wait for sync up, during waiting period page should not timeout, so refresh the page
        every 2 minutes"""
        self.log.info("Wait for sync up for 5 mins")
        sleep(120)
        self.admin_console.refresh_page()
        sleep(120)
        self.admin_console.refresh_page()
        sleep(60)

    @test_step
    def add_replication_pair(self, orig_used):
        """Add Replication group and verify license usage"""
        self.configure_vitualization_group()
        self.verify_vitualization_group_exists()
        self.wait_for_backup_job()
        self.wait_for_replication_job()
        new_purchased, new_used = self.get_license_summary_data()
        if new_used <= orig_used:
            raise CVTestStepFailure(
                "After creation of replication group used license didnt increase,"
                f"Old used {orig_used} new used [{new_used}]"
            )
        return new_used

    @test_step
    def wait_for_backup_job(self):
        """Wait for backup to complete"""
        _agent = self.client.agents.get('virtual server')
        _backupset = _agent.backupsets.get('defaultBackupSet')
        _subclient = _backupset.subclients.get(self.vitualization_group_name)
        self.log.info("Wait for 3 minutes for jobs to trigger")
        sleep(180)
        job_id = _subclient.find_latest_job().job_id
        self.log.info(f"Waiting for Backup job id [{job_id} to complete")
        job_obj = self.commcell.job_controller.get(job_id)
        job_obj.wait_for_completion()
        if job_obj.status != 'Completed':
            raise CVTestStepFailure("Job[%s] failed" % job_id)

    @test_step
    def wait_for_replication_job(self):
        """wait for replication job to complete"""
        self.log.info("Wait for 2 minutes")
        sleep(120)
        schedule_name = self.replication_groups.get_schedule_name_by_replication_group(
            self.vitualization_group_name)
        schedule_obj = self.client.schedules.get(schedule_name)
        schedule_helper = SchedulerHelper(schedule_obj, self.commcell)
        job_obj = schedule_helper.get_jobid_from_taskid()
        self.log.info(f"Waiting for replication job id [{job_obj.job_id} to complete")
        job_obj.wait_for_completion()
        sleep(5)

    @test_step
    def disable_replication_pair(self, current_used):
        """disable Replication group and verify license usage"""
        self.navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(self.vitualization_group_name)
        self.replication_details.disable_replication_group()
        new_purchased, used_after_disable = self.get_license_summary_data()
        if used_after_disable >= current_used:
            raise CVTestStepFailure(
                "After disabling replication group used license didnt decrease,"
                f"Old used {current_used} after disabled [{used_after_disable}]"
            )
        return used_after_disable

    @test_step
    def enable_replication_pair(self, current_used):
        """disable Replication group and verify license usage"""
        self.navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(self.vitualization_group_name)
        self.replication_details.enable_replication_group()
        new_purchased, used_after_enable = self.get_license_summary_data()
        if used_after_enable <= current_used:
            raise CVTestStepFailure(
                "After enabling replication group used license didnt increase,"
                f"Old used {current_used} after enabled [{used_after_enable}]"
            )
        return used_after_enable

    @test_step
    def delete_replication_pair(self, current_used):
        """Delete group and verify count remains same as"""
        if not self.delete_vitualization_group():
            raise CVTestStepFailure(
                f"Group {self.vitualization_group_name} doesnt exist to delete"
            )
        new_purchased, used_after_delete = self.get_license_summary_data()
        if used_after_delete >= current_used:
            raise CVTestStepFailure(
                "After deleting replication group used license didnt decrease,"
                f"Old used {current_used} after delete [{used_after_delete}]"
            )
        return used_after_delete

    def run(self):
        """Starting test case steps"""
        try:
            self.init_commandcenter()
            if self.delete_vitualization_group():
                # if group exists and deleted, wait for schedules/plans to sync once deleted
                self.wait_for_sync()
            orig_purchased, orig_used = self.get_license_summary_data()
            new_used = self.add_replication_pair(orig_used)
            used_after_disable = self.disable_replication_pair(new_used)
            used_after_enable = self.enable_replication_pair(used_after_disable)
            self.delete_replication_pair(used_after_enable)

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
