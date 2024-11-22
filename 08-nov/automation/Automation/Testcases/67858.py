# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    cleanup()                   --  cleans up the environment created by tc on the commcell in current/previous runs

    initial_setup()             --  configures the environment required for tc

    pre_upgrade_steps()         --  run data operations prior to upgrade

    upgrade_steps()             --  perform the upgrade of cv

    post_upgrade_validations()  --  validates required functionality after upgrade is finished

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this case

Sample JSON:
    "67858": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login",
        "MediaAgentName"    : "Name of MediaAgent",
        "Client2Name"       : "Name of Second Client"
        *** optional ***
        "CUPack"            : HPKNumber
    }

Note:
    - Populate CoreUtils/Templates/config.json/
        "Install":"download_server": to the download server that the cs is pointing.
"""
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Install import installer_utils
from Install.update_helper import UpdateHelper
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions


class TestCase(CVTestCase):
    """Class for executing Push Service Pack upgrades of CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()

        self.name = "Upgrade Automation - Validate Copy Promotion with Preserve Encryption setting"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "MediaAgentName": None,
            "Client2Name": None
        }
        # self.config_json = None
        self.client2 = None
        self.cs_machine = None
        self.client_machine = None
        self.client2_machine = None
        self.media_agent_machine = None

        self.library_name = None
        self.backupset_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.subclient_name_suffix = None
        self.agent2 = None
        self.backup_set = None
        self.backup_set2 = None
        self.storage_pool1 = None
        self.storage_pool2 = None
        self.storage_pool3 = None
        self.storage_policy = None
        self.copy_1 = None
        self.copy_2 = None
        self.copy_3 = None
        self.subclient_list = []
        self.backup_jobs_list = []

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.update_helper = None
        self.install_helper = None

        self.tc_client_path = None
        self.tc_client2_path = None
        self.tc_media_agent_path = None
        self.mount_path = None
        self.content_path = None
        self.content2_path = None
        self.dedup_store_path = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # self.config_json = config.get_config()
        self.log.info("Setting up testcase variables and objects")
        self.client2 = self.commcell.clients.get(self.tcinputs.get('Client2Name'))
        self.agent2 = self.client2.agents.get('File System')
        self.cs_machine = Machine(machine_name=self.tcinputs.get('CSHostName'),
                                  username=self.tcinputs.get('CSMachineUsername'),
                                  password=self.tcinputs.get('CSMachinePassword'))
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.client2_machine = Machine(self.tcinputs.get('Client2Name'), self.commcell)
        self.media_agent_machine = Machine(self.tcinputs.get("MediaAgentName"), self.commcell)

        suffix = f'{self.tcinputs.get("MediaAgentName")}{self.tcinputs.get("ClientName")}'

        self.backupset_name = f"{self.id}_BS{suffix}"
        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.subclient_name_suffix = f"{self.id}_SC{suffix}"
        self.storage_pool_name = f"{self.id}_StoragePool{suffix}"

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.install_helper = InstallHelper(self.commcell)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)

        ma_drive = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        client_drive = self.opt_selector.get_drive(self.client_machine, 25*1024)
        client2_drive = self.opt_selector.get_drive(self.client2_machine, 25*1024)

        self.tc_client_path = self.client_machine.join_path(client_drive, str(self.id))
        self.tc_client2_path = self.client_machine.join_path(client2_drive, str(self.id))
        self.tc_media_agent_path = self.media_agent_machine.join_path(ma_drive, str(self.id))
        self.content_path = self.client_machine.join_path(self.tc_client_path, "content_path")
        self.content2_path = self.client2_machine.join_path(self.tc_client2_path, "content_path")
        self.mount_path = self.media_agent_machine.join_path(self.tc_media_agent_path, 'MP')
        self.dedup_store_path = self.media_agent_machine.join_path(self.tc_media_agent_path, 'DDB')

    def cleanup(self):
        """
        Cleans up the environment created by tc on the commcell in current/previous runs
        """
        try:
            self.log.info("Cleanup Started")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.content2_path, self.client2_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.agent2.backupsets.has_backupset(self.backupset_name):
                self.agent2.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)
            if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_1'):
                self.commcell.storage_pools.delete(f'{self.storage_pool_name}_1')
            if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
                self.commcell.storage_pools.delete(f'{self.storage_pool_name}_2')
            if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_3'):
                self.commcell.storage_pools.delete(f'{self.storage_pool_name}_3')
            self.log.info("Cleanup Completed")
        except Exception as exp:
            self.log.warning('Cleanup Failed. Please cleanup manually. Error: %s', str(exp))

    def initial_setup(self):
        """
        Configures the Environment require for TC
        """
        self.log.info("Configuring 3 Dedupe storage pools")
        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_1'):
            self.storage_pool1 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_1',
                                                                 f'{self.mount_path}_1',
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 f'{self.dedup_store_path}_1')
        else:
            self.storage_pool1 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_1')
        self.log.info(f"Storage pool {self.storage_pool_name}_1 configured")
        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
            self.storage_pool2 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_2',
                                                                 f'{self.mount_path}_2',
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 f'{self.dedup_store_path}_2')
        else:
            self.storage_pool2 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_2')
        self.log.info(f"Storage pool {self.storage_pool_name}_2 configured")
        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_3'):
            self.storage_pool3 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_3',
                                                                 f'{self.mount_path}_3',
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 f'{self.dedup_store_path}_3')
        else:
            self.storage_pool3 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_3')
        self.log.info(f"Storage pool {self.storage_pool_name}_3 configured")

        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                     global_policy_name=f'{self.storage_pool_name}_1',
                                                                     global_dedup_policy=True)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
        self.storage_policy.create_secondary_copy('Copy-2', global_policy=f'{self.storage_pool_name}_2')
        self.storage_policy.create_secondary_copy('Copy-3', global_policy=f'{self.storage_pool_name}_3')
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, 'Copy-2')
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, 'Copy-3')
        self.copy_1 = self.storage_policy.get_copy('Primary')
        self.copy_2 = self.storage_policy.get_copy('Copy-2')
        self.copy_3 = self.storage_policy.get_copy('Copy-3')

        self.log.info("Configuring Backup Sets on each clients")
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.backup_set2 = self.mm_helper.configure_backupset(self.backupset_name, self.agent2)

        self.log.info("Configuring 2 Subclients each on both Backup Sets")
        for index in range(2):
            subclient_name = f'{self.subclient_name_suffix}_{index}'
            if not self.backup_set.subclients.has_subclient(subclient_name):
                self.backup_set.subclients.add(subclient_name, self.storage_policy_name)
            self.subclient_list.append(self.backup_set.subclients.get(subclient_name))
            self.log.info("Configured Subclient %s", subclient_name)
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index}')
            self.subclient_list[index].content = [content_path]
        for index in range(2):
            subclient_name = f'{self.subclient_name_suffix}_{index}'
            if not self.backup_set2.subclients.has_subclient(subclient_name):
                self.backup_set2.subclients.add(subclient_name, self.storage_policy_name)
            self.subclient_list.append(self.backup_set2.subclients.get(subclient_name))
            self.log.info("Configured Subclient %s", subclient_name)
            content_path = self.client2_machine.join_path(self.content2_path, f'Data_{index}')
            self.subclient_list[index + 2].content = [content_path]

    def pre_upgrade_steps(self):
        """
        Run Data operations prior to upgrade
        """
        self.log.info("Starting pre upgrade steps")

        self.log.info("Setting Client, Subclient encryption settings: "
                      "Client1: Use SP settings, Client 2: Encrypt on Client: BlowFish 256."
                      "SC0: Encrypt Network and Media, SC1: Encrypt Media only")
        self.client.set_encryption_property("USE_SPSETTINGS")
        self.client2.set_encryption_property("ON_CLIENT", "BlowFish", "256")
        # above operation sets the client enc. settings as: 1, 2, 256
        self.subclient_list[0].encryption_flag = 'ENC_NETWORK_AND_MEDIA'
        self.subclient_list[1].encryption_flag = 'ENC_MEDIA_ONLY'
        self.subclient_list[2].encryption_flag = 'ENC_NETWORK_AND_MEDIA'
        self.subclient_list[3].encryption_flag = 'ENC_MEDIA_ONLY'
        self.log.info(
            "Logging the current config pre Upgrade -- Client1: EncryptionSetting: %s"
            " Client2: EncryptionSetting: %s, CipherType: %s, KeyLen: %s. "
            "Client1 SC1: %s, Client1 SC2: %s, Client2 SC1: %s, Client2 SC2: %s",
            self.client.properties.get('clientProps').get('encryptionSettings'),
            self.client2.properties.get('clientProps').get('encryptionSettings'),
            self.client2.properties.get('clientProps').get('CipherType'),
            self.client2.properties.get('clientProps').get('EncryptKeyLength'),
            self.subclient_list[0].encryption_flag, self.subclient_list[1].encryption_flag,
            self.subclient_list[2].encryption_flag, self.subclient_list[3].encryption_flag
        )
        self.log.info(f"Setting GOST-256 Encryption on {self.storage_pool_name}_1")
        self.storage_pool1.get_copy().set_encryption_properties(
                    re_encryption=True, encryption_type="GOST", encryption_length=256)
        self.log.info(f"Setting Preserve Encryption as in source on {self.storage_pool_name}_2,3")
        self.storage_pool2.get_copy().set_encryption_properties(preserve=True)
        self.storage_pool3.get_copy().set_encryption_properties(preserve=True)

        self.log.info("Running Backups for each of the 4 subclients and waiting for the jobs to complete")
        for index in range(2):
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index}')
            self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 1, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info("Backup Job: %s started for : Client 1 %s_%s",
                          self.backup_jobs_list[index].job_id, self.subclient_name_suffix, index)
        for index in range(2):
            content_path = self.client2_machine.join_path(self.content2_path, f'Data_{index}')
            self.opt_selector.create_uncompressable_data(self.client2_machine, content_path, 1, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient_list[index+2].backup(backup_level='Full'))
            self.log.info("Backup Job: %s started for : Client 2 %s_%s",
                          self.backup_jobs_list[index+2].job_id, self.subclient_name_suffix, index)
        for index in range(4):
            if not self.backup_jobs_list[index].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index].job_id)

        self.log.info("Running Auxcopy to Copy 2")
        auxcopy_job = self.storage_policy.run_aux_copy('Copy-2')
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)
        self.log.info("Running Auxcopy to Copy 3")
        auxcopy_job = self.storage_policy.run_aux_copy('Copy-3')
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

    def upgrade_steps(self):
        """
        Perform the Upgrade of CV
        """
        self.log.info("Fetching details of latest recut for SP: %s and starting download software job",
                      self.tcinputs.get('ServicePack'))
        _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get('ServicePack'))
        latest_cu = 0
        if not self.tcinputs.get('CUPack'):
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
        job_obj = self.commcell.download_software(
            options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
            os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value],
            service_pack=self.tcinputs.get("ServicePack"),
            cu_number=self.tcinputs.get('CUPack', latest_cu))
        self.log.info("Download Software Job: %s started", job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Download Software Job: %s failed with JPR: %s", job_obj.job_id, job_obj.delay_reason)
        self.log.info("Download Software Job: %s completed", job_obj.job_id)

        self.log.info(f"Starting Service pack upgrade of CS from SP %s to %s",
                      str(self.commcell.commserv_version), self.tcinputs.get('ServicePack'))
        self.update_helper.push_sp_upgrade(client_computers=[self.commcell.commserv_name])
        self.log.info("SP upgrade of CS successful")

        self.log.info("Checking Readiness of the CS machine")
        _commserv_client = self.commcell.commserv_client
        if _commserv_client.is_ready:
            self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Check Readiness Failed")
            raise Exception("Check readiness for CS after upgrade.")

    def post_upgrade_validations(self):
        """
        Validates required functionality after upgrade is finished
        """
        self.log.info("Starting Validations post Upgrade")

        self.log.info("****************************** VALIDATION 1 ***************************************")
        self.log.info("Refreshing Client, Subclient objects and Validating pre Upgrade configurations aren't modified")
        self.client.refresh()
        self.client2.refresh()
        self.subclient_list[0].refresh()
        self.subclient_list[1].refresh()
        self.subclient_list[2].refresh()
        self.subclient_list[3].refresh()
        self.log.info(
            "Logging the current config pre Upgrade -- Client1: EncryptionSetting: %s"
            " Client2: EncryptionSetting: %s, CipherType: %s, KeyLen: %s. "
            "Client1 SC1: %s, Client1 SC2: %s, Client2 SC1: %s, Client2 SC2: %s",
            self.client.properties.get('clientProps').get('encryptionSettings'),
            self.client2.properties.get('clientProps').get('encryptionSettings'),
            self.client2.properties.get('clientProps').get('CipherType'),
            self.client2.properties.get('clientProps').get('EncryptKeyLength'),
            self.subclient_list[0].encryption_flag, self.subclient_list[1].encryption_flag,
            self.subclient_list[2].encryption_flag, self.subclient_list[3].encryption_flag
        )
        if self.client.properties.get('clientProps').get('encryptionSettings') == 0:
            self.log.info("Validation PASSED: Client1 Encryption settings are not modified")
        else:
            raise Exception("Client1 Encryption settings are modified after CS Upgrade")
        if (self.client2.properties.get('clientProps').get('encryptionSettings') == 1
                and self.client2.properties.get('clientProps').get('CipherType') == 2
                and self.client2.properties.get('clientProps').get('EncryptKeyLength') == 256):
            self.log.info("Validation PASSED: Client2 Encryption settings are not modified")
        else:
            raise Exception("Client2 Encryption settings are modified after CS Upgrade")
        if (self.subclient_list[0].encryption_flag == 'ENC_NETWORK_AND_MEDIA'
                and self.subclient_list[1].encryption_flag == 'ENC_MEDIA_ONLY'
                and self.subclient_list[2].encryption_flag == 'ENC_NETWORK_AND_MEDIA'
                and self.subclient_list[3].encryption_flag == 'ENC_MEDIA_ONLY'):
            self.log.info("Validation PASSED: Subclient Encryption settings are not modified")
        else:
            raise Exception("SubClient Encryption settings are modified after CS Upgrade")

        self.log.info("****************************** VALIDATION 2 ***************************************")

        self.log.info("Promote Copy-3 as Primary by updating DB")
        query = f"update archGroup " \
                f"set defaultCopy = {self.copy_3.copy_id} where id = {self.storage_policy.storage_policy_id}"
        self.log.info(f"Query is : [{query}]")
        self.opt_selector.update_commserve_db(query)
        query = f"update archGroupCopy set copy = 1, sourceCopyId=0 where id = {self.copy_3.copy_id}"
        self.log.info(f"Query is : [{query}]")
        self.opt_selector.update_commserve_db(query)
        query = f"update archGroupCopy set copy = 3 where id = {self.copy_1.copy_id}"
        self.log.info(f"Query is : [{query}]")
        self.opt_selector.update_commserve_db(query)
        self.log.info("Copy Promotion Done")

        self.log.info("Deleting Old Primary Copy and Copy-2")
        self.storage_policy.delete_secondary_copy(self.copy_1.copy_name)
        self.storage_policy.delete_secondary_copy(self.copy_2.copy_name)
        self.log.info(f"Running DV2 on {self.storage_pool_name}_3")
        engine = self.commcell.deduplication_engines.get(
            self.storage_pool3.global_policy_name, self.storage_pool3.copy_name)
        store = engine.get(engine.all_stores[0][0])
        dv2_job = store.run_ddb_verification(False, False)
        if not dv2_job.wait_for_completion() or dv2_job.status.lower() != 'completed':
            raise Exception(f'DV2 Job: {dv2_job.job_id} did not complete without any errors'
                            f' JPR: {dv2_job.delay_reason}')
        self.log.info(f"DV2 Job: {dv2_job.job_id} completed without any errors")
        self.log.info('Validation PASSED: DV2 Job completed successfully')

        self.log.info("All Validations completed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.cleanup()
            self.initial_setup()
            self.pre_upgrade_steps()
            self.upgrade_steps()
            self.post_upgrade_validations()
        except Exception as exp:
            self.log.error('TC Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
