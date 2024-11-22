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
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper


class TestCase(CVTestCase):
    """Class for executing of CCM Export testcase """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SERVER_COMMCELL MIGRATION_EXPORT FOLDER"
        self.tcinputs = {
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ClientName": None,
            "MountPathLocation": None,
            "MountPathUserName": None,
            "MountPathPassword": None
        }

    def setup(self):
        """Setup function of this testcase"""

        self.ccm_helper = CCMHelper(self)

    def run(self):
        """Main function for test case execution"""

        try:

            self.ccm_helper.create_entities(self.tcinputs["MountPathLocation"],
                                            self.tcinputs["MountPathUserName"],
                                            self.tcinputs["MountPathPassword"])
            export_options = {
                "pathType": self.tcinputs["ExportPathType"],
                "userName": self.tcinputs["ExportUserName"],
                "password": self.tcinputs["ExportPassword"],
                "captureMediaAgents": False
            }
            ccm_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"],
                                                     client_names=[self.client.client_name],
                                                     options=export_options)

            self.log.info("Started CCM Export Job: %s", ccm_job.job_id)

            if ccm_job.wait_for_completion():
                self.log.info("CCM Export Job id %s "
                              "completed sucessfully", ccm_job.job_id)
            else:
                self.log.error("CCM Export Job id %s "
                               "failed/ killed", ccm_job.job_id)
                raise Exception("CCM Export job failed")

        except Exception as excp:
            self.ccm_helper.server.fail(excp)
