# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

     This Testcase verifies if the RFC restore honors the copy precedence that's set
     and the copy's MA is being used as the RFC server during the browse

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

    delete_sc_rfc_folders()                     -- Deletes the VM subclient rfc folders

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from Indexing.validation.vsa_features import VSAFeatures


class TestCase(CVTestCase):
    """
    This Testcase verifies if the RFC restore honors the copy precedence that's set
    and the copy's MA is being used as the RFC server during the browse

    Steps:
        1. Have a backupset, subclient and run a Snap Backup (FULL)
        2. Verify the upload of parent and child RFC folder.
        3. Verify the backup of RFC (validate RFC afile)
        4. Verify the download of RFC files needed for backup copy by checking for backup copy job.
        5. Verfiy the upload of backup copy RFC folder
        6. Do live browse with an MA set, verify that RFC operations are taken care by hat machine.
        7. RFC restore should honor the copy precedence and that copy's MA should act as the RFC server.

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - RFC - Validation of Browse and RFC Restore based on Copy Precedence'
        self.tcinputs = {}
        self.idx_help = None
        self.rfc_server_machine = None
        self.storage_policy = None
        self.sp_primary_copy = None
        self.sp_secondary_copy = None
        self.secondary_copy_precedence = None
        self.secondary_copy_ma_machine = None
        self.idx_vsa = None
        self.auto_subclient = None
        self.auto_commcell = None
        self.vsa_sc_guid = None
        self.vm_guid_sc_guid = {}
        self.default_ma_machine = None
        self.common_utils = None
        self.sc_level_rfc_folders = []

        self._sc_vms = None
        self._cv_vms = {}
        self.rfc_servers = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.idx_help = IndexingHelpers(self.commcell)
        self.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(self.auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

        self.common_utils = CommonUtils(self.commcell)

        storage_policy_name = self.auto_subclient.subclient.storage_policy
        self.storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        self.sp_primary_copy = self.storage_policy.get_primary_copy()
        self.sp_secondary_copy = self.storage_policy.get_secondary_copies()[0]

        self.idx_vsa = VSAFeatures(self.auto_subclient, self)
        self.idx_vsa.initialize_vms()

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('********** Running FULL backup **********')
            full_job = self.run_backup(backup_level='FULL')

            self.log.info('Getting the primary copy MA where RFC files will be downloaded')
            ma_for_download = self.sp_primary_copy.media_agent
            self.log.info('MA for RFC download is %s', ma_for_download)
            if ma_for_download not in self.rfc_servers:
                self.default_ma_machine = Machine(ma_for_download, self.commcell)
                self.rfc_servers[ma_for_download] = self.default_ma_machine
            else:
                self.default_ma_machine = self.rfc_servers.get(ma_for_download)

            self.vsa_sc_guid = self.auto_subclient.subclient.subclient_guid
            self.log.info('VSA subclient GUID is %s', self.vsa_sc_guid)

            for each_vm in self.idx_vsa.vm_guids:
                vm_client_info = self.idx_vsa.get_cv_vm_client(vm_guid=each_vm)
                vm_subclient = vm_client_info.get('subclient')
                vm_sc_guid = vm_subclient.subclient_guid
                self.log.info('VM SC guid is %s', vm_sc_guid)
                self.vm_guid_sc_guid[each_vm] = vm_sc_guid

            self.log.info('VM guid to VM sc guid mapping is %s', self.vm_guid_sc_guid)

            rfc_folders_list = self.validate_rfc_operations(parent_job=full_job)

            for each_folder in rfc_folders_list:
                rfc_folder = each_folder.rsplit(self.default_ma_machine.os_sep, 1)[0]
                self.sc_level_rfc_folders.append(rfc_folder)

            self.delete_sc_rfc_folders()
            self.log.info('********** Running CYCLE 1 INCREMENTAL 1 backup **********')
            inc1_job = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(parent_job=inc1_job)

            secondary_copy_name = self.sp_secondary_copy.copy_name
            self.secondary_copy_precedence = self.sp_secondary_copy.copy_precedence
            secondary_copy_ma = self.sp_secondary_copy.media_agent
            self.secondary_copy_ma_machine = Machine(secondary_copy_ma, self.commcell)

            self.log.info('********* Running Aux Copy Job **********')
            self.storage_policy.run_aux_copy(storage_policy_copy_name=secondary_copy_name, all_copies=False)

            self.delete_sc_rfc_folders()
            self.log.info('********** Running CYCLE 1 INCREMENTAL 2 backup **********')
            inc2_job = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(parent_job=inc2_job)

            # To verify the download of RFC using browse based on copy precedence
            self.validate_rfc_operations(parent_job=inc1_job, verify_only_download=True)

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

        vm_sc_guid_job_info = dict()
        job_id_vm_name = dict()
        self.log.info('Parent job details [%s]', parent_job.details)
        vm_details = parent_job.details['jobDetail']['clientStatusInfo']['vmStatus']
        self.log.info(vm_details)
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
        return vm_sc_guid_job_info, job_id_vm_name

    def verify_rfc_upload(self, job_id, sc_guid):
        """ Fetches the rfc server for the job and verifies the RFC upload on the server

                Args:
                           job_id           (str)   --   Job ID of the job for which RFC upload has to be verified

                           sc_guid         (str)    --  subclient guid of the subclient who's RFC has to be verified

        """

        rfc_server = self.idx_help.get_rfc_server(job_id=job_id)
        rfc_server_name = rfc_server.name
        self.log.info('RFC server for the job: %s is %s', job_id, rfc_server_name)
        if rfc_server_name not in self.rfc_servers:
            rfc_server_machine = Machine(rfc_server_name, self.commcell)
            self.rfc_servers[rfc_server_name] = rfc_server_machine
        else:
            rfc_server_machine = self.rfc_servers.get(rfc_server_name)

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

    def verify_rfc_download(self, vm_sc_guid, child_job_id, job_id_vm_name, ma_machine=None, sp_copy_precedence=0):
        """ Does a live browse and verifies the download of rfc

                Args:
                        vm_sc_guid        (str)  --   subclient guid of the VM

                        child_job_id      (str)  --   child job id of the VM

                        job_id_vm_name    (dict) --   mapping of child job and vm name

                        ma_machine        (obj)  --   Machine object of the MA used for browse

                        sp_copy_precedence (int) -- copy precedence of the storage policy from which browse
                                                    is to be done

        """
        if not ma_machine:
            ma_machine = self.default_ma_machine
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
                    vm_path=f'\\{vm_name}',
                    copy_precedence=sp_copy_precedence
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

    def validate_rfc_operations(self, parent_job, verify_only_download=False):
        """ Verifies all RFC operations at once

                Args:
                    parent_job (obj)               -- Job object of the parent job

                    verify_only_download(boolean)  -- true if only RFC download has to be verified
                                                      (default : False)
                Returns:

                    (list)               -- list of child RFC folders

        """
        rfc_folder_path_list = []
        parent_job_id = parent_job.job_id
        vm_guid_job_info, job_id_vm_name = self.vm_sc_info_from_parent_job(parent_job=parent_job)
        if not verify_only_download:
            if parent_job.backup_level != 'Synthetic Full':
                self.verify_rfc_upload(job_id=parent_job_id, sc_guid=self.vsa_sc_guid)
            if vm_guid_job_info:
                for child_job in vm_guid_job_info:
                    rfc_folder = self.get_rfc_folder_path(self.default_ma_machine, child_job, vm_guid_job_info.get(child_job))
                    rfc_folder_path_list.append(rfc_folder)
                    self.verify_rfc_upload(job_id=child_job, sc_guid=vm_guid_job_info.get(child_job))
                    # first rfc afile created after the snap job
                    self.idx_help.verify_rfc_backup(job_id=child_job)

                if parent_job.backup_level != 'Synthetic Full':
                    self.verify_rfc_download_from_backup_copy(rfc_folder_list=rfc_folder_path_list)
                    backup_copy_job_id = self.common_utils.get_backup_copy_job_id(snap_job_id=parent_job_id)
                    self.verify_rfc_upload(job_id=backup_copy_job_id, sc_guid=self.vsa_sc_guid)

                for child_job in vm_guid_job_info:
                    # second rfc afile created after the backup copy job
                    self.idx_help.verify_rfc_backup(job_id=child_job)
                    self.verify_rfc_download(
                        vm_sc_guid=vm_guid_job_info.get(child_job),
                        child_job_id=child_job,
                        job_id_vm_name=job_id_vm_name
                    )
            else:
                raise Exception('No VMs have been backed up')
        else:
            if vm_guid_job_info:
                for child_job in vm_guid_job_info:
                    self.idx_help.verify_rfc_backup(job_id=child_job)
                    self.verify_rfc_download(
                        vm_sc_guid=vm_guid_job_info.get(child_job),
                        child_job_id=child_job,
                        job_id_vm_name=job_id_vm_name,
                        ma_machine=self.secondary_copy_ma_machine,
                        sp_copy_precedence=self.secondary_copy_precedence
                    )
            else:
                raise Exception('No VMs have been backed up')

        return rfc_folder_path_list

    def verify_rfc_download_from_backup_copy(self, rfc_folder_list):
        """ Verifies RFC download upon running a backup copy

                        Args:
                            rfc_folder_list (list)     -- List of rfc path to be downloaded upon running a backup copy

                """

        self.log.info(' Verify download of the child rfc folders on ma: %s using backup copy',
                      self.default_ma_machine.machine_name)
        for rfc_folder in rfc_folder_list:
            if not self.default_ma_machine.check_directory_exists(rfc_folder):
                self.log.info('RFC folder at %s on this ma is not present', rfc_folder)
            else:
                self.default_ma_machine.remove_directory(rfc_folder)
                self.log.info('Deleting the existing folder %s', rfc_folder)

        self.log.info('Running backup copy to verify download of child job RFC')
        backup_copy_job = self.storage_policy.run_backup_copy()
        self.log.info('Backup copy job id is %s', backup_copy_job.job_id)
        if not backup_copy_job.wait_for_completion():
            raise Exception(f'Backup copy job: {backup_copy_job.job_id} failed at the end')

        for rfc_folder in rfc_folder_list:
            if self.default_ma_machine.check_directory_exists(rfc_folder):
                downloaded_rfc_files = self.default_ma_machine.get_files_in_path(rfc_folder)
                self.log.info('Downloaded RFC files are %s at %s', downloaded_rfc_files, rfc_folder)
                if len(downloaded_rfc_files) != 0:
                    self.log.info(' RFC folder is restored at %s to complete download for live browse', rfc_folder)
                else:
                    raise Exception(f' Downloaded RFC folder has no RFC files at {rfc_folder}')
            else:
                raise Exception('Failed to verify download operation')

    def delete_sc_rfc_folders(self):
        """ Deletes the vm subclient rfc folders """
        for rfc_folder in self.sc_level_rfc_folders:
            if self.default_ma_machine.check_directory_exists(rfc_folder):
                self.default_ma_machine.remove_directory(rfc_folder)
                self.log.info('Deleting the existing folder at SC level %s', rfc_folder)