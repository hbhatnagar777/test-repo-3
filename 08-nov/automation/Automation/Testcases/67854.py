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
    "67854": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login",
        "MediaAgentName"    : "Name of MediaAgent"
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

        self.name = "Upgrade Automation - Encryption Configurations with Client Using Storage Policy Encryption"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "MediaAgentName": None
        }
        # self.config_json = None
        self.cs_machine = None
        self.client_machine = None
        self.media_agent_machine = None

        self.backupset_suffix = None
        self.subclient_suffix = None
        self.storage_pool_suffix = None
        self.storage_policy_suffix = None
        self.backupset_list = []
        self.subclient_list = []
        self.dv_jobs_list = []
        self.sidb_stores_list = []
        self.backup_jobs_list = []
        self.storage_pool_list = []
        self.storage_policy_list = []

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.update_helper = None
        self.install_helper = None

        self.tc_client_path = None
        self.tc_media_agent_path = None
        self.mount_path = None
        self.content_path = None
        self.dedup_store_path = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # self.config_json = config.get_config()
        self.log.info("Setting up testcase variables and objects")
        self.cs_machine = Machine(machine_name=self.tcinputs.get('CSHostName'),
                                  username=self.tcinputs.get('CSMachineUsername'),
                                  password=self.tcinputs.get('CSMachinePassword'))
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.media_agent_machine = Machine(self.tcinputs.get("MediaAgentName"), self.commcell)

        suffix = f'{self.tcinputs.get("MediaAgentName")}{self.tcinputs.get("ClientName")}'

        self.subclient_suffix = f"{self.id}_SC_{suffix}_"
        self.backupset_suffix = f"{self.id}_BS_{suffix}_"
        self.storage_pool_suffix = f"{self.id}_Pool_{suffix}_"
        self.storage_policy_suffix = f"{self.id}_SP_{suffix}_"

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.install_helper = InstallHelper(self.commcell)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)

        ma_drive = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        client_drive = self.opt_selector.get_drive(self.client_machine, 25*1024)

        self.tc_client_path = self.client_machine.join_path(client_drive, str(self.id))
        self.tc_media_agent_path = self.media_agent_machine.join_path(ma_drive, str(self.id))
        self.content_path = self.client_machine.join_path(self.tc_client_path, "content_path")

        self.mount_path = self.media_agent_machine.join_path(self.tc_media_agent_path, 'MP')
        self.dedup_store_path = self.media_agent_machine.join_path(self.tc_media_agent_path, 'DDB')

    def cleanup(self,):
        """
        Cleans up the environment created by tc on the commcell in current/previous runs
        """
        try:
            self.log.info("Cleanup Started")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            for index in range(4):
                if self.agent.backupsets.has_backupset(f'{self.backupset_suffix}_{index}'):
                    self.agent.backupsets.delete(f'{self.backupset_suffix}_{index}')
            for index in range(4):
                if self.commcell.storage_policies.has_policy(f'{self.storage_policy_suffix}_{index}'):
                    self.commcell.storage_policies.get(
                        f'{self.storage_policy_suffix}_{index}').reassociate_all_subclients()
                    self.commcell.storage_policies.delete(f'{self.storage_policy_suffix}_{index}')
            for index in range(4):
                if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_suffix}_{index}'):
                    self.commcell.storage_pools.delete(f'{self.storage_pool_suffix}_{index}')
            self.log.info("Cleanup Completed")
        except Exception as exp:
            self.log.warning('Cleanup Failed. Please cleanup manually. Error: %s', str(exp))

    def initial_setup(self):
        """
        Configures the Environment require for TC
        """
        self.log.info("Configuring 4 storage pools: 2 Non Dedupe, 2 Dedupe")
        for index in range(4):
            if index <= 1:
                # 0, 1 non dedup pools
                ddb_ma = None
                ddb_path = None
            else:
                # 2, 3 dedup pools
                ddb_ma = self.tcinputs.get("MediaAgentName")
                ddb_path = f'{self.dedup_store_path}_{index}'
            if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_suffix}_{index}'):
                self.storage_pool_list.append(self.commcell.storage_pools.add(
                    f'{self.storage_pool_suffix}_{index}', f'{self.mount_path}_{index}',
                    self.tcinputs.get("MediaAgentName"), ddb_ma, ddb_path
                ))
            else:
                self.storage_pool_list.append(self.commcell.storage_pools.get(f'{self.storage_pool_suffix}_{index}'))
            if index > 1:
                self.log.info(f"Dedup: {self.storage_pool_suffix}_{index} configured")
            else:
                self.log.info(f"Non Dedup: {self.storage_pool_suffix}_{index} configured")

        self.log.info("Configuring 4 Storage Policies using the earlier created Storage Pools")
        for index in range(4):
            # 0, 1 non dedup sp. 2, 3 dedup sp
            if not self.commcell.storage_policies.has_policy(f'{self.storage_policy_suffix}_{index}'):
                self.storage_policy_list.append(self.commcell.storage_policies.add(
                    storage_policy_name=f'{self.storage_policy_suffix}_{index}',
                    global_policy_name=f'{self.storage_pool_suffix}_{index}', global_dedup_policy=bool(index//2)
                ))
            else:
                self.storage_policy_list.append(
                    self.commcell.storage_policies.get(f'{self.storage_policy_suffix}_{index}'))
            self.log.info(f"Storage policy {self.storage_policy_suffix} configured")

        self.log.info("Configuring 4 Backup sets")
        for index in range(4):
            self.backupset_list.append(
                self.mm_helper.configure_backupset(f'{self.backupset_suffix}_{index}', self.agent))

        self.log.info("Configuring 4 Subclients each on 4 Backupsets."
                      "With all 4 Subclients in a Backupset being associated to same Storage Policy ")
        for index_b in range(4):
            for index_s in range(4):
                # all subclients in a bs point to same sp
                backupset_name = f'{self.backupset_suffix}_{index_b}'
                storage_policy_name = f'{self.storage_policy_suffix}_{index_b}'
                # subclients with same index use same content. Ex- bs0: sc0, bs1: sc0, bs2: sc0, bs3: sc0 - c:\data_0
                subclient_name = f'{self.subclient_suffix}_{index_s}'
                content_path = self.client_machine.join_path(self.content_path, f'Data_{index_s}')
                if not self.backupset_list[index_b].subclients.has_subclient(subclient_name):
                    self.backupset_list[index_b].subclients.add(subclient_name, storage_policy_name)
                self.subclient_list.append(self.backupset_list[index_b].subclients.get(subclient_name))
                self.subclient_list[-1].content = [content_path]
                self.log.info(
                    f"Configured BS:{backupset_name} - Subclient: {subclient_name} "
                    f"- SP: {storage_policy_name} - Content: {content_path}")

    def pre_upgrade_steps(self):
        """
        Run Data operations prior to upgrade
        """
        self.log.info("Starting pre upgrade steps")

        self.log.info("Disabling Encryption on Pools 0(Non Dedup Pool), 2(Dedup Pool) "
                      " and Enabling settings - ReEncrypt: GOST 256 on Pools 1(Non Dedup Pool), 3(Dedup Pool)")
        for index in range(4):
            if index % 2 == 0:
                self.storage_pool_list[index].get_copy().set_encryption_properties(plaintext=True)
            else:
                self.storage_pool_list[index].get_copy().set_encryption_properties(
                    re_encryption=True, encryption_type="GOST", encryption_length=256)

        self.log.info("Setting Client, Subclient encryption settings: Use storage policy settings."
                      "On all Backup Sets, configuring below Encryption settings: "
                      "SC0: None, SC1: Encrypt Media Only, SC2: Encrypt Network and Media, SC3: Encrypt Network only")
        self.client.set_encryption_property("USE_SPSETTINGS")
        # above operation sets the client enc. settings as: 0
        self.log.info(f"Client Enc. Settings: "
                      f"EncryptionSetting - {self.client.properties.get('clientProps').get('encryptionSettings')}")

        for index in range(16):
            if index % 4 == 0:
                self.subclient_list[index].encryption_flag = 'ENC_NONE'
            elif index % 4 == 1:
                self.subclient_list[index].encryption_flag = 'ENC_MEDIA_ONLY'
            elif index % 4 == 2:
                self.subclient_list[index].encryption_flag = 'ENC_NETWORK_AND_MEDIA'
            else:
                self.subclient_list[index].encryption_flag = 'ENC_NETWORK_ONLY'
            self.log.info(f"BS {index//4}, SC {index % 4} - {self.subclient_list[index].encryption_flag}")

        self.log.info("Running Backups for each of the subclients and waiting for the jobs to complete")
        for index in range(16):
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index % 4}')
            if index // 4 == 0:
                self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 1, num_of_folders=0,
                                                             delete_existing=True)
            else:
                # as mentioned earlier we use same content for same indexed subclients among all backupsets.
                # so we generate data only once
                self.log.info(f'Running backup with same content generated earlier at {content_path}')
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info(
                f"Backup Job: {self.backup_jobs_list[index].job_id} started for : BS {index//4}, SC {index % 4}")
        for index in range(16):
            if not self.backup_jobs_list[index].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index].job_id)

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
        for index in range(16):
            self.subclient_list[index].refresh()
        self.log.info("Logging the current config post Upgrade "),
        self.log.info(f"Client Enc. Settings: "
                      f"EncryptionSetting - {self.client.properties.get('clientProps').get('encryptionSettings')}")
        for index in range(16):
            self.log.info(f"BS {index//4}, SC {index % 4} - {self.subclient_list[index].encryption_flag}")

        if self.client.properties.get('clientProps').get('encryptionSettings') == 0:
            self.log.info("Validation PASSED: Client Encryption settings are not modified")
        else:
            raise Exception("Client Encryption settings are modified after CS Upgrade")
        for index in range(16):
            if (index % 4 == 0 and self.subclient_list[index].encryption_flag == 'ENC_NONE') or \
                (index % 4 == 1 and self.subclient_list[index].encryption_flag == 'ENC_MEDIA_ONLY') or \
                    (index % 4 == 2 and self.subclient_list[index].encryption_flag == 'ENC_NETWORK_AND_MEDIA') or \
                    (index % 4 == 3 and self.subclient_list[index].encryption_flag == 'ENC_NETWORK_ONLY'):
                pass
            else:
                raise Exception("SubClient Encryption settings are modified after CS Upgrade")
        self.log.info("Validation PASSED: Subclient Encryption settings are not modified")

        self.log.info("Changing Encryption on Pools. BlowFish 128 on Pools 0(Non Dedup Pool), 2(Dedup Pool) "
                      " and TwoFish 128 on Pools 1(Non Dedup Pool), 3(Dedup Pool)")
        for index in range(4):
            if index % 2 == 0:
                self.storage_pool_list[index].get_copy().set_encryption_properties(
                    re_encryption=True, encryption_type="BlowFish", encryption_length=128)
            else:
                self.storage_pool_list[index].get_copy().set_encryption_properties(
                    re_encryption=True, encryption_type="TwoFish", encryption_length=128)

        self.log.info("****************************** VALIDATION 2 ***************************************")
        self.log.info(
            "Start Full DV1, Complete DV2 for each of the Pools and wait for the jobs to complete without any errors")
        storage_policy_copy_list = []
        for index in range(2):
            storage_policy_copy_list.append(self.storage_policy_list[index].get_copy('Primary'))
            storage_policy_copy_list[index]._copy_properties["copyFlags"]["archiveCheckBitmap"] = 0
            storage_policy_copy_list[index]._set_copy_properties()
            storage_policy_copy_list[index]._copy_properties["copyFlags"]["archiveCheckBitmap"] = 1
            storage_policy_copy_list[index]._set_copy_properties()
            self.dv_jobs_list.append(self.storage_policy_list[index].run_data_verification(jobs_to_verify='ALL'))
            self.log.info(f"DV1 Job: {self.dv_jobs_list[-1].job_id} started")
        for index in range(2, 4):
            engine = self.commcell.deduplication_engines.get(
                self.storage_pool_list[index].global_policy_name, self.storage_pool_list[index].copy_name)
            self.sidb_stores_list.append(engine.get(engine.all_stores[0][0]))
            self.dv_jobs_list.append(self.sidb_stores_list[index-2].run_ddb_verification(False, False))
            self.log.info(f"DV2 Job: {self.dv_jobs_list[-1].job_id} started")
        for index in range(4):
            if not self.dv_jobs_list[index].wait_for_completion() or\
                    self.dv_jobs_list[index].status.lower() != 'completed':
                raise Exception(f'DV Job: {self.dv_jobs_list[index].job_id} did not complete without any errors'
                                f' JPR: {self.dv_jobs_list[index].delay_reason}')
            self.log.info(f"DV Job: {self.dv_jobs_list[index].job_id} completed without any errors")
        self.log.info('Validation PASSED: All DV2 jobs completed without any errors')

        self.log.info("****************************** VALIDATION 3 ***************************************")
        self.log.info("Running Backups for each of the subclients and waiting for the jobs to complete")
        for index in range(16):
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index % 4}')
            if index // 4 == 0:
                self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 1, num_of_folders=0,
                                                             delete_existing=True)
            else:
                # as mentioned earlier we use same content for same indexed subclients among all backupsets.
                # so we generate data only once
                self.log.info(f'Running backup with same content generated earlier at {content_path}')
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info(
                f"Backup Job: {self.backup_jobs_list[index + 16].job_id} started for : BS {index // 4}, SC {index % 4}")
        for index in range(16):
            if not self.backup_jobs_list[index + 16].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index + 16].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index + 16].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index + 16].job_id)

        self.log.info("****************************** VALIDATION 4 ***************************************")
        self.log.info(
            "Start DV1, Complete DV2 for each of the Pools and wait for the jobs to complete without any errors")
        for index in range(2):
            storage_policy_copy_list[index]._copy_properties["copyFlags"]["archiveCheckBitmap"] = 0
            storage_policy_copy_list[index]._set_copy_properties()
            storage_policy_copy_list[index]._copy_properties["copyFlags"]["archiveCheckBitmap"] = 1
            storage_policy_copy_list[index]._set_copy_properties()
            self.dv_jobs_list.append(self.storage_policy_list[index].run_data_verification(jobs_to_verify='ALL'))
            self.log.info(f"DV1 Job: {self.dv_jobs_list[-1].job_id} started")
        for index in range(2, 4):
            self.dv_jobs_list.append(self.sidb_stores_list[index-2].run_ddb_verification(False, False))
            self.log.info(f"DV2 Job: {self.dv_jobs_list[-1].job_id} started")
        for index in range(4):
            if not self.dv_jobs_list[index + 4].wait_for_completion() or \
                    self.dv_jobs_list[index + 4].status.lower() != 'completed':
                raise Exception(f'DV2 Job: {self.dv_jobs_list[index + 4].job_id} did not complete without any errors'
                                f' JPR: {self.dv_jobs_list[index + 4].delay_reason}')
            self.log.info(f"DV2 Job: {self.dv_jobs_list[index + 4].job_id} completed without any errors")
        self.log.info('Validation PASSED: All DV2 jobs completed without any errors')

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
