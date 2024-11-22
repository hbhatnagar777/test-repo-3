# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

"""

from AutomationUtils import constants as const
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import cloud_connector
from AutomationUtils.machine import Machine
from Application.CloudApps import constants


class TestCase(CVTestCase):
    """Class for Failed Items test case"""

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "To verify failed items case in OneDrive backup"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "application_id": "",
            "application_key_value": "",
            "azure_directory_id": ""
        }
        self._client = None
        self._agent = None
        self._instance = None
        self._subclient = None

        self.cvcloud_object = None
        self.machine = None
        self.JobID = None

    def setup(self):
        """Setup function of this test case"""
        self._initialize_sdk_objects()
        self.cvcloud_object = cloud_connector.CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()
        self.machine = Machine()

    def _initialize_sdk_objects(self):
        self.commcell.refresh()
        details = {
            "azure_directory_id": self.tcinputs.get('azure_directory_id'),
            "application_id": self.tcinputs.get('application_id'),
            "application_key_value": self.tcinputs.get('application_key_value')
        }

        if self._commcell.clients.has_client(self.tcinputs.get('client_name')):
            self.log.info('Deleting the Client as it already exists')
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))

        self.log.info('Create client object for: %s', self.tcinputs.get('client_name'))
        self._commcell.clients.add_onedrive_client(client_name=self.tcinputs.get('client_name'),
                                                   instance_name=self.tcinputs.get("instance_name"),
                                                   server_plan=self.tcinputs.get('server_plan'),
                                                   connection_details=details,
                                                   access_node=self.tcinputs.get('access_node'))
        self._client = self._commcell.clients.get(self.tcinputs.get('client_name'))

        self.log.info('Create agent object for: %s', self.tcinputs.get('agent_name'))
        self._agent = self.client.agents.get(self.tcinputs.get('agent_name'))

        if self._agent is not None:
            self.log.info('Create instance object for: %s', self.tcinputs.get('instance_name'))
            self._instance = self._agent.instances.get(self.tcinputs.get('instance_name'))

            self.log.info('Create subclient object for: %s', self.tcinputs.get('subclient_name'))
            self._instance.subclients.add_onedrive_subclient(subclient_name=self.tcinputs.get('subclient_name'),
                                                             server_plan=self.tcinputs.get('server_plan'))
            self._subclient = self._instance.subclients.get(self.tcinputs.get('subclient_name'))

    def run(self):
        """Run function of this test case"""

        try:

            self._subclient.add_user(user_name=self.tcinputs.get("user_name"))
            self._subclient.refresh()

            no_of_files = constants.NO_OF_FILES_TO_UPLOAD
            self.cvcloud_object.one_drive.delete_folder()
            self.cvcloud_object.one_drive.upload_files_to_onedrive(file_location=constants.GENERATE_FILES_PATH,
                                                                   no_of_files=no_of_files)

            # Create Registry Key
            if not self.machine.check_registry_exists(constants.REG_KEY_IDATAAGENT,
                                                      constants.SIMULATE_FAILURE_ITEMS_KEY):
                if self.machine.update_registry(constants.REG_KEY_IDATAAGENT,
                                                constants.SIMULATE_FAILURE_ITEMS_KEY,
                                                constants.SIMULATE_FAILURE_ITEMS_VALUE,
                                                constants.SIMULATE_FAILURE_ITEMS_REG_TYPE):
                    self.log.info('Created Registry key to Simulate backup failure after [{0}] Items in a backup'.
                                  format(constants.SIMULATE_FAILURE_ITEMS_VALUE))
                else:
                    raise Exception('Failed to create Registry Key')

            # Run a Full Backup
            backup_level = 'FULL'
            self.JobID = self._subclient.backup(backup_level=backup_level)
            self.cvcloud_object.cvoperations.check_job_status(job=self.JobID, backup_level_tc=backup_level)

            # Remove Registry Key
            if self.machine.check_registry_exists(constants.REG_KEY_IDATAAGENT,
                                                  constants.SIMULATE_FAILURE_ITEMS_KEY):
                if self.machine.remove_registry(constants.REG_KEY_IDATAAGENT,
                                                constants.SIMULATE_FAILURE_ITEMS_KEY):
                    self.log.info('Registry Key Removed')
                else:
                    raise Exception('Failed to remove Registry Key')

            backup_files = self.cvcloud_object.cvoperations.get_backup_files()

            num_of_failed_files = self.cvcloud_object.cvoperations.get_number_of_failed_items(self.JobID)

            if len(backup_files) != no_of_files - num_of_failed_files:
                raise Exception('Error! Backup files mismatch')

            DB_failed_files_FULL = self.cvcloud_object.sqlite.get_failed_files_local_db()

            if num_of_failed_files:

                if num_of_failed_files == len(DB_failed_files_FULL):

                    # Deleting a file from the OneDrive User which gets failed from the backup job
                    delete_file = DB_failed_files_FULL[0]
                    del DB_failed_files_FULL[0]
                    self.cvcloud_object.one_drive.delete_single_file(file_name=delete_file)
                    self.log.info(f'File Deleted : {delete_file}')

                    # Run a Incremental Backup
                    backup_level = 'INCREMENTAL'
                    self.JobID = self._subclient.backup(backup_level=backup_level)
                    self.cvcloud_object.cvoperations.check_job_status(job=self.JobID,
                                                                      backup_level_tc=backup_level)

                    backup_files = self.cvcloud_object.cvoperations.get_backup_files()

                    DB_failed_files_INCR = self.cvcloud_object.sqlite.get_failed_files_local_db()

                    # Checking Local DB is getting updated after deleting file from the failed items
                    if DB_failed_files_INCR and delete_file in DB_failed_files_INCR:
                        raise Exception('Local DB Failed to update the deleted file')
                    else:
                        self.log.info('Deleted file removed from Local DB')

                    # Checking whether all failed items are getting backup  and local db getting updated
                    if all(x in backup_files for x in DB_failed_files_FULL):
                        if DB_failed_files_INCR:
                            raise Exception('Local DB Failed to update after Backing up all Failed Items')
                        else:
                            self.log.info('***************************************************************')
                            self.log.info('*****All failed items got backup and local DB gets updated*****')
                            self.log.info('***************************************************************')
                    else:
                        raise Exception('Failed to Backup all Failed files from the First job')

                else:
                    raise Exception('Failed to match the number of failed files with the Local DB Failed files')
            else:
                raise Exception('No Failed Files generated to run this Test Case')

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = const.FAILED

    def tear_down(self):
        if self.status == const.PASSED:
            self.cvcloud_object.one_drive.delete_folder()
            self.cvcloud_object.cvoperations.cleanup()
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))
        del self.cvcloud_object
