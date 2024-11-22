# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    setup()                 --  initial settings for the test case

    run()                   --  run function of this test case
"""

# Test Suite imports
import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper


class TestCase(CVTestCase):
    """Class for executing of CCM Import testcase """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "server_commcell migration _Temperory merge"
        self.tcinputs = {
            "DestinationCSHostName": None,
            "CSUserName": None,
            "CSPassword": None,
            "ImportLocation": None,
            "ClientName": None,
            "SQLUserName": None,
            "SQLPassword": None
        }
        self.ccm_helper = None

    def setup(self):
        """Setup function of this testcase"""

        self.ccm_helper = CCMHelper(self)
        self.ccm_helper.create_destination_commcell(self.tcinputs["DestinationCSHostName"],
                                                 self.tcinputs["CSUserName"],
                                                 self.tcinputs["CSPassword"])

    def run(self):
        """Main function for test case execution"""

        try:
            ccm_job = self.ccm_helper.run_ccm_import(self.tcinputs["ImportLocation"])
            self.log.info("Started CCM Import Job: %s", ccm_job.job_id)

            if ccm_job.wait_for_completion():
                self.log.info("CCM Import Job id %s "
                              "completed sucessfully", ccm_job.job_id)
            else:
                self.log.error("CCM Import Job id %s "
                               "failed/ killed", ccm_job.job_id)
                raise Exception("CCM Import job failed")

            self.ccm_helper.destination_cs.refresh()

            self.ccm_helper.set_libary_mapping(self.commcell.commserv_name)

            time.sleep(3 * 60)

            sub = self.ccm_helper.get_latest_subclient(client_name=self.tcinputs["ClientName"],
                                                       destination_commcell=True)
            restore_job = sub.restore_out_of_place(self.ccm_helper.destination_cs.commserv_name,
                                                   "c:\\Restore123",
                                                   sub.content)
            self.log.info("Restore job started with Jobid : %s", restore_job.job_id)

            if restore_job.wait_for_completion():
                self.log.info("Restore Job with jobid %s "
                              "completed sucessfully", restore_job.job_id)
            else:
                self.log.error("Restore job with Jobid %s "
                               "failed/ killed", restore_job.job_id)
                raise Exception("Restore job failed post CCM")

        except Exception as excp:
            self.ccm_helper.server.fail(excp)
