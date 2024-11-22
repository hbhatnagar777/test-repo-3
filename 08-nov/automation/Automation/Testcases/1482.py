# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate disklibrary mount path operations.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    run()                       --  run function of this test case

    _validate(source_library,
              target_library,
              source,
              target)           -- Validate if the library name for source and target are same

"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for validating testcase on Disklibrary mount paths"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]: Add local/remote mount paths to disk library"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "RemoteMediaAgent": None,
            "RemoteMountPath": None,
            "UserName":None,
            "Password":None
        }

    def _validate(self, source_library, target_library, source, target):
        """ Validate if the library name for source and target are same

        Args:

            source_library (str)        -- Source library name

            target_library (str)        -- Target library name

            source (str)                -- Source where library was created and needs validation

            target (str)                -- Target where library name needs to be validated

        """
        self.log.info("Library name from {0}: {1}".format(source, source_library))
        self.log.info("Library name from {0}: {1}".format(target, target_library))

        assert source_library == target_library, "Library name mismatch for {0}".format(target)

        self.log.info("Validation succeeded")

    def run(self):
        """Main function for test case execution."""
        try:
            tc = ServerTestCases(self)
            entities = CVEntities(self)
            utility = OptionsSelector(self.commcell)

            log = self.log

            tc.log_step("""
                Test Case (as in QC)
                    1) Create magentic disk library with a mount path location on local drive
                    2) Create storage policy and associate it to the library
                    3) Add a new mount path to this magnetic library. (Local Mount Path)
                    4) Add remote mount path to the disk library
            """, 200)

            tc.log_step(""""
                        Step 1,2)
                            [Create magentic disk library with local mount path.
                            Create storage policy and associate library with the storage policy]
                        """)

            entity = entities.create(['disklibrary', 'storagepolicy'])

            sp_name = entity['storagepolicy']['name']
            lib_name = entity['disklibrary']['name']
            storage_policy = entity['storagepolicy']['object']
            lib = entity['disklibrary']['object']
            mediaagent_name = entity['disklibrary']['mediaagent_name']

            log.info("Validating if storage policy [{0}] was created on disklibrary"
                     " [{1}]".format(sp_name, lib_name))

            self._validate(lib.library_name, storage_policy.library_name,
                           source="library object", target="storagepolicy object")

            tc.log_step("Step 3) Add local mount path to disklibrary.")

            new_mount_path = entities.get_mount_path(mediaagent_name)

            log.info("Adding local mount path [{0}] to disklibrary [{1}]".format(new_mount_path,
                                                                                 lib_name))
            lib.add_mount_path(new_mount_path, mediaagent_name)
            lib_alias = utility.get_ma('aliasname', ready=False, mount_path=new_mount_path)

            self._validate(lib_name, lib_alias, source="library object", target="database")

            log.info("Added local mount path [{0}] to disklibrary [{1}] successfully"
                     "".format(new_mount_path, lib_name))

            tc.log_step("Step 4) Add remote mountpath to disklibrary.")

            log.info("Adding remote mount path [{0}] to disklibrary"
                     "[{1}]".format(self.tcinputs['RemoteMountPath'], lib_name))

            lib.add_mount_path(self.tcinputs['RemoteMountPath'],
                               self.tcinputs['RemoteMediaAgent'],
                               self.tcinputs['UserName'],
                               self.tcinputs['Password'])
            lib_alias = utility.get_ma('aliasname',
                                       ready=False,
                                       mount_path=self.tcinputs['RemoteMountPath'])
            self._validate(lib_name, lib_alias, source="library object", target="database")

            log.info("Added remote mount path [{0}] to disklibrary [{1}] successfully"
                     "".format(self.tcinputs['RemoteMountPath'], lib_name))

        except AssertionError as aserr:
            self.log.error("Validation failed with error: [{0}]".format(aserr))
            tc.fail(aserr)
        except Exception as excp:
            tc.fail(excp)
        finally:
            utility.remove_directory(mediaagent_name, new_mount_path)
            entities.cleanup()
