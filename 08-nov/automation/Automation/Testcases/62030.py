# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that troublesome data set items are backed up and browse results are served correctly.

TestCase:
    __init__()                                              --  Initializes the TestCase class

    setup()                                                 --  All testcase objects are initialized in this method

    run()                                                   --  Contains the core testcase logic and
                                                                it is the one executed

    do_browse_restore_and_verify()                          --  Performs browse and restore and verify these operations

    modify_files()                                          --  Method to edit the unicode test data

    do_browse()                                             --  Does browse recursively

    validate_backup()                                       --  Method to perform backup validation

    validate_restore()                                      --  Method to perform restore validation

    validate_backup_restore_using_filename_filters()        -- Method to validate backup and restore results
                                                               with specific filters on unicode file names


    match_result()                                          --  Check if two list of files are same

"""
import random
import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import commonutils
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase
from Indexing.validation.fs_browse_restore import FSBrowseRestore


class TestCase(CVTestCase):
    """This testcase verifies that troublesome data set items are backed up and browse results are served correctly."""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Unicode Characters'
        self.tcinputs = {
            'StoragePolicy': None,
            'SplCharFolder': None,
            'ClientUserName': None,
            'ClientPassword': None,
            # Optional 'AdditionalFilters': None,
            # Optional 'AdditionalFiles': None,
        }
        self.cl_machine = None
        self.idx_tc = None
        self.validation = None
        self.content_dir = None
        self.restore_dir = None
        self.common_utils = None
        self.spl_char_folder_name = None
        self.spl_char_folder_path = None
        self.file_names_to_be_added = []
        self.filters = None
        self.restore_path_before_sfull = None
        self.restore_path_after_sfull = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(
            machine_name=self.client.client_hostname,
            username=self.tcinputs['ClientUserName'],
            password=self.tcinputs['ClientPassword']
        )
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(name='unicode_characters', for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name='unicode_characters_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )
        self.validation = FSBrowseRestore({
            'commcell': self.commcell,
            'backupset': self.backupset,
            'debug': False
        })
        self.content_dir = self.subclient.content[0]
        self.restore_dir = f'{self.content_dir}_restored'
        self.restore_path_before_sfull = self.cl_machine.join_path(self.restore_dir, 'beforesfull')
        self.restore_path_after_sfull = self.cl_machine.join_path(self.restore_dir, 'aftersfull')
        self.common_utils = CommonUtils(self)
        self.file_names_to_be_added = ['filename01.docx', 'filewrong.xlsx', 'fileright.txt']
        new_files = self.tcinputs.get('AdditionalFiles', [])
        for new_file in new_files:
            self.log.info(new_file)
            self.file_names_to_be_added.append(new_file)
        self.log.info('Newly added files are %s', new_files)

        #self.file_names_to_be_added = ['file_chinese_形声字.docx', 'file_telugu_తెలుగు.xlsx', 'file_telugu_kleh.txt']
        self.filters = [r'*.docx', r'*test case*', r'*.*', r'*.txt', r'*.pptx']
        new_filters = self.tcinputs.get('AdditionalFilters', [])
        for new_filter in new_filters:
            self.log.info(new_filter)
            self.filters.append(new_filter)
        self.log.info(' Newly added filters are %s', new_filters)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1. Add the special character data containing folder to the subclient content.
                2. Run a FULL.
                3. Modify the files named in special characters and symbols and run INC
                4. Do a browse without any filters and verify the results.
                5. Do a restore and verify the results.
                6. Repeat step 3 and run SYN FULL.
                7. Repeat 4 and 5 steps.
        """
        try:
            for each_path in self.subclient.content:
                if self.cl_machine.check_directory_exists(each_path):
                    self.cl_machine.remove_directory(each_path)
            self.cl_machine.create_directory(self.content_dir)

            self.log.info('************** Adding unicode character files and folders ***************')
            self.log.info('Copying Unicode Characters Folder to %s', self.content_dir)
            self.cl_machine.copy_folder(self.tcinputs['SplCharFolder'], self.content_dir)
            self.spl_char_folder_name = self.tcinputs['SplCharFolder'].split(self.cl_machine.os_sep)[-1]
            self.spl_char_folder_path = self.cl_machine.join_path(self.content_dir, self.spl_char_folder_name)

            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Full')
            self.modify_files()
            inc_job = self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Incremental')
            self.do_browse_restore_and_verify(job_id=inc_job.job_id)

            self.modify_files()
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Incremental')
            first_sfull = self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Synthetic_full')
            self.do_browse_restore_and_verify(job_id=first_sfull.job_id)

            self.modify_files()
            self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Incremental')
            second_sfull = self.common_utils.subclient_backup(subclient=self.subclient, backup_type='Synthetic_full')
            self.do_browse_restore_and_verify(job_id=second_sfull.job_id)
            self.log.info('**************** SUCCESS, test Case passed for Unicode data. ****************')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def do_browse_restore_and_verify(self, job_id):
        """ Performs browse and restore and verify these operations

                 Args:
                        job_id  (int)   -- Job Id after which the browse and restore are being performed
        """
        restore_path = self.cl_machine.join_path(self.restore_dir, f'j{job_id}')

        self.log.info('*************** Starting browse operation after Job : %s ***************', job_id)
        if not self.validate_backup(self.content_dir):
            raise Exception('Backup validation failed')
        self.log.info('Backup Validation successful')
        self.log.info(' ********** Starting restore after Job : %s ********** ', job_id)
        self.common_utils.subclient_restore_out_of_place(
            destination_path=restore_path,
            paths=[self.spl_char_folder_path]
        )

        if not self.validate_restore(restore_path):
            raise Exception('Restore verification failed')
        self.log.info('Restore Validation successful')
        self.validate_backup_restore_using_filename_filters(job_id=job_id)

    def modify_files(self):
        """ Edits the unicode test data by modifying, adding and deleting random files """

        item_list = self.cl_machine.scan_directory(path=self.spl_char_folder_path, filter_type='file')
        file_list = []
        for item in item_list:
            file_list.append(item['path'])
        self.log.info(file_list)
        files_chosen_to_modify = random.sample(file_list, 2)

        self.log.info('******* Editing the file: %s *********', files_chosen_to_modify[0])
        content_added = 'This is new line added to the file'
        self.cl_machine.append_to_file(files_chosen_to_modify[0], content_added)

        self.log.info('******* Deleting the file: %s *********', files_chosen_to_modify[1])
        self.cl_machine.delete_file(files_chosen_to_modify[1])
        file_to_be_created = self.file_names_to_be_added.pop()
        file_path_to_be_created = self.cl_machine.join_path(self.spl_char_folder_path, file_to_be_created)

        self.log.info('******* Creating the file: %s *********', file_path_to_be_created)
        self.cl_machine.create_file(file_path=file_path_to_be_created, content='1111111')

    def do_browse(self, browse_path, file_dict):
        """ Does browse recursively
                Args:
                     browse_path  (str)   -- path that needs to be browsed

                     file_dict  (dict)    -- Dictionary of file paths and their sizes

                Returns:
                        (dict)  -- dictionary of actual files with their sizes
        """
        actual_files_info = self.subclient.browse(path=browse_path)[1]
        for each_item in actual_files_info:
            if actual_files_info[each_item]['type'] == 'File':
                file_dict[each_item] = actual_files_info[each_item]['size']
            else:
                self.do_browse(browse_path=each_item, file_dict=file_dict)
        return file_dict

    def validate_backup(self, entity_path):
        """Verifies if all the items on the source location have been backed up.

                    Args:
                        entity_path     (str)   --  path to browse the backed up data.

                    Returns:
                        (Boolean)  -- True, if backup validation is successful
                                      False, if backup validation fails

              """
        expected_dict = {}
        self.log.info('Validating the backed up data for %s', entity_path)
        expected_files_info = self.cl_machine.scan_directory(entity_path, filter_type='file', recursive=True)

        for expected_file in expected_files_info:
            expected_dict[expected_file['path']] = expected_file['size']
        actual_dict = self.do_browse(browse_path=entity_path, file_dict={})
        if not self.match_result(expected_dict, actual_dict):
            return False
        self.log.info('Browse validation successful for the path %s', entity_path)
        return True

    def validate_restore(self, restore_path):
        """ Verifies if all the items on the source location have been restored

             Args:
                        restore_path  (str)   -- Path at which results have been restored
             Returns:
                        (Boolean)             -- True, if restore validation is successful
                                                 False, if restore validation fails

            """
        self.log.info('*************** Verify restore operation ***************')
        expected_dict = {}
        actual_dict = {}
        expected = self.cl_machine.scan_directory(path=self.content_dir, filter_type='file')
        actual = self.cl_machine.scan_directory(path=restore_path, filter_type='file')

        for each_file in expected:
            file_name = each_file['path'].replace(self.content_dir, '').strip(self.cl_machine.os_sep)
            expected_dict[file_name] = each_file['size']
        for each_file in actual:
            file_name = each_file['path'].replace(restore_path, '').strip(self.cl_machine.os_sep)
            actual_dict[file_name] = each_file['size']
        if not self.match_result(expected_dict, actual_dict):
            return False

        return True

    def validate_backup_restore_using_filename_filters(self, job_id):
        """ Method to validate backup and restore results with specific filters on unicode file names

                Args:
                    job_id (int)    -- Indicator of when the validation is happening, after which job
        """
        filter_number = 1
        for filter_expression in self.filters:
            expected_dict = {}
            browse_actual_dict = {}
            restore_actual_dict = {}
            filter_restore_dir = self.cl_machine.join_path(
                self.restore_dir, f'restorefilter_j{job_id}_{filter_number}'
            )
            rel_restore_dir = self.cl_machine.os_sep.join(
                [filter_restore_dir, self.content_dir.split(self.cl_machine.os_sep)[-1]])

            self.log.info('************** Verify for filter - %s **************', filter_expression)
            mod_filter_expression = f'.{filter_expression}'
            reg_ex_search = re.compile(mod_filter_expression)
            expected_details = self.cl_machine.scan_directory(path=self.content_dir, filter_type='file')
            expected = [pth['path'] for pth in expected_details]
            filtered_expected_files = list(filter(reg_ex_search.match, expected))

            for each_filtered_file in filtered_expected_files:
                filtered_file_name = each_filtered_file.replace(self.content_dir, '').strip(self.cl_machine.os_sep)
                for file_details in expected_details:
                    if file_details['path'] == each_filtered_file:
                        expected_dict[filtered_file_name] = file_details['size']

            self.log.info('*************** Verify find operation ***************')
            actual_files = self.subclient.find({'file_name': filter_expression})[1]
            for actual_file in actual_files:
                actual_file_name = actual_file.replace(self.content_dir, '').strip(self.cl_machine.os_sep)
                browse_actual_dict[actual_file_name] = actual_files[actual_file]['size']

            if len(expected_dict) == 0 and len(browse_actual_dict) == 0:
                self.log.info('No files found matching this filter')
            else:
                if not self.match_result(expected_dict, browse_actual_dict):
                    raise Exception(f'Find with filter failed. filter: {filter_expression}')

                self.log.info('*************** Verify restore operation ***************')
                self.common_utils.subclient_restore_out_of_place(
                    destination_path=filter_restore_dir,
                    paths=[self.content_dir],
                    client=self.client,
                    subclient=self.subclient,
                    fs_options={
                        'browse_filters': self.validation._prepare_restore_filters_xml(
                            {'filters': [('FileName', filter_expression)]})
                    }
                )
                restore_actual = self.cl_machine.scan_directory(path=rel_restore_dir, filter_type='file')
                for res_actual_file in restore_actual:
                    restore_file_name = res_actual_file['path'].replace(rel_restore_dir, '').strip(
                        self.cl_machine.os_sep
                    )
                    restore_actual_dict[restore_file_name] = res_actual_file['size']
                filter_number = filter_number + 1
                if not self.match_result(expected_dict, restore_actual_dict):
                    raise Exception(f'Restore file with filter failed. filter: {filter_expression}')

    def match_result(self, expected_files, actual_files):
        """Check if two list of files are same

            Args:
                expected_files   (dict)  --  dict of filenames at the client
                actual_files (dict)  --  dict of filenames that are returned as a result of browse or find or restore

            Returns:
                (Boolean) - True, if the dicts match
                            False, if the dicts don't match
        """
        self.log.info('Expected files at the client: %s', expected_files)
        self.log.info('Actual files that came as a result: %s', actual_files)

        result_difference = commonutils.get_dictionary_difference(expected_files, actual_files)
        self.log.info('Only in expected: %s', result_difference[0])
        self.log.info('Only in actual: %s', result_difference[1])
        self.log.info('Modified: %s', result_difference[2])

        if len(result_difference[0]) == 0 and len(result_difference[1]) == 0:
            self.log.info('Both expected and actual results match')
            return True
        self.log.info('Expected and actual files dont match')
        return False
