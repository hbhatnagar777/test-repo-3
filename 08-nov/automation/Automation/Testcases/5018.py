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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    check_if_instance_exists()  --  checks if instance exists

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    create_test_data()          --  creates test data

    drop_tablespace()           --  method to drop tablespace

    drop_datafile()             --  method to drop datafile

    new_subclient()             --  method to create new subclient

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore

    validate_restore()          --  validates whether the restore job was successful

    cleanup()                   --  method to cleanup testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "5018":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"XXXX",
                          "AuxiliaryPath":"path"
                        }
            }

"""

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import OracleSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing Partial Database Test for Oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "CMP - Advanced - Data Protection and Recovery - Partial Database"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.subclient_name = 'CV_5018'
        self.tablespace_name1 = 'CV_TEST_01'
        self.tablespace_name2 = 'CV_TEST_02'
        self.datafile1 = None
        self.datafile2 = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None,
            'AuxiliaryPath': None
        }
        self.test_data = [1, 1, 10]
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.machine_object = None
        self.subclient_page = None
        self.add_subclient = None
        self.restore_panel = None
        self.browse = None
        self.db_helper = None
        self.automation_subclient = []

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = OracleSubclient(self.admin_console)
        self.machine_object = Machine(self.client, self.commcell)
        self.restore_panel = OracleRestorePanel(self.admin_console)
        self.browse = RBrowse(self.admin_console)
        self.db_helper = DbHelper(self.commcell)

    def tear_down(self):
        """ Tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name1,
                user="{0}_user".format(self.tablespace_name1.lower()))
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name2,
                user="{0}_user".format(self.tablespace_name1.lower()))

    @test_step
    def check_if_instance_exists(self):
        """ Checking if instance exists """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found")

    @test_step
    def navigate_to_instance(self):
        """ Navigates to specified Instance """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_helper_object(self):
        """ Creates oracle helper object """
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def create_test_data(self):
        """ Generating Sample Data for test """
        num_of_files, table_limit, row_limit = self.test_data
        self.create_helper_object()
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name1, table_limit, num_of_files, row_limit)
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name2, table_limit, num_of_files, row_limit)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.datafile1 = '{0}{1}{2}.dbf'.format(self.oracle_helper_object.db_fetch_dbf_location(),
                                                self.tablespace_name1, 1)
        self.datafile2 = '{0}{1}{2}.dbf'.format(self.oracle_helper_object.db_fetch_dbf_location(),
                                                self.tablespace_name2, 1)
        self.log.info("Test Data Generated successfully")

    @test_step
    def drop_tablespace(self, tablespace_name):
        """ Drops the tablespace from connected database
            Args:
                tablespace_name   (list): List of tablespace names
        """
        for tablespace in tablespace_name:
            self.oracle_helper_object.oracle_data_cleanup(tablespace=tablespace, tables=["CV_TABLE_01"])

    @test_step
    def drop_datafile(self, datafile_name):
        """ Drops the datafile from tablespace
            Args:
                datafile_name   (list): List of datafile names
        """
        for datafile in datafile_name:
            self.machine_object.delete_file(datafile)

    @test_step
    def new_subclient(self, content):
        """ Adding new subclient
            Args:
                content   (list): List of content to be selected
        """
        self.db_instance_details.access_subclients_tab()
        if self.admin_console.check_if_entity_exists('link', self.subclient_name):
            self.db_instance_details.click_on_entity(self.subclient_name)
            self.admin_console.wait_for_completion()
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.subclient_name, plan=self.tcinputs["Plan"],
            backup_mode="Subset of online database", content=content)
        self.log.info("Waiting for subclient creation completion")
        self.admin_console.wait_for_completion()
        self.automation_subclient.append(self.subclient_name)

    @test_step
    def run_backup(self):
        """ Method to run backup """
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.db_helper.wait_for_job_completion(job_id)
        self.log.info("Oracle Full Backup is completed!")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])

    @test_step
    def run_restore(self, tablespaces=None, datafiles=None, recover_to=None):
        """ Method to run restore
            Args:
                tablespaces   (list): List of tablespaces to be selected
                datafiles     (dict): Dictionary containing the tablespace names as keys
                                      and datafiles to be selected under them as values
                recover_to     (str): Recover to value Ex:"most recent backup"
        """
        self.db_instance_details.access_restore()
        self.db_instance_details.clear_all_selection()
        if tablespaces:
            self.browse.select_files(file_folders=tablespaces)
        if datafiles:
            self.browse.select_from_multiple_pages(mapping_dict=datafiles)
        self.browse.submit_for_restore()
        job_id = self.restore_panel.in_place_restore(auxiliary_path=self.tcinputs['AuxiliaryPath'],
                                                     recover_to=recover_to)
        self.db_helper.wait_for_job_completion(job_id)
        self.log.info("Restore completed!")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])

    @test_step
    def validate_restore(self, datafile_name=None):
        """ Validates if the restore job was successful
            Args:
                datafile_name   (list): List of datafile names to validate
        """
        num_of_files, table_limit, row_limit = self.test_data
        self.oracle_helper_object.validation(
            self.tablespace_name1, num_of_files, "CV_TABLE_", row_limit, table_limit)
        self.oracle_helper_object.validation(
            self.tablespace_name2, num_of_files, "CV_TABLE_", row_limit, table_limit)
        if datafile_name:
            for datafile in datafile_name:
                if self.machine_object.check_file_exists(datafile):
                    self.log.info(f"Validation of {datafile} is successful")
                else:
                    raise CVTestStepFailure(f"Validation of {datafile} is failed !")
        self.log.info("Validation Successful")

    @test_step
    def cleanup(self):
        """ Cleans up testcase created data """
        self.log.info("Deleting automation created subclients")
        self.navigate_to_instance()
        for subclient in self.automation_subclient:
            self.db_instance_details.click_on_entity(subclient)
            self.subclient_page.delete_subclient()

    def run(self):
        """ Main function for test case execution """
        try:
            self.check_if_instance_exists()
            self.navigate_to_instance()
            self.create_test_data()
            self.db_instance_details.click_on_entity('default')
            self.run_backup()

            self.log.info("####### 1. Backup and Restore some Tablespaces #######")
            content = [self.tablespace_name1, self.tablespace_name2]
            self.new_subclient(content)
            self.run_backup()
            self.drop_tablespace(tablespace_name=content)
            self.run_restore(tablespaces=content)
            self.validate_restore()

            self.log.info("####### 2. Backup and Restore some Datafiles #######")
            self.subclient_name = self.subclient_name + "_1"
            content = [self.datafile1, self.datafile2]
            self.new_subclient(content)
            self.run_backup()
            self.drop_datafile(datafile_name=content)
            self.run_restore(datafiles={self.tablespace_name1: [content[0]], self.tablespace_name2: [content[1]]},
                             recover_to="Most Recent Backup")
            self.validate_restore(datafile_name=content)

            self.log.info("####### 3. Backup and Restore some Tablespaces and Datafiles #######")
            self.subclient_name = self.subclient_name.split('_1')[0] + "_2"
            content = [self.tablespace_name1, self.datafile2]
            self.new_subclient(content)
            self.run_backup()
            self.drop_tablespace(tablespace_name=[content[0]])
            self.drop_datafile(datafile_name=[content[1]])
            self.run_restore(tablespaces=[content[0]], datafiles={self.tablespace_name2: [content[1]]})
            self.validate_restore(datafile_name=[content[1]])

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
