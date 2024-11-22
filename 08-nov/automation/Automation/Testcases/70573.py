# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from BigDataApps.CouchbaseUtils.couchbasehelper import Couchbase


CONSTANTS = config.get_config()
class TestCase(CVTestCase):
    """
    Class for creating and performing basic operations on a new couchbase client
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.items = None
        self.value_for_docid = None
        self.bucket_names = None
        self.name = "Testcase for creating and performing basic operations on a new couchbase client"
        self.couchbase = None
        self.tcinputs = {
            'data_access_nodes': None,
            'port': None,
            'staging_type': None,
            'staging_path': None,
            'plan_name': None,
            'user_name': None,
            'password': None,
            "service_host": None
        }

    def setup(self):
        """Initializes objects required for this testcase"""
        self.bucket_names = ["gamesim-sample","beer-sample","travel-sample"]
        self.aws_access_key = CONSTANTS.Bigdata.Couchbase.aws_access_key
        self.aws_secret_key = CONSTANTS.Bigdata.Couchbase.aws_secret_key

    def run(self):
        """ Run function of this test case"""
        try:
            self.log.info("Creating couchbase Object")
            self.couchbase = Couchbase(self)
            self.log.info("couchbase Object Creation Successful")
            self.log.info("About to start adding new couchbase client")
            client_obj = self.couchbase.add_couchbase_client()
            if client_obj is None:
                raise Exception("New Client Creation Failed")
            self.log.info("Addition of New couchbase Client Successful")

            client_details = self.couchbase.get_client_details(
                client_obj, backupset_name="defaultbackupset", subclient_name="default")

            # connect to db and generate test data
            self.couchbase.connect_to_db()
            self.couchbase.generate_test_data()
            self.items = self.couchbase.get_number_of_docs(self.bucket_names)

            # run full backup
            self.couchbase.run_backup(client_obj, client_details)

            # delete buckets, run inplace restore without unconditional overwrite, then validate restored data
            self.couchbase.delete_buckets(self.bucket_names)
            self.couchbase.run_restore(overwrite=False)
            self.couchbase.validate_restored_data(
                self.items, self.bucket_names)

            # run inplace restore with unconditional overwrite, then validate restored data
            self.couchbase.run_restore(overwrite=True)
            self.couchbase.validate_restored_data(
                self.items, self.bucket_names)

            # For loop for repeating the following steps 3 times
            # create a new bucket, run incremental, verify restores with overwrite option and delete bucket
            for i in range(1, 4):
                self.couchbase.create_bucket('auto' + str(i))
                self.items = self.couchbase.get_number_of_docs(['auto' + str(i)])
                self.couchbase.run_backup(client_obj, client_details, backup_type='Incremental')
                self.couchbase.run_restore(overwrite=True)
                self.couchbase.validate_restored_data(self.items, ['auto' + str(i)])

            # delete buckets created in above step
            for i in range(1, 4):
                self.couchbase.delete_buckets(['auto' + str(i)])

            # create bucket, run full backup, Add items to that bucket, run incremental and verify count before and
            # after restores
            for i in range(1, 4):
                self.couchbase.create_bucket('auto' + str(i))
                self.couchbase.run_backup(client_obj, client_details)
                self.couchbase.add_items_to_bucket('auto' + str(i))
                self.items = self.couchbase.get_number_of_docs(['auto' + str(i)])
                self.couchbase.run_backup(client_obj, client_details, backup_type='Incremental')
                self.couchbase.run_restore(overwrite=True)
                self.couchbase.validate_restored_data(self.items, ['auto' + str(i)])

                # Change value of an item, run incremental and verify value after restores

                self.value_for_docid = self.couchbase.get_value_for_docid('auto' + str(i), "test" + str(i))
                self.couchbase.update_value_for_docid('auto' + str(i), "test" + str(i))
                self.couchbase.run_backup(client_obj, client_details, backup_type='Incremental')
                self.couchbase.run_restore(overwrite=True)
                self.couchbase.validate_doc_value(self.value_for_docid, 'auto' + str(i), "test" + str(i))
                self.couchbase.delete_buckets(['auto' + str(i)])

            # cleanup all the created entities
            self.couchbase.delete_buckets(self.bucket_names)
            self.couchbase.delete_couchbase_client()
            self.log.info("testcase execution completed successfully")
            self.status = constants.PASSED


        except Exception as ex:
            self.log.info(Exception)
            self.log.error('failure in automation case : %s', ex)
            self.result_string = str(ex)
            self.log.info('Test case failed')
            self.status = constants.FAILED
