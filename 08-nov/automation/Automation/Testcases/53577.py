# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object

    run()               --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL SNAP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PostgreSQL Clone restore - PIT"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.POSTGRESQL
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'TestDataSize': None,
            'PortForClone': None
        }
        self.postgres_data_population_size = None
        self.postgres_server_user_password = None

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            if isinstance(self.tcinputs['TestDataSize'], str):
                self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])

            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            postgres_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)
            self.postgres_server_user_password = postgres_helper_object._postgres_db_password
            self.postgres_data_population_size = self.tcinputs['TestDataSize']
            self.log.info(
                "Postgres BIN Directory Path:%s",
                self.instance.postgres_bin_directory)

            self.log.info(
                "Snap Engine being used is:%s",
                self.subclient.snapshot_engine_name.lower())
            if "native" in self.subclient.snapshot_engine_name.lower():
                raise Exception("Need a hardware engine to run this testcase")
            if "windows" in self.client.os_info.lower():
                raise Exception("Need a UNIX machine to run this testcase")

            ########################## SNAP Backup/Restore Operation ##########
            self.log.info("##### SNAP Backup/Clone Restore Operations #####")

            self.log.info("Generating Test Data")
            postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                self.postgres_data_population_size[0],
                self.postgres_data_population_size[1],
                self.postgres_data_population_size[2],
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_server_user_password,
                True,
                "auto_snap")
            self.log.info("Test Data Generated successfully")

            clone_options = {"stagingLocaion": "/tmp/53577",
                             "forceCleanup": True,
                             "port": self.tcinputs['PortForClone'],
                             "libDirectory": self.instance.postgres_lib_directory,
                             "isInstanceSelected": True,
                             "reservationPeriodS": 3600,
                             "user": self.instance.postgres_server_user_name,
                             "binaryDirectory": self.instance.postgres_bin_directory
                            }
            self.log.info("Clone Options: %s", clone_options)
            postgres_helper_object.clone_backup_restore(
                self.subclient,
                clone_options,
                point_in_time=True)

            self.log.info("Deleting Automation Created databases")
            postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_server_user_password,
                "auto")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
