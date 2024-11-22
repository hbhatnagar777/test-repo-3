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
from cvpysdk.constants import VSAObjects
from cvpysdk.client import Client, Clients
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerHelper
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Backupset status check with Single VM multiple backupsets - VM removed from Subclient"
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
            "backupvm":None,
            "backupvm1":None
            }
    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            subclient= OptionsSelector.get_custom_str('SubclientName')
            storagepolicy = self.tcinputs.get('storagepolicy')
            backupvm = self.tcinputs.get('backupvm')
            backupvm1 = self.tcinputs.get('backupvm1')
            name = self.tcinputs.get('PseudoClientName')
            backupsetname1 = OptionsSelector.get_custom_str('backupsetname1')
            #Create new client with mutiple backupsets
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            clientnames = [backupvm, name]
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
                subclientlist = [self.subclient, self.subclient1]
                for eachsubclient in subclientlist:
                    eachsubclient.content = [
                        {
                            'type' : VSAObjects.VMName,
                             'name': '*' +backupvm+ '*',
                             'display_name': '*' +backupvm+ '*'}
                        ]
                    VirtualServerUtils.decorative_log('-Content added to subclient successfully-')
            except Exception as exp:
                self.log.error('-Failed to add the content to subclient-')
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
            #Filter the VM
            VirtualServerUtils.decorative_log("Filter the VM")
            auto_commcell.add_filter(self.backupset1, subclient, None, backupvm)
            #updating content
            self.subclient1.content = [
                {
                    'type' : VSAObjects.VMName,
                    'name': '*' +backupvm1+ '*',
                    'display_name': '*' +backupvm1+ '*'}
                ]
            VirtualServerUtils.decorative_log('-Content updated to subclient successfully-')
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job1 = self.subclient1.backup("FULL")
            if not job1.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}"
                                .format(job1.delay_reason))
            VirtualServerUtils.decorative_log("Backup job {0} completed".format(job1.job_id))
            #Change CS time
            VirtualServerUtils.decorative_log('Change CS time')
            self.commserve_client = self.commcell.clients.get(self.commcell.commserv_hostname)
            csobj = Machine(self.commserve_client, self.commcell)
            csobj.add_days_to_system_time(3)
            time.sleep(30)
            #Run data aging
            VirtualServerUtils.decorative_log('run data aging job')
            auto_commcell.run_data_aging()
            #Restart Evmgrs service
            VirtualServerUtils.decorative_log('Restart Evmgrs service')
            self.commcell.commserv_client.restart_service('GxEvMgrS(Instance001)')
            time.sleep(120)
            #Check backupset status
            query = "select id from APP_BackupSetName where Name = '"+backupsetname1+"' INTERSECT \
                    select ChildBackupSetId from APP_VMBackupSet where VMClientId =(select id from APP_Client where name = '"+backupvm+"')"
            self.csdb.execute(query)
            output = self.csdb.fetch_all_rows()
            if output != [['']]:
                VirtualServerUtils.decorative_log('Backupset not deleted which is expected')
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            #Resetting  back CS time to current time
            csobj.add_days_to_system_time(-3)
            time.sleep(30)

        