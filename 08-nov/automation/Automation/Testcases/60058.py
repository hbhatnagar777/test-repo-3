from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Metallic Acceptance testcase
Verify Inputs and table level security for all built-in reports

Input Example:

    "testCases":
            {
                "60058":
                 {
                     
                 }
            }
            """
import time

from selenium.common.exceptions import NoSuchElementException

from cvpysdk.commcell import Commcell
from cvpysdk.storage import Libraries, RPStores
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.API import (
    customreports as custom_reports_api,
)
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
)
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.Custom import inputs
from Web.AdminConsole.Reports.Custom.inputs import ListBoxController
from Web.WebConsole.Reports.sla import WebSla

_CONFIG = get_config()


def get_client_display_name(clients):
    """Gets Client's display name"""
    client_name = clients.keys()
    display_name = []
    for name in client_name:
        display_name.append(clients.get(name).get('displayName'))
    return display_name


class TestCase(CVTestCase):
    """ Testcase """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Context based user security testing for built-in reports"
        self.browser: Browser = None
        self.inputs_list = []
        self.utils = CustomReportUtils(self)
        self.navigator = None
        self.manage_report = None
        self.report = None
        self.viewer = None
        self.security_filters_list = None
        self.admin_console = None
        self.csv_content = None
        self.input_value = None
        self.commcell_inputs = {}
        self.default_url = None
        self.web_adapter = None
        self.commcell = None

    def init_tc(self):
        """Initialize and Opens browse and login to webconsole"""
        try:
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.commcell = Commcell(webconsole_hostname=self.inputJSONnode['commcell']["webconsoleHostname"],
                                     commcell_username=self.inputJSONnode['commcell']["commcellUsername"],
                                     commcell_password=self.inputJSONnode['commcell']["commcellPassword"])
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"],
            )
            time.sleep(5)
            if self.admin_console.driver.title == 'Hub - Metallic':
                self.log.info("Navigating to adminconsole from Metallic hub")
                hub_dashboard = Dashboard(self.admin_console, HubServices.endpoint)
                try:
                    hub_dashboard.choose_service_from_dashboard()
                    hub_dashboard.go_to_admin_console()
                except:  # in case service is already opened
                    hub_dashboard.go_to_admin_console()

            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.report = Report(self.admin_console)
            self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
            self.viewer = viewer.CustomReportViewer(self.admin_console)

            # Columns to be verified in report table, Key should match map_list keys
            self.security_filters_list = {
                "Backup job summary": ['Clients', 'ClientGroups'],
                "CommCell Readiness": ['Clients', 'ClientGroups'],
                "Restore job summary": ['Clients'],
                "Aux copy job details": ['Storage Policy'],
                "SLA": ['Clients', 'ClientGroups'],
                "Audit trail": ['User', 'UserGroups'],
                "Office365 Backup Health": ['Clients'],
                "Infrastructure Load": ['Clients', 'ClientGroups'],
                "Recovery Readiness Report": ['Clients', 'ClientGroups'],
                "Storage Utilization": ['Library'],
                "User and user group permissions": ['User', 'UserGroups', 'Clients', 'Roles'],
                "Dynamics365 Backup Health": ['Clients'],
                "VM Backup Health": ['Clients'],
                "Salesforce Backup Health": ['Clients'],
                "Laptop Backup Health": ['Company'],
                "Databases Backup Health": ['Clients'],
                "Infrastructure Resource Utilization": ['MediaAgents', 'IndexServers']
            }
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def initial_config(self, report):
        """Initial Configuration for report"""
        self.log.info("-" * 50)
        self.log.info(f"Starting Validation for report {report}")
        self.log.info("-" * 50)
        self.navigator.navigate_to_reports()
        self.admin_console.wait_for_completion()
        # self.get_report_inputs(report)
        self.get_commcell_input_values(report)
        self.manage_report.access_report(report)
        self.default_url = self.browser.driver.current_url

    @test_step
    def get_report_inputs(self, report):
        """ Get all inputs present in a Report, which are fetching values from datasets"""
        inputs_list = []
        cre_api = custom_reports_api.CustomReportsAPI(
            self.commcell.webconsole_hostname,
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"]
        )
        report_def = cre_api.get_report_definition_by_name(report)
        for page_no in range(0, len(report_def["pages"])):
            input_dict = report_def["pages"][page_no]["inputs"]
            for i in range(0, len(input_dict)):
                if input_dict[i]['fromDataSet']:
                    inputs_list.append(input_dict[i]["id"])
        if 'commcell' in inputs_list:
            inputs_list.remove('commcell')
        self.inputs_list = self.map_list(inputs_list)

    @test_step
    def get_commcell_input_values(self, report):
        """ Returns dict of all the input values associated with this commcell for logged in user"""

        for inputs in self.security_filters_list[report]:
            input_values = []
            if inputs not in self.commcell_inputs:
                self.log.info(f"Fetching {inputs}")
                if inputs not in self.commcell_inputs:
                    if inputs == "Clients":
                        all_clients = self.commcell.clients.all_clients
                        all_clients.update(self.commcell.clients.hidden_clients)
                        self.commcell_inputs['Clients_name'] = sorted(all_clients.keys())
                        input_values = sorted(get_client_display_name(all_clients))
                        # Adding Hypervisors / VC to client list
                        virtualization_clients = self.commcell.clients._get_virtualization_clients()
                        if virtualization_clients:
                            virtualization_client = virtualization_clients.keys()
                            input_values.extend(virtualization_client)
                        salesforce_clients = self.commcell.clients.salesforce_clients
                        if salesforce_clients:
                            salesforce_client = salesforce_clients.keys()
                            input_values.extend(salesforce_client)
                        dynamic365_clients = self.commcell.clients.dynamics365_clients
                        if dynamic365_clients:
                            dynamic365_clients = dynamic365_clients.keys()
                            input_values.extend(dynamic365_clients)
                    elif inputs == "ClientGroups":
                        input_values = self.commcell.client_groups.all_clientgroups.keys()

                    elif inputs in ('Agents', 'Subclients'):
                        # Add condition here for subclient
                        all_agents = self.get_agents()
                        if inputs == "Agents":
                            if "file system" in all_agents:
                                all_agents.append("windows file system")
                                all_agents.append("linux file system")
                            self.commcell_inputs["Agents"] = sorted(all_agents)
                        # elif inputs == 'Subclients':
                        #     self.commcell_inputs["Subclients"] = sorted(all_subclients)
                        self.log.info(f" All Agents present are {self.commcell_inputs['Agents']}")

                    elif inputs == "Storage Policy":
                        input_values = self.commcell.storage_policies.all_storage_policies.keys()

                    elif inputs == 'User':
                        input_values = self.commcell.users.all_users.keys()

                    elif inputs == 'Library':
                        library_obj = Libraries(self.commcell)
                        input_values = list(library_obj._get_libraries().keys())
                        #rp_store = RPStores(self.commcell)
                        #input_values.extend(list(rp_store._get_rp_stores().keys()))

                    elif inputs == 'UserGroups':
                        input_values = self.commcell.user_groups.all_user_groups.keys()

                    elif inputs == 'Company':
                        input_values = [self.commcell.users.get(self.inputJSONnode['commcell']["commcellUsername"]).user_company_name]

                    elif inputs == 'Roles':
                        input_values = list(self.commcell.roles.all_roles.keys())

                    elif inputs == 'MediaAgents':
                        input_values = self.commcell.media_agents.all_media_agents.keys()

                    elif inputs == 'IndexServers':
                        indexservers_dict = self.commcell.index_servers.all_index_servers
                        input_values = [v.get('engineName').lower() for k, v in indexservers_dict.items()]
                self.commcell_inputs[inputs] = sorted(input_values)
                self.log.info(f"Values for {inputs} present in Commcell are {self.commcell_inputs[inputs]}")

    def get_agents(self):
        """ returns list of agents for all clients"""
        agents_list = []
        self.commcell.clients.refresh()
        for client in self.commcell_inputs["Clients_name"]:
            client_obj = self.commcell.clients.get(client)
            try:
                agents_dict = client_obj.agents.all_agents.keys()
            except Exception:
                agents_dict = []
            for agent in agents_dict:
                if agent not in agents_list:
                    agents_list.append(agent)
                    # agent_obj = client_obj.agents.get(agent)
                    # backupset_dict = ((agent_obj.backupsets.all_backupsets).keys())
                    # for backupset_name in backupset_dict:
                    #     backupset_list.append(backupset_name)
                    #     backupset_obj = agent_obj.backupsets.get(backupset_name)
                    #     subclient_dict = ((backupset_obj.subclients.all_subclients).keys())
                    #     for subclient in subclient_dict:
                    #         subclient_list.append(f"{client} \\ {backupset_name} \\ {subclient}")
        return agents_list

    def get_report_input_values(self, report):
        """Get all values present for inputs from Report"""
        self.input_value = {}
        if self.viewer.is_tab():
            all_tabs = self.viewer.get_all_page_title_names()
            self.log.info(f"The tab names are {all_tabs}")
        else:
            all_pages = self.viewer.get_all_page_title_names()
            if all_pages:
                for page in all_pages:
                    self.switch_page(self.default_url, page)
                    self.log.info(f"Fetching inputs from page {page}")
                    self.get_page_input_values(report)
            else:
                self.get_page_input_values(report)
            self.log.info("Report input values are %s" % self.input_value)

    def get_page_input_values(self, report):
        """Get input values of specified page in report"""
        all_input_value = self.admin_console.browser.driver.execute_script('return rpt.inputs')
        if all_input_value:
            mapped_col = [self.map_list([x])[0] for x in all_input_value]
            all_input_value_mapped = dict(zip(mapped_col, list(all_input_value.values())))
            for input in all_input_value_mapped.keys():
                if all_input_value_mapped[input].get('options', []):
                    dataset_value = []
                    if input in self.security_filters_list[report]:
                        for options in all_input_value_mapped[input].get('options', []):
                            try:
                                if options['label']:
                                    # list of all possible values for input_string
                                    dataset_value.append(str(options['label']).lower())
                            except TypeError:
                                if options:
                                    dataset_value.append(str(options).lower())
                        # converting list of multiple values to string
                        # dataset_value = ','.join(str(i).lower() for i in dataset_value)
                        self.input_value[input] = dataset_value

    @test_step
    def validate_input_security(self, report):
        """ Validates Input values against values from commcell"""
        self.log.info("Validating that values from report matches values fetched from commcell")
        self.get_report_input_values(report)
        # Compare self.input_value with ex: self.all_clients values
        for key in self.input_value:
            self.check_string_exist(self.input_value[key])
            if key in self.security_filters_list[report]:
                mismatch_inputs = list(set(self.input_value[key]) - set(self.commcell_inputs[key]))
                if mismatch_inputs:
                    self.log.info(f"Actual Report Input Values are {self.input_value[key]}")
                    self.log.info(f"Expected Values are {self.commcell_inputs[key]}")
                    raise CVTestStepFailure(f"Input values of input {key} "
                                            f"does not match expected values for Report {report}, Mismatched "
                                            f"column values - {mismatch_inputs}")
        self.log.info(f"Expected Input values are {self.commcell_inputs}")
        self.log.info(f"Input Security Validated for report [{report}]")

    @test_step
    def validate_report_loading(self):
        """ Validates Adminconsole notification error on report loading"""
        notification = self.admin_console.get_notification()
        if notification:
            raise CVTestStepFailure("Report loading has Notification error [%s]" % notification)
        self.log.info("Report loaded successfully")

    @test_step
    def validate_table_security(self, report):
        """Validate table values matches values  from commcell"""
        # verify table security in all tabs present
        if self.viewer.is_tab():
            all_tabs = self.viewer.get_all_page_title_names()
            self.log.info(f"The tab names are {all_tabs}")
        else:
            all_pages = self.viewer.get_all_page_title_names()
            if len(all_pages) == 0:
                self.validate_table_data(report)
            else:
                for page in all_pages:
                    self.switch_page(self.default_url, page)
                    self.log.info(f"Switched tabs to {page}")
                    self.log.info("Validating table values matches values in inputs for Page : %s" % page)
                    self.validate_table_data(report)

    def validate_table_data(self, report):
        """Validating table values matches values in inputs"""
        table_names = self.viewer.get_all_report_table_names()
        if not table_names:
            self.log.info("No tables present by default, selecting input values")
            self.select_required_inputs()
            table_names = self.viewer.get_all_report_table_names()
        for table in table_names:
            self.get_csv_data(table)
            if len(self.csv_content[2]) > 1:
                column_index = 2
            else:
                column_index = 3
            self.csv_content[column_index] = self.map_list(self.csv_content[column_index])
            for each_col in self.csv_content[column_index]:
                column_value = list(filter(None, set(self.get_column_value(column_index, each_col))))
                self.check_string_exist(column_value)
                # Check if table's column_value is sub list of self.commcell_inputs[each_col]
                if each_col in self.security_filters_list[report]:
                    if report == 'User and user group permissions' and table == 'User Details' and each_col == 'UserGroups':
                        self.commcell_inputs[each_col] = [item.split('\\')[-1] for item in self.commcell_inputs[each_col]]
                    # Loop will enter for User column For Audit trail report
                    if report == 'Audit trail':
                        #Adding seperate handling for Audit trail report as it has both User and Usergroup values under User column heading
                        audit_report_values = []
                        for c in self.security_filters_list[report]:# for User and User group
                            # creating a list of values of both user and user group
                            audit_report_values.extend(self.commcell_inputs[c])
                        mismatch_columns = list(set(column_value) - set(audit_report_values))
                    elif each_col == 'UserGroups' and table == 'User Details':
                        mismatch_columns = list(
                            set(column_value) - set([each.split("\\")[1] for each in (self.commcell_inputs[each_col])]))
                    else:
                        mismatch_columns = list(set(column_value) - set(self.commcell_inputs[each_col]))
                    if mismatch_columns and mismatch_columns != ['']:
                        self.log.info(f"Actual Report Column Values are {column_value}")
                        self.log.info(f"Expected Values are {self.commcell_inputs[each_col]}")
                        raise CVTestStepFailure(f"Table values of Column {each_col} "
                                                f"does not match expected values for Report {report}, Mismatched "
                                                f"column values - {mismatch_columns}")
            self.log.info(f"Security is implemented in table [{table}]")
        self.log.info(f"Table Security Validated for report [{report}]")

    def switch_page(self, from_page, to_page):
        """Switching page"""
        new_url = f"{from_page}&pageName={to_page}"
        self.browser.driver.get(new_url)
        self.admin_console.wait_for_completion()

    def select_required_inputs(self):
        """Select values in all required Inputs in UI"""
        required_inputs = self.viewer.get_all_required_input_names()
        cc = None
        for inputs in required_inputs:
            cc = ListBoxController(inputs)
            try:
                self.viewer.associate_input(cc)
                cc.select_all()
            except:
                pass
        if cc:
            cc.apply()
        self.admin_console.wait_for_completion()

    def get_csv_data(self, table_name):
        """ Exports table in CSV and get data of it"""
        self.utils.reset_temp_dir()
        table = viewer.DataTable(table_name)
        self.viewer.associate_component(table)
        table.expand_table()
        table.export_to_csv()
        file_name = self.utils.poll_for_tmp_files(ends_with="csv", min_size=30)[0]
        self.log.info("Csv file is downloaded for the table [%s]", table_name)
        self.csv_content = self.utils.get_csv_content(file_name)

    def get_column_value(self, column_index, column):
        """ Get value of specified column"""
        column_value = []
        index = self.csv_content[column_index].index(column)
        for row in range(column_index + 1, len(self.csv_content)):
            col_value = (self.csv_content[row][index]).lower()
            # Handle comma seperated values and add it to list
            if ',' in col_value:
                y = col_value.split(',')
                column_value.extend(y)
            else:
                column_value.append(col_value)
        return column_value

    @staticmethod
    def check_string_exist(to_check):
        """Validate that text donotsee doesnot exist"""
        for each_item in to_check:
            if "donotsee" in each_item.lower():
                raise CVTestStepFailure(f"Unexpected Text 'donotsee' is observed in report in - {to_check}")

    @staticmethod
    def map_list(values_list):
        """ Returns list mapped as per mapping specified """

        mapping = {
            'Clients': ['Server', 'Servers', 'Clients', 'Client', 'Name', 'Hypervisor'],
            'ClientGroups': ['ClientGroups', 'Client Group', 'Clientgroup', 'Client Groups',
                             'Server Group', 'Servergroup', 'Server Groups', 'Servergroups', 'ClientGroup'],
            'Agents': ['Agents', 'Agent', "AgentType"],
            'Subclients': ['Subclient', 'Subclients'],
            'Storage Policy': ['Storage Policy', 'StoragePolicy'],
            'User': ['User', 'Users', 'userlist', 'users', 'User name'],
            'Library': ['Library', 'Libraries', 'Storage', 'DiskLibrary'],
            'UserGroups': ['User Groups', 'User Group', 'User Group Name', 'Users\\UserGroups', 'usergrouplist',
                           'userGroups', 'User group name', 'UserGroup'],
            'Company': ['Company', 'Companies'],
            'Roles': ['RoleName'],
            'MediaAgents': ['MediaAgent', 'MAs'],
            'IndexServers': ['IndexServer', 'indexServer']
        }

        for i, each in enumerate(values_list):
            for key, value in mapping.items():
                if each.lower() in (x.lower() for x in value):
                    values_list[i] = key
        return values_list

    @test_step
    def validate_text(self, report):
        """ Validate that text DonotSee is not present anywhere in report other than inputs and tables"""
        try:
            text_ele = self.admin_console.browser.driver.find_element(By.XPATH, '//*[contains(text(),"donotsee")]')
            if text_ele:
                self.log.info("Text 'donotsee' found in report")
                raise CVTestStepFailure(f"Unexpected Text 'donotsee' is observed in report - {report}")
        except NoSuchElementException:
            self.log.info("Text donotsee is not found in report")
            self.log.info(f"Validated security on report [{report}] successfully!")

    def select_options_input(self):
        """ Select Options input in VM Backup Health report"""
        option_input = inputs.DropDownController('Options')
        try:
            self.viewer.associate_input(option_input)
            option_input.select_value('Show all VMs')
            option_input.apply()
        except:
            pass
        self.admin_console.wait_for_completion()

    def run(self):
        try:
            self.init_tc()
            reports = ['Backup job summary', #'CommCell Readiness',
                       'Restore job summary', 'Aux copy job details',
                       'SLA', 'Audit trail', 'Infrastructure Load', 'Storage Utilization',
                       #'Recovery Readiness', built-in report is removed starting SP30
                       'User and user group permissions',
                       'Dynamics365 Backup Health', 'Laptop Backup Health',
                       'Office365 Backup Health', 'Databases Backup Health',
                       'Salesforce Backup Health', 'VM Backup Health'#,'Infrastructure Resource Utilization'
                       ]
            for report in reports:
                self.initial_config(report)
                self.validate_report_loading()
                self.validate_input_security(report)
                if report == 'SLA':
                    sla = WebSla(self.web_adapter)
                    sla.access_met_sla()
                    self.validate_table_security(report)
                    self.admin_console.select_breadcrumb_link_using_text("SLA")
                    sla.access_missed_sla()
                    self.validate_table_security(report)
                else:
                    if report == 'VM Backup Health':
                        self.select_options_input()
                    self.validate_table_security(report)
                self.validate_text(report)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
