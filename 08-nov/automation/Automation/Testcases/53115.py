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

    __init__()                      --  initializes test case class object

    run()                           --  run function of this test case

"""
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Cross machine Restore from CLI testcase for Informix iDA"
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

            self.log.info("Creating destination client object")
            destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientname"])
            self.log.info("Creating destination agent object")
            destination_agent = destination_client.agents.get('informix')
            self.log.info("Creating destination instance object")
            destination_instance = destination_agent.instances.get(
                self.tcinputs["DestinationInstancename"])
            destination_backupset = destination_instance.backupsets.get('default')
            destination_subclient = destination_backupset.subclients.get('default')
            self.log.info("Creating destination helper object for destination Client")
            self.log.info("Destination Client name:%s", self.tcinputs["DestinationClientname"])
            self.log.info("Destination Instance name:%s", self.tcinputs["DestinationInstancename"])
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

            destination_machine_object = machine.Machine(destination_client, self.commcell)
            dest_base_directory = destination_machine_object.join_path(
                destination_client.install_directory, "Base")

            ################# create a dbspace in destination client #########
            self.log.info("Creating a dbspace in Destination client")
            destination_helper_object.create_dbspace()
            self.log.info("getting required information for cross machine restore")
            ifx_info_list = informix_helper_object.cross_machine_operations(
                destination_helper_object)
            self.log.info("Informix information list:%s", ifx_info_list)

            ##### ENTIRE INSTANCE Backup/Cross machine Restore Operations #######

            ############### Populate database ###############################
            self.log.info("Operating in source client")
            self.log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ##################### Running Full Backup ########################
            self.log.info("Setting the backup mode of subclient to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"
            dbhelper_object.run_backup(self.subclient, "FULL")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            dbhelper_object.run_backup(self.subclient, "INCREMENTAL")

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            self.log.info("Starting config file restore")
            informix_helper_object.cross_config_only_restore(
                destination_helper_object,
                ifx_info_list[2])

            ####################### Running restore ###########################
            self.log.info("**********Starting entire instance restore Job************")
            destination_helper_object.cross_machine_restore(
                "ENTIRE_INSTANCE",
                destination_client.client_name,
                destination_client.instance,
                ifx_info_list[0],
                base_directory=dest_base_directory)
            self.log.info("Cross machine Restore job of entire instance is now completed")

            # bring the informix server back online with onmode -m
            destination_helper_object.bring_server_online()
            self.log.info("Informix server is now online")
            self.log.info("deleting copied ixbar file from destination")
            destination_machine_object.delete_file(ifx_info_list[4])
            self.log.info("ixbar file removed")

            destination_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = destination_helper_object.collect_meta_data()

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
            dbhelper_object.run_backup(self.subclient, "FULL")

            ############ Adding more data before incremental ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ######### Running Incremental Backup ##############
            dbhelper_object.run_backup(self.subclient, "INCREMENTAL")

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            self.log.info("Starting config file restore")
            informix_helper_object.cross_config_only_restore(
                destination_helper_object,
                ifx_info_list[2])

            ####################### Running restore ###########################
            self.log.info("**********Starting whole system restore Job************")
            destination_helper_object.cross_machine_restore(
                "WHOLE_SYSTEM",
                destination_client.client_name,
                destination_client.instance,
                ifx_info_list[0],
                base_directory=dest_base_directory)
            self.log.info("Cross machine Restore job of whole system is now completed")

            #####bring the informix server back online with onmode -m
            destination_helper_object.bring_server_online()
            self.log.info("Informix server is now online")
            self.log.info("deleting copied ixbar file from destination")
            destination_machine_object.delete_file(ifx_info_list[4])
            self.log.info("ixbar file removed")

            ############## Changing Subclient content to Entire Instance ######
            self.log.info("Changing Subclient content to Entire Instance")
            self.subclient.backup_mode = "Entire_Instance"

            destination_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = destination_helper_object.collect_meta_data()

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
