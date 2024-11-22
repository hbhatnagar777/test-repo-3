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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper


class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commandline Backup Restore testcase for Informix iDA"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.INFORMIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info(
                "Requested data population size=%s",
                self.tcinputs['TestDataSize'])
            informix_helper_object = InformixHelper(
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
            base_directory = informix_helper_object.base_directory
            self.log.info("Client Name:%s", self.client.client_name)
            self.log.info("Client Instance:%s", self.client.instance)
            self.log.info("Base Directory:%s", base_directory)
            ################# ENTIRE INSTANCE Command Line Backup/Restore Operations #######

            ################ Populate database ###############################
            self.log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            self.log.info("Starting commandline Full backup of Entire Instance")
            informix_helper_object.cl_full_backup_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline Full backup of Entire Instance")

            ############ performing table level restore #####################
            if "unix" in machine_object.os_info.lower():
                informix_helper_object.cl_table_level_restore(
                    self.client.client_name,
                    self.client.instance,
                    base_directory)
                row_count_source_table = informix_helper_object.row_count(
                    "tab1",
                    database="auto1")
                row_count_destination_table = informix_helper_object.row_count(
                    "tabTableLevelRestore",
                    database="auto1")
                self.log.info("Source table Size: %s", row_count_source_table)
                self.log.info("Destination table size: %s", row_count_destination_table)
                if row_count_destination_table != row_count_source_table:
                    raise Exception(
                        "DB information validation failed after Table level restore.")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            self.log.info("Starting commandline incremental backup of Entire Instance")
            informix_helper_object.cl_incremental_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline incremental backup of Entire Instance")

            ####stopping the informix server before restore
            self.log.info("Informix instance name %s", self.instance.instance_name)
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            self.log.info("***************Starting restore Job*****************")
            informix_helper_object.cl_physical_restore(
                self.client.client_name,
                self.client.instance,
                base_directory)
            informix_helper_object.cl_log_only_restore(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline restore of Entire Instance")

            # bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()

            informix_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = informix_helper_object.collect_meta_data()

            ################ validating the meta data ########################

            if meta_data_before_backup == meta_data_after_restore:
                self.log.info("Data is validated Successfully.")
            else:
                raise Exception(
                    "Database information validation failed.")
            self.log.info("Dropping tabTableLevelRestore table from auto1 database")
            informix_helper_object.drop_table("tabTableLevelRestore", "auto1")

            #########################################################
            ############### WHOLE SYSTEM BKP/RESTORE ################
            #########################################################

            ###################### Running Full Backup ########################
            self.log.info("Starting commandline Full backup of Whole System")
            informix_helper_object.cl_full_backup_whole_system(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline Full backup of Whole Instance")

            ############ performing table level restore #####################
            if "unix" in machine_object.os_info.lower():
                informix_helper_object.cl_table_level_restore(
                    self.client.client_name,
                    self.client.instance,
                    base_directory)
                row_count_source_table = informix_helper_object.row_count(
                    "tab1",
                    database="auto1")
                row_count_destination_table = informix_helper_object.row_count(
                    "tabTableLevelRestore",
                    database="auto1")
                self.log.info("Source table Size: %s", row_count_source_table)
                self.log.info("Destination table size: %s", row_count_destination_table)
                if row_count_destination_table != row_count_source_table:
                    raise Exception(
                        "DB information validation failed after Table level restore.")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            self.log.info("Starting commandline incremental backup of Whole System")
            informix_helper_object.cl_incremental_whole_system(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline incremental backup of Whole System")

            ####### stopping the informix server before restore #########
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()



            ####################### Running restore ###########################
            self.log.info("***************Starting restore Job*****************")
            informix_helper_object.cl_physical_whole_sys_restore(
                self.client.client_name,
                self.client.instance,
                base_directory)
            informix_helper_object.cl_log_only_restore(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline restore of Whole System")

            #####bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()
            self.log.info("Informix server is now online")

            informix_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = informix_helper_object.collect_meta_data()

            ################ validating the meta data ########################

            if meta_data_before_backup == meta_data_after_restore:
                self.log.info("Data is validated Successfully.")
            else:
                raise Exception(
                    "Database information validation failed.")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
