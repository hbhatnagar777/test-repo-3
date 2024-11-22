# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate Basic operation window Aux copy,disaster recovery features at Commcell level for weekly rule
with do not submit job enabled

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from Server.OperationWindow.ophelper import OpHelper
from Server.OperationWindow.opvalidate import OpValidate
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Basic operation window Aux copy,disaster recovery features validation at Commcell level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Functional] : Basic operation window Aux copy,disaster recovery features validation at " \
                    "commserv level for weekly rule with do not submit job enabled"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.show_to_user = False
        self.op_window, self.entities, self.entity_props = None, None, None
        self.server = None

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
            self.server = ServerTestCases(self)
            self.entities = CVEntities(self)
            self.entity_props = self.entities.create(["disklibrary", "storagepolicy", "subclient"])
            self.subclient = self.entity_props['subclient']['object']
            self.op_window = OpHelper(self, self.commcell)
            self.log.info("Initialised the operation window successfully")

            machine = Machine(self.commcell.commserv_name, self.commcell)
            op_rule = self.op_window.weekly_rule(operations_list, machine, do_not_submit_job=True)
            op_val = OpValidate(self, op_rule)
            op_val.validate(features=operations_list)

        except Exception as excp:
            self.server.fail(excp)
        finally:
            self.op_window.delete(name=self.name)
            try:
                self.entities.delete(self.entity_props)
            except Exception as excp:
                self.log.error("Entities cleanup failure : ", excp)
