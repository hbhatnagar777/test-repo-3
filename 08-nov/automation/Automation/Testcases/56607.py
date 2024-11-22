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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants, logger
from VirtualServer.VSAUtils import VsaTestCaseUtils

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of AMAZON Full Snap backup
    and Restore test case - v2 File Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AMAZON SNAP Incremental  Backup and Restore Cases for V2 file indexing"
        self.product = self.products_list.VIRTUALIZATIONAMAZON
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.failure_msg = ''

    def run(self):

        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_method = "SNAP"
            backup_options.backup_type = "INCREMENTAL"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            self.log.info("Verifying that File Indexing job runs and completes successfully")
            file_indexing_job_id = auto_subclient.get_in_line_file_indexing_job()

            self.log.info("Validating File indexing job status")
            auto_subclient.check_status_file_indexing(file_indexing_job_id)
            try:
                self.log.info('Get details about the File Indexing job to extract child VM Backup Jobs, the VM GUIDs,'
                              'and proxy used for validation')

                file_indexing_job_details = auto_subclient.get_file_indexing_job_details(file_indexing_job_id)
                for guid in file_indexing_job_details.keys():
                    child_backup_job_id = file_indexing_job_details[guid][0]
                    vm_guid = guid
                    self.log.info("Validate Archive Files")
                    auto_subclient.validate_file_indexing_archive_files(child_backup_job_id)
            except Exception as exp:
                self.log.error("Exception when validating File Indexing: %s" % str(exp))

            try:
                VirtualServerUtils.decorative_log("FULL VM out of place restore")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
                if auto_subclient and vm_restore_options:
                    auto_subclient.post_restore_clean_up(vm_restore_options,
                                                         status=self.test_individual_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

