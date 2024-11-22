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
from Database import dbhelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing backup restore for Informix iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Instance/Subclient creation/modification, "
                     "restore from deleted subclient testcase for Informix iDA")
        self.tcinputs = {
            'InformixDatabaseServerName': None,
            'InformixDatabaseOnConfigFileName': None,
            'InformixDatabaseSqlHostFileLocation': None,
            'InformixDirectory': None,
            'StoragePolicyName': None,
            'InformixDatabaseDomainName': None,
            'InformixDatabaseUserName': None,
            'InformixDatabasePassword':None,
            'InformixServiceName': None,
            'TestDataSize': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            dbhelper_object = dbhelper.DbHelper(self.commcell)


            ######################Create a instance #########################
            self.log.info(
                "Creating a instance with name: %s", self.tcinputs['InformixDatabaseServerName'])
            if self.agent.instances.has_instance(self.tcinputs['InformixDatabaseServerName']):
                self.log.info(
                    "Instance with name %s already exists",
                    self.tcinputs['InformixDatabaseServerName'])
                self.log.info("Deleting the instance")
                self.agent.instances.delete(self.tcinputs['InformixDatabaseServerName'])
                self.log.info("Instance is now deleted")
            informix_options = {
                'instance_name': self.tcinputs['InformixDatabaseServerName'],
                'onconfig_file': self.tcinputs['InformixDatabaseOnConfigFileName'],
                'sql_host_file': self.tcinputs['InformixDatabaseSqlHostFileLocation'],
                'informix_dir': self.tcinputs['InformixDirectory'],
                'user_name':self.tcinputs['InformixDatabaseUserName'],
                'domain_name':self.tcinputs['InformixDatabaseDomainName'],
                'password':self.tcinputs['InformixDatabasePassword'],
                'storage_policy':self.tcinputs['StoragePolicyName'],
                'description':'created from automation'
            }
            self.log.info("Informix Option JSON for Instance creation: %s", informix_options)
            instance_object = self.agent.instances.add_informix_instance(informix_options)
            self.log.info("Instance created")


            ####################### Create a subclient ######################
            backup_set = instance_object.backupsets.get('default')
            self.log.info("Creating a subclient: automation_subclient")
            if backup_set.subclients.has_subclient("automation_subclient"):
                self.log.info("subclient with name: automation_subclient, already exists")
                self.log.info("Deleting the subclient")
                backup_set.subclients.delete("automation_subclient")
                self.log.info("Subclient Deleted")
            subclient_object = backup_set.subclients.add(
                "automation_subclient",
                self.tcinputs['StoragePolicyName'],
                "Created from Automation")
            self.log.info("Subclient created.")


            ############## Modify instance property ############
            self.log.info("Modifying the log backup policy for instance")
            instance_object.log_storage_policy_name = self.tcinputs['StoragePolicyName']
            self.log.info("Log backup storage policy is modified to : %s",
                     instance_object.log_storage_policy_name)
            self.log.info(
                "Requested data population size=%s",
                self.tcinputs['TestDataSize'])
            informix_helper_object = InformixHelper(
                self.commcell,
                instance_object,
                subclient_object,
                self.client.client_hostname,
                instance_object.instance_name,
                instance_object.informix_user,
                self.tcinputs['InformixDatabasePassword'],
                self.tcinputs['InformixServiceName'],
                run_log_only_backup=True)

            ################Backup/Restore Operations ######################
            ################ Populate database ###############################
            self.log.info("Populating the informix server")
            informix_helper_object.populate_data(
                scale=self.tcinputs['TestDataSize'])
            self.log.info("Informix server is populated with test data")

            ###################### Running Full Backup ########################
            self.log.info("Setting the backup mode of subclient to Entire Instance")
            subclient_object.backup_mode = "Entire_Instance"
            job = dbhelper_object.run_backup(subclient_object, "FULL")

            ############### Collecting meta data #############################
            meta_data_before_backup = informix_helper_object.collect_meta_data()


            ############# Delete the subclient  #############################
            self.log.info("Deleting the subclient:automation_subclient")
            backup_set.subclients.delete("automation_subclient")
            self.log.info("Subclient deleted Successfully")

            #################################################################

            ####collect the dbspace list in server
            db_space_list = sorted(informix_helper_object.list_dbspace())
            self.log.info("List of DBspaces in the informix server: %s", db_space_list)

            ####stopping the informix server before restore
            self.log.info("Informix instance name %s", instance_object.instance_name)
            self.log.info("Informix directory name %s", instance_object.informix_directory)
            self.log.info("Stopping informix server to perform restore")
            informix_helper_object.stop_informix_server()

            ####################### Running restore ###########################
            self.log.info("***************Starting restore Job*****************")
            job = instance_object.restore_in_place(
                db_space_list)
            self.log.info("started the restore Job with Id:%s",
                     job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run data only restore job with error: {1}".format(
                        job.delay_reason
                    )
                )
            self.log.info("Restore job is now completed")

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

            #################################################################

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
