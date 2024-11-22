# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    run()                   --  run function of this test case
"""

from collections import deque
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Verify default subclient filters with regular and optimized scan
        For Non-VTL:
            Configure BackupSet and Subclients for TC
            Run a full backup for the subclient *IBM and verify if it completes without failures.
            Run find operation on index items and make sure default filters are not picked by backup.
            Repeat the same for Optimized scan backup
        For Non-VTL:
            Configure BackupSet and Subclients for TC
            Run a full backup for the subclient *IBM and verify if it completes without failures.
            Run find operation on index items and make sure default filters are not picked by backup.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify default subclient filters with regular and optimized scan"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.tcinputs = {
            "IBMiMode": None,
            "whichPython": None
        }
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.default_filters = None
        self.scan_type = None
        self.job = None
        self.IBMiMode = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = [ScanType.RECURSIVE]
            data_reader = 1
            if self.IBMiMode == "NON-VTL":
                self.scan_type.append(ScanType.OPTIMIZED)
                data_reader = 8
            self.default_filters = ["/QSYS.LIB/QDOC.LIB",
                                    "/QSYS.LIB/QRECOVERY.LIB",
                                    "/QSYS.LIB/QRPLOBJ.LIB",
                                    "/QSYS.LIB/QSPL.LIB",
                                    "/QSYS.LIB/QSRV.LIB",
                                    "/QSYS.LIB/QTEMP.LIB",
                                    "/QSYS.LIB/QRCL.LIB",
                                    "/QSYS.LIB/QUSRPYMSVR.LIB",
                                    "/QSYS.LIB/QUSER38.LIB",
                                    "/QSYS.LIB/QUSRRDARS.LIB",
                                    "/QSYS.LIB/QDSNX.LIB",
                                    "/QSYS.LIB/QUSRADSM.LIB",
                                    "/QSYS.LIB/QUSRBRM.LIB",
                                    "/QSYS.LIB/QUSRVI.LIB",
                                    "/QSYS.LIB/QGPL38.LIB",
                                    "/QSYS.LIB/QUSRDIRCF.LIB",
                                    "/QSYS.LIB/QMGTC.LIB",
                                    "/QSYS.LIB/QUSRDIRCL.LIB",
                                    "/QSYS.LIB/QMGTC2.LIB",
                                    "/QSYS.LIB/QUSRDIRDB.LIB",
                                    "/QSYS.LIB/QMPGDATA.LIB",
                                    "/QSYS.LIB/QSRVAGT.LIB",
                                    "/QSYS.LIB/QUSRIJS.LIB",
                                    "/QSYS.LIB/QMQMDATA.LIB",
                                    "/QSYS.LIB/QUSRINFSKR.LIB",
                                    "/QSYS.LIB/QMQMPROC.LIB",
                                    "/QSYS.LIB/QUSRNOTES.LIB",
                                    "/QSYS.LIB/QPFRDATA.LIB",
                                    "/QSYS.LIB/QUSROND.LIB",
                                    "/QSYS.LIB/QUSRPOSGS.LIB",
                                    "/QSYS.LIB/QS36F.LIB",
                                    "/QSYS.LIB/QUSRPOSSA.LIB"]
            for each in self.scan_type:
                self.log.info("*** STARTING RUN FOR SC: *IBM with %s SCAN **", each.name)
                self.log.info("Configure BackupSet and Subclients for TC")
                self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}_{1}".format(self.id, self.IBMiMode),
                                                      subclient_name="*IBM",
                                                      storage_policy=self.storage_policy,
                                                      scan_type=each,
                                                      data_readers=data_reader,
                                                      allow_multiple_readers=True,
                                                      delete=False)

                self.log.info("Run a full backup for the subclient *IBM and verify if it completes without failures.")
                self.job = self.helper.run_backup_verify(each, "Full")[0]

                self.log.info("Run find operation and verify if all default filters are not picked for backup.")
                for each1 in self.default_filters:
                    self.log.info("run Find operation for library [{0}] and verify "
                                  "if it is dropped from backup".format(each1))
                    if self.helper.is_path_found_in_index(path=each1, job=self.job):
                        raise Exception(
                            "Default filter {0} got picked by backup job.".format(each1))
                self.log.info("**%s SCAN RUN OF *IBM SC PROPERLY DROPPED DEFAULT FILTERS**", each.name)

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
