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

    create_sybase_helper_object()--  creates object of MYSQLHelper class

    backup_validate()          --  method to run backup job

    restore_validate()          --  method to run restore and validate test data

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59266": {
                    "ClientName": "sybase_client",
                    "InstanceName": "sybase_instance",
                    "DestinationClient": "destination_sybase_client",
                    "DestinationInstance": "destination_sybase_instance"
                    "InPlaceRedirectPath": "C://",  (Path to restore data files to,
                                                    including separator)
                    "OutOfPlaceRedirectPath": "C://"(Path to restore data files to,
                                                    including separator)
                }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.SybaseUtils.sybasehelper import SybaseHelper, SybaseCVHelper


class TestCase(CVTestCase):
    """ Class for executing Single DB redirect restore Sybase IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Single DB redirect restore Sybase IDA Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper = None
        self.cv_helper = None
        self.destination_helper = None
        self.destination_cv_helper = None
        self.restore_panel = None
        self.database_group = None
        self.database_name = "CV_59266"
        self.in_place_delete = [self.database_name]
        self.out_of_place_delete = []
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "DestinationClient": None,
            "DestinationInstance": None,
            "InPlaceRedirectPath": None,
            "OutOfPlaceRedirectPath": None
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
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.database_group = SubClient(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        for database in self.in_place_delete:
            self.cv_helper.sybase_cleanup_test_data(database)
        for database in self.out_of_place_delete:
            self.destination_cv_helper.sybase_cleanup_test_data(database)

        self.helper.sybase_helper_cleanup()
        self.destination_helper.sybase_helper_cleanup()

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.SYBASE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_sybase_helper_object(self):
        """Creates object of sybasehelper class"""
        self.instance = self.client.agents.get("sybase").instances.get(
            self.tcinputs["InstanceName"])
        self.helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.cv_helper = SybaseCVHelper(self.helper)
        self.helper.csdb = self.csdb
        # Setting Sybase Instance user password
        self.helper.sybase_sa_userpassword = self.helper.get_sybase_user_password()
        destination_client_name = self.tcinputs["DestinationClient"]
        destination_instance_name = self.tcinputs["DestinationInstance"]
        destination_client = self.commcell.clients.get(destination_client_name)
        destination_instance = destination_client.agents.get("sybase").instances.get(
            destination_instance_name)
        self.destination_helper = SybaseHelper(
            self.commcell, destination_instance, destination_client)
        self.destination_cv_helper = SybaseCVHelper(self.destination_helper)
        self.destination_helper.csdb = self.csdb
        self.destination_helper.sybase_sa_userpassword =\
            self.destination_helper.get_sybase_user_password()

    @test_step
    def backup_and_validate(self, backup_type):
        """Executes backup according to backup type and validates backup
        Args:
            backup_type  (Backup.BackupType):  Type of backup required
        """
        actual_backup_type = ""
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
            actual_backup_type = "Full"
        elif backup_type.value == "INCREMENTAL":
            self.log.info("Transaction Log Backup")
            actual_backup_type = "Transaction Log"
        job_id = self.database_group.backup(backup_type=backup_type)
        self.wait_for_job_completion(job_id)
        status = self.cv_helper.common_utils_object.backup_validation(
            job_id, actual_backup_type)
        if status:
            self.log.info("Backup Validation successful")
        else:
            raise CVTestStepFailure("Failed in job validation: {0}".format(job_id))

    @test_step
    def single_database_restore_validate(self, database_name, user_table_list,
                                         in_place=True):
        """Executes restore according to restore type input and validates restore
            database_name  (str):  Database name
            user_table_list     (str):  List of tables in database
            in_place            (bool): True if restore to be done in place
                default: True
        """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["InstanceName"])
        status, all_database_list_before_restore = self.helper.get_database_list()
        table_list_before = self.helper.get_table_list(database_name)
        table_content_before = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_before[table] = self.helper.get_table_content(database_name,
                                                                                table)
        device_list_source = self.helper.get_device_name(database_name)

        database_status = False
        device_status = False
        if in_place:
            # Drop database before in place restore
            self.cv_helper.sybase_cleanup_test_data(database_name)
            self.log.info("In place restore of single database")
            self.admin_console.recovery_point_restore()
            self.restore_panel = self.database_group.restore_folders(
                DBInstances.Types.SYBASE, items_to_restore=[database_name])
            job_id = self.restore_panel.in_place_restore(
                database_names=[database_name], path=self.tcinputs['InPlaceRedirectPath'])
            in_place_redirect_options = self.restore_panel.redirect_options_dict
            self.wait_for_job_completion(job_id)
            new_database_name = (
                in_place_redirect_options)[database_name][device_list_source[1]]['target_db'] or (
                    in_place_redirect_options)[database_name][device_list_source[0]]['target_db']
            if len(new_database_name) == 0:
                new_database_name = database_name
            if new_database_name not in self.in_place_delete:
                self.in_place_delete.append(new_database_name)
            device_list = [in_place_redirect_options[database_name][device]['device_name']
                           for device in device_list_source]
            device_list.sort()
            device_path_list = [in_place_redirect_options[database_name][device]['physical_path']
                                for device in device_list_source]
            device_path_list.sort()
            status, all_database_list_after_restore = self.helper.get_database_list()
            database_status = (new_database_name in all_database_list_after_restore)
            table_list_after = self.helper.get_table_list(new_database_name)
            table_content_after = dict.fromkeys(user_table_list, None)
            for table in user_table_list:
                status, table_content_after[table] = self.helper.get_table_content(
                    new_database_name, table)
            device_list_destination = self.helper.get_device_name(new_database_name)
            device_list_destination.sort()
            device_path_list_destination = [self.helper.get_device_path(
                device)[1] for device in device_list_destination]
            device_path_list_destination.sort()

        else:
            self.log.info("Out of place restore of single database")
            self.admin_console.recovery_point_restore()
            self.restore_panel = self.database_group.restore_folders(
                DBInstances.Types.SYBASE, items_to_restore=[database_name])
            job_id = self.restore_panel.out_of_place_restore(
                destination_client=self.tcinputs['DestinationClient'],
                destination_instance=self.tcinputs['DestinationInstance'],
                database_names=[database_name], path=self.tcinputs['OutOfPlaceRedirectPath'])
            out_of_place_redirect_options = self.restore_panel.redirect_options_dict
            self.wait_for_job_completion(job_id)

            new_database_name = (
                out_of_place_redirect_options)[database_name][device_list_source[1]]['target_db']\
                or (
                    out_of_place_redirect_options)[database_name][device_list_source[0]][
                        'target_db']
            if len(new_database_name) == 0:
                new_database_name = database_name
            if new_database_name not in self.out_of_place_delete:
                self.out_of_place_delete.append(new_database_name)
            device_list = [out_of_place_redirect_options[database_name][device]['device_name']
                           for device in device_list_source]
            device_list.sort()
            device_path_list = \
                [out_of_place_redirect_options[database_name][device]['physical_path']
                 for device in device_list_source]
            device_path_list.sort()
            status, all_database_list_after_restore = self.destination_helper.get_database_list()
            database_status = (new_database_name in all_database_list_after_restore)
            table_list_after = self.destination_helper.get_table_list(new_database_name)
            table_content_after = dict.fromkeys(user_table_list, None)
            for table in user_table_list:
                status, table_content_after[table] = self.destination_helper.get_table_content(
                    new_database_name, table)
            device_list_destination = self.destination_helper.get_device_name(new_database_name)
            device_list_destination.sort()
            device_path_list_destination = [self.destination_helper.get_device_path(
                device)[1] for device in device_list_destination]
            device_path_list_destination.sort()

        database_content_status = self.cv_helper.table_validation(table_list_before,
                                                                  table_list_after,
                                                                  table_content_before,
                                                                  table_content_after)
        device_name_status = (device_list == device_list_destination)
        device_path_status = all(device_path.startswith(device_path_destination)
                                 for device_path, device_path_destination
                                 in zip(device_path_list, device_path_list_destination))
        device_status = device_name_status and device_path_status
        self.log.info("Database status : %s", database_status)
        self.log.info("Database List before : %s", all_database_list_before_restore)
        self.log.info("Database List after : %s", all_database_list_after_restore)
        self.log.info("Database Content status after validation : %s", database_content_status)
        self.log.info("Device status : %s", device_status)
        self.log.info("Device List before : %s", device_list_source)
        self.log.info("New Device list given in redirect options: %s", device_list)
        self.log.info("New Device paths given in redirect options: %s", device_path_list)
        self.log.info("Device List after : %s", device_list_destination)
        self.log.info("Device paths after : %s", device_path_list_destination)

        if database_status and database_content_status and device_status:
            return True
        else:
            raise CVTestStepFailure("Restore validation failed after single db restore")

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.SYBASE,
                                                          self.tcinputs["InstanceName"],
                                                          self.tcinputs["ClientName"]):
                self.log.info("Instance found")
                self.navigate_to_instance()
            else:
                raise Exception("Instance not found. Create instance of database"
                                " server and execute the testcase")
            self.db_instance_details.click_on_entity("default")
            self.create_sybase_helper_object()
            user_tables = ["T_FULL"]
            self.cv_helper.sybase_populate_data(self.database_name, user_tables[0])
            self.backup_and_validate(Backup.BackupType.FULL)

            restore_status = self.single_database_restore_validate(
                database_name=self.database_name, user_table_list=user_tables,
                in_place=False)
            if restore_status:
                self.log.info("Single database out of place Restore Succeeded")

            restore_status = self.single_database_restore_validate(
                database_name=self.database_name, user_table_list=user_tables)
            if restore_status:
                self.log.info("Single database in place Restore Succeeded")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
