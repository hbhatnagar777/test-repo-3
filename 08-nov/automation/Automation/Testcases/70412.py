# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase: Class for executing this test case

  __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom.inputs import ListBoxController
from Web.AdminConsole.Reports.Custom.viewer import CustomReportViewer, DataTable

from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException

class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()

        self.name = "MIRU - Report Automation"

        self.browser = None
        self.driver = None
        self.admin_console = None
        self.tcinputs = {}

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.driver = self.browser.driver
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        self.init_tc()

        self.report = Report(self.admin_console)
        self.manage_report = ManageReport(self.admin_console)
        self.custom_report_viewer = CustomReportViewer(self.admin_console)

    def assert_active_tab_is(self, tab_name):
        """Assert if the landing tab is correct"""

        active_tab = RModalDialog(self.admin_console).current_tab()

        assert(active_tab == tab_name), f"Landing tab is [{active_tab}] but Expected was [{tab_name}]"

    @test_step
    def access_report(self, report_name, tab_name):
        """Access the report from the admin console"""

        self.admin_console.navigator.navigate_to_reports()
        self.manage_report.access_report(report_name)
        # We are asserting that on Landing to report the default tab should be the one we are expecting
        self.assert_active_tab_is(tab_name)
        self.report.verify_page_load(can_be_empty=True)

    def get_input_options_and_values(self):
        """
        Get the input options of the current Report page

        Note: If you want inputs of a specific tab then navigate to that tab first 
              and then refresh the page and then call this fn 
        """

        input_options = {}
        input_values =  {}

        rpt_inputs: dict = self.driver.execute_script("return rpt.inputs")

        for key,value in rpt_inputs.items():
            input_options[key] = []
            input_values[key] = value.get("value")

            if value.get("options"):
                for option in value["options"]:
                    if type(option) is dict:
                        input_options[key].append(option["label"])
                    else:
                        input_options[key].append(str(option))

        return input_options,input_values
    
    def _validate_table_load(self,table_name):
        """Validate the table load for a specific table
        
        Args:
            table_name (str) : Name of the table to validate

        Raises:
            CVWebAutomationException: If the table is not loaded correctly
        """

        # If API request fails , for example if you enter a some irrelevant filter then the table will not load
        # instead will show error message 'Something went wrong' and the table will not load

        table_obj = DataTable(table_name)
        self.custom_report_viewer.associate_component(table_obj)

        # If the table is not loaded correctly then the table columns will not appear
        if(table_obj.get_table_columns() == []):
            raise CVWebAutomationException(f"Table {table_name} not loaded correctly")
            
    def get_table_data(self,table_name):
        """Get the data of the table
        
        Args:
            table_name (str) : Name of the table to get data from

        Returns:
            table_data (dict) : dictionaries where evrey key is the column name and value is the list of data in that column
        """
        
        table_obj = DataTable(table_name)
        self.custom_report_viewer.associate_component(table_obj)
        return table_obj.get_table_data()
            
    def select_inputs(self,inputs):
        """
        Select Given inputs for the report

        inputs : {inp1 : [value1,value2], inp2 : [vlaue1,value2,value3], ...}

        if value of inp is All, then we choose select all option
        if value of inp is Any, then select the first value of inp

        Returns:
            It will replace All and Any with the actual values selected along with the inputs passed
            selected_inputs : {inp1 : [selected_value1,selected_value2], inp2 : [selected_value1]}

        Note: This function works only when page is loaded freshly and no default input exists
        This is technically enough for the current test case so we don't need to handle all edge cases
        """

        selected_inputs = {}
        input_obj = None

        for inp,inp_values in inputs.items():
            input_obj = ListBoxController(inp)
            self.custom_report_viewer.associate_input(input_obj)

            # most ideal way is to unselect all the values of the input and then select req values
            # so that older values are not deselected in process of selecting
            # But now their is no such helper function to unselect all values
            # But for our testcase its fine so we can ignore this

            if type(inp_values) is list:
                selected_inputs[inp] = inp_values
                input_obj.select_values(selected_inputs[inp])

            elif inp_values == "All":
                selected_inputs[inp] = input_obj.get_available_options()
                # some inputs don't have select_all option
                # but for our case we can ignore this
                input_obj.select_all()

            elif inp_values == "Any":
                selected_inputs[inp] = input_obj.get_available_options()[0]
                input_obj.select_value(selected_inputs[inp])
            
        if input_obj:
            input_obj.apply()

        return selected_inputs
    
    def set_quick_filters(self,table_name,filters):
        """
        Set the filters for the table using quick filters
        
        Args:
            table_name (str) : Name of the table to set filters
            filters (dict) : {column1 : filter_string, column2 : filter_string, ...}
        """
        
        table_obj = DataTable(table_name)
        self.custom_report_viewer.associate_component(table_obj)
        
        for column_name,filter_str in filters.items():
            table_obj.set_filter(column_name,filter_str)

    
    @test_step
    def validate_input_keys(self,input_keys):
        """Validate if only expected inputs are present"""

        expected_input_keys = input_keys
        self.page_input_options, self.page_input_values = self.get_input_options_and_values()
        actual_input_keys = list(self.page_input_options.keys())
        
        if(set(expected_input_keys) != set(actual_input_keys)):
            self.log.error(f"Input Keys mismatched")
            self.log.info(f"Expected Input Keys : {expected_input_keys}")
            self.log.info(f"Actual Input Keys : {actual_input_keys}")
            raise CVTestStepFailure("Input Keys mismatched")

        self.log.info(f"Page Input Options : {self.page_input_options}")           
    
    @test_step
    def validate_input_options_exist(self,input_keys):
        """Validate if input options have been loaded"""

        self.log.info("Validating the input options")
        # Check if the input options have some data
        for key in input_keys:
            if self.page_input_options[key] == []:
                raise CVTestStepFailure(f"No data found for the key {key}")
        self.log.info("Input options validated successfully")

    @test_step
    def validate_default_time_range_input(self,time_range_input_key):
        """Validate the time range input"""

        self.log.info("Validating the time range input")
        time_range = self.page_input_values[time_range_input_key]
        if time_range != "-PT72H P0D":
            raise CVTestStepFailure(f"Time Range By default should be set to Last 72 Hours but is not")
        self.log.info("Time Range validated successfully")

    @test_step
    def validate_table_load_with_default_inputs(self,table_name):
        """We are checking if the table is loaded correctly with default inputs"""

        self.log.info(f"Validating the table [{table_name}] load with default inputs")
        self._validate_table_load(table_name)
        self.log.info(f"Table [{table_name}] loaded successfully with default inputs")

    @test_step
    def validate_input_filter(self,table_name):
        """
        Validate the input filter
        Here we are only checking Media Agent filter, no need to check all filters
        """

        ma_name = self.select_inputs({"MediaAgents" : "Any"})["MediaAgents"]
        self.log.info(f"Selected Media Agent : {ma_name} in the input filter")

        self.log.info(f"Validating the input filters for [{table_name}] table")
        self._validate_table_load(table_name)

        table_data = self.get_table_data(table_name)

        column_name = "MediaAgent"

        if not all([ma_name == name for name in table_data[column_name]]):
            raise CVTestStepFailure(f"Input filter not working correctly for {table_name} table")
        
        self.log.info(f"Input filters validated successfully for {table_name} table")

    @test_step
    def validate_table_filter(self,table_name):
        """Validate the table filter"""

        # because in the validate_input_filters we selected only one Media Agent so...
        # the below code will select all the Media Agents but in the process will unselect the previously selected Media Agent
        self.select_inputs({"MediaAgents" : "All"})
        self.log.info(f"Validating the Table filters for [{table_name}] table")

        column_name = "Role(s)"
        filter_str = "Storage MediaAgent"
        filters = {column_name : filter_str}
        self.set_quick_filters(table_name,filters)

        self._validate_table_load(table_name)

        self.log.info(f"Role : Storage MediaAgent filter applied for [{table_name}] table")
        table_data = self.get_table_data(table_name)

        if not all([filter_str in roles for roles in table_data[column_name]]):
            raise CVTestStepFailure(f"Table filter not working correctly for [{table_name}] table")
        
        self.log.info(f"Table filters validated successfully for [{table_name}] table")

    def run(self):

        try:
            report_name = "Metallic Infrastructure Resource Utilization"
            tab_name = "MediaAgent"

            input_keys = ['commcell','company', 'region', 'clientGroups', 'MAs', 'timeRange']
            table_name = 'Performance'

            time_range_input_key = 'timeRange'

            self.access_report(report_name,tab_name)
            self.validate_input_keys(input_keys)
            
            # we don't expect options for timeRange
            input_keys.remove(time_range_input_key)
            self.validate_input_options_exist(input_keys)
            self.validate_default_time_range_input(time_range_input_key)
            self.validate_table_load_with_default_inputs(table_name)
            self.validate_input_filter(table_name)
            self.validate_table_filter(table_name)

            self.browser.close_silently(self.browser)

        except Exception as e:
            handle_testcase_exception(self, e)
