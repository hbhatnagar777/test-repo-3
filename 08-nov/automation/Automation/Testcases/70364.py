# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case



TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case

This testcase verifies the basic validation of 
AI Code Assistant in API Engineer

Validation.json in Server/RestAPI/APIEngineer folder contains the validation data
for the AI Code Assistant

Add more validation data in the validation.json file to validate more scenarios
"""

from AutomationUtils import constants
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.APIEngineer.assistantvalidator import AIAssistantValidator
import os
import json

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

        This method initializes the name and additional_settings attributes, 
        and calls the parent class's __init__ method.
        """
        super(TestCase, self).__init__()
        self.name = "Validate the API Engineer Assistant basic queries"
        self.additional_settings = None

    def setup(self):
        """Setup function of this test case

        This method sets up the test case by checking if the API Engineer is enabled.
        If it's not enabled, it raises an exception and skips the test case.
        """
        self.csdb.execute("SELECT  name, value FROM GxGlobalParam WHERE name like '%apiengineer%'")
        self.result_dict = {key: value for key, value in self.csdb.fetch_all_rows()}
        if (not (self.result_dict.get('apiEngineerEndPoint') and self.result_dict.get('apiEngineerAuthKey'))):
            raise Exception("API Engineer is not enabled. Skipping the test case")

    def run(self):
        """Run function of this test case

        This method runs the test case. It initializes the AIAssistantValidator class, 
        loads the validation data from a JSON file, and validates the AI assistant. 
        It then calculates the median and mean response times and logs them. 
        If the validation fails, it logs the failed queries and raises an exception. 
        If the validation passes, it logs a success message.
        """
        #try:
            # Initialize the AIAssistantValidator class
            # Load validation data from JSON file
        with open(os.path.join(constants.AUTOMATION_DIRECTORY, "Server", "RestAPI", "APIEngineer","validation.json"), "r") as f:
            validation_data = json.load(f) 
        ai_assistant = AIAssistantValidator(validation_data, self.log, self.result_dict)
        api_results = ai_assistant.validate_ai_assistant()

        response_times = [result["TimeTaken"] for result in api_results]

        # Calculate the median and mean response times
        median_response_time = sorted(response_times)[len(response_times) // 2]
        mean_response_time = sum(response_times) / len(response_times)
        self.log.info(f"Median response time: {median_response_time}")
        self.log.info(f"Mean response time: {mean_response_time}")
        
        if not all(result["Result"] == "Passed" for result in api_results) or median_response_time > 20: 
            self.log.info("API Engineer validation failed")
            for results in api_results:
                if results['Result'] == "Failed":
                    self.log.info("Query Number "+ str(results['Question']) + " " + validation_data[str(results['Question'])]['question'])
            raise Exception("API Engineer validation failed")
        else:
            self.log.info("API Engineer validation passed")
