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
import time

from cvpysdk.job import Job

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers


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
        self.name = "MSP Testcase: Deactivate and validation"
        self.company_name = None
        self.company_alias = None
        self.navigator = None
        self.__table = None
        self.__company_details = None
        self.MSP_obj = None
        self.file_server = None
        self.client_name = None
        self.config = get_config()
        self.tcinputs = {
            "client": "",
            "subclient": ""
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator = self.admin_console.navigator
        self.__table = Table(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)
        self.__companies = Companies(self.admin_console)
        self.MSP_obj = MSPHelper(admin_console=self.admin_console, commcell=self.commcell)
        self.file_server = FileServers(self.admin_console)

        self.client_name = self.tcinputs['client']
        self.subclient = self.tcinputs['subclient']
        self.company_name = \
            self.commcell.clients.get(self.client_name).properties['clientProps']['company']['connectName']
        self.company_alias = \
            self.commcell.clients.get(self.client_name).properties['clientProps']['company']['shortName']['domainName']

    @test_step
    def validate_restore(self):
        """Validate that restore is not working"""
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        try:
            self.file_server.restore_subclient(self.client_name, subclient_name='default')
            job_id = self.admin_console.get_jobid_from_popup()
            job = Job(self.commcell, job_id)
            if job.status != 'Failed to Start':
                raise Exception(
                    f"Since the company is deactivated, the restore job with id {job_id} should fail"
                )
        except Exception:
            self.log.info(Exception)

    @test_step
    def validate_backup(self):
        """Validate that backup is not working"""
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        job_id = self.file_server.backup_subclient(self.client_name, 'full', subclient_name='default')
        try:
            job = Job(self.commcell, job_id)
            if job.status != 'Failed to Start':
                raise Exception(
                    f"Since the company is deactivated, the job backup with id {job_id} should fail"
                )
        except Exception:
            self.log.info(Exception)

    @test_step
    def validate_activities(self):
        """Validate the deactivated entities on company's page"""
        self.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name, deactivated=True)
        enabled_activities = self.__company_details.enabled_activities()
        if enabled_activities != ['Data aging']:
            raise Exception(
                f"The enabled activities are not correct, {enabled_activities} activities are enabled"
            )

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_companies()

            self.log.info("deactivating company")
            self.__companies.deactivate_company(self.company_name)

            self.__companies.access_company(self.company_name, deactivated=True)
            deactivated_activities = self.__company_details.deactivated_activities()
            if deactivated_activities != 'Login, Backup, Restore':
                raise Exception(
                    f"The Deactivated activities doesn't match the set values, {deactivated_activities} are deactivated"
                )

            self.validate_activities()
            self.validate_backup()
            self.validate_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.navigator.navigate_to_companies()
        self.log.info("Activating Company again")
        self.__companies.activate_company(self.company_name)
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
