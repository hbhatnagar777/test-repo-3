# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that during browse, files, folders are displayed based on the current logged in user's ACL.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    initialize_users()          --  Initializes the users and their CVPySDK objects

    validate_browse()           --  Validates the browse results for the user

    validate_find()             --  Validates the find results for the user

    validate_restore()          --  Validates the restore results for the user

    verify_user_files()         --  Verifies browse, find and restore for all the users that files/folders are
    displayed only the user has permission for.

    edit_files()                --  Edits one file which are owned by the users

"""

import random

from cvpysdk.commcell import Commcell

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that during browse, files, folders are displayed based on the current logged
    in user's ACL.

        Steps:
            1) Have testdata ready with user 1 having permission of some files and user 2 having permission of some
            other files
            2) Create a subclient, enable ACL collection and set the testdata folder.
            3) Run Full backup
            4) Verify browse, find and restore for every user and see if the users are able to browse only the
            files they have permission for.
            5) Run INC backup
            6) Repeat step 4
            7) Run Synthetic full backup
            8) Repeat step 4 for the SFULL job.

        Syntax for "Users" input:
            "Users": {
                "user1": {
                    "username": "idx\\aakash",
                    "password": "<pwd>",
                    "file_id": "user1"
                },
                "user2": {
                    "username": "idx\\aakash2",
                    "password": "<pwd>",
                    "file_id": "user2"
                }
            }

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - End user browse of ACL files'

        self.tcinputs = {
            'TestData': None,
            'RestoreLocation': None,
            'StoragePolicy': None,
            'Users': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.testdata = None
        self.idx_db = None

        self.users = None
        self.users_obj = {}
        self.timerange = [0, 0]
        self.restore_location = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('acl_test', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_acl_test',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            content=[self.tcinputs.get('TestData')]
        )

        self.subclient.catalog_acl = True

        self.restore_location = self.tcinputs.get('RestoreLocation')
        self.users = self.tcinputs.get('Users')
        self.initialize_users()

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('***** Running FULL backup *****')
        self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=True)

        self.verify_user_files()

        self.edit_files()

        self.log.info('***** Running Incremental backup *****')
        self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=True)

        self.verify_user_files()

        self.log.info('***** Running Synthetic full backup *****')
        sfull_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', verify_backup=True)

        self.timerange = [sfull_job.start_timestamp, sfull_job.end_timestamp]
        self.verify_user_files()

    def initialize_users(self):
        """Initializes the users and their CVPySDK objects"""

        webserver = self.inputJSONnode['commcell']['webconsoleHostname']

        for i in range(1, 3):
            user_key = 'user' + str(i)
            user_data = self.users[user_key]

            self.log.info('Initializing user [%s]', user_key)

            cc = Commcell(webserver, user_data['username'], user_data['password'], verify_ssl=False)
            client = cc.clients.get(self.client.client_name)
            agent = client.agents.get(self.agent.agent_name)
            backupset = agent.backupsets.get(self.backupset.backupset_name)
            subclient = backupset.subclients.get(self.subclient.subclient_name)

            self.users_obj[user_key] = {
                'client': client,
                'subclient': subclient,
            }

    def validate_browse(self, user_key, folder):
        """Validates the browse results for the user

            Args:
                user_key        (str)       --      The user key/ID of the user to browse for.

                folder          (str)       --      The folder to browse and verify the results for

            Returns:
                None

            Raises:
                Exception when the browse results are incorrect for the specified user
        """

        subclient = self.users_obj[user_key]['subclient']
        username = self.users[user_key]['username']
        file_id = self.users[user_key]['file_id']
        actual_files = {}
        expected_files = {}

        self.log.info('Path [%s]', folder)

        item_in_disk = self.cl_machine.scan_directory(folder, recursive=False)
        for item in item_in_disk:
            item_path = item['path']

            if item['type'] == 'file':
                if file_id in item_path:
                    expected_files[item_path] = item['size']

            if item['type'] == 'directory':
                self.validate_browse(user_key, item_path)

        self.log.info('= Expected files [%s]', expected_files)

        self.log.info('Doing browse [%s]', folder)
        items, results = subclient.browse(
            path=folder,
            from_time=self.timerange[0],
            to_time=self.timerange[1]
        )

        for item_path, item_props in results.items():
            if item_props['type'].lower() == 'file':
                if file_id in item_props['name']:
                    actual_files[item_path] = str(item_props['size'])
                else:
                    self.log.error('Full results [%s]', results)
                    raise Exception(f'File [{item_path}] does not belong to user [{username}]')

        self.log.info('= Actual files [%s]', actual_files)

        if actual_files != expected_files:
            self.log.error('Mismatch in results. Actual [%s] Expected [%s]', actual_files, expected_files)
            raise Exception('Mismatch in actual and expected browse results')

    def validate_find(self, user_key):
        """Validates the find results for the user

            Args:
                user_key        (str)       --      The user key/ID of the user to browse for.

            Returns:
                None

            Raises:
                Exception when the browse results are incorrect for the specified user
        """

        subclient = self.users_obj[user_key]['subclient']
        username = self.users[user_key]['username']
        file_id = self.users[user_key]['file_id']
        actual_files = {}
        expected_files = {}

        files_in_disk = self.cl_machine.scan_directory(self.subclient.content[0], 'file')
        for file in files_in_disk:
            file_path = file['path']
            if file_id in file_path and '.txt' in file_path:
                expected_files[file_path] = file['size']

        self.log.info('= Expected files [%s]', expected_files)

        self.log.info('Doing find')
        items, results = subclient.find(
            filename='*.txt',
            from_time=self.timerange[0],
            to_time=self.timerange[1]
        )

        for item_path, item_props in results.items():
            if item_props['type'].lower() == 'file':
                if file_id not in item_props['name']:
                    self.log.error('Find results [%s]', results)
                    raise Exception(f'File [{item_path}] does not belong to user [{username}]')
                else:
                    actual_files[item_path] = str(item_props['size'])

        self.log.info('= Actual files [%s]', actual_files)

        if actual_files != expected_files:
            self.log.error('Mismatch in results. Actual [%s] Expected [%s]', actual_files, expected_files)
            raise Exception('Mismatch in actual and expected find results')

    def validate_restore(self, user_key):
        """Validates the restore results for the user

            Args:
                user_key        (str)       --      The user key/ID of the user to browse for.

            Returns:
                None

            Raises:
                Exception when the browse results are incorrect for the specified user
        """

        client = self.users_obj[user_key]['client']
        subclient = self.users_obj[user_key]['subclient']
        file_id = self.users[user_key]['file_id']
        content = self.subclient.content[0]
        actual_files = {}
        expected_files = {}

        self.cl_machine.remove_directory(self.restore_location)

        restore_job = subclient.restore_out_of_place(
            client=client,
            destination_path=self.restore_location,
            paths=self.subclient.content,
            fs_options={
                'preserve_level': 0
            }
        )

        self.log.info('Started restore job [%s]', restore_job.job_id)
        if not restore_job.wait_for_completion():
            raise Exception('Restore job did not complete successfully')
        else:
            self.log.info('Restore job completed successfully')

        files_in_disk = self.cl_machine.scan_directory(content, 'file')
        for file in files_in_disk:
            file_path = file['path']
            if file_id in file_path:
                mod_path = file_path.replace(content, '')
                expected_files[mod_path] = file['size']

        files_restored = self.cl_machine.scan_directory(self.restore_location, 'file', recursive=True)
        for file in files_restored:
            file_path = file['path']
            if file_id in file['path']:
                mod_path = file_path.replace(self.restore_location, '')
                actual_files[mod_path] = file['size']

        self.log.info('Restored files [%s]', actual_files)

        if actual_files != expected_files:
            self.log.error('Mismatch in results. Actual [%s] Expected [%s]', actual_files, expected_files)
            raise Exception('Mismatch in actual and expected restore results')

    def verify_user_files(self):
        """Verifies browse, find and restore for all the users that files/folders are displayed only
        the user has permission for.

            Returns:
                None

            Raises:
                Exception when the browse, find and restore results are incorrect for the specified user
        """

        content = self.subclient.content[0]

        for i in range(1, 3):
            user_key = 'user' + str(i)
            user_data = self.users[user_key]

            self.log.info('***** Verifying for user [%s] [%s] *****', user_key, user_data['username'])

            self.log.info('***** Verifying browse *****')
            self.validate_browse(user_key, content)
            self.log.info('***** Browse results are verified *****')

            self.log.info('***** Verifying find *****')
            self.validate_find(user_key)
            self.log.info('***** Find results are verified *****')

            self.log.info('***** Verifying restore *****')
            self.validate_restore(user_key)
            self.log.info('***** Restore results are verified *****')

    def edit_files(self):
        """Edits one file which are owned by the users"""

        content = self.subclient.content[0]
        items_in_disk = self.cl_machine.scan_directory(content, 'file', recursive=True)
        random.shuffle(items_in_disk)

        for i in range(1, 3):
            user_key = 'user' + str(i)
            file_id = self.users[user_key]['file_id']

            for item in items_in_disk:
                if file_id in item['path']:
                    self.log.info('Editing file %s', item['path'])
                    self.cl_machine.append_to_file(item['path'], '1'*50)
                    break
