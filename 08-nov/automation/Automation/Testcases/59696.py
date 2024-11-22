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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerHelper
from cvpysdk.client import Client
from cvpysdk.subclients.vssubclient import VirtualServerSubclient
from cvpysdk.constants import VSAObjects

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vm part of two pseudo clients and de-configure one pseudo  client"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client1 = None
        self.agent1 = None
        self.subclient1 = None
        self.helper = None
        self.vsa_obj = None
        self.backupset1 = None
        self.admin_console = None
        self.tcinputs = {
            "PseudoClientName":None,
            "PseudoClientName1":None,
            "vcenterhostname":None,
            "vcenterusername":None,
            "proxy": None,
            "storagepolicy":None,
            "SubclientName":None,
            "backupvm":None
            }
    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            subclient = self.tcinputs.get('SubclientName')
            storagepolicy = self.tcinputs.get('storagepolicy')
            backupvm = self.tcinputs.get('backupvm')
            name = self.tcinputs.get('PseudoClientName')
            name1 = self.tcinputs.get('PseudoClientName1')
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            clientnames = [backupvm, name]
            # Create pesudo client
            self.client = auto_commcell.create_pesudo_client(clientnames, name, self.tcinputs['vcenterhostname'], self.tcinputs['vcenterusername'], self.tcinputs['vcenterpassword'], [self.tcinputs['proxy']])
            self.agent = self.client.agents.get('Virtual Server')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            #create new subclient
            self.backupset.create_subclient(subclient, storagepolicy, description='New')
            self.subclient = self.backupset.subclients.get(subclient)
            # Create second pesudo client
            clientname = [name1]
            self.client1 = auto_commcell.create_pesudo_client(clientname, name1, self.tcinputs['vcenterhostname'], self.tcinputs['vcenterusername'], self.tcinputs['vcenterpassword'], [self.tcinputs['proxy']])
            self.agent1 = self.client1.agents.get('Virtual Server')
            self.backupset1 = self.agent1.backupsets.get('defaultBackupSet')
            #create new subclient
            self.backupset.subclients.add(subclient, storagepolicy)
            self.subclient1 = self.backupset1.subclients.get(subclient)
            #adding content under both clients
            try:
                backupsetlist = [self.backupset, self.backupset1]
                for eachbackupset in backupsetlist:
                    contentobj = VirtualServerSubclient(eachbackupset, subclient, None)
                    contentobj.content = [
                        {
                            'type' : VSAObjects.VMName,
                            'name': '*' +backupvm+ '*',
                            'display_name': '*' +backupvm+ '*'}
                        ]
                VirtualServerUtils.decorative_log('-Content added to subclients successfully-')
            except Exception as exp:
                self.log.error('-Failed to add content-')
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job = self.subclient.backup("FULL")
            time.sleep(180)
            job1 = self.subclient1.backup("FULL")
            joblist = [job, job1]
            for eachjob in joblist:
                if not eachjob.wait_for_completion():
                    raise Exception("Failed to run FULL backup with error: {0}"
                                    .format(eachjob.delay_reason))
            VirtualServerUtils.decorative_log("Backup job {0} completed".format(joblist))
            #Releasing license
            VirtualServerUtils.decorative_log('Releasing license')
            self.client.release_license()
            #Validating VM's status on DB
            auto_commcell.statuscheck(1, 2,status = 'configured',clientname = [backupvm])
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
        