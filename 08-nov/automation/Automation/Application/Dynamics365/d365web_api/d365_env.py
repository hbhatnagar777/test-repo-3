from .constants import ENVIRONMENT_WHO_AM_I_ENDPOINT, ACCESSIBILITY_ERROR_CODE, \
    ACCESSIBILITY_ERROR_MESSAGE, ORG_WEB_API_URL, GET_ENVIRONMENT_PROP, GET_ENVIRONMENT_ENTITIES, \
    GET_ENVIRONMENT_ENTITIES_WITH_CHANGE_TRACKING_ENABLED, CURRENT_SIGNED_IN_USER_INFO, GLOBAL_DISCOVERY_ACCESS_URL_DEFAULT, \
    GLOBAL_DISCOVERY_ACCESS_URL_GCC, GET_ENVIRONMENT_PROP_USERID_PASS_DEFAULT, GET_ENVIRONMENT_PROP_USERID_PASS_GCC, CREDENTIAL_TYPE
from .web_req import PyWebAPIRequests
from .web_auth import Credentials
from .d365_entity import Entity
from Application.Dynamics365 import constants


class Environment:
    def __init__(self, credentials: Credentials, tenant_id="", env_id="", unique_name="",
                 env_url: str = "", api_url: str = "", env_name: str = "", friendly_name: str = str(), region=1):
        """
            Initialize the environment object for a particular Dynamics 365 environment
                Arguments:
                    credentials     (Credentials):  Credential object to access the table

                # If credentials type is Client one, user needs to pass the API URL or the organization URL
                # If credential type is user id and password, passing friendly name would also work
        """


        self._tenant_id = tenant_id
        self._id = env_id
        self._unique_name = unique_name
        self._env_name = env_name
        self._env_url = env_url
        self._api_url = api_url
        self._credentials = credentials
        self._friendly_name: str = friendly_name

        self._access_credentials = Credentials
        self._entities = None

        self._pyd365req = PyWebAPIRequests()
        self._cloud_region = region
        self.set_environment_properties()

    @property
    def is_accessible(self):
        """
            Property depicting if an environment is accessible or not
        :return:
            Accessibility status of the environment
        :rtype bool
        """
        return self._is_environment_accessible()

    def _is_environment_accessible(self):
        """
            Function to determine if an environment is accessible or not.
            :return: None
        """

        accessible_endpoint = ENVIRONMENT_WHO_AM_I_ENDPOINT % self.env_url
        response = self._pyd365req.make_webapi_request(method="GET", resource=self.env_url.join("/.default"),
                                                       access_endpoint=accessible_endpoint, credentials=self._credentials)
        if response.get('error', {}).get('code', "") == ACCESSIBILITY_ERROR_CODE or response.get('error', {}).get(
                'message', "").lower() == ACCESSIBILITY_ERROR_MESSAGE.lower():
            return False
        return True

    @property
    def api_url(self):
        """API URL for this environment"""
        return self._api_url

    @property
    def env_url(self):
        """URL for the environment"""
        return self._env_url

    @property
    def env_name(self):
        """Name of the environment"""
        return self._env_name

    @property
    def access_url(self):
        """Access URL for the Dynamics 365 environment"""
        return self.env_url

    @property
    def entities(self):
        """Entities in the environment"""
        if self._entities is None:
            self._entities = self.get_environment_entities()
        return self._entities

    @entities.setter
    def entities(self, value):
        self._entities = value

    def _get_environment_properties(self):

        access_endpoint = self.api_url + GET_ENVIRONMENT_PROP
        environment_resource = f"{self._api_url}/.default"

        response = self._pyd365req.make_webapi_request(method="GET", resource=environment_resource,
                                                       credentials=self._credentials,
                                                       access_endpoint=access_endpoint)
        return response

    def set_environment_properties(self):
        env_prop_response = self._get_environment_properties()
        self._set_environment_properties_from_resp(response=env_prop_response)

    def _set_environment_properties_from_resp(self, response):
        try:
            env_details = response['value'][0]
        except KeyError:
            env_details = response["Detail"]
        self._id = env_details.get('OrganizationId', self._id)
        self._env_url = env_details.get("Url", self._env_url)
        self._env_name = env_details.get('UrlName', self._env_name)
        self._unique_name = env_details.get('UniqueName', self._unique_name)
        self._tenant_id = env_details.get('TenantId', self._tenant_id)
        self._friendly_name = env_details.get("FriendlyName", self._friendly_name)

    def get_environment_entities(self, change_tracking_enabled=True, with_metadata=False, filter: str = None):
        """
            Method to get all the entities in the environment
                change_tracking_enables     (bool):     Get only those tables which have change tracking enabled
                with_metadata               (bool):     Whether to fetch table level metadata also
                filter                      (str):      Filter to be applied, if any
        """
        url = GET_ENVIRONMENT_ENTITIES % self.env_url
        resource_url = f"{self._api_url}/.default"
        if change_tracking_enabled:
            url = GET_ENVIRONMENT_ENTITIES_WITH_CHANGE_TRACKING_ENABLED % url

        if filter is not None:
            if not change_tracking_enabled:
                url = url + "?$filter=" + filter
            else:
                url = url + " and " + filter
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url)
        entities = self._create_entity_dict_from_resp(response=response, with_metadata=with_metadata)
        return entities

    def _create_entity_dict_from_resp(self, response, with_metadata=False):
        entities = dict()
        for entity_dict in response['value']:
            display_name = str()
            if not entity_dict.get("IsCustomEntity") and entity_dict.get("LogicalName") not in constants.ENTITIES_INCLUDED:
                continue
            try:
                display_name = entity_dict.get("DisplayName", {}).get("LocalizedLabels", [])[0].get(
                    "Label")
            except IndexError:
                display_name = entity_dict.get("LogicalName")
            entity = Entity(credentials=self._credentials, env_access_url=self.access_url, env_api_url=self.api_url,
                            logical_name=entity_dict["LogicalName"],
                            # display_name=entity_dict["DisplayName"]["LocalizedLabels"][0]["Label"])
                            display_name=display_name)
            if with_metadata:
                entity.entity_metadata = entity_dict
            entities[display_name] = entity
        return entities
