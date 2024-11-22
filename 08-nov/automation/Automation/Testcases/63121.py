# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Acceptance case for Activate Datasource Management : From CSV

TestCase:
    __init__()          --  initialize TestCase class

    navigate_to_adm()   --  Navigates the browser to ADM landing page

    generate_csv_data() --  Generates DS config csv file and returns a dictionary and
                            file path with the config data

    add_data_sources_from_csv() --  Enters data sources details for all DS configs
                                    present in the config csv file

    validate_datasources()  --  Validates the datasource status

    init_tc()             --  Initializes all the variables

    run()               --  run function of this test case

    tear_down()         --  tear down function of this test case

Input Example:

    "testCases":
            {
                "63121":
                 {
                     "Username": "Command center user name",
                     "Password": "Password of the user"
                 }
            }
            """
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
)
from Web.AdminConsole.GovernanceAppsPages.FileStorageOptimization import (
    FileStorageOptimization,
    FSODataSourceManagement
)
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from cvpysdk.commcell import Commcell
ADM_CONFIG_DATA = get_config().DynamicIndex.DataSourceManagement


class TestCase(CVTestCase):
    """ Testcase """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Acceptance case for Activate Datasource Management : From CSV"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            "Username": None,
            "Password": None,
        }
        self.commcell = None
        self.activate_utils = None
        self.fso_helper = None
        self.navigator = None
        self.gdpr_obj = None
        self.adm_helper = None
        self.config_data = None
        self.csv_path = None
        self.ds_helper = None
        self.validation_data = None

    @test_step
    def navigate_to_adm(self):
        """Navigates the browser to ADM inputs page"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.view_datasources()

    @test_step
    def generate_csv_data(self):
        """Generates csv config data from give automation config values"""
        self.config_data, self.csv_path, self.validation_data = self.activate_utils.\
            generate_fso_datasource_config(ADM_CONFIG_DATA.NumberOfDatasources)

    @test_step
    def add_data_sources_from_csv(self):
        """Adds multiple datasources from csv file"""
        self.adm_helper.add_multiple_data_sources(ADM_CONFIG_DATA.InventoryName,
                                                  import_csv=True, csv_file_path=self.csv_path)

    @test_step
    def validate_datasources(self):
        """Verifies if all the datasources were created successfully and invalid ones were not"""
        try:
            self.ds_helper.validate_adm_datasources_with_config(self.validation_data, cleanup=True)
        except Exception as exception:
            raise CVTestStepFailure(exception) from exception

    def init_tc(self):
        """Initialize and Opens browse and login to webconsole"""
        try:
            self.commcell = Commcell(
                webconsole_hostname=self.inputJSONnode['commcell']["webconsoleHostname"],
                commcell_username=self.tcinputs["Username"],
                commcell_password=self.tcinputs["Password"])
            self.activate_utils = ActivateUtils(self.commcell)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.tcinputs["Username"],
                self.tcinputs["Password"],
            )
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.fso_helper = FileStorageOptimization(self.admin_console)
            self.adm_helper = FSODataSourceManagement(self.admin_console)
            self.ds_helper = DataSourceHelper(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_adm()
            self.generate_csv_data()
            self.add_data_sources_from_csv()
            self.validate_datasources()
        except Exception as exception:
            raise CVTestStepFailure(exception) from exception
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
