"""Test Case to trigger unplanned failover

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case
"""

import time
from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from Server.CVFailover import cvfailover
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test case class for invoking maintenance failover"""

    def __init__(self):
        super().__init__()
        self.name = ("Regression test case for CVFailover - Production Unplanned")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "productionSQL": None,
            "webconsole": None,
            "drsql": None
        }

    def run(self):
        """ Main function for test case execution.
        This Method creates cvfailover objects to perform cvfailover.
        """
        try:

            # Getting TCInputs from JSON.
            productionSQL = self.tcinputs["productionSQL"]
            drsql = self.tcinputs["drsql"]

            # Shutting down the Active Host.
            activesqlclient = Client(self.commcell, productionSQL)
            drsqlclient = Client(self.commcell, drsql)
            drsqlpath = drsqlclient.install_directory
            machine_obj = Machine(activesqlclient)
            machine_obj.shutdown_client()

            # Checking if Active machine turned off properly, before initiating Unplanned Fail-over
            is_alive = False
            while is_alive is False:
                ret_code = machine_obj.execute_command("ipconfig /all")
                if ret_code == 0:
                    time.sleep(25)
                elif ret_code != 0:
                    is_alive = True
                    time.sleep(25)
            # Log-on to DR_CS and perform Unplanned Fail-over:

            self.log.info("Active machine turned off succesfully, initiating Unplanned Failover")
            cvfailoverobj = cvfailover.CVFailoverHelper(drsql, op_type="Production", log=self.log)
            cvfailoverobj.path = drsqlpath
            cvfailoverobj.run_cvfailover()

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
