# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils import constants, logger
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for verifying the Retire Option for pseudo client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Retire Client - Perform Retire Operation on a pseudo client."

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        dummy_client = "DummyClient_"+self.id
        try:
            # Create a pseudo client and the object for the client
            _client = self.commcell.clients.create_pseudo_client(dummy_client)
            if not _client:
                raise Exception("Failed to create the pseudo client.")
            log.info("Pseudo Client %s is created successfully. Will perform Retire operation now.", dummy_client)

            # Perform the Retire Client Operation
            _client.retire()

            # Refreshing the clients associated with the commcell Object
            self.commcell.clients.refresh()

            # Validate that client is deleted
            if self.commcell.clients.has_client(_client.client_name):
                raise Exception("Client has NOT been deleted. Check logs to make sure Retire Operation succeeded.")

            log.info("Test case to retire a pseudo client completed successfully.")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
