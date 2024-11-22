""""
TestCase to validate Metrics Data Collection Window configuration.
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure

from cvpysdk.metricsreport import PrivateMetrics

from datetime import datetime
from time import sleep


class TestCase(CVTestCase):
    """TestCase to validate Metrics Data Collection Window configuration"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Data Collection Window Validation"
        self.private_metrics = None
        self.utils = TestCaseUtils(self)
        self.last_collection_time = None

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_metrics()
        self.private_metrics.set_upload_freq(1)
        self.last_collection_time = self.private_metrics.lastcollectiontime

    def push_last_collection_time(self):
        """set last collection time to an hour before"""
        self.log.info("set Private last collection time to an hour before")
        cmd = "-sn SetKeyIntoGlobalParamTbl.sql -si CommservSurveyPrivateLastCollectionTime " \
            f"-si y -si {self.private_metrics.lastcollectiontime - 4600}"
        self.commcell._qoperation_execscript(cmd)
        self.private_metrics.refresh()

    @test_step
    def set_dc_window(self):
        """Sets DC windows for private metrics server"""
        current_seconds = datetime.now().time().hour * 3600 + datetime.now().time().minute * 60
        dc_seconds = current_seconds + 900  # setting dc windows for 15 minutes later (15*60)
        self.log.info("Setting DC window to 15 minutes later")
        self.private_metrics.set_data_collection_window(dc_seconds)
        self.private_metrics.save_config()

    @test_step
    def validate_collection_execution(self):
        """Validates Collection window is honored"""
        self.private_metrics.refresh()
        if self.last_collection_time < self.private_metrics.lastcollectiontime:
            self.log.info("DC window honored, collection happened during DC window period")
        else:
            self.log.error(f"Collection time before window set : {self.last_collection_time}")
            self.log.error(f"Current Collection time : {self.private_metrics.lastcollectiontime}")
            raise CVTestStepFailure("Collection didnt happen during DC window period")

    def run(self):
        try:
            self.push_last_collection_time()
            self.set_dc_window()
            self.log.info('Wait for an hour')
            sleep(3600)
            self.validate_collection_execution()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.private_metrics.remove_data_collection_window()
            self.private_metrics.save_config()
