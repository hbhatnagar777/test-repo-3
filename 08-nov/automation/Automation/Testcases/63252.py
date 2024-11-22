# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    generate_test_data()    --     Generate test data

    enable_archive()        --     Set disk cleanup and retention rules

    change_timestamps()     --     Changes the Access time and Last Modified time of files.

    verify_access_time()     --    Verify that Last Access time of files is not changed.

    verify_modified_time()     --  Verify that Last Modified time of files is not changed.

    verify_automount_unmounted()       --  Validate auto mount path is unmounted.

    verify_number_of_backup_files()    --  Verify all files meet archiving criteria are archived

    verify_archived_files_got_deleted()--  Verify file meet archiving rules were deleted after archiving job

    verify_out_of_place_restore()      --  Run out of place data restore and verify the restore result

    verify_in_place_restore()          --  Run in place data restore and verify the restore result

Input Example:

   "testCases": {
        "63252": {
            "StoragePolicyName": "",
            "AgentName": "",
            "ClientName": "",
            "DataAccessNodes":[],
            "Multipath_Content":[]
        }
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
import time


class TestCase(CVTestCase):
    """Class for NFS AutoMount Multiple Paths Archive and Delete verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "NFS AutoMount archiving with multiple paths - archive and delete"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_origin_folder_path = []
        self.origin_folder_path = []
        self.mount_path = None
        self.mount_folder_path = None
        self.origin_mount_path = None
        self.data_mount_path1 = None
        self.archiveset = ""
        self.test_file_list = []
        self.nfs_server = []
        self.nfs_share = []
        self.OPHelper = None
        self.before_mtime = None
        self.before_atime = None
        self.orig_hashcode = []
        self.content = []
        self.num_path = None
        self.tcinputs = {
            "StoragePolicyName": "",
            "AgentName": "",
            "ClientName": "",
            "DataAccessNodes": [],
            "Multipath_Content": []
        }

    def setup(self):
        """Setup function of this test case"""
        self.tcinputs.setdefault("TestPath", "")
        self.tcinputs.setdefault("NASTurboType", "NetworkShare")
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs(mandatory=False)
        self.log.info("Test inputs populated successfully")
        self.num_path = len(self.tcinputs["Multipath_Content"])

        for i in range(self.num_path):
            test_file_list1 = [(str(i) +
                                "test1.txt", True), (str(i) +
                                                     "test2.txt", True), (str(i) +
                                                                          "test3.txt", True), (str(i) +
                                                                                               "test4.txt", True)]
            self.test_file_list.append(test_file_list1)

        self.mount_path = self.tcinputs.get("MountPath", "/mnt")
        self.log.info("mount path: %s", self.mount_path)
        self.origin_mount_path = self.OPHelper.client_machine.join_path(
            self.mount_path, 'origin')
        self.data_mount_path1 = self.OPHelper.client_machine.join_path(
            self.mount_path, 'restore')

    def generate_test_data(self):
        """ Function to generate test data with required file_size and modified_time attribute """
        for i in range(self.num_path):
            path = self.tcinputs["Multipath_Content"][i]
            self.base_folder_path = path + '{0}{1}'.format(
                self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
            self.content.append(self.base_folder_path)
            self.origin_folder_path.append(
                self.OPHelper.client_machine.join_path(
                    self.base_folder_path, 'origin'))
            self.UNC_origin_folder_path1 = '/' + self.origin_folder_path[i]
            self.UNC_origin_folder_path.append(
                self.UNC_origin_folder_path1.replace(':', ''))
            self.nfs_server.append(path[:path.find(':')])
            self.nfs_share.append(path[path.find(':') + 1:])
            try:
                self.OPHelper.client_machine.unmount_path(
                    mount_path=self.mount_path, force_unmount=True)
            except Exception:
                self.log.info(Exception)
            self.OPHelper.client_machine.mount_nfs_share(
                nfs_client_mount_dir=self.mount_path,
                server=self.nfs_server[i],
                share=self.nfs_share[i])
            self.OPHelper.client_machine.remove_directory(
                self.OPHelper.client_machine.join_path(
                    self.mount_path, str(
                        self.OPHelper.testcase.id)))
            self.OPHelper.test_file_list = self.test_file_list[i]
            hashcode = self.OPHelper.prepare_turbo_testdata(
                self.OPHelper.client_machine.join_path(
                    self.mount_path,
                    str(
                        self.OPHelper.testcase.id),
                    'origin'),
                self.test_file_list[i],
                size1=1024 * 1024,
                size2=1024 * 1024)
            self.orig_hashcode.append(hashcode)
            self.log.info("Test data populated successfully for path %s", path)
            self.log.info(
                "Changing timestamps of all files to older than 90 days")
            self.change_timestamps(
                path=self.OPHelper.client_machine.join_path(
                    self.mount_path, str(
                        self.OPHelper.testcase.id), 'origin'))
            self.OPHelper.client_machine.unmount_path(
                mount_path=self.mount_path, force_unmount=True)

    def enable_archive(self):
        """ Function to enable archiving rules """
        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "fileModifiedTimeOlderThan": 91,
            "fileAccessTimeOlderThan": 89,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 2,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def change_timestamps(self, path):
        """
        Changes the last timestamps of files
        Args:
            path    (str)   --  file paths
        """
        for i in range(4):
            self.OPHelper.client_machine.modify_item_datetime(
                path=self.OPHelper.client_machine.join_path(
                    path, self.OPHelper.test_file_list[i][0]), creation_time=datetime(
                    year=2019, month=1, day=1), access_time=datetime(
                    year=2019, month=3, day=3), modified_time=datetime(
                    year=2019, month=2, day=2))
            time.sleep(30)

        self.before_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(
                path,
                self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()
        self.log.info(self.before_mtime)

        self.before_atime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(
                path,
                self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastAccessTimeUtc'").strip()
        self.log.info(self.before_atime)

    def verify_modified_time(self, path):
        """
        Verify that Last Modified time of files is not changed.
        Args:
            path    (str)   --  file paths
        """
        changed_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(
                path,
                self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

        self.log.info("After mtime: %s", str(changed_mtime))
        self.log.info("Before mtime: %s", str(self.before_mtime))
        if str(self.before_mtime) != str(changed_mtime):
            raise Exception("The mtime of the files have been changed.")
        else:
            self.log.info("The mtime of the files have not been changed.")

    def verify_access_time(self, path):
        """
        Verify that Last Access time of files is not changed.
        Args:
            path    (str)   --  file paths
        """
        changed_atime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(
                path,
                self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastAccessTimeUtc'").strip()

        self.log.info("After: atime: %s", str(changed_atime))
        self.log.info("Before atime: %s", str(self.before_atime))
        if str(self.before_atime) != str(changed_atime):
            raise Exception("The atime of the files have been changed.")
        else:
            self.log.info("The atime of the files have not been changed.")

    def verify_automount_unmounted(self, job_id):
        """
        To Validate auto mount path is unmounted
        Args:
            job_id   (Object)   --  instance of the Job class for this archive job if
                          its an immediate return Job
                          instance of the Job class for the archive job if
                          its a finished Job
        """
        scan_logs = self.OPHelper.client_machine.get_logs_for_job_from_file(
            job_id=job_id, log_file_name="FileScan.log", search_term="FileShareAutoMount::mount")
        logs = scan_logs.split('\n')
        for log in logs:
            log = log.strip()
            if len(log) != 0:
                auto_mount_path = log[log.find(
                    self.OPHelper.client_machine.client_object.install_directory):log.find(",")]
                self.log.info(auto_mount_path)
                if self.OPHelper.client_machine.is_path_mounted(
                        mount_path=auto_mount_path):
                    raise Exception("AutoMount path is still mounted")

        self.log.info("AutoMount path was unmounted after the job.")

    def verify_number_of_backup_files(self):
        """verify number of files are archived correctly"""
        backedup_list, __ = self.subclient.find(
            file_name='*.txt', show_deleted=True)
        self.log.info("Deleted backed up items in dir: " +
                      str(len(backedup_list)))

        to_be_archived = 0
        for test_file_list in self.test_file_list:
            for file in test_file_list:
                if file[1]:
                    to_be_archived += 1
        self.log.info("to be archived : %s", str(to_be_archived))

        if len(backedup_list) is to_be_archived:
            self.log.info("The files are backed up successfully.")
        else:
            raise Exception("The files are not backed up correctly.")

    def verify_out_of_place_restore(self):
        """run out of place restore and verify the restore result"""
        self.OPHelper.client_machine.mount_nfs_share(
            nfs_client_mount_dir=self.mount_path,
            server=self.nfs_server[0],
            share=self.OPHelper.client_machine.join_path(
                self.nfs_share[0],
                str(
                    self.OPHelper.testcase.id)))
        file_paths = []
        for i in range(self.num_path):
            file_paths.extend([self.OPHelper.client_machine.join_path(
                self.UNC_origin_folder_path[i], file[0]) for file in self.test_file_list[i]])
        self.OPHelper.restore_out_of_place(
            client=self.OPHelper.agent_name_list[0],
            destination_path=self.data_mount_path1,
            paths=file_paths,
            fs_options={
                'restoreDataInsteadOfStub': True},
            proxy_client=self.tcinputs.get("DataAccessNodes")[0],
            restore_ACL=False,
            restore_data_and_acl=False,
            no_of_streams=10)
        restore_hashcode = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.data_mount_path1)
        org_hashcode = []
        for hashcode in self.orig_hashcode:
            org_hashcode.extend(hashcode)
        _matched, _code = self.client_machine._compare_lists(
            sorted(restore_hashcode),
            sorted(org_hashcode)
        )
        if _matched is False:
            raise Exception("At least one restored file " +
                            " does not match with the original")

        self.OPHelper.client_machine.unmount_path(
            mount_path=self.mount_path, force_unmount=True)

        self.log.info(
            "Successfully verified onepass out of place data restore")

    def verify_in_place_restore(self):
        """run in place restore and verify the restore result"""
        file_paths = []
        for i in range(self.num_path):
            file_paths.extend([self.OPHelper.client_machine.join_path(
                self.UNC_origin_folder_path[i], file[0]) for file in self.test_file_list[i]])

        job = self.OPHelper.restore_in_place(
            client=self.OPHelper.agent_name_list[0],
            paths=file_paths,
            restoreDataInsteadOfStub=True,
            proxy_client=self.tcinputs.get("DataAccessNodes")[0],
            no_of_streams=10)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: "
                + job.delay_reason
            )
        if not job.status.lower() == "completed":
            raise Exception(
                "Job status is not Completed, job has status: "
                + job.status
            )

        for i in range(self.num_path):
            self.OPHelper.client_machine.mount_nfs_share(
                nfs_client_mount_dir=self.mount_path,
                server=self.nfs_server[i],
                share=self.OPHelper.client_machine.join_path(
                    self.nfs_share[i],
                    str(
                        self.OPHelper.testcase.id)))

            restore_hashcode = self.OPHelper.client_machine.get_checksum_list(
                data_path=self.origin_mount_path)

            time.sleep(60)
            _matched, _code = self.client_machine._compare_lists(
                sorted(restore_hashcode),
                sorted(self.orig_hashcode[i])
            )
            if _matched is False:
                raise Exception("At least one restored file " +
                                " does not match with the original")
            self.OPHelper.client_machine.unmount_path(
                mount_path=self.mount_path, force_unmount=True)

        self.log.info("Successfully verified onepass in place data restore")

    def verify_archived_files_got_deleted(self):
        """ Verifies that Archived files are deleted or not. """
        for i in range(self.num_path):
            self.OPHelper.test_file_list = self.test_file_list[i]
            self.OPHelper.client_machine.mount_nfs_share(
                nfs_client_mount_dir=self.mount_path,
                server=self.nfs_server[i],
                share=self.OPHelper.client_machine.join_path(
                    self.nfs_share[i],
                    str(
                        self.OPHelper.testcase.id)))
            time.sleep(120)
            if (
                (
                    self.OPHelper.client_machine.check_file_exists(
                        self.OPHelper.client_machine.join_path(
                            self.origin_mount_path,
                            self.OPHelper.test_file_list[0][0])) is False) and (
                    self.OPHelper.client_machine.check_file_exists(
                        self.OPHelper.client_machine.join_path(
                            self.origin_mount_path,
                            self.OPHelper.test_file_list[1][0])) is False) and (
                                self.OPHelper.client_machine.check_file_exists(
                                    self.OPHelper.client_machine.join_path(
                                        self.origin_mount_path,
                                        self.OPHelper.test_file_list[2][0])) is False) and (
                                            self.OPHelper.client_machine.check_file_exists(
                                                self.OPHelper.client_machine.join_path(
                                                    self.origin_mount_path,
                                                    self.OPHelper.test_file_list[3][0])) is False)):
                self.log.info("Delete the file option property is satisfied.")
            else:
                raise Exception(
                    "Delete the file options property is not satisfied")
            self.OPHelper.client_machine.unmount_path(
                mount_path=self.mount_path, force_unmount=True)

    def run(self):
        """Run function of this test case"""
        _desc = """
        1. Create test files with atime and mtime greater than 90 days.
        2. Create Archiveset and Subclient and run archive job.
        3. Validate that automount created during the archive job was unmounted.
        4. Verify the files are deleted after archiving.
        5. Restore out of place as data and verify files are restored as data.
        6. restore in place as data and verify files are restored correctly
        """
        try:
            self.log.info(_desc)
            self.generate_test_data()

            self.OPHelper.create_archiveset(
                delete=True, is_nas_turbo_backupset=True)
            self.OPHelper.create_subclient(
                name=self.base_folder_path,
                delete=True,
                content=self.content,
                scan_type=ScanType.RECURSIVE)

            self.enable_archive()
            job = self.OPHelper.run_archive(repeats=1)[0]

            self.verify_automount_unmounted(job.job_id)
            self.verify_archived_files_got_deleted()
            self.verify_number_of_backup_files()
            self.verify_out_of_place_restore()
            self.verify_in_place_restore()

            self.log.info(
                'NFS AutoMount MultiplePath Archive and Delete test case run successfully')
            self.status = constants.PASSED

        except Exception as exp:
            try:
                self.OPHelper.client_machine.unmount_path(
                    mount_path=self.mount_path, force_unmount=True)
            except Exception:
                self.log.info(Exception)
            self.log.error(
                'NFS AutoMount Multiple Path Archive and Delete test is not running correctly with error: %s',
                exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
        finally:
            self.log.info("Clean up test archiveset")
            self.instance.backupsets.delete(
                'Archiveset_{0}'.format(str(self.id)))
