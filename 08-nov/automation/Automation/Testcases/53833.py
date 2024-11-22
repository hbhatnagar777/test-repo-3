# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Verifies RPO driven backup Job honour's Job Estimated run time

"""
import sys
import random
import string

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.JobManager.rpo_helper import RpoHelper
from Server.JobManager.rpo_helper import RPOBasedSubclient as RpoSubClientHelper
from Server.JobManager.rpo_constants import RPO_ADDITIONAL_SETTING_KEY


class TestCase(CVTestCase):
    """Class for executing verification test for RPO driven backup based on Estimated run time"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "verify Job estimation run time takes priority in resource allocation."
        self.retval = 0
        self.tcinputs = {
            'ClientName': None,  # client name where subclient will be created
            'MediaAgent': None,  # media agent where disk library is created
            'SubclientCount': None,  # number of subclient to be created in testing the scenario
            'StoragePolicy': None # storage policy with stream count '1' to be associated with subclients
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

        self.log.info("creating %s subclients", self.tcinputs['SubclientCount'])
        rand_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))

        for count in range(int(self.tcinputs['SubclientCount'])):
            sc_name = "subclientrpo-" + rand_string + "-" + self.id + "-" + str(count)
            self.log.info("creating RPO subclient helper instance for %s", sc_name)
            rpo_subclient = RpoSubClientHelper(self.rpo_helper_obj, sc_name)
            self.sc_instances.append(rpo_subclient)

        file_size = (5*1024)
        num_backups = 220
        for count in range(int(self.tcinputs['SubclientCount'])):
            self.log.info("running backup jobs to achieve estimated job "
                          "run time for subclient %s", self.sc_instances[count].subclient_name)
            self.sc_instances[count].force_estimated_runtime(num_backups, file_size)
            file_size = file_size * 2

    def run(self):
        """Main function for test case execution"""
        try:
            self.rpo_helper_obj.validate_rsc_alloc_order(self.sc_instances)

            message = "subtest : estimated run time verification is successful".center(70, '-')
            self.log.info(message)

            strike_count = 2
            for count in range(int(self.tcinputs['SubclientCount'])):
                self.log.info("setting strike count %s for subclient%s", strike_count, count)
                self.sc_instances[count].force_strike_count(strike_count)
                strike_count += 1

            self.rpo_helper_obj.validate_rsc_alloc_order(self.sc_instances)

            message = "subtest : strike count is prioritized over ECT is successful".center(70, '-')
            self.log.info(message)

            # we will not delete subclient instances in case of any exceptions to debug
            # as it is very difficult to reproduce the setup
            for count in range(int(self.tcinputs['SubclientCount'])):
                self.sc_instances[count].cleanup()

            self.log.info("deleting registry key %s for commcell", RPO_ADDITIONAL_SETTING_KEY)
            self.commcell.delete_additional_setting('CommServe', RPO_ADDITIONAL_SETTING_KEY)
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.rpo_helper_obj.start_ma_services()
        self.rpo_helper_obj.commserv_machine_obj.set_logging_debug_level("EvMgrs", "0")




