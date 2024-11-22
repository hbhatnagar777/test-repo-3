# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate Basic operation window Data management features validation at client group level for weekly rule
 with do not submit job enabled

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    tcinputs        --  "ClientGroupName": "rodeo"

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import CVEntities
from Server.OperationWindow.ophelper import OpHelper
from Server.OperationWindow.opvalidate import OpValidate
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Basic operation window Data management features validation at client group level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Functional] : Basic operation window Data management features validation at client group level " \
                    "for weekly rule with do not submit job enabled"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.show_to_user = False
        self.clientgroup = None
        self.tcinputs = {
            'ClientGroupName': None
        }
        self.op_window, self.entities, self.entity_props = None, None, None
        self.server = None

    def run(self):
        """
        Main function for test case execution
        Follows the following steps
                1) Creates required entities: disklibrary, storagepolicy, subclient
                2) Creates an operation window at client group level for a list of operations:
                            ["FULL_DATA_MANAGEMENT",
                               "DATA_RECOVERY",
                               "NON_FULL_DATA_MANAGEMENT"]
                3) Validates each feature present in the list of operations
                4) The feature triggered job should honor the created operation window i.e., job should be queued
                5) If successfully queued, Modify the operation window to allow the job to run.
                6) Checks whether the job is running state or not
                7) Repeats 4,5,6 steps for every feature present in list of operations
                8) Testcase will be successful if all the above steps are executed without exceptions
                9) Deletes the created operation window and entities
        """
        try:
            operations_list = ["FULL_DATA_MANAGEMENT",
                               "DATA_RECOVERY",
                               "NON_FULL_DATA_MANAGEMENT"]

            self.log.info("Validating clientgroup level operation window for the features:%s",
                          operations_list)

            self.log.info("Initialising the subclient that honors the operation window")
            self.server = ServerTestCases(self)
            self.entities = CVEntities(self)
            self.entity_props = self.entities.create(["disklibrary", "storagepolicy", "subclient"])
            self.subclient = self.entity_props['subclient']['object']
            self.clientgroup = self.commcell.client_groups.get(self.tcinputs['ClientGroupName'])
            self.op_window = OpHelper(self, self.clientgroup)
            self.log.info("Initialised the operation window successfully")

            machine = Machine(self.client)
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
