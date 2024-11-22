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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

Inputs:
    PseudoClientname    --      Client Name of the pseudo client to be created.

"""
from cvpysdk.client import Client
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating retire client on child level which has backup's associated"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job = self.subclient.backup("FULL")
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}"
                                .format(job.delay_reason))
        #Retire VM
            try:
                client = Client(self.commcell, auto_subclient.vm_list[0], client_id=None)
                VirtualServerUtils.decorative_log('Retire VM')
                self.commcell.clients.refresh()
                client.retire()
                VirtualServerUtils.decorative_log('Retire VM operation ran successfully')
            except Exception as exp:
                self.log.error('---Failed to retire VM----')
        # checking client status on DB
            auto_commcell.statuscheck(
                1, 2,status = 'deconfigured',clientname = [auto_subclient.vm_list[0]])
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED