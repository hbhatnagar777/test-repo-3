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

    tear_down()     --  tear down method for this testcase
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
        self.name = ("GUI Backup Restore testcase "
                     "for Informix iDA with JM Job Authentication")
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
        """Run function of this test case"""
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
                self.client.client_name,
                self.instance.instance_name,
                self.instance.informix_user,
                self.informix_password,
                self.informix_service,
                run_log_only_backup=True)
            ########## Set JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key ##########
            self.log.info("Setting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry Key")
            self.commcell.add_additional_setting(
                "CommServDB.GxGlobalParam",
                "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION",
                "INTEGER",
                "1")
            self.log.info(
                "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key is set Successfully")
            ################# ENTIRE INSTANCE Backup/Restore Operations #######

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

            ####stopping the informix server before restore
            informix_directory = self.instance.informix_directory
            log.info("Informix instance name %s", self.instance.instance_name)
            log.info("Informix directory name %s", informix_directory)
            log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            log.info("***************Starting restore Job*****************")
            job = self.instance.restore_in_place(db_space_list)

            log.info("started the restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Restore job is now completed")

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

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """tear down method for this testcase"""
        ####### Deleting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry ##########
        self.log.info("Deleting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry Key")
        self.commcell.delete_additional_setting(
            "CommServDB.GxGlobalParam",
            "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION")
        self.log.info(
            "JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry key is deleted Successfully")
