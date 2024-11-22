from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from Web.AdminConsole.AdminConsolePages.NetworkPage import NetworkPage
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable,  Rfilter
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, CVTestStepFailure


"""
Command Center- Network - Validation of Sorting, Searching, Views, filters in Topology Page

Inputs to the testcase:

Client1, Client2, Client3, Client4 - Any 4 clients in the commcell
"""


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center- Network - Validation of Sorting, Searching, Views, filters in Topology Page"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "Client1": None,
            "Client2": None,
            "Client3": None,
            "Client4": None
        }
        self.all_clients = None
        self.driver = None
        self._client_group_name1 = "CG_60340_1"
        self._client_group_name2 = "CG_60340_2"
        self._client_group_name3 = "CG_60340_3"
        self._client_group_name4 = "CG_60340_4"
        self._client_group_name5 = "CG_60340_5"

        self.client_group_obj1 = None
        self.client_group_obj2 = None
        self.client_group_obj3 = None
        self.client_group_obj4 = None
        self.client_group_obj5 = None
        self._network = None
        self.clients_grps_obj = None
        self.client_groups = None
        self.all_cgs = None
        self.client_grp_obj_list = None
        self.networkpage = None
        self.rtable = None
        self.all_views = None
        self.topology_columnname = "Topology name"
        self.oneway_toplogy_lptp = "ONE_WAY_TOPOLOGY_LAPTOP"
        self.two_way_topology_server = "TWO_WAY_TOPOLOGY_SERVER"
        self.network_topology_server = "NETWORKG_TOPOLOGY_SERVER"
        self.topology_names = ["ONE_WAY_TOPOLOGY_SERVER", self.oneway_toplogy_lptp, self.two_way_topology_server,
                               self.network_topology_server, "CASCADING_TOPOLOGY_SERVER"]
        self.clienttype = "Client type"
        self.network_topology_laptop = "NETWORKG_TOPOLOGY_LAPTOP"
        self.view1 = "62248_View1"
        self.view2 = "62248_View2"
        self.server = "Server"

    @TestStep()
    def configure_topologies(self):
        """Configure all the topologies"""
        self._network = NetworkHelper(self)
        self.clients_grps_obj = self.commcell.client_groups
        self.all_clients = [self.tcinputs["Client1"], self.tcinputs["Client2"], self.tcinputs["Client3"],
                            self.tcinputs["Client4"], self.commcell.commserv_name]
        self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                          self._client_group_name2,
                                                                          self._client_group_name3,
                                                                          self._client_group_name4,
                                                                          self._client_group_name5])
        self.all_cgs = [self._client_group_name1,
                        self._client_group_name2,
                        self._client_group_name3,
                        self._client_group_name4,
                        self._client_group_name5]
        self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
        self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
        self.client_group_obj3 = self.client_groups[self._client_group_name3]['object']
        self.client_group_obj4 = self.client_groups[self._client_group_name4]['object']
        self.client_group_obj5 = self.client_groups[self._client_group_name5]['object']
        self.client_grp_obj_list = [self.client_group_obj1, self.client_group_obj2, self.client_group_obj3,
                                    self.client_group_obj4, self.client_group_obj5]
        self.client_grp_obj_list[0].add_clients([self.all_clients[0]])
        self.client_grp_obj_list[1].add_clients([self.all_clients[1]])
        self.client_grp_obj_list[2].add_clients([self.all_clients[2]])
        self.client_grp_obj_list[3].add_clients([self.all_clients[3]])
        self.client_grp_obj_list[4].add_clients([self.all_clients[4]])
        # One way topology from CG1 ---> CG2 (SERVERS)
        self._network.one_way_topology(self.all_cgs[0], self.all_cgs[1], self.topology_names[0])
        self._network.one_way_topology(self.all_cgs[1], self.all_cgs[2], self.topology_names[1],
                                       display_type=1)
        self._network.two_way_topology(self.all_cgs[2], self.all_cgs[3], self.topology_names[2])
        self._network.proxy_topology(self.all_cgs[1], self.all_cgs[3], self.all_cgs[4], self.topology_names[3],
                                     wildcard=True)

    @TestStep()
    def open_nw_toplogies(self):
        """Navigate to topologies page"""
        self.configure_topologies()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_network()
        self.networkpage = NetworkPage(self.admin_console)
        self.networkpage.click_topologies()
        self.rtable = Rtable(self.admin_console)
        self.all_views = self.rtable.get_all_tabs()

    @TestStep()
    def validate_created_topologies(self):
        """Search for the created topologies in the network page"""
        for topology in self.topology_names[:4]:
            self.rtable.search_for(topology)
            rows = self.rtable.get_table_data()[self.topology_columnname]
            if rows[0] != topology or rows[0] == "One-way":
                raise CVTestStepFailure("Created topology {0} is not present in the React table".format(topology))

    @TestStep()
    def validate_sorting(self):
        """Sort the rows in the table based on name ascending, verify and vice versa"""
        self.rtable.clear_search()
        self.rtable.apply_sort_over_column(column_name=self.topology_columnname)
        rows = self.rtable.get_table_data()[self.topology_columnname]
        rows = [i for i in rows if i in self.topology_names]
        if not rows == sorted(self.topology_names[:4]):
            self.log.info("Rows in table : {0}".format(rows))
            raise CVTestStepFailure("Topologies aren't sorted properly")

        self.rtable.apply_sort_over_column(column_name=self.topology_columnname, ascending=False)
        rows = self.rtable.get_table_data()[self.topology_columnname]
        rows = [i for i in rows if i in self.topology_names]
        if not rows == sorted(self.topology_names[:4], reverse=True):
            self.log.info("Rows in table : {0}".format(rows))
            raise CVTestStepFailure("Topologies aren't sorted properly")

    @TestStep()
    def validate_view_servertype_tplgies(self):
        """Create view for Client type as Servers and validate the rows"""
        self.rtable.create_view(self.view1, {self.clienttype: self.server})
        rows = self.rtable.get_table_data()
        topologies = rows[self.topology_columnname]
        topologies = [i for i in topologies if i in self.topology_names]
        expected_data = sorted(self.topology_names[:4], reverse=True)
        expected_data.remove(self.oneway_toplogy_lptp)
        if not topologies == expected_data:
            self.log.info("Rows in table : {0}".format(topologies))
            self.log.info("Rows expected : {0}".format(expected_data))
            raise CVTestStepFailure("View- Client type : server does not contain the required rows")
        self.rtable.select_view()

    @TestStep()
    def validate_view_cascading_tplgies(self):
        """Create a view -> Cascading topology (Filter By: Client type, Condition - Contains, Value : Cascading
        gateways """
        self.rtable.create_view(self.view2, {"Topology type": "Cascading gateways"})
        rows = self.rtable.get_table_data()[self.topology_columnname]
        if (self.oneway_toplogy_lptp in rows or self.two_way_topology_server in rows or
                self.network_topology_server in rows):
            self.log.info("Table data : {0}".format(rows))
            raise CVTestStepFailure("Table does not contain proper data")

    @TestStep()
    def validate_filter_laptop(self):
        """Navigate to All view and apply filter Client type -> Laptops"""
        self.rtable.select_view()
        self.rtable.apply_filter_over_column(self.clienttype, self.server, criteria=Rfilter.not_contains)
        rows = self.rtable.get_table_data()[self.topology_columnname]
        if self.oneway_toplogy_lptp not in rows:
            self.log.info("Table data {0}".format(rows))
            raise CVTestStepFailure("Invalid rows in the filter laptops")
    @TestStep()
    def validate_filter_tplgy_name(self):
        """Edit topology and reapply filter & verify, Apply another filter Name of topology contains TWO_WAY """
        self.rtable.clear_column_filter(self.clienttype, "Client type does not contain Server")
        self.networkpage.edit_topology(self.network_topology_server, ModifyClientType="clienttype",
                                       ModifyTopologyName=self.network_topology_laptop)
        self.rtable.select_view()
        self.rtable.apply_filter_over_column(self.clienttype, "Laptop", criteria=Rfilter.contains)
        rows = self.rtable.get_table_data()[self.topology_columnname]
        if self.network_topology_laptop not in rows or self.oneway_toplogy_lptp not in rows:
            self.log.info("Table data {0}".format(rows))
            raise CVTestStepFailure("Invalid entries for laptop type rows ")
        self.rtable.clear_column_filter(self.clienttype, "Laptop")
        self.rtable.apply_filter_over_column(self.topology_columnname, "TWO_WAY", Rfilter.contains)
        rows = self.rtable.get_table_data()[self.topology_columnname]
        if self.two_way_topology_server not in rows:
            self.log.info("Table data {0}".format(rows))
            raise CVTestStepFailure("Invalid entries in the table")
        self.rtable.clear_column_filter(self.topology_columnname, "TWO_WAY")

    @TestStep()
    def validate_reload_table(self):
        """Clear the filters and delete the rows after deleting via API and hard refresh"""
        self.rtable.clear_column_filter(self.topology_columnname, "Topology name contains TWO_WAY")
        self._network.topologies.refresh()
        self._network.delete_topology(self.network_topology_laptop)
        self.rtable.reload_data()
        rows = self.rtable.get_table_data()[self.topology_columnname]
        if self.network_topology_laptop in rows:
            raise CVTestStepFailure("Topology name present in table even after deletion")

    @TestStep()
    def delete_views(self):
        """Delete the created views"""
        views = self.rtable.list_views()
        if self.view1 in views:
            self.rtable.delete_view(self.view1)
        if self.view2 in views:
            self.rtable.delete_view(self.view2)

    def run(self):
        try:
            self.open_nw_toplogies()
            self.delete_views()
            self.validate_created_topologies()
            self.validate_sorting()
            self.validate_view_servertype_tplgies()
            self.validate_view_cascading_tplgies()
            self.validate_filter_laptop()
            self.validate_filter_tplgy_name()
            self.validate_reload_table()
            self.delete_views()
            self._network.entities.cleanup()

        except Exception as e:
            raise CVTestStepFailure(e)
        finally:
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
