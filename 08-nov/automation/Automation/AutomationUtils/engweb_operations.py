# -*- coding: utf-8 -*-
# pylint: disable=R0913
# pylint: disable=W0703

"""
File for operations on EngWeb via REST API.

EngWeb is the class representing the connection to EngWeb, and operations on EngWeb via REST API.

EngWeb:

    __init__()                          --  initialize connection to EngWeb using given credentials

    _update_response()                  --  parse the response received, and extract the error

    _get_testset_id_by_display_name()   --  get the test set id using the test set display name

    _get_testset_id_by_params()         --  get the test set id using the full test set name

    domain                              --  returns value of domain attribute

    username                            --  returns value of username attribu

    password                            --  returns value of password attributete

    auth                                --  returns the NTLM Auth object

    api                                 --  returns value of the base API URL

    features                            --  list consisting of the features listed on EngWeb

    get_features()                      --  gets the list of all the features on EngWeb

    get_testsets()                      --  gets the list of all testsets for a release / feature

    get_testset_id()                    --  returns the test set id for the given test set

    get_testcases()                     --  gets the list of all test cases for a test set

    get_testcase_details()              --  returns the details of a test case

    get_instance_id()                   --  returns the instance id for test set and a test case

    update_testcase_status()            --  updates the test case run status to QA

    update_qa()                         --  wrapper method to update the QA with test case status

"""

import requests

from AutomationUtils.config import get_config


ERROR_MESSAGE = "No Error Returned from the Server"
_CONFIG = get_config()


class EngWeb:
    """Class for operations on EngWeb."""

    def __init__(self):
        """
        Initializes the connection to EngWeb with the given credentials.

        """
        self._domain = _CONFIG.UpdateQA.domain
        self._username = _CONFIG.UpdateQA.username
        self._password = _CONFIG.UpdateQA.password

        if not (self._domain and self._username and self._password):
            raise ValueError()

        import requests_ntlm
        self._auth = requests_ntlm.HttpNtlmAuth(self.domain + '\\' + self.username, self.password)

        self._api = 'https://engweb.commvault.com/api/qa/{0}'

        self._features = {}

    @staticmethod
    def _update_response(input_string):
        """Returns only the relevant response from the response received from the server.

            Args:
                input_string    (str)   --  input string to retrieve the relevant response from

            Returns:
                str     -   final response to be used

        """
        if '<title>' in input_string and '</title>' in input_string:
            response_string = input_string.split("<title>")[1]
            response_string = response_string.split("</title>")[0]
            return response_string

        return input_string

    def _get_testset_id_by_display_name(self, testset_name):
        """Returns the id of the Test Set for the given Test Set Display Name.

            Args:
                testset_name    (str)   --  Display Name of the Test Set

            Returns:
                int     -   id of the testset

            Raises:
                Exception:
                    if the key `testset` is not present in the response

                    if the response is not SUCCESS

        """
        request_uri = self.api.format('testset')

        params = {
            "displayname": testset_name
        }

        response = requests.get(request_uri, params=params, auth=self.auth)

        if response.status_code == 200:
            if 'testset' not in response.json():
                exception_message = (
                    'Test Set not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Message: {1}'.format(
                        response.status_code,
                        response.json().get(
                            'errList', [response.json().get('msg', ERROR_MESSAGE)]
                        )[0]
                    )
                )
                raise Exception(exception_message)

            testset = response.json()['testset']
            return testset['nTestSetID']

        exception_message = (
            'Failed to get the test set details\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def _get_testset_id_by_params(self, testset_name):
        """Returns the id of the Test Set for the given Test Set name.

            Args:
                testset_name    (str)   --  Name of the Test Set

                    testset name should of the format:

                    **release_feature_os_applicationVersion_additionalProp**

                    if any property is missing in the testset name, it will be replaced by
                    **'' (empty strings)**

            Returns:
                int     -   id of the testset

            Raises:
                Exception:
                    if the key `testset` is not present in the response

                    if the response is not SUCCESS

        """
        testset_attributes = testset_name.split('_')

        if len(testset_attributes) < 5:
            testset_attributes += [''] * (5 - len(testset_attributes))

        release, feature, os_name, application_version, additional_prop = testset_attributes

        request_uri = self.api.format('testset')

        params = {
            "release": release,
            "feature": feature,
            "os": os_name,
            "applicationversion": application_version,
            "additionalprop": additional_prop
        }

        response = requests.get(request_uri, params=params, auth=self.auth)

        if response.status_code == 200:
            if 'testset' not in response.json():
                exception_message = (
                    'Test Set not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Message: {1}'.format(
                        response.status_code,
                        response.json().get(
                            'errList', [response.json().get('msg', ERROR_MESSAGE)]
                        )[0]
                    )
                )
                raise Exception(exception_message)

            testset = response.json()['testset']

            return testset['nTestSetID']

        exception_message = (
            'Failed to get the test set details\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    @property
    def domain(self):
        """Returns the value of domain attribute."""
        return self._domain

    @property
    def username(self):
        """Returns the value of username attribute."""
        return self._username

    @property
    def password(self):
        """Returns the value of password attribute."""
        return self._password

    @property
    def auth(self):
        """Returns the value of auth attribute."""
        return self._auth

    @property
    def api(self):
        """Returns the value of api attribute."""
        return self._api

    @property
    def features(self):
        """Returns the value of features attribute."""
        if not self._features:
            self.get_features()

        return list(self._features)

    def get_features(self):
        """Returns the list of features on EngWeb.

            Returns:
                list    -   list of feature names

            Raises:
                Exception:
                    if the key `features` is not present in the response

                    if the response is not SUCCESS

        """
        response = requests.get(self.api.format('features'), auth=self.auth)

        if response.status_code == 200:
            if 'features' not in response.json():
                exception_message = (
                    'Features not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Text: {1}'.format(
                        response.status_code, self._update_response(response.text)
                    )
                )
                raise Exception(exception_message)

            features = response.json()['features']

            for feature in features:
                self._features[feature['sFeatureName']] = feature['nFeatureID']

            return self.features

        exception_message = (
            'Failed to get the features\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def get_testsets(self, release, feature=''):
        """Returns the list of all the test sets for the specified release.
            Filters the test sets if the feature is also provided.

            Args:
                release     (str)   --  Release for the test set

                feature     (str)   --  Feature name as given in the features list

            Returns:
                dict    -   dictionary consisting of the testset name as the key,
                and testset id as its value

                    {
                        "testset1_name": "testset1_id",

                        "testset2_name": "testset2_id",

                        "testset3_name": "testset3_id",

                        "testset4_name": "testset4_id"
                    }

            Raises:
                Exception:
                    if the key `testsets` is not present in the response

                    if the response is not SUCCESS

        """
        request_uri = self.api.format('testsets?release={0}&feature={1}'.format(release, feature))
        response = requests.get(request_uri, auth=self.auth)

        if response.status_code == 200:
            if 'testsets' not in response.json():
                exception_message = (
                    'Test Sets not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Text: {1}'.format(
                        response.status_code, self._update_response(response.text)
                    )
                )
                raise Exception(exception_message)

            testsets = response.json()['testsets']

            testsets_dict = {}

            for testset in testsets:
                testset_name = '_'.join(
                    [
                        testset['sRelease'],
                        testset['sFeatureName'],
                        testset['sOSTypeName']
                    ]
                )

                if testset['sApplicationVersionName']:
                    testset_name += f'_{testset["sApplicationVersionName"]}'

                if testset['sAdditionalPropName']:
                    testset_name += f'_{testset["sAdditionalPropName"]}'

                testsets_dict[testset_name] = testset['nTestSetID']

            return testsets_dict

        exception_message = (
            'Failed to get the test sets\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def get_testset_id(self, testset_name):
        """Returns the id of the Test Set for the given Test Set name.

            Args:
                testset_name    (str)   --  Name of the Test Set

                testset name should either be the Test Set Display Name, or of the format:

                    **release_feature_os_applicationVersion_additionalProp**

                if any property is missing in the testset name, it will be replaced by
                **'' (empty strings)**

            Returns:
                int     -   id of the testset

            Raises:
                Exception:
                    if the key `testset` is not present in the response

                    if the response is not SUCCESS

        """
        try:
            return self._get_testset_id_by_display_name(testset_name)
        except Exception:
            return self._get_testset_id_by_params(testset_name)

    def get_testcases(self, testset_id):
        """Returns the list of all the test cases for the specified test set.

            Args:
                testset_id  (int)   --  ID for the Test Set to get the test cases of

            Returns:
                dict    -   dictionary consisting of the testcase name as the key,
                and testset id as its value

                    {
                        "testset1_name": "testset1_id",

                        "testset2_name": "testset2_id",

                        "testset3_name": "testset3_id",

                        "testset4_name": "testset4_id"
                    }

            Raises:
                Exception:
                    if the key `testcases` is not present in the response

                    if the response is not SUCCESS

        """
        request_uri = self.api.format('testcases?testset={0}'.format(testset_id))
        response = requests.get(request_uri, auth=self.auth)

        if response.status_code == 200:
            if 'testcases' not in response.json():
                exception_message = (
                    'Test Cases not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Text: {1}'.format(
                        response.status_code, self._update_response(response.text)
                    )
                )
                raise Exception(exception_message)

            testcases = response.json()['testcases']

            testcases_dict = {}

            for testcase in testcases:
                testcase_id = testcase['nTestCaseID']
                testcase_instance_id = testcase['nInstanceID']
                testcase_name = testcase['sTestCaseName']
                testcases_dict[testcase_id] = {
                    'name': testcase_name,
                    'instance_id': testcase_instance_id
                }

            return testcases_dict

        exception_message = (
            'Failed to get the test cases\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def get_testcase_details(self, testcase_id):
        """Returns the details of the test case for the given test case id.

            Args:
                testcase_id     (int)   --  ID of the Test Case

            Returns:
                dict    -   details dict for the test case

            Raises:
                Exception:
                    if the key `details` is not present in the response

                    if the response is not SUCCESS

        """
        request_uri = self.api.format('testcase/{0}'.format(testcase_id))
        response = requests.get(request_uri, auth=self.auth)

        if response.status_code == 200:
            if 'details' not in response.json():
                exception_message = (
                    'Test Case Details not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Message: {1}'.format(
                        response.status_code,
                        response.json().get(
                            'errList', [response.json().get('msg', ERROR_MESSAGE)]
                        )[0]
                    )
                )
                raise Exception(exception_message)

            return response.json()['details']

        exception_message = (
            'Failed to get the test case details\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def get_instance_id(self, testset_id, testcase_id):
        """Returns the Instance ID for the given test set, and test case id.

            Args:
                testset_id      (int)   --  ID of the Test Set

                testcase_id     (int)   --  ID of the Test Case

            Returns:
                int     -   instance ID for the test set and test case

            Raises:
                Exception:
                    if the key `details` is not present in the response

                    if the response is not SUCCESS

        """
        request_uri = self.api.format(
            'instance?testset={0}&testcase={1}'.format(testset_id, testcase_id)
        )
        response = requests.get(request_uri, auth=self.auth)

        if response.status_code == 200:
            if 'instance' not in response.json():
                exception_message = (
                    'Instance Details not returned in the API response\n'
                    'Response Status Code: {0}\n'
                    'Response Message: {1}'.format(
                        response.status_code,
                        response.json().get(
                            'errList', [response.json().get('msg', ERROR_MESSAGE)]
                        )[0]
                    )
                )
                raise Exception(exception_message)

            return response.json()['instance']['nInstanceID']

        exception_message = (
            'Failed to get the instance details\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def update_testcase_status(self, testset_id, testcase_id, instance_id, status, comments=''):
        """Updates the Test Case run status to the Quality Center.

            Args:
                testset_id      (int)   --  ID of the Test Set being run

                testcase_id     (int)   --  ID of the Test Case to update the status of

                instance_id     (int)   --  Instance ID for the Test Case and the Test Set

                status          (int)   --  Test Case run status

                    **1**, for SUCCESS

                    **0**, for FAILURE

                comments        (str)   --  Additional comments for the test case run (if any)

            Returns:
                bool    -   True, if updated the Test Case run status successfully

            Raises:
                Exception:
                    if the response is not SUCCESS

        """
        request_body = {
            "testset": testset_id,
            "testcase": testcase_id,
            "instance": instance_id,
            "status": status,
            "comments": comments
        }

        response = requests.post(
            self.api.format('automationrun'), auth=self.auth, json=request_body
        )

        if response.status_code == 200:
            return True

        exception_message = (
            'Failed to Update the Test Case run status\n'
            'Response Status Code: {0}\n'
            'Response Text: {1}'.format(
                response.status_code, self._update_response(response.text)
            )
        )
        raise Exception(exception_message)

    def update_qa(self, testset_name, testcase_id, status, comments=''):
        """Updates the Test Case run status to the Quality Center.

            Args:
                testset_name    (str)   --  Name of the Test Set

                testset name should either be the Test Set Display Name, or of the format:

                    **release_features_os_applicationVersion_additionalProp**

                if any property is missing in the testset name, it will be replaced by
                **'' (empty strings)**

                testcase_id     (int)   --  ID of the Test Case to update the status of

                status          (int)   --  Test Case run status

                    **1**, for SUCCESS

                    **0**, for FAILURE

                comments        (str)   --  Additional comments for the test case run (if any)

            Returns:
                bool    -   True, if updated the Test Case run status successfully

            Raises:
                Exception:
                    if the response is not SUCCESS

        """
        testset_id = self.get_testset_id(testset_name)
        instance_id = self.get_instance_id(testset_id, testcase_id)
        return self.update_testcase_status(testset_id, testcase_id, instance_id, status, comments)
