# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate creating/deleting commcell entities

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for creating/deleting commcell entities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]: Create/Delete commcell entities"
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
            entities = CVEntities(self)

            tc.log_step("""Test Case:
                            1) Create
                                    backupset,
                                    subclient,
                                    disklibrary,
                                    storage policy(with Magnetic library),
                                    storage policy(with tape library),
                                    client group
                                    user,
                                    usergroup,
                                    alert,
                                    schedule,
                                    schedule policy,

                            2) Delete the above created entities
            """, 200)

            # Creating all entities and validating
            all_entities = entities.create()

            # Create Storage policy with Tape Library
            tape_storage_policy = entities.create({
                'storagepolicy':{
                    'library': self.tcinputs['TapeLibraryName'],
                    'mediaagent': self.tcinputs['MediaAgent'],
                    'drivepool': self.tcinputs['DrivePoolName'],
                    'scratchpool': self.tcinputs['ScratchPoolName'],
                    'istape': True
                }
            })

            # Delete all entities [ Although not required here. cleanup() will handle cleanup.
            # For this test case explicit is better than implicit
            entities.delete(all_entities)
            entities.delete(tape_storage_policy)

            # To do:
            # Add support for create/delete user/usergroup/alert/schedule
            # policy, once helpers support is available for server
            #

        except Exception as excp:
            tc.fail(excp)
        finally:
            # Deleting all entities and validating
            entities.cleanup()
