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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.serverhelper import ServerTestCases
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils import config
from Web.Common.page_object import TestStep
from datetime import datetime
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.Custom.inputs import ListBoxController, DropDownController


class TestCase(CVTestCase):
    test_step = TestStep()
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.admin_console = None
        self.browser = None
        self.name = """[Backup Job Summary Report] Perform basic validations on the report"""
        self.show_to_user = True
        self.config_json = config.get_config()
        self.tcinputs = {
            "ClientName": "",
            "FSClientName": "",
            "SQLServerClientName": "",
            "SQLServerInstanceName": "",
            "SQLServerBackupsetName": "",
            "SQLServerSubclientName": "",
            "VirtualServerClientName": "",
            "VirtualServerInstanceName": "",
            "VirtualServerBackupsetName": "",
            "VirtualServerSubclientName": ""
        }
        self.server = ServerTestCases(self)

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

    def setup_company(self):
        """Creates a company and adds the given client to it."""
        self.company = 'Company' + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.orghelper.create(self.company, company_alias=self.company)
        self.ta_name = f'tenantadmin'
        self.userhelper.create_user(f'{self.company}\\{self.ta_name}',
                                    email=f'{self.ta_name}@{self.company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.company + '\\Tenant Admin'])
        self.tu_name = f'tenantuser'
        self.userhelper.create_user(f'{self.company}\\{self.tu_name}',
                                    email=f'{self.tu_name}@{self.company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.company + '\\Tenant Users'])

        self.clientcompany = self.client.company_name if self.client.company_name else "Commcell"
        self.client.change_company_for_client(self.company)
        self.log.info(f"Client {self.tcinputs['ClientName']} is migrated to {self.company}")

        self.subclient = self.create_subclient(self.tcinputs["ClientName"],
                                               self.entity_props["storagepolicy"]["name"])['object']

        job = self.subclient.backup("full")
        job.wait_for_completion()
        self.jobids['company'] = job.job_id
        self.log.info(f"Job of company {self.company} : {job.job_id}")

    def start_required_jobs(self):
        """This function starts different kinds of jobs required for this report validation"""
        self.log.info("Starting required jobs for report validation")
        self.subclient = self.create_subclient(self.tcinputs["FSClientName"],
                                               self.entity_props["storagepolicy"]["name"])['object']
        self.jobids = {}
        self.clientgroupname = "ClientGroup_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.commcell.client_groups.add(self.clientgroupname, [self.tcinputs["FSClientName"]])
        self.log.info(f"Created client group {self.clientgroupname}")
        # completed
        job = self.subclient.backup("full")
        job.wait_for_completion()
        if job.status.lower() == 'completed':
            self.jobids['completed'] = job.job_id
            self.log.info(f"Job with status {job.status} : {job.job_id}")

        # completed with errors
        machine_obj = Machine(self.subclient.properties['subClientEntity']['clientName'], self.commcell)
        dir = machine_obj.scan_directory(self.subclient.content[0])
        if dir[0]['type'] == 'directory':
            machine_obj.remove_directory(dir[0]['path'])
        else:
            machine_obj.delete_file(dir[0]['path'])
        self.subclient.content = [self.subclient.content[0], dir[0]['path']]
        job = self.subclient.backup("full")
        job.wait_for_completion()
        if job.status.lower() == 'Completed w/ one or more errors'.lower():
            self.jobids['cwe'] = job.job_id
            self.log.info(f"Job with status {job.status} : {job.job_id}")

        # killed
        job = self.subclient.backup("full")
        job.kill(wait_for_job_to_kill=True)
        if job.status.lower() == 'Killed'.lower():
            self.jobids['killed'] = job.job_id
            self.log.info(f"Job with status {job.status} : {job.job_id}")

        # failed
        self.subclient.content = [dir[0]['path']]
        job = self.subclient.backup("full")
        job.wait_for_completion()
        if job.status.lower() == 'failed'.lower():
            self.jobids['failed'] = job.job_id
            self.log.info(f"Job with status {job.status} : {job.job_id}")

        # vsa
        vsa_subclient = self.commcell.clients.get(self.tcinputs["VirtualServerClientName"]) \
            .agents.get("virtual server") \
            .instances.get(self.tcinputs["VirtualServerInstanceName"]) \
            .backupsets.get(self.tcinputs["VirtualServerBackupsetName"]) \
            .subclients.get(self.tcinputs["VirtualServerSubclientName"])
        job = vsa_subclient.backup("full")
        self.jobids['vsa'] = job.job_id
        job.kill()
        self.log.info(f"Job of 'Virtual Server Agent' : {job.job_id}")

        # db
        sql_subclient = self.commcell.clients.get(self.tcinputs["SQLServerClientName"]) \
            .agents.get("sql server") \
            .instances.get(self.tcinputs["SQLServerInstanceName"]) \
            .backupsets.get(self.tcinputs["SQLServerBackupsetName"]) \
            .subclients.get(self.tcinputs["SQLServerSubclientName"])

        job = sql_subclient.backup("full")
        self.jobids['sql'] = job.job_id
        job.kill()
        self.log.info(f"Job of 'SQL Server Agent' : {job.job_id}")

        self.setup_company()

        self.log.info("All the required jobs are created for validation")
        self.log.info(self.jobids)

    def setup(self):
        """Setup function of this test case"""

        self.entities = CVEntities(self)
        self.orghelper = OrganizationHelper(self.commcell)
        self.userhelper = UserHelper(self.commcell)
        self.entity_props = self.entities.create(["disklibrary", "storagepolicy"])
        self.start_required_jobs()

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_reports()
        self.report_manager = ManageReport(self.admin_console)
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.report_manager.access_report("Backup job summary")
        self.job_details_table = viewer.DataTable("Job Details")
        self.database_jobs_table = viewer.DataTable("Databases in SQL Server and Sybase Backup Jobs")
        self.jobs_in_jdtable = None
        self.jobs_in_dbtable = None

    def select_report_input(self, inputs_dict):
        """
        This function selects the input values for a report

        Args:
            inputs_dict (dict) : dict containing keys as inputs to be selected and values as options to be selected
                Supported inputs  : 'Job status', 'Advanced', 'App types / Workloads', 'Company' and
                                                   'Select time range'
                Supported values  : value can be string/'list of strings', we can select multiple values in a dropdown

            Ex: {
                "Company" : ['CompanyA', 'CompanyB'],
                "Advanced" : "Show Server Groups"
            }

        """
        self.admin_console.refresh_page()

        controller_mapping = {
            'Job status': ListBoxController,
            'Advanced': ListBoxController,
            'Select time range': DropDownController,
            'App types / Workloads': ListBoxController,
            'Company': ListBoxController
        }

        input_controller = ListBoxController("Servers")
        self.log.info(inputs_dict)
        self.report_viewer.associate_input(input_controller)
        input_controller.expand_input_controller()

        for input_name, value in inputs_dict.items():
            controller_class = controller_mapping[input_name]
            controller = controller_class(input_name)
            self.report_viewer.associate_input(controller)

            if input_name == 'Select time range':
                controller.select_value(value)
            else:
                if input_name in ['Advanced']:
                    controller.unselect_all()
                if value:
                    if not isinstance(value, list):
                        value = [value]
                    controller.select_values(value)

        input_controller.apply()

    def get_table_data(self):
        """Retrieves all the jobs that are displayed in the tables"""
        self.report_viewer.associate_component(self.job_details_table)
        self.jobs_in_jdtable = self.job_details_table.get_table_data()['Job ID']
        self.log.info(f"Jobs present in Job details table : {self.jobs_in_jdtable}")
        self.report_viewer.associate_component(self.database_jobs_table)
        self.jobs_in_dbtable = self.database_jobs_table.get_table_data()['JobId']
        self.log.info(f"Jobs present in DB Jobs table : {self.jobs_in_dbtable}")

    @test_step
    def verify_advanced_setting(self):
        """Verifies advanced input of the report"""
        self.report_viewer.associate_component(self.job_details_table)
        current_columns = self.job_details_table.get_table_columns()
        self.log.info("Verifying Advanced options")
        self.select_report_input({
            "Advanced": ["Show Server Groups"]
        })
        if "Server groups" not in current_columns:
            self.job_details_table.toggle_column_visibility('Server groups')
        self.report_viewer.associate_component(self.job_details_table)
        self.job_details_table.set_number_of_rows(number_of_results=500)
        data = self.job_details_table.get_table_data()
        idx = data['Job ID'].index(self.jobids['completed'])
        server_groups = data['Server groups'][idx]
        self.log.info(f"Server groups of Job {self.jobids['completed']} are {server_groups}")
        if self.clientgroupname not in server_groups:
            raise Exception(
                f'Table shows {self.tcinputs["FSClientName"]} is not in client group {self.clientgroupname}')
        self.log.info(f'Report shows "{self.tcinputs["FSClientName"]}" is part of client group {self.clientgroupname}')
        self.select_report_input({
            "Advanced": None
        })
        self.report_viewer.associate_component(self.job_details_table)
        self.job_details_table.toggle_column_visibility('Server groups')
        self.job_details_table.toggle_column_visibility('Company')
        self.job_details_table.set_number_of_rows(number_of_results=500)
        data = self.job_details_table.get_table_data()
        idx = data['Job ID'].index(self.jobids['completed'])
        server_groups = data['Server groups'][idx]
        if server_groups != '':
            raise Exception("Disabling the advanced option to show server groups also showing the server groups")
        self.log.info("'Show Server Groups' Advanced option validated successfully")

    @test_step
    def verify_company_value(self):
        """Verifies company value of the job"""
        self.report_viewer.associate_component(self.job_details_table)
        current_columns = self.job_details_table.get_table_columns()
        self.log.info("Verifying Company of the job")
        data = self.job_details_table.get_table_data()
        idx = data['Job ID'].index(self.jobids['completed'])
        company = data['Company'][idx]
        if company != "Commcell":
            raise Exception(f"Job {self.jobids['completed']} company is not Commcell")
        self.log.info(f"Job {self.jobids['completed']} company is {company}")

        idx = data['Job ID'].index(self.jobids['company'])
        company = data['Company'][idx]
        if company != self.company:
            raise Exception(f"Job {self.jobids['completed']} company is not {self.company}")
        self.log.info(f"Job {self.jobids['completed']} company is {company}")

        # handle empty company case
        for index, company_name in enumerate(data['Company']):
            if company_name == "":
                raise Exception(f"Company name is set to Null for job {data['Job ID'][index]}")

        self.log.info("Verified company value of the jobs successfully in the report")

    @test_step
    def verify_tables(self):
        """Verifies if correct jobs are present in the table"""
        self.log.info("Verifying if correct jobs are present in tables.")
        self.get_table_data()
        for job_type, job in self.jobids.items():
            if job not in self.jobs_in_jdtable:
                raise Exception(f"Job {job} is not present in Job details table, please check")
            if job_type == 'sql' and job not in self.jobs_in_dbtable:
                raise Exception(f"Job {job} is not present in DB Jobs table, please check")
            elif job_type != 'sql' and job in self.jobs_in_dbtable:
                raise Exception(f"{job_type} Job {job} is present in DB Jobs table, please check")
        self.log.info("Verified that correct jobs are present in tables")

    @test_step
    def verify_sql_filter(self):
        """Applies input workload filter on sql server"""
        self.log.info("Adding filter for SQL Jobs")
        self.select_report_input({
            'App types / Workloads': "SQL Server"
        })
        self.get_table_data()
        for job_type, job in self.jobids.items():
            if job_type != 'sql':
                if job in self.jobs_in_jdtable:
                    raise Exception(f"{job_type} Job {job} is present in Job details table when applied sql filter")
                if job in self.jobs_in_dbtable:
                    raise Exception(f"{job_type} Job {job} is present in DB Jobs table when applied sql filter")

            if job_type == 'sql':
                if job not in self.jobs_in_dbtable:
                    raise Exception(f"Job {job} is not present in DB Jobs table when applied sql filter")
                if job not in self.jobs_in_jdtable:
                    raise Exception(f"Job {job} is not present in DB Jobs table when applied sql filter")

        self.select_report_input({
            'App types / Workloads': "SQL Server"
        })
        self.log.info("SQL Server Workload filter verified successfully")

    @test_step
    def verify_fs_filter(self):
        """Applies input workload filter on file system jobs"""
        self.log.info("Adding filter for FS Jobs")
        self.select_report_input({
            'App types / Workloads': ["Windows Server", "Linux File System"]
        })
        self.get_table_data()
        if self.jobs_in_dbtable != ['No data available']:
            raise Exception("There are database jobs present in DB table even when FS filter is applied")

        for job_type, job in self.jobids.items():
            if job_type in ["sql", "vsa"] and job in self.jobs_in_jdtable:
                raise Exception(f"{job_type} Job {job} is present in Job details table when FS filter is applied")

        self.select_report_input({
            'App types / Workloads': ["Windows Server", "Linux File System"]
        })
        self.log.info("File System Workload filter verified successfully")

    @test_step
    def verify_company_filter(self):
        """Verifies input company filter"""
        self.log.info(f"Adding filter for Company {self.company}")
        self.select_report_input({
            "Company": self.company
        })
        self.get_table_data()
        if self.jobs_in_dbtable != ['No data available']:
            raise Exception("There are jobs present in DB table even when Company is applied \
                                                            where no sql server is linked to that company")

        for job_type, job in self.jobids.items():
            if job_type != 'company' and job in self.jobs_in_jdtable:
                raise Exception(f"{job_type} Job {job} is present in Job details table when Company filter is applied")

        self.select_report_input({
            "Company": self.company
        })
        self.log.info("Company filter verified successfully")

    def verify_jobs_present(self, include_jobs, exclude_jobs):
        """
        Verifies that jobs that are in include_jobs list should be present in the job details table and jobs in
        exclude jobs list are excluded
        """
        self.get_table_data()
        for job in include_jobs:
            if job not in self.jobs_in_jdtable:
                raise Exception(f"Job {job} should be present in job details table, but its not present")

        for job in exclude_jobs:
            if job in self.jobs_in_jdtable:
                raise Exception(f"Job {job} not should be present in job details table, but its present")

    def apply_and_verify_job_status_filter(self, status, expected_present, expected_absent):
        """Applies filters for different kinds of job statuses"""
        self.log.info(f"Adding filter for job status '{status}'")
        self.select_report_input({
            'Job status': [status]
        })
        self.verify_jobs_present(expected_present, expected_absent)
        self.log.info(f"Verified filter for job status '{status}'")
        self.select_report_input({
            'Job status': [status]
        })

    @test_step
    def verify_status_filter(self):
        """Verifies input status filter"""
        # Define job status filters and their corresponding expected job IDs
        filters = {
            "Completed": (
                [self.jobids['completed']], [self.jobids['failed'], self.jobids['cwe'], self.jobids['killed']]),
            "Completed with Errors": (
                [self.jobids['cwe']], [self.jobids['failed'], self.jobids['completed'], self.jobids['killed']]),
            "Failed": ([self.jobids['failed']], [self.jobids['completed'], self.jobids['cwe'], self.jobids['killed']]),
            "Killed": ([self.jobids['killed']], [self.jobids['failed'], self.jobids['cwe'], self.jobids['completed']])
        }
        # by default all the job statuses are selected, unselecting them below
        self.select_report_input({
            'Job status': ["Completed", "Completed with Errors", "Failed", "Killed"]
        })
        # Apply each filter and verify
        for status, (expected_present, expected_absent) in filters.items():
            self.apply_and_verify_job_status_filter(status, expected_present, expected_absent)

    @test_step
    def verify_filters(self):
        """Verifies if the input filters are working fine"""
        self.log.info("Verifying filters on the report")
        self.verify_sql_filter()
        self.verify_fs_filter()
        self.verify_company_filter()
        self.verify_status_filter()
        self.log.info("Input filters on the report verified successfully")

    @test_step
    def verify_tenant_admin_persona(self):
        """Logs in as tenant admin of a company and verifies report data"""
        self.log.info(f"Logging in as tenant admin {self.ta_name} of company {self.company} and verifying report")
        self.admin_console.logout()
        self.admin_console.login(
            username=f'{self.company}\\{self.ta_name}',
            password=self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.navigator.navigate_to_reports()
        self.report_manager.access_report("Backup job summary")
        self.get_table_data()

        if self.jobs_in_dbtable != ['No data available']:
            raise Exception(f"There are jobs present in DB table even when logged in as tenant admin of {self.company} \
                                                                    where no sql server is linked to that company")
        for job_type, job in self.jobids.items():
            if job_type != 'company' and job in self.jobs_in_jdtable:
                raise Exception(f"{job_type} Job {job} is present in Job details table for tenant admin")

        self.log.info("verified tenant admin persona successfully")

    @test_step
    def verify_tenant_user_persona(self):
        """Logs in as tenant user of a company and verifies report data"""
        self.log.info(f"Logging in as tenant user {self.tu_name} of company {self.company} and verifying report")
        self.admin_console.logout()
        self.admin_console.login(
            username=f'{self.company}\\{self.tu_name}',
            password=self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.navigator.navigate_to_reports()
        self.report_manager.access_report("Backup job summary")
        self.get_table_data()

        if self.jobs_in_dbtable != ['No data available']:
            raise Exception(f"There are jobs present in DB table even when logged in as tenant user of {self.company} \
                                                                            where there are no associations")
        if self.jobs_in_jdtable != ['No data available']:
            raise Exception(f"There are jobs present in Job Details table even when logged in as tenant user " \
                            f"of {self.company} where there are no associations for the user")

        self.log.info("verified tenant user persona successfully")

    @test_step
    def verify_empty_tenant_admin_persona(self):
        """Logs in as a tenant admin of a company with no associations and verifies report"""
        empty_company_name = 'Company' + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.orghelper.create(empty_company_name, company_alias=empty_company_name)
        empty_ta_name = f'tenantadmin'
        self.userhelper.create_user(f'{empty_company_name}\\{empty_ta_name}',
                                    email=f'{empty_ta_name}@{empty_company_name}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[empty_company_name + '\\Tenant Admin'])
        self.log.info(f"Create a company {empty_company_name} with no associations")
        self.admin_console.logout()
        self.log.info(f"Logging in as a tenant admin({empty_ta_name}) of empty company")

        self.admin_console.login(
            username=f'{empty_company_name}\\{empty_ta_name}',
            password=self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.navigator.navigate_to_reports()
        self.report_manager.access_report("Backup job summary")
        self.get_table_data()

        if self.jobs_in_dbtable != ['No data available']:
            raise Exception(f"There are jobs present in DB table even when logged in as tenant admin of empty company")
        if self.jobs_in_jdtable != ['No data available']:
            raise Exception(f"There are jobs present in Job details table when logged in as tenant admin of empty "
                            f"company")

        self.log.info("Successfully verified report as tenant admin of a company with no associations")

    @test_step
    def verify_tenant_personas(self):
        """Verifies the report by logging in as tenant admin and tenant user of a company"""

        self.verify_tenant_admin_persona()
        self.verify_tenant_user_persona()
        self.verify_empty_tenant_admin_persona()

    def verify_testcases(self):
        """This method validates all the testcases mentioned in the testcase"""

        self.verify_advanced_setting()
        self.verify_company_value()
        self.verify_tables()
        self.verify_filters()
        self.verify_tenant_personas()

    def run(self):
        """Run function of this test case"""
        try:
            self.verify_testcases()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.client.change_company_for_client(self.clientcompany)
            self.log.info(f"Client {self.tcinputs['ClientName']} is migrated back to  {self.clientcompany}")
            self.log.info('Deleting company {0}'.format(self.company))
            self.commcell.organizations.delete(self.company)
            self.commcell.client_groups.delete(self.clientgroupname)
            pass
        finally:
            self.entities.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
