# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate Basic operation window Aux copy,disaster recovery features at Commcell level

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from Server.OperationWindow.ophelper import OpHelper
from Server.OperationWindow.opvalidate import OpValidate


class TestCase(CVTestCase):
    """Class for executing Basic operation window Aux copy,disaster recovery features validation at Commcell level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance] : Basic operation window Aux copy,disaster recovery features validation at" \
                    " Commcell level"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.show_to_user = False

    def run(self):
        """
        Main function for test case execution
        Follows the following steps
                1) Creates required entities: disklibrary, storagepolicy, subclient
                2) Creates an operation window at Commserv level for a list of operations: ["AUX_COPY", "DR_BACKUP"]
                3) Validates each feature present in the list of operations
                4) The feature triggered job should honor the created operation window i.e., job should be queued
                5) If successfully queued, Modify the operation window to allow the job to run.
                6) Checks whether the job is running state or not
                7) Repeats 3,4,5 steps for every feature present in list of operations
                8) Testcase will be successful if all the above steps are executed without exceptions
                9) Deletes the created operation window
        """
        try:
            operations_list = ["AUX_COPY", "DR_BACKUP"]

            self.log.info("Validating commcell level operation window for the features:%s",
                          operations_list)

            self.log.info("Initialising the subclient that honors the operation window")
            entities = CVEntities(self)
            entity_props = entities.create(["disklibrary", "storagepolicy", "subclient"])
            self.subclient = entity_props['subclient']['object']
            op_window = OpHelper(self, self.commcell)
            self.log.info("Initialised the operation window successfully")

            op_rule = op_window.testcase_rule(operations_list)

            op_val = OpValidate(self, op_rule)

            op_val.validate(features=operations_list)

        except Exception as excp:
            self.log.error('Test case failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            op_window.delete(name=self.name)
            entities.delete(entity_props)
