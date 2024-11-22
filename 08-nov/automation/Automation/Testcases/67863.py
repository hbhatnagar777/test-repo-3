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

    validate_retention_settings()           --  validate if retention settings are updated post upgrade

    validate_credentials()                  --  validate credentials are not deleted post upgrade

    validate_garbage_collection()           --  validate garbage collection settings are retained post upgrade

    post_upgrade_validations()              --  validates required functionality after upgrade is finished

    update_job_start_time()                 --  update create time for the given sidb store

    run_data_aging()                        --  run data aging job

    verify_job_aged()                       --  verify that jobs are aged

    verify_mm_deleted_af()                  --  verify that mmdeletedaf entries for the jobs are pruned

    update_store_creation_time()            --  update create time for the given sidb store

    verify_store_sealed()                   --  verify if the sidb store is marked sealed

    update_max_wormtimestamp()              --  update the max wormtimestamp for the given store.

    verify_store_pruned()                   --  verify that sidb store is pruned successfully

    seal_clean_store()                      --  perform pruning for worm enabled sidb store

    age_and_prune_data()                    --  marks the jobs as aged and prunes the data

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this case

Sample JSON:
    "67863": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login"
        "MediaAgentName"    : "Name of MediaAgent"
        "UNCPath"           : "UNC Path where MP will be created"
        "credentialName"    : "name of saved credential to access UNC Path"
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

        self.name = "Upgrade Automation - DA Validations"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "MediaAgentName": None,
            "UNCPath": None,
            "credentialName": None
        }
        # self.config_json = None
        self.cs_machine = None
        self.client_machine = None
        self.media_agent_machine = None

        self.worm_store = None
        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.backup_set = None
        self.storage_pool1 = None
        self.storage_pool2 = None
        self.storage_policy = None
        self.copy_1 = None
        self.copy_2 = None
        self.subclient = None
        self.backup_jobs_list = []

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.update_helper = None
        self.install_helper = None

        self.tc_client_path = None
        self.tc_media_agent_path = None
        self.mount_path2 = None
        self.content_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None

        self.ret_pre_upg = None
        self.ext_ret_pre_upg = None
        self.cred_pre_upg = None
        self.gc_pre_upg = None

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

        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"
        self.library_name = f"{self.id}_Lib{suffix}"
        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.storage_pool_name = f"{self.id}_StoragePool{suffix}"

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
        self.mount_path2 = self.media_agent_machine.join_path(self.tc_media_agent_path, 'MP2')
        self.dedup_store_path1 = self.media_agent_machine.join_path(self.tc_media_agent_path, 'DDB1')
        self.dedup_store_path2 = self.media_agent_machine.join_path(self.tc_media_agent_path, 'DDB2')

    def cleanup(self):
        """
        Cleans up the environment created by tc on the commcell in current/previous runs
        """
        try:
            self.log.info("Cleanup Started")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy_name)
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
        self.commcell.disk_libraries.add(f'{self.library_name}_1', self.tcinputs.get("MediaAgentName"),
                                         self.tcinputs.get("UNCPath"),
                                         saved_credential_name=self.tcinputs.get("credentialName"))
        self.log.info("Configuring 2 Dedupe storage pools")
        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_1'):
            self.storage_pool1 = self.mm_helper.add_storage_pool_using_existing_library(f'{self.storage_pool_name}_1',
                                                                 f'{self.library_name}_1',
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.dedup_store_path1)
        else:
            self.storage_pool1 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_1')
        self.log.info(f"Storage pool {self.storage_pool_name}_1 configured")

        if not self.commcell.storage_pools.has_storage_pool(f'{self.storage_pool_name}_2'):
            self.storage_pool2 = self.commcell.storage_pools.add(f'{self.storage_pool_name}_2',
                                                                 self.mount_path2,
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.tcinputs.get("MediaAgentName"),
                                                                 self.dedup_store_path2)
        else:
            self.storage_pool2 = self.commcell.storage_pools.get(f'{self.storage_pool_name}_2')
        self.log.info(f"Storage pool {self.storage_pool_name}_2 configured")

        self.log.info(f"Configuring Storage Policy ==> {self.storage_policy_name}")
        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(
                storage_policy_name=self.storage_policy_name, global_policy_name=f'{self.storage_pool_name}_1',
                global_dedup_policy=True)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
        self.storage_policy.create_secondary_copy('Copy-2', global_policy=f'{self.storage_pool_name}_2')
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, 'Copy-2')

        self.copy_1 = self.storage_policy.get_copy('Primary')
        self.copy_2 = self.storage_policy.get_copy('Copy-2')
        self.copy_1.copy_retention = (15, 1, -1)
        self.copy_2.copy_retention = (2, 1, -1)
        self.storage_pool2.enable_worm_storage_lock(2)

        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.subclient = self.mm_helper.configure_subclient(
            self.backupset_name,
            self.subclient_name,
            self.storage_policy_name,
            self.content_path,
            self.agent)

    def pre_upgrade_steps(self):
        """
        Run Data operations prior to upgrade
        """
        self.log.info("Starting pre upgrade steps")

        self.log.info("Running Backups on subclient and waiting for the jobs to complete")
        for index in range(4):
            self.opt_selector.create_uncompressable_data(self.client_machine, self.content_path, 1, num_of_folders=0,
                                                         delete_existing=True)
            self.backup_jobs_list.append(self.subclient.backup(backup_level='Full'))
            self.log.info("Backup Job: %s started", self.backup_jobs_list[index].job_id)
            if not self.backup_jobs_list[index].wait_for_completion():
                raise Exception(f'Backup Job: {self.backup_jobs_list[index].job_id} failed'
                                f' with JPR: {self.backup_jobs_list[index].delay_reason}')
            self.log.info("Backup Job: %s completed", self.backup_jobs_list[index].job_id)

        self.log.info("Running Auxcopy to Storage Policy 1: Copy 2")
        auxcopy_job = self.storage_policy.run_aux_copy()
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

        worm_engine = self.commcell.deduplication_engines.get(
            self.storage_pool2.global_policy_name, self.storage_pool2.copy_name)
        self.worm_store = worm_engine.get(worm_engine.all_stores[0][0])

        failed_validations = []
        self.log.info("Fetching Retention settings pre upgrade")
        if not self.validate_retention_settings('pre'):
            self.log.error("Retention settings fetch failed")
            failed_validations.append("Retention settings fetch failed")

        self.log.info("Fetching Credentials details pre upgrade")
        if not self.validate_credentials('pre'):
            self.log.error("UNC Credentials validation failed")
            failed_validations.append("UNC Credentials validation failed")

        self.log.info("Fetching Garbage collection settings pre upgrade")
        if not self.validate_garbage_collection('pre'):
            self.log.error("Garbage Collection settings fetch failed")
            failed_validations.append("Garbage Collection settings fetch failed")

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
        self.update_helper.push_sp_upgrade(client_computers=[self.commcell.commserv_name])
        self.log.info("SP upgrade of CS successful")

        self.log.info("Checking Readiness of the CS machine")
        _commserv_client = self.commcell.commserv_client
        if _commserv_client.is_ready:
            self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Check Readiness Failed")
            raise Exception("Check readiness for CS after upgrade.")

    def validate_retention_settings(self, iteration):
        """Validate if retention settings are updated post upgrade
        Args:
            iteration (str) --  "pre"/"post" to indicate whether the check is pre or post upgrade
        Returns:
              bool  --  Boolean to indicate whether validation passed on not
        """
        query1 = """select copyId, retentionDays, fullCycles from archAgingRule"""
        self.log.info(f"Executing Query: {query1}")
        self.csdb.execute(query1)
        result1 = self.csdb.fetch_all_rows()
        query2 = """select copyId, retentionDays, retentionRule, GraceDays from archAgingRuleExtended"""
        self.log.info(f"Result: {result1}")
        self.log.info(f"Executing Query: {query2}")
        self.csdb.execute(query2)
        result2 = self.csdb.fetch_all_rows()
        self.log.info(f"Result: {result2}")
        if iteration == 'pre':
            self.ret_pre_upg = result1
            self.ext_ret_pre_upg = result2
            return True
        elif iteration == 'post':
            if result1 == self.ret_pre_upg and result2 == self.ext_ret_pre_upg:
                return True
        return False

    def validate_credentials(self, iteration):
        """Validate credentials are not deleted post upgrade
        Args:
            iteration (str) --  "pre"/"post" to indicate whether the check is pre or post upgrade
        Returns:
              bool  --  Boolean to indicate whether validation passed on not
        """
        query = """
                select	mdc.DeviceControllerId, mdc.ClientId, mdc.DeviceId, 
                    ac.credentialId, ac.credentialName, ac.userName
                from	MMDeviceController mdc
                    inner join APP_CredentialAssoc aca on mdc.CredentialAssocId = aca.assocId
                    inner join APP_Credentials ac on aca.credentialId = ac.credentialId"""
        self.log.info(f"Executing Query: {query}")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"Result: {result}")
        if iteration == 'pre':
            self.cred_pre_upg = result
            return True
        elif iteration == 'post':
            if result == self.cred_pre_upg:
                return True
        return False

    def validate_garbage_collection(self, iteration):
        """Validate garbage collection settings are retained post upgrade
        Args:
            iteration (str) --  "pre"/"post" to indicate whether the check is pre or post upgrade
        Returns:
              bool  --  Boolean to indicate whether validation passed on not
        """
        engine1 = self.commcell.deduplication_engines.get(
            self.storage_pool1.global_policy_name, self.storage_pool1.copy_name)
        store1 = engine1.get(engine1.all_stores[0][0])
        engine2 = self.commcell.deduplication_engines.get(
            self.storage_pool2.global_policy_name, self.storage_pool2.copy_name)
        store2 = engine2.get(engine2.all_stores[0][0])
        result = [store1.enable_garbage_collection, store2.enable_garbage_collection]
        self.log.info(f"Garbage Collection flags: {result}")
        if iteration == 'pre':
            self.gc_pre_upg = result
            return True
        elif iteration == 'post':
            if result == self.gc_pre_upg:
                return True
        return False

    def post_upgrade_validations(self):
        """
        Validates required functionality after upgrade is finished
        """
        self.log.info("Starting Validations post Upgrade")

        failed_validations = []
        self.log.info("Validating Retention settings post upgrade")
        if not self.validate_retention_settings('post'):
            self.log.error("Retention settings validation failed")
            failed_validations.append("Retention settings validation failed")
        else:
            self.log.info("Retention settings validation passed")

        self.log.info("Validating UNC Credentials details post upgrade")
        if not self.validate_credentials('post'):
            self.log.error("UNC Credentials validation failed")
            failed_validations.append("UNC Credentials validation failed")
        else:
            self.log.info("UNC Credentials validation passed")

        self.log.info("Validating Garbage Collection settings post upgrade")
        if not self.validate_garbage_collection('post'):
            self.log.error("Garbage Collection settings validation failed")
            failed_validations.append("Garbage Collection settings validation failed")
        else:
            self.log.info("Garbage Collection settings validation passed")
        self.log.info("All Validations completed")

        if failed_validations:
            raise Exception(str(failed_validations))

    def update_job_start_time(self, job_id):
        """
        Update start time for the given job in JMBkpStats.
        Args:
            job_id      (int)   -- job if for which start time is to be updated.
        """
        query1 = f"""select servStartDate from JMBkpStats where jobId = {job_id}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        start_time = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"RESULT: {start_time}")
        start_time = start_time - 86400 * 10
        self.log.info("10 Day Backed Time for Job %s is %s", job_id, start_time)
        query2 = f"""update JMBkpStats set servStartDate = {start_time} where jobid = {job_id}"""
        self.log.info("Query: %s", query2)
        self.opt_selector.update_commserve_db(query2)
        self.log.info(f"Successfully Updated start time for {job_id}")

    def run_data_aging(self):
        """Run data aging job"""
        self.log.info("Updating Prune Process Interval to 2")
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 2, 2)
        self.log.info("Updating Maintenance Thread Interval to 5 mins")
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)
        data_aging_job = self.mm_helper.submit_data_aging_job()
        self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error("DA job(%s) failed with JPR: %s.", data_aging_job.job_id, data_aging_job.delay_reason)
            raise Exception(
                f"Data Aging job({data_aging_job.job_id}) failed with JPR: {data_aging_job.delay_reason}.")
        self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

    def verify_job_aged(self, job_list, copy_id):
        """
        Verify that Jobs are Aged.
        Args:
            job_list    - (list) list of jobs to be verified.

            copy_id     - (list) id of storage policy copy

        Returns:
              bool  --  Boolean to indicate whether jobs are aged or not
        """


        self.log.info(f"Validating JMJobDataStats table for {job_list} in copy {copy_id}")
        jobs_str = ','.join(job_list)
        query = f"""select agedBy from JMJobDataStats  where jobid in ({jobs_str}) and archGrpCopyId={copy_id}"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        aged_flags = [x[0] for x in res]
        self.log.info(f"RESULT: {aged_flags}")
        for flag in aged_flags:
            if flag != '512':
                self.log.info("All jobs are not aged yet!")
                return False
        self.log.info("All jobs are aged successfully!")
        return True

    def verify_mm_deleted_af(self, store_id):
        """
        Verify that MMDeletedAF entries for the jobs are pruned.
        Args:
            store_id      (str)   -- SIDB Store id for which mmdeletedaf entries needs to be checked
        Returns:
              bool  --  Boolean to indicate whether mmdeletedaf entries are cleared or not
        """
        self.log.info(f"Validating MMDeletedAF table for {store_id}")
        query = f"""select count(archFileId) from MMDeletedAF where SIDBStoreId = {store_id}"""
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) != 0:
            return False
        self.log.info("MMDeletedAF entries pruned successfully")
        return True

    def update_store_creation_time(self, store_id):
        """
        Update create time for the given SIDB store.
        Args:
            store_id      (str)   -- SIDB Store id for which creation time is to be updated.
        """
        query1 = f"""select CreatedTime from IdxSIDBStore where SIDBStoreId = {store_id}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        created_time = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"RESULT: {created_time}")
        backdated_created_time = created_time - (86400 * 20)
        self.log.info("20 Day Backed CreatedTime for SIDB store %s is %s", store_id, backdated_created_time)
        query2 = f"""update IdxSIDBStore SET CreatedTime={backdated_created_time}  where SIDBStoreId={store_id}"""
        self.log.info("Query: %s", query2)
        self.opt_selector.update_commserve_db(query2)
        self.log.info(f"Successfully Updated CreateTime for {store_id}")

    def verify_store_sealed(self, store_id):
        """
        Verify if the sidb store is marked sealed.
        Args:
            store_id      (str)   -- SIDB Store id to be checked whether selaed or not
        Returns:
              bool  --  Boolean to indicate whether store is sealed or not
        """
        self.log.info(f"Verifying store sealed for store Id: {store_id}")
        query = f"select sealedReason from IdxSIDBStore where SIDBStoreID = {store_id}"
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT: {res}")
        if int(res) == 0:
            return False
        self.log.info("SIDBStore sealed successfully")
        return True

    def update_max_wormtimestamp(self, store_id):
        """
        Update the max wormtimestamp for the given store.
        Args:
            store_id      (str)   -- SIDB Store id for which mmdeletedaf entries needs to be checked
        """
        query1 = f"""select intVal, longlongVal from MMEntityProp
         where EntityId = {store_id} and propertyName = 'DDBMaxWORMLockTimestamp'"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        result = self.csdb.fetch_one_row()
        int_val, long_val = int(result[0]), int(result[1])
        if int_val == 0:
            self.log.info(f"RESULT: {long_val}")
            start_time = long_val - 86400 * 20
            update_query = f"""update MMEntityProp set longlongVal = {start_time}
             where EntityId = {store_id} and propertyName = 'DDBMaxWORMLockTimestamp'"""
        else:
            self.log.info(f"RESULT: {int_val}")
            start_time = int_val - 86400 * 20
            update_query = f"""update MMEntityProp set intVal = {start_time}
             where EntityId = {store_id} and propertyName = 'DDBMaxWORMLockTimestamp'"""

        self.log.info("4 Day Backed Time is %s", start_time)
        self.log.info("Query: %s", update_query)
        self.opt_selector.update_commserve_db(update_query)
        self.log.info(f"Successfully Updated max worm timestamp for {store_id}")

    def verify_store_pruned(self, store_id):
        """
        Verify that SIDB Store is pruned successfully.
        Args:
            store_id      (str)   -- SIDB Store id for which pruning needs to be checked
        Returns:
              bool  --  Boolean to indicate whether store is pruned or not
        """
        self.log.info(f"Validating SIDBStore for {store_id}")
        query1 = f"""select count(SIDBStoreId) from IdxSIDBStore where SIDBStoreId = {store_id}"""
        self.log.info("Query: %s", query1)
        self.csdb.execute(query1)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY1: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBStore entries are not pruned!!")
            return False

        query2 = f"""select count(IdxAccessPathId) from IdxAccessPath where IdxAccessPathId in 
        (select IdxAccessPathId from IdxSIDBSubStore where SIDBStoreId = {store_id})"""
        self.log.info("Query: %s", query2)
        self.csdb.execute(query2)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY2: {res}")
        if int(res) != 0:
            self.log.info("IdxAccessPath entries are not pruned!")
            return False

        query3 = f"""select count(IdxCacheId) from IdxCache where IdxCacheId in 
        (select IdxCacheId from IdxSIDBSubStore where SIDBStoreId = {store_id})"""
        self.log.info("Query: %s", query3)
        self.csdb.execute(query3)
        res = self.csdb.fetch_one_row()[0]
        self.log.info(f"RESULT QUERY3: {res}")
        if int(res) != 0:
            self.log.info("IdxSIDBSubStore entries are not pruned for all stores!")
            return False
        self.log.info("SIDB Store Pruned Successful!")
        return True

    def seal_clean_store(self, store, jobs_to_be_aged):
        """
        Perform pruning for WORM enabled SIDB Store.
        Args:
            store               (Store) -- store on which WORM jobs are to be aged

            jobs_to_be_aged     (list)  -- list of jobs on WORM store to be aged.
        """
        self.log.info(f"Updating SIDB Store {store.store_id} First job Start Time!")
        self.update_store_creation_time(store.store_id)
        store_sealed = False
        for _ in range(3):
            self.log.info(f"Waiting for Store ID: {store.store_id} to be sealed!!")
            time.sleep(5 * 60)
            if self.verify_store_sealed(store.store_id):
                store_sealed = True
                break
        if not store_sealed:
            raise Exception(f"SIDBStore ID: {store.store_id} was not sealed!!")

        # As per design, last job will be held for Basic Cycle retention
        # Running 1 more Full Job so that as per expectation, job_list will get aged

        self.log.info("Running 1 full backup to age required jobs")
        job_obj = self.subclient.backup("Full")
        if not job_obj.wait_for_completion():
            raise Exception(f'Backup Job: {job_obj.job_id} failed'
                            f' with JPR: {job_obj.delay_reason}')
        self.log.info("Backup Job: %s completed", job_obj.job_id)

        self.log.info("Running Auxcopy to Storage Policy 1: Copy 2")
        auxcopy_job = self.storage_policy.run_aux_copy()
        self.log.info(f"AuxCopy job {auxcopy_job.job_id} Initiated. waiting for the job to complete")
        if not auxcopy_job.wait_for_completion():
            raise Exception(
                f"AuxCopy job {auxcopy_job.job_id} failed with JPR: {auxcopy_job.delay_reason}")
        self.log.info("AuxCopy Job %s completed", auxcopy_job.job_id)

        for job in jobs_to_be_aged:
            self.update_job_start_time(job)

        job_aged = False
        for _ in range(3):
            self.run_data_aging()
            time.sleep(5 * 60)
            if self.verify_job_aged(jobs_to_be_aged, self.copy_2.copy_id):
                job_aged = True
                break
        if not job_aged:
            raise Exception(f"Jobs are not pruned!")

        # deleting a job to send for pruning
        job_id = self.backup_jobs_list[1].job_id
        self.log.info(f"Deleting Job ID: {job_id} on copy {self.copy_1.copy_id}")
        self.copy_1.delete_job(self.backup_jobs_list[0].job_id)
        self.log.info(f"Deleting subclient {self.subclient_name}")
        self.agent.backupsets.get(self.backupset_name).subclients.delete(self.subclient_name)

        entries_pruned = False
        for _ in range(3):
            self.run_data_aging()
            self.log.info(f"Sleeping for 5 mins for prune process interval")
            time.sleep(5 * 60)
            if self.verify_mm_deleted_af(store.store_id):
                entries_pruned = True
                break
        if not entries_pruned:
            raise Exception("MMDeleted entried Volume Flag not invalid!")

        self.update_max_wormtimestamp(store.store_id)

        # Verify SIDBStore pruned.
        flag = True
        for _ in range(3):
            if not self.verify_store_pruned(self.worm_store.store_id):
                self.log.info("Starting Data Aging Job.")
                self.run_data_aging()
                self.log.info(f"Sleeping for 11 min for maintenance process interval")
                time.sleep(11 * 60)
            else:
                self.log.info("SIDBStore Prune Validation Complete!")
                flag = False
        if flag:
            raise Exception("SIDBStore Prune Validation Failed.")

    def age_and_prune_data(self):
        """Marks the jobs as aged and prunes the data"""
        self.log.info("Update startTime of the jobs and validate if jobs are pruned.")
        for index in range(3):
            job_id = self.backup_jobs_list[index].job_id
            self.log.info(f"Updating Start Time for Job {job_id}")
            self.update_job_start_time(job_id)

        self.log.info("Verify Jobs marked are aged and Volume Flags are set in MMDeletedAF.")
        job_aged = False
        backups_list = [job.job_id for job in self.backup_jobs_list]
        for _ in range(3):
            # Running Data Aging Job.
            self.run_data_aging()
            if self.verify_job_aged(backups_list[:3], self.copy_2.copy_id):
                job_aged = True
                break
        if not job_aged:
            raise Exception(f"Jobs are not marked aged on WORM Copy")

        # deleting a job to send for pruningJobs are not pruned!
        job_id = self.backup_jobs_list[0].job_id
        self.log.info(f"Deleting Job ID: {job_id} on copy {self.copy_1.copy_id}")
        self.copy_1.delete_job(self.backup_jobs_list[0].job_id)

        entries_pruned = False
        for _ in range(3):
            self.run_data_aging()
            self.log.info(f"Sleeping for 5 mins for prune process interval")
            time.sleep(5 * 60)
            if self.verify_mm_deleted_af(self.worm_store.store_id):
                entries_pruned = True
                break
        if not entries_pruned:
            self.log.error("MMDeletedAF entries not pruned")
        self.seal_clean_store(self.worm_store, backups_list)

    def run(self):
        """Main function for test case execution"""
        try:
            self.cleanup()
            self.initial_setup()
            self.pre_upgrade_steps()
            self.upgrade_steps()
            self.post_upgrade_validations()
            self.age_and_prune_data()
        except Exception as exp:
            self.log.error('TC Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
