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

    validate_aux_populator()    --  validates if populator feature has kicked off or not for the auxcopy jobs

    post_upgrade_validations()  --  validates required functionality after upgrade is finished

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this case

"67861": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login",
        "PrimaryCopyMediaAgent"     : "Name of MediaAgent for Source Copy"
        "SecondaryCopyMediaAgent"   : "Name of MediaAgent for Destination Copy"
        *** optional ***
        "CUPack"            : HPKNumber
    }

Note:
    - Populate CoreUtils/Templates/config.json/
        "Install":"download_server": to the download server that the cs is pointing.
"""
import time

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

        self.name = "Upgrade Automation - Aux Populator Validations"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "PrimaryCopyMediaAgent": None,
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
        self.copy_4 = None
        self.subclient_list = []
        self.backup_jobs_list = []
        self.auxcopy_job1 = None
        self.auxcopy_job2 = None

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.update_helper = None
        self.install_helper = None

        self.tc_client_path = None
        self.tc_media_agent1_path = None
        self.tc_media_agent2_path = None
        self.mount_path1 = None
        self.mount_path2 = None
        self.content_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None
        self.cs_sp_pre_upg = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # self.config_json = config.get_config()
        self.cs_sp_pre_upg = int(self.commcell.commserv_client.service_pack)
        if not self.cs_sp_pre_upg <= 34 or not int(self.tcinputs.get("ServicePack")) > 34:
            raise Exception("TestCase not valid as TC requirement is: source SP <= 34 and Target SP > 34")

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

        ma1_drive = self.opt_selector.get_drive(self.media_agent_machine1, 25 * 1024)
        ma2_drive = self.opt_selector.get_drive(self.media_agent_machine2, 25 * 1024)
        client_drive = self.opt_selector.get_drive(self.client_machine, 25 * 1024)

        self.tc_client_path = self.client_machine.join_path(client_drive, str(self.id))
        self.tc_media_agent1_path = self.media_agent_machine1.join_path(ma1_drive, str(self.id))
        self.tc_media_agent2_path = self.media_agent_machine2.join_path(ma2_drive, str(self.id))
        self.content_path = self.client_machine.join_path(self.tc_client_path, "content_path")
        self.mount_path1 = self.media_agent_machine1.join_path(self.tc_media_agent1_path, 'MP1')
        self.mount_path2 = self.media_agent_machine1.join_path(self.tc_media_agent2_path, 'MP2')
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
            self.storage_pool1 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_1', self.mount_path1,
                                                                 self.tcinputs.get("PrimaryCopyMediaAgent"),
                                                                 self.tcinputs.get("PrimaryCopyMediaAgent"),
                                                                 self.dedup_store_path1)
        else:
            self.storage_pool1 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_1')
        self.log.info(f"Storage pool {self.storage_pool_name}_1 configured")

        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
            self.storage_pool2 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_2', self.mount_path2,
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
                storage_policy_name=f'{self.storage_policy_name}_2', global_policy_name=f'{self.storage_pool_name}_1',
                global_dedup_policy=True)
        else:
            self.storage_policy_2 = self.commcell.storage_policies.get(f'{self.storage_policy_name}_2')
        self.storage_policy_2.create_secondary_copy('Copy-2', global_policy=f'{self.storage_pool_name}_2')
        self.mm_helper.remove_autocopy_schedule(f'{self.storage_policy_name}_2', 'Copy-2')
        self.copy_3 = self.storage_policy_2.get_copy('Primary')
        self.copy_4 = self.storage_policy_2.get_copy('Copy-2')

        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.log.info("Configuring 2 Subclients on Backupset")
        for index in range(2):
            subclient_name = f'{self.subclient_name}_{index}'
            if not self.backup_set.subclients.has_subclient(subclient_name):
                self.backup_set.subclients.add(subclient_name, f'{self.storage_policy_name}_{index + 1}')
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
            self.opt_selector.create_uncompressable_data(self.client_machine, content_path, 4, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient_list[index].backup(backup_level='Full'))
            self.log.info("Backup Job: %s started for : %s_%s",
                          self.backup_jobs_list[index].job_id, self.subclient_name, index)

        for index in range(2):
            if not self.backup_jobs_list[index].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index].job_id)

        self.log.info(f"Running Auxcopy to {self.storage_policy_name}_1 Copy 2")
        self.auxcopy_job1 = self.storage_policy_1.run_aux_copy()
        self.log.info(
            f"AuxCopy job {self.auxcopy_job1.job_id} Initiated. waiting for the job status as running by 150 secs")
        retry = 10
        while self.auxcopy_job1.status.lower() != 'running' and retry > 0:
            time.sleep(15)
            retry -= 1
        if retry == 0:
            raise Exception(f"Auxcopy job {self.auxcopy_job1.job_id} didn't get to running state in 150 secs")
        self.log.info("Suspending Auxcopy job. Will resume it post upgrade")
        self.auxcopy_job1.pause(wait_for_job_to_pause=True)
        self.log.info("Auxcopy job suspended.")

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

        self.log.info(f"Starting Service pack upgrade of CS, MAs from SP %s to %s",
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

        self.log.info("SP upgrade on MA")
        self.update_helper.push_sp_upgrade(client_computers=[self.tcinputs.get('PrimaryCopyMediaAgent'),
                                                             self.tcinputs.get('SecondaryCopyMediaAgent')])
        self.log.info("SP upgrade of MAs successful")

    def validate_aux_populator(self, pre_upg_aux, post_upg_aux):
        """Validates if Populator feature has kicked off or not for the Auxcopy jobs
        Args:
            pre_upg_aux(Job)    --  Job object for Auxcopy launched prior to upgrade

            post_upg_aux(Job)   --  Job object for Auxcopy launched post upgrade
        Returns:
              bool  --  Boolean to indicate whether validation passed on not
        """
        self.log.info("Starting Validating if Populator has kicked off or not for the Auxcopy job")

        failed_validations = []
        self.log.info("Validating JMJobOptions for the auxcopy jobs")
        query = f'''select count(*) from JMJobOptions
                where attributeName = 'Using CVJobReplicatorPopulator'
                    and JobId = {pre_upg_aux.job_id} and attributeValueInt = 1'''
        self.log.info(f'Executing Query: {query}')
        self.csdb.execute(query)
        option1 = int(self.csdb.fetch_one_row()[0])
        query = f'''select count(*) from JMJobOptions
                where attributeName = 'Using CVJobReplicatorPopulator'
                    and JobId = {post_upg_aux.job_id} and attributeValueInt = 1'''
        self.log.info(f'Executing Query: {query}')
        self.csdb.execute(query)
        option2 = int(self.csdb.fetch_one_row()[0])
        if option1 == 0 and option2 > 0:
            # option 1 expected to be 0: not using populator. option 2 expected to be 1: using populator
            self.log.info("JMJobOptions set correctly for both AuxCopies")
        else:
            self.log.error(
                f"JMJobOptions are not set correctly for the Auxcopy Jobs. "
                f"PreUpgrade Aux: {pre_upg_aux.job_id}: {option1}, PostUpgrade Aux: {post_upg_aux}: {option2}")
            failed_validations.append(
                f"JMJobOptions are not set correctly for the Auxcopy Jobs."
                f" PreUpgrade Aux: {pre_upg_aux.job_id}: {option1}, PostUpgrade Aux: {post_upg_aux}: {option2}")

        self.log.info("Validate CVJobReplicatorPopulator logs on CS for auxcopy jobs")
        log_string = f'AMChunkReplicateHandler::isNewStreamReaderPossibleForCoordinator'
        (matched_line, matched_string) = self.dedup_helper.parse_log(
            self.commcell.commserv_name, 'CVJobReplicatorPopulator.log', log_string, pre_upg_aux.job_id)
        if not matched_line:
            self.log.info('Validation Pass: Populator is not kicked off for Auxcopy job launched pre upgrade')
        else:
            self.log.error('Populator is kicked off for Auxcopy job launched pre upgrade')
            failed_validations.append('Populator is kicked off for Auxcopy job launched pre upgrade')

        (matched_line, matched_string) = self.dedup_helper.parse_log(
            self.commcell.commserv_name, 'CVJobReplicatorPopulator.log', log_string, post_upg_aux.job_id)
        if matched_line:
            self.log.info('Validation Pass: Populator is kicked off for Auxcopy job launched post upgrade')
        else:
            self.log.error('Populator is not kicked off for Auxcopy job launched post upgrade')
            failed_validations.append('Populator is not kicked off for Auxcopy job launched post upgrade')

        if failed_validations:
            return False
        return True

    def post_upgrade_validations(self):
        """
        Validates required functionality after upgrade is finished
        """
        self.log.info("Starting Validations post Upgrade")

        self.log.info(f"Running Auxcopy to {self.storage_policy_name}_1 Copy-2: {self.auxcopy_job1.job_id}")
        self.auxcopy_job1.resume(wait_for_job_to_resume=True)
        self.log.info(f"Running Auxcopy to {self.storage_policy_name}_2 Copy-2")
        self.auxcopy_job2 = self.storage_policy_2.run_aux_copy()
        self.log.info(f"AuxCopy job {self.auxcopy_job2.job_id} Initiated")

        self.log.info("Waiting for the auxcopy jobs to complete")
        if not self.auxcopy_job1.wait_for_completion():
            raise Exception(
                f"AuxCopy job {self.auxcopy_job1.job_id} failed with JPR: {self.auxcopy_job1.delay_reason}")
        self.log.info("AuxCopy Job %s completed", self.auxcopy_job1.job_id)
        if not self.auxcopy_job2.wait_for_completion():
            raise Exception(
                f"AuxCopy job {self.auxcopy_job2.job_id} failed with JPR: {self.auxcopy_job2.delay_reason}")
        self.log.info("AuxCopy Job %s completed", self.auxcopy_job2.job_id)

        self.log.info("Validating Populator process usage for the auxcopy jobs")
        if not self.validate_aux_populator(self.auxcopy_job1, self.auxcopy_job2):
            raise Exception("Validation failed post upgrade for Aux Populator process usage")
        self.log.info("Validation passed post upgrade for Aux Populator process usage")

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
