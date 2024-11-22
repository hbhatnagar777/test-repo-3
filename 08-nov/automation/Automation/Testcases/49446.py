from time import time

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.commcell_groups import CommcellGroup
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Components.alert import Alert

from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics CommCell Group: Validate group creation with no CommCell"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = True
        self.log = logger.get_log()
        self.browser: Browser = None
        self.admin_console: AdminConsole = None
        self.commcell_group: CommcellGroup = None
        timestamp = int(time())
        self.COMMCELL_GROUP_NAME = 'Automated_commcellGroup' + str(timestamp)

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.commcell_group = CommcellGroup(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.manage_reports = ManageReport(self.admin_console)
            self.navigator.navigate_to_metrics()
            self.manage_reports.access_commcell_group()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_empty_commcell_group(self):
        """Creation of the commcell group with empty commcell"""
        self.commcell_group.create(self.COMMCELL_GROUP_NAME)

    @test_step
    def validate_empty_group(self):
        """Validate empty commcell group created now"""
        ret = self.commcell_group.is_group_exist(self.COMMCELL_GROUP_NAME)
        if ret is False:
            raise CVTestStepFailure(
                "Commcell group %s created now doesn't exist in Group listing page"
                % self.COMMCELL_GROUP_NAME)
        cc_count = self.commcell_group.commcell_count_of_group(self.COMMCELL_GROUP_NAME)
        if int(cc_count) != 0:
            raise CVTestStepFailure(
                "commcell group has %d commcells, instead of zero commcells " % cc_count)

    @test_step
    def validate_commcells_in_group(self):
        """Validate the commcells page is showing correct message in this empty group"""
        self.commcell_group.access_commcell_group(self.COMMCELL_GROUP_NAME)
        get_no_data_message = Alert(self.admin_console)
        label = get_no_data_message.get_content()
        if label == ("You do not have any data or the required permissions to access the dashboard. "
                     "Ensure at least one registered CommCell is associated with this CommCell Group."):
            self.log.info("Correct message is shown for the commcells page")
        else:
            raise CVTestStepFailure(
                "Correct message is not shown, instead %s text is shown " % label)

    def run(self):
        try:
            self.init_tc()
            self.create_empty_commcell_group()
            self.validate_empty_group()
            self.validate_commcells_in_group()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.manage_reports.access_commcell_group()
            self.commcell_group.delete(self.COMMCELL_GROUP_NAME)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
