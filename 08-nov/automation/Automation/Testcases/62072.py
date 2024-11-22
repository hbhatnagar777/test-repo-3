# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function of the test case

    run()                   --  Main function for testcase execution

Input Example:
    "testCases":{
        "62072":{
            "hadoop_app": "<Name of the hadoop app to be used>",
            "access_nodes": "<Access nodes to be used as part of this App>",
            "plan": "<Plan to be used>",
            "connection_string": "<JDBC connection string for hive backup and restore>",
            "database": "<Database to be backed up> (optional, default - autodb_62072)",
            "hadoop_instance": "<Instance to be used>" (optional, default - hadoop_app),
            "hdfs_user": "<hdfs user>" (optional, default - hdfs),
            "hive_user": "<hive user>" (optional, default - hive),
            "hive_password": "<hive password>" (optional, default - hive),
            "tables_per_sc": "<No of tables to be created per sc>" (optional, default - 10 per sc),
            "test_data": "<string representation of test data dictionary>" (optional,eg."{'key':'val'}")
                default - {
                "skip_create": "<skips creation of tables and runs backup for existing database>", (default - False)
                "force_insert": "<generates data in the tables before running backup>", (optional, default - False)
                "table_modes": "<Managed/External tables>" (optional, default - ["Managed"])
                "table_types": "<types of tables to be generated>" (optional, default - ["partition_bucket"])
                    supported_types - ["default", "partition", "bucket", "partition_bucket"]
                "file_formats": "<file types to be used>" (optional, default - ["textfile", "orc"]),
                    supported_types - ["sequencefile", "rcfile", "orc", "parquet", "textfile", "avro"]
                }
        }
    }

"""

# Test suite Imports
import json
from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase

from Database.HiveUtils.hivehelper import HiveHelper
from Server.Workflow.workflowhelper import WorkflowHelper

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Forms.forms import Forms

from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for validating this testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Hive - Verify Backup & Restore Functionality, includes serde properties and table deletion"
        self.browser = None
        self.web_console = None
        self.admin_console = None
        self.show_to_user = False
        self._workflow = None
        self.forms = None
        self.hive_backup = "Hive Backup"
        self.hive_restore = "Hive Restore"
        self.instances = None
        self.access_nodes = None
        self.hive_helper = None
        self.source_db = None
        self.destination_db = None
        self.multiple_restores = None
        self.tcinputs = {
            'hadoop_app': None,
            'access_nodes': None,
            'plan': None,
            'connection_string': None
        }

    def switch_to_webconsole(self):
        """switches to webconsole and navigates to forms page"""
        if self.web_console is None:
            self.web_console = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.web_console.goto_webconsole()
        if self.web_console.is_login_page():
            self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                   self.inputJSONnode['commcell']['commcellPassword'])
        self.web_console.wait_till_load_complete()
        self.web_console.goto_forms()
        self.forms = Forms(self.web_console)

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.admin_console.navigator.navigate_to_big_data()
        self.instances = Instances(self.admin_console)
        nodes = self.tcinputs['access_nodes']
        self.access_nodes = json.loads(nodes) if isinstance(nodes, str) else nodes
        self._workflow = WorkflowHelper(self, self.hive_backup, deploy=True)
        WorkflowHelper(self, self.hive_restore, deploy=True)
        self.hive_helper = HiveHelper(self.commcell, self.access_nodes[0],
                                      self.tcinputs['connection_string'],
                                      self.tcinputs.get('hdfs_user', 'hdfs'),
                                      self.tcinputs.get('hive_user', 'hive'))

    def fill_and_submit_backup_form(self, backup_type='Full'):
        """fills backup workflow form and submits it"""
        hadoop_app = self.tcinputs.get('hadoop_app')
        database = self.source_db
        hdfs_user = self.tcinputs.get('hdfs_user', 'hdfs')
        hive_user = self.tcinputs.get('hive_user', 'hive')
        hive_password = self.tcinputs.get('hive_password', 'hive')
        tables_per_sc = int(self.tcinputs.get('tables_per_sc', '10'))
        self.forms.select_dropdown('Client Name', hadoop_app)
        self.forms.set_textbox_value('Instance Name', self.tcinputs.get('hadoop_instance', hadoop_app))
        self.forms.set_textbox_value('Database Name', database)
        self.forms.select_dropdown('Backup Type', backup_type)
        self.forms.select_dropdown('Hive Node', self.access_nodes[0])
        self.forms.set_textbox_value('JDBC Connection String', self.tcinputs['connection_string'])
        self.forms.set_textbox_value('Hive User ', hive_user)
        self.forms.set_textbox_value('Hive Password', hive_password)
        self.forms.set_textbox_value('HDFS User', hdfs_user)
        self.forms.set_textbox_value('Number of Tables in a subclient', tables_per_sc)
        self.forms.select_dropdown_list_value("List of storage policy to assign to subclients.",
                                              [self.tcinputs.get('plan')])
        self.forms.submit()

        # Info message
        if self.forms.is_form_submitted():
            self.forms.close_form()
        else:
            raise CVTestStepFailure("Form is not submitted")

    def fill_and_submit_restore_form(self):
        """fills restore workflow form and submits it"""
        hadoop_app = self.tcinputs.get('hadoop_app')
        database = self.source_db
        hdfs_user = self.tcinputs.get('hdfs_user', 'hdfs')
        hive_user = self.tcinputs.get('hive_user', 'hive')
        hive_password = self.tcinputs.get('hive_password', 'hive')
        timetorestore = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        db_list = [f"/warehouse/tablespace/{tablespace}/hive/{database}.db" for tablespace in ['managed', 'external']]
        db_list = self.multiple_restores or db_list

        # First window
        self.forms.select_dropdown('Source Client Name', hadoop_app)
        self.forms.set_textbox_value('Instance Name', self.tcinputs.get('hadoop_instance', hadoop_app))
        self.forms.set_calendar('timeRangeToRestore', timetorestore)
        self.forms.submit()

        # Info message
        self.forms.submit()

        open_form_window = 'Select the database to Restore'
        # Second window
        if self.forms.is_form_open(open_form_window):
            src_dbs = set()
            for database in db_list:
                self.forms.select_dropdown('Source Database Name', database)
                selected_value = self.forms.get_dropdown_value('Source Database Name')
                if selected_value is not None:
                    src_dbs.add(selected_value)

            if len(src_dbs) == 1:
                self.multiple_restores = False
                self.forms.select_dropdown('Source Database Name', db_list[0])
            elif len(src_dbs) == 0:
                raise Exception("Failing the tc, since no database is listed. Please verify "
                                "given backup and restore inputs")
            else:
                self.multiple_restores = [db_list[0]]

            self.forms.click_action_button('Next')
        else:
            raise Exception(f'Wrong window is open, {open_form_window} window should be loaded')

        open_form_window = 'Select table/s to Restore'
        # Third window
        if self.forms.is_form_open(open_form_window):
            self.forms.select_dropdown_list_value('Table/s', ['SelectAll'])
            self.forms.click_action_button('Next')
        else:
            raise Exception(f'Wrong window is open, {open_form_window} window should be loaded')

        open_form_window = 'Select Destination Client'
        # Fourth window
        if self.forms.is_form_open(open_form_window):
            self.forms.select_dropdown('Destination Client Name', hadoop_app)
            self.forms.set_textbox_value('Destination Database Name', f"{self.destination_db}")
            self.forms.click_action_button('Next')
        else:
            raise Exception(f'Wrong window is open, {open_form_window} window should be loaded')

        open_form_window = 'Select Destination Instance'
        # Fifth window
        if self.forms.is_form_open(open_form_window):
            self.forms.select_dropdown('Destination Instance Name', self.tcinputs.get('hadoop_instance', hadoop_app))
            self.forms.select_dropdown('Hive Node', self.access_nodes[0])
            self.forms.set_textbox_value('ConnectionString', self.tcinputs['connection_string'])
            self.forms.set_textbox_value('Hive User', hive_user)
            self.forms.set_textbox_value('Hive Password', hive_password)
            self.forms.set_textbox_value('HDFS User', hdfs_user)
            self.forms.click_action_button('Next')
        else:
            raise Exception(f'Wrong window is open, {open_form_window} window should be loaded')

        open_form_window = 'Summary'
        # Final window
        if self.forms.is_form_open(open_form_window):
            self.forms.click_action_button('Finish')
        else:
            raise Exception(f'Wrong window is open, {open_form_window} window should be loaded')

    @test_step
    def create_client(self):
        """Access client if exists else creates new one"""
        hadoop_app = self.tcinputs['hadoop_app']
        if not self.instances.is_instance_exists(hadoop_app):
            self.log.info(f"Hadoop pseudo client:{hadoop_app} does not exist, Creating new one")
            hadoop_instance = self.instances.add_hadoop_server()
            hadoop_instance.add_hadoop_parameters(name=hadoop_app,
                                                  access_nodes=self.access_nodes,
                                                  hdfs_user=self.tcinputs.get('hdfs_user', 'hdfs'),
                                                  plan_name=self.tcinputs['plan'])
            hadoop_instance.save()
        else:
            self.log.info(f"Using Existing hadoop pseudo client:{hadoop_app}")

    def _validate_backup(self, backup_tables, dropped_tables):
        """Validates if subclient content is set properly based on existing tables"""
        hadoop_app = self.tcinputs.get('hadoop_app')
        hadoop_instance = self.tcinputs.get('hadoop_instance', hadoop_app)
        client = self.commcell.clients.get(hadoop_app)
        hdfs_bs = client.agents.get('Big Data Apps').instances.get(hadoop_instance).backupsets.get('hdfs')
        sc_list = [sc for sc in hdfs_bs.subclients.all_subclients if sc.startswith(f"cv_hive_{self.source_db}")]
        sc_content = []
        for sc in sc_list:
            sc_content.extend(hdfs_bs.subclients.get(sc).content)
        bkp_content = sorted([content.split('/hive/')[-1].split('_cvtemp_')[0] for content in sc_content if '/cv_hivemeta/' not in content])
        src_del_content = [f"{table.replace('.','.db/')}" for table in dropped_tables]
        src_bkp_content = sorted([f"{table.replace('.','.db/')}" for table in backup_tables])
        for table in src_del_content:
            if table in src_bkp_content:
                log_error = f"Deleted table:{table} is still present in sc_content:{bkp_content}"
                raise Exception(log_error)
        if src_bkp_content != bkp_content:
            log_error = f"subclient content is not matched with existing tables, hive_list:[{src_bkp_content}] and sc_list:[{bkp_content}]"
            self.log.error(log_error)
            raise Exception(log_error)
        else:
            self.log.info("Backup validation using subclient content is successful")

    @test_step
    def generate_data_and_backup(self, backup_type='Full', iteration=None):
        """Generates data in tables and runs hive backup workflow"""
        test_data = self.tcinputs.get('test_data', {})
        test_data = json.loads(test_data) if isinstance(test_data, str) else test_data
        is_incremental = backup_type == 'Incremental'
        force_insert = test_data.get('force_insert', is_incremental)
        self.source_db = self.tcinputs.get('database', f'autodb_{self.id}')
        dropped_tables = []
        if test_data.get('skip_create') or iteration == 1:
            contains = test_data.get('drop_tables', 'orc')
            self.log.info(f"Dropping tables that contains:[{contains}] in its table name")
            dropped_tables = self.hive_helper.drop_tables(database=self.source_db, contains=contains)
            self.hive_helper.acid_the_tables(database=self.source_db)
        else:
            table_modes = test_data.get('table_modes', ['managed'])
            table_types = test_data.get('table_types', ['partition_bucket'])
            file_formats = test_data.get('file_formats', ['orc', 'textfile'])
            table_types = json.loads(table_types) if isinstance(table_types, str) else table_types
            table_modes = json.loads(table_modes) if isinstance(table_modes, str) else table_modes
            file_formats = json.loads(file_formats) if isinstance(file_formats, str) else file_formats
            table_properties = {"transactional_modes": True, "transactional_properties": ['default']}

            self.hive_helper.generate_test_data(database=self.source_db, table_modes=table_modes,
                                                table_types=table_types, file_formats=file_formats,
                                                table_properties=table_properties, serde_properties=True,
                                                force_insert=force_insert)

        backup_tables = self.hive_helper.get_tables(databases=[self.source_db])
        self.destination_db = f"{self.source_db}_{backup_type}_Restore"
        self.hive_helper.drop_database(self.destination_db)

        self.forms.open_workflow(self.hive_backup)
        if self.forms.is_form_open(self.hive_backup):
            self.fill_and_submit_backup_form(backup_type)
            self._workflow.workflow_job_status(self.hive_backup, wait_for_job=True)
        else:
            raise Exception("Workflow Input Window isn't loaded")
        self._validate_backup(backup_tables, dropped_tables)

    @test_step
    def restore_and_validate_data(self):
        """Restores the backed up database using hive restore workflow and validates it against source database"""
        self.admin_console.refresh_page()
        self.forms.open_workflow(self.hive_restore)
        if self.forms.is_form_open(self.hive_restore):
            self.fill_and_submit_restore_form()
            self._workflow.workflow_job_status(self.hive_restore, wait_for_job=True)
        else:
            raise Exception("Workflow Input Window isn't loaded")
        if self.multiple_restores:
            self.log.info("Backup DB is eligible for multiple restores since it contains external and managed tables")
            self.restore_and_validate_data()
        else:
            database_map = {self.destination_db: self.source_db}
            self.hive_helper.validate_test_data(database_map)
            self.hive_helper.drop_database(self.destination_db)

    def run(self):
        """
        Main function for testcase execution
        1) Access the client, creates new client if not present
        2) Generates data in given database and runs two incremental backup using hive backup workflow
        3) For second incremental, some tables are dropped and subclient content validation is done
        4) Restores database using hive restore workflow and validates it against source database
        """
        try:
            self.create_client()
            self.switch_to_webconsole()
            for iteration in range(2):
                self.generate_data_and_backup(backup_type='Incremental', iteration=iteration)
                self.restore_and_validate_data()
        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
