# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: 3DFS restore for Casandra support

Steps:
    1. Create test subclient (testSC) with test data
    2. trigger subclient full backup for testSc and wait for it to complete
    3. create 3DFS share (testsh) with uid and gid of root user
    4. mount 3DFS share testsh on restore client
    5. copy the data from 3DFS share to restore client and verify the data

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils
from FileSystem.FSUtils.tdfshelper import TDfsServerUtils
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing verification test for 3DFS restore for Casandra support"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "3DFS restore for Casandra support"
        self.tcinputs = {
            'NFSServer': None,
            'BackupClient': None,
            'RestoreClient': None,
            'StoragePolicy': None,
            'DataSize': None,
            'NumberOfFiles': None,
            'Num_LRU': None
        }
        self.subclient_props = []
        self.subclient_name = None
        self.bkp_client_machine = None
        self.content = None
        self.restore_client_machine = None
        self.restore_path = None
        self.mount_dir = None
        self.service_wait_time = 120

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")
        self.subclient_name = "testCasandra" + self.id

        self.log.info("Initializing machine class instance for backup machine %s" % self.tcinputs['BackupClient'])
        self.bkp_client_machine = Machine(self.tcinputs['BackupClient'], self.commcell)

        self.log.info("Initializing machine class instance for restore machine %s" % self.tcinputs['RestoreClient'])
        self.restore_client_machine = Machine(self.tcinputs['RestoreClient'], self.commcell)
        if 'unix' not in self.restore_client_machine.os_info.lower():
            raise Exception("non unix casandra restore client is not supported")

        self.entities = CVEntities(self.commcell)
        self.serverbase = CommonUtils(self.commcell)

        self.content = self.bkp_client_machine.join_path(self.bkp_client_machine.tmp_dir, "subclientcontent")
        self.log.info("subclient content directory %s" % self.content)
        self.log.info("creating content folder %s on client %s" % (self.content,
                                                                   self.tcinputs['BackupClient']))
        self.bkp_client_machine.create_directory(self.content, force_create=True)

        self.log.info("creating subclient content at %s" % self.content)
        for count in range(self.tcinputs['NumberOfFiles']):
            file_path = self.bkp_client_machine.join_path(self.content, "file"+str(count))
            size_in_bytes = self.tcinputs['DataSize'] * 1024 * 1024
            self.log.debug("creating test file %s with size %sMB size" % (file_path, self.tcinputs['DataSize']))
            self.bkp_client_machine.create_file(file_path, '', file_size=size_in_bytes)

        subclient_inputs = {
            'target':
                {
                    'client': self.tcinputs['BackupClient'],
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagePolicy': self.tcinputs['StoragePolicy'],
                    'backupset': "defaultBackupSet"
                },
            'subclient':
                {
                    'name': self.subclient_name,
                    'client_name': self.tcinputs['BackupClient'],
                    'description': "Automation - 3DFS support for Casandra restore",
                    'content': [self.content],
                    'force': True
                }
        }
        self.subclient_props = self.entities.create(subclient_inputs)
        self.serverbase.subclient_backup(self.subclient_props['subclient']['object'],
                                         backup_type="full")

        if self.tcinputs['Num_LRU'] is not None:
            self.log.info("updating nfs server registry with Num_LRU as %s" % self.tcinputs['Num_LRU'])
            self.log.info("Initializing machine class instance for machine %s" % self.tcinputs['NFSServer'])
            nfs_server_machine_ob = Machine(self.tcinputs['NFSServer'], self.commcell)
            nfs_server_machine_ob.create_registry("3Dfs", "DiskCacheLRUSize", self.tcinputs['Num_LRU'])
            nfs_server_client_obj = self.commcell.clients.get(self.tcinputs['NFSServer'])
            self.log.info("restarting CV services on nfs server %s" % self.tcinputs['NFSServer'])
            nfs_server_client_obj.restart_services()
            self.log.info("waiting %s seconds for 3dfs server to come up" % self.service_wait_time)
            time.sleep(self.service_wait_time)

    def run(self):
        """Main function for test case execution"""
        additional_params = {"subclientName": self.subclient_name,
                             "refresh_on_backup": "0",
                             "uid": "0",
                             "gid": "0",
                             "accessMask": "600"
                             }
        self.nfs_ser_obj = TDfsServerUtils(self, self.tcinputs['NFSServer'])
        self.log.info("creating 3dfs share with additional params %s" % additional_params)
        self.nfs_share_name = self.nfs_ser_obj.create_3dfs_share("defaultBackupSet",
                                                                 extra_option=additional_params,
                                                                 client_name=self.tcinputs['BackupClient'])
        self.log.info("3dfs share %s created successfully" % self.nfs_share_name)

        self.mount_dir = self.restore_client_machine.join_path(self.restore_client_machine.tmp_dir,
                                                               self.nfs_share_name)
        self.log.info("creating local mount directory %s" % self.mount_dir)

        self.restore_client_machine.create_directory(self.mount_dir, force_create=True)
        self.restore_client_machine.mount_nfs_share(self.mount_dir,
                                                    self.tcinputs['NFSServer'],
                                                    self.nfs_ser_obj.tdfs_machine_obj.os_sep + self.nfs_share_name)

        self.restore_path = self.restore_client_machine.join_path(self.restore_client_machine.tmp_dir,
                                                                  self.id+"restoreFolder")
        start_time = time.time()
        self.log.info("copying data from src:%s to dest:%s" % (self.mount_dir, self.restore_path))
        self.restore_client_machine.copy_folder(self.mount_dir, self.restore_path)
        end_time = time.time()
        self.log.info("time taken to copy share content of size %sMB is %s seconds" % (
            (self.tcinputs['DataSize'] * self.tcinputs['NumberOfFiles']), int(end_time-start_time)))

        source_checksums = self.bkp_client_machine.get_checksum_list(self.content)
        dest_checksums = self.restore_client_machine.get_checksum_list(self.restore_path)
        self.log.info("source checksum:%s, restore checksum:%s" % (source_checksums, dest_checksums))
        for count in range(len(source_checksums)):
            chksum_s, size_s, path_s = source_checksums[count].split()
            chksum_d, size_d, path_d = source_checksums[count].split()

            if chksum_s != chksum_d or size_s != size_d or path_d not in path_s:
                self.log.error("checksum for content and 3DFS restore didn't match")
                self.log.error("source checksum:%s, restore checksum:%s" % (source_checksums, dest_checksums))

        self.log.info("data validated successfully for 3DFS restore")

    def tear_down(self):
        try:
            self.nfs_ser_obj.delete_3dfs_share(self.nfs_share_name)
        except Exception as excp:
            self.log.error("delete 3dfs share %s failed with error %s" % (self.nfs_share_name, excp))
        self.entities.delete(self.subclient_props)
        self.bkp_client_machine.remove_directory(self.content)
        self.restore_client_machine.remove_directory(self.restore_path)
        self.log.info("unmounting directory %s" % self.mount_dir)
        self.restore_client_machine.unmount_path(self.mount_dir)
        self.restore_client_machine.remove_directory(self.mount_dir)

        self.log.info("removing DiskCacheLRUSize from 3dfs registry")
        self.nfs_ser_obj.tdfs_machine_obj.remove_registry("3Dfs", "DiskCacheLRUSize")
