# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case


    Input Example:
    multiple access nodes,  AccessNodes value need be string "<node1>,<node2>,..."

    "testCases": {

		"70621": {
            "Region": None,
            "CloudAccount": None,
            "CloudAccountPassword": None,
            "AccessNodes": None,
            "Plan": None,
            "SubscriptionId": None,
            "CredentialName": None,
            "TenantID": None,
            "ApplicationID": None,
            "ApplicationSecret": None
		}
    }
"""

from Reports.utils import TestCaseUtils
from Application.CloudApps.azure_cosmos_sql_api import CosmosCassandraAPI
from Application.CloudApps.AzureCosmosDBUtils.cosmosdbcassandraapihelper import CosmosDBCassandraAPIHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, constants


CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Instance creation/backup/restore for CosmosDB Cassandra API Instance"""

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Acceptance test for CosmosDB Cassandra API"
        self.utils = TestCaseUtils(self)
        self.helper = None
        self.orig_data = None
        self.restore_data = None
        self.cloudaccountname = None
        self.tcinputs = {
            "Region": None,
            "CloudAccount": None,
            "CloudAccountPassword": None,
            "AccessNodes": None,
            "Plan": None,
            "SubscriptionId": None,
            "CredentialName": None,
            "TenantID": None,
            "ApplicationID": None,
            "ApplicationSecret": None
        }

    def validate_restore_data(self, orig_data, dest_data):
        """compare the original data and the restored data"""
        if sorted(orig_data) == sorted(dest_data):
            self.log.info("restored data are same as original data")
        else:
            raise Exception("restored data does not match with original data")

    def populate_test_data(self):
        """populate test data"""
        self.cosmoshelper = CosmosCassandraAPI(
            cloudaccount=self.tcinputs["CloudAccount"],
            cloudaccount_password=self.tcinputs["CloudAccountPassword"])
        self.cosmoshelper.drop_keyspace(self.keyspace)
        self.cosmoshelper.drop_keyspace('restore1')
        self.cosmoshelper.create_keyspace(self.keyspace)
        self.cosmoshelper.create_table(self.keyspace, self.tablename)
        self.cosmoshelper.add_test_data(
            self.keyspace, self.tablename, user_ids=[
                1, 2, 3, 4, 5])

    def cleanup_testdata(self):
        """drop test keyspaces, disconnect db connections and delete db instances"""
        self.cosmoshelper.drop_keyspace(self.keyspace)
        self.cosmoshelper.disconnect()

    def setup(self):
        """Initializes object required for this testcase"""

        self.instance_name = "automated_cosmosdb_cassandra_" + self.id
        self.cloudaccount = self.tcinputs["CloudAccount"]
        self.keyspace = 'automationks_' + self.id
        self.tablename = 'automationtb_' + self.id
        self.tablename2 = 'automationtb2_' + self.id
        self.cloudaccountname = self.tcinputs["CloudAccount"] + "_automation"
        self.pathlist = ["/" + self.cloudaccount]
        self.helper = CosmosDBCassandraAPIHelper(self)

    def run_restore_verify(self):
        """run restore job and validate the restore data"""
        self.log.info("run restore job and validate restored data")
        self.orig_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.cosmoshelper.drop_keyspace(self.keyspace)
        self.helper.run_restore(
            srckeyspacename=self.keyspace,
            destkeyspacename=self.keyspace)
        self.dest_data = self.cosmoshelper.get_rows(
            self.keyspace, self.tablename)
        self.validate_restore_data(self.orig_data, self.dest_data)

    def run(self):
        """Run function of this testcase"""
        try:
            _desc = """
                This test case will cover CosmosDB Cassandra API acceptance test:
                1: connect to cloud account populate test data
                2: delete existing instance if exist, create CosmosDB Cassandra AP instance
                3: Run full backup job
                4: run restore and verify the restored data
                5: update data, run inc job
                6:  run restore and verify the restored data
                7: cleanup test data, drop db connections, delete instance
            """
            self.log.info(_desc)

            self.log.info("step 1: connect to db, populate test data")
            self.populate_test_data()

            self.log.info("step 2: add CosmosDB cassandra api instance")
            self.helper.add_instance()

            self.log.info("step 3: run full backup job")
            self.helper.run_backup(backup_level="FULL")

            self.log.info("step 4: run restore and verify restored data")
            self.run_restore_verify()

            self.log.info("step 5: update test data, run incremental job")
            self.cosmoshelper.add_test_data(
                self.keyspace, self.tablename, user_ids=[6, 7, 8, 9])
            self.helper.run_backup()

            self.log.info("step 6: run restore and verify restored data")
            self.run_restore_verify()

            self.log.info("step 7: clean test data and delete test instnace")
            self.cleanup_testdata()
            self.helper.delete_instance()
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.info(Exception)
            self.log.error('cockroachdb automation failed: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
