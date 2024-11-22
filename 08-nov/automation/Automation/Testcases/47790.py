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
        self.name = "Cross machine Restore testcase for Informix iDA"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.INFORMIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'InformixDatabasePassword': None,
            'InformixServiceName': None,
            'TestDataSize': None,
            'DestinationClientname': None,
            'DestinationInstancename': None,
            'DestinationInformixServiceName': None,
            'DestinationInformixDatabasePassword': None
        }

    def run(self):
        """Run function of this test case"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
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

            log.info("Creating destination client object")
            destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientname"])
            log.info("Creating destination agent object")
            destination_agent = destination_client.agents.get('informix')
            log.info("Creating destination instance object")
            destination_instance = destination_agent.instances.get(self.tcinputs["DestinationInstancename"])
            destination_backupset = destination_instance.backupsets.get('default')
            destination_subclient = destination_backupset.subclients.get('default')
            log.info("Creating destination helper object for destination Client")
            log.info("Destination Client name:%s", self.tcinputs["DestinationClientname"])
            log.info("Destination Instance name:%s", self.tcinputs["DestinationInstancename"])
            destination_helper_object = InformixHelper(
                self.commcell,
                destination_instance,
                destination_subclient,
                self.tcinputs["DestinationClientname"],
                self.tcinputs["DestinationInstancename"],
                destination_instance.informix_user,
                self.tcinputs["DestinationInformixDatabasePassword"],
                self.tcinputs["DestinationInformixServiceName"],
                run_log_only_backup=True)

            ################# create a dbspace in destination client #########
            log.info("Creating a dbspace in Destination client")
            destination_helper_object.create_dbspace()

            ######## ENTIRE INSTANCE Backup/Cross machine Restore Operations #######

            ################ Populate database ###############################
            log.info("Operating in source client")
            log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
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
            informix_directory = destination_instance.informix_directory
            log.info("Informix instance name %s", destination_instance.instance_name)
            log.info("Informix directory name %s", informix_directory)
            log.info("Stopping destination informix server to perform restore")
            destination_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            log.info("***************Starting restore Job*****************")
            job = self.instance.restore_out_of_place(
                db_space_list,
                self.tcinputs["DestinationClientname"],
                self.tcinputs["DestinationInstancename"])

            log.info("started the cross machine restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Cross machine Restore job is now completed")

            # bring the informix server back online with onmode -m
            destination_helper_object.bring_server_online()
            log.info("Informix server is now online")

            destination_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = destination_helper_object.collect_meta_data()

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

            ####### stopping the informix server before restore #########
            log.info("Stopping informix server to perform restore")
            destination_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            log.info("************Starting Cross machine restore Job**************")
            job = self.instance.restore_out_of_place(
                db_space_list,
                self.tcinputs["DestinationClientname"],
                self.tcinputs["DestinationInstancename"],
                restore_type="WHOLE SYSTEM")

            log.info("started the whole system Cross machine restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            log.info("Whole System Cross machine Restore job is now completed")

            #####bring the informix server back online with onmode -m
            destination_helper_object.bring_server_online()
            log.info("Informix server is now online")

            ############## Changing Subclient content to Entire Instance ######
            log.info("Changing Subclient content to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"

            destination_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = destination_helper_object.collect_meta_data()

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
