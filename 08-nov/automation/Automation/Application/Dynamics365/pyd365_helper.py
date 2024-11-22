# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking Dynamics 365 APIs.

CVInstance, CVRecord, CVTable, D365APIHelper are the classes defined in this file.

CVInstance: Class for all Dynamics 365 CRM Instance,

CVRecord: Class for all Dynamics 365 CRM Record,

CVTable: Class for all Dynamics 365 CRM Tables

D365APIHelper: Class for performing all Dynamics 365 CRM Third party library operations

"""
import random
import threading
import time
import math
from .d365web_api.d365_entity import Entity
from .d365web_api.d365_env import Environment
from .d365web_api.d365_rec import Record
from .d365web_api.web_req import Credentials
from .d365web_api.d365_org import Organization
from . import constants
from ..Office365.o365_data_gen import O365DataGenerator
from collections import defaultdict
from .d365web_api.user import Users


class D365APIHelper(object):
    """ Wrapper class for performing all third party Dynamics 365 Package operations"""

    def __init__(self, d365_object):
        """Initializes the D365APIHelper object.

                Args:
                    d365_object  (Object)  --  instance of CVDynamics365 class


                Returns:
                    object  --  instance of D365APIHelper class
        """
        self.tc_object = d365_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__

        self.d365_online_user = d365_object.d365_online_user
        self.d365_online_passwd = d365_object.d365_online_password
        self.client_id = d365_object.azure_app_id
        self.client_secret = d365_object.azure_app_secret
        self.tenant_id = d365_object.azure_tenant_id
        self.cloud_region = d365_object.cloud_region

        self.credentials = Credentials(client_id=self.client_id, client_secret=self.client_secret,
                                       tenant_id=self.tenant_id)
        self.organization = Organization(credentials=self.credentials, region=self.cloud_region)
        # self.users = Users(self.credentials)
        self._d365_data_gen = O365DataGenerator(logger_obj=self.log)

    def get_instances_in_tenant(self):
        """
            Method to get a list of Instances in the Dynamics 365 CRM Environment

        Returns:
            instances_list  (list)--    List of Instances in the Dynamics 365 Organization

        """
        _organization = Organization(credentials=self.credentials, region=self.cloud_region)
        environments = _organization.get_organization_environments()

        return environments.keys()

    def get_tables_in_instance(self, instance: Environment = None, instance_name: str = str()):
        """
            Method to get a list of tables in the Dynamics 365 CRM Instance
        Args:
            instance: <Environment>:     Instance object denoting the Dynamics 365 CRM Instance
            instance_name:      <str>:  Name of the Dynamics 365 CRM Instance
                if CVInstance object passed, then instance name is not required
        Returns:
            environment_entities    <dict>: Dictionary of all the tables in the Instance
                Format:
                    <key, value>
                    key: Logical Name of the Table
                    value: Instance of pys365.Entity denoting that particular table

        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities(filter=constants.QUERY_TABLE_FILTERS)

        return tables

    def get_table_properties(self, table_name: str, instance_name: str, instance: Environment = None):
        """
            Method to get the properties for a particular Dynamics 365 CRM Table
        Args:
            table_name:             <str>:      Logical Name of the Dynamics 365 CRM Table
            instance_name:          <str>:      Name of the instance to which the table belongs to
            instance:               <obj>:      Instance of the Dynamics 365 CRM Environment

        Returns:
            table_records:          <dict>:     Dictionary of Table records
                Format:
                    <record_id, record_object>
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table = tables.get(table_name)
        entities = table.get_all_records()
        return entities

    @staticmethod
    def get_friendly_name_of_tables(tables_dict: dict):
        """
            Method to get the friendly name of the tables from the Table Response
        Args:
            tables_dict:        <dict>:         Dictionary of tables, in the environment, as returned by the

        Returns:
            table_friendly_name <list(str)>:    Friendly name for the tables in the Environment
        """
        fr_tables = list()
        for table_name, table_details in tables_dict.items():
            if table_details._display_name == "":
                fr_tables.append(table_details.logical_name)
            else:
                fr_tables.append(table_details._display_name)
        for not_processed_table in constants.TABLES_NOT_PROCESSED:
            fr_tables.remove(not_processed_table)
        return fr_tables

    def create_related_records(self, source_table, related_tables, instance_name):
        """
            Args:
                source_table:       <str>:      Name of the source table
                related_tables:     <str>:      Comma separated string of all tables to be related to
                instance_name:      <str>:      Name of the instance where the tables belong to
            Returns:
                None
        """
        _instance = Environment(credentials=self.credentials, env_name=instance_name, region=self.cloud_region)
        _instance.set_environment_properties()
        tables = _instance.get_environment_entities(change_tracking_enabled=True)
        source_table_obj = tables[source_table]
        source_table_records = source_table_obj.get_all_records()
        dest_tables_records = defaultdict(list)
        for dest_table in related_tables.split(','):
            dest_table_records = tables[dest_table].get_all_records()
            for record in dest_table_records:
                dest_tables_records[dest_table].append([record, dest_table_records[record]])

        count = 0
        values = {}
        for record in source_table_records:
            for table in dest_tables_records:
                values[str(tables[table].schema_name) + str('@odata.bind')] = '/' + str(
                    tables[table].entity_collection_name) + '(' + str(dest_tables_records[table][count // 2][0]) + ')'
            source_table_obj.update_record(record, values)
            count += 1

    def create_table_records(self, table_name: list, instance_name: str, number_of_records: int = 10):
        """
            Method to create records for a table
        Args:
            table_name:         <str>:      Logical Name for the table for which record is to be created
            instance_name:      <str>:      Name of the Dynamics 365 instance to which the table belongs to
            number_of_records:  <int>:      Number of records to be created
                Default Value: 10

        Returns:
            None
        """
        _processed_table_list: list = list()  # Add system entities: business unit ID, users, currency to this list
        _instance = Environment(credentials=self.credentials, env_name=instance_name, region=self.cloud_region)
        _instance.set_environment_properties()
        tables = _instance.get_environment_entities(change_tracking_enabled=True)
        if table_name:
            self._create_table_record(tables[table_name], number_of_records=number_of_records)
        else:
            for _table_name, table_obj in tables.items():
                self.log.info("Creating Record for Table: {}".format(_table_name))
                self._create_table_record(table_obj, number_of_records=number_of_records)

    def _create_table_record(self, table_obj: Entity, number_of_records: int = 10):
        """
            Method to create records in a table
            Args:
                table_obj:          <obj>:      Object of the table
                number_of_records:  <int>:      Number of records to be created

            Returns:
                None
        """
        required_attributes = table_obj.get_entity_attributes(compulsory_attributes=True)
        for record in range(number_of_records):
            data = {}
            for attribute in required_attributes:
                if required_attributes[attribute].attribute_ref_type == "String":
                    data[attribute] = attribute + str(int(time.time()))
                elif required_attributes[attribute].attribute_ref_type in ["BigInt", "Integer"]:
                    data[attribute] = int(time.time())
                else:
                    raise Exception("This data type of field isn't being handled")
            table_obj.create_record(data)
            time.sleep(2)


    def cleanup_table(self, table_name: str, instance_name: str, table_entities: dict = None):
        """
            Method to cleanup/ delete all records of a table
        Args:
            table_name:         <str>:      Logical Name for the table
            instance_name:      <str>:      Name of the Dynamics 365 Instance
            table_entities:     <dict>:     Dictionary of table entities to be deleted  (optional)

        Returns:

        """
        _instance = Environment(credentials=self.credentials, env_name=instance_name, region=self.cloud_region)
        tables = _instance.get_environment_entities()
        table = tables.get(table_name)
        if not table_entities:
            table_entities = table.get_all_records()

        class myThread(threading.Thread):
            def __init__(self, entity_id):
                threading.Thread.__init__(self)
                self._entity_id = entity_id

            def run(self):
                table.delete_record(record_id=self._entity_id)

        _table_entities_id = list(table_entities.keys())
        # convert record keys to a list
        threads = list()

        iter_count = math.ceil(len(_table_entities_id) / 50)
        _index = 0
        # run 50 threads parallely
        for _ in range(iter_count):
            for entity_id in _table_entities_id[
                             _index:min(_index + 50,
                                        len(_table_entities_id))]:  # batch over 50 rows at aa time
                thread = myThread(entity_id)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            _index = _index + 50
        time.sleep(15)

    def create_accounts(self, instance_name: str, number_of_records: int = 100, instance: Environment = None):
        """
            Method to create records for account table
            Args:
                instance_name:      <str>:      Name of the Dynamics 365 instance to which the table belongs to
                number_of_records:  <int>:      Number of records to be created
                    Default Value: 100
                instance:           <obj>:      Instance of the Dynamics 365 CRM Environment

            Returns:
                None
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table_name = "Account"
        table = tables.get(table_name)

        class D365Thread(threading.Thread):
            def __init__(self, threadID, d365_data_gen):
                threading.Thread.__init__(self)
                self.threadID = threadID
                self._d365_data_gen = d365_data_gen

            def run(self):
                print("Thread: {} started executing".format(self.threadID))
                data = {
                    "name": self._d365_data_gen.gen_name(),
                    "websiteurl": self._d365_data_gen.gen_website_url(),
                    "description": self._d365_data_gen.get_random_unicode(length=100),
                    "fax": self._d365_data_gen.gen_number(),

                }
                table.create_record(data=data)
                print("Thread: {} finished executing".format(self.threadID))

        iter_count = number_of_records // 25
        threads = list()
        for i in range(iter_count):
            for _ in range(25):
                thread = D365Thread(_, self._d365_data_gen)
                thread.start()
                threads.append(thread)

        for t in threads:
            t.join()
        time.sleep(5)

    def create_contacts(self, instance_name: str, number_of_records: int = 100, instance: Environment = None):
        """
            Method to create records for contact table
            Args:
                instance_name:      <str>:      Name of the Dynamics 365 instance to which the table belongs to
                number_of_records:  <int>:      Number of records to be created
                    Default Value: 100
                instance:           <obj>:      Instance of the Dynamics 365 CRM Environment
            Returns:
                None
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table_name = "Contact"
        table = tables.get(table_name)

        class D365Thread(threading.Thread):
            def __init__(self, thread_ID, d365_data_gen):
                threading.Thread.__init__(self)
                self.threadID = thread_ID
                self._d365_data_gen = d365_data_gen

            def run(self):
                print("Thread: {} started executing".format(self.threadID))
                data = {

                    "firstname": self._d365_data_gen.gen_name().split(' ')[0],
                    "lastname": self._d365_data_gen.gen_name().split(' ')[-1],
                    "middlename": self._d365_data_gen.gen_name().split(' ')[1],
                    "emailaddress1": self._d365_data_gen.gen_email_addr(),
                    "mobilephone": self._d365_data_gen.gen_number(),
                    "creditlimit": self._d365_data_gen.gen_double()
                }
                table.create_record(data=data)
                print("Thread: {} finished executing".format(self.threadID))

        iter_count = number_of_records // 25
        threads = list()
        for i in range(iter_count):
            for _ in range(25):
                thread = D365Thread(_, self._d365_data_gen)
                thread.start()
                threads.append(thread)

        for t in threads:
            t.join()
        time.sleep(5)

    def delete_accounts(self, instance_name: str, instance: Environment = None):
        """
            Method to delete records for account table
            Args:
                instance_name:      <str>:      Name of the Dynamics 365 instance to which the table belongs to
                instance:           <obj>:      Instance of the Dynamics 365 CRM Environment

            Returns:
                None
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table_name = "Account"
        table = tables.get(table_name)

        _accounts = table.get_all_records()

        class D365Thread(threading.Thread):
            def __init__(self, _entity_id):
                threading.Thread.__init__(self)
                self._entity_id = _entity_id

            def run(self):
                table.delete_record(record_id=self._entity_id)

        _table_entities_id = list(_accounts.keys())
        # convert record keys to a list
        threads = list()

        iter_count = math.ceil(len(_table_entities_id) / 50)
        _index = 0
        # run 50 threads parallely
        for _ in range(iter_count):
            for entity_id in _table_entities_id[
                             _index:min(_index + 50, len(_table_entities_id))]:  # batch over 50 rows at aa time
                thread = D365Thread(entity_id)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            _index = _index + 50
            threads = list()  # empty the list of threads
        time.sleep(15)

    def delete_contacts(self, instance_name: str, instance: Environment = None):
        """
            Method to delete records for contact table
            Args:
                instance_name:      <str>:      Name of the Dynamics 365 instance to which the table belongs to
                instance:           <obj>:      Instance of the Dynamics 365 CRM Environment

            Returns:
                None
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table_name = "Contact"
        table = tables.get(table_name)

        _contacts = table.get_all_records()

        class D365Thread(threading.Thread):
            def __init__(self, _entity_id):
                threading.Thread.__init__(self)
                self._entity_id = _entity_id

            def run(self):
                table.delete_record(record_id=self._entity_id)

        _table_entities_id = list(_contacts.keys())
        # convert record keys to a list
        threads = list()

        iter_count = math.ceil(len(_table_entities_id) / 50)
        _index = 0
        # run 50 threads parallely
        for _ in range(iter_count):
            for entity_id in _table_entities_id[_index:min(_index + 50, len(_table_entities_id))]:
                # batch over 50 rows at aa time
                thread = D365Thread(entity_id)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            _index = _index + 50
            threads = list()
        time.sleep(15)

    def modify_accounts(self, instance_name: str):
        """
            Method to modify all the accounts in an instance

            Arguments:
                instance_name       (str)--     Name of the Dynamics 365 Instance.
        """
        _instance = Environment(credentials=self.credentials, env_name=instance_name)
        tables = _instance.get_environment_entities()
        table_name = "Account"
        table = tables.get(table_name.lower())

        _accounts = table.get_all_records()

        class D365Thread(threading.Thread):
            def __init__(self, _entity_id, record, d365_data_gen):
                threading.Thread.__init__(self)
                self._entity_id = _entity_id
                self._record = record
                self._d365_data_gen = d365_data_gen

            def run(self):
                _data_dict = {
                    "name": self._d365_data_gen.gen_name(),
                    "websiteurl": self._d365_data_gen.gen_website_url(),
                    "description": self._d365_data_gen.get_random_unicode(length=100),
                    "fax": self._d365_data_gen.gen_number(),

                }
                self._record.modify_record(new_val=_data_dict)

        _table_entities_id = list(_accounts.keys())
        # convert record keys to a list
        threads = list()

        iter_count = math.ceil(len(_table_entities_id) / 50)
        _index = 0
        # run 50 threads parallely
        for _ in range(iter_count):
            for entity_id in _table_entities_id[
                             _index:min(_index + 50, len(_table_entities_id))]:  # batch over 50 rows at aa time
                thread = D365Thread(entity_id, _accounts[entity_id], self._d365_data_gen)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            _index = _index + 50
            threads = list()  # empty the list of threads
        time.sleep(15)

    def modify_single_record_of_table(self, table_name: str, instance_name: str, instance: Environment = None, columns: list = None):
        """
            Method to modify all the records of a table
        Args:
            table_name:         <str>:      Logical Name for the table
            instance_name:      <str>:      Name of the Dynamics 365 Instance
            instance:           <obj>:      Instance of the Dynamics 365 CRM Environment
            columns:            <list>:     List of columns to be modified

        Returns:

        """
        record_dict = {}
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table = tables.get(table_name)
        records = table.get_all_records()
        table.get_entity_metadata()
        primary_attribute = table.entity_metadata.get("PrimaryNameAttribute")
        random_record_key = random.choice(list(records.keys()))
        random_record = records[random_record_key]
        older_record = random_record
        attributes = table.get_entity_attributes()
        for column in columns:
            column = column.lower().replace(' ', '')
            data = {}
            for attribute in attributes:
                if column in attribute:
                    if attributes[attribute].attribute_ref_type == "String":
                        data[attribute] = attribute + str(int(time.time()))
                    elif attributes[attribute].attribute_ref_type in ["BigInt", "Integer"]:
                        data[attribute] = int(time.time())
                    else:
                        raise Exception("This data type of field isn't being handled")
                    random_record.modify_record(new_val=data)
        updated_record = table.get_record(random_record_key)
        record_dict["PrimaryNameAttribute"] = primary_attribute
        record_dict["OldRecord"] = older_record
        record_dict["UpdatedRecord"] = updated_record
        return record_dict

    def compare_records(self, table_name: str, instance_name: str, instance: Environment = None,
                        older_record: Record = None, columns: list = None):
        """
            Method to compare the records of a table
        Args:
            table_name:         <str>:      Logical Name for the table
            instance_name:      <str>:      Name of the Dynamics 365 Instance
            instance:           <obj>:      Instance of the Dynamics 365 CRM Environment
            older_record:       <Record>:     Dictionary of the older record
            columns:            <list>:     List of columns to be compared
        Returns:
            None
        """
        if instance is None:
            _organization = Organization(credentials=self.credentials, region=self.cloud_region)
            environments = _organization.get_organization_environments()
            instance = environments.get(instance_name)
        else:
            instance = Environment(credentials=self.credentials, env_name=instance.env_name, env_url=instance.env_url,
                                   api_url=instance.api_url, region=self.cloud_region)
        tables = instance.get_environment_entities()
        table = tables.get(table_name)
        attributes = table.get_entity_attributes()
        column_schema_names = []
        for column in columns:
            column = column.lower().replace(' ', '')
            for attribute in attributes:
                if column in attribute:
                    column_schema_names.append(attribute)
        current_record = table.get_record(older_record.record_id, columns=column_schema_names)
        for column in column_schema_names:
            if older_record.record_data.get(column) != current_record.record_data.get(column):
                return False
        return True
