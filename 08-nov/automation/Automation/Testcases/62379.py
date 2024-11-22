# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

     It verifies if RFC framework is able to be consistent with it's functionalities when the backups
     happen on more than one platform.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    run_backup()                                -- Runs VSA backup

    vm_sc_info_from_parent_job()                -- To create a mapping of VM subclient to it's child jobs

    verify_rfc_upload()                         -- Fetches the rfc server for the job and verifies
                                                   the RFC upload on the server

    get_rfc_folder_path()                       -- RFC folder path list of the given job on the rfc server

    verify_rfc_download()                       -- Does a live browse and verifies the download of rfc

    validate_rfc_operations()                   -- Verifies all RFC operations at once

    verify_rfc_download_from_backup_copy()      -- Verifies RFC download by running a backup copy

    switch_datapaths_change_is()                -- To switch between the datapaths for Index server and snap copy MA

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from Indexing.validation.vsa_features import VSAFeatures


class TestCase(CVTestCase):
    """
    It verifies if RFC framework is able to be consistent with it's functionalities when the backups
    happen on more than one platform.

    Steps:
        1. Have a backupset and sublcient
        2. Have two datapaths for the SP, one Unix and one Windows.
        3. Verify all RFC operations when snap and backup copy job each run on two
        different OS platforms datapath MAs
        4. Verify all RFC operations when FULL snap and backup copy runs on one OS datapath MA and next INC snap and backup copy job  runs on another OS datapath MA.
        5. Verify RFC and SFULL when the previous INCs run on different OS datapath MAs.

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - RFC - Validation of Cross Platform Operations'
        self.tcinputs = {}
        self.idx_help = None
        self.cl_machine = None
        self.rfc_server_machine = None
        self.storage_policy = None
        self.sp_primary_copy = None
        self.sp_snap_copy = None
        self.idx_tc = None
        self.idx_vsa = None
        self.auto_subclient = None
        self.auto_backupset = None
        self.auto_commcell = None
        self.vsa_sc_guid = None
        self.vm_guid_sc_guid = {}
        self.common_utils = None
        self.sc_level_rfc_folders = []
        self.vm_backupsets = []
        self.options_help = None

        self._sc_vms = None
        self._cv_vms = {}
        self.rfc_servers = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.commcell.commserv_name, self.commcell)
        self.idx_help = IndexingHelpers(self.commcell)
        self.idx_tc = IndexingTestcase(self)
        self.options_help = self.idx_tc.options_help

        self.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(self.auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
        self.auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        self.auto_subclient = VirtualServerHelper.AutoVSASubclient(self.auto_backupset, self.subclient)

        self.common_utils = self.idx_tc.cv_ops

        storage_policy_name = self.auto_subclient.subclient.storage_policy
        self.storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        self.sp_primary_copy = self.storage_policy.get_primary_copy()
        snap_copy_name = self.storage_policy.snap_copy
        self.sp_snap_copy = self.storage_policy.get_copy(copy_name=snap_copy_name)

        self.idx_vsa = VSAFeatures(self.auto_subclient, self)
        self.idx_vsa.initialize_vms()

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.vsa_sc_guid = self.auto_subclient.subclient.subclient_guid
            self.log.info('VSA subclient GUID is %s', self.vsa_sc_guid)

            for each_vm in self.idx_vsa.vm_guids:
                vm_client_info = self.idx_vsa.get_cv_vm_client(vm_guid=each_vm)
                vm_subclient = vm_client_info.get('subclient')
                vm_backupset = vm_client_info.get('backupset')
                vm_sc_guid = vm_subclient.subclient_guid
                self.log.info('VM SC guid is %s', vm_sc_guid)
                self.vm_guid_sc_guid[each_vm] = vm_sc_guid
                self.vm_backupsets.append(vm_backupset)

            self.log.info('VM guid to VM sc guid mapping is %s', self.vm_guid_sc_guid)

            self.log.info('******** Scenario 1: Snap and Backup copy on different MAs of different OS ********')
            is_ma_s1, snapcopy_ma_s1 = self.switch_datapaths_change_is(keep_same=False)
            self.log.info('********** Running FULL backup **********')
            full_job_s1 = self.run_backup(backup_level='FULL')
            self.validate_rfc_operations(
                parent_job=full_job_s1,
                snap_ma_machine=snapcopy_ma_s1,
                is_machine=is_ma_s1
            )

            self.log.info('****** Scenario 2: FULL with MA1 and INC with MA2, where each MA is on different OS ******')
            is_ma_s2, snapcopy_ma_s2 = self.switch_datapaths_change_is(keep_same=True)
            self.log.info('********** Running FULL backup **********')
            full_job_s2 = self.run_backup(backup_level='FULL')
            self.validate_rfc_operations(
                parent_job=full_job_s2,
                snap_ma_machine=snapcopy_ma_s2,
                is_machine=is_ma_s2
            )

            new_is_ma_s2, new_snapcopy_ma_s2 = self.switch_datapaths_change_is(keep_same=True, change_both=True)
            self.log.info('********** Running INCREMENTAL backup **********')
            inc_job_s2 = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(
                parent_job=inc_job_s2,
                snap_ma_machine=new_snapcopy_ma_s2,
                is_machine=new_is_ma_s2
            )

            self.log.info('****** Scenario 3: SFULL with two previous INCs on two MAs, one Windows and one Unix ******')
            is_ma_s3, snapcopy_ma_s3 = self.switch_datapaths_change_is(keep_same=True, change_both=True)
            self.log.info('********** Running INCREMENTAL backup **********')
            inc_job_s3 = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(
                parent_job=inc_job_s3,
                snap_ma_machine=snapcopy_ma_s3,
                is_machine=is_ma_s3
            )

            new_is_ma_s3, new_snapcopy_ma_s3 = self.switch_datapaths_change_is(keep_same=True, change_both=True)
            self.log.info('********** Running SYNTHETIC FULL backup **********')
            sfull_job_s3 = self.run_backup(backup_level='SYNTHETIC_FULL')
            self.validate_rfc_operations(
                parent_job=sfull_job_s3,
                snap_ma_machine=new_snapcopy_ma_s3,
                is_machine=new_is_ma_s3
            )

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def run_backup(self, backup_level):
        """ Runs VSA backup
                     Args:
                           backup_level     (str)   --   Type of backup job

                    Returns:
                           (obj)      --   Job object

                """
        backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
        backup_options.backup_type = backup_level
        if backup_level == 'SYNTHETIC_FULL':
            backup_options.incr_level = ''

        self.auto_subclient.backup(backup_options, skip_discovery=True)
        job = self.auto_subclient.backup_job

        return job

    def vm_sc_info_from_parent_job(self, parent_job):
        """ To create a mapping of VM subclient to it's child jobs
             Args:
                   parent_job     (obj)   --   Job object of the parent job

            Returns:
                   (dict)      --   Mapping of VM's subclient GUIDS and their child jobs
                   (dict)      --   Mapping of child job and vm name

        """
        self.log.info('Creating two mappings of VM subclient GUIS, the child job IDs and VM names and child jobs IDs')
        vm_sc_guid_job_info = {}
        job_id_vm_name = {}
        self.log.info('Parent job details [%s]', parent_job.details)
        vm_details = parent_job.details['jobDetail']['clientStatusInfo']['vmStatus']
        self.log.info(vm_details)
        # VM subclient GUID and it's child job ID mapping is needed to get the RFC folder path both during
        # the upload and the download verification of RFC
        for vm in vm_details:
            vm_name = vm.get('vmName', None)
            vm_guid = vm.get('GUID', None)
            vm_sc_guid = self.vm_guid_sc_guid[vm_guid]
            child_job_id = vm.get('jobID', None)
            if not vm_name or not vm_guid or not child_job_id:
                raise Exception('Unable to fetch VM and its job details')
            vm_sc_guid_job_info[str(child_job_id)] = vm_sc_guid
            job_id_vm_name[str(child_job_id)] = vm_name

        self.log.info(' VM SC GUID and job matching is %s', vm_sc_guid_job_info)
        # Child job ID and VM name mapping is needed during the browse, as the
        # guest file browse needs to be done with vm name as the path to restore the RFC
        return vm_sc_guid_job_info, job_id_vm_name

    def verify_rfc_upload(self, job_id, sc_guid):
        """ Fetches the rfc server for the job and verifies the RFC upload on the server

                Args:
                           job_id           (str)   --   Job ID of the job for which RFC upload has to be verified

                           sc_guid         (str)    --  subclient guid of the subclient who's RFC has to be verified

        """
        self.log.info(' Verifying the upload of RFC for Job: %s', job_id)
        rfc_server = self.idx_help.get_rfc_server(job_id=job_id)
        rfc_server_name = rfc_server.name
        self.log.info('RFC server for the job: %s is %s', job_id, rfc_server_name)
        if rfc_server_name not in self.rfc_servers:
            rfc_server_machine = Machine(rfc_server_name, self.commcell)
            self.rfc_servers[rfc_server_name] = rfc_server_machine
        else:
            rfc_server_machine = self.rfc_servers.get(rfc_server_name)

        # RFC folder path is created using the RFC server retrieved, child job ID and VM subclient GUID
        rfc_folder = self.get_rfc_folder_path(
            rfc_server_machine=rfc_server_machine,
            job_id=job_id,
            sc_guid=sc_guid
        )
        self.log.info('RFC folder path for the job: %s is %s', job_id, rfc_folder)

        self.log.info('***** Checking for the uploaded rfc folder job ******')
        if rfc_server_machine.check_directory_exists(rfc_folder):
            rfc_files = rfc_server_machine.get_files_in_path(rfc_folder)
            self.log.info('RFC files under %s are %s', rfc_folder, rfc_files)
            if len(rfc_files) != 0:
                self.log.info('Upload of the RFC verified at %s', rfc_folder)
            else:
                raise Exception(f'Upload of RFC failed, no files at RFC path {rfc_folder}')
        else:
            raise Exception(f'RFC folder at {rfc_folder} doesnt exist ')

    def get_rfc_folder_path(self, rfc_server_machine, job_id, sc_guid):
        """ RFC folder path of the given job on the rfc server
            Args:
                    rfc_server_machine  (obj)  --    rfc server of the job

                    job_id              (str)  --   job id

                    sc_guid             (str)  --   subclient guid

            Returns:
                    (str)      --      path of the RFC folder for given job
        """

        rfc_ma = self.commcell.media_agents.get(rfc_server_machine.machine_name)
        rfc_folder_path = rfc_server_machine.join_path(rfc_ma.index_cache_path, 'RemoteFileCache',
                                                       str(self.commcell.commcell_id), sc_guid,
                                                       job_id)
        return rfc_folder_path

    def verify_rfc_download(self, vm_sc_guid, child_job_id, job_id_vm_name, ma_machine):
        """ Does a live browse and verifies the download of rfc

                Args:
                        vm_sc_guid     (str)  --   subclient guid of the VM

                        child_job_id   (str)  --   child job id of the VM

                        job_id_vm_name (dict) --   mapping of child job and vm name

                        ma_machine     (obj)  --   Machine object of the index server MA

        """
        self.log.info(' Verifying the RFC download for the Job: %s', child_job_id)
        vm_name = job_id_vm_name.get(child_job_id)
        # Download of RFC using browse can only be verified if the VM backed up is Windows
        if self.idx_vsa.vms[vm_name]['type'] == 'windows':
            self.log.info(' Verify download of the child rfc folders on ma: %s', ma_machine.machine_name)
            rfc_folder = self.get_rfc_folder_path(ma_machine, child_job_id, vm_sc_guid)
            self.log.info('RFC folder path for the job: %s is %s', child_job_id, rfc_folder)

            if not ma_machine.check_directory_exists(rfc_folder):
                self.log.info('RFC folder at %s on this ma is not present', rfc_folder)
            else:
                ma_machine.remove_directory(rfc_folder)
                self.log.info('Deleting the existing folder %s', rfc_folder)

            self.log.info('Doing guest browse to verify download of child job RFC')
            try:
                self.auto_subclient.subclient.guest_files_browse(
                    vm_path=f'\\{vm_name}'
                )
            except Exception:
                self.log.info('Live browse is taking time to fetch results, avoiding the time out error')

            # Checking if the RFC files are downloaded on the index server MA upon browse
            if ma_machine.check_directory_exists(rfc_folder):
                downloaded_rfc_files = ma_machine.get_files_in_path(rfc_folder)
                self.log.info('Downloaded RFC files are %s at %s', downloaded_rfc_files, rfc_folder)
                if len(downloaded_rfc_files) != 0:
                    self.log.info(' RFC folder is restored at %s to complete download for live browse', rfc_folder)
                else:
                    raise Exception(f' Downloaded RFC folder has no RFC files at {rfc_folder}')
            else:
                raise Exception('Failed to verify download operation')
        else:
            self.log.info('%s is a linux vm, download of RFC using browse can not be verified. So skipping it', vm_name)

    def validate_rfc_operations(self, parent_job, snap_ma_machine, is_machine, verify_download=True):
        """ Verifies all RFC operations at once

                Args:
                    parent_job (obj)                       -- Job object of the parent job

                    snap_ma_machine (obj)                  -- Machine object of the primary snap copy MA

                    is_machine (obj)                       -- Machine object of the index server MA

                    verify_download  (boolean)             -- true if download of RFC has to be verified (When Index
                                                              server is reachable)
                                                              false if index server is down and browse is not possible
                                                              to verify rfc download
                                                              default - True

        """
        self.log.info('Validating the RFC operations one by one')
        # rfc_folder_path_list is used to verify if all RFC files are restored
        # during the verification of RFC download using the backup copy
        rfc_folder_path_list = []
        parent_job_id = parent_job.job_id
        vm_guid_job_info, job_id_vm_name = self.vm_sc_info_from_parent_job(parent_job=parent_job)

        # In case of a sfull, RFC under parent folder is not uploaded
        if parent_job.backup_level != 'Synthetic Full':
            # RFC upload verification of the parent folder
            self.verify_rfc_upload(job_id=parent_job_id, sc_guid=self.vsa_sc_guid)
        if vm_guid_job_info:
            for child_job in vm_guid_job_info:
                # RFC upload verification of each of the child folder
                rfc_folder = self.get_rfc_folder_path(is_machine, child_job, vm_guid_job_info.get(child_job))
                rfc_folder_path_list.append(rfc_folder)
                self.verify_rfc_upload(job_id=child_job, sc_guid=vm_guid_job_info.get(child_job))
                # first rfc afile created after the snap job
                self.idx_help.verify_rfc_backup(job_id=child_job)

            # In case of a sfull, RFC of the child job won't be restored during the backup copy
            if parent_job.backup_level != 'Synthetic Full':
                self.verify_rfc_download_from_backup_copy(
                    rfc_folder_list=rfc_folder_path_list,
                    ma_machine=is_machine
                )
                backup_copy_job_id = self.common_utils.get_backup_copy_job_id(snap_job_id=parent_job_id)
                # RFC upload verification of the backup copy job folder
                self.verify_rfc_upload(job_id=backup_copy_job_id, sc_guid=self.vsa_sc_guid)

            # RFC backup and download verification of each of the child jobs
            for child_job in vm_guid_job_info:
                # second rfc afile created after the backup copy job
                self.idx_help.verify_rfc_backup(job_id=child_job)
                if verify_download:
                    self.verify_rfc_download(
                        vm_sc_guid=vm_guid_job_info.get(child_job),
                        child_job_id=child_job,
                        job_id_vm_name=job_id_vm_name,
                        ma_machine=snap_ma_machine
                    )
        else:
            raise Exception('No VMs have been backed up')

    def verify_rfc_download_from_backup_copy(self, rfc_folder_list, ma_machine):
        """ Verifies RFC download upon running a backup copy

                Args:
                    rfc_folder_list (list)          -- List of rfc path to be downloaded upon running a backup copy

                    ma_machine (obj)                -- Machine object of the index server MA

        """

        self.log.info(' Verify download of the child rfc folders on ma: %s using backup copy',
                      ma_machine.machine_name)
        for rfc_folder in rfc_folder_list:
            if not ma_machine.check_directory_exists(rfc_folder):
                self.log.info('RFC folder at %s on this ma is not present', rfc_folder)
            else:
                ma_machine.remove_directory(rfc_folder)
                self.log.info('Deleting the existing folder %s', rfc_folder)

        self.log.info('Running backup copy to verify download of child job RFC')
        backup_copy_job = self.storage_policy.run_backup_copy()
        backup_copy_id = backup_copy_job.job_id
        self.log.info('Backup copy job id is %s', backup_copy_id)

        if not backup_copy_job.wait_for_completion():
            raise Exception(f'Backup copy job: {backup_copy_job.job_id} failed at the end')

        # Checking if the RFC of child jobs is downloaded onto the index server
        for rfc_folder in rfc_folder_list:
            if ma_machine.check_directory_exists(rfc_folder):
                downloaded_rfc_files = ma_machine.get_files_in_path(rfc_folder)
                self.log.info('Downloaded RFC files are %s at %s', downloaded_rfc_files, rfc_folder)
                if len(downloaded_rfc_files) != 0:
                    self.log.info(' RFC folder is restored at %s to complete download for live browse', rfc_folder)
                else:
                    raise Exception(f' Downloaded RFC folder has no RFC files at {rfc_folder}')
            else:
                raise Exception('Failed to verify download operation')

    def switch_datapaths_change_is(self, keep_same, change_both=False):
        """To switch between the datapaths for Index server and snap copy MA
                Args:
                    keep_same   (boolean)           --  true if both the index server and snap copy MA are to be kept
                                                        the same

                    change_both (boolean)           --  true if both the index server and snap copy MA have to be
                                                        changed. default: False
        """

        ma_index_server = self.keep_same_is_for_all_vms()
        self.log.info('Current Index Server MA is %s', ma_index_server)
        ma_snap_copy = self.sp_snap_copy.media_agent
        self.log.info('Current Primary Snap Copy MA is %s', ma_snap_copy)

        if keep_same:
            self.log.info('Checking if both the index server and snap copy MA as same')
            if ma_snap_copy != ma_index_server:
                self.log.info('Changing the snap copy MA to make it same as the index server')
                self.idx_tc.rotate_default_data_path(storage_policy_copy=self.sp_snap_copy)
            else:
                if change_both:
                    self.log.info('Changing both index server and snap copy MA when both are already same')
                    self.idx_tc.rotate_default_data_path(storage_policy_copy=self.sp_snap_copy)
                    ma_snap_copy = self.sp_snap_copy.media_agent
                    cl_snap_copy = self.auto_commcell.commcell.clients.get(ma_snap_copy)
                    for each in self.vm_backupsets:
                        each.index_server = cl_snap_copy
        else:
            self.log.info('Both the index server and snap copy MA have to be different')
            if ma_snap_copy == ma_index_server:
                self.log.info('Changing the snap copy MA to make it different from index server')
                self.idx_tc.rotate_default_data_path(storage_policy_copy=self.sp_snap_copy)

        ma_snap_copy = self.sp_snap_copy.media_agent
        self.log.info('New Primary Snap Copy MA is %s', ma_snap_copy)
        time.sleep(60)
        for each in self.vm_backupsets:
            each.refresh()
        ma_index_server = self.vm_backupsets[0].index_server.name
        self.log.info('New Index Server MA is %s', ma_index_server)

        self.log.info('Initializing index and snap copy MA machines')
        if ma_snap_copy not in self.rfc_servers:
            snap_copy_ma_machine = Machine(ma_snap_copy, self.commcell)
            self.rfc_servers[ma_snap_copy] = snap_copy_ma_machine
        else:
            snap_copy_ma_machine = self.rfc_servers.get(ma_snap_copy)

        if ma_index_server not in self.rfc_servers:
            is_machine = Machine(ma_index_server, self.commcell)
            self.rfc_servers[ma_index_server] = is_machine
        else:
            is_machine = self.rfc_servers.get(ma_index_server)

        return is_machine, snap_copy_ma_machine

    def keep_same_is_for_all_vms(self):
        """To assign the same index server for all the VMs that are to be backed up"""
        self.log.info('Keeping the index server same for the VM backupsets')
        index_server_clients = []
        for each in self.vm_backupsets:
            each.refresh()
            index_server_clients.append(each.index_server.client_name)
        if len(set(index_server_clients)) == 1:
            ma_index_server = index_server_clients[0]
        else:
            index_client = self.auto_commcell.commcell.clients.get(index_server_clients[0])
            for each in self.vm_backupsets:
                each.index_server = index_client
            for each in self.vm_backupsets:
                each.refresh()
            ma_index_server = self.vm_backupsets[0].index_server.client_name

        return ma_index_server
