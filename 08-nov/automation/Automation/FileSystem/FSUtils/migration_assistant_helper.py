# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing operations related to the Migration Assistance feature.

MigrationAssistantHelper is the only class defined in this file.

MigrationAssistantHelper: Helper class to perform operations for the Migration Assistance feature.

MigrationAssistantHelper:
=========================
    __init__()                              --  Initializes MA helper object.

    populate_migration_assistant_inputs()   --  Initializes the MA specific attributes
    in addition to calling FSHelper.populate_tc_inputs() to initialize all other inputs.

    create_default_backupset()              --  Creates a new backup set with the provided name
    if it doesn't exist and sets it as the default backup set.

    get_ma_entries_from_machine()           --  Prepares a list of entries
    from the machine that should get backed up as part of Migration Assistant User Settings.

    get_ma_entries_from_cvfs()              --  Prepares a list of MA entries
    from the collect file.

    collect_registry_entries()              --  Collects registry entries
    from the specified machine under a specified sub key.

    compare_lists()                         --  Compares the source list with destination list
    and checks for equality or if the entries in the destination list can
    form a subset of the entries in the source list.

    get_sid_for_user_profile()              --  Retrieves the SID for the user profile.

    run_sync_restore()                      --  Launches a Sync. Restore job
    on the specified destination client.

    get_moniker_paths()                     --  Fetches the path for each of the monikers
    from the machine for the given user profile.

    perform_ma_validation()                 --  Validates whether the collect file has all
    the MA entries by comparing it against a list of expected MA entries from the machine.

    generate_test_data_for_ma()             --  Generates test data under the well-known folders.

    ma_restore_verify()                     --  Initiates restore for data backed up in the
    given job and performs the applicable verifications.

    delete_dataset_for_ma()                 --  Cleans up the dataset created under well known folders.

MigrationAssistantHelper Instance Attributes:
=============================================

    **moniker_dict**    --  Returns a dictionary of monikers to their paths on the client machine.

"""

import re
from copy import deepcopy
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from FileSystem.FSUtils import fs_constants
from AutomationUtils.machine import Machine
from cvpysdk.client import Client
from .fshelper import FSHelper


class MigrationAssistantHelper(FSHelper):
    """Helper class to perform Migration Assistance operations"""

    def create_MigrationAssistantHelper_object(self, machine_name=None, commcell_object=None):

        """Returns the instance of one of the Subclasses MigrationAssisatntHelper for MAc/Windows,
            based on the OS details of the remote client.

            If Commcell Object is given, and the Client is Commvault Client:
                Gets the OS Info from Client OS Info attribute

            Otherwise, Pings the client, and decides the OS based on the TTL value.

            TTL Value: 64 (Linux) / 128 (Windows) / 255 (UNIX)

        """
        if machine_name:
            client = None

            if isinstance(machine_name, Client):
                client = machine_name
            else:
                if (commcell_object is not None and
                        commcell_object.clients.has_client(machine_name)):
                        client = commcell_object.clients.get(machine_name)

            if 'mac' in client.os_info.lower():
                return MigrationAssistantHelperMac(self)
            elif 'windows' in client.os_info.lower():
                return MigrationAssistantHelper(self)


    def __init__(self, testcase):
        """Initialize instance of the UnixFSHelper class."""
        self._moniker_dict = None
        super(MigrationAssistantHelper, self).__init__(testcase)
        self.populate_migration_assistant_inputs(testcase)
        self.log = logger.get_log()

    @property
    def moniker_dict(self):
        return self._moniker_dict

    @moniker_dict.setter
    def moniker_dict(self, value):
        self._moniker_dict = self.get_moniker_paths(value[0], value[1])

    @staticmethod
    def populate_migration_assistant_inputs(cv_testcase, mandatory=True):
        """Initializes all the test case inputs after validation

        Args:
            cv_testcase     (object)    --  Object of CVTestCase.

            mandatory       (bool)      --  Whether to check for mandatory inputs
            and raise exception if not found.

                default:    True

        Returns:
             None   -   If the inputs were populated successfully.

        Raises:
            Exception:
                If a valid CVTestCase object is not passed.

                If CVTestCase object doesn't have agent initialized.

        """

        if not isinstance(cv_testcase, CVTestCase):
            raise Exception("Valid test case object must be passed as argument")

        cv_testcase.src_client = cv_testcase.commcell.clients.get(cv_testcase.tcinputs.get('SourceClient', None))
        cv_testcase.dst_client = cv_testcase.commcell.clients.get(cv_testcase.tcinputs.get('DestinationClient', None))
        cv_testcase.src_machine = Machine(cv_testcase.src_client, cv_testcase.commcell)
        cv_testcase.dst_machine = Machine(cv_testcase.dst_client, cv_testcase.commcell)
        if cv_testcase.tcinputs.get('SourceProfile').find(cv_testcase.src_machine.os_sep) != -1:
            cv_testcase.src_domain = cv_testcase.tcinputs.get('SourceProfile').split(cv_testcase.src_machine.os_sep)[0]
            cv_testcase.src_user_acc = cv_testcase.tcinputs.get('SourceProfile').split(cv_testcase.src_machine.os_sep)[1]
            cv_testcase.src_user_acc = cv_testcase.tcinputs.get('SourceProfile')
            cv_testcase.dst_domain = cv_testcase.tcinputs.get(
                'DestinationProfile').split(cv_testcase.dst_machine.os_sep)[0]
            cv_testcase.dst_user_acc = cv_testcase.tcinputs.get(
                'DestinationProfile').split(cv_testcase.dst_machine.os_sep)[1]
        else:
            cv_testcase.src_user_acc = cv_testcase.tcinputs.get('SourceProfile')
            cv_testcase.dst_user_acc = cv_testcase.tcinputs.get('DestinationProfile')

        cv_testcase.storage_policy = cv_testcase.tcinputs.get('StoragePolicyName', None)
        cv_testcase.agent = (cv_testcase.src_client).agents.get(cv_testcase.tcinputs['AgentName'])

        if(cv_testcase.storage_policy is None and mandatory):
            raise Exception("StoragePolicyName is mandatory for this test case")

        cv_testcase.client_machine = cv_testcase.src_client
        cv_testcase.client = cv_testcase.src_client  # USED BY fshelper.restore_out_of_place()

        FSHelper.populate_tc_inputs(cv_testcase, mandatory=False)

    def create_default_backupset(self, name):
        """Creates a new backup set with the given name and sets it as the default backup set.

        Args:
            name    (str)   --  Name of the backupset.

        Returns:
            None    -   If the backupset was created successfully.

        Raises:
            Exception:
                Any error occured during backupset creation or updation of backupset as default.

        """

        try:
            FSHelper.create_backupset(self, name)
            self.log.info("Attemping to set {} as the default backupset".format(name))
            self.testcase.backupset.set_default_backupset()

        except Exception as excp:
            error_message = "Backupset couldn't be set as default : {}".format(str(excp))
            self.log.error(error_message)
            raise Exception(error_message)

    def get_ma_entries_from_machine(self, machine_object, appdata_path):
        """Prepares a list of entries from the machine that should
        get backed up as part of Migration Assistant User Settings.

        Args:
            machine_object  (object)    --  Instance of Machine class
            connected to the remote machine to get MA entries from.

            appdata_path    (str)       --  Profile path for the given user.
            E.g. C:\\Users\\Administrator\\\AppData

        Returns:
            list    -   list of items that would be backed up
            as part of MA for given user profile.

        Raises:
            Exception:
            If any error occurs when collecting MA entries from the machine.

        """
        try:
            win_ma_paths = [r"AppData\\Local\\Microsoft\\Feeds Cache",
                            r"AppData\\Local\\Microsoft\\Feeds",
                            r"AppData\\Local\\Microsoft\\Internet Explorer",
                            r"AppData\\Local\\Microsoft\\Media Player",
                            r"AppData\\Local\\Microsoft\\Outlook",
                            r"AppData\\Local\\Microsoft\\Windows\\History",
                            r"AppData\\Roaming\\Microsoft\\Internet Explorer\\Quick Launch",
                            r"AppData\\Roaming\\Microsoft\\Office",
                            r"AppData\\Roaming\\Microsoft\\Outlook",
                            r"AppData\\Roaming\\Microsoft\\PowerPoint",
                            r"AppData\\Roaming\\Microsoft\\Signatures",
                            r"AppData\\Roaming\\Microsoft\\Stationery",
                            r"AppData\\Roaming\\Microsoft\\SystemCertificates",
                            r"AppData\\Roaming\\Microsoft\\UProof",
                            r"AppData\\Roaming\\Microsoft\\Windows\\Cookies",
                            r"AppData\\Roaming\\Microsoft\\Network",
                            r"Favorites"]
            file_list = []

            # FETCH LIST OF ITEMS UNDER APP DATA EXCLUDING HIDDEN ITEMS
            ma_item_list = set((machine_object.get_test_data_info(appdata_path, name=True)).split("\n"))

            # FETCH LIST OF HIDDEN ITEMS UNDER APP DATA
            # DEFINE HIDDEN ITEMS COMMAND
            win_hidden_items_cmd = ("Get-ChildItem -Recurse \"{}\" -Force -ErrorAction Ignore "
                                    "| Where {{$_.FullName -notlike \"*\\Local\\Packages\\*\" "
                                    "-and $_.FullName -notlike \"*\\Local\\Temp\\*\"}} | Format-Table "
                                    "-HideTableHeaders -AutoSize -Property @{{e={{$_.FullName}};width=1000}} "
                                    "| Out-String -Width 60960".format(appdata_path))

            # EXECUTE HIDDEN ITEMS COMMAND
            # UPDATE LIST OF ITEMS WITH HIDDEN ITEMS
            ma_item_list.update(set((machine_object.execute_command(win_hidden_items_cmd)).output.split("\r\n")))
            profile_path = (appdata_path.lower()).replace("\\appdata", "")
            ma_item_list.update(set((machine_object.get_test_data_info(profile_path, name=True)).split("\n")))

            # PROFILE PATH IS PARENT PATH OF APP DATA
            profile_path = profile_path.replace(machine_object.os_sep, 2 * machine_object.os_sep)
            for item in ma_item_list:
                for path in win_ma_paths:
                    item, path = item.lower(), path.lower()
                    if re.match(r"{}.*\\.*{}.*".format(profile_path, path), item.strip("\n")) is not None:
                        item = str(item.strip("\n"))
                        # OST/PST FILES ARE NOT BACKED UP BY MA SO WE WILL NOT CONSIDER THEM.
                        if (item.endswith(".pst") or item.endswith(".ost")):
                            self.log.info("{} NOT being considered for comparison".format(item))
                        file_list.append(item.rstrip())
                        # APPEND ALL PARENTS AS WELL SINCE THIS IS CURRENT COLLECT FILE FORMAT
                        # NOT INCLUDING THIS COULD POTENTIALLY MESS UP THE WHOLE COMPARISON LOGIC.
                        while item.find(machine_object.os_sep) != -1 and len(item.split('\\')) > 4:
                            parent = item[0:str(item).rfind("\\")]
                            item = parent
                            if len(item) > 3:
                                file_list.append(item.rstrip())
            file_list.sort()
            return list(set(file_list))

        except Exception as excp:
            error_message = "Error occurred when preparing a list of MA entries from the machine {0}".format(excp)
            raise Exception(error_message)

    def get_ma_entries_from_cvfs(
            self,
            machine_object,
            backup_level,
            profile=None,
            get_entries_as_list=True,
            flag="<ma>"):
        """Prepares a list of MA entries from the collect file.

        Args:
            machine_object      (object)    --  Instance of Machine class
            connected to the remote machine to get collect file entries from.

            backup_level        (str)                           --  Level of backup.

                Valid values are:
                    -   Full
                    -   Incremental
                    -   Differential
                    -   Synthetic_full

            profile             (str)                           --  The profile
            whose MA entries need to be fetched.

            get_entries_as_list (bool)                          --  Whether entries
            need to be returned in the form of a list.

                default:    True

            flag                (str)                           --  The flag(s) to search for
            as written in the collect file.

                default:    <ma>

        Returns:
            list    -   list of MA items from the collect file.

        Raises:
            Exception:
            If any error occurs when collecting MA entries from the collect files.

        """
        try:
            sc_jr_path = list(self.subclient_job_results_directory.values())[0]
            cvf_ptrn = re.compile(r".*NumColTot\d+\.cvf$") if backup_level.upper() == "FULL" \
                else re.compile(r".*NumColInc\d+\.cvf$")

            cvf_names = [cvf for cvf in (machine_object.get_test_data_info(sc_jr_path, name=True)).split("\n")
                         if cvf_ptrn.search(cvf) is not None]
            cvfs = []

            for cvf_name in cvf_names:
                cvf = [cvf_name.lower()]
                for item in (machine_object.read_file(cvf_name)).split("\r\n"):
                    cvf.append(item.lower())
                cvf.sort()
                cvfs.append(cvf)

            if get_entries_as_list:
                profile = (profile.lower()).replace("\\appdata", "")
                ma_entries_list = []
                for cvf in cvfs:
                    for entry in cvf:
                        entry = str(entry).lower()
                        if entry.find(flag) != -1 and profile is None:
                            ma_entries_list.append(str(entry[3:str(entry).find("|")]).rstrip("\\"))
                        elif entry.find(profile) != -1:
                            ma_entries_list.append(str(entry[3:str(entry).find("|")]).rstrip("\\"))
                ma_entries_list.sort()
                return list(set(ma_entries_list))

            return cvfs

        except Exception as excp:
            error_message = "Error occurred when preparing a list of MA entries from  collect files {0}".format(excp)
            raise Exception(error_message)

    def collect_registry_entries(self, machine_object, subkey_name, recurse=True, find_subkey=None, find_entry=None):
        """Collects registry entries from the specified machine under a specified sub key.

        Args:
            machine_object  (object)    --  Instance of Machine class
            connected to the remote machine to get registry entries from.

            subkey_name     (str)       --  Name of the subkey
            in the registry. An example of a subkey name is 'HKLM:\SOFTWARE\CommVault Systems'

            recurse         (bool)      --  Whether to recurse through subkeys or not.

                default:    True

            find_subkey     (str)       --  Name of the key to search for in the given subkey.

                default:    None

            find_entry      (str)       --  Name of the entry to search for,
            specifying a subkey is mandatory.

                default:    None

        Returns:
            dict    -   A dictionary of dictionaries containing
            the entry name as the key and the entry data as value.

        Raises:
            Exception:
            If any error occurs when collecting registry entries.

        """

        try:
            self.log.info("Subkey name is {}".format(subkey_name))
            output_list, output_dict, tmp_dict = list(), dict(), dict()
            j = 0

            for item in [x for x in (machine_object.get_registry_entries_for_subkey(
                    subkey_name, recurse=False)).split("\r\n") if x != '']:
                if not str(item).startswith(" "):
                    output_list.insert(j, item.strip())
                    j += 1
                else:
                    output_list[j - 1] = (output_list[j - 1] + str(item.lstrip()))
            for item in output_list:
                tmp_item = [i.rstrip() for i in item.split(":", 1)]
                if tmp_dict.get(tmp_item[0]) is None:
                    if tmp_item[0] != 'PSPath':
                        if tmp_item[0] not in ('PSProvider', 'PSParentPath', 'PSChildName'):
                            tmp_dict[str(tmp_item[0]).rstrip()] = str(tmp_item[1]).lstrip()
                    else:
                        output_dict[str((tmp_item[1]).replace("Microsoft.PowerShell.Core\\", "")).lstrip()] = tmp_dict
                        tmp_dict = dict()
            return output_dict

        except Exception as excp:
            error_message = "Error occurred when collecting registry entries from machine {0}".format(excp)
            raise Exception(error_message)

    def compare_lists(self, source_list, destination_list, check_subset=True):
        """Compares the source list with destination list and checks if they are same or if
        the entries in the destination list can form a subset of the entries in the source list.

        Args:
            source_list         (list)  --  1st list to compare the contents of.

            destination_list    (list)  --  2nd list to compare the contents of.

            check_subset        (bool)  --  Checks if the entries in the destination list
            can form a subset of the entries in the source list.

                 default:    True

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line
        Raises:
            None

        """

        diff_output = ""

        if check_subset:
            self.log.info(
                "CHECKING IF ENTRIES IN {} IS A SUBSET OF ENTRIES IN {}".format(
                    source_list, destination_list))

            source_set, destination_set = set(source_list), set(destination_list)

            if source_set.issubset(destination_set):
                return source_set.issubset(destination_set), diff_output
            else:
                diff_output = list(source_set - destination_set)
                # THE NTUSER.DAT FILE GETS RENAMED DURING BACKUP, WE WILL IGNORE THIS CHECK.
                if len(diff_output) == 1 and diff_output[0].find("ntuser.dat") != -1:
                    self.log.info("{} is the only item present in collect file that we couldn't find on the client, "
                                  "the NTUSER.DAT file can be ignored as this is expected".format(diff_output))
                    return True, diff_output
                return source_set.issubset(destination_set), diff_output
        else:
            # CALLING machine.compare_lists()
            self.testcase.src_machine.compare_lists(source_list, destination_list)

    def get_sid_for_user_profile(self, machine_object, user_profile):
        """Retrieves the SID for the user profile.

        Args:
            machine_object  (object)    --  Instance of Machine class
            connected to the remote machine from which we need to get
            the SID of the provided user profile.

            user_profile    (str)       --  Name of the user profile.

        Returns:
            str -   SID of the user profile.

        Raises:
            None

        """

        cmd = ("(New-Object System.Security.Principal.NTAccount(\"{}\")).Translate("
               "[System.Security.Principal.SecurityIdentifier]).Value").format(user_profile).replace('\n', '')

        self.log.info("Going to obtain SID for user profile {} on {}".format(str(machine_object), user_profile))
        output = machine_object.execute_command(cmd)
        return output.formatted_output

    def run_sync_restore(self, dst_client):
        """Launches a Sync. Restore job on the specified destination client.

        Args:
            dst_client      (object)    --  Instance of Client object destination client
            for the Sync. Restore.

        Returns:
           object -   Returns an instance of Job class for the Sync. Restore.

        Raises:
            Exception:
            Any error occurred while running
            Sync. Restore or if it did not complete successfully.

        """

        if self.moniker_dict is None:
            self.moniker_dict = (self.testcase.src_machine, self.testcase.src_user_acc)

        moniker_dict = deepcopy(self.moniker_dict)
        profile_path = moniker_dict["AppData"].strip("AppData").rstrip("\\")

        monikers_suffixes = fs_constants.WIN_MA_PATHS

        paths, sync_option_paths = list(), list()
        sync_option_paths_format = "!#22!{}\\{}|\\{}"

        for moniker in monikers_suffixes:
            paths.append("{{20d03aa2-7726-42d8-8381-fdda7a8a1c47}}\\SmartContent\\{}\\{}\\{}".
                         format(self.testcase.src_domain, self.testcase.src_user_acc, moniker))

            sync_option_paths.append(
                {"destinationPath":
                     sync_option_paths_format.format(self.testcase.dst_domain, self.testcase.dst_user_acc, moniker),
                 "sourcePath":
                     sync_option_paths_format.format(self.testcase.src_domain, self.testcase.src_user_acc, moniker)
                }
            )

        dst_path = self.testcase.dst_machine.join_path(profile_path, "cvauto_tmp")
        fs_options = {'sync_restore': True, 'sync_option_paths': sync_option_paths}
        job = self.testcase.subclient.restore_out_of_place(client=dst_client,
                                                           destination_path=dst_path,
                                                           paths=paths,
                                                           fs_options=fs_options)
        self.log.info("Waiting for completion of {} restore with Job ID: {}".format(job.job_type, str(job.job_id)))

        if not job.wait_for_completion():
            err_msg = "Failed to run Sync. Restore {} with error: {}".format(str(job.job_id), job.delay_reason)
            raise Exception(err_msg)
        return job

    def get_moniker_paths(self, machine_object, user_profile):
        """Fetches the path for each of the monikers from the machine for the given user profile.

        Args:
            machine_object  (object)    --  Instance of Machine class
            connected to the remote machine for which the paths corresponding
            to the monikers need to be fetched from.

            user_profile    (str)       --  Name of the user profile
            for which the paths corresponding to the monikers need to be fetched.

        Returns:
            dict    -   A dictionary of the monikers and their corresponding paths.

        Raises:
            None

        """
        moniker_dict = dict()

        # STEP 1 - OBTAIN THE SID FOR THE USER
        src_sid = self.get_sid_for_user_profile(machine_object, user_profile)

        # STEP 2 - OBTAIN SHELL FOLDER PATHS FOR SID (SINCE HKCU AND HKCR AREN'T
        # AVAILABLE ON REMOTE REGISTRY)
        reg_path = "Registry::HKU\{}\Software\Microsoft\\Windows\CurrentVersion\Explorer\Shell Folders".format(src_sid)
        reg_entry_output = self.collect_registry_entries(self.testcase.src_machine, reg_path)

        # STEP 3 - OBTAIN ALL MONIKER PATHS
        appdata_path = ((reg_entry_output.get(reg_path)).get("AppData", None)).strip("Roaming").strip("\\")
        desktop_path = ((reg_entry_output.get(reg_path)).get("Desktop", None))
        music_path = ((reg_entry_output.get(reg_path)).get("My Music", None))
        pictures_path = ((reg_entry_output.get(reg_path)).get("My Pictures", None))
        videos_path = ((reg_entry_output.get(reg_path)).get("My Video", None))
        docs_path = ((reg_entry_output.get(reg_path)).get("Personal", None))

        moniker_dict["AppData"] = appdata_path
        moniker_dict["Desktop"] = ["%Desktop%", machine_object.join_path(desktop_path, str(self.testcase.runid))]
        moniker_dict["Music"] = ["%Music%", machine_object.join_path(music_path, str(self.testcase.runid))]
        moniker_dict["Pictures"] = ["%Pictures%", machine_object.join_path(pictures_path, str(self.testcase.runid))]
        moniker_dict["Videos"] = ["%Videos%", machine_object.join_path(videos_path, str(self.testcase.runid))]
        moniker_dict["Documents"] = ["%Personal%", machine_object.join_path(docs_path, str(self.testcase.runid))]

        return moniker_dict

    def perform_ma_validation(self, backup_level):
        """Validates whether the collect file has all the MA entries by comparing it
        against a list of expected MA entries from the machine.

        Args:
            backup_level    (str)   --  Level of backup.

                Valid values are:
                    -   Full
                    -   Incremental
                    -   Differential
                    -   Synthetic_full

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        Raises:
            None

        """



        if self.moniker_dict is None:
            self.moniker_dict = (self.testcase.src_machine, self.testcase.src_user_acc)

        moniker_dict = deepcopy(self.moniker_dict)
        client_entries = self.get_ma_entries_from_machine(self.testcase.src_machine, moniker_dict["AppData"])
        cvf_entries = self.get_ma_entries_from_cvfs(self.testcase.src_machine, backup_level, moniker_dict["AppData"])

        result, diff_output = self.compare_lists(client_entries, cvf_entries)
        #Empty folders will not be backedup, so filtering them out from the diff to get correct comparision.
        for item in diff_output:
            if int(self.testcase.src_machine.get_folder_size(item)) > 0:
                result = False
                return result, diff_output

        result = True
        self.log.info("RESULT = {} & DIFF = {}".format(str(result), str(diff_output)))
        return result, diff_output

    def generate_test_data_for_ma(self, machine_object, suffix="", add_incr=False):
        """Generates test data under the well-known folders.

        Args:
            machine_object  (object)    --  Instance of the Machine class
            connected to the remote machine on which the test data needs to be generated.

            suffix          (str)       --  An optional suffix to help identify the dataset.

            add_incr        (bool)      --  Specifies whether
            data is being added for an incremental backup or not.

                default:    True

        Returns:
            None

        Raises:
            None

        """

        if self.moniker_dict is None:
            self.moniker_dict = (self.testcase.src_machine, self.testcase.src_user_acc)

        moniker_dict = deepcopy(self.moniker_dict)
        moniker_dict.pop("AppData", None)  # WE DO NOT REQUIRE THIS
        for value in moniker_dict.values():
            self.log.info("Moniker = {} \n Local Path = {}".format(value[0], value[1]))
            data_path = machine_object.join_path(value[1], suffix)
            if add_incr:
                self.log.info("Adding new data for incremental backup")
                self.add_new_data_incr(data_path, self.testcase.slash_format)
            else:
                machine_object.generate_test_data(data_path)

    def ma_restore_verify(self, job, suffix, ma_validation_flag=False):
        """Initiates restore for data backed up in the given job
        and performs the applicable verifications.

        Args:
            job                 (object)    --  Instance of Job class
            of the backup job that backed up MA items.

            suffix              (str)       --  The suffix used to identify the subset of
            the dataset that needs to be restored.

            ma_validation_flag  (bool)      --  Whether MA validation is required.

        Returns:
            None

        Raises:
            None

        """
        if self.moniker_dict is None:
            self.moniker_dict = (self.testcase.src_machine, self.testcase.src_user_acc)

        moniker_dict = deepcopy(self.moniker_dict)

        # VALIDATE WELL KNOWN FOLDER CONTENT RESTORE
        profile_path = moniker_dict["AppData"].strip("AppData").rstrip("\\")
        tmp_restore_path = self.testcase.src_machine.join_path(profile_path, "cvauto_tmp", str(self.testcase.runid))

        moniker_dict.pop("AppData", None)  # WE DO NOT REQUIRE THIS
        for value in moniker_dict.values():
            data_path = self.testcase.src_machine.join_path(value[1], suffix)
            self.run_restore_verify(self.testcase.slash_format, data_path, tmp_restore_path, suffix, job)

        # VALIDATE MA CONTENT RESTORE
        if ma_validation_flag:
            result, diff_output = self.perform_ma_validation(job.backup_level)
            if result:
                self.log.info("MA Validation was successful")
            else:
                self.log.info("MA Validation failed with the following differences {}".format(str(diff_output)))
        else:
            self.log.info("MA Validation was skipped")

    def cleanup_run_for_ma(self, days=None):
        """Removes the dataset that was created under the well known folders and deletes the backupset.

        Args:
            days            (int)   --  dataset older than the given days will be cleaned up.

                default: None

        Returns:
            None

        Raises:
            None

        """

        self.create_default_backupset("defaultBackupSet")
        self.testcase.instance.backupsets.delete(self.testcase.bset_name)

        if self.moniker_dict is None:
            self.moniker_dict = (self.testcase.src_machine, self.testcase.src_user_acc)

        moniker_dict = deepcopy(self.moniker_dict)
        moniker_dict.pop("AppData", None)

        for value in moniker_dict.values():
            self.testcase.src_machine.remove_directory(value[1], days)


class MigrationAssistantHelperMac(MigrationAssistantHelper):
    def __init__(self, testcase):
        """Initialize the Installation class instance for performing Install related
            operations.
            Args:
                client    (object)    --  instance of the client class

            Returns:
                object  -   instance of the MigrationAssistantHelperMac class

        """
        super(MigrationAssistantHelperMac, self).__init__(testcase)

        self.populate_migration_assistant_inputs(testcase)



    def get_ma_entries_from_mac_machine(self, machine_object, profile):
        """Prepares a list of entries from the machine that should
        get backed up as part of Migration Assistant User Settings.

        Args:
            machine_object  (object)    --  Instance of Machine class
            connected to the remote machine to get MA entries from.

            appdata_path    (str)       --  Profile path for the given user.
            E.g. C:\\Users\\Administrator\\\AppData

        Returns:
            list    -   list of items that would be backed up
            as part of MA for given user profile.

        Raises:
            Exception:
            If any error occurs when collecting MA entries from the machine.

        """
        try:
            mac_ma_paths = fs_constants.MAC_MA_PATHS
            for item in mac_ma_paths:
                loc = mac_ma_paths.index(item)
                mac_ma_paths.remove(item)
                item = "/Users/"+ profile + item
                mac_ma_paths.insert(loc,item)

            file_list = []

            # FETCH LIST OF ITEMS UNDER APP DATA EXCLUDING HIDDEN ITEMS
            ma_item_list = []

            # EXECUTE HIDDEN ITEMS COMMAND
            # UPDATE LIST OF ITEMS WITH HIDDEN ITEMS
            for path in mac_ma_paths:
                if machine_object.get_test_data_info(path, name=True) == '\n' and path.find('.cvconflict') == -1:
                    file_list.append(path.lower())
                elif len(machine_object.get_test_data_info(path, name=True)) >= 1:
                    machine_object.get_test_data_info(path, name=True).split("\n").remove('')
                    for item in machine_object.get_test_data_info(path, name=True).split("\n"):
                        if item.find('.cvconflict') == -1:
                            item = path + item
                            ma_item_list.append(item.lower())

            # PROFILE PATH IS PARENT PATH OF APP DATA

            file_list.extend(ma_item_list)
            return file_list

        except Exception as excp:
            error_message = "Error occurred when preparing a list of MA entries from the machine {0}".format(excp)
            raise Exception(error_message)


    def get_ma_entries_from_mac_cvfs(
            self,
            machine_object,
            backup_level,
            profile=None,
            get_entries_as_list=True,
            flag="<ma>"):
        """Prepares a list of MA entries from the collect file.

        Args:
            machine_object      (object)    --  Instance of Machine class
            connected to the remote machine to get collect file entries from.

            backup_level        (str)                           --  Level of backup.

                Valid values are:
                    -   Full
                    -   Incremental
                    -   Differential
                    -   Synthetic_full

            profile             (str)                           --  The profile
            whose MA entries need to be fetched.

            get_entries_as_list (bool)                          --  Whether entries
            need to be returned in the form of a list.

                default:    True

            flag                (str)                           --  The flag(s) to search for
            as written in the collect file.

                default:    <ma>

        Returns:
            list    -   list of MA items from the collect file.

        Raises:
            Exception:
            If any error occurs when collecting MA entries from the collect files.

        """
        try:
            sc_jr_path = list(self.subclient_job_results_directory.values())[0]
            cvf_ptrn = re.compile(r".*CollectTot\d+\.cvf$") if backup_level.upper() == "FULL" \
                else re.compile(r".*CollectInc\d+\.cvf$")

            cvf_names = [cvf for cvf in (machine_object.get_test_data_info(sc_jr_path, name=True)).split("\n")
                         if cvf_ptrn.search(cvf) is not None]
            cvfs = []

            for cvf_name in cvf_names:
                cvf_name = sc_jr_path +cvf_name
                cvf = [cvf_name]
                for item in (machine_object.read_file(cvf_name)).split("\n"):
                    cvf.append(item.lower())
                cvf.sort()
                cvfs.append(cvf)

            if get_entries_as_list:
                ma_entries_list = []
                for cvf in cvfs:
                    for entry in cvf:
                        entry = str(entry).lower()
                        if  entry.find('library') != -1:
                            if entry.endswith('/'):
                                entry = entry[:-1]
                            ma_entries_list.append(str(entry).replace('??ma', ''))
                ma_entries_list.sort()
                return list(set(ma_entries_list))

            return cvfs

        except Exception as excp:
            error_message = "Error occurred when preparing a list of MA entries from  collect files {0}".format(excp)
            raise Exception(error_message)


    def perform_ma_validation(self, backup_level):
        """Validates whether the collect file has all the MA entries by comparing it
        against a list of expected MA entries from the machine.

        Args:
            backup_level    (str)   --  Level of backup.

                Valid values are:
                    -   Full
                    -   Incremental
                    -   Differential
                    -   Synthetic_full

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        Raises:
            None

        """

        client_entries = self.get_ma_entries_from_mac_machine(self.testcase.src_machine, self.testcase.src_user_acc)
        cvf_entries = self.get_ma_entries_from_mac_cvfs(self.testcase.src_machine, backup_level, self.testcase.src_user_acc)

        result, diff_output = self.compare_lists(client_entries, cvf_entries)
        self.log.info(diff_output)
        #Empty folders will not be backedup, so filtering them out from the diff to get correct comparision.
        for item in diff_output:
            if int(self.testcase.src_machine.get_folder_size(item)) > 0:
                result = False
                return result, diff_output

        result = True
        self.log.info("RESULT = {} & DIFF = {}".format(str(result), str(diff_output)))
        return result, diff_output

