# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: verify custom parameters added for Cassandra API are honored

Steps:
    1. Create test subclient (testSC) with test data
    2. trigger subclient full backup for testSc and wait for it to complete
    3. create user0 and user1 on linux restore client
    4. create 3DFS share (testsh) with uid and gid of user0
    5. mount 3DFS share testsh on restore client
    6. verify testsh share access for read and write with user0 and user1
       user0 access should be allowed and user1 access should be denied

"""
import re

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils
from FileSystem.FSUtils.tdfshelper import TDfsServerUtils
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing verification test for 3DFS custom parameters for Casandra support"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "verify custom parameters added for Cassandra API are honored"
        self.tcinputs = {
            'NFSServer': None,
            'BackupClient': None,
            'RestoreClient': None,
            'StoragePolicy': None
        }

        self.subclient_props = []
        self.subclient_name = None
        self.bkp_client_machine = None
        self.content = None
        self.entities = None
        self.serverbase = None
        self.user_string = None
        self.default_password = "#####"
        self.default_encrypted_password = ('#####')
        self.access_mask = "640:640"
        self.mount_dir = None
        self.users_list = []
        self.restore_client_machine = None
        self.nfs_share_name = None
        self.nfs_ser_obj = None

    def setup(self):
        """ Setup function of this test case """
        self.subclient_name = "testCasandra" + self.id
        self.user_string = "user" + self.id
        self.client_name = self.tcinputs['BackupClient']

        self.log.info("executing testcase")
        self.log.info("Initializing machine class instance for restore machine %s" % self.tcinputs['RestoreClient'])
        self.restore_client_machine = Machine(self.tcinputs['RestoreClient'], self.commcell)
        if self.restore_client_machine.os_info.lower() == 'windows':
            self.log.error("windows restore client %s not supported as casandra subclient" %
                           self.tcinputs['RestoreClient'])
            return

        self.entities = CVEntities(self.commcell)
        self.serverbase = CommonUtils(self.commcell)

        subclient_inputs = {
            'target':
                {
                    'client': self.tcinputs['BackupClient'],
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'StoragePolicy': self.tcinputs['StoragePolicy'],
                    'backupset': "defaultBackupSet"
                },
            'subclient':
                {
                    'name': self.subclient_name,
                    'client_name': self.tcinputs['BackupClient'],
                    'description': "Automation - 3DFS support for Casandra restore",
                    'size': 10,
                    'force': True
                }
        }
        self.subclient_props = self.entities.create(subclient_inputs)
        self.serverbase.subclient_backup(self.subclient_props['subclient']['object'],
                                         backup_type="full")

    def run(self):
        """Main function for test case execution"""

        # create users on the restore client machine
        self.users_list = [(self.user_string + str(i)) for i in range(2)]
        self.log.info("creating required users to test share access")
        for user in self.users_list:
            self.restore_client_machine.add_user(user, self.default_encrypted_password)

        # get the uid and gid for the first user which will be used in creating 3DFS share
        pattern = r"uid=(\d+)\((\w+)\) gid=(\d+)"
        cmd = "/usr/bin/id " + self.users_list[0]
        self.log.debug("executing %s command to get uid and gid for user %s" % (cmd, self.users_list[0]))
        output = self.restore_client_machine.execute_command(cmd)
        self.log.debug("output for id command %s" % output.output)
        uid, _, gid = re.findall(pattern, output.output)[0]
        self.log.info("uid:%s, gid:%s for user %s" % (uid, gid, self.users_list[0]))

        # create 3DFS share with uid, gid and accessmask in additional params
        self.nfs_ser_obj = TDfsServerUtils(self, self.tcinputs['NFSServer'])
        additional_params = {"subclientName": self.subclient_name,
                             "refresh_on_backup": "0",
                             "uid": uid,
                             "gid": gid,
                             "accessMask": self.access_mask}
        self.log.info("creating 3dfs share with additional params %s" % additional_params)
        self.nfs_share_name = self.nfs_ser_obj.create_3dfs_share("defaultBackupSet",
                                                                 extra_option=additional_params,
                                                                 client_name=self.tcinputs['BackupClient'])

        self.mount_dir = self.restore_client_machine.join_path(self.restore_client_machine.tmp_dir,
                                                               self.nfs_share_name)
        self.log.info("creating local mount directory %s" % self.mount_dir)
        self.restore_client_machine.create_directory(self.mount_dir, force_create=True)

        self.log.info("mounting share %s on local path %s" % (self.nfs_share_name, self.mount_dir))
        # mount 3DFS share and access the data
        self.restore_client_machine.mount_nfs_share(self.mount_dir,
                                                    self.tcinputs['NFSServer'],
                                                    self.nfs_ser_obj.tdfs_machine_obj.os_sep + self.nfs_share_name)

        file_path = self.restore_client_machine.join_path(self.mount_dir, "testfile")
        self.log.info("create machine instance for user session %s" % self.users_list[0])
        usr0_machine_obj = Machine(self.tcinputs['RestoreClient'], username=self.users_list[0],
                                   password=self.default_password)
        # verify allow read permission
        usr0_machine_obj.scan_directory(self.mount_dir)
        self.log.info("read access for user %s is successful on 3dfs share" % self.users_list[0])

        # verify allow write permission
        usr0_machine_obj.create_file(file_path, content="CVadded")
        self.log.info("write access for user %s is successful on 3dfs share" % self.users_list[0])

        self.log.info("create machine instance for user session %s" % self.users_list[1])
        usr1_machine_obj = Machine(self.tcinputs['RestoreClient'], username=self.users_list[1],
                                   password=self.default_password)

        # verify deny read permission
        exception = False
        try:
            usr1_machine_obj.scan_directory(self.mount_dir)
        except Exception as excp:
            exception = True
            self.log.info("read access denied as expected. exception:%s" % excp)
        if not exception:
            self.log.error("read access granted incorrectly to user %s" % self.users_list[1])

        # verify deny write permission
        exception = False
        try:
            usr1_machine_obj.create_file(file_path, content="CVadded")
        except Exception as excp:
            exception = True
            self.log.info("write access denied as expected. exception:%s" % excp)
        if not exception:
            self.log.error("write access granted incorrectly to user %s" % self.users_list[1])

    def tear_down(self):
        try:
            self.log.info("deleting 3dfs share %s" % self.nfs_share_name)
            self.nfs_ser_obj.delete_3dfs_share(self.nfs_share_name)
        except Exception as excp:
            self.log.error("delete 3dfs share %s failed with error %s" % (self.nfs_share_name, excp))

        self.entities.delete(self.subclient_props)

        if self.restore_client_machine.check_directory_exists(self.mount_dir):
            self.log.info("unmounting the share on path %s" % self.mount_dir)
            self.restore_client_machine.unmount_path(self.mount_dir)

            self.log.info("removing mount directory %s" % self.mount_dir)
            self.restore_client_machine.remove_directory(self.mount_dir)

        self.restore_client_machine.delete_users(self.users_list)