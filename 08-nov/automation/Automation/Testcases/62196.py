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

    run()              --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from Server.DisasterRecovery.drhelper import DRHelper


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
        self.name = "TAPE_IMPORT_ON_DR_RESTORED_COMMCELL"
        self.tcinputs = {
            "TapeLibrary": None,
            "DRPath": None,
            "ClientName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.CCM_helper = CCMHelper(self)
        self.DR_Helper = DRHelper(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.DR_Helper.set_er_directory(self.tcinputs["DRPath"])
            clients_list = [client for client in self.commcell.clients.all_clients]
            self.DR_Helper.trigger_dr_backup(client_list=clients_list)
            self.CCM_helper.create_entities(tape_library=self.tcinputs["TapeLibrary"])
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"])
            media_list = self.CCM_helper.get_barcode_list(new_subclient.subclient_id)
            self.DR_Helper.restore_db_with_csrecovery_assistant(
                dbdumplocation=self.tcinputs["DRPath"],
                operation="production",
                start_services_after_recovery=True
            )
            self.CCM_helper.create_destination_commcell(self.inputJSONnode["commcell"]["webconsoleHostname"],
                                                        self.inputJSONnode['commcell']['commcellUsername'],
                                                        self.inputJSONnode['commcell']['commcellPassword'])
            self.CCM_helper.tape_import(media_list, foreign_media_import=True)
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"],
                                                                                destination_commcell=True)
            new_backupset.restore_out_of_place(client=self.client,
                                           destination_path=self.tcinputs["RestoreFolder"],
                                           paths=[],
                                           fs_options={"index_free_restore": True},
                                           restore_jobs=self.CCM_helper.get_jobs_for_subclient(new_subclient))

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
