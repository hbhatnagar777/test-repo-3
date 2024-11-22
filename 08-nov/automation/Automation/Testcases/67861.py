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

    validate_pool_ddbma_mapping()   --  validate mmstoragepooltoddbma population

    validate_path_trimming()        --  validate idxaccesspath entries are trimmed with trailing slashes

    validate_storage_accelerator()  --  validates if sa feature has kicked off or not

    post_upgrade_validations()  --  validates required functionality after upgrade is finished

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this case

Sample JSON:
    "67861": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login",
        "PrimaryCopyMediaAgent"     : "Name of MediaAgent for Source Copy"
        "CloudLibraryName"          : "Name of Cloud Library"
        "SecondaryCopyMediaAgent"   : "Name of MediaAgent for Destination Copy where CloudLib is hosted"
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

        self.name = "Upgrade Automation - Storage Accelerator and Throttling Validation"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "PrimaryCopyMediaAgent": None,
            "CloudLibraryName": None,
            "SecondaryCopyMediaAgent": None
        }
        # self.config_json = None
        self.cs_machine = None
        self.ma1_client = None
        self.ma2_client = None
        self.client_machine = None
        self.media_agent_machine1 = None
        self.media_agent_machine2 = None

        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.backup_set = None
        self.storage_pool1 = None
        self.storage_pool2 = None
        self.storage_policy_1 = None
        self.storage_policy_2 = None
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
        self.tc_media_agent1_path = None
        self.tc_media_agent2_path = None
        self.mount_path = None
        self.content_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # self.config_json = config.get_config()
        self.log.info("Setting up testcase variables and objects")
        self.ma1_client = self.commcell.clients.get(self.tcinputs.get("PrimaryCopyMediaAgent"))
        self.ma2_client = self.commcell.clients.get(self.tcinputs.get("SecondaryCopyMediaAgent"))
        self.cs_machine = Machine(machine_name=self.tcinputs.get('CSHostName'),
                                  username=self.tcinputs.get('CSMachineUsername'),
                                  password=self.tcinputs.get('CSMachinePassword'))
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.media_agent_machine1 = Machine(self.tcinputs.get("PrimaryCopyMediaAgent"), self.commcell)
        self.media_agent_machine2 = Machine(self.tcinputs.get("SecondaryCopyMediaAgent"), self.commcell)

        suffix = f'{self.tcinputs.get("PrimaryCopyMediaAgent")}{self.tcinputs.get("ClientName")}'

        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"
        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.storage_pool_name = f"{self.id}_StoragePool{suffix}"

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.install_helper = InstallHelper(self.commcell)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)

        ma1_drive = self.opt_selector.get_drive(self.media_agent_machine1, 25*1024)
        ma2_drive = self.opt_selector.get_drive(self.media_agent_machine2, 25*1024)
        client_drive = self.opt_selector.get_drive(self.client_machine, 25*1024)

        self.tc_client_path = self.client_machine.join_path(client_drive, str(self.id))
        self.tc_media_agent1_path = self.media_agent_machine1.join_path(ma1_drive, str(self.id))
        self.tc_media_agent2_path = self.media_agent_machine2.join_path(ma2_drive, str(self.id))
        self.content_path = self.client_machine.join_path(self.tc_client_path, "content_path")
        self.mount_path = self.media_agent_machine1.join_path(self.tc_media_agent1_path, 'MP')
        self.dedup_store_path1 = self.media_agent_machine1.join_path(self.tc_media_agent1_path, 'DDB')
        self.dedup_store_path2 = self.media_agent_machine2.join_path(self.tc_media_agent2_path, 'DDB')

    def cleanup(self):
        """
        Cleans up the environment created by tc on the commcell in current/previous runs
        """
        try:
            self.log.info("Cleanup Started")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}_1'):
                self.commcell.storage_policies.get(f'{self.storage_policy_name}_1').reassociate_all_subclients()
                self.commcell.storage_policies.delete(f'{self.storage_policy_name}_1')
            if self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}_2'):
                self.commcell.storage_policies.get(f'{self.storage_policy_name}_2').reassociate_all_subclients()
                self.commcell.storage_policies.delete(f'{self.storage_policy_name}_2')
            if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_1'):
                self.commcell.storage_pools.delete(f'{self.storage_pool_name}_1')
            if self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
                self.commcell.storage_pools.delete(f'{self.storage_pool_name}_2')
            self.log.info("Cleanup Completed")
        except Exception as exp:
            self.log.warning('Cleanup Failed. Please cleanup manually. Error: %s', str(exp))

    def initial_setup(self):
        """
        Configures the Environment require for TC
        """
        self.log.info("Configuring 2 Dedupe storage pools")
        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_1'):
            self.storage_pool1 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_1', self.mount_path,
                                                                 self.tcinputs.get("PrimaryCopyMediaAgent"),
                                                                 self.tcinputs.get("PrimaryCopyMediaAgent"),
                                                                 self.dedup_store_path1)
        else:
            self.storage_pool1 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_1')
        self.log.info(f"Storage pool {self.storage_pool_name}_1 configured")

        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
            self.storage_pool2 = self.mm_helper.add_storage_pool_using_existing_library(f'{self.storage_pool_name}_2',
                                                                self.tcinputs.get("CloudLibraryName"),
                                                                self.tcinputs.get("SecondaryCopyMediaAgent"),
                                                                self.tcinputs.get("SecondaryCopyMediaAgent"),
                                                                self.dedup_store_path2)
        else:
            self.storage_pool2 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_2')
        self.log.info(f"Storage pool {self.storage_pool_name}_2 configured")

        self.log.info(f"Configuring Storage Policy ==> {self.storage_policy_name}_1")
        if not self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}_1'):
            self.storage_policy_1 = self.commcell.storage_policies.add(
                storage_policy_name=f'{self.storage_policy_name}_1', global_policy_name=f'{self.storage_pool_name}_1',
                global_dedup_policy=True)
        else:
            self.storage_policy_1 = self.commcell.storage_policies.get(f'{self.storage_policy_name}_1')
        self.storage_policy_1.create_secondary_copy('Copy-2', global_policy=f'{self.storage_pool_name}_2')
        self.mm_helper.remove_autocopy_schedule(f'{self.storage_policy_name}_1', 'Copy-2')
        self.copy_1 = self.storage_policy_1.get_copy('Primary')
        self.copy_2 = self.storage_policy_1.get_copy('Copy-2')
        self.log.info(f"Configuring Storage Policy ==> {self.storage_policy_name}_2")
        if not self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}_2'):
            self.storage_policy_2 = self.commcell.storage_policies.add(
                storage_policy_name=f'{self.storage_policy_name}_2', global_policy_name=f'{self.storage_pool_name}_2',
                global_dedup_policy=True)
        else:
            self.storage_policy_2 = self.commcell.storage_policies.get(f'{self.storage_policy_name}_2')
        self.copy_3 = self.storage_policy_2.get_copy('Primary')

        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.log.info("Configuring 2 Subclients on Backupset")
        for index in range(2):
            subclient_name = f'{self.subclient_name}_{index}'
            if not self.backup_set.subclients.has_subclient(subclient_name):
                self.backup_set.subclients.add(subclient_name, f'{self.storage_policy_name}_{index+1}')
            self.subclient_list.append(self.backup_set.subclients.get(subclient_name))
            self.log.info("Configured Subclient %s", subclient_name)
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index}')
            self.subclient_list[index].content = [content_path]

    def pre_upgrade_steps(self):
        """
        Run Data operations prior to upgrade
        """
        self.log.info("Starting pre upgrade steps")

        self.log.info("Running Backups for each of the subclients and waiting for the jobs to complete")
        for index in range(2):
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index}')
            self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 1, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info("Backup Job: %s started for : %s_%s",
                          self.backup_jobs_list[index].job_id, self.subclient_name, index)

        for index in range(2):
            if not self.backup_jobs_list[index].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index].job_id)

        self.log.info("Running Auxcopy to Storage Policy 1: Copy 2")
        auxcopy_job = self.storage_policy_1.run_aux_copy()
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

        failed_validations = []
        self.log.info("Validating SA pre Upgrade")
        if not self.validate_storage_accelerator(self.backup_jobs_list[-1], self.ma2_client, self.client):
            self.log.error("SA Validation failed pre upgrade for backup")
            failed_validations.append("SA Validation failed pre upgrade for backup")
        else:
            self.log.info("SA Validation passed pre upgrade for backup")
        if not self.validate_storage_accelerator(auxcopy_job, self.ma2_client, self.ma1_client):
            self.log.error("SA Validation failed pre upgrade for auxcopy")
            failed_validations.append("SA Validation failed pre upgrade for auxcopy")
        else:
            self.log.info("SA Validation passed pre upgrade for auxcopy")
        if failed_validations:
            raise Exception(str(failed_validations))

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
        self.update_helper.push_sp_upgrade(client_computers=[
            self.commcell.commserv_name])
        self.log.info("SP upgrade of CS successful")
        self.log.info(f"Starting Service pack upgrade of MAs from SP %s to %s",
                      str(self.commcell.commserv_version), self.tcinputs.get('ServicePack'))
        self.update_helper.push_sp_upgrade(client_computers=[self.tcinputs.get('PrimaryCopyMediaAgent'),
        self.tcinputs.get('SecondaryCopyMediaAgent')])
        self.log.info("SP upgrade of MAs successful")

        self.log.info("Checking Readiness of the CS machine")
        _commserv_client = self.commcell.commserv_client
        if _commserv_client.is_ready:
            self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Check Readiness Failed")
            raise Exception("Check readiness for CS after upgrade.")

    def validate_pool_ddbma_mapping(self):
        """Validate MMStoragePoolToDDBMA population
        Returns:
              bool  --  Boolean to indicate whether validation passed or not
        """
        if int(self.commcell.commserv_version) >= 34:
            self.log.info("Validating if MMStoragePoolToDDBMA table is populated post upgrade or not")
            query = """select count(*) from MMStoragePoolToDDBMA"""
            self.log.info(f"Executing Query: {query}")
            self.csdb.execute(query)
            result = self.csdb.fetch_one_row()
            self.log.info(f"Result: {result}")
            if int(result[0]) > 0:
                self.log.info("Validation Pass: MMStoragePoolToDDBMA is populated post upgrade")
                return True
            self.log.info("Validation Fail: MMStoragePoolToDDBMA is not populated post upgrade")
            return False
        else:
            return True

    def validate_path_trimming(self):
        """Validate IdxAccessPath entries are trimmed with trailing slashes
        Returns:
              bool  --  Boolean to indicate whether validation passed or not
        """
        self.log.info("Validating if trailing slashes in IdxAccessPath entries are trimmed")
        query = """select IdxAccessPathId, Path from IdxAccessPath"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"Result: {result}")
        for row in result:
            if row[1][-1] == '\\' or row[1][-1] == '/':
                self.log.info("Validation Fail: Trailing spaces are not trimmed in IdxAccessPath")
                return False
        self.log.info("Validation Pass: Trailing spaces are trimmed in IdxAccessPath post Upgrade")
        return True

    def validate_storage_accelerator(self, job, actual_ma, core_ma):
        """Validates if SA feature has kicked off or not
        Args:
              job(Job)          -- Job object for which SA validation needs to be done

              actual_ma(Client) -- Client object for MA on which the library is configured

              core_ma(Client)   -- Client object for MA which is expected to override for SA

        Returns:
              bool  --  Boolean to indicate whether validation passed or not
        """
        if int(actual_ma.service_pack) >= 32 and int(core_ma.service_pack) >= 32:
            self.log.info("Validating if SA has kicked off or not. It is expected to kickoff as SP Level is >= 32")

            self.log.info("Validate ArchMgr logs on CS for MA Override")
            archmgr_log_string = f'Overriding dest MA as this is detected as CORE MA' \
                                 f'[{core_ma.client_id}]'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.commcell.commserv_name, 'ArchMgr.log', archmgr_log_string,
                job.job_id)
            if matched_line:
                self.log.info('Validation Pass: ArchMgr logs indicate SA kicking off')
            else:
                self.log.error('Validation Fail: No ArchMgr logs to indicate SA kicking off')
                return False

            self.log.info("Validating cvd logs on Core MA, if it has written the chunks or not")
            client_cvd_log_string = 'Creating new chunk id'
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                core_ma.client_name, 'cvd.log', client_cvd_log_string, jobid=job.job_id)
            if matched_line:
                self.log.info('Validation Pass: CVD logs indicate Core MA writing chunks to destination')
                return True
            else:
                self.log.error('Validation Fail: No CVD logs to indicate Core MA writing chunks to destination')
                return False
        else:
            self.log.info("Validating if SA has kicked off or not. It is not expected to kickoff as SP Level is < 32")
            self.log.info("Validate ArchMgr logs for MA Override")
            (matched_line, matched_string) = self.dedup_helper.parse_log(
                self.commcell.commserv_name, 'ArchMgr.log', 'Overriding dest MA as this is detected as CORE MA',
                job.job_id)
            if not matched_line:
                self.log.info('Validation Pass: ArchMgr logs indicate SA not kicking off as expected for lower SP')
                return True
            self.log.error('Validation Fail: ArchMgr logs indicate SA kicking off when not expected for lower SP')
            return False

    def post_upgrade_validations(self):
        """
        Validates required functionality after upgrade is finished
        """
        self.log.info("Starting Validations post Upgrade")

        self.log.info("Running Backups for each of the subclients and waiting for the jobs to complete")
        for index in range(2):
            content_path = self.client_machine.join_path(self.content_path, f'Data_{index}')
            self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 1, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info("Backup Job: %s started for : %s_%s",
                          self.backup_jobs_list[index+2].job_id, self.subclient_name, index)

        for index in range(2):
            if not self.backup_jobs_list[index+2].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index+2].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index+2].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index+2].job_id)

        self.log.info("Running Auxcopy to Storage Policy 1: Copy 2")
        auxcopy_job = self.storage_policy_1.run_aux_copy()
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

        failed_validations = []

        self.log.info("Validating SA post Upgrade")
        if not self.validate_storage_accelerator(self.backup_jobs_list[-1], self.ma2_client, self.client):
            self.log.error("SA Validation failed post upgrade for backup")
            failed_validations.append("SA Validation failed post upgrade for backup")
        else:
            self.log.info("SA Validation passed post upgrade for backup")
        if not self.validate_storage_accelerator(auxcopy_job, self.ma2_client, self.ma1_client):
            self.log.error("SA Validation failed post upgrade for auxcopy")
            failed_validations.append("SA Validation failed post upgrade for auxcopy")
        else:
            self.log.info("SA Validation passed post upgrade for auxcopy")

        if not self.validate_pool_ddbma_mapping():
            self.log.error("Validation failed for MMStoragePoolToDDBMA population post upgrade")
            failed_validations.append("Validation failed for MMStoragePoolToDDBMA population post upgrade")
        else:
            self.log.info("Validation passed for MMStoragePoolToDDBMA population post upgrade")

        if not self.validate_path_trimming():
            self.log.error("Validation failed for Trimming of idxAccessPath entries post upgrade")
            failed_validations.append("Validation failed for Trimming of idxAccessPath entries post upgrade")
        else:
            self.log.info("Validation passed for Trimming of idxAccessPath entries post upgrade")

        if failed_validations:
            raise Exception(str(failed_validations))
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
