from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.unix_machine import UnixMachine

class TestCase(CVTestCase):
    """Hyperscale test class for HSX 3.x non-root user / cvbackupadmin user validations for Smoke Testing"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX 3.x non-root user / cvbackupadmin user validations for Smoke Testing"
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

        self.node_user = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]
        self.mas = self.tcinputs["Nodes"]
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")

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
            
            # Non-root user validations
            self.log.info(f"Validating non-root user")
            for ma_name in self.mas:
                self.log.info(f"Creating machine object with {self.node_user} for {ma_name}")
                try:
                    _ = UnixMachine(ma_name, username=self.node_user, password=self.node_password)
                    self.log.info(f"Successfully validated {self.node_user} user exists on {ma_name}")
                except Exception as e:
                    reason = f"{self.node_user} user validation failed on {ma_name}. {e}"
                    return self.fail_test_case(reason)
                    

            self.successful = True
            self.log.info(f"Non-root user validated successfully on all nodes")


        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)