# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate Basic operation window Data Management features for clients in different timezones.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from Server.OperationWindow.ophelper import OpHelper
from Server.OperationWindow.opvalidate import OpValidate
from Server.serverhelper import ServerTestCases
from Web.Common.page_object import TestStep
from datetime import datetime, timedelta


class TestCase(CVTestCase):
    """Class for executing Basic operation window Data Management features for clients in different timezones"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Validation] : Basic operation window Data Management features for clients in different timezones"
        self.applicable_os = self.os_list.NA
        self.product = self.products_list.FILESYSTEM
        self.show_to_user = False
        self.op_window, self.entities, self.entity_props = None, None, None
        self.client2 = None
        self.client1 = None
        self.clientgroup = None
        self.clientgroupname = None
        self.subclient1 = None
        self.subclient2 = None
        self.tcinputs = {
            'Client1Name': None,
            'Client2Name': None
        }

    def create_subclient(self, clientname, storagepolicy):
        """
        Create subclient with given client and storagepolicy.
        Returns subclient properties dict.
        """
        subclient_pattern = {
            'subclient':
                {
                    'client': clientname,
                    'storagepolicy': storagepolicy,
                    'backupset': 'defaultBackupSet',
                    'agent': "File system",
                    'instance': "defaultinstancename",
                }
        }
        try:
            return self.entities.create(subclient_pattern)['subclient']
        except Exception as e:
            self.log.info(e)

    @test_step
    def verify_commserv_level_operation_window(self):
        """Creates operation window at commserv level and verify the teststep 1"""
        try:
            operations_list = ["FULL_DATA_MANAGEMENT", "NON_FULL_DATA_MANAGEMENT"]
            self.log.info("Validating commcell level operation window for the features:%s", operations_list)
            self.client = self.commcell.commserv_client
            self.op_window = OpHelper(self, self.commcell)
            machine = Machine(self.commcell.commserv_name, self.commcell)
            op_rule = self.op_window.weekly_rule(operations_list, machine)
            self.log.info("Initialised the operation window successfully")
            self.log.info(f"Verifying immediate full backup job for "
                          f"{self.subclient1.subclient_name} and {self.subclient2.subclient_name}")
            op_val = OpValidate(self, op_rule)
            op_val.validate_clients_in_different_timezones(True, True)
        finally:
            self.op_window.delete(name=self.name)

    def get_local_time(self, clientname):
        """returns the current time in the client machine as a datetime object"""
        client_machine = Machine(clientname, self.commcell)
        command = "date +%d-%m-%Y\ %H:%M:%S" if client_machine.os_info == "UNIX" \
            else '$a = Get-Date;$a.ToString("dd-MM-yyyy HH:mm:ss")'
        time_str = client_machine.execute_command(command).formatted_output
        local_time = datetime.strptime(time_str, "%d-%m-%Y %H:%M:%S")
        return local_time

    @test_step
    def verify_client_group_level_operation_window(self):
        """Creates operation window at clientgroup level and verify the teststep 3"""
        operations_list = ["FULL_DATA_MANAGEMENT", "NON_FULL_DATA_MANAGEMENT"]
        self.log.info("Validating client group level operation window for the features:%s", operations_list)
        """
        To verify this, we first set a client group level window at local time of any one of the client, say client1.
        Job should be interrupted by BW in client 1 and should run fine in client2.
        The above process should be replicated at client 2 and job should be interrupted in client 2
        """
        self.op_window = OpHelper(self, self.clientgroup)
        clients = [self.tcinputs['Client1Name'], self.tcinputs['Client2Name']]
        for client in range(2):
            try:
                self.log.info(f"setting client level operation window at {clients[client]} timezone")
                start_time = self.get_local_time(clients[client])
                end_time = start_time + timedelta(hours=1)
                op_rule = self.op_window.testcase_rule(
                    operations=operations_list,
                    start_time=start_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    start_date=start_time.strftime("%d/%m/%Y"),
                    end_date=end_time.strftime("%d/%m/%Y")
                )
                op_val = OpValidate(self, op_rule)
                op_val.validate_clients_in_different_timezones((client+1) % 2, client % 2)
            finally:
                self.op_window.delete(name=self.name)

    def setup(self):
        self.server = ServerTestCases(self)
        self.client1 = self.commcell.clients.get(self.tcinputs["Client1Name"])
        self.client2 = self.commcell.clients.get(self.tcinputs["Client2Name"])
        if self.client1.timezone == self.client2.timezone:
            raise Exception("Both the clients given are in same timezone.Please input clients with different timezones")
        self.log.info(f"Client 1 Timezone : {self.client1.timezone}\n Client 2 Timezone : {self.client2.timezone}")
        self.clientgroupname = "ClientGroup" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        self.log.info(f"Created client group {self.clientgroupname} with clients {self.client1},{self.client2}")
        self.clientgroup = self.commcell.client_groups.add(self.clientgroupname,
                                                           [self.tcinputs["Client1Name"], self.tcinputs["Client2Name"]])

        self.entities = CVEntities(self)
        self.entity_props = self.entities.create(["disklibrary", "storagepolicy"])
        self.subclient1 = self.create_subclient(self.tcinputs["Client1Name"],
                                                self.entity_props["storagepolicy"]["name"])['object']
        self.subclient2 = self.create_subclient(self.tcinputs["Client2Name"],
                                                self.entity_props["storagepolicy"]["name"])['object']

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.verify_commserv_level_operation_window()
            self.verify_client_group_level_operation_window()
        except Exception as e:
            self.log.error(e)
            self.server.fail(e)

    def tear_down(self):
        self.commcell.client_groups.delete(self.clientgroupname)
        self.op_window.delete()
        self.entities.cleanup()
