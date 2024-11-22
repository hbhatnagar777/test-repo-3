# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

design steps:
1. Install a client
2. Add config param ‘DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS’ if doesn’t exist and set it to 0
3. Run some backups on it
4. Delete all backups on client except for 1 backup job
5. Run data aging
6. Deconfigure the client --> use retire client option
7. Make sure config ‘DA_CONFIG_DELETE_DECONFIGURED_CLIENTS_WITH_NO_DATA’ is enabled
8. Run data aging and make sure the client is not deleted as it still has jobs on it
9. Now delete the backup job and run DA. Make sure deconfigured client is deleted.

"""

import os
import time
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "data aging case for validation of delete deconfigured clients config"
        self.tcinputs = {
            "MediaAgentName": None,
            "SqlSaPassword": None,
            "InstallClientHostName": None,
            "InstallClientUserName": None,
            "InstallClientPassword": None
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.path = None
        self.content_path = None
        self.mount_path = None
        self.mmhelper = None
        self.client_machine = None
        self.library = None
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.copy = None
        self.client_name = None
        self.clients = None
        self.client = None
        self.agent = None

    def setup(self):
        """Setup function of this test case"""
        self.library_name = str(self.id) + "_lib"
        self.storage_policy_name = str(self.id) + "_SP"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        # self.path = os.path.normpath(self.tcinputs["PathToUse"])
        # self.mount_path = os.path.join(self.path, "MP")
        self.mmhelper = MMHelper(self)


    def set_days_to_keep_deconfigured_clients(self, value=0):
        """
        sets config param 'DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS' with number of days value
        Args:
            value (int): number of days to set as config param value
        """
        _query = """
                    IF NOT EXISTS (
                        SELECT * FROM MMConfigs
                        WHERE NAME = 'DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS'
                    )
                    BEGIN
                        INSERT INTO MMConfigs(NAME,value,bExposeInGUI,nType,nMin,nMax,
                        nConfigSubSystemId,fallBackValueName)
                        VALUES ('DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS',{0},0,1,0,30,2,
                        'number of days to delete deconfigured clients')
                    END
                    ELSE
                    BEGIN
                        UPDATE MMConfigs
                        SET VALUE = {0}
                        WHERE NAME = 'DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS'
                    END""".format(value)
        self.mmhelper.execute_update_query(_query, self.tcinputs['SqlSaPassword'])

    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (int): size of backup content to generate

        Returns:
        (object) -- returns job object to backup job
        """
        # add content
        self.client_machine.remove_directory(os.path.join(self.content_path, r'*'))
        self.mmhelper.create_uncompressable_data(self.client, self.content_path, size)
        self.log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self.log.info("Backup job completed.")
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(self.name)
            self.log.info("Running install job...")
            install_job = self.commcell.install_software(client_computers=[self.tcinputs['InstallClientHostName']],
                                        windows_features=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                        username=self.tcinputs['InstallClientUserName'],
                                        password=b64encode(self.tcinputs["InstallClientPassword"].encode()).decode())
            self.log.info("Install job: %s", install_job.job_id)
            if not install_job.wait_for_completion():
                raise Exception(
                    "Failed to run install client job with error: {0}".format(install_job.delay_reason)
                )
            self._log.info("Client:%s installed.", self.tcinputs['InstallClientHostName'])
            # self.clients = Clients(self.commcell)
            self.commcell.refresh()
            self.client = self.commcell.clients.get(self.tcinputs['InstallClientHostName'])#.split('.')[0])
            self.client_name = self.client.client_name
            self.agent = self.client.agents.get(self.tcinputs['AgentName'])

            self.client_machine = Machine(self.client, self.commcell)
            self.content_path = os.path.join(self.client.log_directory, 'data')
            if not self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.create_directory(self.content_path)
            # select drive
            utility = OptionsSelector(self.commcell)
            media_agent = self.commcell.clients.get(self.tcinputs['MediaAgentName'])
            media_agent_machine = Machine(media_agent, self.commcell)
            mount_path_drive = utility.get_drive(media_agent_machine, size=3072)
            if not mount_path_drive:
                raise Exception("no free space on MA to create library")
            self.log.info("selected backup content drive: %s", mount_path_drive)
            self.mount_path = os.path.join(mount_path_drive, 'MP')

            # 2. Add config param ‘DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS’ if doesn’t exist and set to 0
            self.log.info("set config param DA_CONFIG_NUMBER_OF_DAYS_TO_KEEP_DECONFIGURED_CLIENTS to 0")
            self.set_days_to_keep_deconfigured_clients()

            # 3. Run some backups on it
            # create library, dedupe sp, backupset and subclient
            self.library = self.mmhelper.configure_disk_library(self.library_name,
                                                                self.tcinputs["MediaAgentName"],
                                                                self.mount_path)

            self.storage_policy = self.mmhelper.configure_storage_policy(self.storage_policy_name,
                                                                         self.library_name,
                                                                         self.tcinputs["MediaAgentName"])

            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                               self.subclient_name,
                                                               self.storage_policy_name,
                                                               self.content_path,
                                                               self.agent)

            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.copy_retention = (1, 0, 1)

            job1 = self.run_backup()
            job2 = self.run_backup()
            job3 = self.run_backup()

            # 4. Delete all backups on client except for 1 backup job
            self.log.info("deleting jobs: %s %s", job1.job_id, job2.job_id)
            self.copy.delete_job(job1.job_id)
            self.copy.delete_job(job2.job_id)

            # 5. Run data aging
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name,
                                                  is_granular=True,
                                                  include_all_clients=True,
                                                  select_copies=True,
                                                  prune_selected_copies=True)
            self.log.info("start data aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: {0}".format(da_job.delay_reason)
                )
            self.log.info("data aging job completed!")

            # 6. Deconfigure the client --> use retire client option
            self.client.retire()
            job_ctrl = self.commcell.job_controller
            for job_id in job_ctrl.active_jobs(job_filter='UNINSTALLCLIENT').keys():
                self.log.info("wait for job: %s to complete", job_id)
                uninstall_job = job_ctrl.get(job_id)
                if not uninstall_job.wait_for_completion():
                    raise Exception(
                        "Failed to run retire client job with error: {0}".format(uninstall_job.delay_reason)
                    )
            self.log.info("retire client job completed!")

            # 7. Make sure config ‘DA_CONFIG_DELETE_DECONFIGURED_CLIENTS_WITH_NO_DATA’ is enabled
            query = """
                    IF NOT EXISTS (
                    SELECT * FROM MMConfigs 
                    WHERE NAME = 'DA_CONFIG_DELETE_DECONFIGURED_CLIENTS_WITH_NO_DATA' AND VALUE = 1
                    )
                    BEGIN
                        UPDATE MMConfigs
                        SET VALUE = 1
                        WHERE NAME = 'DA_CONFIG_DELETE_DECONFIGURED_CLIENTS_WITH_NO_DATA'
                    END
                    """
            self.log.info("QUERY: %s", query)
            self.mmhelper.execute_update_query(query, self.tcinputs['SqlSaPassword'])

            # 8. Run data aging and make sure the client is not deleted as it still has jobs on it
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name,
                                                  is_granular=True,
                                                  include_all_clients=True,
                                                  select_copies=True,
                                                  prune_selected_copies=True)
            self.log.info("start data aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: {0}".format(da_job.delay_reason)
                )
            self.log.info("data aging job completed!")
            self.log.info("VALIDATION: check Client is not deleted")
            self.commcell.clients.refresh()
            if not self.commcell.clients.has_client(self.client_name):
                self.log.error("client was not expected to be deleted by data aging")
                raise Exception("client was not expected to be deleted by data aging")
            self.log.info("client is present as expected")

            # 9. Now delete the backup job and run DA. Make sure deconfigured client is deleted.
            self.log.info("deleting job: %s", job3.job_id)
            self.copy.delete_job(job3.job_id)
            da_job = self.commcell.run_data_aging('Primary', self.storage_policy_name,
                                                  is_granular=True,
                                                  include_all_clients=True,
                                                  select_copies=True,
                                                  prune_selected_copies=True)
            self.log.info("start data aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: {0}".format(da_job.delay_reason)
                )
            self.log.info("data aging job completed!")
            time.sleep(60)
            self.commcell.refresh()
            self.log.info("VALIDATION: check Client should be deleted")
            if self.commcell.clients.has_client(self.client_name):
                self.log.error("client was expected to be deleted by data aging")
                raise Exception("client was expected to be deleted by data aging")
            self.log.info("client is deleted as expected")

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Main function to perform cleanup operations"""
        self.log.info("cleaning up configs and installed client...")
        self.commcell.refresh()
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("deleting client...")
            self.client.retire()
            self.commcell.clients.delete(self.client_name)
            self.log.info("delete client done!")
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info("deleting storage policy...")
            self.commcell.storage_policies.delete(self.storage_policy_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("deleting library...")
            self.commcell.disk_libraries.delete(self.library_name)
        self.log.info("cleanup done.")


