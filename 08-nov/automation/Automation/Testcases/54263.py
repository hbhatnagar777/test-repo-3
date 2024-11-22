# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" verify download center anonymous access feature """

from time import sleep

from AutomationUtils.windows_machine import WindowsMachine
from Web.AdminConsole.DownloadCenter.downloadcenter import DownloadCenter
from Web.AdminConsole.DownloadCenter.settings import ManageInformation
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "verify download center anonymous access feature"
        self.show_to_user = True
        self.browser = None
        self.web_console = None
        self.download_center = None
        self.manage_information = None
        self.test_admin_console = None
        self.test_adminconsole_dc = None
        self.test_webconsole_manage_information = None
        self.category = "AnonymousCategory"
        self.sub_category = "AnonymousSC"
        self.utils = TestCaseUtils(self)

    def access_download_center_url(self, webconsole):
        """Access download center url"""
        dc_url = self.test_adminconsole_dc.download_center_url
        webconsole.browser.driver.get(dc_url)
        webconsole.wait_for_completion()

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.cs_machine = WindowsMachine(machine_name=self.commcell.webconsole_hostname,
                                             commcell_object=self.commcell)
            self.browser = BrowserFactory().create_browser_object(
                browser_type= Browser.Types.CHROME, name="ClientBrowser")
            self.browser.open()

            # login to admin console
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_download_center()
            self.download_center = DownloadCenter(self.admin_console)
            self.manage_information = ManageInformation(self.admin_console)
            self.utils.reset_temp_dir()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def verify_xml_downloaded(self):
        """Verify xml file is downloaded"""
        xml_path = self.utils.poll_for_tmp_files('xml')
        self.log.info("[%s] XML file downloaded successfully!", xml_path)

    def initial_configuration(self):
        """Check if subcategory already anonymous access is enabled, if yes disable it"""
        try:
            self.log.info("Check if subcategory already anonymous access is enabled, "
                          "if yes disable it")
            self.initiate_test_browser()
            self.test_admin_console.login()
            self.test_navigator = self.test_admin_console.navigator
            self.test_navigator.navigate_to_download_center()
            self.test_admin_console.access_tab("Downloads")
            self.test_adminconsole_dc.access_manage_information()
            self.test_adminconsole_manage_information.search_category(self.category)
            self.test_adminconsole_manage_information.select_category(self.category)
            self.test_admin_console.wait_for_completion()
            sub_category = self.test_adminconsole_manage_information.edit_sub_category(self.sub_category)
            sub_category.switch_anonymous_access(status=False)
            sub_category.save()
            sleep(6) # wait for sync to complete
        except Exception:
            self.log.info("Configuration settings are as expected")
        finally:
            self.test_admin_console.browser.close()

    @test_step
    def verify_public_view_enabled_download_disabled(self):
        """Enable anonymous access and see packages can be seen without login"""
        try:
            self.log.info("Enabling anonymous access")
            self.admin_console.access_tab("Downloads")
            self.download_center.access_manage_information()
            self.manage_information.select_category(self.category)
            sub_category = self.manage_information.edit_sub_category(self.sub_category)
            sub_category.switch_anonymous_access(status=True)
            sub_category.switch_free_downloads(status=False)
            sub_category.save()
            self.log.info("Anonymous access is enabled!")
            self.log.info("Verify expected sub category is visible without login")
            self.log.info("Restart IIS to refresh cache & Wait for 2 minutes for syncup")
            try:
                self.cs_machine.restart_iis()
            except Exception as e:
                pass
            sleep(120)

            self.initiate_test_browser()
            if self.test_adminconsole_dc.is_subcategory_exists(self.sub_category) is False:
                raise CVTestStepFailure("Subcategory [%s] is not found without login" %
                                        self.sub_category)
            self.log.info("Expected sub category [%s] exists in download center",
                          self.sub_category)
            self.log.info("click on download and then login, search for subcategory. "
                          "click on download package")
            self.test_adminconsole_dc.search_package_keyword(self.category)
            package_name = self.test_adminconsole_dc.get_package_list()[0]
            self.test_adminconsole_dc.download_package(package_name)
            self.test_admin_console.login()
            # After redirected login, it should show Downloads by default
            self.test_adminconsole_dc.search_package_keyword(self.category)
            package_name = self.test_adminconsole_dc.get_package_list()[0]
            self.test_adminconsole_dc.download_package(package_name, True)

            # Verify xml is downloaded
            self.verify_xml_downloaded()
            AdminConsole.logout_silently(self.test_admin_console)
            Browser.close_silently(self.test_browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def verify_public_view_disabled(self):
        """Disable anonymous access and see packages cannot be seen without login"""
        try:
            self.log.info("Disabling anonymous access")
            # self.admin_console.access_tab("Downloads")
            # self.download_center.access_manage_information()
            self.manage_information.select_category(self.category)
            sub_category = self.manage_information.edit_sub_category(self.sub_category)
            sub_category.switch_anonymous_access(status=False)
            sub_category.save()
            self.log.info("Anonymous access is Disabled!")

            self.log.info("Verify expected sub category is NOT visible without login")
            self.log.info("Restart IIS to refresh cache & Wait for 2 minutes for syncup")
            try:
                self.cs_machine.restart_iis()
            except Exception as e:
                pass
            sleep(120)
            self.initiate_test_browser()
            if self.test_adminconsole_dc.is_subcategory_exists(self.sub_category) is True:
                raise CVTestStepFailure("Subcategory [%s] is found without login" %
                                        self.sub_category)
            self.log.info("Expected sub category [%s] doesnot exist in download center",
                          self.sub_category)
            Browser.close_silently(self.test_browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def verify_public_download_enabled(self):
        """Enable anonymous download, verify without login should be able to download the xml"""
        try:
            self.utils.reset_temp_dir()
            self.log.info("Enabling free download")
            self.manage_information.select_category(self.category)
            sub_category = self.manage_information.edit_sub_category(self.sub_category)
            sub_category.switch_anonymous_access(status=True)
            sub_category.switch_free_downloads(status=True)
            sub_category.save()

            self.log.info("Access download center url, verify xml can be downloaded without"
                          " login")
            self.log.info("Restart IIS to refresh cache & Wait for 2 minutes for syncup ")
            try:
                self.cs_machine.restart_iis()
            except Exception as e:
                pass
            sleep(120)
            self.initiate_test_browser()
            self.test_adminconsole_dc.search_package_keyword(self.category)
            package_name = self.test_adminconsole_dc.get_package_list()[0]
            self.test_adminconsole_dc.download_package(package_name)

            # Verify xml is downloaded
            self.verify_xml_downloaded()
            Browser.close_silently(self.test_browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    def initiate_test_browser(self):
        """Initiate test browser"""
        self.test_browser = BrowserFactory().create_browser_object(
            browser_type= Browser.Types.CHROME, name="TestDCBrowser")
        self.test_browser.set_downloads_dir(self.utils.get_temp_dir())
        self.test_browser.open()
        # login to Admin console
        self.test_admin_console = AdminConsole(self.test_browser, self.commcell.webconsole_hostname)
        self.test_adminconsole_dc = DownloadCenter(self.test_admin_console)
        self.access_download_center_url(self.test_admin_console)
        self.test_adminconsole_manage_information = ManageInformation(self.test_admin_console)

    def revert_changes(self):
        """Disable anonymous access for sub category"""
        self.manage_information.select_category(self.category)
        sub_category = self.manage_information.edit_sub_category(self.sub_category)
        sub_category.switch_anonymous_access(status=False)
        sub_category.save()
        self.log.info("Reverted configuration changes")

    def run(self):
        try:
            # self.initial_configuration()
            self.init_tc()
            self.verify_public_view_enabled_download_disabled()
            self.verify_public_view_disabled()
            self.verify_public_download_enabled()
            self.revert_changes()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.test_admin_console)
            Browser.close_silently(self.test_admin_console.browser)
