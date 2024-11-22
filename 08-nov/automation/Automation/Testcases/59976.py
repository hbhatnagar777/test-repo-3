"""
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

Acceptance testcase for file system Add/Remove exclusions/exceptions

Sample input:
        "59976": {
          "ClientName": "vm1",
          "AgentName": "File System",
          "StoragePolicyName": "policy1",
          "TestPath": "C:\\testData",
          "RestorePath": "C:\\restoredTestData",
          "IsNetworkShareClient": None //Only required for network share client
          "DestinationClientName": "vm2", // Only required for network share client
          // as the machine to restore data on
        }
"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """
    Class used to automation acceptance testcase for filters and exceptions
    for all types of file system clients
    Initially this TC supports NAS, CIFS, and Windows and Unix
    """
    _INSTANCE_NAME = 'defaultInstanceName'
    _BACKUPSET_NAME = 'Backupset_59976'
    def __init__(self):
        super(TestCase, self).__init__()
        self.client_name = None
        self.name = "file system Add/Remove exclusions/exceptions at file level"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "StoragePolicyName": None,
            "TestPath": None,
            "RestorePath": None
            # "IsNetworkShareClient": None,
        }
        self.is_client_network_share = None
        self.data_path = ''
        self.exceptions = []
        self.exclusions = []

        self.utils = None
        self.fs_helper = None

        self.instance = None
        self.backupset = None
        self.subclient = None
        self.storage_policy = None
        self.client_machine = None
        self.machine = None
        self.restore_path = None
        self.hostname = None
        self.test_path = None
        self.config = None

    @property
    def subclient_name(self):
        """Returns the subclient name"""
        return f"Subclient_TC_{self.id}"

    def get_restore_path(self):
        """Gets the restored data path"""
        if self.is_client_network_share:
            if self.client_machine.os_info.lower() == 'windows':
                return self.client_machine.join_path(self.restore_path, f"UNC-NT_{self.hostname}")
            # TODO: Determine path for unix
            return self.restore_path
        return self.restore_path

    def setup(self):
        """Setup the testcase"""
        self.fs_helper = FSHelper(self)
        self.instance = self.agent.instances.get(self._INSTANCE_NAME)
        self.fs_helper.create_backupset(self._BACKUPSET_NAME, delete=True)
        self.is_client_network_share = bool(self.tcinputs.get('IsNetworkShareClient', False))

        self.utils = TestCaseUtils(self)
        self.config = get_config()
        self.fs_helper.populate_tc_inputs(self, mandatory=False)

    def get_filter_path(self, filter_type):
        """ Gets the file paths set for the subclient for exceptions, exclusions or backup paths
                Args:
                    filter_type (str) : Entity to get it's path
                            'includePath'  for Exceptions
                            'excludePath'  for Exclusions
                            'path'         for Content
                Returns :
                     filter_paths : path of the entity
        """
        self.log.info("%s Gets the path of a selected filter of a subclient %s", "*" * 8, "*" * 8)
        self.subclient.refresh()
        sub_cont_obj = self.subclient._content
        keys_list = []
        for dic in sub_cont_obj:
            dic_keys = list(dic.keys())
            keys_list.append(dic_keys)
        keys_list = [key for lst in keys_list for key in lst]
        filter_paths = []
        for idx, key in enumerate(keys_list):
            if keys_list[idx] == filter_type:
                filter_paths.append(sub_cont_obj[idx][key])
        return filter_paths

    def define_content_and_filters(self):
        """ Define the subclient content, exclusions and exceptions """
        self.log.info("Creating test data at %s on machine %s", self.test_path, self.client_machine.machine_name)
        self.fs_helper.generate_testdata(['.html', '.css'], self.test_path, 4)

        if self.is_client_network_share:
            if self.client_machine.os_info.lower() == 'windows':
                share_name = self.test_path.split('\\')[1]
                try:
                    self.client_machine.unshare_directory(share_name)
                except Exception:
                    pass
                self.client_machine.share_directory(share_name, self.test_path)
            else:
                pass
                # TODO: Add a way to share folder to NFS server

    def add_subclient(self):
        """Deletes the subclient and backupset if it already exists and creates a new one"""
        files_list = self.client_machine.get_files_in_path(self.test_path)
        self.exclusions = [file for file in files_list if file.endswith(".html")]
        for index, exclusion in enumerate(self.exclusions):
            if index % 3 == 0:
                # Every third exclusion is considered as an exception
                self.exceptions.append(exclusion)

        if self.client_machine.os_info.lower() == 'windows':
            path = self.test_path.split('\\')
            self.data_path = self.test_path
            if self.is_client_network_share:
                self.data_path = f"\\\\{self.client_machine.machine_name}\\" + '\\'.join(path[1:])
                replace_drive_letter = lambda x: f"\\\\{self.client_machine.machine_name}" + x.replace(path[0], '')
                self.exclusions = [replace_drive_letter(exclusion) for exclusion in self.exclusions]
                self.exceptions = [replace_drive_letter(exception) for exception in self.exceptions]
        else:
            path = self.test_path.split('//')[1:]
            self.data_path = "/"
        impersonate_user = ({"username": self.config.Network.username, "password": self.config.Network.password}
                            if self.is_client_network_share else None)
        self.fs_helper.create_subclient(self.subclient_name,
                                        self.storage_policy,
                                        [self.data_path],
                                        filter_content=self.exclusions,
                                        exception_content=self.exceptions,
                                        delete=True,
                                        impersonate_user=impersonate_user)

    def backup(self ,backup_level = None):
        """Perform a full backup of the subclient"""
        self.log.info("Initiating a  backup for the subclient: %s", self.subclient_name)
        if backup_level == 'Incremental':
            self.fs_helper.run_backup(backup_level="Incremental")
        elif backup_level == 'Synthetic_full':
            self.fs_helper.run_backup(backup_level="Synthetic_full")
        else:
            self.fs_helper.run_backup(backup_level="Full")

    def restore(self):
        """Performs a restore of the data of the subclient"""
        if self.is_client_network_share:
            machine = Machine(self.tcinputs['DestinationClientName'], self.commcell)
        else:
            machine = self.client_machine
        machine.create_directory(self.restore_path, force_create=True)
        if machine.os_info.lower() == "windows":
            des_path = self.restore_path.replace("/", "\\")
        else:
            des_path = self.restore_path[1:]
        self.fs_helper.restore_out_of_place(des_path,
                                            [self.data_path],
                                            client=self.tcinputs['DestinationClientName'],
                                            impersonate_user=self.config.Network.username,
                                            impersonate_password=self.config.Network.password)

    def verify_restore(self):
        """Verifies that the restore was successfully done"""
        restore_path = self.get_restore_path()
        self.fs_helper.validate_backup(dest_client=self.tcinputs.get('DestinationClientName'),
                                       content_paths=[self.test_path],
                                       restore_path=restore_path,
                                       add_exclusions=self.exclusions,
                                       exceptions_list=self.exceptions)

    def edit_filters(self):
        """Edit the filters after performing the initial backup and restore"""
        self.subclient = self.backupset.subclients.get(self.subclient_name)
        path1 = self.client_machine.join_path(self.test_path, 'newfile1.html')
        path2 = self.client_machine.join_path(self.test_path, 'newfile2.html')
        self.client_machine.create_file(path1, 'New file is added after full backup')
        self.client_machine.create_file(path2, 'New file is added after incremental backup')

        if self.is_client_network_share:
            path = self.test_path.split('\\')
            replace_drive_letter = lambda x: f"\\\\{self.client_machine.machine_name}" + x.replace(path[0], '')
            path1 = replace_drive_letter(path1)
            path2 = replace_drive_letter(path2)

        self.exclusions.append(path1)
        self.exceptions.append(path2)
        self.fs_helper.update_subclient(filter_content=self.exclusions, exception_content=self.exceptions)

    def remove_filters(self):
        """Remove filters after performing the initial backup and restore"""
        self.exception_files_list = []
        self.exclusion_files_list = []
        self.fs_helper.update_subclient(filter_content=self.exception_files_list,
                                        exception_content=self.exclusion_files_list)


    def run(self):
        """Run the testcase by performing 2 backup and restores"""
        try:
            self.define_content_and_filters()
            if self.is_client_network_share == False or self.is_client_network_share is None:
                self.tcinputs['DestinationClientName']= self.client_name
            self.add_subclient()
            self.backup()
            self.restore()
            self.verify_restore()
            self.edit_filters()
            self.backup(backup_level='Incremental')
            self.restore()
            self.verify_restore()
            self.backup(backup_level='Synthetic_full')
            self.restore()
            self.verify_restore()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
