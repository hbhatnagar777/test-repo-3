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

    run()           --  run function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.SplunkApplication.splunk import Splunk
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing advanced test case for creating new splunk client and performing
    backup and recovery and verifying the same.
    """
    test_step = TestStep()
    def __init__(self):
        """
        init method of the test-case class which defines test-case arguments
        """
        super(TestCase, self).__init__()
        self.index_name = None
        self.client_obj = None
        self.index_obj = None
        self.name = "Splunk iDA, Advanced Backup and Restore with unconditional overwrite"
        self.show_to_user = False
        self.splunk_object = None
        self.tcinputs = {
            "NewClientName": None,
            "MasterNode": None,
            "MasterUri": None,
            "UserName": None,
            "Password": None,
            "SplunkHomePath": None,
            "Plan": None,
            "Nodes": None,  # list of slave nodes:[slave1, slave2]
            "Slave1Ip": None,
            "Slave1Port": None,
            "Slave1SplunkUsername": None,
            "Slave1SplunkPassword": None
        }

    def setup(self):
        """
        Creates a new Splunk Client on CS and adds a new index to Splunk cluster
        """
        self.log.info("Creating Splunk Object")
        self.splunk_object = Splunk(self)
        self.log.info("Splunk Object Creation Successful")
        self.log.info("Starting Splunk Client Creation")
        try:
            self.client_obj = self.splunk_object.cvoperations.add_splunk_client()
            self.log.info("Splunk Client Creation Successful")
            self.index_obj = self.splunk_object.add_splunk_index()
            self.log.info("Splunk Index Creation Successful")
        except Exception as e:
            raise Exception(e)

    @test_step
    def perform_backup(self):
        """
        Updates Content of New client with the newly created index and performs backup
        """
        try:
            self.index_name = self.index_obj["name"]
            self.log.info("Starting Backup Job")
            nodes = self.tcinputs.get("Nodes")
            self.splunk_object.cvoperations.update_client_nodes(self.client_obj, nodes)
            self.splunk_object.cvoperations.update_client_content(self.client_obj, [self.index_name])
            self.splunk_object.cvoperations.run_backup(self.client_obj)
            self.log.info("Backup job Successful")
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def verify_restore(self):
        """
        Verifies Eventcount is same after restore
        """
        try:
            total_eventcount = self.index_obj["totalEventCount"]
            self.splunk_object.cvoperations.run_restore(self.client_obj, [self.index_name])
            self.splunk_object.splunk_rolling_restart()
            self.splunk_object.cvoperations.verify_restore(total_eventcount, self.index_name)
        except Exception as e:
            raise CVTestStepFailure(e)

    def cleanup(self):
        self.log.info("Starting Cleanup Job")
        self.splunk_object.cvoperations.cleanup(self.client_obj)
        self.splunk_object.cleanup_index(self.index_name)
        self.log.info("Cleanup Job Successful")

    def run(self):
        """
        Run function of this test case
        """
        self.perform_backup()
        self.splunk_object.edit_splunk_index(self.index_name)
        self.verify_restore()
        self.cleanup()
