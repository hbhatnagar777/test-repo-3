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
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerHelper
from cvpysdk.subclients.vssubclient import VirtualServerSubclient
from cvpysdk.constants import VSAObjects


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Delete backupset - Single VM multiple backupsets"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.backupset1 = None
        self.subclient1 = None
        self.vsa_obj = None
        self.admin_console = None
        self.tcinputs = {
            "PseudoClientName":None,
            "vcenterhostname":None,
            "vcenterusername":None,
            "proxy": None,
            "storagepolicy":None,
            "SubclientName":None,
            "vmpattern":None,
            "backupsetname1":None
            }
    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            subclient = self.tcinputs.get('SubclientName')
            storagepolicy = self.tcinputs.get('storagepolicy')
            vmpattern = self.tcinputs.get('vmpattern')
            name = self.tcinputs.get('PseudoClientName')
            backupsetname1 = self.tcinputs.get('backupsetname1')
            #Create new client
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            clientnames = [vmpattern, name]
            self.client = auto_commcell.create_pesudo_client(clientnames, name, self.tcinputs['vcenterhostname'], self.tcinputs['vcenterusername'], self.tcinputs['vcenterpassword'], [self.tcinputs['proxy']])
            self.agent = self.client.agents.get('Virtual Server')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            VirtualServerUtils.decorative_log("-Create new backupset-")
            self.backupset1 = self.agent.backupsets.add(backupsetname1)
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            #create new subclient under both backupsets
            self.backupset.subclients.add(subclient, storagepolicy)
            self.backupset1.subclients.add(subclient, storagepolicy)
            self.subclient = self.backupset.subclients.get(subclient)
            self.subclient1 = self.backupset1.subclients.get(subclient)
            #adding content
            try:
                backupsetlist = [self.backupset, self.backupset1]
                for eachbackupset in backupsetlist:
                    contentobj = VirtualServerSubclient(eachbackupset, subclient, None)
                    contentobj.content = [
                        {
                            'type' : VSAObjects.VMName,
                            'name': '*' +vmpattern+ '*',
                            'display_name': '*' +vmpattern+ '*'}
                        ]
                    VirtualServerUtils.decorative_log('-Content added to subclient successfully-')
            except Exception as exp:
                self.log.error('-Failed to add the content-')
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job = self.subclient.backup("FULL")
            time.sleep(120)
            job1 = self.subclient1.backup("FULL")
            joblist = [job, job1]
            for eachjob in joblist:
                if not eachjob.wait_for_completion():
                    raise Exception("Failed to run FULL backup with error: {0}"
                                    .format(eachjob.delay_reason))
            VirtualServerUtils.decorative_log("Backup job {0} completed".format(joblist))
            time.sleep(60)
            #Delete backupset
            VirtualServerUtils.decorative_log('Delete backupset')
            self.agent.backupsets.delete(backupsetname1)
            auto_commcell.statuscheck(2, 1, status = 'deleted', backupsetname =  [backupsetname1])
            time.sleep(360)
            # checking client status on DB
            auto_commcell.statuscheck(1, 2,status = 'configured',clientname = [vmpattern])
            #Validating job entries
            joblist =[job.job_id]
            auto_commcell.statuscheck(3, 3, status = 'deleted', jobid = joblist)
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
        