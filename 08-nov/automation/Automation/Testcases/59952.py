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

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for Basic Acceptance tests for Browse and Restore: Deleted items, All versions, Point in Time"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance tests for Browse and Restore: Deleted items, All versions, Point in Time"
        self.fs_helper = None
        self.is_nas_turbo_type = None
        self.base_folder_path = None
        self.origin_folder_path = None
        self.UNC_base_folder_path = None
        self.UNC_origin_folder_path = None
        self.test_data_list_unc = None
        self.test_data_list = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.only_dc = None

    def setup(self):
        """Setup function of this test case"""
        self.fs_helper = FSHelper(self)
        self.fs_helper.populate_tc_inputs(self)
        self.log.info("Test inputs populated successfully.")

        self.base_folder_path = self.client_machine.join_path(self.test_path, str(self.fs_helper.testcase.id))
        self.origin_folder_path = self.client_machine.join_path(self.base_folder_path, 'origin')

        if self.base_folder_path.startswith("\\\\"):
            self.is_nas_turbo_type = True

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = f"\\UNC-NT_{self.UNC_base_folder_path}"
            self.UNC_origin_folder_path = self.client_machine.join_path(self.UNC_base_folder_path, 'origin')

        self.client_machine.create_directory(self.base_folder_path, force_create=True)
        self.client_machine.create_directory(self.origin_folder_path, force_create=True)
        self.test_data_list = []
        self.test_data_list_unc = []
        for file in range(0, 10):
            self.test_data_list.append(
                self.client_machine.join_path(self.origin_folder_path, "file{}.txt".format(str(file))))
            if self.is_nas_turbo_type:
                self.test_data_list_unc.append(
                    self.client_machine.join_path(self.UNC_origin_folder_path, "file{}.txt".format(str(file))))
            self.client_machine.create_file(
                self.test_data_list[file],
                content="This is test data generated for file number {}".format(str(file)), file_size=8 * 1024)
        self.log.info("Test data populated successfully.")

        self.fs_helper.create_backupset('Backupsetset_{0}'.format(str(self.fs_helper.testcase.id)), delete=True,
                                        is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.fs_helper.create_subclient('Subclient_{0}'.format(str(self.fs_helper.testcase.id)),
                                        storage_policy=self.storage_policy, delete=True,
                                        content=[self.origin_folder_path])

        if self.is_nas_turbo_type:
            update_properties = self.fs_helper.testcase.subclient.properties
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.fs_helper.testcase.subclient.update_properties(update_properties)

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. create test[0..9] files.
        2. Run full backup job:1.
        3. delete test[0..2] files, modify test3 file.
        4. incremental backup job:2.
        5. add test[10..11] files. again modify the test3 file.
        6. incremental backup job:3.
        8. restore deleted items inplace. test[0..2]
        8. restore all version of test3 files. oop
        9. point in time restore oop for job2 duration. 
        """

        try:
            self.log.info(_desc)
            file3_modified_hash_0 = self.client_machine.get_checksum_list(data_path=self.test_data_list[3])[0]
            origin_hash_before_job1 = self.client_machine.get_checksum_list(data_path=self.origin_folder_path,
                                                                            sorted_output=False)
            self.fs_helper.run_backup()

            for file in range(0, 3):
                self.client_machine.delete_file(self.test_data_list[file])

            self.client_machine.append_to_file(self.test_data_list[3],
                                               content="1st Modified data for file {}".format(str(3)))

            file3_modified_hash_1 = self.client_machine.get_checksum_list(data_path=self.test_data_list[3])[0]
            job2 = self.fs_helper.run_backup()[0]

            for file in range(10, 12):
                self.test_data_list.append(
                    self.client_machine.join_path(self.origin_folder_path, "file{}.txt".format(str(file))))
                if self.is_nas_turbo_type:
                    self.test_data_list_unc.append(
                        self.client_machine.join_path(self.UNC_origin_folder_path, "file{}.txt".format(str(file))))
                self.client_machine.create_file(
                    self.test_data_list[file],
                    content="This is test data generated for file number {}".format(str(file)), file_size=8 * 1024)

            self.client_machine.append_to_file(self.test_data_list[3],
                                               content="1st Modified data for file {}".format(str(3)))
            file3_modified_hash_2 = self.client_machine.get_checksum_list(data_path=self.test_data_list[3])[0]

            self.fs_helper.run_backup()

            self.log.info("Restore Deleted items out of place")
            deleted_folder = self.client_machine.join_path(self.base_folder_path, 'deleted_folder')
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=deleted_folder,
                                                    paths=self.test_data_list_unc[0:3],
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    no_image=True,
                                                    client=self.tcinputs.get("ProxyClient", None),
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser", None),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword", None))
            else:
                self.fs_helper.restore_out_of_place(destination_path=deleted_folder,
                                                    paths=self.test_data_list[0:3],
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    no_image=True)

            restore_deleted_hash = self.client_machine.get_checksum_list(data_path=deleted_folder)
            if self.fs_helper.compare_lists(origin_hash_before_job1[0:3], restore_deleted_hash, sort_list=True):
                self.log.info("Deleted items are restored successfully.")
            else:
                raise Exception("Deleted items are not getting restored.")

            self.log.info("Restore out of place All versions of file3")
            all_versions_folder = self.client_machine.join_path(self.base_folder_path, 'all_versions_file3')
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=all_versions_folder,
                                                    paths=[self.test_data_list_unc[3]],
                                                    all_versions=True,
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                    client=self.tcinputs.get("ProxyClient"),
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10))
            else:
                self.fs_helper.restore_out_of_place(destination_path=all_versions_folder,
                                                    all_versions=True,
                                                    paths=[self.test_data_list[3]],
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10))

            restore_version_hash = self.client_machine.get_checksum_list(all_versions_folder)
            if self.fs_helper.compare_lists([file3_modified_hash_0, file3_modified_hash_1, file3_modified_hash_2],
                                            restore_version_hash, sort_list=True):
                self.log.info("All versions of files are restored correctly.")
            else:
                raise Exception("All versions of files are not restored correctly.")

            self.log.info("Restore out of place Point in time between job2 and job3")
            point_in_time_folder = self.client_machine.join_path(self.base_folder_path, 'point_in_time')
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=point_in_time_folder,
                                                    paths=[self.UNC_origin_folder_path],
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                    client=self.tcinputs.get("ProxyClient"),
                                                    preserve_level=0,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    from_time=job2.start_time,
                                                    to_time=job2.end_time)
            else:
                self.fs_helper.restore_out_of_place(destination_path=point_in_time_folder,
                                                    paths=[self.origin_folder_path],
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    from_time=job2.start_time,
                                                    to_time=job2.end_time)
            point_in_time_hash = self.client_machine.get_checksum_list(data_path=point_in_time_folder)[0]
            if self.fs_helper.compare_lists(point_in_time_hash, file3_modified_hash_1):
                self.log.info("Point in time items are restored successfully.")
            else:
                raise Exception("Point in time items are not getting restored.")

            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance testcase failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
