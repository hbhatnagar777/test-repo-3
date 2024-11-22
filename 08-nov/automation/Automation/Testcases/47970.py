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
import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Optimizing Informix On-demand Log Backups testcase for Informix"
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
            dbhelper_object = dbhelper.DbHelper(self.commcell)
            informix_helper_object = InformixHelper(
                self.commcell,
                self.instance,
                self.subclient,
                self.client.client_name,
                self.instance.instance_name,
                self.instance.informix_user,
                self.tcinputs['InformixDatabasePassword'],
                self.tcinputs['InformixServiceName'],
                run_log_only_backup=True)
            machine_object = machine.Machine(self.client, self.commcell)
            base_directory = machine_object.join_path(self.client.install_directory, "Base")
            self.log.info("Client Name:%s", self.client.client_name)
            self.log.info("Client Instance:%s", self.client.instance)
            self.log.info("Base Directory:%s", base_directory)

            ################ Populate database ###############################
            self.log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            self.log.info("Starting commandline Full backup")
            self.subclient.backup_mode = "Entire_Instance"
            informix_helper_object.cl_full_backup_entire_instance(
                self.client.client_name,
                self.client.instance,
                base_directory)
            self.log.info("Finished commandline Full backup")

            ################# Set sPerformanceModeOn registry key ########################
            self.log.info("Setting sPerformanceModeOn registry Key")
            self.client.add_additional_setting("InformixAgent", "sPerformanceModeOn", "STRING", "Y")
            self.log.info("sPerformanceModeOn registry key is set Successfully")
            self.log.info(
                "Now the log backups will be handled by single GUI job untill 6hrs(default)")
            self.log.info("Sleeping for 2 mins after setting the reg Key")
            time.sleep(120)

            ############ Adding more data ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############ Switch logs ###############
            informix_helper_object.cl_switch_log(
                self.client.client_name,
                self.client.instance,
                base_directory)

            ############ Perform log only backup ##########
            informix_helper_object.cl_log_only_backup(
                self.client.client_name,
                self.client.instance,
                base_directory)

            ########### get the job Id of log backup #########
            job_1 = informix_helper_object.get_command_line_job()

            ############ Adding more data ############
            informix_helper_object.insert_rows(
                "tab1",
                database="auto1",
                scale=2)

            ############ Switch logs ###############
            informix_helper_object.cl_switch_log(
                self.client.client_name,
                self.client.instance,
                base_directory)

            ############ Perform log only backup ##########
            informix_helper_object.cl_log_only_backup(
                self.client.client_name,
                self.client.instance,
                base_directory)

            ############ get the job Id of log backup #########
            job_2 = informix_helper_object.get_command_line_job()

            ########### check if job id differs ##############
            if job_1.job_id != job_2.job_id:
                raise Exception(
                    "Different jobs are triggered for subsequent log only backups.!")

            self.log.info("Subsequent log backups are being handled by the same GUI job.")

            ################# Set nPERFMODEIFXJOBCLOSEMINS registry key ########################
            self.log.info(
                "Setting nPERFMODEIFXJOBCLOSEMINS registry Key and setting value to 1 min")
            self.client.add_additional_setting(
                "InformixAgent",
                "nPERFMODEIFXJOBCLOSEMINS",
                "STRING",
                "1")
            self.log.info("nPERFMODEIFXJOBCLOSEMINS registry key is set Successfully")
            self.log.info("Now the JOb %s has to end in next two mins", job_1.job_id)
            self.log.info("Sleeping for 4 minutes before checking job status")
            time.sleep(240)
            self.log.info("Checking status of JOB: %s", job_1.job_id)
            if job_1.status.lower() != "completed":
                raise Exception(
                    "Job status is not completed even after waiting 3 minutes.")
            self.log.info("Job is completed, proceeding to restore operations.")
            del job_1
            del job_2

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            ####stopping the informix server before restore
            self.log.info("Informix instance name %s", self.instance.instance_name)
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()
            self.log.info("informix server is now stopped")

            ####################### Running commandline restore ###########################
            self.log.info("***************Starting restore Job*****************")
            informix_helper_object.cl_restore_entire_instance(
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
                self.log.info("Data is validated Successfully for CL restore.")
            else:
                raise Exception(
                    "Database information validation failed for CL restore.")

            ####### Run a GUI full Backup ##########
            dbhelper_object.run_backup(self.subclient, "FULL")

            ####stopping the informix server before restore
            self.log.info("Informix instance name %s", self.instance.instance_name)
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()
            self.log.info("informix server is now stopped")

            ####################### Running GUI restore ###########################
            self.log.info("***************Starting restore Job*****************")
            job = self.instance.restore_in_place(db_space_list)

            self.log.info("started the restore Job with Id:%s", job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {0}".format(
                        job.delay_reason
                    )
                )
            self.log.info("Restore job is now completed")

            # bring the informix server back online with onmode -m
            informix_helper_object.bring_server_online()

            informix_helper_object.reconnect()

            ############### Collecting meta data #############################
            meta_data_after_restore = informix_helper_object.collect_meta_data()

            ################ validating the meta data ########################

            if meta_data_before_backup == meta_data_after_restore:
                self.log.info("Data is validated Successfully for GUI restore.")
            else:
                raise Exception(
                    "Database information validation failed for GUI restore.")

            self.log.info("Testcase executed Succesfully..!!!")

            ####### Deleting JM_ENABLE_THIRD_PARTY_JOB_AUTHENTICATION registry ##########
            self.log.info("Deleting registry Keys")
            self.client.delete_additional_setting(
                "InformixAgent",
                "nPERFMODEIFXJOBCLOSEMINS")
            self.log.info(
                "nPERFMODEIFXJOBCLOSEMINS key is deleted Successfully")
            self.client.delete_additional_setting(
                "InformixAgent",
                "sPerformanceModeOn")
            self.log.info(
                "sPerformanceModeOn key is deleted Successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
