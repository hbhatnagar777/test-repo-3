# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Verifies RPO driven backup Job honour's Job strike count

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.rpo_helper import RpoHelper
from Server.JobManager.rpo_helper import RPOBasedSubclient as RpoSubClientHelper
from Server.JobManager.rpo_constants import RPO_ADDITIONAL_SETTING_KEY


class TestCase(CVTestCase):
    """Class for executing verification test for RPO driven backup based on strike count"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "verify Jobs with higher strike count are prioritized"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.JOBMANAGEMENT
        self.show_to_user = True
        self.retval = 0
        self.tcinputs = {
            'ClientName': None,  # client name where subclient will be created
            'MediaAgent': None,  # media agent where disk library is created
            'SubclientCount': None,  # number of subclient to be created in testing the scenario
            'StoragePolicy': None  # storage policy with stream count '1' to be associated with subclients
        }
        self.sc_instances = []
        self.rpo_helper_obj = None
        self.server = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.server = ServerTestCases(self)

        self.log.info("creating RPO helper instance")
        self.rpo_helper_obj = RpoHelper(self.commcell,
                                        self.tcinputs['ClientName'],
                                        self.tcinputs['MediaAgent'],
                                        self.tcinputs['StoragePolicy'])

        self.log.info("creating {0} subclients".format(self.tcinputs['SubclientCount']))
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("creating RPO subclient helper instance for {0}".format(
                "rposubclient" + self.id + str(count)))
            rpo_subclient = RpoSubClientHelper(self.rpo_helper_obj,
                                               "rposubclient" + self.id + str(count))
            self.sc_instances.append(rpo_subclient)

        strike_count = 3
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("setting strike count {0} for subclient{1}".format(
                strike_count, count))
            self.sc_instances[count].force_strike_count(strike_count)
            strike_count += 1

    def run(self):
        """Main function for test case execution"""
        try:
            self.rpo_helper_obj.validate_rsc_alloc_order(self.sc_instances)
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.sc_instances[count].cleanup()

        self.log.info("deleting registry key %s for commcell", RPO_ADDITIONAL_SETTING_KEY)
        self.commcell.delete_additional_setting('CommServe', RPO_ADDITIONAL_SETTING_KEY)
