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
import time

class TestCase(CVTestCase):
    """Class for Basic Acceptance tests for Restore: Unconditional Overwrite, Restore only newer, Restore ACLs Only, Restore Data Only, Restore Both ACLs and Data"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance tests for Restore: Unconditional Overwrite, Restore only newer, Restore ACLs Only, Restore Data Only, Restore Both ACLs and Data"
        self.fs_helper = None
        self.is_nas_turbo_type = None
        self.base_folder_path = None
        self.origin_folder_path = None
        self.UNC_base_folder_path = None
        self.UNC_origin_folder_path = None
        self.origin_hash = None
        self.origin_acl = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

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

        if self.client_machine.check_directory_exists(self.base_folder_path):
            self.log.info("Removing subclient content %s", self.base_folder_path)
            self.client_machine.remove_directory(self.base_folder_path)

        time.sleep(60)
        self.client_machine.create_directory(self.base_folder_path, force_create=True)
        self.client_machine.generate_test_data(file_path=self.origin_folder_path, acls=True,
                                               username=self.tcinputs.get("ImpersonateUser"),
                                               password=self.tcinputs.get("ImpersonatePassword"))

        self.origin_hash = self.client_machine.get_checksum_list(data_path=self.origin_folder_path)
        origin_acl = self.client_machine.get_acl_list(data_path=self.origin_folder_path)
        self.origin_acl = []
        for item in origin_acl:
            if "owner" in item:
                self.origin_acl.append(item)

        self.log.info("Test data populated successfully.")

        self.fs_helper.create_backupset('Backupsetset_{0}'.format(str(self.fs_helper.testcase.id)), delete=True,
                                        is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.fs_helper.create_subclient('Subclient_{0}'.format(str(self.fs_helper.testcase.id)),
                                        storage_policy=self.storage_policy, delete=True,
                                        content=[self.origin_folder_path], catalog_acl=True)

        if self.is_nas_turbo_type:
            update_properties = self.fs_helper.testcase.subclient.properties
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.fs_helper.testcase.subclient.update_properties(update_properties)

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. create test data.
        2. Run full backup job:1.
        3. Restore oop both data and acl and verify.
        4. Restore oop data only and verify.
        5. Restore oop acl only and verify.
        6. Modify in place data and acls.
        7. restore only if file in backup is newer in place and verify.
        8. unconditional overwrite inplace and verify.
        """

        try:

            self.log.info(_desc)
            self.fs_helper.run_backup()

            self.log.info("Restore out of place Both Data and ACLs")
            oop_data_acl_folder = self.client_machine.join_path(self.base_folder_path, 'oop_data_acl')
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_acl_folder,
                                                    paths=[self.UNC_origin_folder_path],
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                    client=self.tcinputs.get("ProxyClient"),
                                                    restore_data_and_acl=True,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)
            else:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_acl_folder,
                                                    paths=[self.origin_folder_path],
                                                    restore_data_and_acl=True,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)

            oop_data_acl_folder_hash = self.client_machine.get_checksum_list(data_path=oop_data_acl_folder)
            oop_data_acl_folder_acls = self.client_machine.get_acl_list(data_path=oop_data_acl_folder)
            oop_data_acl_folder_acls_cleaned = []
            for item in oop_data_acl_folder_acls:
                if "owner" in item:
                    oop_data_acl_folder_acls_cleaned.append(item)

            if self.fs_helper.compare_lists(self.origin_hash, oop_data_acl_folder_hash,
                                            sort_list=True) and self.fs_helper.compare_lists(
                        self.origin_acl, oop_data_acl_folder_acls_cleaned, sort_list=True):
                self.log.info("Data and ACL restored correctly.")
            else:
                raise Exception("Data and ACL IS NOT restored correctly.")

            self.log.info("Restore out of place Data only")
            oop_data_folder = self.client_machine.join_path(self.base_folder_path, 'oop_data')
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_folder,
                                                    paths=[self.UNC_origin_folder_path],
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                    client=self.tcinputs.get("ProxyClient"),
                                                    restore_ACL=False,
                                                    restore_data_and_acl=False,
                                                    restore_data_only=True,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)
            else:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_folder,
                                                    paths=[self.origin_folder_path],
                                                    restore_ACL=False,
                                                    restore_data_and_acl=False,
                                                    restore_data_only=True,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)

            oop_data_folder_hash = self.client_machine.get_checksum_list(data_path=oop_data_folder)
            oop_data_folder_acls = self.client_machine.get_acl_list(data_path=oop_data_folder)

            oop_data_folder_acls_cleaned = []
            for item in oop_data_folder_acls:
                if "owner" in item:
                    oop_data_folder_acls_cleaned.append(item)

            if self.fs_helper.compare_lists(self.origin_hash, oop_data_folder_hash, sort_list=True):
                self.log.info("Data is restored correctly.")
            else:
                raise Exception("Data IS NOT restored correctly.")

            self.log.info("Restore out of place ACLs")
            if self.is_nas_turbo_type:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_folder,
                                                    paths=[self.UNC_origin_folder_path],
                                                    impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                    impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                    client=self.tcinputs.get("ProxyClient"),
                                                    restore_acls_only=True,
                                                    restore_ACL=True,
                                                    restore_data_and_acl=False,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)
            else:
                self.fs_helper.restore_out_of_place(destination_path=oop_data_folder,
                                                    paths=[self.origin_folder_path],
                                                    restore_acls_only=True,
                                                    restore_ACL=True,
                                                    restore_data_and_acl=False,
                                                    no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                    preserve_level=0)

            oop_data_folder_hash = self.client_machine.get_checksum_list(data_path=oop_data_folder)
            oop_data_folder_acls = self.client_machine.get_acl_list(data_path=oop_data_folder)

            oop_data_folder_acls_cleaned = []
            for item in oop_data_folder_acls:
                if "owner" in item:
                    oop_data_folder_acls_cleaned.append(item)

            if self.fs_helper.compare_lists(self.origin_hash, oop_data_folder_hash, sort_list=True):
                self.log.info("Data is restored correctly.")
            else:
                raise Exception("Data IS NOT restored correctly.")

            if self.fs_helper.compare_lists(self.origin_acl, oop_data_folder_acls_cleaned):
                self.log.info("ACLs is restored when restore only ACL is selected.")
            else:
                raise Exception("ACLs is not restored when restore only ACL is selected.")

            self.log.info("Modifying in place data")
            self.client_machine.modify_test_data(data_path=self.origin_folder_path, modify=True, acls=True)
            modified_origin_hash = self.client_machine.get_checksum_list(data_path=self.origin_folder_path)
            modified_origin_acl = self.client_machine.get_acl_list(data_path=self.origin_folder_path)

            modified_origin_acls_cleaned = []
            for item in modified_origin_acl:
                if "owner" in item:
                    modified_origin_acls_cleaned.append(item)

            if self.is_nas_turbo_type:
                self.fs_helper.restore_in_place(paths=[self.UNC_origin_folder_path], overwriteFiles=True,
                                                overwrite=False,
                                                no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                proxy_client=self.tcinputs.get("ProxyClient", None),
                                                impersonate_user=self.tcinputs.get("ImpersonateUser", None),
                                                impersonate_password=self.tcinputs.get("ImpersonatePassword", None))
            else:
                self.fs_helper.restore_in_place(paths=[self.origin_folder_path], overwriteFiles=True, overwrite=False,
                                                no_of_streams=self.tcinputs.get("RestoreStreams", 10))

            self.log.info("Getting restore only newer checksum and ACLs")
            restore_only_newer_origin_hash = self.client_machine.get_checksum_list(
                data_path=self.origin_folder_path)
            restore_only_newer_origin_acl = self.client_machine.get_acl_list(
                data_path=self.origin_folder_path)

            restore_only_newer_origin_acls_cleaned = []
            for item in restore_only_newer_origin_acl:
                if "owner" in item:
                    restore_only_newer_origin_acls_cleaned.append(item)

            self.log.info("comparing modified and restore only new checksum and ACLs")
            if not self.fs_helper.compare_lists(modified_origin_hash, restore_only_newer_origin_hash, sort_list=True):
                raise Exception("Inplace restore only newer hash differs")
            else:
                self.log.info("Restore only newer and modified hash matches.")

            if self.applicable_os == self.os_list.UNIX.name:
                for modified_file_acl, restore_file_acl in zip(modified_origin_acls_cleaned,
                                                               restore_only_newer_origin_acls_cleaned):
                    if "file" in modified_file_acl and "file" in restore_file_acl:
                        if modified_file_acl != restore_file_acl:
                            raise Exception("Inplace restore only newer ACLs differs")
            else:
                if not self.fs_helper.compare_lists(
                            modified_origin_acls_cleaned, restore_only_newer_origin_acls_cleaned,
                            sort_list=True):
                    raise Exception("Inplace restore only newer ACLs differs")
                else:
                    self.log.info("Restore only newer and modified ACLs matches.")

            if self.is_nas_turbo_type:
                self.fs_helper.restore_in_place(paths=[self.UNC_origin_folder_path], overwrite=True,
                                                overwriteFiles=False,
                                                no_of_streams=self.tcinputs.get("RestoreStreams", 10),
                                                proxy_client=self.tcinputs.get("ProxyClient", None),
                                                impersonate_user=self.tcinputs.get("ImpersonateUser", None),
                                                impersonate_password=self.tcinputs.get("ImpersonatePassword", None))
            else:
                self.fs_helper.restore_in_place(paths=[self.origin_folder_path], overwrite=True, overwriteFiles=False,
                                                no_of_streams=self.tcinputs.get("RestoreStreams", 10))

            self.log.info("Getting restore unconditionally checksum and ACLs")
            restore_unconditionally_origin_hash = self.client_machine.get_checksum_list(
                data_path=self.origin_folder_path)
            restore_unconditionally_origin_acl = self.client_machine.get_acl_list(
                data_path=self.origin_folder_path)

            restore_unconditionally_origin_acl_cleaned = []
            for item in restore_unconditionally_origin_acl:
                if "owner" in item:
                    restore_unconditionally_origin_acl_cleaned.append(item)

            self.log.info("comparing initial and restore unconditionally checksum and ACLs")
            if not self.fs_helper.compare_lists(self.origin_hash, restore_unconditionally_origin_hash, sort_list=True):
                raise Exception("Inplace restore unconditionally hash differs")
            else:
                self.log.info("Restore unconditionally and initial hash matches.")
            if not self.fs_helper.compare_lists(self.origin_acl, restore_unconditionally_origin_acl_cleaned,
                                                sort_list=True):
                raise Exception("Inplace restore unconditionally ACLs differs")
            else:
                self.log.info("Restore unconditionally and initial ACLs matches.")

            self.log.info('Basic Acceptance tests for File System Restores passed')
            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance tests failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
