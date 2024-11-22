# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.options_selector import CVEntities
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from datetime import datetime


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.jobs_page = None
        self.client1, self.client2 = None, None
        self.client1_company, self.client2_company = None, None
        self.subclient1, self.subclient2 = None, None
        self.entity_props = None
        self.entities = None
        self.reseller_userhelper = None
        self.reseller_orghelper = None
        self.reseller_commcell = None
        self.child_company = None
        self.reseller_company = None
        self.userhelper = None
        self.orghelper = None
        self.reseller_helper = None
        self.name = "Job Visibility in Reseller/Child companies"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'Client1Name': None,
            'Client2Name': None,
            'wait_time': None
        }

    def create_subclient(self, clientname, storagepolicy):
        """
        Create subclient with given client and storagepolicy.
        Returns subclient properties dict.
        """
        subclient_pattern = {
            'subclient':
                {
                    'client': clientname,
                    'storagepolicy': storagepolicy,
                    'backupset': 'defaultBackupSet',
                    'agent': "File system",
                    'instance': "defaultinstancename",
                }
        }
        try:
            return self.entities.create(subclient_pattern)['subclient']
        except Exception as e:
            self.log.info(e)

    def setup_reseller_company(self):
        self.orghelper = OrganizationHelper(self.commcell)
        self.reseller_company = 'reseller' + str(datetime.today().microsecond)
        self.orghelper.create(self.reseller_company, company_alias=self.reseller_company)
        self.orghelper.edit_company_properties({"general": {"resellerMode": True}})
        ta_name = f'{self.reseller_company}_admin'
        self.userhelper.create_user(f'{self.reseller_company}\\{ta_name}',
                                    email=f'{ta_name}@{self.reseller_company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.reseller_company + '\\Tenant Admin'])
        tu_name = f'{self.reseller_company}_user'
        self.userhelper.create_user(f'{self.reseller_company}\\{tu_name}',
                                    email=f'{tu_name}@{self.reseller_company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.reseller_company + '\\Tenant Users'])

    def setup_child_company(self):
        self.child_company = 'child_' + str(datetime.today().microsecond)
        self.reseller_commcell = Commcell(self.commcell.webconsole_hostname,
                                          f'{self.reseller_company}\\{self.reseller_company}_admin',
                                          self.inputJSONnode['commcell']['commcellPassword'])
        self.reseller_orghelper = OrganizationHelper(self.reseller_commcell)
        self.reseller_orghelper.create(self.child_company, company_alias=self.child_company)
        ta_name = f'{self.child_company}_admin'
        self.userhelper.create_user(f'{self.child_company}\\{ta_name}',
                                    email=f'{ta_name}@{self.child_company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.child_company + '\\Tenant Admin'])
        tu_name = f'{self.child_company}_user'
        self.userhelper.create_user(f'{self.child_company}\\{tu_name}',
                                    email=f'{tu_name}@{self.child_company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.child_company + '\\Tenant Users'])

    @test_step
    def setup_file_servers_to_companies(self):
        """Creates a reseller company and its child company and
        adds the given clients to each one of these companies."""
        self.setup_reseller_company()
        self.setup_child_company()
        self.client1.change_company_for_client(self.reseller_company)
        self.log.info(f"Client {self.tcinputs['Client1Name']} is migrated to {self.reseller_company}")
        self.client2.change_company_for_client(self.child_company)
        self.log.info(f"Client {self.tcinputs['Client2Name']} is migrated to {self.child_company}")

    def start_job(self, subclients=[1, 2]):
        """ starts backup job """
        if 1 in subclients:
            bkp_job1 = self.subclient1.backup("Full")
            bkp_job1.pause(True)
            self.job1 = bkp_job1.job_id
            self.log.info(f"Job {self.job1} started on subclient {self.subclient1.subclient_name}")
        if 2 in subclients:
            bkp_job2 = self.subclient2.backup("Full")
            bkp_job2.pause(True)
            self.job2 = bkp_job2.job_id
            self.log.info(f"Job {self.job2} started on subclient {self.subclient2.subclient_name}")

    @test_step
    def msp_admin_test(self):
        """Tests job visibility for MSP Admin"""
        self.start_job()
        self.admin_console.navigator.navigate_to_jobs()
        job_presence = self.jobs_page.if_table_job_exists(self.job1, search=True, clear=True)
        if not job_presence:
            raise CVTestStepFailure(f"Job {self.job1} is not visible to MSP Admin. Please check logs.")
        job_presence = self.jobs_page.if_table_job_exists(self.job2, search=True, clear=True)
        if not job_presence:
            raise CVTestStepFailure(f"Job {self.job2} is not visible to MSP Admin. Please check logs.")
        self.log.info("Both the jobs are visible to MSP Admin. ")
        self.log.info("Validated MSP Admin Cases.")
        self.commcell.job_controller.get(self.job1).kill(True)
        self.commcell.job_controller.get(self.job2).kill(True)
        self.admin_console.logout()

    @test_step
    def tenant_admin_test(self, username, job1, job2):
        """Tests job visibility for Tenant Admin"""
        # Job1 - Reseller Company
        # Job2 - Child Company
        self.start_job()
        user_company = username.split('\\')[0]
        self.admin_console.login(username=username,
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.navigator.navigate_to_jobs()
        job_mapping = [[job1, self.job1], [job2, self.job2]]
        for jm in range(2):
            job_presence = self.jobs_page.if_table_job_exists(job_mapping[jm][1], search=True, clear=True)
            if job_mapping[jm][0]:
                if not job_presence:
                    raise CVTestStepFailure(
                        f"Job {job_mapping[jm][1]} is not visible to {user_company}'s tenant admin.")
                self.log.info(f"Job {job_mapping[jm][1]} is visible to Tenant Admin of {user_company}")
            else:
                if job_presence:
                    raise CVTestStepFailure(f"Job {job_mapping[jm][1]} is visible to Tenant Admin of {user_company}")
                self.log.info(f"Job {job_mapping[jm][1]} is not visible to Tenant Admin of {user_company}")

        self.commcell.job_controller.get(self.job1).kill(True)
        self.commcell.job_controller.get(self.job2).kill(True)
        self.admin_console.logout()
        self.log.info(f"Verified MSP Admin testcase for {user_company} company.")

    def tenant_user_test(self, username, client):
        """Tests job visibility for Tenant User"""
        self.start_job(subclients=[client])
        job = {
            1: [self.job1, self.tcinputs["Client1Name"]],
            2: [self.job2, self.tcinputs["Client2Name"]]
        }
        self.admin_console.login(username=username,
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.navigator.navigate_to_jobs()
        job_presence = self.jobs_page.if_table_job_exists(job[client][0], search=True, clear=True)
        if job_presence:
            raise CVTestStepFailure(f"Job {job[client][0]} is visible to {username}\
                                                        without permissions on the {job[client][1]}")
        self.log.info(f"Job {job[client][0]} is not visible to {username} \
                                                        without permission.\n Working as expected.")
        self.log.info(f'Adding View permissions for {username} on {job[client][1]}')
        user = self.commcell.users.get(username)
        security_assoc = {
            'assoc2':
                {
                    'clientName': [job[client][1]],
                    'role': ['View']
                }
        }
        user.update_security_associations(security_assoc, "UPDATE")
        self.jobs_page.reload_jobs()
        job_presence = self.jobs_page.if_table_job_exists(job[client][0], search=True, clear=True)
        if not job_presence:
            raise CVTestStepFailure(f"Job {job[client][0]} is not visible to {username} even with permissions on the "
                                    f"{job[client][1]}")
        self.log.info(f"Job {job[client][0]} is visible to {username} with permission.\n Working as expected.")
        self.commcell.job_controller.get(job[client][0]).kill(True)
        self.admin_console.logout()
        self.log.info(f"Verified tenant user testcase for {username}.")

    def setup(self):
        self.userhelper = UserHelper(self.commcell)
        self.client1 = self.commcell.clients.get(self.tcinputs["Client1Name"])
        self.client2 = self.commcell.clients.get(self.tcinputs["Client2Name"])
        self.client1_company = self.client1.company_name
        self.client2_company = self.client2.company_name
        self.jd_wait = self.tcinputs['wait_time']
        self.setup_file_servers_to_companies()
        self.entities = CVEntities(self)
        self.entity_props = self.entities.create(["disklibrary", "storagepolicy"])
        self.subclient1 = self.create_subclient(self.tcinputs["Client1Name"],
                                                self.entity_props["storagepolicy"]["name"])['object']
        self.subclient2 = self.create_subclient(self.tcinputs["Client2Name"],
                                                self.entity_props["storagepolicy"]["name"])['object']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.jobs_page = Jobs(self.admin_console)

    def run(self):
        try:
            self.msp_admin_test()
            self.tenant_admin_test(f'{self.reseller_company}\\{self.reseller_company}_admin', True, True)
            self.tenant_admin_test(f'{self.child_company}\\{self.child_company}_admin', False, True)
            self.tenant_user_test(f'{self.reseller_company}\\{self.reseller_company}_user', 1)
            self.tenant_user_test(f'{self.child_company}\\{self.child_company}_user', 2)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            company1 = self.client1_company if self.client1_company else "Commcell"
            company2 = self.client2_company if self.client2_company else "Commcell"
            self.client1.change_company_for_client(company1)
            self.log.info(f"Client {self.tcinputs['Client1Name']} is migrated back to  {company1}")
            self.client2.change_company_for_client(company2)
            self.log.info(f"Client {self.tcinputs['Client2Name']} is migrated back to  {company2}")
            self.log.info('Deleting company {0}'.format(self.child_company))
            self.reseller_commcell.organizations.delete(self.child_company)
            self.log.info('Deleting company {0}'.format(self.reseller_company))
            self.commcell.organizations.delete(self.reseller_company)
        finally:
            self.entities.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
