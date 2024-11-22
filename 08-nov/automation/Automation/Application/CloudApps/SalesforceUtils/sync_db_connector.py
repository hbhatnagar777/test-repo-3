# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Helper file to handle sync database operations

SyncDbConnector: Connector class for sync database

SyncDbConnector:

    create_new_sqlserver_database()     --  Create a new database in SQLSERVER. If a database with given name already
    exists, then drops existing database and recreates.

    validate_schema_in_sqlserver_database() -- Validate schema of Salesforce CustomObject in database

    delete_sqlserver_database()         --  Delete SQL Server database

    create_new_postgresql_database()    --  Create a new database in POSTGRESQL. If a database with given name already
    exists, then drops existing database and recreates.

    validate_schema_in_postgresql_database() -- Validate schema of Salesforce CustomObject in database

    delete_postgresql_database()        --  Delete PostgreSQL database

    create_database()                   --  Creates database based on DbType given in testcase inputs

    delete_database()                   --  Deletes database based on DbType given in testcase inputs

    retrieve_object_data_from_postgres_db()  -- Gets data from postgres db for a given Salesforce object
"""
from AutomationUtils.database_helper import PostgreSQL, MSSQL
from .constants import POSTGRESQL_DEFAULT_PORT, SQLSERVER_DEFAULT_PORT, DbType
from .base import SalesforceBase


class SyncDbConnector(SalesforceBase):
    """Class to handle sync database operations"""

    def __create_sqlserver_connection(self, database="master"):
        """
        Creates a new SQL Server connection

        Args:
            database (str): Name of database to connect to (default master)

        Returns:
            MSSQL: SQL Server helper object
        """
        try:
            port = self.sqlserver_options.db_port
        except AttributeError:
            port = SQLSERVER_DEFAULT_PORT
        return MSSQL(
            server=f"{self.sqlserver_options.db_host_name}\\{self.sqlserver_options.db_instance},{port}",
            user=self.sqlserver_options.db_user_name,
            database=database,
            password=self.sqlserver_options.db_password
        )

    def create_new_sqlserver_database(self, database):
        """
        Create a new database in SQL Server. If a database with given name already exists. then drops existing database
        and recreates

        Args:
            database (str): Name of new database

        Returns:
            None:
        """
        self._log.info(f"Creating database with name {database} on host {self.sqlserver_options.db_host_name}")
        self.__create_sqlserver_connection().create_db(database)
        self._log.info("Database created successfully")

    def validate_schema_in_sqlserver_database(self, sf_object, database=None, deleted_fields=None):
        """
        Validate schema of Salesforce CustomObject in database

        Args:
            sf_object (zeep.xsd.valueobjects.CompoundValue): Salesforce CustomObject
            database (str): Database name (Only required if overriding value set in tcinputs/config)
            deleted_fields (list): List of FullNames of any deleted fields

        Returns:
            None:

        Raises:
            Exception: If validation fails
        """
        self._log.info(f"Validating schema of {sf_object.fullName} in database {database} on host "
                       f"{self.sqlserver_options.db_host_name}")
        mssql = self.__create_sqlserver_connection(database)
        db_response = mssql.execute(f"SELECT column_name FROM information_schema.columns "
                                    f"WHERE table_name = '{sf_object.fullName.lower()}';")
        db_column_names = [row[0] for row in db_response.rows]
        self._log.info("Queried column names from database successfully")
        sf_field_names = [field.fullName for field in sf_object.fields]
        if deleted_fields:
            sf_field_names.extend([f"{name}_DELD" for name in deleted_fields])
        sf_field_names = [name.split(".")[-1] for name in sf_field_names]
        if not all(name in db_column_names for name in sf_field_names):
            raise Exception(f"Validation of schema in database failed\n"
                            f"Salesforce Fields = {sf_field_names}\n"
                            f"Database Columns = {db_column_names}")
        self._log.info("Validation successful")

    def delete_sqlserver_database(self, database):
        """
        Delete SQL Server database

        Args:
            database (str): Name of database to delete

        Returns:
            None:
        """
        self._log.info(f"Deleting database {database} on host {self.sqlserver_options.db_host_name}")
        self.__create_sqlserver_connection().drop_db(database)
        self._log.info(f"{database} deleted successfully")

    def __create_postgresql_connection(self, database="postgres"):
        """
        Creates new PostgreSQL connection

        Args:
            database (str): Name of database to connect to (default postgres)

        Returns:
            PostgreSQL: PostgreSQL connection
        """
        try:
            port = self.postgresql_options.db_port
        except AttributeError:
            port = POSTGRESQL_DEFAULT_PORT
        return PostgreSQL(
            host=self.postgresql_options.db_host_name,
            port=port,
            user=self.postgresql_options.db_user_name,
            password=self.postgresql_options.db_password,
            database=database
        )

    def create_new_postgresql_database(self, database):
        """
        Create a new database in POSTGRESQL. If a database with given name already exists, then drops existing database
        and recreates.

        Args:
            database (str): Name of new Database

        Returns:
            None:
        """
        self._log.info(f"Creating database with name {database} on host {self.postgresql_options.db_host_name}")
        self.__create_postgresql_connection().create_db(database)
        self._log.info("Database created successfully")

    def validate_schema_in_postgresql_database(self, sf_object, database=None, deleted_fields=None):
        """
        Validate schema of Salesforce CustomObject in database

        Args:
            sf_object (zeep.xsd.valueobjects.CompoundValue): Salesforce CustomObject
            database (str): Database name (Only required if overriding value set in tcinputs/config)
            deleted_fields (list): List of FullNames of any deleted fields

        Returns:
            None:

        Raises:
            Exception: If validation fails
        """
        self._log.info(f"Validating schema of {sf_object.fullName} in database {database} on host "
                       f"{self.postgresql_options.db_host_name}")
        pgsql = self.__create_postgresql_connection(database)
        db_response = pgsql.execute(f"SELECT column_name FROM information_schema.columns "
                                    f"WHERE table_name = '{sf_object.fullName.lower()}';")
        db_column_names = [row[0] for row in db_response.rows]
        self._log.info("Queried column names from database successfully")
        sf_field_names = [field.fullName for field in sf_object.fields]
        if deleted_fields:
            sf_field_names.extend([f"{name}_deld" for name in deleted_fields])
        sf_field_names = [name.split(".")[-1] for name in sf_field_names]
        if not all(name.lower() in db_column_names for name in sf_field_names):
            raise Exception(f"Validation of schema in database failed\n"
                            f"Salesforce Fields = {sf_field_names}\n"
                            f"Database Columns = {db_column_names}")
        self._log.info("Validation successful")

    def delete_postgresql_database(self, database):
        """
        Delete PostgreSQL database

        Args:
            database (str): Name of database to delete

        Returns:
            None:
        """
        self._log.info(f"Deleting database {database} on host {self.postgresql_options.db_host_name}")
        self.__create_postgresql_connection().drop_db(database)
        self._log.info(f"{database} deleted successfully")

    def create_new_database(self, database):
        """
        Gets sync db type from testcase inputs and creates database accordingly

        Args:
            database (str): Name of new database

        Returns:
            None:
        """
        if self.infrastructure_options.db_type == DbType.POSTGRESQL.value:
            self.create_new_postgresql_database(database)
        else:
            self.create_new_sqlserver_database(database)

    def delete_database(self, database):
        """
        Delete database

        Args:
            database (str): Name of database to delete

        Returns:
            None:
        """
        if self.infrastructure_options.db_type == DbType.POSTGRESQL.value:
            self.delete_postgresql_database(database)
        else:
            self.delete_sqlserver_database(database)

    def retrieve_object_data_from_postgres_db(self, database_name, table_name, fields):
        """
                Gets data from postgres db for a given Salesforce object

                Args:
                    database_name (str): Name of database

                    table_name (str): Name of object whose data needs to be retrieved

                    fields (list): List of fields where the data needs to be extracted from

                Returns:
                    sf_data (list): Object data in the form of list of dictionaries
        """
        self._log.info(f"Retrieving object {table_name} from Database {database_name}")
        pgsql = self.__create_postgresql_connection(database_name)
        if fields:
            raw_data = pgsql.execute(f"SELECT {', '.join(fields)} FROM public.{table_name.lower()};")
            sf_data = [{key: val for key, val in zip(fields, row)} for row in raw_data.rows]
        else:
            raw_data = pgsql.execute(f"SELECT * FROM public.'{table_name.lower()}';")
            sf_data = [{key: val for key, val in zip(raw_data.columns, row)} for row in raw_data.rows]

        return sf_data
