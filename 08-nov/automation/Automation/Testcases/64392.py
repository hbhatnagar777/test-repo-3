# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.Setup.data_insights_guided_setup import DataInsights
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from cvpysdk.activateapps.file_storage_optimization import FsoServers
from cvpysdk.activateapps.constants import EdiscoveryConstants


class TestCase(CVTestCase):
    """Class to validate FSO Guided setup UI by configuring the solution and validating same"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Acceptance case for FSO Guided Setup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.getting_started = None
        self.data_insights = None
        self.dc_plan = None
        self.fso = None
        self.ds_name = None
        self.fs_name = None
        self.inv_name = None
        self.fso_server = None
        self.ds_obj = None
        self.ds_helper = None
        self.tcinputs = {
            'UserName': None,
            'Password': None,
            'ISName': None,
            'InventoryName': None,
            'FSOServerName': None,
            'CrawlPath': None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.getting_started = GettingStarted(self.admin_console)
            self.data_insights = DataInsights(self.admin_console)
            self.ds_helper = DataSourceHelper(self.commcell)
            self.dc_plan = "FSO Plan %s" % self.id
            self.ds_name = "Data Source %s" % self.id
            self.inv_name = self.tcinputs['InventoryName']
            self.fs_name = self.tcinputs['FSOServerName']
            self.fso = FsoServers(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @TestStep()
    def configure_fso(self):
        """Navigates to the FSO solution configure page and creates a FSO DC plan"""
        self.navigator.navigate_to_getting_started()
        self.getting_started.configure_wizard_for_solution("File storage optimization", new_guided_setup=True)
        self.data_insights.configure_wizard_for_fso(dc_plan=self.dc_plan, index_server=self.tcinputs['ISName'])

    @TestStep()
    def validate_fso_plan(self):
        """Validates the FSO plan by creating a FSO server"""
        try:
            self.fso_server = self.fso.add_file_server(
                server_name=self.fs_name, data_source_name=self.ds_name, inventory_name=self.inv_name,
                plan_name=self.dc_plan, source_type=EdiscoveryConstants.SourceType.SOURCE,
                crawl_path=[self.tcinputs['CrawlPath']])
            self.ds_obj = self.fso_server.data_sources.get(self.ds_name)
            self.wait_for_job()
        except Exception as e:
            handle_testcase_exception(self, e)

    def wait_for_job(self):
        """Waits for crawl job to complete on data source"""
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for FSO server added")
        job_id = list(jobs.keys())[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.ds_helper.monitor_crawl_job(job_id=job_id, retry_interval=30)
        self.log.info(f"Crawl job - {job_id} completed")

    @TestStep()
    def cleanup(self):
        """Cleanup deletes the DC plan and FSO server created during the testcase"""
        self.log.info(f"Deleting fso data source {self.ds_name}")
        self.fso_server.data_sources.delete(self.ds_name)
        self.log.info(f"FSO data source {self.ds_name} deleted successfully")
        self.log.info(f"Deleting FSO DC plan {self.dc_plan}")
        self.commcell.plans.delete(self.dc_plan)
        self.log.info(f"FSO plan {self.dc_plan} deleted successfully")

    def run(self):
        try:
            self.init_tc()
            self.configure_fso()
            self.validate_fso_plan()
            self.cleanup()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
