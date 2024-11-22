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
import datetime

from AutomationUtils.machine import Machine
from Application.CloudApps.azure_compute_helper import AzureCompute
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Office365Pages import constants


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verification of CvScale Manager for Office 365 multi app type"
        self.azure_rg = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.app_type = None
        self.users = None
        self.mailboxes = None
        self.sites = None
        self.teams = None
        self.exchange_app_name = None
        self.onedrive_app_name = None
        self.sharepoint_app_name = None
        self.teams_app_name = None
        self.input_doc_count = None
        self.O365_plan = None
        self.utils = TestCaseUtils(self)

    @test_step
    def create_client_for_agent(self, app_type):
        """Create clients for agent to verify License Usage"""
        if app_type == O365AppTypes.exchange:
            self.log.info("------------------------------------"
                          "Creating Exchange Online Application"
                          "------------------------------------")
            self.office365_obj.app_type = O365AppTypes.exchange
            self.office365_obj.constants = constants.ExchangeOnline
            self.app_name = f'ExchangeOnline{self.tcinputs["Name"]}'
            self.mailboxes = self.tcinputs["ExchangeOnlineUsers"].split(',')
        elif app_type == O365AppTypes.onedrive:
            self.log.info("-----------------------------"
                          "Creating OneDrive Application"
                          "-----------------------------")
            self.office365_obj.app_type = O365AppTypes.onedrive
            self.office365_obj.constants = constants.OneDrive
            self.app_name = f'OneDrive{self.tcinputs["Name"]}'
            self.users = self.tcinputs["OneDriveUsers"].split(',')
        elif app_type == O365AppTypes.sharepoint:
            self.log.info("-------------------------------"
                          "Creating SharePoint Application"
                          "-------------------------------")
            self.office365_obj.app_type = O365AppTypes.sharepoint
            self.office365_obj.constants = constants.SharePointOnline
            self.app_name = f'SharePoint{self.tcinputs["Name"]}'
            self.sites = dict(zip(self.tcinputs['Sites'].split(","), self.tcinputs['SitesTitle'].split(",")))
        elif app_type == O365AppTypes.teams:
            self.log.info("--------------------------"
                          "Creating Teams Application"
                          "--------------------------")
            self.office365_obj.app_type = O365AppTypes.teams
            self.office365_obj.constants = constants.Teams
            self.app_name = f'Teams{self.tcinputs["Name"]}'
            self.teams = self.tcinputs["Teams"].split(',')
        self.office365_obj.create_office365_app(name=self.app_name,
                                                global_admin=self.tcinputs['GlobalAdmin'],
                                                password=self.tcinputs['Password'])
        self.app_name = self.office365_obj.get_app_name()
        if app_type == O365AppTypes.exchange:
            self.exchange_app_name = self.app_name
        elif app_type == O365AppTypes.onedrive:
            self.onedrive_app_name = self.app_name
        elif app_type == O365AppTypes.sharepoint:
            self.sharepoint_app_name = self.app_name
        elif app_type == O365AppTypes.teams:
            self.teams_app_name = self.app_name

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('OneDrive-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@onedrive{current_timestamp}.com')

    def start_machines(self, machines_list):
        """
        verify if required machines are running or not,if not start them

        Args:
            machines_list(list)    ----    list of machines
        """
        try:
            for machine in machines_list:
                status = self.azure_compute.get_virtual_machine_status(machine)
                self.log.info('Status of the machine: %s is %s', machine, status)
                if status != "VM running":
                    self.log.info('Starting the machine: %s', machine)
                    self.azure_compute.start_virtual_machine(machine)
                    time.sleep(30)  # time to start
        except Exception:
            raise CVTestStepFailure(f'Verification of machine status failed')

    def set_workers_per_node(self, number_of_workers):
        """
        Sets the nScaleMgrWorkersPerNode key

        Args:
            number_of_workers(int)    ----   number of workers
        """
        try:
            coordinator_machine_obj = Machine(commcell_object=self.commcell, machine_name=self.tcinputs["Coordinator"])
            coordinator_machine_obj.update_registry('iDataAgent', 'nScaleMgrWorkersPerNode', str(number_of_workers),
                                                    'Dword')
            self.log.info('Number of workers set to : %s successfully', number_of_workers)
        except Exception:
            raise CVTestStepFailure(f'setting of nScaleMgrWorkersPerNode key in registry failed')

    def setup(self):
        """Setup function of this testcase"""
        self.azure_compute = AzureCompute(self)
        self.create_tenant()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name, self.inputJSONnode['commcell']['commcellPassword'])
        self.jobs = Jobs(self.admin_console)
        self.service = HubServices.office365
        self.app_type = O365AppTypes.onedrive
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.service_catalogue.start_office365_trial()
        self.navigator = self.admin_console.navigator
        self.input_doc_count = self.tcinputs["input_doc_count"]
        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)
        self.create_client_for_agent(O365AppTypes.exchange)
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_backup"])
        self.office365_obj.add_user(self.mailboxes)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.onedrive)
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_backup"])
        self.office365_obj.add_user(self.users)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.sharepoint)
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_backup"])
        self.office365_obj.add_user(self.sites)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.teams)
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_backup"])
        self.office365_obj.add_user(self.teams)

    @test_step
    def add_users(self):
        """
         adds users in content
        """
        try:
            self.office365_obj.add_user(users=self.users)
        except Exception:
            raise CVTestStepFailure(f'Adding users failed')

    @test_step
    def verify_instances_before_job(self):
        """
        verify instances before start of job in scale set
        """
        try:
            ins_count = len(self.azure_compute.get_VM_scale_set_instances_list(self.tcinputs["VM_Scale_Set"]))
            self.log.info('Number of instances running are %s before start of job', ins_count)
            if ins_count != 0:
                raise Exception("Initial Instances count is not 0")
        except Exception:
            raise CVTestStepFailure(f'verification of instances before start of job failed')

    @test_step
    def verify_instances_during_job(self, exp_count):
        """
        verify instances during job in scale set

        Args:
             exp_count(int)   ----  expected number of instances
        """
        try:
            ins_count = len(self.azure_compute.get_VM_scale_set_instances_list(self.tcinputs["VM_Scale_Set"]))
            self.log.info('Number of instances running are %s during job', ins_count)
            if ins_count != exp_count:
                raise Exception("Instances count is not %s during job", exp_count)
        except Exception:
            raise CVTestStepFailure(f'verification of instances during job failed')

    @test_step
    def verify_instances_after_job(self):
        """
        verify instances after job in scale set
        """
        try:
            ins_count = len(self.azure_compute.get_VM_scale_set_instances_list(self.tcinputs["VM_Scale_Set"]))
            self.log.info('Number of instances running are %s after job', ins_count)
            if ins_count != 0:
                raise Exception("Instances count is not 0 after job")
        except Exception:
            raise CVTestStepFailure(f'verification of instances after job failed')


@test_step
def wait_till_instances(self, operation):
    """
    waiting till instance
    Args:
        operation(str)  --  creation/deletion
    """
    try:
        self.log.info(f'waiting till instance gets into {operation} state')
        ins_list = self.azure_compute.get_VM_scale_set_instances_list(self.tcinputs["VM_Scale_Set"])
        ins_ids = self.azure_compute.get_VM_scale_set_instances_list(self.tcinputs["VM_Scale_Set"], instance_ids=True)
        attempts = 12
        while attempts != 0:
            time.sleep(30)
            status = []
            for instance in ins_list:
                sts = self.azure_compute.get_VM_scale_set_VM_instance_status(scale_set=self.tcinputs["VM_Scale_Set"],
                                                                             instance_id=ins_ids[instance])
                status.append(sts)
            if operation.lower() == "creation":
                if all(i == "Provisioning succeeded" for i in status):
                    return True
            elif operation.lower() == "deletion":
                if all(i == "Deleting" for i in status):
                    return True
            status.clear()
            attempts -= 1
    except Exception:
        raise CVTestStepFailure(f'Instances did not get into {operation} state in stipulated time')


@test_step
def wait_till_job_completion(self, job):
    """
    wait till backup or restore job completion
    Args:
        job(str)     --   job id
    """
    try:
        job_details = self.jobs.job_completion(job_id=job)
        return job_details
    except Exception:
        raise CVTestStepFailure(f'job completion failed')


@test_step
def verify_streams(self, job, exp_count):
    """
    verify streams during backup or restore job

    Args:
         job(str)   ----  job id
         exp_count(int)  ----  expected number of streams
    """
    try:
        stream_data = self.office365_obj.process_streams_tab(job_id=job)
        if len(stream_data) > exp_count or len(stream_data) == 0:
            raise Exception("Mismatch in expected streams count %s", len(stream_data))
        self.log.info('Streams verified successfully')
    except Exception:
        raise CVTestStepFailure(f'Verification of Streams failed')


@test_step
def verify_backup(self, bkp_job_details, input_count):
    """
     verification of backup
    Args:
        bkp_job_details(dict)  :  backup job details
        input_count(int)            :    input count
    """
    try:
        if int(bkp_job_details["No of objects backed up"]) != input_count:
            raise Exception("Mismatch in backed up items count")
        self.log.info('Backup verified successfully')
    except Exception:
        raise CVTestStepFailure(f'Verification of backup failed')


@test_step
def verify_browse(self):
    """
    verification of browse
    """
    try:
        rows = self.office365_obj.get_rows_from_browse()
        if rows == 0:
            raise Exception("Browse Failed, Please check index playback")
        self.log.info('Browse verified successfully')
    except Exception:
        raise CVTestStepFailure(f'Verification of browse failed')


@test_step
def verify_restore(self, rest_job_details, input_count):
    """
    verification of restore
    Args:
        rest_job_details(dict)  :    restore job details
        input_count(int)            :    input count
    """
    try:
        if int(rest_job_details["No of files restored"]) != input_count:
            raise Exception("Mismatch in restore items count")
        self.log.info('Restore verified successfully')
    except Exception:
        raise CVTestStepFailure(f'Verification of restore failed')


@test_step
def deallocate_machines(self, machines_list):
    """
    deallocating the machines

    Args:
        machines_list(list)    ----    list of machines
    """
    try:
        for machine in machines_list:
            status = self.azure_compute.get_virtual_machine_status(machine)
            self.log.info('Status of the machine: %s is %s', machine, status)
            if status != "VM deallocated":
                self.log.info('Deallocating the machine: %s', machine)
                self.azure_compute.deallocate_virtual_machine(machine)
                time.sleep(30)  # time to deallocate

    except Exception:
        raise CVTestStepFailure(f'Deallocating of machines failed')


def run(self):
    """Run function for test case execution"""
    try:
        self.verify_instances_before_job()
        self.office365_obj.goto_office365_app(self.exchange_app_name)
        exch_bkp_job_id = self.office365_obj.start_backup_job()
        self.office365_obj.goto_office365_app(self.onedrive_app_name)
        od_bkp_job_id = self.office365_obj.start_backup_job()
        self.office365_obj.goto_office365_app(self.sharepoint_app_name)
        sp_bkp_job_id = self.office365_obj.start_backup_job()
        self.office365_obj.goto_office365_app(self.teams_app_name)
        teams_bkp_job_id = self.office365_obj.start_backup_job()
        time.sleep(300)  # waiting till instance gets to running state
        if self.wait_till_instances(operation="creation"):
            self.log.info("Instances got into running state")
        time.sleep(60)  # waiting for docking
        self.verify_streams(exch_bkp_job_id, self.tcinputs["max_streams_before_backup"])
        self.verify_streams(od_bkp_job_id, self.tcinputs["max_streams_before_backup"])
        self.verify_streams(sp_bkp_job_id, self.tcinputs["max_streams_before_backup"])
        self.verify_streams(teams_bkp_job_id, self.tcinputs["max_streams_before_backup"])
        self.verify_instances_during_job(exp_count=1)
        self.azure_compute.compare_registry()
        exch_bkp_job_details = self.wait_till_job_completion(exch_bkp_job_id)
        od_bkp_job_details = self.wait_till_job_completion(od_bkp_job_id)
        sp_bkp_job_details = self.wait_till_job_completion(sp_bkp_job_id)
        teams_bkp_job_details = self.wait_till_job_completion(teams_bkp_job_id)

        self.verify_backup(exch_bkp_job_details, self.tcinputs["exch_input_count"])
        self.verify_backup(od_bkp_job_details, self.tcinputs["od_input_count"])
        self.verify_backup(sp_bkp_job_details, self.tcinputs["sp_input_count"])
        self.verify_backup(teams_bkp_job_details, self.tcinputs["teams_input_count"])

        time.sleep(360)  # waiting till instance gets deleted
        if self.wait_till_instances(operation="deletion"):
            self.log.info("Instances got deleted")
        time.sleep(120)  # waiting for deletion
        self.verify_instances_after_job()
        #
        self.office365_obj.goto_office365_app(self.exchange_app_name)
        self.verify_browse()
        self.admin_console.driver.back()
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_restore"])
        self.office365_obj.goto_office365_app(self.onedrive_app_name)
        self.verify_browse()
        self.admin_console.driver.back()
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_restore"])
        self.office365_obj.goto_office365_app(self.sharepoint_app_name)
        self.verify_browse()
        self.admin_console.driver.back()
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_restore"])
        self.office365_obj.goto_office365_app(self.teams_app_name)
        self.verify_browse()
        self.admin_console.driver.back()
        self.office365_obj.edit_streams(self.tcinputs["max_streams_before_restore"])

        self.verify_instances_before_job()

        self.office365_obj.goto_office365_app(self.exchange_app_name)
        exch_rest_job_id = self.office365_obj.start_restore_job()
        self.office365_obj.goto_office365_app(self.onedrive_app_name)
        od_rest_job_id = self.office365_obj.start_restore_job()
        self.office365_obj.goto_office365_app(self.sharepoint_app_name)
        sp_rest_job_id = self.office365_obj.start_restore_job()
        self.office365_obj.goto_office365_app(self.teams_app_name)
        teams_rest_job_id = self.office365_obj.start_restore_job()
        time.sleep(300)  # waiting till instance gets to running state
        if self.wait_till_instances(operation="creation"):
            self.log.info("Instances got into running state")
        time.sleep(
            60)  # waiting for docking            self.verify_streams(exch_rest_job_id, self.tcinputs["max_streams_before_restore"])
        self.verify_streams(od_rest_job_id, self.tcinputs["max_streams_before_restore"])
        self.verify_streams(sp_rest_job_id, self.tcinputs["max_streams_before_restore"])
        self.verify_streams(teams_rest_job_id, self.tcinputs["max_streams_before_restore"])
        self.verify_instances_during_job(exp_count=2)
        self.azure_compute.compare_registry()
        exch_rest_job_details = self.wait_till_job_completion(exch_rest_job_id)
        od_rest_job_details = self.wait_till_job_completion(od_rest_job_id)
        sp_rest_job_details = self.wait_till_job_completion(sp_rest_job_id)
        teams_rest_job_details = self.wait_till_job_completion(teams_rest_job_id)

        self.verify_restore(exch_rest_job_details, self.tcinputs["exch_input_count"])
        self.verify_restore(od_rest_job_details, self.tcinputs["od_input_count"])
        self.verify_restore(sp_rest_job_details, self.tcinputs["sp_input_count"])
        self.verify_restore(teams_rest_job_details, self.tcinputs["teams_input_count"])
        time.sleep(360)  # waiting till instance gets deleted
        if self.wait_till_instances(operation="deletion"):
            self.log.info("Instances got deleted")
        time.sleep(120)  # waiting for deletion
        self.verify_instances_after_job()
    except Exception as err:
        handle_testcase_exception(self, err)


def tear_down(self):
    """Tear Down function of this test case"""
    self.navigator.navigate_to_office365()
    self.office365_obj.delete_office365_app(self.exchange_app_name)
    self.office365_obj.delete_office365_app(self.onedrive_app_name)
    self.office365_obj.delete_office365_app(self.sharepoint_app_name)
    self.office365_obj.delete_office365_app(self.teams_app_name)
    AdminConsole.logout_silently(self.admin_console)
    Browser.close_silently(self.browser)
    self.hub_utils.deactivate_tenant(self.tenant_name)
    self.hub_utils.delete_tenant(self.tenant_name)
