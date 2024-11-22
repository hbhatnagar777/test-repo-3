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

import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants as cv_constants
from Database.SplunkApplication.splunk import Splunk


class TestCase(CVTestCase):
    """
    Class for executing basic test case for creating a new splunk client
    and verifying its parameters
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Basic test for creating splunk client in commcell"
        self.show_to_user = False
        self.splunk_object = None
        self.tcinputs = {
            'NewClientName': None,
            'MasterNode': None,
            'MasterUri': None,
            'UserName': None,
            'Password': None,
            'Plan': None
        }

    def run(self):
        """ Run function of this test case"""
        try:
            self.log.info("Creating Splunk Object")
            self.splunk_object = Splunk(self)
            self.log.info("Splunk Object Creation Successful")
            self.log.info("About to start adding new splunk client")
            client_obj = self.splunk_object.cvoperations.add_splunk_client()
            if client_obj is None:
                raise Exception("New Client Creation Failed")
            self.log.info("Addition of New Splunk Client Successful")
            self.log.info("Starting Bigdata App Validation")
            instance_id = self.splunk_object.validate_bigdata_app_list(client_obj)
            self.log.info("Bigdata App Validation Successful")
            self.log.info("Starting client parameter validation")
            self.splunk_object.validate_client_parameters(instance_id, client_obj)
            self.log.info("Client Parameter Validation Successful")
            self.log.info("Starting Cleanup job")
            self.splunk_object.cvoperations.cleanup(client_obj)
            self.log.info("Cleanup Job Successful")
            self.log.info("TEST CASE SUCCESSFUL")

        except Exception as ex:
            self.log.error("Exception in the test case")
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
