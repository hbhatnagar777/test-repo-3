# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class defined in this file.
"""
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import cloud_connector
from AutomationUtils import constants as const
from Application.CloudApps import constants

class TestCase(CVTestCase):
    """
        Class for OneDrive Backup Finalize phase
    """

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Verification for OneDrive Backup Finalize phase"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "application_id": "",
            "application_key_value": "",
            "azure_directory_id": "",
        }
        self._client = None
        self._agent = None
        self._instance = None
        self._subclient = None

        self.cvcloud_object = None
        self.JobID = None

    def setup(self):
        self._initialize_sdk_objects()
        self.cvcloud_object = cloud_connector.CloudConnector(self)

    def _initialize_sdk_objects(self):
        self.commcell.refresh()
        details = {
            "azure_directory_id": self.tcinputs.get("azure_directory_id"),
            "application_id": self.tcinputs.get("application_id"),
            "application_key_value": self.tcinputs.get("application_key_value")
        }

        if self._commcell.clients.has_client(self.tcinputs.get('client_name')):
            self.log.info('Deleting the Client as it already exists')
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))

        self.log.info('Create client object for: %s', self.tcinputs.get("client_name"))
        self._commcell.clients.add_onedrive_client(client_name=self.tcinputs.get("client_name"),
                                                   instance_name=self.tcinputs.get("instance_name"),
                                                   server_plan=self.tcinputs.get("server_plan"),
                                                   connection_details=details,
                                                   access_node=self.tcinputs.get("access_node"))
        self._client = self._commcell.clients.get(self.tcinputs.get("client_name"))

        self.log.info('Create agent object for: %s', self.tcinputs.get("agent_name"))
        self._agent = self.client.agents.get(self.tcinputs.get("agent_name"))

        if self._agent is not None:
            self.log.info('Create instance object for: %s', self.tcinputs.get("instance_name"))
            self._instance = self._agent.instances.get(self.tcinputs.get("instance_name"))

            self.log.info('Create subclient object for: %s', self.tcinputs.get("subclient_name"))
            self._instance.subclients.add_onedrive_subclient(subclient_name=self.tcinputs.get("subclient_name"),
                                                             server_plan=self.tcinputs.get("server_plan"))
            self._subclient = self._instance.subclients.get(self.tcinputs.get("subclient_name"))

    def run(self):

        try:
            self._subclient.add_user(user_name=self.tcinputs.get("user_name"))
            self._subclient.refresh()

            self.cvcloud_object.one_drive.delete_folder()
            self.cvcloud_object.one_drive.upload_files_to_onedrive(file_location=constants.GENERATE_FILES_PATH,
                                                                   no_of_files=constants.NO_OF_FILES_TO_UPLOAD)

            # Run a Full Backup
            backup_level = 'FULL'
            self.JobID = self._subclient.backup(backup_level=backup_level)
            self.cvcloud_object.cvoperations.check_job_status(job=self.JobID, backup_level_tc=backup_level)

            self.cvcloud_object.one_drive.verify_finalize_phase(job_id=self.JobID.job_id)
            self.log.info('Finalize phase successful for backup job : [{0}]'.format(self.JobID.job_id))

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = const.FAILED

    def tear_down(self):
        if self.status == const.PASSED:
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))
        del self.cvcloud_object


