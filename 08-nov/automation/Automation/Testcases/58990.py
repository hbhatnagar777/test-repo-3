from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.manage_reports import Tag, ManageReport
from Web.API.webconsole import Reports
import Web.AdminConsole.adminconsole
from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Reports: Built in UI tags to not overwrite user defined tags"
        self.utils = CustomReportUtils(self)
        self.webconsole: WebConsole = None
        self.admin_console = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.api = None
        self.rpt_definition = None
        self.navigator = None
        self.obj_manage_report = None
        self.tag = None
        self.rpt_api = None
        self.inpt_tags = ['Azure', 'Analytics', 'Amazon']
        self.report_name = 'TC 58990-Adding UI Tags'

    def init_tc(self):
        try:
            self.utils.cre_api.delete_custom_report_by_name(
                self.report_name, suppress=True
            )
            self.rpt_api = Reports(
                self.commcell.webconsole_hostname,
                username=self.inputJSONnode['commcell']['commcellUsername'],
                password=self.inputJSONnode['commcell']['commcellPassword']
            )
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.utils.reset_temp_dir()
            self. webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])

            Navigator(self.webconsole).goto_report_builder()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def add_ui_tags(self, tags):
        """Add UI TAGS"""
        self.rpt_builder.add_tags(tags)
        self.rpt_builder.save_and_deploy()

    @test_step
    def export_report_definition(self):
        """export report definition"""
        self.rpt_builder.export_report_template()
        self.webconsole.logout()

    @test_step
    def login_admin_console(self):
        """login to Admin Console"""
        self.admin_console = Web.AdminConsole.adminconsole.AdminConsole(
            self.browser,
            self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_reports()

    @test_step
    def verify_tags(self):
        """Check tags from Admin Console"""
        self.obj_manage_report = ManageReport(self.admin_console)
        self.obj_manage_report.tag_report(self.report_name)
        self.tag = Tag(self.admin_console)
        if list(self.tag.get_associated_tags()) != sorted(self.inpt_tags):
            raise CVTestStepFailure(f'Expected tag {self.inpt_tags} received tags {self.tag.get_associated_tags()}')
    
    @test_step
    def addTag(self):
        """Add tag from reports page (Admin Console)"""
        self.tag.create_tag('Clients', apply_to_all=True)
        self.inpt_tags.append('Clients')

    @test_step
    def import_report_definition(self):
        """Import the report defintion"""
        # xml_data = open(self.utils.get_temp_dir() + '\\TC 58990-Adding UI Tags.xml', "r")
        self.rpt_api.import_custom_report_xml(self.utils.get_temp_dir() + '\\TC58990AddingUITags.xml')
        self.admin_console.refresh_page()

    def run(self):
        try:
            self.init_tc()
            self.add_ui_tags(self.inpt_tags)
            self.export_report_definition()
            self.login_admin_console()
            self.verify_tags()
            self.addTag()
            self.import_report_definition()
            self.verify_tags()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

