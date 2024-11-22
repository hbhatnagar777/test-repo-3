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

    navigate_to_instance()      --  navigates to specified instance

    check_prerequisite()        --  method to check the snap and block level properties

    restore_and_validate()      --  method to perform restore and validation of data restored

    backup_and_validate()        -- method to perform backup and validation of backup-copy jobs

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "71097": {
                    "ClientName": "mysql",
                    "InstanceName": "mysql_1_3306",
                    "Port": "3306",
                    "AgentName": "MySQL",
                    "SubclientName": "default",
                    "SocketFile": "/var/lib/mysql/mysql.sock", // For unix client
                    "ProxyClientNameName": "mysql_proxy",
                    "ProxyIP": "172.11.226.192",
                    "ProxyUsername": "administartor",
                    "ProxyPassword": "pswd",
                    "ProxyInstanceNumber": "001" //Example :Instance001/002/003
                }
            }
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing MySQL Snap backups with proxy for backup copy on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'MySQL Snap backups with proxy for backup copy'
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.database_group = None
        self.db_group_content = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "Port": None,
            "SubclientName": None,
            "ProxyClientName": None,
            "ProxyIP": None,
            "ProxyUsername": None,
            "ProxyPassword": None,
            "ProxyInstanceNumber": None
        }
        self.helper_object = None
        self.dbhelper = None
        self.db_list = None
        self.start_services = False
        self.proxy_machine_object = None
        self.restore_panel = None

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.dbhelper = DbHelper(self.commcell)
        connection_info = {
            'client_name': self.client.client_name,
            'instance_name': self.instance.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell, hostname=self.client.client_hostname,
                                         user=self.instance.mysql_username,
                                         port=self.tcinputs["Port"], connection_info=connection_info
                                         )
        self.proxy_machine_object = Machine(machine_name=self.tcinputs["ProxyIP"],
                                            username=self.tcinputs["ProxyUsername"],
                                            password=self.tcinputs["ProxyPassword"])
        self.proxy_machine_object.instance = self.tcinputs['ProxyInstanceNumber']

    def tear_down(self):
        """Tear down method for TC"""
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance.instance_name,
                                                self.client.client_name)

    @test_step
    def check_prerequisite(self, use_source=False):
        """ method to check the snap and block level properties
        Args:
            use_source (bool) : To enable use source if access node is unreachable toggle
        """
        subclient_page = MySQLSubclient(self.admin_console)
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        snap_engine = subclient_page.get_snap_engine()
        if snap_engine == "native":
            raise CVTestStepFailure("Engine type is native, TC requires hardware engine setup")
        if "unix" in self.client.os_info.lower():
            if subclient_page.is_blocklevel_backup_enabled():
                self.log.info("Disabling block level option as it is enabled")
                subclient_page.disable_blocklevel_backup()
        subclient_page.disable_snapshot()
        if use_source:
            subclient_page.enable_snapshot(snap_engine, proxy_node=self.tcinputs['ProxyClientName'], use_source=True)
            self.log.info("### Stoping all commvault services in the Proxy Client machine ###")
            self.proxy_machine_object.stop_all_cv_services()
            self.start_services = True
        else:
            subclient_page.enable_snapshot(snap_engine, proxy_node=self.tcinputs['ProxyClientName'])
        self.admin_console.refresh_page()

    @test_step
    def restore_and_validate(self, db_list):
        """
        Executes restore according to restore type input and validates restore
            db_list  (dict): Dictionary of database content before restore for validation
        """
        self.navigate_to_instance()
        self.db_instance_details.access_actions_item_of_entity(
            entity_name=self.tcinputs['SubclientName'], action_item="Restore")
        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, all_files=True)
        self.log.info("Data + Log Restore")
        job_id = self.restore_panel.in_place_restore(data_restore=True,
                                                     log_restore=True)
        self.dbhelper.wait_for_job_completion(job_id)
        db_info_after_restore = self.helper_object.get_database_information()
        self.helper_object.validate_db_info(db_list, db_info_after_restore)

    @test_step
    def backup_and_validation(self, use_source=False):
        """ Method to perform backup and validation
            use_source (bool) : To enable the toggle, use source if access node is unreachable
        """
        if use_source:
            self.log.info("Verify option Use source if access node is unreachable")
            self.check_prerequisite(use_source=True)

        self.log.info("Full Backup")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.FULL)
        self.dbhelper.wait_for_job_completion(job_id)

        log_jobid = self.dbhelper.get_snap_log_backup_job(job_id)
        self.log.info("Log backup job with ID:%s is now completed", log_jobid)

        db_info = self.helper_object.get_database_information()

        self.log.info("Run backup copy for the full job")
        self.dbhelper.run_backup_copy(self.subclient.storage_policy)
        backup_copy_job_obj = self.dbhelper.get_backup_copy_job(job_id)
        if use_source:
            if not self.dbhelper.check_if_backup_copy_run_on_proxy(
                    backup_copy_job_obj.job_id,
                    self.commcell.clients.get(self.tcinputs['ClientName'])):
                raise CVTestStepFailure("Source client was not used for backup copy")
            else:
                self.log.info("### Source client was used for backup copy ###")
        else:
            if not self.dbhelper.check_if_backup_copy_run_on_proxy(
                    backup_copy_job_obj.job_id,
                    self.commcell.clients.get(self.tcinputs['ProxyClientName'])):
                raise CVTestStepFailure("Proxy client was not used for backup copy")
            else:
                self.log.info("### Proxy client was used for backup copy ###")
        return db_info

    def cleanup(self):
        """Removes testcase created changes"""
        if self.start_services:
            self.log.info("### Starting all the commvault services on the Proxy Client machine###")
            self.proxy_machine_object.start_all_cv_services()

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.subclient.subclient_name)
            self.check_prerequisite()
            db_list = self.helper_object.generate_test_data(f"auto_{int(time.time())}")
            self.backup_and_validation()
            self.helper_object.populate_database(subclient_content=db_list)
            db_info = self.backup_and_validation(use_source=True)
            self.helper_object.cleanup_test_data("auto")
            self.restore_and_validate(db_list=db_info)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
