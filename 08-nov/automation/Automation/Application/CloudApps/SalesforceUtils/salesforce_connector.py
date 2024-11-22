# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing salesforce operations

SalesforceConnector: Connector class to perform salesforce operations

SalesforceConnector:
    __init__()                          --  initializes salesforce connector object

    reconnect()                         --  Connects to Salesforce API

    bulk_query()                        --  Runs a SOQL query using BULK API

    bulk_update()                       --  Updates records in a Salesforce Object using BULK API

    rest_query()                        --  Runs a SOQL query using REST API

    read_standard_object()              --  Retrieves a standard object definition from Salesforce Metadata API

    describe_object()                   --  Retrieves describe of an object from REST API

    create_test_object()                --  Creates a new Salesforce CustomObject and inserts data into it

    create_custom_object()              --  Creates a new Salesforce CustomObject with a single name Field of type Text

    create_custom_field()               --  Adds a CustomField with given label and Type text to Salesforce CustomObject

    create_parent_child_relationship()  --  Creates a parent-child relationship between the given Salesforce
    CustomObjects

    create_child_object()               --  Creates a new Salesforce CustomObject that is a child of given parent_object
    with relationship field label "{parent_object.label} Id"

    create_records()                    --  Creates new records in Salesforce CustomObject for incremental backup job

    create_files()                      --  Creates new files in Salesforce

    create_incremental_files()          --  Adds/Deletes/Modifies files in Salesforce

    modify_records()                    --  Updates records in data list in Salesforce and returns new records

    create_incremental_data()           --  Inserts/updates/deletes test data in Salesforce object

    create_field_for_incremental()      --  Creates new CustomField and inserts data into it

    validate_object_data_in_salesforce() -- Validates records in Salesforce

    validate_object_data()               -- Validates data for an object

    validate_object_exists_in_salesforce() -- Validates whether CustomObject exists in Salesforce

    validate_metadata_in_salesforce()   --  Validates metadata component in Salesforce

    validate_files_in_salesforce()      --  Validates files in Salesforce

    delete_custom_object()              --  Delete a CustomObject in Salesforce

    delete_custom_field()               --  Deletes Custom Field with given FullName from a Salesforce CustomObject

    delete_object_data()                --  Deletes records from Salesforce CustomObject for given Ids. If data is not
    provided, then queries and deletes all records from CustomObject

    download_metadata_zip()               --  Method to download metadata from salesforce

    update_field_permissions()            --  Updates field permissions for a Salesforce object

Instance attributes:
    **limits**          --  Salesforce limits

    **rest_limit**      --  Max daily limit for rest API calls
"""
import datetime
from base64 import b64encode
from time import sleep
from urllib.parse import urlparse
from simple_salesforce import Salesforce
from zeep.xsd.valueobjects import CompoundValue
from AutomationUtils.machine import Machine
from .base import SalesforceBase
from .constants import TEXT, CONTENT_VERSION, CONTENT_DOCUMENT, BULK_MAX_ROWS
from .decorator import SalesforceAPICall
from .data_generator import SalesforceDataGenerator
from io import BytesIO
from zipfile import ZipFile


def _label_to_full_name(label):
    """
    Creates a FullName for Custom Metadata component from label

    Args:
        label (str): Label of Metadata component

    Returns:
        str: FullName of Metadata component
    """
    return f"{label.replace(' ', '')}__c"


class SalesforceConnector(SalesforceBase):
    """Class to connect to Salesforce"""
    api_call = SalesforceAPICall()

    def __init__(self, tcinputs=None, commcell=None):
        """
        Constructor for the class. Pass commcell object to use CvConnector object. If tcinputs is not passed, then
        inputs will be read from config file.

        Args:
            commcell (Commcell): commcell object
            tcinputs (dict): testcase inputs

        Returns:
            None:
        """
        super().__init__(tcinputs, commcell)
        self.__sf = None
        self.__bulk = None
        self.__mdapi = None
        self.api_call.sf_connector = self
        self.__generator = SalesforceDataGenerator(self)
        self.__session_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000+0000')

    @property
    @api_call()
    def limits(self):
        """
        Gets limits from Salesforce

        Returns:
            dict[str, dict]:
        """
        return self.__sf.limits()

    @property
    def rest_limit(self):
        """
        Gets daily rest API limit for org

        Returns:
            int: rest API limit
        """
        return self.limits['DailyApiRequests']['Max']

    def reconnect(self, **kwargs):
        """
        Connects to Salesforce API and creates Salesforce object

        Args:
            kwargs (dict): Salesforce connection details to override the options in tcinputs/config

        Returns:
            None:
        """
        sf_options = self.updated_salesforce_options(**kwargs)
        domain = '.'.join(urlparse(sf_options.login_url).netloc.split('.')[:-2])
        self._log.info(f"Connecting to Salesforce API with user {sf_options.salesforce_user_name} and domain {domain}")
        self.__sf = Salesforce(
            username=sf_options.salesforce_user_name,
            password=sf_options.salesforce_user_password,
            security_token=sf_options.salesforce_user_token,
            domain=domain
        )
        self.__mdapi = self.__sf.mdapi
        self.__bulk = self.__sf.bulk
        self._log.info("Connection established with Salesforce successfully")

    def reset_session_time(self):
        """Resets session time for created date condition in queries"""
        self.__session_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000+0000')
        sleep(60)

    def __add_created_date_condition(self, query):
        """
        Adds a condition to only retrieve records that were modified after current salesforce helper session started

        Args:
            query (str): SOQL query

        Returns:
            str: Query with condition on LastModifiedDate
        """
        split_query = query.split()
        if 'where' in query.lower():
            where_index = query.lower().split().index('where') + 1
            return " ".join(
                split_query[:where_index] + ['CreatedDate >', self.__session_time, 'AND'] + split_query[where_index:])
        from_index = query.lower().split().index('from') + 2
        return " ".join(
            split_query[:from_index] + ['WHERE CreatedDate >', self.__session_time] + split_query[from_index:])

    def __handle_bulk_response(self, response):
        """
        Handles response from bulk insert/update/delete

        Args:
            response (list): Bulk response from simple_salesforce

        Returns:
            None:

        Raises:
            Exception: If response contains error messages

        Examples:
            Bulk response example:

            [[
                {'success': True, 'created': True, 'id': 'a055g000000WhFzAAK', 'errors': []},

                {'success': False, 'created': False, 'id': 'a055g000000WhFzAAJ',
                'errors': [{'statusCode': 'ExceededQuota', 'message': 'TotalRequests Limit exceeded.'}]}
            ]]
        """
        if not all(result['success'] for result in response):
            raise Exception("\n".join([
                f"""{result['id']}:
                    {', '.join([f"({error['statusCode']}, {error['message']})" for error in result['errors']])}"""
                for result in response if not result['success']
            ]))
        self._log.info(f"Bulk operation with {len(response)} records successful")

    @api_call()
    def bulk_query(self, query, current_session=True):
        """
        Runs a SOQL query using BULK API

        Args:
            query (str): SOQL query
            current_session (bool): If True, adds a condition to query records in current session else queries all
                records (Default True)

        Returns:
            list: List of dicts containing where each dict is a record
        """
        if current_session:
            query = self.__add_created_date_condition(query)
        from_index = query.lower().split().index('from')
        full_name = query.split()[from_index + 1]
        self._log.info(f"Running query \"{query}\" on object {full_name}")
        response = getattr(self.__bulk, full_name).query(query)
        self._log.info(f"Retrieved {len(response)} records")
        return [{key: value for key, value in row.items() if key != 'attributes'} for row in response]

    @api_call()
    def bulk_insert(self, full_name, data):
        """
        Inserts records in a Salesforce object using BULK API

        Args:
            full_name (str): FullName of Salesforce Object
            data (list[dict]): List of data to update

        Returns:
            list[data]: data list with 'Id' field added

        Raises:
            Exception: If response contains error messages
        """
        self._log.info(f"Doing BULK insert on {full_name}({data[0].keys()}) with {len(data)} records")
        return_data = list()
        itr = len(data) // BULK_MAX_ROWS
        if len(data) % BULK_MAX_ROWS != 0:
            itr += 1
        for i in range(itr):
            response = getattr(self.__bulk, full_name).insert(data[i * BULK_MAX_ROWS: (i + 1) * BULK_MAX_ROWS])
            self.__handle_bulk_response(response)
            self._log.info(f"Successfully inserted {len(response)} records")
            return_data.extend([{'Id': result['id'], **row} for result, row in
                                zip(response, data[i * BULK_MAX_ROWS: (i + 1) * BULK_MAX_ROWS])])
        return return_data

    @api_call()
    def bulk_update(self, full_name, data):
        """
        Updates records in a Salesforce Object using BULK API

        Args:
            full_name (str): FullName of Salesforce Object
            data (list[dict]): List of data to update

        Returns:
            None:

        Raises:
            Exception: If response contains error messages
        """
        self._log.info(f"Doing BULK update on {full_name}({data[0].keys()}) with {len(data)} records")
        response = getattr(self.__bulk, full_name).update(data)
        self.__handle_bulk_response(response)

    @api_call()
    def rest_query(self, query, current_session=True):
        """
        Runs a SOQL query using REST API

        Args:
            query (str): SOQL query
            current_session (bool): If True, adds a condition to query records in current session else queries all
                records (Default True)

        Returns:
            list: List of dicts containing where each dict is a record
        """
        if current_session:
            query = self.__add_created_date_condition(query)
        self._log.info(f"Running query \"{query}\"")
        response = self.__sf.query_all(query)
        self._log.info(f"Retrieved {len(response['records'])} records")
        return [{key: value for key, value in row.items() if key != 'attributes'} for row in response['records']]

    @api_call()
    def rest_insert(self, full_name, record):
        """
        Inserts a record in Salesforce using rest API and returns id

        Args:
            full_name (str): Fullname of Salesforce object
            record (dict): Dict containing record to insert

        Returns:
            str: Id of new record
        """
        response = getattr(self.__sf, full_name).create(record)
        if response['success']:
            return response['id']
        raise Exception(f"Error inserting record into {full_name}: {response['errors']}")

    @api_call()
    def read_standard_object(self, full_name):
        """
        Retrieves a standard object definition from Salesforce Metadata API

        Args:
            full_name (str): Fullname of Standard Object

        Returns:
            CompoundValue: Salesforce object describes
        """
        return self.__mdapi.CustomObject.read(full_name)

    @api_call()
    def describe_object(self, full_name):
        """
        Retrieves describe of an object from REST API

        Args:
            full_name (str): FullName of Salesforce Object

        Returns:
            (collections.OrderedDict): Describes of Object
        """
        return getattr(self.__sf, full_name).describe()

    def create_test_object(self, label, field_labels=None, rec_count=None):
        """
        Creates a new Salesforce CustomObject and inserts data into it

        Args:
            label (str): Label for new CustomObject
            field_labels (list): Labels for any CustomFields to be created
            rec_count (int): Number of records to insert ( > 0) (Default 500)

        Returns:
            tuple[zeep.xsd.valueobjects.CompoundValue, list]: The new Salesforce object, and a list of dicts containing
                    data that was inserted

        Raises:
            Exception: If rec_count <= 0
        """
        if not rec_count:
            rec_count = self.rec_count
        sf_object = self.create_custom_object(label)
        if field_labels:
            for field_label in field_labels:
                sf_object = self.create_custom_field(sf_object, field_label)
        data = self.create_records(sf_object.fullName, rec_count=rec_count)
        return sf_object, data

    @api_call()
    def create_custom_object(self, label):
        """
         Creates a new Salesforce CustomObject with a single name Field of type Text

        Args:
            label (str): Label of new custom object

        Returns:
            CompoundValue: Salesforce CustomObject
        """
        full_name = _label_to_full_name(label)
        custom_object = self.__mdapi.CustomObject.read(full_name)
        if custom_object.fullName:
            self._log.info(f"CustomObject with FullName {full_name} exists in Salesforce")
            self.delete_custom_object(full_name)
        custom_object = self.__mdapi.CustomObject(
            fullName=full_name,
            label=label,
            pluralLabel=f"{label}s",
            deploymentStatus=self.__mdapi.DeploymentStatus("Deployed"),
            sharingModel=self.__mdapi.SharingModel("ReadWrite"),
            nameField=self.__mdapi.CustomField(label="Name", type=self.__mdapi.FieldType(TEXT))
        )
        self._log.info(f"Creating custom object {custom_object.fullName} in Salesforce")
        self.__mdapi.CustomObject.create(custom_object)
        self._log.info(f"{custom_object.fullName} created successfully")
        return self.__mdapi.CustomObject.read(custom_object.fullName)

    @api_call()
    def create_custom_field(self, sf_object, label, type=TEXT, reference_obj=None):
        """
        Adds a CustomField with given label and Type text to Salesforce CustomObject

        Args:
            sf_object (CompoundValue): A Salesforce object
            label (str): Label for new Custom Field
            type (str): Type of Custom Field (Default Text)
            reference_obj (CompoundValue): Parent CustomObject
        Returns:
            CompoundValue: The updated Salesforce CustomObject

        Raises:
            Exception: If a CustomField with given label already exists in object
        """
        field_full_name = _label_to_full_name(label)
        if any(field.fullName.lower() == field_full_name.lower() for field in sf_object.fields):
            raise Exception(f"'{label}' already exists in {sf_object.fullName}")
        if type in ("Lookup", "MasterDetail"):
            custom_field = self.__mdapi.CustomField(
                fullName=f"{sf_object.fullName}.{field_full_name}",
                label=reference_obj.label,
                referenceTo=reference_obj.fullName,
                relationshipLabel=reference_obj.pluralLabel,
                relationshipName=reference_obj.pluralLabel.replace(" ", ""),
                type=self.__mdapi.FieldType(type)
            )
        elif type != "TextArea":
            custom_field = self.__mdapi.CustomField(
                fullName=f"{sf_object.fullName}.{field_full_name}",
                label=label,
                type=self.__mdapi.FieldType(type),
                length=100
            )
        else:
            custom_field = self.__mdapi.CustomField(
                fullName=f"{sf_object.fullName}.{field_full_name}",
                label=label,
                type=self.__mdapi.FieldType(type)
            )
        self._log.info(f"Creating custom field {custom_field.fullName} in Salesforce")
        self.__mdapi.CustomField.create(custom_field)
        self._log.info(f"{custom_field.fullName} created successfully")
        self.__mdapi.Profile.update(self.__mdapi.Profile(
            fullName=self.profile,
            fieldPermissions=[self.__mdapi.ProfileFieldLevelSecurity(
                editable=True, field=custom_field.fullName, readable=True
            )]
        ))
        self._log.info(f"Set field {custom_field.fullName} as editable")
        return self.__mdapi.CustomObject.read(sf_object.fullName)

    @api_call()
    def update_field_permissions(self, sf_object, field_name):
        """
        Updates field permissions for a Salesforce object

        Args:
            sf_object (CompoundValue): A Salesforce object fullname
            field_name (str): API name of custom field

        """
        self._log.info(f"Updating field permissions for {sf_object}.{field_name}")
        self.__mdapi.Profile.update(self.__mdapi.Profile(
            fullName=self.profile,
            fieldPermissions=[self.__mdapi.ProfileFieldLevelSecurity(
                editable=True, field=f"{sf_object}.{field_name}", readable=True
            )]
        ))
        self._log.info(f"Field permissions updated for {sf_object}.{field_name}")

    @api_call()
    def create_parent_child_relationship(self, child_object, parent_object, relation_type="MasterDetail"):
        """
        Creates a parent-child relationship between the given Salesforce CustomObjects

        Args:
            child_object (CompoundValue): Child CustomObject
            parent_object (CompoundValue): Parent CustomObject
            relation_type (str): Type of relationship (Default MasterDetail)
        Returns:
            CompoundValue: Updated child CustomObject
        """
        relationship_field = self.__mdapi.CustomField(
            fullName=f"{child_object.fullName}.{parent_object.fullName}",
            label=parent_object.label,
            referenceTo=parent_object.fullName,
            relationshipLabel=child_object.pluralLabel,
            relationshipName=child_object.pluralLabel.replace(" ", ""),
            type=self.__mdapi.FieldType(relation_type)
        )
        self._log.info(f"Creating new relationship {relationship_field.fullName} in Salesforce")
        self.__mdapi.CustomField.create(relationship_field)
        self._log.info(f"{relationship_field.fullName} created successfully")
        if relation_type == "Lookup":
            self.update_field_permissions(child_object.fullName, parent_object.fullName)
        return self.__mdapi.CustomObject.read(child_object.fullName)

    def create_child_object(self, label, parent_object, field_labels=None, rec_count=None,
                            relation_type="MasterDetail"):
        """
        Creates a new Salesforce CustomObject that is a child of given parent_object with relationship field label
        "{parent_object.label} Id"

        Args:
            label (str): Label for new object
            parent_object (CompoundValue): Parent CustomObject
            field_labels (list): List of labels of any additional fields to create in child object
            rec_count (int): Number of records to insert into child CustomObject (Default 500)
            relation_type (str): Type of relationship (Default MasterDetail)

        Returns:
            tuple[CompoundValue, list]: The new Salesforce object, and a list of dicts containing data that was inserted
        """
        if not rec_count:
            rec_count = self.rec_count
        child_object = self.create_custom_object(label)
        child_object = self.create_parent_child_relationship(child_object, parent_object, relation_type)
        if field_labels:
            for field_label in field_labels:
                child_object = self.create_custom_field(child_object, field_label)
        child_data = self.__generator.generate_data(self.describe_object(child_object.fullName), rec_count=rec_count)
        child_data = self.bulk_insert(child_object.fullName, child_data)
        return child_object, child_data

    def create_records(self, sf_object, fields=None, rec_count=None):
        """
        Creates new records in Salesforce CustomObject

        Args:
            sf_object (str): FullName of Salesforce Object
            fields (list): List of Fullnames of fields to insert data into (Default None, and all fields will be
                    populated)
            rec_count (int): Number of records to insert into CustomObject (Default 500)

        Returns:
            list[dict]: List of dicts of data inserted
        """
        if not rec_count:
            rec_count = self.rec_count
        data = self.__generator.generate_data(self.describe_object(sf_object), fields, rec_count=rec_count)
        return self.bulk_insert(sf_object, data)

    def create_files(self, rec_count=None):
        """
        Creates new files in Salesforce

        Args:
            rec_count (int): Number of files to create (Default is retrieved from config)

        Returns:
            tuple[dict[dict], list[dict]]: ContentVersion, ContentDocument. ContentVersion is a dict with keys as ids
                and records containing Title, PathOnClient, ContentLocation and VersionData fields as values.
                ContentDocument is a list of dicts as queried from Salesforce with the following fields - Id, Title,
                FileType, LatestPublishedVersionId
        """
        if not rec_count:
            rec_count = self.rec_count
        self._log.info(f"Creating {rec_count} files in Salesforce")
        content_version = {
            self.rest_insert(CONTENT_VERSION, record): record
            for record in self.__generator.generate_content_version(rec_count)
        }
        content_document = self.rest_query("SELECT Id, Title, FileType, LatestPublishedVersionId FROM ContentDocument")
        content_document = [row for row in content_document if row['LatestPublishedVersionId'] in content_version]
        self._log.info(
            f"New files: {', '.join(map(lambda document: document['Title'], content_document[:rec_count]))}"
        )
        return content_version, content_document

    def create_incremental_files(self, content_version, content_document, rec_count=None):
        """
        Adds/Deletes/Modifies files in Salesforce

        Args:
            content_document (list[dict]): existing ContentDocument records
            content_version (dict[dict]): existing ContentVersion
            rec_count (int): Number of files to add/modify/delete

        Returns:
            tuple[dict[dict], list[dict]]: ContentVersion, ContentDocument. ContentVersion is a dict with keys as ids
                and records containing Title, PathOnClient, ContentLocation and VersionData fields as values.
                ContentDocument is a list of dicts as queried from Salesforce with the following fields - Id, Title,
                FileType, LatestPublishedVersionId
        """
        self._log.info("Creating incremental files")
        if not rec_count:
            rec_count = int(len(content_document) / 10)
        # Delete rec_count files
        self.delete_object_data(CONTENT_DOCUMENT, content_document[:rec_count])
        for version_id in map(lambda row: row['LatestPublishedVersionId'], content_document[:rec_count]):
            content_version.pop(version_id, None)
        self._log.info(
            f"Deleted files: {', '.join(map(lambda document: document['Title'], content_document[:rec_count]))}"
        )
        del content_document[:rec_count]
        # Update rec_count files
        self._log.info(f"Updating {rec_count} files in Salesforce")
        update_version = self.__generator.generate_content_version(
            file_names=[record['Title'] for record in content_document[:rec_count]]
        )
        update_version = [
            {**version, 'ContentDocumentId': document['Id']}
            for version, document in zip(update_version, content_document[:rec_count])
        ]
        update_version = {self.rest_insert(CONTENT_VERSION, record): record for record in update_version}
        for version_id in map(lambda row: row['LatestPublishedVersionId'], content_document[:rec_count]):
            content_version.pop(version_id, None)
        content_version.update(update_version)
        update_document = {value['ContentDocumentId']: key for key, value in update_version.items()}
        content_document[:rec_count] = [
            {**row, 'LatestPublishedVersionId': update_document[row['Id']]} for row in content_document[:rec_count]
        ]
        self._log.info(
            f"Updated files: {', '.join(map(lambda document: document['Title'], content_document[:rec_count]))}"
        )
        # Create rec_count new files
        new_version, new_document = self.create_files(rec_count=rec_count)
        content_version.update(new_version)
        content_document.extend(new_document)
        return content_version, content_document

    def modify_records(self, sf_object, data):
        """
        Updates records in data list in Salesforce and returns new records

        Args:
            sf_object (str): FullName of Salesforce object
            data (list[dict]): Records to modify

        Returns:
            list[dict]: Updated records
        """
        update_data = self.__generator.generate_data(self.describe_object(sf_object), list(data[0].keys()), len(data))
        update_data = [{'Id': old['Id'], **new} for old, new in zip(data, update_data)]
        self.bulk_update(sf_object, update_data)
        return update_data

    def create_incremental_data(self, sf_object, data=None, fields=None, rec_count=None, add=None, modify=None,
                                delete=None):
        """
        Inserts/updates/deletes test data in Salesforce object

        Args:
             sf_object (str): FullName of Salesforce object
             data (list[dict]): Data in sf_object (Default None, and will be queried from Salesforce)
             fields (list): List of Fullnames of fields to insert data for (Default None, and all fields will be used)
             rec_count (int): Number of records to insert
             add (int): Number of records to add
             modify (int): Number of records to modify
             delete (int): Number of records to delete

        Returns:
            list[dict]: Updated records in Salesforce
        """
        if not rec_count:
            rec_count = min(BULK_MAX_ROWS, int(self.rec_count / 10))
        if not data:
            if not fields:
                describe = self.describe_object(sf_object)
                fields = [field['name'] for field in describe['fields'] if field['updateable']]
            data = self.bulk_query(f"SELECT Id, {', '.join(fields)} FROM {sf_object}")
        else:
            if not fields:
                fields = list(data[0].keys())
        self.delete_object_data(sf_object, data[:delete or rec_count])
        del data[:delete or rec_count]
        data[:modify or rec_count] = self.modify_records(sf_object, data[:modify or rec_count])
        data.extend(self.create_records(sf_object, fields, rec_count=(add or rec_count)))
        return data

    def create_field_for_incremental(self, sf_object, label, data=None):
        """
        Creates new CustomField and inserts data into it

        Args:
            sf_object (CompoundValue): Salesforce CustomObject
            label (str): Label of new CustomField to be created
            data (list): List of dicts of data already in sf_object. If not provided, will be queried from Salesforce

        Returns:
            tuple[CompoundValue, list]: The new Salesforce object, and a list of dicts containing updated data.
                                        If data was not passed as parameter, this will only contain id and the new
                                        CustomField that was created
        """
        if not data:
            data = self.bulk_query(f"SELECT Id from {sf_object.fullName}")
        sf_object = self.create_custom_field(sf_object, label)
        inc_data = self.__generator.generate_data(
            self.describe_object(sf_object.fullName),
            field_names=[_label_to_full_name(label)],
            rec_count=len(data))
        data = [{**row, **inc_row} for row, inc_row in zip(data, inc_data)]
        self.bulk_update(sf_object.fullName, data)
        return sf_object, data

    def __quick_validate(self, local_data, sf_data, name_field='Name'):
        """
        Validates that local data matches data in Salesforce using python dictionaries

        Args:
            local_data (list): Local data before deletion
            sf_data (list): Salesforce data after restore

        Returns:
            None:

        Raises:
            Exception: if local data does not match Salesforce data
        """
        local_data = {row[name_field]: row for row in local_data}
        sf_data = {row[name_field]: row for row in sf_data}
        for name, row in local_data.items():
            if name not in sf_data:
                raise Exception(f"Validation in Salesforce failed. Record {row} does not exist in Salesforce.")
            if not all(val == sf_data[name][key] for key, val in row.items() if key != 'Id'):
                raise Exception(f"Validation in Salesforce failed. Record {row} in given data does not match record "
                                f"{sf_data[name]} in Salesforce")

    def __deep_validate(self, local_data, sf_data):
        """
        Validates that local data matches data in Salesforce using brute force

        Args:
            local_data (list): Local data before deletion
            sf_data (list): Salesforce data after restore

        Returns:
            None:

        Raises:
            Exception: if local data does not match Salesforce data
        """
        for local_row in local_data:
            if not any(all(sf_row[key] == local_row[key] for key in local_row if key != 'Id') for sf_row in sf_data):
                raise Exception(f"Validation in Salesforce failed. Record {local_row} does not exist in Salesforce.")

    @api_call(out_of_place=True)
    def validate_object_data_in_salesforce(self, full_name, data, fields=None, **kwargs):
        """
        Validates records in Salesforce

        Args:
            full_name (str): Fullname of Salesforce object
            data (list): List of dicts of records to validate
            fields (list): Fields to use for validation
            kwargs (dict): Salesforce organization connection details to override value set in tcinputs/config

        Keyword Args:
            login_url (str): Salesforce login url
            salesforce_user_name (str); Salesforce user name for out of place execution
            salesforce_user_password (str): Salesforce password for out of place execution
            salesforce_user_token (str): Salesforce API token for out of place execution

        Returns:
            None:

        Raises:
            Exception: If validation fails
        """
        self._log.info(f"Validating object {full_name} in salesforce")
        if not fields:
            describe = self.describe_object(full_name)
            fields = [field['name'] for field in describe['fields']
                      if field['name'] in data[0].keys() - {'Id'} and field['type'] != 'reference']
        local_data = [{key: val for key, val in row.items() if key in fields} for row in data]
        sf_data = self.bulk_query(f"SELECT {', '.join(fields)} FROM {full_name}")
        if not kwargs:
            if (n_local := len(local_data)) != (n_sf := len(sf_data)):
                raise Exception(f"Validation in Salesforce failed. Number of records in local data ({n_local}) do not "
                                f"match number of records retrieved from Salesforce ({n_sf})")
            self._log.info("Number of records in Salesforce match number of records in local data")
        try:
            self.validate_object_data(local_data, sf_data)
        except Exception as exp:
            self._log.error("Validation failed")
            self._log.error(f"Backed up records were {data}")
            self._log.error(f"Records retrieved from Salesforce are {sf_data}")
            raise exp
        self._log.info("Validation in Salesforce successful")

    def validate_object_data(self, local_data, sf_data, fields=None):
        """
        Validates records for an object

        Args:
            local_data (list[dict]): source data for validation
            sf_data (list[dict]): destination data for validation
            fields (list): fields to use for validation
        Returns:
            None:

        Raises:
            Exception: If validation fails

        """
        if fields:
            local_data = [{key: val for key, val in row.items() if key in fields} for row in local_data]
            sf_data = [{key: val for key, val in row.items() if key in fields} for row in sf_data]

        if 'Name' in local_data[0].keys():
            self._log.info(f"Found name field in data, using quick validation")
            self.__quick_validate(local_data, sf_data)
        else:
            self._log.info(f"Name field not found. Using deep validation")
            self.__deep_validate(local_data, sf_data)

    @api_call(out_of_place=True)
    def validate_dictionary_data_masking_policy(self, sobject, field, **kwargs):
        """
        Validate out of place restore with data masking policy

        Args:
            sobject (str): Name of Salesforce object
            field (str): Field on which dictionary data masking policy exists
            **kwargs (dict): Out of place salesforce credentials

        Keyword Args:
            login_url (str): Salesforce login url
            salesforce_user_name (str); Salesforce user name for out of place execution
            salesforce_user_password (str): Salesforce password for out of place execution
            salesforce_user_token (str): Salesforce API token for out of place execution
            source_data (list[dict]): Source data to verify when connection to access node fails

        Returns:
            None:

        Raises:
            Exception: if validation fails
        """
        values = []
        try:
            self._log.info(f"Establishing connection with access node: {self.infrastructure_options.access_node}")
            access_node = Machine(self.infrastructure_options.access_node, self._commcell)
            self._log.info("Connected to access node successfully")
            dictionary_path = f"{access_node.get_registry_value('Base', 'dBASEHOME')}/CvDmDictionaries/"
            if access_node.check_file_exists(f"{dictionary_path}{sobject.lower()}.{field.lower()}.csv"):
                dictionary_path += f"{sobject.lower()}.{field.lower()}.csv"
            else:
                dictionary_path += f"{field.lower()}.csv"
            self._log.info(f"Retrieving data masking dictionary for object {sobject}, field {field} from path "
                           f"{dictionary_path} on access node {self.infrastructure_options.access_node}")
            values = access_node.read_file(dictionary_path).split('\n')[1:-1]
            values = [val.replace('\r', '') for val in values]
            values = [val.replace('"', '') for val in values]
            self._log.info(f"Read {len(values)} values from dictionary file")
            self._log.debug(f"Dictionary values: {values}")
        except Exception:
            self._log.info("Unable to connect with access node,"
                           " verifying only the destination data is not same as source")
        sf_data = self.bulk_query(f"SELECT {field} FROM {sobject}")
        if len(values) != 0:
            if any((val := record[field]) not in values for record in sf_data):
                raise Exception(f"Validation failed for field {field} in object {sobject}. {val} does not match "
                                "any of the values given in dictionary file.")
        else:
            if any((val := record[field]) in [rec[field] for rec in kwargs.get('source_data')] for record in sf_data):
                raise Exception(f"Validation failed for field {field} in object {sobject}."
                                f" There is a record at source with {field}: {val}")
        self._log.info(f"Dictionary data masking policy for field {field} in object {sobject} validated successfully")

    @api_call(out_of_place=True)
    def validate_object_exists_in_salesforce(self, sf_object, **kwargs):
        """
        Validates whether CustomObject exists in Salesforce

        Args:
            sf_object (CompoundValue): CustomObject to validate
            kwargs (dict): Salesforce organization connection details to override value set in tcinputs/config

        Keyword Args:
            salesforce_user_name (str); Salesforce user name for out of place execution
            salesforce_user_password (str): Salesforce password for out of place execution
            salesforce_user_token (str): Salesforce API token for out of place execution

        Returns:
            None:

        Raises:
            Exception: If given object does not exist in Salesforce
        """
        self._log.info(f"Validating Custom Object {sf_object.fullName} in Salesforce")
        cloud_object = self.__mdapi.CustomObject.read(sf_object.fullName)
        if not cloud_object.fullName:
            raise Exception(f"Custom Object {sf_object.fullName} does not exist in Salesforce")
        self._log.info(f"Validation successful. Custom Object {cloud_object.fullName} exists in Salesforce")

    def __recursive_validate(self, component1, component2):
        """
        Recursively validates metadata component

        Args:
            component1 (CompoundValue): Local copy of metadata definition
            component2 (CompoundValue): Metadata definition retrieved from cloud

        Returns:
            bool: True if validation successful, else False
        """
        if not component1 and not component2:
            return True
        if isinstance(component1, CompoundValue):
            return all(self.__recursive_validate(val, component2[key]) for key, val in component1.__values__.items())
        if isinstance(component1, list):
            if 'fullName' not in component1[0]:
                return all(any(self.__recursive_validate(val1, val2) for val2 in component2) for val1 in component1)
            return all(self.__recursive_validate(val1, val2) for val1, val2 in
                       zip(sorted(component1, key=lambda x: x.fullName), sorted(component2, key=lambda x: x.fullName)))
        return component1 == component2

    @api_call(out_of_place=True)
    def validate_metadata_in_salesforce(self, metadata_component, **kwargs):
        """
        Validates metadata component in Salesforce

        Args:
            metadata_component (CompoundValue): Metadata component to validate
            kwargs (dict): Salesforce organization connection details to override value set in tcinputs/config

        Keyword Args:
            salesforce_user_name (str); Salesforce user name for out of place execution
            salesforce_user_password (str): Salesforce password for out of place execution
            salesforce_user_token (str): Salesforce API token for out of place execution

        Returns:
            None:

        Raises:
            Exception: If validation fails
        """
        sf_component = getattr(self.__mdapi, type(metadata_component).__name__).read(metadata_component.fullName)[0]
        if not self.__recursive_validate(metadata_component, sf_component):
            raise Exception(f"Metadata validation failed. Local metadata component {metadata_component.fullName} does "
                            f"not match with its corresponding component in Salesforce")
        self._log.info(f"Successfully validated metadata component {metadata_component.fullName} in Salesforce")

    @api_call(out_of_place=True)
    def validate_files_in_salesforce(self, content_version, content_document, **kwargs):
        """
        Validates files in Salesforce

        Args:
            content_version (dict[dict]): ContentVersion
            content_document (list[dict]): ContentDocument records with fields -
                Title, FileType, LatestPublishedVersionId

        Keyword Args:
            salesforce_user_name (str); Salesforce user name for out of place execution
            salesforce_user_password (str): Salesforce password for out of place execution
            salesforce_user_token (str): Salesforce API token for out of place execution

        Returns:
            None:

        Raises:
            Exception: If validation fails
        """
        self._log.info(f"Validating {len(content_document)} files in Salesforce")
        # Query ContentDocument
        sf_content_document = self.bulk_query(
            f"SELECT Title, FileType, LatestPublishedVersionId FROM {CONTENT_DOCUMENT}"
        )
        # Verify number of files match
        if (n_sf := len(sf_content_document)) != (n_local := len(content_document)):
            self._log.warn(f"Warning: Number of records in local data ({n_local}) do not match number of records "
                           f"retrieved from Salesforce ({n_sf})")
        combined_content_document = {row['Title']: row for row in content_document}
        # Verify that for every file in local data, a file exists on Salesforce
        for document in sf_content_document:
            try:
                combined_content_document[document['Title']]['RestoredVersion'] = document['LatestPublishedVersionId']
            except KeyError:
                self._log.warn(f"Warning: {document['Title']} not found in local data")
        # Verify file contents match
        for document in combined_content_document.values():
            new_version = self.__sf.ContentVersion.get(
                f"{document['RestoredVersion']}/VersionData",
                parse_json=False
            )
            if b64encode(new_version.encode()).decode() != \
                    content_version[document['LatestPublishedVersionId']]['VersionData']:
                raise Exception(f"Local version of {document['Title']} does not match version on Salesforce")
            self._log.info(f"{document['Title']} validated successfully")
        self._log.info(f"File validation complete")

    @api_call(out_of_place=True)
    def delete_custom_object(self, full_name, data=None, **kwargs):
        """
        Delete a CustomObject in Salesforce

        Args:
            full_name (str): FullName of CustomObject to delete
            data (list): List of dicts of data in object. Must contain all records in object to free up maximum space in
                            Salesforce. If not provided, will be queried from Salesforce
            kwargs (dict): Salesforce organization connection details to override value set in tcinputs/config

        Returns:
            None:
        """
        self.delete_object_data(full_name, data)
        self._log.info(f"Deleting custom object {full_name} in Salesforce")
        self.__mdapi.CustomObject.delete(full_name)
        self._log.info(f"{full_name} deleted successfully")

    @api_call()
    def delete_custom_field(self, sf_object, full_name=None):
        """
        Deletes Custom Field with given FullName from a Salesforce CustomObject

        Args:
            sf_object (CompoundValue): A Salesforce object
            full_name (str): FullName/label of CustomField to be deleted. If this parameter is not provided, then
                             deletes the first field in sf_object by default.

        Returns:
            CompoundValue: The updated Salesforce CustomObject

        Raises:
            Exception:
                If no CustomField with given full_name exists in sf_object
                If no field exists in sf_object
        """
        if not sf_object.fields:
            raise Exception(f"{sf_object.fullName} does not have any fields")
        if full_name and any(field.label == full_name for field in sf_object.fields):
            full_name = [field for field in sf_object.fields if field.label == full_name][0].fullName
        elif full_name and all(field.fullName != full_name for field in sf_object.fields):
            raise Exception(f"No field with fullName {full_name} exists in "
                            f"{sf_object.fullName}({[field.fullName for field in sf_object.fields]})")
        if not full_name:
            full_name = f"{sf_object.fullName}.{sf_object.fields[0].fullName}"
        else:
            full_name = f"{sf_object.fullName}.{full_name}"
        self._log.info(f"Deleting custom field {full_name} in Salesforce")
        self.__mdapi.CustomField.delete(full_name)
        self._log.info(f"{full_name} deleted successfully")
        return self.__mdapi.CustomObject.read(sf_object.fullName)

    @api_call(out_of_place=True)
    def delete_object_data(self, full_name, data=None, hard_delete=True, current_session=True, **kwargs):
        """
       Deletes records from Salesforce CustomObject for given Ids. If data is not provided, then queries and deletes all
       records from CustomObject

        Args:
            full_name (str): FullName of Object
            data (list): List of dicts of records in Object containing at least 'Id' field
            hard_delete (bool): If True, performs a hard delete API call, else performs a delete API call
            current_session (bool): If True, deletes all records, including old

        Returns:
            None:
        """
        if not data:
            data = self.bulk_query(f"SELECT Id FROM {full_name}", current_session)
        elif 'Id' not in data[0]:
            field_name = list(data[0].keys())[0]
            field_data = set([row[field_name] for row in data])
            sf_data = self.bulk_query(
                query=f"SELECT Id, {field_name} FROM {full_name}",
                current_session=current_session
            )
            data = [{'Id': row['Id']} for row in sf_data if row[f'{field_name}'] in field_data]
        else:
            data = [{'Id': row['Id']} for row in data]
        if len(data) == 0:
            self._log.info("There are no records to be deleted. Skipping deletion")
            return
        if hard_delete:
            self._log.info(f"Hard deleting {len(data)} records from {full_name}")
            response = getattr(self.__bulk, full_name).hard_delete(data)
        else:
            self._log.info(f"Deleting {len(data)} records from {full_name}")
            response = getattr(self.__bulk, full_name).delete(data)
        try:
            self.__handle_bulk_response(response)
        except Exception as exp:
            self._log.info("Unable to delete all the records, likely due to salesforce generated records")
            self._log.error(exp.__str__().replace("\n", "\t"))
            return
        self._log.info("Delete completed successfully")

    @api_call(out_of_place=True)
    def download_metadata_zip(self, package):
        """
        Method to download metadata from salesforce

        Args:
            package (dict[str, list]): Dict containing member type as key and list of members as list

        Returns:
            Object of ZipFile
        """
        self._log.info("Creating metadata request")
        req_id, status = self.__mdapi.retrieve("test", unpackaged=package)
        self._log.info(f"Created metadata request request_id: {req_id}")
        while status in ('InProgress', 'Queued', 'Pending'):
            status, _, _ = self.__mdapi.check_retrieve_status(req_id)
        self._log.info(f"Request {req_id} got processed, retrieving data")
        _, _, _, data = self.__mdapi.retrieve_zip(req_id)
        self._log.info(f"Retrieved metadata zip")
        file = BytesIO(data)
        return ZipFile(file, "r")
