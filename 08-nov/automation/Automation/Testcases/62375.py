# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

     This Testcase verifies all the RFC operations for a VSA streaming backup

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    run_backup()                                -- Runs VSA backup

    check_for_rfc_backup()                      -- Checks if RFC files have been backed up by checking the
                                                   presence of valid rfc afile for the job.

    vm_sc_info_from_parent_job()                -- To create a mapping of VM subclient to it's child jobs

    verify_rfc_upload()                         -- Fetches the rfc server for the job and verifies
                                                   the RFC upload on the server

    get_rfc_folder_path_list()                  -- RFC folder paths list of parent and child jobs on the rfc server

    verify_rfc_download()                       -- Does a live browse and verifies the download of rfc

    validate_rfc_operations()                   -- Verifies all RFC operations at once

    delete_sc_rfc_folders()                     -- Deletes the VM subclient rfc folders

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from Indexing.validation.vsa_features import VSAFeatures


class TestCase(CVTestCase):
    """
    This Testcase verifies that all  the RFC operations for a VSA streaming backup

    Steps:
        1. Have backupset and subclient.
        2. Run a streaming VSA backup job
        3. Verify the upload of files in parent and child RFC folder
        4. Verify the backup of RFC files from each child job.
        5. Delete the RFC cache of the child job and do a live browse.
        6. Verify the download of the child RFC folder from RFC afile.
        7. Run a series of INC and SFULL jobs
        7. Verify RFC upload, backup and download for each job.

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - RFC - VSA Streaming Backup'
        self.tcinputs = {}
        self.idx_help = None
        self.rfc_server_machine = None
        self.storage_policy = None
        self.sp_primary_copy = None
        self.idx_vsa = None
        self.auto_subclient = None
        self.vsa_sc_guid = None
        self.vm_guid_sc_guid = {}
        self.default_ma_machine = None
        self.sc_level_rfc_folders = []

        self._sc_vms = None
        self._cv_vms = {}
        self.rfc_servers = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.idx_help = IndexingHelpers(self.commcell)
        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

        storage_policy_name = self.auto_subclient.subclient.storage_policy
        self.storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        self.sp_primary_copy = self.storage_policy.get_primary_copy()

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
                vm_subclient = vm_client_info['subclient']
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

            self.delete_sc_rfc_folders()

            self.log.info('********** Running CYCLE 1 INCREMENTAL 2 backup **********')
            inc2_job = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(parent_job=inc2_job)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            sfull1_job = self.run_backup(backup_level='SYNTHETIC_FULL')
            self.validate_rfc_operations(parent_job=sfull1_job)

            self.delete_sc_rfc_folders()

            self.log.info('********** Running CYCLE 2 INCREMENTAL 1 backup **********')
            inc3_job = self.run_backup(backup_level='INCREMENTAL')
            self.validate_rfc_operations(parent_job=inc3_job)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            sfull2_job = self.run_backup(backup_level='SYNTHETIC_FULL')
            self.validate_rfc_operations(parent_job=sfull2_job)

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
            # If the VM is linux/unix rfc is not uploaded at all
            if self.idx_vsa.vms[vm_name]['type'] == 'windows':
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
        """ RFC folder paths list of parent and child jobs on the rfc server
            Args:
                    rfc_server_machine  (obj)  --    rfc server of the job

                    job_id              (str)  --   job id

                    sc_guid             (str)  --   subclient guid

            Returns:
                    (list)      --     List of paths of the RFC folder for both parent and child VSA jobs
        """

        rfc_ma = self.commcell.media_agents.get(rfc_server_machine.machine_name)
        rfc_folder_path = rfc_server_machine.join_path(rfc_ma.index_cache_path, 'RemoteFileCache',
                                                       str(self.commcell.commcell_id), sc_guid,
                                                       job_id)
        self.log.info('RFC folder path for the job: %s is %s', job_id, rfc_folder_path)

        return rfc_folder_path

    def verify_rfc_download(self, vm_sc_guid, child_job_id, job_id_vm_name):
        """ Does a live browse and verifies the download of rfc

                Args:
                        vm_sc_guid     (str)  --   subclient guid of the VM

                        child_job_id   (str)  --   child job id of the VM

                         job_id_vm_name (dict) --   mapping of child job and vm name
        """
        vm_name = job_id_vm_name.get(child_job_id)
        self.log.info(' Verify download of the child rfc folders on ma: %s', self.default_ma_machine.machine_name)
        rfc_folder = self.get_rfc_folder_path(self.default_ma_machine, child_job_id, vm_sc_guid)

        if not self.default_ma_machine.check_directory_exists(rfc_folder):
            self.log.info('RFC folder at %s on this ma is not present', rfc_folder)
        else:
            self.default_ma_machine.remove_directory(rfc_folder)
            self.log.info('Deleting the existing folder %s', rfc_folder)

        self.log.info('Doing guest browse to verify download of child job RFC')
        try:
            self.auto_subclient.subclient.guest_files_browse(
                vm_path=f'\\{vm_name}'
            )
        except Exception:
            self.log.info('Live browse is taking time to fetch results, avoiding the time out error')

        if self.default_ma_machine.check_directory_exists(rfc_folder):
            downloaded_rfc_files = self.default_ma_machine.get_files_in_path(rfc_folder)
            self.log.info('Downloaded RFC files are %s at %s', downloaded_rfc_files, rfc_folder)
            if len(downloaded_rfc_files) != 0:
                self.log.info(' RFC folder is restored at %s to complete download for live browse', rfc_folder)
            else:
                raise Exception(f' Downloaded RFC folder has no RFC files at {rfc_folder}')
        else:
            raise Exception('Failed to verify download operation')

    def validate_rfc_operations(self, parent_job):
        """ Verifies all RFC operations at once

                Args:
                    parent_job (obj)     -- Job object of the parent job

                Returns:

                    (list)               -- list of child RFC folders

        """

        rfc_folder_path_list = []
        parent_job_id = parent_job.job_id
        vm_guid_job_info, job_id_vm_name = self.vm_sc_info_from_parent_job(parent_job=parent_job)
        if parent_job.backup_level != 'Synthetic Full':
            self.verify_rfc_upload(job_id=parent_job_id, sc_guid=self.vsa_sc_guid)
        if vm_guid_job_info:
            for child_job in vm_guid_job_info:
                rfc_folder = self.get_rfc_folder_path(self.default_ma_machine, child_job,
                                                      vm_guid_job_info.get(child_job))
                rfc_folder_path_list.append(rfc_folder)
                self.verify_rfc_upload(job_id=child_job, sc_guid=vm_guid_job_info[child_job])
                self.idx_help.verify_rfc_backup(job_id=child_job)
                self.verify_rfc_download(
                    vm_sc_guid=vm_guid_job_info[child_job],
                    child_job_id=child_job,
                    job_id_vm_name=job_id_vm_name
                )
        else:
            raise Exception('No VMs have been backed up')

        return rfc_folder_path_list

    def delete_sc_rfc_folders(self):
        """ Deletes the vm subclient rfc folders """
        for rfc_folder in self.sc_level_rfc_folders:
            if self.default_ma_machine.check_directory_exists(rfc_folder):
                self.default_ma_machine.remove_directory(rfc_folder)
                self.log.info('Deleting the existing folder at SC level %s', rfc_folder)
