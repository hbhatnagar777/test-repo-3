# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Class which validates VSA features like guest files browse, restore and file indexing

VSAFeatures:
    __init__()                  --  Initializes the object

    initialize_vms()            --  Initializes this object with all the information needed to work with all the VMs
    set to backup

    get_cv_vm_client()          --  Gets the CV client and backupset object for the given VM GUID

    create_guest_files()        --  Creates guest files under all the VMs

    edit_guest_files()          --  Edits the guest files created under the VMs

    record_guest_files()        --  Scans and stores the files/folders under all the VMs in memory

    record_copy_precedence()    --  Marks all the jobs are backed up in that particular copy

    verify_vm_afiles()          --  Verifies if the VM backup has the necessary afiles

    verify_gf_browse_restore()  --  Verifies guest files browse and restore

    verify_file_indexing_job()  --  Verifies if file indexing job runs and waits fot it completion

    is_file_indexing_enabled()  --  Verifies if the file indexing is enabled for the parent subclient

    set_gf_restore_options()    --  Sets the default client and destination folder to restore guest files of the VM

    log_difference()            --  Logs the difference between actual and expected results

"""

import random
import time

from AutomationUtils import logger
from AutomationUtils import commonutils
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase

from VirtualServer.VSAUtils.VirtualServerHelper.AutoVSASubclient import AutoVSASubclient

from Indexing.database import index_db


class VSAFeatures(object):

    def __init__(self, auto_subclient: AutoVSASubclient, tc: CVTestCase):
        """Initializes this class

            Args:
                auto_subclient      (obj)   --      The auto VSA subclient object

                tc                  (obj)   --      The CVTestcase object

        """

        self.log = logger.get_log()
        self.auto_subclient = auto_subclient

        self.tc = tc
        self.csdb = tc.csdb

        self.commcell = tc.commcell
        self.subclient = self.auto_subclient.subclient
        self.backupset = self.subclient._backupset_object

        self.vms = {}
        self.vm_names = {}
        self.vm_guids = {}
        self.all_jobs = {}

        self.restore_info = {
            'count': 0
        }

    def initialize_vms(self, collect_vm_info=True):
        """Initializes this object with all the information needed to work with all the VMs set to backup

            Args:
                collect_vm_info     (bool)      --      Decides whether to fetch VM data like VM, machine obj & testdata

            Returns:
                None

        """

        self.vm_guids, self.vm_names = self.subclient._get_vm_ids_and_names_dict()
        self.log.info(self.vm_guids)
        self.log.info(self.vm_names)

        for vm_name in self.auto_subclient.vm_list:

            self.vms[vm_name] = {}

            if not collect_vm_info:
                self.log.info('Skipping collection of VM data for [%s]', vm_name)
                continue

            self.log.info('***** Fetching VM info for [%s] *****', vm_name)
            auto_vm_obj = self.auto_subclient.hvobj.VMs[vm_name]
            auto_vm_obj.update_vm_info('All', os_info=True, force_update=True)

            if auto_vm_obj.machine is None:
                raise Exception(f'Failed to get machine object for the VM [{vm_name}]')

            self.vms[vm_name]['vm_obj'] = auto_vm_obj
            self.vms[vm_name]['machine'] = auto_vm_obj.machine
            self.vms[vm_name]['type'] = auto_vm_obj.machine.os_info.lower()

            if not auto_vm_obj.drive_list:
                raise Exception(f'Failed to get drives of the VM [{vm_name}]')

            testdata = []
            self.log.info(auto_vm_obj.drive_list)
            for drive_name, drive in auto_vm_obj.drive_list.items():
                path = auto_vm_obj.machine.join_path(drive, 'automation', str(self.tc.id))
                try:
                    auto_vm_obj.machine.remove_directory(path)
                except Exception as e:
                    self.log.error('Got exception while deleting directory [%s]', e)
                self.log.info('Testdata path [%s]', path)
                testdata.append(path)

            self.vms[vm_name]['testdata'] = testdata

        for vm_guid, vm_name in self.vm_guids.items():
            cv_vm = self.get_cv_vm_client(vm_guid)
            self.vms[vm_name]['guid'] = vm_guid
            self.vms[vm_name]['client_obj'] = cv_vm['client']
            self.vms[vm_name]['backupset_obj'] = cv_vm['backupset']
            self.vms[vm_name]['subclient_obj'] = cv_vm['subclient']

        self.log.info('***** Successfully initialized the VMs *****')
        self.log.info(self.vms)

    def initialize_index_dbs(self):
        """Initializes the index DB for all the VMs"""

        for vm_name, vm_info in self.vms.items():
            self.log.info('***** Initializing index DB for VM [%s] *****', vm_name)

            if 'index_db' not in self.vms[vm_name]:
                bkset_obj = self.vms[vm_name]['backupset_obj']
                vm_db = index_db.get(bkset_obj)
                self.vms[vm_name]['index_db'] = vm_db
                self.log.info('VM index is in [%s] path [%s]', vm_db.index_server.client_name, vm_db.db_path)

    def get_cv_vm_client(self, vm_guid):
        """Gets the CV client and backupset object for the given VM GUID

            Args:
                vm_guid     (str)   --  The client GUID of the VM

            Returns:
                 dict   --  The dictionary which contains all the VM's client and backupset objects.

        """

        self.log.info('Getting CV client objects for the VM [%s]', vm_guid)

        self.csdb.execute(f"select name from app_client where guid = '{vm_guid}'")
        row = self.csdb.fetch_one_row()

        if not row[0]:
            raise Exception(f'Cannot get client name for the VM with guid [{vm_guid}]. Result [{row}]')

        vm_name = row[0]

        self.log.info('CV VM name is [%s]', vm_name)
        vm_client = self.commcell.clients.get(vm_name)
        vm_agent = vm_client.agents.get('Virtual Server')
        vm_bkset = vm_agent.backupsets.get(self.backupset.backupset_name)
        vm_subclient = vm_bkset.subclients.get(self.subclient.name)

        return {
            'client': vm_client,
            'backupset': vm_bkset,
            'subclient': vm_subclient
        }

    def create_guest_files(self):
        """Creates guest files under all the VMs"""

        for vm_name, vm_info in self.vms.items():
            self.log.info('***** Creating testdata for VM [%s] *****', vm_name)
            for path in vm_info['testdata']:
                self.log.info('***** Generating data on path on VM [%s] *****', path)
                vm_info['machine'].generate_test_data(path, slinks=False, hlinks=False, sparse=False)

    def edit_guest_files(self):
        """Edits the guest files created under the VMs"""

        for vm_name, vm_info in self.vms.items():
            self.log.info('***** Editing testdata for VM [%s] *****', vm_name)
            for path in vm_info['testdata']:
                try:
                    vm_info['machine'].modify_test_data(path, modify=True, rename=True)
                except Exception as e:
                    self.log.error('Failed to modify guest files [%s]', e)

    def record_guest_files(self, job_obj):
        """Scans and stores the files/folders under all the VMs in memory

            Args:
                job_obj         (obj)       --      The SDK job object of the parent job

            Returns:
                None

        """

        job_id = str(job_obj.job_id)
        self.all_jobs[job_id] = {
            'copy': ['1']
        }

        for vm_name, vm_info in self.vms.items():
            self.log.info('***** Recording testdata for VM [%s] *****', vm_name)

            if 'files' not in self.vms[vm_name]:
                self.vms[vm_name]['files'] = {}

            if job_id not in self.vms[vm_name]['files']:
                self.vms[vm_name]['files'][job_id] = []

            for path in vm_info['testdata']:
                all_items = vm_info['machine'].scan_directory(path)
                if not all_items:
                    raise Exception('Cannot scan testdata from the VM [%s]', vm_name)

                # Setting parent for the paths
                for item in all_items:
                    item['org_path'] = item['path']
                    item_path = self._item_cv_path(vm_name, item['path'])
                    item['path'] = item_path
                    item['parent'] = commonutils.get_parent_path(item_path, '\\')

                self.vms[vm_name]['files'][job_id] += all_items

    def record_copy_precedence(self, copy_precedence):
        """Marks all the jobs are backed up in that particular copy

            Args:
                copy_precedence         (int/str)   --  The copy precedence to mark the jobs with

        """

        copy_precedence = str(copy_precedence)

        for job, job_info in self.all_jobs.items():
            if copy_precedence not in job_info['copy']:
                self.all_jobs[job]['copy'].append(copy_precedence)
                self.log.info('Marked job [%s] with copy precedence [%s]', job, copy_precedence)

    def verify_vm_afiles(self, parent_job_obj):
        """Verifies if the VM backup has the necessary afiles

            Args:
                parent_job_obj      (obj)   --      The SDK job object of the parent job

        """

        self.log.info('***** Verifying backup afiles job [%s] *****', parent_job_obj.job_id)

        self.log.info('Parent job details [%s]', parent_job_obj.details)
        vm_details = parent_job_obj.details['jobDetail']['clientStatusInfo']['vmStatus']
        vm_jobs = {}
        for vm in vm_details:
            job_id = vm.get('jobID', None)
            vm_name = vm.get('vmName', None)
            if not job_id or not vm_name:
                raise Exception('Cannot get VM name or VM job ID from parent job details')

            vm_jobs[vm_name] = job_id

        self.log.info('Child jobs [%s]', vm_jobs)

        for vm_name, vm_info in self.vms.items():
            self.log.info('Verifying for VM [%s]', vm_name)
            if vm_name not in vm_jobs:
                raise Exception(f'VM [{vm_name}] is not backed up. Cannot find job ID')

            vm_job = vm_jobs[vm_name]
            self.log.info('Verifying VM job ID [%s]', vm_job)
            self.csdb.execute(f'''
                select id, name, fileType, cTime, appId, jobId, isValid 
                from archFile 
                where jobId = '{vm_job}' and isvalid = 1 and filetype in (2,7,9)
            ''')
            results = self.csdb.fetch_all_rows(named_columns=True)
            self.log.info('Result [%s]', results)

            afile_flags = [0, 0, 0]
            for result in results:
                if result['fileType'] == '2':
                    afile_flags[0] = 1

                if result['fileType'] == '7':
                    afile_flags[1] = 1

                if result['fileType'] == '9':
                    afile_flags[2] = 1

            if not all(afile_flags):
                raise Exception(f'Mismatch in afiles for the VM job [{vm_job}]')

            self.log.info('***** VM job [%s] has been verified *****', vm_job)

    def verify_gf_browse_restore(self, options=None):
        """Verifies guest files browse and restore

            Args:
                options         (dict)  --  The list of browse/restore options. Refer below for the options

            Returns:
                None

            Raises:
                Exception on verification failure

        """

        self.log.info('Received browse/restore options %s', options)

        jobs_list = []
        options = {} if options is None else options

        copy_precedence = str(options.get('copy_precedence', '0'))
        cp_check = '1' if copy_precedence == '0' else copy_precedence
        for job, job_info in self.all_jobs.items():
            if cp_check in job_info['copy']:
                jobs_list.append(job)

        if not jobs_list:
            raise Exception(f'There are no jobs in the given copy precedence [{copy_precedence}]')
        self.log.info('Jobs in copy precedence [%s] are [%s]', copy_precedence, jobs_list)

        org_job_id = options.get('job_id', None)
        job_id = jobs_list[-1] if org_job_id is None else org_job_id
        do_restore = options.get('restore', True)
        from_time = options.get('from_time', 0)
        to_time = options.get('to_time', 0)

        if org_job_id:
            job_obj = self.commcell.job_controller.get(job_id)
            to_time = job_obj.end_timestamp

        options['from_time'] = from_time
        options['to_time'] = to_time

        self.log.info('***** Verifying browse/restore results from job [%s] *****', job_id)

        for vm_name, vm_info in self.vms.items():
            self.log.info('Verifying for VM [%s]', vm_name)
            for path in vm_info['testdata']:
                self.log.info('Verifying browse/restore for items under path [%s]', path)
                all_items = vm_info['files'][job_id]
                test_dirs_info = self._get_gf_random_dirs(all_items, 3)
                self.log.info('Test directories picked [%s]', test_dirs_info)

                self.log.info('***** Verifying browse *****')
                for test_dir_info in test_dirs_info:
                    test_dir = test_dir_info['path']
                    self.log.info('Doing browse for path [%s]', test_dir)

                    options['path'] = test_dir
                    expected_items = self._get_gf_browse_expected_items(all_items, options)
                    actual_items = self._get_gf_browse_actual_items(self.subclient, options)

                    if expected_items == actual_items:
                        self.log.info('***** Browse results verified for the path *****')
                    else:
                        self.log_difference(actual_items, expected_items)
                        raise Exception('There is a mismatch in file indexing browse results')

                if not do_restore:
                    return None

                self.log.info('***** Verifying restore *****')
                restore_dir_info = test_dirs_info[0]
                restore_src = restore_dir_info['org_path']
                self.log.info('Doing restore for path [%s]', restore_src)
                options['path'] = restore_src

                restore_expected = self._get_gf_restore_expected_items(all_items, options)
                restore_actual = self._get_gf_restore_actual_items(vm_info['subclient_obj'], vm_name, options)

                if restore_expected == restore_actual:
                    self.log.info('***** Restore results verified for the path *****')
                else:
                    self.log_difference(restore_actual, restore_expected)
                    raise Exception('There is a mismatch in file restore results')

    def verify_file_indexing_job(self):
        """Verifies if file indexing job runs and waits fot it completion"""

        time.sleep(30)
        fi_job_id = self.auto_subclient.get_in_line_file_indexing_job()

        self.log.info('File indexing job id is [%s]', fi_job_id)
        if not fi_job_id:
            raise Exception('File indexing job did not start')

        fi_job = self.commcell.job_controller.get(fi_job_id)
        if not fi_job.wait_for_completion():
            raise Exception('File indexing job failed to complete.')

        self.log.info('File indexing job completed successfully')

    def is_file_indexing_enabled(self):
        """Verifies if the file indexing is enabled for the parent subclient

            Returns:
                True, if file indexing is enabled. False otherwise.

        """

        self.log.info('Checking if file indexing is enabled')

        query = f"""select attrval from APP_SubClientProp where componentNameId = '{self.subclient.subclient_id}' and 
        attrName = 'Advanced indexing status' order by id asc"""

        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info('File indexing status query response [%s]', row)

        if row[0] == '1':
            self.log.info('File indexing is enabled on the subclient')
            return True
        else:
            self.log.error('File indexing is not enabled on the subclient')
            return False

    def set_gf_restore_options(self, client_name, destination_path):
        """Sets the default client and destination folder to restore guest files of the VM

            Args:
                client_name         (str)       --      The name of the client to restore

                destination_path    (str)       --      The folder under which GF should be restored

            Returns:
                None

        """

        restore_client = self.commcell.clients.get(client_name)
        client_machine = Machine(restore_client)

        self.restore_info['client'] = restore_client
        self.restore_info['client_machine'] = client_machine
        self.restore_info['destination_path'] = destination_path

    @staticmethod
    def _get_gf_browse_actual_items(sc_obj, options):
        """Gets the actual browse results for the given CV item path

            Args:
                sc_obj      (obj)       --      The SDK subclient object to browse

                options         (dict)  --      The browse options dictionary

            Returns:
                (list)      --      The list of actual results found

        """

        path = options.get('path')
        from_time = options.get('from_time')
        to_time = options.get('to_time')
        copy_precedence = options.get('copy_precedence', '0')

        item_list, item_details = sc_obj.guest_files_browse(
            vm_path=path, from_date=from_time, to_date=to_time,
            copy_precedence=copy_precedence
        )
        actual_items = {}

        for item_path, item_info in item_details.items():
            item_type = item_info['type'].lower()
            item_type = 'directory' if item_type == 'folder' else 'file'
            item_size = '0' if item_type == 'directory' else str(item_info['size'])
            actual_items[item_path] = {
                'type': item_type,
                'size': item_size
            }

        return actual_items

    @staticmethod
    def _get_gf_browse_expected_items(all_items, options):
        """Gets the browse expected items

            Args:
                all_items       (list)      --      List of items

                options         (dict)      --      The browse options dictionary

            Returns:
                (list)      --      The list of expected browse items

        """

        expected_items = {}
        path = options.get('path')

        for item in all_items:
            if item['parent'] == path:
                item_size = '0' if item['type'] == 'directory' else str(item['size'])
                expected_items[item['path']] = {
                    'type': item['type'],  # file or directory
                    'size': item_size
                }

        return expected_items

    def _get_gf_restore_actual_items(self, sc_obj, vm_name, options):
        """Gets the actual restore results

            Args:
                sc_obj      (obj)       --      The SDK subclient object of the VM client

                vm_name     (str)       --      The name of the VM to submit restore job

                options     (dict)      --      The restore options dictionary

            Returns:
                (list)      --      List of relative path of items restored by restore job

        """

        self.log.info('Restore options [%s]', options)
        self.restore_info['count'] += 1

        restore_src = options['path']  # This is native path of the item to restore
        from_time = int(options.get('from_time'))
        to_time = int(options.get('to_time'))
        copy_precedence = options.get('copy_precedence', '0')

        restore_client = self.restore_info['client']
        cl_machine = self.restore_info['client_machine']
        destination_dir = cl_machine.join_path(self.restore_info['destination_path'], str(self.restore_info['count']))

        self.log.info(
            'Starting restore [%s] of [%s] to path [%s]',
            str(self.restore_info['count']),
            restore_src,
            destination_dir
        )

        actual_results = {}
        self.subclient._subClientEntity = sc_obj._subClientEntity

        try:
            cl_machine.remove_directory(destination_dir)
        except Exception as e:
            self.log.error(e)

        restore_job = self.subclient.guest_file_restore(
            destination_path=destination_dir,
            vm_name=vm_name,
            destination_client=restore_client.client_name,
            folder_to_restore=restore_src,
            preserve_level=0,
            verify_path=False,
            from_date=commonutils.convert_to_formatted_time(from_time),
            to_date=commonutils.convert_to_formatted_time(to_time),
            copy_precedence=int(copy_precedence)
        )

        self.log.info('Started restore job [%s]', restore_job.job_id)

        if not restore_job.wait_for_completion():
            raise Exception(f'Restore job [{restore_job.job_id}] did not complete successfully')

        self.log.info('Restore job [%s] completed successfully', restore_job.job_id)
        out = cl_machine.scan_directory(destination_dir)
        if not out:
            raise Exception('No items were restored')

        for item in out:
            path = item['path']
            size = '0' if item['type'] == 'directory' else str(item['size'])
            new_path = path.replace(destination_dir, '')
            new_path = new_path.replace('/', '\\')
            actual_results[new_path] = {
                'type': item['type'],  # file or directory
                'size': size
            }

        return actual_results

    @staticmethod
    def _get_gf_restore_expected_items(all_items, options):
        """Gets the expected restore results for the item restored

            Args:
                all_items       (list)      --      List of items

                options         (dict)      --      The restore options dictionary

            Returns:
                (list)  --  The expected restore results for the given path

        """

        restore_src = options['path']  # This is native path of the item to restore
        expected_items = {}

        for item in all_items:
            path = item['org_path']
            if restore_src in path:
                size = '0' if item['type'] == 'directory' else str(item['size'])
                new_path = path.replace(restore_src, '')

                if not new_path:
                    continue

                new_path = new_path.replace('/', '\\')
                expected_items[new_path] = {
                    'type': item['type'],  # file or directory
                    'size': size
                }

        return expected_items

    @staticmethod
    def _get_gf_random_dirs(all_items, count):
        """Gets random directories from the items list

            Args:
                all_items       (list)      --      List of items

                count           (int)       --      Number of random directories to get

            Returns:
                (list)  --  List of random directories picked

        """

        all_dirs = []
        for item in all_items:
            if item['type'] == 'directory':
                all_dirs.append(item)

        if not all_dirs:
            raise Exception('No directories found in the testdata to browse/restore')

        try:
            return random.sample(all_dirs, count)
        except ValueError:
            return all_dirs

    @staticmethod
    def _item_cv_path(vm_name, path):
        """Converts the native item path to CV VM index path"""

        path = path.replace('/', '\\')
        path = commonutils.remove_prefix_sep(path, '\\')
        return '\\'.join(['', vm_name, path])

    def log_difference(self, actual, expected):
        """Logs the difference between actual and expected results

            Args:
                actual      (dict)      --      The actual results

                expected    (dict)      --      The expected results

            Returns:
                None

        """

        added, removed, modified = commonutils.get_dictionary_difference(expected, actual)

        self.log.info('Actual items: [%s]', actual)
        self.log.info('Expected items: [%s]', expected)
        self.log.info('Added: [%s]', added)
        self.log.info('Removed: [%s]', removed)
        self.log.info('Modified: [%s]', modified)
