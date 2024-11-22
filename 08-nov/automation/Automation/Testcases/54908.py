# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
TestCase to validate Private Metrics and cloud UploadNow operation from Command Center

TestCase:
    validate_private_uploadnow()    --  Validates Private Metrics uploadNow operation

    run()           -               --  run function of this test case
"""
import dateutil.parser

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.metrics_reporting import (
    RemotePrivateMetrics,
    CloudMetrics
)

from cvpysdk.metricsreport import PrivateMetrics as SdkPrivate
from cvpysdk.metricsreport import CloudMetrics as SdkCloud

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)


class TestCase(CVTestCase):
    """TestCase to validate Private Metrics UploadNow operation from CommServe"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Command Center: Metrics Private and cloud Upload Now"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            navigator = self.admin_console.navigator
            navigator.navigate_to_metrics_reporting()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def validate_private_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        private_metrics = RemotePrivateMetrics(self.admin_console)
        readable_date = private_metrics.last_upload_time
        last_upload_time = int(
            dateutil.parser.parse(private_metrics.last_upload_time, dayfirst=True).timestamp()
        )
        private_metrics.upload_now()
        sdk_private_metrics = SdkPrivate(self.commcell)
        sdk_private_metrics.wait_for_uploadnow_completion()
        private_metrics.reload_data()
        readable_date_new = private_metrics.last_upload_time
        new_upload_time = int(
            dateutil.parser.parse(private_metrics.last_upload_time, dayfirst=True).timestamp()
        )
        if new_upload_time < last_upload_time:
            raise CVTestStepFailure(
                "Last upload time didnt change after upload completed. Time before upload "
                f"[{readable_date}], time after upload [{readable_date_new}]"
            )
        self.log.info('Private Metrics upload now completed Successfully')
        if private_metrics.download_url != sdk_private_metrics.downloadurl:
            raise CVTestStepFailure(
                f"Download url is not the one in DB, in browser [{private_metrics.download_url}],"
                f" from sdk [{sdk_private_metrics.downloadurl}]"
            )

    @test_step
    def validate_cloud_uploadnow(self):
        """Validates Cloud Metrics uploadNow operation """
        cloud_metrics = CloudMetrics(self.admin_console)
        readable_date = cloud_metrics.last_upload_time
        last_upload_time = int(
            dateutil.parser.parse(cloud_metrics.last_upload_time, dayfirst=True).timestamp()
        )
        cloud_metrics.upload_now()
        sdk_cloud_metrics = SdkCloud(self.commcell)
        sdk_cloud_metrics.wait_for_uploadnow_completion()
        cloud_metrics.reload_data()
        readable_date_new = cloud_metrics.last_upload_time
        new_upload_time = int(
            dateutil.parser.parse(cloud_metrics.last_upload_time, dayfirst=True).timestamp()
        )
        if new_upload_time < last_upload_time:
            raise CVTestStepFailure(
                "Last upload time didnt change after upload completed. Time before upload "
                f"[{readable_date}], time after upload [{readable_date_new}]"
            )
        self.log.info('Private Metrics upload now completed Successfully')
        self.log.info('Cloud Metrics upload now completed Successfully')

    def run(self):
        try:
            self.init_tc()
            self.validate_private_uploadnow()
            self.validate_cloud_uploadnow()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
