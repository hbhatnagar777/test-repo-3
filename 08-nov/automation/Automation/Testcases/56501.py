# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that troublesome data set items are backed up and browse results are served correctly.

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initialized in this method

    run()                            --  Contains the core testcase logic and it is the one executed

    validate_backup_restore()        --  Method to perform validation

    get_client_files_recursively()   --  Get all files from directory and sub-directories

    match_result()                   --  Check if two list of files are same

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase
from Indexing.validation.fs_browse_restore import FSBrowseRestore


class TestCase(CVTestCase):
    """This testcase verifies that troublesome data set items are backed up and browse results are served correctly."""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Troublesome dataset'

        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.backupset_name = None
        self.subclient_name = None

        self.cl_machine = None
        self.idx_tc = None
        self.validation = None

        self.content_dir = None
        self.restore_dir = None

        self.common_utils = None

        self.files = None
        self.filters = None
        self.new_file = None
        self.new_file_filters = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'TROUBLESOME_DATA'
        self.subclient_name = f'SUBCLIENT_1'

        self.cl_machine = Machine(self.client, self.commcell)
        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset(name=self.backupset_name, for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name=self.subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        self.validation = FSBrowseRestore({
            'commcell': self.commcell,
            'backupset': self.backupset,
            'debug': False
        })

        self.content_dir = self.subclient.content[0]
        self.restore_dir = f"{self.content_dir}_restored"

        self.common_utils = CommonUtils(self)

        self.files = [
            '.txt',
            '.doc',
            '.docx',
            'data',
            'data.txt',
            'abc_[213].docx',
            'data_abc1234.docx',
            'presentation.pptx',
            'Spreadsheet new!.xlsx',
            f'new folder{self.cl_machine.os_sep}profile.dat',
            f'new folder @2{self.cl_machine.os_sep}archi;ve.txt'
        ]
        self.filters = {
            r'*.docx': ['.docx', 'abc_[213].docx', 'data_abc1234.docx'],
            r'*.*': [
                '.txt',
                '.doc',
                '.docx',
                'data.txt',
                'abc_[213].docx',
                'data_abc1234.docx',
                'presentation.pptx',
                'Spreadsheet new!.xlsx',
                f'new folder{self.cl_machine.os_sep}profile.dat',
                f'new folder @2{self.cl_machine.os_sep}archi;ve.txt'
            ],
            r'*.docx AND data*': ['data_abc1234.docx'],
            r'*.txt OR *.xlsx': ['.txt', 'data.txt', 'Spreadsheet new!.xlsx',
                                 f'new folder @2{self.cl_machine.os_sep}archi;ve.txt'],
        }
        self.new_file = 'incremental.xlsx'
        self.new_file_filters = [r'*.*', r'*.txt OR *.xlsx']

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1 - Run full backup job
                2 - Verify following:
                    1) Find results - Without filters (all files are listed with correct filename)
                    2) Find results - With filename filter
                    3) Restore results - Without filters
                    4) Restore with filename filter.
                3 - Add new file
                4 - Run incremental backup job
                5 - Repeat step 2
                6 - Run Synthetic Full
                7 - Repeat step 2

        """

        try:
            # clear the content directory before adding new content
            self.cl_machine.remove_directory(self.content_dir)
            for file in self.files:
                file_path = self.cl_machine.os_sep.join([self.content_dir, file])
                self.cl_machine.create_file(file_path=file_path, content='Test.')

            self.validate_backup_restore(backup_level='Full')

            # add one more file before running an incremental
            self.cl_machine.create_file(self.cl_machine.os_sep.join([self.content_dir, self.new_file]),
                                        content='This is a test file.')

            self.files.append(self.new_file)
            for new_file_filter in self.new_file_filters:
                self.filters[new_file_filter].append(self.new_file)

            self.validate_backup_restore(backup_level='Incremental')

            self.validate_backup_restore(backup_level='Synthetic_full')

            self.log.info('**************** SUCCESS, test Case passed for troublesome data. ****************')

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.result_string = str(e)
            self.status = constants.FAILED
            self.log.exception(e)

    def validate_backup_restore(self, backup_level):
        """Method to perform validation

            1) Find results - Without filters (all files are listed with correct filename)
            2) Find results - With filename filter
            3) Restore results - Without filters
            4) Restore with filename filter.

        """

        self.log.info(f'*********** Running backup: {backup_level} ***********')
        self.common_utils.subclient_backup(subclient=self.subclient, backup_type=backup_level)

        rel_restore_dir = self.cl_machine.os_sep.join(
            [self.restore_dir, self.content_dir.split(self.cl_machine.os_sep)[-1]])

        self.log.info('*************** Verify find operation ***************')
        result = self.subclient.find({'file_size_gt': '0'})[0]
        result = [pth.replace(self.content_dir, '').strip(self.cl_machine.os_sep) for pth in result]
        if not self.match_result(files=self.files, result=result):
            raise Exception('Find all files failed.')

        self.log.info('*************** Verify restore operation ***************')
        self.cl_machine.remove_directory(self.restore_dir)
        self.common_utils.subclient_restore_out_of_place(destination_path=self.restore_dir, paths=[self.content_dir],
                                                         client=self.client, subclient=self.subclient)

        result = self.get_client_files_recursively(directory_name=rel_restore_dir)
        result = [pth.replace(rel_restore_dir, '').strip(self.cl_machine.os_sep) for pth in result]
        if not self.match_result(files=self.files, result=result):
            raise Exception('Restore all files failed.')

        for filter_expression in self.filters:
            self.log.info(f'************** Verify for filter - {filter_expression} **************')
            expected = self.filters[filter_expression]

            self.log.info('*************** Verify find operation ***************')
            result = self.subclient.find({'file_name': filter_expression})[0]
            result = [pth.replace(self.content_dir, '').strip(self.cl_machine.os_sep) for pth in result]
            if not self.match_result(files=expected, result=result):
                raise Exception(f'Find with filter failed. filter: {filter_expression}')

            self.log.info('*************** Verify restore operation ***************')
            self.cl_machine.remove_directory(self.restore_dir)
            self.common_utils.subclient_restore_out_of_place(
                destination_path=self.restore_dir,
                paths=[self.content_dir],
                client=self.client,
                subclient=self.subclient,
                fs_options={
                    'browse_filters': self.validation._prepare_restore_filters_xml(
                        {'filters': [('FileName', filter_expression)]})
                }
            )

            result = self.get_client_files_recursively(directory_name=rel_restore_dir)
            result = [pth.replace(rel_restore_dir, '').strip(self.cl_machine.os_sep) for pth in result]
            if not self.match_result(files=expected, result=result):
                raise Exception(f'Restore file with filter failed. filter: {filter_expression}')

        self.log.info(f'*********** Validation successful for backup-type: {backup_level} ***********')

    def get_client_files_recursively(self, directory_name):
        """Get all files from directory and sub-directories

            Args:
                directory_name  (str)  --  directory path

            Returns:
                (list) - absolute path of all files

        """

        self.log.info(f"Get items from directory: {directory_name}")

        result = self.cl_machine.get_items_list(directory_name)
        only_files = [pth for pth in result if self.cl_machine.is_directory(pth) == 'False']
        return only_files

    def match_result(self, files, result):
        """Check if two list of files are same"""

        self.log.info(f"Expected: {files}")
        self.log.info(f"Result: {result}")

        if len(files) != len(result):
            self.log.info(f'Unequal Lengths. expected: {len(files)}  got: {len(result)}')
            return False

        sorted_files = sorted(files)
        sorted_result = sorted(result)

        for i, pth in enumerate(sorted_files, 0):
            if pth != sorted_result[i]:
                self.log.info('Files do not match')

                self.log.info('Expected:')
                self.log.info(pth)

                self.log.info('Got:')
                self.log.info(sorted_result[i])

                return False

        return True
