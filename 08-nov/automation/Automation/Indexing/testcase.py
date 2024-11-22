#  -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""IndexingTestcase: Helper class which has methods which are frequently used in indexing testcases

IndexingTestcase:

    __init__()              --  Initializes the Indexing testcase helper class

    create_backupset()      --  Creates a backupset under the testcase client and File system IDA

    create_subclient()      --  Creates a subclient under the given backupset with a random
    directory created as subclient content

    new_testdata()          --  Generates new testdata in the paths provided

    edit_testdata()         --  Modifies testdata in the paths provided

    copy_testdata()         --  Copies the given folder to the paths provided

    create_only_files()     --  Creates only files under the given directory.

    edit_files()            --  Edits the data of the given files

    run_backup()            --  Runs a backup job and adds the job to Indexing validation

    run_backup_sequence()   --  Runs a sequence of backup-jobs and data-generation operations

    run_interrupt_job()     --  Runs a backup job and interrupts it like suspend and resume / kill

    verify_browse_restore() --  Validates browse and restore using the Validation class

    verify_job_find_results()-- Validates job based find results using the Validation class

    verify_item_permissions()-- Validates job based find results using the Validation class

    verify_synthetic_full_job()  --  Verifies various checks after a synthetic full job is complete

    get_total_folder_size_disk() --  Gets the total folder size of the given directory paths

    get_last_job()          --  Gets the latest job for the given subclient

    get_backup_jobs_stats() --  Gets the list of backup jobs from JmBkpStats table for the given entity

    check_log_line()        --  Reads the log file and checks if any line is found with the
    specified words

    rotate_default_data_path()  --  Changes the default datapath of the storage policy primary copy

    log_section()           --  Logs a line to indicate the start of a section

"""

import random
import time
import re

from AutomationUtils import commonutils
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.idautils import CommonUtils

from Indexing.validation.fs_browse_restore import FSBrowseRestore
from Indexing.misc import MetallicConfig

from Server.JobManager.jobmanager_helper import JobManager

from cvpysdk.job import Job
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient


class IndexingTestcase(object):
    """Helper class which has methods which are frequently used in indexing testcases"""

    def __init__(self, testcase_obj):
        """Initializes the Indexing testcase helper class"""

        self.tc = testcase_obj
        self.log = self.tc.log
        self.commcell = self.tc.commcell

        self._client = None
        self._client_name = None
        self._agent = None
        self._agent_name = None
        self._cl_machine = None
        self._cl_delim = None

        metallic = MetallicConfig(self.commcell)
        admin_cc = self.commcell
        if metallic.is_configured:
            testcase_obj.csdb = metallic.csdb
            admin_cc = metallic.metallic_admin_cc

        if self.tc._client is not None:
            self.client = self.tc.client
            self.agent = self.tc.agent
            self.cl_machine = self.tc.cl_machine

        self.cv_entities = CVEntities(self.commcell)
        self.cv_ops = CommonUtils(self.commcell)
        self.options_help = OptionsSelector(admin_cc)

        self.debug = True if hasattr(self.tc, 'debug') else False

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value
        self._client_name = value.client_name

    @property
    def agent(self):
        return self._agent

    @agent.setter
    def agent(self, value):
        self._agent = value
        self._agent_name = value.agent_name

    @property
    def cl_machine(self):
        return self._cl_machine

    @cl_machine.setter
    def cl_machine(self, value):
        self._cl_machine = value
        self._cl_delim = value.os_sep

    def _generate_random_items(self, path, **kwargs):
        """Generate random items under the given folder"""

        self.log.info('Creating random files [{0}]'.format(path))

        random_dir = self._cl_delim.join([path, 'random_dir'])
        self.cl_machine.generate_test_data(random_dir, **kwargs)

    def _generate_tracked_items(self, path, base_dir='tracked_dir', count=2, size=(1024, 1024)):
        """Generate items with a pattern under the given folder"""

        self.log.info('Creating tracking files under [{0}] in [{1}]'.format(base_dir, path))

        tracked_dir = self._cl_delim.join([path, base_dir])
        self.cl_machine.create_directory(tracked_dir)

        for i in range(count):
            file_name = 'edit_file-' + str(i + 1) + '.txt'
            file_path = self._cl_delim.join([tracked_dir, file_name])
            file_size = random.randint(*size)
            self.cl_machine.create_file(file_path, '1', file_size)

        for i in range(count):
            rand_id = commonutils.get_random_string(5, digits=False)
            file_name = 'delete_file_' + rand_id + '-1.ini'
            file_path = self._cl_delim.join([tracked_dir, file_name])
            file_size = random.randint(*size)
            self.cl_machine.create_file(file_path, '1', file_size)

        to_rc_file = self._cl_delim.join([tracked_dir, 'recreate_file'])
        file_size = random.randint(*size)
        self.cl_machine.create_file(to_rc_file, '1', file_size)

        for i in range(count):
            rand_id = commonutils.get_random_string(5, digits=False)
            to_delete_dir = self._cl_delim.join([tracked_dir, 'delete_dir_' + rand_id + '-1'])
            dir_file = self._cl_delim.join([to_delete_dir, 'dummy_file.txt'])
            file_size = random.randint(*size)
            self.cl_machine.create_directory(to_delete_dir)
            self.cl_machine.create_file(dir_file, '1', file_size)

    def _edit_random_items(self, path):
        """Randomly delete, edit files under the given folder"""

        random_dir = self._cl_delim.join([path, 'random_dir'])

        self.log.info('Modifying random files in path [{0}]'.format(random_dir))

        content = str(random.randint(1, 9)) * 1024
        all_files = self.cl_machine.scan_directory(
            random_dir, filter_type='file', recursive=True)

        random.shuffle(all_files)

        if len(all_files) < 5:
            self.log.info('Sufficient items are not available in directory to edit')
            return

        file_to_delete = all_files.pop()
        self.cl_machine.delete_file(file_to_delete['path'])

        file_to_edit = all_files.pop()
        self.cl_machine.append_to_file(file_to_edit['path'], content)

        rand_id = commonutils.get_random_string(10, digits=False)
        file_to_create = self._cl_delim.join([random_dir, rand_id])
        self.cl_machine.create_file(file_to_create, content)

        file_to_delete_split = file_to_delete['path'].split(self._cl_delim)
        file_to_delete_split.pop()
        file_to_delete_split.append(commonutils.get_random_string(10, digits=False))
        new_file_path = self._cl_delim.join(file_to_delete_split)
        self.cl_machine.create_file(new_file_path, content)

    def _edit_tracked_items(self, path, base_dir='tracked_dir'):
        """Edits items in the given path like below

            1) Edit files (by appending content)
            2) Add & Delete items (by renaming the item name)
            3) Recreate item by renaming the item like it was before

        """

        tracked_dir = self._cl_delim.join([path, base_dir])

        self.log.info('Modifying tracked items in path [{0}]'.format(tracked_dir))

        content = str(random.randint(1, 9)) * 1024
        all_files = self.cl_machine.scan_directory(
            tracked_dir, filter_type='file', recursive=False)

        for file in all_files:
            file_path = file['path']

            if 'edit_file' in file_path:
                self.cl_machine.append_to_file(file_path, content)

            if 'delete_file' in file_path:
                new_file_path = self._rename_item_increment_id(file_path)
                self.cl_machine.append_to_file(new_file_path, content)

            if 'recreate_file' in file_path:
                if file_path[-3:] == '-rn':
                    self.cl_machine.rename_file_or_folder(file_path, file_path[:-3])
                    self.cl_machine.append_to_file(file_path[:-3], content)
                else:
                    self.cl_machine.rename_file_or_folder(file_path, file_path + '-rn')
                    self.cl_machine.append_to_file(file_path + '-rn', content)

        all_dirs = self.cl_machine.scan_directory(
            tracked_dir, filter_type='directory', recursive=False)

        for directory in all_dirs:
            dir_path = directory['path']

            if 'delete_dir' in dir_path:
                self._rename_item_increment_id(dir_path)

    def _rename_item_increment_id(self, item_path):
        """Renames the file/folder by incrementing the ID present in the item name"""

        path_items = item_path.split(self._cl_delim)
        dir_path = self._cl_delim.join(path_items[:-1])
        item_name = path_items[-1]
        item_id = int(re.findall('\d+', item_name)[0])
        new_item_name = item_name.replace(str(item_id), str(item_id + 1))
        new_item_path = self._cl_delim.join([dir_path, new_item_name])
        self.cl_machine.rename_file_or_folder(item_path, new_item_path)

        return new_item_path

    def create_backupset(self, name, for_validation=True):
        """Creates a backupset under the testcase client and File system IDA

            Args:
                name    (str)       --  Name of the backupset to create

                for_validation  (bool)  --  Create the indexing validation DB once backupset
                is created automatically

            Returns:
                The CvPySDK backupset object

        """

        bkset_props = self.cv_entities.create({
            'backupset': {
                'name': name,
                'client': self._client_name,
                'agent': self._agent_name,
                'instance': 'defaultinstancename'
            }
        })

        bkset_obj = bkset_props['backupset']['object']

        if for_validation:
            bkset_obj.idx = FSBrowseRestore({
                'commcell': self.commcell,
                'backupset': bkset_obj,
                'debug': self.debug
            })

        return bkset_obj

    def create_subclient(self, name, backupset_obj, storage_policy, content=None,
                         register_idx=True, delete_existing_testdata=True):
        """Creates a subclient under the given backupset with a random directory created as
        subclient content

            Args:
                name       (str)        --  Name of the subclient

                backupset_obj  (obj)   --  The backupset pySDK object

                storage_policy (str)   --  Name of the storage policy

                content     (list)     --  Testdata content path of the subclient. Content path
                will be automatically created if None

                register_idx    (bool)   --  Register the subclient with the indexing
                validation object

                delete_existing_testdata (bool) --  Deletes the backupset directory created if True else reuses
                the backupset directory

            Returns:
                The CvPySDK subclient object

        """

        bkset_name = backupset_obj.backupset_name

        if content is None:
            testdata_path = self.tc.tcinputs.get('TestDataPath', None)

            if testdata_path is None:
                self.log.info('No testdata path provided, choosing testdata path automatically')
                free_drive = self.options_help.get_drive(self.cl_machine)
                free_drive = commonutils.remove_trailing_sep(free_drive, self._cl_delim)
                testdata_path = self._cl_delim.join([free_drive, 'automation', 'testdata'])

            testdata_path = testdata_path.split(';')

            self.log.info('Base testdata path {0}'.format(testdata_path))

            bkset_paths = [self._cl_delim.join([path, bkset_name])
                           for path in testdata_path]

            if delete_existing_testdata:
                for path in bkset_paths:
                    if self.cl_machine.check_directory_exists(path):
                        self.log.info('Deleting previous testdata directory [{0}]'.format(path))
                        self.cl_machine.remove_directory(path)

            content = []
            for path in bkset_paths:
                rand_id = commonutils.get_random_string(3)
                dir_name = name + '_' + rand_id
                content.append(self._cl_delim.join([path, dir_name]))

        sc_props = self.cv_entities.create({
            'subclient': {
                'name': name,
                'client': self._client_name,
                'agent': self._agent_name,
                'instance': 'defaultinstancename',
                'backupset': bkset_name,
                'storagepolicy': storage_policy,
                'content': content,
                'description': self.tc.id
            }
        })

        subclient_obj = sc_props['subclient']['object']
        subclient_obj.scan_type = 1

        try:
            # Setting default cycles to 2 for subclient level index
            if 'indexSettings' in subclient_obj._commonProperties:
                self.log.info('Setting default cycles retention to [2] cycles for subclient [%s]', subclient_obj.name)
                subclient_obj.index_pruning_cycles_retention = 2
        except Exception as e:
            self.log.error('Failed to set default index pruning cycles retention [%s]', e)

        if hasattr(backupset_obj, 'idx') and register_idx:
            self.log.info('Indexing validation - Registering subclient [{0}]'.format(name))
            backupset_obj.idx.register_subclient(subclient_obj)
            subclient_obj.idx = backupset_obj.idx

        return subclient_obj

    def new_testdata(self, paths, large_files=None, count=2, **kwargs):
        """Generates new testdata in the paths provided.

            - One folder where random items are generated
            - Tracked folder where items are generated in pattern for editing later

            Args:
                paths       (list)  --  List of the paths under which data will be generated

                large_files (tuple) --  Generate large files with range of file size as
                the parameter. E.g: (10240000, 20480000) creates large files with random file size
                between 10MB and 20 MB

                count       (int)   --  Number of tracked files to be created

                **kwargs    --  All the arguments supported by machine.generate_test_data method

            Returns:
                None

            Raises:
                Exception, if any file/dir creation failed in machine.generate_test_data

        """

        if isinstance(paths, str):
            paths = [paths]

        for path in paths:

            self._generate_random_items(path, **kwargs)

            self._generate_tracked_items(path, base_dir='tracked_dir', count=count)

            if large_files is not None:
                self._generate_tracked_items(
                    path, base_dir='large_files_dir', size=large_files, count=count)

    def edit_testdata(self, paths):
        """Modifies testdata in the paths provided.

            Args:
                paths       (list)  --  List of the paths under which data will be generated

            Returns:
                None

            Raises:
                Exception, if any file/dir creation failed in machine.modify_test_data

        """

        if isinstance(paths, str):
            paths = [paths]

        for path in paths:

            self._edit_random_items(path)

            self._edit_tracked_items(path, base_dir='tracked_dir')

            large_files_dir = self._cl_delim.join([path, 'large_files_dir'])
            if self.cl_machine.check_directory_exists(large_files_dir):
                self._edit_tracked_items(path, base_dir='large_files_dir')

    def copy_testdata(self, paths, copy_data_folder):
        """Copies the given folder to the paths provided

            Args:
                paths            (list)  --  List of the paths under which the folder has to be copied

                copy_data_folder (str)   --  The path of the folder to copy data from

            Returns:
                None

        """

        self.log.info(
            'Size of copy folder [%s] is [%s] bytes',
            copy_data_folder,
            self.cl_machine.get_folder_size(copy_data_folder)
        )

        for path in paths:
            self.log.info('Copying folder [%s] to [%s]', copy_data_folder, path)
            self.cl_machine.copy_folder(copy_data_folder, path)

    def create_only_files(self, paths, count=10, name='test_file',
                          size=(1024, 10240), base_dir=None, extensions=None):
        """Creates only files under the given directory.

            Args:
                paths       (list/str)  --  List of folders or single folder to create files under

                count       (int)       --  Number of files to create

                name        (str)       --  Name of the files

                size        (tuple)     --  Tuple which contains the min and max size of the files

                base_dir    (str)       --  When set, all files will be created under this folder

                extensions  (list)      --  List of extensions to use for the file (without dot)

            Returns:
                None

        """

        if isinstance(paths, str):
            paths = [paths]

        if not isinstance(extensions, list):
            extensions = ['txt', 'ini']

        for path in paths:

            if base_dir is not None:
                dir_path = self._cl_delim.join([path, base_dir])
                try:
                    self.cl_machine.create_directory(dir_path)
                except Exception as e:
                    self.log.error(e)
            else:
                dir_path = path

            for i in range(1, count + 1):
                file_ext = random.choice(extensions)
                file_name = f'{name}_{i:04d}.{file_ext}'
                file_paths = [dir_path, file_name]
                file_path = self._cl_delim.join(file_paths)
                file_size = random.randint(*size)
                self.cl_machine.create_file(file_path, '1', file_size)

    def edit_files(self, paths, content=None):
        """Edits the data of the given files

            Args:
                paths       (list/str)  --  List of files to edit

                content     (str)       --  The content to append to the file

            Returns:
                None

        """

        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            file_content = time.time() if content is None else content
            self.cl_machine.append_to_file(path, file_content)

    def run_backup(self, subclient_obj, backup_level='Incremental', verify_backup=True,
                   restore=False, **kwargs):
        """Runs a backup job and adds the job to Indexing validation

            Args:
                subclient_obj   (obj)   --  The subclient cvpysdk object

                backup_level    (str)   --  The backup level of the backup job

                verify_backup   (bool)  --  To verify find results of the job after backup job

                restore         (bool)  --  To do restore and verify restore results

        """

        obj = self.cv_ops.subclient_backup(subclient_obj, backup_level, **kwargs)

        if isinstance(obj, Job):
            if not obj.job_id:
                raise Exception('Backup job did not start as expected')

            if hasattr(subclient_obj, 'idx'):
                copy_id = self.tc.primary_copy_precedence if hasattr(self.tc, 'primary_copy_precedence') else 1

                idx_obj = subclient_obj.idx
                idx_obj.record_job(obj, copy_id)

                if verify_backup:
                    self.verify_job_find_results(obj, idx_obj, restore=restore)

            return obj

        return obj

    def run_backup_sequence(self, subclient_obj, steps, verify_backup=False):
        """Runs a sequence of backup-jobs and data-generation operations

            Args:
                subclient_obj   (obj)   --  The subclient cvpysdk object

                steps    (List(str))    --

                    1 - New - Deleted old test-data and generate new
                    2 - Edit - Edit test-data
                    3 - Full - Full backup
                    4 - Incremental - Incremental backup
                    5 - Synthetic_full - Synthetic full backup

                verify_backup   (bool)  --  To verify find results of the job after backup job

            Returns:

                (List(Job))  -  List of Job objects for backup jobs
        """

        jobs = []
        for step in steps:
            step = step.lower()

            if step == 'new':
                for path in subclient_obj.content:
                    if path == self.cl_machine.os_sep:
                        continue
                    self.cl_machine.remove_directory(directory_name=path)
                self.new_testdata(paths=subclient_obj.content)

            elif step == 'edit':
                self.edit_testdata(paths=subclient_obj.content)

            elif step == 'copy':
                copy_folder = self.tc.tcinputs.get('CopyData')
                if not copy_folder:
                    raise Exception('CopyData input is not present in the testcase to copy data from folder')
                self.copy_testdata(
                    paths=subclient_obj.content,
                    copy_data_folder=copy_folder
                )

            elif step in ['full', 'incremental', 'synthetic_full', 'differential']:
                job = self.run_backup(
                    subclient_obj=subclient_obj, backup_level=step, verify_backup=verify_backup, restore=False)
                jobs.append(job)

        return jobs

    def run_interrupt_job(
            self, subclient_obj, backup_level='Incremental',
            phase='backup', action='suspend_resume', wait=5, verify_backup=True,
            restore=False, **kwargs
    ):
        """Runs a backup job and interrupts it like suspend and resume / kill

            Args:
                subclient_obj   (obj)   --  The CvPySDK subclient object

                backup_level    (str)   --  The backup type to run

                phase           (str)   --  Phase of the backup to interrupt

                action          (str)   --  The interrupt action (suspend_resume/kill)

                wait            (int)   --  The time to wait before interrupt operation

                verify_backup   (bool)  --  To verify find results of the job after backup job

                restore         (bool)  --  To do restore and verify restore results

            Returns:

                job_obj         (obj)   --  The CvPySDK job object if job is still is running

                None     --  If the job is killed

            Raises:

                Exception, if job cannot attain the expected phase

                           if failed to kill job

        """

        action = action.lower()

        if action not in ['suspend_resume', 'kill', 'none']:
            raise Exception('Invalid action for interrupt job')

        job_obj = subclient_obj.backup(backup_level, **kwargs)
        jm_obj = JobManager(job_obj, self.commcell)
        jm_obj.wait_for_phase(phase=phase, total_attempts=120, check_frequency=1)

        if action == 'suspend_resume':

            self.log.info('Job is at [{0}] phase, suspending job in [{1}] seconds'.format(
                phase, wait))

            time.sleep(wait)
            self.log.info('Suspending job')
            job_obj.pause(wait_for_job_to_pause=True)

            self.log.info('Job is suspended, resuming it in [5] minutes')
            time.sleep(300)
            self.log.info('Resuming job')
            job_obj.resume(wait_for_job_to_resume=True)

            self.log.info('Job is resumed, waiting for it to complete')
            jm_obj.wait_for_state('completed')
            self.log.info('Job completed successfully')

            if hasattr(subclient_obj, 'idx'):
                copy_id = self.tc.primary_copy_precedence if hasattr(self.tc, 'primary_copy_precedence') else 1
                idx_obj = subclient_obj.idx
                idx_obj.record_job(job_obj, copy_id)

                if verify_backup:
                    self.verify_job_find_results(job_obj, idx_obj, restore=restore)

            return job_obj

        if action == 'kill':

            self.log.info('Job is at [{0}] phase, killing job in [{1}] seconds'.format(
                phase, wait))

            time.sleep(wait)
            self.log.info('Killing job')

            try:
                job_obj.kill(wait_for_job_to_kill=False)  # For commit operation
                time.sleep(2)
                job_obj.kill(wait_for_job_to_kill=True)  # For killing job
            except Exception:
                self.log.error(
                    'Got exception while killing job. Checking job status and proceeding further')

            if job_obj.status.lower() != 'killed':
                raise Exception('Failed to kill job')
            else:
                self.log.info('Job is killed successfully')

        if action == 'none':
            return job_obj

    @staticmethod
    def verify_browse_restore(backupset_obj, options):
        """Validates browse and restore using the Validation class

            Args:
                backupset_obj   (obj)  --   The backupset object which holds the Indexing
                validation class object

                options         (obj)   --  The browse/find options to validate for. Refer
                default_options in Indexing/validation/fs_browse_restore.py for the default options

            Returns:
                None

            Raises:
                Exception, if validation results failed

        """

        if not hasattr(backupset_obj, 'idx'):
            raise Exception('Backupset object does not have indexing validation object')

        if backupset_obj.idx.validate_browse_restore(options) != 0:
            raise Exception('Validation failed. Please refer mismatch in browse/restore results')

    def verify_job_find_results(self, job_obj, idx_obj=None, restore=False):
        """Validates job based find results using the Validation class

            Args:
                job_obj     (obj)   --      The CvPySDK job object for which find validation has
                to be done

                idx_obj     (obj)   --      The indexing Validation class object

                restore     (bool)  --      To perform restore after validating find results

            Returns:
                None

            Raises:
                Exception, if the find/restore validation results failed

        """

        self.log.info(
            '********** VALIDATING JOB BASED FIND FOR JOB [{0}] **********'.format(
                job_obj.job_id
            ))

        ret_code = idx_obj.validate_browse_restore({
            'job_id': job_obj.job_id,
            'restore': {
                'do': restore
            }
        })

        if ret_code != 0:
            raise Exception(f'Job [{job_obj.job_id}] [{job_obj.backup_level}] has mismatch in backed up items')

    def verify_item_permissions(self, actual_list, exp_list, actual_dir, exp_dir):
        """Verifies file permission for the list of files given.

            Args:
                actual_list     (list/dict)     --  List of full path files to
                verify permission. Example: ['/testdata/abcd']

                exp_list        (list/dict)     --  List of full path files with the
                expected permission. Example: {'/home/restored/abcd': '772'}

                actual_dir      (str)   --  The base directory of the actual
                list items. Example: /testdata

                exp_dir         (str)   --  The base directory of the expected list. Example:
                /home/restored

        """

        items_checked = 0

        exp_list_relative = {}
        for exp_item in exp_list:
            relative_path = exp_item.replace(exp_dir, '')
            exp_list_relative[relative_path] = exp_list[exp_item]

        self.log.info('Expected file permissions: [{0}]'.format(exp_list_relative))

        for item in actual_list:
            item_relative = item.replace(actual_dir, '')
            exp_permission = exp_list_relative.get(item_relative, None)

            if exp_permission is None:
                continue

            actual_permission = self.cl_machine.get_file_permissions(item)
            items_checked += 1

            if actual_permission != exp_permission:
                raise Exception(
                    'Item [{0}] has unexpected permission. Expected [{1}] Actual [{2}]'.format(
                        item, exp_permission, actual_permission
                    ))

        if items_checked != len(actual_list):
            raise Exception('File permission was not checked for some items')

    def verify_synthetic_full_job(self, job_obj, subclient_obj):
        """Verifies various checks like, RFC afile, browse & restore, app size after a synthetic full job is complete

            Args:
                job_obj             (obj)   --  The job object

                subclient_obj       (obj)   --  The subclient object

            Raises:
                Exception:
                    if any of the verification failed

        """

        self.log.info('Verifying SFULL job [%s]', job_obj.job_id)

        self.log.info('********** Checking if RFC afile is created **********')
        if 'windows' in subclient_obj._client_object.os_info.lower():
            self.tc.csdb.execute(
                f"SELECT * FROM archFile WHERE fileType = 7 AND isValid = 1 AND jobId = '{job_obj.job_id}'"
            )
            row = self.tc.csdb.fetch_one_row()
            if not row[0]:
                raise Exception(f'Job [{job_obj.job_id}] did not contain RFC_AFILE')
            self.log.info('RFC afile is created')
        else:
            self.log.warning('***** Client is non-windows. Not checking for RFC afiles *****')

        if hasattr(subclient_obj, 'idx'):
            self.verify_job_find_results(job_obj, subclient_obj.idx, restore=True)
        else:
            self.log.warning('Indexing validation not enabled. Not checking job based browse and restore')

        error_threshold = float(self.tc.tcinputs.get('AppSizeThreshold', 20.0))
        app_size = self.get_application_size(job_obj=job_obj)
        size_on_disk = self.get_total_folder_size_disk(subclient_obj.content)

        self.log.info('Application size of job [%s] bytes', app_size)
        self.log.info('Size of content on disk [%s] bytes', size_on_disk)

        size_diff = (abs(app_size - size_on_disk) / size_on_disk) * 100.0
        self.log.info('Difference [%.2f%%]', size_diff)

        self.log.info('******** Verifying Application Size ********')
        if size_diff > error_threshold:
            raise Exception('Application size and disk size do not match')
        else:
            self.log.info('Application size verified and is under threshold')

    def get_total_folder_size_disk(self, paths):
        """Gets the total folder size of the given directory paths

            Args:
                paths       (str/list)      --      List of directory paths or single folder path

            Returns:
                Total folder size of the give directories

        """

        if isinstance(paths, str):
            paths = [paths]

        total_size = 0

        for path in paths:
            total_size += self.cl_machine.get_folder_size(path, in_bytes=True)

        return total_size

    def get_application_size(self, subclient_obj=None, job_obj=None, cycle_num=None):
        """Gets the application size of the given job id or subclient

            Args:
                subclient_obj   (obj)   --  The subclient object

                job_obj         (obj)   --  The job object

                cycle_num       (int)   --  The cycle number to get total application size for.
                If None, gets the latest cycle application size

            Returns:
                (float) - Total application size for the given entity

        """

        if job_obj is None and subclient_obj is None:
            return None

        total_size = 0

        if job_obj is not None:
            self.tc.csdb.execute(
                "select totalUncompBytes from JMBkpStats where jobid = {0}".format(
                    job_obj.job_id
                ))

            total_size = self.tc.csdb.fetch_one_row()[0]

        if subclient_obj is not None:

            if cycle_num is None:
                cycle_num_val = """(select max(fullCycleNum) 
                from jmbkpstats where appid={0})""".format(subclient_obj.subclient_id)
            else:
                cycle_num_val = cycle_num

            self.tc.csdb.execute(
                """
            select sum(totalUncompBytes) from jmbkpstats
            where appid = {0}
            and fullCycleNum = {1}
            group by appid
            """.format(subclient_obj.subclient_id, cycle_num_val))

            total_size = self.tc.csdb.fetch_one_row()[0]

        return float(total_size)

    def get_last_job(self, subclient_obj):
        """Gets the latest job for the given subclient

            Args:
                subclient_obj   (obj)       --  The subclient object to get last job for

            Returns:
                The job object of the last job of the subclient

        """

        self.tc.csdb.execute(
            "select top 1 jobid from archfile where appid={0} and isvalid=1 "
            "order by jobid desc".format(
                subclient_obj.subclient_id))

        if not self.tc.csdb.rows:
            raise Exception('No jobs are available for the given subclient')

        job_id = self.tc.csdb.fetch_one_row()[0]

        return Job(self.commcell, job_id)

    def get_backup_jobs_stats(self, entity_obj):
        """Gets the list of backup jobs from JmBkpStats table for the given entity

            Args:
                entity_obj      (obj)       --  The backupset/subclient pySDK object

            Returns:
                (list)  -   List of dictionary of jobs from JmBkpStats table.

        """

        if isinstance(entity_obj, Backupset):
            self.tc.csdb.execute("""
                select * from jmbkpstats where appid = (select id from app_backupsetname where id = '{0}') 
                order by jobid asc
            """.format(entity_obj.backupset_id))

        if isinstance(entity_obj, Subclient):
            self.tc.csdb.execute("""
                select * from jmbkpstats where appid = '{0}' 
                order by jobid asc
            """.format(entity_obj.subclient_id))

        return self.tc.csdb.fetch_all_rows(named_columns=True)

    def check_log_line(self, client_obj, machine_obj, name, words, attempts=20, wait=10):
        """Reads the log file and checks if any line is found with the specified words

            Args:
                client_obj      (obj)       --  The cvpysdk client object

                machine_obj     (obj)       --  The machine object of the client

                name            (str)       --  Filename of the log file. Ex: IndexServer.log

                words           (list)      --  List of words to search in the log file

                attempts        (int)       --  Number of attempts to check the log file

                wait            (int)       --  Wait time before every check attempt

            Returns:
                The lines which were found in the log file for the given words

        """

        log_file_path = machine_obj.join_path(client_obj.install_directory, 'Log Files', name)
        attempt = 1
        lines = []

        self.log.info('Checking log file [{0}] on machine [{1}]'.format(
            log_file_path, client_obj.client_name))

        while True:

            if attempt > attempts:
                self.log.error('Attempts exhausted while waiting for log line to printed')
                return False

            self.log.info('Looking for words {0}. Attempt [{1}/{2}]'.format(
                words, attempt, attempts
            ))

            out = machine_obj.find_lines_in_file(log_file_path, words)
            lines = list(filter(len, out))

            if lines:
                break
            else:
                attempt += 1
                self.log.info('Log line not found. Trying again in [{0}] seconds'.format(wait))
                time.sleep(wait)
                continue

        self.log.info('Found log lines: {0}'.format(lines))
        return lines

    def rotate_default_data_path(self, storage_policy_copy):
        """Changes the default datapath of the storage policy primary copy

            Args:
                storage_policy_copy     (obj)       --      Storage policy copy object

            Returns:
                (str)   --      The name of the new default media agent set to the copy

        """

        self.log.info(
            'Current default MA is [%s] in copy [%s] in policy [%s]',
            storage_policy_copy.media_agent,
            storage_policy_copy.copy_name,
            storage_policy_copy.storage_policy.storage_policy_name
        )

        query = f"""
            declare @prev as integer
            declare @next as integer
            declare @cur as integer
            declare @defCopy as integer
            
            set @defCopy = '{storage_policy_copy.copy_id}'
            
            select @prev = HostClientId from MMDataPath where copyId = @defCopy and flag = 7
            
            select TOP 1 @next = HostClientId from MMDataPath 
            where copyId = @defCopy and flag = 4 and HostClientId > @prev 
            order by HostClientId ASC
                
            select @next = ( 
                case when @next is NULL then ( 
                    select TOP 1 HostClientId from MMDataPath 
                    where CopyId = @defCopy and flag = 4 order by HostClientId ASC 
                ) 
                else @next end 
            )
                
            update MMDataPath set flag = 7 where HostClientId = ( 
                select top 1 HostClientId from MMDataPath
                where CopyId = @defCopy and HostClientId = @next
            )
            update MMDataPath set flag = 4 where HostClientId = @prev and CopyId = @defCopy
        """

        self.options_help.update_commserve_db(query, log_query=False)

        storage_policy_copy.refresh()
        self.log.info('New default MA is [%s]', storage_policy_copy.media_agent)

        return storage_policy_copy.media_agent

    def log_section(self, *args):
        """Logs a line to indicate the start of a section"""

        self.log.info('-' * len(args[0]))
        self.log.info(*args)
        self.log.info('-' * len(args[0]))
