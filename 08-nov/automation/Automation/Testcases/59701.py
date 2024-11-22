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
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerHelper
from cvpysdk.subclients.vssubclient import VirtualServerSubclient
from cvpysdk.constants import VSAObjects


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Deconfigure virtual client"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.commserve_client = None
        self.admin_console = None
        self.tcinputs = {
            "PseudoClientName":None,
            "vcenterhostname":None,
            "vcenterusername":None,
            "proxy": None,
            "storagepolicy":None,
            "SubclientName":None,
            "backupvm":None,
            "sqlusername":None,
            "sqlpassword":None,
            "starttime":None,
            "endtime":None
            }
    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            subclient = self.tcinputs.get('SubclientName')
            storagepolicy = self.tcinputs.get('storagepolicy')
            backupvm = self.tcinputs.get('backupvm')
            name = self.tcinputs.get('PseudoClientName')
            #Create new client
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            clientnames = [backupvm, name]
            self.client = auto_commcell.create_pesudo_client(clientnames, name, self.tcinputs['vcenterhostname'], self.tcinputs['vcenterusername'], self.tcinputs['vcenterpassword'], [self.tcinputs['proxy']])
            self.agent = self.client.agents.get('Virtual Server')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            #create new subclient
            self.backupset.subclients.add(subclient, storagepolicy)
            self.subclient = self.backupset.subclients.get(subclient)
            contentobj = VirtualServerSubclient(self.backupset, subclient, None)
            contentobj.content = [
                {
                    'type' : VSAObjects.VMName,
                    'name': '*' +backupvm+ '*',
                    'display_name': '*' +backupvm+ '*'}
                ]
            VirtualServerUtils.decorative_log('-Content added to subclient successfully-')
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            job = self.subclient.backup("FULL")
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}"
                                .format(job.delay_reason))
            VirtualServerUtils.decorative_log("Backup job {0} completed".format(job.job_id))
            #Release client
            VirtualServerUtils.decorative_log('release license on Virtual client')
            self.client.release_license()
            #update  job servdate and enddate
            sqlinstancename = self.commcell.commserv_hostname + r"\Commvault"
            sqlpasswd = self.tcinputs['sqlpassword']
            sqlusername = self.tcinputs['sqlusername']
            starttime = self.tcinputs['starttime']
            endtime = self.tcinputs['endtime']
            mssql_obj = MSSQL(sqlinstancename, sqlusername, sqlpasswd, "CommServ")
            auto_commcell.update_job_time(job.job_id, starttime, endtime, mssql_obj)
            #Change CS time
            VirtualServerUtils.decorative_log('Change the CS time')
            self.commserve_client = self.commcell.clients.get(self.commcell.commserv_hostname)
            csobj = Machine(self.commserve_client, self.commcell)
            csobj.add_days_to_system_time(10)
            #Run data aging
            auto_commcell.run_data_aging()
            # checking client status on DB
            auto_commcell.statuscheck(1, 2,status = 'deleted', clientname = clientnames)
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            #Resetting CS to current time
            csobj.add_days_to_system_time(-10)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED