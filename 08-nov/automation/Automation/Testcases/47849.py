""""
TestCase to validate Metrics Randomization feature.
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure

from cvpysdk.metricsreport import CloudMetrics

from time import sleep


class TestCase(CVTestCase):
    """TestCase to validate Metrics Randomization feature"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Randomization feature"
        self.cloud_metrics = None
        self.utils = TestCaseUtils(self)
        self.last_upload_time = None
        self.last_download_time = None

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.cloud_metrics = CloudMetrics(self.commcell)
        self.cloud_metrics.enable_metrics()
        self.last_download_time = self.cloud_metrics.lastdownloadtime
        self.last_upload_time = self.cloud_metrics.lastuploadtime

    def int_tc(self):
        """Testcase intialization checks"""
        if self.last_download_time == 0:
            self.log.info("last download time is 0 intiating Cloud metrics upload")
            self.cloud_metrics.upload_now()
            self.cloud_metrics.wait_for_uploadnow_completion()
        if self.cloud_metrics.randomization_minutes != 0:
            self.log.info("Randomization value is nonzero setting it to 0")
            self.set_randomization_time(0)
        self.cloud_metrics.refresh()
        self.last_download_time = self.cloud_metrics.lastdownloadtime
        self.log.info(f"Current last download time {self.last_download_time}")

    def set_randomization_time(self, value):
        """set randomization value"""
        cmd = "-sn SetKeyIntoGlobalParamTbl.sql -si CommservSurveyRandomizationEnabled " \
              f"-si y -si {value}"
        exec_command = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.commcell._cvpysdk_object.make_request("POST", exec_command)

    @test_step
    def set_lesser_downloadtime(self):
        """Sets downloadtime for public metrics to a lower value"""
        temp_time = self.last_download_time - 200
        self.log.info(f"setting last download time to {temp_time}")
        cmd = "-sn SetKeyIntoGlobalParamTbl.sql -si CommservSurveyLastScriptDownloadTime " \
              f"-si y -si {temp_time}"
        exec_command = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.commcell._cvpysdk_object.make_request("POST", exec_command)
        self.cloud_metrics.refresh()

    @test_step
    def validate_randomization_set(self):
        """Validates randomization set and upload not initiated"""
        self.cloud_metrics.refresh()
        if self.cloud_metrics.lastdownloadtime < self.last_download_time:
            raise CVTestStepFailure(
                f"Public download time [{self.cloud_metrics.lastdownloadtime}]is still less than "
                f"the download time recoreded initally [{self.last_download_time}]."
            )
        if self.cloud_metrics.randomization_minutes == 0:
            raise CVTestStepFailure("Randomization value not set")
        if self.cloud_metrics.lastuploadtime > self.last_upload_time:
            raise CVTestStepFailure(
                "upload seem to have been initatied but should have been skipped "
                f"Current upload time [{self.cloud_metrics.lastuploadtime}] and"
                f"upload time recorded intially [{self.last_upload_time}]"
            )
        self.log.info(
            f"Randomization is properly set to [{self.cloud_metrics.randomization_minutes}]"
            f" and download initiated but not upload"
        )

    @test_step
    def validate_post_randomization(self):
        """Validates upload initiated and randomization is reset"""
        self.cloud_metrics.refresh()
        if self.cloud_metrics.randomization_minutes != 0:
            raise CVTestStepFailure("Randomization value not set to 0")
        if self.cloud_metrics.lastuploadtime <= self.last_upload_time:
            raise CVTestStepFailure(
                "upload seem to have been not initatied"
                f"Current upload time [{self.cloud_metrics.lastuploadtime}] and"
                f"upload time recorded initially [{self.last_upload_time}]"
            )

    def is_survey_thread_triggered(self):
        """Checks survey thread triggered"""
        self.cloud_metrics.refresh()
        if self.cloud_metrics.lastdownloadtime < self.last_download_time:
            return False
        return True

    def run(self):
        try:
            self.int_tc()
            self.set_lesser_downloadtime()
            self.log.info('Wait till survey thread triggered for maximum of hour')
            maxtime = 3600
            time = 0
            while time < maxtime:
                if not self.is_survey_thread_triggered():
                    self.log.info('Survey thread not triggered waiting for 10 minutes')
                    sleep(600)
                    time = time + 600
                else:
                    self.log.info('Survey thread triggered')
                    break
            self.validate_randomization_set()
            self.log.info("Setting Randomization time to 20")
            self.set_randomization_time(20)
            self.log.info('Wait for an hour')
            sleep(3600)
            self.validate_post_randomization()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.cloud_metrics.remove_data_collection_window()
            self.cloud_metrics.save_config()
