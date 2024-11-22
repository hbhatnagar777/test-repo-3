# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase to Metrics: verify Enable/Disable survey and Delete CommCell
"""

from time import sleep

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.commcells import Commcell
from Web.AdminConsole.adminconsole import AdminConsole
from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk.commcell import Commcell as cvcommcell


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.monitoringform import ManageCommcells

from Reports.utils import TestCaseUtils

from Reports import utils

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Metrics: verify Enable/Disable survey and Delete CommCell"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.metrics_commcell = None
        self.manage_reports = None
        self.driver = None
        self.admin_console = None
        self.name = "Metrics: verify Enable/Disable survey and Delete CommCell"
        self.utils = TestCaseUtils(self)
        self.webconsole_user_name = None
        self.webconsole_password = None
        self.webconsole_host_name = None
        self.commcell_monitoring_page = None
        self.browser = None
        self.non_admin_user = None
        self.non_admin_password = None
        self.private_metrics = None
        self.webconsole = None
        self.navigator = None
        self.uploading_cs = None
        self.new_commcell_name = None
        self.cs_name = None
        self.tcinputs = {
            "commcell_to_delete": None
        }
        self.v11_cs_name = None

    def setup(self):
        """Initializes Private metrics object required for this testcase"""
        self.v11_cs_name = self.tcinputs["commcell_to_delete"]
        cs_username = self.tcinputs["user_name"]
        password = self.tcinputs["password"]
        self.cs_name = self.v11_cs_name.split('.')
        self.uploading_cs = cvcommcell(self.v11_cs_name, cs_username, password)
        self.webconsole_user_name = self.inputJSONnode['commcell']["commcellUsername"]
        self.webconsole_password = self.inputJSONnode['commcell']["commcellPassword"]
        self.webconsole_host_name = self.inputJSONnode['commcell']["webconsoleHostname"]
        self.non_admin_user = "automated_non_admin_user_48268"
        self.non_admin_password = "######"
        self.new_commcell_name = "CommCell_48268"
        self.utils = utils.TestCaseUtils(self)
        self.create_non_admin_user()
        self.configure_cs()

    def configure_cs(self):
        """Update download and upload urls to metrics server """
        # before triggering survey make sure upload urls are pointing to required metrics server
        self.private_metrics = PrivateMetrics(self.uploading_cs)
        if self.webconsole_host_name in self.private_metrics.downloadurl:
            return
        self.private_metrics.enable_metrics()
        self.private_metrics.update_url(self.webconsole_host_name)
        self.private_metrics.save_config()
        self.initiate_private_upload()

    def init_tc(self, user_name, password):
        """Initialize browser and redirect to page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(user_name, password)
            self.navigator = self.admin_console.navigator
            self.driver = self.browser.driver
            self.navigator.navigate_to_metrics()
            self.manage_reports = ManageReport(self.admin_console)
            self.metrics_commcell = Commcell(self.admin_console)
            self.manage_reports.access_dashboard()
            self.metrics_commcell.goto_commcell_tab()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def associate_user_to_commcell(self):
        """Associate user to commcell in commcell monitoring page"""
        if not self.metrics_commcell.associate_user(self.uploading_cs.commserv_name, self.non_admin_user ):
            raise CVTestStepFailure(f"User {self.non_admin_user} is not associated to the CommCell")

    @test_step
    def verify_disable_survey(self):
        """Verify disabling survey, disables commcell in monitoring page"""
        self.private_metrics.disable_metrics()
        self.private_metrics.save_config()
        self.log.info("Disabled survey")
        self.log.info("Waiting for 2 minutes for the disable private survey xml to be processed")
        sleep(120)
        self.admin_console.browser.driver.refresh()
        self.admin_console.wait_for_completion()
        if not self.commcell_monitoring_page.is_commcell_disabled(self.uploading_cs.commserv_name):
            raise CVTestStepFailure("By disabling survey, Disabled icon is not present for [%s] "
                                    "CommCell" % self.uploading_cs.commserv_name)
        self.log.info("verified disabling survey,  disabled icon displayed in monitoring page")

    @test_step
    def verify_enable_survey(self):
        """Enabling survey, commcell is enabled in monitoring page"""
        self.private_metrics.enable_metrics()
        self.private_metrics.save_config()
        self.log.info("Enabled survey")
        self.log.info("Waiting for 2 minutes for the enable private survey xml to be processed")
        sleep(120)
        self.admin_console.browser.driver.refresh()
        self.admin_console.wait_for_completion()
        if self.commcell_monitoring_page.is_commcell_disabled(self.uploading_cs.commserv_name):
            raise CVTestStepFailure("By enabling survey, Disabled icon is still present for [%s] "
                                    "CommCell" % self.uploading_cs.commserv_name)
        self.log.info("verified enabling survey disabled icon disappeared in monitoring page")

    def initiate_private_upload(self):
        """Initiate private upload now"""
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    def create_non_admin_user(self):
        """create non admin user """
        role_name = "Report_Management_48268"
        # If user exists no need to create user/role.
        if not self.commcell.users.has_user(self.non_admin_user):
            self.log.info("Creating user [%s]", self.non_admin_user)
            self.commcell.users.add(user_name=self.non_admin_user,
                                    email="AutomatedUser@cvtest.com",
                                    password=self.non_admin_password
                                    )
        else:
            self.log.info("non admin user [%s] already exists", self.non_admin_user)
            return
        # Create role
        if not self.commcell.roles.has_role(role_name):
            self.commcell.roles.add(rolename=role_name, permission_list=["Report Management"])
        self.log.info("Non admin user [%s] is created", self.non_admin_user)

    @test_step
    def verify_delete_commcell_admin_user(self):
        """Delete commcell, verify commcell is deleted"""

        self.init_tc(self.webconsole_user_name, self.webconsole_password)
        self.log.info("Deleting [%s] commcell from commcell monitoring page with admin "
                      "user", self.commcell.commserv_name)
        self.metrics_commcell.delete(self.uploading_cs.commserv_name)
        if self.metrics_commcell.is_commcell_exist(self.uploading_cs.commserv_name):
            raise CVTestStepFailure("Failure to delete commcell with admin user. [%s]commcell "
                                    "exists in commcell monitoring "
                                    "page" % self.uploading_cs.commserv_name)
        self.log.info("[%s] commcell deleted successfully by admin "
                      "user", self.uploading_cs.commserv_name)

    @test_step
    def verify_commcell_rename(self):
        """
        verify update commcell name is working
        """
        self.metrics_commcell.access_commcell(self.cs_name[0])
        self.metrics_commcell.edit(self.new_commcell_name)
        if self.metrics_commcell.is_commcell_exist(self.new_commcell_name) is False:
            raise CVTestStepFailure("Failed to update commcell name, new commcell name [%s] is not "
                                    "exist in the commcell monitoring page" % self.new_commcell_name)

    @test_step
    def revert_commcell_name(self):
        """
        revert the commcell name
        """
        self.metrics_commcell.access_commcell(self.new_commcell_name)
        self.metrics_commcell.edit(self.cs_name[0])
        if self.metrics_commcell.is_commcell_exist(self.cs_name[0]) is False:
            raise CVTestStepFailure(f"Exported CommCell name [%s] but received [%s]"
                                    % (self.cs_name[0], self.new_commcell_name))

    @test_step
    def verify_delete_commcell_non_admin_user(self):
        """verify delete option does not exists for non admin user"""
        self.log.info("Deleting [%s] commcell from commcell monitoring page with [%s]"
                      "user", self.uploading_cs.commserv_name, self.non_admin_user)
        self.init_tc(user_name=self.non_admin_user, password=self.non_admin_password)
        actions = self.commcell_monitoring_page.get_commcell_action_options(
            commcell_name=self.uploading_cs.commserv_name)
        if ManageCommcells.CommcellActions.DELETE in actions:
            raise CVTestStepFailure("Delete option is available for non admin user [%s] "
                                    "in commcell monitoring page" % self.non_admin_user)
        self.log.info("Verified delete option is not available for not admin user ")
        Browser.close_silently(self.browser)

    def run(self):
        """ run method"""
        try:
            self.init_tc(self.webconsole_user_name, self.webconsole_password)
            self.associate_user_to_commcell()
            self.verify_commcell_rename()
            self.revert_commcell_name()
            self.verify_disable_survey()
            self.verify_enable_survey()
            Browser.close_silently(self.browser)
            self.verify_delete_commcell_non_admin_user()
            self.verify_delete_commcell_admin_user()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
            self.private_metrics.enable_metrics()
            self.private_metrics.save_config()
        finally:
            self.utils.private_metrics_upload()
            self.webconsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
