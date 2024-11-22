# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Store: Auto Login verification and access based downloading of reports and media kits

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case.
                        Validates different CommCell's accessibility

    Input Example:

    "testCases": {

                "58887": {
                    "Premium_no_media" : "#####",
                    "Free_no_media" : "#####",
                    "Free_with_media": "#####",
                    "Premium_with_media": "#####"
                }
            }
"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Reports import utils
from Reports.storeutils import StoreUtils
from Web.API.customreports import logout_silently, CustomReportsAPI
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp, ReadMe
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """
        TestCase class used to execute the test case from here.
        """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Auto-login verification and access based downloading of reports and media kits"
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.store: StoreApp = None
        self.utils = None
        self.inputs = None
        self.cre_api = None
        self.tcinputs = {
            "Free_no_media": None,
            "Free_with_media": None,
            "Premium_no_media": None,
            "Premium_with_media": None,
        }

    def init_tc(self):
        """
                Initial configuration for the test case
        """
        try:
            self.utils = StoreUtils(self)
            self.inputs = StoreUtils.get_store_config()

            # check if package has free and premium status on store server
            self.utils.validate_for_free_status(
                self.inputs.Reports.FREE.name
            )
            # self.utils.validate_for_premium_status(
            #     self.inputs.Reports.PREMIUM
            # )
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def webconsole_login(self, commcell_name):
        """Login to webconsole"""
        config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.utils.get_temp_dir())
        self.browser.open()
        self.webconsole = WebConsole(
            self.browser,
            commcell_name
        )
        self.webconsole.login()
        self.store = StoreApp(self.webconsole)
        self.cre_api = CustomReportsAPI(
            commcell_name,
            username=config.ADMIN_USERNAME,
            password=config.ADMIN_PASSWORD
        )

    def webconsole_logout(self):
        """Logout of webconsole"""
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)
        logout_silently(self.cre_api)

    @test_step
    def free_report_accessibility(self):
        """If the report's pricing is set to 'Free' report should be installable"""
        self.cre_api.delete_custom_report_by_name(
            self.inputs.Reports.FREE.name, suppress=True
        )
        self.log.info("Installing Free report")
        self.webconsole.goto_store(direct=True)
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.FREE.name,
            category="Reports"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                "[%s] is not having install status" %
                self.inputs.Reports.FREE.name
            )
        self.store.install_report(
            self.inputs.Reports.FREE.name
        )
        self.log.info("Free report installed successfully")

    def premium_package_status(self):
        """Returns status of premium package"""
        self.cre_api.delete_custom_report_by_name(
            self.inputs.Reports.PREMIUM, suppress=True
        )
        self.webconsole.goto_store(direct=True)
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.PREMIUM,
            category="Reports"
        )
        return pkg_status

    @test_step
    def premium_report_install(self):
        """If package is premium, report should be installable by Premium users"""
        pkg_status = self.premium_package_status()
        if pkg_status != "Install":
            raise CVTestStepFailure(
                "[%s] is not having install status" %
                self.inputs.Reports.PREMIUM
            )
        self.log.info("Installing premium report")
        self.store.install_report(
            self.inputs.Reports.PREMIUM
        )
        self.log.info("Premium report installed successfully")

    @test_step
    def premium_report_message(self):
        """If package is premium, Purchase status should be seen by Free users"""
        pkg_status = self.premium_package_status()
        if pkg_status != "Purchase":
            raise CVTestStepFailure(
                "[%s] is having [%s] status instead of Purchase" % (
                    self.inputs.Reports.PREMIUM,
                    pkg_status
                )
            )
        self.log.info("Verifying info message displayed after clicking on Purchase")
        info_msg = self.store.get_premium_info_message(
            self.inputs.Reports.PREMIUM
        )
        if "You must be a Premium Member" not in info_msg:
            raise CVTestStepFailure(
                f"Unexpected message [{info_msg}] in Premium popup "
                f"window"
            )
        self.log.info("Expected message is displayed in Premium popup window")

    @test_step
    def media_kit_download(self):
        """Download media kit package"""
        self.utils.reset_temp_dir()
        readme = ReadMe(self.webconsole)
        self.log.info("Downloading media kit")
        self.store.download_package(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        self.store.goto_readme(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        descriptions = readme.get_readme_description()
        self.utils.poll_for_tmp_files(ends_with="exe", count=1)
        self.utils.validate_tmp_files(
            ends_with="exe",
            count=1,
            hashes=[
                description[:32].lower()
                for description in descriptions.split(" ")
                if len(description.strip()) >= 32
            ]
        )
        self.log.info("Media kit downloaded successfully")

    @test_step
    def media_kit_message(self):
        """Download media kit with no permission should display access restricted message"""
        self.log.info("Verifying info message displayed after clicking on Download")
        info_msg = self.store.get_access_restricted_info_message(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        if "Contact your software provider to obtain access to this package" not in info_msg:
            raise CVTestStepFailure(
                f"Unexpected message [{info_msg}] in Access Restricted popup window"
            )
        self.log.info("Expected message is displayed in access restricted pop-up window")

    @test_step
    def validate_premium_no_media(self, commcell_name):
        """Validates Premium no media CommCell accessibility"""
        self.webconsole_login(commcell_name)
        self.free_report_accessibility()
        self.premium_report_install()
        self.media_kit_message()
        self.webconsole_logout()

    @test_step
    def validate_free_no_media(self, commcell_name):
        """Validates Free no media CommCell accessibility"""
        self.webconsole_login(commcell_name)
        self.free_report_accessibility()
        # self.premium_report_message()
        self.media_kit_message()
        self.webconsole_logout()

    @test_step
    def validate_premium_with_media(self, commcell_name):
        """Validates Premium with media CommCell accessibility"""
        self.webconsole_login(commcell_name)
        self.free_report_accessibility()
        self.premium_report_install()
        self.media_kit_download()
        self.webconsole_logout()

    @test_step
    def validate_free_with_media(self, commcell_name):
        """Validates Free with media CommCell accessibility"""
        self.webconsole_login(commcell_name)
        self.free_report_accessibility()
        # self.premium_report_message()
        self.media_kit_download()
        self.webconsole_logout()

    def run(self):
        try:
            self.init_tc()
            # commenting as all reports are made free as of 12/1/2020
            # self.validate_premium_no_media(self.tcinputs['Premium_no_media'])
            # self.validate_premium_with_media(self.tcinputs['Premium_with_media'])
            self.validate_free_with_media(self.tcinputs['Free_with_media'])
            self.validate_free_no_media(self.tcinputs['Free_no_media'])

        except Exception as err:
            utils.TestCaseUtils(self).handle_testcase_exception(err)
            self.webconsole_logout()
