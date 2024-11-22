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

    setup()         --  create objects etc

    allocate_resources()  --  create environment

    deallocate_resources() -- cleanup

    run_backup_job() --  run supplied number of backup jobs

    prune_job() -- delete a job and run data aging

    mmdeletedaf_empty() -- confirm mmdeletedaf has no entries for supplied mountpathid

    build_mount_path() -- build the complete path including CV_MAGNETIC

    modify_mp_label() -- invalidate the mountpaths label file so it cant prune

    get_vol_count() -- for given mountpath, fetch volumeid count in mmvolume

    csdb_validation() -- for given table and mountpathid, check that volid count is 0

    exists_check() -- validates expected volume directories are physically deleted on give mountpath

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Input JSON:

64527: {
        "AgentName": "File System",
        "MediaAgentName": "ma name",
        "ClientName" : "client name"
}

"""
import time
from AutomationUtils import constants
from AutomationUtils import config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "nondedup batch pruning when a mountpath is offline"
        self.tcinputs = {
            "MediaAgentName": None,
        }

        self.mm_helper = None
        self.optionobj = None
        self.backupset_obj = None
        self.sp_copy_obj = None
        self.library = None
        self.storage_policy = None
        self.gacp = None
        self.subclient1_obj = None
        self.subclient2_obj = None
        self.client_machineobj = None
        self.ma_machineobj = None
        self.mediaagentname = None
        self.mountpath0 = None
        self.mountpath1 = None
        self.mountpath0_id = None
        self.mountpath1_id = None
        self.storage_policy_name = None
        self.gacp_name = None
        self.library_name = None
        self.backupset_name = None
        self.subclient1_name = None
        self.subclient2_name = None
        self.content1_path = None
        self.content2_path = None
        self.client_system_drive = None
        self.ma_system_drive = None
        self.sqluser = None
        self.sqlpassword = None
        self.backup_jobs_list = None
        self.os_sep = None
        self.result_string = ""

    def setup(self):
        """
        Setup function of this test case
        """

        self.optionobj = OptionsSelector(self.commcell)
        self.mm_helper = mahelper.MMHelper(self)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.client_machineobj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machineobj, 25*1024)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_system_drive = self.optionobj.get_drive(self.ma_machineobj, 25*1024)
        suffix = str(self.mediaagentname) + "_" + str(self.client.client_name)

        self.library_name = f'{self.id}_LIB_{suffix}'
        self.gacp_name = f'{self.id}_GACP_{suffix}'
        self.storage_policy_name = f'{self.id}_SP_{suffix}'
        self.backupset_name = f'{self.id}_BS_{suffix}'
        self.subclient1_name = f'{self.id}_SC1_{suffix}'
        self.subclient2_name = f'{self.id}_SC2_{suffix}'
        self.content1_path = self.client_machineobj.join_path(self.client_system_drive, f'content1_{self.id}')
        self.content2_path = self.client_machineobj.join_path(self.client_system_drive, f'content2_{self.id}')
        self.os_sep = self.ma_machineobj.os_sep
        self.sqluser = config.get_config().SQL.Username
        self.sqlpassword = config.get_config().SQL.Password

    def allocate_resources(self):
        """
        create the resources needed before starting backups
        """

        # disable ransomware protection so mountpath can be manipulated
        if self.ma_machineobj.os_info.lower() == 'windows' and \
                self.mm_helper.ransomware_protection_status(self.commcell.clients.get(self.mediaagentname).client_id):
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)
            self.log.info("Successfully disabled Ransomware protection on MA")
        else:
            self.log.info("either this isnt windows or RWP is already disabled")

        # Create paths
        self.mountpath0 = self.ma_machineobj.join_path(self.ma_system_drive, self.id, "mountpath0")
        self.mountpath1 = self.ma_machineobj.join_path(self.ma_system_drive, self.id, "mountpath1")

        # create library with one mountpath
        self.library = self.commcell.disk_libraries.add(self.library_name, self.mediaagentname, self.mountpath0)

        # add second mountpath
        self.library.add_mount_path(self.mountpath1, self.mediaagentname)

        # get mountpathids
        query = f'select mountpathid from mmmountpath where libraryid = ' \
                f'( select LibraryId from mmlibrary where aliasname =  \'{self.library_name}\') order by mountpathid'
        self.log.info(f'QUERY: {query}')
        self.csdb.execute(query)
        mountpath_id_list = self.csdb.fetch_all_rows()
        self.mountpath0_id = int(mountpath_id_list[0][0])
        self.mountpath1_id = int(mountpath_id_list[1][0])
        self.log.info(f'MountPathId0 = {self.mountpath0_id} and mountpathid1 = {self.mountpath1_id}')

        # create GACP
        self.gacp = self.commcell.policies.storage_policies.add_global_storage_policy(
            self.gacp_name, self.library_name, self.tcinputs['MediaAgentName'])

        self.log.info(f'---Successfully configured non dedup storage pool - {self.gacp_name}')

        # create dependent storage policy
        self.storage_policy = self.commcell.policies.storage_policies.add(
            storage_policy_name=self.storage_policy_name, global_policy_name=self.gacp_name,
            global_dedup_policy=False)

        self.log.info(f'---Successfully configured dependent storage policy - {self.storage_policy_name}')

        # get dependent copy object to be referenced later
        self.sp_copy_obj = self.storage_policy.get_copy("Primary")

        # Configure backup set and subclients
        self.log.info("---Configuring backup set---")
        self.backupset_obj = self.mm_helper.configure_backupset(self.backupset_name)
        if self.client_machineobj.check_directory_exists(self.content1_path):
            self.client_machineobj.remove_directory(self.content1_path)
        self.client_machineobj.create_directory(self.content1_path)
        self.log.info("---Configuring subclient---")
        self.subclient1_obj = self.mm_helper.configure_subclient(self.backupset_name, self.subclient1_name,
                                                                 self.storage_policy_name,
                                                                 content_path=self.content1_path)
        if self.client_machineobj.check_directory_exists(self.content2_path):
            self.client_machineobj.remove_directory(self.content2_path)
        self.client_machineobj.create_directory(self.content2_path)
        self.log.info("---Configuring subclient---")
        self.subclient2_obj = self.mm_helper.configure_subclient(self.backupset_name, self.subclient2_name,
                                                                 self.storage_policy_name,
                                                                 content_path=self.content2_path)
        self.backup_jobs_list = []

        self.log.info("---Creating uncompressable unique data---")
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content1_path, 0.1)
        self.mm_helper.create_uncompressable_data(self.client.client_name, self.content2_path, 0.1)

        # set multiple readers for subclient to increase volume count
        self.subclient1_obj.data_readers = 10
        self.subclient2_obj.data_readers = 10
        self.subclient1_obj.allow_multiple_readers = True
        self.subclient2_obj.allow_multiple_readers = True

        # add reg key to set max vols to macroprune to 100 per ma (100 is lowest allowed setting)
        self.log.info("adding reg key nMMMaxNoOfVolumesToMacroPrune, value set to 100")
        self.commcell.add_additional_setting("MediaManager", "nMMMaxNoOfVolumesToMacroPrune", "INTEGER", "100")

    def deallocate_resources(self):
        """
        removes all resources allocated by the Testcase
        """

        if self.client_machineobj.check_directory_exists(self.content1_path):
            self.client_machineobj.remove_directory(self.content1_path)
            self.log.info("content1_path deleted")
        else:
            self.log.info("content1_path does not exist.")

        if self.client_machineobj.check_directory_exists(self.content2_path):
            self.client_machineobj.remove_directory(self.content2_path)
            self.log.info("content2_path deleted")
        else:
            self.log.info("content2_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("dependent storage policy deleted")
        else:
            self.log.info("dependent storage policy does not exist.")

        if self.commcell.storage_policies.has_policy(self.gacp_name):
            self.commcell.storage_policies.delete(self.gacp_name)
            self.log.info("Storage pool deleted")
        else:
            self.log.info("Storage pool does not exist.")
        self.commcell.disk_libraries.refresh()

        self.log.info("clean up successful")

    def run_backup_job(self, num_backups=1, backuptype="Full"):
        """
        run a backup job and start new media on each of two subclients
        Args:
            num_backups (int) -- how many backup iterations to run
            backuptype (str) -- Backup type , Incremental by default.
        """

        for bkps in range(1, num_backups+1):
            self.log.info(f'Starting backup iteration - [{bkps}]')
            job1 = self.subclient1_obj.backup(backuptype,
                                              advanced_options={'mediaOpt': {'markMediaFullOnSuccess': True}})
            job2 = self.subclient2_obj.backup(backuptype,
                                              advanced_options={'mediaOpt': {'markMediaFullOnSuccess': True}})
            self.backup_jobs_list.append(job1)
            self.log.info(f'new backup job {job1.job_id} submitted')
            self.backup_jobs_list.append(job2)
            self.log.info(f'new backup job {job2.job_id} submitted')
            if not job1.wait_for_completion():
                raise Exception(f'Failed to run {backuptype} backup with error: {job1.delay_reason}')
            self.log.info(f'Backup job [{job1.job_id}] completed')
            if not job2.wait_for_completion():
                raise Exception(f'Failed to run {backuptype} backup with error: {job2.delay_reason}')
            self.log.info(f'Backup job [{job2.job_id}] completed')
            # prevents problem where jobs overlap and next job fails to start
            time.sleep(5)

    def prune_job(self, joblist):
        """
        deletes job and runs data aging

        args:
            joblist(list) - list of jobs
        returns:

        """

        for interval in range(len(joblist)):
            self.log.info(f'Deleting backup job [{joblist[interval].job_id}]')
            self.sp_copy_obj.delete_job(joblist[interval].job_id)
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 1, 1)
        data_aging_job = self.mm_helper.submit_data_aging_job('Primary', self.storage_policy_name)
        self.log.info(f'data aging job: {data_aging_job.job_id}')
        if not data_aging_job.wait_for_completion():
            self.log.info(f'Failed to run data aging with error: {data_aging_job.delay_reason}')

    def mmdeletedaf_empty(self, mountpathid):
        """
        for given mountpathid, return true if the query returns nothing, otherwise false.

        args:
            mountpathid (int) - mountpathid
        return:
            (bool) - returns true if query output is 0, otherwise returns false
        """

        query = f'select count(distinct volumeid) from mmdeletedaf where mountpathid  = {mountpathid}'
        self.log.info(f'Query => {query}')
        self.csdb.execute(query)
        vol_count = int(self.csdb.fetch_one_row()[0])
        self.log.info(f'mountpathid {mountpathid} volcount: {vol_count}')
        return vol_count == 0

    def build_mount_path(self, mountpath, mountpathid):
        """
        for given mountpath and mountpathid, build the complete path including CV_MAGNETIC

        args:
            mountpath (str) - short version of the given mountpath
            mountpathid (int) - mountpathid

        return:
            fullpath (str) - the full path for the mp, including CV_MAGNETIC
        """
        query = f'select mountpathname from mmmountpath where mountpathid  = {mountpathid}'
        self.log.info(f'Query => {query}')
        self.csdb.execute(query)
        mp_name = self.csdb.fetch_one_row()[0]
        self.log.info(f'mountpathname is {mp_name}')
        fullpath = mountpath + self.os_sep + mp_name + self.os_sep + "CV_MAGNETIC"
        return fullpath

    def modify_mp_label(self, make_invalid):
        """
        for first mountpath, invalidate mountpath_label file (or delete it so correct will regenerate)

        args:
            make_invalid (bool) - whether to invalidate the label file or delete it, which will generate a new one

        return:

        """
        # build full mountpath path for mountpath0
        local_mp_location = self.build_mount_path(self.mountpath0, self.mountpath0_id)

        if make_invalid:
            self.ma_machineobj.create_file(local_mp_location + self.os_sep + 'MOUNTPATH_LABEL',
                                           'this file has been corrupted', 0)
        else:
            self.ma_machineobj.delete_file(local_mp_location + self.os_sep + 'MOUNTPATH_LABEL')

    def get_vol_count(self, mountpathid):
        """
        for given mountpath, fetch volumeid count in mmvolume

        args:
            mountpathid (int)

        return:
            vol_count (int)
        """

        # fetching current volumeid count in mmvolume for mountpathid
        query = f'select count(distinct volumeid) from mmvolume where currmountpathid = {mountpathid}'
        self.log.info(f'Query => {query}')
        self.csdb.execute(query)
        vol_count = int(self.csdb.fetch_one_row()[0])
        self.log.info(f' mpid {mountpathid} volcount: {vol_count}')
        return vol_count

    def csdb_validation(self, table, mountpathid):
        """
        for given table and mountpathid, check that volid count is 0

        args:
            table (str) - table to run queries on
            mountpathid (int) - mountpathid

        returns:
            validation_status (bool) - true if table entries were removed, false if not
        """

        iterations = 0
        validation_status = True
        if table == 'mmdeletedaf':
            while (not self.mmdeletedaf_empty(mountpathid)) and iterations < 10:
                self.log.info(f'try {iterations}: mmdelaf not empty for mp {mountpathid}, sleep 1 min and retry')
                iterations += 1
                time.sleep(60)
            if iterations == 10:
                validation_status = False
            else:
                self.log.info("cleared all mmdelaf entries for mp")
        elif table == 'mmvolume':
            while not self.get_vol_count(mountpathid) == 0 and iterations < 10:
                self.log.info(f'try {iterations}: {mountpathid} still has vols, sleep 1 min and retry')
                iterations += 1
                time.sleep(60)
            if iterations == 10:
                validation_status = False
            else:
                self.log.info("volumes on mp were pruned")
        return validation_status

    def exists_check(self, mountpath, mountpathid):
        """
        validates expected volume directories are physically deleted on give mountpath
        args:
            mountpath (str)
            mountpathid (int)
        returns:
            (bool)
        """

        deleted_status = True
        exists_iteration = 0
        fullmountpath = self.build_mount_path(mountpath, mountpathid)
        while len(self.ma_machineobj.get_folders_in_path(
                fullmountpath, recurse=False)) != 0 and exists_iteration < 10:
            self.log.info(f'iteration {exists_iteration}: vol dirs still exist, will retry')
            exists_iteration += 1
            time.sleep(60)
        if exists_iteration == 10:
            deleted_status = False
        else:
            self.log.info(f'confirmed vol directories count on {mountpath} is 0, as expected')
        return deleted_status

    def run(self):
        """Run function of this test case"""
        try:

            # clean up from previous failed run
            self.deallocate_resources()

            self.log.info("----------TC environment configuration started----------")
            self.allocate_resources()
            self.log.info("----------TC environment configuration completed----------")

            # run 10 backups that create 90 full volumes on each mountpath
            self.run_backup_job(10)

            # make first mountpath label file invalid
            self.log.info(f'----------modifying label file on {self.mountpath0}----------')
            self.modify_mp_label(make_invalid=True)
            self.log.info("----------label modified----------")

            # get count of volumes in bad mountpath in mmvolume before deleting any jobs
            volcount_mp0_beforepruning = self.get_vol_count(self.mountpath0_id)

            # delete all the jobs from both mountpaths
            self.prune_job(self.backup_jobs_list)
            time.sleep(10)

            self.log.info("----------VALIDATING MMDEL ENTRIES REMOVED FOR GOOD MP----------")
            if not self.csdb_validation('mmdeletedaf', self.mountpath1_id):
                raise Exception(f'not all entries were removed from mmdeletedaf for good mp, not expected')

            # verify count of volumes in mmvolume for good mountpath is now 0
            self.log.info("----------VALIDATING MMVOL COUNT IS 0 FOR GOOD MP----------")
            if not self.csdb_validation('mmvolume', self.mountpath1_id):
                raise Exception("volumes on good mountpath were not pruned, not expected")

            # confirm with exists check that volume dirs on good mountpath are gone
            self.log.info("----------VALIDATING VOLS ARE PHYSICALLY DELETED ON GOOD MP----------")
            if not self.exists_check(self.mountpath1, self.mountpath1_id):
                raise Exception(f'vol directories still present on {self.mountpath1}, not expected')

            # verify count of volumes in mmvolume for bad mountpath is still same as pre deletion
            self.log.info("----------VALIDATING MMVOL COUNT IS STILL SAME FOR BAD MP----------")
            if not self.get_vol_count(self.mountpath0_id) == volcount_mp0_beforepruning:
                raise Exception("volumes were pruned on the bad mountpath")
            else:
                self.log.info("volcount before and after pruning on bad mountpath is equal, as expected")

            # fix the bad mountpath
            self.log.info(f'------------fixing bad mountpath {self.mountpath0}------------')
            self.modify_mp_label(make_invalid=False)

            self.log.info("----------VALIDATING MMDEL ENTRIES REMOVED FOR BAD (FIXED) MP----------")
            if not self.csdb_validation('mmdeletedaf', self.mountpath0_id):
                raise Exception("not all entries were removed from mmdeletedaf for fixed mp, not expected")

            # verify count of volumes in mmvolume for bad (fixed) mountpath is now 0
            self.log.info("----------VALIDATING MMVOL COUNT IS NOW 0 FOR FIXED MP----------")
            if not self.csdb_validation('mmvolume', self.mountpath0_id):
                raise Exception("volumes on fixed mountpath were not pruned, not expected")

            # confirm with exists check that volume directory count matches mmvolume count on fixed mp
            self.log.info("----------VALIDATING VOLS ARE PHYSICALLY DELETED ON FIXED MP----------")
            if not self.exists_check(self.mountpath0, self.mountpath0_id):
                raise Exception(f'vol directories still present on {self.mountpath0}, not expected')

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("-------------------tear down method-------------------")

        # set prune process interval back to default
        self.mm_helper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)

        if self.ma_machineobj.os_info.lower() == 'windows' and not \
                self.mm_helper.ransomware_protection_status(self.commcell.clients.get(self.mediaagentname).client_id):
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
            self.log.info("Successfully enabled Ransomware protection on MA")
        else:
            self.log.info("RWP is already enabled here, no need to re-enable it")

        # remove reg key for macroprune batching
        self.log.info("removing reg key nMMMaxNoOfVolumesToMacroPrune")
        self.commcell.delete_additional_setting("MediaManager", "nMMMaxNoOfVolumesToMacroPrune")

        # re-associate SP
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info(f'reassociating storage policy {self.storage_policy_name} in '
                          f'case it is associated to ddbbackup')
            self.storage_policy.reassociate_all_subclients()

        self.log.info("Performing unconditional cleanup")
        self.deallocate_resources()
