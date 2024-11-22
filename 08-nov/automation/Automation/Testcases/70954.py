# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    run()               --   run function of this test case calls SnapHelper Class to execute and
                            Validate  Below Operations:

    TC Steps:
    1. Add array, Create library, Storage Policy,
        and create a subclient
    2. Set Snap Primary as Spool Copy
    3. Run Backup copy where source of Backup copy is Snap copy and validate if snaps are
        deleted from Snap copy as it was spool
    4. Cleanup"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from cvpysdk.exception import SDKException


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Spool copy"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None
        }
        self.name = """Test Case for Basic Acceptance Test of IntelliSnap Spool copy"""
        self.snapconstants = None
        self.snaphelper = None

    def run(self):
        """Main function for test case execution
        run function of this test case calls SnapHelper Class to execute and Validate"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Initializing pre-requisites setup for this test case")
            self.snaphelper.setup()

            # set Snap copy as spool
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.snap_copy_name)
            spcopy.copy_retention = (0, 0, 0, 0)

            self.snaphelper.add_array()

            # Run Snapbackup and Backup Copy and Validate if snapshots are deleted within first 2 cleanups
            job = self.snaphelper.snap_backup()
            self.snaphelper.backup_copy()
            wait_time = 0
            while True:
                volumeid_val = self.snapconstants.execute_query(self.snapconstants.get_volumeid_da,
                                                                {'a': job.job_id, 'b': spcopy.copy_id})
                if volumeid_val[0][0] in [None, ' ', '']:
                    break
                else:
                    self.log.info("Sleeping for 2 minutes")
                    time.sleep(120)
                    wait_time += 2
                if wait_time > 4:
                    raise Exception(
                        f'Snapshot of jobid: {job.job_id} is not yet deleted,'
                        'please check the CVMA logs'
                    )

            self.log.info(f'Snapshot for job {job.job_id} deleted successfully')

            self.log.info("****Cleanup of Snap Entities****")
            self.snaphelper.cleanup()
            self.snaphelper.delete_array()
            self.log.info("TestCase completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
