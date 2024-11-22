from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure
from Server.Plans.planshelper import PlansHelper
from Server.organizationhelper import OrganizationHelper
from cvpysdk.subclient import Subclients
from random import randint
from time import sleep

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[CC]: Server plan acceptance testcase"
        self.tcinputs = {
            "file_server": ""
        }

    def setup(self):
        """Setup function of this test case"""
        # set plan name and get available storage pool
        self.plan_name = f"TC 70556 PLAN - {str(randint(0, 100000))}"
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.storage_name = self.sdk_plans_helper.get_storage_pool()
        
        # job controller
        self.job_controller = self.commcell.job_controller

        # file server details
        self.file_server_name = self.tcinputs['file_server']
        self.log.info(f'Provided FS Client => {self.file_server_name}')

        # kill active jobs on client
        old_jobs = self.job_controller.active_jobs(client_name=self.file_server_name)
        for job in old_jobs.keys():
            self.log.info(f'Killing job [{job}] on client [{self.file_server_name}]...')
            self.job_controller.get(job_id=job).kill(wait_for_job_to_kill=True)

        # get default subclient and remove plan association
        self.default_subclient = Subclients(self.commcell.clients.get(self.file_server_name).agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
        self.default_subclient.plan = None

        # login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        # required objects
        self.plans = Plans(self.admin_console)
        self.rpo = RPO(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(f'Creating Server Plan [{self.plan_name}] using storage: {self.storage_name}...')
            self.navigator.navigate_to_plan()
            self.plans.create_server_plan(plan_name=self.plan_name, storage={'pri_storage': self.storage_name, 'pri_ret_period':'1', 'ret_unit':'Day(s)'})
            self.admin_console.wait_for_completion()

            self.log.info('Setting RPO to 5 minutes...')
            schedule_index = self.rpo.get_schedule_index('Incremental')[0]
            self.rpo.edit_schedule(index=schedule_index, new_values={'Frequency' : '5', 'FrequencyUnit' : 'Minute(s)'})

            self.log.info('Updating backup content and disabling Backup System State...')
            content = {
                "windowsIncludedPaths": ["Desktop"],
                "unixIncludedPaths": ["Music"],
                "backupSystemState": False
            }
            self.commcell.plans.refresh()
            self.commcell.plans.get(self.plan_name).update_backup_content(content)

            self.log.info('Associating plan to file server...')
            self.default_subclient.plan = self.plan_name

            # validate plan schedule triggers job on file server client at least 3 times
            self.navigator.navigate_to_jobs()
            
            num_jobs = 3
            while num_jobs > 0:
                self.check_if_plan_schedule_triggers_job()
                num_jobs -= 1

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        if self.default_subclient:
            self.default_subclient.plan = None
            self.sdk_plans_helper.cleanup_plans('TC 70556 PLAN')
            
    @test_step
    def check_if_plan_schedule_triggers_job(self):
        """Check if plan schedule triggers job"""
        self.log.debug('Killing active jobs on file server client...')
        OrganizationHelper(commcell=self.commcell)._kill_active_jobs_on_client(client_name=self.file_server_name, wait_before_kill=0)
        
        self.log.info('Waiting for plan to trigger backup job on file server...')
        timeout = 360  # Max 6 minutes
        while timeout > 0:
            sleep(10)
            new_jobs = self.job_controller.active_jobs(client_name=self.file_server_name, job_filter='Backup')
            if new_jobs:
                self.log.info('Backup job triggered successfully.')
                self.log.info(f'Backup job details: {new_jobs}')
                break
            timeout -= 10
        else:
            raise CVTestStepFailure('Backup job did not start within the specified time.')
        
        self.log.debug('Validating if backup job triggered by correct plan...')
        job_ids = list(new_jobs.keys())
        if len(job_ids) > 1:
            raise CVTestStepFailure('Multiple jobs found for client. Expected only 1 job. Cannot proceed with validation.')
        
        backup_job_id = job_ids[0]
        self.log.debug(f'Found backup job ID => {backup_job_id}')
        job = self.job_controller.get(job_id=backup_job_id)
        plan_name = job._get_job_details()['jobDetail']['generalInfo'].get('plan', {}).get('planName')
        
        if not plan_name:
            self.log.debug(f'Job details: {job._get_job_details()}')
            raise CVTestStepFailure('Plan name not found in job details. Cannot proceed with validation.')
        
        if plan_name.lower() != self.plan_name.lower():
            raise CVTestStepFailure(f'Backup job triggered with different plan. Plan Name: [{plan_name}] Expected: [{self.plan_name}]')

        self.log.info(f'Backup job [{backup_job_id}] triggered successfully by plan [{self.plan_name}]. Waiting for job to complete...')
        self.log.debug('NOTE: The testcase does not consider if the backup job is successful or not. It only validates if the job is triggered and if its by the correct plan.')
        job.wait_for_completion(timeout=1)
        
        self.log.info('Plan schedule triggered job successfully.')
        