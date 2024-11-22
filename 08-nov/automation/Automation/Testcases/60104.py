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
    __init__()              --  Initialize TestCase class

    restore_verify()        -- Initiates restore for data backed up in the given job and
                                performs the applicable verifications

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Verify all IBMi advanced subclient options with VTL backup
        Step1: configure BackupSet and Subclient with advanced options for TC and VTL SP
        Step2: On client, create a library.
        Step3: Run a full backup for the subclient.
        Step4: verify the full backup logs and validate all advanced options.
        Step5: Run a Incremental backup for the subclient.
        Step6: verify the Inc backup logs and validate all advanced options.
        Step7: OOP Restore and validate the restored content.
        Step8: Run a Differential backup for the subclient.
        Step9: verify the Differential backup logs and validate all advanced options.
        Step10: OOP Restore and validate the restored content.
        Step11: Update the SC with new values for additional options.
        Step12: Run a full backup for the subclient.
        Step13: verify the full backup logs and validate all advanced options.
        Step14: Run a Inc backup for the subclient.
        Step15: verify the Inc backup logs and validate all advanced options.
        Step16: OOP Restore and validate the restored content.
        Step17: Run a Differential backup for the subclient.
        Step18: verify the Differential backup logs and validate all advanced options.
        Step19: OOP Restore and validate the restored content.
        Step20: Cleanup libraries from client disk
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify all IBMi advanced subclient options with VTL backup and restores"
        # Other attributes which will be initialized in FSHelper.populate_tc_inputs
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.scan_type = None
        self.job = None
        self.IBMiMode = None

    def restore_verify(self, source, destination):
        """
                Initiates restore for data backed up in the given job
                and performs the applicable verifications

                    Args:
                        source              (str)   : Source Library

                        destination        (str)   : destination library
        """
        self.client_machine.manage_library(operation='delete', object_name=destination)
        self.log.info("Starting restore {0} to destination library {1} ".format(source, destination))
        self.job = self.helper.restore_out_of_place(destination_path=self.client_machine.lib_to_path(destination),
                                                    paths=[self.client_machine.lib_to_path(source)],
                                                    restore_ACL=False,
                                                    preserve_level=0)
        self.log.info("Verify restore logs to verify parallel backup tapes are used")

        self.helper.compare_ibmi_data(source_path="{0}/*".format(self.client_machine.lib_to_path(destination)),
                                      destination_path="{0}/*".format(self.client_machine.lib_to_path(destination)))
        self.client_machine.manage_library(operation='delete', object_name=destination)
        return self.job

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE

            self.log.info("*** STARTING RUN FOR SC ADDITIONAL OPTIONS VALIDATION ***")
            self.log.info("Step1, configure BackupSet and Subclient with advanced options for TC and VTL SP")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "Subclient_{0}".format(self.id)
            srclib = "TC{0}".format(self.id)
            destlib = "TC{0}R".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]

            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=content,
                                         scan_type=self.scan_type,
                                         data_readers=2,
                                         allow_multiple_readers=True,
                                         delete=True)

            sc_options = {'savact': '*LIB',
                          'savactwait': 10,
                          'dtacpr': '*NO',
                          'dedupe_on_ibmi': False,
                          'updhst': False,
                          'accpth': '*SYSVAL',
                          'pvtaut': False,
                          'qdta': False,
                          'splfdta': False,
                          'savfdta': False,
                          'object_level': False
                          }
            self.helper.set_ibmi_sc_options(**sc_options)
            self.log.info("Step2: On client, create a library %s.", srclib)
            self.client_machine.manage_library(operation='delete', object_name=srclib)
            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=50, prefix="A")
            self.log.info("Step3: Run a full backup for the subclient.")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   **sc_options)
            self.log.info("Step5: Run a Incremental backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='INC1')
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step6: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   backup_level="Incremental",
                                                   **sc_options)
            self.log.info("Step7: OOP Restore and validate the restored content. Validate if parallel backup "
                          "tapes are used for restore.")
            self.job = self.restore_verify(source=srclib, destination=destlib)
            self.log.info("Step8: Run a Differential backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='DIFF1')
            self.job = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("Step9: verify the Differential backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   backup_level="Differential",
                                                   **sc_options)
            self.log.info("Step10: OOP Restore and validate the restored content. Validate if parallel backup "
                          "tapes are used for restore.")
            self.job = self.restore_verify(source=srclib, destination=destlib)

            self.log.info("Step11: Update the SC with new values for additional options.")
            sc_options1 = {'savact': '*SYSDFN',
                           'savactwait': 210,
                           'dtacpr': '*LOW',
                           'dedupe_on_ibmi': True,
                           'updhst': True,
                           'accpth': '*YES',
                           'tgtrls': self.client_machine.get_ibmi_version("*SUPPORTED"),
                           'pvtaut': True,
                           'qdta': True,
                           'splfdta': True,
                           'savfdta': True,
                           'object_level': False
                           }
            self.helper.set_ibmi_sc_options(**sc_options1)
            self.log.info("Step12: Run a full backup for the subclient.")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step13: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   **sc_options1)
            self.log.info("Step14: Run a Inc backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='INC2')
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step15: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   backup_level="Incremental",
                                                   **sc_options1)
            self.log.info("Step16: OOP Restore and validate the restored content.")
            self.job = self.restore_verify(source=srclib, destination=destlib)
            self.log.info("Step17: Run a Differential backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='DIFF2')
            self.job = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("Step18: verify the Differential backup logs and validate all advanced options.")
            self.helper.verify_ibmi_vtl_sc_options(jobid=self.job.job_id,
                                                   backup_level="Differential",
                                                   **sc_options1)
            self.log.info("Step19: OOP Restore and validate the restored content. Validate if parallel backup "
                          "tapes are used for restore.")
            self.job = self.restore_verify(source=srclib, destination=destlib)
            self.log.info("Step20: Cleanup libraries from client disk")
            self.client_machine.manage_library(operation='delete', object_name=srclib)

            self.log.info("**VTL BACKUP RUN VALIDATION OF ADVANCED SC OPTIONS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
