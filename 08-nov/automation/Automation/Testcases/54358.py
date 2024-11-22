# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate Software Version report"""

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils


class TestCase(CVTestCase):
    """
    Verify Version and Service pack report
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Software Version report validation"
        self.tcinputs = {
            "ClientName": None}
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.navigator = None
        self.utils = CustomReportUtils(self)
        self.viewer = None
        self.table = None
        self.tile_outcome = None
        self.laptop_table = None
        self.laptop_viewer = None
        self.version_sp_tile = None
        self.tile_count = {}
        self.client_type = ["Server", "MediaAgent", "Laptop", "Infrastructure Client"]

    def init_tc(self):
        """
        initialize testcase objects
        """
        try:
            commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=commcell_password)
            self.navigator = self.admin_console.navigator
            dashboard = RDashboard(self.admin_console)
            dashboard.access_details_page('Health')

            self.version_sp_tile = GenericTile(self.admin_console, 'Software Version')
            self.tile_outcome = self.version_sp_tile.get_outcome()

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    @test_step
    def verify_tile_status(self):
        """
        verify the version and service pack tile status in health report
        """
        version_sp_status = self.version_sp_tile.get_health_status()
        self.version_sp_tile.access_view_details()
        self.table = viewer.DataTable("Servers")
        self.viewer = viewer.CustomReportViewer(self.admin_console)
        self.viewer.associate_component(self.table)
        service_pack = int(self.client.service_pack)
        difference = int(self.get_major_sp()) - service_pack
        if difference <= 4:
            raise CVTestCaseInitFailure(
                f"Client [{self.client}] is not older by 4 major SP "
                f"provide such a client in input"
            )
        client_status = self.get_client_status()
        if client_status != version_sp_status:
            raise CVTestStepFailure(f"The expected tile status is [{client_status}] "
                                    f"but received [{version_sp_status}]")

    @test_step
    def verify_commserver_status(self):
        """
        verify the commserv status from the report
        """
        html_comp = viewer.HtmlComponent("")
        self.viewer.associate_component(html_comp)
        status = html_comp.get_html_component_contents()
        cs_status = status.split('Status: ')[1]
        expected_status = 'Good'
        if expected_status not in cs_status:
            raise CVTestStepFailure(f"The expected commcell [{self.commcell.commserv_name}] "
                                    f"status is [Good] but received [{cs_status}]")

    @test_step
    def validate_critical_status(self):
        """
        validate the critical client status`
        """
        expected_status = 'Critical'
        self.table.set_filter("Name", self.tcinputs["ClientName"])
        client_status = self.table.get_column_data('Update Status')
        if expected_status != client_status[0]:
            raise CVTestStepFailure(
                f"The expected client status is [{expected_status}] "
                f"but received [{client_status[0]}]"
            )
        self.table.set_filter("Name", "")  # removing name filter from table

    def get_client_status(self):
        """ get the client status from the report page
        Returns: status
        """
        client_status = self.table.get_column_data('Update Status')
        if "Critical" in client_status:
            return "Critical"
        if "Warning" in client_status:
            return "Warning"
        return "Good"

    def get_client_count(self, client_type):
        """ Get each client count from tile outcome """
        tile_count = int((self.tile_outcome.split(client_type+'s :')[1]).split(',')[0])
        return tile_count

    def get_table_count(self, client_type):
        """ Get each client count from detailed report """
        if client_type == "Laptop":
            self.laptop_table = viewer.DataTable("Laptops")
            self.laptop_viewer = viewer.CustomReportViewer(self.admin_console)
            self.laptop_viewer.associate_component(self.laptop_table)
            self.laptop_table.set_filter("Type", '=' + client_type)
            self.laptop_table.set_filter("Update Status", 'Critical || Warning')
            table_count = self.laptop_table.get_row_count()
        elif client_type == "Infrastructure Client":
            self.table.set_filter("Type", "Infrastructure")
            self.table.set_filter("Update Status", 'Critical || Warning')
            table_count = self.table.get_row_count()
        else:
            self.table.set_filter("Type", '=' + client_type)
            self.table.set_filter("Update Status", 'Critical || Warning')
            table_count = self.table.get_row_count()

        return table_count

    def get_major_sp(self):
        """
        get the major service pack from CvCloud DB
        Returns: service pack number
        """
        query = """
                SELECT VALUE FROM CF_SURVEYCONFIG 
                WHERE NAME='11_0_LatestSPMajorNo'
                """
        major_version = self.utils.cre_api.execute_sql(
            query,
            database_name="CVCloud",
            desc="Getting major service pack info from CF_SURVEYCONFIG table")[0][0]
        return major_version

    def validate_tile_and_detailed_report(self):
        """
        verify equality for tile outcome and detailed report
        """
        failed_clients = []
        for client in self.client_type:
            if self.tile_count[client] != self.get_table_count(client):
                failed_clients.append(client)

        if failed_clients:
            raise CVTestStepFailure("Tile data and Detailed Table data do not match for "
                                    + str(failed_clients))

    def run(self):
        try:
            self.init_tc()
            for client in self.client_type:
                self.tile_count[client] = self.get_client_count(client)
            self.verify_tile_status()
            self.verify_commserver_status()
            self.validate_critical_status()
            self.validate_tile_and_detailed_report()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
