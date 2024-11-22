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
    __init__()                      --  initialize TestCase class
    init_tc()                       --  initial Configuration for testcase
    add_repository                  --  Adds a repository
    add_package                     --  Adds a downloadable package
    download_package                --  Downloads the package files
    verify_download                 --  Verified if the files got downloaded successfully and the checksum is matching
    perform_cleanup()               --  Perform Cleanup Operation
    run()                           --  run function of this test case
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DownloadCenter.downloadcenter import DownloadCenter
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Testcase for Download center from AdminConsole"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance testcase for Download Center from AdminConsole"
        self.tcinputs = {
            "WebServer": None
        }
        # Test Case constants
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.repository_name = None
        self.package_name = None
        self.category_name = None
        self.subcategory_name = None
        self.download_center = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """Initial Configuration for testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.repository_name = f'{self.id}_Repository'
            self.package_name = f'{self.id}_Package'
            self.category_name = f'{self.id}_Category'
            self.subcategory_name = f'{self.id}_SubCategory'
            self.download_center = DownloadCenter(self.admin_console)
            self.utils.reset_temp_dir()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def add_repository(self):
        """
        Adds a repository
        """
        self.navigator.navigate_to_download_center()
        self.download_center.add_repository(
            repository_name=self.repository_name, entity_name=self.tcinputs['WebServer'])

    @test_step
    def add_package(self):
        """
        Adds a downloadable package
        """
        self.navigator.navigate_to_download_center()
        self.download_center.navigate_to_downloads_tab()
        self.download_center.add_package(package_name=self.package_name, repository_name=self.repository_name,
                                         category_name=self.category_name, subcategory_name=self.subcategory_name)

    @test_step
    def download_package(self):
        """
        Downloads the package files
        """
        self.navigator.navigate_to_download_center()
        self.download_center.navigate_to_downloads_tab()
        self.download_center.download_package(self.package_name, user_logged_in=True)

    @test_step
    def verify_download(self, file_with_checksum_dict):
        """
        Verified if the files got downloaded successfully and the checksum is matching
        Args:
            file_with_checksum_dict     (dict): dictionary having key as file name and value as it's md5 checksum
        """
        machine_obj = Machine()
        for file_name in file_with_checksum_dict:
            file_path = self.utils.poll_for_tmp_files(file_name, timeout=60)[0]
            checksum = machine_obj.get_file_hash(file_path, algorithm="SHA256")
            self.log.info(f"File: {checksum}, UI: {file_with_checksum_dict[file_name]}")
            if checksum.upper() == file_with_checksum_dict[file_name].upper():
                self.log.info(f'Checksum matched for file: {file_name} having checksum {checksum}')
            else:
                raise Exception(f'Checksum does not matched for file: {file_name} with checksum at '
                                f'UI: {file_with_checksum_dict[file_name]} & checksum of directory file: {checksum}')

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        # Package Deletion
        self.navigator.navigate_to_download_center()
        self.download_center.navigate_to_downloads_tab()
        if self.download_center.is_package_exists(self.package_name):
            self.download_center.delete_package(self.package_name)

        # Category Deletion
        self.navigator.navigate_to_download_center()
        self.download_center.navigate_to_downloads_tab()
        manage_info = self.download_center.access_manage_information()
        if manage_info.is_category_exist(self.category_name):
            manage_info.delete_category(self.category_name)

        # Repository Deletion
        self.navigator.navigate_to_download_center()
        if self.download_center.is_repository_exists(self.repository_name):
            self.download_center.delete_repository(self.repository_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.perform_cleanup()
            self.add_repository()
            self.add_package()
            self.download_package()
            file_with_checksum_dict = self.download_center.get_file_names_with_checksum(self.package_name)
            self.verify_download(file_with_checksum_dict)
            self.perform_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
