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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from datetime import datetime, timedelta
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.serverhelper import ServerTestCases
from Server.Scheduler import schedulerhelper
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import BlackoutWindow
from Web.Common.page_object import TestStep
from cvpysdk import schedules
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanagement_helper import JobManagementHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = """[Functional] : Basic operation window Data Management features validation at Plan level"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SECURITYANDROLES
        self.show_to_user = True
        self.config_json = config.get_config()
        self.tcinputs = {
            'planName': ''
        }
        self.server = ServerTestCases(self)
        self.navigator = None
        self.fs_helper = None
        self.options_selector = None

    def create_subclient(self, client_name=None, backupset=None):
        """Creates a subclient"""
        self.client_name = self.commcell.commserv_client.client_name if not client_name else client_name
        self.subclient_name = "subclient_" + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.subclient_content = self.options_selector.create_test_data(self.client_name)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.table.access_link(self.client_name)
        self.admin_console.access_tab("Subclients")
        self.subclient_page.add_subclient(
            self.subclient_name,
            self.tcinputs['planName'],
            [self.subclient_content],
            define_own_content=True
        )

    def get_local_time(self, clientname, delay=0):
        """Returns the current time as a datetime object in the client machine's timezone"""
        client_machine = Machine(clientname, self.commcell)
        if client_machine.os_info == "UNIX":
            command = "date -d '+{} minutes' +%Y-%m-%d\ %H:%M:%S".format(delay)
        else:
            command = '$a = Get-Date.AddMinutes({});$a.ToString("yyyy-MM-dd HH:mm:ss")'.format(delay)
        time_str = client_machine.execute_command(command).formatted_output.strip()
        time_format = "%Y-%m-%d %H:%M:%S"
        time_obj = datetime.strptime(time_str, time_format)
        return time_obj

    def job_via_plan_schedule_policy(self, schedule_properties):
        """
        Schedules a job via plan's RPO and returns its job id

        Args:
            schedule_properties (dict) : RPO to be set
            Ex:
            {
                'BackupType' : 'Full',
                'Agents'     : 'All agents',
                'Frequency'  : '1',
                'FrequencyUnit' : 'Day(s)',
                'StartTime'  : '10:30 pm',
                'ScheduleMode'  : 'Continuous',
                'AdvanceOptions': True,
                'ForceFullBackup' : (1, 'Week(s)'),
                'TimeZone': 'CommServe TimeZone',
                'DiskCache' :   True,
                'CommitEvery' : 24
            }

        Returns:
            Job Class instance of the job launched from the RPO schedule
        """
        old_schedule_ids = [schedule['schedule_id'] for schedule in self.plan.schedule_policies['data'].all_schedules]
        self.rpo.create_schedule(schedule_properties)
        self.plan.refresh()
        new_schedule_ids = [schedule['schedule_id'] for schedule in self.plan.schedule_policies['data'].all_schedules]
        schedule_id = list(filter(lambda x: x not in old_schedule_ids, new_schedule_ids))[0]
        schedule_object = schedules.Schedule(self.commcell, schedule_id=schedule_id)
        job_list = schedulerhelper.SchedulerHelper(schedule_object,
                                                   self.commcell).check_job_for_taskid(retry_count=15,
                                                                                       retry_interval=30)
        if not job_list:
            raise Exception("Job did not get triggered for the plan's schedule")

        for job_object in job_list:
            if job_object.subclient_name == self.subclient_name:
                return job_object
        raise Exception(f"Job did not get triggered for the plan's schedule on subclient {self.subclient_name}")

    @test_step
    def validate_plan_blackout_window(self, schedule_job=True):
        """
        1. Adds a plan level blackout window for 2 hrs from current time
        2. Creates a schedule using plan's RPO and sets it to current time+1min
        3. Checks if the job is queued due to this blackout window
        4. modifies the blackout window and checks if job is resumed
        5. wait until job completion
        """
        self.navigator.navigate_to_plan()
        self.table.access_link(self.tcinputs['planName'])
        local_time = self.get_local_time(self.client_name)
        next_box_time = local_time + timedelta(hours=2)
        self.rpo.click_on_edit_full_backup_window()
        self.blackout_window.select_all()

        if local_time.date() != next_box_time.date():
            first_day, first_time = local_time.strftime('%A'), [f"{local_time.strftime("%I%p")}-12am".lower()]
            second_day, second_time = next_box_time.strftime('%A'), [
                f"12am-{next_box_time.strftime("%I%p")}".lower()]
            self.log.info(f"setting blackout window at {second_time}")
            self.blackout_window.deselect_values(second_day, second_time)
        else:
            first_day, first_time = local_time.strftime('%A'), [
                f"{local_time.strftime("%I%p")}-{next_box_time.strftime("%I%p")}".lower()]
        self.log.info(f"setting blackout window at {first_time}")
        self.blackout_window.deselect_values(first_day, first_time)
        self.admin_console.click_button(id='Save')
        self.admin_console.wait_for_completion()
        self.admin_console.check_error_message()

        if schedule_job:
            job = self.job_via_plan_schedule_policy({
                'BackupType': 'Full',
                'Agents': 'All agents',
                'Frequency': '1',
                'FrequencyUnit': 'Day(s)',
                'StartTime': self.get_local_time(self.client_name, delay=10).strftime("%I:%M %p"),
                'AdvanceOptions': True,
                'TimeZone': 'Client time zone'
            })
        else:
            self.subclient = self.commcell. \
                clients.get(self.client_name). \
                agents.get("File System"). \
                instances.get("defaultinstancename"). \
                backupsets.get("defaultbackupset"). \
                subclients.get(self.subclient_name)
            job = self.subclient.backup(backup_level="Full")

        self.job_manager.job = job

        if schedule_job:
            self.log.info(f"job {self.job_manager.job.job_id} should be queued")
            self.job_manager.wait_for_state(expected_state="queued", retry_interval=10, time_limit=5,
                                            hardcheck=False)
            self.log.info(job.pending_reason)
            if f"{self.plan.plan_name} full backup window".lower() in job.pending_reason.lower():
                self.log.info("Job is queued due to plan's blackout window, JPR validated successfully")
            else:
                raise Exception("Job is not queued due to plan's blackout window")
            self.log.info("Success:%s is queued", job.job_type)
            self.log.info("Modifying the blackout window to check if the job will be running")

            self.rpo.click_on_edit_full_backup_window()
            self.blackout_window.select_all()
            self.admin_console.click_button(id='Save')
            self.admin_console.wait_for_completion()
            self.admin_console.check_error_message()

            self.log.info("successfully modified the backup window")
            self.log.info("%s should be running", job.job_type)
            self.job_manager.wait_for_state(expected_state=['running', 'completed'],
                                            hardcheck=False)

            self.log.info("Success:%s is resumed", job.job_type)
        else:
            self.log.info("Ondemand job on the subclient should not be effected for blackout window on plans")
            self.job_manager.wait_for_state(expected_state=['running', 'completed'], retry_interval=10,
                                            time_limit=5, hardcheck=False)

        self.log.info("Waiting for the %s job to complete", job.job_type)
        job.wait_for_completion(timeout=300)
        self.log.info("%s job completed successfully", job.job_type)
        self.log.info("Successfully validated blackout window on plan")

    @test_step
    def validate_blackout_window_at_higher_level(self):
        """
        1. create a cs level blackout window for the whole day
        2. create a plan backup window till next 1 hour
        3. Start a scheduled job from plan's RPO, make sure that job is queued due to cs level blackout window
        4. Remove the cs level blackout window, wait until job is completed
        """
        op_rule = self.commcell.operation_window.create_operation_window(operations=["FULL_DATA_MANAGEMENT"], name=self.name)
        self.navigator.navigate_to_plan()
        self.table.access_link(self.tcinputs['planName'])
        local_time = self.get_local_time(self.client_name)
        next_box_time = local_time + timedelta(hours=2)
        self.rpo.click_on_edit_full_backup_window()
        self.blackout_window.clear_all()

        if local_time.date() != next_box_time.date():
            first_day, first_time = local_time.strftime('%A'), [f"{local_time.strftime("%I%p")}-12am".lower()]
            second_day, second_time = next_box_time.strftime('%A'), [f"12am-{next_box_time.strftime("%I%p")}".lower()]
            self.log.info(f"setting backup window at {second_time}")
            self.blackout_window.select_values(second_day, second_time)
        else:
            first_day, first_time = local_time.strftime('%A'), [
                f"{local_time.strftime("%I%p")}-{next_box_time.strftime("%I%p")}".lower()]

        self.log.info(f"setting backup window at {first_time}")
        self.blackout_window.select_values(first_day, first_time)
        self.admin_console.click_button(id='Save')
        self.admin_console.wait_for_completion()
        self.admin_console.check_error_message()

        job = self.job_via_plan_schedule_policy({
            'BackupType': 'Full',
            'Agents': 'All agents',
            'Frequency': '1',
            'FrequencyUnit': 'Day(s)',
            'StartTime': self.get_local_time(self.client_name, delay=10).strftime("%I:%M %p"),
            'AdvanceOptions': True,
            'TimeZone': 'Client time zone'
        })
        self.job_manager.job = job
        self.log.info("Since blackout window is set at higher level, i.e, at commcell,\
         backup window should not be honoured, job should be queued")
        self.job_manager.wait_for_state(expected_state='queued',
                                        time_limit=5,
                                        hardcheck=False)

        self.log.info("Success:%s is queued", job.job_type)

        self.log.info("Deleting the commcell level blackout window to check if job resumes on plan's backup window")
        self.commcell.operation_window.delete_operation_window(op_rule.rule_id)
        self.log.info("Successfully deleted the commcell level blackout window")

        self.log.info("%s should be resumed", job.job_type)

        self.job_manager.wait_for_state(expected_state=['running', 'completed'],
                                        time_limit=5,
                                        hardcheck=False,
                                        fetch_job_state_in_validate=False)
        self.log.info("Success : %s is resumed", job.job_type)

        self.log.info("Waiting for the %s job to complete", job.job_type)
        job.wait_for_completion(timeout=300)
        self.log.info("Completed the %s job", job.job_type)
        self.log.info("Successfully validated blackout window hierarchy")

    def setup(self):
        """Setup function of this test case"""

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)
        self.options_selector = OptionsSelector(self.commcell)
        self.plan = self.commcell.plans.get(self.tcinputs['planName'])
        self.subclient_page = Subclient(self.admin_console)
        self.plan_details = Plans(self.admin_console)
        self.rpo = RPO(self.admin_console)
        self.blackout_window = BlackoutWindow(self.admin_console)
        self.create_subclient()
        self.management = JobManagementHelper(self.commcell)
        self.common_utils = CommonUtils(self.commcell)
        self.job_manager = self.common_utils.job_manager

    def run(self):
        """Run function of this test case"""
        try:
            self.validate_plan_blackout_window()
            self.log.info("Successfully validated plan level blackout window for scheduled job")
            self.validate_plan_blackout_window(schedule_job=False)
            self.log.info("Successfully validated plan level blackout window for ondemand job")
            self.validate_blackout_window_at_higher_level()
            self.log.info("Successfully validated is plan level blackout window honours higher level blackout window")
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.rpo.delete_schedule(len(self.rpo.get_schedules()))
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.table.access_link(self.client_name)
        self.admin_console.access_tab("Subclients")
        self.subclient_page.delete_subclient(self.subclient_name)
        self.options_selector.remove_directory(self.client_name, self.subclient_content)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
