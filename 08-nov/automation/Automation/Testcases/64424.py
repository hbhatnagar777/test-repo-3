"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function for this testcase

    prerequisite_for_setup()            --  Must needed steps to run the automation

    delete_instance()                   --  Deletes the DB2 instance given in input file from commserve

    create_instance()                   --  Adds DB2 instance give in input file to commserve

    delete_backupset()                  --  Deletes the backupset given in input file from input instance

    return_backupset()                  --  Adds the input backupset to input instance

    create_subclient()                  --  Adds the input subclient to the input backupset

    initialize_db2_helper()             --  Initializes db2 helper class object

    update_client_properties()          --  Updating DB2 logging properties on client and takes cold backup

    create_test_data()                  --  Adds a tablespace and a table and populates the table with data

    delete_tablespace_data_file()       --  Deletes the tablespace data file

    validate_backup()                   --  Validates the backup job

    validate_one_min_rpo()              --  Validates if one min RPO is enabled at backupset level from CSDB

    get_active_log()                    --  Fetches the current active log number of given backupset from the client

    generate_logs()                     --  Generates logs of given backupset

    run_and_validate_sweep_job()        --  Adds SweepStartTime registry key to MA, triggers sweep job and validates it

    restore_validation()                --  validates the restore job

    gui_backup()                        --  Runs the GUI full / incremental / differential backups

    cleanup_testdata()                  --  Cleans up the test data added before restore

    run()                               --  run function of this test case

    cleanup()                           --  cleanup function to delete automation generated data

Input Example:
    "testCases":
            {
                "64424":
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
                            "DB2Port": "60000",
                            "credential_name": "cred_name"
                        }
            }

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from Database.dbhelper import DbHelper
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ GUI Backup and out of place restore to same instance different DB check from MA post sweep for archived logs """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test for DB2 1 Min RPO from GUI to verify out of place restore from MA post sweep for archived logs"
        self.db2_helper = None
        self.machine_obj = None
        self.db2_user = None
        self.db2_password = None
        self.db2_instance = None
        self.db2_home = None
        self.db2_dbname = None
        self.dest_dbname = None
        self.storagepolicy = None
        self.table_name = None
        self.tablespace_name = None
        self.subclients = None
        self.subclient = None
        self.subclient_name = None
        self.command_line_sub_client = None
        self.port = None
        self.os_info = None
        self.datafile = None
        self.dbhelper_object = None
        self.media_agent = None
        self.ma_obj = None
        self.db2_instance_options_windows = None
        self.db2_instance_options = None
        self.db2_backupset_options = None
        self.credential_name = None
        self.instance = None
        self.instances = None
        self.backupset = None
        self.backupsets = None
        self.dest_backupset = None
        self.version = None
        self.tablespace_list = None
        self.tblcount_full = None
        self.tablespace_count = None
        self.operation_type = None
        self.tcinputs = {
            'Instance': None,
            'Backupset': None,
            'Subclient': None,
            'StoragePolicyName': None,
            'DB2User': None,
            'DB2UserPassword': None,
            'DB2HomePath': None,
            'DB2Port': None,
            'credential_name': None
        }

    def setup(self):
        """setup function for this testcase"""
        self.machine_obj = Machine(self.client)
        self.db2_user = self.tcinputs['DB2User']
        self.db2_password = self.tcinputs['DB2UserPassword']
        self.db2_instance = self.tcinputs['Instance']
        self.db2_home = self.tcinputs['DB2HomePath']
        self.db2_dbname = self.tcinputs['Backupset']
        self.subclient_name = self.tcinputs['Subclient']
        self.storagepolicy = self.tcinputs['StoragePolicyName']
        self.credential_name = self.tcinputs['credential_name']
        self.table_name = "T64424"
        self.tablespace_name = "TS64424"
        self.os_info = self.client.os_info
        self.port = None if len(str(self.tcinputs['DB2Port']).strip()) == 0 else str(self.tcinputs['DB2Port']).strip()
        self.dbhelper_object = DbHelper(self.commcell)
        self.media_agent = self.dbhelper_object.get_ma_names(self.storagepolicy)[0]
        self.ma_obj = Machine(self.media_agent, self.commcell)
        self.instances = self.agent.instances
        self.operation_type = ['N', 'O', 'E']
        self.dest_dbname = "DES64424"
        self.db2_instance_options_windows = {"domain_name": self.client.client_name,
                                             "password": self.db2_password,
                                             "user_name": self.client.display_name + "\\" + self.db2_user,
                                             "instance_name": self.db2_instance,
                                             "home_directory": self.db2_home,
                                             "data_storage_policy": self.storagepolicy,
                                             "log_storage_policy": self.storagepolicy,
                                             "command_storage_policy": self.storagepolicy,
                                             "storage_policy": self.storagepolicy,
                                             "credential_name": self.credential_name}

        self.db2_instance_options = {"password": self.db2_password,
                                     "user_name": self.db2_user,
                                     "instance_name": self.db2_instance,
                                     "home_directory": self.db2_home,
                                     "data_storage_policy": self.storagepolicy,
                                     "log_storage_policy": self.storagepolicy,
                                     "command_storage_policy": self.storagepolicy,
                                     "storage_policy": self.storagepolicy,
                                     "credential_name": self.credential_name}

        self.db2_backupset_options = {"backupset_name": self.db2_dbname,
                                      "storage_policy_name": self.storagepolicy}

    @test_step
    def prerequisite_for_setup(self):
        """Prerequisites for test case to run

            Raises:
                Exception:
                    If Unable to delete or create the instance

        """
        try:
            self.delete_instance()
            self.log.info("Sleeping for 10sec before creating new instance")
            time.sleep(10)
            self.create_instance()
        except Exception as exp:
            self.log.info("Failed establishing prerequisite setup for testcase")
            self.log.info(f"Creation or deletion of instance has been failed with the exception {exp}")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def delete_instance(self):
        """ Deletes the DB2 instance given in input file from commserve

            Raises:
                Exception:
                    If Unable to delete the instance

        """
        try:
            if self.instances.has_instance(instance_name=self.tcinputs['Instance']):
                self.log.info("Deleting instance from CS")
                self.instances.delete(self.tcinputs['Instance'])
                self.instances.refresh()
                self.commcell.refresh()
            else:
                self.log.info("Instance is not present in CS to delete")
        except Exception as exp:
            self.log.info("Deletion of instance failed from CS!!")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def create_instance(self):
        """ Adds DB2 instance give in input file to commserve

            Raises:
                Exception:
                    If Unable to create the instance

        """
        try:
            self.log.info("creating instance")
            if 'windows' in self.os_info.lower():
                self.instance = self.agent.instances.add_db2_instance(
                    self.db2_instance_options_windows)
            else:
                self.instance = self.agent.instances.add_db2_instance(
                    self.db2_instance_options)
            self.log.info("Instance creation has been successful")
            self.log.info("Initializing backupsets object with respect to instance")
            self.backupsets = self.instance.backupsets
            self.commcell.refresh()
        except Exception as exp:
            self.log.info("Creation of instance has been failed inside CS!!")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def delete_backupset(self):
        """ Deletes the backupset given in input file from input instance

            Raises:
                Exception:
                    If Unable to delete backupset inside the instance

        """
        try:
            self.log.info("Trying to delete the backupset from given instance")
            self.backupsets.delete(self.db2_dbname)
            self.log.info("Successfully deleted the backupset")
        except Exception as exp:
            self.log.info("Unable to delete the backupset inside the given instance")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def return_backupset(self, dbname):
        """ Adds the input backupset to input instance and returns backupset object

                Raises:
                    Exception:
                        If Unable to create the backupset inside instance

                """
        try:
            self.log.info(f"Adding backupset {dbname} to the instance {self.instance.instance_name}")
            self.log.info("If backupset already exists, it will be deleted and recreated ")
            if self.backupsets.has_backupset(dbname):
                self.log.info("Deleting the given backupset from instance as it is already present")
                self.delete_backupset()
                self.log.info("Sleeping for 10 sec before creating the backupset")
                time.sleep(10)
            self.backupsets.add(dbname, storage_policy=self.storagepolicy)
            self.log.info("Backupset Created successfully")
            self.commcell.refresh()
            return self.backupsets.get(dbname)
        except Exception as exp:
            self.log.info("Unable to add the backupset")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def create_subclient(self):
        """ Adds the input subclient to the input backupset

        Raises:
            Exception:
                If Unable to create the subclient inside backupset

        """
        try:
            self.log.info("If given subclient is not present inside the backupset it will be created")
            if self.subclients.has_subclient(self.subclient_name):
                self.log.info("Given subclient already exists inside backupset")
                self.subclient = self.subclients.get(self.subclient_name)
            else:
                self.subclient = self.subclients.add(self.subclient_name, self.storagepolicy)
                self.log.info("Successfully created the subclient")
            self.subclient.refresh()
            self.command_line_sub_client = self.backupset.subclients.get("(command line)")
            self.commcell.refresh()
        except Exception as exp:
            self.log.info("Unable to create the subclient")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def initialize_db2_helper(self):
        """Initializes db2 helper object

            Raises:
                Exception:
                    If there is any error initializing DB2 helper

        """
        try:
            self.log.info("Initializing DB2Helper")
            self.db2_helper = DB2(self.commcell, self.client, self.instance, self.backupset, port=self.port)
            self.commcell.refresh()
        except Exception as exception:
            self.log.info("Failed to initialize db2 helper or any of its parameters")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def update_client_properties(self):
        """ Updates logarchmeth1, logarchopt1 and vendoropt properties in client machine

        Raises:
            Exception:
                If Unable to update DB properties in client

        """
        try:
            if "unix" in self.client.os_info.lower():
                backup_path = "/dev/null"
                self.log.info(f"Cold backup will be taken to the path {backup_path}")
            else:
                install_loc = self.client.install_directory
                backup_path = f"{install_loc}\\Base\\Temp"
                self.log.info(f"Cold backup will be taken to the path {backup_path}")
            self.db2_helper.update_db2_database_configuration1(cold_backup_path=backup_path)
        except Exception as exception:
            self.log.info("Failed to update the client machine properties or to take Database backup")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def create_test_data(self, backup_type, create_tablespace):
        """ Adds a tablespace and a table and populates the table with data

            Args:

                backup_type (str) -- _FULL, _INCR/ _DELTA to append to table name

                create_tablespace (boolean) -- TRUE/ FALSE to create a tablespace or not

            Raises:
                Exception:
                    If Unable to create the test data inside DB

         """
        try:
            if create_tablespace:
                self.datafile = self.db2_helper.get_datafile_location()
                self.log.info("#####Get Version#######")
                self.version = self.db2_helper.get_db2_version()
                self.log.info("DB2 Version is: %s", self.version)
                self.log.info("##### Creating test Data#######")
                self.log.info(
                    f"creating the tablespace {self.tablespace_name} inside database {self.db2_dbname}")
            self.log.info(
                f"creating the table {self.table_name + backup_type} inside tablespace {self.tablespace_name}")
            self.db2_helper.create_table2(self.datafile, self.tablespace_name, self.table_name + backup_type,
                                          create_tablespace)
            if create_tablespace:
                self.log.info("Getting required parameters to validate backup and restore")
                (self.tblcont_full, self.tablespace_list, self.tablespace_count) = self.db2_helper.prepare_data(
                    self.table_name + "_FULL")
                self.log.info(f"Rows count in the created table are {self.tblcount_full}")
                self.log.info(f"Tablespace list in the given database is {self.tablespace_list}")
                self.log.info(f"Tablespace count in the given database is {self.tablespace_count}")
        except Exception as exp:
            self.log.info("Failed to create test data using db2 helper in given database")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def delete_tablespace_data_file(self):
        """ Deletes the tablespace data file

        Raises:
            Exception:
                If failed to delete the tablespace data file inside client

        """
        try:
            if "{}{}_Full.dbf.ORG".format(self.datafile, self.tablespace_name):
                self.machine_obj.delete_file("{}{}_Full.dbf.ORG".format(self.datafile, self.tablespace_name))
        except Exception as exp:
            self.log.info("Unable to delete the table space data file dbf.org file")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def validate_backup(self, operation_type, tablespace_list, backup_time_stamp):
        """ Validates the backup job

            Args:

                operation_type (Char) -- [N / O / E] Depending on the backup type that needs to get validated

                tablespace_list (List) -- List of tablespaces inside DB

                backup_time_stamp (Str) -- Backup job time stamp

            Raises:
                Exception:
                    If Failed to validate the Backup Job

        """
        try:
            self.log.info("Started the backup validation")
            self.db2_helper.backup_validation(operation_type, tablespace_list, backup_time_stamp)
            self.log.info("Successfully validated given backup job")
        except Exception as exp:
            self.log.info("Unable to validate the backup JOB")
            raise CVTestStepFailure(exp) from exp

    @test_step
    def validate_one_min_rpo(self):
        """ Validates if one min RPO is enabled at backupset level from CSDB

        Raises:
            Exception:
                If ONE MIN RPO is not enabled at backup set level

        """
        self.log.info("Validating if one min rpo is enabled at backupset level")
        self.log.info("sleeping for 30sec before validation")
        time.sleep(30)
        boolean = self.db2_helper.verify_one_min_rpo_backupset_level()
        if not boolean:
            raise Exception(
                "Test case Failed as ONE MIN RPO is not working and schedule policy not working at backupset level")

    @test_step
    def get_active_log(self):
        """ gets current active log file number

        Returns:
            active_log_number (INT)   -- Active log file number of given backupset

        Raises:
            Exception:
                If Unable to fetch the active log file number of DB from client

        """
        try:
            self.log.info(f"Fetching the active log file of DB {self.db2_dbname}")
            self.db2_helper.reconnect()
            active_log_number = self.db2_helper.get_active_logfile()[1]
            self.log.info(f"Active log file number of given DB {self.db2_dbname} is {active_log_number}")
            return active_log_number
        except Exception as exception:
            self.log.info(f"Failed to get active log number of db {self.db2_dbname}")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def generate_logs(self, archive_log_count):
        """ Generates archive logs for DB

        Args:

            archive_log_count (Int) -- Number of archive logs that needs to be generated

        Raises:
            Exception:
                If Failed to generate the log files

        """
        try:
            self.db2_helper.db2_archive_log(self.db2_dbname, archive_log_count)
        except Exception as exception:
            self.log.info("Failed to generate the archive logs")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def run_and_validate_sweep_job(self):
        """ Runs sweep job on MA and validates it

            Raises:
                Exception:
                    If Sweep job is not ran

        """
        try:
            self.log.info("Adding the registry key to run sweep job")
            self.db2_helper.run_sweep_job_using_regkey(self.media_agent)
            self.log.info("Successfully ran the sweep job and validated it")
        except Exception as exception:
            self.log.info("Failed to run or validate the sweep JOB")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def restore_validation(self):
        """ validates the restore job

        Raises:
            Exception:
                If Failed to validate the restore job

        """
        try:
            self.log.info("Initializing DB2 helper for the destination database")
            self.dest_backupset = self.return_backupset(self.dest_dbname)
            dest_db2_helper = DB2(commcell=self.commcell,
                                  client=self.client,
                                  instance=self.instance,
                                  backupset=self.dest_backupset)
            self.log.info("Validating the restore job")
            dest_db2_helper.restore_validation(self.tablespace_name, self.table_name, self.tblcont_full)
            self.log.info("Successfully validated the restore job")
            dest_db2_helper.close_db2_connection()
        except Exception as exp:
            raise Exception(f"Failed to validate the restore job with exception {exp}")

    @test_step
    def gui_backup(self, backup_type):
        """ Runs the GUI full / incremental / differential backups

        Args:

            backup_type (Str) -- FULL / INCREMENTAL / DIFFERENTIAL job that needs to be triggered

        Returns:
            backup_time_stamp (Str) -- Backup time stamp of the triggered backup job

        Raises:
            Exception:
                If Unable to trigger the gui backup jobs

        """
        job = self.db2_helper.run_backup(self.subclient, backup_type)
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run {backup_type} backup job with error: {job.delay_reason} delay_reason")
        (backup_time_stamp, streams) = self.db2_helper.get_backup_time_stamp_and_streams(job.job_id)
        self.log.info(f"Successfully ran {backup_type} backup")
        return backup_time_stamp

    @test_step
    def cleanup_testdata(self):
        """ Cleans up the test data added before restore

        Raises:
            Exception:
                If failed to clear the test data in given backupset

        """
        try:
            self.log.info("cleaning up test data before restore ")
            self.db2_helper.disconnect_applications(self.backupset.backupset_name)
            if "{0}{1}_Full.dbf".format(self.datafile, self.tablespace_name):
                self.machine_obj.rename_file_or_folder("{0}{1}_Full.dbf".format(self.datafile, self.tablespace_name),
                                                       "{0}{1}_Full.dbf.ORG".format(self.datafile,
                                                                                    self.tablespace_name))
            self.log.info("Successfully deleted test data before restore")
        except Exception as exp:
            raise Exception(f"Failed to clean up the test data with the following exception {exp}")

    def run(self):
        """ run function of this test case

        Raises:
            Exception:
                If the TC is FAILED with any of the steps listed in run method

        """
        try:
            self.prerequisite_for_setup()
            self.backupset = self.return_backupset(self.db2_dbname)
            self.subclients = self.backupset.subclients
            self.commcell.refresh()
            self.create_subclient()

            self.initialize_db2_helper()
            self.update_client_properties()
            self.log.info("Creating and enabling One Min RPO at schedule policy")
            self.db2_helper.create_sweep_schedule_policy()

            self.create_test_data("_FULL", True)
            self.delete_tablespace_data_file()

            backup_time_stamp = self.gui_backup("FULL")
            self.log.info("Sleeping for 30 sec before running backup validation")
            time.sleep(30)
            self.validate_backup(self.operation_type[0], self.tablespace_list, backup_time_stamp)

            self.validate_one_min_rpo()

            self.db2_helper.reconnect()
            self.log.info("Fetching active log number from MA")
            active_log_number = self.get_active_log()
            self.log.info(f"Current active log number of the given database is {active_log_number}")
            self.log.info("Generating 50 log files")
            self.generate_logs(50)
            self.log.info("sleeping for 60 sec before verifying logs inside MA")
            time.sleep(60)
            self.log.info("Verifying logs on MA")
            self.db2_helper.verify_logs_on_ma(active_log_number, self.ma_obj)
            self.run_and_validate_sweep_job()

            self.cleanup_testdata()
            self.db2_helper.gui_out_of_place_restore_same_instance(self.dest_dbname)
            self.restore_validation()
            self.db2_helper.close_db2_connection()

            self.log.info("************ TC PASSED *************")

        except Exception as exp:
            self.log.error("************ TC FAILED *************")
            self.result_string = exp
            self.status = constants.FAILED
            raise Exception(f"Test case Failed with the exception: {exp}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup function to delete automation generated data"""
        self.log.info("Deleting Automation Created Tablespaces")
        self.db2_helper.reconnect()
        if self.db2_helper is not None:
            self.db2_helper.drop_tablespace(self.tablespace_name)
        self.log.info("Deleting automation created Schedule policy")
        if self.commcell.schedule_policies.has_policy('db2_sweep_schedule'):
            self.log.info("Deleting the automation created sweep schedule policy")
            self.commcell.schedule_policies.delete('db2_sweep_schedule')