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
from VirtualServer.VSAUtils import VirtualServerUtils



class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""
    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware retire validation for Hypervisor with no backups"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            try:
                VirtualServerUtils.decorative_log('---Creating new VMware Hypervisor-- ')
                client = self.commcell._clients.add_vmware_client(self.tcinputs.get('PseudoClientName'),
                                                                  self.tcinputs['vcenterhostname'],
                                                                  self.tcinputs['vcenterusername'],
                                                                  self.tcinputs['vcenterpassword'],
                                                                  [self.tcinputs['proxy']])
            except Exception as exp:
                raise Exception
                self.log.error('---Failed to create new vmware Hypervisor----')
            VirtualServerUtils.decorative_log('Hypervisor created successfully')

            # Checking DB for client entry
            try:
                VirtualServerUtils.decorative_log(
                    'checking DB if Hypervisor entry got created ')
                name = self.tcinputs.get('PseudoClientName')
                query = "SELECT ID from APP_CLIENT where Name = '"+name+"'"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
                VirtualServerUtils.decorative_log('Newly created Hypervisor got DB entry')
                if output == [['']]:
                    VirtualServerUtils.decorative_log('Hypervisor id is not null')
                else:
                    self.log.error('Hypervisor entry found in DB---')
            except Exception as exp:
                raise Exception
                self.log.error('---Failed to retire Hypervisor----')
            #Validating if Hypervisor got deleted from GUI
            try:
                VirtualServerUtils.decorative_log(
                    'Validating if Hypervisor got deleted from GUI')
                self.commcell.clients.refresh()
                if self.commcell.clients.has_client(client.client_name):
                    VirtualServerUtils.decorative_log(
                        'Hypervisor has been deleted ON GUI which is expected since it has no backups associated to it')
            except Exception as exp:
                self.log.error(
                    '---Hypervisor not been deleted on GUI which is not expected----')
                raise Exception
            #Retire client
            try:
                VirtualServerUtils.decorative_log('Perform the Retire Operation')
                self.commcell.clients.refresh()
                client.retire()
                VirtualServerUtils.decorative_log('--Retire operation ran successfully')
            except Exception as exp:
                self.log.error('---Failed to retire Hypervisor----')

            #Validating if Hypervisor got deleted from GUI
            try:
                VirtualServerUtils.decorative_log(
                    'Validating if Hypervisor got deleted from GUI')
                self.commcell.clients.refresh()
                if self.commcell.clients.has_client(client.client_name):
                    raise Exception("Hypervisor has NOT been deleted")
            except Exception as exp:
                self.log.error('---Failed to delete Hypervisor after retire operation from GUI----')

            VirtualServerUtils.decorative_log(
                'Newly created Hypervisor got deleted successfully from GUI')

            #Validating DB
            try:
                VirtualServerUtils.decorative_log(
                    'checking DB if Hypervisor entry got deleted')
                name = self.tcinputs.get('PseudoClientName')
                query = "SELECT ID from APP_CLIENT where Name = '"+name+"'"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
                raise Exception
            except Exception as exp:
                VirtualServerUtils.decorative_log('---no entries found in DB for Hypervisor which is expected----')
            if output == [['']]:
                VirtualServerUtils.decorative_log('---Hypervisor details deleted from the DB--')
            else:
                self.log.error('Hypervisor details not deleted from DB as expected---')
                raise Exception

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED


        