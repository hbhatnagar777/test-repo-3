# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module which contains the class to execute and validate browse/find and restore operations.

Validation:

    __init__()              --  Initializes the indexing validation DB class

    register_subclient()    --  Registers a subclient to the validation object

    record_job()            --  Scans the test data, calculates the modified/added/deleted items
    of the subclient and adds them into the SQLite DB for validation

    validate_browse_restore()-- Performs browse & restore operation and validates the
    results of both

    validate_browse()       --  Performs browse/find/version operation and validates the actual
    and expected results

    validate_browse_recursive() --  Performs browse operation recursively and validates the result

    validate_restore()      --  Performs restore operation and verifies the actual and
    expected results

    do_after_aux_copy()     --  Update validation DB after running auxiliary copy for a job

    do_after_backup_copy()  --  Update validation DB after running backup copy for a storage policy

    do_after_data_aging()   --  Marks jobs are aged in the validation DB. The jobs will not be
    considered for browse and restore for validation

    do_age_jobs()           --  Marks jobs are aged in the validation DB. These jobs will not be considered for
    browse and restore validation

    do_age_jobs_storage_policy() -- Picks the jobs to aged based on the cycle to retain and marks them as aged in
    the validation DB

    do_delete_items()       --  Marks the given list of items as erased in the the validation DB.
    The items will then be not considered for browse and restore validation

    get_items()             --  Queries the validation DB and returns items which match as per
    the parameters passed.

    cleanup()               --  Closes and deletes the validation DB directory

"""

import os
import time
import json
import shutil
import re
import xmltodict
import random
import threading

from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils import machine
from AutomationUtils import commonutils
from AutomationUtils import idautils
from AutomationUtils import options_selector

from cvpysdk.job import Job
from cvpysdk.commcell import Commcell
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient


class FSBrowseRestore(object):
    """This class is used to validate browse and results for backupset/subclient.
    Supported clients for now are Windows, Unix and NAS

    Usage:
    ======
        1) - Initialize the validation class with commcell and backupset objects
            >>> idx = FSBrowseRestore({
            >>>     'commcell' : '<commcell_pysdk_object>',
            >>>     'backupset': '<backupset_pysdk_object>'
            >>> })

        2) - Register the subclients and some of its properties related to validation class.
            >>> idx.register_subclient('<subclient_obj>', '{subclient_props}')

        3) - When the backup job completes for the subclient, record the job for validation
            >>> idx.record_job('<job_obj>')

        4) - Validate browse, restore using the validate_* methods
            >>> idx.validate_browse('{browse_options}')
            >>> idx.validate_restore('{restore_options}')

    """

    def __init__(self, config):
        """Initializes the Browse & Restore validation object

            Args:
                config          (dict)          Dictionary of backupset under validation

            Example:
                Validation({
                    'commcell': <commcell_pysdk_object>,
                    'backupset': <backupset_pysdk_object>,
                    'debug': True
                })

            Returns:
                The validation class object

            Raises:
                Exception when the commcell and backupset objects are not PySDK objects

        """

        self.log = logger.get_log()
        self._config = config
        self._commcell = config['commcell']
        self._client = None
        self._backupset = None
        self._agent = None

        self._client_os = None
        self._client_machine = None
        self._delim = None
        self._restore_clients = dict()

        self._repo_dir = config.get('repo_dir', None)
        self._debug = config.get('debug', False)
        self._last_restore_directory = None

        self._browse_count = FSBrowseRestore.Counter(0)
        self._restore_count = FSBrowseRestore.Counter(0)

        self.client_obj = None
        self.backupset_obj = config['backupset']
        self.agent_obj = None
        self.subclients = {}

        if not isinstance(self._commcell, Commcell):
            raise Exception('Commcell object is expected as argument for validation class')

        if not isinstance(self.backupset_obj, Backupset):
            raise Exception('Backupset object is expected as argument for validation class')

        self._initialize_entities()
        self._initialize_repo()
        self._initialize_validation_db()

        self._cv_utils = idautils.CommonUtils(self._commcell)
        self._options_help = options_selector.OptionsSelector(self._commcell)

        self._has_failure = False
        self._has_stop_browse = False

        self.log.info(
            'Indexing verification object created successfully for [{0}->{1}->{2}] '
            'Repository path [{3}]\n'.format(
                self._client,
                self._agent,
                self._backupset,
                self._repo_dir))

        self.default_options = {
            'subclient': None,
            'operation': 'find',
            'from_time': 0,
            'to_time': 0,
            'path': '\\**\\*',
            'filters': [],
            'show_deleted': False,
            'job_id': 0,
            'media_agent': '',
            'copy_precedence': 0,
            'include_aged_data': False,
            'include_hidden': False,
            'include_running_jobs': False,
            'compute_folder_size': False,
            'page_size': 10000,

            '_version_number': 0,
            '_is_restore': False,
            '_verify_size': 'skip_auto',
            '_verify_jobid': True,
            '_verify_jobid_directory': True,
            '_verify_live_browse': False,
            '_verify_volume_level': False,
            '_exclude_jobs': [],
            '_mount_point_level': 2,
            '_item_type': 'all',
            '_raw_response': True,

            'restore': {
                'do': False,
                'dest_client': None,
                'dest_path': '',
                'source_items': ['\\'],
                'select_version': 0,
                'media_agent': '',
                'in_place': False,
                'snap_mount_client': '',
                'preserve_level': 1,
                'no_of_streams': 10,
                '_force_dest_path': ''
            }
        }

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    @property
    def repo_dir(self):
        return self._repo_dir

    @property
    def restore_clients(self):
        return self._restore_clients

    @property
    def last_restore_directory(self):
        return self._last_restore_directory

    @last_restore_directory.setter
    def last_restore_directory(self, value):
        self._last_restore_directory = value

    def _initialize_entities(self):
        """Initializes the CvPySDK client, agent and backupset object entities"""

        self.agent_obj = self.backupset_obj._agent_object
        self.client_obj = self.backupset_obj._client_object

        self._client = self.client_obj.client_name
        self._agent = self.agent_obj.agent_name
        self._backupset = self.backupset_obj.backupset_name

        client_name = self._client
        full_client_os = self.client_obj.os_info.lower()

        if 'windows' in full_client_os:
            self._client_os = 'windows'

        if 'unix' in full_client_os:
            self._client_os = 'unix'

        if 'nas' in full_client_os:
            self._client_os = 'nas'
            client_name = self._commcell.commserv_name

        self._client_machine = machine.Machine(client_name, self._commcell)
        self._delim = self._client_machine.os_sep

        self.log.info('Client, agent and backupset object initialized successfully')

    def _initialize_repo(self):
        """Initializes the repository folder where the validation data DB is stored"""

        if self._repo_dir is None:
            dir_name = self._client + '_' + self._backupset
            self._repo_dir = os.path.join(
                logger.get_log_dir(), 'Indexing', dir_name, str(int(time.time())))
            os.makedirs(self._repo_dir)

    def _initialize_validation_db(self):
        """Initializes and creates the SQLite DB in repository folder for storing
            the backup data"""

        self._db_path = os.path.join(self._repo_dir, 'validation.db')
        does_db_exist = os.path.exists(self._db_path)

        if does_db_exist:
            self.log.info('Validation DB is already created [{0}]'.format(self._db_path))

        self.db = database_helper.SQLite(self._db_path, check_same_thread=False)

        if does_db_exist:
            return True

        self.db.execute('''CREATE TABLE indexing
                   (
                    path        TEXT        NOT NULL,
                    parent      TEXT        NOT NULL,
                    name        TEXT        NOT NULL,
                    type        TEXT        NOT NULL,
                    size        INTEGER     NOT NULL,
                    mtime       INTEGER     NOT NULL,
                    status      TEXT        NOT NULL,
                    subclient   TEXT        NOT NULL,
                    cycle       INTEGER     NOT NULL,
                    jobid       INTEGER     NULL,
                    cjobid      INTEGER     NULL,
                    jobendtime  INTEGER     NULL,
                    jobtype     TEXT        NULL,
                    sp          TEXT        NULL,
                    erased      TEXT        NULL
                   );''')

        self.db.execute('''CREATE TABLE spcopy
                   (
                    sp          TEXT        NOT NULL,
                    jobid       INTEGER     NOT NULL,
                    copy        INTEGER     NOT NULL,
                    aged        TEXT        NULL
                   );''')

        self.log.info('Indexing validation tables are created successfully')

    def _initialize_restore_client(self, restore_client):
        """Initializes the machine object of the client which is selected for restore

            Args:
                restore_client      (str)       Destination restore client name

            Returns:
                None

        """

        if restore_client in self._restore_clients:
            return None

        self.log.info('Initializing restore client [{0}]'.format(restore_client))

        if restore_client is self._client:
            self._restore_clients[restore_client] = {
                'machine': self._client_machine,
                'delim': self._delim,
                'os': self._client_os,
                'obj': self.client_obj,
                'restore_path': None
            }

        else:

            self.log.info('Creating restore client machine objects [{0}]'.format(restore_client))

            rst_client_obj = self._commcell.clients.get(restore_client)
            full_client_os = rst_client_obj.os_info.lower()

            rst_client_machine = machine.Machine(restore_client, self._commcell)
            rst_client_delim = rst_client_machine.os_sep
            rst_client_obj = self._commcell.clients.get(restore_client)
            rst_client_os = None

            if 'windows' in full_client_os:
                rst_client_os = 'windows'

            if 'unix' in full_client_os:
                rst_client_os = 'unix'

            if 'nas' in full_client_os:
                rst_client_os = 'nas'

            self._restore_clients[restore_client] = {
                'machine': rst_client_machine,
                'delim': rst_client_delim,
                'os': rst_client_os,
                'obj': rst_client_obj,
                'restore_path': None
            }

        if self._restore_clients[restore_client]['os'] in ['windows', 'unix']:
            rc_delim = self._restore_clients[restore_client]['delim']
            rc_machine = self._restore_clients[restore_client]['machine']
            free_drive = self._options_help.get_drive(rc_machine)
            free_drive = commonutils.remove_trailing_sep(free_drive, rc_delim)

            self._restore_clients[restore_client]['restore_path'] = rc_delim.join(
                [free_drive, 'automation', 'restores'])

    def _set_default_options(self, options=None):
        """Initializes the options dictionary with the default values"""

        options = dict() if options is None else dict(options)

        # Set default values
        commonutils.set_defaults(options, self.default_options)

        # Set restore options
        if options['restore']['do']:
            if options['restore']['select_version'] > 0:
                v_tag = '|\\|#15!vErSiOnS|#15!\\'.replace('\\', self._delim)
                version_tag = v_tag + str(options['restore']['select_version'])
                if version_tag not in options['restore']['source_items']:
                    options['restore']['source_items'].append(version_tag)

        if options['job_id'] != 0:
            job_obj = Job(self._commcell, options['job_id'])
            options['from_time'] = job_obj.start_timestamp
            options['to_time'] = job_obj.end_timestamp

        return options

    def _get_index_path(self, path):
        """Translates the given path to a similar format as stored in Index"""

        if self._client_os == 'windows':
            if path[:2] == '\\\\':
                return '\\UNC-NT_' + path[2:]
            else:
                return commonutils.add_prefix_sep(path, self._delim)

        if self._client_os == 'unix':
            return commonutils.add_prefix_sep(path, self._delim)

        if self._client_os == 'nas':
            return path

    def _read_collect_file(self, subclient, file_type):
        """Reads the collect file maintained by validation object to find modified testdata"""

        col_file = self.subclients[subclient]['collect_files'][file_type]

        if not os.path.isfile(col_file):
            return {}

        with open(col_file) as col_file_hdl:
            try:
                col_file_dict = json.load(col_file_hdl)
            except ValueError:
                col_file_dict = {}

        return col_file_dict

    def _write_collect_file(self, subclient, file_type, content):
        """Writes to the local collect file maintained to track modified testdata"""

        if not isinstance(content, dict):
            raise Exception('Collect file content to write is not a dictionary')

        if subclient not in self.subclients:
            raise Exception('Subclient [{0}] not a registered for validation'.format(subclient))

        col_file_path = self.subclients[subclient]['collect_files'][file_type]

        try:
            with open(col_file_path, 'w') as col_file_hdl:
                col_file_hdl.write(json.dumps(content))
        except IOError as e:
            raise Exception('Cannot write collect file: [{0}]'.format(e))

    def _get_latest_cycle(self, subclient, from_time=0, to_time=0, copy_precedence=0):
        """Returns the latest cycle for the given subclient"""

        if to_time == 0:
            to_time = self._get_latest_backup_time()

        query = ("select max(cycle) from indexing where "
                 "jobendtime between {0} and {1} and subclient = '{2}'".format(
                    from_time, to_time, subclient))

        if copy_precedence not in (0, 1):
            query += ' and jobid in ( select jobid from spcopy where copy = {0} )'.format(
                copy_precedence)

        response = self.db.execute(query)

        cycle_no = 0
        if response.rowcount != 0:
            cycle_no = response.rows[0][0]

        return cycle_no

    def _get_latest_backup_time(self):
        """Returns the latest job's backup time from validation DB"""

        query = 'select max(jobendtime) from indexing'

        response = self.db.execute(query)

        latest_time = int(time.time())
        if response.rowcount != 0:
            latest_time = response.rows[0][0]

        return int(latest_time)

    def _has_backup_copy(self, to_time, sp='', subclient=''):
        """Checks if backup copy happened for the given subclient, end time and storage policy"""

        sp_query = ''
        subclient_query = ''

        if sp != '':
            sp_query = "and spcopy.sp = '{0}'".format(sp)

        if subclient is not None:
            subclient_query = "and indexing.subclient = '{0}'".format(subclient)

        query = ('select copy from spcopy join indexing where indexing.jobid = spcopy.jobid and '
                 'indexing.jobendtime <= {0} {1} {2} '
                 'order by indexing.jobid desc, spcopy.copy desc limit 1'.format(
                    to_time, sp_query, subclient_query))

        self.log.info('Backup copy check query [{0}]'.format(query))

        response = self.db.execute(query)

        if response.rowcount != 0:
            copy = str(response.rows[0][0])
            self.log.info('Latest available copy is [{0}]'.format(copy))
            if copy == '1':
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def _get_filter_timestamps(day):
        """TODO"""
        return day

    def _stop_browse(self, path):
        """Checks if recursive browse has to stop for the given directory"""

        if not self._has_stop_browse:
            return False

        path = commonutils.add_prefix_sep(path, self._delim)
        query = 'select name from indexing where parent = "{0}"'.format(path)
        response = self.db.execute(query)

        for row in response.rows:
            name = row[0]
            if 'stop_browse.txt' in name:
                return True

        return False

    def _print_result_difference(self, actual_results, expected_results):
        """Prints the difference between the actual and expected results dictionaries"""

        added, removed, modified = commonutils.get_dictionary_difference(
            actual_results, expected_results)

        self.log.info('-' * 80)
        self.log.info('Actual results [%s] items: %s', len(actual_results), json.dumps(actual_results))
        self.log.info('Expected results [%s] items: %s', len(expected_results), json.dumps(expected_results))
        self.log.info('Only in Actual results [%s] items: %s', len(added), str(added))
        self.log.info('Only in expected results [%s] items: %s', len(removed), str(removed))
        self.log.info('Modified [%s] items: %s', len(modified), str(modified))
        self.log.info('-' * 80)

    def _is_file_path(self, path):
        """Checks if the given path is a file or folder"""

        last_item = path.split(self._delim)[-1]
        name, ext = os.path.splitext(last_item)

        if 'UNC-NT_' in last_item:
            return False

        if ext == '':
            return False
        else:
            return True

    def _scan_test_data(self, subclient):
        """Scans the testdata directory of the given subclient

            Args:
                subclient       (str)           Subclient Name

            Returns:
                Dictionary of scanned items of below format
                {
                    'item_1_path': {
                        'parent': 'item_parent',
                        'type': 'item_type',
                        'size': 'item_size',
                        'mtime': 'item_mtime'
                    }
                }

        """

        sc_content = self.subclients[subclient]['content']
        scanned_items = {}

        for sc_path in sc_content:
            self.log.info('Scanning folder [{0}]'.format(sc_path))
            root_size = 0
            root_mtime = 0
            scan_items_list = self._client_machine.scan_directory(sc_path)

            for item in scan_items_list:
                path = self._get_index_path(item['path'])
                size = item['size']
                i_type = item['type']
                mtime = item['mtime']
                root_size += int(size) if i_type == 'file' else 0
                root_mtime = max(root_mtime, int(mtime))
                scanned_items[path] = {
                    'parent': commonutils.get_parent_path(path, self._delim),
                    'type': i_type,
                    'size': size,
                    'mtime': mtime
                }

            sc_path_index = self._get_index_path(sc_path)
            sc_path_split = sc_path_index.split(self._delim)

            for i in range(len(sc_path_split)):
                item = self._delim.join(sc_path_split)
                item_parent = commonutils.get_parent_path(item, self._delim)
                if item == '':
                    continue
                if item == item_parent:  # UNC, NAS case
                    continue
                scanned_items[item] = {
                    'parent': item_parent,
                    'type': 'directory',
                    'size': root_size,
                    'mtime': root_mtime
                }
                sc_path_split.pop()

        if self._debug:
            self.log.info(json.dumps(scanned_items))

        return scanned_items

    def _scan_restore_data(self, dest_path, restore_client):
        """Scans the restored data directory for the given path and client

            Args:
                dest_path       (str)           Destination restore directory
                restore_client  (str)           Restore client name

            Returns:
                Dictionary of scanned items of below format
                {
                    'item_i_path': {
                        'parent': 'item_parent',
                        'type': 'item_type',
                        'size': 'item_size'
                    }
                }

        """

        restored_data = {}
        rst_client = self._restore_clients[restore_client]
        rc_machine = rst_client['machine']

        scan_items_list = rc_machine.scan_directory(dest_path)

        for item in scan_items_list:
            path = item['path']
            size = item['size']
            type = item['type']

            if self._client_os == 'nas' and 'restore_symboltable' in path:
                continue

            if type != 'file':
                continue

            restored_data[path] = commonutils.get_int(size)

        if self._debug:
            self.log.info(json.dumps(restored_data))

        return restored_data

    def _identify_testdata_changes(self, scan_items, job_info):
        """Identify items which are added, modified & deleted from the scan list"""

        subclient = job_info['subclient']
        job_id = job_info['job_id']
        job_type = job_info['job_type']
        job_endtime = job_info['job_endtime']
        cycle = job_info['cycle']

        final_items = dict()
        col_items = dict()

        if job_type == 'full':
            cycle += 1
            self.subclients[subclient]['current_cycle'] = cycle
            col_items = {}

        if job_type == 'incremental':
            col_items = self._read_collect_file(subclient, 'inc')

        if job_type == 'differential':
            col_items = self._read_collect_file(subclient, 'full')

        for sitem in scan_items:
            prop = scan_items[sitem]
            final_items[sitem] = []
            version = {
                'type': prop['type'],
                'size': prop['size'],
                'mtime': prop['mtime'],
                'parent': prop['parent'],
                'subclient': subclient,
                'jobid': job_id,
                'jobtype': job_type,
                'jobendtime': job_endtime,
                'cycle': cycle,
                'cjobid': '',
            }

            if sitem not in col_items:
                version['status'] = 'new'
            else:
                cprop = col_items[sitem]
                if cprop['size'] != prop['size'] or cprop['mtime'] != prop['mtime']:
                    version['status'] = 'modified'

            final_items[sitem].append(version)

        # Identify deletions
        for citem in col_items:
            prop = col_items[citem]
            if citem not in scan_items:
                final_items[citem] = []
                version = {
                    'type': prop['type'],
                    'size': prop['size'],
                    'mtime': prop['mtime'],
                    'parent': prop['parent'],
                    'status': 'deleted',
                    'subclient': subclient,
                    'jobid': job_id,
                    'jobtype': job_type,
                    'jobendtime': job_endtime,
                    'cycle': cycle,
                    'cjobid': '',
                }
                final_items[citem].append(version)

        if job_type in ['full', 'differential']:
            col_items_inc = self._read_collect_file(subclient, 'inc')
            for citem_inc in col_items_inc:
                prop = col_items_inc[citem_inc]
                if citem_inc not in final_items:
                    final_items[citem_inc] = []
                    version = {
                        'type': prop['type'],
                        'size': prop['size'],
                        'mtime': prop['mtime'],
                        'parent': prop['parent'],
                        'status': 'deleted',
                        'subclient': subclient,
                        'jobid': job_id,
                        'jobtype': job_type,
                        'jobendtime': job_endtime,
                        'cycle': cycle,
                        'cjobid': '',
                    }
                    final_items[citem_inc].append(version)

        if self._debug:
            self.log.info(json.dumps(final_items))

        return final_items

    def _filter_scan_results(self, scan_items, job_type):

        # Filter eligible files from the scanned dictionary
        filter_items = {}
        for fitem in scan_items.keys():
            version = scan_items[fitem][-1]

            '''
                For windows:
                    1. Select new/modified files
                    2. Recursively add its parent folders

                For Unix:
                    1. Select new/modified/deleted files
                    2. Recursively add its parent folders
            '''

            # Select files which are new/modified and also deleted file if it is unix OS
            if 'status' in version and version['type'] == 'file' and (
                    version['status'] != 'deleted' or self._client_os in ['unix', 'nas']):

                # Add the file to the list
                filter_items[fitem] = scan_items[fitem]

                # Add the root paths of this file to the list
                cur_parent = version['parent']
                cur_parent_split = cur_parent.split(self._delim)

                for i in range(len(cur_parent_split)):

                    p_parent = self._delim.join(cur_parent_split)
                    if p_parent == '':
                        break

                    # if parent itself is deleted, do not add it, instead continue
                    # and add its grand parents which are only modified

                    if ('status' in scan_items[p_parent][-1]
                            and scan_items[p_parent][-1]['status'] == 'deleted'):
                        cur_parent_split.pop()
                        continue

                    # Add the parent to the list
                    if p_parent not in filter_items:
                        filter_items[p_parent] = scan_items[p_parent]
                        filter_items[p_parent][-1]['status'] = 'modified'

                    cur_parent_split.pop()

            # Add all the items which are marked deleted
            if 'status' in version and version['status'] == 'deleted':
                filter_items[fitem] = scan_items[fitem]

            '''
                Adding folders which are not covered by above method

                How emtpy folders are backed up ?

                Type\platform                    |   Win     |    Unix
                --------------------------------------------------------
                New empty dir (FULL backup)      |   Yes     |    Yes
                New empty dir (INC backup)       |   No      |    Yes
                Folder became empty              |   No      |    Yes
                Nothing changed in dir           |   No      |    No

            '''

            # Add all the folders which are new ( for empty folder case )
            if ('status' in version and version['type'] == 'directory'
                    and version['status'] == 'new'):

                if (self._client_os in ['windows']
                        and job_type in ['full']) or self._client_os not in ['windows']:
                    filter_items[fitem] = scan_items[fitem]

            # For Unix alone add folders which are modified
            # ( like, a file is deleted but other items are not modified )

            if ('status' in version and version['type'] == 'directory'
                    and self._client_os in ['unix']):
                filter_items[fitem] = scan_items[fitem]

        if self._debug:
            self.log.info(json.dumps(filter_items))

        return filter_items

    def _insert_into_db(self, scanned_items):
        """Inserts the scanned test data items into the SQLite DB for validation

            Args:
                scanned_items       (dict)          Dictionary of scanned items

            Returns:
                None

        """

        self.log.info('Inserting scanned items into DB')
        insert_values = []

        for path in scanned_items:
            versions = scanned_items[path]
            name = path.split(self._delim)[-1]

            for ver in versions:
                sp_name = self.subclients[ver['subclient']]['sp']

                if name in 'stop_browse.txt':
                    self._has_stop_browse = True

                if 'status' in ver:
                    insert_values.append(
                        (
                            path,              ver['parent'],      name,
                            ver['type'],       ver['size'],        ver['mtime'],
                            ver['status'],     ver['subclient'],   ver['jobid'],
                            ver['jobtype'],    ver['jobendtime'],  ver['cycle'],
                            ver['cjobid'],     sp_name,            'no'
                         )
                    )

        inserted_records = len(insert_values)

        self.db.execute(
            "INSERT INTO indexing "
            "( path, parent, name, type, size, mtime, status, subclient, jobid, "
            "jobtype, jobendtime, cycle, cjobid, sp, erased ) VALUES "
            "( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", insert_values)

        self.log.info(
            'Validation DB updated successfully. Inserted [{0}] items into DB'.format(
                inserted_records))

    def _insert_into_spcopy(self, sp, job_id, copy):
        """Inserts the SP, Copy and job_id in spcopy table

            Args:
                sp          (str)           Storage policy name of the subclient
                job_id      (int)           Job ID to be inserted
                copy        (int)           Copy ID of the job

            Returns:
                None

        """

        copy = 1 if copy is None else copy

        values = (sp, job_id, copy)
        self.db.execute(
            'insert into spcopy ( sp, jobid, copy, aged ) values ( ?, ?, ?, "no" )', values)

        self.log.info('Inserted job copy details in spcopy table {0}'.format(str(values)))

    def _prepare_browse_sql_query(self, options):
        """Prepares the SQL query for the browse/find operation to get the expected results"""

        if len(self.subclients) == 0:
            raise Exception('No subclients registered for validation !')

        operation = options['operation'].lower()
        subclient = options['subclient']
        from_time = options['from_time']
        to_time = options['to_time']
        browse_path = options['path']
        filters = options['filters']
        job_id = options['job_id']
        copy_precedence = options['copy_precedence']
        exclude_jobs = options['_exclude_jobs']
        item_type = options['_item_type']
        is_restore = options['_is_restore']

        for paths in ['\\', '/']:
            browse_path = browse_path.replace(paths, self._delim)

        # Initializing the path
        if browse_path != self._delim:
            browse_path = commonutils.remove_trailing_sep(browse_path, self._delim)
            browse_path = commonutils.add_prefix_sep(browse_path, self._delim)

        operators = {
            'LT': '<',
            'GT': '>',
            'LTE': '<=',
            'GTE': '>='
        }

        # Initializing the filters
        filter_query_list = []
        for filter in filters:
            temp_query = ''
            if filter[0] == 'FileSize':
                operator = filter[2]
                op = operators.get(operator, '')
                temp_query = ' and (size ' + op + ' ' + str(filter[1]) + ' and type="file"'

            if filter[0] == 'ModifiedDate':
                day = filter[1]
                from_date, to_date = self._get_filter_timestamps(day)
                temp_query = 'and (mtime between ' + str(from_date) + ' and ' + str(to_date)

            if filter[0] == 'FileName':
                f_name = '*' + filter[1] + '*' if '*' not in filter[1] else filter[1]
                temp_query = ' and (name like "' + f_name.replace('*', '%') + '"'

            # During filtered browse include directories in SQL result
            if operation == 'browse':
                temp_query += ' or type = "directory")'
            else:
                temp_query += ')'

            filter_query_list.append(temp_query)

        # Set to time if not set
        if to_time == 0:
            to_time = self._get_latest_backup_time()

        query = 'select * from indexing where jobendtime between {0} and {1} '.format(
            from_time, to_time
        )

        # Filter by job id if set in request
        if job_id != 0:
            query += ' and ( jobId = {0} or status = "deleted" ) '.format(job_id)

        if operation == 'find':
            browse_path = browse_path.replace(self._delim + '**' + self._delim + '*', '')
            browse_path = browse_path.replace('*', '%')
            query = query + ' and path like "%{0}%" '.format(browse_path)

        if operation == 'versions':
            query = query + ' and path like "%{0}%" '.format(browse_path)

        if operation in ['browse', 'find']:
            for fQuery in filter_query_list:
                query = query + fQuery

        # Add subclient to query
        if subclient is not None:
            query += ' and subclient="{0}" '.format(subclient)

        # Add exclude jobs query
        if len(exclude_jobs) > 0:
            query += ' and ( jobid not in ( ' + (','.join(exclude_jobs)) + ')  ) '

        # Add item type to query
        if item_type != 'all':
            query += ' and type="{0}" '.format(item_type)

        cycle_restriction = True

        # Handlers for deleted items
        '''
            NAS NDMP - Deleted items are always not marked
            NAS Snap - Snap copy - Deleted items are marked
            NAS Snap - Backup copy - Deleted items are marked

            Block - Snap copy - Deleted items are marked
            Block - Backup copy - Deleted items are marked

            FS Snap - Snap copy - Deleted items are marked
            FS Snap - Backup copy - Deleted folders alone are not marked
        '''

        if subclient is None:
            for sc in self.subclients:
                mode = self.subclients[sc]['mode']

                if mode == 'nas_ndmp' and not is_restore:
                    query += ' and ( status <> "deleted" and subclient = "' + sc + '" )'

                if mode == 'nas_snap':
                    pass

                if mode == 'fs_block':
                    pass

                if mode == 'fs_snap':
                    if self._has_backup_copy(to_time, self.subclients[sc]['sp'], sc):
                        query += ' and ( ( status <> "deleted" and type = "directory" ) ' \
                                 'or type = "file" and subclient = "' + sc + '" ) '

                if mode == 'fs_snap_skipcatalog':
                    if self._has_backup_copy(to_time, self.subclients[sc]['sp'], sc):
                        query += ' and ( status <> "deleted" and subclient = "' + sc + '" ) '
        else:
            mode = self.subclients[subclient]['mode']

            if mode == 'nas_ndmp' and not is_restore:
                query += ' and status <> "deleted" '

            if mode == 'nas_snap':
                pass

            if mode == 'fs_block':
                pass

            if mode == 'fs_snap':
                if self._has_backup_copy(to_time, self.subclients[subclient]['sp']):
                    query += ' and ( ( status <> "deleted" and type = "directory" )' \
                             ' or type = "file" ) '

            if mode == 'fs_snap_skipcatalog':
                if self._has_backup_copy(to_time, self.subclients[subclient]['sp']):
                    query += ' and status <> "deleted" '

        # Add copy precedence query
        if copy_precedence not in [0, 1]:
            query += ' and ( jobid in ( select jobid from spcopy where copy = {0} ) )'.format(
                copy_precedence
            )

        # Restrict indexing to latest cycle in that timerange when from_time is not set
        if from_time == 0 and cycle_restriction:
            self.log.info(
                'Restricting browse to latest cycle in that timerange since from_time is not set')

            # Backupset level operation
            if subclient is None:
                sc_cycles_list = []
                for sc in self.subclients:
                    cycle_to_restrict = self._get_latest_cycle(
                        sc,
                        from_time,
                        to_time,
                        copy_precedence
                    )

                    sc_cycles_list.append(' ( subclient = "' + sc + '" and cycle = "' +
                                          str(cycle_to_restrict) + '" ) ')

                sc_cycle_query = ' and ( ' + ('or'.join(sc_cycles_list)) + ' )'
                query += sc_cycle_query
            else:
                cycle_to_restrict = self._get_latest_cycle(
                    subclient,
                    from_time,
                    to_time,
                    copy_precedence
                )
                query += ' and cycle="' + str(cycle_to_restrict) + '"'

        return query

    def _get_directories_and_size(self, browse_query_result, include_deleted=False):
        """Prepares a dictionary of all the directories and its size from the
        browse query result"""

        directories = dict()

        for item in browse_query_result:
            version = browse_query_result[item][-1]  # Take the latest version
            if version['type'] == 'file':
                if version['status'] == 'deleted' and not include_deleted:
                    continue
                else:
                    cur_parent = version['parent']
                    cur_parent_split = cur_parent.split(self._delim)

                    for i in range(len(cur_parent_split)):
                        cur_parent_join = self._delim.join(cur_parent_split)
                        cur_parent_join = (
                            self._delim
                            if cur_parent_join == ''
                            else cur_parent_join
                        )

                        if cur_parent_join in directories:
                            directories[cur_parent_join] += int(version['size'])
                        else:
                            directories[cur_parent_join] = int(version['size'])

                        cur_parent_split.pop()

        if self._debug:
            self.log.info(directories)

        return directories

    def _query_db(self, query, versions, sfull_props, deleted_time_threshold):
        """Queries the validation DB and returns the list of items matching the query

            Args:
                query                   (str)       SQL query to run on validation DB
                versions                (int)       No of versions to select for an item
                sfull_props             (dict)      SFULL job details
                deleted_time_threshold  (int)       Threshold to carry forward the deleted items

            Returns:
                Dictionary of items which comes as a result of SQL query. Format:
                {
                    'item_path': [{item_1_props} ... {items_n_props}]
                }

        """

        if 'select * from indexing' not in query:
            self.log.error('Invalid DB query')
            return {}
        else:
            # Add clause to not include items from aged jobs
            query += (' and ( jobid in ( select distinct jobid from spcopy'
                      ' where aged <> "yes" ) or status = "deleted" ) and erased <> "yes"'
                      ' order by jobid asc')

        query_list = dict()
        is_sfull = False

        self.log.info('Querying DB - [{0}]'.format(str(query)))
        resp = self.db.execute(query)

        if sfull_props:
            is_sfull = True

        for row in resp.rows:
            path = resp.get_column(row, 'path')
            version = dict()
            version['type'] = resp.get_column(row, 'type')
            version['size'] = resp.get_column(row, 'size') if version['type'] == 'file' else 0
            version['mtime'] = resp.get_column(row, 'mtime')
            version['parent'] = resp.get_column(row, 'parent')
            version['status'] = resp.get_column(row, 'status')
            version['subclient'] = resp.get_column(row, 'subclient')
            version['jobid'] = resp.get_column(row, 'jobid')
            version['jobtype'] = resp.get_column(row, 'jobtype')
            version['jobendtime'] = resp.get_column(row, 'jobendtime')
            version['cycle'] = resp.get_column(row, 'cycle')
            version['cjobid'] = resp.get_column(row, 'cjobid')

            if is_sfull:
                version['jobtype'] = 'SFULL'
                version['cjobid'] = version['jobid']
                version['jobid'] = sfull_props['jobid']
                version['cycle'] = sfull_props['cycle']
                version['jobendtime'] = sfull_props['jobendtime']

            if version['status'] == 'deleted':
                if path in query_list:
                    query_list[path][-1]['status'] = 'deleted'
                    query_list[path][-1]['deletedtime'] = version['jobendtime']
            else:
                if path not in query_list:
                    query_list[path] = []
                    query_list[path].append(version)
                else:

                    item_versions = query_list[path]

                    # Pop if version stack is full
                    if len(item_versions) == versions:
                        query_list[path].pop(0)

                    # Pop duplicate versions
                    if len(item_versions) != 0:
                        for i_ver in list(item_versions):
                            if (i_ver['mtime'] == version['mtime'] and
                                    i_ver['size'] == version['size']):
                                query_list[path].remove(i_ver)

                    query_list[path].append(version)

        if self._debug:
            self.log.info(json.dumps(query_list))

        # Go through the final list and remove items which are out of image
        # as per the deleted item carry forward threshold
        if is_sfull:

            items = list(query_list)
            self.log.info('Current time [{0}], deleted item threshold [{1}]'.format(
                str(int(time.time())), str(deleted_time_threshold)))

            for item in items:

                if query_list[item][-1]['status'] == 'deleted':

                    current_time = int(time.time())
                    deleted_time = int(query_list[item][-1]['deletedtime'])
                    should_drop = (current_time - deleted_time > int(deleted_time_threshold))

                    if self._debug:
                        self.log.info(json.dumps({
                            'item': item,
                            'current_time': current_time,
                            'deleted_time': deleted_time,
                            'threshold': deleted_time_threshold,
                            'should_drop': should_drop
                        }))

                    # Check if the last deleted version is qualified for carry forward
                    if should_drop:
                        query_list.pop(item, None)  # deleted file not qualified so delete it

                    else:
                        # if deleted file is qualified, make it active and
                        # add another version to mark it deleted
                        # add a version to mark it delete
                        query_list[item].append(dict(query_list[item][-1]))

                        # make the last previous version as the active one
                        query_list[item][-2]['status'] = 'modified'

        return query_list

    def _get_browse_expected_results(self, options):
        """Gets the expected browse results for the given browse options"""

        operation = options['operation'].lower()
        browse_path = options['path']
        show_deleted = options['show_deleted']
        version_number = options['_version_number']
        is_restore = options['_is_restore']
        filters = options['filters']
        query_versions = 9999 if operation == 'versions' else 1

        for paths in ['\\', '/']:
            browse_path = browse_path.replace(paths, self._delim)

        # Initializing the path
        if browse_path != self._delim:
            browse_path = commonutils.remove_trailing_sep(browse_path, self._delim)
            browse_path = commonutils.add_prefix_sep(browse_path, self._delim)

        # Prepare the browse SQL query for the browse/find operation
        query = self._prepare_browse_sql_query(options)

        # Query local SQLite DB
        browse_result = self._query_db(query, query_versions, False, 999999)

        # Get all directories and its size
        dirs = self._get_directories_and_size(browse_result, show_deleted)

        # Loop through the query result and prepare the expected results dictionary
        final_list = dict()
        browse_items = browse_result.keys()

        for item in browse_items:
            browse_item = browse_result[item]

            if operation == 'browse':
                v_select = -1
                v_item = browse_item[v_select]

                if (v_item['parent'] == browse_path
                        and (v_item['parent'] in dirs or v_item['parent'] == self._delim)):

                    if not show_deleted and v_item['status'] == 'deleted':
                        continue
                    else:
                        # empty folders ( no folder size in list ) set folder size as 0
                        if v_item['type'] == 'directory' and item not in dirs:
                            # If no filters are selected, then show empty dir, else skip it
                            if len(filters) == 0:
                                dirs[item] = 0
                            else:
                                continue

                        # if directory, take it from the calculated list
                        v_size = (
                            v_item['size']
                            if v_item['type'] == 'file'
                            else dirs[item]
                        )

                        # Remove prefix slash for windows
                        item = (
                            commonutils.remove_prefix_sep(item, self._delim)
                            if self._client_os == 'windows'
                            else item
                        )

                        final_list[item] = [
                            v_item['type'],
                            True if v_item['status'] == 'deleted' else False,
                            v_size,
                            v_item['jobid']
                        ]

            if operation == 'find':
                v_select = -1
                v_item = browse_item[v_select]

                # UNC case, do not select root slash item.
                if 'UNC-NT_' in item and item.count(self._delim) == 1:
                    continue

                if not show_deleted and v_item['status'] == 'deleted':
                    continue
                else:
                    # Remove prefix slash for windows
                    item = (
                        commonutils.remove_prefix_sep(item, self._delim)
                        if self._client_os == 'windows'
                        else item
                    )

                    final_list[item] = [
                        v_item['type'],
                        True if v_item['status'] == 'deleted' else False,
                        v_item['size'],
                        v_item['jobid']
                    ]

            if operation == 'versions':
                for idx, ver in enumerate(browse_item):
                    version_id = idx + 1

                    if version_number > 0:
                        if version_number != version_id:
                            continue

                    v_comma = ',' + str(version_id)

                    # No version number for NAS version restores
                    if self._client_os == 'nas' and is_restore:
                        v_comma = ''

                    path_split = os.path.splitext(item)
                    v_path = path_split[0] + v_comma + path_split[1]

                    # Remove prefix slash for windows
                    v_path = (
                        commonutils.remove_prefix_sep(v_path, self._delim)
                        if self._client_os == 'windows'
                        else v_path
                    )

                    final_list[v_path] = [
                        browse_item[idx]['type'],
                        True if browse_item[idx]['status'] == 'deleted' else False,
                        browse_item[idx]['size'],
                        browse_item[idx]['jobid']
                    ]

        if self._debug:
            self.log.info(json.dumps(final_list))

        return final_list

    def _get_browse_actual_results(self, options):
        """Performs browse operation and gets the actual results for the given options"""

        subclient = options.get('subclient', None)
        operation = options['operation'].lower()
        options_copy = dict(options)  # Sending copy of the options to CvPySDK
        entity_obj = None
        browse_response = {}

        options_copy['path'] = commonutils.add_trailing_sep(options_copy['path'], self._delim)
        for paths in ['\\', '/']:
            options_copy['path'] = options_copy['path'].replace(paths, self._delim)

        if subclient is None:
            entity_obj = self.backupset_obj
        else:
            entity_obj = self.subclients[subclient]['obj']
            options_copy['_subclient_id'] = entity_obj._subclient_id

        if operation == 'browse':
            dummy_var, browse_response = entity_obj.browse(options_copy)

        elif operation == 'find':
            dummy_var, browse_response = entity_obj.find(options_copy)

        elif operation == 'versions':
            dummy_var, browse_response = entity_obj.find_all_versions(options_copy)

        return self._process_browse_response(browse_response)

    def _process_browse_response(self, response):
        """Reads the browse response from Indexing and extracts the required validation data

            Args:
                response            (dict)          Browse response dictionary

            Returns:
                Dictionary of items present in browse response.
                {
                    'item_i_path': [type, deleted, size, job_id]
                }

        """

        ret_code = 0
        result = dict()
        browse_responses = response['browseResponses']

        for browse_response in browse_responses:
            resp_type = browse_response['respType']

            if resp_type != 5 and 'session' in browse_response:
                if 'sessionId' in browse_response['session']:
                    self.log.info('Browse session ID [{0}]'.format(
                        browse_response['session']['sessionId']))

            if resp_type == 2:
                ret_code = -2
                if 'messages' in browse_response:
                    self.log.warning('Got partial results: [{0}]'.format(
                        str(browse_response['messages'])))

            if resp_type == 3:
                ret_code = -1
                if 'messages' in browse_response:
                    self.log.warning('Got error: [{0}]'.format(
                        str(browse_response['messages'])))

            if resp_type == 4:
                ret_code = 0
                if 'messages' in browse_response:
                    if 'live browse' in str(browse_response['messages']):
                        return -3, {}

                    self.log.warning('Got warning: [{0}]'.format(
                        str(browse_response['messages'])))

            if 'browseResult' in browse_response:
                if ('queryId' in browse_response['browseResult']
                        and (browse_response['browseResult']['queryId'] == 'dataQuery'
                             or browse_response['browseResult']['queryId'] == '0')):

                    browse_items = browse_response['browseResult'].get('dataResultSet', list())

                    self.log.info('Items in actual results [{0}]'.format(len(browse_items)))

                    for item in browse_items:
                        path = item['path']
                        size = item['size']
                        type = 'directory' if item['flags'].get('directory', False) else 'file'
                        deleted = item['flags'].get('deleted', False)
                        job_id = item['advancedData']['backupJobId']

                        if self._client_os == 'windows':
                            path = commonutils.remove_prefix_sep(path, self._delim)

                        if type == 'file':
                            version = item.get('version', 0)
                            if version != 0:
                                version_tag = ',' + str(version)
                                path_split = os.path.splitext(path)
                                path = path_split[0] + version_tag + path_split[1]

                        result[path] = [type, deleted, size, job_id]

                    del browse_items

        del browse_responses

        return ret_code, result

    def _verify_browse_results(self, options, actual_results, expected_results):
        """Compares the actual and expected browse results"""

        # In Unix, NAS OS remove the root slash from both the lists
        if self._client_os in ['unix', 'nas']:
            if self._delim in actual_results:
                actual_results.pop(self._delim, None)

        # If it is browse without filters or find, then set directory size to 0
        if (options['_verify_size'] == 'skip_auto' and (options['operation'] == 'find' or (
                options['operation'] == 'browse' and not options['compute_folder_size']))):
            self.log.info('Skipping folder size. Resetting folder size to 0')
            for aitem in actual_results:
                if actual_results[aitem][0] == 'directory':
                    actual_results[aitem][2] = 0
                    if aitem in expected_results:
                        expected_results[aitem][2] = 0

        # Skip size check for all the items if option is set
        if options['_verify_size'] == 'skip_all':
            self.log.warning('Skipping size check in actual and expected results')
            for aitem in actual_results:
                actual_results[aitem][2] = 0
                if aitem in expected_results:
                    expected_results[aitem][2] = 0

        # Skip job ID check for all the items if option is set
        if not options['_verify_jobid']:
            self.log.warning('Skipping job ID check in actual and expected results')
            for aitem in actual_results:
                if aitem in expected_results:
                    actual_results[aitem].pop()
                    expected_results[aitem].pop()

        # Skip job ID check for all the items if option is set
        if not options['_verify_jobid_directory']:
            self.log.warning('Skipping job ID check for dirs in actual and expected results')
            for aitem in actual_results:
                if aitem in expected_results and expected_results[aitem][0] == 'directory':
                    actual_results[aitem].pop()
                    expected_results[aitem].pop()

        self.log.info('Actual items [%s], Expected items [%s]', len(actual_results), len(expected_results))

        if actual_results != expected_results:
            self.log.error(
                '---------- {0} verification failed, there is a difference between '
                'actual and expected results ----------'.format(
                        options['operation'].capitalize()
            ))

            self._print_result_difference(actual_results, expected_results)
            return -1, actual_results

        else:
            self.log.info(
                '++++++++++ {0} operation results verified ++++++++++'.format(
                    options['operation'].capitalize()
            ))

            return 0, actual_results

    def _prepare_restore_filters_xml(self, options):
        """Prepares the browse filters XML for the restore operation"""

        filters = options['filters']
        where_clause = []

        if len(filters) == 0:
            return []

        data_browse_tag = {
            'databrowse_Query': {
                '@type': '0',
                '@queryId': '0',
                'dataParam': {
                    'sortParam': {
                        '@ascending': '1',
                        'sortBy': [{'@val': '38'}, {'@val': '0'}]
                    },
                    'paging': {
                        '@firstNode': '0',
                        '@pageSize': '100000',
                        '@skipNode': '0'
                    }
                },
                'whereClause': []
            }
        }

        if len(filters) > 0:
            for filter in filters:
                if filter[0] != 'ModifiedDate':
                    filter_dict = {
                        'connector': 'AND',
                        'criteria': {
                            'field': filter[0],
                            'values': filter[1]
                        }
                    }
                    if filter[0] == 'FileSize':
                        filter_dict['criteria']['dataOperator'] = filter[2]
                    where_clause.append(filter_dict)
                else:
                    pass

        data_browse_tag['databrowse_Query']['whereClause'] = where_clause
        bf_xml = xmltodict.unparse(data_browse_tag) # Get browse filters XML
        bf_xml_clean = bf_xml.replace("\n", '') # Remove new lines
        bf_xml_clean = bf_xml_clean.replace('"', "'") # Replace double quotes with single quotes

        return [bf_xml_clean]

    def _get_restore_expected_results(self, options):
        """Gets the expected results for the restore job"""

        final_list = {}
        dest_path = options['restore']['dest_path']
        source_items = options['restore']['source_items']
        restore_client = options['restore']['dest_client']
        preserve_level = options['restore']['preserve_level']

        rst_client = self._restore_clients[restore_client]
        rc_delim = rst_client['delim']
        rc_os = rst_client['os']

        for src_item in source_items:

            if 'vErSiOnS' in src_item:
                continue

            options['path'] = src_item
            options['operation'] = 'find'
            options['_item_type'] = 'file'
            options['_is_restore'] = True

            v_restore = options['restore']['select_version']

            if v_restore != 0:
                options['operation'] = 'versions'
                options['_version_number'] = v_restore

            for d in ['\\', '/']:
                src_item = src_item.replace(d, self._delim)

            expected_items = self._get_browse_expected_results(options)

            if self._debug:
                self.log.info(json.dumps(expected_items))

            for e_item in expected_items:

                if not self._is_file_path(src_item):

                    s_item = src_item
                    s_item = commonutils.remove_trailing_sep(s_item, self._delim)
                    s_item = commonutils.add_prefix_sep(s_item, self._delim)

                    for i in range(0, preserve_level):
                        if (s_item.count(self._delim) > 1 or 'UNC-NT_' in s_item
                                or '/vol' in s_item):
                            unc_split = s_item.split(self._delim)
                            unc_split.pop()
                            s_item = self._delim.join(unc_split)

                    dest_path = commonutils.remove_trailing_sep(dest_path, rc_delim)
                    e_item_processed = commonutils.add_prefix_sep(e_item, self._delim)

                    # src= \c:\test\ | expectedItem = \c:\test\hello.txt => hello.txt
                    pattern = re.compile(re.escape(s_item), re.IGNORECASE)
                    rem_expected_path = pattern.sub('', e_item_processed, 1)

                    if self._client_os == 'windows' and rc_os == 'windows':
                        rem_expected_path = rem_expected_path.replace(':', '')

                    if rc_os == 'unix':
                        rem_expected_path = rem_expected_path.replace('\\\\', rc_delim)

                    rem_expected_path = rem_expected_path.replace(self._delim, rc_delim)
                    rem_expected_path = commonutils.remove_prefix_sep(rem_expected_path, self._delim)

                    f_path = dest_path + rc_delim + rem_expected_path
                    f_path = f_path.replace(self._delim, rc_delim)

                    final_list[f_path] = expected_items[e_item][2]

                else:

                    f_path = dest_path + self._delim + e_item.split(self._delim)[-1]
                    final_list[f_path] = expected_items[e_item][2]

        if self._debug:
            self.log.info(json.dumps(final_list))

        return final_list

    def _get_restore_actual_results(self, options):
        """Starts a restore job and gets the actual restored data for the given options"""

        subclient = options.get('subclient', None)
        restore_client = options['restore']['dest_client']
        dest_path = options['restore']['dest_path']
        source_items = options['restore']['source_items']
        rc_machine = self._restore_clients[restore_client]['machine']
        rc_obj = self._restore_clients[restore_client]['obj']
        include_deleted_items = options['show_deleted']
        copy_precedence = options['copy_precedence']
        all_versions = (options['restore']['select_version'] == -1)
        restore_filter_xml = self._prepare_restore_filters_xml(options)

        if not options['restore']['in_place']:
            skip_deletes = ['/', '/opt', '/home', '/bin', '/lib']
            can_delete = True
            for skip_path in skip_deletes:
                if skip_path == dest_path:
                    can_delete = False

            if can_delete:
                self.log.info('Deleting previous run restore directory [{0}]'.format(dest_path))
                rc_machine.remove_directory(dest_path)

        restore_options = {
            'client': rc_obj,
            'paths': source_items,
            'destination_path': dest_path,
            'from_time': commonutils.convert_to_formatted_time(options['from_time']),
            'to_time': commonutils.convert_to_formatted_time(options['to_time']),
            'copy_precedence': copy_precedence,
            'wait': True,
            'fs_options': {
                'in_place': options['restore']['in_place'],
                'no_image': include_deleted_items,
                'browse_filters': restore_filter_xml,
                'all_versions': all_versions,
                'preserve_level': options['restore']['preserve_level'],
                'no_of_streams': options['restore']['no_of_streams']
            }
        }

        if options['job_id'] != 0:
            restore_options['fs_options']['browse_job_id'] = options['job_id']

        self.log.info('Restore options passed to SDK [{0}]'.format(restore_options))
        self._last_restore_directory = dest_path

        cv_utils = idautils.CommonUtils(self._commcell)

        try:
            if subclient is None:
                restore_options['backupset'] = self.backupset_obj
                cv_utils.backupset_restore_out_of_place(**restore_options)
            else:
                restore_options['subclient'] = self.subclients[subclient]['obj']
                cv_utils.subclient_restore_out_of_place(**restore_options)

        except Exception as e:
            self.log.error('Restore job failed: ' + str(e))
            return -1, {}

        return 0, self._scan_restore_data(dest_path, restore_client)

    def _verify_restore_results(self, options, actual_results, expected_results):
        """Verifies the actual and expected restore results"""

        if options['_verify_size'] == 'skip_all':
            for aitem in actual_results:
                if aitem in expected_results:
                    actual_results[aitem] = 0
                    expected_results[aitem] = 0

        if actual_results != expected_results:
            self.log.error('---------- Restore verification failed, there is a difference '
                           'between actual and expected results ----------')
            self._print_result_difference(actual_results, expected_results)
            return -1, actual_results

        else:
            self.log.info('++++++++++ Restore results verified ++++++++++')
            return 0, actual_results

    def _print_browse_log_line(self, options):
        """Prints a header log line based on the type of browse operation being done"""

        if options['job_id'] != 0:
            l_level = 'job'
        elif options['subclient'] is not None:
            l_level = 'subclient'
        else:
            l_level = 'backupset'

        if options['from_time'] == 0 and options['to_time'] == 0:
            l_type = 'latest'
        elif options['from_time'] == 0 and options['to_time'] != 0:
            l_type = 'point-in-time'
        else:
            l_type = 'timerange'

        l_operation = options['operation']
        l_restore = 'with restore' if options['restore']['do'] else 'no restore'
        l_sdi = 'with deleted items' if options['show_deleted'] else 'without deleted items'
        l_filters = f'with filters {options["filters"]}' if options['filters'] else 'without filters'

        if l_level == 'job':
            l_line = 'Verifying - job level - {0} - for job {1} - {2}'.format(
                l_operation, options['job_id'], l_filters)

        else:
            l_line = 'Verifying - {0} - {1} - at {2} level - {3} - {4} - {5}'.format(
                l_type, l_operation, l_level, l_sdi, l_restore, l_filters
            )

        self.log.info('********** ' + l_line.upper() + ' **********')

    def register_subclient(self, subclient_obj, sc_props=None):
        """Registers a subclient to the validation object

            Args:
                subclient_obj   (obj)           The subclient object
                sc_props        (dict)          Subclient properties

            Returns:
                None

        """

        if not isinstance(subclient_obj, Subclient):
            raise Exception(
                'Subclient object expected as argument to register with validation object')

        name = subclient_obj.subclient_name
        content = subclient_obj.content
        storage_policy_name = subclient_obj.storage_policy
        nversion = subclient_obj.file_version['DaysOrNumber']
        drop_deleted_age = (9999999999 if subclient_obj.backup_retention_days == -1
                            else subclient_obj.backup_retention_days)

        sc_props = dict() if sc_props is None else sc_props
        collect_file_dir = os.path.join(self._repo_dir, name)

        if not os.path.exists(collect_file_dir):
            os.makedirs(collect_file_dir)

        collect_file_full = os.path.join(collect_file_dir, 'full_job.txt')
        collect_file_inc = os.path.join(collect_file_dir, 'inc_job.txt')

        if type(content) is str:
            content = content.split(',')
        else:
            content = list(content)

        self.subclients[name] = {
            'obj': subclient_obj,
            'content': content,
            'sp': storage_policy_name,
            'nversion': nversion,
            'drop_deleted_age': drop_deleted_age,
            'collect_files': {
                'full': collect_file_full,
                'inc': collect_file_inc
            },
            'current_cycle': sc_props.get('start_cycle', 0),
            'mode': sc_props.get('mode', 'fs'),
            'last_job_type': None,
            'last_job_id': None
        }

        self.log.info('Registered new subclient [{0}] - [{1}]'.format(name, str(self.subclients)))

    def record_job(self, job_obj, copy_id=1):
        """Scans the test data, calculates the modified/added/deleted items of the subclient
            and adds them into the SQLite DB for validation

            Args:
                job_obj       (obj)       The CvPySDK job object

                copy_id       (int)       The copy ID of the job to register against

            Returns:
                Dictionary of items which were found in subclient test data

        """

        if not isinstance(job_obj, Job):
            raise Exception('Job object is expected as argument to record job for validation')

        subclient = job_obj.subclient_name
        job_type = job_obj.backup_level.lower()
        job_id = job_obj.job_id
        job_endtime = job_obj.end_timestamp

        if int(job_endtime) == 0:
            self.log.info('Job end time is 0. Waiting for some time to refresh the details')
            time.sleep(120)
            job_obj.refresh()
            if int(job_obj.end_timestamp) == 0:
                raise Exception('Job end time is 0. Unable to record job details')
            job_endtime = job_obj.end_timestamp

        self.log.info(
            'Recording the changes of the subclient and updating '
            'the DB for subclient [{0}] job [{1}] jobId [{2}] end time [{3}]'.format(
                subclient, job_type, job_id, job_endtime
            ))

        if subclient not in self.subclients:
            raise Exception('Subclient [{0}] is not registered with validation object'.format(
                subclient))

        final_items = {}
        cycle = self.subclients[subclient]['current_cycle']
        mode = self.subclients[subclient]['mode']
        sp = self.subclients[subclient]['sp']
        nversion = self.subclients[subclient]['nversion']
        drop_deleted_age = self.subclients[subclient]['drop_deleted_age']

        if job_type in ('full', 'incremental', 'differential'):

            # Scan testdata items
            scan_items = self._scan_test_data(subclient)

            # Identify testdata modifications
            final_items = self._identify_testdata_changes(scan_items, {
                'subclient': subclient,
                'job_id': job_id,
                'job_type': job_type,
                'job_endtime': job_endtime,
                'cycle': cycle
            })

            # Filter eligible items from the scanned list
            final_items = self._filter_scan_results(final_items, job_type)

            if job_type == 'full':
                self._write_collect_file(subclient, 'full', scan_items)

            self._write_collect_file(subclient, 'inc', scan_items)

        elif job_type == 'synthetic full':

            # If the last job is SFULL then replace the FULL collect file with last INC's state
            self.log.info('Updating local collect file of FULL for the new cycle')

            shutil.copyfile(self.subclients[subclient]['collect_files']['inc'],
                            self.subclients[subclient]['collect_files']['full'])

            sfull_query = ('select * from indexing where subclient = "{0}" '
                           'and cycle = "{1}" and jobid < "{2}"'.format(
                                subclient, cycle, job_id))

            sfull_props = {
                'jobid': job_id,
                'cycle': int(cycle) + 1,
                'jobendtime': job_endtime
            }

            # Include latest version + x number of previous versions (specified while initializing)
            version_count = int(nversion) + 1
            final_items = self._query_db(sfull_query, version_count, sfull_props, drop_deleted_age)

            self.subclients[subclient]['current_cycle'] += 1

            # Update cycle number for jobs which ran in parallel with SFULL
            cycle_change_query = ('update indexing set cycle = "{0}"'
                                  ' where subclient = "{1}" and jobid > "{2}"'.format(
                self.subclients[subclient]['current_cycle'], subclient, job_id))

            self.log.info(
                'Updating cycle number for jobs which ran in parallel with SFULL [{0}]'.format(
                    cycle_change_query))
            self.db.execute(cycle_change_query)

        self.subclients[subclient]['last_job_type'] = job_type
        self.subclients[subclient]['last_job_id'] = job_id

        # Insert the eligible items from scan results to the SQLite DB
        self._insert_into_db(final_items)
        self._insert_into_spcopy(sp, job_id, copy_id)

        # Automatic backup copy conditions
        if mode == 'fs_block':
            self.do_after_backup_copy(sp)

        if mode in ['fs_snap', 'fs_snap_skipcatalog'] and job_type in ('SFULL', 'MSFULL'):
            self.do_after_backup_copy(sp)

        if self._debug:
            self.log.info(json.dumps(final_items))

        return final_items

    def validate_browse_restore(self, options=None):
        """Performs browse & restore operation and validates the results of both

            Args:
                options         (dict)          Dictionary of browse/restore options

            Returns:
                 0 on validation passed
                -1 on validation failed

        """

        options = self._set_default_options(options)
        operation = options['operation'].lower()

        self._print_browse_log_line(options)

        # Browse operation
        if operation in ['find', 'versions']:
            ret_code, browse_result = self.validate_browse(options)

        elif operation == 'browse':
            ret_code = self.validate_browse_recursive(options, options['path'])

        else:
            ret_code = -1

        if ret_code == -1:
            self.log.error('Browse operation returned unexpected results. Not performing restore')
            return -1

        # Restore operation
        if options['restore']['do'] and ret_code != -1:
            ret_code, restore_result = self.validate_restore(options)

        return ret_code

    def validate_browse(self, options=None):
        """Performs browse/find/version operation and validates the actual and expected results

            Args:
                options     (dict)      The browse options to validate.
                                        Refer self.default_options for supported options

            Returns:
                ret_code    (int)       0 if browse results are same as expected
                                        -1 if browse results are mismatching

                results     (dict)      The browse results from Indexing

        """

        options = self._set_default_options(options)

        if options['operation'].lower() not in ['browse', 'find', 'versions']:
            self.log.error('Unrecognized operation set in options')
            return -1, {}

        self._browse_count.increment()
        self.log.info('=> Browse options [{0}]'.format(json.dumps(options)))

        ret_code = -1
        skip_node = 0
        page_size = options['page_size']
        actual_results = {}

        # Loop across multiple pages and get actual results
        while True:
            current_page = int(skip_node / page_size) + 1
            browse_attempts = 0

            self.log.info('********** Doing browse [{0}] - Page [{1}] **********'.format(
                self._browse_count.value(), current_page
            ))

            while True:
                ret_code, page_results = self._get_browse_actual_results(options)

                # If we got partial results, do browse again for 3 times with an interval
                if ret_code == -2:
                    if browse_attempts <= 3:
                        rand_time = random.randint(10, 15)
                        browse_attempts += 1
                        self.log.info(
                            'Got partial results, trying browse again in [{0}] secs. '
                            'Attempt [{1}/3]'.format(rand_time, browse_attempts))
                        time.sleep(rand_time)
                        continue
                    else:
                        self.log.error(
                            'Partial results attempts exhausted. Browse did not give full results')
                        return -1, {}
                else:
                    break

            if options['_verify_live_browse'] and ret_code == -3:
                self.log.info('Live browse has been initiated successfully as expected')
                return 0, {}

            if not options['_verify_live_browse'] and ret_code == -3:
                self.log.error('Live browse has started unexpectedly. Please check further')
                return 0, {}

            if options['_verify_volume_level'] and len(page_results) == 0:
                self.log.warning('Volume level browse returned no items.')
                return 0, {}

            if len(page_results) == 0:
                break

            elif len(page_results) < page_size:
                actual_results.update(page_results)
                break

            else:
                if current_page >= 200:
                    self.log.error('Quitting as something is wrong, there are about 200 pages !')
                    break

                actual_results.update(page_results)
                skip_node += page_size
                options['skip_node'] = skip_node
                continue

        if ret_code == 0:
            expected_results = self._get_browse_expected_results(options)
        else:
            self.log.error('Failed to get actual browse results, aborting browse operation')
            self._has_failure = True
            return ret_code, {}

        if options['operation'] == 'browse':
            if self._stop_browse(options['path']):
                self.log.warning('Stopping browse beyond this path')
                return 0, {}

        ret_code, results = self._verify_browse_results(options, actual_results, expected_results)

        if ret_code == -1:
            self._has_failure = True

        return ret_code, results

    def validate_browse_recursive(self, options, path, level=1):
        """Performs browse operation recursively and validates the result

            Args:
                options     (dict)      The browse options to validate.
                                        Refer self.default_options for supported options

                path        (str)       The starting path to begin recursive browse validation

                level       (int)       Level of the current path provided

            Returns:
                ret_code    (int)       0 if browse results are same as expected
                                        -1 if browse results are mismatching

        """

        mount_point_level = options['_mount_point_level']
        options['path'] = path

        self.log.info('Doing browse for path [{0}]'.format(path))
        ret_code, browse_result = self.validate_browse(options)

        if (options['_verify_volume_level'] and level == mount_point_level
                and len(browse_result) == 0):
            self.log.info('Volume level browse is successful. Level {0} returned no items.'.format(
                mount_point_level
            ))

        if options['_verify_live_browse'] and level > mount_point_level:
            self.log.error('Live browse is expected here, but browse goes '
                           'further than mount point level {0}'.format(mount_point_level))

        if ret_code == 0:
            for browse_item in browse_result:
                if browse_result[browse_item][0] == 'directory':
                    level += 1
                    recursive_browse = self.validate_browse_recursive(options, browse_item, level)
                    if recursive_browse == -1:
                        return -1
                else:
                    continue
        else:
            self.log.error('Failed while verifying result of path [{0}]'.format(path))
            return -1

        return 0

    def validate_restore(self, options=None):
        """Performs restore operation and verifies the actual and expected results

            Args:
                options     (dict)      The restore options to validate.
                                        Refer self.default_options for supported options

            Returns:
                ret_code    (int)       0 if restore results are same as expected
                                        -1 if restore results are mismatching

                results     (dict)      The restore results

        """

        options = self._set_default_options(options)

        self._restore_count.increment()
        self.log.info('=> Restore options [{0}]'.format(json.dumps(options)))

        restore_client = options['restore'].get('dest_client', None)
        restore_client = self._client if restore_client is None else restore_client
        options['restore']['dest_client'] = restore_client

        source_items = options['restore']['source_items']
        source_items = list(source_items) if isinstance(source_items, list) else [source_items]
        options['restore']['source_items'] = source_items

        # Initialize restore client object
        self._initialize_restore_client(restore_client)

        rst_client = self._restore_clients[restore_client]
        rc_delim = rst_client['delim']
        final_dest_path = ''

        if options['restore']['_force_dest_path'] != '':
            final_dest_path = options['restore']['_force_dest_path']

        elif options['restore']['in_place']:
            final_dest_path = source_items[0]

        else:
            if options['restore']['dest_path'] == '':
                if rst_client['restore_path'] is None:
                    raise Exception(
                        'Restore path is empty. Possibly cannot assume a default restore path')

                dest_path = rst_client['restore_path']
            else:
                dest_path = commonutils.remove_trailing_sep(
                    options['restore']['dest_path'], rc_delim
                )

            final_dest_path = rc_delim.join([dest_path, self._backupset, str(self._restore_count.value())])

        options['restore']['dest_path'] = final_dest_path
        self.log.info('Destination path [{0}]'.format(final_dest_path))

        ret_code, actual_results = self._get_restore_actual_results(options)

        if ret_code == 0:
            expected_results = self._get_restore_expected_results(options)
        else:
            self.log.error('Failed to run restore job')
            self._has_failure = True
            return ret_code, {}

        ret_code, results = self._verify_restore_results(options, actual_results, expected_results)

        if ret_code == -1:
            self._has_failure = True

        return ret_code, results

    def do_after_aux_copy(self, sp='no_name_sp', copy=2):
        """Update validation DB after running auxiliary copy for a job"""

        self.db.execute(
            'insert into spcopy ( sp, jobid, copy, aged ) select sp, jobid, ?, "no" '
            'from spcopy where sp = ? and copy <> ?',
            (copy, sp, copy)
        )

        self.log.info('After aux copy operation complete')

    def do_after_backup_copy(self, sp):
        """Update validation DB after running backup copy for a storage policy"""

        return self.do_after_aux_copy(sp, 2)

    def do_after_data_aging(self, jobs, copy=None):
        """Actions to perform after aging some jobs in the CommCell. This is used to mark the jobs as aged in Index.

            Args:
                jobs        (list)      --      List of jobs to age in validation DB

                copy        (int)       --      Copy ID of the SP to age (1 for primary, 2 for secondary, None for all)

            Returns:
                None, if operation is successful

            Raises:
                Exception if SQLite DB query execution fails

        """

        self.log.info('Marking jobs aged in validation DB after data aging')

        if copy is None:
            resp = self.db.execute("select distinct copy from spcopy")
            for row in resp.rows:
                self.do_age_jobs(jobs, row[0])
        else:
            self.do_age_jobs(jobs, copy)

    def do_age_jobs(self, jobs, copy=1):
        """Marks jobs are aged in the validation DB. These jobs will not be considered for browse and restore validation

            Args:
                jobs        (list)      --      List of jobs to age in validation DB

                copy        (int)       --      Copy ID of the SP to age for (1 for primary, 2 for secondary)

            Returns:
                None, if operation is successful

            Raises:
                Exception if SQLite DB query execution fails

        """

        jobs_list = ','.join(str(job) for job in jobs)

        self.db.execute("update spcopy set aged='yes' where copy={0} and jobid in ({1})".format(
            copy, jobs_list
        ))

        self.log.info('Jobs [%s] are marked aged in copy [%s] in validation DB', jobs_list, copy)

    def do_age_jobs_storage_policy(self, storage_policy, copy=1, retain_cycles=2):
        """Picks the jobs to aged based on the cycle to retain and marks them as aged in the validation DB

            Args:
                storage_policy      (str)   --      The name of the storage policy

                copy                (int)   --      Copy ID of the SP to age for (1 for primary, 2 for secondary)

                retain_cycles       (int)   --      The number of cycles to retain for the storage policy copy

            Returns:
                (list)      --    String of job IDs which are marked aged in the validation DB

        """

        if int(retain_cycles) <= 0:
            raise Exception('Invalid retain cycles parameter value')

        retain_cycles = int(retain_cycles) - 1
        jobs_list = []

        for subclient in self.subclients:
            query = f"""select distinct i.jobid from indexing as i 
            join spcopy on i.jobid = spcopy.jobid 
            and spcopy.copy = '{copy}' 
            and i.sp = '{storage_policy}'
            and i.subclient = '{subclient}'
            and cycle < ( 
                select max(cycle)-{retain_cycles} from indexing 
                join spcopy on indexing.jobid = spcopy.jobid 
                where spcopy.copy = '{copy}'
                and spcopy.sp = '{storage_policy}'
                and subclient = '{subclient}'
            )"""

            self.log.info('Querying jobs [%s]', query)

            resp = self.db.execute(query)

            for row in resp.rows:
                jobs_list.append(row[0])

        self.log.info('Jobs except latest [%s] cycles are [%s]', retain_cycles + 1, jobs_list)

        self.do_age_jobs(jobs_list, copy=copy)

        return jobs_list

    def do_delete_items(self, paths):
        """Marks the given list of items as erased in the the validation DB. The items will then
        be not considered for browse and restore validation

            Args:
                paths   (str/list)      --      List of item paths to mark erased in index

            Returns:
                 None, if operation is successful

            Raises:
                Exception if SQLite DB query execution fails

        """

        all_paths = []
        the_paths = []

        if isinstance(paths, str):
            all_paths.append(paths)
        else:
            all_paths = paths

        for path in all_paths:
            clean_path = commonutils.remove_trailing_sep(path, self._delim)
            clean_path = commonutils.add_prefix_sep(clean_path, self._delim)
            clean_path = clean_path + '%'
            the_paths.append(clean_path)

        where_clause = ['path like "' + path + '"' for path in the_paths]

        query = 'update indexing set erased="yes" where {0}'.format(
            ' or '.join(where_clause)
        )

        self.log.info('Erasing items from validation DB. Query [{0}]'.format(query))
        self.db.execute(query)
        self.log.info('Successfully marked items as erased in validation DB')

    def get_items(self, parent=None, name=None, type=None, status=None,
                  jobid=None, jobendtime=None, cycle=None, subclient=None, one_result=True):
        """Queries the validation DB and returns items which match as per the parameters passed.

            Args:
                parent      (str)       --      Name of the parent folder to filter

                name        (str)       --      Name of the file to filter

                type        (str)       --      Type of item to filter. E.g: file, directory

                status      (str)       --      Status of the file

                jobid       (tuple)     --      Range of jobids to filter. E.g: (1234, 3456)

                jobendtime  (tuple)     --      Range of job end timerange to filter

                cycle       (str)       --      Cycle to filter for

                subclient   (str)       --      Name of the subclient

                one_result  (bool)      --      Returns only one result

            Returns:
                List of items which were filtered through the criteria

        """

        items = list()
        query = 'select path from indexing where 1=1 '

        if parent is not None:
            query += ' and parent like "%' + parent + '%"'

        if name is not None:
            query += ' and name like "%' + name + '%"'

        if type is not None:
            query += ' and type="' + type + '"'

        if status is not None:
            query += ' and status="' + status + '"'

        if cycle is not None:
            query += ' and cycle="' + str(cycle) + '"'

        if subclient is not None:
            query += ' and subclient="' + subclient + '"'

        if jobid is not None and isinstance(jobid, tuple) and len(jobid) == 2:
            query += ' and jobid between {0} and {1}'.format(jobid[0], jobid[1])

        if jobendtime is not None and isinstance(jobendtime, tuple) and len(jobendtime) == 2:
            query += ' and jobendtime between {0} and {1}'.format(jobendtime[0], jobendtime[1])

        resp = self.db.execute(query)

        for row in resp.rows:
            items.append(row[0])

        self.log.info('Get items query [{0}]. Got items [{1}]'.format(query, resp.rows))

        if one_result:
            return items[0]
        else:
            return items

    def cleanup(self):
        """Closes and deletes the validation DB directory"""

        self.log.info('Cleaning validation repository')

        self.log.info('Closing SQLite DB')
        self.db.close()

        if self._debug:
            self.log.info('Skipping cleanup of validation repository as debugging is enabled.')
            return True

        if self._has_failure:
            self.log.info('Skipping cleanup of validation repository as there is a failure')
            return True

        if os.path.exists(self._repo_dir):
            shutil.rmtree(self._repo_dir, ignore_errors=True)
            self.log.info('Validation repository [{0}] is deleted successfully'.format(
                self._repo_dir))

    # Thread safe counter class used for browse/restore counts
    class Counter:
        def __init__(self, default):
            self._count = default
            self._lock = threading.Lock()

        def increment(self):
            with self._lock:
                self._count += 1

        def value(self):
            with self._lock:
                return self._count
