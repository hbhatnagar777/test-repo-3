import os

from cvpysdk.metricsreport import PrivateMetrics, CloudMetrics

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.metricsutils import MetricsServer
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """TestCase to validate Include/Exclude is honoured in metrics collection"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.private_metrics_machine = None
        self.public_metrics_machine = None
        self.public_excl_file = None
        self.public_incl_file = None
        self.private_excl_file = None
        self.private_incl_file = None
        self.public_metrics_server = None
        self.public_scripts_dir = None
        self.private_scripts_dir = None
        self.scripts_dir = None
        self.private_metrics_server = None
        self.cs_machine = None
        self.private_metrics = None
        self.private_metrics_name = None
        self.metrics_server = None
        self.name = "Verify Include/Exclude"
        self.public_metrics = None
        self.cs_machine = Machine()
        self.config = config.get_config()
        self.include_list = ["CommservSurveyQuery_54.sql",
                             "CommservSurveyQuery_117.sql",
                             "CommservSurveyQuery_161.sql",
                             "CommservSurveyQuery_181.sql"]
        self.exclude_list = ["CommservSurveyQuery_54.sql",
                             "CommservSurveyQuery_117.sql"]
        self.public_metrics_config = self.config.Cloud
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Intializes Private and Public metrics and Metrics Server Objects required for this testcase"""
        self.cs_machine = Machine(self.commcell.commserv_client)
        scripts_dir = self.cs_machine.join_path(self.commcell.commserv_client.install_directory,
                                                "Reports", "CommservSurvey")
        self.private_scripts_dir = self.cs_machine.join_path(scripts_dir, "private")
        self.public_scripts_dir = self.cs_machine.join_path(scripts_dir, "public")
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                                    self.inputJSONnode['commcell']["commcellUsername"],
                                                    self.inputJSONnode['commcell']["commcellPassword"])
        self.private_metrics_machine = self.private_metrics_server.metrics_machine

        self.public_metrics = CloudMetrics(self.commcell)
        self.public_metrics_server = MetricsServer(self.public_metrics_config.host_name,
                                                   self.public_metrics_config.username,
                                                   self.public_metrics_config.password)
        #self.public_metrics_machine = self.public_metrics_server.metrics_machine

    def get_queries_from_private_metrics_upload(self):
        """ Private Metrics UploadNow operation and returns list of all queries executed """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')
        archive_dir = self.private_metrics_server.archive_dir
        filename = self.private_metrics.get_uploaded_filename()
        self.log.info(f"Last Uploaded XML File is {filename}")
        file_path = self.private_metrics_machine.join_path(archive_dir, filename)
        self.private_metrics_server.wait_for_xml_parsing(filename)
        query_list = self.private_metrics_server.get_queryids_from_uploaded_xml(file_path)
        return query_list

    def get_queries_from_public_metrics_upload(self):
        """ Public Metrics UploadNow operation and returns list of all queries executed  """
        self.log.info('Initiating Public Metrics upload now')
        self.public_metrics.upload_now()
        self.public_metrics.wait_for_uploadnow_completion()
        self.log.info('Public Metrics upload now completed Successfully')
        archive_dir = self.public_metrics_server.archive_dir
        filename = self.public_metrics.get_uploaded_filename()
        file_path = os.path.join(archive_dir, filename)
        self.log.info(f"Last Uploaded XML File is {filename}")
        self.public_metrics_server.wait_for_xml_parsing(filename)
        query_list = self.public_metrics_server.get_queryids_from_uploaded_xml(file_path)
        return query_list

    def verify_include_honoured(self, query_list, incl_list):
        """ Verifies Include list is same as Queries executed"""
        incl_list.extend(["CommservSurveyQuery_2.sql", "CommservSurveyQuery_1.sql", "CommservSurveyQuery_57.sql"])
        incl_set = set(incl_list)
        query_set = set(query_list)
        if not (incl_set == query_set):
            self.log.info("Queries Present in Include file " + str(incl_set))
            self.log.info("Queries Prsent in Uploaded XML " + str(query_set))
            return False
        return True

    def verify_exclude_honoured(self, query_list, excl_list):
        """ Verifies Exclude list is honoured duting metrics collection"""
        excl_set = set(excl_list)
        query_set = set(query_list)
        if not excl_set.isdisjoint(query_set):
            self.log.info("Queries Present in Exclude file " + str(excl_set))
            self.log.info("Queries Prsent in Uploaded XML " + str(query_set))
            return False
        return True

    @test_step
    def check_private_include(self):
        """ Checks for Private Metrics Include """
        self.private_incl_file = self.cs_machine.join_path(self.private_scripts_dir, 'MetricsInclude.txt')
        if self.cs_machine.check_file_exists(self.private_incl_file):
            self.cs_machine.delete_file(self.private_incl_file)
        incl_string = r'\n'.join(self.include_list)
        self.cs_machine.create_file(self.private_incl_file, incl_string)
        query_list = self.get_queries_from_private_metrics_upload()
        if not self.verify_include_honoured(query_list, self.include_list):
            raise CVTestStepFailure("Private Include is not honoured")
        self.log.info("Private Include is honoured")
        self.cs_machine.delete_file(self.private_incl_file)

    @test_step
    def check_private_exclude(self):
        """ Checks for Private Metrics Exclude """
        self.private_excl_file = self.cs_machine.join_path(self.private_scripts_dir, 'MetricsExclude.txt')
        if self.cs_machine.check_file_exists(self.private_excl_file):
            self.cs_machine.delete_file(self.private_excl_file)
        excl_string = r'\n'.join(self.exclude_list)
        self.cs_machine.create_file(self.private_excl_file, excl_string)
        query_list = self.get_queries_from_private_metrics_upload()
        if not self.verify_exclude_honoured(query_list, self.exclude_list):
            raise CVTestStepFailure("Private Exclude is not honoured")
        self.log.info("Private Exclude is honoured")
        self.cs_machine.delete_file(self.private_excl_file)

    @test_step
    def check_public_include(self):
        """ Checks for Public Metrics Include """
        self.public_incl_file = self.cs_machine.join_path(self.public_scripts_dir, 'MetricsInclude.txt')
        if self.cs_machine.check_file_exists(self.public_incl_file):
            self.cs_machine.delete_file(self.public_incl_file)
        incl_string = r'\n'.join(self.include_list)
        self.cs_machine.create_file(self.public_incl_file, incl_string)
        query_list = self.get_queries_from_public_metrics_upload()
        if not self.verify_include_honoured(query_list, self.include_list):
            raise CVTestStepFailure("Public Include is not honoured")
        self.log.info("Public Include is honoured")
        self.cs_machine.delete_file(self.public_incl_file)

    @test_step
    def check_public_exclude(self):
        """ Checks for Public Metrics Exclude """
        self.public_excl_file = self.cs_machine.join_path(self.public_scripts_dir, 'MetricsExclude.txt')
        if self.cs_machine.check_file_exists(self.public_excl_file):
            self.cs_machine.delete_file(self.public_excl_file)
        excl_string = r'\n'.join(self.exclude_list)
        self.cs_machine.create_file(self.public_excl_file, excl_string)
        query_list = self.get_queries_from_public_metrics_upload()
        if not self.verify_exclude_honoured(query_list, self.exclude_list):
            raise CVTestStepFailure("Public Exclude is not honoured")
        self.log.info("Public Exclude is honoured")
        self.cs_machine.delete_file(self.public_excl_file)

    @test_step
    def check_private_include_and_exclude(self):
        """ Checks for Private Metrics Exclude/Include """
        excl_string = r'\n'.join(self.exclude_list)
        self.cs_machine.create_file(self.private_excl_file, excl_string)
        incl_string = r'\n'.join(self.include_list)
        self.cs_machine.create_file(self.private_incl_file, incl_string)
        query_list = self.get_queries_from_private_metrics_upload()
        if not self.verify_exclude_honoured(query_list, self.exclude_list):
            raise CVTestStepFailure("Private Exclude is not honoured when both Include/Exclude is present")
        self.log.info("Private Exclude is honoured when both Include/Exclude is present")

    def run(self):
        try:
            self.check_private_exclude()
            self.check_private_include()
            self.check_public_exclude()
            self.check_public_include()
            self.check_private_include_and_exclude()

        except Exception as error:
            self.utils.handle_testcase_exception(error)

        finally:
            self.cs_machine.delete_file(self.private_excl_file)
            self.cs_machine.delete_file(self.private_incl_file)
            self.cs_machine.delete_file(self.public_incl_file)
            self.cs_machine.delete_file(self.public_excl_file)
