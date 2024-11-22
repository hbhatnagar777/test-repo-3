# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing IBMi File System operations
IBMiHelper: Helper class to perform file system operations which derives from the UnixFSHelper.

IBMiHelper
==========

    __init__()                      --  initializes IBMi helper object

    num_libraries()                 --  Returns the number of libraries that are generated.

    get_subclient_content()         --  Generates the subclient content list.

    add_new_data_incr()             --  Adds new data for incremental backups

    mod_data_incr()                 --  Modifies the data added by add_new_data_incr

    is_path_found_in_index()        --  Check if the path found from the index and return

    run_restore_verify()            --  Initiates restore for data
                                        backed up in the given job
                                        and performs the applicable verifications

    run_find_verify()               --  Finds items backed up in the given job
                                        and compares it with items from machine

    run_complete_restore_verify()   --  Initiates restore of complete /QSYS.LIB data backed up for
                                        this subclient

    set_client_side_deduplication() --  Set subclient property to perform client side deduplication

    set_object_level_backup()       --  Set the subclient property to backup data as objects.

    get_log_directory()             --  Returns the log directory of the IBMi client

    verify_from_log()               --  Parse the log file to match a regular expression.

    update_filter_and_exception()   --  Updates the subclient's filter and exception content.

    get_wildcard_content()          --  Returns a wildcard content for subclient.

    enable_synclib()                --  Enables synclib for subclient.

    create_ibmi_dr_subclient()      --  Create IBMi DR subclient with IBMi specific parameters

    set_savf_file_backup()          --  Enable SAVF file backups for an IBMi subclient

    configure_ibmi_default_sc()      --  Creates new backupset, check pre-defined subclient
                                            and set with specified parameters
                                            under the current testcase Instance.

    compare_ibmi_data()             --  Function to perform meta data comparision & Checksum
                                            comparision of source and destination paths.

    verify_sc_defaults()            --  Function to verify all the default subclient options.

    set_ibmi_sc_options()           -- Function to set IBMi specific options to subclient.

    verify_ibmi_sc_options()        -- Function to verify subclient options in client logs.

    update_pre_post()               -- Sets the pre post commands on a subclient

    verify_vtl_multistream()        -- Function to verify if mutiple streams used by VTL backup.

    verify_ibmi_vtl_sc_options()    -- Function to verify subclient options in client logs for VTL backups.

    verify_adv_restore_options()    -- Function to verify advanced restore options in client logs

    verify_adv_restore_options_vtl()-- Function to verify advanced restore options in client logs for VTL

"""

import re
import time

from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.unixfshelper import UnixFSHelper


class IBMiHelper(UnixFSHelper):
    """Helper class to perform file system operations"""

    def __init__(self, testcase):
        """Initialize instance of the IBMi Helper class."""
        super(IBMiHelper, self).__init__(testcase)
        self._num_libraries = int(testcase.tcinputs.get('NumLibraries', '2'))
        testcase.client_machine.initialize_param_from_testcase(testcase.tcinputs)
        self._testcaseid = testcase.id
        self._lfs_backup = False
        self._incr_path = None

    @property
    def num_libraries(self):
        """Returns the number of libraries that are generated for this test"""
        # Never change this value, so we always have a reference as to how many libraries we
        # initially started the testcase with.  Hence no setter method for this.
        # To increase the number of libraries on client, update the IBMIMachine::num_libraries
        return self._num_libraries

    def get_subclient_content(self, test_path, slash_format, subclient_name):
        """
        Generates the subclient content list. For IFS, calls the unix implementation.

        Args:
            test_path           (str)   : The test path provided for the test case

            slash_format        (str)   : The slash format for the platform

            subclient_name      (str)   : The name of the subclient for which data is generated.

        Returns:
            list : list of subclient contents for this test case
        """
        temp = list()
        if '/QSYS.LIB' not in test_path:
            return super(IBMiHelper, self).get_subclient_content(test_path,
                                                                 slash_format,
                                                                 subclient_name)

        for itr in range(self.testcase.client_machine.num_libraries):
            sub_lib = '{0}{1}AL{2}{3}.LIB'.format(test_path,
                                                  slash_format,
                                                  str(self._testcaseid),
                                                  str(itr)[:2])
            temp.append(sub_lib)
            self.testcase.client_machine.remove_directory(sub_lib)
        return temp

    def add_new_data_incr(self,
                          incr_path,
                          slash_format,
                          scan_type=ScanType.RECURSIVE,
                          **kwargs):
        """
        Adds new data for incremental. For IFS paths, this will call the UnixFsHelper
        implementation with provisions for modification after this function execution call
        mod_data_incr for modifications

        Args:
            incr_path           (str)   : path for adding data

            slash_format        (str)   : OS path separator format

            scan_type           (str)   : scan type as one of below
                                RECURSIVE
                                OPTIMIZED
                                CHANGEJOURNAL
                default: ScanType.RECURSIVE

            **kwargs            (dict)  : dictionary of optional arguments

                options:

                    dirs        (int)   : number of directories in each level.
                        default: 3

                    files       (int)   : number of files in each directory
                        default: 5

                    file_size   (int)   : Size of the files in KB
                        default: 20

                    levels      (int)   : number of levels to be created
                        default: 1

                    hlinks      (bool)  : whether to create hardlink files
                        default: True

                    slinks      (bool)  : whether to create symbolic link files
                        default: True

                    sparse      (bool)  : whether to create sparse files
                        default: True

                    sparse_hole_size (int) : Size of the holes in sparse files in KB
                        default: 1024

                    options     (str)   : to specify any other additional parameters to the script.
                        default: ""

                    increment_count (bool)  : to specify if counters need to be incremented

        Returns:
            None

        Raises:
            Exception:
                Any error occurred while populating the data.
        """
        if 'QSYS.LIB' not in incr_path:
            kwargs['hlinks'] = False
            return super(IBMiHelper, self).add_new_data_incr(
                incr_path,
                slash_format,
                scan_type,
                **kwargs
            )

        # Not adding any new data area during incremental. Same data area is modified again before
        # incremental backups.
        increment_count = kwargs.get('increment_count', True)
        self._lfs_backup = True
        self._incr_path = incr_path

        if increment_count:
            if self.testcase.client_machine.num_data_files != 0:
                self.testcase.client_machine.num_data_files += 1

            if self.testcase.client_machine.num_members != 0:
                self.testcase.client_machine.num_members += 2

            if self.testcase.client_machine.num_empty_files != 0:
                self.testcase.client_machine.num_empty_files += 1

            if self.testcase.client_machine.num_attribute_changes != 0:
                self.testcase.client_machine.num_attribute_changes += 1

            if self.testcase.client_machine.num_savf_files != 0:
                self.testcase.client_machine.num_savf_files += 2

        return self.testcase.client_machine.generate_test_data(incr_path)

    def mod_data_incr(self, scan_type=ScanType.RECURSIVE):
        """
        Modifies the data added by add_new_data_incr call add_new_data_incr before calling this.
        For LFS, it adds more incremental data. For IFS, it calls the UnixFsHelper implementation

            Args:
                scan_type       (ScanType(Enum))    : scan type
                    default : ScanType.RECURSIVE

            Returns:
                None

            Raises:
                Exception:
                    Any error occurred while modifying the data.
        """
        if self._lfs_backup:
            self.add_new_data_incr(self._incr_path, '/', scan_type)
        else:
            # IBMi doesn't support ACL changes, Permission changes and XATTR changes
            self.log.info("Deleting path: %s", self.testcase.incr_delete_data)
            self.testcase.client_machine.remove_directory(self.testcase.incr_delete_data)

            self.log.info("Renaming directory: %s", self.testcase.incr_dir_rename)
            self.testcase.client_machine.rename_file_or_folder(
                self.testcase.incr_dir_rename,
                "{0}_renamed".format(self.testcase.incr_dir_rename)
            )

            self.log.info("Modifying files on path: %s", self.testcase.incr_modify)
            self.testcase.client_machine.modify_test_data(
                self.testcase.incr_modify,
                modify=True
            )

            self.log.info("Renaming folders on path: %s", self.testcase.incr_file_rename)
            self.testcase.client_machine.rename_file_or_folder(
                self.testcase.incr_file_rename,
                "{0}_renamed".format(self.testcase.incr_file_rename)
            )

    def run_find_verify(self, machine_path, job=None):
        """
        Finds items backed up in the given job and compares it with items from machine

            Args:
                machine_path    (str)   : Source data path on the machine

                job             (obj)   : instance of the job class whose data needs to be restored
                    default : None

            Returns:
                None

            Raises:
                Exception:
                    Any error occurred while finding items or during verification.
        """
        from_time = job.summary['jobStartTime'] if job is not None else None
        to_time = job.summary['jobEndTime'] if job is not None else None

        _, meta_data = self.find_items_subclient(from_time=from_time, to_time=to_time)

        machine_items = self.testcase.client_machine.get_items_list(
            machine_path,
            include_parents=False,
            sorted_output=True
        )
        index_items = [item for item in meta_data if meta_data[item]['type'] != 'Folder'
                       and machine_path in item]
        index_items.sort()

        if self.compare_lists(index_items, machine_items):
            self.log.info(
                "Items from find operation matches with items on the machine"
            )
        else:
            raise Exception(
                "Items from find operation doesn't match"
                " with items on the machine")

    def is_path_found_in_index(self, path, job=None):
        """
        Check if the path found from the index and return

            Args:
                path            (str)   : Source data path on the machine

                job             (obj)   : instance of the job class whose data needs to be restored
                    default : None

            Returns:
                True /False
        """
        from_time = job.summary['jobStartTime'] if job is not None else None
        to_time = job.summary['jobEndTime'] if job is not None else None

        _, meta_data = self.find_items_subclient(from_time=from_time, to_time=to_time)
        index_items = [item for item in meta_data if meta_data[item]['type'] != 'Folder'
                       and path in item]
        if not index_items:
            self.log.info("Path {0} not found".format(path))
            return False
        else:
            self.log.info("Path {0} found".format(path))
            return True
    
    def run_restore_verify(self,
                           slash_format,
                           data_path,
                           tmp_path,
                           data_path_leaf,
                           **kwargs):
        """
        Initiates restore for data backed up in the given job
        and performs the applicable verifications

            Args:
                slash_format    (str)   : OS path separator format

                data_path       (str)   : Source data path

                tmp_path        (str)   : temporary path for restoring the data

                data_path_leaf  (str)   : leaf level of the data_path

                **kwargs        (dict)  : Dictionary of optional arguments.

                    options             :

                        job     (obj)   : instance of the job class whose data needs to be restored
                            default : None

                        cleanup (bool)  : to indicate if restored data should be cleaned up
                            default : True

            Returns:
                None

            Raises:
                Exception:
                    Any error occurred while running restore or during verification.
        """
        # pylint: disable=arguments-differ
        job = kwargs.get('job', None)
        cleanup = kwargs.get('cleanup', True)

        # For IFS do the same as Unix restore verification.
        if '/QSYS.LIB' not in data_path:
            super(IBMiHelper, self).run_restore_verify(slash_format,
                                                       data_path,
                                                       tmp_path,
                                                       data_path_leaf,
                                                       job,
                                                       cleanup)
        else:
            # For LFS, source and destination paths will be of the form /QSYS.LIB/XYZ.LIB
            if data_path_leaf != '':
                data_path = self.testcase.client_machine.join_path(data_path, data_path_leaf)

            paths = list()
            paths.append(data_path)
            dest_path = tmp_path

            restore_from_time = None
            restore_to_time = None
            if job is not None:
                restore_from_time = str(datetime.utcfromtimestamp(job.summary['jobStartTime']))
                restore_to_time = str(datetime.utcfromtimestamp(job.summary['jobEndTime']))

            # clean up destination directory before starting restore
            self.testcase.client_machine.remove_directory(dest_path)

            self.log.info('Starting restore with source:%s destination:%s from_time:%s to_time:%s',
                          str(paths),
                          dest_path,
                          str(restore_from_time),
                          str(restore_to_time)
                          )

            self.restore_out_of_place(destination_path=dest_path,
                                      paths=paths,
                                      from_time=restore_from_time,
                                      to_time=restore_to_time)

            compare_source = data_path
            if data_path_leaf != '':
                compare_destination = self.testcase.client_machine.join_path(dest_path, data_path_leaf)
            else:
                compare_destination = dest_path

            self.log.info("Comparing source: %s destination: %s", compare_source, compare_destination)
            result, diff_output = self.testcase.client_machine.compare_meta_data(
                compare_source,
                compare_destination
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", str(diff_output))
                raise Exception("Meta data comparison failed")

            if cleanup:
                self.testcase.client_machine.remove_directory(dest_path)

    def run_complete_restore_verify(self, content):
        """
        Initiates restore of complete /QSYS.LIB data backed up for this subclient.
        This runs a find on source, then deletes all the source files and
        attempts an in-place restore. The initial find is compared with find on restored data.

            Args:
                content     (list)  : list of the content for this testcase

            Returns:
                None

            Raises:
                Exception:
                    Any error occurred while running restore or during verification.
        """
        complete_source_find_list = list()
        paths = list()
        source_path = '/QSYS.LIB'
        paths.append(source_path)
        restore_from_time = None
        restore_to_time = None

        for data_path in content:
            if 'QSYS.LIB' in data_path:
                complete_source_find_list.extend(
                    self.testcase.client_machine.get_items_list(data_path)
                )
                self.testcase.client_machine.remove_directory(data_path)

        if not complete_source_find_list:
            return

        self.log.info('Starting restore for:%s from_time:%s to_time:%s',
                      source_path,
                      str(restore_from_time),
                      str(restore_to_time)
                      )

        self.restore_in_place(
            paths=paths,
            from_time=restore_from_time,
            to_time=restore_to_time
        )

        self.log.info('Restored complete %s data in place.', source_path)

        complete_restore_find_list = list()
        for data_path in content:
            if 'QSYS.LIB' in data_path:
                complete_restore_find_list.extend(
                    self.testcase.client_machine.get_items_list(data_path)
                )

        if self.compare_lists(complete_source_find_list, complete_restore_find_list):
            self.log.info('Restore of %s was successful', source_path)
        else:
            raise Exception(
                "Restored and source data do not match"
            )

    def set_client_side_deduplication(self, generate_signature_on_ibmi=True):
        """
        Set the subclient property to generate signature on ibmi client.

        Args:
            generate_signature_on_ibmi  (bool)  : Enable or disable the property
                default: True

        Returns:
            SDKException:
                if failed to update number properties for subclient
        """
        if generate_signature_on_ibmi:
            self.testcase.subclient.generate_signature_on_ibmi = 1
        else:
            self.testcase.subclient.generate_signature_on_ibmi = 0

    def set_object_level_backup(self, object_level_backup=True):
        """
        Set the subclient property to backup data as objects.

        Args:
            object_level_backup     (bool)  : Enable or disable the property
                default: True

        Returns:
            SDKException:
                if failed to update number properties for subclient
        """
        self.testcase.subclient.object_level_backup = object_level_backup

    def set_vtl_multiple_drives(self, backup_using_multiple_drives=True):
        """
        Set the subclient property to use multiple tape drives.

        Args:
            backup_using_multiple_drives     (bool)  : Enable or disable the property
                default: True

        Returns:
            SDKException:
                if failed to update number properties for subclient
        """
        self.testcase.subclient.backup_using_multiple_drives = backup_using_multiple_drives

    def get_log_directory(self):
        """
        Returns the log directory of the IBMi client

        Returns:
            str : The log directory path
        """
        # IBMI needs this because IBMI doesn't maintain a registry key file in text format to grep
        # the dataFolder from.
        data_folder = self.testcase.client._properties['pseudoClientInfo']['ibmiInstallOptions']['dataFolder']
        return self.testcase.client_machine.join_path(data_folder, 'log')

    def verify_from_log(self, logfile, regex, jobid=None, expectedvalue=None):
        """
        Parse the log file for regex and check if the expected value matches.

        Args:
            logfile         (str) : Log file to parse

            regex           (str) : Regex to parse the log file with

            jobid           (str) : Job id
                default: None

            expectedvalue   (str) : The expected value in regex match
                default: None

        Returns:
             bool : True if lines matching regex and expected value were found.

        Raises:
            Exception:
                If no lines matching the regex and expected value is found.
        """
        logfilepath = self.testcase.client_machine.join_path(self.get_log_directory(), logfile)
        self.log.info("Checking %s for Job:[%s] regex:[%s]",
                      logfilepath,
                      jobid,
                      regex)

        lines = self.testcase.client_machine.parse_log_file(logfilepath, regex, jobid=jobid)

        if not expectedvalue:
            if lines:
                return True
            else:
                raise Exception("No lines match the regular expression in the logs")

        expected_lines = [line for line in lines if expectedvalue in line]

        if not expected_lines:
            raise Exception("No lines match the expected value in the logs")
        else:
            self.log.info("Matching lines\n%s", str(expected_lines))
            return True

    def get_wildcard_content(self, subclient_content):
        """
        Get a wildcard to substitute for the subclient content.

        Args:
            subclient_content       (str) : subclient content path

        Returns:
            str : subclient content in wildcard format.

        Raises:
            Exception:
                If the subclient content provided is not library file system.
        """
        list_path_element = subclient_content.split("/")[1:]  # Ignore the first empty element.
        if list_path_element[0] == "QSYS.LIB":
            wildcard_library = "/{0}/AL{1}*".format(list_path_element[0],
                                                    str(self._testcaseid))
            return wildcard_library
        elif list_path_element[1] == "QSYS.LIB":
            wildcard_library = "/{0}/{1}/AL{2}*".format(list_path_element[0],
                                                        list_path_element[1],
                                                        str(self._testcaseid))
            return wildcard_library
        else:
            raise Exception("Not library file system content. Can't generate wildcard.")

    def update_filter_and_exception(self, filter_content=None, exception_content=None):
        """
        Update subclient with new filters and exceptions

        Args:
            filter_content          (list) : List of filters
                default : None

            exception_content       (list) : List of exceptions
                default : None

        Returns:
            None

        Raises:
            Exception:
                If the filter and exception update fails.
        """
        try:
            self.testcase.client_machine.filter_list = filter_content
            self.testcase.client_machine.exception_list = exception_content

            if filter_content is not None:
                self.testcase.subclient.filter_content = filter_content

            if exception_content is not None:
                self.testcase.subclient.exception_content = exception_content

        except Exception as excp:
            self.log.error('Filter and exception creation failed with error: %s', str(excp))
            raise Exception('Filter and exception creation failed. Error:{0}'.format(str(excp)))

    def verify_dc(self, jobid, log_dir=None):
        """
        Verifies whether the job used Scan optimization

             Args:
                jobid       (int)   : jobid to be checked

                log_dir     (str)   : path of the log directory
                    default: None

            Returns:
                bool    : Returns True if dc scan was successful or else false

            Raises:
                Exception:
                    if any error occurred while verifying the scan status
        """
        # DC Verification not supported by IBMi
        return True

    def enable_synclib(self,
                       synclib_value="*SYNCLIB",
                       sync_queue='',
                       sync_all_lib=True,
                       check_point='',
                       active_wait_time=600):
        """
        Enables the synclib backups for the subclient in testcase.

        Args:
                synclib_value       (str)   :  Value to which save while active option is set.
                    default: '*SYNCLIB'

                sync_queue          (str)   :  Path for the sync queue
                    default: ''

                sync_all_lib        (bool)  :  Whether to synchronize all libraries before backup
                    default: True

                check_point         (str)   :  Command to run on checkpoint
                    default: ''

                active_wait_time    (int)   :  Amount of time to wait for check point in seconds.
                    default: 600

        Returns:
            None
        """
        synclib_config = {
            'saveWhileActiveOpt': synclib_value,
            'syncQueue': sync_queue,
            'syncAllLibForBackup': sync_all_lib,
            'txtlibSyncCheckPoint': check_point,
            'activeWaitTime': active_wait_time
        }
        self.testcase.subclient.enable_synclib = synclib_config

    def create_ibmi_dr_subclient(self,
                                 subclient_name,
                                 storage_policy,
                                 additional_library=None,
                                 data_readers=2,
                                 allow_multiple_readers=False,
                                 delete=False,
                                 **kwargs):
        """
        Creates a IBMi DR subclient with specific IBMi configurations set.
        Args:
            subclient_name          (str)   :   Name of the new subclient

            storage_policy          (str)   :   Name of the storage policy to use

            additional_library      (list)  :   List of additional libraries to backup
                default :   None

            data_readers            (int)   :   number of data readers
                default: 2

            allow_multiple_readers (bool)   : enable / disable allow multiple readers
                default: False

            delete                  (bool)  :   Should subclient be deleted if existing
                default :   False

             **kwargs               (dict)  : Dictionary of optional arguments.

                    options                 :

                        tmp_dir         (str)   :   Temporary path

                        backup_max_time (int)   :   Maximum time the backup can run, in minutes

                        save_security   (bool)  :   Option to enable SAVSEC backup
                            default : True

                        save_config     (bool)  :   Option to enable SAVCFG backup
                            default : False

                        user_program    (str)   :   program to bring system to ristricted state

                        print_system_info   (bool)  :   Pring system information during backup

                        notify_user     (bool)  : notify users about DR backup initiation

                        notify_delay    (int)   :   delay time before ending subsystems, in minutes

                        notify_message  (str)   : message content to noitify users

                        user_ipl_program    (str)   : custom startup program

                        rstd_cmd        (str)   : command to run in ristricted state.

                        dvd_image_format    (str)   ; dvd image naming format

            Returns:
                None    :   Sets the testcase.subclient object

            Raises:
                Exception:
                    Any error occurred while creating subclient:
    """
        self.create_subclient(name=subclient_name,
                              storage_policy=storage_policy,
                              content=additional_library,
                              scan_type=ScanType.RECURSIVE,
                              data_readers=data_readers,
                              allow_multiple_readers=allow_multiple_readers,
                              delete=delete)
        dr_config = {}

        dr_config.update({'library': [{'path': lib} for lib in additional_library]})
        if 'temp_dir' in kwargs.keys():
            dr_config.update({'SRBootServerDir': kwargs.get('temp_dir')})

        if 'backup_max_time' in kwargs.keys():
            dr_config.update({'backupMaxTime': kwargs.get('backup_max_time')})

        if 'save_security' in kwargs.keys():
            dr_config.update({'saveSecData': kwargs.get('save_security')})

        if 'save_config' in kwargs.keys():
            dr_config.update({'saveConfObject': kwargs.get('save_config')})

        if 'user_program' in kwargs.keys():
            dr_config.update({'userProgram': kwargs.get('user_program')})

        if 'print_system_info' in kwargs.keys():
            dr_config.update({'printSysInfo': kwargs.get('print_system_info')})

        if 'notify_user' in kwargs.keys():
            dr_config.update({'notifyuser': kwargs.get('notify_user')})

        if 'notify_delay' in kwargs.keys():
            dr_config.update({'notifyDelay': kwargs.get('notify_delay')})

        if 'notify_message' in kwargs.keys():
            dr_config.update({'notifyMessage': kwargs.get('notify_message')})

        if 'user_ipl_program' in kwargs.keys():
            dr_config.update({'userIPLProgram': kwargs.get('user_ipl_program')})

        if 'rstd_cmd' in kwargs.keys():
            dr_config.update({'userCommand': kwargs.get('rstd_cmd')})

        if 'dvd_image_format' in kwargs.keys():
            dr_config.update({'DVDImageFileFormat': kwargs.get('dvd_image_format')})

        self.log.info("setting the IBMi DR SC options {0}".format(dr_config))
        self.testcase.subclient.ibmi_dr_config = dr_config

        fs_options = {}
        if 'accpth' in kwargs.keys():
            fs_options.update({'accpth': kwargs.get('accpth')})

        if 'updhst' in kwargs.keys():
            fs_options.update({'updhst': kwargs.get('updhst')})

        if 'splfdta' in kwargs.keys():
            fs_options.update({'splfdta': kwargs.get('splfdta')})

        if len(fs_options) != 0:
            self.set_ibmi_sc_options(**fs_options)

    def set_savf_file_backup(self, value=True):
        """
        Set the savf file backup property to user provided value

        Args:
            value   (bool)  :   Boolean to set/unset the savf file backup property

        Returns:
            None

        Raises:
            None
        """
        self.testcase.subclient.backup_savf_file_data = value

    def configure_ibmi_default_sc(self, backupset_name,
                                  subclient_name,
                                  storage_policy,
                                  filter_content=None,
                                  exception_content=None,
                                  scan_type=ScanType.RECURSIVE,
                                  data_readers=2,
                                  allow_multiple_readers=False,
                                  savfdta=True,
                                  delete=False):
        """Creates new backupset, check pre-defined subclient and set with specified parameters
                     under the current testcase Instance.

                    Checks if the backupset exists or not.
                    If the backupset exists, deletes the existing backupset
                    and creates new one with the testcase id.

                    Args:
                        backupset_name   (str)          -- name of the backupset

                        subclient_name   (str)          -- subclient name

                        storage_policy (str)            -- storage policy to assign to subclient

                        exception_content (list)        -- content list

                        filter_content (list)           -- filter list
                            default: None

                        exception_conent (list)         -- exception list
                            default: None

                         data_readers (int)             -- number of data readers
                            default: 2

                        allow_multiple_readers (bool)   -- enable / disable allow multiple readers
                            default: False

                        scan_type(ScanType(Enum))        --  scan type (RECURSIVE/OPTIMIZED)
                            default: ScanType.RECURSIVE

                        savfdta (bool)                   -- backup save file data along with SAVF object
                            default: True

                        delete (bool)                    -- indicates whether existing backupset should be deleted
                            default: False

                    Returns:
                        None

                    Raises:
                        Exception - Any error occured while configuring pre-defined subclient.
        """

        self.log.info("Create backupset for this testcase if it does not exist")
        self.create_backupset(backupset_name, delete=delete)
        self.log.info("Checking if pre-defined subclient %s exists.", subclient_name)
        subclients_object = self.testcase.backupset.subclients
        if subclients_object.has_subclient(subclient_name):
            self.log.info("Pre-defined Subclient {0} exists. Now, updating with "
                          "additional parameters".format(subclient_name))
            self.testcase.subclient = subclients_object.get(subclient_name)

            self.update_subclient(storage_policy=storage_policy,
                                  content=None,
                                  filter_content=filter_content,
                                  exception_content=exception_content,
                                  scan_type=scan_type,
                                  data_readers=data_readers,
                                  allow_multiple_readers=allow_multiple_readers)
            if savfdta is not True:
                self.set_savf_file_backup(savfdta)
        else:
            raise Exception("Failed: Pre-defined Subclient {0} is not auto-created"
                            "under backupSet {1}".format(subclient_name, backupset_name))

    def compare_ibmi_data(self, source_path, destination_path):
        """ Function to perform meta data comparision & Checksum comparision
            of source and destination paths.
            Args:
                source_path(str)       -- Source Path for the restore
                destination_path(str)  -- Destination Path you want to restore
            Returns:
                None
            Raises:
                Exception - error while comparing the paths.
        """
        self.log.info("Comparing source:%s destination:%s", source_path, destination_path)
        result, output = self.testcase.client_machine.compare_meta_data(source_path, destination_path)
        if result:
            self.log.info("Meta data comparison successful")
        else:
            self.log.error("Meta data comparison failed")
            self.log.info("Diff output: \n%s", output)
            raise Exception("Meta data comparison failed")

        result, output = self.testcase.client_machine.compare_checksum(source_path, destination_path)
        if result:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", output)
            raise Exception("Checksum comparison failed")

    def verify_sc_defaults(self, job):
        """ Function to verify all the default subclient options.
            Args:
                job         (str)-- Job details
            Returns:
                None
            Raises:
                Exception - error while verifying logs for default values.
        """
        self.log.info("Check Default value for Private authorities")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_PrivateAuthority_Enabled] - [0]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="PVTAUT(*NO)")

        self.log.info("Check Default value for data queue data")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_QueueData_Enabled] - [0]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="QDTA(*NONE)")

        self.log.info("Check Default value for save access path")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_Save_Access_Path] - [*SYSVAL]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="ACCPTH(*SYSVAL)")

        self.log.info("Check Default value for save while active")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="SAVACT(*LIB)")

        self.log.info("Check Default value for save while active wait time")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_Save_ActiveWait_Time] - [0]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="SAVACTWAIT(0 ")

        self.log.info("Check Default value for save file data")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_SaveFileData_Enabled] - [1]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="SAVFDTA(*YES)")

        self.log.info("Check Default value for spool file data")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Backup_SpoolFileData_Enabled] - [0]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="SPLFDTA(*NONE")

        self.log.info("Check Default value for client side data compression")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[JOB_COMPRESSION_LEVEL] - [*NO]")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="DTACPR(*NO)")

        self.log.info("Check Default value for update history")
        self.verify_from_log('cvbkp*.log',
                             'Processing JOBLOG for',
                             jobid=job,
                             expectedvalue="UPDHST(*NO)")

        self.log.info("Check Default value for optimized scan option")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[ScanlessBackup] - [0]")

        self.log.info("Check Default value for target and release")
        self.verify_from_log('cvbkp*.log',
                             'processJobStartMessage',
                             jobid=job,
                             expectedvalue="[Target_release_For_Backup_Data] - []")

    def set_ibmi_sc_options(self, **kwargs):
        """
        set IBMi specific options to subclient.
        **kwargs               (dict)  : Dictionary of optional arguments.

                savact              (str)   : Value to which save while active option is set
                    default: '*LIB'
                    allowedValues: '*LIB' or '*NO' or '*SYSDFN' or *SYNCLIB

                savactwait          (int)   :  Amount of time to wait for check point in seconds.
                    default: 0

                savactmsgq          (str)   :  specify the name of the message queue in <lib>/<msgq> format.
                    example: QSYS/QSYSOPR

                sync_cmd            (str)   : specify the command which runs once backup reaches check-point
                    example: QGPL/SYNCREACH

                dtacpr              (str)   :  compression level on IBMi
                    default: '*NO'
                    allowedValues: *NO or *LOW or *MEDIUM or *HIGH

                dedupe_on_ibmi      (bool)  : dedeplication to run on IBMi client
                    default: False

                updhst              (bool)  : update backup history on IBMi client
                    default: False

                accpth              (str)   : save access path
                    default: "*SYSVAL"
                    allowedValues: "*SYSVAL" or "*YES" or "*NO"

                tgtrls              (str)   : OS release version of targeted IBMi for restore
                    default: ''
                    allowedValues: version of OS in the format of VXRXMX

                pvtaut              (bool)  : backup private authorities
                    default: False

                qdta                (bool)  : backup data inside data queue
                    default: False

                splfdta             (bool)  : backup spool files along with OUTQ object
                    default: False

                savfdta             (bool)  : backup save file data along with SAVF object
                    default: True

        Returns:
            None

        Raises:
            Exception:
                Raises exception if no inputs.

        Dict sample:
        sc_options = {'savact': '*LIB/*NO/*SYSDFN/*SYNCLIB',
                      'savactwait': '<Value in seconds>',
                      'savactmsgq': '<LIB_NAME>/<MSGQ_NAME>',
                      'sync_cmd': '<LIB_NAME>/<CMD_NAME>',
                      'dtacpr': '*NO/*LOW/*MEDIUM/*HIGH',
                      'dedupe_on_ibmi': 'True/False',
                      'updhst': 'True/False',
                      'accpth': '*SYSVAL/*YES/*NO',
                      'tgtrls': 'VXRXMX',
                      'pvtaut': 'True/False',
                      'qdta': 'True/False',
                      'splfdta': 'True/False',
                      'savfdta': 'True/False',
                      'pendingRecordChange' : '*LOCKWAIT/*NOCMTBDY/*NOMAX',
                      'otherPendingChange' : '*LOCKWAIT/*NOMAX'
                      }
        """
        if len(kwargs) == 0:
            self.log.info("inputs expected for function set_ibmi_sc_options()")
            raise Exception("No inputs received for function set_ibmi_sc_options()")

        self.log.info("setting the IBMi SC options {0}".format(kwargs))
        if 'savact' in kwargs.keys():
            if kwargs.get('savact') == "*SYNCLIB":
                synclib_config = {
                    'saveWhileActiveOpt': "*SYNCLIB",
                    'syncQueue': kwargs.get('savactmsgq'),
                    'syncAllLibForBackup': True,
                    'txtlibSyncCheckPoint': kwargs.get('sync_cmd', ''),
                    'activeWaitTime': kwargs.get('savactwait', 600)
                }
                self.log.info("set [SWA] to value [{0}]".format(synclib_config))
                self.testcase.subclient.enable_synclib = synclib_config
            else:
                swa_config = {
                    'saveWhileActiveOpt': kwargs.get('savact'),
                    'activeWaitTime': kwargs.get('savactwait', 0)}
                self.log.info("set [SWA] to value [{0}]".format(swa_config))
                self.testcase.subclient.save_while_active_option = swa_config

        if 'dtacpr' in kwargs.keys():
            self.log.info("set [DTACPR] to value [{0}]".format(kwargs.get('dtacpr')))
            self.testcase.subclient.ibmi_compression = kwargs.get('dtacpr')

        if 'dedupe_on_ibmi' in kwargs.keys():
            self.log.info("set [DEDUP ON IBMi] to value [{0}]".format(kwargs.get('dedupe_on_ibmi')))
            if kwargs.get('dedupe_on_ibmi'):
                self.testcase.subclient.generate_signature_on_ibmi = 1
            else:
                self.testcase.subclient.generate_signature_on_ibmi = 0

        if 'updhst' in kwargs.keys():
            self.log.info("set [UPDHST] to value [{0}]".format(kwargs.get('updhst')))
            if kwargs.get('updhst'):
                self.testcase.subclient.update_history = '*YES'
            else:
                self.testcase.subclient.update_history = '*NO'

        if 'accpth' in kwargs.keys():
            self.log.info("set [ACCPTH] to value [{0}]".format(kwargs.get('accpth')))
            self.testcase.subclient.save_access_path = kwargs.get('accpth')

        if 'tgtrls' in kwargs.keys():
            self.log.info("set [TGTRLS] to value [{0}]".format(kwargs.get('tgtrls')))
            self.testcase.subclient.target_release = kwargs.get('tgtrls')

        if 'pvtaut' in kwargs.keys():
            self.log.info("set [PVTAUT] to value [{0}]".format(kwargs.get('pvtaut')))
            self.testcase.subclient.backup_private_authorities = kwargs.get('pvtaut')

        if 'qdta' in kwargs.keys():
            self.log.info("set [QDTA] to value [{0}]".format(kwargs.get('qdta')))
            self.testcase.subclient.backup_queue_data = kwargs.get('qdta')

        if 'splfdta' in kwargs.keys():
            self.log.info("set [SPLFDTA] to value [{0}]".format(kwargs.get('splfdta')))
            self.testcase.subclient.backup_spool_file_data = kwargs.get('splfdta')

        if 'savfdta' in kwargs.keys():
            self.log.info("set [SAVFDTA] to value [{0}]".format(kwargs.get('savfdta')))
            self.testcase.subclient.backup_savf_file_data = kwargs.get('savfdta')

        if 'object_level' in kwargs.keys():
            self.log.info("set [OBJECT_LEVEL] to value [{0}]".format(kwargs.get('object_level')))
            self.testcase.subclient.object_level_backup = kwargs.get('object_level')

        if 'pendingRecordChange' in kwargs.keys():
            self.log.info("set [pendingRecordChange] to value [{0}]".format(kwargs.get('pendingRecordChange')))
            self.testcase.subclient.pending_record_changes = kwargs.get('pendingRecordChange')

        if 'otherPendingChange' in kwargs.keys():
            self.log.info("set [otherPendingChange] to value [{0}]".format(kwargs.get('otherPendingChange')))
            self.testcase.subclient.other_pending_changes = kwargs.get('otherPendingChange')
    
    def update_pre_post(self,
                        pre_scan_command=None,
                        post_scan_command=None,
                        pre_backup_command=None,
                        post_backup_command=None
                        ):
        """
                Sets the pre post commands on a subclient
                Args:

                        pre_scan_command    (str)       --     The pre scan command to be set
                        post_scan_command   (str)       --     The post scan command to be set
                        pre_backup_command  (str)       --     The pre backup command to be set
                        post_backup_command (str)       --     The post backup command to be set

                    Returns:
                        None

                    Raises:
                        None
        """
        pre_post_process = {}
        if pre_scan_command is not None:
            pre_post_process["pre_scan_command"] = pre_scan_command
        if post_scan_command is not None:
            pre_post_process["post_scan_command"] = post_scan_command
        if pre_backup_command is not None:
            pre_post_process["pre_backup_command"] = pre_backup_command
        if post_backup_command is not None:
            pre_post_process["post_backup_command"] = post_backup_command

        if pre_post_process != {}:
            self.log.info("updating pre-post commands for subclient with values %s", pre_post_process)
            self.testcase.subclient.pre_post_commands = pre_post_process
        else:
            self.log.info("pre-post commands are not updated")

    def verify_ibmi_sc_options(self, jobid, **kwargs):
        """
          Function to verify subclient options in client logs
                Args:
                        jobid           (str)  : Job ID

                **kwargs               (dict)  : Dictionary of optional arguments.

                        savact              (str)   : Value to which save while active option is set
                            default: '*LIB'
                            allowedValues: '*LIB' or '*NO' or '*SYSDFN' or *SYNCLIB

                        savactwait          (int)   :  Amount of time to wait for check point in seconds.
                            default: 0

                        savactmsgq          (str)   :  specify the name of the message queue in <lib>/<msgq> format.
                            example: QSYS/QSYSOPR

                        sync_cmd            (str)   : specify the command which runs once backup reaches check-point
                            example: QGPL/SYNCREACH

                        dtacpr              (str)   :  compression level on IBMi
                            default: '*NO'
                            allowedValues: *NO or *LOW or *MEDIUM or *HIGH

                        dedupe_on_ibmi      (bool)  : dedeplication to run on IBMi client
                            default: False

                        updhst              (bool)  : update backup history on IBMi client
                            default: False

                        accpth              (str)   : save access path
                            default: "*SYSVAL"
                            allowedValues: "*SYSVAL" or "*YES" or "*NO"

                        object_level        (bool)  : backup library content as objects
                            default: False
                            allowedValues: True or False

                        tgtrls              (str)   : OS release version of targeted IBMi for restore
                            default: ''
                            allowedValues: version of OS in the format of VXRXMX

                        pvtaut              (bool)  : backup private authorities
                            default: False

                        qdta                (bool)  : backup data inside data queue
                            default: False

                        splfdta             (bool)  : backup spool files along with OUTQ object
                            default: False

                        savfdta             (bool)  : backup save file data along with SAVF object
                            default: True

                Returns:
                    None

                Raises:
                    Exception:
                        Raises exception if no inputs.

                Dict sample:
                sc_options = {'savact': '*LIB/*NO/*SYSDFN/*SYNCLIB',
                              'savactwait': '<Value in seconds>',
                              'savactmsgq': '<LIB_NAME>/<MSGQ_NAME>',
                              'sync_cmd': '<LIB_NAME>/<CMD_NAME>',
                              'dtacpr': '*NO/*LOW/*MEDIUM/*HIGH',
                              'dedupe_on_ibmi': 'True/False',
                              'updhst': 'True/False',
                              'accpth': '*SYSVAL/*YES/*NO',
                              'tgtrls': 'VXRXMX',
                              'pvtaut': 'True/False',
                              'qdta': 'True/False',
                              'splfdta': 'True/False',
                              'savfdta': 'True/False'
                                  }
                """

        if len(kwargs) == 0:
            self.log.info("inputs expected for function verify_ibmi_sc_options()")
            raise Exception("No inputs received for function verify_ibmi_sc_options()")

        if 'savact' in kwargs.keys():
            self.log.info("Verify the client logs for option [SWA] with value [{0}]".format(kwargs.get('savact')))
            self.verify_from_log('cvbkp*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Backup_SAVACT] - [{0}]".format(kwargs.get('savact')))
            if kwargs.get('savact') == "*SYNCLIB":
                self.log.info("Verify the client logs for option [SAVACT] with value [{0}]".format(
                    kwargs.get('savact')))
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SyncLib_Enabled] - [1]")
                if 'savactmsgq' in kwargs.keys():
                    self.log.info("Verify the client logs for option [SAVCATMSGQ] with value [{0}]".format(
                        kwargs.get('savactmsgq')))
                    self.verify_from_log('cvbkp*.log',
                                         'processJobStartMessage',
                                         jobid=jobid,
                                         expectedvalue="[Backup_Sync_Queue] - [{0}]".format(
                                             kwargs.get('savactmsgq')))
                if 'sync_cmd' in kwargs.keys():
                    self.log.info("Verify the client logs for option [SYNCCMD] with value [{0}]".format(
                        kwargs.get('sync_cmd')))
                    self.verify_from_log('cvbkp*.log',
                                         'processJobStartMessage',
                                         jobid=jobid,
                                         expectedvalue="[Backup_LibSync_Checkpoint] - [{0}]".format(
                                             kwargs.get('sync_cmd')))
            else:
                self.log.info("Verify the client logs for option [SWA] with value [{0}]".format(
                    kwargs.get('savact')))
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SyncLib_Enabled] - [0]")

        if 'savactwait' in kwargs.keys():
            self.log.info("Verify the client logs for option [SAVACTWAIT] with value [{0}]".format(
                kwargs.get('savactwait')))
            self.verify_from_log('cvbkp*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Backup_Save_ActiveWait_Time] - [{0}]".format(
                                     kwargs.get('savactwait')))
            self.verify_from_log('cvbkp*.log',
                                 'Processing JOBLOG for',
                                 jobid=jobid,
                                 expectedvalue="SAVACTWAIT({0}".format(kwargs.get('savactwait')))

        if 'dtacpr' in kwargs.keys():
            self.log.info("Verify the client logs for option [DTACPR] with value [{0}]".format(kwargs.get('dtacpr')))
            self.verify_from_log('cvbkp*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[JOB_COMPRESSION_LEVEL] - [{0}]".format(kwargs.get('dtacpr')))
            self.verify_from_log('cvbkp*.log',
                                 'Processing JOBLOG for',
                                 jobid=jobid,
                                 expectedvalue="DTACPR({0})".format(kwargs.get('dtacpr')))

        if 'dedupe_on_ibmi' in kwargs.keys():
            self.log.info("Verify the client logs for option [DEDUP_ON_IBMi] with value [{0}]".format(
                kwargs.get('dedupe_on_ibmi')))
            if kwargs.get('dedupe_on_ibmi'):
                self.verify_from_log('cvbkp*.log',
                                     'ClientBackup::doBackup',
                                     jobid=jobid,
                                     expectedvalue="Prepipeline deduplication configured.")
            else:
                self.verify_from_log('cvbkp*.log',
                                     'ClientBackup::doBackup',
                                     jobid=jobid,
                                     expectedvalue="Deduplication will happen on Proxy.")

        if 'updhst' in kwargs.keys():
            self.log.info("Verify the client logs for option [UPDHST] with value [{0}]".format(kwargs.get('updhst')))
            if 'savact' not in kwargs.keys() or kwargs.get('savact') != "*SYNCLIB":
                if kwargs.get('updhst'):
                    self.verify_from_log('cvbkp*.log',
                                         'Processing JOBLOG for',
                                         jobid=jobid,
                                         expectedvalue="UPDHST({0})".format('*YES'))
                else:
                    self.verify_from_log('cvbkp*.log',
                                         'Processing JOBLOG for',
                                         jobid=jobid,
                                         expectedvalue="UPDHST({0})".format('*NO'))

        if 'accpth' in kwargs.keys():
            self.log.info("Verify the client logs for option [ACCPTH] with value [{0}]".format(kwargs.get('accpth')))
            if 'savact' not in kwargs.keys() or kwargs.get('savact') != "*SYNCLIB":
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_Save_Access_Path] - [{0}]".format(kwargs.get('accpth')))
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="ACCPTH({0})".format(kwargs.get('accpth')))

        if 'tgtrls' in kwargs.keys():
            self.log.info("Verify the client logs for option [TGTRLS] with value [{0}]".format(kwargs.get('tgtrls')))
            self.verify_from_log('cvbkp*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Target_release_For_Backup_Data] - [{0}]".format(
                                     kwargs.get('tgtrls')))

        if 'pvtaut' in kwargs.keys():
            self.log.info("Verify the client logs for option [PVTAUT] with value [{0}]".format(kwargs.get('pvtaut')))
            if kwargs.get('pvtaut'):
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*YES)")
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_PrivateAuthority_Enabled] - [1]")
            else:
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*NO)")
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_PrivateAuthority_Enabled] - [0]")

        if 'qdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [QDTA] with value [{0}]".format(kwargs.get('qdta')))
            if kwargs.get('qdta'):
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_QueueData_Enabled] - [1]")
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="QDTA(*DTAQ)")
            else:
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_QueueData_Enabled] - [0]")
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="QDTA(*NONE)")

        if 'splfdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [SPLFDTA] with value [{0}]".format(kwargs.get('splfdta')))
            if kwargs.get('splfdta'):
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SpoolFileData_Enabled] - [1]")
                '''self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="SPLFDTA(*ALL")'''
            else:
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SpoolFileData_Enabled] - [0]")
                '''self.verify_from_log('cvbkp*.log',
                                 'Processing JOBLOG for',
                                 jobid=jobid,
                                 expectedvalue="SPLFDTA(*NONE")'''

        if 'savfdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [SAVFDTA] with value [{0}]".format(kwargs.get('savfdta')))
            if kwargs.get('savfdta'):
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SaveFileData_Enabled] - [1]")
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="SAVFDTA(*YES)")
            else:
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SaveFileData_Enabled] - [0]")
                self.verify_from_log('cvbkp*.log',
                                     'Processing JOBLOG for',
                                     jobid=jobid,
                                     expectedvalue="SAVFDTA(*NO)")

            if 'object_level' in kwargs.keys():
                self.log.info("Verify the client logs for option [Object_Level] "
                              "with value [{0}]".format(kwargs.get('object_level')))
                if kwargs.get('object_level'):
                    self.verify_from_log('cvscan*.log',
                                         'ProcessWorkUnit',
                                         jobid=jobid,
                                         expectedvalue="Backup running in object level mode")
                else:
                    self.verify_from_log('cvscan*.log',
                                         'ProcessWorkUnit',
                                         jobid=jobid,
                                         expectedvalue="Backup running in library level mode")

    def verify_vtl_multistream(self, job, no_of_streams):
        """ Function to verify if mutiple streams used by VTL backup.
            Args:
                job                 (str)-- Job details
                no_of_streams       (int)-- number of streams
            Returns:
                None
            Raises:
                Exception - error while verifying logs for default values.
        """
        self.log.info("Check if {0} streams are used by VTL backup.".format(no_of_streams))
        self.verify_from_log(logfile='cvbkpvtl*.log',
                             regex='getDataStreamSocket',
                             jobid=job.job_id,
                             expectedvalue="All {0} tapes obtained".format(no_of_streams))
        self.verify_from_log(logfile='cvbkpvtl*.log',
                             regex='MediaDefinition',
                             jobid=job.job_id,
                             expectedvalue="created")
        self.verify_from_log(logfile='cvbkpvtl*.log',
                             regex='runEachCommand',
                             jobid=job.job_id,
                             expectedvalue="DEV(*MEDDFN) MEDDFN")

    def verify_vtl_multistream_restore(self, job, no_of_streams):
        """ Function to verify if mutiple streams used by VTL restore.
            Args:
                job                 (str)-- Job details
                no_of_streams       (int)-- number of streams
            Returns:
                None
            Raises:
                Exception - error while verifying logs for default values.
        """
        self.log.info("Check if {0} streams are used by VTL backup.".format(no_of_streams))
        self.verify_from_log(logfile='cvrest*.log',
                             regex='Setting Media Definition',
                             jobid=job.job_id,
                             expectedvalue="with {0} drives".format(no_of_streams))
        self.verify_from_log(logfile='cvrest*.log',
                             regex='MediaDefinition',
                             jobid=job.job_id,
                             expectedvalue="created")
        self.verify_from_log(logfile='cvrest*.log',
                             regex='TapeRestoreHandlerImpl',
                             jobid=job.job_id,
                             expectedvalue="DEV(*MEDDFN) MEDDFN")

    def verify_ibmi_vtl_sc_options(self, jobid, backup_level="Full", **kwargs):
        """
          Function to verify subclient options in client logs for VTL backups.
                Args:
                        jobid           (str)  : Job ID

                        backup_level            (str)   --  level of backup
                        (Full/Incremental/Differential)
                        default: Full

                **kwargs               (dict)  : Dictionary of optional arguments.

                        savact              (str)   : Value to which save while active option is set
                            default: '*LIB'
                            allowedValues: '*LIB' or '*NO' or '*SYSDFN' or *SYNCLIB

                        savactwait          (int)   :  Amount of time to wait for check point in seconds.
                            default: 0

                        savactmsgq          (str)   :  specify the name of the message queue in <lib>/<msgq> format.
                            example: QSYS/QSYSOPR

                        sync_cmd            (str)   : specify the command which runs once backup reaches check-point
                            example: QGPL/SYNCREACH

                        dtacpr              (str)   :  compression level on IBMi
                            default: '*NO'
                            allowedValues: *NO or *LOW or *MEDIUM or *HIGH

                        updhst              (bool)  : update backup history on IBMi client
                            default: False

                        accpth              (str)   : save access path
                            default: "*SYSVAL"
                            allowedValues: "*SYSVAL" or "*YES" or "*NO"

                        object_level        (bool)  : backup library content as objects
                            default: False
                            allowedValues: True or False

                        tgtrls              (str)   : OS release version of targeted IBMi for restore
                            default: ''
                            allowedValues: version of OS in the format of VXRXMX

                        pvtaut              (bool)  : backup private authorities
                            default: False

                        qdta                (bool)  : backup data inside data queue
                            default: False

                        splfdta             (bool)  : backup spool files along with OUTQ object
                            default: False

                        savfdta             (bool)  : backup save file data along with SAVF object
                            default: True

                Returns:
                    None

                Raises:
                    Exception:
                        Raises exception if no inputs.

                Dict sample:
                sc_options = {'savact': '*LIB/*NO/*SYSDFN/*SYNCLIB',
                              'savactwait': '<Value in seconds>',
                              'savactmsgq': '<LIB_NAME>/<MSGQ_NAME>',
                              'sync_cmd': '<LIB_NAME>/<CMD_NAME>',
                              'dtacpr': '*NO/*LOW/*MEDIUM/*HIGH',
                              'updhst': 'True/False',
                              'accpth': '*SYSVAL/*YES/*NO',
                              'tgtrls': 'VXRXMX',
                              'pvtaut': 'True/False',
                              'qdta': 'True/False',
                              'splfdta': 'True/False',
                              'savfdta': 'True/False'
                                  }
                """

        if len(kwargs) == 0:
            self.log.info("inputs expected for function verify_ibmi_sc_options()")
            raise Exception("No inputs received for function verify_ibmi_sc_options()")

        if 'savact' in kwargs.keys():
            self.log.info("Verify the client logs for option [SWA] with value [{0}]".format(kwargs.get('savact')))
            self.verify_from_log('cvbkpvtl*.log',
                                 'runEachCommand',
                                 jobid=jobid,
                                 expectedvalue="SAVACT({0})".format(kwargs.get('savact')))
            if kwargs.get('savact') == "*SYNCLIB":
                self.log.info("Verify the client logs for option [SAVACT] with value [{0}]".format(
                    kwargs.get('savact')))
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SyncLib_Enabled] - [1]")
                if 'savactmsgq' in kwargs.keys():
                    self.log.info("Verify the client logs for option [SAVCATMSGQ] with value [{0}]".format(
                        kwargs.get('savactmsgq')))
                    self.verify_from_log('cvbkp*.log',
                                         'processJobStartMessage',
                                         jobid=jobid,
                                         expectedvalue="[Backup_Sync_Queue] - [{0}]".format(
                                             kwargs.get('savactmsgq')))
                if 'sync_cmd' in kwargs.keys():
                    self.log.info("Verify the client logs for option [SYNCCMD] with value [{0}]".format(
                        kwargs.get('sync_cmd')))
                    self.verify_from_log('cvbkp*.log',
                                         'processJobStartMessage',
                                         jobid=jobid,
                                         expectedvalue="[Backup_LibSync_Checkpoint] - [{0}]".format(
                                             kwargs.get('sync_cmd')))
            else:
                self.log.info("Verify the client logs for option [SWA] with value [{0}]".format(
                    kwargs.get('savact')))
                self.verify_from_log('cvbkp*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Backup_SyncLib_Enabled] - [0]")

        if 'savactwait' in kwargs.keys():
            self.log.info("Verify the client logs for option [SAVACTWAIT] with value [{0}]".format(
                kwargs.get('savactwait')))
            self.verify_from_log('cvbkpvtl*.log',
                                 'runEachCommand',
                                 jobid=jobid,
                                 expectedvalue="SAVACTWAIT({0}".format(kwargs.get('savactwait')))

        if 'dtacpr' in kwargs.keys():
            self.log.info("Verify the client logs for option [DTACPR] with value [{0}]".format(kwargs.get('dtacpr')))
            self.verify_from_log('cvbkp*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[JOB_COMPRESSION_LEVEL] - [{0}]".format(kwargs.get('dtacpr')))
            # self.verify_from_log('cvbkpvtl*.log',
            #                      'runEachCommand',
            #                      jobid=jobid,
            #                      expectedvalue="DTACPR({0})".format(kwargs.get('dtacpr')))

        if 'updhst' in kwargs.keys():
            self.log.info("Verify the client logs for option [UPDHST] with value [{0}]".format(kwargs.get('updhst')))
            if 'savact' not in kwargs.keys() or kwargs.get('savact') != "*SYNCLIB":
                if kwargs.get('updhst'):
                    self.verify_from_log('cvbkpvtl*.log',
                                         'runEachCommand',
                                         jobid=jobid,
                                         expectedvalue="UPDHST(*YES)")
                else:
                    self.verify_from_log('cvbkpvtl*.log',
                                         'runEachCommand',
                                         jobid=jobid,
                                         expectedvalue="UPDHST(*NO)")

        if 'accpth' in kwargs.keys():
            self.log.info("Verify the client logs for option [ACCPTH] with value [{0}]".format(kwargs.get('accpth')))
            if 'savact' not in kwargs.keys() or kwargs.get('savact') != "*SYNCLIB":
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="ACCPTH({0})".format(kwargs.get('accpth')))

        if 'tgtrls' in kwargs.keys():
            self.log.info("Verify the client logs for option [TGTRLS] with value [{0}]".format(kwargs.get('tgtrls')))
            if kwargs.get('pvtaut'):
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="TGTRLS({0})".format(kwargs.get('tgtrls')))

        if 'pvtaut' in kwargs.keys():
            self.log.info("Verify the client logs for option [PVTAUT] with value [{0}]".format(kwargs.get('pvtaut')))
            if kwargs.get('pvtaut'):
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*YES)")
            else:
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*NO)")

        if 'qdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [QDTA] with value [{0}]".format(kwargs.get('qdta')))
            if kwargs.get('qdta'):
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="QDTA(*DTAQ)")
            else:
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="QDTA(*NONE)")

        if 'splfdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [SPLFDTA] with value [{0}]".format(kwargs.get('splfdta')))
            if kwargs.get('splfdta'):
                if backup_level == "Full":
                    self.verify_from_log('cvbkpvtl*.log',
                                         'runEachCommand',
                                         jobid=jobid,
                                         expectedvalue="SPLFDTA(*ALL")
                # else:
                #     self.verify_from_log('cvbkpvtl*.log',
                #                          'runEachCommand',
                #                          jobid=jobid,
                #                          expectedvalue="SPLFDTA(*NEW")
            else:
                if backup_level == "Full":
                    self.verify_from_log('cvbkpvtl*.log',
                                         'runEachCommand',
                                         jobid=jobid,
                                         expectedvalue="SPLFDTA(*NONE")

        if 'savfdta' in kwargs.keys():
            self.log.info("Verify the client logs for option [SAVFDTA] with value [{0}]".format(kwargs.get('savfdta')))
            if kwargs.get('savfdta'):
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="SAVFDTA(*YES)")
            else:
                self.verify_from_log('cvbkpvtl*.log',
                                     'runEachCommand',
                                     jobid=jobid,
                                     expectedvalue="SAVFDTA(*NO)")
    
    def verify_adv_restore_options(self, jobid, **kwargs):
        """
          Function to verify advanced restore options in client logs
                Args:
                        jobid           (str)  : Job ID

                **kwargs               (dict)  : Dictionary of optional arguments.

                        PVTAUT              (bool)  : Restore private authorities
                            default: False

                        SPLFDTA             (bool)  : Restore spool file data
                            default: True

                        FRCOBJCVN           (str)   :  Force object conversion
                            default: '*SYSVAL'
                            allowedValues: *SYSVAL or *NO or "*YES *RQD" or "*YES *ALL"

                        SECDTA              (str)   :  what to restore with secuirty data
                            default: '*USRPRF'
                            allowedValues: *USRPRF or *PVTAUT or *PWDGRP or *DCM

                        DFRID              (str)   :  restore using defered procedure using this ID.
                            default: '*NONE'

                        ALOWOBJDIF              (str)   :  Allow object difference
                            default: 'NONE'
                            allowedValues:NONE or *ALL or *COMPATIBLE or OTHER

                        autl      (bool)  : authorization list
                            default: False

                        fileLevel      (bool)  : file level restore
                            default: False

                        owner      (bool)  : owner restore
                            default: False

                        pgp           (bool)  : pgp restore
                            default: False

                Returns:
                    None

                Raises:
                    Exception:
                        Raises exception if no inputs.

                Dict sample:
                ibmi_restore_opt = {
                    'PVTAUT': False/True,
                    'SPLFDTA': True/False,
                    'FRCOBJCVN': "*SYSVAL/*NO/*YES *RQD/*YES *ALL",
                    'SECDTA': *USRPRF/*PVTAUT/*PWDGRP/*DCM,
                    'DFRID': *NONE/<STRING>,
                    'ALOWOBJDIF': None/*ALL/*COMPATIBLE/OTHER,
                    'autl': True/False,
                    'fileLevel': True/False,
                    'owner': True/False,
                    'pgp': True/False,
                    }
                """

        if len(kwargs) == 0:
            self.log.info("inputs expected for function verify_adv_restore_options()")
            raise Exception("No inputs received for function verify_adv_restore_options()")

        if 'PVTAUT' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [PVTAUT] with value [{0}]".
                          format(kwargs.get('PVTAUT')))
            if kwargs.get('PVTAUT') is True:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_PrivateAuthority_Enabled] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*YES)")
            else:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_PrivateAuthority_Enabled] - [0]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*NO)")

        if 'SPLFDTA' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [SPLFDTA] with value [{0}]".
                          format(kwargs.get('SPLFDTA')))
            if kwargs.get('SPLFDTA') is True:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_SpoolFileData_Enabled] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="SPLFDTA(*NEW)")
            else:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_SpoolFileData_Enabled] - [0]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="SPLFDTA(*NONE)")

        if 'FRCOBJCVN' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [FRCOBJCVN] with value [{0}]".
                          format(kwargs.get('FRCOBJCVN')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Force_ObjectConversion_Selection] - [{0}]".format(
                                     kwargs.get('FRCOBJCVN')))
            self.verify_from_log('cvrest*.log',
                                 'QaneRsta',
                                 jobid=jobid,
                                 expectedvalue="FRCOBJCVN({0})".format(kwargs.get('FRCOBJCVN')))

        if 'SECDTA' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [SECDTA] with value [{0}]".
                          format(kwargs.get('SECDTA')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Security_Data_Param] - [{0}]".format(
                                     kwargs.get('SECDTA')))

        if 'DFRID' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [DFRID] with value [{0}]".
                          format(kwargs.get('DFRID')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Defer_ID] - [{0}]".format(
                                     kwargs.get('DFRID')))
            if kwargs.get('DFRID') != "*NONE":
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="DFRID({0})".format(kwargs.get('DFRID')))
                self.verify_from_log('cvrest*.log',
                                     'Final_Cleanup',
                                     jobid=jobid,
                                     expectedvalue="RSTDFROBJ DFRID({0})".format(kwargs.get('DFRID')))
            else:
                self.verify_from_log('cvrest*.log',
                                     'Final_Cleanup',
                                     jobid=jobid,
                                     expectedvalue="RSTDFROBJ DFRID() is not called this time")

        if 'ALOWOBJDIF' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [ALOWOBJDIF] with value [{0}]".
                          format(kwargs.get('ALOWOBJDIF')))
            if kwargs.get('ALOWOBJDIF') == "*ALL":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="ALWOBJDIF({0})".format(kwargs.get('ALOWOBJDIF')))
            elif kwargs.get('ALOWOBJDIF') == "*COMPATIBLE":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [2]")
                self.verify_from_log('cvrest*.log',
                                     'QaneRsta',
                                     jobid=jobid,
                                     expectedvalue="ALWOBJDIF({0})".format(kwargs.get('ALOWOBJDIF')))
            elif kwargs.get('ALOWOBJDIF') == "OTHER":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [3]")
                if 'autl' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [autl] with value [{0}]".
                                  format(kwargs.get('autl')))
                    if kwargs.get('autl') is True:
                        self.verify_from_log('cvrest*.log',
                                             'QaneRsta',
                                             jobid=jobid,
                                             expectedvalue="*AUTL")
                if 'fileLevel' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [fileLevel] with value [{0}]".
                                  format(kwargs.get('fileLevel')))
                    if kwargs.get('fileLevel') is True:
                        self.verify_from_log('cvrest*.log',
                                             'QaneRsta',
                                             jobid=jobid,
                                             expectedvalue="*FILELVL")
                if 'owner' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [owner] with value [{0}]".
                                  format(kwargs.get('owner')))
                    if kwargs.get('owner') is True:
                        self.verify_from_log('cvrest*.log',
                                             'QaneRsta',
                                             jobid=jobid,
                                             expectedvalue="*OWNER")
                if 'pgp' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [pgp] with value [{0}]".
                                  format(kwargs.get('pgp')))
                    if kwargs.get('pgp') is True:
                        self.verify_from_log('cvrest*.log',
                                             'QaneRsta',
                                             jobid=jobid,
                                             expectedvalue="*PGP")

    def verify_adv_restore_options_vtl(self, jobid, **kwargs):
        """
          Function to verify advanced restore options in client logs for vtl
                Args:
                        jobid           (str)  : Job ID

                **kwargs               (dict)  : Dictionary of optional arguments.

                        PVTAUT              (bool)  : Restore private authorities
                            default: False

                        SPLFDTA             (bool)  : Restore spool file data
                            default: True

                        FRCOBJCVN           (str)   :  Force object conversion
                            default: '*SYSVAL'
                            allowedValues: *SYSVAL or *NO or "*YES *RQD" or "*YES *ALL"

                        SECDTA              (str)   :  what to restore with secuirty data
                            default: '*USRPRF'
                            allowedValues: *USRPRF or *PVTAUT or *PWDGRP or *DCM

                        DFRID              (str)   :  restore using defered procedure using this ID.
                            default: '*NONE'

                        ALOWOBJDIF              (str)   :  Allow object difference
                            default: 'NONE'
                            allowedValues:NONE or *ALL or *COMPATIBLE or OTHER

                        autl      (bool)  : authorization list
                            default: False

                        fileLevel      (bool)  : file level restore
                            default: False

                        owner      (bool)  : owner restore
                            default: False

                        pgp           (bool)  : pgp restore
                            default: False

                Returns:
                    None

                Raises:
                    Exception:
                        Raises exception if no inputs.

                Dict sample:
                ibmi_restore_opt = {
                    'PVTAUT': False/True,
                    'SPLFDTA': True/False,
                    'FRCOBJCVN': "*SYSVAL/*NO/*YES *RQD/*YES *ALL",
                    'SECDTA': *USRPRF/*PVTAUT/*PWDGRP/*DCM,
                    'DFRID': *NONE/<STRING>,
                    'ALOWOBJDIF': None/*ALL/*COMPATIBLE/OTHER,
                    'autl': True/False,
                    'fileLevel': True/False,
                    'owner': True/False,
                    'pgp': True/False,
                    }
                """

        if len(kwargs) == 0:
            self.log.info("inputs expected for function verify_adv_restore_options()")
            raise Exception("No inputs received for function verify_adv_restore_options()")

        if 'PVTAUT' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [PVTAUT] with value [{0}]".
                          format(kwargs.get('PVTAUT')))
            if kwargs.get('PVTAUT') is True:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_PrivateAuthority_Enabled] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*YES)")
            else:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_PrivateAuthority_Enabled] - [0]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="PVTAUT(*NO)")

        if 'SPLFDTA' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [SPLFDTA] with value [{0}]".
                          format(kwargs.get('SPLFDTA')))
            if kwargs.get('SPLFDTA') is True:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_SpoolFileData_Enabled] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="SPLFDTA(*NEW)")
            else:
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="Restore_SpoolFileData_Enabled] - [0]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="SPLFDTA(*NONE)")

        if 'FRCOBJCVN' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [FRCOBJCVN] with value [{0}]".
                          format(kwargs.get('FRCOBJCVN')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Force_ObjectConversion_Selection] - [{0}]".format(
                                     kwargs.get('FRCOBJCVN')))
            self.verify_from_log('cvrest*.log',
                                 'executeRestore',
                                 jobid=jobid,
                                 expectedvalue="FRCOBJCVN({0})".format(kwargs.get('FRCOBJCVN')))

        if 'SECDTA' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [SECDTA] with value [{0}]".
                          format(kwargs.get('SECDTA')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Security_Data_Param] - [{0}]".format(
                                     kwargs.get('SECDTA')))

        if 'DFRID' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [DFRID] with value [{0}]".
                          format(kwargs.get('DFRID')))
            self.verify_from_log('cvrest*.log',
                                 'processJobStartMessage',
                                 jobid=jobid,
                                 expectedvalue="[Restore_Defer_ID] - [{0}]".format(
                                     kwargs.get('DFRID')))
            if kwargs.get('DFRID') != "*NONE":
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="DFRID({0})".format(kwargs.get('DFRID')))
                self.verify_from_log('cvrest*.log',
                                     'Final_Cleanup',
                                     jobid=jobid,
                                     expectedvalue="RSTDFROBJ DFRID({0})".format(kwargs.get('DFRID')))
            else:
                self.verify_from_log('cvrest*.log',
                                     'Final_Cleanup',
                                     jobid=jobid,
                                     expectedvalue="RSTDFROBJ DFRID() is not called this time")

        if 'ALOWOBJDIF' in kwargs.keys():
            self.log.info("Verify the client logs for restore option [ALOWOBJDIF] with value [{0}]".
                          format(kwargs.get('ALOWOBJDIF')))
            if kwargs.get('ALOWOBJDIF') == "*ALL":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [1]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="ALWOBJDIF({0})".format(kwargs.get('ALOWOBJDIF')))
            elif kwargs.get('ALOWOBJDIF') == "*COMPATIBLE":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [2]")
                self.verify_from_log('cvrest*.log',
                                     'executeRestore',
                                     jobid=jobid,
                                     expectedvalue="ALWOBJDIF({0})".format(kwargs.get('ALOWOBJDIF')))
            elif kwargs.get('ALOWOBJDIF') == "OTHER":
                self.verify_from_log('cvrest*.log',
                                     'processJobStartMessage',
                                     jobid=jobid,
                                     expectedvalue="[Restore_Allow_Object_Difference_Type] - [3]")
                if 'autl' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [autl] with value [{0}]".
                                  format(kwargs.get('autl')))
                    if kwargs.get('autl') is True:
                        self.verify_from_log('cvrest*.log',
                                             'executeRestore',
                                             jobid=jobid,
                                             expectedvalue="*AUTL")
                if 'fileLevel' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [fileLevel] with value [{0}]".
                                  format(kwargs.get('fileLevel')))
                    if kwargs.get('fileLevel') is True:
                        self.verify_from_log('cvrest*.log',
                                             'executeRestore',
                                             jobid=jobid,
                                             expectedvalue="*FILELVL")
                if 'owner' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [owner] with value [{0}]".
                                  format(kwargs.get('owner')))
                    if kwargs.get('owner') is True:
                        self.verify_from_log('cvrest*.log',
                                             'executeRestore',
                                             jobid=jobid,
                                             expectedvalue="*OWNER")
                if 'pgp' in kwargs.keys():
                    self.log.info("Verify the client logs for restore option [pgp] with value [{0}]".
                                  format(kwargs.get('pgp')))
                    if kwargs.get('pgp') is True:
                        self.verify_from_log('cvrest*.log',
                                             'executeRestore',
                                             jobid=jobid,
                                             expectedvalue="*PGP")

