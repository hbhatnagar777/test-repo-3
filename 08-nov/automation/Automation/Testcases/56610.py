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

    setup()         -- sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  cleans up the element created during test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
from Reports.utils import TestCaseUtils



class TestCase(CVTestCase):
    """Class for executing Basic Acceptance Test of File Indexing from SYNTHETIC FULL Streaming Backup
    - v1/v2 File Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of v1/v2 File Indexing from SYNTHETIC Backup"
        self.product = self.products_list.VIRTUALIZATIONAMAZON
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}
        self.utils = TestCaseUtils(self)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.run_incr_before_synth = False
            backup_options.incr_level = "None"
            backup_options.backup_type = "SYNTHETIC_FULL"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            self.log.info("Validate Synthetic Full job for each VM and make sure each phase is successful.")

            auto_commcell.get_backup_phase_status(auto_subclient.backup_job.job_id)
            file_indexing_job_details = auto_subclient.get_file_indexing_job_details(auto_subclient.backup_job.job_id,
                                                                                     synthfull=True)
            try:
                for guid in file_indexing_job_details.keys():
                    child_backup_job_id = file_indexing_job_details[guid][0]
                    proxy_used = file_indexing_job_details[guid][1]
                    vm_guid = guid
                    self.log.info("Validate Archive Files")
                    auto_subclient.validate_file_indexing_archive_files(child_backup_job_id)
                    self.log.info("Archive Files is committed successfully")
            except Exception as exp:
                self.log.error("Exception when validating File Indexing: %s" % str(exp))

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED


