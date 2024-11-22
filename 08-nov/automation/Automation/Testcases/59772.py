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

import csv
import os
from cvpysdk.commcell import Commcell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case to find out localization changes in alert tokens across different service packs"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Alert when Backup Job Succeeds'
        self.cache = None

    def get_locale_messages(self, commcell_obj):
        """Function to return query results to fetch alert token different locale values"""
        self.log.info(f"Getting locale details for commcell : {commcell_obj.commserv_hostname}")
        options_selector = OptionsSelector(commcell_obj)
        query = "select LocaleID, Message, MessageID from EvLocaleMsgs where SubsystemID=74 and left(message, 1)='<';"
        query_output = options_selector.update_commserve_db(query).rows
        return query_output

    def transform_query_output(self, commcell_obj):
        """Transforms the locale messages output returned by the query into a form easy for parsing and comparision"""
        # Constructs a dictionar of Keys : (localeid, messageId) against values of message
        # Late index using localeid, messageid to get the message
        index_data = {}
        locale_query_output = self.get_locale_messages(commcell_obj)
        for row in locale_query_output:
            index_data[(row[0], row[2])] = row[1]
        return index_data

    def get_input_commcell_obj(self):
        """Returns the commcell object for the input commcell details"""
        cell = Commcell(self.tcinputs["CommcellHostname"], self.tcinputs["CommcellUsername"], self.tcinputs["CommcellPassword"])
        return cell

    def compare_lozalization_data(self, index_data1, index_data2):
        """Compares the alert token localization data between commcells and generates report"""
        self.log.info(f"Comparing alert token localization values")
        differences = []
        # Index data is a dictionary of keys (localeid, messsageid) with the key value as a Message
        for localization_token in index_data1.keys():
            if(index_data1[localization_token] != index_data2[localization_token]):
                differences.append(localization_token+(index_data1[localization_token], index_data2[localization_token]))
        return differences

    def save_localization_differences(self, differences, commcell_obj1, commcell_obj2):
        """Converts localization difference data to CSV and saves it"""
        # Get the versions for the two commcells
        commcell_version_1 = commcell_obj1.version
        commcell_version_2 = commcell_obj2.version
        self.log.info("Writing alert localization differences to alert_localization_differences.csv")
        try:
            current_user_desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            with open(os.path.join(current_user_desktop, 'alert_localization_differences.csv'),
                      mode='w', newline='', encoding='utf-8') as diff_file:
                writer = csv.writer(diff_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['localeID', 'MessageID', f'{commcell_version_1} Message', f'{commcell_version_2} Message'])
                for difference in differences:
                    writer.writerow(list(difference))
            self.log.info(f"Saved csv file at : {current_user_desktop}")
        except Exception as excp:
            self.log.error(f"Encountered exception {excp}")

    def run(self):
        """Main function for test case execution"""
        try:
            # Get localization data for self.commcell
            index_current = self.transform_query_output(self.commcell)
            # Get commcell object for inputs
            input_commcell = self.get_input_commcell_obj()
            # Get localization data for input commcell
            index_input = self.transform_query_output(input_commcell)
            # Compoare localization data for self.commcell and input commcell
            localization_diff = self.compare_lozalization_data(index_current, index_input)
            if (len(localization_diff) != 0):
                self.log.info("Found localization changes in alert token values between the two service pack commcells")
                self.save_localization_differences(localization_diff, self.commcell, input_commcell)
                raise Exception("Found localization changes across the service packs")
            else:
                self.log.info("Found no differences in localization between the two SPs")

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED