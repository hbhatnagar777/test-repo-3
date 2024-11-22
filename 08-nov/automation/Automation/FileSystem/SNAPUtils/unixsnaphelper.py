# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Intellisnap operations

Restore , Data, Queries and UnixSnapHelper are 4 classes defined in this file.

Restore: Enum constants for all the Restore supported by intellisnap subclients

Data: Enum constant for data operations

Queries: Enum constant for required queries for snap operation

UnixSnapHelper - Helper class to perform intellisnap operations

UnixSnapHelper:
    _create_paths()            - Creates necessary paths on client and MA

    _delete_paths()            - Deletes up paths created by the test case

    _create_disk_lib()         - Creates disk library entity on CS

    _create_storage_policy()   - Creates storage policy entity on CS

    _create_subclient()        - Creates subclient entity on CS

    setup_snap_environment()   - Wrapper function that setups necessary environment
                                 for the test case

    _execute_query()           - Execute DB queries

    _add_array()               - Function to add storage array

    _generate_test_data()      - Generate test data required for the test case

    _modify_test_data()        - Modify test data between the jobs

    snap_backup()              - Adds or modifies data and run a snapshot backup job

    backup_copy()              - Run backup copy jobs for the storage policy

    restore()                  - Run restore job either in place or out of place

    compare_data()             - Compare the source and destination files and folders

    verify_restore()           - Verifies restore job by comparing the source and restored data

    verify_mount()             - Mounts the snapshot and compares source and snapshot data

    verify_unmount()           - Mounts and unmounts the snapshot, and verifies that snapshot
                                 is unmounted and temporary directories are deleted

    verify_revert()            - Performs a hardware revert and compares the reverted data with
                                 copy of source

    snap_operation()           - Helper function for performing snap operation
                                 mount/unmount/revert/delete

    verify_optimized_scan()    - Verifies that jobs was run with optimized scan

    _make_test_data_copy()     - Make copy of source preserving the metadata

    _get_mount_status()        - Returns mount status for the snapshot

    cleanup()                  - Cleans up entities and paths created at the beginning
                                 of the test case

    add_data_to_path()         - Add files to the folder path and return the
                                 list of files added to be Backed-up

    verify_collect_extent()-   - Verify if all teh extents are backed up for the source_list

    acceptance_tamplate()      - Snap Acceptance template to be used for all test cases
                                 with different Unix configurations and snap engines

    snap_extent_template()     - Template to run extent test case for intellisnap

    check_volume_monitoring()  - Check the state of the volume for DC

    get_backup_stream_count()  - Returns the number of streams used by a backup job

    get_restore_stream_count() - Returns the number of streams used by a restore job

    verify_job_streams()       - Verifies if the job used expected number of streams


"""

from __future__ import unicode_literals
import time
from base64 import b64encode
from datetime import datetime
from enum import Enum
import itertools
from cvpysdk.exception import SDKException
from cvpysdk.job import Job
from cvpysdk.policies.storage_policies import StoragePolicyCopy
from cvpysdk.schedules import Schedules
from AutomationUtils import constants
from AutomationUtils import logger
from AutomationUtils.constants import backup_level, \
    UNIX_VOLUME_STATE, UNIX_GET_RESTORE_STREAM_COUNT
from AutomationUtils.database_helper import get_csdb
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from FileSystem.FSUtils.fshelper import ScanType


class Restore(Enum):
    """ Restore Types enumeration """
    RESTORE_FROM_SNAP = 1
    RESTORE_FROM_TAPE = 2


class Data(Enum):
    """ Data Operation enumeration """
    ADD_DATA = 1
    MODIFY_DATA = 2
    ADD_MODIFY_DATA = 3
    DELETE_DATA = 4


class Queries(Enum):
    """ Queries required for snap backup """
    BACKUP_COPY_JOB_QUERY = 'SELECT childJobId FROM JMJobWF WHERE jobId = {a}'
    BACKUP_SIZE_QUERY = 'SELECT totalBackupSize FROM JMBkpStats WHERE jobID = {a}'
    MOUNT_STATUS_QUERY = 'SELECT MountStatus FROM SMVolume WHERE JobId = {a}'
    JOB_IDS_QUERY = 'SELECT JobId FROM SMVolume WHERE CopyId = {a}'
    MOUNT_PATH_QUERY = 'SELECT SourcePath, MountPath FROM SMVolume \
                        WHERE JobId = {a} AND CopyId = {b}'
    VOLUME_ID_QUERY = 'SELECT SMVolumeId FROM SMVolume WHERE jobID = {a} AND CopyId = {b}'
    CONTROL_HOST_QUERY = 'SELECT ControlHostId FROM SMsnap WHERE SMSnapId in \
                                (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in \
                                (SELECT SMVolumeId from SMVolume WHERE JobId = {a}))'
    SNAP_COUNT_QUERY = 'SELECT snap.SMSnapId FROM SMVolume AS Vol \
                                INNER JOIN SMVolSnapMap AS map ON vol.SMVolumeId = map.SMVolumeId \
                                INNER JOIN SMSnap AS snap ON map.SMSnapId = snap.SMSnapId AND \
                                snap.ReserveField2 = {a} WHERE vol.JobId = {b} AND \
                                snap.ControlHostId IN ({c}, {d})'
    SNAP_COPY_NAME_QUERY = 'SELECT name FROM ArchGroupCopy WHERE ArchGroupId = {a} \
                            AND copy = 1 AND isSnapCopy = 1'


class UnixSnapHelper():
    """
    UnixSnapHelper - helper class for Unix FS snap automation

    """

    def __init__(self, commcell, client, agent, tcinputs):
        """
        Constructor
        Args:
            commcell        (commcell)          -- Commcell object

            client          (client)            -- client object

            agent           (agent)             -- Agent object

            tcinputs        (dict)              -- tcinputs dictionary of test case class

        """
        self.storage_policy = None
        self.disk_library = None
        self.backupset = None
        self.subclient = None
        self.source_path = None
        self.snap_mount_path = None
        self.job = None
        self.inc_data_dir = None
        self.scan_type = None
        self.snap_proxy = None
        self.backup_copy_proxy = None

        self.job_tracker = []
        self.test_data_paths = []
        self.inc_data_paths = []
        self.entities = {}

        self.log = logger.get_log()
        self.csdb = get_csdb()
        self.commcell = commcell
        self.client = client
        self.agent = agent
        self.tcinputs = tcinputs

        self.client_machine = Machine(self.client)
        self.cv_entities = CVEntities(self.commcell)

        self.ma_machine = Machine(
            self.commcell.clients.get(
                self.tcinputs['MediaAgentName']))
        if self.tcinputs.get('ScanType'):
            self.scan_type = ScanType.OPTIMIZED \
                if self.tcinputs['ScanType'].lower() == 'optimized' \
                else ScanType.RECURSIVE
        else:
            self.scan_type = ScanType.RECURSIVE

        self.contents = self.tcinputs['SubclientContent'].split(',')
        self.restore_location = self.tcinputs['RestoreLocation']
        self.instance_name = self.tcinputs['InstanceName'] \
            if self.tcinputs.get('InstanceName') else 'DefaultInstanceName'
        self.filter_content = self.tcinputs['Filter_content'].split(
            ',') if self.tcinputs.get('Filter_content') else None
        self.epoch = str(int(time.time()))

        self.disk_lib_dir = 'automation_disklib_' + self.epoch
        self.disk_lib_name = 'automation_lib_' + self.epoch
        self.storage_policy_name = 'automation_sp_' + self.epoch
        self.backupset_name = 'automation_bs_' + self.epoch
        self.subclient_name = 'automation_sc_' + self.epoch \
                              + "_".join(self.tcinputs['SnapEngine'].split())

        self.disk_lib_path = self.tcinputs['DiskLibLocation'].rstrip(
            self.ma_machine.os_sep) + self.ma_machine.os_sep + self.disk_lib_dir
        self.restore_path = self.restore_location.rstrip(
            self.client_machine.os_sep) + self.client_machine.os_sep + self.epoch + '_restore'
        self.test_data_copy_path = self.restore_location.rstrip(
            self.client_machine.os_sep) + self.client_machine.os_sep + self.epoch + '_copy'
        self.bkpset_name = self.tcinputs.get('BackupsetName', None)
        self.sc_name = self.tcinputs.get('SubclientName', None)
        self.snap_copy_name = 'snapCopy'
        self.is_iris = True if "IsIris" in self.tcinputs else False

    def _create_paths(self):
        """
        Create necessary folders
        """
        self.log.info('Create disk library path')
        self.ma_machine.create_directory(self.disk_lib_path, force_create=True)
        self.log.info('Created disk library path [%s]', self.disk_lib_path)

        for content in self.contents:
            path = content + self.client_machine.os_sep + self.epoch
            self.log.info('Create content directory')
            self.client_machine.create_directory(path, force_create=True)
            self.test_data_paths.append(path)
            self.log.info('Created content directory [%s]', path)

        self.log.info('Create restore path')
        self.client_machine.create_directory(
            self.restore_path, force_create=True)
        self.log.info('Created restore path [%s]', self.restore_path)

        self.log.info('Create copy path')
        self.client_machine.create_directory(
            self.test_data_copy_path, force_create=True)
        self.log.info('Created copy path [%s]', self.test_data_copy_path)

    def _delete_paths(self):
        """
        Delete folders created during setup
        """
        if self.ma_machine.check_directory_exists(self.disk_lib_path):
            self.log.info('Cleanup disk library path')
            self.ma_machine.remove_directory(self.disk_lib_path)

        for content in self.contents:
            path = content + self.client_machine.os_sep + self.epoch
            if self.client_machine.check_directory_exists(path):
                self.log.info('Cleanup content paths')
                self.client_machine.remove_directory(path)

        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info('Cleanup restore path')
            self.client_machine.remove_directory(self.restore_path)

        if self.client_machine.check_directory_exists(
                self.test_data_copy_path):
            self.log.info('Cleanup copy path')
            self.client_machine.remove_directory(self.test_data_copy_path)

        if self.client_machine.check_directory_exists(self.snap_mount_path):
            self.log.info('Cleanup mount path')
            self.client_machine.remove_directory(self.snap_mount_path)

    def _create_disk_lib(self):
        """
        Create disk library
        """
        entity = self.cv_entities.create({
            'target':
                {
                    'force': False,
                    'mediaagent': str(self.tcinputs['MediaAgentName'])
                },
            'disklibrary':
                {
                    'name': self.disk_lib_name,
                    'mount_path': self.disk_lib_path
                },
        })
        self.entities['disklibrary'] = entity['disklibrary']
        self.disk_library = self.entities['disklibrary']['object']

    def _create_storage_policy(self):
        """
        Create storage policy
        """
        entity = self.cv_entities.create({
            'target':
                {
                    'force': False,
                    'mediaagent': str(self.tcinputs['MediaAgentName'])
                },
            'storagepolicy':
                {
                    'name': self.storage_policy_name,
                    'library': str(self.disk_lib_name),
                    'retention_period': 0,
                    'number_of_streams': 50
                },
        })
        self.entities['storagepolicy'] = entity['storagepolicy']
        self.storage_policy = self.entities['storagepolicy']['object']
        self.storage_policy.create_snap_copy(
            self.snap_copy_name, False, True, self.disk_library.library_name, str(
                self.tcinputs['MediaAgentName']), None)
        # time.sleep(5)
        # Adding snapshot copy to SP triggers creation of backup copy schedule
        # check and delete the schedule as it interferes with the test case flow
        # there is no way to disable the creations of the schedule
        schedules = Schedules(self.commcell)
        schedules.refresh()
        schedule = schedules.get(self.storage_policy_name + ' snap copy')
        if schedules.has_schedule(
                schedule.schedule_name,
                schedule.schedule_id):
            schedules.delete(schedule.schedule_name)

    def _create_subclient(self):
        """
        Create subclient
        """
        entity = self.cv_entities.create({
            'target':
                {
                    'force': False,
                    'client': self.client.client_name
                },
            'backupset':
                {
                    'name': self.backupset_name,
                    'agent': self.agent.agent_name,
                    'client': self.client.client_name,
                    'instance': self.instance_name
                },
            'subclient':
                {
                    'agent': self.agent.agent_name,
                    'name': self.subclient_name,
                    'content': self.test_data_paths,
                    'filter_content': self.filter_content,
                    'instance': self.instance_name,
                    'storagepolicy': self.storage_policy_name,
                    'backupset': self.backupset_name,
                    'client': self.client.client_name
                },
        })
        self.entities['backupset'] = entity['backupset']
        self.entities['subclient'] = entity['subclient']
        self.backupset = self.entities['backupset']['object']
        self.subclient = self.entities['subclient']['object']
        self.subclient.scan_type = self.scan_type.value
        self.subclient.enable_intelli_snap(self.tcinputs['SnapEngine'])

    def setup_snap_environment(self):
        """
        Setup snap environment
        """

        self._add_array()
        self.client.enable_intelli_snap()
        if self.is_iris:
            self.contents = self.tcinputs['IrisSourcePath'].split(',')
            self._create_paths()
            self.contents = self.tcinputs['SubclientContent'].split(',')
        else:
            self._create_paths()
        if self.sc_name and self.bkpset_name is not None:
            self.log.info('Note creating entites as test case is run on existing subclient')
            self.backupset = self.agent.backupsets.get(self.bkpset_name)
            self.subclient = self.backupset.subclients.get(self.sc_name)
            self.subclient.scan_type = self.scan_type.value
            self.subclient.enable_intelli_snap(self.tcinputs['SnapEngine'])
            self.storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            self.snap_copy_name = self._execute_query(
                Queries.SNAP_COPY_NAME_QUERY.value, {
                    'a': self.storage_policy.storage_policy_id}, fetch_rows='one')
        else:
            self._create_disk_lib()
            self._create_storage_policy()
            self._create_subclient()

    def _execute_query(self, query, options=None, fetch_rows='all'):
        """
        Execute query and return one or all rows
        Args:
            query           (str)   -- SQL query to be excuted

            options         (str)   -- values to be replaced in the query


            fetch_rows      (str)   -- By default return all rows, if not return one row

        Return:
            (str) query output
        """
        if options is None:
            self.csdb.execute(query)
        elif isinstance(options, dict):
            self.csdb.execute(query.format(**options))

        if fetch_rows != 'all':
            return self.csdb.fetch_one_row()[0]
        return self.csdb.fetch_all_rows()

    def _add_array(self):
        """
        Add array entry
        """
        try:
            if self.tcinputs.get('ArrayName') and self.tcinputs.get('ArrayVendor') \
                    and self.tcinputs.get('ArrayUserName') and self.tcinputs.get('ArrayPassword'):
                self.log.info("Adding array management entry")
                self.commcell.array_management.add_array(
                    self.tcinputs['ArrayVendor'],
                    self.tcinputs['ArrayName'],
                    self.tcinputs['ArrayUserName'],
                    b64encode(
                        self.tcinputs['ArrayPassword'].encode()).decode(),
                    self.tcinputs['ControlHost'],
                    None,
                    False)
            else:
                self.log.info('Array details not provided skipping add array')
        except SDKException as exp:
            if exp.exception_id == '101':
                self.log.info("Array already exist")
            else:
                raise Exception(exp)

    def _generate_test_data(self):
        """
        Generate test data
        """
        for path in self.test_data_paths:
            self.log.info('Generating test data under [%s]', path)
            self.client_machine.generate_test_data(path)

    def _modify_test_data(self, operation):
        """
        Modify test data
        """
        if operation == Data.ADD_DATA:
            for path in self.test_data_paths:
                self.inc_data_dir = 'incdata_' + str(int(time.time()))
                inc_data_path = path + self.client_machine.os_sep + self.inc_data_dir
                self.inc_data_paths.append(inc_data_path)
                self.log.info('Adding test data under [%s]', inc_data_path)
                self.client_machine.create_directory(inc_data_path)
                self.client_machine.generate_test_data(inc_data_path)

    def snap_backup(self, level, skip_data_creation=False, option=None):
        """
         Generate test data and run snap backup

        Args:
            level                 (backup_level)     -- Following values are supported:
                                                        backup_level.Full
                                                        backup_level.INCREMENTAL
                                                        backup_level.SYNTHETICFULL

            skip_data_creation   (bool)              -- False if data need to be create
                                                        before running backup otherwise False.

            option              (dict)               -- advance option for snap backup.

                    key:'inline_bkp_cpy'               Value: (bool) - To run backup copy
                                                                       immediately

                    key:'skip_catalog'                 Value: (bool) - To run snap backup
                                                                       with or without cataloging

        Returns:
              job               (job object)        -- job object of snap backup
        """
        if not skip_data_creation:
            if level == backup_level.FULL:
                self._generate_test_data()
            elif level == backup_level.INCREMENTAL:
                self._modify_test_data(Data.ADD_DATA)
        if option is None:
            option = dict()
        advanced_option = {
            'inline_bkp_cpy': option.get('inline_bkp_cpy', False),
            'skip_catalog': option.get('skip_catalog', True)
        }

        if level == backup_level.SYNTHETICFULL:
            job = self.subclient.backup('Synthetic_Full')
        else:
            job = self.subclient.backup(
                level.value, advanced_options=advanced_option)
        self.log.info(
            'Monitoring [%s] [%s] job [%s]',
            job.backup_level,
            job.job_type,
            job.job_id)
        if not job.wait_for_completion():
            self.log.error(
                'Failed to run [%s] snap backup job with error [%s]',
                level.value,
                job.delay_reason)
            raise Exception('Failed to run snap backup job')

        if job.backup_level != level.value.replace('_', ' '):
            self.log.error(
                'Backup not run at same level as started expected [%s] actual [%s]',
                level.value,
                job.backup_level)
            raise Exception('Backup not run at the same level as started')

        self.log.info('Successfully finished [%s] [%s] job [%s]',
                      job.backup_level, job.job_type, job.job_id
                      )
        self.job_tracker.append(job.job_id)
        self.job = job

        return job

    def backup_copy(self, subclient_level=False):
        """
        Run backup copy for a subclient or storage policy

        Args:
            subclient_level     (bool)     --following option for running
                                            backup copy from different level.
                                            True - subclient level
                                            False - Storage policy level
        """
        if subclient_level:
            work_flow_job = self.subclient.run_backup_copy()
        else:
            work_flow_job = self.storage_policy.run_backup_copy()
        time.sleep(5)

        backup_copy_job_id = self._execute_query(
            Queries.BACKUP_COPY_JOB_QUERY.value, {
                'a': work_flow_job.job_id}, fetch_rows='one')

        if backup_copy_job_id in [None, ' ', '']:
            self.log.error(
                'Backup copy job for the workflow job [%s] is not started',
                work_flow_job.job_id)
            raise Exception('Backup copy job not started')
        else:
            backup_copy_job = Job(self.commcell, backup_copy_job_id)
            self.log.info(
                'Monitoring [%s] [%s] job [%s]',
                backup_copy_job.backup_level,
                backup_copy_job.job_type,
                backup_copy_job.job_id)
        if not backup_copy_job.wait_for_completion():
            self.log.error('Backup copy job failed with error [%s]',
                           backup_copy_job.delay_reason
                           )
            raise Exception('Backup copy job failed')
        self.log.info(
            'Successfully finished backup copy job [%s]',
            backup_copy_job.job_id)

        if not work_flow_job.wait_for_completion():
            self.log.error('Backup copy workflow job failed with error [%s]',
                           work_flow_job.delay_reason
                           )
            raise Exception('Backup copy workflow job failed')

        self.job_tracker.append(backup_copy_job.job_id)
        self.backup_copy_job = backup_copy_job
        return backup_copy_job

    def restore(self,
                copy_precedence,
                src_path,
                inplace=True,
                dst_client=None,
                restore_path=None,
                no_of_streams=1,
                **kwargs):
        """
        Restore from last job

        Args:
            copy_precedence (str)       -- Copy precedence
                                            1 - snapcopy,
                                            2 - primary copy

            src_path        (str)       -- source path for restore

            inplace         (str)       -- By default do inplace restore,
                                           otherwise out of place restore

            dst_client      (str)       -- Destination client for cross client out of place restore

            restore_path    (str)       -- Restore path on destination client

            \*\*kwargs  (dict)          --  Optional keyword arguments

            Available kwargs options:

                instant_clone_options       (dict)  -- Options for performing an instant clone restore operation.
                The following key-value pairs are supported.

                    clone_mount_path        (str)   --  The path to which the snapshot needs to be mounted.
                    This  key is NOT OPTIONAL.

                    reservation_time        (int)   --  The amount of time, specified in seconds, that the mounted
                    snapshot needs to be reserved for before it is cleaned up.
                    This key is OPTIONAL.

                            Default :   3600

                    post_clone_script       (str)   --  The script that will run post clone.
                    This key is OPTIONAL.

                    clone_cleanup_script    (str)   --  The script that will run after clean up.
                    This key is OPTIONAL.

        """
        if self.job is not None and copy_precedence is Restore.RESTORE_FROM_SNAP:
            from_time = str(
                datetime.utcfromtimestamp(
                    self.job.summary['jobStartTime']))
            to_time = str(
                datetime.utcfromtimestamp(
                    self.job.summary['jobEndTime']))
        else:
            from_time = None
            to_time = None

        if not inplace:
            self.log.info(
                'Running out of place restore from copy precedence [%s]',
                copy_precedence)
            fs_options = {
                'preserve_level': 100,
                'no_of_streams': no_of_streams,
                'instant_clone_options': kwargs.get('instant_clone_options', None)}
            if dst_client:
                if not restore_path:
                    self.log.error(
                        'Restore path required cross machine out of place restore')
                    raise Exception(
                        'Restore path not provided cross machine out of place restore')
                dst_client_name = dst_client.client_name

            else:
                dst_client_name = self.client.client_name
                dst_client = self.client
                restore_path = kwargs.get('restore_path', self.restore_path)

            if no_of_streams > 1:
                fs_options['destination_appTypeId'] = 33 if "windows" in \
                                                            dst_client._os_info.lower() else 29
            job = self.subclient.restore_out_of_place(
                dst_client_name,
                restore_path,
                src_path,
                copy_precedence=copy_precedence,
                from_time=from_time,
                to_time=to_time,
                fs_options=fs_options)
        else:
            self.log.info(
                'Running in place restore from copy precedence [%s]',
                copy_precedence)
            self._make_test_data_copy()
            job = self.subclient.restore_in_place(
                src_path,
                copy_precedence=copy_precedence,
                from_time=from_time, to_time=to_time,
                fs_options={'preserve_level': 100})
        self.log.info('Monitoring restore job [%s]', job.job_id)

        if not job.wait_for_completion():
            self.log.error(
                'Restore job failed with error [%s]',
                job.delay_reason)
            raise Exception('Restore job failed')

        if no_of_streams > 1 and not kwargs.get('instant_clone_options', None):
            self.verify_job_streams(
                job, no_of_streams, self.get_restore_stream_count(job))

        return job

    def compare_data(
            self,
            dst_client_machine,
            src_path,
            dst_path,
            compare_meta=True):
        """
        Compare metadata and md5sum for the source and destination path

        Args:
            dst_client_machine      (str)   -- Destination client machine object for comparison

            src_path                (str)   -- Source data path

            dst_path                (str)   -- Restore data path

            compare_meta            (str)   -- By default do metadata comparison, otherwise skip
        """
        if compare_meta:
            status, diff_output = self.client_machine.compare_meta_data(
                src_path, dst_path, skiplink=True)
            if not status:
                self.log.error(
                    'Meta data comparison for source [%s] and destination [%s] failed',
                    src_path,
                    dst_path)
                self.log.error("Diff output \n%s" % diff_output)
                raise Exception("Meta data comparison failed")
            else:
                self.log.info(
                    'Meta data comparison for source [%s] and destination [%s] successful',
                    src_path,
                    dst_path)

        status = self.client_machine.compare_folders(
            dst_client_machine, src_path, dst_path)
        if not bool(status):
            self.log.info(
                'md5sum comparison for source [%s] and destination [%s] successful',
                src_path,
                dst_path)
            return True

        self.log.error(
            'md5sum comparison for source [%s] and destination [%s] failed',
            src_path,
            dst_path)
        self.log.error("Diff output %s" % str(status))
        raise Exception('md5sum comparison failed')

    def verify_restore(self, dst_client_machine, src_path, dst_path):
        """
        Verify Restore by comparing restored data and source data
        """
        for path in src_path:
            dpath = dst_path.rstrip(self.client_machine.os_sep) + path
            self.compare_data(dst_client_machine, path, dpath)
        self.log.info('Restore verification successful')

    def verify_mount_unmount(
            self,
            src_path,
            mount_client=None,
            mount_path=None):
        """
       Verify mount, Mount snapshot and compare with source. Unmount the snapshot

            Args:
                src_path        (str)       -- Source path for comparison

                dst_client      (str)       -- Destination client if snap
                                               to be mounted on another client

                dst_mount_path  (str)       -- Temoporary location for mountinf snapshot
        """

        copy_name = self.snap_copy_name
        if not mount_client:
            mount_client = self.client
            mount_path = constants.UNIX_TMP_DIR
        mount_client_machine = Machine(mount_client)
        self.snap_operation(self.job.job_id, 'mount', mount_client, mount_path, copy_name)
        for path in src_path:
            for mnt_path in self.snap_mount_path:
                if mnt_path[0] in path:
                    dst_path = mnt_path[1].rstrip(
                        mount_client_machine.os_sep) + mount_client_machine.os_sep + self.epoch

                    self.compare_data(mount_client_machine, path, dst_path)
                    self.log.info('Mount verification successful for job [%s]',
                                  self.job.job_id
                                  )
        time.sleep(5)
        if self._get_mount_status(self.job.job_id)[0][0] == '59':
            self.snap_operation(self.job.job_id, 'unmount', copy_name=copy_name)
            if self._get_mount_status(self.job.job_id)[0][0] == '79':
                for path in self.snap_mount_path:
                    if not mount_client_machine.check_directory_exists(
                            path[1]):
                        self.log.info('Unmount verification successful')
        time.sleep(10)

    def verify_revert(self):
        """
        Verify hardware revert

        Make a copy of source data

        Perform hardware revert

        Compare source data with copy
        """

        copy_name = self.snap_copy_name
        if not (self.job.backup_level == backup_level.SYNTHETICFULL or
                self.subclient.scan_type == ScanType.OPTIMIZED):
            self._make_test_data_copy()
            for path in self.test_data_paths:
                self.client_machine.remove_directory(path)
            self.snap_operation(self.job.job_id, 'revert', copy_name=copy_name)
            for path in self.test_data_paths:
                dpath = self.test_data_copy_path.rstrip(
                    self.client_machine.os_sep) + path
                self.compare_data(self.client_machine, path, dpath)
            self.log.info('Revert verification successful')
        time.sleep(10)

    def snap_operation(self,
                       job_id,
                       operation,
                       mount_client=None,
                       mount_path=None,
                       copy_name=None
                       ):
        """
        Perform Snap Operations for given job id

            Args:

            job_id          (str)      -- Snapbackup Job ID

            operation       (str)      -- Following operations are allowed

                                            mount - mount snapshots

                                            unmount - unmount snapshot

                                            revert - perform hardware revert

                                            delete - delete snapshot

                                            force_delete - force delete snapshot

            copy_name       (str)       -- Snapshot copy name
        """
        copy_id = StoragePolicyCopy(
            self.commcell,
            self.storage_policy,
            copy_name).copy_id
        volume_id = self._execute_query(
            Queries.VOLUME_ID_QUERY.value, {
                'a': job_id, 'b': copy_id})

        if operation == 'mount':
            if not mount_client:
                mount_client = self.client
                mount_path = constants.UNIX_TMP_DIR
            job = self.commcell.array_management.mount(
                volume_id, mount_client.client_name, mount_path, False)
        elif operation == 'unmount':
            job = self.commcell.array_management.unmount(volume_id)
        elif operation == 'revert':
            job = self.commcell.array_management.revert(volume_id)
        elif operation == 'delete':
            job = self.commcell.array_management.delete(volume_id)
        elif operation == 'force_delete':
            job = self.commcell.array_management.force_delete(volume_id)
        else:
            self.log.error("operation %s is invalid", operation)
            raise Exception("operation %s is invalid", operation)

        self.log.info(
            'Monitoring Snap Operation [%s] job [%s]',
            operation,
            job.job_id)

        if not job.wait_for_completion():
            self.log.error('Failed to run snap operation [%s]', operation)
            raise Exception('Failed to run snap operation')

        time.sleep(10)
        self.log.info(
            'Completed snap operation [%s] for job [%s] and volume_id [%s]',
            operation,
            job_id,
            volume_id)

        if operation == 'mount':
            self.snap_mount_path = self._execute_query(
                Queries.MOUNT_PATH_QUERY.value, {
                    'a': job_id, 'b': copy_id})

    def verify_optimized_scan(self, jobid):
        """
              Verify if DC was run for the job

                  Args:
                      jobid       (str)       -- jobid of the required job

                  Returns
                      (bool)                  -- return true if all the volume in subclient content has used optimized scan
                                                  else False
              """
        command = "grep {} {}//FileScan*.log ".format(
            jobid,
            self.client.log_directory) + r'|grep " DataClassificationHelper initialized for"|wc -l'

        output = self.client_machine.execute_command(command)
        if output.exit_code:
            raise Exception(
                "Failed checking the log lines for DC .output {} error {}".format(
                    output.output, output.exception_message))

        if output.output.rstrip('\n') == str(len(self.test_data_paths)):
            return True

        self.log.info(
            "Optimized scan used for {} volumes which is not expected")
        return False

    def _make_test_data_copy(self):
        """
        Make copy of the test data
        """
        for path in self.contents:
            self.client_machine.copy_folder(
                path, self.test_data_copy_path, optional_params='-fp')

    def _get_mount_status(self, job_id):
        """
        To get the mount status of a snap.

            Returns:
                mount status
        """
        return self._execute_query(
            Queries.MOUNT_STATUS_QUERY.value, {
                'a': job_id})

    def cleanup(self):
        """
        Cleanup entities
        """
        if self.sc_name and self.bkpset_name is not None:
            self.log.info('Not deleting entities as the test case run on existing subclient')
        else:
            self.cv_entities.delete({'subclient': self.entities['subclient']})
            self.cv_entities.delete({'backupset': self.entities['backupset']})
            self.cv_entities.delete(
                {'storagepolicy': self.entities['storagepolicy']})
            self.cv_entities.delete({'disklibrary': self.entities['disklibrary']})
        if self.is_iris:
            self.contents = self.tcinputs['IrisSourcePath'].split(',')
            self._delete_paths()
            self.contents = self.tcinputs['SubclientContent'].split(',')
        else:
            self._delete_paths()

    def add_data_to_path(self, full_data_path):
        """
        Add files to the folder path and return the list of files added to be Backed-up

            Args :
                full_data_path:      (str)      --   Folder path to create the files

            Return:
                list of files to be Backed-up
        """
        list_of_files = []
        list_of_non_extent_files = []
        for path in full_data_path:
            for i in range(1, 5):
                file_name = "{0}{1}{2}.txt".format(
                    path, self.client_machine.os_sep, str(i))
                list_of_files.append(file_name)
                command = "dd if=/dev/urandom of={0} count=17 bs=1048576".format(
                    file_name)
                self.client_machine.execute(command)
            for i in range(1, 3):
                file_name = "{0}{1}{2}.doc".format(
                    path, self.client_machine.os_sep, str(i))
                list_of_non_extent_files.append(file_name)
                command = "dd if=/dev/urandom of={0} count=1 bs=1048".format(
                    file_name)
                self.client_machine.execute(command)

        self.log.info(
            "List of files that doesnt qualify for extent backup: %s",
            list_of_non_extent_files)
        self.log.info("List of extent qualified files: %s", list_of_files)
        return list_of_files

    def verify_collect_extents(self, source_list):
        """
        Verify if all the extents are backed up for the source_list
        Args:
            source_list        (list)       -- Source list to compare it with collect file
        """

        file_list = []
        # Get the job results directory
        collect_path = "{0}/{1}/{2}/{3}/{4}".format(
            self.client.job_results_directory, str('CV_JobResults'), str(
                self.commcell.commcell_id), str('0'), str(self.backup_copy_job.job_id))
        self.log.info(collect_path)
        # Check the collect files based on job type

        # Check for Extents and Container flag in CollectTot
        cmd = "cat  {0}/CollectTot* | grep %EXTENT%".format(collect_path)
        extent_output = self.client_machine.execute(cmd)
        cmd_container = "cat {0}/CollectTot* | grep %CONTAINER%".format(
            collect_path)
        container_output = self.client_machine.execute(cmd_container)
        extent_output_loop = extent_output.formatted_output
        container_loop = container_output.formatted_output
        self.log.info("Container output:")
        self.log.info(container_loop)
        # Maintain container only list and extent only list to compare flags
        # are sent correctly
        container_file_list = []
        extent_file_list = []
        # Splitting the collect file items to get the path list for extents or
        # ACLs
        for list1 in itertools.chain(
                extent_output_loop,
                container_loop):
            for innerlist in list1:
                subpaths = innerlist.split("/")
                self.log.info(subpaths)
                length = len(subpaths)
                if subpaths[0] == "%CONTAINER%":
                    lastword = subpaths[length - 1]
                    container_file_split = lastword.split(":")
                    container_file_list.append("/" + "/".join(subpaths[1:len(subpaths) - 1])
                                               + "/" + str(container_file_split[0]))
                    self.log.info(container_file_list)
                else:
                    file_list.append(
                        "/" + "/".join(subpaths[1:len(subpaths) - 1]))
                    extent_file_list.append(
                        "/" + "/".join(subpaths[1:len(subpaths) - 1]))
                    self.log.info(file_list)
                    self.log.info(extent_file_list)

        collect_list = list(set(file_list))
        container_cmp_list = list(set(container_file_list))
        extent_cmp_list = list(set(extent_file_list))
        if container_cmp_list:
            self.log.info("Comparing extent files against container list:")
            compare_result = self.client_machine.compare_lists(
                extent_cmp_list, container_cmp_list, True)
            if not compare_result:
                self.log.info(
                    "Extent back up file may not have associated container")
            else:
                self.log.info(
                    "Containers are sent correctly for extent backed up files!")
        self.log.info("collect list:")
        self.log.info(collect_list)
        self.log.info("source list:")
        self.log.info(source_list)
        result = False
        if len(source_list) == len(collect_list):
            result = self.client_machine.compare_lists(
                source_list, collect_list, True)
        if result:
            self.log.info("Collect file comparison is successful")
            return True

        self.log.info("Failed to compare the collect files")
        return False

    def validate_filters(self, unix_filters):
        """

        :type unix_filters: Provide the filter option for validation
        """
        try:
            # Get the job results directory
            collect_file_path = "{0}/{1}/{2}/{3}/{4}/{5}".format(
                self.client.job_results_directory, str('CV_JobResults'), str(
                    self.commcell.commcell_id), str('0'), str(
                        self.backup_copy_job.job_id), "CollectTot1.cvf")
            self.log.info(collect_file_path)

            self.log.info(unix_filters)

            for filter in unix_filters:
                if filter.replace(
                        '*', '') in self.client_machine.read_file(collect_file_path):
                    self.log.error(
                        "The filter %s is not being honoured ", filter)
                    raise Exception("The filter %s is not being honoured")
                self.log.info("The filters %s is  honoured ", filter)

        except Exception as excp:
            raise Exception(str(excp))

    def acceptance_tamplate(self, **kwargs):
        """
        Snap Acceptance template to be used for all test cases with different
        Unix configurations and snap engines

        Full SnapBackup -> Restore from Snapshot -> Incremental SnapBackup ->
        Backup Copy -> Restore from Tape - > Incremental SnapBackup ->
        Backup Copy -> Verify Mount Unmount -> Synth Full ->
        Restore from Synth Full

        Args:
            \*\*kwargs  (dict)          --  Optional keyword arguments

            Available kwargs options:

                instant_clone_options       (dict)  -- Options for performing an instant clone restore operation.
                The following key-value pairs are supported.

                    clone_mount_path        (str)   --  The path to which the snapshot needs to be mounted.
                    This  key is NOT OPTIONAL.

                    reservation_time        (int)   --  The amount of time, specified in seconds, that the mounted
                    snapshot needs to be reserved for before it is cleaned up.
                    This key is OPTIONAL.

                            Default :   3600

                    post_clone_script       (str)   --  The script that will run post clone.
                    This key is OPTIONAL.

                    clone_cleanup_script    (str)   --  The script that will run after clean up.
                    This key is OPTIONAL.

        """

        self.setup_snap_environment()
        self.snap_backup(backup_level.FULL)
        self.restore(Restore.RESTORE_FROM_SNAP.value, self.test_data_paths, inplace=False, **kwargs)
        self.verify_restore(self.client_machine,
                            self.test_data_paths,
                            dst_path=kwargs.get('restore_path', self.restore_path))

        # WILL PROCEED FURTHER ONLY IF INSTANT CLONE OPTIONS ISN'T SPECIFIED
        if not kwargs.get('instant_clone_options', False):
            self.snap_backup(backup_level.INCREMENTAL)
            self.backup_copy()
            self.restore(Restore.RESTORE_FROM_TAPE.value,
                         self.inc_data_paths, inplace=False
                         )
            self.snap_backup(backup_level.INCREMENTAL)
            self.snap_backup(backup_level.FULL, skip_data_creation=True)
            self.verify_mount_unmount(self.test_data_paths)
            self.snap_backup(backup_level.INCREMENTAL)
            self.backup_copy()
            self.snap_backup(backup_level.SYNTHETICFULL)
            self.restore(Restore.RESTORE_FROM_TAPE.value,
                         self.test_data_paths, inplace=False
                         )
            self.verify_restore(self.client_machine,
                                self.test_data_paths, self.restore_path)
        else:
            # WAIT FOR THE RESERVATION PERIOD FOR THE INSTANT CLONE TO EXPIRE
            self.log.info(f"Waiting {kwargs['instant_clone_options']['reservation_time']}s for snap to be unmounted.")
            time.sleep(kwargs['instant_clone_options']['reservation_time']+120)  # ADDING AN EXTRA 120 SECONDS
            op = self.client_machine.execute_command(f"df | grep {kwargs['restore_path']}").formatted_output
            if self.client_machine.execute_command(f"df | grep {kwargs['restore_path']}").formatted_output == '':
                self.log.info(f"Clone has been unmounted since df | grep {kwargs['restore_path']} returned nothing.")
            else:
                raise Exception('Clone either failed to be unmounted or we did not receive expected final output.')

        self.cleanup()

    def snap_extent_template(self, set_proxy_options=False):
        """

        Template to run extent test case for intellisnap

            Args:
                set_proxy_options      (bool)   --    True, if the proxy needed otherwise False.

        """

        self.log.info("*" * 20 + "Running with Skip Catalog Phase" + "*" * 20)

        self.setup_snap_environment()
        proxy_options = {
            'snap_proxy': self.tcinputs['Snap_Proxy'],
            'backupcopy_proxy': self.tcinputs['Backupcopy_Proxy'],
            'use_source_if_proxy_unreachable': True
        }
        if set_proxy_options:
            self.subclient.enable_intelli_snap(
                self.tcinputs['SnapEngine'], proxy_options)
        fsa = "FileSystemAgent"
        enable = "bEnableFileExtentBackup"
        slab = "mszFileExtentSlabs"
        slab_val = str(self.tcinputs.get("Slab", "1-1024=5"))
        self.log.info("01 : Enable feature by setting {} under {} on client."
                      .format(enable, fsa))
        self.client_machine.create_registry(fsa, enable, 1)
        self.log.info(
            "02 : Lowering threshold by setting {} under {} on client." .format(
                slab, fsa))
        self.client_machine.create_registry(fsa, slab, slab_val)
        source_list = self.add_data_to_path(self.test_data_paths)
        self.snap_backup(backup_level.FULL, skip_data_creation=True)
        self.backup_copy()
        self.verify_collect_extents(source_list)
        self.restore(Restore.RESTORE_FROM_TAPE.value,
                     self.test_data_paths, inplace=False
                     )
        self.verify_restore(self.client_machine,
                            self.test_data_paths,
                            self.restore_path
                            )
        remove_msg = "Removing registry entries {} and {} under {}".format(
            enable, slab, fsa)
        self.log.info(remove_msg)
        self.client_machine.remove_registry(fsa, enable)
        self.client_machine.remove_registry(fsa, slab)
        self.cleanup()
        self.log.info(
            "Snap Backup and restore with Extent Base Feature Test case completed Successfully")

    def check_volume_monitoring(self, volume):
        """
        Check the state of the volume for DC

            Args:
                volume         (str)       --   Volume which need to be check for monitoring.

            Returns:
                (bool)                     -- Returns True, if the volume is
                                             monitoring else raise exception.

        """
        base_dir = self.client_machine.get_registry_value('Base', 'dBASEHOME')
        script_arguments = "-basedir {0} -volume {1}".format(base_dir,
                                                             volume)
        repeat = True
        while repeat:
            output = self.client_machine.execute(
                UNIX_VOLUME_STATE, script_arguments)
            if output.exit_code:
                self.log.error(
                    'Error %s while executing the script',
                    output.output)
                raise Exception('Volume state checked fails')
            if output.output.rstrip() == "FULL_SCAN_ATTEMPTED" or output.output.rstrip(
            ) == "INCR_SCAN_ATTEMPTED":
                self.log.info(
                    "The DC scan is going on. We will wait for 5 mins")
                time.sleep(300)
            elif output.output.rstrip() == "MONITORING":
                self.log.info(
                    "volume %s is monitoring and ready for DC" %
                    volume)
                repeat = False
            elif output.output.rstrip() == "NOT_LISTED":
                self.log.info("Volume is not added to DC monitoring list")
                repeat = False
            else:
                self.log.error("%s", output.output)
                raise Exception("Volume can't be monitored for now")

    def get_backup_stream_count(self, job):
        """Returns the number of streams used by a backup job

                Args:
                    job    (object)  -- job object of the backup job to be checked

                Returns:
                    int   -   the number of streams used by a backup job

        """

        self.log.info("Getting the number of streams from job details")
        return int(job.details['jobDetail']['detailInfo']['numOfStreams'])

    def get_restore_stream_count(self, job, log_dir=None):
        """Returns the number of streams used by a restore job

                 Args:
                     job    (object)  -- job object of the restore job to be checked

                     log_dir  (str)  -- path of the log directory
                         default:None

                 Returns:
                     int   -   the number of streams used by a restore job

                 Raises:
                     Exception:
                         if any error occurred while getting the restore stream count

             """

        if log_dir is None:
            log_dir = self.client_machine.get_registry_value(
                'EventManager', 'dEVLOGDIR')

        jobid = job.job_id

        script_arguments = "-logdir {0} -jobid {1}".format(log_dir, str(jobid))

        output = self.client_machine.execute(
            UNIX_GET_RESTORE_STREAM_COUNT, script_arguments)

        if output.exit_code != 0:

            self.log.error(
                "Error occurred while getting the number of restore streams %s %s",
                output.output,
                output.exception)

            raise Exception(
                "Error occurred while getting the number of restore streams {0} {1}".format(
                    output.output, output.exception))
        else:
            result = output.output.strip('\n')

        return int(result)

    def verify_job_streams(self, job, no_of_streams, streams_used):
        """ Verifies if the job used expected number of streams

                 Args:
                    job (obj)                --  instance of the job class

                     no_of_streams (int)      --  expected number of streams to be used

                     streams_used (int)       --  actual number of streams used

                 Raises:
                     Exception - if the job didn't use expected streams

         """

        if streams_used == no_of_streams:
            self.log.info(
                "Job %s used %s streams as expected", str(
                    job.job_id), str(streams_used))
        else:
            self.log.error(
                "Job:%s used incorrect streams ExpectedStreams:%s ActualStreams:%s", str(
                    job.job_id), str(no_of_streams), str(streams_used))
            raise Exception(
                "Job:{0} used incorrect streams ExpectedStreams:{1} ActualStreams:{2}".format(
                    job.job_id, no_of_streams, streams_used))

    def iris_template(self, is_single_iris_instance=True, **kwargs):
        """
        Snap Acceptance template to be used for CACHEDB/IRISDB

        For Single IRIS Instance we would run the following
        Full SnapBackup -> Restore from Snapshot -> Backup Copy -> Restore from Tape

        For all IRIS Instances we would only run
        Full SnapBackup -> Restore from Snapshot

        Args:
            is_single_iris_instance    (bool)    -- run the template for single or all instances
            \*\*kwargs  (dict)          --  Optional keyword arguments
        """

        self.setup_snap_environment()
        self._generate_test_data()
        self.snap_backup(backup_level.FULL, skip_data_creation=True)
        self.restore(Restore.RESTORE_FROM_SNAP.value, self.test_data_paths, inplace=False, **kwargs)
        self.verify_restore(self.client_machine,
                            self.test_data_paths,
                            dst_path=kwargs.get('restore_path', self.restore_path))
        if is_single_iris_instance:
            self.backup_copy(subclient_level=True)
            """
            CACHEDB/IRIS data can only be browsed in logical format, 
            so we can't use the standard data paths during restore.
            Data created on the IRIS install path gets mapped under
            /%IRSIDB%/<INSTANCENAME>/INSTALL/IRISHEALTH
            So we must manipulate the path passed to restore for it to work
            """
            iris_restore_path = [ self.contents[0] + self.client_machine.os_sep + \
                                "INSTALL" + self.client_machine.os_sep + "IRISHEALTH" + \
                                self.client_machine.os_sep + self.epoch ]
            self.restore(Restore.RESTORE_FROM_TAPE.value, iris_restore_path, inplace=False, **kwargs)
            self.verify_restore(self.client_machine,
                                self.test_data_paths,
                                dst_path=kwargs.get('restore_path', self.restore_path))
        self.cleanup()
    