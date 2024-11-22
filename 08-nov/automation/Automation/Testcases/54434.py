# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()         --  initialize TestCase class

    setup()            --  setup function of this test case

    run()              --  run function of this test case

    create_entities()  --  Creates storage policy, backupset, subclient and starts a backup job on the subclient.

    get_media_list()   --  Retrieves media list from tape library created.

    tape_import()      --  Starts a tape import job.

    clean_entities()   --  Clears entities created during testcase run

    restore_job()      --  Restore by job
"""

"""
Design Steps:
1. Create the storage policy, backup set & sub client using a tape library. All the entities should be created
2. Run few backups to the subclient. Backups should be successfully completed 
3. Delete the subclient, backupset & storage policy. All the entities should be delete successfully 
4. Run the tape import from the tape media. Tape import should be complete successfully.
5. All the required entities should be created. All the required entities should be completed successfully 
6. Run a restore from tape imported data. Restores should be complete successfully.
"""

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
        self.name = "SERVER_COMMCELL_MIGRATION_TAPE_IMPORT"
        self.tcinputs = {
            "ClientName": None,
            "TapeLibrary": None,
            "RestoreFolderOnClient": None
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
            self.CCM_helper.clean_entities()
            self.commcell.run_data_aging()
            self.CCM_helper.tape_import(media_list)
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"])
            new_backupset.restore_out_of_place(client=self.client,
                                       destination_path=self.tcinputs["RestoreFolderOnClient"],
                                       paths=[],
                                       fs_options={"index_free_restore": True},
                                       restore_jobs=self.CCM_helper.get_jobs_for_subclient(new_subclient))

        except Exception as exp:
            self.CCM_helper.server.fail(exp)
