# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for managing operations on nas filer

An object of NASClient will be returned for each nas filer.

NASClient, NetAPPClusterClient, NetAPPClient, Volume, IsilonClient, HuaweiClient, NutanixClient
UnityVnxCelerraClient,and HNASClient are 8 classes defined in this file

NASClient: Base class for any NAS Client

NetAPPClusterClient: Class to perform operations on NetAPP cluster filer

NetAPPClient: Class to perform operations on NetAPP filer

Volume: Class to perform operations on Volume

IsilonClient: Class to perform operations on Isilon Filer

HuaweiClient: Class to perform operations on Huawei filer

UnityVnxCelerraClient: Class to perform operations on Unity/ Celerra/ VNX Clients

HNASClient: Class to perform operation on HNAS filer

NutanixClient : Class to perform operations on Nutanix filer

NASClient:
    __init__()               --  initialize nas filer object

    _get_folder_hash()       --  returns the hash value generated for folder

    _get_file_hash()         --   returns the hash value generated for files

    remove_folder()          --  removed the folder at network location

    exec_command()           --  executes the command remotely

    get_volumes_by_pattern() -- returns list of volumes which match a pattern

    copy_folder()            --  copies the source folder to specified destination path

    get_restore_volume()     --   returns the volume name hat can be used for restore

    connect_to_cifs_share()  --  connect to CIFS share with credentials

    compare_volumes()        --  compares the content on two volumes of same filer

    compare_folders()        --  compares the content on 2 different machines (Windows/Unix/Filer)

    compare_files()          --   compares the files on 2 different machines (Windows/Unix/Filer)

    get_content_size()       --  returns the storage size for the specified volume path

    get_fs_from_path_fsnas() -- returns the file system name from path

NetappClusterClient:
    __init__()              --  initialize Netapp Cluster client object

    _get_used_space()       --  returns used space details of volume

    get_content_size()      --  returns total size of a content

    get_vserver_ip()        --  gets the interface ip from vserver name

    get_path_from_content() --  generates cifs path from content path

NetAPPClient:
    __init__()              --  initialize NetApp client object

    _get_volumes()          --  gets the list of volumes on file server

    has_volume()            --  verifies whether volume exists on file server and is online

    get_content_size()      --  returns total size of a content

    get_volume()            --  returns volume class object for given volume name

    get_path_from_content() --  generates cifs path from content path

Volume:
    __init__()           --  initializes the volume object for specified filer

    _get_usage_details() --  populates memory usage details of volume

    restrict()      --  restricts this volume

    status()        --  returns the status of this volume

    online()        --  process the volume to make online

    snap_list()     --  returns the list of snaps associated with this volume

    has_snap()      --  checks if snap with specified name exists on this volume

    create_snap()   --  creates the snap with specified name

    delete_snap()   --  deletes the snap with specified name

IsilonClient:
    __init__()              --  initialize Isilon client class

    get_path_from_content() --  generates cifs path from content path

HuaweiClient:
    __init__()              --  initialize Huawei client class

    get_fsid_from_path()    --  returns file system id from content path

    get_fsname_from_fsid()  --  returns file system name fromfile system ID

    get_path_from_content() --  generates cifs path from content path

UnityVnxCelerraClient:
    __init__()              --   initialize Unity/VNX/Celerra client class

    get_path_from_content   --   generates cifs path from content path
	
VNXCelerraVDMClient:
    __init__()              --   initialize Unity/VNX/Celerra VDM client class

    get_path_from_content   --   generates cifs path from content path

HNASClient:
    __init__()             --   initialize HNAS client class

    get_path_from_content  --   generates cifs path from content path

NutanixClient:
    __init__()              --  initialize Nutanix client class

    get_path_from_content() --  generates cifs path from content path

"""

import re
import os
import time
import shutil

from AutomationUtils import logger
from AutomationUtils.pyping import ping
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine


class NASClient(UnixMachine):
    """Helper class to connect to nas client"""

    def __new__(cls, filer_name, commcell_object, agent_obj, username, password, controlhost=None):
        """Returns the instance of one of the Subclasses NASClient,
            based on the instance of the class.

            Pings the filer and make sure it is accessible

            If we get TTL value it means machine is pingable
        """
        response = ping(filer_name)
        # Extract TTL value form the response.output string.
        try:
            int(re.match(r"(.*)ttl=(\d*) .*", response.output[2]).group(2))
        except AttributeError:
            raise Exception(
                'Failed to connect to the machine.\nError: "{0}"'.format(response.output)
            )

        return object.__new__(cls)

    def __init__(self, filer_name, commcell_object, agent_obj, username, password):
        """Initializes the filer client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --    python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected
        """
        UnixMachine.__init__(self, filer_name, commcell_object, username, password)
        self._filer_name = filer_name
        self._cifs_access = False

        self._login_with_credentials()

        # create logger object
        self._log = logger.get_log()

        # get local machine object
        import socket
        local_machine = socket.gethostname()
        self._agent = agent_obj.agent_name
        self._local_machine = Machine(local_machine, commcell_object)

    def _get_folder_hash(self, content, ignore_folder=None, ignore_case=False, algorithm="MD5"):
        """Returns the set of volume paths and its hash value

            Args:
                content     (str)   --  content for which the folder hash is to be calculated

                ignore_folder       (list)  --  list of folders to be ignored.
                Default: None.

              ignore_case         (bool)  --  ignores the case if set to True.
                Default: False.

              algorithm           (str)   --  Specifies the cryptographic hash function
                    to use for computing the hash value of the contents.

                Default: "MD5"

              The acceptable values for algorithm parameter are:
                 * SHA1
                 * SHA256
                 * SHA384
                 * SHA512
                 * MD5

            Returns:
                set of file paths and their hash value

            Raises:
                Exception:
                    if CIFS share is not connected
        """
        if not self._cifs_access:
            raise Exception(
                "CIFS share is not connected. "
                "Please connect it by calling connect_to_cifs_share().")
        volume_path, _ = self.get_path_from_content(content)
        mount_drive = self._local_machine.mount_network_path(
            volume_path, self._cifs_username, self._cifs_password
        )
        hash_value = self._local_machine._get_folder_hash(mount_drive, ignore_folder)

        self._local_machine.unmount_drive(mount_drive)

        return hash_value

    def _get_file_hash(self,
                       content,
                       ignore_folder=None,
                       ignore_case=False,
                       algorithm="MD5",
                       files=None):
        """Returns the set of volume paths and its hash value

            Args:
                content     (str)   --  content for which the folder hash is to be calculated

                ignore_folder       (list)  --  list of folders to be ignored.
                Default: None.

              ignore_case         (bool)  --  ignores the case if set to True.
                Default: False.

              algorithm           (str)   --  Specifies the cryptographic hash function
                    to use for computing the hash value of the contents.

                Default: "MD5"

              The acceptable values for algorithm parameter are:
                 * SHA1
                 * SHA256
                 * SHA384
                 * SHA512
                 * MD5

            Returns:
                set of file paths and their hash value

            Raises:
                Exception:
                    if CIFS share is not connected
        """
        if not self._cifs_access:
            raise Exception(
                "CIFS share is not connected. "
                "Please connect it by calling connect_to_cifs_share().")
        volume_path, volname = self.get_path_from_content(content, files=files)
        mount_drive = self._local_machine.mount_network_path(
            volume_path, self._cifs_username, self._cifs_password
        )
        filepath = mount_drive+":\\"+volname[1]
        self._log.info("File path is %s", filepath)
        hash_value = self._local_machine._get_file_hash(filepath)

        if self._local_machine.os_info == "WINDOWS":
            self._local_machine.unmount_drive(mount_drive)
        elif self._local_machine.os_info == "UNIX":
            self._local_machine.unmount_path(mount_drive)

        return hash_value

    def remove_folder(self, volume_path):
        shutil.rmtree(volume_path, ignore_errors=True)

    def exec_command(self, command):
        """Executes commands on filer"""
        try:
            self._login_with_credentials()
            command = command.encode('utf8').strip()
            self._log.info("Running Command: " + str(command))
            _, stdout, stderr = self._client.exec_command(command)

            # Wait for the command to terminate
            while not stdout.channel.exit_status_ready() and not stdout.channel.recv_ready():
                time.sleep(1)

            out = stdout.readlines()
            err = stderr.readlines()
            self._client.close()
            return out, err
        except Exception as exp:
            raise Exception("Failed to execute command with error: {0}".format(str(exp)))

    def get_volumes_by_pattern(self, content):
        """Returns list of all volumes which match certain pattern

            Args:
                content     (str)   --  pattern which can be mapped with volumes on filer
                    Ex: /vol/My_Volume_*

            Returns:
                list of volumes that matches the pattern
        """
        self._log.info("Determine the volumes list for %s pattern", content)
        volumes_list = []

        for vol in self.volumes:
            _, pattern = self.get_path_from_content(content)
            if pattern.replace("*", "") in vol:
                volumes_list.append(vol)

        self._log.info("Volumes list from pattern: %s", str(volumes_list))

        return volumes_list

    def copy_folder(self, source_path, volume_path):
        """Copies the source folder content to the specified volume path

            Args:
                source_path     (str)   --  source folder path

                volume_path     (str)   --  destination volume path
        """
        if not self._cifs_access:
            raise Exception(
                "CIFS share is not connected. "
                "Please connect it by calling connect_to_cifs_share().")
        self._local_machine.copy_folder_to_network_share(
            source_path, volume_path, self._cifs_username, self._cifs_password
        )

    def get_restore_volume(self, size=20480):
        """Returns the volume name that can be used in restore job

            Args:
                size    (int)   --  min size in MB that should be available on volume to be
                                        selected for restore job
                    default: 20480

        """
        command = 'df -m'
        out, err = self.exec_command(command)

        if err != []:
            raise Exception(
                "Failed to get available space on all volumes with error: {0}".format(
                    str(err)))

        out = out[1:]

        vol_dict = {}

        for vol in out:
            vol = ' '.join(vol.strip().split())
            vol = vol.split(" ")
            if '/.snapshot' in vol[0]:
                continue
            vol_dict[vol[0]] = vol[3].replace("MB", "")

        for vol in self.volumes:
            vol = "/vol/{0}/".format(vol)
            if vol in vol_dict.keys():
                if int(vol_dict[vol]) >= size:
                    return vol

        raise Exception(
            "Failed to get restore volume. "
            "Please check if enough space is avaialble on any of your volume"
        )

    def connect_to_cifs_share(self, username, password):
        """Sets the connection parameters to connect to cifs share

            Args:
                username    (str)   --  name of the user which should be used to make a
                                            cifs share connection

                password    (str)   --  asscoiated authentication string for the specified user

        """
        self._cifs_username = username
        self._cifs_password = password
        self._cifs_access = True

    def compare_volumes(self, source_volume, destination_volume, ignore_files=[]):
        """Compares the two volumes on this filer

            Args:
                source_volume           (str)    --  source volume on this filer

                destination_volume      (str)       --  destination volume on this filer

                ignore_files            (list)      --  list of files/patterns to be ignored
                    default: []

            Returns:
                list -  list of file paths if any are difference exists else []

            Raises:
                Exception:
                    if cifs share credentials are not specified
        """
        if not self._cifs_access:
            raise Exception("CIFS share is not connected."
                            "Please connect it by calling connect_to_cifs_share().")

        source_path = os.path.join("\\\\" + self._filer_name, source_volume)
        destination_path = os.path.join("\\\\" + self._filer_name, destination_volume)

        source_drive = self._local_machine.mount_network_path(
            source_path, self._cifs_username, self._cifs_password
        )

        destination_drive = self._local_machine.mount_network_path(
            destination_path, self._cifs_username, self._cifs_password
        )

        return self._local_machine.compare_folders(
            self._local_machine, source_drive, destination_drive, ignore_files
        )

    def compare_folders(self, destination_machine, content, destination_path, ignore_files=[]):
        """Compares the two directories on different machines

            Args:
                destination_machine     (object)    --  Machine class object for destination
                                                            machine

                content                 (str)       --  subclient content path

                destination_path        (str)       --  path on destination machine that is to be
                                                            compared

                ignore_files            (list)      --  list of files/patterns to be ignored
                    default: []

            Returns:
                list -  list of file paths if any are difference exists else []

            Raises:
                Exception:
                    if source_path does not exist

                    if destination_path does not exist
        """
        self._log.info(f"Comparing folders: {content} and {destination_path} on machine : {destination_machine}")
        source_hash = self._get_folder_hash(content, ignore_files)
        destination_hash = destination_machine._get_folder_hash(destination_path, ignore_files)

        difference = source_hash - destination_hash

        if bool(difference):
            return destination_machine._validate_ignore_files(
                dict(difference).keys(), ignore_files
            )

        return []

    def compare_files(self, destination_machine, content, destination_path, files=None):
        """Compares the two directories on different machines

            Args:
                destination_machine     (object)    --  Machine class object for destination
                                                            machine

                content                 (str)       --  subclient content path

                destination_path        (str)       --  path on destination machine that is to be
                                                            compared

                ignore_files            (list)      --  list of files/patterns to be ignored
                    default: []

            Returns:
                list -  list of file paths if any are difference exists else []

            Raises:
                Exception:
                    if source_path does not exist

                    if destination_path does not exist
        """
        source_hash = self._get_file_hash(content, files=files)
        destination_hash = destination_machine._get_file_hash(destination_path)
        difference = (source_hash == destination_hash)

        if difference:
            return []
        else:
            return [content]

    def get_content_size(self, contents):
        """Returns the total size in MB for specified content

            Args:
                contents    (list)  -- subclient content list

            Returns:
                total size of specified contents
        """
        self._log.info("Get subclient content size")

        if not self._cifs_access:
            raise Exception("CIFS share is not connected."
                            "Please connect it by calling connect_to_cifs_share().")

        size = 0
        for content in contents:
            volume_path, _ = self.get_path_from_content(content)
            mount_drive = self._local_machine.mount_network_path(
                volume_path, self._cifs_username, self._cifs_password
            )

            size += self._local_machine.get_folder_size(mount_drive)

            self._local_machine.unmount_drive(mount_drive)

        size = size + 200
        self._log.info("Obtained subclient size: %d", size)
        return size

    def get_fs_from_path_fsnas(self, content):
        """Returns fs name from subclient content path (applicable for FS under NAS)

            Args:
                content  (str)
        """
        fsname = content.split('\\')[3]
        return fsname

class NetAPPClusterClient(NASClient):
    """Class to represent NetAPPClusterClient"""

    def __init__(self, filer_name, commcell_object, agent_obj, username, password,
                 controlhost=None):
        """Initializes the netapp cluster client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --    python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

        """
        NASClient.__init__(self, filer_name, commcell_object, agent_obj, username, password)
        self._is_cluster = True

    def _get_used_space(self, volume, vserver):
        """Returns the available space on the volume

            Args:
                volume      (str)   --  name of the volume on specified vserver for which the
                                            used space is to be computed

                vserver     (str)   --  name of the vserver on which the specified volume
                                            is mounted

            Returns:
                int     -   total used space by contents on volume

            Raises:
                Exception:
                    if failed to get used space on specified volume

        """
        command = "volume show -vserver {0} -volume {1} -fields used".format(vserver, volume)

        out, err = self.exec_command(command)

        if err != []:
            raise Exception(
                "Failed to get used space on volume {0} with error: {1}".format(volume, str(err))
            )

        out = out[2:]

        for row in out:
            row = row.strip().split(" ")
            if volume in row[1]:
                if "MB" in row[2]:
                    return float(row[2].replace("MB", ""))
                elif "GB" in row[2]:
                    return float(row[2].replace("GB", "")) * 1000

    def get_content_size(self, contents):
        """Returns the total size in MB for specified content

            Args:
                contents    (list)  -- subclient content list

            Returns:
                int     -   total size of specified contents

        """
        self._log.info("Get subclient content size")

        size = 0
        for content in contents:
            content = content.split('/')
            vserver = content[1]
            volume = content[2]
            size += self._get_used_space(volume, vserver)

        size = size + 200
        self._log.info("Obtained subclient size: %d", size)
        return size

    def get_vserver_ip(self, vserver_name):
        """Returns the vserver ip of specified vserver name

            Args:
                vserver_name    (str)   --  name of the vserver whose ip is to be determined

            Returns:
                str     -   ip of the specified vserver

        """
        command = "network interface show -data-protocol cifs -vserver {0} \
                    -status-admin up -fields Address".format(vserver_name)
        out, err = self.exec_command(command)

        if err != []:
            raise Exception("Failed to get vserver ip with error: {0}".format(str(err)))

        out = out[-2].strip().split(" ")

        return str(out[2])

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        content = content.strip("/").split("/")
        vserver_name, volume_name = content[0].strip(), content[1]
        vserver_ip = self.get_vserver_ip(vserver_name)
        return r"\\{0}\{1}".format(vserver_ip, "\\".join(content[1:])), content[-1]

class NetAPPClient(NASClient):
    """Class to represent NetAPPClient"""

    def __init__(self, filer_name, commcell_object, agent_obj, username, password,
                 controlhost=None):
        """Initializes the netapp client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --    python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

        """
        NASClient.__init__(self, filer_name, commcell_object, agent_obj, username, password)
        self._volumes = self._get_volumes()

    def _get_volumes(self):
        """Returns list of volumes on filer"""
        command = 'vol status'

        out, err = self.exec_command(command)

        if err != []:
            raise Exception("Failed to get list of all volumes with error: {0}".format(str(err)))

        volumes_list = []

        out = out[1:]

        for vol in out:
            vol = vol.strip().split(" ")
            if len(vol) > 1:
                if str(vol[1]).lower() == "online":
                    volumes_list.append(str(vol[0]))

        return volumes_list

    @property
    def volumes(self):
        """Treats volumes as a read-only property"""
        return self._volumes

    def has_volume(self, volume_name):
        """Checks if volume with specififed name exists on filer

            Args:
                volume_name     (str)   --  name of the volume which is to be checked
                                                if exists on this filer

            Returns:
                True    -   if volume exist on this filer

                False   -   if volume does not exist on this filer

        """
        if volume_name in self.volumes:
            return True

        return False

    def get_content_size(self, contents):
        """Returns the total size in MB for specified content

            Args:
                contents    (list)  -- subclient content list

            Returns:
                total size of specified contents
        """
        self._log.info("Get subclient content size")

        size = 0
        for content in contents:
            volume = self.get_volume(content)
            size += volume.used_space
        self._log.info("Obtained subclient size: %d", size)
        size = size + 10
        return size

    def get_volume(self, volume_name):
        """Returns volume class object for specified volume name

            Args:
                volume_name     (str)   --  name of the volume for which the Volume object
                                                is to be created

            Returns:
                object  -   Volume class object for specified volume

            Raises:
                Exception:
                    if specified volume doesn't exist on this filer

        """
        if "/vol/" in volume_name:
            volume_name = volume_name.split('/')[2]
        if not self.has_volume(volume_name):
            raise Exception("Volume {0} doesn't exist".format(volume_name))

        return Volume(self, volume_name)

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            volume_name = content.replace("/", "\\").replace("\\vol\\", "")
            if files is None:
                return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
            elif files == 1:
                v1, v2 = r"\\{0}\{1}".format(self._filer_name, content.split('/')[2]), content.split('/')[-2:]
                self._log.info("path being returned is %s, %s", v1, v2)
                return v1, v2
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname

class Volume(object):
    """Class to manage volume level operations"""

    def __init__(self, filer_obj, volume_name):
        """Initializes Volume object

            Args:
                filer_obj       (object)    --  instance of the filer client class on which
                                                    this volume is present

                volume_name     (str)       --  name of the volume for which this
                                                    class object is initialized

        """
        self._filer_obj = filer_obj
        self._volume_name = volume_name
        self._log = logger.get_log()

    def _get_usage_details(self):
        """Populates the memory usage details for this volume"""
        self._log.info("Get the memory usage details of %s volume", self._volume_name)
        command = "df -m {0}".format(self._volume_name)

        output, error = self._filer_obj.exec_command(command)

        if error != []:
            raise Exception(
                "Failed to get {0} volume details with error: {1}".format(
                    self._volume_name, str(error)
                )
            )

        output = output[1:]

        for row in output:
            row = row.strip()
            row = re.sub(' +', ' ', row).split(" ")
            if ".snapshot" not in row[0] and self._volume_name in row[0]:
                return row

        raise Exception("Failed to get volume details")

    @property
    def available_space(self):
        """Returns the available space in MB on this volume"""
        output = self._get_usage_details()
        available_space = str(output[3]).replace("MB", "")
        return float(available_space)

    @property
    def used_space(self):
        """Returns the used space in MB by this volume"""
        output = self._get_usage_details()
        used_space = str(output[2]).replace("MB", "")
        return float(used_space)

    @property
    def total(self):
        """Returns the total space in MB on this volume"""
        output = self._get_usage_details()
        total_space = str(output[1]).replace("MB", "")
        return float(total_space)

    @property
    def name(self):
        """Treats the name as  a read-only property"""
        return self._volume_name

    def restrict(self):
        """Restricts this volume"""
        self._log.info("Restricting volume: %s", self._volume_name)
        command = "vol restrict /vol/{0}".format(self._volume_name)
        _, err = self._filer_obj.exec_command(command)

        if err != []:
            if "is already restricted" not in str(err[0]):
                raise Exception(
                    "Failed to restrict volume {0} with error: {1}".format(
                        self._volume_name, str(err)
                    )
                )

        self._log.info("Successfully restricted volume")

    @property
    def status(self):
        """Returns the status of his volume"""
        self._log.info("Retrieving status for volume: %s", self._volume_name)
        command = "vol status /vol/{0}".format(self._volume_name)
        out, err = self._filer_obj.exec_command(command)
        if err != []:
            raise Exception(
                "Failed to get status of volume {0} with error: {1}".format(
                    self._volume_name, str(err)))

        status = str(out[1]).strip().split(" ")[1].lower()

        self._log.info("%s is %s", self._volume_name, status)

        return status

    def online(self):
        """Turns ON the volume"""
        self._log.info("Turning %s volume on", self._volume_name)
        command = 'vol online /vol/{0})'.format(self._volume_name)
        out, err = self._filer_obj.exec_command(command)

        # Check if any error
        if err != []:
            if "is already online" not in str(err[0]):
                raise Exception(
                    "Failed to make volume : {0} online with error: {1}".format(
                        self._volume_name, str(err)
                    )
                )

        self._log.info("%s is now ONLINE", self._volume_name)

        return out

    @property
    def snaps_list(self):
        """Returns list of snaps for this volume"""
        self._log.info("Retrieving the snaps list for %s", self._volume_name)
        command = 'snap list {0}'.format(self._volume_name)
        out, err = self._filer_obj.exec_command(command)

        # check if snap is created
        if err != []:
            raise Exception(
                "Failed to list snap for volume: {0} with error: {1}".format(
                    self._volume_name, str(err)
                )
            )

        out = out[5:]

        snaps_list = []
        for row in out:
            snaps_list.append(str(row).strip().split(" ")[-1])

        self._log.info("Snaps on %s are %s", self._volume_name, str(snaps_list))

        return snaps_list

    def has_snap(self, snap_name):
        """Checks if a snap with given name exists on this volume

            Args:
                snap_name   (str)   --  name of the snap which has to be checked
                                            if is created for this volume

            Returns:
                True    -   if specified snap was created for this volume

                False   -   if specified snap was not created for this volume

        """
        if snap_name in self.snaps_list:
            return True

        return False

    def create_snap(self, snap_name):
        """Creates a snap with specified name

            Args:
                snap_name   (str)   --  name of the snap which is to be created on this volume

            Raises:
                Exception:
                    if a snap with specified name is already exists

                    if failed to create snap with specified snap name

        """
        self._log.info("Creating snap %s on %s", snap_name, self._volume_name)
        if self.has_snap(snap_name):
            raise Exception(
                "{0} snap already exists on {1} volume".format(snap_name, self._volume_name)
            )

        command = 'snap create {0} {1}'.format(self._volume_name, snap_name)
        _, err = self._filer_obj.exec_command(command)

        # check if snap is created
        if err != []:
            raise Exception(
                "Failed to create snap {0} with error: {1}".format(
                    snap_name, str(err)
                )
            )

        self._log.info("Successfully created %s snap", snap_name)

    def delete_snap(self, snap_name):
        """Deletes a snap with specified name

            Args:
                snap_name   (str)   --  name of the snap which is to be deleted on this volume

            Raises:
                Exception:
                    if a snap with specified name does not exist

                    if failed to delete snap with specified snap name

        """
        self._log.info("Deleting snap %s on %s}", snap_name, self._volume_name)
        if not self.has_snap(snap_name):
            raise Exception(
                "{0} snap doesn't exist on volume: {1}".format(snap_name, self._volume_name)
            )

        command = 'snap delete {0} {1}'.format(self._volume_name, snap_name)
        _, err = self._filer_obj.exec_command(command)

        # check if snap is created
        if err != []:
            raise Exception(
                "Failed to create snap {0} with error: {1}".format(snap_name, str(err))
            )

        self._log.info("Successfully deleted %s snap", snap_name)

class IsilonClient(NASClient):
    """Class to represent IsilonClient"""

    def __init__(self, filer_name, commcell_object, agent_obj, username, password, controlhost):

        """Initializes the Isilon client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

        """
        NASClient.__init__(self, controlhost, commcell_object, agent_obj, username, password)

        self._filer_name = filer_name
        self._cifs_access = False
        # create logger object
        self._log = logger.get_log()

        # get local machine object
        import socket
        local_machine = socket.gethostname()

        self._local_machine = Machine(local_machine, commcell_object)

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            volume_name = content.replace("/", "\\").replace("\\ifs\\", "")
            return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname

class HuaweiClient(NASClient):
    """Class to represent Huawei Client"""
    def __init__(self, filer_name, commcell_object, agent_obj, username, password, controlhost):
        """Initializes the Huawei client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

                controlhost         (str)           --  control host of the filer
        """
        NASClient.__init__(self, controlhost, commcell_object, agent_obj, username, password)
        self._filer_name = filer_name
        self._local_machine = Machine()

    def get_fsid_from_path(self, content):
        """Returns the FS ID from content path"""
        fsid = content.split('/')[1][2:]
        return fsid

    def get_fsname_from_fsid(self, fsid):
        """Returns the CIFS Share name from fs id"""
        command = ("show share cifs|filterRow column=File\sSystem\sID predict=match value={0}|"
                   "filterColumn include columnList=Name".format(fsid))
        out, err = self.exec_command(command)
        if err != []:
            raise Exception(
                "Failed to get fsname details with error: %s", (str(err))
            )
        return str(out[4].strip()
                  )

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            fsid = self.get_fsid_from_path(str(content))
            fsname = self.get_fsname_from_fsid(fsid)
            folderinfs = content.replace('/', '\\').replace('\\fs'+fsid, '')
            return r"\\{0}\{1}".format(self._filer_name, fsname+folderinfs), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname

class UnityVnxCelerraClient(NASClient):
    """Class to represent DELL Unity/ VNX/ Celerra Client"""
    def __init__(self, filer_name, commcell_object, agent_obj, username, password, controlhost):
        """Initializes the Unity/ VNX/ Celerra client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

                controlhost         (str)           --  control host of the file server
        """

        self._filer_name = filer_name
        self._cifs_access = False
        # create logger object
        self._log = logger.get_log()
        self._agent = agent_obj.agent_name
        # get local machine object
        import socket
        local_machine = socket.gethostname()

        self._local_machine = Machine(local_machine, commcell_object)

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            vol_name = content.replace("/", "", 1)
            volume_name = vol_name.replace("/", "\\")
            return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname

class VnxCelerraVDMClient(NASClient):
    """Class to represent DELL Unity/ VNX/ Celerra VDM Client"""
    def __init__(self, filer_name, commcell_object, agent_obj, username, password, controlhost):
        """Initializes the Unity/ VNX/ Celerra client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

                controlhost         (str)           --  control host of the file server
        """

        self._filer_name = filer_name
        self._cifs_access = False
        # create logger object
        self._log = logger.get_log()
        self._agent = agent_obj.agent_name
        # get local machine object
        import socket
        local_machine = socket.gethostname()

        self._local_machine = Machine(local_machine, commcell_object)

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """

        if self._agent.upper() == 'NDMP':
            vol_name = content.split("/")
            volume_name = "\\".join(vol_name[2:])
            return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname
			
class HNASClient(NASClient):
    """Class to represent BluearcClient"""
    def __init__(self, filer_name, commcell_object, agent_obj, username, password, controlhost):
        """Initializes the HNAS client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

        """
        NASClient.__init__(self, controlhost, commcell_object, agent_obj, username, password)
        self._filer_name = filer_name
        self._cifs_access = False
        # create logger object
        self._log = logger.get_log()

        # get local machine object
        import socket
        local_machine = socket.gethostname()

        self._local_machine = Machine(local_machine, commcell_object)

    def get_path_from_content(self, content, files=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            volume_name = content.replace("/", "\\").replace("\\__VOLUME__\\", "")
            return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname


class NutanixClient(NASClient):
    """Class to represent NutanixClient"""

    def __init__(self, filer_name:str, commcell_object:object, agent_obj:object, username:str, password:str):

        """Initializes the Nutanix client object

            Args:
                filer_name          (str)           --  name of filer to be connected

                commcell_object     (object)    --  python sdk commcell object

                username            (str)           --  name of the user which should be used to
                                                        make a connection to client

                password            (str)           --  password of filer to be connected

        """
        # NASClient.__init__(self, filer_name, commcell_object, agent_obj, username, password)
        self._agent = agent_obj.agent_name
        self._filer_name:str = filer_name
        self._cifs_access:bool = False
        # create logger object
        self._log = logger.get_log()

        # get local machine object
        import socket
        local_machine:str = socket.gethostname()
        self._local_machine = Machine(local_machine, commcell_object)

    def get_path_from_content(self, content:str, files:int|None=None):
        """Returns the CIFS Share path and volume name

            Args:
                content     (str)   --  volume path from the subclient content

                files       (int)   --  default None, for files, set the value to '1'

            Returns:
                (str, str)  -   cifs share path and path of the volume

        """
        if self._agent.upper() == 'NDMP':
            volume_name = content.replace("/", "\\").replace("\\ifs\\", "")
            return r"\\{0}\{1}".format(self._filer_name, volume_name), content.split('/')[-1]
        else:
            fsname = self.get_fs_from_path_fsnas(str(content))
            return content, fsname