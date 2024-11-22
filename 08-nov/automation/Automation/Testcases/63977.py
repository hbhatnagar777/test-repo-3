# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from dynamicindex.index_server_helper import IndexServerHelper
from Web.Common.page_object import TestStep
from dynamicindex.utils import constants as dynamic_constants


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()
    indicator_type = "mem"

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Index Server - Health Indicators - Validate JVM Based Indicators"
        self.tcinputs = {
            "IndexServer": None
        }
        self.machine_obj = None
        self.index_server_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])

    @test_step
    def validate_defaults(self, thresholds):
        """Validate default indicator values"""
        if len(thresholds) > 0:
            for key in thresholds.keys():
                if key == self.indicator_type:
                    current_values = {}
                    current_values = eval(thresholds[key])
                    for value in current_values.keys():
                        if not self.index_server_helper.validate_default_indicators(self.indicator_type, value,
                                                                                    current_values[value]):
                            self.log.error("Default Indicator values are not matched for indicator [{}]".format(value))
                            self.log.error("Default Indicator values are not matched")

    @test_step
    def validate_indicator_override(self):
        """Validate change of indicator via additional setting"""
        thresholds = {}
        action_codes = {}
        current_action_code = None
        thresholds, action_codes = self.index_server_helper.get_index_server_health_summary()
        if len(action_codes) > 0:
            current_action_code = int(list(action_codes.keys())[0])
            if current_action_code > 0:
                raise CVTestStepFailure(
                    "Action code is already set, can not verify further. Please check index server state")
        self.index_server_helper.set_validate_memory_indicator()
        self.index_server_helper.wait_for_summary_doc_sync(extended_wait=True)
        thresholds, action_codes = self.index_server_helper.get_index_server_health_summary()
        if len(action_codes) > 0:
            current_action_code = int(list(action_codes.keys())[0])
            if current_action_code == dynamic_constants.INDEX_SERVER_HEALTH_ACTION_CODE_MEM_HIGH_INCREASE_JVM_HEAP:
                self.log.info('Action code [{}] with '
                              'description [{}] '
                              'is set correctly'.format(current_action_code,
                                                        action_codes[
                                                            str(current_action_code)]))
            else:
                raise CVTestStepFailure(
                    "Expected action code [{}] is not set".format(
                        dynamic_constants.INDEX_SERVER_HEALTH_ACTION_CODE_MEM_HIGH_INCREASE_JVM_HEAP))

    @test_step
    def cleanup(self, post_cleanup=False):
        """Cleanup of health indicators"""
        try:
            self.log.info(
                'Index Server Client Name [{}]'.format(self.index_server_helper.index_server_obj.client_name[0]))
            self.index_server_helper.check_and_remove_indicators(
                dynamic_constants.ANALYTICS_REG_KEY,
                dynamic_constants.INDEX_SERVER_HEALTH_MEM_USAGE_PERCENTAGE_THRESHOLD)
            self.index_server_helper.check_and_remove_indicators(
                dynamic_constants.ANALYTICS_REG_KEY,
                dynamic_constants.INDEX_SERVER_HEALTH_MEM_EXCEEDED_TIME)
            self.index_server_helper.check_and_remove_indicators(
                dynamic_constants.ANALYTICS_REG_KEY,
                dynamic_constants.INDEX_SERVER_HEALTH_MEM_BYTES_THRESHOLD)
            self.index_server_helper.wait_for_summary_doc_sync()
            if post_cleanup:
                self.index_server_helper.cleanup_monitoring(indicator_type=self.indicator_type)
                self.index_server_helper.check_and_remove_indicators(
                    dynamic_constants.SOLR_CONFIG_REG_KEY_PATH,
                    dynamic_constants.INDEX_SERVER_HEALTH_SUMMARY_DOC_TRIGGER_INTERVAL)
                self.index_server_helper.check_and_remove_indicators(
                    dynamic_constants.SOLR_CONFIG_REG_KEY_PATH,
                    dynamic_constants.INDEX_SERVER_HEALTH_RUN_SCHEDULER_AT_INTERVAL)
        except CVTestStepFailure as error:
            self.log.error('Cleanup failed due to [{}]'.format(error))
        finally:
            if post_cleanup:
                self.index_server_helper.manage_index_server_access_control(enable=True)

    def run(self):
        """Run function of this test case"""
        thresholds = {}
        action_codes = {}
        try:
            if self.index_server_helper is not None:
                self.cleanup()
                self.index_server_helper.set_index_server_health_environment()
                thresholds, action_codes = self.index_server_helper.get_index_server_health_summary()
                self.validate_defaults(thresholds)
                self.validate_indicator_override()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('Finishing up.')
        self.cleanup(post_cleanup=True)
