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
    __init__()              --  initialize TestCase class

    ccm_export()            --  Function to perform CCM Export

    ccm_import()            --  Function to perform CCM Import

    create_destination_cs() --  Post CCM restore from a tape library

    restore_a_job()         --  Function to restore a backup job

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

"""
STEPS:
1. On source cs, create a tape library and run backup jobs to the library.
2. Perform CCM of the client.	
3. Copy media from source cs to the tape libraries imported on the destination cs.
4. Restore a job on client on destination cs.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Post CCM, Restore a job from a tape library"
        self.ccm_helper = None
        self.destination_cs = None
        self.tcinputs = {
            "ClientName": None,
            "TapeLibrary": None,
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ImportLocation": None,
            "ImportPathType": None,
            "ImportUserName": None,
            "ImportPassword": None,
            "DestinationCommcellHostname": None,
            "DestinationCommcellUsername": None,
            "DestinationCommcellPassword": None,
            "RestoreFolder": None
        }

    def ccm_export(self):
        """Function to run CCM Export."""
        options = {
            "pathType": self.tcinputs["ExportPathType"],
            "userName": self.tcinputs["ExportUserName"],
            "password": self.tcinputs["ExportPassword"],
            "captureMediaAgents": False
        }

        export_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"],
                                                    self.tcinputs["ClientName"],
                                                    options=options)

        self.log.info("Started CCM Export Job: {}".format(export_job.job_id))

        if export_job.wait_for_completion():
            self.log.info("CCM Export Job id {} completed successfully".format(export_job.job_id))
        else:
            self.log.error("CCM Export Job id {} failed/ killed".format(export_job.job_id))
            raise Exception("CCM Export job failed")

    def create_destination_cs(self):
        """Function to create Destination Commcell Object."""
        self.destination_cs = self.ccm_helper.create_destination_commcell(
            self.tcinputs["DestinationCommcellHostname"],
            self.tcinputs["DestinationCommcellUsername"],
            self.tcinputs["DestinationCommcellPassword"]
        )
        self.log.info("Successfully created and logged into destination commcell {}".format(
            self.destination_cs.commserv_name))

    def ccm_import(self):
        """Function to run CCM Import."""
        import_job = self.ccm_helper.run_ccm_import(
            self.tcinputs["ImportLocation"]
        )
        self.log.info("Started CCM Import Job: {}".format(import_job.job_id))

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id {} completed successfully".format(import_job.job_id))
        else:
            self.log.error("CCM Import Job id {} failed/ killed".format(import_job.job_id))
            raise Exception("CCM Import job failed")

    def restore_a_job(self):
        """Function to restore a backup job on destination commcell."""
        subclient = self.ccm_helper.get_latest_subclient(self.tcinputs["ClientName"], destination_commcell=True)
        job = subclient.restore_out_of_place(self.ccm_helper.destination_cs.commserv_name,
                                             self.tcinputs["RestoreFolder"],
                                             subclient.content)

        self.log.info("Restore job started with Jobid : {}".format(job.job_id))

        if job.wait_for_completion():
            self.log.info("Restore Job with jobid {} completed successfully".format(job.job_id))

        else:
            self.log.error("Restore job with Jobid {} failed/ killed".format(job.job_id))
            raise Exception("Restore job failed post CCM")

    def setup(self):
        """Setup function of this test case"""
        self.ccm_helper = CCMHelper(self)
        self.ccm_helper.create_entities(tape_library=self.tcinputs["TapeLibrary"])

    def run(self):
        """Run function of this test case"""
        try:
            self.ccm_export()
            self.create_destination_cs()
            self.ccm_import()
            self.restore_a_job()

        except Exception as exp:
            self.log.error('Failed to execute test case with error {}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function for this test case"""
        try:
            self.destination_cs.clients.delete(self.tcinputs["ClientName"])

        except Exception as exp:
            self.log.error('Failed to execute test case with error {}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
