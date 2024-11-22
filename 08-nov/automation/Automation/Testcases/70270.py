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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

"""
import time
import zipfile

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Office365Pages.office365_apps import DashboardTile
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.constants import TEMP_DIR


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    OneDrive Self Service User Case:
    Verification of export
    """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = f'OneDrive Self Service Export Verification Testcase'
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.app_type = None
        self.dashboard_tile = None
        self.machine = None

    def setup(self):
        """ Initial configuration for the test case. """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname, enable_ssl=True)

        self.admin_console.login(
            self.inputJSONnode['commcell']['loginUsername'],
            self.inputJSONnode['commcell']['loginPassword'], saml=True)

        self.navigator = self.admin_console.navigator
        self.admin_console.hotkey_settings('bEnableReactBrowsePages')
        self.dashboard_tile = DashboardTile(self.admin_console)

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.one_drive_for_business
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console)
        self.machine = WindowsMachine()

    def run(self):
        try:
            self.navigator.navigate_to_office365(access_tab=False)
            self.verify_export()
            self.navigator.navigate_to_office365(access_tab=False)
            self.verify_export(select_all=True)
        except Exception as err:
            handle_testcase_exception(self, err)

    @test_step
    def verify_export(self, select_all=False):
        """Verifies restore page"""
        self.dashboard_tile.click_restore_by_client(self.tcinputs['Client'])
        self.admin_console.wait_for_completion()
        self.office365_obj.search_in_browse_page(self.tcinputs['SearchKeyword'])
        self.office365_obj.select_rows_in_table(names=self.tcinputs['RowsToSelect'])
        export_name = self.tcinputs['ExportName'] + ("_All" if select_all else "_Selected")
        export_job_details = self.office365_obj.perform_export(export_name=export_name, select_all=select_all)
        num_exported_items = int(export_job_details["Number of files transferred"])
        self.navigator.navigate_to_office365(access_tab=False)
        self.dashboard_tile.click_restore_by_client(self.tcinputs['Client'])
        self.admin_console.wait_for_completion()
        self.office365_obj.download_export(export_name=export_name)
        path = TEMP_DIR + "\\" + export_name + '.zip'
        self.wait_for_file_to_download(path=path, timeout_period=200, sleep_time=1)
        self.verify_exported_file(export_name, num_exported_items, path)

    def wait_for_file_to_download(self, path, timeout_period=200, sleep_time=1):
        i = 0
        self.log.info("Waiting for file to be downloaded")
        while i < timeout_period:
            exists = self.machine.check_file_exists(file_path=path)
            if exists:
                time.sleep(5)
                self.log.info(f"Found file {path}")
                return
            else:
                time.sleep(sleep_time)
            i += sleep_time
        self.log.error("File couldn't be downloaded in time")
        raise CVWebAutomationException("Time out occurred during file download")

    def verify_exported_file(self, export_name, num_exported_items, path):
        if self.machine.check_file_exists(file_path=path):
            value = self.machine.get_file_size(file_path=path)
            if value == 0:
                raise CVWebAutomationException('Exported file size is 0!')
            else:
                self.log.info(f"The exported file size is : {value} MB")
                # zip file handler
                zip_file = zipfile.ZipFile(path)
                # list available files in the container
                zip_count = len(zip_file.namelist())
                zip_file.close()
                if zip_count != num_exported_items:
                    raise CVWebAutomationException(f'Number of items in Zip ({zip_count}) is '
                                                   f'not equal to items selected for export ({num_exported_items})!')
                else:
                    self.log.info(f'Number of items in Zip file is equal to items selected for export : {zip_count}')
        else:
            raise CVWebAutomationException("The exported file doesn't exist!")

    def tear_down(self):
        self.log.info(f'Test case status: {self.status}')
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
