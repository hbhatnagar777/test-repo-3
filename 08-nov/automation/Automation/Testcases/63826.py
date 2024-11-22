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
    __init__()                                            --  initialize TestCase class
    self.init_commandcenter()                             --  Initialize pre-requisites
    self.verify_entity_excluded()                         -- Verify server is excluded properly
    self.verify_entity_excluded()                        -- Verify server is excluded properly
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "63826":
                        {
                            "ClientName"        : "Fs_client_Name",
                            "ClientName1"       : "Fs_client_Name",
                            "AgentName"         : "Agent_name",
                            "BackupsetName"     : "BackupSet_NAME",
                            "SubclientName"     : "Subclient_Name",
                            "SubclientName1"    : "Subclient_Name",
                            "MUserName"			: "Machine_name",
                            "MPassword"			: "machine_cred"
                        }
            }

"""
import time
from datetime import datetime
from time import sleep

from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils

from FileSystem.FSUtils.fshelper import FSHelper

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.sla import WebSla
from Web.WebConsole.Reports.navigator import Navigator
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.adminconsole import AdminConsole

_CONFIG = get_config()


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.exclude_reason = None
        self.exclude_machine = None
        self.subclient1 = None
        self.backupset1 = None
        self.agent1 = None
        self.client1 = None
        self.web_adapter = None
        self.name = "SLA validation for exclude categories in Command Center"
        self.browser: Browser = None
        self.navigator: Navigator = None
        self.utils: TestCaseUtils = None
        self.custom_report_utils = CustomReportUtils(self)
        self.admin_console = None
        self.sla = None

    def init_tc(self):
        """ initialize the Testcase object"""
        try:
            self.utils = TestCaseUtils(self)
            self.client1 = self.commcell.clients.get(self.tcinputs['ClientName1'])
            self.agent1 = self.client1.agents.get(self.tcinputs['AgentName'])
            self.backupset1 = self.agent1.backupsets.get(self.tcinputs['BackupsetName'])
            self.subclient1 = self.backupset1.subclients.get(self.tcinputs['SubclientName1'])
            self.exclude_machine = Machine(
                self.client1.client_hostname,
                username=self.tcinputs.get('MUserName'),
                password=self.tcinputs.get('MPassword')
            )
        except Exception as excep:
            raise CVTestCaseInitFailure(excep) from excep

    def init_commandcenter(self):
        """ initialize command center"""
        self.utils = TestCaseUtils(self)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.navigator = self.admin_console.navigator
        self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        self.sla = WebSla(self.web_adapter)
        self.exclude_reason = self.sla.Exclude_sla_categories.INVESTIGATION_APPLICATION.value

    @test_step
    def verify_entity_excluded(self, entity_name=None, exclude_category=None):
        """ verify the entity is excluded from SLA report"""
        reason_exclude = 'AutoClassifyTenantActionPending - No storage policy association'
        category_type = 'Customer action pending'
        self.navigator.navigate_to_reports()
        manage_report_admin = ManageReport(self.admin_console)
        manage_report_admin.access_report("SLA")
        self.sla.access_excluded_sla()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Excluded Entities")
        report_viewer.associate_component(table_obj)
        table_obj.toggle_column_visibility('Exclusion Reason')
        if category_type in ['Customer action pending']:
            table_obj.set_filter(column_name='Server', filter_string=entity_name)
            client_name = table_obj.get_column_data('Server')
            exclude_reason = table_obj.get_column_data('Exclusion Reason')
            category = table_obj.get_column_data('Category')
            if entity_name not in client_name and exclude_category not in category \
                    and reason_exclude not in exclude_reason:
                raise CVTestStepFailure(f"Expected subclient is {client_name[0]} but received {entity_name}"
                                        f"and Expected category is {exclude_category} but received{category}"
                                        f" Expected exclude reason is {reason_exclude} but received {exclude_reason}"
                                        )

    def run(self):
        """ run method"""
        try:
            self.init_tc()
            fs_helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            fs_helper.create_backupset('Backupset_TC_63826', delete=False)
            self.init_commandcenter()
            job_obj = self.subclient1.backup(backup_level='Full')
            time.sleep(2)
            self.exclude_machine.stop_all_cv_services()
            res = job_obj.wait_for_completion(timeout=6)
            if res is not False:
                job_obj.kill()
                self.log.info(f"Job ID {job_obj} is killed to check the SLA excluded status")
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes, waiting")
            sleep(minutes * 60)
            # verify subclient without storage policy association
            self.log.info("Check for client which is not reachable")
            self.verify_entity_excluded(entity_name=self.client.display_name, exclude_category=self.exclude_reason)
            self.log.info("Check for subclient without storage Policy")
            # verify the server down case
            self.verify_entity_excluded(entity_name=self.client1.display_name, exclude_category=self.exclude_reason)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.exclude_machine.start_all_cv_services()
            Browser.close_silently(self.browser)
