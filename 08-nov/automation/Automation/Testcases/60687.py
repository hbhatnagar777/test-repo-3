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


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating child vm backupset after deleting another child vm backupset"
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
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            agentlist = []
            for eachclient in auto_subclient.vm_list:
                client = Client(self.commcell, eachclient, client_id=None)
                agent = client.agents.get('Virtual Server')
                agentlist.append(agent)
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job = self.subclient.backup("INCREMENTAL")
            if not job.wait_for_completion():
                raise Exception("Failed to run INCREMENTAL backup with error: {0}"
                                .format(job.delay_reason))
            #Delete backupset for one child VM
            agentlist[0].backupsets.delete(self.tcinputs.get('BackupsetName'))
            self.log.info('Deleted backupset successfully for vm: %s', auto_subclient.vm_list[0])
            # checking backupset status
            if agentlist[1].backupsets.has_backupset:
                VirtualServerUtils.decorative_log(
                    'backupset for other vm didnt get deleted which is expected')
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED