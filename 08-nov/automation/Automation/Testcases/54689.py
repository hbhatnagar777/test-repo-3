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

    setup()             --  Setup function for this testcase

    tear_down()         --  Tear down function to delete automation generated data

    run()               --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing Cross machine clone restore testcase of PostgreSQL """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PostgreSQL Cross machine Clone restore"
        self.tcinputs = {
            'PortForClone': None,
            'DestinationClient': None,
            'DestinationInstance': None
        }
        self.postgres_helper_object = None
        self.postgres_server_user_password = None
        self.destination_client = None
        self.destination_instance = None


    def setup(self):
        """setup function for this testcase"""
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_server_user_password = self.postgres_helper_object._postgres_db_password
        self.destination_client = self.commcell.clients.get(
            self.tcinputs['DestinationClient'])
        self.destination_instance = self.destination_client.agents.get(
            'postgresql').instances.get(self.tcinputs['DestinationInstance'])

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_server_user_password,
            "auto")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            postgres_data_population_size = [3, 10, 10]
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
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                postgres_data_population_size[0],
                postgres_data_population_size[1],
                postgres_data_population_size[2],
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_server_user_password,
                True,
                "auto_snap")
            self.log.info("Test Data Generated successfully")

            clone_options = {"stagingLocaion": "/tmp/51309",
                             "forceCleanup": True,
                             "port": self.tcinputs['PortForClone'],
                             "libDirectory": self.destination_instance.postgres_lib_directory,
                             "isInstanceSelected": True,
                             "reservationPeriodS": 3600,
                             "user": self.destination_instance.postgres_server_user_name,
                             "binaryDirectory": self.destination_instance.postgres_bin_directory
                            }
            self.log.info("Clone Options: %s", clone_options)

            self.postgres_helper_object.clone_backup_restore(
                self.subclient, clone_options,
                destination_client=self.destination_client.client_name,
                destination_instance=self.destination_instance.instance_name)

            ########## checking over-write feature #########
            self.log.info("Add more data to the database")
            self.log.info("Next steps are to verify the over-write snap feature")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                1,
                5,
                100,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_server_user_password,
                True,
                "auto_snap_incremental")

            self.postgres_helper_object.clone_backup_restore(
                self.subclient, clone_options,
                destination_client=self.destination_client.client_name,
                destination_instance=self.destination_instance.instance_name)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
