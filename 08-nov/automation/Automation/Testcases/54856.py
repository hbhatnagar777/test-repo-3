# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""
Main file for executing this test case
This test case verifies that the workflow "Disaster recovery backup" runs a DR backup job and the
backup job completes successfully without errors and with valid data.
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import commonutils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Databases.db_instances import DBInstances, OracleInstance
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This automation verifies that "Migrate to cloud" feature works for "Oracle DB to Azure" from admin console"""
    PASSWORD = "######"
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Migrate DB to cloud - Oracle DB to Azure cloud'
        self.tcinputs = {
            'recovery_target': None,
            'template': None,
            'vm_size': None,
            'proxy_client': None
        }
        self.browser = None
        self.vm_name = None
        self.admin_console = None

    def init_tc(self):
        self.vm_name = 'Orac2Azu' + commonutils.get_random_string(length=4, lowercase=False)
        self.log.info('Azure VM which will be created for the run [{0}]'.format(self.vm_name))

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()
        self.admin_console.navigator.navigate_to_db_instances()
        instances = DBInstances(self.admin_console)
        db_type = DBInstances.Types.ORACLE
        instances.select_instance(db_type, self.tcinputs.get('instance'))

    @test_step
    def migrate_oracle_db_to_azure(self):
        """Configures all the necessary inputs to the Migration Modal"""
        oracle_instance = OracleInstance(self.admin_console)
        migrate = oracle_instance.configure_migrate_to_cloud(OracleInstance.MigrationVendor.AZURE)
        migrate.set_vm_name(self.vm_name)
        migrate.set_username(self.vm_name)
        migrate.set_password(TestCase.PASSWORD)
        migrate.set_confirm_password(TestCase.PASSWORD)
        migrate.set_recovery_target(self.tcinputs['recovery_target'])
        migrate.set_template(self.tcinputs['template'])
        migrate.set_size(self.tcinputs['vm_size'])
        migrate.set_proxy(self.tcinputs['proxy_client'])
        migrate.submit()
        return self.admin_console.get_jobid_from_popup()

    def wait_for_job_completion(self, job_id):
        self.log.info('Migration job [%s] has been started' % str(job_id))
        job_obj = JobManager(job_id, self.commcell)
        try:
            assert job_obj.wait_for_state(expected_state=['completed'], retry_interval=30, time_limit=120) is True
        except AssertionError:
            raise Exception("Job is not completed successfully")
        self.log.info('***** Oracle DB to Azure migration job completed successfully *****')

    def run(self):
        """Contains the core test case logic and it is the one executed"""
        try:
            self.init_tc()
            job_id = self.migrate_oracle_db_to_azure()
            self.wait_for_job_completion(job_id)

        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)






