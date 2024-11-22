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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """ Class for executing
        DR Backup on IBMi client with VTL Storage Policy.
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
        self.name = "IBMi - DR Backup using VTL Storage Policy with *RESUME"
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
            self.subclient_name = "subclient_{0}_VTL_DR".format(self.id)
            xtra_lib = []
            destlib="DRVTLRST"
            xtra_lib.append("DR{0}".format(self.id))
            #xtra_lib.append("DR{0}1".format(self.id))
            self.log.info("Step3, Create extra libraries on IBMi client")
            for each in xtra_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.populate_lib_with_data(library_name=each,
                                                       tc_id=self.id,
                                                       count=5)
            self.client_machine.manage_library(operation='delete', object_name=destlib)
            xtra_lib_path = []
            for each in xtra_lib:
                xtra_lib_path.append(self.client_machine.lib_to_path(each))
            self.dr = {'temp_dir': '/var/DR_VTL',
                       'save_security': True,
                       'save_config': True,
                       'backup_max_time': 123,
                       'user_program': '',
                       'print_system_info': False,
                       'notify_user': True,
                       'notify_delay': 1,
                       'notify_message': 'Automation_run_DR_VTL_Backup_started',
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
                                                 data_readers=1,
                                                 allow_multiple_readers=True,
                                                 delete=True,
                                                 **self.dr
                                                 )
            self.log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
            self.log.info("Step4, Run a DR backup for the subclient "
                          "and verify it completes without failures.")
            drjob = self.helper.run_backup_verify(scan_type, "Full")[0]

            self.log.info("Reconnect with IBMi client.")
            self.client_machine.reconnect()

            # Ignoring find operation and verification
            # self.log.info("Step5, Run a find operation for the full job and verify the results.")

            # for content in xtra_lib_path:
            #     self.log.info("Run a find and verify operation for extra library {0}.".format(content))
            #     self.helper.run_find_verify(content)

            self.log.info("Step6, Verify that backup used tape media")
            query_tape = ("select MM.BarCode, MM.MediaTypeId, Vol.VolumeId from MMMedia as MM INNER JOIN MMVolume as "
                          "Vol on MM.MediaId=Vol.MediaId where MediaTypeId=2004 and Vol.VolumeId in (select volumeId "
                          "from archChunk where id in ( select archChunkId from archChunkMapping where jobId={0}))"
                          ).format(drjob.job_id)
            self.csdb.execute(query_tape)
            rows = self.csdb.fetch_all_rows()
            if not rows:
                raise Exception("Could not find the tapes for backup job")
            else:
                for row in rows:
                    self.log.info("Tape information for backup job %s, Tape Barcode %s", str(drjob.job_id), row[0])

            self.log.info("Step7, Run a restore of the extra libraries from DR  backup data"
                          " and verify correct data is restored.")

            for each in xtra_lib:
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                               data_path="{0}".format(self.client_machine.lib_to_path(each)),
                                               tmp_path="{0}".format(self.client_machine.lib_to_path(destlib)),
                                               data_path_leaf="")
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.manage_library(operation='delete', object_name=destlib)

            self.log.info("**%s SCAN RUN COMPLETED SUCCESSFULLY**", scan_type.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED