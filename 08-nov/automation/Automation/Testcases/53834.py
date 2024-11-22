# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: verify strike count takes priority on estimated Job run time

"""
import sys

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.rpo_helper import RpoHelper
from Server.JobManager.rpo_helper import RPOBasedSubclient as RpoSubClientHelper
from Server.JobManager.rpo_constants import RPO_ADDITIONAL_SETTING_KEY


class TestCase(CVTestCase):
    """Class for executing verification test for strike count takes priority on
       estimated Job run time"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify strike count takes priority on estimated job run time"
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
        self.tcinputs['SubclientCount'] = 2

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.server = ServerTestCases(self)

        self.log.info("creating RPO helper instance")
        self.rpo_helper_obj = RpoHelper(self.commcell,
                                        self.tcinputs['ClientName'],
                                        self.tcinputs['MediaAgent'],
                                        self.tcinputs['StoragePolicy'])

        self.log.info("creating %s subclients", self.tcinputs['SubclientCount'])
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("creating RPO subclient helper instance for %s",
                          "rposubclient" + str(count))
            rpo_subclient = RpoSubClientHelper(self.rpo_helper_obj,
                                               "rposubclient" + str(count))
            self.sc_instances.append(rpo_subclient)

        file_size = (10*1024)  # size in KB
        num_backups = 220
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("running backup jobs to achieve estimated job "
                          "run time for subclient %s", self.sc_instances[count])
            self.sc_instances[count].force_estimated_runtime(num_backups, file_size)
            file_size = file_size - (5*1024)

        strike_count = 3
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("setting strike count %s for subclient%s", strike_count, count)
            self.sc_instances[count].force_strike_count(strike_count)
            strike_count += 1

    def run(self):
        """Main function for test case execution"""
        try:
            self.rpo_helper_obj.validate_rsc_alloc_order(self.sc_instances)
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.sc_instances[count].cleanup()

        self.log.info("deleting registry key %s for commcell", RPO_ADDITIONAL_SETTING_KEY)
        self.commcell.delete_additional_setting('CommServe', RPO_ADDITIONAL_SETTING_KEY)


