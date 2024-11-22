# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Unix File System operations

UnixFSHelper is the only class defined in this file.

UnixFSHelper: Helper class to perform file system operations

UnixFSHelper:
    __init__()                       --  initializes unix file system helper object

    verify_dc()                      --  Verifies whether the job used Scan optimization

    get_restore_stream_count()       --  returns the number of streams used by a restore job

    get_node_and_stream_count()      --  Returns the number of nodes and streams used by a given job

    compare_and_verify()             --  Compares and verifies if data in given source and destination paths matches

    verify_node_and_stream_count()   --  Verifies if the given job has used specified number of nodes and streams

    mount_openvms_testpath()         --  Mounts OpenVMS test path on the associated unix proxy

    execute_openvms_command()        --  Executes a command on OpenVMS remotely using ssh

    unmount_openvms_testpath()       --  Unmounts the OpenVMS test path mounted on the proxy client.

"""

from AutomationUtils.constants import UNIX_VERIFY_DC
from AutomationUtils.constants import VMS_MOUNTED_DISK
from AutomationUtils.constants import VMS_UNIX_MOUNT_PATH
from AutomationUtils.constants import UNIX_GET_RESTORE_STREAM_COUNT
from AutomationUtils.constants import UNIX_GET_NODE_AND_STREAM_COUNT
from FileSystem.FSUtils.fshelper import FSHelper


class UnixFSHelper(FSHelper):
    """Helper class to perform file system operations"""

    def __init__(self, testcase):
        """Initialize instance of the UnixFSHelper class."""
        super(UnixFSHelper, self).__init__(testcase)
        self.is_openvms_testpath_mounted = False
        self.os_flavour = self.testcase.client_machine.os_flavour
        if self.os_flavour != "OS400":
            if self.os_flavour == "OpenVMS":
                self.testcase.proxy = self.testcase.commcell.clients.get(
                    self.testcase.client_machine.proxy_name)
                self.testcase.client_machine.instance = self.testcase.proxy.instance
            elif (self.testcase.is_client_big_data_apps is not True) and (
                    self.testcase.is_client_network_share is not True):
                self.testcase.client_machine.instance = self.testcase.client.instance
            self.registry = self.testcase.client_machine.get_registry_dict()
            self.galaxy_home = self.registry['dGALAXYHOME']
            self.base_dir = self.registry['dBASEHOME']
            self.job_results_dir = self.registry['dJOBRESULTSDIR']
            self.log_files_dir = self.registry['dEVLOGDIR']

    def verify_dc(self, jobid, log_dir=None):
        """Verifies whether the job used Scan optimization

             Args:
                jobid    (int)  -- jobid to be checked

                log_dir  (str)  -- path of the log directory
                    default:None

            Returns:
                bool   -   Returns True if dc scan was successful or else false

            Raises:
                Exception:
                    if any error occurred while verifying the scan status

        """
        if log_dir is None:
            log_dir = self.log_files_dir
        script_arguments = "-logdir {0} -jobid {1}".format(log_dir, str(jobid))
        output = self.testcase.client_machine.execute(UNIX_VERIFY_DC, script_arguments)

        if output.exit_code != 0:
            self.log.error(
                "Error occurred while verifying the scan status %s %s",
                output.output,
                output.exception)
            raise Exception(
                "Error occurred while verifying the scan status {0} {1}".format(
                    output.output,
                    output.exception))
        else:
            result = output.output.strip('\n')
            return result == "success"

    def get_restore_stream_count(self, job, log_dir=None):
        """Returns the number of streams used by a restore job

             Args:
                job    (object)  -- job object of the restore job to be checked

                log_dir  (str)  -- path of the log directory
                    default:None

            Returns:
                int   -   the number of streams used by a restore job

            Raises:
                Exception:
                    if any error occurred while getting the restore stream count

        """
        if log_dir is None:
            log_dir = self.log_files_dir
        jobid = job.job_id
        script_arguments = "-logdir {0} -jobid {1}".format(log_dir, str(jobid))
        output = self.testcase.client_machine.execute(UNIX_GET_RESTORE_STREAM_COUNT, script_arguments)

        if output.exit_code != 0:
            self.log.error(
                "Error occurred while getting the number of restore streams %s %s",
                output.output,
                output.exception)
            raise Exception(
                "Error occurred while getting the number of restore streams {0} {1}".format(
                    output.output,
                    output.exception))
        else:
            result = output.output.strip('\n')
            return int(result)

    def get_node_and_stream_count(self, job, pkg, log_dir=None):
        """Returns the number of nodes and streams used by a given job

             Args:
                job      (object)  -- job object of the job to be checked

                pkg      (enum)    -- Instance of constants.DistributedClusterPkgName

                log_dir  (str)     -- path of the log directory
                    default:None

            Returns:
                tuple   -   tuple consisting of an int and an int, where:

                    int:
                        the number of nodes used by the given job

                    int:
                        the number of streams used by the given job

            Raises:
                Exception:
                    if any error occurred while getting the node and stream count

        """
        if log_dir is None:
            log_dir = self.log_files_dir
        jobid = job.job_id
        script_arguments = "-logdir {0} -jobid {1} -pkg {2}".format(log_dir, str(jobid), pkg.value)
        output = self.testcase.client_machine.execute(UNIX_GET_NODE_AND_STREAM_COUNT, script_arguments)

        if output.exit_code != 0:
            self.log.error(
                "Error occurred while getting the number of nodes and streams %s %s",
                output.output,
                output.exception)
            raise Exception(
                "Error occurred while getting the number of nodes and streams {0} {1}".format(
                    output.output,
                    output.exception))

        result = output.output.strip('\n').split(':')
        return int(result[0]), int(result[1])

    def verify_node_and_stream_count(self, job, pkg, node_count, stream_count):
        """Verifies if the given job has used specified number of nodes and streams

             Args:
                job          (object)  -- job object of the job to be checked

                pkg          (enum)    -- Instance of constants.DistributedClusterPkgName

                node_count   (int)     -- expected number of nodes

                stream_count (int)     -- expected number of streams

            Raises:
                Exception:
                    if job didn't use expected number of nodes and streams.

        """
        nodes_used, streams_used = self.get_node_and_stream_count(job, pkg)
        if nodes_used == node_count and streams_used == stream_count:
            self.log.info("Job %s used %s nodes and %s streams as expected",
                          str(job.job_id), str(node_count), str(stream_count))
        else:
            self.log.error("Expected %s nodes and %s streams", str(node_count), str(stream_count))
            self.log.error("Job %s used %s nodes and %s streams", str(job.job_id), str(nodes_used), str(streams_used))
            raise Exception("Job {0} didn't use expected number of nodes and streams".format(str(job.job_id)))

    def compare_and_verify(self, source, destination, cleanup_destination=True):
        """Compares and verifies if data in given source and destination paths matches

             Args:
                source                 (str)  -- Source path to compare

                destination            (str)  -- Destination path to compare

                cleanup_destination    (bool) -- whether to clean up the destination after successful comparison
                    default: True

            Raises:
                Exception:
                    if source and destination differs.

        """
        testcase = self.testcase
        log = self.log
        client_machine = testcase.client_machine
        log.info("Comparing source:%s destination:%s", source, destination)
        result, diff_output = client_machine.compare_meta_data(
            source,
            destination,
            dirtime=testcase.dirtime,
            skiplink=testcase.skiplink
        )
        if result:
            log.info("Meta data comparison successful")
        else:
            log.error("Meta data comparison failed")
            log.info("Diff output: \n%s", diff_output)
            raise Exception("Meta data comparison failed")

        result, diff_output = client_machine.compare_checksum(source, destination)
        if result:
            log.info("Checksum comparison successful")
        else:
            log.error("Checksum comparison failed")
            log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

        if testcase.acls:
            result, diff_output = client_machine.compare_acl(source, destination)
            if result:
                log.info("ACL comparison successful")
            else:
                log.error("ACL comparison failed")
                log.info("Diff output: \n%s", diff_output)
                raise Exception("ACL comparison failed")
        if testcase.xattr:
            result, diff_output = client_machine.compare_xattr(source, destination)
            if result:
                log.info("XATTR comparison successful")
            else:
                log.error("XATTR comparison failed")
                log.info("Diff output: \n%s", diff_output)
                raise Exception("XATTR comparison failed")
        if cleanup_destination:
            testcase.client_machine.remove_directory(destination)

    def mount_openvms_testpath(self, test_path):
        """Mounts OpenVMS test path on the proxy associated with the OpenVMS client.

            For OpenVMS,
            since we cannot directly execute shell script on OpenVMS,
            we first mount the OpenVMS test path onto the associated proxy client.
            Finally, we execute the shell scripts or commands to generate data,
            verify data or related tasks on the proxy client at the mount location.

             Args:
                test_path   (str)   -- OpenVMS test path to be mounted.

            Raises:
                Exception:
                    if any error occurred while mounting OpenVMS test path.

        """
        pos = test_path.find("/", 1)
        disk_name_openvms = test_path[1:pos] + ":"
        mounted_path_openvms = VMS_MOUNTED_DISK + test_path[pos:]

        self.log.info(
            "Mounting OpenVMS test path [%s] onto proxy path [%s]",
            test_path,
            VMS_UNIX_MOUNT_PATH)

        command_string = "TCPIP ADD PROXY {0} /uid=0 /gid=0 /HOST=*".format(self.testcase.username)
        self.execute_openvms_command(command_string)

        command_string = "TCPIP MAP \"{0}\" {1}".format(VMS_MOUNTED_DISK, disk_name_openvms)
        self.execute_openvms_command(command_string)

        command_string = "TCPIP ADD EXPORT \"{0}\" /HOST=* /OPTIONS=NAME_CONVERSION".format(
            mounted_path_openvms)
        self.execute_openvms_command(command_string)

        command_string = "showmount -e {0}".format(self.testcase.client.client_hostname)
        output = self.testcase.client_machine.execute(command_string)
        if mounted_path_openvms not in output.output or output.exit_code is not 0:
            self.log.error(
                "Error occurred while mounting OpenVMS test path %s %s",
                output.output,
                output.exception)
            raise Exception("Error occurred while mounting OpenVMS test path {0} {1}".format(
                output.output, output.exception))

        if not self.testcase.client_machine.check_directory_exists(VMS_UNIX_MOUNT_PATH):
            if not self.testcase.client_machine.create_directory(VMS_UNIX_MOUNT_PATH):
                self.log.error(
                    "Error occurred while creating directory %s %s",
                    output.output,
                    output.exception)
                raise Exception("Error occurred while mounting OpenVMS test path {0} {1}".format(
                    output.output, output.exception))

        command_string = "mount -vt nfs {0}:{1} {2}".format(
            self.testcase.client.client_hostname, mounted_path_openvms, VMS_UNIX_MOUNT_PATH)
        output = self.testcase.client_machine.execute(command_string)
        if output.exit_code != 0:
            self.log.error(
                "Error occurred while mounting OpenVMS test path %s %s",
                output.output,
                output.exception)
            raise Exception("Error occurred while mounting OpenVMS test path {0} {1}".format(
                output.output, output.exception))

        self.is_openvms_testpath_mounted = True

    def unmount_openvms_testpath(self, test_path):
        """Unmounts the OpenVMS test path mounted on the proxy client.
        This function is only executed when the mounting was successful.
        To check that we use the boolean variable is_openvms_testpath_mounted.

             Args:
                test_path   (str)   -- OpenVMS test path to be unmounted.

        """
        if self.is_openvms_testpath_mounted is False:
            return

        pos = test_path.find("/", 1)
        mounted_path_openvms = VMS_MOUNTED_DISK + test_path[pos:]

        self.log.info(
            "Unmounting OpenVMS test path [%s] from proxy client path [%s]",
            test_path,
            VMS_UNIX_MOUNT_PATH)

        command_string = "umount -f {0}".format(VMS_UNIX_MOUNT_PATH)
        output = self.testcase.client_machine.execute(command_string)
        if output.exit_code != 0:
            self.log.error(
                "Error occurred while unmounting OpenVMS test path %s %s",
                output.output,
                output.exception)

        command_string = "TCPIP REMOVE EXPORT \"{0}\"".format(
            mounted_path_openvms)
        self.execute_openvms_command(command_string)

        command_string = "TCPIP UNMAP \"{0}\"".format(VMS_MOUNTED_DISK)
        self.execute_openvms_command(command_string)

        command_string = "TCPIP REMOVE PROXY \"{0}\"".format(self.testcase.username)
        self.execute_openvms_command(command_string)

        command_string = "showmount -e {0}".format(self.testcase.client.client_hostname)
        output = self.testcase.client_machine.execute(command_string)
        if mounted_path_openvms in output.output or output.exit_code is not 0:
            self.log.error(
                "Error occurred while unmounting OpenVMS test path %s %s",
                output.output,
                output.exception)

    def execute_openvms_command(self, command_string):
        """Verifies whether the job used Scan optimization

             Args:
                command_string  (str)   -- command to be executed

            Raises:
                Exception:
                    if any error occurred while executing the command on OpenVMS
        """
        command_string = (
            "{0}/sshf -p {1} -- ssh  -oKexAlgorithms=+diffie-hellman-group1-sha1 "
            "-oHostKeyAlgorithms=+ssh-dss -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no -o ConnectTimeout=15 {2}@{3} \'{4}\'"
        ).format(
            self.base_dir, self.testcase.password, self.testcase.username,
            self.testcase.client.client_hostname, command_string
        )

        output = self.testcase.client_machine.execute(command_string)

        if output.exit_code != 0:
            self.log.error(
                "Error occurred while executing remotely OpenVMS cmd %s %s %s",
                command_string,
                output.output,
                output.exception)
            raise Exception("Error occurred while verifying the scan status {0} {1}".format(
                output.output, output.exception))

    def get_logs_for_job_from_file(self, job_id=None, log_file_name=None, search_term=None):
        """From a log file object only return those log lines for a particular job ID.

        Args:
            job_id          (str)   --  Job ID for which log lines need to be fetched.

            log_file_name   (bool)  --  Name of the log file.

            search_term     (str)   --  Only capture those log lines containing the search term.

        Returns:
            str     -   \r\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """

        # GET ONLY LOG LINES FOR A PARTICULAR JOB ID
        return self.testcase.client_machine.get_logs_for_job_from_file(job_id, log_file_name, search_term)
