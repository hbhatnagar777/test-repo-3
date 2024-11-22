from .constants import GLOBAL_DISCOVERY_ACCESS_URL_DEFAULT, GLOBAL_DISCOVERY_ACCESS_URL_GCC,\
    GLOBAL_DISCOVERY_RESOURCE_URL_DEFAULT, GLOBAL_DISCOVERY_RESOURCE_URL_GCC, GLOBAL_DISCOVERY_ACCESS_ENDPOINT
from .web_req import PyWebAPIRequests
from .d365_env import Environment


class Organization:
    """
        This class would denote any Dynamics 365 Organization
    """

    def __init__(self, credentials, region=1):
        """
            Initializes the Organization Object
            :param credentials: Object of type Credential
                   region:  Cloud region for the client
        """
        self._credentials = credentials
        self.environments = dict()
        self._pyd365req = PyWebAPIRequests()
        self._cloud_region = region

    def _get_environments_dict_from_resp(self, response_list):
        env_dict = dict()
        for environment in response_list:
            env = Environment(credentials=self._credentials, tenant_id=environment['TenantId'],
                              env_id=environment['Id'], unique_name=environment['UniqueName'],
                              env_url=environment['Url'], friendly_name=environment['FriendlyName'],
                              env_name=environment['UrlName'], api_url=environment["ApiUrl"], region=self._cloud_region)
            env_dict[environment["FriendlyName"]] = env
        return env_dict

    def _get_environments_in_org(self):
        """
            Private class function to get the list of Dynamics 365 Environments present in
            the MSFT Organization/ Tenet
            :return: Dictionary of environments in the organization
                 Dictionary format:
                { <environment-friendly-name> :
                    <object of Environment class depicting that environment> }
        """
        instances = self._fetch_environments_in_org()
        self.environments = self._get_environments_dict_from_resp(response_list=instances)

    def get_organization_environments(self, is_accessible=False):
        """
            Function to get a dictionary of the environments present in the Dynamics 365 Organization

        :param is_accessible: Whether to get only accessible or all environments
            Default : false
            Accepted values:
                True / False
            if false:
                all environments discovered are returned
            if true:
                only accessible environments are returned

        :return: Dictionary of environments in the organization
                 Dictionary format:
                { <environment-friendly-name> :
                    <object of Environment class depicting that environment> }
        """
        self._get_environments_in_org()
        environment_dict = self.environments
        if is_accessible:
            for name, environment in self.environments.values():
                if not environment.is_accessible:
                    del environment_dict[name]
        return environment_dict

    def _fetch_environments_in_org(self):
        """
            This functions fetches the list of all environments in the Dynamics 365 Organization.
            :return: Response, from the global discovery service
        """

        if self._cloud_region == 1:
            response = self._pyd365req.make_webapi_request(method="GET",
                                                           access_endpoint=GLOBAL_DISCOVERY_ACCESS_ENDPOINT,
                                                           credentials=self._credentials,
                                                           resource=GLOBAL_DISCOVERY_ACCESS_URL_DEFAULT
                                                           )
        elif self._cloud_region == 2:
            response = self._pyd365req.make_webapi_request(method="GET",
                                                           access_endpoint=GLOBAL_DISCOVERY_ACCESS_URL_GCC,
                                                           credentials=self._credentials,
                                                           resource=GLOBAL_DISCOVERY_RESOURCE_URL_GCC
                                                           )
        return response['value']
