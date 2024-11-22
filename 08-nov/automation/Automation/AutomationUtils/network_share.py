# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ?2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for handling operations on network shared drives

NetworkShare, CIFSShare and NFSShare are teh classes defined in this file

NetworkShare: Base class including common operations on network shares

CIFSShare: Class for performing operations on cifs shares

NFSShare: Class for performing operations on nfs shares

NetworkShare:

    __init__()                  --  initializes network share object

    compare()                   --  compares two network share objects

    compare_network_paths()     --  compares network paths on same machine

    mount_path()                --  mounts network path on controller machine

    unmount_path()              --  dis mounts network path from controller machine
"""""

import random
import string

from .machine import Machine

class NetworkShare(object):
    """Base class to handle network shared drives"""

    def __init__(self, network_share_machine, username, password, domain):
        """Initialize Network share object

            Takes network share machine authentication details
        """
        self._network_share_machine = network_share_machine
        self._username = username
        self._password = password
        self._domain = domain

        # get local machine object
        import socket
        local_machine = socket.gethostname()

        self._local_machine = Machine(local_machine)

    def compare(self, network_share_obj, source_path, destination_path, ignore_files=[]):
        """Compares the two network directories

            Args:
                network_share_obj           (object)    --  NetworkShare subclass object

                source_path                 (str)       --  source path on this machine

                destination_path            (str)       --  destination path on remote machine

                ignore_files                (list)      --  list of files/patterns to be ignored
                    default: []

            Returns:
                list -  list of file paths if any are difference exists else []

            Raises:
                Exception:
                    if source_path does not exist

                    if destination_path does not exist
        """
        source_mount_path = self.mount_path(source_path)
        destination_mount_path = network_share_obj.mount_path(destination_path)

        diff = self._local_machine.compare_folders(
            self._local_machine, source_mount_path, destination_mount_path, ignore_files
        )

        self.unmount_path(source_mount_path)
        network_share_obj.unmount_path(destination_mount_path)

        return diff

    def compare_network_paths(self, source_path, destination_path, ignore_files=[]):
        """Compares the two network paths

            Args:
                source_path           (str)         --  source network share path

                destination_path      (str)         --  destination network share path

                ignore_files          (list)        --  list of files/patterns to be ignored
                    default: []

            Returns:
                list -  list of file paths if any are difference exists else []
        """
        source_mount_path = self.mount_path(source_path)
        destination_mount_path = self.mount_path(destination_path)

        diff = self._local_machine.compare_folders(
            self._local_machine, source_mount_path, destination_mount_path, ignore_files
        )

        self.unmount_path(source_mount_path)
        self.unmount_path(destination_mount_path)

        return diff

    def mount_path(self, path):
        """Mounts the specified path on controller machine

            Args:
                path    (str)   --  path/volume name to be mounted

            Returns:
                mounted drive letter if controller is windows

                mounted path if controller is unix
        """
        unc_path = self._get_unc_path(path)

        if self._local_machine.os_info == "WINDOWS":
            return self._mount_on_windows(unc_path)
        else:
            mount_cmd = self._get_mount_cmd()

            # Create the mount directory
            random_string = "".join([random.choice(string.ascii_letters) for _ in range(4)])
            mount_path = "/mount" + random_string

            self._local_machine.create_directory(mount_path)

            # Mount the network path
            mount_path_cmd = mount_cmd.format(self._username, self._password, self._domain,
                                              unc_path, mount_path)

            output = self._local_machine.execute_command(mount_path_cmd)

            if output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)

        return mount_path

    def unmount_path(self, mount_path):
        """Dis mounts the network share path from controller machine"""
        if self._local_machine.os_info == "WINDOWS":
            return self._local_machine.unmount_drive(mount_path)
        else:
            return self._local_machine.unmount_path(mount_path)


class CIFSShare(NetworkShare):
    """Helper class to handle cifs shares"""

    def _get_mount_cmd(self):
        """Returns the mount command to mount CIFS share on unix machine"""
        return r'mount -t cifs -o username={0},password={1},domain={2} "{3}" {4}'

    def _mount_on_windows(self, network_path):
        """Mounts the network path on windows machine"""
        return self._local_machine.mount_network_path(
            network_path, self._domain + "\\" + self._username, self._password
        )

    def _get_unc_path(self, path):
        """Returns the network share path"""
        if self._local_machine.os_info == "WINDOWS":
            path = path.replace(':', '$')
            return r'\\{0}\{1}'.format(self._network_share_machine, path)
        else:
            path = path.replace(':', '$').replace('\\', '/')
            return r'//{0}/{1}'.format(self._network_share_machine, path)


class NFSShare(NetworkShare):
    """Helper class to handle nfs shares"""

    def _get_mount_cmd(self):
        """Returns the mount command to mount NFS share on unix machine"""
        return r'mount -t nfs -o username={0},password={1},domain={2} "{3}" {4}'

    def _get_unc_path(self, path):
        """Returns the network share path"""
        return path

    def _mount_on_windows(self, network_path):
        """Mounts the network path on windows machine"""
        raise Exception("NFS mount on windows is not supported.")
