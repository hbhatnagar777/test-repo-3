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

    init_tc()       --  initialize browser and redirect to required page

    run()           --  run function of this test case


    Input Example:

    "testCases": {
                "62445": {
                            "access_nodes": "",
                            "port": "",
                            "username": "",
                            "password": "",
                            "staging_type": "",
                            "credentials":"",
                            "service_host": "",
                            "staging_path": "",
                            "plan": "",
                            "destination_instance": ""
        }
    }
"""
import time
from Reports.utils import TestCaseUtils

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.couchbase_helper import Couchbase



CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate acceptance from admin console - Couchbase - s3 staging path"""

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.port = None
        self.items = None
        self.value_for_docid = None
        self.bucket_names = None
        self.utils = None
        self.name = "Acceptance test from admin console - Couchbase - S3 staging path"
        self.browser = None
        self.admin_console = None
        self.couchbase_server_name = None
        self.couchbase = None
        self.tcinputs = {
            "access_nodes": None,
            "port": None,
            "username": None,
            "password": None,
            "staging_type": None,
            "credentials": None,
            "service_host": None,
            "staging_path": None,
            "plan": None,
            "destination_instance": None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.couchbase_server_name = "automated_couchbase_server_62445"
        self.utils = TestCaseUtils(self)
        self.bucket_names = ["gamesim-sample", "travel-sample", "beer-sample"]

    def init_tc(self):
        """Initialize browser and redirect to required page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def run(self):
        """Run function of this testcase"""
        try:
            self.init_tc()

            self.couchbase = Couchbase(self.admin_console, self)
            self.couchbase.create_couchbase_instance()

            # connect to couchbase cluster
            self.couchbase.connect_to_db()

            # create test data, run backup
            self.couchbase.generate_test_data()
            self.items = self.couchbase.get_number_of_docs(self.bucket_names)
            self.couchbase.verify_backup('FULL')

            # run a second full backup
            self.couchbase.verify_backup('FULL')

            # delete buckets, run inplace restore without unconditional overwrite, then validate restored data
            self.couchbase.delete_buckets(self.bucket_names)
            self.couchbase.verify_restore(outofplace=False, overwrite=False)
            self.couchbase.validate_restored_data(
                self.items, self.bucket_names)

            # run inplace restore with unconditional overwrite, then validate restored data
            self.couchbase.verify_restore(outofplace=False, overwrite=True)
            self.couchbase.validate_restored_data(
                self.items, self.bucket_names)

            # run out of place restore of a bucket and validate data in destination bucket
            self.couchbase.verify_restore(outofplace=True, overwrite=True)
            self.couchbase.validate_restored_data(
                self.items, self.bucket_names)
            self.couchbase.delete_buckets(self.bucket_names)

            # For loop for repeating the following steps 3 times
            # create a new bucket, run incremental, verify restores with overwrite option and delete bucket
            for i in range(1, 4):
                self.couchbase.create_bucket('auto' + str(i))
                self.items = self.couchbase.get_number_of_docs(['auto' + str(i)])
                self.couchbase.verify_backup('INCR')
                self.couchbase.verify_restore(outofplace=False, overwrite=True)
                self.couchbase.validate_restored_data(self.items, ['auto' + str(i)])

            # delete buckets created in above step
            for i in range(1, 4):
                self.couchbase.delete_buckets(['auto' + str(i)])

            # create bucket, run full backup, Add items to that bucket, run incremental and verify count before and
            # after restores
            for i in range(1, 4):
                self.couchbase.create_bucket('auto' + str(i))
                self.couchbase.verify_backup('FULL')
                self.couchbase.add_items_to_bucket('auto' + str(i))
                self.items = self.couchbase.get_number_of_docs(['auto' + str(i)])
                self.couchbase.verify_backup('INCR')
                self.couchbase.verify_restore(outofplace=False, overwrite=True)
                self.couchbase.validate_restored_data(self.items, ['auto' + str(i)])

                # Change value of an item, run incremental and verify value after restores

                self.value_for_docid = self.couchbase.get_value_for_docid('auto' + str(i), "test" + str(i))
                self.couchbase.update_value_for_docid('auto' + str(i), "test" + str(i))
                self.couchbase.verify_backup('INCR')
                self.couchbase.verify_restore(outofplace=False, overwrite=True)
                self.couchbase.validate_doc_value(self.value_for_docid, 'auto' + str(i), "test" + str(i))
                self.couchbase.delete_buckets(['auto' + str(i)])

            # clean up the test data, shutdown DB connection and delete the couchbase
            # pseudo client
            self.couchbase.delete_couchbase_instance()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
