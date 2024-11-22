from .constants import ATTRIBUTE_METADATA, PICKLIST_OPTION_SET, GET_OPTION_SET_VALUE
from .web_auth import Credentials
from .web_req import PyWebAPIRequests


class Attribute:
    def __init__(self, credentials: Credentials, env_access_url: str, env_api_url: str,
                 logical_name: str, e_collection_name: str, e_logical_name: str):
        """
            Initialize the Attribute Object
                Arguments:
                    credentials         (Credentials):  Credential object to access the table attribute
                    env_access_url      (str):          URL to generate access token from
                        sample would be:
                            https://env-name.crm.dynamics.com
                    env_api_url         (str):          API endpoint for the particular environment
                        it is different from the access URL
                        sample would be:
                            https://env-name.crm.dynamics.com/<dynamics-version>/api
                    logical_name        (str):          Logical name of the attribute
                        required as it will dictate the endpoint for requests
                        sample would be:
                            https://env-name.crm.dynamics.com/accounts(firstName)
                    e_collection_name   (str):          Collection name of the entity
                        Required for create/ update/ delete operation
                    e_logical_name      (str):          Logical name of the entity
                        Required for fetching metadata/ picklist options etc operations
        """
        self._logical_name = logical_name
        self._target_attribute = str()
        self._env_access_url = env_access_url
        self._env_api_url = env_api_url
        self._parent_entity_collection_name = e_collection_name
        self._entity_logical_name = e_logical_name
        self._pyd365req = PyWebAPIRequests()
        self._credentials = credentials
        self._metadata: dict = None

    @property
    def logical_name(self):
        return self._logical_name

    @property
    def attribute_type(self):
        return self.get_entity_metadata_value(key="@odata.type")

    @property
    def attribute_ref_type(self):
        return self.get_entity_metadata_value(key="AttributeType")

    @property
    def is_required_for_form(self):
        return self.get_entity_metadata_value(key="IsRequiredForForm")

    @property
    def max_length(self):
        return self.get_entity_metadata_value(key="MaxLength")

    @property
    def schema_name(self):
        return self.get_entity_metadata_value(key="SchemaName")

    @property
    def target_attribute(self):
        return self.get_entity_metadata_value(key="Targets")

    @property
    def attribute_metadata(self):
        return self._metadata

    @attribute_metadata.setter
    def attribute_metadata(self, data_dict: dict):
        self._metadata = data_dict

    def get_entity_metadata_value(self, key):
        if self.attribute_metadata is None:
            self._get_attribute_metadata()

        if key in self.attribute_metadata.keys():
            return self.attribute_metadata[key]

    def _get_attribute_metadata(self):
        _endpoint = ATTRIBUTE_METADATA % (self._env_api_url, self._entity_logical_name, self._logical_name)
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=self._env_access_url,
                                                       credentials=self._credentials, resource=_endpoint)
        self.attribute_metadata = response

    def get_picklist_value_set(self):
        # if column is picklist type, then get the possible values
        _endpoint = PICKLIST_OPTION_SET % (self._env_api_url, self._entity_logical_name, self._logical_name)
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=self._env_access_url,
                                                       credentials=self._credentials, resource=_endpoint)
        _options = response["OptionSet"]["Options"]
        _option_set = list()
        for _option in _options:
            _option_set.append(_option["Value"])
        return _option_set

    def get_value_set(self):
        # if column is picklist type, then get the possible values
        _endpoint = GET_OPTION_SET_VALUE % (self._env_api_url, self._entity_logical_name,
                                            self._logical_name, self.attribute_type)
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=self._env_access_url,
                                                       credentials=self._credentials, resource=_endpoint)
        _options = response["OptionSet"]["Options"]
        _option_set = list()
        for _option in _options:
            _option_set.append(_option["Value"])
        return _option_set
