# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Initial configuration for the test case

    create_vtl_plan()               --  create IBMi VTL Plan

    is_ibmi_vtl_plan_exist()        --  check if IBMi VTL Plan exists

    delete_ibmi_vtl_plan()          --  Delete IBMi VTL Plan

    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "62604":
                        {
                            "PlanName":"Test-Auto",
                            "ClientName": "Existing-client",
                            "AccessNode": ["proxy1", "proxy2"],
                            "HostName": "IBMi-host-name",
                            "TestPath": "/QSYS.LIB",
                            "VTLLibrary": "IBM 3573-TL 76"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMiVTL plan creation and validation with IBMi VTL plan details from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.browser = None
        self.table = None
        self.temp_vtl_plan = None
        self.plans_page = None
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None,
            "VTLLibrary": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.table = Rtable(self.admin_console)
            self.plans_page = Plans(self.admin_console)
            self.temp_vtl_plan = "Auto_{0}".format(self.id)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def create_vtl_plan(self):
        """create IBMi VTL Plan"""
        self.navigator.navigate_to_plan()
        self.plans_page.create_ibmi_vtl_plan(plan_name=self.temp_vtl_plan,
                                             vtl_library=self.tcinputs['VTLLibrary'],
                                             retention={'value': '5', 'unit': "Week(s)"},
                                             rpo_details={'inc_frequency': {'Frequency': '365',
                                                                            'FrequencyUnit': 'Day(s)',
                                                                            'StartTime': '10:30 pm'},
                                                          'full_frequency': {'FullFrequency': 'Yearly',
                                                                             'FullStartTime': '11:30 pm',
                                                                             'FullStartEvery': 'Sunday',
                                                                             'FullStartWeek': 'Last',
                                                                             'FullStartMonth': 'March'},
                                                          'inc_window': {'Monday and Thursday': ['All day'],
                                                                         'Tuesday': ['2am-6am', '1pm-6pm'],
                                                                         'Tuesday through Thursday': ['9pm-12am'],
                                                                         'Wednesday': ['5am-2pm'],
                                                                         'Friday': ['1am-3am', '5am-1pm'],
                                                                         'Saturday': ['2am-5am', '9am-12pm', '2pm-6pm',
                                                                                      '9pm-12am'],
                                                                         'Sunday': ['1am-5am', '7am-1pm', '7pm-11pm']},
                                                          'full_window': {'Monday and Thursday': ['All day'],
                                                                          'Tuesday': ['2am-6am', '1pm-6pm'],
                                                                          'Tuesday through Thursday': ['9pm-12am'],
                                                                          'Wednesday and Friday': ['1am-3am'],
                                                                          'Saturday and Sunday': ['All day']}})

    @test_step
    def is_ibmi_vtl_plan_exist(self):
        """check if IBMi VTL Plan exists"""
        self.navigator.navigate_to_plan()
        all_vtl_plans = self.plans_page.list_plans(plan_type="IBM i VTL")
        return self.temp_vtl_plan in all_vtl_plans

    @test_step
    def delete_ibmi_vtl_plan(self):
        """Delete IBMi VTL Plan"""
        self.navigator.navigate_to_plan()
        self.table.view_by_title("IBM i VTL")
        self.plans_page.action_delete_plan(plan=self.temp_vtl_plan)

    def run(self):
        try:
            if self.is_ibmi_vtl_plan_exist():
                self.delete_ibmi_vtl_plan()
            self.create_vtl_plan()
            # Validation of plan details will be added once the current issue with VTL
            #   Plan details page is fixed.
            self.delete_ibmi_vtl_plan()

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
