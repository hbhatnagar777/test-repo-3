# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This test case is for verifying  write operation using Data Server IP MA via a dedupe-enabled storage pool. Also, check
data consistency with DDB Verification (DV2) job.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    run()                               --  run function of this test case

    tear_down()                         --  teardown function of this test case

    _cleanup()                          --  cleanup the entities created

    _validate_dsip_share()              --  validates whether DSIP mediagent is shared with mountpath as expected

    _validate_dsip_ma_writes_by_db()    --  validates whether the job is written by DSIP MA or not using DB

    _validate_dsip_ma_writes_by_logs()  --  validates whether the job is written by DSIP MA or not using logs

Design Steps :
    1.Create dedupe-enabled storage pool
    2.Share the store with MA using DSIP R/W access
    3.Create a dependent SP-copy
    4.Associate to a sub-client
    5.Generate content of 3G size, Run full1 backup
    6.Add 500 MB more data before running an Inc1, Inc2, Inc3
    7.Do not modify data and run Full2, so that we ref to the existing sign in DDB.
    8.Add 500 MB more data before running an Inc4
    9.Run Full3
    10.Run DDB verification

Sample Input:
"64052": {
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


class TestCase(CVTestCase):

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Test dedupe backups using Data server IP MA"
        self.tcinputs = {
            "MediaAgentName": None,
            "DataServerIPMediaAgentName": None
        }
        self.storage_policy_name = None
        self.backup_set_name = None
        self.client_machine = None
        self.ma_machine = None
        self.mount_path = None
        self.ddb_path = None
        self.content_path = None
        self.mm_helper = None
        self.storage_pool = None
        self.sub_client_name = None
        self.options_selector = None
        self.data_server_ip_client_ma = None
        self.dedupe_helper = None
        self.regular_ma = None
        self.common_util = None

    def _validate_dsip_share(self, lib_id, ma_name):
        """"
        Validates whether DSIP mediagent is shared with mountpath as expected
            Args:
                lib_id(int) : Library id of mountpath

                ma_name(str) -- name of the media agent to validate on
        """
        self.log.info('validating if DSIP mediagent [%s] shared as expected...', ma_name)
        query = f""" 
                    SELECT  COUNT(1)
                    FROM    MMDeviceController MDC WITH (NOLOCK),
                            MMMountPathToStorageDevice MPSD WITH (NOLOCK),
                            MMMountPath MP WITH (NOLOCK),
                            APP_Client AC WITH (NOLOCK)
                    WHERE   MDC.DeviceId = MPSD.DeviceId
                            AND MPSD.MountPathId = MP.MountPathId
                            AND MP.LibraryId = {lib_id}
                            AND MDC.ClientId = AC.id
                            AND MDC.DeviceAccessType = 22
                            AND AC.name = '{ma_name}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        res = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", res)
        if not int(res[0]) == 1:
            self.log.error('DSIP mediaagent [%s] is not shared as expected', ma_name)
            raise Exception('DSIP mediaagent [{0}] is not shared as expected'.format(ma_name))
        self.log.info('DSIP mediaagent [%s] is shared as expected', ma_name)

    def _validate_dsip_ma_writes_by_db(self, job_id):
        """
            Validates from CSDB whether DSIP mediaagent is used for write operation during backup

            Args:
                job_id(int)   -- Job ID to be validated
        """
        self.log.info('Verifying from CSDB if DSIP mediaagent is used for write operation during backup')
        query = f"""
                    SELECT  COUNT(1)
                    FROM    JMJobResourceHistory JMRH WITH (NOLOCK), APP_Client AC WITH (NOLOCK)
                    WHERE   AC.id=JMRH.ClientId
                            AND JMRH.jobId={job_id}
                            AND AC.name = '{self.data_server_ip_client_ma}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if not int(cur[0]) > 0:
            self.log.error('DSIP mediaagent is not used for write operation during backup')
            raise Exception('DSIP mediaagent is not used for write operation during backup')
        self.log.info('DSIP mediaagent is used for write operation during backup')

    def _validate_dsip_ma_writes_by_logs(self, job_id):
        """
        Validates whether the job is written by DSIP MA or not

        Args:
            job_id(int)   -- Job ID to be validated
        """
        self.log.info('Verifying from MM log if DSIP mediaagent is used for write operation during backup')
        mount_req_regex = "MOUNT REQUEST from [%s]" % self.data_server_ip_client_ma
        parse_result = self.dedupe_helper.parse_log(self.commcell.commserv_name, 'MediaManager.log', mount_req_regex,
                                                    jobid=job_id, single_file=True, only_first_match=True)[0]
        if parse_result:
            self.log.info('Verifying from cvd log if DSIP mediaagent is used for write operation during backup')
            vol_mounted_regex = 'Successfully mounted Active volume'
            parse_result1 = self.dedupe_helper.parse_log(self.data_server_ip_client_ma, 'cvd.log', vol_mounted_regex,
                                                         jobid=job_id, single_file=True, only_first_match=True)[0]
            if parse_result1:
                self.log.info('DSIP mediaagent is used for write operation during backup')
            else:
                self.log.error('DSIP mediaagent is not used for write operation during backup')
                raise Exception('DSIP mediaagent is not used for write operation during backup')
        else:
            self.log.error('DSIP mediaagent is not used for write operation during backup')
            raise Exception('DSIP mediaagent is not used for write operation during backup')

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
        self.ma_machine = self.options_selector.get_machine_object(self.tcinputs['MediaAgentName'])
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = self.options_selector.get_drive(self.client_machine, size=30 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = self.options_selector.get_drive(self.ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mount_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

        # DDB partition path
        if self.tcinputs.get("PartitionPath") is not None:
            self.ddb_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            else:
                self.ddb_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # storage pool creation
            pool_obj, lib_obj = self.mm_helper.configure_storage_pool(self.storage_pool, self.mount_path,
                                                                      self.regular_ma, self.regular_ma, self.ddb_path)

            # sharing mount_path
            lib_obj.media_agent = self.regular_ma
            lib_obj.mount_path = self.mount_path
            self.log.info("Sharing mediaagent [%s] as dataserver IP controller", self.data_server_ip_client_ma)
            lib_obj.share_mount_path(self.data_server_ip_client_ma, new_mount_path="", access_type=22)
            # Validating mountpath share
            self._validate_dsip_share(lib_obj.library_id, self.data_server_ip_client_ma)

            # storage policy creation
            self.mm_helper.configure_storage_policy(self.storage_policy_name,
                                                    storage_pool_name=self.storage_pool)
            # Create backupset
            self.mm_helper.configure_backupset(self.backup_set_name, self.agent)
            # Create subclient
            sub_client_obj = self.mm_helper.configure_subclient(self.backup_set_name, self.sub_client_name,
                                                                self.storage_policy_name, self.content_path, self.agent)

            # Generate data
            self.options_selector.create_uncompressable_data(self.client_machine, self.content_path, 0.5, 6)
            job_type_list = ['full', 'incremental', 'incremental', 'incremental', 'full', 'incremental', 'full']

            # Run Backup
            for type_of_backup in job_type_list:
                if type_of_backup == 'incremental':
                    self.options_selector.create_uncompressable_data(self.client_machine, self.content_path, 0.5)
                job_obj = self.common_util.subclient_backup(sub_client_obj, type_of_backup,
                                                            advanced_options={
                                                                "media_agent_name": self.data_server_ip_client_ma
                                                            })
                self._validate_dsip_ma_writes_by_db(job_obj.job_id)
                self._validate_dsip_ma_writes_by_logs(job_obj.job_id)

            # Run ddb verification
            copy_name = pool_obj.copy_name
            dedupe_engine_obj = self.commcell.deduplication_engines.get(self.storage_pool, copy_name)
            store_obj = dedupe_engine_obj.get(dedupe_engine_obj.all_stores[0][0])
            self.dedupe_helper.run_dv2_job(store_obj, dv2_type='full', option='complete')

            # validating ddb verification
            if self.mm_helper.get_bad_chunks(store_obj.store_id):
                raise Exception("Found corrupted chunks during DDB verification")

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")

            # deleting content path if exists
            self.log.info("Deleting content path: %s if exists", self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)