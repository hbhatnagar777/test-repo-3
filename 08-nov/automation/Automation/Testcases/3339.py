# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

[Acceptance] : Incremental Storage Policy basic operations validation

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
    """Class for validating testcase Incr Storage Policy to tape storage policy data backup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance] : Incremental Storage Policy to tape storage policy data backup"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "TapeLibraryName": None,
            "DrivePoolName":None,
            "ScratchPoolName":None,
            "MediaAgent": None,
        }

    def run(self):
        """Main function for test case execution."""
        try:
            tc = ServerTestCases(self)
            cv_entities = CVEntities(self)
            ida_utils = CommonUtils(self.commcell)

            disk_library = cv_entities.default_library
            disk_ma = cv_entities.default_mediaagent
            disk_sp = ''.join(['Acceptance_', self.id])
            tape_library = self.tcinputs['TapeLibraryName']
            tape_ma = self.tcinputs['MediaAgent']
            tape_sp = ''.join(['Acceptance_tape_', self.id])
            client = self.client.client_name

            # Check pre conditions.
            # Tape library Media agent and disk library media agent should be different.
            if tape_library == disk_library or tape_ma == disk_ma:
                raise Exception("""
                        Testcase failed to meet requirements.
                            - TapeLibrary [{0}] and Disklibrary [{1}] should be different.
                            - MediaAgent [{2}] and testcase initialized subclient's mediaagent
                                [{3}] should be different. """
                                .format(tape_library, disk_library, tape_ma, disk_ma))


            #-------------------------------------------------------------------------------------
            tc.log_step("""
                Test Case [ As automated in old Framework ]
                1) Create storage policy with disk library
                   Create storage policy with tape library and incremental storage policy.
                   Create subclient with tape storage policy
                2) Execute full backup on the subclient and wait for job to complete
                3) Add incremental content to full content
                   Execute incremental backup for subclient and wait for job to complete
                4) Execute out of place restore for subclient content
                5) Compare source and restored data
                6) Run Synthetic full backup and wait for job to complete

                Finally:
                    Cleanup test data""", 200)


            #-------------------------------------------------------------------------------------
            tc.log_step("""
                        Step 1) Create storage policy with disk library
                                Create storage policy with tape library and incremental storage
                                    policy.
                                Create subclient with tape storage policy""")

            # There is no API available yet to delete a storage policy associated to an
            # incremental storage policy, so skip deleting the policy and create a unique
            # policy for this test case.
            _ = cv_entities.create({
                'storagepolicy':{
                    'name': disk_sp,
                    'library': disk_library,
                    'mediaagent': disk_ma,
                    'force': False,
                    'cleanup': False
                }
            })

            props = cv_entities.create({
                'storagepolicy':{
                    'name': tape_sp,
                    'library': tape_library,
                    'mediaagent': tape_ma,
                    'drivepool': self.tcinputs['DrivePoolName'],
                    'scratchpool': self.tcinputs['ScratchPoolName'],
                    'incremental_sp_tape': disk_sp,
                    'istape': True,
                    'force': False,
                    'cleanup': False
                },
                'subclient': None
            })

            subclient = props['subclient']['object']
            target = props['subclient']['target']


            #-------------------------------------------------------------------------------------
            tc.log_step("""
                        Step 2) Execute full backup on the subclient and wait for
                                    job to complete""")
            _ = ida_utils.subclient_backup(subclient, 'full')


            #-------------------------------------------------------------------------------------
            tc.log_step("""
                        Step 3) Add incremental content to full content
                                Execute incremental backup for subclient and wait for
                                    job to complete
                        Step 4) Execute out of place restore for subclient content.
                        Step 5) Compare source and restored data
                        """)
            ida_utils.subclient_backup_and_restore(client, subclient)


            #-------------------------------------------------------------------------------------
            tc.log_step("""Step 6) Run Synthetic full backup and wait for job to complete""")
            ida_utils.subclient_backup(subclient, 'Synthetic_full', target_subclient=target)

        except Exception as excp:
            tc.fail(excp)
        finally:
            ida_utils.cleanup_jobs()
            cv_entities.cleanup()
