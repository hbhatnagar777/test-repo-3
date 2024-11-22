# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Database.SAPHANAUtils.hana_helper import HANAHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of SAP HANA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of SAP HANA Backup and Restore"
        self.product = self.products_list.SAPHANA
        self.feature = self.features_list.DATAPROTECTION
        self.hana_helper = None

    def setup(self):
        """
        Initializes the helper objects
        """
        self.hana_helper = HANAHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info("Creating test tables in the database")
            self.hana_helper.create_test_tables()

            self.hana_helper.hana_backup("FULL")

            self.log.info("Creating test tables before incremental backup")
            self.hana_helper.create_test_tables()

            self.hana_helper.hana_backup("INCREMENTAL")
            self.log.info("Creating test tables before differential backup")
            self.hana_helper.create_test_tables()

            self.hana_helper.hana_backup("DIFFERENTIAL")
            self.log.info("Successfully ran all three types of backup")

            self.hana_helper.hana_restore()

            self.hana_helper.hana_restore(point_in_time=True)
            self.hana_helper.hana_restore(data_only=True)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """
        Cleans up the test tables created
        """
        self.hana_helper.cleanup_test_data()
