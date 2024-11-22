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
    __init__()             --  Initialize TestCase clas

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """ Class for executing
        IBMi - DR Backup on IBMi client with *RESUME
        Step1, Create backupset for this testcase if it doesn't exist
        Step2, Create subclient if it doesn't exist.
        Step3, Create all the libraries on IBMi client.
        Step4, Run a full backup for the subclient and verify it completes without failures.
        Step5, Run a restore of the full backup data and verify correct data is restored.
        Step6, Run a find operation for the full job and verify the results.
        Step7, Verify that backup used tape media
    """

    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - DR Backup on IBMi client with *RESUME"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = ""
        self.helper = None
        self.storage_policy = None
        self.client_name = ""
        self.subclient_name = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = None
        self.dr = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            scan_type = ScanType.RECURSIVE
            # Create backup set
            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=False)
            # Create the subclient content paths
            self.log.info("Step2, Create subclient for the scan type "
                          "%s if it doesn't exist.", scan_type.name)
            self.subclient_name = "subclient_{0}_DR".format(self.id)
            xtra_lib = ["DR{0}".format(self.id), "DR1{0}".format(self.id)]
            xtra_lib_path = []
            for each in xtra_lib:
                xtra_lib_path.append(self.client_machine.lib_to_path(each))
            self.dr = {'temp_dir': '/var/DR_Auto',
                       'save_security': True,
                       'save_config': False,
                       'backup_max_time': 250,
                       'user_program': '',
                       'print_system_info': False,
                       'notify_user': True,
                       'notify_delay': 1,
                       'notify_message': 'Automation_run_DR_Backup_started',
                       'user_ipl_program': '',
                       'rstd_cmd': '',
                       'dvd_image_format': 'AUTO_%y%m%d_',
                       'accpth': '*YES',
                       'updhst': True,
                       'splfdta': True
                       }
            self.helper.create_ibmi_dr_subclient(subclient_name=self.subclient_name,
                                                 storage_policy=self.storage_policy,
                                                 additional_library=xtra_lib_path,
                                                 data_readers=5,
                                                 allow_multiple_readers=True,
                                                 delete=True,
                                                 **self.dr
                                                 )
            self.log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
            self.log.info("Step3, Create extra libraries on IBMi client")
            for each in xtra_lib:
                self.client_machine.populate_lib_with_data(library_name=each,
                                                           tc_id=self.id,
                                                           count=5)
            self.log.info("Step4, Run a full backup for the subclient "
                          "and verify it completes without failures.")
            self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Reconnect with IBMi client.")
            self.client_machine.reconnect()

            self.log.info("Step5, check DR job log if correct parameters are used")
            self.log.info("Verify batch time limit value [{0}]".format(self.dr['backup_max_time']))
            self.helper.verify_from_log(logfile="cvd*.log",
                                        regex="ENDSBS",
                                        jobid=None,
                                        expectedvalue="{0}".format(self.dr['backup_max_time']))

            self.log.info("Verify SAVSYS completion message")
            if self.dr['save_security']:
                if self.dr['save_config']:
                    self.helper.verify_from_log('cvd*.log',
                                                'CMDEXEC',
                                                expectedvalue="SAVSYS Backup is completed"
                                                )
                elif not self.dr['save_config']:
                    self.helper.verify_from_log('cvd*.log',
                                                'CMDEXEC',
                                                expectedvalue="SAVSYS Backup is completed without CFG"
                                                )
            elif not self.dr['save_security']:
                if self.dr['save_config']:
                    self.helper.verify_from_log('cvd*.log',
                                                'CMDEXEC',
                                                expectedvalue="SAVSYS Backup is completed without SECDTA"
                                                )
                elif not self.dr['save_config']:
                    self.helper.verify_from_log('cvd*.log',
                                                'CMDEXEC',
                                                expectedvalue="SAVSYS Backup is completed without CFG & SECDTA"
                                                )
            self.log.info("Verify SAVLIB command for Commvault libraries.")
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="SAVLIB LIB(CVLIB CVLIBOBJ) DEV(CVVRTOPT)"
                                        )
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="objects saved from library CVLIB."
                                        )
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="objects saved from library CVLIBOBJ"
                                        )
            self.log.info("Verify SAVLIB command for *IBM libraries.")
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="SAVLIB LIB(*IBM) DEV(CVVRTOPT)"
                                        )
            self.log.info("Verify SAVLIB command for sytem libraries with user data.")
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="SAVLIB LIB(QSYS2 QGPL QUSRSYS) DEV(CVVRTOPT)"
                                        )
            self.log.info("Verify extra library backup initiation.")
            for each in xtra_lib:
                self.helper.verify_from_log('cvd*.log',
                                            'CMDEXEC',
                                            expectedvalue="objects saved from library {0}".format(each)
                                            )
            self.log.info("Verify IFS save command initiation.")
            self.helper.verify_from_log('cvd*.log',
                                        'CMDEXEC',
                                        expectedvalue="SAV DEV('/QSYS.LIB/CVVRTOPT.DEVD')"
                                        )
            for each in xtra_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("**%s SCAN RUN COMPLETED SUCCESSFULLY**", scan_type.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
