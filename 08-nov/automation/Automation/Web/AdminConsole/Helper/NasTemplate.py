# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This Module provides methods to run different template for NAS Operations

Class : NASTemplate

Functions:
    cleanup()           : To cleanup entities created during execution

    create_entities()   : To create required entities like Plans, Subclient etc

    verify_backup()     : To backup nas client

    verify_restore()     : To restore nas client

    get_test_data_path()  : Getting test data path

    add_test_data()      : Add test data for nas subclient

    get_path_from_content() : Add path from content

    validate_restored_content() : to validate restore data

    compare_data()   : to compare backed up data and restored data

    nastemplate()     : Template for NAS Test Cases

"""
import random
import string
from datetime import date
from cvpysdk.policies.storage_policies import StoragePolicies
from cvpysdk.agent import Agent
from cvpysdk.client import Client
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.database_helper import get_csdb
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
import time
import enum
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, Overview, FsAgentAdvanceOptions
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview
import os


class NASTemplate(object):
    """ NasTemplate Class for NAS Cases"""
    test_step = TestStep()

    def __init__(self, testcase, admin_console):

        """Initializing the Test case file"""
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.tcinputs = testcase.tcinputs
        self.commcell = testcase.commcell
        self.testcase = testcase
        self.__driver = admin_console.driver
        self.plan_obj = Plans(self.__admin_console)
        self.fs_servers = FileServers(self.__admin_console)
        self.fs_subclient = FsSubclient(self.__admin_console)
        self.fs_scdetails = FsSubclientDetails(self.__admin_console)
        self.policies = StoragePolicies(self.commcell)
        self.log = testcase.log
        self._csdb = get_csdb()
        self._storagepool_name = {'pri_storage': self.tcinputs['StoragePoolName']}
        self.string = self.tcinputs['ArrayVendor'].replace("/", "").replace(" ", "").replace("(", "").replace(")", "")
        self._plan_name = "CC_AutoPlan_{0}_{1}".format(self.string, self.testcase.id)
        self._subclient_name = "CC_AutoSC_{0}_{1}".format(self.string, self.testcase.id)
        self.server_name = self.tcinputs['ServerName']
        self._backupset_name = 'defaultBackupSet'
        self.out_restore_path = None
        self.local_machine = Machine()
        self.is_cluster = self.tcinputs.get('IsCluster', False)
        self.subclient_content = self.tcinputs["SubclientContent"].split(',')
        self.domainUser = self.tcinputs["domainUsername"]
        self.domainPassword = self.tcinputs["domainPassword"]
        self.agent_name = self.tcinputs['Agent']
        self.dest_filer = self.tcinputs["DestinationFiler"]
        self.filer_restore_path = self.tcinputs["FilerRestoreLocation"]
        self.windows_client = self.tcinputs['WindowsDestinationClient']
        self.unix_client = self.tcinputs['UnixDestinationClient']
        self.access_node = self.tcinputs.get('AccessNode', None)
        self.array_vendor = self.tcinputs.get('ArrayVendor', None)
        self.array_name = self.tcinputs['ArrayName']
        self.nfsmountpoint = '/nfsautomount'
        self.arrays = Arrays(self.__admin_console)
        self.nas_helper = None
        self.client_obj = None
        self.agent_obj = None
        self.nas_client = None
        if self.agent_name.lower()=='ndmp':
            self.nas_helper = NASHelper()
        self.full = Backup.BackupType.FULL
        self.incr = Backup.BackupType.INCR
        self.diff = Backup.BackupType.DIFF
        self.vendor = None
        self.ndmp_streaming_not_nre = ["Huawei"]
        self.ndmp_snap_not_nre = ["Dell EMC VNX/Celerra", "Huawei", "Dell EMC Unity"]
        if self.array_vendor:
            class Vendor(enum.Enum):
                DELL_EMC_ISILON = "Dell EMC Isilon"
                DELL_EMC_UNITY = "Dell EMC Unity"
                DELL_EMC_VNXCELERRA = "Dell EMC VNX/Celerra"
                HITACHI_NAS = "Hitachi NAS"
                HUAWEI = "Huawei"
                NETAPP = "NetApp"

            self.array_user = self.tcinputs.get('ArrayUser', None)
            self.array_pass = self.tcinputs.get('ArrayPass', None)
            self.array_host = self.tcinputs.get('ArrayControlHost', None)
            for i in Vendor:
                if i.value == self.tcinputs['ArrayVendor']:
                    self.vendor = i
                    break
        self.get_sp = """SELECT DISTINCT AG.name FROM archGroup AG JOIN archGroupCopy AGC ON AG.id = AGC.archGroupId
                                                            WHERE AG.name LIKE '{a}'"""
        windows_client_obj = self.commcell.clients.get(self.windows_client)
        self.windows_restore_machine = Machine(windows_client_obj)
        unix_client_obj = self.commcell.clients.get(self.unix_client)
        self.unix_restore_machine = Machine(unix_client_obj)
        self.options_selector = OptionsSelector(self.commcell)
        self.enable_snap = testcase.enable_snap
        self.engine_name = self.tcinputs.get('SnapEngine', None)
        self.__admin_console.load_properties(self)
        self.test_data_paths = []
        self.rfs_servers = FileServers(self.__admin_console)
        self.rfs_subclient = Subclient(self.__admin_console)
        self.array_access_nodes = self.tcinputs.get('ArrayAccessNodes', None)
        self.rtable= Rtable(self.__admin_console)
        self.rfs_sdetails_overview = SubclientOverview(self.__admin_console)
        self.backupjobid = """select childJobId from JMJobWF where processedjobid={a}"""
        self.primary = "Primary"
        self.rfs_adv = FsAgentAdvanceOptions(self.__admin_console)

    @property
    def storagepool_name(self):
        """Return Storage Pool Name"""
        return self._storagepool_name

    @storagepool_name.setter
    def storagepool_name(self, value):
        """Set Storage Pool name"""
        self._storagepool_name = value

    @property
    def plan_name(self):
        """Return Plan Name"""
        return self._plan_name

    @plan_name.setter
    def plan_name(self, value):
        """Set Plan name"""
        self._plan_name = value

    @property
    def subclient_name(self):
        """Return Subclient Name"""
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """Set Subclient Name"""
        self._subclient_name = value

    def wait_for_job_completion(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            if self.rfs_servers.is_client_exists(self.server_name):
                self.rfs_servers.access_server(self.server_name)
                self.__admin_console.wait_for_completion()
                if self.rfs_servers.access_agent(self.agent_name):
                    self.__admin_console.access_tab("Subclients")
                    if self.rfs_subclient.is_subclient_exists(self.subclient_name):
                        self.rfs_subclient.delete_subclient(backupset_name=self._backupset_name,
                                                            subclient_name=self.subclient_name)
                        if self.rfs_subclient.is_subclient_exists(self.subclient_name):
                            raise Exception("Subclient Deletion Failed. Hence failing the TC")
                self.__admin_console.wait_for_completion()
                self.__navigator.navigate_to_file_servers()
                self.__admin_console.access_tab("File servers")
                self.rfs_servers.access_server(self.server_name)
                self.__admin_console.wait_for_completion()
                self.rfs_servers.release_license()
                self.__admin_console.wait_for_completion()
                self.__navigator.navigate_to_arrays()
                self.arrays.action_list_snaps(self.array_name)
                delete_snaps_job = self.arrays.delete_all_snapshots()
                if delete_snaps_job:
                    self.wait_for_job_completion(delete_snaps_job)
                self.__navigator.navigate_to_arrays()
                self.arrays.action_delete_array(self.array_name)
                self.__navigator.navigate_to_file_servers()
                self.__admin_console.access_tab("File servers")
                self.rtable.reload_data()
                self.rfs_servers.delete_client(server_name=self.server_name)
                self.__admin_console.wait_for_completion()
                if self.rfs_servers.is_client_exists(self.server_name):
                    raise Exception("Client Deletion Failed. Hence failing the TC")
            self.__navigator.navigate_to_plan()
            if self.plan_obj.is_plan_exists(self.plan_name):
                self.plan_obj.delete_plan(self.plan_name)
                self.__admin_console.wait_for_completion()
                self.log.info(f"Plan: {self.plan_name} deleted successfully.")
                if self.plan_obj.is_plan_exists(self.plan_name):
                    self.log.info(f"Plan still exists. Please check the associations and cleanup manually.")

            self.policies.refresh()
            sp = self.execute_query(self.get_sp, {'a': self.plan_name})
            if not (sp in [[[]], [['']], ['']]):
                self.log.info(f"Deleting storage policy: {sp}")
                self.policies.delete(self.plan_name)
            if self.agent_name.lower() == 'nfs':
                if self.unix_restore_machine.is_path_mounted(self.nfsmountpoint):
                    self.log.info(f"Unmounting NFS path: {self.nfsmountpoint}")
                    self.unix_restore_machine.unmount_path(self.nfsmountpoint)
                if self.unix_restore_machine.check_directory_exists(self.nfsmountpoint):
                    self.unix_restore_machine.remove_directory(self.nfsmountpoint)

        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup entities failed with error : {exp}')

    @test_step
    def create_entities(self):
        """To create required entities for test case"""
        try:
            #To create a new plan
            self.log.info("Adding a new plan: %s", self.plan_name)
            self.__navigator.navigate_to_plan()
            self.plan_obj.create_server_plan(plan_name=self.plan_name,
                                                 storage=self.storagepool_name)
            self.log.info("successfully created plan: %s", self.plan_name)
            # To add a new client
            self.log.info("Adding a new client %s", self.server_name)
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            cifsk = None
            nfsk = None
            ndmpk = None
            array_details = None
            cifs_sub = None
            if self.agent_name.lower() == 'ndmp':
                ndmpuser = self.tcinputs['ndmpUser']
                ndmppass = self.tcinputs['ndmpPassword']
                ndmpk = {'impersonate_user': {'username': ndmpuser, 'password': ndmppass},
                'access_nodes': self.access_node.split(',') if self.access_node else None,
                         'credential_manager': self.tcinputs.get('CredentialManager', False),
                         'credential_manager_name': self.tcinputs.get('CredentialManagerName', None),
                         'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
            elif self.agent_name.lower() == 'cifs':
                cifsuser = self.tcinputs['CIFSShareUser']
                cifspass = self.tcinputs['CIFSSharePassword']
                cifsk = {'impersonate_user': {'username': cifsuser, 'password': cifspass},
                         'access_nodes': self.access_node.split(',') if self.access_node else None,
                         'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
                cifs_sub = {'username': cifsuser, 'password': cifspass}
            else:
                nfsk = {'access_nodes': self.access_node.split(',') if self.access_node else None,
                        'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
            if self.array_user:
                array_details = {'array_name': self.array_name, 'username': self.array_user,
                                 'password': self.array_pass, 'control_host': self.array_host,
                                 'access_nodes': self.array_access_nodes}
            self.rfs_servers.add_nas_client(name=self.server_name,
                                           host_name=self.server_name,
                                           plan=self.plan_name,
                                           vendor=self.vendor,
                                           array_details=array_details,
                                           cifs=cifsk,
                                           nfs=nfsk,
                                           ndmp=ndmpk
                                           )
            self.log.info("Created a new nas server %s", self.server_name)
            # To add a new Subclient
            self.log.info("Adding a new subclient %s", self.subclient_name)
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rtable.reload_data()
            self.rfs_servers.access_server(self.server_name)
            self.rfs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            self.rfs_subclient.add_subclient(subclient_name=self.subclient_name,
                                                contentpaths=self.subclient_content,
                                                plan_name=self.plan_name,
                                                impersonate_user=cifs_sub,
                                                is_nas_subclient=True
                                                )
            self.log.info("Created a new subclient %s", self.subclient_name)
            if self.enable_snap:
                self.__navigator.navigate_to_file_servers()
                self.__admin_console.access_tab("File servers")
                self.rfs_servers.enable_snap(self.server_name)
                self.rfs_servers.access_agent(self.agent_name)
                self.__admin_console.access_tab("Subclients")
                self.rfs_subclient.access_subclient(backupset_name=self._backupset_name,
                                                    subclient_name=self.subclient_name)
                self.rfs_subclient.enable_snapshot_engine(enable_snapshot=True,
                                                         engine_name=self.engine_name)

            if self.agent_name.lower() == 'ndmp':
                self.commcell.refresh()
                self.client_obj=Client(self.commcell, self.server_name)
                self.agent_obj=Agent(self.client_obj, self.agent_name)
                self.nas_client = self.nas_helper.get_nas_client(self.client_obj, self.agent_obj,
                                                                 is_cluster=self.is_cluster)
        except Exception as exp:
            raise CVTestStepFailure(f'Create entities failed with error : {exp}')

    @test_step
    def verify_backup(self, backup_type):
        """Verify Backup"""
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rfs_servers.access_server(self.server_name)
            self.rfs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            jobid = self.rfs_subclient.backup_subclient(backupset_name=self._backupset_name,
                                                        subclient_name=self.subclient_name,
                                                        backup_type=backup_type)
            job_status = self.wait_for_job_completion(jobid)
            if not job_status:
                exp = "{0} Job ID {1} didn't succeed".format(backup_type, jobid)
                raise Exception(exp)
            return jobid
        except Exception as exp:
            raise CVTestStepFailure(f'Backup operation failed : {exp}')

    @test_step
    def verify_restore(self, dest_client=None, restore_path=None, storage_copy_name=None):
        """Restores a NAS Subclient from subclient level and verifies restore job completion

        Args:
            restore_path:str: restore path of the destination  (optional)
            dest_client: str: destination client       (optional)
            storage_copy_name: str: Storage copy name  (optional)
        """
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.server_name)
            self.fs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            selected_content = []
            cifs, impersonate_user, ndmp, nfs = None, None, None, None
            for path in self.subclient_content:
                if '\\' in path:
                    selected_content.append(path)
                    cifs = True
                    cifsuser = self.tcinputs['CIFSShareUser']
                    cifspass = self.tcinputs['CIFSSharePassword']
                    # restore_path is empty then we impersonate_user
                    if restore_path is None:
                        impersonate_user = {'username': cifsuser, 'password': cifspass}
                    else:
                        # we don't pass impersonate creds if restore path is windows
                        if ":\\" not in restore_path:
                            impersonate_user = {'username': cifsuser, 'password': cifspass}
                    dest_client = self.tcinputs['AccessNode']
                else:
                    temp_path = path.strip('/').split('/')
                    if len(temp_path) > 1:
                        selected_content.append('/'.join(temp_path))
                    else:
                        selected_content.append(temp_path[0])

            if self.agent_name.lower() == 'nfs':
                dest_client = self.tcinputs['AccessNode']
                nfs = True
            if self.agent_name.lower() == 'ndmp':
                ndmp = True
            rjobid = self.rfs_subclient.restore_subclient(backupset_name="defaultBackupSet",
                                                         subclient_name=self.subclient_name,
                                                         dest_client=dest_client,
                                                         destination_path=restore_path,
                                                         selected_files=selected_content,
                                                         impersonate_user=impersonate_user,
                                                         storage_copy_name=storage_copy_name,
                                                         cifs=cifs,
                                                         ndmp=ndmp,
                                                         nfs=nfs)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'Restore operation failed : {exp}')

    @test_step
    def restore_from_client(self, dest_client=None, restore_path=None):
        """Restores a NAS Subclient from Client level and verifies restore job completion

        Args:
            restore_path:str: restore path of the destination  (optional)
            dest_client: str: destination client       (optional)

        """
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            selected_content = []
            ndmp = None
            if self.agent_name.lower() == 'ndmp':
                ndmp = True
            for path in self.subclient_content:
                if '\\' in path:
                    selected_content.append(path.strip('\\'))
                else:
                    temp_path = path.strip('/').split('/')
                    if len(temp_path) > 1:
                        selected_content.append('/'.join(temp_path))
                    else:
                        selected_content.append(temp_path[0])
            rjobid = self.rfs_servers.restore_subclient(client_name=self.server_name,
                                                       dest_client=dest_client,
                                                       restore_path=restore_path,
                                                       selected_files=selected_content,
                                                       ndmp=ndmp)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'Restore operation failed : {exp}')

    @test_step
    def restore_from_recovery_point(self, recovery_time, dest_client=None, restore_path=None):
        """Restores from a recovery point and verifies restore job completion

        Args:
            recovery_time:dict: the backup date format ex: { year: 2000, month : "March", date : "21" }
            restore_path:str: restore path of the destination  (optional)
            dest_client: str: destination client       (optional)

        """
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rfs_servers.access_server(self.tcinputs['ServerName'])
            self.rfs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            self.rfs_subclient.access_subclient(backupset_name=self._backupset_name, subclient_name=self.subclient_name)
            selected_content = []
            ndmp=None
            if self.agent_name.lower() == 'ndmp':
                ndmp=True
            for path in self.subclient_content:
                if '\\' in path:
                    selected_content.append(path.strip('\\'))
                else:
                    temp_path = path.strip('/').split('/')
                    if len(temp_path) > 1:
                        selected_content.append('/'.join(temp_path))
                    else:
                        selected_content.append(temp_path[0])
            rjobid = self.rfs_sdetails_overview.restore_from_calender(calender=recovery_time,
                                                                     dest_client=dest_client,
                                                                     rest_path=restore_path,
                                                                     selected_files=selected_content,
                                                                     ndmp=ndmp)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'Restore operation failed : {exp}')

    @test_step
    def restore_by_job(self, jobid, dest_client=None, restore_path=None):
        """Restores a NAS Subclient from subclient level and verifies restore job completion

        Args:
            restore_path:str: restore path of the destination  (optional)
            dest_client: str: destination client       (optional)

        """
        try:
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rfs_servers.access_server(self.tcinputs['ServerName'])
            self.rfs_servers.access_agent(self.agent_name)
            selected_content = []
            ndmp=None
            if self.agent_name.lower() == 'ndmp':
                ndmp=True
            for path in self.subclient_content:
                if '\\' in path:
                    selected_content.append(path.strip('\\'))
                else:
                    temp_path = path.strip('/').split('/')
                    if len(temp_path) > 1:
                        selected_content.append('/'.join(temp_path))
                    else:
                        selected_content.append(temp_path[0])
            rjobid = self.rfs_subclient.restore_subclient_by_job(backupset_name="defaultBackupSet",
                                                                subclient_name=self.subclient_name,
                                                                job_id=jobid,
                                                                dest_client=dest_client,
                                                                restore_path=restore_path,
                                                                selected_files=selected_content,
                                                                ndmp=ndmp)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'Restore operation failed : {exp}')

    def get_test_data_path(self, size, local_machine):
        """Returns the test data path on this machine

            Args:
                size            (int)       --  size of test data that is to be generated

            Returns:
                str     -   path where test data is generated

            Raises:
                Exception:
                    if failed to generate test data on controller machine
        """
        drives_dict = local_machine.get_storage_details()
        if local_machine.os_info == "WINDOWS":
            for drive in drives_dict.keys():
                if not isinstance(drives_dict[drive], dict):
                    continue

                if float(drives_dict[drive]['available']) >= size:
                    return drive + ":\\" + ''.join(random.choices(string.ascii_uppercase, k=7))
        elif local_machine.os_info == "UNIX":
            if float(drives_dict['available']) >= size:
                return "/" + ''.join(random.choices(string.ascii_uppercase, k=7))

        raise Exception("Failed to get test data path")

    @test_step
    def add_test_data(self):
        """
                Adds test under every path in subclient content

                Returns:
                    list    --  paths where test data is generated
        """
        list_paths = {}
        local_machine = self.local_machine
        if self.agent_name.lower() == "nfs":
            local_machine = self.unix_restore_machine
        for item in self.subclient_content:
            if self.agent_name.lower() == 'ndmp':
                path, vol = self.nas_client.get_path_from_content(item)
            else:
                path, vol = self.get_path_from_content(self.server_name, item)
            test_data_size = 10
            test_data_path = self.get_test_data_path(test_data_size, local_machine)
            test_data_folder = test_data_path.split(local_machine.os_sep)[-1]
            local_machine.generate_test_data(test_data_path, file_size=test_data_size)

            self.log.info("Generated Test Data at path: " + test_data_path)
            if self.agent_name.lower() == "nfs":
                mountpoint = self.nfsmountpoint
                temp = item.split(":")
                self.log.info(f"NFS Mount: {temp}")
                server = temp[0]
                share = temp[1]
                if not local_machine.is_path_mounted(mountpoint):
                    local_machine.mount_nfs_share(mountpoint, server, share, cleanup=False, version=None)
                self.log.info("Folder %s will be copied to %s", test_data_path, mountpoint)
                local_machine.copy_folder(test_data_path, mountpoint, '-f')
                path=server+share
            else:
                local_machine.copy_folder_to_network_share(test_data_path, path,
                                                       self.domainUser, self.domainPassword)
            self.log.info("Copying test data to: " + path)
            list_paths[path + local_machine.os_sep + test_data_folder] = local_machine.get_folder_hash(test_data_path)
            self.log.info(f"Removing locally generated test data {test_data_path}")
            local_machine.remove_directory(test_data_path)

        return list_paths

    def get_path_from_content(self, server_name, content):
        """Returns the Share path and volume name

            Args:
                server_name (str)  -- server name
                content     (str)   --  volume path from the subclient content

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self.agent_name.upper() == 'NDMP':

            vol_name = content.replace("/", "", 1)
            volume_name = vol_name.replace("/", "\\")
            return r"\\{0}\{1}".format(server_name, volume_name), content.split('/')[-1]
        if '/' in content:
            content = content.strip("/").split("/")
        else:
            content = content.strip("\\").split("\\")
        volume_name = "\\".join(content[1:])
        vserver_ip = server_name
        return r"\\{0}\{1}".format(vserver_ip, volume_name), volume_name

    def get_ndmp_path_from_content(self, content):
        """Returns the Share path and volume name

            Args:
                server_name (str)  -- server name
                content     (str)   --  volume path from the subclient content

            Returns:
                (str, str)  -   ndmp share path and path of the volume

        """
        if not self.enable_snap and self.vendor.value == 'Huawei':
            vol = self.subclient_content[0].replace('/', '\\').strip('\\')
            test_folder = content.split('\\')[-1]
            return content, '\\'.join([vol, test_folder])
        return content, '\\'.join(content.split('\\')[3:])

    @test_step
    def validate_filer_restored_content(self, restored_filer_name, filer_restore_location):
        """Validates the restored content
                Args:
                    restored_filer_name: str: name of the filer
                    filer_restore_location: str: restore path on the filer
            Raises:
                Exception:
                    if failed to validate restored content

        """
        for content in self.test_data_paths.keys():
            src_path, volume_name = self.get_path_from_content(self.tcinputs["ServerName"], content)

            dest_path, restore_vol = self.get_path_from_content(restored_filer_name, filer_restore_location)
            dest_restore_path = dest_path + "\\" + volume_name

            if self.agent_name.lower()=='ndmp':
                src_path, volume_name = self.get_ndmp_path_from_content(content)
                dest_path, restore_vol = self.nas_client.get_path_from_content(filer_restore_location)
                self.log.info(f"Destination Path: {dest_path} ; Restored Test Data path: {volume_name}")
                dest_restore_path = dest_path + "\\" + volume_name
            self.log.info("Destination Restore Path:{0}".format(dest_restore_path))

            src_hash = self.test_data_paths[content]

            dest_mount_drive = self.local_machine.mount_network_path(dest_restore_path,
                                                                     self.domainUser, self.domainPassword)
            dest_hash = self.local_machine._get_folder_hash(dest_mount_drive)
            self.log.info(f"Unmounting {dest_restore_path} at {dest_mount_drive}")
            self.local_machine.unmount_drive(dest_mount_drive)
            if src_hash == dest_hash:
                self.log.info("Restore validation Success.")
            else:
                raise Exception("Restore validation failed. Please check logs for more details.")

    @test_step
    def validate_inplace_restored_content(self, test_data):
        """Validates the restored content
                Args:
                    test_data : dict: local {test_data path : data_hash}
            Raises:
                Exception:
                    if failed to validate restored content

        """
        if self.agent_name.lower()=='nfs':
            for i in test_data.keys():
                mountpoint=self.nfsmountpoint
                temp = i.split('/')
                self.log.info(f"Inplace: {temp}")
                folder=temp[-1]
                dest_restored_hash = self.unix_restore_machine.get_folder_hash(mountpoint+'/'+folder)
                if dest_restored_hash == test_data[i]:
                    self.log.info("Restore Validation Success.")
                else:
                    raise Exception("Restore validation failed. Please check logs for more details.")

        else:
            for i in test_data.keys():
                mount_drive = self.windows_restore_machine.mount_network_path(i,
                                                                    self.domainUser, self.domainPassword)
                dest_restored_hash = self.windows_restore_machine._get_folder_hash(mount_drive)
                self.log.info(f"Unmounting {i} at {mount_drive}")
                self.local_machine.unmount_drive(mount_drive)
                if dest_restored_hash == test_data[i]:
                    self.log.info("Restore Validation Success.")
                else:
                    raise Exception("Restore validation failed. Please check logs for more details.")

    @test_step
    def validate_os_restored_content(self, restore_client, restore_location, os_type='windows'):
        """Validates the restored content in windows/Unix client

            Args:
                restore_client      (object)    --  machine class object for  client
                                                                where the content was restored
                restore_location (str) -- destination restore location path
                os_type (str) -- 'windows' or 'unix' OS

            Raises:
                Exception:
                    if failed to validate restored content

        """
        diff = True
        for content in self.test_data_paths:
            src_path, volume_name = self.get_path_from_content(self.tcinputs["ServerName"], content)
            if self.agent_name.lower()=='ndmp':
                src_path, volume_name = self.get_ndmp_path_from_content(content)

            restore_path = restore_location + "\\" + volume_name
            if os_type == 'unix':
                volume_name = volume_name.replace('\\', '/')
                restore_path = restore_location + "/" + volume_name
            if self.agent_name.lower()=='nfs':
                src_path=content
                volume_name='/'.join(volume_name.split('/')[-2:])
                restore_path = restore_location + "/" + volume_name
            self.log.info("source path:{0} ,volume path: {1}".format(src_path, volume_name))
            self.log.info("Destination Restore Path:{0}".format(restore_path))
            diff = self.compare_data(src_path, restore_client, restore_path)
        if not diff:
            self.log.error(
                "Restore validation failed.")
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self.log.info("Successfully validated restored content")

    def compare_data(self, source_content, destination_machine, restore_path):
        """Compares the two directories on different machines
            Arguments:
                source_content: str: data path at source
                destination_machine: object: destination client machine object
                restore_path: str: restore data path at  dest restored client

            Returns:
                 bool: True : if hash check matches
                       False: if hash match fails
        """
        if self.agent_name.lower()=='nfs':
            source_hash = self.test_data_paths[source_content]  #self.unix_restore_machine.get_folder_hash(mountpoint+'/'+folder)
            dest_hash = destination_machine.get_folder_hash(restore_path)
            if dest_hash == source_hash:
                return True
            else:
                return False
        else:
            mount_drive = self.local_machine.mount_network_path(source_content,
                                                                self.domainUser, self.domainPassword)
            source_hash = self.local_machine._get_folder_hash(mount_drive)
            self.local_machine.unmount_drive(mount_drive)
            dest_hash = destination_machine._get_folder_hash(restore_path)
            result = bool(source_hash == dest_hash)
            if not result:
                self.log.info("Data at two paths do not match")
                return False
            self.log.info('Comparison successful , data at both paths is identical')
            return True

    def execute_query(self, query, my_options=None, fetch_rows='all'):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options      (dict)  -- options in the query
                default: None

                fetch_rows      (str)   -- By default return all rows, if not return one row
            Return:
                    str : first column of the sql output

        """
        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))

        if fetch_rows != 'all':
            return self._csdb.fetch_one_row()[0]
        return self._csdb.fetch_all_rows()

    def run_inline_backup_copy(self) -> str:
        """
             Run inline backup copy at subclient

             Return: Snap job id
        """
        try:
            self.log.info("*" * 20 + "inline backup copy initiation" + "*" * 20)
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rfs_servers.access_server(self.server_name)
            self.rfs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            jobid = self.rfs_subclient.run_inline_backup_copy(subclientname=self.subclient_name,
                                                              backupsetname=self._backupset_name)
            self.log.info(f"Running Snap backup is with Job ID:{jobid}")
            job_status = self.wait_for_job_completion(jobid)
            time.sleep(30)
            backupjobid = self.execute_query(self.backupjobid, {'a': jobid})
            backupjobid = backupjobid[0][0]
            if not job_status:
                exp = f"Snap Job ID {jobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {jobid} Snap backup job Successful")
            self.log.info(f"Running Backup copy is with Job ID:{backupjobid}")
            time.sleep(5)
            backup_job_status = self.wait_for_job_completion(backupjobid)
            if not backup_job_status:
                exp = f"Backup Copy Job ID {backupjobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {backupjobid} Backup job Successful")
            return jobid
        except Exception as exp:
            raise CVTestStepFailure(f'Run inline backup copy failed with error : {exp}')

    def run_offline_backup_copy_subclient_level(self):
        """
             Run backup Copy at Subclient Level
        """
        try:
            self.log.info("*" * 20 + "offline backup copy initiation at Subclient" + "*" * 20)
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab("File servers")
            self.rfs_servers.access_server(self.server_name)
            self.rfs_servers.access_agent(self.agent_name)
            self.__admin_console.access_tab("Subclients")
            self.rfs_subclient.run_offline_backup_copy(subclient_name=self.subclient_name,
                                                                     backupset_name=self._backupset_name)
            backupjobid = self.__admin_console.get_jobid_from_popup()
            self.log.info(f"Running Backupcopy is with Job ID:{backupjobid}")
            job_status = self.wait_for_job_completion(backupjobid)
            if not job_status:
                exp = f"Snap Job ID {backupjobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {backupjobid} offline backup job Successful")
        except Exception as exp:
            raise CVTestStepFailure(f'Run offline backup copy at Subclient Level failed with error : {exp}')

    def NasTemplate(self):
        """Main function for test case execution"""
        self.cleanup()
        self.create_entities()
        self.log.info("Add Test Data")
        self.test_data_paths = self.add_test_data()
        # Run Full backup and Inplace Restore
        self.verify_backup(self.full)
        self.log.info("Sleeping for 5mins before first restore")
        time.sleep(120)     #Sleeping for 2mins as restore option sometimes is not visible instantly
        self.verify_restore()
        self.validate_inplace_restored_content(self.test_data_paths)
        ndmp_nre = True
        if self.agent_name.lower()!='nfs':
            # Run INCR Backup and Outplace filer Restore
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.verify_backup(self.incr)
            self.verify_restore(dest_client=self.dest_filer, restore_path=self.filer_restore_path)
            self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)

            # Run DIFF backup and Outplace Restore to Windows Client
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            if self.agent_name.lower() == 'ndmp':
                self.verify_backup(self.diff)
            else:
                self.verify_backup(self.incr)
            if self.agent_name.lower()=='ndmp':
                if (self.enable_snap and self.vendor.value not in self.ndmp_snap_not_nre) or (
                        not self.enable_snap and self.vendor.value not in self.ndmp_streaming_not_nre):
                    ndmp_nre=True
                else:
                    ndmp_nre=False
            if ndmp_nre:
                dir_name = self.options_selector._get_restore_dir_name()
                windows_restore_path = f"C:\\{dir_name}"
                self.out_restore_path = windows_restore_path
                self.log.info(f"Creating restore path at destination : {windows_restore_path}")
                self.windows_restore_machine.create_directory(windows_restore_path)
                self.verify_restore(dest_client=self.windows_client, restore_path=self.out_restore_path)
                self.validate_os_restored_content(self.windows_restore_machine, self.out_restore_path)
                self.log.info(f"Removing windows restored directory: {windows_restore_path}")
                self.windows_restore_machine.remove_directory(windows_restore_path)
        # Run FULL backup and Outplace Restore to Unix Client
        if not self.agent_name.lower()=='cifs' and ndmp_nre:
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.verify_backup(self.incr)
            dir_name = self.options_selector._get_restore_dir_name()
            unix_restore_path = f"/root/Desktop/{dir_name}"
            self.out_restore_path = f"/root/Desktop/{dir_name}"
            self.log.info(f"Creating restore path at destination : {unix_restore_path}")
            self.unix_restore_machine.create_directory(unix_restore_path)
            self.verify_restore(dest_client=self.unix_client, restore_path=self.out_restore_path)
            self.validate_os_restored_content(self.unix_restore_machine, unix_restore_path, os_type='unix')
            self.log.info(f"Removing Unix restored directory: {unix_restore_path}")
            self.unix_restore_machine.remove_directory(unix_restore_path)
        if self.enable_snap:
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.log.info("Run Inline Backup copy at Subclient Level")
            self.run_inline_backup_copy()
            self.log.info("Restore from Primary Copy")
            if self.agent_name.lower() == 'nfs':
                dir_name = self.options_selector._get_restore_dir_name()
                unix_restore_path = f"/root/Desktop/{dir_name}"
                self.out_restore_path = f"/root/Desktop/{dir_name}"
                self.log.info(f"Creating restore path at destination : {unix_restore_path}")
                self.unix_restore_machine.create_directory(unix_restore_path)
                self.verify_restore(storage_copy_name=self.primary, dest_client=self.unix_client,
                                    restore_path=self.out_restore_path)
                self.validate_os_restored_content(self.unix_restore_machine, unix_restore_path, os_type='unix')
                self.log.info(f"Removing Unix restored directory: {unix_restore_path}")
                self.unix_restore_machine.remove_directory(unix_restore_path)
            else:
                self.verify_restore(storage_copy_name=self.primary, dest_client=self.dest_filer,
                                    restore_path=self.filer_restore_path)
                self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.log.info("Run Incremental Backup")
            self.verify_backup(self.incr)
            self.log.info("Run Offline Backup copy at Subclient Level")
            self.run_offline_backup_copy_subclient_level()
            self.log.info("Restore from Primary Copy")
            if self.agent_name.lower() == 'nfs':
                dir_name = self.options_selector._get_restore_dir_name()
                unix_restore_path = f"/root/Desktop/{dir_name}"
                self.out_restore_path = f"/root/Desktop/{dir_name}"
                self.log.info(f"Creating restore path at destination : {unix_restore_path}")
                self.unix_restore_machine.create_directory(unix_restore_path)
                self.verify_restore(storage_copy_name=self.primary, dest_client=self.unix_client,
                                    restore_path=self.out_restore_path)
                self.validate_os_restored_content(self.unix_restore_machine, unix_restore_path, os_type='unix')
                self.log.info(f"Removing Unix restored directory: {unix_restore_path}")
                self.unix_restore_machine.remove_directory(unix_restore_path)
            else:
                self.verify_restore(storage_copy_name=self.primary, dest_client=self.dest_filer,
                                    restore_path=self.filer_restore_path)
                self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)
        self.cleanup()

    def NasTemplate2(self):
        """Main function for test case execution
            Implementing restores from different points"""
        self.cleanup()
        self.create_entities()
        self.log.info("Add Test Data")
        self.test_data_paths = self.add_test_data()
        # Run Full backup and Inplace Restore
        self.verify_backup(self.full)
        self.log.info("Sleeping for 5mins before first restore")
        time.sleep(300)
        self.verify_restore()
        self.validate_inplace_restored_content(self.test_data_paths)
        # Run INCR Backup and Outplace filer Restore
        self.log.info("Add Test Data")
        self.test_data_paths = self.add_test_data()
        self.verify_backup(self.incr)
        self.restore_from_client(dest_client=self.dest_filer, restore_path=self.filer_restore_path)
        self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)
        # Run DIFF backup and Outplace Windows Restore
        self.log.info("Add Test Data")
        self.test_data_paths = self.add_test_data()
        backup_jobid = self.verify_backup(self.diff)
        ndmp_nre=False
        if self.agent_name.lower() == 'ndmp':
            if (self.enable_snap and self.vendor.value not in self.ndmp_snap_not_nre) or (
                    not self.enable_snap and self.vendor.value not in self.ndmp_streaming_not_nre):
                ndmp_nre = True
            else:
                ndmp_nre = False
        if ndmp_nre:
            dir_name = self.options_selector._get_restore_dir_name()
            windows_restore_path = f"C:\\{dir_name}"
            self.out_restore_path = windows_restore_path
            self.log.info(f"Creating restore path at destination : {windows_restore_path}")
            self.windows_restore_machine.create_directory(windows_restore_path)
            self.restore_by_job(backup_jobid, dest_client=self.windows_client, restore_path=self.out_restore_path)
            self.validate_os_restored_content(self.windows_restore_machine, self.out_restore_path)
            self.log.info(f"Removing windows restored directory: {windows_restore_path}")
            self.windows_restore_machine.remove_directory(windows_restore_path)
            # Run FULL backup and Outplace Unix Restore
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.verify_backup(self.full)

            recovery_point = {'year': date.today().strftime("%Y"), 'month': date.today().strftime("%B"),
                              'date': date.today().strftime("%d").strip("0") if
                              date.today().strftime("%d").startswith("0") else date.today().strftime("%d")}
            dir_name = self.options_selector._get_restore_dir_name()
            unix_restore_path = f"/root/Desktop/{dir_name}"
            self.out_restore_path = f"/root/Desktop/{dir_name}"
            self.log.info(f"Creating restore path at destination : {unix_restore_path}")
            self.unix_restore_machine.create_directory(unix_restore_path)
            self.restore_from_recovery_point(recovery_time=recovery_point,
                                             dest_client=self.unix_client, restore_path=self.out_restore_path)
            self.validate_os_restored_content(self.unix_restore_machine, unix_restore_path, os_type='unix')
            self.log.info(f"Removing windows restored directory: {unix_restore_path}")
            self.unix_restore_machine.remove_directory(unix_restore_path)

        else:
            self.restore_by_job(backup_jobid, dest_client=self.dest_filer, restore_path=self.filer_restore_path)
            self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)

            # Run FULL backup
            self.log.info("Add Test Data")
            self.test_data_paths = self.add_test_data()
            self.verify_backup(self.full)
            recovery_point = {'year': date.today().strftime("%Y"), 'month': date.today().strftime("%B"),
                              'date': date.today().strftime("%d").strip("0") if
                              date.today().strftime("%d").startswith("0") else date.today().strftime("%d")}
            self.restore_from_recovery_point(recovery_time=recovery_point,
                                             dest_client=self.dest_filer, restore_path=self.filer_restore_path)
            self.validate_filer_restored_content(self.dest_filer, self.filer_restore_path)


