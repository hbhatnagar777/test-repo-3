# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function for this testcase

    run()                   --  Main function for this testcase

    tear_down()             --  tear down method for this testcase

    validate_lookup()       --  validates the result of client lookup

TestCase Inputs (Optional):
    {
        "clients": str     -    comma seperated client names to test on
                                default: will use file servers belonging to clients
        "lookup_tool": str -    name of the lookup tool
                                default: ClientLookup.exe
    }

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Client Lookup: Hostname and short name lookups between companies"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Client Lookup: Hostname and short name lookups between companies"
        self.tcinputs = {}
        self.clients = []
        self.tool_name = None
        self.command = None
        self.lookup_type_code = {
            "hostname": 1,
            "shortname": 2,
            "anyname": 3
        }

    def setup(self):
        """setup function for this testcase"""
        if "clients" in self.tcinputs:
            self.clients = [client.strip() for client in self.tcinputs['clients'].split(',')]
        else:
            self.clients = [
                client_name for client_name in self.commcell.clients.file_server_clients
                if "windows" in self.commcell.clients.get(client_name).os_info.lower()
                and self.commcell.clients.get(client_name).company_name.lower() != 'commcell'
            ]

        self.log.info(f"Testing on Clients {self.clients}")
        self.tool_name = self.tcinputs.get("lookup_tool", "ClientLookup.exe")
        self.command = f"{self.tool_name} %s %s %s"

    def run(self):
        """Main function for test case execution"""
        client_name = None
        try:
            for client_name in self.clients:
                client = self.commcell.clients.get(client_name)
                path = f"{client.install_directory}\\Base"
                client_machine = Machine(client)

                # TODO: proper check for Client lookup tool


                self.log.info(f"------ TESTING ON CLIENT  {client_name} ------")
                for lookup_client in self.clients:
                    looked_client = self.commcell.clients.get(lookup_client)
                    lookup_name = {
                        "hostname": looked_client.client_hostname,
                        "shortname": lookup_client,
                    }
                    lookup_instance = looked_client.instance
                    for lookup_type in ["hostname", "shortname"]:
                        self.log.info(
                            f"Attempting Lookup to {lookup_client} using {lookup_type} -> {lookup_name[lookup_type]}"
                        )

                        output = client_machine.execute_command_unc(
                            self.command % (
                                lookup_instance, self.lookup_type_code[lookup_type], lookup_name[lookup_type]),
                            path
                        )
                        cmd_result = output.formatted_output.split('\n')[-1]

                        self.validate_lookup(lookup_type, client, looked_client, cmd_result)

        except Exception as excp:
            self.log.error(f'Failed on client {client_name}')
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
            raise excp

    def validate_lookup(self, lookup_type, client, looked_client, cmd_result) -> None:
        """
        Verifies the result obtained from client lookup attempt

        Args:
            lookup_type (str)   -   type of lookup (hostname or shortname)
            client  (obj)       -   client sdk object of the source of lookup
            looked_client(obj)  -   client sdk object of the client looked up
            cmd_result  (str)   -   the result obtained after lookup
        
        Raises:
            AssertionError  -   if cmd_result is unexpected/incorrect
        
        Returns:
            None
        """
        try:
            if lookup_type == "hostname":
                if looked_client.company_name == client.company_name:
                    assert "success" in cmd_result
                    assert f"Client name[{looked_client.client_name}]" in cmd_result
                    assert f"id[{looked_client.client_id}]" in cmd_result
                else:
                    assert "error" in cmd_result
                    assert looked_client.client_name not in cmd_result
                    assert f"[{looked_client.client_id}]" not in cmd_result
            elif lookup_type == "shortname":
                assert "success" in cmd_result
                assert f"Client name[{looked_client.client_name}]" in cmd_result
                assert f"id[{looked_client.client_id}]" in cmd_result
            elif lookup_type == "anyname":
                pass
        except AssertionError as exc:
            self.log.error(f"Got response {cmd_result}")
            raise exc
        self.log.info(f"{lookup_type} lookup on {looked_client.client_name} passed")
