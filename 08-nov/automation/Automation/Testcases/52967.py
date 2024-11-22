# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case

    run_restore()       --  Runs restore job and brings server up

    validate_restore()  --  Validates restored contents

    tear_down()         --  tear down method for this testcase

"""
from time import sleep
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper


class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Commandline Backup Restore testcase "
                     "for Informix iDA with JM Job Authentication")
        self.informix_helper_object = None
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None,
            'TokenFilePath': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info(
                "Requested data population size=%s",
                self.tcinputs['TestDataSize'])
            self.informix_helper_object = InformixHelper(
                self.commcell,
                self.instance,
                self.subclient,
                self.client.client_hostname,
                self.instance.instance_name,
                self.instance.informix_user,
                self.tcinputs['InformixDatabasePassword'],
                self.tcinputs['InformixServiceName'],
                run_log_only_backup=True)
            machine_object = machine.Machine(self.client, self.commcell)
            if "unix" in machine_object.os_info.lower():
                self.log.info("changing token file permission to 666")
                machine_object.change_file_permissions(self.tcinputs['TokenFilePath'], '666')
            base_directory = self.informix_helper_object.base_directory
            self.log.info("Client Name:%s", self.client.client_name)
            self.log.info("Client Instance:%s", self.client.instance)
            self.log.info("Base Directory:%s", base_directory)
            self.log.info(
                "Token File Location in Client: %s",
                self.tcinputs['TokenFilePath'])

            ########## Set JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key ##########
            self.log.info("Setting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry Key")
            self.commcell.add_additional_setting(
                "CommServDB.GxGlobalParam",
                "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION",
                "INTEGER",
                "1")
            self.log.info(
                "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key is set Successfully")

            ################# ENTIRE INSTANCE Command Line Backup/Restore Operations #######

            ################ Populate database ###############################
            self.log.info("Populating the informix server")
            self.informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            self.log.info("Starting commandline Full backup of Entire Instance")
            self.informix_helper_object.cl_full_backup_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory,
                token_file_path=self.tcinputs['TokenFilePath'])
            self.log.info("Finished commandline Full backup of Entire Instance")

            ############ performing table level restore #####################
            if "unix" in machine_object.os_info.lower():
                self.informix_helper_object.cl_table_level_restore(
                    self.client.client_name,
                    self.client.instance,
                    base_directory,
                    token_file_path=self.tcinputs['TokenFilePath'])
                row_count_source_table = self.informix_helper_object.row_count(
                    "tab1",
                    database="auto1")
                row_count_destination_table = self.informix_helper_object.row_count(
                    "tabTableLevelRestore",
                    database="auto1")
                self.log.info("Source table Size: %s", row_count_source_table)
                self.log.info("Destination table size: %s", row_count_destination_table)
                if row_count_destination_table != row_count_source_table:
                    raise Exception(
                        "DB information validation failed after Table level restore.")

            ############ Adding more data before incremental ############
            self.informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = self.informix_helper_object.collect_meta_data()
            sleep(120)
            ######### Running Incremental Backup ##############
            self.log.info("Starting commandline incremental backup of Entire Instance")
            self.informix_helper_object.cl_incremental_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory,
                token_file_path=self.tcinputs['TokenFilePath'])
            self.log.info("Finished commandline incremental backup of Entire Instance")

            ####################### Running restore ###########################
            self.run_restore(base_directory)
            self.validate_restore(meta_data_before_backup)
            self.log.info("Dropping tabTableLevelRestore table from auto1 database")
            self.informix_helper_object.drop_table("tabTableLevelRestore", "auto1")

            if "unix" in machine_object.os_info.lower():
                self.log.info("Sleeping for a minute before checking salvage log case")
                sleep(60)
                ###################### Running Full Backup ########################
                self.log.info("Starting commandline Full backup of Entire Instance")
                self.informix_helper_object.cl_full_backup_entire_instance(
                    self.client.client_name,
                    self.client.instance,
                    base_directory,
                    token_file_path=self.tcinputs['TokenFilePath'])
                self.log.info("Finished commandline Full backup of Entire Instance")

                ############ Adding more data before salvage log backup ############
                self.informix_helper_object.insert_rows(
                    "tab1",
                    database="auto1",
                    scale=2)
                sleep(60)
                meta_data_before_backup = self.informix_helper_object.collect_meta_data()
                self.run_restore(base_directory, salvage=True)
                self.validate_restore(meta_data_before_backup)

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def run_restore(self, base_directory, salvage=False):
        """Runs restore job and brings server up"""
        ####stopping the informix server before restore
        self.log.info("Informix instance name %s", self.instance.instance_name)
        self.log.info("Stopping informix server to perform restore")
        self.informix_helper_object.stop_informix_server()
        ####################### Running restore ###########################
        self.log.info("***************Starting restore Job*****************")
        if not salvage:
            self.informix_helper_object.cl_physical_restore(
                self.client.client_name,
                self.client.instance,
                base_directory,
                token_file_path=self.tcinputs['TokenFilePath'])
            self.informix_helper_object.cl_log_only_restore(
                self.client.client_name,
                self.client.instance,
                base_directory,
                token_file_path=self.tcinputs['TokenFilePath'])
        else:
            self.informix_helper_object.cl_restore_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory,
                token_file_path=self.tcinputs['TokenFilePath'])
        self.log.info("Finished commandline restore of Entire Instance")

        # bring the informix server back online with onmode -m
        self.informix_helper_object.bring_server_online()
        self.informix_helper_object.reconnect()

    def validate_restore(self, data_before_backup):
        """Validates restored contents"""
        ############### Collecting meta data #############################
        meta_data_after_restore = self.informix_helper_object.collect_meta_data()

        ################ validating the meta data ########################

        if data_before_backup == meta_data_after_restore:
            self.log.info("Data is validated Successfully.")
        else:
            raise Exception(
                "Database information validation failed.")

    def tear_down(self):
        """tear down method for this testcase"""
        ####### Deleting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry ##########
        self.log.info("Deleting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry Key")
        self.commcell.delete_additional_setting(
            "CommServDB.GxGlobalParam",
            "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION")
        self.log.info(
            "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key is deleted Successfully")
