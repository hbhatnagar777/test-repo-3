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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.datacube.constants import IndexServerConstants
from dynamicindex.Datacube.exchange_client_helper import ExchangeClientHelper
from dynamicindex.index_server_helper import IndexServerHelper


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
        self.name = "CvSolr Multi Node Index server - Validation of exchange role"
        self.tcinputs = {
            "IndexServerNodeNames": None,
            "RestoreMachineName": None
        }
        self.exchange_client = None
        self.node_machine_obj = None
        self.media_agent_machine_obj = None
        self.exchange_helper = None
        self.restore_path = None
        self.is_helper = None
        self.index_server_name = None
        self.index_server_roles = [IndexServerConstants.ROLE_EXCHANGE_INDEX]

    def setup(self):
        """Setup function of this test case"""
        self.node_machine_obj = [Machine(machine_name=node, commcell_object=self.commcell)
                                 for node in self.tcinputs['IndexServerNodeNames'].split(',')]
        self.media_agent_machine_obj = Machine(machine_name=self.tcinputs['RestoreMachineName'],
                                               commcell_object=self.commcell)
        option_selector_obj = OptionsSelector(self.commcell)
        index_directory_drive_letters = [option_selector_obj.get_drive(node) for node in self.node_machine_obj]
        restore_directory_drive_letter = option_selector_obj.get_drive(self.media_agent_machine_obj)
        self.tcinputs['IndexLocation'] = [f"{drive}index_directory{self.id}" for drive in index_directory_drive_letters]
        self.restore_path = f"{restore_directory_drive_letter}restore_mail_{self.id}"
        self.index_server_name = "IS_%s" % self.id
        IndexServerHelper.create_index_server(self.commcell, self.index_server_name,
                                              self.tcinputs['IndexServerNodeNames'].split(','),
                                              self.tcinputs['IndexLocation'], self.index_server_roles)
        self.is_helper = IndexServerHelper(self.commcell, self.index_server_name)
        self.exchange_helper = ExchangeClientHelper(self.commcell)
        self.exchange_client = self.exchange_helper.create_exchange_mailbox_client(
            tc_object=self, index_server_name=self.index_server_name)

    def run(self):
        """Run function of this test case"""
        self.exchange_helper.add_user_mailbox(self.exchange_client)
        self.exchange_client.cvoperations.run_backup(post_backup_wait=True)
        self.exchange_helper.restore_exchange_mailbox_client(exchange_mailbox_client=self.exchange_client,
                                                             restore_machine=self.tcinputs['RestoreMachineName'],
                                                             restore_path=self.restore_path)

    def tear_down(self):
        """Tear down function of this test case"""
        self.exchange_helper.clear_exchange_environment(self.exchange_client)
        self.is_helper.delete_index_server()
        self.media_agent_machine_obj.remove_directory(self.restore_path, 0)
