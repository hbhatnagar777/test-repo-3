# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing

        File System Data Protection Using Problematic Dataset - Full, Incremental, Synthetic Full
        This test case will cover acceptance using the problematic dataset.

        01. Create a new backupset.

        02. Create a new subclient.

        03. Generate the problematic dataset.

        04. Run a Full backup and let it complete.

        05. Run an Incremental backup and let it complete.

        06. Run a Synthetic Full backup and let it complete.

        07. Run an In Place restore.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection Using Problematic Dataset - Full, Incremental, Synthetic Full"
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.id = None
        self.client_machine = None
        self.cleanup_run = None
        self.RETAIN_DAYS = None
        self.tmp_path = None
        self.full_path = None
        self.incr_path = None
        self.tmp_path = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.sc_name = '_'.join(("subclient", str(self.id)))
        self.content = self.slash_format.join((self.test_path, str(self.id), self.sc_name))
        self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name))
        self.incr_path = self.slash_format.join((self.content, "incr"))

    def run(self):
        """Main function for test case execution"""
        try:

            self.log.info(self.__doc__)

            self.log.info("01. Create a new backupset.")
            self.helper.create_backupset(self.bset_name, delete=self.cleanup_run)

            self.log.info("02. Create a new subclient.")
            self.helper.create_subclient(name=self.sc_name, storage_policy=self.storage_policy, content=[self.content])

            self.log.info(f"04. Generating the problematic dataset under {self.content}.")
            self.client_machine.generate_test_data(self.content, problematic=True)

            self.log.info("05. Run a Full backup and let it complete.")
            self.helper.run_backup_verify(backup_level="Full")

            self.log.info(f"06. Adding new data for Incremental backup under {self.incr_path}")
            self.helper.add_new_data_incr(self.incr_path, self.slash_format)

            self.log.info("07. Run an Incremental backup and let it complete.")
            self.helper.run_backup_verify(backup_level="Incremental")

            self.log.info("08. Run a Synthetic Full backup and let it complete.")
            synth_full = self.helper.run_backup_verify(backup_level="Synthetic_full")[0]

            self.log.info("09. Run an In Place restore.")
            if self.client_machine.os_info == "WINDOWS":
                self.client_machine.rename_file_or_folder(self.content, "".join((self.content, "_source")))
                self.helper.restore_in_place([self.content])

                # HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled
                # IN CASE OF FAILURE, ENABLE IT AND REBOOT SETUP. ONE OF THE POSSIBLE REASONS BEHIND FAILURE.

                # FOR PROBLEMATIC DATA THE METADATA AND CHECKSUM COMPARISON HAS BEEN IMPLEMENTED DIFFERENTLY.
                # THE REASON IS ISSUES WITH ASCII CHARACTERS IN ProblematicData\Files 0 to 255

                source_path = self.content
                dest_path = "".join((self.content, "_source"))

                # METADATA COMPARISON
                # COMPARISON 1 - COMPARE EVERYTHING EXCEPT PROBLEMATIC DATA SET EXCEPT FOLDER NAMED Files 0 to 255
                cmd = "GCI -R {} -EA Ignore -Exclude 'Files 0 to 255' | WHERE {{$_.FullName -notlike '*Files 0 to 255*'}} | " \
                      "FT -AutoSize -HideTableHeaders -Property @{{e={{$_.LastWriteTime}}}}, @{{e={{$_.Length}};width=50}}, @{{e={{$_.FullName -replace '^.{{'+$({})+'}}'}};width=10000}} | " \
                      "Out-String -Width 60960"

                source_metadata = self.client_machine.execute_command(cmd.format(source_path, len(source_path)+1)).output.split("\r\n")
                dest_metadata = self.client_machine.execute_command(cmd.format(dest_path, len(dest_path)+1)).output.split("\r\n")

                result, diff_op = self.client_machine.compare_lists(source_metadata, dest_metadata)

                if result:
                    self.log.info("Metadata comparison successful.")
                else:
                    self.log.info(f"Metadata comparison failed \n {diff_op}")
                    raise Exception("Metadata comparison failed.")

                # COMPARISON 2 - COMPARE PROBLEMATIC DATA SET FOLDER NAMED Files 0 to 255 SIMPLE dir OUTPUT COMPARISON
                cmd = "cmd.exe /c dir /b /s '{}\\ProblematicData\\Files 0 to 255'"

                source_metadata = self.client_machine.execute_command(cmd.format(source_path)).output.split("\r\n")
                source_metadata = [i[len(source_path):] for i in source_metadata]

                dest_metadata = self.client_machine.execute_command(cmd.format(dest_path)).output.split("\r\n")
                dest_metadata = [i[len(dest_path):] for i in dest_metadata]

                result, diff_op = self.client_machine.compare_lists(source_metadata, dest_metadata)

                if result:
                    self.log.info("Metadata comparison successful.")
                else:
                    self.log.info(f"Metadata comparison failed \n {diff_op}")
                    raise Exception("Metadata comparison failed.")

                # CHECKSUM COMPARISON
                # COMPARISON 1 - COMPARE EVERYTHING EXCEPT PROBLEMATIC DATA SET FOLDER NAMED Files 0 to 255, encrypted, File permissions
                cmd = "foreach($item in $(GCI -R -File {} -EA Ignore -Exclude 'Files 0 to 255', 'encrypted', 'File permissions' | " \
                      "WHERE {{$_.FullName -notlike '*Files 0 to 255*' -and $_.FullName -notlike '*encrypted*' -and $_.FullName -notlike '*File permissions*'}}).FullName) {{ Write-Host (Get-FileHash -Path $item -Algorithm MD5 | " \
                      "FT -Property Hash, @{{n='Path';e={{$_.Path -replace '^.{{'+$({})+'}}'}}}} -HideTableHeaders -AutoSize | Out-String).Trim()}} "

                source_checksum = self.client_machine.execute_command(cmd.format(source_path, len(source_path)+1)).output.split("\n")
                dest_checksum = self.client_machine.execute_command(cmd.format(dest_path, len(dest_path)+1)).output.split("\n")

                result, diff_op = self.client_machine.compare_lists(source_checksum, dest_checksum)

                if result:
                    self.log.info("Checksum comparison successful.")
                else:
                    self.log.info(f"Checksum comparison failed \n {diff_op}")
            else:
                self.helper.run_restore_verify(self.slash_format, self.content, self.tmp_path, str(self.id), synth_full, in_place=True)

                self.log.info("10. For UNIX FS, Running an Out of Place restore as well.")
                self.helper.run_restore_verify(self.slash_format, self.content, self.tmp_path, self.sc_name, synth_full)

            if self.cleanup_run:
                if self.client_machine.os_info == "WINDOWS":
                    self.log.info("Cleaning up data")
                    self.client_machine.create_directory(f"{self.test_path}\\empty")
                    self.client_machine.execute_command(f"cmd.exe /c robocopy '{self.test_path}\\empty' '{self.content}' /purge")
                    self.client_machine.execute_command(f"cmd.exe /c robocopy '{self.test_path}\\empty' '{self.content}_source' /purge")
                    self.client_machine.remove_directory(self.test_path)
                else:
                    self.client_machine.remove_directory(self.content)
                self.instance.backupsets.delete(self.bset_name)
            else:
                self.client_machine.remove_directory(self.content, self.RETAIN_DAYS)

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED
