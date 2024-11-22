"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function for this testcase

    tear_down()         --  tear down function to delete automation generated data

    get_active_log()    --  Fetches DB2 Database active log file number using db2 helper

    run()               --  run function of this test case

Input Example:
    "testCases":
            {
                "64310":
                        {
                            "ClientName": "client_name",
                            "AgentName": "DB2",
                            "Instance": "db2_instance_name",
                            "Backupset": "database_name",
                            "Subclient": "subclient_name",
                            "StoragePolicyName": "plan_name",
                            "DB2User": "db2_instance_user",
                            "DB2UserPassword": "db2_user_password",
                            "DB2HomePath": "instance_home_path",
                            "DB2Port": "60000"
                        }
            }
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ GUI Backup's and restore check from dump location """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1 Test for DB2 1 Min RPO from GUI to verify restores from dump location"
        self.db2_helper = None
        self.machine_obj = None
        self.db2_user = None
        self.db2_password = None
        self.db2_instance = None
        self.db2_home = None
        self.db2_dbname = None
        self.storagepolicy = None
        self.table_name = None
        self.tablespace_name = None
        self.loadcopy_tablespace = None
        self.loadcopy_table = None
        self.subclient = None
        self.port = None
        self.os_info = None
        self.datafile = None
        self.dbhelper_object = None
        self.ma_obj = None
        self.tcinputs = {
            'Instance': None,
            'Backupset': None,
            'Subclient': None,
            'StoragePolicyName': None,
            'DB2User': None,
            'DB2UserPassword': None,
            'DB2HomePath': None,
            'DB2Port': None
        }

    def setup(self):
        """setup function for this testcase"""
        self.machine_obj = Machine(self.client)
        self.db2_user = self.tcinputs['DB2User']
        self.db2_password = self.tcinputs['DB2UserPassword']
        self.db2_instance = self.tcinputs['Instance']
        self.db2_home = self.tcinputs['DB2HomePath']
        self.db2_dbname = self.tcinputs['Backupset']
        self.subclient = self.tcinputs['Subclient']
        self.storagepolicy = self.tcinputs['StoragePolicyName']
        self.table_name = "T64310"
        self.tablespace_name = "TS64310"
        self.loadcopy_tablespace = "LOADTBS"
        self.loadcopy_table = "LOADTB"
        self.os_info = self.client.os_info
        self.port = None if len(str(self.tcinputs['DB2Port']).strip()) == 0 else str(self.tcinputs['DB2Port']).strip()
        self.dbhelper_object = DbHelper(self.commcell)
        self.ma_obj = Machine(self.dbhelper_object.get_ma_names(self.storagepolicy)[0], self.commcell)

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created Tablespaces")
        self.db2_helper.reconnect()
        if self.db2_helper is not None:
            self.db2_helper.drop_tablespace(self.tablespace_name)
            self.db2_helper.drop_tablespace(self.loadcopy_tablespace)
        self.log.info("Deleting automation created Schedule policy")
        if self.commcell.schedule_policies.has_policy('db2_sweep_schedule'):
            self.log.info("Deleting the automation created sweep schedule policy")
            self.commcell.schedule_policies.delete('db2_sweep_schedule')

    @test_step
    def get_active_log(self):
        """ gets current active log file number """
        try:
            self.log.info(f"Fetching the active log file of DB {self.tcinputs['Backupset']}")
            self.db2_helper.reconnect()
            active_log_number = self.db2_helper.get_active_logfile()[1]
            self.log.info(f"Active log file number of given DB {self.tcinputs['Backupset']} is {active_log_number}")
            return active_log_number
        except Exception as exception:
            self.log.info(f"Failed to get active log number of db {self.tcinputs['Backupset']}")
            raise CVTestStepFailure(exception) from exception

    def run(self):
        """executes basic acceptance test case DB2 """

        try:

            db2_instance_options_windows = {"domain_name": self.client.client_name,
                                            "password": self.db2_password,
                                            "user_name": self.db2_user,
                                            "instance_name": self.db2_instance,
                                            "home_directory": self.db2_home,
                                            "data_storage_policy": self.storagepolicy,
                                            "log_storage_policy": self.storagepolicy,
                                            "command_storage_policy": self.storagepolicy,
                                            "storage_policy": self.storagepolicy}

            db2_instance_options = {"password": self.db2_password,
                                    "user_name": self.db2_user,
                                    "instance_name": self.db2_instance,
                                    "home_directory": self.db2_home,
                                    "data_storage_policy": self.storagepolicy,
                                    "log_storage_policy": self.storagepolicy,
                                    "command_storage_policy": self.storagepolicy,
                                    "storage_policy": self.storagepolicy}

            db2_backupset_options = {"backupset_name": self.db2_dbname,
                                     "storage_policy_name": self.storagepolicy}

            try:
                instances = self.agent.instances
                if instances.has_instance(instance_name=self.tcinputs['Instance']):
                    self.log.info("Deleting instance from CS as it already exist!")
                    instances.delete(self.tcinputs['Instance'])
                    instances.refresh()
                    self.commcell.refresh()
                    self.log.info("Sleeping for 10sec before creating new instance")
                    time.sleep(10)
                self.log.info("creating instance")
                if 'windows' in self.os_info.lower():
                    self.instance = self.agent.instances.add_db2_instance(
                        db2_instance_options_windows)
                else:
                    self.instance = self.agent.instances.add_db2_instance(
                        db2_instance_options)
            except Exception as exp:
                self.log.error('add instance failed: %s exp ', exp)
            self.commcell.refresh()
            try:
                self.instance = self.agent.instances.get(
                    db2_instance_options['instance_name'])
                self.log.info("trying to add backupset")
                try:
                    self.log.info(
                        "If backupset already exists, it will be deleted and recreated ")
                    self.backupset = self.instance.backupsets.get(
                        db2_backupset_options['backupset_name'])
                    self.instance.backupsets.delete(
                        db2_backupset_options['backupset_name'])
                    self.backupset = self.instance.backupsets.add(
                        self.db2_dbname, storage_policy=self.storagepolicy)
                except BaseException:
                    self.backupset = self.instance.backupsets.add(
                        self.db2_dbname, storage_policy=self.storagepolicy)
            except BaseException:
                self.log.info("backupset exists")
                self.backupset = self.instance.backupsets.get(
                    db2_backupset_options['backupset_name'])
            try:
                self.subclient = self.backupset.subclients.add(
                    self.subclient, self.storagepolicy)
                self.log.info("subclient created successfully")
                self.subclient.refresh()
            except BaseException:
                self.log.info("subclient exists")
                self.subclient = self.backupset.subclients.get(self.subclient)

            self.commcell.refresh()

            self.log.info("######### loading db2helper ##########")
            self.db2_helper = DB2(
                self.commcell, self.client, self.instance, self.backupset, port=self.port)
            self.datafile = self.db2_helper.get_datafile_location()

            self.log.info("#####Get Version#######")
            version = self.db2_helper.get_db2_version()
            self.log.info("Version: %s", version)
            self.log.info("#####Update Db2 Config#######")
            self.db2_helper.update_db2_database_configuration1()
            self.log.info("#####Create New Database#######")

            self.log.info("##### Creating test Data#######")

            self.db2_helper.create_table2(
                self.datafile, self.tablespace_name, self.table_name + "_FULL", True)
            (tblcont_full, tablespace_list, tablespace_count) = self.db2_helper.prepare_data(
                self.table_name + "_FULL")

            if "{}{}_Full.dbf.ORG".format(self.datafile, self.tablespace_name):
                self.machine_obj.delete_file(
                    "{}{}_Full.dbf.ORG".format(
                        self.datafile, self.tablespace_name))

            self.log.info("Creating and enabling One Min RPO at schedule policy")
            self.db2_helper.create_sweep_schedule_policy()

            self.log.info(
                " ##### CASE 1 : FULL/INCR/DELTA command line backups ####")
            self.log.info(
                "#####Running  Command Line online full Backup#######")
            backup_time_stamp = self.db2_helper.third_party_command_backup(
                self.backupset.backupset_name.upper(), "FULL")
            if 'windows' in self.os_info.lower():
                self.db2_helper.third_party_command(
                    "set-item -path env:DB2CLP -value **$$** ;"
                    " db2 connect to {0}; db2 prune history {1} with force option and delete".format(
                        self.db2_dbname, backup_time_stamp))
            else:
                self.db2_helper.third_party_command(
                    "db2 connect to {0}; db2 prune history {1} with force option and delete".format(
                        self.db2_dbname, backup_time_stamp))
            backup_time_stamp = self.db2_helper.third_party_command_backup(
                self.backupset.backupset_name.upper(), "FULL")
            operation_type = ['N', 'O', 'E']

            self.db2_helper.backup_validation(
                operation_type[0], tablespace_list, backup_time_stamp)

            self.log.info(
                "###Running command line online incremental backup #####")
            self.db2_helper.create_table2(
                self.datafile, self.tablespace_name, self.table_name + "_INCR", False)
            backup_time_stamp1 = self.db2_helper.third_party_command_backup(
                self.backupset.backupset_name.upper(), "INCREMENTAL")
            operation_type = ['N', 'O', 'E']
            self.db2_helper.backup_validation(
                operation_type[1], tablespace_list, backup_time_stamp1)

            self.log.info("###Running command line online  delta backup #####")
            self.db2_helper.create_table2(
                self.datafile, self.tablespace_name, self.table_name + "_DELTA", False)
            backup_time_stamp2 = self.db2_helper.third_party_command_backup(
                self.backupset.backupset_name.upper(), "DELTA")
            operation_type = ['N', 'O', 'E']
            self.db2_helper.backup_validation(
                operation_type[2], tablespace_list, backup_time_stamp2)

            self.log.info("sleeping for 30sec")
            time.sleep(30)
            self.log.info("Validating if one min rpo is enabled at backupset level")

            boolean = self.db2_helper.verify_one_min_rpo_backupset_level()
            if not boolean:
                raise Exception(
                    "Test case Failed as ONE MIN RPO is not working and schedule policy not working at backupset level")

            self.log.info(
                " #### CASE 2 : Archiving logs, load copy images and checking if they are moving to dump location ####")

            active_log_number = self.get_active_log()

            self.log.info("archiving logs for 50 times")
            self.db2_helper.db2_archive_log(
                self.backupset.backupset_name.upper(), 50)
            self.db2_helper.get_active_logfile()
            self.log.info("sleeping for 180 sec")
            time.sleep(180)

            self.log.info("Generating load copy images for 5 times")
            output = self.db2_helper.db2_load_copy(self.datafile, self.loadcopy_tablespace, self.loadcopy_table,
                                                   self.db2_dbname, 5, True)
            self.log.info(f"Output of load copy images generated is {output}")
            self.log.info("sleeping for 180 sec before verifying logs and load copy images inside MA")
            time.sleep(180)
            self.log.info("Verifying logs on MA")
            self.db2_helper.verify_logs_on_ma(active_log_number, self.ma_obj)
            self.log.info("Verifying load copy images on MA")
            self.db2_helper.verify_load_copy_images_on_ma(self.ma_obj, output)

            if 'windows' in self.os_info.lower():
                unquiesce_command = (
                    "set-item -path env:DB2CLP -value **$$** ; "
                    "db2 unquiesce instance {0}".format(self.db2_instance))
                quiesce_command = (
                    "set-item -path env:DB2CLP -value **$$** ; db2 quiesce"
                    " instance {0} restricted access immediate force "
                    "connections".format(self.db2_instance))
            else:
                unquiesce_command = "db2 unquiesce instance {0}".format(
                    self.db2_instance)
                quiesce_command = (
                    "db2 quiesce instance {0} restricted access"
                    " immediate force connections".format(self.db2_instance))

            self.db2_helper.third_party_command(unquiesce_command)
            self.db2_helper.third_party_command(quiesce_command)

            self.log.info("#### CASE 3 : CLI recover and restore jobs ####")
            self.log.info(
                "#####Running Third Party Command Line Recover#######")
            self.db2_helper.disconnect_applications(
                self.backupset.backupset_name)
            self.db2_helper.third_party_command_recover(db_name=self.backupset.backupset_name.upper())

            self.log.info(
                "#####Running Third Party Command Line Restore#######")
            self.db2_helper.disconnect_applications(
                self.backupset.backupset_name)
            self.db2_helper.third_party_command_restore(
                self.backupset.backupset_name.upper(), backup_time_stamp2, version, True)

            self.db2_helper.reconnect()
            self.db2_helper.restore_validation(
                self.tablespace_name, self.table_name, tblcont_full)
            self.db2_helper.reconnect()

            self.log.info(" #### CASE 4 : GUI Full/Incr/Delta backups ####")
            self.log.info("#####Running GUI FULL Backup#######")
            job = self.db2_helper.run_backup(self.subclient, "FULL")
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0} delay_reason ".
                                format(str(job.delay_reason)))
            operation_type = ['N', 'O', 'E']
            (backup_time_stamp, streams) = self.db2_helper.get_backup_time_stamp_and_streams(
                job.job_id)

            self.log.info("#####Running Backup Validation#######")
            self.log.info("sleeping for 30sec")
            time.sleep(30)
            self.db2_helper.backup_validation(
                operation_type[0], tablespace_list, backup_time_stamp)
            self.log.info("Successfully ran full backup")

            self.log.info("#####Running GUI Incremental Backup#######")
            job = self.db2_helper.run_backup(self.subclient, "INCREMENTAL")
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0} delay_reason ".
                                format(str(job.delay_reason)))
            operation_type = ['N', 'O', 'E']

            (backup_time_stamp_incr, streams) = self.db2_helper.get_backup_time_stamp_and_streams(
                job.job_id)

            self.log.info("#####Running Backup Validation#######")
            self.log.info("sleeping for 30sec")
            time.sleep(30)
            self.db2_helper.backup_validation(
                operation_type[1], tablespace_list, backup_time_stamp_incr)
            self.log.info("Successfully ran incremental backup")

            active_log_number = self.get_active_log()

            self.log.info("archiving logs for 200 times")
            self.db2_helper.db2_archive_log(
                self.backupset.backupset_name.upper(), 200)
            self.db2_helper.get_active_logfile()
            self.log.info("sleeping for 20sec")
            time.sleep(20)
            self.log.info("Generating load copy images for 5 times")
            output = self.db2_helper.db2_load_copy(self.datafile, self.loadcopy_tablespace, self.loadcopy_table,
                                                   self.db2_dbname, 5, True)
            self.log.info(f"Output of load copy images generated is {output}")
            self.log.info("#####Running GUI DELTA Backup#######")
            job = self.db2_helper.run_backup(self.subclient, "DIFFERENTIAL")
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0} delay_reason ".
                                format(str(job.delay_reason)))

            operation_type = ['N', 'O', 'E']

            (backup_time_stamp_delta, streams) = self.db2_helper.get_backup_time_stamp_and_streams(
                job.job_id)

            self.log.info("#####Running Backup Validation#######")
            self.log.info("sleeping for 30sec")
            time.sleep(30)
            self.db2_helper.backup_validation(
                operation_type[2], tablespace_list, backup_time_stamp_delta)
            self.log.info("Successfully ran full backup")

            self.log.info("#####Disconnect Applications#######")

            self.db2_helper.disconnect_applications(
                self.backupset.backupset_name)
            self.log.info("sleeping for 180 sec before verifying logs and load copy images inside MA")
            time.sleep(180)
            self.log.info("Verifying logs on MA")
            self.db2_helper.verify_logs_on_ma(active_log_number, self.ma_obj)
            self.log.info("Verifying load copy images inside MA")
            self.db2_helper.verify_load_copy_images_on_ma(self.ma_obj, output)

            self.log.info("cleaning up test data before restore ")
            if "{0}{1}_Full.dbf".format(self.datafile, self.tablespace_name):
                self.machine_obj.rename_file_or_folder(
                    "{0}{1}_Full.dbf".format(
                        self.datafile, self.tablespace_name),
                    "{0}{1}_Full.dbf.ORG".format(self.datafile, self.tablespace_name))

            self.log.info(
                "#### CASE 5 : Run GUI RECOVER and RESTORE jobs ####")
            self.log.info(
                "###Submitting Restore with recover job starts here###")
            self.db2_helper.disconnect_applications(
                self.backupset.backupset_name)
            job = self.db2_helper.run_restore(self.backupset)
            self.log.info(
                "Started Current time restore to same client job with Job ID: %s job_id ",
                job.job_id)
            self.db2_helper.disconnect_applications(
                self.backupset.backupset_name)
            self.log.info(
                "###Submitting Restore without recover job starts here###")

            job = self.db2_helper.run_restore(self.backupset, recover_db=False)
            self.log.info(
                "Started Current time restore to same client job with Job ID: %s job_id ",
                job.job_id)
            self.log.info("#### Reconnection to Database####")
            self.db2_helper.reconnect()
            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with error: "
                                + str(job.delay_reason))

            self.log.info("#####Restore Validation#######")
            self.db2_helper.reconnect()
            self.db2_helper.restore_validation(
                self.tablespace_name, self.table_name, tblcont_full)
            self.log.info(
                "Successfully finished Current time restore to same client")
            self.db2_helper.close_db2_connection()
            self.log.info("************ TC PASSED *************")

        except Exception as exp:
            self.log.error('Failed with error: %s exp ', exp)
            self.result_string = exp
            self.status = constants.FAILED
