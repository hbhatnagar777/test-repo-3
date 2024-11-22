# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

[Acceptance] : Basic file system backup and aux copy operation validations

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    run()                       --  run function of this test case

"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for validating Basic file system backup and aux copy validation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance] : Basic file system backup and aux copy validation"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True

    def run(self):
        """Main function for test case execution."""
        try:
            tc = ServerTestCases(self) # testcase object
            cv_entities = CVEntities(self)
            tc_base = CommonUtils(self)
            sp_copy_name = ''.join(['copy', self.id])

            tc.log_step("""
                        Test Case
                            1) Create disklibrary, backupset and subclient
                            2) Create storage policy copy for the created storage policy
                            3) Execute full backup for the subclient
                            4) Execute Aux Copy on a specific copy of storage policy
                            5) Start Data Aging operation
                            6) Cleanup entities.""", 200)

            tc.log_step("""
                            Step 1) Create disklibrary, backupset, subclient.
                            Step 2) Create secondary copy for the storage policy.""")

            entities = cv_entities.create({'disklibrary':None,
                                           'backupset':None,
                                           'subclient':None,
                                           'storagepolicy':{'copy_name':sp_copy_name}
                                          })

            tc.log_step("Step 3) Execute full backup for subclient {0}"
                        "".format(''.join([entities['subclient']['target'],
                                           entities['subclient']['name']])))

            _ = tc_base.subclient_backup(entities['subclient']['object'], "full")

            tc.log_step("Step 4) Execute Aux Copy on specific copy of storage policy")

            _ = tc_base.aux_copy(entities['storagepolicy']['object'],
                                 sp_copy_name,
                                 entities['storagepolicy']['mediaagent_name'])

            tc.log_step("Step 5) Start Data Aging on commcell")

            _ = tc_base.data_aging(entities['storagepolicy']['name'], sp_copy_name)

        except Exception as excp:
            tc.fail(excp)
        finally:
            tc_base.cleanup_jobs()
            cv_entities.cleanup()
