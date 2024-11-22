""" helper class for starting Subscription in Metallic Ring

    SaaSSubscriptionHelper:

        __init__()                              --  Initializes client group Ring Helper

        start_o365_trial()                      --  Starts the Subscription for tenant

        get_o365_enterprise_plan()              -- get o365 enterprise plan

        get_server_plan()                       -- get metallic server plan



"""
import json
from AutomationUtils.config import get_config
from AutomationUtils import logger
from MetallicRing.Utils import Constants as cs
from MetallicHub.Utils import Constants as h_cs


_START_TRIAL_CONFIG = get_config(json_path=h_cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub.start_trial_config


class SaaSSubscriptionHelper():
    """Class for starting trial for tenant"""

    def __init__(self, commcell):
        """Initializes the Start Subscription helper class"""
        self._commcell = commcell
        self._cvpysdk_object = commcell._cvpysdk_object
        self._auth_token = self._commcell.auth_token
        self.log = logger.get_log()

    def _response_not_success(self, response):
        """Helper method to raise exception when response is not 200 (ok)

            Raises:
                Exception:
                    Response was not success
        """
        raise Exception(f"Response not success {response}")

    def start_o365_trial(self, lh_base_url):
        """Starts Subscription for Office 365 for tenant

            Args:
                lh_base_url  --Light house base url
            Returns:
                None
        """
        payload = {
            "CommandCenterUrl__c": f"http://{self._commcell.webconsole_hostname}",
            "ProductType__c": cs.ProductType.O365.value,
            "SubscriptionType__c": cs.TRIAL
        }

        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "commcell-name": self._commcell.commserv_name
        }

        url = f"{lh_base_url}{_START_TRIAL_CONFIG.SUBSCRIPTION_ENDPOINT}"

        self.log.info(f"Sending request to URL [{url}] with data [{payload}]")
        flag, response = self._cvpysdk_object.make_request(
            method='POST', url=url, payload=payload, headers=headers
        )

        if flag:
            if response.json():
                if "data" in response.json():
                    error_code = response.json().get("data", {}).get("errorCode", None)
                    if error_code != 0:
                        raise Exception("Start O365 trial failed")
                if 'error' in response.json():
                    error_string = response.json().get("error", {}).get("message", {})
                    err_str = 'Failed to start subscription\nError: "{0}"'.format(error_string)
                    raise Exception(err_str)
        else:
            self._response_not_success(response)

        self.log.info("Getting the status of trial")
        flag, response = self._cvpysdk_object.make_request(
            method='GET', url=url, headers=headers
        )
        if flag:
            if response.json() and 'data' in response.json():
                if 'subscriptions' in response.json().get("data", {}):
                    subscriptions = response.json()["data"]["subscriptions"]
                    if "IsActive__c" in subscriptions[0] and "Id" in subscriptions[0]:
                        self.log.info("Trial started successfully")
                    else:
                        raise Exception("Subscription failed")
            else:
                error_string = response.json().get("error", {}).get("message", {})
                raise Exception(f"Failed to get subscription status, Error {error_string}")
        else:
            self._response_not_success(response)

    def get_o365_enterprise_plan(self):
        """ Get O365 Standards and Enterprise plans

            Returns:
                (str)   --  O365 Enterprise plans
        """
        headers = {
            'Authtoken': self._auth_token
        }
        payload = json.dumps({})
        url = f"https://{self._commcell.webconsole_hostname}{_START_TRIAL_CONFIG.MSP_EXCHANGE_PLAN_ENDPOINT}"

        self.log.info(f"Sending request to URL [{url}] with data [{payload}] to get O365 plans")
        flag, response = self._cvpysdk_object.make_request(
            method='POST', url=url, payload=payload, headers=headers
        )
        if flag:
            if response.json():
                error_code = response.json().get("error_code", None)
                if error_code != 0:
                    error_string = response.json().get("error_message", {})
                    raise Exception('Failed to start subscription\nError: "{0}"'.format(error_string))
        else:
            self._response_not_success(response)

        self.log.info("Getting office 365 enterprise plan")
        flag, response = self._cvpysdk_object.make_request(
            method='GET', url=url, headers=headers
        )
        if flag:
            if response.json():
                error_code = response.json().get("error_code", None)
                if error_code != 0:
                    error_string = response.json().get("error_message", {})
                    raise Exception('Failed to start subscription\nError: "{0}"'.format(error_string))
                elif 'data' in response.json() and 'plans' in response.json().get("data", {}):
                    self.o365_plans = response.json()['data']['plans']
        else:
            self._response_not_success(response)
        o365_enterprise_plan = [plan["planName"] for plan in self.o365_plans
                                if "enterprise-metallic-o365-plan" in plan["planName"]][0]
        self.log.info(f"{o365_enterprise_plan} plan created ")
        return o365_enterprise_plan

    def get_server_plan(self):
        """ Get metallic server plan

                    Returns:
                        (str)   --  metallic server plan
                """
        headers = {
            'Authtoken': self._auth_token
        }
        payload = {
            "regionId": cs.RegionId.EASTUS2_ID.value
        }
        url = f"https://{self._commcell.webconsole_hostname}{_START_TRIAL_CONFIG.MSP_O365_PLAN_URL}"

        self.log.info(f"Sending request to URL [{url}] with data [{payload}] to get server plan")

        flag, response = self._cvpysdk_object.make_request(
            method='POST', url=url, payload=payload, headers=headers
        )
        if flag:
            if response.json():
                error_code = response.json().get("error_code", None)
                if error_code != 0:
                    error_string = response.json().get("error_message", {})
                    raise Exception('Failed to start subscription\nError: "{0}"'.format(error_string))
                elif 'data' in response.json() and 'plan' in response.json().get("data", {}):
                    self.server_plan = response.json().get("data", {}).get("plan", {})
                    self.log.info(f"{self.server_plan.get("planName", {})} plan created")
        else:
            self._response_not_success(response)
        return self.server_plan["planName"]
