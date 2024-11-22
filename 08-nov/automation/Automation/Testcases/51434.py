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

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi- Backup and restore with save while active option *SYNCLIB
        Step1, configure BackupSet and Subclient with multiple libraries as content and enable SYNCLIB.
        Step2: On client, create a libraries and objects.
        Step3: Run a full backup for the subclient.
        Step4: verify the full backup logs and validate all advanced options.
        Step5, Run a restore of the full backup data and verify correct data is restored.
        Step6, Add new data on all the libraries for the incremental backup
        Step7, Run an incremental job for the subclient
        Step8, Run a restore of the full + incremental  backup data and verify correct data is restored.
        Step9, Add new data on all the libraries for the Differential  backup
        Step10, Run an Differential backup job for the subclient
        Step11, Run a restore of the latest data and verify correct data is restored.
        Step12, Perform cleanup of data on client machine
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi- Backup and restore of LFS data with save while active option *SYNCLIB"
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
        self.IBMiMode = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE

            self.log.info("*** STARTING RUN FOR SC ADDITIONAL OPTIONS validation WITH <ContentFIle> ***")
            self.log.info("Step1, configure BackupSet and Subclient with ContentFile content")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "subclient_{0}".format(self.id)
            srclib = ["TC{0}".format(self.id), "TC{0}1".format(self.id), "TC{0}2".format(self.id)]
            sc_content = []
            for each in srclib:
                sc_content.append(self.client_machine.lib_to_path(each))
            destlib = "RST{0}".format(self.id)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=sc_content,
                                         scan_type=self.scan_type,
                                         delete=True)
            if self.IBMiMode == "VTLParallel":
                self.log.info("Enable multiple drives option for VTL Backup")
                self.helper.set_vtl_multiple_drives()
            self.log.info("update the subclient additional options and set SWA(*SYNCLIB.)")
            sc_options = {'savact': '*SYNCLIB',
                          'savactwait': 345,
                          'savactmsgq': 'QSYS/QSYSOPR',
                          'txtlibSyncCheckPoint': 'SNDMSG MSG("AUTOMATION SYNCLIB TC#{0}") TOUSR(*SYSOPR)'.format(
                              self.id),
                          'dtacpr': '*NO',
                          'updhst': False,
                          'accpth': '*SYSVAL',
                          'tgtrls': self.client_machine.get_ibmi_version("*SUPPORTED"),
                          'pvtaut': False,
                          'qdta': False,
                          'splfdta': False,
                          'savfdta': False
                          }
            self.helper.set_ibmi_sc_options(**sc_options)
            self.log.info("Step2: On client, create a libraries and objects.".format(srclib))
            for each in srclib:
                self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=10, prefix="F")

            self.log.info("Step3: Run a full backup for the subclient.")
            job = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Step4: verify the full backup logs and validate all advanced options.")
            # Log verification fail for VTL backups as logging would be different.
            # self.helper.verify_ibmi_sc_options(jobid=job.job_id, **sc_options)

            self.log.info("Step5, Run a restore of the full backup data"
                          " and verify correct data is restored.")
            for each in srclib:
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                               data_path=self.client_machine.lib_to_path(each),
                                               tmp_path=self.client_machine.lib_to_path(destlib),
                                               data_path_leaf="")

            self.log.info("Step6, Add new data on all the libraries for the incremental backup")
            object_name = ['SRCPF1', "SRCPF2", "SRCPF3"]
            for each in srclib:
                self.log.info("Adding data under library: %s", each)
                for objs in object_name:
                    self.client_machine.create_sourcepf(library=each, object_name=objs)

            self.log.info("Step7, Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            job = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step8, Run a restore of the full + incremental  backup data"
                          " and verify correct data is restored.")
            for each in srclib:
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                               data_path=self.client_machine.lib_to_path(each),
                                               tmp_path=self.client_machine.lib_to_path(destlib),
                                               data_path_leaf="")

            self.log.info("Step9, Add new data on all the libraries for the Differential  backup")
            object_name = ['DRCPF1', "DRCPF2", "DRCPF3"]
            for each in srclib:
                self.log.info("Adding data under library: %s", each)
                for objs in object_name:
                    self.client_machine.create_sourcepf(library=each, object_name=objs)

            self.log.info("Step10, Run an Differential backup job for the subclient"
                          " and verify it completes without failures.")
            job = self.helper.run_backup(backup_level="Differential")[0]

            self.log.info("Step11, Run a restore of the latest data"
                          " and verify correct data is restored.")
            for each in srclib:
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                               data_path=self.client_machine.lib_to_path(each),
                                               tmp_path=self.client_machine.lib_to_path(destlib),
                                               data_path_leaf="")

            self.log.info("Step12, Perform cleanup of data on client machine")

            for each in srclib:
                self.client_machine.manage_library(operation='delete', object_name=each)
            self.client_machine.manage_library(operation='delete', object_name=destlib)

            self.log.info("**SYNCLIB BACKUP AND RESTORE COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
