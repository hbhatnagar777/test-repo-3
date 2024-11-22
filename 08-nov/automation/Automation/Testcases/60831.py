# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    cleanup()       --  cleanup the entities created in this/previous run

    parse_files()   --  parses the log file in the specified location based on the given job id and pattern

    run()           --  run function of this test case

    run_validations()    --  runs the validations

    tear_down()     --  tear down function of this test case

Sample JSON:
    "60831": {
        "ClientName": "Name of Client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "library_name": "name of the Library to be reused",
        "mount_path": "path where the data is to be stored",
        "dedup_path": "path where dedup store to be created",
        "copy_library_name": "name of the Library to be reused for auxcopy",
        "copy_mount_path": "path where the data is to be stored for auxcopy",
        "copy_dedup_path": "path where dedup store to be created for auxcopy"
    }

    Note: Both the MediaAgents can be the same machine
    For linux MA, User must explicitly provide a ddb path that is inside a Logical Volume.(LVM support required for DDB)

Steps:

1: Configure the environment: create a library,Storage Policy-with Primary, Secondary Copy,
                              a BackupSet,a SubClient

2: Set Properties: Set Network Throttling limit to 4000MBPH on Copy level

3: Run a Backup Job and then AuxCopy

4: Run the Validations:
    - archGroupCopy: DB Value of Network Thrott limit
    - CVThrottMgrOut.log: Log Validation on Source MA
    - PerfLog_JobsStreamStats.csv: Final Througput Value on Destination MA after Aux is Completed. Tolerance: 10%
    - archFileCopy:  DB Validation for Successfull AuxCopy
5: CleanUp the environment
"""

import re
import os
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Network Throttling at Storage Policy Copy Level Basic Test Case"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.copy_ddb_path = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.subclient = None
        self.copy_name = None
        self.library_name = None
        self.library_name_2 = None
        self.storage_policy = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None
        self.list_primary = []
        self.list_secondary = []
        self.config_strings = None
        self.is_user_defined_lib = False
        self.is_user_defined_copy_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False

    def setup(self):
        """Setup function of this test case"""
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs.get('PrimaryCopyMediaAgent'), self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs.get('SecondaryCopyMediaAgent'), self.commcell)
        client_drive = self.utility.get_drive(self.client_machine, 25*1024)
        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.copy_name = '%s%s' % (str(self.id), '_Copy')
        self.subclient_name = '%s%s' % (str(self.id), '_SC')
        self.backupset_name = '%s%s%s' % (str(self.id), '_BS_',
                                          str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:])
        self.storage_policy_name = '%s%s%s' % (str(self.id), '_SP_',
                                               str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:])

        if self.tcinputs.get('library_name'):
            self.is_user_defined_lib = True
        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('copy_library_name'):
            self.is_user_defined_copy_lib = True
        if self.tcinputs.get('copy_mount_path'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine_1, 25*1024)
            self.primary_ma_path = self.ma_machine_1.join_path(ma_1_drive, 'test_' + str(self.id))
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            ma_2_drive = self.utility.get_drive(self.ma_machine_2, 25*1024)
            self.secondary_ma_path = self.ma_machine_2.join_path(ma_2_drive,
                                                                 'test_' + str(self.id))

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs["library_name"]
        else:
            self.library_name = '%s%s%s' % (str(self.id), '_Lib1_',
                                            str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:])
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine_1.join_path(
                    self.tcinputs.get('mount_path'), 'test_' + self.id, 'MP1')

        if self.is_user_defined_copy_lib:
            self.log.info("Existing library name supplied for secondary copy")
            self.library_name_2 = self.tcinputs.get("copy_library_name")
        else:
            self.library_name_2 = '%s%s%s' % (str(self.id), '_Lib2_',
                                              str(self.tcinputs.get('SecondaryCopyMediaAgent'))[2:])
            if not self.is_user_defined_copy_mp:
                self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, 'MP2')
            else:
                self.log.info("custom copy_mount_path supplied")
                self.mount_path = self.ma_machine_2.join_path(
                    self.tcinputs.get('copy_mount_path'), 'test_' + self.id, 'MP2')

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine_1.join_path(self.tcinputs.get("dedup_path"),
                                                        'test_' + self.id, "DDB")
        else:
            if "unix" in self.ma_machine_1.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDB")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copydedup path supplied")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.tcinputs.get("copy_dedup_path"),
                                                             'test_' + self.id, "CopyDDB")
        else:
            if "unix" in self.ma_machine_2.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.copy_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "CopyDDB")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """Cleans Up the Entities created in the TC"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)
            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
            if not self.is_user_defined_copy_lib:
                if self.commcell.disk_libraries.has_library(self.library_name_2):
                    self.commcell.disk_libraries.delete(self.library_name_2)
            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.log.error('ERROR in Cleanup. Might need to Cleanup Manually: %s', str(exe))

    def parse_files(self,
                    client_machine,
                    file_name,
                    file_directory,
                    regex,
                    regex2=None,
                    escape_regex=True,
                    single_file=False):
        """
        This function parses the log file in the specified location based on the given job id and pattern

        Args:
            client_machine  (str)   --  MA/Client Name on which log is to be parsed

            file_name       (str)   --  Name of log file to be parsed

            file_directory  (str)   --  Name of log file to be parsed

            regex           (str)   --  Pattern to be searched for in the log file

            regex2          (str)   --  Second regex to be searched

            escape_regex    (bool)  --  Add escape characters in regular expression before actual comparison

            single_file     (bool)  --  To parse only the provided log file instead of all older logs
        Returns:
           (tuple) --  Result of string searched on all log files of a file name
        """
        found = 0
        matched_string = []
        matched_line = []
        if escape_regex:
            self.log.info("Escaping regular expression as escape_regex is True")
            regex = re.escape(regex)
        self.log.info("Log path : {0}".format(str(file_directory)))
        if not single_file:
            all_log_files = client_machine.get_files_in_path(file_directory)
            self.log.info("Got files in path ")
            matched_files = [x for x in all_log_files if os.path.splitext(file_name)[0].lower() in x.lower()]
        else:
            matched_files = [client_machine.join_path(file_directory, file_name)]

        if client_machine.os_info == 'UNIX':
            logfile_index = 0
            for file in matched_files:
                if os.path.splitext(file_name)[1].lower() == '.bz2':
                    command = 'bzip2 -d %s' % file_name
                    self._log.info("decompressing .bz2 file %s", file)
                    exit_code, response, error = client_machine.client_object.execute_command(command)
                    if exit_code == 0:
                        self.log.info("Successfully decompressed log file %s", file)
                        matched_files[logfile_index] = file.replace(r'.bz2', '')
                    else:
                        self.log.error("Failed to decompress log file %s", file)
                logfile_index += 1

            # get log file versions
        for file in matched_files:
            if found == 0:
                lines = []
                if os.path.splitext(file)[1].lower() not in ['.zip', '.bz2']:
                    lines = client_machine.read_file(file, search_term=regex).splitlines()
                if os.path.splitext(file)[1].lower() == '.zip':
                    base_dir = client_machine.join_path(client_machine.client_object.install_directory, 'Base')
                    command = '"%s%sunzip" -o "%s" -d "%s"' % (base_dir, client_machine.os_sep,
                                                               file, file_directory)
                    response = client_machine.client_object.execute_command(command)
                    if response[0] == 0:
                        self.log.info('Decompressed log file %s', file)
                        extracted_file = os.path.splitext(file)[0]
                        lines = client_machine.read_file(extracted_file, search_term=regex).splitlines()
                    else:
                        self.log.error('Failed to Decompress log file %s', file)
                if not regex2 and lines:
                    self.log.info("Searching for [{0} in file {1}]".format(regex, file))
                    for line in lines:
                        line = str(line)
                        regex_check = re.search(regex, line)
                        if regex_check:
                            matched_line.append(line)
                            matched_string.append(regex_check.group(0))
                            found = 1
                elif lines:
                    self.log.info("""Searching for string [{0}] and string [{1}] in file [{2}]
                                   """.format(regex, regex2, file))
                    for line in lines:
                        # required to change a byte stream to string
                        line = str(line)
                        reg2_check = re.search(regex2, line)
                        if reg2_check:
                            regex_check = re.search(regex, line)
                            if regex_check:
                                matched_line.append(line)
                                matched_string.append(regex_check.group(0))
                                found = 1
        if found:
            count = len(matched_line)
            self.log.info("Found {0} matching line(s)".format(str(count)))
            return matched_line, matched_string
        self.log.error("Not found!")
        return None, None

    def run(self):
        """Run Function of This Case"""
        self.log.info('**************** Cleaning up Entities from older runs ****************')
        self.cleanup()
        try:
            # 1: Setup the Environment
            self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                      self.content_path, 4)
            if not self.is_user_defined_lib:
                self.mm_helper.configure_disk_library(self.library_name,
                                                      self.tcinputs.get('PrimaryCopyMediaAgent'),
                                                      self.mount_path)
            if not self.is_user_defined_copy_lib:
                self.mm_helper.configure_disk_library(self.library_name_2,
                                                      self.tcinputs.get('SecondaryCopyMediaAgent'),
                                                      self.mount_path_2)

            self.storage_policy = self.dedupe_helper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.library_name,
                self.tcinputs.get('PrimaryCopyMediaAgent'),
                self.ma_machine_1.join_path(self.ddb_path, 'Dir'))
            storage_policy_copy = self.dedupe_helper.configure_dedupe_secondary_copy(
                self.storage_policy, self.copy_name,
                self.library_name_2, self.tcinputs.get('SecondaryCopyMediaAgent'),
                self.ma_machine_2.join_path(self.copy_ddb_path,
                                            'Dir' + self.utility.get_custom_str()),
                self.tcinputs.get('SecondaryCopyMediaAgent'))
            self.mm_helper.configure_backupset(self.backupset_name)
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)

            # Remove Association with System Created AutoCopy Schedule
            self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)

            # 2: Set Properties: Network Throttle Bandwidth to 4000 MBPH
            self.log.info('Setting Network Throttle Bandwidth on Secondary Copy to 4000 MBPH')
            storage_policy_copy.network_throttle_bandwidth = 4000

            # 3: Run a Backup Job and then AuxCopy and run Validations(properties set)
            self.log.info('Submitting 1st Full Backup')
            backup_job = self.subclient.backup(backup_level='Full')
            if backup_job.wait_for_completion():
                self.log.info('1st Backup Completed :Id - %s', backup_job.job_id)
            else:
                raise Exception(f'1st Backup {backup_job.job_id} Failed with JPR: {backup_job.delay_reason}')

            # set debug level on CVThrottMgrOut on Primary Copy MA to 5
            self.ma_machine_1.set_logging_debug_level('CVThrottMgrOut', '5')

            self.log.info('Submitting AuxCopy job with scalable resource allocation')
            aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True)
            if aux_copy_job.wait_for_completion():
                self.log.info('1st AuxCopy Completed :Id - %s', aux_copy_job.job_id)
            else:
                raise Exception(f'1st AuxCopy {aux_copy_job.job_id} Failed with JPR: {aux_copy_job.delay_reason}')

            self.run_validations(aux_copy_job.job_id, storage_policy_copy.copy_id)
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Occurred: %s', str(exe))

    def run_validations(self, aux_copy_job_id, copy_id):
        """
        Runs the validations
        Args:
            aux_copy_job_id       (str):  Id of the AuxCopy Job

            copy_id               (str):  Id of the Secondary Copy
        """
        self.log.info('*** DB Validation for Network Throttling Bandwidth ***')
        query = f'''select NWWriteSpeed
                from archGroupCopy
                where id={copy_id}'''
        self.log.info('Executing Query: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("Result: %s", str(result))
        if int(result[0]) == 4000:
            self.log.info('Success Result : Passed')
        else:
            self.log.error('Error  Result : Failed')
            self.status = constants.FAILED

        log_file = 'CVThrottMgrOut.log'
        self.log.info('*** VALIDATION 2: CVThrottMgrOut on Source Copy  ***')
        (matched_line, matched_string) = self.parse_files(
            self.ma_machine_1, log_file,
            self.ma_machine_1.client_object.log_directory,
            '\\bThrottleMBPH', f'{aux_copy_job_id}', escape_regex=False)
        if matched_line:
            throughput = int(matched_line[0].split()[7])
            self.log.info('ThrottleMBPH = %d', throughput)
            if throughput == 4000:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error Result : Failed. Throughput is not limited as expected')
                self.status = constants.FAILED
        else:
            self.log.error('Error Result : Failed. No Matching lines')
            self.status = constants.FAILED

        log_file = 'PerfLog_JobsStreamStats.csv'
        self.log.info('*** VALIDATION 3: PerfLog_JobsStreamStats Pipe-Network ThroughPut ***')
        (matched_line, matched_string) = self.parse_files(
            self.ma_machine_2, log_file,
            self.ma_machine_2.join_path(self.ma_machine_2.client_object.log_directory, 'ResourceMonitor'),
            f',{aux_copy_job_id},', escape_regex=False)

        if matched_line:
            throughput = 0
            for line in matched_line:
                throughput += float(line.split(',')[23])
            self.log.info('Pipe-Network ThroughPut = %f', throughput)
            # giving a tolerance of 10%
            if throughput*1024 <= 4000 + 400:
                self.log.info('Success Result : Passed')
            else:
                self.log.error('Error Result : Failed. Throughput is not limited as expected')
                self.status = constants.FAILED
        else:
            self.log.error('Error Result : Failed. No Matching lines')
            self.status = constants.FAILED

        self.log.info('******** VALIDATION 4: Valid archFile Count Same in Both the Copies *********')

        query = f'''SELECT archCopyId, count(*)
                FROM archFileCopy
                WHERE archCopyId in ({self.storage_policy.get_copy('Primary').copy_id},{copy_id})
                    AND isValid = 1 
                GROUP BY archCopyId'''
        self.log.info('Query: %s', query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info('Result: %s', str(rows))

        if int(rows[0][1]) != int(rows[1][1]):
            self.log.error('FAILED: Count of archFiles mismatch for the Copies')
            self.status = constants.FAILED
        else:
            self.log.info('VALIDATION: SUCCESS')

    def tear_down(self):
        """Tear Down Function of this Case"""
        # 5: CleanUp the environment
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
