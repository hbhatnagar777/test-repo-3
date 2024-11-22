# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                            --  initialize TestCase class
    self.init_commandcenter()                             --  Initialize pre-requisites
    self.exclude_server_configuration()                   -- Exclude a server from command center
    self.exclude_file_server_page()                       -- Excclude a file server from command center
    self.verify_entity_excluded()                        -- Verify server is excluded properly
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "63346":
                        {
                            "ClientName" : "Fs_client_Name",
                            "ServerClient" : "Server_Name",
                            "AgentName" : "Agent_name",
                            "SubclientName1" : "Subclient_Name",
                            "storage_policy" : "Name of Plan",
                            "Hyperv_client" :   "Name of HyperV"
                        }
            }

"""
from datetime import datetime
from time import sleep

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils

from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.AdminConsolePages.server_details import ServerDetails

from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.sla import WebSla
from Web.WebConsole.Reports.navigator import Navigator
from Web.AdminConsole.Reports.Custom import viewer

from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.FileServerPages.file_servers import FileServers

_CONFIG = get_config()


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.backup_content = None
        self.subclient_names = None
        self.fssubclient_obj = None
        self.sla_panel = None
        self.server_client = None
        self.file_servers = None
        self.web_adapter = None
        self.tcinputs = {
            "ServerClient": None,
            "Hyperv_client": None
        }
        self.servers = None
        self.helper = None
        self.name = "SLA validation for exclude categories in Command Center"
        self.browser: Browser = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.utils: TestCaseUtils = None
        self.custom_report_utils = CustomReportUtils(self)
        self.admin_console = None
        self.sla = None
        self.subclient_names = None

    def init_commandcenter(self):
        """ initialize command center"""
        self.utils = TestCaseUtils(self)
        self.helper = FSHelper(self)
        FSHelper.populate_tc_inputs(self, mandatory=False)
        self.server_client = self.commcell.clients.get(self.tcinputs['ServerClient'])

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_servers()
        self.file_servers = FileServers(self.admin_console)
        self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        self.sla = WebSla(self.web_adapter)

    @test_step
    def exclude_server_configuration(self):
        """ exclude a server from server configuration page"""
        servers = Servers(self.admin_console)
        servers.select_client(self.server_client.display_name)
        server_details = ServerDetails(self.admin_console)
        server_details.enable_sla_toggle()

    @test_step
    def verify_entity_excluded(self, category_type=None, entity_name=None, exclude_category=None):
        """ verify the entity is excluded from SLA report"""
        self.navigator.navigate_to_reports()
        manage_report_admin = ManageReport(self.admin_console)
        manage_report_admin.access_report("SLA")
        self.sla.access_excluded_sla()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Excluded Entities")
        report_viewer.associate_component(table_obj)
        if category_type not in ['Backup Activity Disabled', 'Recently Installed']:
            table_obj.set_filter(column_name='Server', filter_string=entity_name)
            server_name = table_obj.get_column_data('Server')
            category = table_obj.get_column_data('Category')
            if entity_name not in server_name and exclude_category not in category:
                raise CVTestStepFailure(f"Expected client is {entity_name} but received {server_name} and "
                                        f"Expected category is {exclude_category} but received{category}")
        if category_type in ['Backup Activity Disabled', 'Recently Installed']:
            table_obj.set_filter(column_name='Subclient', filter_string=entity_name)
            subclient_name = table_obj.get_column_data('Subclient')
            category = table_obj.get_column_data('Category')
            if self.subclient_names[0] not in subclient_name and exclude_category not in category:
                raise CVTestStepFailure(f"Expected subclient is {self.subclient_names[0]} but received {subclient_name}"
                                        f"and Expected category is {exclude_category} but received{category}")

    @test_step
    def exclude_file_server_page(self):
        """ exclude a server from fileserver page"""
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client.display_name)
        fssubclient_obj = FsSubclient(self.admin_console)
        fssubclient_obj.access_subclient('defaultBackupSet',self.tcinputs['SubclientName1'])
        self.file_servers.enable_sla_toggle()

    @test_step
    def add_subclient_fs(self, subclient_name, backup_content):
        """ create new subclient in fs client"""
        self.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client.display_name)
        self.helper.create_backupset('Backupset_TC_63346', delete=False)
        self.helper.create_subclient(
            name= subclient_name,
            storage_policy=self.tcinputs['storage_policy'],
            content=backup_content,
            delete=True
        )

    def run(self):
        """ run method"""
        try:
            self.init_commandcenter()
            self.exclude_server_configuration()
            self.exclude_file_server_page()
            backup_content = [['/dummy'], ['/dummy/TEST']]
            self.subclient_names = ['Auto_TC63346', 'Activity_disabled_subclient']
            self.add_subclient_fs(self.subclient_names[0], backup_content[0])
            self.add_subclient_fs(self.subclient_names[1], backup_content[1])
            self.subclient.disable_backup()
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.verify_entity_excluded(entity_name=self.server_client.display_name)
            self.verify_entity_excluded(entity_name=self.client.display_name)
            # verify recently created subclient
            self.verify_entity_excluded('Recently Installed', entity_name=self.subclient_names[0],
                                        exclude_category=self.sla.Exclude_sla_categories.RECENTLY_INSTALLED.value)
            # verify the subclient category showing as disabled
            self.verify_entity_excluded('Backup Activity Disabled', entity_name=self.subclient_names[1],
                                        exclude_category=self.sla.Exclude_sla_categories.BACKUP_ACTIVITY_DISABLED.value)
            # verify the hyperv client category
            self.verify_entity_excluded('Excluded Server Type', entity_name=self.tcinputs['Hyperv_client'],
                                        exclude_category=self.sla.Exclude_sla_categories.EXCLUDED_SERVER_TYPE.value)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
