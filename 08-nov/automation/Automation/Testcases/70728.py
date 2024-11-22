from typing import Dict
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.unix_machine import UnixMachine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper

class TestCase(CVTestCase):
    """Hyperscale test class for HSX 3.x RWP validations for Smoke Testing"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX 3.x RWP validations for Smoke Testing"
        self.result_string = ""
        self.mas = []
        self.hyperscale_helper = None
        self.tcinputs = {
            "Nodes": [
            ],
            "NodeUser": None,
            "NodePassword": None
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        
        # MA setup
        self.node_user = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]
        self.mas = self.tcinputs["Nodes"]
        self.ma_machines: Dict[str, UnixMachine] = {}
        self.rw_helpers: Dict[str, UnixRansomwareHelper] = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = UnixMachine(ma_name, username=self.node_user, password=self.node_password)
            self.ma_machines[ma_name] = machine
            self.rw_helpers[ma_name] = UnixRansomwareHelper(machine, self.commcell, self.log)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case failed")
            self.status = constants.FAILED

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def run(self):
        """ run function of this test case"""
        try: 
            
            # RWP validations
            self.log.info(f"Validating ransomware protection")
            result, reason = UnixRansomwareHelper.hsx_rwp_validation_suite(self.mas,self.ma_machines,self.hyperscale_helper,self.rw_helpers)
            if not result: 
                reason += f"RWP validations failed"
                return self.fail_test_case(reason)

            self.successful = True
            self.log.info(f"Ransomware protection validated successfully")


        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)