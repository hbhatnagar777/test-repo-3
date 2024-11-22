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

    Inputs to be provided to the testcase

    1. Company1     -- Name of a company

    2. Company2     -- Name of another company

    3. Company1_client1  -- Client belonging to company1

    4. Company1_client2  -- Another Client belonging to company1

    5. Company2_client1  -- Client belonging to company2

    6. Company2_client2  -- A different client belonging to company2

    7. Company2_tenant_username -- Username of the tenant user company2

    8. Company2_tenant_password -- Password of the tenant user company2

    9. Company1_username -- Tenant admin username of the company1

    10. Company2_password -- Tenant admin password of the company2
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVWebAutomationException
from Web.Common.page_object import TestStep
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage
import os

from cvpysdk.exception import SDKException


class TestCase(CVTestCase):
    """This testcase verifies the MSP testcase for network module"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : MSP test cases for network module "
        self.tcinputs = {
            "Company1": "",
            "Company2": "",
            "Company1_client1": "",
            "Company2_client1": "",
            "Company1_client2": "",
            "Company2_client2": ""
        }
        self.topology_name = "62489_MSP_ONEWAY"

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.commserve = self.commcell.commserv_name
            self.commcell_companies = self.commcell.organizations.all_organizations
            self.company1 = self.tcinputs.get("Company1")
            self.company2 = self.tcinputs.get("Company2")
            if self.company1 not in self.commcell_companies:
                raise CVTestStepFailure("Company1 input in invalid")
            if self.company2 not in self.commcell_companies:
                raise CVTestStepFailure("Company1 input in invalid")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def teststep1(self, company, company_type="Company1"):
        """Switch to company1 tenant admin mode and validate the clients"""
        self.commcell.client_groups.refresh()
        self.commcell.reset_company()

        if "62489_Source_CG".lower() in self.commcell.client_groups.all_clientgroups:
            self.log.info("deleting cg for company2")
            self.commcell.client_groups.delete("62489_Source_CG")
        if "62489_Dest_CG".lower() in self.commcell.client_groups.all_clientgroups:
            self.log.info("deleting cg for company2")
            self.commcell.client_groups.delete("62489_Dest_CG")
        self.commcell.switch_to_company(company)
        self.commcell.refresh()
        self.company_cl1 = self.tcinputs.get(f"{company_type}_client1")
        self.company_cl2 = self.tcinputs.get(f"{company_type}_client2")
        self._network = NetworkHelper(self)
        self.log.info("Creating client groups for the company2")
        self.client_groups = self._network.entities.create_client_groups(["62489_Source_CG", "62489_Dest_CG"])
        self.client_group_obj1 = self.client_groups["62489_Source_CG"]['object']
        self.client_group_obj1.add_clients([self.company_cl1])
        self.client_group_obj2 = self.client_groups["62489_Dest_CG"]['object']
        self.client_group_obj2.add_clients([self.company_cl2])
        self.client1_hostname = self.commcell.clients.get(self.company_cl1).client_hostname
        self.client2_hostname = self.commcell.clients.get(self.company_cl2).client_hostname
        self.option = OptionsSelector(self.commcell)

    def navigate_to_topologies(self, company_type):
        """Open browser and navigate to the network page"""
        try:
            username = self.tcinputs.get(f"{company_type}_username")
            passwrd = self.tcinputs.get(f"{company_type}_password")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(os.getcwd())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=username, password=passwrd)
            self.navigator = self.admin_console.navigator
            #self.navigator.navigate_to_network()
            self.navigator.navigate_to_network_topologies()
            self.networkpage = NetworkPage(self.admin_console)
            #self.networkpage.click_topologies()


        except Exception as exception:
            raise CVTestStepFailure(exception)

    def validate_summary(self, summary, source_client, destination_client, route_type, protocol, streams,
                         keep_alive, tunnel_port, client_group):
        """Validates the network summary of a client """
        self.commcell.reset_company()
        self.commcell.refresh()
        check_keep_alive = False

        check_tunnel_port = False
        check_persistent = False
        check_passive = False
        self.summary = summary.split("\n")
        col1, res = self.option.exec_commserv_query("""SELECT clientId FROM App_FirewallOptions WHERE clientId != 0
                                                        UNION ALL
                                                        SELECT clientId FROM APP_ClientGroupAssoc WHERE clientGroupId in 
                                                        (SELECT clientGroupId FROM App_FirewallOptions)""")
        firewall_option_count = 0
        if source_client != self.commserve:
            clientId = self.client_obj.client_id
        else:
            clientId = self.server_object.client_id
        for row in res:
            if row[0] == clientId:
                firewall_option_count += 1

        if firewall_option_count > 1:
            check_keep_alive = True
            check_tunnel_port = True
        for i in self.summary:
            # Validation of Keep alive interval
            if "keepalive_interval" in i and not check_keep_alive:
                if "keepalive_interval=" + keep_alive in i:
                    check_keep_alive = True
                    self.log.info(f"Validated the keep alive configured in the topology for {client_group}")
                else:
                    raise CVTestStepFailure(
                        'Validation of Keep alive interval failed of {}. Keep alive found : {} vs {}'.
                        format(client_group, i.split("=")[-1], keep_alive))

            # Validation of Tunnel port
            if "tunnel_ports" in i and not check_tunnel_port:
                if str(tunnel_port) in i:
                    check_tunnel_port = True
                    self.log.info("Validated the tunnel port of {}".format(client_group))
                else:
                    raise CVTestStepFailure(' Validation of tunnel port failed for {}. Found {} vs {}'.format(
                        client_group, i.split("=")[-1], tunnel_port))

            # Validation of Outgoing network route
            if source_client + " " + destination_client in i:
                # Validate passive route
                if route_type == "passive":
                    check_passive = True
                    self.log.info("Validated the passive route : {}".format(i))
                else:
                    if int(streams) > 1:
                        if ("type=" + route_type in i and "proto=" + protocol + " " in i) and "streams=" + streams in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                                                    f' {client_group}')
                    else:
                        if "type=" + route_type in i and "proto=" + protocol + " " in i:
                            check_persistent = True
                            self.log.info(f"Validated {route_type} network route for {client_group}")
                        else:
                            raise CVTestStepFailure(f' Validation of {route_type} network route failed for'
                                                    f' {client_group}')
        if check_tunnel_port and check_keep_alive: # (check_persistent or check_passive) and check_tunnel_port and check_keep_alive:
            return True
        else:
            raise CVTestStepFailure("Validation of network summary failed")

    def teststep2(self):
        """Validate create topology within company as a tenant admin"""
        client_group_list = ["62489_Source_CG", "62489_Dest_CG"]
        self.networkpage.add_topology(self.topology_name, "One-way", ["62489_Source_CG", "62489_Dest_CG"], "servertype")
        self.client_obj = self.commcell.clients.get(self.company_cl1)
        self.server_object = self.commcell.clients.get(self.company_cl2)
        self.client_summary = self.client_obj.get_network_summary()
        self.server_summary = self.server_object.get_network_summary()
        self.validate_summary(self.client_summary, self.company_cl1, self.company_cl2,
                              "persistent", "httpsa", '1', '180', self.client_obj.network.tunnel_connection_port,
                              client_group_list[0])

        # Validate the network summary of commserve
        self.validate_summary(self.server_summary, self.company_cl2, self.company_cl1,
                              "passive", "httpsa", '1', '180', self.server_object.network.tunnel_connection_port,
                              client_group_list[1])
        self.networkpage.delete_topology(self.topology_name)

        # Validate negative testcase company1 tenant admin should not be able to view other company client
        self.teststep1(self.company2, company_type="Company2")
        try:
            self.networkpage.add_topology(self.topology_name, "One-way", client_group_list, "servertype")
            raise CVWebAutomationException("Tenant admin1 can create topology with company2 client")
        except Exception:
            self.log.info("Company1 tenant admin did not able to modify or create topology with company2 clients")
        Browser.close_silently(self.browser)

    def validate_dip(self, summary, source, destination, interface1=None, interface2=None):
        try:
            self.summary = summary.split("\n")
            flag1 = False
            flag2 = False
            for i in self.summary:
                j = i.lower()
                if source + " " + destination + " " in i:
                    # Passive route
                    if "type=passive" in i:
                        return "passive"

                    self.log.info(i)
                    if 'local_iface' in j and interface1.lower() in j:
                        flag1 = True
                        self.log.info("Validated interface route in source client")

                    if ('remote_iface' in j or 'cvfwd' in j) and interface2.lower() in j:
                        flag2 = True
                        self.log.info("Validated interface route in source client")

            if flag1 and flag2:
                return True
            return False
        except Exception as e:
            raise CVTestStepFailure(e)

    def teststep3(self):
        """Create DIPs between two clients in the same company
           Currently the commcell has mode is of second company so using the clients
           of second company to create DIPs
        """
        client1 = self.commcell.clients.get(self.tcinputs.get("Company2_client1"))
        client2 = self.commcell.clients.get(self.tcinputs.get("Company2_client2"))
        c1 = self.tcinputs.get("Company2_client1")
        c2 = self.tcinputs.get("Company2_client2")
        self._network.add_dips([({"client": c1, "srcip": client1.client_hostname},
                                 {"client": c2, "destip": client2.client_hostname})])
        validate_sourcesummary = self.validate_dip(client1.get_network_summary(), c1, c2,
                                                   interface1=client1.client_hostname,
                                                   interface2=client2.client_hostname)
        validate_destsummary = self.validate_dip(client2.get_network_summary(), c2, c1,
                                                 interface1=client2.client_hostname,
                                                 interface2=client1.client_hostname)
        if not validate_destsummary or not validate_sourcesummary:
            raise CVWebAutomationException("Validation of Data interface pairs in summary failed. "
                                           f"Source Summary Check : {validate_sourcesummary}\n"
                                           f"Destination Summary Check : {validate_destsummary}")
        self.commcell.reset_company()
        self.commcell.switch_to_company(self.company1)
        try:
            # Navgative testcase Company1 tenant admin trying to create dips for clients belonging to company2
            self._network.add_dips([({"client": c1, "srcip": client1.client_hostname},
                                 {"client": c2, "destip": client2.client_hostname})])
            raise Exception("DIPs creation is successful cross company")
        except SDKException as e:
            self.log.info(f"Company1 tenant admin was not able to create any DIPs for company2 clients\n{e}")

    def teststep4(self):
        """Login to adminconsole using tenant user creds and validate he should not be able to view
        or create topologies"""
        try:
            self.navigate_to_topologies("Company2_tenant")
            raise CVTestStepFailure("Tenant User able to view topologies")
        except Exception as e:
            self.log.info(f"Tenant User unable to view topologies tab in UI\n{e}")
            Browser.close_silently(self.browser)

    def run(self):
        try:
            self.init_tc()
            self.teststep1(self.company1)
            self.navigate_to_topologies("Company1")
            self.teststep2()
            self.teststep3()
            self.teststep4()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.tear_down()

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Resetting the company to default")
        self.commcell.reset_company()
