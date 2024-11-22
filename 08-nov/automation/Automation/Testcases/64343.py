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
from Web.Common.page_object import handle_testcase_exception
from Server import mongodb_helper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.name = "MongoDB: MongoDB working and CommcellEntityCache hard refresh"
        self.tcinputs = {
            "machine_name":None,
            "mongodb_password":None
        }

    def setup(self):
        """Setup function of this test case"""
        self.mongodb = mongodb_helper.MongoDBHelper(self.commcell, self.tcinputs["machine_name"],
                                                    self.tcinputs["mongodb_password"])

    def run(self):
        """ run function of this test case """
        try:
            self.mongodb.validate_service_status()
            self.mongodb.validate_check_readiness()
            if self.mongodb.connection:
                self.mongodb.validate_entity_cache()

        except Exception as exp:
            handle_testcase_exception(self,exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.mongodb.connection.close()
        self.commcell.logout()

