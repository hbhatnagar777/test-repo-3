# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing user-centric laptop testcase
            to check for pseudo-client creation, backup and restore.

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from FileSystem.FSUtils import fshelper

class TestCase(CVTestCase):
    """
    Class for executing user-centric laptop testcase

    This testcase does the following

    Step 1, Remote login to the client machine with non-admin credentials

    Step 2, Check if pseudo-client exists on CS

    Step 3, Check if the first backup job on pseudo-client 
            was scheduled and if it finished successfully

    Step 4, Run restore by job and verify if it completes successfully
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "ClientAdminUsername": None,
            "ClientAdminPassword": None,
            "ClientNonAdminUsername": None,
            "ClientNonAdminPassword": None
            }
        self.name = "User-centric laptop"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            fshelper.FSHelper.populate_tc_inputs(self, False)

            self.log.info("""User-centric laptop
                This testcase does the following
                Step 1, Remote login to the client machine with non-admin credentials
                Step 2, Check if pseudo-client exists on CS
                Step 3, Check if the first backup job
                    on pseudo-client was scheduled and if it finished
                    successfully
                Step 4, Run restore by job and verify if it
                    completes successfully
                    """)
            
            pseudo_client = "{0}{1}{2}".format(
                self.tcinputs['ClientName'],
                "_",
                self.tcinputs['ClientNonAdminUsername'].replace("\\", "_")
                )

            #Set TestPath
            username = self.tcinputs["ClientNonAdminUsername"]
            if '\\' in username:
                username = username[username.index("\\")+1 : ]
            if self.applicable_os is 'WINDOWS':
                self.tcinputs["TestPath"] = self.client_machine.join_path(
                    "C:\\Users",
                    username,
                    "Documents"
                    )
            elif self.applicable_os is 'MAC':
                self.tcinputs["TestPath"] = self.client_machine.join_path(
                    "/Users",
                    username,
                    "Documents"
                    )
            self.test_path = self.tcinputs["TestPath"]
            #Remote login to client machine
            self.log.info("Step 1, Remote login to the client machine with non-admin credentials")
            self.helper.remote_login()
            
            #Wait so that pseudo-client is created on CS
            self.log.info("Waiting for 10 mins before checking for pseudo-client...")
            time.sleep(600)

            #Check for pseudo-client existence on CS
            self.log.info("Step 2, Check if pseudo-client exists on CS")
            self.helper.check_pseudo_client(pseudo_client)

            #Wait so that backup job is started on CS
            self.log.info("Waiting for 10 mins before checking for backup...")
            time.sleep(600)

            #Check for status of scheduled backup of the pseudo-client
            self.log.info("""Step 3, Check if the first backup job
                    on pseudo-client was scheduled and if it finished
                    successfully""")
            self.helper.check_scheduled_backup()

            #Check for restore
            self.log.info("""Step 4, Run restore by job and verify if it
                    completes successfully""")
            #Replace client object with pseudo-client object
            self.client = self.commcell.clients.get(pseudo_client)
            self.agent = self.client.agents.get("File System")
            self.backupset = self.agent.backupsets.get("defaultBackupset")
            self.subclient = self.backupset.subclients.get("default")
            self.helper.run_restore_verify(
                self.slash_format,
                self.client_machine.join_path(
                    self.test_path,
                    "test"),
                "C:",
                "test",
                self.first_job
                )
            
        except Exception as excp:
            self.log.error("Test case failed with exception: " + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        
        finally:
            #Clean up pseudo-client
            self.log.info("Cleaning up pseudo-client if created")
            if self.helper:
                self.helper.pseudo_client_cleanup(pseudo_client)
            