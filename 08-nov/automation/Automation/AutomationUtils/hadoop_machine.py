# -*- coding: utf-8 -*-
# pylint: disable=W0223
# pylint: disable=W0221
# pylint: disable=R0913

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing Hadoop operations on a machine with Hadoop Client.

This file consists of a class named: HadoopMachine, which can connect to the Hadoop Cluster
and perform various Hadoop operations.

The instance of this class can be used to perform various operations on a Hadoop Cluster, like,

    #.  Generating test data on hdfs
    #.  Modifying test data on hdfs
    #.  Get information about the items on the given path on hdfs
    #.  Remove an existing Directory on hdfs

HadoopMachine
=============

    __init__()                           --  initialize object of the class

    run_kinit()                          --  Runs kinit for hdfs principal using keytab file for kerberos cluster

    run_kdestroy()                       --  Runs kdestroy command to delete kerberos cache for kerberos cluster

    generate_test_data()                 --  generates and adds random testdata on the specified path

    modify_test_data()                   --  Modifies the test data at the given path

    get_test_data_info()                 --  Gets information about the items on the given path

    get_items_list()                     --  Gets the list of items at the given path

    remove_directory()                   --  Removes a directory on the hadoop client.

    create_directory()                   --  Creates a directory on the hadoop client.

    fetch_snapshots()                    --  Returns snapshots in given hdfs locations

    remove_snapshots()                   --  Removes snapshots in given hdfs locations

"""

import os
from .unix_machine import UnixMachine
from .constants import UNIX_TMP_DIR
from .constants import HADOOP_MANAGE_DATA


class HadoopMachine(UnixMachine):
    """Class for performing operations on a UNIX OS remote Hadoop client."""

    def __init__(self,
                 hdfs_user,
                 machine_name,
                 commcell_object=None,
                 username=None,
                 password=None,
                 keytab_file=None,
                 **kwargs):
        """Initializes instance of the HadoopMachine class.

        Args:
            hdfs_user           (str)       --  hadoop username for the client to connect to hadoop

            machine_name        (str)       --  name / ip address of the client to connect to

            commcell_object     (object)    --  instance of the Commcell class from CVPySDK

                default:    None

            username            (str)       --  username for the client to connect to

                    Only Applicable if the client is not a Commvault Client

                default:    None

            password            (str)       --  password for the above specified user

                default:    None

            keytab_file         (str)       --  absolute path for the keytab file to be used for kinit

                default:    None, Raise exception if None is specified for a kerberos enabled cluster

            kwargs              (dict)      -- dictionary of acceptable key-worded arguments
                key_filename        (str/list)  --  string or list containing ppk key location(s) for

                        machines that require a private key for SSH

                    default:    None

                run_as_sudo         (bool)      --  variable for running commands as sudo for machines

                        where root login is disabled

                    default:    False

        Also, initializes the Client object, if it is Commvault Client.

        Otherwise, it creates a paramiko SSH client object for the client.

        """
        super(HadoopMachine, self).__init__(machine_name, commcell_object, username, password, **kwargs)
        self._hdfs_user = hdfs_user
        self._jar_path = self.join_path(UNIX_TMP_DIR, os.path.basename(HADOOP_MANAGE_DATA))
        super(HadoopMachine, self).remove_directory(self._jar_path)
        self.copy_from_local(HADOOP_MANAGE_DATA, UNIX_TMP_DIR)
        self.keytab_file = keytab_file
        self.is_kerberos_cluster = None

    def __is_kerberos_cached(self):
        """Determines if kerberos cache is present or not

        Returns:
            bool    -   boolean value True is returned if kerberos cache is present.
        """
        kcache_cmd = f"sudo -u {self._hdfs_user} klist -s"
        kcache = self.execute(kcache_cmd)
        if kcache.exit_code == 0:
            return True
        else:
            return False

    def _execute_jar(self, script_arguments=""):
        """Execute the hadoop jar file with given arguments

        Args:
            script_arguments       (str)             --  Arguments to the hadoop jar file

        """
        java_command = """
        export CLASSPATH=`hadoop classpath --glob`;
        java -cp $CLASSPATH:{0} com.cv_hadoop.cv_hdfs_manage_data.ManageHadoopData {1} -user {2} 2>/dev/null
        """.format(self._jar_path, script_arguments, self._hdfs_user)
        return self.execute(java_command)

    def run_kinit(self, keytab_file=None):
        """Runs kinit for hdfs principal using keytab file for kerberos cluster

        Args:
            keytab_file         (str)       --  absolute path for the keytab file to be used for kinit

                default:    None, uses keytab file specified during class initialisation

        Raises:
            Exception:
                if any error occurred while running kinit.
        """
        if self.is_kerberos_cluster is None:
            is_kerberos_cmd = "hdfs getconf -confkey hadoop.security.authentication"
            is_kerberos = self.execute(is_kerberos_cmd)
            if is_kerberos.exit_code == 0 and is_kerberos.output.lower() == "kerberos":
                self.is_kerberos_cluster = True
            else:
                self.is_kerberos_cluster = False
        if self.is_kerberos_cluster:
            keytab_file = keytab_file or self.keytab_file
            if keytab_file is None:
                raise Exception(f"keytab file is not specified for kerberos cluster")
            awk = "awk {\'print $NF\'}"
            fetch_kinituser = f"klist -kt {keytab_file} | grep -v  \"{keytab_file}\" | grep -w \"" \
                              f"{self._hdfs_user}\" | {awk} | sort | uniq | head -1"
            kinit_user = self.execute(fetch_kinituser)
            if kinit_user.exit_code == 0:
                kinit_user = kinit_user.output
            else:
                raise Exception(f"Unable to fetch kinit user:{kinit_user.exception}")
            kinit_cmd = f"sudo -u {self._hdfs_user} kinit -kt {keytab_file} {kinit_user}"
            kinit = self.execute(kinit_cmd)
            if kinit.exit_code == 0:
                self.log.info('Kinit is successful.')
            else:
                raise Exception(f"kinit failed with error:{kinit.exception}")
        else:
            self.log.info('Kerberos authentication is not enabled')

    def run_kdestroy(self):
        """Runs kdestroy command to delete kerberos cache for kerberos cluster

        Raises:
            Exception:
                If any error occurred while deleting kerberos credentials cache
        """
        if self.is_kerberos_cluster:
            if self.__is_kerberos_cached():
                kdestroy_cmd = f"sudo -u {self._hdfs_user} kdestroy"
                kdestroy = self.execute(kdestroy_cmd)
                if kdestroy.exit_code == 0:
                    self.log.info('kdestroy is successful.')
                else:
                    raise Exception(f"kdestroy failed with error:{kdestroy.exception}")
            else:
                self.log.info('kerberos credentials cache is empty, skipping kdestroy')
        else:
            self.log.info('This is not a kerberos cluster, skipping kdestroy')

    def generate_test_data(self, file_path, **kwargs):
        """Generates and adds random test data at the given path with the specified options

        Args:
            file_path           (str)   --  directory path where
                                            the data will be generated.

            kwargs              (dict)  -- dict of keyword arguments as follows

                dirs                (int)   --  number of directories
                                                in each level

                    default: 1

                files               (int)   --  number of files
                                                in each directory

                    default: 1

                file_size           (int)   --  Size of the files in MB

                    default: 512

                levels              (int)   --  number of levels to be created

                    default: 1

                sparse              (bool)  --  whether to create sparse files

                    default: True

                sparse_hole_size    (int)   --  Size of the holes
                                                in sparse files in MB

                    default: 100

                long_path           (bool)  --  whether to create long files

                    default: False

                long_level          (int)   --  length of the long path

                    default: 1200

                unicode             (bool)  --  whether to create
                                                unicode files

                    default: False

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while generating the test data.

        """
        dirs = kwargs.get('dirs', 1)
        files = kwargs.get('files', 1)
        file_size = kwargs.get('file_size', 512)
        levels = kwargs.get('levels', 1)
        sparse = kwargs.get('sparse', True)
        sparse_hole_size = kwargs.get('sparse_hole_size', 100)
        long_path = kwargs.get('long_path', False)
        long_level = kwargs.get('long_level', 1200)
        unicode = kwargs.get('unicode', False)
        script_arguments = (
            "-optype add -path \"{0}\" -regular -dirs {1} -files {2} -sizeinmb {3} -levels {4}".format(
                file_path,
                str(dirs),
                str(files),
                str(file_size),
                str(levels)))

        if sparse:
            script_arguments = ("{0} -sparse"
                                " -holesizeinmb {1}".format(
                                    script_arguments, str(sparse_hole_size)))
        if long_path:
            script_arguments = ("{0} -longpath"
                                " -longlevel {1}".format(
                                    script_arguments, str(long_level)))
        if unicode:
            script_arguments = "{0} -unicode".format(script_arguments)

        output = self._execute_jar(script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while generating test data {0} {1}".format(output.output, output.exception)
            )
        return True

    def modify_test_data(self, data_path, **kwargs):
        """Modifies the test data at the given path based on the specified options

        Args:
            data_path   (str)   --  directory path where the dataset resides.

            kwargs      (dict)  --  dict of keyword arguments as follows

                rename_dir          (bool)  --  whether to rename the whole directory

                    default: False

                rename              (bool)  --  whether to rename all files

                    default: False

                modify              (bool)  --  whether to modify data of all files

                    default: False

                permissions         (bool)  --  whether to change permission of all files

                    default: False

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data modification.

        Raises:
            Exception:
                if any error occurred while modifying the test data.

        """
        rename_dir = kwargs.get('rename_dir', False)
        rename = kwargs.get('rename', False)
        modify = kwargs.get('modify', False)
        permissions = kwargs.get('permissions', False)
        script_arguments = "-optype change -path \"{0}\"".format(data_path)

        if rename_dir:
            script_arguments = "{0} -renamedir".format(script_arguments)

        if rename:
            script_arguments = "{0} -rename".format(script_arguments)

        if modify:
            script_arguments = "{0} -modify".format(script_arguments)

        if permissions:
            script_arguments = "{0} -permissions".format(script_arguments)

        output = self._execute_jar(script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while modifying test data {0} {1}".format(output.output, output.exception)
            )
        return True

    def get_test_data_info(self, data_path, **kwargs):
        """Gets information about the items on the given path based on the given options

        Args:
            data_path             (str)   --  directory path from where the data should be retrieved.

            kwargs                (dict)  --  dict of keyword arguments as follows

                meta                  (bool)  --  whether to get meta data of all files

                    default: False

                checksum              (bool)  --  whether to get checksum of all files

                    default: False

        Returns:
            list    -   list of output lines while executing the script.

        Raises:
            Exception:
                if any error occurred while getting the data information.

        """
        meta = kwargs.get('meta', False)
        checksum = kwargs.get('checksum', False)
        script_arguments = "-optype get -path \"{0}\"".format(data_path)

        if meta:
            script_arguments = "{0} -meta -strip".format(script_arguments)

        if checksum:
            script_arguments = "{0} -sum -strip".format(script_arguments)

        output = self._execute_jar(script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting the data information {0} {1}".format(output.output, output.exception)
            )
        return output.output

    def get_items_list(
            self,
            data_path,
            sorted_output=True,
            include_parents=False):
        """Gets the list of items at the given path.

        Args:
            data_path           (str)    --  directory path
                                             to get the items list

            sorted              (bool)   --  to specify whether
                                             the list should be sorted.

                default: True

            include_parents     (bool)   --  to specify whether
                                             parent paths should be include

                default: False

        Returns:
            list    -   list of the items

        """
        output = self.get_test_data_info(data_path)
        output_list = output.split('\n')
        if include_parents:
            data_path = data_path.replace("//", "/")
            parent_list = ["/", data_path.rstrip('/')]
            for itr in range(1, data_path.count('/')):
                parent_list.append(data_path.rsplit('/', itr)[0])
            output_list.extend(parent_list)

        if sorted_output:
            output_list.sort()
        # remove empty items and return output list
        while '' in output_list:
            output_list.remove('')
        return output_list

    def remove_directory(self, directory_name):
        """Removes a directory on the hadoop client.

        Args:
            directory_name  (str)   --  name / full path of the directory to remove

        Raises:
            Exception:
                if any error occurred while removing the directory.

        """
        self.remove_snapshots(locations=[directory_name], nested_remove=False, only_cvsnap=False)
        script_arguments = "-optype change -path \"{0}\" -delete".format(directory_name)
        output = self._execute_jar(script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while removing the directory {0} {1}".format(output.output, output.exception)
            )

    def create_directory(self, directory_name):
        """Creates a directory on the hadoop client.

        Args:
            directory_name  (str)   --  name / full path of the directory to create

        Raises:
            Exception:
                if any error occurred while creating the directory.

        """
        script_arguments = "-optype add -path \"{0}\" -mkdir".format(directory_name)
        output = self._execute_jar(script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while creating the directory {0} {1}".format(output.output, output.exception)
            )

    def fetch_snapshots(self, locations, only_cvsnap=False):
        """Returns snapshots in given hdfs locations

        Args:
            locations       (list)  -- list containing locations from where snaps need to be deleted

            only_cvsnap     (bool)  -- retrieves only commvault created snaps with name format - cvsnap_*

        Returns:
            snap_list (dict) with keys as locations and list of snap names as values respectively

        """
        if self.is_kerberos_cluster and not self.__is_kerberos_cached():
            self.run_kinit()
        if isinstance(locations, str):
            locations = [locations]
        snap_list = {}
        awk = "awk \'{print $8}\'"
        for location in locations:
            list_snap_cmd = f"sudo -u {self._hdfs_user} hdfs dfs -ls {location}/.snapshot | {awk}"
            snap_list_out = self.execute(list_snap_cmd)
            if snap_list_out.output != '' and snap_list_out.exception == '':
                snap_list[location] = [snap.split(f"{location}/.snapshot/")[-1] for snap
                                       in snap_list_out.output.strip().split('\n')]
                if only_cvsnap:
                    snap_list[location] = [snap for snap in snap_list[location] if 'cvsnap_' in snap]
                self.log.info(f"snap list for {location} is {snap_list[location]}")
            else:
                snap_list[location] = []
                self.log.info(f"snap list for {location} is empty")
        return snap_list

    def remove_snapshots(self, locations, nested_remove=False, only_cvsnap=True):
        """Removes snapshots in given hdfs locations

        Args:
            locations       (list)  -- list containing locations from where snaps need to be deleted

            nested_remove   (bool)  -- removes snapshots if child folder has any

            only_cvsnap     (bool)  -- retrieves only commvault created snaps with name format - cvsnap_*

        Raises:
            Exception:
                if any error occurred while removing the snapshots.

        """
        if self.is_kerberos_cluster and not self.__is_kerberos_cached():
            self.run_kinit()
        if isinstance(locations, str):
            locations = [locations]
        awk = "awk \'{print $10}\'"
        snappable_dir_cmd = f"sudo -u hdfs {self._hdfs_user} lsSnapshottableDir  | {awk}"
        snappable_dir_out = self.execute(snappable_dir_cmd)
        if snappable_dir_out.exit_code == 0:
            snappable_dirs = snappable_dir_out.output.strip().split('\n')
        else:
            snappable_dirs = []
        for location in locations:
            matched = [snappable_dir for snappable_dir in snappable_dirs if location in snappable_dir]
            if matched == [location] or nested_remove:
                snap_list = self.fetch_snapshots(matched, only_cvsnap)
                for snap_loc in snap_list:
                    for snap in snap_list[snap_loc]:
                        delete_snap_cmd = f"sudo -u hdfs {self._hdfs_user} dfs -deleteSnapshot {snap_loc} {snap}"
                        delete_snap_out = self.execute(delete_snap_cmd)
                        if delete_snap_out.exit_code == 0:
                            self.log.info(f"snap:{snap} deletion is successful")
                        else:
                            raise Exception(f"snap:{snap} deletion failed with error: {delete_snap_out.exception}")
