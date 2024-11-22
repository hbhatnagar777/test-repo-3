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
    __init__()         --  initialize TestCase class

    setup()            --  setup function of this test case

    run()              --  run function of this test case.
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
        self.name = "FOREIGN_COMMCELL_MERGE"
        self.tcinputs = {
            "ClientName": None,
            "TapeLibrary": None,
            "RestoreFolder": None,
            "ForeignCommcellHostname": None,
            "ForeignCommcellUsername": None,
            "ForeignCommcellPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.CCM_helper = CCMHelper(self)

    def run(self):
        """Run function of this test case"""
        try:
            self.CCM_helper.create_entities(tape_library=self.tcinputs["TapeLibrary"])
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"])
            media_list = self.CCM_helper.get_barcode_list(new_subclient.subclient_id)
            self.foreign_cs = self.CCM_helper.create_destination_commcell(
                self.tcinputs["ForeignCommcellHostname"],
                self.tcinputs["ForeignCommcellUsername"],
                self.tcinputs["ForeignCommcellPassword"]
            )
            self.CCM_helper.tape_import(media_list, foreign_media_import=True)
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"],
                                                                                destination_commcell=True)
            job = new_backupset.restore_out_of_place(client=self.client,
                                               destination_path=self.tcinputs["RestoreFolder"],
                                               paths=[],
                                               fs_options={"index_free_restore": True},
                                               restore_jobs=self.CCM_helper.get_jobs_for_subclient(new_subclient))
            if not job.wait_for_completion():
                raise Exception("Restore Job with id {} failed with message {}".format(job.job_id,
                                                                                       job.delay_reason))
            self.CCM_helper.clean_entities()


        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
