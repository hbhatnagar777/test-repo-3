from .web_auth import Credentials
from .constants import RECORD_MODIFY_DELETE
from .web_req import PyWebAPIRequests


class Record:
    """
        This is a class for representing a specific record present in a Dynamics 365 Entity
    """

    def __init__(self, credentials: Credentials, env_access_url: str, env_api_url: str,
                 r_id: str, e_collection_name: str):
        """
            Initialize the Record Object
                Arguments:
                    credentials         (Credentials):  Credential object to access the table attribute
                    env_access_url      (str):          URL to generate access token from
                        sample would be:
                            https://env-name.crm.dynamics.com
                    env_api_url         (str):          API endpoint for the particular environment
                        it is different from the access URL
                        sample would be:
                            https://env-name.crm.dynamics.com/<dynamics-version>/api
                    r_id                (str):          ID of the particular record in Dynamics 365

                    e_collection_name   (str):          Collection name of the entity
                        Required for create/ update/ delete operation

        """

        self._parent_entity_collection_name = e_collection_name
        self._record_id = r_id
        self._credentials = credentials
        self._env_access_url = env_access_url
        self._env_api_url = env_api_url
        self._record_data: dict = None
        self._pyd365req = PyWebAPIRequests()

    def modify_record(self, new_val: dict):
        """
            new_val         dict:   Value to be modified for the record.
        """
        url = RECORD_MODIFY_DELETE % (self._env_api_url, self._parent_entity_collection_name, self._record_id)
        resource_url = self._env_api_url + "/.default"
        response = self._pyd365req.make_webapi_request(method="PATCH", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url,
                                                       body=new_val)
        return response

    def delete_record(self):
        """Delete the record."""
        url = RECORD_MODIFY_DELETE % (self._env_api_url, self._parent_entity_collection_name, self._record_id)
        resource_url = self._env_api_url + "/.default"
        response = self._pyd365req.make_webapi_request(method="DELETE", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url)
        return response

    def get_record(self):
        """Get the record."""
        url = RECORD_MODIFY_DELETE % (self._env_api_url, self._parent_entity_collection_name, self._record_id)
        resource_url = self._env_api_url + "/.default"
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url)
        self.record_data = response
        return response

    @property
    def record_data(self):
        """Get the data for the record."""
        if self._record_data is None:
            self._record_data = self.get_record()
        return self._record_data

    @record_data.setter
    def record_data(self, data_dict: dict):
        """Set the value for the record."""
        self._record_data = data_dict

    @property
    def record_id(self):
        """Get the record ID."""
        return self._record_id