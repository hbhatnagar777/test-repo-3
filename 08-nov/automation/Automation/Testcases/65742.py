# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    tear_down()     --  Tear down function to delete automation generated data

    run()           --  Main function for test case executions

"""

from time import sleep
import time
import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Application.AD.ms_azuread import AzureAd, CvAzureAd
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ Testcase to verify Point In Time Restore for Azure AD"""

    TestStep = TestStep()

    def __init__(self):
        """ initial class
        Properties to be initialized:
        name            (str)        -- name of this test case
        applicable_os   (str)    -- applicable os for this test case
        product         (str)    -- applicable product for AD
        """
        super().__init__()
        self.attribute_list = None
        self.name = "Azure AD Point in time Restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.ACTIVEDIRECTORY
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "AgentName": "Azure AD",
        }
        self.commcell = self._commcell
        self.aad_ins = None
        self.user_id = None
        self.cv_aad = None
        self.cv_azure_ad = None
        self.display_name = None
        self.client_name = None

    @TestStep
    def view_properties(self, job_time):
        """
           performs view_properties (Cvpysdk Api call)
           :param job_time: (Epoch timestamp) to_time for the job
           :return: (dict) view properties json form cvpysdk api call
        """
        self.log.info(
            f"Performing view properties at {self.epoch_to_local(job_time)} "
            f"for attribute {self.display_name}")
        view_attr = self._backupset.get_view_attribute_response(job_time=job_time,
                                                                display_name=self.display_name)
        self.log.info(f"Completed getting view attributes data {view_attr}")
        return view_attr

    @TestStep
    def get_user_info(self):
        """
        get the user attributes from ms-aad
        :return: User
        """
        self.log.info(f"Getting user info {self.display_name}")
        sleep(20)
        user = self.aad_ins.user(**{"displayName": self.display_name})
        return user

    @TestStep
    def perform_updates(self, attributes):
        """
        performs update/changes on user's attribute
        :param attributes: List of common attributes to update like ["city", "companyName"] etc.
        :return: update_data (changes which were made on original data)
        """

        self.log.info("Changing attribute of user %s", self.display_name)

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
    def perform_restore(self, to_time):
        """
        Performs restore for a selected object at selected time
        :param to_time: restores from a backup_job_time
        :return: restore job object
        """
        self.log.info("Performing restore")
        azure_ad_obj = self.get_user_info()
        self.cv_azure_ad.cv_obj_restore(browsetime=to_time, obj_=azure_ad_obj)
        self.log.info("Restore completed")

    @TestStep
    def validate_results(self, job_time):
        """
        This method performs validation for test case
        :param job_time: update-info which was present in backup
        :return: None
        """
        # Validating Results
        self.log.info("Getting user live data")
        live_data = self.get_user_info()
        self.log.info("Completed: getting user live data")

        self.log.info("Getting user backup data")
        backup_data = self.view_properties(job_time=job_time)

        self.log.info("Completed: getting backup data")

        # Comparing result
        self.log.info("Comparing results")
        self.log.info(f"Live data : {live_data}")
        self.log.info(f"Backup data : {backup_data}")

        is_equal, diff = self.compare_common_attributes(live_data, backup_data)

        if is_equal:
            self.log.info("Success TestCase Passed")
        else:
            self.log.info("comparison failed")
            self.log.info(f"Difference is {diff}")
            raise Exception("Failed : Point in time restore TestCase Failed")

    @TestStep
    def epoch_to_local(self, timestamp):
        """
        Create local time from epoch time-stamp
        :param timestamp: (int)timestamp
        :return: time in string format
        """
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def setup(self):
        """ prepare the setup environment"""
        aad_credential = [self.tcinputs['ClientId'],
                          self.tcinputs['ClientPass'],
                          self.tcinputs['TenantName']]
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.user_id = self.tcinputs['user_id']
        self.display_name = self.tcinputs["display_name"]
        self.client_name = self.tcinputs["ClientName"]
        self.attribute_list = self.tcinputs["attribute_list"]
        self.cv_azure_ad = CvAzureAd(self.aad_ins, self._subclient)

    def run(self):
        """
                this method performs the following steps
                step 1) changes attribute of user
                step 2) perform backup
                step 3) calculate time range for point in time restore
                step 4) selects last 2nd job and perform search on it
                        return doc_id and attributes that will be changed
                step 5) restore the last 2nd job for particular user
                step 6) compare restored attributes with live data
                :return: None
        """

        self.perform_updates(self.attribute_list)  # Changing attribute for user
        first_backup_job = self.perform_backup()  # Performing backup (2nd latest)

        self.perform_updates(self.attribute_list)  # Changing attribute for user
        self.perform_backup()  # Performing backup (latest)

        backup_job_time = first_backup_job.end_timestamp
        self.perform_restore(backup_job_time)
        self.validate_results(job_time=backup_job_time)  # Validating results

    def tear_down(self):
        """tear down when the case is completed, include an error handle"""
        self.log.info("In teardown function")
