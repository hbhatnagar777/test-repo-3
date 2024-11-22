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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper

class TestCase(CVTestCase):
    """ Unix snap"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Snap Backup - LVM testing scenario - Striped LV for Snap'
        self.tcinputs = {
            "SubclientContent": None,
            "ScanType": None,
            "MediaAgentName": None,
            "RestoreLocation": None,
            "DiskLibLocation": None,
            "SnapEngine": None
            }

    def run(self):
        """Main function for test case execution"""
        log = self.log

        try:
            log.info("Started executing %s testcase", format(self.id))
            snap_helper = UnixSnapHelper(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper.acceptance_tamplate()
            self.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: [%s]', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            snap_helper.cleanup()
        