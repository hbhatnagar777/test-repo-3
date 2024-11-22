from .web_req import PyWebAPIRequests
from .web_auth import Credentials
from .constants import GET_ALL_RECORDS_FOR_ENTITY, GET_ENTITY_METADATA, \
    GET_INDIVIDUAL_ENTITY_RECORD, ENTITY_ATTRIBUTES_NAME, CREATE_RECORD, RECORD_MODIFY_DELETE
from .d365_rec import Record
from .d365_attr import Attribute


class Entity:
    """
        Entity Represents a Table in a Dynamics 365 CRM Environment.
    """

    def __init__(self, credentials: Credentials, env_access_url: str, env_api_url: str, logical_name: str,
                 display_name: str = str()):
        """
            Initialize the Entity Object
                Arguments:
                    credentials     (Credentials):  Credential object to access the table
                    env_access_url  (str):          URL to generate access token from
                        sample would be:
                            https://env-name.crm.dynamics.com
                    env_api_url     (str):          API endpoint for the particular environment
                        it is different from the access URL
                        sample would be:
                            https://env-name.crm.dynamics.com/<dynamics-version>/api
                    logical_name    (str):          Logical name of the table
                        required as it will dictate the endpoint for requests
                        sample would be:
                            https://env-name.crm.dynamics.com/accounts
                    display_name    (str):          display name of the table
        """
        self._credentials = credentials
        self._env_access_url = env_access_url
        self._env_api_url = env_api_url
        self._entity_metadata: dict = None
        self._logical_name = logical_name
        self._display_name = display_name
        self._pyd365req = PyWebAPIRequests()
        self._primary_attribute_name: str = str()
        # set some attributes
        self._primary_attribute_id = str()
        self._is_system_entity: bool

        self._attributes: dict = None
        self._required_attributes: list = None

    @property
    def entity_metadata(self):
        """
            Metadata for the particular entity/ table
            Metadata comes handy, in cases like:
                fetch the primary key for the table: used as dictionary key in
                    fetching all/ some table record
                whether the entity is a custom entity or not
                fetching the logical collection name: endpoint to be
                    used for creating/ modifying records
        """
        return self._entity_metadata

    @entity_metadata.setter
    def entity_metadata(self, value):
        """
            Set the value for metadata
        """
        self._entity_metadata = value

    def get_entity_metadata_value(self, key):
        """
            Get the value for a particular key from the table attribute
        """
        if self.entity_metadata is None:
            self.get_entity_metadata()

        if key in self.entity_metadata.keys():
            return self.entity_metadata[key]

    @property
    def logical_name(self):
        """Logical name of the table"""
        return self._logical_name

    @property
    def schema_name(self):
        return self.get_entity_metadata_value(key="SchemaName")

    @property
    def env_api_url(self):
        """API URL for the table's environment"""
        return self._env_api_url

    @property
    def env_access_url(self):
        """Access URL for the table's environment"""
        return self._env_access_url

    @property
    def entity_collection_name(self):
        """
            Logical collection name for the table
                logical collection name is used for create/ modify endpoints
            example:
                account ->  accounts
                entity  ->  entities
        """
        return self.get_entity_metadata_value(key="LogicalCollectionName")

    @property
    def is_system_entity(self):
        """
            Whether the table is a system entity or not
        """
        if self.entity_metadata is None:
            self.get_entity_metadata()
        return not self.get_entity_metadata_value(key='IsCustomEntity')

    def get_entity_metadata(self, select_columns: list = None):
        """
            Get the metadata for the entity
            :param      select_columns:     if metadata is required for selected columns only
            :return:    entity_metadata:    Dictionary of metadata for the current entity
        """
        _metadata_url = GET_ENTITY_METADATA % (self.env_api_url, self.logical_name)
        resource_url = self.env_api_url + "/.default"
        select_filter = str()
        if select_columns is not None:
            select_filter = ",".join(select_columns)
            _metadata_url = _metadata_url + "?$select=" + select_filter
        response = self._pyd365req.make_webapi_request(method="GET", access_endpoint=_metadata_url,
                                                       credentials=self._credentials, resource=resource_url)
        self.entity_metadata = response

    @property
    def primary_attribute_id(self):
        """
            Returns the primary key/ primary attribute ID for this entity.
        """
        self._primary_attribute_id = self._primary_attribute_id if self._primary_attribute_id \
            else self.get_entity_metadata_value(key='PrimaryIdAttribute')
        return self._primary_attribute_id

    def get_all_records(self, linked_records=False):
        """
            Get all the records for that particular Dynamics 365 Entity
            :return:    dict: dictionary with record is as key and record data as field
        """
        _table_url = self.get_entity_metadata_value(key="LogicalCollectionName")
        get_all_records_url = GET_ALL_RECORDS_FOR_ENTITY % (self.env_api_url, _table_url)
        resource_url = self.env_api_url + "/.default"
        completed = False
        records = dict()
        while not completed:
            record_res = self._pyd365req.make_webapi_request(method="GET", credentials=self._credentials,
                                                             resource=resource_url,
                                                             access_endpoint=get_all_records_url)
            if '@odata.nextLink' in record_res:
                get_all_records_url = record_res.get('@odata.nextLink')
            else:
                completed = True
            record_dict = self._handle_get_entity_response(response=record_res)
            # records.extend(record_dict)
            records = {**records, **record_dict}
        return records

    def get_record(self, record_id: str, columns: list = None):
        """
            Get a particular record belonging to this entity/
            :param record_id:   ID of the record to be fetched
            :param columns:     List of columns to be fetched.
            :return:            Record attribute corresponding to that Dynamics 365 record.
        """
        _fetch_entity_record_url = GET_INDIVIDUAL_ENTITY_RECORD % (
            self.env_api_url, self.entity_collection_name, record_id)
        _resource_url = self.env_api_url + "/.default"
        if columns is not None:
            select_filter = ",".join(columns)
            _fetch_entity_record_url = _fetch_entity_record_url + "?$select=" + select_filter
        record_res = self._pyd365req.make_webapi_request(method="GET", credentials=self._credentials,
                                                         resource=_resource_url,
                                                         access_endpoint=_fetch_entity_record_url)
        return self._handle_get_entity_response(response=record_res)

    def get_records(self, filters: list = None, count: int = -1, columns: list = None):
        """
            This function would return table records on the basis of the provided filters.
            filter:     <list<str>>     List of filter to be applied
            count       <int>           Number of records to be fetched
            columns     <list<str>>     List of columns to be fetched
        """
        _table_url = self.entity_metadata.get("LogicalCollectionName")
        endpoint = GET_ALL_RECORDS_FOR_ENTITY % (self.env_api_url, _table_url)
        if filters or (count > 0) or columns:
            endpoint = endpoint + "?"
            modified = False
            if columns:
                _cols = ",".join(columns)
                endpoint = endpoint + "$select=" + _cols
                modified = True

            if count > 0:
                endpoint = endpoint + "&$top={}".format(count) if modified else endpoint + "$top={}".format(count)
                modified = True
            if filters:
                _filters = " and ".join(filters)
                endpoint = endpoint + "&$filter={}".format(count) if modified else endpoint + "$filter={}".format(count)

        record_res = self._pyd365req.make_webapi_request(method="GET", credentials=self._credentials,
                                                         resource=endpoint,
                                                         access_endpoint=self.env_access_url)
        return self._handle_get_entity_response(response=record_res)

    def _handle_get_entity_response(self, response: dict):
        """
            Method to create a 'Reccord' instance, for the row data received from Dynamics 365
        """
        records: dict = dict()
        if 'value' not in response:
            record_id: str = response[self.primary_attribute_id]
            record = Record(credentials=self._credentials, env_api_url=self.env_api_url,
                            env_access_url=self.env_access_url, r_id=record_id,
                            e_collection_name=self.entity_collection_name)
            record.record_data = response
            return record
        for record_dict in response['value']:
            record_id: str = record_dict[self.primary_attribute_id]
            record = Record(credentials=self._credentials, env_api_url=self.env_api_url,
                            env_access_url=self.env_access_url, r_id=record_id,
                            e_collection_name=self.entity_collection_name)
            record.record_data = record_dict
            records[record_id] = record
        return records

    def create_record(self, data: dict, return_id: bool = False):
        """
            Create a record for this entity/
            :param data:        data dictionary of the created record
            :param return_id:   whether to return the ID of the newly created record
            :return:            NONE
        """
        url = CREATE_RECORD % (self._env_api_url, self.entity_collection_name)
        resource_url = self._env_api_url + "/.default"
        response = self._pyd365req.make_webapi_request(method="POST", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url, body=data)
        return response

    def delete_record(self, record_id: str):
        """
            Delete a record for this entity/
            :param record_id:   ID of the record to be deleted.
            :return: None
        """
        url = RECORD_MODIFY_DELETE % (self.env_api_url, self.entity_collection_name, record_id)
        resource_url = self.env_api_url + "/.default"
        response = self._pyd365req.make_webapi_request(method="DELETE", access_endpoint=url,
                                                       credentials=self._credentials, resource=resource_url)
        return response

    def get_entity_attributes(self, compulsory_attributes: bool = False):
        """
            This function would return all the attributes/ columns for this entity.
            compulsory_attributes   bool    :Get list of compulsory attributes
        """
        _req_url = ENTITY_ATTRIBUTES_NAME % (self.env_api_url, self.logical_name)
        if compulsory_attributes is True:
            _req_url = "{}&$filter=RequiredLevel/Value eq 'ApplicationRequired'".format(_req_url)
        _attr_res = self._pyd365req.make_webapi_request(method="GET", credentials=self._credentials,
                                                        resource=_req_url,
                                                        access_endpoint=self.env_access_url)
        _env_attributes = self._handle_get_entity_attribute_response(get_attr_response=_attr_res)
        return _env_attributes

    def _handle_get_entity_attribute_response(self, get_attr_response: dict):
        attributes: dict = dict()
        for attr_dict in get_attr_response['value']:
            logical_name: str = attr_dict["LogicalName"]
            attribute_dict = Attribute(logical_name=logical_name, e_collection_name=self.entity_collection_name,
                                       e_logical_name=self.logical_name, env_api_url=self.env_api_url,
                                       credentials=self._credentials, env_access_url=self.env_access_url)
            attributes[logical_name] = attribute_dict
        return attributes

    @property
    def attributes(self):
        """Attributes/ columns for this table"""
        if self._attributes is None:
            self._attributes = self.get_entity_attributes()
        return self._attributes

    def update_record(self, record, values):
        """
            Update a record for this entity
            :param record:        Record to be modified
            :param values:        Value with which the properties are to be modified
            :return:            NONE
        """
        url = RECORD_MODIFY_DELETE % (self._env_api_url, self.entity_collection_name, record)

        response = self._pyd365req.make_webapi_request(method="PATCH", access_endpoint=self._env_access_url,
                                                       credentials=self._credentials, resource=url, body=values)
        return response


