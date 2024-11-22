# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    run()           --  Main function for test case execution

Input Example:
    "testCases": {
				"61953": {
					"ClientName": "client1",
					"AgentName": "POSTGRESQL",
					"InstanceName": "instance1",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default",
                    "DestinationClient": "client2",
                    "DestinationInstance": "instance2"
				}
			}
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing Postgresql cross machine revert restore should fail with proper JPR"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Postgresql cross machine revert restore should fail with proper JPR"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.POSTGRESQL
        self.feature = self.features_list.DATAPROTECTION

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")
            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")
            postgres_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)
            self.log.info("Run full block level snap backup")
            postgres_helper_object.run_backup(self.subclient, "FULL")
            self.log.info("Run cross machine revert restore")
            restore_job_object = postgres_helper_object.run_restore(
                ["/data"],
                self.subclient,
                destination_client=self.tcinputs["DestinationClient"],
                destination_instance=self.tcinputs["DestinationInstance"],
                revert=True,
                skip_status_check=True)
            time.sleep(20)
            if restore_job_object.status.lower() == "failed":
                jpr = restore_job_object.delay_reason
                if "Revert restore is not applicable for cross instance restores" in jpr:
                    self.log.info("Revert failed with expected JPR")
                else:
                    raise Exception("Job:{} failed but JPR is"
                                    " {}".format(restore_job_object.job_id, jpr))
            else:
                raise Exception("Job did not fail as expected. Job status is" 
                                " {}".format(restore_job_object.status))

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
