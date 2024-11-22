# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing 3dfs server operations

TDFSServerUtils is the class defined in this file.



tdfshelper: Helper class to perform 3dfs server operations

TDfsServerUtils:
    create_3dfs_share()                 --  For creating 3dfs share

    list_3dfs_share()                   --  For listing all the share of 3dfs server

    delete_3dfs_share()                 --  To delete a particular share

    cleanup_3dfs()                      --  To delete all the share

    compare_ace()                       --  Method which compare ace of two path
                                            used for 3dfs ACL project

    validate_user_folder_permission()   --  To validate if the user has expected access
                                            on folder

    validate_user_file_permission()     --  To validate if the user has expected access
                                            on folder

    get_tdfs_ip()                       --  To get ip address of 3dfs server



"""
import time
from AutomationUtils import logger
from AutomationUtils.machine import Machine


class TDfsServerUtils():
    """Helper class for 3dfs
    Initialize instance of the TDfsServerHelper class.

                Args:

                    nfs_server_hostname  (str)       --  hostname of NFS server

                    testcase            (object)     --  instance of the CVTestCase class

                Returns:
                    object - instance of the TDfsServerHelper class
    """

    def __init__(self, testcase, tdfs_server_name):
        self.log = logger.get_log()
        self.tdfs_server_name = tdfs_server_name
        self.testcase = testcase
        self.tdfs_machine_obj = Machine(
            tdfs_server_name, self.testcase.commcell)

    def create_3dfs_share(self, backupset_name, extra_option=None, client_name=None):
        """
        Function to create 3dfs share

        Args:
            backsettName   (str)   --  Backupset Name for 3dfs server

            extra_option   (dict)  -- dictionary that includes all optional options
                options:

                    subclientName       (str)  : If provided it will create subclient level share
                                                otherwise backupset level share will be created

                    show_deleted        (bool) : Include deleted items option

                    enable_acl          (bool) : Enable acl for share option

                    refresh_on_backup   (bool) : Forever share option

                    to_time             (str)  : To_time for share

                    nfs_clients         (str)  : Comma separated nfs clients for permission

                    uid                 (str)  : Cassandra OS user that needs permission for the restored files

                    gid                 (str)  : The Cassandra OS group that needs permission for the restored files

                    access_mask          (str)  : access mask for Casandra restore subclients

            client_name   (str)    --  client name for 3dfs server

        Return:
            Str -  return share_name of the share created.

        """
        if not hasattr(self.testcase, 'client_name'):
            if client_name is None:
                raise Exception("client_name is not defined")
            self.testcase.client_name = client_name

        try:
            if extra_option is None:
                extra_option = dict()
            options = {
                "subclientName": extra_option.get("subclientName", None),
                "show_deleted": extra_option.get("show_deleted", "0"),
                "enable_acl": extra_option.get("enable_acl", "0"),
                "refresh_on_backup": extra_option.get("refresh_on_backup", "1"),
                "copy_precedence": extra_option.get("copy_precedence", "0"),
                "to_time": extra_option.get("to_time", None),
                "nfs_clients": extra_option.get("nfs_clients", None),
                "uid": extra_option.get("uid", None),
                "gid": extra_option.get("gid", None),
                "access_mask": extra_option.get("access_mask", None)
            }
            share_name = "{0}_" + str(int(time.time()))
            if options['subclientName'] is None:
                request_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no' ?>
                <App_Set3DFSSharePropsReq opType='4'>
                <shareInfo copyPrecedence='REPLACE_COPYPRECEDENCE' isForeverShare='REPLACE_FOREVER'
                isReadOnly='REPLACE_READONLY' shareName='REPLACE_SHARENAME' showDeleted='REPLACE_SHOWDELETED'
                acl='REPLACE_ACL' status='0'>
                <tdfsServer mediaAgentName='REPLACE_TDFSSERVERNAME'/>
                <backupSet _type_='6' clientName='REPLACE_CLIENTNAME' appName='File System'
                instanceName='DefaultInstanceName' backupsetName='REPLACE_BACKUPSETNAME'/>
                <indexingServer mediaAgentName='REPLACE_INDEXINGSERVERNAME'/>
                <toTime time='REPLACE_TOTIME'/>
                REPLACE_NFSCLIENTS
                """
                share_name = share_name.format(backupset_name)
                request_xml = request_xml.replace(
                    'REPLACE_BACKUPSETNAME', backupset_name)
                if options.get('refresh_on_backup') == "1":
                    share_name = backupset_name
                else:
                    share_name = share_name.format(backupset_name)
            else:
                request_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no' ?>
                <App_Set3DFSSharePropsReq opType='4'>
                <shareInfo copyPrecedence='REPLACE_COPYPRECEDENCE' isForeverShare='REPLACE_FOREVER'
                isReadOnly='REPLACE_READONLY' shareName='REPLACE_SHARENAME' showDeleted='REPLACE_SHOWDELETED'
                acl='REPLACE_ACL' status='0' fsmType="5" fsmSubtype="1">
                <tdfsServer mediaAgentName='REPLACE_TDFSSERVERNAME'/>
                <subclient _type_='7' clientName='REPLACE_CLIENTNAME' appName='File System'
                instanceName='DefaultInstanceName' backupsetName='REPLACE_BACKUPSETNAME'
                subclientName='REPLACE_SUBCLIENTNAME'/>
                <indexingServer mediaAgentName='REPLACE_INDEXINGSERVERNAME'/>
                <toTime time='REPLACE_TOTIME'/>
                REPLACE_NFSCLIENTS"""
                request_xml = request_xml.replace(
                    'REPLACE_BACKUPSETNAME', backupset_name).replace(
                        'REPLACE_SUBCLIENTNAME', options.get('subclientName'))

                if options.get('refresh_on_backup') == "1":
                    share_name = options.get('subclientName')
                else:
                    share_name = share_name.format(
                        options.get('subclientName'))

            if options['uid'] is not None:
                request_xml += """<customParams key="uid" value="%s"/>
                                  <customParams key="gid" value="%s"/>
                                  <customParams key="accessPerm" value="%s"/>"""

            request_xml += """</shareInfo>
                              </App_Set3DFSSharePropsReq>"""

            if options['uid'] is not None:
                request_xml = request_xml % (options['uid'], options['gid'], options['access_mask'])
            self.log.debug("request xml for creating 3dfs share %s" % request_xml)

            # check if share is already present
            self.delete_3dfs_share(share_name)
            if options['to_time']:
                pattern = '%Y-%m-%d %H:%M:%S'
                epoctime = str(
                    int(time.mktime(time.strptime(options['to_time'], pattern))))
            else:
                epoctime = str(int(time.time()))

            if options.get('nfs_clients') is None:
                nfs_clients_xml = "<nfsClients val=\'0.0.0.0\'/>"
            else:
                nfs_clients = options.get('nfs_clients').split(',')
                nfsclientreplacestr = []
                for nfsclient in nfs_clients:
                    nfsclientreplacestr.append(
                        f"<nfsClients val=\'{nfsclient}\'/>")
                nfs_clients_xml = ''.join(nfsclientreplacestr)
            request_xml = request_xml.replace(
                'REPLACE_SHOWDELETED', options.get('show_deleted')).replace(
                    'REPLACE_FOREVER', options.get('refresh_on_backup')).replace(
                        'REPLACE_READONLY', options.get('refresh_on_backup')).replace(
                            'REPLACE_ACL', options.get('enable_acl')).replace(
                                'REPLACE_TDFSSERVERNAME', self.tdfs_server_name).replace(
                                    'REPLACE_CLIENTNAME', self.testcase.client_name).replace(
                                        'REPLACE_INDEXINGSERVERNAME', self.tdfs_server_name).replace(
                                            'REPLACE_TOTIME', epoctime).replace(
                                                'REPLACE_COPYPRECEDENCE', options.get('copy_precedence')).replace(
                                                    'REPLACE_NFSCLIENTS', nfs_clients_xml).replace(
                                                        'REPLACE_SHARENAME', share_name)
            self.log.info("final request xml %s" % request_xml)
            response = self.testcase.commcell._qoperation_execute(request_xml)
            if 'errorCode' in response:
                raise Exception(
                    "3dfs export failed with error %s" %
                    response['errorMessage'])
            if response['errorResp']['errorCode']:
                raise Exception("%s" % response['errorResp']['errorMessage'])
            self.log.info(
                "share %s is created for tdfs server %s",
                share_name, self.tdfs_server_name)
            return share_name
        except Exception as excp:
            self.log.error('3dfs export creation failed with error: %s', excp)
            raise Exception(
                '3dfs export Creation Failed with error: {0}'.format(
                    excp))

    def list_3dfs_share(self):
        """
        To list the 3dfs share present for the server

        Return:

             Dict- Share name as key and share id as value

        """
        try:

            request_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <App_Get3DFSShareReq opType="0">
            </App_Get3DFSShareReq>
            """
            response = self.testcase.commcell._qoperation_execute(request_xml)

            share_list = dict()
            for share in response['tdfsShares']:
                if share['tdfsServer']['mediaAgentName'] == self.tdfs_server_name:
                    share_list[share['shareName']] = share['shareId']

            return share_list
        except Exception as excp:
            self.log.error('Failed to list 3dfs with error: %s', excp)
            raise Exception(
                'Failed to list 3dfs with error: {0}'.format(
                    excp))

    def delete_3dfs_share(self, share_name):
        """
        Function to delete the share

        Args:

            share_name     (str)    :share name which you want to delete


        """
        try:
            share_list = self.list_3dfs_share()
            if share_list:
                if share_name in share_list.keys():
                    request_xml = """<?xml version='1.0' encoding='UTF-8'?>
                    <App_Set3DFSSharePropsReq opType="7">
                    <shareInfo shareId='REPLACE_SHAREID'>
                    </shareInfo>
                    </App_Set3DFSSharePropsReq>
                    """
                    request_xml = request_xml.replace(
                        'REPLACE_SHAREID', str(share_list[share_name]))
                    self.log.info("Share %s exist. Deleting it", share_name)
                    self.testcase.commcell._qoperation_execute(request_xml)
                    self.log.info("Share %s Deleted", share_name)
                    time.sleep(30)
                else:
                    self.log.info(
                        "Share %s does not exist for %s 3dfs Server",
                        share_name,
                        self.tdfs_server_name)
        except Exception as excp:
            self.log.error('3dfs deletion failed with error: %s', excp)
            raise Exception(
                '3dfs deletion failed with error: {0}'.format(
                    excp))

    def cleanup_3dfs(self):
        """
        Delete all the 3dfs share for a 3dfs server


        """
        try:
            share_list = self.list_3dfs_share()
            if share_list:
                for sharename in share_list.keys():
                    request_xml = """<?xml version='1.0' encoding='UTF-8'?>
                                <App_Set3DFSSharePropsReq opType="7">
                                <shareInfo shareId='REPLACE_SHAREID'>
                                </shareInfo>
                                </App_Set3DFSSharePropsReq>
                                """
                    request_xml = request_xml.replace(
                        'REPLACE_SHAREID', str(share_list[sharename]))
                    self.testcase.commcell._qoperation_execute(request_xml)
                    self.log.info("Share %s Deleted", sharename)
            self.log.info("All share deleted")
        except Exception as excp:
            self.log.error('3dfs cleanup failed with error: %s', excp)
            raise Exception(
                '3dfs cleanup failed with error: {0}'.format(
                    excp))

    def compare_ace(self, source_path, destination_path, user, user_obj):
        """
        compare ace of user between source and destination path

        Args:
            source_path     (str)   --  Source path for ACE comparison

            destination_path (str)  --  Destination path for ACE comparison

            user             (str)  --  Required user

            user_obj         (str)  --  User which has acl read permission

        Return:
            (Bool) -- True if it matches


        Raises Exception            - If ace does not match
        """
        try:
            source_ace = user_obj.get_ace(user, source_path)
            destination_ace = user_obj.get_ace(user, destination_path)
            (retcode, retval) = self.testcase.client_machine._compare_lists(
                source_ace, destination_ace)
            if not retcode:
                raise Exception(
                    "ACL Comparison fails with difference %s" %
                    retval)
            self.log.info(
                "ACL match of %s and %s for user %s",
                source_path, destination_path, user)
            return True
        except Exception as excp:
            self.log.error('Compare acl fails with error %s', excp)
            raise Exception(
                'compare AC; failed with error: {0}'.format(
                    excp))

    def validate_user_folder_permission(
            self,
            action,
            user_machine_obj,
            permission,
            test_path):
        """
        Test the access of user of based on the permission and action

        Args:
            action              (str)   --  Allow or Deny

            user_machine_obj    (machine_obj)   -- Machine obejct created
                                                    with required user credential

            permission          (str)           -- Permission to check
                                                   Valid permission- read, readandexecute,

                                                   write, modify and full control
            test_path           (str)           -- Folder for which we need
                                                    to check the permission

        Return:
            bool                                --  IF the access is as expected return True

        """
        try:
            test_file = user_machine_obj.join_path(
                test_path, "created file")
            if permission.lower() == "read" or permission.lower() == "readandexecute":
                user_machine_obj.scan_directory(test_path)
            elif permission.lower() == "write":

                user_machine_obj.create_file(test_file, content="CVadded")
            elif permission.lower() == "modify":
                user_machine_obj.scan_directory(test_path)
                user_machine_obj.create_file(test_file, content="CVadded")
                user_machine_obj.delete_file(test_file)
            elif permission.lower() == "FullControl":
                user_machine_obj.scan_directory(test_path)
                user_machine_obj.create_file(test_file, content="CVadded")
                user_machine_obj.delete_file(test_file)
            else:
                raise Exception("Please correct input for permission")
            if action.lower() == "allow":
                self.log.info(
                    "User %s does have permission %s for file %s which "
                    "is expected",
                    user_machine_obj.username,
                    permission,
                    test_path)
                return True

            raise Exception("The user access is not as expected")

        except Exception as excp:
            if isinstance(excp.args, tuple):
                if(excp.args[1].find("denied") and action.lower() == "deny"):
                    self.log.info(
                        "User %s does not have permission %s for folder %s which "
                        "is expected", user_machine_obj.username, permission, test_path)
                    return True
            self.log.error("User validation fails with this erorr %s", excp)
            raise Exception("User validation fails with this erorr %s" % excp)

    def validate_user_file_permission(
            self,
            action,
            user_machine_obj,
            permission,
            test_path):
        """
        Test the access of user of based on the permission and action
        Args:
            action              (str)   --  Allow or deny

            user_machine_obj    (machine_obj)   -- Machine obejct created with
                                                    required user credentials

            permission          (str)           -- Permission to check
                                                   Valid permission- read, readandexecute,write,
                                                   modify and full control

            test_path           (str)           -- File for which we need to check the permission

        Return:

            bool                                --  IF the access is as expected return True

        """
        try:
            if permission.lower() == "read":
                user_machine_obj.read_file(test_path)
            elif permission.lower() == "readandexecute":
                user_machine_obj.read_file(test_path)

            elif permission.lower() == "write":
                user_machine_obj.append_to_file(
                    test_path, content="cvappended")
            elif permission.lower() == "modify":
                user_machine_obj.read_file(test_path)
                user_machine_obj.append_to_file(
                    test_path, content="cvappended")
                user_machine_obj.delete_file(test_path)
            elif permission.lower() == "FullControl":
                user_machine_obj.read_file(test_path)
                user_machine_obj.append_to_file(
                    test_path, content="cvappended")
                user_machine_obj.delete_file(test_path)
            else:
                raise Exception("Please correct input for permission")
            if action.lower() == "allow":
                self.log.info(
                    "User %s does have permission %s for file %s which "
                    "is expected",
                    user_machine_obj.username,
                    permission,
                    test_path)
                return True

            raise Exception("The user access is not as expected")
        except Exception as excp:
            if isinstance(excp.args, tuple):
                if (excp.args[1].find("denied") and action.lower() == "deny"):
                    self.log.info(
                        "User %s does not have permission %s for file %s which "
                        "is expected", user_machine_obj.username, permission, test_path)
                    return True
            self.log.error("User validation fails with this error %s", excp)
            raise Exception("User validation fails with this error %s" % excp)

    def get_tdfs_ip(self):
        """
        To get the ip address of tdfs server

        Return:

             (str)  -- ip address of tdfs server
        """

        self.tdfs_machine_obj._get_client_ip()
        return self.tdfs_machine_obj._ip_address

    def data_copy_compare(
            self,
            sourcemachine,
            mountpoint_name,
            test_path,
            nfsclient=None,
            username=None,
            password=None):
        """Compares the checksum of source path with exported share on nfs client
            and checks if they are same. (This is Unix checksum)

             Args:
                sourcemachine (object)  -- machine object of client machine

                mountpoint_name (str)   -- Directory name on which share is mounted

                test_path (str)         -- path for comaparison

                nfsclient(str)          -- if Mentioned, username and password need

                username (str)          -- NFS cliennt username

                passwordd   (str)       -- NFS client password

        Return:
            (bool)                      --True if source hash match with destination

        """
        try:
            self.log.info("Comparing checksum of source and share")
            # get the checksum of source and destination
            if self.testcase.applicable_os == 'WINDOWS':
                test_path1 = test_path.replace(':', '$').replace('\\', '//')
            else:
                test_path1 = test_path

            if nfsclient:
                nfs_machine = Machine(
                    nfsclient, username=username, password=password)
            elif (nfsclient and (not username or not password)):
                raise Exception(
                    "username or password is empty. Please provide correct credentials")
            else:
                nfs_machine = self.tdfs_machine_obj


            # get the checksum of destination list
            destpath = nfs_machine.join_path(mountpoint_name, test_path1)
            difference = sourcemachine.compare_folders(nfs_machine, test_path, destpath)
            if not bool(difference):
                self.log.info("Source and destination list is same")
                return True

            self.log.info("Source and destination list differ")
            raise Exception("diff output %s", str(difference))

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            raise Exception('Failed with error %s', str(excp))
