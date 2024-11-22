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

    run()           --  run function of this test case
"""

import re
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Azure auto scale validation
    with failed VMManagement job"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Auto Scale Validation for failed VMManagement job"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.tc_utils.initialize(self)
                _adv = {"create_backup_copy_immediately": True}
                self.tc_utils.run_auto_scale_validation(self, backup_type="INCREMENTAL")

            except Exception as err:
                self.log.error(err)
                if re.search("VMManagement job [0-9]+ has failed", str(err)):
                    if re.search("Resource.* is not cleaned up", str(err)):
                        raise Exception("Resource clean up failed for failed VMManagement job")
                    if re.search("Client not deleted from Commcell", str(err)):
                        raise Exception("Client not deleted from Commcell for failed VMManagement job")

                else:
                    raise Exception("No VMManagement failed.")

                self.ind_status = True
                self.failure_msg = ""

        except Exception as err:
            self.log.error(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            self.failure_msg = str(err)

        finally:
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
