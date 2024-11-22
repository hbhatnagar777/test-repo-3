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

    __init__()      --  initializes test case class object

    setup()         --  setup function of this test case

    run()           --  run function of this test case
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Restore database upto logical log testcase for Informix iDA"
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
        """Run function of this test case"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info(
                "Requested data population size=%s",
                self.tcinputs['TestDataSize'])
            dbhelper_object = dbhelper.DbHelper(self.commcell)
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
            ################ ENTIRE INSTANCE Backup/Restore Operations #######

            ################ Populate database ###############################
            self.log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            self.log.info("Setting the backup mode of subclient to Entire Instance")
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
            last_log_backedup = informix_helper_object.get_last_log_number(job.job_id)
            self.log.info(
                "Last logical log backedup is:%s",
                last_log_backedup)

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            ####stopping the informix server before restore
            informix_directory = self.instance.informix_directory
            self.log.info("Informix instance name %s", self.instance.instance_name)
            self.log.info("Informix directory name %s", informix_directory)
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            self.log.info("***************Starting upto logical log restore Job*****************")
            job = self.instance.restore_in_place(
                db_space_list,
                restore_option_type="UPTO_LOGICAL_LOG",
                upto_log=last_log_backedup)

            self.log.info(
                "started the upto logical log restore Job with Id:%s",
                job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            self.log.info("upto logical log Restore job is now completed")

            # bring the informix server back online with onmode -m
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

            #########################################################
            ############### WHOLE SYSTEM BKP/RESTORE ################
            #########################################################

            ##Updating Subclient Property for whole system backup
            self.log.info("Changing Subclient content to Whole System")
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
            last_log_backedup = informix_helper_object.get_last_log_number(job.job_id)
            self.log.info(
                "Last logical log backedup is:%s",
                last_log_backedup)

            #####collect the dbspace list in server
            db_space_list = informix_helper_object.list_dbspace()
            db_space_list.sort()
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            ####### stopping the informix server before restore #########
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            self.log.info("*******Starting database upto logical log restore Job*********")
            job = self.instance.restore_in_place(
                db_space_list,
                restore_type="WHOLE SYSTEM",
                restore_option_type="UPTO_LOGICAL_LOG",
                upto_log=last_log_backedup)

            self.log.info(
                "started the whole system upto logical log restore Job with Id:%s",
                job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            self.log.info("Whole System upto logical log Restore job is now completed")

            #####bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()
            self.log.info("Informix server is now online")

            ############## Changing Subclient content to Entire Instance ######
            self.log.info("Changing Subclient content to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"

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
