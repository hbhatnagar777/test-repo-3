# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    _validate_storage_default_settings(storage_pool_name, ma_name)
                    --  checks whether defaults are met for the given media agent and storage pool

    _validate_max_concurrent_writers_on_device_controller_level(storage_pool_name, ma_name)
                    --  checks whether max concurrent writers are set on device controller level

    _get_library_name(storage_pool_name)
                    --  returns the library_name for the given storage pool

    _get_device_controller_ids(ma_name, library_name)
                    --  returns mountpath_id, device_id, device_controller_id, media_agent_id, for the given
                        media agent and library

    _validate_for_read_write_access(storage_pool_name, ma_name)
                    --  validates the read and write is set for the given media agent and storage pool

    _get_cred_user_name(cred_name)
                    --  returns user name for given saved credential name

    _restore_and_validate(restore_path, subclient, media_agent)
                    --  restores the subclient and validates the restore

    _cleanup()      --  checks if entities exists and cleans them

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case




Design steps:

    This testcase is specific to windows machine only, since, network path is used

    Configure Disk and validate defaults, Add MP, Share MP, delete controller

	1. Create disk Pool and validate flags.

		- Create disk pool with Local path on MA1
		        - Validate from DB:
			            - Max concurrent writers are set on device controller, Mountpath and storage all three levels
                        - Spill and Fill is enabled by defaults
                        - Micro pruning is ON
                        - Support of drill hole is ON if supported
                        - Reserve space is used instead of do not consume more than ## GB

        - Validate the MA with a backup job that it can write.

		- Change the device access type from R/W to Read on MA1, and run a new backup and
		  validate backup return a good JPR.

		- Update back to r/w from read.


	2. Validate for UNC possitive and negative case

		- Add a new MA2 on MP1 with UNC path

		- check MA has read/write access with max writers

		- Run backup via MA2 and ensure it completes

		- Modify the credential used to a read only cred and run new backup again and it should fail with good JPR.


    3. Restore using two MA if needed two jobs. ensure restore complete from MA2 and MA1 both.




Sample Input :

"64508": {
		    "ClientName": "sh_vm1",
		    "AgentName": "File System",
		    "MediaAgent1": "sh_vm2",
		    "MediaAgent2": "sh_vm4",
		    "SavedReadOnlyCred": "team_mm",
		    "SavedFullControlCred": "admin",
		    "isDrillHoleSupported": true
    }

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import (CVEntities, OptionsSelector)
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)
from AutomationUtils.idautils import (CommonUtils)
from Server.JobManager.jobmanager_helper import JobManager
import time


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case file"""

        super(TestCase, self).__init__()
        self.cventities = None
        self.name = "Acceptance for Disk storage pool"
        self.storage_policy = None
        self.storage_policy_name = None
        self.storage_pool_name = None
        self.mount_path = None
        self.media_agent1 = None
        self.media_agent2 = None
        self.client_machine = None
        self.dedup_path = None
        self.content_path = None
        self.restore_path1 = None
        self.restore_path2 = None
        self.ma_drive = None
        self.client_drive = None
        self.max_concurrent_writers_set_on_storage_level = None
        self.max_concurrent_writers_set_on_mount_path_level = None
        self.max_concurrent_writers_set_on_device_controller_level = None
        self.spill_and_fill_is_enabled = None
        self.micro_pruning_is_disabled = None
        self.drill_hole_is_enabled = None
        self.reserve_space_is_used = None
        self.read_write_access_is_enabled = None
        self.library_name = None
        self.backupset_name = None
        self.mmhelper = None
        self.commonutils = None
        self.disk_library = None
        self.job_manager = None
        self.share_name = None
        self.read_access = None
        self.read_write_access = None
        self.errors = None
        self.tcinputs = {
            'MediaAgent1': None,
            'MediaAgent2': None,
            'isDrillHoleSupported': None,
            'SavedReadOnlyCred': None,
            'SavedFullControlCred': None
        }

    def _validate_storage_default_settings(self, storage_pool_name, ma_name):
        """
            checks whether defaults are met for given media agent and storage pool
            Args:
                storage_pool_name (str) -- name of the storage pool to validate on
                ma_name (str) -- name of the media agent to validate on
            Return:
                Exception - If defaults are not excpected
        """

        query = f''' SELECT mmp.maxswitchforhost,
                    mp.maxconcurrentwriters,
                    drp.maxdrivestoswitch,
                    l.extendedattributes,
                    mp.attribute,
                    mp.maxdatatowritemb
                FROM   archgroup ag WITH (nolock),
                    archgroupcopy agc WITH (nolock),
                    mmdatapath dp WITH (nolock),
                    mmdrivepool drp WITH (nolock),
                    app_client ac WITH (nolock),
                    mmmasterpool mmp WITH (nolock),
                    mmlibrary l WITH (nolock),
                    mmmountpath mp WITH (nolock)
                WHERE  ag.NAME = '{storage_pool_name}'
                    AND ag.id = agc.archgroupid
                    AND agc.id = dp.copyid
                    AND dp.drivepoolid = drp.drivepoolid
                    AND drp.clientid = ac.id
                    AND ac.NAME = '{ma_name}'
                    AND drp.masterpoolid = mmp.masterpoolid
                    AND mmp.libraryid = l.libraryid
                    AND l.libraryid = mp.libraryid   '''

        self.log.info(query)
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()

        self.max_concurrent_writers_set_on_storage_level = int(table[0]) == -1
        self.max_concurrent_writers_set_on_mount_path_level = int(table[1]) == 1000
        self.max_concurrent_writers_set_on_device_controller_level = int(table[2]) == -1
        self.spill_and_fill_is_enabled = int(table[3]) & 1 == 1
        self.micro_pruning_is_disabled = int(table[4]) & 32768 == 32768
        self.drill_hole_is_enabled = int(table[4]) & 128 == 128
        self.reserve_space_is_used = int(table[5]) == -1

        if self.max_concurrent_writers_set_on_storage_level:
            self.log.info(
                f"Max concurrent writers set on storage level : {self.max_concurrent_writers_set_on_storage_level}")
        else:
            self.log.warning(f"Max concurrent writers set on storage level : "
                             f"{self.max_concurrent_writers_set_on_storage_level}")
            self.errors.append(f"Max concurrent writers set on storage level : "
                               f"{self.max_concurrent_writers_set_on_storage_level}")

        if self.max_concurrent_writers_set_on_mount_path_level:
            self.log.info(
                f"Max concurrent writers set on mount path level : "
                f"{self.max_concurrent_writers_set_on_mount_path_level}")
        else:
            self.log.warning(f"Max concurrent writers set on mount path level : "
                             f"{self.max_concurrent_writers_set_on_mount_path_level}")
            self.errors.append(f"Max concurrent writers set on mount path level : "
                               f"{self.max_concurrent_writers_set_on_mount_path_level}")

        if self.max_concurrent_writers_set_on_device_controller_level:
            self.log.info(
                f"Max concurrent writers set on device controller level : "
                f"{self.max_concurrent_writers_set_on_device_controller_level}")
        else:
            self.log.warning(f"Max concurrent writers set on device controller level : "
                             f"{self.max_concurrent_writers_set_on_device_controller_level}")
            self.errors.append(f"Max concurrent writers set on device controller level : "
                               f"{self.max_concurrent_writers_set_on_device_controller_level}")

        if self.spill_and_fill_is_enabled:
            self.log.info(f"Spill and Fill is enabled : {self.spill_and_fill_is_enabled}")
        else:
            self.log.warning(f"Spill and Fill is enabled : {self.spill_and_fill_is_enabled}")
            self.errors.append(f"Spill and Fill is enabled : {self.spill_and_fill_is_enabled}")

        if not self.micro_pruning_is_disabled:
            self.log.info(f"Micro pruning disabled : {self.micro_pruning_is_disabled}")
        else:
            self.log.warning(f"Micro pruning disabled : {self.micro_pruning_is_disabled}")
            self.errors.append(f"Micro pruning disabled : {self.micro_pruning_is_disabled}")

        if self.drill_hole_is_enabled == self.tcinputs['isDrillHoleSupported']:
            self.log.info(f"Drill hole is set as expected")
        else:
            self.log.warning(f"Drill hole is not set as expected")
            self.errors.append(f"Drill hole is not set as expected")

        if self.reserve_space_is_used:
            self.log.info(f"Reserve space is used : {self.reserve_space_is_used}")
        else:
            self.log.warning(f"Reserve space is used : {self.reserve_space_is_used}")
            self.errors.append(f"Reserve space is used : {self.reserve_space_is_used}")

        if not (
                self.max_concurrent_writers_set_on_storage_level and self.max_concurrent_writers_set_on_mount_path_level
                and self.max_concurrent_writers_set_on_device_controller_level and self.spill_and_fill_is_enabled and
                not self.micro_pruning_is_disabled and (
                        self.drill_hole_is_enabled == self.tcinputs[
                    'isDrillHoleSupported']) and self.reserve_space_is_used):
            self.log.warning('Storage default settings are not as expected')
            self.errors.append('Storage default settings are not as expected')
        else:
            self.log.info("Storage default settings are as expected")

    def _validate_max_concurrent_writers_on_device_controller_level(self, storage_pool_name, ma_name):
        """
            checks whether max concurrent writers are set on device controller level
            Args:
                storage_pool_name (str) -- name of the storage pool to validate on
                ma_name (str) -- name of the media agent to validate on
            Return:
                (Bool) True, if max concurrent writers on device controller level are set.
                (Bool) False, if max concurrent writers on device controller level are not set.
        """

        query = f''' SELECT drp.maxdrivestoswitch
                    FROM   archgroup ag WITH (nolock),
                        archgroupcopy agc WITH (nolock),
                        mmdatapath dp WITH (nolock),
                        mmdrivepool drp WITH (nolock),
                        app_client ac WITH (nolock)
                    WHERE  ag.NAME = '{storage_pool_name}'
                        AND ag.id = agc.archgroupid
                        AND agc.id = dp.copyid
                        AND dp.drivepoolid = drp.drivepoolid
                        AND drp.clientid = ac.id
                        AND ac.NAME = '{ma_name}' '''
        self.log.info(f"QUERY : {query}")
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()
        return int(table[0]) == -1

    def _get_library_name(self, storage_pool_name):
        """
            returns the library_name for the given storage pool
            Args:
                storage_pool_name (str) -- name of the storage pool to which library belongs to
            Return:
                (str) - Name of the library
        """

        query = f''' SELECT DISTINCT l.aliasname
                    FROM   archgroup ag WITH (nolock),
                        archgroupcopy agc WITH (nolock),
                        mmdatapath dp WITH (nolock),
                        mmdrivepool drp WITH (nolock),
                        mmmasterpool mmp WITH (nolock),
                        mmlibrary l WITH (nolock)
                    WHERE  ag.NAME = '{storage_pool_name}'
                        AND agc.archgroupid = ag.id
                        AND agc.id = dp.copyid
                        AND dp.drivepoolid = drp.drivepoolid
                        AND drp.masterpoolid = mmp.masterpoolid
                        AND mmp.libraryid = l.libraryid   '''
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()
        return table[0]

    def _get_device_controller_ids(self, ma_name, library_name):
        """
            returns mountpath_id, device_id, device_controller_id, media_agent_id, for given media agent and library
            Args:
                ma_name (str) -- name of the media agent which controlls library
                library_name (str)
                              -- name of the library
            Return:
                (int, int, int, int)
                              -- mountpath_id, device_id, device_controller_id, media_agent_id
        """

        query = f''' SELECT mp.mountpathid,
                    mpsd.deviceid,
                    dc.devicecontrollerid,
                    ac.id
                FROM   mmlibrary l WITH (nolock),
                    mmmountpath mp WITH (nolock),
                    mmmountpathtostoragedevice mpsd WITH (nolock),
                    mmdevicecontroller dc WITH (nolock),
                    app_client ac WITH (nolock)
                WHERE  l.libraryid = mp.libraryid
                    AND mp.mountpathid = mpsd.mountpathid
                    AND mpsd.deviceid = dc.deviceid
                    AND dc.clientid = ac.id
                    AND ac.NAME = '{ma_name}'
                    AND l.aliasname = '{library_name}'  '''
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()
        return int(table[0]), int(table[1]), int(table[2]), int(table[3])

    def _validate_for_read_write_access(self, storage_pool_name, ma_name):
        """"
            validates the read and write is set for given media agent and storage pool
            Args:
                storage_pool_name (str) -- name of the storage pool to validate on
                ma_name (str) -- name of the media agent to validate on
            Return:
                (Bool) True, if read write access is used
                (Bool) False, if read write access is not used
        """

        query = f''' SELECT dc.deviceaccesstype
                FROM   mmdevicecontroller dc WITH (nolock),
                    app_client ac WITH (nolock),
                    mmmountpathtostoragedevice mpsd WITH (nolock),
                    mmmountpath mp WITH (nolock),
                    mmdrivepool drp WITH (nolock),
                    mmdatapath dp WITH (nolock),
                    archgroupcopy agc WITH (nolock),
                    archgroup ag WITH (nolock)
                WHERE  dc.clientid = ac.id
                    AND ac.NAME = '{ma_name}'
                    AND dc.deviceid = mpsd.deviceid
                    AND mpsd.mountpathid = mp.mountpathid
                    AND mp.masterpoolid = drp.masterpoolid
                    AND ac.id = drp.clientid
                    AND drp.drivepoolid = dp.drivepoolid
                    AND dp.copyid = agc.id
                    AND agc.archgroupid = ag.id
                    AND ag.NAME = '{storage_pool_name}'  '''

        self.log.info(f"QUERY : {query}")
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()
        return int(table[0]) & 6 == 6

    def _get_cred_user_name(self, credname):
        """
            returns username for the given saved credential name
            Args:
                credname (str) -- name of saved credential
            Return:
                (str) - Username
        """

        query = f''' SELECT username
                    FROM   app_credentials WITH (nolock)
                    WHERE  credentialname = '{credname}' '''
        self.csdb.execute(query)
        table = self.csdb.fetch_one_row()
        return table[0]

    def _restore_and_validate(self, restore_path, subclient, media_agent):
        """
            restores the subclient and validates the restore
            Args:
                restore_path (str) -- path to which restore need to happen
                subclient (obj) -- subclient object which needed to be restored
                media_agent (str) -- expected media agent to used for restore
            Return:
                None
        """
        job = self.commonutils.subclient_restore_out_of_place(restore_path, [self.content_path],
                                                              self.tcinputs['ClientName'], subclient)
        job_details = job._get_job_details()
        ma = job_details['jobDetail']['generalInfo']['mediaAgent']['mediaAgentName']
        if (media_agent == ma):
            self.log.info(f"Restore successfully completed using {ma}...")
        else:
            self.log.error("Restore job is not using expected media agent...")
            raise Exception("Restore job is not using expected media agent...")
        self.log.info("Comparing source content and restore destination content data.")
        if self.client_machine.compare_folders(self.client_machine, self.content_path,
                                               self.client_machine.join_path(restore_path, 'TestData')):
            self.log.error("Restored data is different from content data")
            raise Exception("Restored data is different from content data")
        self.log.info("Restored data is same as content data")

    def _cleanup(self):
        """Checks if entities exists and cleans them"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Deleting backup set
            self.log.info("Deleting backup set : %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f"Deleted backup set: {self.backupset_name}")

            # Deleting Storage policy
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info(f"Deleted Storage Policy: {self.storage_policy_name}")

            # Deleting Storage pool
            self.log.info("Deleting Storage pool : %s if exists", self.storage_pool_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info(f"Deleted storage pool : {self.storage_pool_name}")

        except Exception as exp:
            self.log.error(f"Error during clean up : {str(exp)}")
            raise Exception(f"Error during clean up : {str(exp)}")

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.cventities = CVEntities(self.commcell)
        self.dedupe_helper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.commonutils = CommonUtils(self)
        self.job_manager = JobManager(commcell=self.commcell)
        self.share_name = f"{self.tcinputs['MediaAgent1']}_{self.id}"
        self.read_access = 4
        self.read_write_access = 6
        self.errors = []
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.media_agent1 = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.media_agent2 = options_selector.get_machine_object(self.tcinputs['MediaAgent2'])
        self.storage_pool_name = f"{self.tcinputs['ClientName']}_{self.tcinputs['MediaAgent1']}_{self.id}_disk_pool"
        self.storage_policy_name = \
            f"{self.tcinputs['ClientName']}_{self.tcinputs['MediaAgent1']}_{self.id}_storage_policy"
        self.backupset_name = f"{self.id}_backupset"
        self.ma_drive = options_selector.get_drive(self.media_agent1,
                                                   size=20 * 1024)
        if self.ma_drive is None:
            raise Exception("No free space to host mountpath and ddb")
        self.log.info(f"Selected Media Agent drive : {self.ma_drive}")
        self.client_drive = options_selector.get_drive(self.client_machine,
                                                       size=20 * 1024)
        if self.client_drive is None:
            raise Exception("No free space to host content on client machine")
        self.log.info(f"Selected client drive : {self.client_drive}")
        self.mount_path = self.media_agent1.join_path(self.ma_drive, 'Automation', str(self.id), f'MP1')
        self.dedup_path = self.media_agent1.join_path(self.ma_drive, 'Automation', str(self.id), f'DDB')

        self.content_path = self.client_machine.join_path(self.client_drive, 'Automation', str(self.id), 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        self.restore_path1 = self.client_machine.join_path(self.client_drive, 'Automation', str(self.id),
                                                           'Restoredata1')
        if self.client_machine.check_directory_exists(self.restore_path1):
            self.client_machine.remove_directory(self.restore_path1)
        self.client_machine.create_directory(self.restore_path1)

        self.restore_path2 = self.client_machine.join_path(self.client_drive, 'Automation', str(self.id),
                                                           'Restoredata2')
        if self.client_machine.check_directory_exists(self.restore_path2):
            self.client_machine.remove_directory(self.restore_path2)
        self.client_machine.create_directory(self.restore_path2)

        if self.share_name in self.media_agent1.list_shares_on_network_path(
                f'\\\\{self.media_agent1.get_hostname()}', username='', password=''):
            self.media_agent1.unshare_directory(self.share_name)

        self._cleanup()

    def run(self):
        """Run function of this test case"""
        try:

            # Creating disk storage pool on local path on MA1
            self.storage_pool = self.cventities.create_storage_pool(storage_pool_name=self.storage_pool_name,
                                                                    mountpath=self.mount_path,
                                                                    mediaagent=self.tcinputs['MediaAgent1'],
                                                                    ddb_ma=self.tcinputs['MediaAgent1'],
                                                                    deduppath=self.dedup_path)

            self.library_name = self._get_library_name(self.storage_pool_name)

            # Validation from DB :
            # Checking whether defaults are met.
            self.log.info("Validating default settings for MA1")
            self._validate_storage_default_settings(self.storage_pool_name, self.tcinputs['MediaAgent1'])

            # Creating the dependent storage policy
            self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
                storage_policy_name=self.storage_policy_name,
                storage_pool_name=self.storage_pool_name, is_dedup_storage_pool=True)

            # Creating backupset
            self.mmhelper.configure_backupset(self.backupset_name,
                                              self.agent)

            # Creating subclient
            subclient_name = f"{self.id}_subclient"
            subclient = self.mmhelper.configure_subclient(self.backupset_name, subclient_name,
                                                          self.storage_policy_name, self.content_path, self.agent)

            # Generating data on subclient
            if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 5):
                self.log.error('Error in generating the data')
                raise Exception(f"Unable to generate data at {self.content_path}")
            self.log.info(f"Generated Data at {self.content_path}")

            # Running backpup using MA1
            self.log.info("Backup using MA1 ...")
            job = self.commonutils.subclient_backup(subclient, 'Full')
            job_details = job._get_job_details()
            ma = ''
            for attempt in range(len(job_details['jobDetail']['attemptsInfo'])):
                phase = job_details['jobDetail']['attemptsInfo'][attempt]['phaseName']
                status = job_details['jobDetail']['attemptsInfo'][attempt]['status']
                if ('Backup' in phase) and status == 'Completed':
                    ma = job_details['jobDetail']['attemptsInfo'][attempt]['mediaAgent']['mediaAgentName']
            if self.tcinputs['MediaAgent1'] == ma:
                self.log.info(f"Backup successfully completed using {ma}...")
            else:
                self.log.error("Backup job is not using expected media agent...")
                raise Exception("Backup job is not using expected media agent...")

            # Changing access to read only  for MA1 to obtain expected JPR
            self.log.info(f"Changing read write access to read access on {self.tcinputs['MediaAgent1']}")
            mountpath_id, device_id, device_controller_id, media_agent_id = self._get_device_controller_ids(
                self.tcinputs['MediaAgent1'], self.library_name)
            self.disk_library = self.commcell.disk_libraries.get(self.library_name)
            self.disk_library.mount_path = self.mount_path
            self.disk_library.media_agent = self.tcinputs['MediaAgent1']
            self.disk_library.change_device_access_type(mountpath_id, device_id,
                                                        device_controller_id,
                                                        media_agent_id,
                                                        self.read_access)

            # Running backup job using MA1 with read permissions
            self.log.info("Backup using MA1 ... using read only access to obtain valid jpr")
            job = self.commonutils.subclient_backup(subclient, "Full", wait=False)
            self.job_manager.job = job
            upper_bound = time.time() + 300
            delay_reason = ''
            while (job.delay_reason == None and time.time() <= upper_bound):
                time.sleep(5)
            if (job.delay_reason == None):
                raise Exception('Timed out, since, 5 mins there is no delay reason...')
            delay_reason = job.delay_reason
            self.log.info(f"Job Pending Reason : {delay_reason}")

            # Providing the read write access for MA1, to resume job
            self.log.info(f"Updating to read write access on {self.tcinputs['MediaAgent1']}")
            self.disk_library.change_device_access_type(mountpath_id, device_id,
                                                        device_controller_id,
                                                        media_agent_id,
                                                        self.read_write_access)
            self.job_manager.wait_for_state(expected_state='completed', retry_interval=10, time_limit=75)
            job_details = job._get_job_details()
            for attempt in range(len(job_details['jobDetail']['attemptsInfo'])):
                phase = job_details['jobDetail']['attemptsInfo'][attempt]['phaseName']
                status = job_details['jobDetail']['attemptsInfo'][attempt]['status']
                if ('Backup' in phase) and status == 'Completed':
                    ma = job_details['jobDetail']['attemptsInfo'][attempt]['mediaAgent']['mediaAgentName']
            if self.tcinputs['MediaAgent1'] == ma:
                self.log.info(f"Backup successfully completed using {ma}...")
            else:
                self.log.error("Backup job is not using expected media agent...")
                raise Exception("Backup job is not using expected media agent...")
            if 'MediaAgent does not have write access enabled for the mount path to this device' in delay_reason:
                self.log.info("Got valid jpr....")
            else:
                self.log.error("Invalid jpr...")
                raise Exception('Not valid jpr...')

            # UNC positive case
            # Sharing mountpath to MA2 using network path
            share_path = self.mount_path
            unc_path = f'\\\\{self.media_agent1.get_hostname()}\\{self.share_name}'
            self.media_agent1.share_directory(self.share_name, share_path,
                                              user=self._get_cred_user_name(self.tcinputs['SavedFullControlCred']),
                                              permission='FULL')

            self.disk_library.change_device_access_type(mountpath_id, device_id,
                                                        device_controller_id,
                                                        media_agent_id,
                                                        device_access_type=self.read_access)
            self.disk_library.share_mount_path(new_media_agent=self.tcinputs['MediaAgent2'],
                                               new_mount_path=unc_path,
                                               credential_name=self.tcinputs['SavedFullControlCred'],
                                               access_type=self.read_write_access)
            self.log.info('Mount path successfully shared to MA2...')

            # Validating max writers on device controller :
            self.log.info('Verifying max writers and read/write access for MA2')
            self.max_concurrent_writers_set_on_device_controller_level = (
                self._validate_max_concurrent_writers_on_device_controller_level(
                    self.storage_pool_name, self.tcinputs['MediaAgent2']))
            if self.max_concurrent_writers_set_on_device_controller_level:
                self.log.info(
                    f"Max concurrent writers set on device controller level : "
                    f"{self.max_concurrent_writers_set_on_device_controller_level}")
            else:
                self.log.warning(f"Max concurrent writers set on device controller level : "
                                 f"{self.max_concurrent_writers_set_on_device_controller_level}")
                self.errors.append("Max concurrent writers are not set on MA2..")

            # Validating for read and write access :
            self.read_write_access = self._validate_for_read_write_access(self.storage_pool_name,
                                                                          self.tcinputs['MediaAgent2'])
            self.log.info(f"Read write access is enabled : {self.read_write_access}")
            if not self.read_write_access:
                raise Exception("read write access is not set on MA2...")

            # Running backup job using MA2
            self.log.info("Running backup using MA2...")
            job = self.commonutils.subclient_backup(subclient, 'Full')
            job_details = job._get_job_details()
            for attempt in range(len(job_details['jobDetail']['attemptsInfo'])):
                phase = job_details['jobDetail']['attemptsInfo'][attempt]['phaseName']
                status = job_details['jobDetail']['attemptsInfo'][attempt]['status']
                if ('Backup' in phase) and status == 'Completed':
                    ma = job_details['jobDetail']['attemptsInfo'][attempt]['mediaAgent']['mediaAgentName']
            if self.tcinputs['MediaAgent2'] == ma:
                self.log.info(f"Backup successfully completed using {ma}...")
            else:
                self.log.error("Backup job is not using expected media agent...")
                raise Exception("Backup job is not using expected media agent...")

            # UNC negative case :
            # Accessing mount path using read only creds
            self.media_agent1.unshare_directory(self.share_name)
            self.media_agent1.share_directory(self.share_name,
                                              share_path,
                                              user=self._get_cred_user_name(self.tcinputs['SavedReadOnlyCred']),
                                              permission='READ')
            mountpath_id, device_id, device_controller_id, media_agent_id = self._get_device_controller_ids(
                self.tcinputs['MediaAgent2'], self.library_name)
            self.disk_library.update_device_controller(mountpath_id, device_id,
                                                       device_controller_id,
                                                       media_agent_id,
                                                       self.read_write_access,
                                                       credential_name=self.tcinputs['SavedReadOnlyCred'],
                                                       path=unc_path)
            self.log.info("Running the job with read only creds to obtain valid jpr")
            job = self.commonutils.subclient_backup(subclient, 'Full', wait=False)
            self.job_manager.job = job
            self.job_manager.wait_for_state('pending', retry_interval=10, time_limit=75)
            delay_reason = job.delay_reason
            self.log.info(f"Job Pending Reason : {delay_reason}")
            if 'Permission denied error while accessing the path' in delay_reason:
                self.log.info("Got valid jpr....")
            else:
                self.log.error("Invalid jpr...")
                raise Exception('Not valid jpr...')

            # Updating with read write creds to resume job
            self.media_agent1.unshare_directory(self.share_name)
            self.media_agent1.share_directory(self.share_name, share_path,
                                              user=self._get_cred_user_name(self.tcinputs['SavedFullControlCred']),
                                              permission='FULL')
            self.disk_library.update_device_controller(mountpath_id,
                                                       device_id,
                                                       device_controller_id,
                                                       media_agent_id,
                                                       self.read_write_access,
                                                       credential_name=self.tcinputs['SavedFullControlCred'],
                                                       path=unc_path)
            job.resume()
            self.job_manager.wait_for_state(expected_state='completed', retry_interval=10, time_limit=75)
            job_details = job._get_job_details()
            for attempt in range(len(job_details['jobDetail']['attemptsInfo'])):
                phase = job_details['jobDetail']['attemptsInfo'][attempt]['phaseName']
                status = job_details['jobDetail']['attemptsInfo'][attempt]['status']
                if ('Backup' in phase) and status == 'Completed':
                    ma = job_details['jobDetail']['attemptsInfo'][attempt]['mediaAgent']['mediaAgentName']
            if self.tcinputs['MediaAgent2'] == ma:
                self.log.info(f"Backup successfully completed using {ma}...")
            else:
                self.log.error("Backup job is not using expected media agent...")
                raise Exception("Backup job is not using expected media agent...")

            # Restorartion :
            # Restoration using MA2 :
            mountpath_id, device_id, device_controller_id, media_agent_id = self._get_device_controller_ids(
                self.tcinputs['MediaAgent1'], self.library_name)
            self.disk_library.update_device_controller(mountpath_id,
                                                       device_id,
                                                       device_controller_id,
                                                       media_agent_id,
                                                       self.read_write_access, path=self.mount_path, enabled=False)
            self.log.info('Restore using MA2 ..')
            self._restore_and_validate(self.restore_path1, subclient, self.tcinputs['MediaAgent2'])

            # Restoration using MA1 :
            self.disk_library.update_device_controller(mountpath_id,
                                                       device_id, device_controller_id, media_agent_id,
                                                       self.read_write_access, path=self.mount_path, enabled=True)
            mountpath_id, device_id, device_controller_id, media_agent_id = self._get_device_controller_ids(
                self.tcinputs['MediaAgent2'], self.library_name)
            self.disk_library.update_device_controller(mountpath_id, device_id, device_controller_id, media_agent_id,
                                                       self.read_write_access,
                                                       credential_name=self.tcinputs['SavedFullControlCred'],
                                                       path=unc_path, enabled=False)
            self.log.info('Restore using MA1 ..')
            self._restore_and_validate(self.restore_path2, subclient, self.tcinputs['MediaAgent1'])
            if len(self.errors) >= 1:
                error = '\n'.join(self.errors)
                self.errors = []
                raise Exception(error)

        except Exception as exp:
            error = str(exp)
            if len(self.errors) >= 1:
                error = error + '\n' + '\n'.join(self.errors)
            self.log.error(f'Errors : {error}')
            self.result_string = error
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        if self.share_name in self.media_agent1.list_shares_on_network_path(
                f'\\\\{self.media_agent1.get_hostname()}', username='', password=''):
            self.media_agent1.unshare_directory(self.share_name)

        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

        if self.client_machine.check_directory_exists(self.restore_path1):
            self.client_machine.remove_directory(self.restore_path1)

        if self.client_machine.check_directory_exists(self.restore_path2):
            self.client_machine.remove_directory(self.restore_path2)

        if (self.status != constants.FAILED):
            self.log.info("Test case executed successfully...")
            self._cleanup()
        else:
            self.log.error("Test case failed. no cleaning...")
