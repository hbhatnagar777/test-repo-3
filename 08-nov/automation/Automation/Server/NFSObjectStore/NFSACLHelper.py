# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–
"""File for performing ACL related operations for NFS objectstore

NfsAclHelper is the class defined in this file.

ObjectstoreClientUtils: Class for providing common functions for test clients

NFSServerHelper: Class for providing NFS server related operations

NfsAclHelper:
    __init__()                    --  initialize instance of the NfsAclHelper class
    by defining common test path
"""

import string
import random

from AutomationUtils import logger
from AutomationUtils.machine import Machine


class NfsAclHelper:
    """NFS objectstore utils class to perform common operations for test clients"""

    def __init__(self, client_name, commcell=None, username=None, password=None):
        """Initialize instance of the NfsAclHelper class..

            Args:
                client_name   (str)     -- hostname or IP address of test client machine

                username      (str)     -- login username of client_name

                password      (str)     -- login password of client_name

                commcell      (object)  --  instance of the Commcell class

            Returns:
                object - instance of the ObjectstoreClientUtils class

            Raises:
                Exception:
                    if any error occurs in the initialization
        """
        self.log = logger.get_log()
        self.width = 100
        # Unix add user expects crypted password and it is not supported on windows.
        # So we are using hard coded password string and encrypted password for the same
        # This password is used only during the test and deleted in the cleanup
        self.default_password = "yfyw@48"

        # encrypted password below to to pass to adduser.
        """ TODO: crypt() is supported for unix platform only. but most of the time, controller
                  machines are windows. So using the encrypted password below for now until
                  we research on alternative solution"""
        self.default_encrypted_password = ('$6$PBZ.zevbwUMtV5QY$WWpxwCz9EuGF/0mCxHbUyr'
                                           'ZwXbj3R9FiJrxnlmDxUbEtj4jQOAg52r9pZlTKiPoA'
                                           'dFIKz7sbIVhcdHPa8IqWb1')
        self.ace_user_string = "testacluser"
        self.client_name = client_name
        self.machine_obj_su_user = []

        if not commcell and (not username or not password):
            self.log.error("NfsAclHelper require either commcell object or "
                           "system login details. Both cannot be None")
            raise Exception("NfsAclHelper require either commcell object or "
                            "system login details. Both cannot be None")

        if client_name in commcell.clients.all_clients:
            # if client machine is a commcell client
            self.machine_obj = Machine(client_name, commcell)
        else:
            # if client machine is not a commcell client
            self.machine_obj = Machine(client_name, username=username, password=password)

        if self.machine_obj.os_info.lower() == 'Windows':
            raise Exception("Windows platform is currently not supported")
            # self.nfs4_setfacl_path = "/usr/bin/nfs4_setfacl"
            # self.nfs4_getfacl_path = "/usr/bin/nfs4_getfacl"
            # self.default_ace_file_permissions = {"read":"r", "write":"watTNcCy",
            #                                      "append":"a", "execute":"x"}

        self.nfs4_setfacl_path = '/usr/bin/nfs4_setfacl'
        self.nfs4_getfacl_path = '/usr/bin/nfs4_getfacl'
        self.default_ace_file_permissions = {"read": "r",
                                             "write": "wa",
                                             "append": "wa",
                                             "execute": "rx"}

        self.default_ace_folder_permissions = {"read": "r",
                                               "write": "wx",
                                               "append": "ax",
                                               "execute": "x"}
        self.disable_other_users = '700'
        self.allow_other_users = '777'
        self.ace_allow = 'A'
        self.ace_deny = 'D'

        if not self.machine_obj.check_file_exists(self.nfs4_setfacl_path) and \
           not self.machine_obj.check_file_exists(self.nfs4_getfacl_path):
            self.log.error("NFSv4 ACL tools are not installed on client %s machine",
                           client_name)
            raise Exception("NFSv4 ACL tools are not installed on client {0} machine".format(
                client_name))

    def validate_user_file_permission(self, action, user_machine_obj, permission, test_path,
                                      valiadate_before_acl=False):
        """Verify the user operations for the given file operation permission

        Args:
            action               (str)   --  Ace type in test (allow/block)

            user_machine_obj     (obj)   --  user machine object object

            permission           (str)   --  valid file operation (read|write|execute|append)

            test_path            (str)   --  path of file for which access to be verified

            valiadate_before_acl (bool)  -- is this function called before applying ACL

        Returns:
            True    -   user has permission to perform the operation
            False   -   user doesn't have permission to perform the operation


        Raises:
            Exception(Exception_Code, Exception_Message):
                if invalid file operation is passed

        """
        ret_val = True
        if valiadate_before_acl:
            ace_type_str = 'deny' if action == self.ace_allow else 'allow'
            if action == self.ace_allow:
                self.machine_obj.change_file_permissions(test_path,
                                                         self.disable_other_users)
            else:
                self.machine_obj.change_file_permissions(test_path,
                                                         self.allow_other_users)
            self.log.info("required file permissions changed for test path %s",
                          test_path)
        else:
            ace_type_str = 'allow' if action == self.ace_allow else 'deny'

        try:
            if permission == "read":
                user_machine_obj.read_file(test_path)
            elif permission == "write":
                user_machine_obj.create_file(test_path, content="CVadded")
            elif permission == "append":
                user_machine_obj.modify_content_of_file(test_path)
            elif permission == "execute":
                output = user_machine_obj.execute_command(test_path)
                if output.exception:
                    raise Exception(output.exception)
            else:
                ret_val = False
                raise Exception("invalid input operation {0} passed".format(permission))
        except Exception as e:
            self.log.info("exception received %s", e)
            ret_val = False

        if valiadate_before_acl:
            if action == self.ace_allow and ret_val:
                raise Exception("user {0} have {1} permission"
                                " before applying ACLs".format(user_machine_obj, ace_type_str))
            if action == self.ace_deny and not ret_val:
                raise Exception("user {0} doesn't have {1} permission"
                                "before applying ACLs".format(user_machine_obj, ace_type_str))
        else:
            if action == self.ace_allow and not ret_val:
                raise Exception("user {0} didn't get {1} permission"
                                " after applying ACLs".format(user_machine_obj, ace_type_str))
            if action == self.ace_deny and ret_val:
                raise Exception("user {0} still have {1} permission"
                                " after applying ACLs".format(user_machine_obj, ace_type_str))

    def validate_user_folder_permission(self, action, user_machine_obj, permission, test_path,
                                        valiadate_before_acl=False):
        """Verify the user operation for the given directory permissions

        Args:
            action                 (str)   --  Ace type in test (allow/block)

            user_machine_obj       (obj)   --  user machine object object

            permission             (str)   --  valid file operation (read|write|execute|append)

            test_path              (str)   --  path of file for which access to be verified

            valiadate_before_acl   (bool)  -- is this function called before applying ACL

        Returns:
            True    -   user has permission to perform the operation
            False   -   user doesn't have permission to perform the operation


        Raises:
            Exception(Exception_Code, Exception_Message):
                if invalid file operation is passed

        """
        ret_val = True

        if valiadate_before_acl:
            ace_type_str = 'deny' if action == self.ace_allow else 'allow'
            if action == self.ace_allow:
                self.machine_obj.change_file_permissions(test_path,
                                                         self.disable_other_users)
            else:
                self.machine_obj.change_file_permissions(test_path,
                                                         self.allow_other_users)
            self.log.info("required file permissions changed for test path %s",
                          test_path)
        else:
            ace_type_str = 'allow' if action == self.ace_allow else 'deny'

        try:
            if permission == "read":
                # TODO: need to get more generic method to list directory. which returns
                # TODO:      exception message
                user_machine_obj.scan_directory(test_path)
            elif permission == "write":
                test_file = self.machine_obj.join_path(test_path, "testfile")
                user_machine_obj.create_file(test_file, content="CVadded")
            elif permission == "append":
                test_subdir = self.machine_obj.join_path(test_path, "testsubdir")
                self.log.info("creating subdirectory %s", test_subdir)
                if not user_machine_obj.create_directory(test_subdir):
                    ret_val = False
            elif permission == "execute":
                cmd = "cd {0}".format(test_path)
                output = user_machine_obj.execute_command(cmd)
                if output.exception:
                    ret_val = False
            else:
                raise Exception("invalid input operation {0} passed".format(permission))
        except Exception as e:
            self.log.info("exception received %s", e)
            ret_val = False

        if valiadate_before_acl:
            if action == self.ace_allow and ret_val:
                raise Exception("user {0} have {1} permission"
                                " before applying ACLs".format(user_machine_obj, ace_type_str))
            if action == self.ace_deny and not ret_val:
                raise Exception("user {0} doesn't have {1} permission"
                                "before applying ACLs".format(user_machine_obj, ace_type_str))
        else:
            if action == self.ace_allow and not ret_val:
                raise Exception("user {0} didn't get {1} permission"
                                " after applying ACLs".format(user_machine_obj, ace_type_str))
            if action == self.ace_deny and ret_val:
                raise Exception("user {0} still have {1} permission"
                                " after applying ACLs".format(user_machine_obj, ace_type_str))

    def create_users_machine_objs(self, users_list):
        """create required users and machine instance logged in as those users

        Args:
            users_list   (list)   --  list of username strings to be used to create user

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create users or user machine objects

        """
        for user in users_list:
            self.log.info("creating user %s", user)
            self.machine_obj.add_user(user, self.default_encrypted_password)

            self.log.info("creating machine object for user %s", user)
            machine_obj = Machine(self.client_name, username=user,
                                  password=self.default_password)
            self.machine_obj_su_user.append(machine_obj)

    def read_permissions_inputs(self, file_operations, usage, test_type="file"):
        """read inputs required to verify file or folder ACL permissions.

        Args:
            file_operations  (list or dict or str)   --
                if file_operations == str, input should be 'all' | supported file operations
                    example: file_operations="read", file_operations="write"
                if file_operations == str, input should be list of supported file operations
                    example: file_operations=["read", "write", "append"]
                if file_operations == dict, input should be dictionary containing key as file
                operation and value as ACE to be used to verify the operation
                    example: file_operations={"read":'r', "write":w'}

                In case of dictionary user passed ACEs are used to verify the operations. In case
                of others, default ACEs will be used for each operations

            usage   (str)                            --  usage string to call the function

            test_type (str)                          -- used to get the default permissions

        Returns:
            tuple(file permissions, dict{file operation:ACEs})

        Raises:
            Exception(Exception_Message):
                in case of any failures in the test

        """
        if isinstance(file_operations, dict):
            permissions_to_test = list(file_operations)
            ace_permissions = file_operations
        elif isinstance(file_operations, list):
            permissions_to_test = file_operations
            if test_type == "file":
                ace_permissions = self.default_ace_file_permissions
            else:
                ace_permissions = self.default_ace_folder_permissions
        elif isinstance(file_operations, str):
            if file_operations == 'all':
                permissions_to_test = list(self.default_ace_file_permissions)
            else:
                permissions_to_test = [file_operations]
            if test_type == "file":
                ace_permissions = self.default_ace_file_permissions
            else:
                ace_permissions = self.default_ace_folder_permissions
        else:
            raise Exception("invalid inputs. expected usage {0}".format(usage))

        diff_file_perm = set(permissions_to_test) - set(self.default_ace_folder_permissions)
        if bool(diff_file_perm):
            raise Exception("these file operations {0} are currently not defined in"
                            " the test".format(diff_file_perm))

        self.log.info("file operations %s, ACL_permissions %s" % (permissions_to_test,
                                                                  ace_permissions))

        return permissions_to_test, ace_permissions

    def verify_ace_file_permissions(self, test_directory, file_operations="all"):
        """verify NFS v4 ACEs for file.

        Args:
            test_directory   (str)                   --  NFSv4 ACL supported mounted path

            file_operations  (list or dict or str)   --
                if file_operations == str, input should be 'all' | supported file operations
                    example: file_operations="read", file_operations="write"
                if file_operations == str, input should be list of supported file operations
                    example: file_operations=["read", "write", "append"]
                if file_operations == dict, input should be dictionary containing key as file
                operation and value as ACE to be used to verify the operation
                    example: file_operations={"read":'r', "write":w'}

                In case of dictionary user passed ACEs are used to verify the operations. In case
                of others, default ACEs will be used for each operations

        Returns:
            None

        Raises:
            Exception(Exception_Message):
                in case of any failures in the test

        """
        usage = "verify_ace_file_permissions(test_path, file_operations=list(file_operations)" \
                " or file_operations=dict(file_operation:acl_permissions)" \
                " or file_operations='all'"

        permissions_to_test, ace_file_permissions = self.read_permissions_inputs(file_operations,
                                                                                 usage)

        # generate user string for test
        random_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
        users_list = [(self.ace_user_string + '-' + random_string + '-' + str(i)) for i in range(2)]
        self.create_users_machine_objs(users_list)

        # verify for file allow permission
        test_file = self.machine_obj.join_path(test_directory,
                                               "testaclfile")

        self.log.info("test path to be used for ACL %s", test_file)
        self.log.info("deleting test file %s if already exist",test_file)
        try:
            self.machine_obj.delete_file(test_file)
        except Exception as e:
            self.log.info("ignoring the exception %s", e)

        for ace_permission in permissions_to_test:
            for action in [self.ace_allow, self.ace_deny]:
                ace_type_string = 'allow' if action == self.ace_allow else 'deny'
                self.log.info('=' * self.width)
                self.log.info("verifying ACL for {0} {1} on file".format(ace_type_string,
                                                                         ace_permission))

                self.log.info("user %s generating required setup to run the test",
                              self.machine_obj_su_user[0])
                if ace_permission == "read":
                    content = "writing from user {0} for read".format(users_list[0])
                    self.machine_obj_su_user[0].create_file(test_file, content)
                elif ace_permission == "write":
                    self.machine_obj_su_user[0].create_file(test_file, '')
                elif ace_permission == "append":
                    content = "writing from user {0} for append".format(users_list[0])
                    self.machine_obj_su_user[0].create_file(test_file, content)
                elif ace_permission == "execute":
                    content = "echo \"test script\""
                    self.machine_obj_su_user[0].create_file(test_file, content)

                self.log.info("validate file permissions before adding ACLs")
                self.validate_user_file_permission(action,
                                                   self.machine_obj_su_user[1],
                                                   ace_permission,
                                                   test_file,
                                                   valiadate_before_acl=True)

                self.log.info("apply ACL for %s %s operation" % (
                    ace_type_string, ace_permission))
                self.machine_obj.nfs4_setfacl(test_file, action, users_list[1],
                                              ace_file_permissions[ace_permission])

                self.log.info("validate file permissions after adding ACLs")

                # now let's test latest permissions are applied on the user
                self.validate_user_file_permission(action,
                                                   self.machine_obj_su_user[1],
                                                   ace_permission,
                                                   test_file)
                self.log.info("validation of ACL file permission %s %s was"
                              " successful" % (ace_type_string, ace_permission))

                self.log.info("deleting test file %s", test_file)
                self.machine_obj.delete_file(test_file)
                self.log.info('=' * self.width)
        self.machine_obj.delete_users(users_list)
        self.machine_obj_su_user = []

    def verify_ace_folder_permissions(self, test_directory, file_operations="all"):
        """verify NFS v4 ACEs for directory.

        Args:
            test_directory   (str)                   --  NFSv4 ACL supported mounted path

            file_operations  (list or dict or str)   --
                if file_operations == str, input should be 'all' | supported file operations
                    example: file_operations="read", file_operations="write"
                if file_operations == str, input should be list of supported file operations
                    example: file_operations=["read", "write", "append"]
                if file_operations == dict, input should be dictionary containing key as file
                operation and value as ACE to be used to verify the operation
                    example: file_operations={"read":'r', "write":w'}

                In case of dictionary user passed ACEs are used to verify the operations. In case
                of others, default ACEs will be used for each operations

        Returns:
            None

        Raises:
            Exception(Exception_Message):
                in case of any failures in the test

        """

        usage = "verify_ace_folder_permissions(test_path, file_operations=list(file_operations)" \
                " or file_operations=dict(file_operation:acl_permissions)" \
                " or file_operations='all'"

        permissions_to_test, ace_folder_permissions = self.read_permissions_inputs(
            file_operations,
            usage,
            test_type="folder")

        # generate user string for test
        random_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
        users_list = [(self.ace_user_string + '-' + random_string + '-' + str(i)) for i in range(2)]
        self.create_users_machine_objs(users_list)

        test_path = self.machine_obj.join_path(test_directory,
                                               "testaclfolder")
        self.log.info("test path to be used for ACL %s", test_path)

        for ace_permission in permissions_to_test:
            for action in [self.ace_allow, self.ace_deny]:
                ace_type_string = 'allow' if action == self.ace_allow else 'deny'

                self.log.info('=' * self.width)
                self.log.info("verifying ACL for %s %s on directory" % (ace_type_string,
                                                                        ace_permission))

                self.log.info("%s creating test directory %s" % (
                    self.machine_obj_su_user[0],
                    test_path))
                self.machine_obj_su_user[0].create_directory(test_path, force_create=True)

                self.log.info("validate file permissions before adding ACLs")
                self.validate_user_folder_permission(action,
                                                     self.machine_obj_su_user[1],
                                                     ace_permission,
                                                     test_path,
                                                     valiadate_before_acl=True)

                self.log.info("apply ACL for %s %s operation" % (ace_type_string,
                                                                 ace_permission))
                self.machine_obj.nfs4_setfacl(test_path,
                                              action,
                                              users_list[1],
                                              ace_folder_permissions[ace_permission])

                # now let's test other user have got required permissions
                self.log.info("validate file permissions after adding ACLs")
                self.validate_user_folder_permission(action,
                                                     self.machine_obj_su_user[1],
                                                     ace_permission,
                                                     test_path)

                self.log.info("validation of ACL folder permission %s %s was"
                              " successful" % (ace_type_string, ace_permission))

                self.log.info("remove directory %s", test_path)
                self.machine_obj.remove_directory(test_path)
                self.log.info('=' * self.width)
        self.machine_obj.delete_users(users_list)
        self.machine_obj_su_user = []
