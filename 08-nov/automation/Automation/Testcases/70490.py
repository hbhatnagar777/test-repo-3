""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Plans.planshelper import PlansHelper
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Entity Caching] - validate the data for plans entity"
        self.tcinputs = {
            'fq_filter': None,
            'expected_result': None
        }
        self._helper = None

    def setup(self):
        """Setup function of this test case"""
        self._helper = PlansHelper(commcell_obj=self.commcell)

    def run(self):
        """ run function of this test case """
        try:
            self._helper.validate_plans_cache_data()

            self._helper.validate_sort_on_cached_data()

            self._helper.validate_limit_on_cache()

            self._helper.validate_search_on_cache()

            self._helper.validate_filters_on_cache(filters=self.tcinputs['fq_filter'],
                                                   expected_response=self.tcinputs['expected_result'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._helper.cleanup_plans('caching_automation_')

