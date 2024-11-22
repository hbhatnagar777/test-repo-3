# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This test case is to validate that we are not sending any pruning request to the DSIP MA for non-dedupe
enabled storage pool.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    run()                           --  run function of this test case

    tear_down()                     --  teardown function of this test case

    _cleanup()                      --  cleanup the entities created

    _get_mount_path_id_and_name()   --  get mountpath id and name

    _get_aged_volumes()             --  get aged volumes for respective job

    _validate_dsip_share()          --  validates whether DSIP mediagent is shared with mountpath as expected

    _validate_pruning_request()     --  validate whether pruning request is sent to regular MA and not to DSIP MA

    _validate_aged_volume_prune()   --  validate whether expected aged volumes are pruned by the regular MA

Design Steps :
    1. Run 3 traditional full backups to copy with retention on 0D,1C. Use new media for each job.
    2. J1 and J2 should qualify for the pruning.
    3. Run the Granular Data Aging operation.
    4. Based on the pruning interval the data will be pruned by regular MA.

Sample Input:
"58023": {
    "ClientName": "client1",
    "AgentName": "File System",
    "MediaAgentName": "mediaagent1",
    "DataServerIPMediaAgentName": "mediaagent2",
}

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
import time


class TestCase(CVTestCase):

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Data Server IP and Non-dedupe Pruning"
        self.tcinputs = {
            "MediaAgentName": None,
            "DataServerIPMediaAgentName": None,
        }
        self.storage_policy_name = None
        self.backup_set_name = None
        self.client_machine = None
        self.regular_ma_machine = None
        self.mount_path = None
        self.content_path = None
        self.mm_helper = None
        self.storage_pool = None
        self.sub_client_name = None
        self.options_selector = None
        self.lib_name = None
        self.data_server_ip_client_ma = None
        self.regular_ma = None
        self.dedupe_helper = None
        self.common_util = None

    def _get_mount_path_id_and_name(self, library_id):
        """
        Get mountpath id and name of the given library
        Args:
            library_id (int)  --  Library Id
        """
        query = f"""
                    SELECT	MM.MountPathId,  MM.MountPathName
                    FROM    MMMountPath MM WITH(NOLOCK)
                    WHERE	MM.LibraryId = {library_id}"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur != ['']:
            return [int(cur[0]), cur[1]]
        self.log.error("No mountpath entries present")
        raise Exception("Invalid LibraryId")

    def _get_aged_volumes(self, aged_job_list):
        """
        Returns aged_volumes for respective jobs
        Args:
            aged_job_list(list)   -- First two jobids, these are eligible for pruning
        Returns:
            (list)          -- Returns aged_volumes for respective job
        """
        aged_volumes = []
        query = f"""
                    SELECT  DISTINCT MV.VolumeName
                    FROM    archChunkMapping ACM WITH (NOLOCK), archChunk AC WITH (NOLOCK), MMVolume MV WITH (NOLOCK)
                    WHERE   AC.id=ACM.archChunkId 
                            AND AC.commCellId=ACM.chunkCommCellId
                            AND MV.VolumeId = AC.volumeId
                            AND ACM.jobId in ({aged_job_list[0]},{aged_job_list[1]})"""
        self.log.info(f"Query: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        for volume in cur:
            aged_volumes.append(volume[0])
        self.log.info(f'Volumes list: {aged_volumes}')
        return aged_volumes

    def _validate_pruning_request(self, mount_path_id):
        """
        Validate whether pruning request is sent to regular MA and not to DSIP MA
        Args:
            mount_path_id(int)  -- Mountpath id

        """
        self.log.info("Validating if pruning request is sent to regular MA and not to DSIP MA")
        dsip_ma_id = self.commcell.clients.get(self.data_server_ip_client_ma).client_id
        mm_prune_regex_dsip_ma = (r"Submitting Magnetic Pruning for .* Volumes in Mount Path \[%s\] on Host \[%s\]"
                                  % (mount_path_id, dsip_ma_id))

        parse_result = self.dedupe_helper.parse_log(self.commcell.commserv_name, 'MediaManagerPrune.log',
                                                    mm_prune_regex_dsip_ma, escape_regex=False,
                                                    single_file=True, only_first_match=True)[0]
        if parse_result:
            self.log.error("Pruning request is sent to DSIP MA which is not expected")
            raise Exception("Pruning request is sent to DSIP MA which is not expected")

        # check for regular ma
        regular_ma_id = self.commcell.clients.get(self.regular_ma).client_id
        mm_prune_regex_regular_ma = (r"Submitting Magnetic Pruning for .* Volumes in Mount Path \[%s\] on Host \[%s\]"
                                     % (mount_path_id, regular_ma_id))
        parse_result = self.dedupe_helper.parse_log(self.commcell.commserv_name, 'MediaManagerPrune.log',
                                                    mm_prune_regex_regular_ma, escape_regex=False,
                                                    single_file=True, only_first_match=True)[0]
        if parse_result:
            self.log.info('Pruning request is sent to regular MA as expected')
            return True
        self.log.warning("Pruning request submission is still pending")
        return False

    def _validate_aged_volume_prune(self, aged_volumes, mount_path_name):
        """
        Validate whether expected aged volumes are pruned by the regular MA
        Args:
            aged_volumes(list)      -- list of volume names which are eligible for pruning

            mount_path_name(str)    -- mountpath name
        """
        self.log.info("Validating if expected aged volumes are pruned by the regular MA")
        for volume in aged_volumes:
            volume_path = self.regular_ma_machine.join_path(self.mount_path, mount_path_name, 'CV_MAGNETIC', volume)
            volume_prune_regex = "Deleted directory %s" % volume_path
            parse_result = self.dedupe_helper.parse_log(self.regular_ma, 'CVMA.log', volume_prune_regex,
                                                        single_file=True, only_first_match=True)[0]
            if not parse_result:
                self.log.error("Expected aged volume [%s] is not pruned by the regular MA", volume)
                raise Exception("Expected aged volume [{0}] is not pruned by the regular MA".format(volume))
            self.log.info("Expected aged volume [%s] is pruned by the regular MA", volume)

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # deleting content path if exists
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            # Delete backup_set
            self.log.info("Deleting BackupSet: %s if exists", self.backup_set_name)
            if self.agent.backupsets.has_backupset(self.backup_set_name):
                self.agent.backupsets.delete(self.backup_set_name)
                self.log.info("Deleted BackupSet: %s", self.backup_set_name)

            # Delete Storage Policy
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

            # Deleting Storage pool
            self.log.info("Deleting Storage Pool: %s if exists", self.storage_pool)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool):
                self.commcell.storage_pools.delete(self.storage_pool)
                self.log.info("Deleted Storage Pool: %s", self.storage_pool)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        self.options_selector = OptionsSelector(self.commcell)
        self.common_util = CommonUtils(self)
        self.data_server_ip_client_ma = self.tcinputs['DataServerIPMediaAgentName']
        self.regular_ma = self.tcinputs['MediaAgentName']
        self.storage_pool = '%s-pool-ma(%s-%s)-client(%s)' % (str(self.id), self.data_server_ip_client_ma, 
                                                              self.regular_ma, self.tcinputs['ClientName'])
        self.storage_policy_name = '%s-policy-ma(%s-%s)-client(%s)' % (str(self.id), self.data_server_ip_client_ma, 
                                                                       self.regular_ma, self.tcinputs['ClientName'])
        self.backup_set_name = '%s-bs-ma(%s-%s)-client(%s)' % (str(self.id), self.data_server_ip_client_ma, 
                                                               self.regular_ma, self.tcinputs['ClientName'])
        self.sub_client_name = "%s_sc" % str(self.id)
        
        self.client_machine = self.options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.regular_ma_machine = self.options_selector.get_machine_object(self.regular_ma)
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = self.options_selector.get_drive(self.client_machine, size=30 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')

        # To select drive with space available in regular mediaagent machine
        self.log.info('Selecting drive in the regular mediaagent machine based on space available')
        ma_drive = self.options_selector.get_drive(self.regular_ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mount_path = self.regular_ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # storage pool creation
            pool_obj, lib_obj = self.mm_helper.configure_storage_pool(self.storage_pool, self.mount_path,
                                                                      self.regular_ma)
            # sharing mount_path
            lib_obj.media_agent = self.regular_ma
            lib_obj.mount_path = self.mount_path
            self.log.info("Sharing mediaagent [%s] as dataserver IP controller", self.data_server_ip_client_ma)
            lib_obj.share_mount_path(self.data_server_ip_client_ma, new_mount_path="", access_type=22)

            # storage policy creation
            storage_policy_obj = self.mm_helper.configure_storage_policy(self.storage_policy_name,
                                                                         storage_pool_name=self.storage_pool)
            # setting retention
            copy_obj = storage_policy_obj.get_primary_copy()
            copy_obj.copy_retention = (0, 1, -1)
            self.log.info('Retention set to 0 day 1 cycle')

            # Create backupset
            self.mm_helper.configure_backupset(self.backup_set_name, self.agent)
            # Create subclient
            sc_obj = self.mm_helper.configure_subclient(self.backup_set_name, self.sub_client_name,
                                                        self.storage_policy_name, self.content_path, self.agent)

            # Generate data
            self.options_selector.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10)

            aged_job_list = []
            # Run Backup
            for _ in range(1, 4):
                job_obj = self.common_util.subclient_backup(sc_obj, "full", advanced_options={"start_new_media": True})
                # storing job ids to find correct volumes are pruning or not, last job doesn't
                # age(retention:0 days 1cycle), so not storing last job_id
                if _ != 3:
                    aged_job_list.append(job_obj.job_id)

            # finding aged volumes for the excepted aged jobs
            aged_volumes = self._get_aged_volumes(aged_job_list)
            mount_path_id, mount_path_name = self._get_mount_path_id_and_name(lib_obj.library_id)

            # update prune process interval
            self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', nmin=5, value=10)

            # data aging
            data_aging_job = self.mm_helper.submit_data_aging_job(storage_policy_name=self.storage_policy_name)
            self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

            # wait for 30 min to complete pruning
            self.log.info("Waiting for 2 minutes to allow pruning request submission")
            time.sleep(120)
            pruning_result = self._validate_pruning_request(mount_path_id)
            time_limit = time.time() + (30 * 60)
            while not pruning_result:
                self.log.info("Waiting further 5 minutes to allow pruning request submission")
                time.sleep(300)
                pruning_result = self._validate_pruning_request(mount_path_id)
                if time.time() >= time_limit:
                    raise Exception("Pruning request submission still pending, waited 30 minutes. exiting...")

            # verifying physical deletes by regular MA
            self._validate_aged_volume_prune(aged_volumes, mount_path_name)

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', nmin=10, value=60)
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")

            # deleting content path if exists
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
