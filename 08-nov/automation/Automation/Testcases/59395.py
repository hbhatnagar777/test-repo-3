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

    verify_file_attributes()    --  to verify the attributes of the files.

    verify_file_size_on_disk()  --  to verify size of file on disk.

    verify_file_size()  --  to verify file size.

    verify_modified_time()  --  to verify the modified time of the file.

    prepare_subclient() --  to create and set subclient properties.

    prepare_test_data() --  to prepare test data.
"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper, ScanType
from AutomationUtils import constants
import time


class TestCase(CVTestCase):
    """Class for Cross Platform stubs restore Celerra to Local, Dmnas, Netapp."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Cross Platform stubs restore Celerra to Local, Dmnas, Netapp."
        self.local_folder_path = None
        self.celerra_folder_path = None
        self.dmnas_folder_path = None
        self.netapp_folder_path = None
        self.UNC_celerra_folder_path = None
        self.before_mtime = None
        self.OPHelper = None
        self.tcinputs = {
            "StoragePolicyName": None,
            'LocalPath': None,
            'CelerraPath': None,
            'DmnasPath': None,
            'NetappPath': None
        }

    def prepare_test_data(self, path):
        """ to prepare test data.  """

        self.OPHelper.org_hashcode = self.OPHelper.prepare_turbo_testdata(
            path,
            self.OPHelper.test_file_list,
            size1=self.tcinputs.get("OriginalFileSize", 1024 * 1024),
            size2=self.tcinputs.get("OriginalFileSize", 1024 * 1024)
        )
        self.before_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

    def prepare_subclient(self, path):
        """ to create and set subclient properties. """

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=True)
        self.OPHelper.create_subclient(delete=True, content=[path], scan_type=ScanType.RECURSIVE)

        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
        update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def verify_file_attributes(self, path, valid_attributes=['ARCHIVE', 'OFFLINE', 'SPARSEFILE', 'REPARSEPOINT']):
        """ to verify the attributes of the files.   """

        attributes_list = self.OPHelper.client_machine.get_test_data_info(data_path=path,
                                                                          custom_meta_list="'Attributes'")
        for attributes, file in zip(attributes_list.strip().split('\r\n'), list(zip(*self.OPHelper.test_file_list))[0]):
            if any(x.upper() not in attributes.upper() for x in valid_attributes):
                raise Exception(
                    "Following File : " + file + " with Attributes : " + attributes + "Is not Expected. Valid is " +
                    str(valid_attributes))
            else:
                self.log.info("Attributes of file %s are %s", file, attributes)

    def verify_file_size_on_disk(self, path, valid_size=0):
        """ To verify size of file on disk.  """

        size_list = self.OPHelper.client_machine.get_test_data_info(data_path=path,
                                                                    custom_meta_list="'SizeOnDisk','FilesOnly'")
        for size, file in zip(size_list.split(), list(zip(*self.OPHelper.test_file_list))[0]):
            if int(size.strip()) != valid_size:
                raise Exception(
                    "Following File : " + file + " with size : " + size + " Is not Expected. Valid is " + str(
                        valid_size))
            else:
                self.log.info("The size on disk of file %s is %s", file, size)

    def verify_file_size(self, path, valid_size=0):
        """ To verify size of file. """

        size_list = self.OPHelper.client_machine.get_test_data_info(data_path=path,
                                                                    custom_meta_list="'Size','FilesOnly'")
        for size, file in zip(size_list.split(), list(zip(*self.OPHelper.test_file_list))[0]):
            if int(size.strip()) != valid_size:
                raise Exception(
                    "Following File : " + file + " with size : " + size + " Is not Expected. Valid is " + str(
                        valid_size))
            else:
                self.log.info("The size of file %s is %s", file, size)

    def verify_modified_time(self, path):
        """ Verify that Last Modified time of files is not changed. """

        changed_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

        self.log.info("After mtime: %s", str(changed_mtime))
        self.log.info("Before mtime: %s", str(self.before_mtime))
        if str(self.before_mtime) != str(changed_mtime):
            raise Exception("The mtime of the files have been changed.")
        else:
            self.log.info("The mtime of the files have not been changed.")

    def setup(self):
        """Setup function of this test case"""

        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully.")

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.local_folder_path = self.tcinputs.get('LocalPath', None) + '{0}{1}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.celerra_folder_path = self.tcinputs.get('CelerraPath', None) + '{0}{1}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.dmnas_folder_path = self.tcinputs.get('DmnasPath', None) + '{0}{1}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.netapp_folder_path = self.tcinputs.get('NetappPath', None) + '{0}{1}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.UNC_celerra_folder_path = "\\UNC-NT_" + self.celerra_folder_path[2:]

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Prepare test data and sub-client.
        2. Run archive jobs to backup, stub and backup stubs on Celerra.
        3. Verify file size, file size on disk, attributes on Celerra.
        4. Recall file and verify modified time and attributes.
        5. Out of place Restore stub to Local.
        6. Verify file size, file size on disk, attributes on Local.
        7. Recall file and verify modified time and attributes on Local.
        8. Out of place Restore stub to Dmnas.
        9. Verify file size, file size on disk, attributes on Dmnas.
        10. Recall file and verify modified time and attributes on Dmnas.
        11. Out of place Restore stub to Netapp.
        12. Verify file size, file size on disk, attributes on Netapp.
        13. Recall file and verify modified time and attributes on Netapp.
        """

        try:
            self.log.info(_desc)
            self.prepare_test_data(self.celerra_folder_path)
            self.prepare_subclient(self.celerra_folder_path)
            self.OPHelper.run_archive(repeats=3)

            self.log.info("For Celerra Client")
            time.sleep(240)
            self.verify_file_attributes(path=self.celerra_folder_path,
                                        valid_attributes=self.tcinputs.get('CelerraStubAttributes',
                                                                           ['OFFLINE', 'SPARSEFILE']))
            self.verify_file_size_on_disk(path=self.celerra_folder_path,
                                          valid_size=self.tcinputs.get("CelerraStubSizeOnDisk", 8192))
            self.verify_file_size(path=self.celerra_folder_path,
                                  valid_size=self.tcinputs.get("CelerraStubSize", 1024 * 1024))
            self.OPHelper.recall(path=self.celerra_folder_path)
            self.verify_file_attributes(path=self.celerra_folder_path,
                                        valid_attributes=self.tcinputs.get('CelerraRecalledStubAttributes',
                                                                           ['ARCHIVE']))
            self.verify_modified_time(path=self.celerra_folder_path)

            self.log.info("For Local Client")
            self.OPHelper.restore_out_of_place(client=self.tcinputs.get("ProxyClient"),
                                               destination_path=self.local_folder_path,
                                               paths=[self.OPHelper.client_machine.join_path(
                                                   self.UNC_celerra_folder_path, file[0])
                                                   for file in self.OPHelper.test_file_list],
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               proxy_client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               no_of_streams=10)
            time.sleep(240)
            self.verify_file_attributes(path=self.local_folder_path,
                                        valid_attributes=self.tcinputs.get('LocalRestoredStubAttributes',
                                                                           ['ARCHIVE', 'OFFLINE', 'SPARSEFILE',
                                                                            'REPARSEPOINT']))
            self.verify_file_size_on_disk(path=self.local_folder_path,
                                          valid_size=self.tcinputs.get("LocalStubSizeOnDisk", 0))
            self.verify_file_size(path=self.local_folder_path,
                                  valid_size=self.tcinputs.get("LocalStubSize", 1024 * 1024))
            self.OPHelper.recall(path=self.local_folder_path)
            self.verify_file_attributes(path=self.local_folder_path,
                                        valid_attributes=self.tcinputs.get('LocalRecalledStubAttributes', ['ARCHIVE']))
            self.verify_modified_time(path=self.local_folder_path)

            self.log.info("For Dmnas Client")
            self.OPHelper.restore_out_of_place(client=self.tcinputs.get("ProxyClient"),
                                               destination_path=self.dmnas_folder_path,
                                               paths=[self.OPHelper.client_machine.join_path(
                                                   self.UNC_celerra_folder_path, file[0])
                                                   for file in self.OPHelper.test_file_list],
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               proxy_client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               no_of_streams=10)
            time.sleep(240)
            self.verify_file_attributes(path=self.dmnas_folder_path,
                                        valid_attributes=self.tcinputs.get('DmnasRestoredStubAttributes',
                                                                           ['ARCHIVE', 'OFFLINE']))
            self.verify_file_size(path=self.dmnas_folder_path,
                                  valid_size=self.tcinputs.get("DmnasStubSize", 1234))
            self.OPHelper.recall(path=self.dmnas_folder_path)
            self.verify_file_attributes(path=self.dmnas_folder_path,
                                        valid_attributes=self.tcinputs.get('DmnasRecalledStubAttributes', ['ARCHIVE']))
            self.verify_modified_time(path=self.dmnas_folder_path)

            self.log.info("For Netapp Client")
            self.OPHelper.restore_out_of_place(destination_path=self.netapp_folder_path,
                                               paths=[self.OPHelper.client_machine.join_path(
                                                   self.UNC_celerra_folder_path, file[0])
                                                   for file in self.OPHelper.test_file_list],
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               no_of_streams=10)
            time.sleep(240)
            self.verify_file_attributes(path=self.netapp_folder_path,
                                        valid_attributes=self.tcinputs.get('NetappRestoredStubAttributes',
                                                                           ['ARCHIVE', 'OFFLINE', 'SPARSEFILE']))
            self.verify_file_size_on_disk(path=self.netapp_folder_path,
                                          valid_size=self.tcinputs.get("NetappStubSize", 8192))
            self.verify_file_size(path=self.netapp_folder_path,
                                  valid_size=self.tcinputs.get("NetappStubSize", 1024 * 1024))
            self.OPHelper.recall(path=self.netapp_folder_path)
            self.verify_file_attributes(path=self.netapp_folder_path,
                                        valid_attributes=self.tcinputs.get('NetappRecalledStubAttributes',
                                                                           ['ARCHIVE', 'SPARSEFILE']))
            self.verify_modified_time(path=self.netapp_folder_path)

            self.log.info('Cross Platform stubs restore Celerra to Local, Dmnas, Netapp passed')

        except Exception as exp:
            self.log.error('Cross Platform stubs restore Celerra to Local, Dmnas, Netapp failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
