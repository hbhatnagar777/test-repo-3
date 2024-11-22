# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case
TestCase is the only class definied in this file
TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize test case class object

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Main function for test case execution
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper

class TestCase(CVTestCase):
    """ Class for executing the test case.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Unix File System - Snap Backup -  Instant Clone Restore - Basic Acceptance"
        self.tcinputs = {
            "SubclientContent": None,
            "CloneMountPath": None,
            "ScanType": None,
            "MediaAgentName": None,
            "RestoreLocation": None,
            "DiskLibLocation": None,
            "SnapEngine": None
            }
        self.reservation_period = None
        self.post_clone_command = None
        self.clone_cleanup_script = None
        self.instant_clone_options = {}

    def setup(self):
        """Initializes pre-requisites for this test case."""

        # FOLLOWING INPUTS CAN BE PROVIDED THOUGH THEY AREN'T REQUIRED FOR ACCEPTANCE
        self.reservation_period = int(self.tcinputs.get("ReservationTime", 120))  # 2 MINUTES BY DEFAULT
        self.post_clone_command = self.tcinputs.get("PostCloneCmd", None)
        self.clone_cleanup_script = self.tcinputs.get("CleanupScriptPath", None)
        self.instant_clone_options = {'clone_mount_path': self.tcinputs.get('CloneMountPath'),
                                      'reservation_time': self.reservation_period,
                                      'post_clone_command': self.post_clone_command,
                                      'clone_cleanup_script': self.clone_cleanup_script,
                                      'instant_clone_src_path': [self.tcinputs['SubclientContent']]
                                      }

    def run(self):
        """Main function for test case execution"""

        try:
            snap_helper = UnixSnapHelper(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper.acceptance_tamplate(instant_clone_options=self.instant_clone_options,
                                            restore_path=self.tcinputs.get('CloneMountPath'),
                                            no_of_streams=10)

        except Exception as excep:
            self.log.error(f"Failed with error: {str(excep)}")
            self.result_string = str(excep)
            self.status = constants.FAILED
            snap_helper.cleanup()

