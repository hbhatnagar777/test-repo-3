# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate generation of Charter"""

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import (inputs, viewer)

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports.reportsutils import DocManager


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Charter generation & validation"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.viewer_obj = None

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.webconsole.goto_reports()
            navigator = Navigator(self.webconsole)
            self.viewer_obj = viewer.CustomReportViewer(self.webconsole)
            navigator.goto_worldwide_report("Charter and Plan Of Record")
            self.file_type = "docx"
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def select_sp(self):
        """
           Gets a list of SP available from SP Input and selects a SP from it
        """
        sp_input_controller = inputs.DropDownController("Service Pack")
        self.viewer_obj.associate_input(sp_input_controller)
        sp_input_controller.select_value('SP' + str(self.commcell.commserv_version))  # selecting current SP

    def generate_charter(self):
        """
           Generates charter document by clicking on 'Generate Charter'
        """
        html_component = viewer.HtmlComponent("")  # because title of html component is blank
        self.viewer_obj.associate_component(html_component)
        html_component.click_button("Generate Charter")

    def get_charter_data(self):
        """
        Get a list of text containing SP, Version and Themes to be searched in document
        """
        version_value = self.commcell.version.split('.')[0]
        sp_value = self.commcell.commserv_version
        line1 = "\t\tSP" + str(sp_value) + " Charter + Plan of Record"
        line2 = "Version " + version_value + " Service Pack " + str(sp_value)
        theme1 = 'Roadmap Theme: Journey to the Cloud'
        theme2 = 'Roadmap Theme: Complete Backup and Recovery'
        theme3 = 'Roadmap Theme: Complete: Enable Service Providers'
        theme4 = 'Roadmap Theme: Modern Infrastructures'
        theme5 = 'Roadmap Theme: Orchestration and Automation'
        theme6 = 'Roadmap Theme: Understand and Activate Data'
        text_list = [line1, line2, theme1, theme2, theme3, theme4, theme5, theme6]
        return text_list

    def validate_data(self, text_list):
        """Verify SP, Version, Themes  displayed in charter export are correct"""

        _files = self.utils.poll_for_tmp_files(ends_with=self.file_type)
        _doc = DocManager(_files[0])
        _doc.read_doc()
        _doc.search_text(text_list)
        self.log.info("SP, Version and Themes in Charter document are verified")

    @test_step
    def verify_charter_generation(self):
        """
        Verify charter document is generated
        """
        self.select_sp()
        self.generate_charter()
        self.utils.wait_for_file_to_download(self.file_type, timeout_period=120)
        self.utils.validate_tmp_files(self.file_type)
        self.log.info("Verified generation of charter and Plan of Record")

    @test_step
    def validate_charter_data(self):
        """
        Validate the data in generated charter document
        """
        self.log.info("Validating data in exported charter document")
        text_list = self.get_charter_data()
        self.validate_data(text_list)
        self.log.info("Validated data in Charter document!")

    def run(self):
        try:
            self._init_tc()
            self.verify_charter_generation()
            self.validate_charter_data()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
