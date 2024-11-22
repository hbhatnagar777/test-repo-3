# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import (
    ReadMe, StoreApp
)
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Readme loading on all browsers"
        self.store: StoreApp = None
        self.readme: ReadMe = None
        self.inputs = StoreUtils.get_store_config()
        self.browser = None
        self.webconsole = None

    def webconsoles(self):
        try:
            browsers = (
                Browser.Types.CHROME,
                Browser.Types.FIREFOX
                # Browser.Types.IE  # TODO: Uncomment IE when IE issue is fixed
            )
            for type_ in browsers:
                factory = BrowserFactory()
                self.browser = factory.create_browser_object(type_)
                self.browser.open()
                self.webconsole = WebConsole(
                    self.browser,
                    self.commcell.webconsole_hostname
                )
                self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                      self.inputJSONnode['commcell']["commcellPassword"])
                self.store = StoreApp(self.webconsole)
                self.webconsole.goto_store()
                yield self.webconsole
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def close_resource(self):
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)

    @test_step
    def validate_description(self, webconsole):
        """Description set on the download center should be shown"""
        readme = ReadMe(webconsole)
        StoreApp(webconsole).goto_readme(self.inputs.Reports.FREE.name)
        readme_desc = readme.get_readme_description()
        expected_desc = self.inputs.Reports.FREE.desc
        if expected_desc not in readme_desc:
            raise CVTestStepFailure(
                "Unexpected readme description for [%s]; expected=[%s];"
                " received=[%s]" % (
                    self.inputs.Reports.FREE.name,
                    expected_desc,
                    readme_desc
                ))

    @test_step
    def validate_readme_screenshot(self, webconsole):
        """If readme is HTML, a message SAMPLE SCREENSHOT should be shown"""
        if ReadMe(webconsole).get_sample_screenshot_message() != "SAMPLE SCREENSHOT":
            raise CVTestStepFailure(
                "SAMPLE SCREENSHOT message not seen for package [%s]" %
                self.inputs.Reports.FREE.name
            )

    @test_step
    def validate_html_doc_readme(self, webconsole):
        """Check readme with HTML and document file types"""
        readme = ReadMe(webconsole)
        readme_text = readme.get_html_readme_text_content()
        if len(readme_text) < 100:
            raise CVTestStepFailure("Unable to view readme")
        webconsole.goto_store(direct=True)

        # Document readme
        self.store.goto_readme(
            self.inputs.Alerts.FREE.name,
            category="Alerts"
        )
        readme_text = readme.get_html_readme_text_content()
        if self.inputs.Alerts.FREE.readme not in readme_text:
            raise CVTestStepFailure("Unable to view readme")
        return readme

    @test_step
    def validate_hyperlink(self, readme):
        """If hyperlink exists on readme, it should work"""
        hyperlinks = readme.get_hyperlink_link_text()
        if len(hyperlinks) == 4:
            if hyperlinks[0] == "Traditional License - Getting Started":
                readme.visit_hyperlink(hyperlinks[0])
                return
        raise CVTestStepFailure(
            "No hyperlinks visible or unexpected hyperlinks"
        )

    @test_step
    def validate_mk_readme(self, webconsole):
        """Validate mediakit readme"""
        readme = ReadMe(webconsole)
        readme.goto_store_home()
        self.store.goto_readme(
            self.inputs.MEDIAKIT.Multi.name,
            category="Media Kits"
        )
        links = readme.get_hyperlink_link_text()
        if links != ["New Features", "List of Updates", "Release Notes"]:
            raise CVTestStepFailure(
                "Expected hyperlink not found inside "
                f"[{self.inputs.MEDIAKIT.Multi.name}] package."
                f"Received [{links}]"
            )

    def run(self):
        try:
            for webconsole in self.webconsoles():
                self.validate_description(webconsole)
                self.validate_readme_screenshot(webconsole)
                readme = self.validate_html_doc_readme(webconsole)
                self.validate_hyperlink(readme)
                self.validate_mk_readme(webconsole)
                self.close_resource()
        except Exception as err:
            StoreUtils(self).handle_testcase_exception(err)
        finally:
            self.close_resource()
