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

    wait_for_job_completion()   --  Waits for completion of job and gets the
                                    end date once job completes

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    restore_instance()          --  method to run restore

    create_mysql_helper_object()--  creates object of MYSQLHelper class

    create_test_data()          --  method to create test databases according to input

    set_subclient_content()     --  sets content of the subclient to database list
                                    argument passed as input

    first_phase()               --  method to get the first phase of the job
                                    represented by input job id

    backup_subclient()          --  method to run backup job

    check_if_instance_exists()  --  method to check if instance with given name exists

    validate_db_sizes()         --  method to compare size of databases in master and
                                    standby instances
                                    
    cleanup()                   --  method to remove testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "57844": {
                    "TestData": [10, 20, 100], (eg. [No. of Databases, No. of Tables, No. of Rows)
                    "MasterInfo": [client_name, instance_name],
                    "StandbyInfo": [client_name, instance_name]
                }
            }

"""

import time
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Class for executing test for MySQL Proxy Backup from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MySQL Proxy Backup from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.master_helper_object = None
        self.standby_helper_object = None
        self.standby_dbhelper_object = None
        self.restore_panel = None
        self.database_group = None
        self.db_group_content = None
        self.page_container = None
        self.tcinputs = {
            "TestData": [None, None, None],
            "MasterInfo": [None, None],
            "StandbyInfo": [None, None]
        }

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        self.master_helper_object.cleanup_test_data("auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_instance(self, instance_name, client_name):
        """Navigates to Instance page
        Args:
            instance_name   (str):  Name of the instance to navigate to
            client_name     (str):  Name of the client
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL, instance_name,
                                                client_name)

    @test_step
    def restore_instance(self, data_restore, log_restore, db_list, instance_name):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            db_list  (list):  List of databases to restore
            instance_name   (str): Name iof the instance restoring
        """
        if data_restore and log_restore:
            info = "Data + Log "
        else:
            info = "Data only " if data_restore else "Log only "
        info += "restore"
        self.log.info(info)
        self.admin_console.select_breadcrumb_link_using_text(instance_name)
        self.db_instance_details.access_restore()
        self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL, db_list)
        job_id = self.restore_panel.in_place_restore(data_restore=data_restore,
                                                     log_restore=log_restore)
        self.wait_for_job_completion(job_id)

    @test_step
    def create_mysql_helper_object(self):
        """Creates object of SDK mysqlhelper class"""
        master_machine_object = Machine(self.tcinputs["MasterInfo"][0], self.commcell)
        master_client = master_machine_object.client_object
        master_instance = master_client.agents.get("MySQL").instances.get(
            self.tcinputs["MasterInfo"][1])

        master_connection_info = {
            'client_name': self.tcinputs["MasterInfo"][0],
            'instance_name': self.tcinputs["MasterInfo"][1],
            'socket_file': master_instance.properties['mySqlInstance']['port']
        }
        self.master_helper_object = MYSQLHelper(commcell=self.commcell,
                                                hostname=master_client.client_hostname,
                                                user=master_instance.mysql_username,
                                                port=int(
                                                    self.tcinputs["MasterInfo"][1].split("_")[1]),
                                                connection_info=master_connection_info)

        standby_machine_object = Machine(self.tcinputs["StandbyInfo"][0], self.commcell)
        standby_client = standby_machine_object.client_object
        standby_instance = standby_client.agents.get("MySQL").instances.get(
            self.tcinputs["StandbyInfo"][1])

        standby_connection_info = {
            'client_name': self.tcinputs["StandbyInfo"][0],
            'instance_name': self.tcinputs["StandbyInfo"][1],
            'socket_file': standby_instance.properties['mySqlInstance']['port']
        }
        self.standby_helper_object = MYSQLHelper(commcell=self.commcell,
                                                 hostname=standby_client.client_hostname,
                                                 user=standby_instance.mysql_username,
                                                 port=int(
                                                     self.tcinputs["StandbyInfo"][1].split(
                                                         "_")[1]),
                                                 connection_info=standby_connection_info)
        self.standby_dbhelper_object = database_helper.MySQL(standby_client.client_hostname,
                                                             self.standby_helper_object.usr,
                                                             self.standby_helper_object.pwd,
                                                             self.standby_helper_object.port)
        self.standby_dbhelper_object.start_slave()

    @test_step
    def create_test_data(self, prefix):
        """Creates test databases according to input
            returns:    list of names of databases created
        """
        timestamp = str(int(time.time()))
        if self.tcinputs["TestData"] is not None:
            num_of_db, num_of_tables, num_of_rows = self.tcinputs["TestData"]
            db_list = self.master_helper_object.generate_test_data(prefix+"_"+timestamp,
                                                                   num_of_db,
                                                                   num_of_tables,
                                                                   num_of_rows)
        else:
            db_list = self.master_helper_object.generate_test_data(
                database_prefix=prefix+"_"+timestamp)
        return db_list

    @test_step
    def set_subclient_content(self, db_list):
        """Sets subclient content to test databases
        Args:
            db_list  (list):  List of databases to be in subclient content
        """
        self.admin_console.refresh_page()
        self.database_group.edit_content(db_list)

    @test_step
    def first_phase(self, job_id):
        """ Returns first phase of given job id of MySQL Database Backup
            Args:
                job_id  (str)   :   ID of the job
            Returns:
                first phase of job
        """
        csdb = database_helper.get_csdb()
        query = "select name from JMPhase where opTableId in (select id from JMOpTable where" \
                " opName='MySQL Database Backup') and phase in (select top 1 phase from" \
                " JMBkpAtmptStats with (NOLOCK) where jobID="+job_id+")"
        csdb.execute(query)
        jlist = csdb.fetch_one_row()
        return jlist[0]

    @test_step
    def backup_subclient(self, backup_type):
        """Executes backup according to backup type
        Args:
            backup_type  (Backup.BackupType):  Type of backup required
        """
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            self.wait_for_job_completion(job_id)
            if self.first_phase(job_id) == 'ProxyCheck':
                self.log.info("Verified first phase of backup is ProxyCheck")
            else:
                raise Exception("First phase of backup job is not ProxyCheck")
        elif backup_type.value == "INCREMENTAL":
            self.log.info("Incremental Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            self.wait_for_job_completion(job_id)

    @test_step
    def check_if_instance_exists(self, instance_name, client_name):
        """Method to check if instance exists
        Args:
            instance_name    (str):  Name of the instance to check
            client_name      (str):  Name of the client
        """
        self.log.info("Checking if %s instance exists", instance_name)
        if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL, instance_name,
                                                      client_name):
            self.log.info("Instance found")
        else:
            raise Exception("{0} instance not found. Create instance "
                            "of database server".format(instance_name))

    @test_step
    def validate_db_sizes(self):
        """Method to validate database info in master and standby servers"""
        master_db_list = self.master_helper_object.get_database_information()
        self.log.info("Waiting for 30 seconds before continuing testcase execution")
        time.sleep(30)
        standby_db_list = self.standby_helper_object.get_database_information()
        self.master_helper_object.validate_db_info(master_db_list, standby_db_list)

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigate_to_instance(self.tcinputs["MasterInfo"][1], self.tcinputs["MasterInfo"][0])
        self.db_instance_details.click_on_entity("default")
        self.set_subclient_content(self.db_group_content)

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.check_if_instance_exists(self.tcinputs["StandbyInfo"][1],
                                          self.tcinputs["StandbyInfo"][0])
            self.check_if_instance_exists(self.tcinputs["MasterInfo"][1],
                                          self.tcinputs["MasterInfo"][0])
            self.log.info("Navigating to Master instance")
            self.navigate_to_instance(self.tcinputs["MasterInfo"][1],
                                      self.tcinputs["MasterInfo"][0])
            self.db_instance_details.enable_standby_instance_backup(
                self.tcinputs["StandbyInfo"][1])
            self.page_container.select_entities_tab()
            self.db_instance_details.click_on_entity("default")
            self.database_group.enable_standby_backup()
            self.create_mysql_helper_object()

            self.db_group_content = self.database_group.database_group_autodiscovered_content()
            db_list = self.create_test_data("auto")
            self.admin_console.refresh_page()
            if not self.standby_dbhelper_object.slave_status():
                raise Exception("Slave has not started")
            self.validate_db_sizes()
            self.backup_subclient(RBackup.BackupType.FULL)
            self.master_helper_object.populate_database(subclient_content=db_list)
            self.validate_db_sizes()
            self.backup_subclient(RBackup.BackupType.INCR)
            self.master_helper_object.populate_database(subclient_content=db_list)
            self.validate_db_sizes()
            self.backup_subclient(RBackup.BackupType.INCR)

            self.master_helper_object.cleanup_test_data("auto")
            self.restore_instance(data_restore=True, log_restore=True,
                                  db_list=db_list,
                                  instance_name=self.tcinputs["MasterInfo"][1])
            self.validate_db_sizes()
            self.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
