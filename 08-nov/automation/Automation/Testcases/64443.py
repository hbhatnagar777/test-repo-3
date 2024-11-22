# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that backup, browse, restore of files with special character in name works as expected
TestCase:
    __init__()                                              --  Initializes the TestCase class

    setup()                                                 --  All testcase objects are initialized in this method

    run()                                                   --  Contains the core testcase logic and
                                                                it is the one executed

    modify_files()                                          --  Method to edit the special character test data


"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies that backup, browse, restore of files with special character in name works as expected"""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Special Characters Acceptance'
        self.tcinputs = {
            'StoragePolicy': None,
            'SplCharFolder': None,
            'FilesInTestData': None,

        }
        self.cl_machine = None
        self.idx_tc = None
        self.content_dir = None
        self.restore_dir = None
        self.common_utils = None
        self.spl_char_folder_path = None
        self.file_names_to_be_added = []
        self.file_names_in_testdata = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(name='spl_char_bkpst', for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name='spl_char_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        self.content_dir = self.subclient.content[0]
        self.restore_dir = f'{self.content_dir}_restored'
        self.common_utils = CommonUtils(self)
        self.file_names_to_be_added = ['filename01.docx', 'filewrong.xlsx', 'fileright.txt']

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1. Add the special character data containing folder to the subclient content.
                2. Run a FULL.
                3. Modify the files named in special characters and symbols and run INC
                4. Run a SFULL
                5. Do a browse and compare results with expected input list of files
                6. Do a restore and compare the number of files restored

        """
        try:
            for each_path in self.subclient.content:
                if self.cl_machine.check_directory_exists(each_path):
                    self.cl_machine.remove_directory(each_path)
            self.cl_machine.create_directory(self.content_dir)

            self.log.info('Copying Unicode Characters Folder to %s', self.content_dir)
            self.cl_machine.copy_folder(self.tcinputs['SplCharFolder'], self.content_dir)
            spl_char_folder_name = self.tcinputs['SplCharFolder'].split(self.cl_machine.os_sep)[-1]
            self.spl_char_folder_path = self.cl_machine.join_path(self.content_dir, spl_char_folder_name)

            self.file_names_in_testdata = self.tcinputs['FilesInTestData']
            self.log.info('Expected Browse Results are %s', self.file_names_in_testdata)

            self.log.info(' ****** Running two cycles of jobs ******** ')
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Full')

            self.modify_files()
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Incremental')
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Synthetic_full')

            self.modify_files()
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Incremental')
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Synthetic_full')

            browse_result_file_names = []
            self.log.info(' ******** Performing a browse from the special character folder ********')
            actual_files = self.subclient.browse(path=self.spl_char_folder_path)[0]
            self.log.info('The actual files in browse results are %s', actual_files)
            for each_file in actual_files:
                file_name = each_file.split(self.cl_machine.os_sep)[-1]
                browse_result_file_names.append(file_name)
            self.log.info('The list of actual file names in the browse result are %s', browse_result_file_names)
            self.log.info('The list of expected files in testdata for the browse are %s', self.file_names_in_testdata)
            if set(self.file_names_in_testdata) == set(browse_result_file_names):
                self.log.info('All the files in browse result are same as the files in testdata')
            else:
                raise Exception('Browse has not returned all the expected files')

            self.log.info(' ********** Starting a out of the place restore ********** ')
            self.common_utils.subclient_restore_out_of_place(
                destination_path=self.restore_dir,
                paths=[self.spl_char_folder_path]
            )
            actual_file_count = self.cl_machine.number_of_items_in_folder(
                folder_path=self.spl_char_folder_path,
                recursive=True
            )
            self.log.info('Number of actual files at %s is %s', self.spl_char_folder_path, actual_file_count)
            restored_spl_char_folder_path = self.cl_machine.join_path(self.restore_dir, spl_char_folder_name)
            restored_file_count = self.cl_machine.number_of_items_in_folder(
                folder_path=restored_spl_char_folder_path,
                recursive=True
            )
            self.log.info('Number of restored files at %s is %s', restored_spl_char_folder_path, restored_file_count)

            if actual_file_count == restored_file_count:
                self.log.info('All files/folders are restored as expected')
            else:
                raise Exception('Failed to restore all expected files/folders')

            self.log.info('**************** SUCCESS, test Case passed for Unicode data. ****************')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def modify_files(self):
        """ Edits the unicode test data by modifying, adding and deleting random files """

        file_to_be_created = self.file_names_to_be_added.pop()
        file_path_to_be_created = self.cl_machine.join_path(self.spl_char_folder_path, file_to_be_created)

        self.log.info('******* Creating the file: %s *********', file_path_to_be_created)
        self.cl_machine.create_file(file_path=file_path_to_be_created, content='1111111')

        file_name = file_path_to_be_created.split(self.cl_machine.os_sep)[-1]
        self.file_names_in_testdata.append(file_name)
