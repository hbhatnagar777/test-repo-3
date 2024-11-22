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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

import os
from time import sleep, time
import time
import datetime
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AD.azuread import AzureADPage
from Application.AD.ms_azuread import AzureAd, CvAzureAd
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing View Properties, compare properties, Download properties:
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes a test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test Case for View Properties , Compare properties , Download Properties"
        self.password = None
        self.username = None
        self.browser = None
        self.adminconsole = None
        self.navigator = None
        self.utils = TestCaseUtils(self)
        self.driver = None
        self.__driver = None
        self.server = None
        self.download_dir = None
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.ACTIVEDIRECTORY
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "AgentName": "Azure AD",
        }
        self.aad_ins = None
        self.cv_aad = None
        self.display_name = None
        self.client_name = None
        self.attribute_list = None
        self.azureadpage = None

    @TestStep
    def create_user(self):
        """
            Creates a new user using the Azure Active Directory (AAD) API.
            :return: dict: A dictionary containing information about the created user.
        """
        self.log.info(f"Creating new user")
        sleep(10)
        user = self.aad_ins.user(operation="create")
        sleep(10)
        self.log.info(f"Created new user with display name {user['displayName']}")
        return user

    @TestStep
    def delete_user(self, display_name):
        """
        Deletes a user using the Azure Active Directory (AAD) API
        :param display_name:(str) The display name of the user to be deleted
        :return: None
        """
        self.log.info(f"deleting user with display name : {display_name}")
        sleep(10)
        self.aad_ins.user(operation="harddelete", **{"displayName": display_name})
        self.log.info(f"Completed deleting user with display name : {display_name}")

    @TestStep
    def perform_updates(self, attributes):
        """
        performs update/changes on user's attribute
        :param attributes: List of common attributes to update like ["city", "companyName"] etc.
        :return: update_data (changes which were made on original data)
        """

        self.log.info("Changing attribute of user %s", self.display_name)
        sleep(20)
        before_update = self.aad_ins.user(**{"displayName": self.display_name})
        sleep(20)
        update_data = {}  # create a dictionary of attribute to be changed
        for attribute in attributes:
            # Generating a random value (current time in string format) for each attribute
            update_data[attribute] = str(int(time.time()))
        update_data["id"] = before_update["id"]
        self.aad_ins.user(operation="update", **update_data)
        sleep(20)
        after_update = self.aad_ins.user(**{"displayName": self.display_name})

        for attribute in attributes:
            if before_update[attribute] != after_update[attribute]:
                self.log.info("Details changed %s: %s to %s", attribute, before_update[attribute],
                              after_update[attribute])
        update_data.pop("id")  # remove id
        self.log.info("Update completed")
        return update_data

    @TestStep
    def perform_backup(self):
        """
        Performs backup
        :return: Job object
        """
        self.log.info("Performing backup")
        job = self._subclient.backup()
        job.wait_for_completion()
        self.log.info("Backup job completed")
        return job

    @TestStep
    def view_properties(self, job_time):
        """
           performs view_properties (Cvpysdk Api call)
           :param job_time: (Epoch timestamp) to_time for the job
           :return: (dict) view properties json form cvpysdk api call
        """
        self.log.info(
            f"Performing view properties at {job_time} "
            f"for attribute {self.display_name}")
        view_attr = self._backupset.get_view_attribute_response(job_time=job_time,
                                                                display_name=self.display_name)
        self.log.info(f"Completed getting view attributes data {view_attr}")
        return view_attr

    @TestStep
    def compare_common_attributes(self, view_attributes_dict, live_data_dict):
        """
              Compare common attributes between two dictionaries.
              [view attributes and response from live data]
              :param view_attributes_dict: response view attributes
              :param live_data_dict: response from live data
              :return: is_equal: (boolean) is properties are matching or not,
              common_attributes_diff: (dict) return attribute and changed value
        """

        def convert_to_bool(value):
            """
                converts string to bool if (str in true or false)
            """
            if isinstance(value, str):
                value_lower = value.lower()
                if value_lower == 'true':
                    return True
                if value_lower == 'false':
                    return False
            return value

        is_equal = True
        common_attributes_diff = {}
        common_attributes = [
            'accountEnabled', 'businessPhones', 'city', 'companyName', 'country',
            'createdDateTime', 'department', 'displayName', 'employeeHireDate',
            'employeeId', 'employeeType', 'faxNumber', 'givenName', 'id',
            'isLicenseReconciliationNeeded', 'jobTitle', 'mail', 'mailNickname',
            'mobilePhone', 'officeLocation', 'postalCode', 'proxyAddresses',
            'refreshTokensValidFromDateTime', 'securityIdentifier',
            'signInSessionsValidFromDateTime', 'state', 'streetAddress',
            'surname', 'userPrincipalName', 'userType'
        ]

        for attr in common_attributes:
            if attr in view_attributes_dict and attr in live_data_dict:
                value_view_attribute = convert_to_bool(view_attributes_dict[attr])
                value_live_data = convert_to_bool(live_data_dict[attr])
                if value_view_attribute != value_live_data:
                    common_attributes_diff[attr] = (value_view_attribute, value_live_data)
                    is_equal = False

        return is_equal, common_attributes_diff

    @TestStep
    def setup_browser(self):
        """
            Sets up the browser for interacting with the web application.
             :return: None
        """
        self.log.info("Opening the browser")
        self.browser.open()
        self.adminconsole = AdminConsole(self.browser,
                                         self.inputJSONnode['commcell']['webconsoleHostname'])
        self.adminconsole.login(self.username, self.password)
        self.log.info("Logging in to Command Center")
        self.driver = self.browser.driver
        self.__driver = self.adminconsole.driver
        self.navigator = self.adminconsole.navigator
        self.azureadpage = AzureADPage(self.adminconsole)

    @TestStep
    def compare_properties_front_end(self, from_timestamp, to_timestamp):
        """
            Performs Compare properties through Web-Automation
            :param from_timestamp: The first timestamp (in epoch format).
            :param to_timestamp: The second timestamp (in epoch format).
            :return: (dict) compare properties from front-end
        """
        if from_timestamp > to_timestamp:
            from_timestamp, to_timestamp = to_timestamp, from_timestamp

        def convert_timestamp(timestamp):
            """
                Changes epoch value to searchable value for compare properties
                :param timestamp: timestamp (in epoch format)
            """
            dt_object = datetime.fromtimestamp(timestamp)
            formatted_time = (dt_object.strftime("%b %d, %Y %I:%M:%S %p").
                              lstrip("0").replace(" 0", " "))
            return formatted_time

        self.log.info("Performing Compare properties")
        self.log.info("Navigating to Active Directory")
        self.navigator.navigate_to_activedirectory()

        self.log.info(f"Searching for the client {self.client_name}")

        self.azureadpage.browse_to_client(self.client_name)

        self.log.info(f"Performing download properties for the client {self.client_name}")

        return self.azureadpage.compare_properties(user_name=self.display_name,
                                                   from_time=convert_timestamp(from_timestamp + 10),
                                                   to_time=convert_timestamp(to_timestamp + 10))

    @TestStep
    def check_if_file_exists(self, file_path):
        """
            Check if file exists in download
            :param file_path: (str) file_path for file to be checked
            :return: boolean
        """
        self.log.info(f"checking for file path: {file_path}")
        return os.path.exists(file_path)

    @TestStep
    def generate_file_path(self, user_name):
        """
            Generate a file path
            :param user_name: (str) Name of the user
            :return: file path in string format
        """
        file_name = user_name + ".json"
        self.log.info(f"File name generated {file_name}")
        file_path = os.path.join(self.download_dir, file_name)
        self.log.info(f"File path generated {file_path}")

        return file_path

    @TestStep
    def download_properties(self):
        """
        Performing download properties (Web-automation)
        """
        self.log.info("Performing download properties")
        self.log.info("Navigating to Active Directory")
        self.navigator.navigate_to_activedirectory()

        self.log.info(f"Searching for the client {self.client_name}")
        self.azureadpage.browse_to_client(self.client_name)

        self.log.info(f"Performing download properties for the client {self.client_name}")
        self.azureadpage.download_properties(self.display_name)

    @TestStep
    def perform_download_properties(self, username):
        """
            Performs download properties through web-automation
            :param username :  (str) Username
            :return: None
        """
        self.log.info("Performing Download properties")
        # generating file_path
        file_path = self.generate_file_path(username)

        # check if file already presents delete file
        if self.check_if_file_exists(file_path):
            self.log.info("File already exists removing file")
            os.remove(file_path)
            self.log.info(f"The {file_path} has been removed")

        # download properties
        self.download_properties()

        # Validation
        if self.check_if_file_exists(file_path):
            self.log.info("Success : File exists")
            os.remove(file_path)  # removing file not required
        else:
            raise Exception('Failed : File doesnt exists')

    @TestStep
    def compare_front_back_end_result(self,
                                      front_end,
                                      back_end,
                                      from_timestamp,
                                      to_timestamp):
        """
        Compare the Comparison Results from Front-end compare property response
        and Back-end compare property response

        :param front_end: (dict) compare property response from front-end
        :param back_end: (dict) compare property response from back-end
        :param from_timestamp: (int) The first timestamp (Front-end job time).
        :param to_timestamp: (int) The second timestamp (Front-end job time).
        :return: (boolean) if the Comparison Results from
        Front-end compares property response and
        Back-end compares property response
        """
        if from_timestamp > to_timestamp:
            from_timestamp, to_timestamp = to_timestamp, from_timestamp

        def convert_timestamp(timestamp):
            """
                Changes epoch value to searchable value for compare properties
                :param timestamp: timestamp (in epoch format)
            """
            dt_object = datetime.fromtimestamp(timestamp)
            formatted_time = (dt_object.strftime("%b %d, %Y %I:%M:%S %p")
                              .lstrip("0").replace(" 0", " "))
            return formatted_time

        key_list = front_end.keys()
        key_val = []
        key_val += [x for x in key_list if convert_timestamp(from_timestamp + 10) in x]
        key_val += [x for x in key_list if convert_timestamp(to_timestamp + 10) in x]

        index_dict = {}
        for i in range(len(front_end['Name'])):
            index_dict[front_end['Name'][i]] = (front_end['Type'][i], front_end['Last backup time'][i])
        del index_dict[next(iter(index_dict))]

        is_equal = index_dict == back_end

        return is_equal

    def setup(self):
        """ prepare the setup environment"""
        self.commcell = self._commcell
        self.client_name = self.tcinputs["ClientName"]
        self.attribute_list = self.tcinputs["attribute_list"]

        aad_credential = [self.tcinputs['ClientId'],
                          self.tcinputs['ClientPass'],
                          self.tcinputs['TenantName']]
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.cv_aad = CvAzureAd(aad_ins=self.aad_ins, sc_ins=self._subclient)

        self.browser = BrowserFactory().create_browser_object()
        self.download_dir = self.browser.get_downloads_dir()
        self.username = self.tcinputs['TenantUsername']
        self.password = self.tcinputs['TenantPassword']

    def run(self):
        """
            this method performs the steps for
                A) view properties validation
                    step 1) changes attribute of user (perform update)
                    step 2) perform backup
                    step 3) perform view attributes
                    step 4) comparison
                B) compare properties
                    step 1) changes attribute of user (perform update)
                    step 2) perform backup
                    step 3) perform view attributes
                    step 4) comparison with view_property_1 and latest backup
                    step 5) access changes through web automation
                    step 6) compare changes through web automation to comparison result
                C) download property
                    step 1) perform download properties (web automation)
                    step 2) generate file path
                    step 3) check if file exists
        """
        # creating new user for a test case
        user = self.create_user()
        self.display_name = user['displayName']

        # # view properties test case
        # self.log.info("Performing view properties test case")
        update_data_1 = self.perform_updates(self.attribute_list)  # Changing attribute for user
        first_backup_job = self.perform_backup()  # Performing backup
        backup_job_time_1 = first_backup_job.end_timestamp
        view_property_1 = self.view_properties(job_time=backup_job_time_1)
        is_equal, differences = self.compare_common_attributes(update_data_1, view_property_1)

        if is_equal:
            self.log.info("Success : View Properties Test Case Passed")
        else:
            self.log.info("Failed : View Properties Test Case Failed")
            self.log.info(f"Differences are {differences}")
            raise Exception("Failed : View Properties Test Case Failed")

        # compare properties test case

        update_data_2 = self.perform_updates(self.attribute_list)  # Changing attribute for user
        second_backup_job = self.perform_backup()  # Performing backup
        second_backup_job_time = second_backup_job.end_timestamp
        view_property_2 = self.view_properties(job_time=second_backup_job_time)

        is_equal, compare_back_end = self.compare_common_attributes(update_data_1, update_data_2)

        if is_equal:
            self.log.info("Update Failed : something is wrong both view properties are same")
            raise Exception("Failed : Update Failed")
        # # Web automation part start here
        self.setup_browser()
        compare_front_end = self.compare_properties_front_end(from_timestamp=first_backup_job.start_timestamp,
                                                              to_timestamp=second_backup_job.start_timestamp)
        self.log.info(f"Backend result : {compare_back_end}")
        self.log.info(f"Backend result : {compare_front_end}")
        is_equal = self.compare_front_back_end_result(back_end=compare_back_end,
                                                      front_end=compare_front_end,
                                                      from_timestamp=first_backup_job.start_timestamp,
                                                      to_timestamp=second_backup_job.start_timestamp,
                                                      attribute_list=self.attribute_list)
        if is_equal:
            self.log.info("Success : Compare Properties test case passed")
        else:
            self.log.info("Failed : Compare Properties test case failed")
            raise Exception("Failed : Compare Properties test case failed")

        # Test 3 download properties
        self.perform_download_properties(self.display_name)

    def tear_down(self):
        """tear down when the case is completed, include error handle"""
        self.log.info("Tear down process started")
        if self.status == constants.PASSED:
            self.delete_user(self.display_name)
            self.log.info("Testcase completed successfully")
        else:
            self.log.info("Testcase failed")
        self.browser.close()

