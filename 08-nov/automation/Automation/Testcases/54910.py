# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function for this test case

    run()           --  run function of this test case

    teardown()      --  teardown function for this test case
"""

import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper


class TestCase(CVTestCase):
    """Class for executing ACCT1 of Salesforce backup and Restore test case using Mutual Auth certificate"""

    def __init__(self):
        """Initializes test case class object
            Example for tc inputs:
            "54910": {
					"client_name": "",
					"agent_name": "Cloud Apps",
					"instance_name": "",
					"backupset_name": "",
					"subclient_name": "default",
					"access_node": "",
					"download_cache_path": "/tmp",
					"mutual_auth_path": "/tmp/mutual_auth",
					"storage_policy": "",
					"salesforce_options" : {
						"login_url": "https://test.salesforce.com",
						"consumer_id": "",
						"consumer_secret": "",
						"salesforce_user_name":"",
						"salesforce_user_password":"",
						"salesforce_user_token":"",
						"salesforce_non_massl_user_name":"",
						"salesforce_non_massl_user_password":"",
						"salesforce_non_massl_user_token":"",
						"sandbox": true

					},
					"db_options":{
						"db_enabled" : true,
						"db_type": "SQLSERVER",
						"db_host_name": "",
						"db_instance": "",
						"db_name": "",
						"db_port": "",
						"db_user_name": "",
						"db_user_password": ""
					}
				}
        """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Salesforce Backup and Restore using Mutual Auth certificate"
        self.salesforce_object = None
        self.filter_query = ""
        self.query = ""
        self.restore_options = {}
        self.rec_count = 1000
        self.tc_inputs = {
            "client_name": None,
            "instance_name": None,
            "subclient_name": "default",
            "access_node": None,
            "download_cache_path": "/tmp",
            "mutual_auth_path": "/tmp/mutual_cert",
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": None,
                "salesforce_user_password": None,
                "salesforce_user_token": None,
                "salesforce_non_massl_user_name": None,
                "salesforce_non_massl_user_password": None,
                "salesforce_non_massl_user_token": None,
                "consumer_id": None,
                "conumser_secret": None
            },
            "db_options": {
                "db_enabled": False,
                "db_type": "SQLSERVER",
                "db_host_name": None,
                "db_user_name": None,
                "db_user_password": None,
                "db_port": "1432",
                "db_instance": None,
                "db_name": None
            },
            "storage_policy": None,

        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Salesforce client object.')
        self.salesforce_object = SalesforceHelper(self.commcell, self.tcinputs)
        self.salesforce_object.object_name = "Contact"
        self.salesforce_object.column_data = "ABD_54910_"
        self.filter_query = "FirstName like '{0}%' limit 100".format(self.salesforce_object.column_data)
        self.query = "select FirstName from {0} where FirstName like '%{1}%'".format(self.salesforce_object.object_name,
                                                                                     self.salesforce_object.column_data)
        self.restore_options = {"object_list": '/Objects/Contact'}
        # Enable mutual auth certificate on backupset
        backupset_properties = {'mutual_auth_path': self.tcinputs.get('mutual_auth_path', '')}
        self.salesforce_object.cvconnector.update_salesforce_backupset(backupset_properties)
        # Enable metadata on subclient
        subclient_properties = {'metadata': self.tcinputs.get('metadata', 'true')}
        self.salesforce_object.cvconnector.update_salesforce_subclient(subclient_properties)

    def run(self):
        """Main function for test case execution"""
        try:
            # Validate mutual auth user
            self.salesforce_object.validate_mutual_auth_user()
            # Create test data and run full
            self.salesforce_object.create_test_data(self.rec_count)
            self.salesforce_object.cvconnector.run_backup('Full')
            # Create test data and run incremental
            self.salesforce_object.create_test_data_for_incremental('Email', self.filter_query, self.rec_count)
            backup_data = self.salesforce_object.query_test_data(self.query)
            self.salesforce_object.cvconnector.run_backup('Incremental')
            # Delete test data in cloud
            self.filter_query = "FirstName like '%{0}%' limit 10000".format(self.salesforce_object.column_data)
            self.salesforce_object.delete_test_data(self.filter_query)
            # Run restore to salesforce and validate data in cloud
            self.salesforce_object.cvconnector.run_restore_to_salesforce_from_database(self.restore_options)
            self.salesforce_object.validate_test_data_in_cloud(self.query, backup_data)

        except Exception as exp:
            self.log.error('Error %s on line %s. Error %s', type(exp).__name__,
                           sys.exc_info()[-1].tb_lineno, exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes the test data"""
        try:
            self.salesforce_object.delete_test_data(self.filter_query)
        except Exception as exp:
            self.log.error("Error in tear down {0}".format(str(exp)))
