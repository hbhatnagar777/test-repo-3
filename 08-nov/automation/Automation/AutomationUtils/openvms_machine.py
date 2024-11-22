# -*- coding: utf-8 -*-
# pylint: disable=W0703

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing operations on a machine / computer with OpenVMS Operating System.

This file consists of a class named: OpenVMSMachine, which can connect to the proxy remote machine
associated with the OpenVMS client, using CVD, if it is a Commvault Client, or using UNIX Shell, otherwise.

Since in OpenVMS, we cannot directly execute shell script on OpenVMS, we first mount the OpenVMS test path
onto the associated proxy client. Finally, we execute the shell scripts or commands to generate data,
verify data or related tasks on the proxy client at the mount location. Hence, the OpenVMS machine class
serves the following two purposes:

    #.  Mapping OpenVMS test path to the path on proxy where the test path is mounted.
    #.  Modify / bypass commands which cannot or should not be executed on the proxy client mounted path.

The instance of this class can be used to perform various operations on a machine, like,

    #.  Generating test data
    #.  Modifying test data
    #.  Get the list of items at the given path
    #.  Remove an existing Directory
    #.  Rename a File / Folder

OpenVMSMachine
===========

    __init__()                      --  initialize object of the class

    get_uname_output()              --  Gets the uname output from the machine

    generate_test_data()            --  generates and adds random testdata on the specified path

    modify_test_data()              --  Modifies the test data at the given path

    get_items_list()                --  Gets the list of items at the given path

    remove_directory()              --  removes a directory on a remote client

    rename_file_or_folder()         --  renames a file / folder on a remote client

Attributes
----------

    **proxy_name**                  --  name of the proxy associated with the OpenVMS client

"""

from .unix_machine import UnixMachine
from .constants import VMS_UNIX_MOUNT_PATH


class OpenVMSMachine(UnixMachine):
    """Class for performing operations on an OpenVMS OS remote client."""

    def __init__(self, machine_name=None, commcell_object=None, username=None, password=None):
        """Initializes instance of the Machine class. Since, in OpenVMS, all the commands and scripts
        are executed on the proxy client rather than the OpenVMS machine directly, the machine object
        is initialized with the proxy name although the OS flavor is set to OpenVMS.

            Args:
                machine_name        (str)       --  name / ip address of the client to connect to

                    if machine name is not provided, then the Machine object for the local machine
                    will be created

                    default:    None

                commcell_object     (object)    --  instance of the Commcell class from CVPySDK

                    default:    None

                username            (str)       --  username for the client to connect to

                        Only Applicable if the client is not a Commvault Client

                    default:    None

                password            (str)       --  password for the above specified user

                    default:    None
        """
        super(OpenVMSMachine, self).__init__(machine_name, commcell_object, username, password)
        self.proxy_name = self.client_object._properties['pseudoClientInfo']['openVMSProperties']['proxyClient'][
            'clientName']
        assert self.proxy_name is not None, "Proxy name should be initialized"
        super(OpenVMSMachine, self).__init__(self.proxy_name, commcell_object, username, password)
        assert self._os_flavour == 'OpenVMS', "OpenVMS machine class used for non-OpenVMS device"

    def get_uname_output(self, options="-s"):
        """Gets the uname output from the machine. Since we execute the
        commands on the proxy rather than on clients itself, instead of
        executing uname command

            Args:
                options     (str)   --  options to uname command
                    default: "-s"
            Returns:
                (str)               --   uname output

            Raises:
                Exception:
                    if any error occurred while getting the uname output.
        """
        return "OpenVMS"

    def generate_test_data(
            self,
            file_path,
            **kwargs):
        """Generates and adds random test data
            at the given path with the specified options

        Args:
            file_path           (str)   --  directory path where
                                            the data will be generated.

            dirs                (int)   --  number of directories
                                            in each level

                default: 3

            files               (int)   --  number of files
                                            in each directory

                default: 5

            file_size           (int)   --  Size of the files in KB

                default: 20

            levels              (int)   --  number of levels to be created

                default: 1

            hlinks              (bool)  --  whether to create
                                            hardlink files

                default: True

            slinks              (bool)  --  whether to create
                                            symbolic link files

                default: True

            sparse              (bool)  --  whether to create sparse files

                default: True

            sparse_hole_size    (int)   --  Size of the holes
                                            in sparse files in KB

                default: 1024

            long_path           (bool)  --  whether to create long files

                default: False

            long_level          (int)   --  length of the long path

                default: 1500

            acls                (bool)  --  whether to create
                                            files with acls

                default: False

            unicode             (bool)  --  whether to create
                                            unicode files

                default: False

            problematic         (bool)  --  whether to create
                                            problematic data

                default: False

            xattr               (bool)  --  whether to create files
                                            with xattr

                default: False

            options             (str)   --  to specify any other
                                            additional parameters
                                            to the script.

                default: ""

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while generating the test data.

        """
        file_path = file_path.replace(self.test_path, VMS_UNIX_MOUNT_PATH)
        return super(OpenVMSMachine, self).generate_test_data(file_path, **kwargs)

    def modify_test_data(
            self,
            data_path,
            **kwargs):
        """Modifies the test data at the given path
            based on the specified options

        Args:
            data_path   (str)   --  directory path where
                                    dataset resides.

            rename              (bool)  --  whether to rename all files

                default: False

            modify              (bool)  --  whether to modify

                                            data of all files
                default: False

            hlinks              (bool)  --  whether to add hard link
                                            to all files

                default: False

            permissions         (bool)  --  whether to change permission
                                            of all files

                default: False

            slinks              (bool)  --  whether to add symbolic link
                                            to all files

                default: False

            acls                (bool)  --  whether to change
                                            acls of all files

                default: False

            xattr               (bool)  --  whether to change
                                            xattr of all files

                default: False

            options             (str)   --  to specify any other
                                            additional parameters
                                            to the script.

                default: ""

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while modifying the test data.

        """
        data_path = data_path.replace(self.test_path, VMS_UNIX_MOUNT_PATH)
        return super(OpenVMSMachine, self).modify_test_data(data_path, **kwargs)

    def get_items_list(
            self,
            data_path,
            **kwargs):
        """Gets the list of items at the given path.

            Args:
                data_path       (str)   : directory path to get the items list

                sorted_output   (bool)  : to specify whether the list should be sorted.
                    default: True

                include_parents (bool)  : to specify whether parent paths should be include
                    default: False

            Returns:
                list : list of the items

            Raises:
                Exception:
                    if any error occurred while getting the items list.
        """
        data_path = data_path.replace(self.test_path, VMS_UNIX_MOUNT_PATH)
        output_list = super(OpenVMSMachine, self).get_items_list(data_path, **kwargs)
        output_list[:] = [path.replace(VMS_UNIX_MOUNT_PATH, self.test_path) for path in output_list]
        while '/' in output_list:
            output_list.remove('/')
        return output_list

    def remove_directory(
            self,
            directory_name,
            **kwargs):
        """Removes a directory on the client.
            If days is specified then directories older than given days
            will be cleaned up

        Args:
            directory_name  (str)   --  name / full path of the directory to remove

            days            (int)   --  dirs older than the given days will be cleaned up

                default: None

        Returns:
            None    -   if directory was removed successfully

        Raises:
            Exception:
                if any error occurred during cleanup

        """
        directory_name = directory_name.replace(self.test_path, VMS_UNIX_MOUNT_PATH)
        return super(OpenVMSMachine, self).remove_directory(directory_name, **kwargs)

    def rename_file_or_folder(self, old_name, new_name):
        """Renames a file or a folder on the client.

        Args:
            old_name    (str)   --  name / full path of the directory to rename

            new_name    (str)   --  new name / full path of the directory

        Returns:
            None    -   if the file or folder was renamed successfully

        Raises:
            Exception:
                if failed to rename the file or folder

        """
        old_name = old_name.replace(self.test_path, VMS_UNIX_MOUNT_PATH)
        new_name = new_name.replace(self.test_path, VMS_UNIX_MOUNT_PATH)

        output = self.execute('cp -r {0} {1}'.format(old_name, new_name))
        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        output = self.execute('rm -rf {0}'.format(old_name))
        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        return output.formatted_output == ''
