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

    setup()         --  Setup function of this test case

    run()           --  run function of this test case
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper

class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AUX copy Restore testcase for Informix iDA"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.INFORMIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None
        }
        self.informix_password = None
        self.informix_service = None
        self.informix_data_population_size = None

    def setup(self):
        """Setup function of this test case"""
        self.informix_password = self.tcinputs['InformixDatabasePassword']
        self.informix_service = self.tcinputs['InformixServiceName']
        self.informix_data_population_size = self.tcinputs['TestDataSize']

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
                "Requested data population size=%s",
                self.informix_data_population_size)
            dbhelper_object = dbhelper.DbHelper(self.commcell)
            informix_helper_object = InformixHelper(
                self.commcell,
                self.instance,
                self.subclient,
                self.client.client_hostname,
                self.instance.instance_name,
                self.instance.informix_user,
                self.informix_password,
                self.informix_service,
                run_log_only_backup=True)

            ################# ENTIRE INSTANCE Backup/Restore Operations #######
            log.info(
                "Storage Policy Associated with default subclient is: %s",
                self.subclient.storage_policy)

            ################ Populate database ###############################
            log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.informix_data_population_size)
            log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            log.info("Setting the backup mode of subclient to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"
            job = dbhelper_object.run_backup(self.subclient, "FULL")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            job = dbhelper_object.run_backup(self.subclient, "INCREMENTAL")

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            log.info("List of DBspaces in the informix server: %s", db_space_list)

            ###################### creating aux copy ########################
            copy_precedence = dbhelper_object.prepare_aux_copy_restore(
                self.subclient.storage_policy)
            log.info(
                "Proceeding to restore with copy precendence value = %s",
                copy_precedence)

            ####stopping the informix server before restore
            informix_directory = self.instance.informix_directory
            log.info("Informix instance name %s", self.instance.instance_name)
            log.info("Informix directory name %s", informix_directory)
            log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            log.info("***************Starting restore Job*****************")
            job = self.instance.restore_in_place(
                db_space_list,
                copy_precedence=copy_precedence,
                logical_restore=False)

            log.info("started the physical restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Physical Restore job is now completed")

            job = self.instance.restore_in_place(
                db_space_list,
                copy_precedence=copy_precedence,
                physical_restore=False)

            log.info("started the logical restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Logical Restore job is now completed")

            # bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()
            log.info("Informix server is now online")

            informix_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = informix_helper_object.collect_meta_data()

            ################ validating the meta data ########################

            if meta_data_before_backup == meta_data_after_restore:
                log.info("Data is validated Successfully.")
            else:
                raise Exception(
                    "Database information validation failed.")

            #########################################################
            ############### WHOLE SYSTEM BKP/RESTORE ################
            #########################################################

            ##Updating Subclient Property for whole system backup
            log.info("Changing Subclient content to Whole System")
            self.subclient.backup_mode = "Whole_System"

            ###################### Running Full Backup ########################
            job = dbhelper_object.run_backup(self.subclient, "FULL")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            job = dbhelper_object.run_backup(self.subclient, "INCREMENTAL")

            #####collect the dbspace list in server
            db_space_list = informix_helper_object.list_dbspace()
            db_space_list.sort()
            log.info("List of DBspaces in the informix server: %s", db_space_list)

            ###################### creating aux copy ########################
            copy_precedence = dbhelper_object.prepare_aux_copy_restore(
                self.subclient.storage_policy)
            log.info(
                "Proceeding to restore with copy precendence value = %s",
                copy_precedence)

            ####### stopping the informix server before restore #########
            log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            log.info("***************Starting restore Job*****************")
            job = self.instance.restore_in_place(
                db_space_list,
                restore_type="WHOLE SYSTEM",
                copy_precedence=copy_precedence,
                logical_restore=False)

            log.info("started the physical restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Physical Restore job is now completed")

            job = self.instance.restore_in_place(
                db_space_list,
                restore_type="WHOLE SYSTEM",
                copy_precedence=copy_precedence,
                physical_restore=False)

            log.info("started the logical restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Logical Restore job is now completed")

            # bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()
            log.info("Informix server is now online")

            informix_helper_object.reconnect()

            ############## Changing Subclient content to Entire Instance ######
            log.info("Changing Subclient content to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"

            ############### Collecting meta data #############################
            meta_data_after_restore = informix_helper_object.collect_meta_data()

            ################ validating the meta data ########################

            if meta_data_before_backup == meta_data_after_restore:
                log.info("Data is validated Successfully.")
            else:
                raise Exception(
                    "Database information validation failed.")

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
