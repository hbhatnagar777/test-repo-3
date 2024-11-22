# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that backup, restore of data when backup only ACL feature is enabled

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    get_file_path()             --  Returns the file path for the given directory

    verify_no_extents()         --  Verifies that no extents are backed up by doing a browse

    verify_no_acl()             --  Verifies that files are backed up in normal way, without
    ACL only

    verify_restore_and_permissions() --  Starts restore and verifies file permission once complete

    verify_restore_and_checksum()   --  Verifies latest cycle restore and verifies file
    md5 hash against source

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback

from AutomationUtils import commonutils
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that backup, restore of data when backup only
    ACL feature is enabled"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Backup only ACL - Acceptance testcase'
        self.show_to_user = False

        self.tcinputs = {
            'StoragePolicyName': None
        }

        self.backupset = None
        self.subclient = None
        self.storage_policy = None
        self.sc_content = None

        self.cl_machine = None
        self.cl_delim = None
        self.idx_tc = None
        self.idx_help = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.backupset_name = self.tcinputs.get('Backupset', 'acl_only_auto1')
            self.subclient_name = self.tcinputs.get('Subclient', self.id)
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')

            self.cl_machine = Machine(self.client, self.commcell)
            self.cl_delim = self.cl_machine.os_sep

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name)

            self.subclient = self.idx_tc.create_subclient(
                name=self.subclient_name,
                backupset_obj=self.backupset,
                storage_policy=self.storagepolicy_name
            )

            sc_content_tmp = self.subclient.content
            self.log.info(sc_content_tmp)

            if isinstance(sc_content_tmp, list) and len(sc_content_tmp) > 1:
                self.subclient.content = sc_content_tmp[0]

            self.sc_content = self.subclient.content[0]
            self.log.info(self.sc_content)
            self.acl_files_dir = self.cl_delim.join([self.sc_content, 'acl_files'])

            self.cl_machine.create_registry('FileSystemAgent', 'nACLOnlyBackup', '0')

            self.cl_machine.create_registry('FileSystemAgent', 'bEnableFileExtentBackup', '0')

            self.cl_machine.create_registry(
                'FileSystemAgent', 'mszFileExtentSlabs', '15-100=4')

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            file1 = self.get_file_path('file_0001.txt')  # Reg, ACL, ACL, ACL, ACL
            file2 = self.get_file_path('file_0002.txt')  # Reg, ACL, DEL
            file3 = self.get_file_path('file_0003.txt')  # Reg, EXT, ACL, ACL, ACL
            file4 = self.get_file_path('file_0004.txt')  # Reg, EXT, DEL
            file5 = self.get_file_path('file_0005.txt')  # Reg, EXT, ACL, EXT, ACL

            self.log.info('********** FULL - JOB **********')
            self.idx_tc.new_testdata(self.sc_content)
            self.idx_tc.create_only_files(
                self.sc_content, base_dir='acl_files', count=5,
                size=(30000000, 50000000), name='file', extensions=['txt'])

            self.cl_machine.change_file_permissions(file1, 770)
            self.cl_machine.change_file_permissions(file2, 770)
            self.cl_machine.change_file_permissions(file3, 770)
            self.cl_machine.change_file_permissions(file4, 770)
            self.cl_machine.change_file_permissions(file5, 770)
            full_job = self.idx_tc.run_backup(self.subclient, 'full')

            # Verification
            self.verify_no_extents()

            self.log.info('********** Enabling ACL only backup for the client **********')
            self.cl_machine.create_registry('FileSystemAgent', 'nACLOnlyBackup', '1')
            self.cl_machine.create_registry('FileSystemAgent', 'bEnableFileExtentBackup', '1')

            self.log.info('********** INC 1 - JOB **********')
            self.cl_machine.change_file_permissions(file1, 771)
            self.cl_machine.change_file_permissions(file2, 771)
            self.idx_tc.edit_files([file3, file4, file5])
            inc1_job = self.idx_tc.run_backup(self.subclient, 'incremental')

            # Verification
            self.idx_help.verify_acl_only_flag(self.subclient, [file1, file2])
            self.idx_help.verify_extents_files_flag(self.subclient, 30000000, [
                file3, file4, file5
            ])
            self.verify_no_acl([file3, file4, file5])

            self.log.info('********** Latest cycle browse and restore 1 - ACL Files **********')
            self.verify_restore_and_permissions({
                file1: '771',
                file2: '771',
                file3: '770',
                file4: '770',
                file5: '770',
            })

            self.log.info('********** INC 2 - JOB **********')
            self.cl_machine.change_file_permissions(file1, 772)
            self.cl_machine.delete_file(file2)
            self.cl_machine.change_file_permissions(file3, 772)
            self.cl_machine.delete_file(file4)
            self.cl_machine.change_file_permissions(file5, 772)
            inc2_job = self.idx_tc.run_backup(self.subclient, 'incremental')

            # Verification
            self.idx_help.verify_acl_only_flag(self.subclient, [file1, file3, file5])

            self.log.info('********** INC 3 - JOB **********')
            self.cl_machine.change_file_permissions(file1, 773)
            self.cl_machine.change_file_permissions(file3, 773)
            self.idx_tc.edit_files(file5)
            inc3_job = self.idx_tc.run_backup(self.subclient, 'incremental')

            # Verification
            self.idx_help.verify_acl_only_flag(self.subclient, [file1, file3])
            self.idx_help.verify_extents_files_flag(self.subclient, 30000000, file5)

            self.log.info('********** Latest cycle browse and restore 1 - All files **********')
            self.verify_restore_and_checksum()

            self.log.info('********** Latest cycle browse and restore 2 - ACL files **********')
            self.verify_restore_and_permissions({
                file1: '773',
                file2: '771',
                file3: '773',
                file4: '770',
                file5: '772',
            })

            self.log.info('********** Point in time restore INC2 - ACL files **********')
            self.verify_restore_and_permissions({
                file1: '772',
                file2: '771',
                file3: '772',
                file4: '770',
                file5: '772'
            }, to_time_job=inc2_job)

            self.log.info('********** SFULL 1 - JOB **********')
            sfull1_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full')

            self.log.info('********** Latest cycle browse and restore 2 - All files **********')
            self.verify_restore_and_checksum()

            self.log.info('********** After SFULL job 1 - Latest browse and restore **********')
            self.verify_restore_and_permissions({
                file1: '773',
                file3: '773',
                file5: '772'
            })

            self.log.info('********** INC 4 - JOB **********')
            self.cl_machine.change_file_permissions(file1, 774)
            self.cl_machine.change_file_permissions(file3, 774)
            self.cl_machine.change_file_permissions(file5, 774)
            inc4_job = self.idx_tc.run_backup(self.subclient, 'incremental')

            # Verification
            self.idx_help.verify_acl_only_flag(self.subclient, [file1, file3, file5])

            self.log.info('********** INC 5 - JOB **********')
            self.cl_machine.change_file_permissions(file1, 775)
            self.cl_machine.change_file_permissions(file3, 775)
            self.idx_tc.edit_files(file5)
            inc5_job = self.idx_tc.run_backup(self.subclient, 'incremental')

            # Verification
            self.idx_help.verify_acl_only_flag(self.subclient, [file1, file3])
            self.idx_help.verify_extents_files_flag(self.subclient, 30000000, file5)

            self.log.info('********** SFULL 2 - JOB **********')
            sfull2_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full')

            self.log.info('********** Latest cycle browse and restore 3 - All files **********')
            self.verify_restore_and_checksum()

            self.log.info('********** After SFULL job 2 browse and restore **********')
            self.verify_restore_and_permissions({
                file1: '775',
                file3: '775',
                file5: '774',
            })

            self.log.info('********** Point in time restore INC4 - ACL files directory **********')
            self.verify_restore_and_permissions({
                file1: '774',
                file3: '774',
                file5: '774'
            }, to_time_job=inc4_job)

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def get_file_path(self, name, base_dir='acl_files'):
        """Returns the file path for the given directory"""

        return self.cl_delim.join([self.sc_content, base_dir, name])

    def verify_no_extents(self):
        """Verifies that no extents are backed up by doing a browse"""

        has_extents = False
        try:
            self.idx_help.verify_extents_files_flag(self.subclient, 30000000)
            has_extents = True
        except Exception:
            self.log.info('********** Files do not have extents **********')

        if has_extents:
            raise Exception('Files have extents which is not expected')

    def verify_no_acl(self, file_paths):
        """Verifies that files are backed up in normal way, without ACL only"""

        is_acl_only = False
        try:
            self.idx_help.verify_acl_only_flag(self.subclient, file_paths)
            is_acl_only = True
        except Exception:
            self.log.info('********** Files do not have ACL only flag **********')

        if is_acl_only:
            raise Exception('One of the file has ACL only flag **********')

    def verify_restore_and_permissions(self, exp_permissions, to_time_job=None):
        """Starts restore and verifies file permission once complete"""

        to_time = (0 if to_time_job is None
                   else commonutils.convert_to_timestamp(to_time_job.end_time))

        ret_code, restored_files = self.subclient.idx.validate_restore({
            'operation': 'find',
            'path': '/**/*',
            'show_deleted': True,
            'from_time': 0,
            'to_time': to_time,
            'restore': {
                'do': True,
                'source_items': self.acl_files_dir
            }
        })

        if ret_code == -1:
            raise Exception('Restore results of ACL files are incorrect')

        restored_dir = self.subclient.idx.last_restore_directory

        self.log.info('********** Verifying file permissions **********')
        self.idx_tc.verify_item_permissions(
            restored_files, exp_permissions, restored_dir, self.sc_content)

    def verify_restore_and_checksum(self):
        """Verifies latest cycle restore and verifies file md5 hash against source"""

        self.subclient.idx.validate_browse_restore({
            'show_deleted': False,
            'restore': {
                'do': True,
                'source_items': self.sc_content,
                'preserve_level': 0
            }
        })

        self.log.info('********** Verifying checksum after restore job **********')
        ret_code, diff_list = self.cl_machine.compare_checksum(
            self.sc_content, self.subclient.idx.last_restore_directory)

        if not ret_code:
            self.log.error(diff_list)
            raise Exception('Mismatch in file checksum after latest browse restore')

    def tear_down(self):
        """Cleans the data created for Indexing validation and reset time"""

        self.backupset.idx.cleanup()

        self.log.info('Removing registry keys set by the testcase')

        registries = [
            ('FileSystemAgent', 'nACLOnlyBackup'),
            ('FileSystemAgent', 'bEnableFileExtentBackup'),
            ('FileSystemAgent', 'mszFileExtentSlabs')
        ]

        for registry in registries:
            self.log.info('Checking registry key [{0}]'.format(registry))
            if self.cl_machine.check_registry_exists(registry[0], registry[1]):
                if self.cl_machine.remove_registry(registry[0], registry[1]):
                    self.log.info('Successfully removed')
                else:
                    self.log.info('Error while removing registry key')
            else:
                self.log.error('Registry key does not exist')
