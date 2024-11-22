from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-s

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions or operations that can be performed
on the Database instance

DBInstances:

    select_instance()           --  Select the database instance in DB instances page

    is_instance_exists()        --  Checks if instance with given name exists

    add_postgresql_instance()   --  Adds new postgresql instance

    add_sapmaxdb_instance()     --  Adds new SAP MaxDB instance

    __click_add_cloud_db()        --  Clicks on 'CLoud DB' under Add Instance

    add_dynamodb_instance()     --  Adds new DynamoDB instance

    add_redshift_instance()     --  Adds new Redshift instance

    add_documentdb_instance()   --  Adds new DocumentDB instance

    add_rds_instance()          -- Adds new Amazon RDS instance

    add_db2_instance()          --  Adds new db2 instance

    add_multinode_database_instance()   --  Adds new Multinode Database instance

    add_mysql_instance()        --  Adds new MySQL instance

    add_sybase_instance()       --  Adds new Sybase instance

    add_gcp_postgresql_instance()       --  Adds new GCP PostgreSQL instance

    add_gcp_mysql_instance()            --  Adds new GCP MySQL instance

    add_alibaba_postgresql_instance()   --  Adds new Alibaba PostgreSQL instance

    add_alibaba_mysql_instance()        --  Adds new Alibaba MySQL instance

    add_amazonrds_postgresql_instance() --  Adds new Amazon RDS PostgreSQL instance

    add_amazonrds_mysql_instance()      --  Adds new Amazon RDS MySQL instance

    add_azure_postgresql_instance()     --  Adds new Azure PostgreSQL instance

    add_azure_mysql_instance()          --  Adds new Azure MySQL instance
    
    add_azure_mariadb_instance()        --  Adds new Azure MariaDB instance

    access_databases_tab()      --  Clicks on 'Databases' tab in Databases page

    access_instant_clones_tab()  -- Clicks on 'Instant clones' tab in Databases page

    add_informix_instance()     --  Adds new Informix instance

    add_cosmosdb_sql_instance() --  Adds new Azure CosmosDB SQL API instance

    add_oracle_instance()       --  Adds new Oracle instance

    add_oracle_rac_instance()   --  Adds new Oracle RAC instance

    add_saphana_instance()      --  Adds new SAP HANA instance

    discover_instances()        --  Discovers instances of specified client and agent

    backup()                    --  triggers backup from instances page

    add_server()                --  adds database server

    instant_clone()             --  Clicks on Instant clone in Instant clones tab and
    returns the object of instant clone class corresponding to database_type argument

    is_database_exists()        --  Check if database is present in databases tab

    select_database_from_databases_tab() -- Selects database from Databases Tab using Client name
    
    add_postgresql_cluster_instance()   --   Adds new postgresql cluster instance

    add_sap_oracle_instance()       --  Adds new SAP Oracle instance


SQLInstance

    sql_backup()                    --  Initiates SQL backup from the instance list page

    sql_restore()                   --  Initiates SQL restore from the instance list page

    select_content_for_restore()    --  Selects the content to restore


SpannerInstance

    db_type                         --  Returns the DBInstances Type enum of Cloud Spanner

    spanner_restore()               --  Initiates Spanner restore from the instance list page

    select_content_for_restore()    --  Selects the content to restore

    add_spanner_instance()          --  Adds new Spanner instance

"""

from abc import ABC, abstractmethod
from enum import Enum
from selenium.webdriver.common.keys import Keys
from Web.Common.page_object import (
    PageService, WebAction
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RBackup, RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Databases._migrate_to_cloud import (
    MigrateToCloud,
    MigrateSQLToAzure,
    MigrateOracleToAzure
)
from Web.AdminConsole.Databases.Instances import add_instance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import DynamoDBInstance, AzureMariaDBInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import AmazonRDSInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import RedshiftInstance, DocumentDBInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import CosmosDBSQLInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import CosmosDBCassandraInstance
from Web.AdminConsole.Databases.Instances.instant_clone import OracleInstantClone
from Web.AdminConsole.Databases.Instances.instant_clone import PostgreSQLInstantClone
from Web.AdminConsole.Databases.Instances.instant_clone import MySQLInstantClone
from Web.AdminConsole.Databases.Instances.restore_panels import SQLRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import SpannerRestorePanel
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import GoogleCloudPlatformPostgreSQLInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import GoogleCloudPlatformMySQLInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import GoogleCloudPlatformAlloydbInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import GoogleCloudPlatformSpannerInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import AlibabaPostgreSQLInstance, AlibabaMySQLInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import AmazonRDSPostgreSQLInstance, \
    AmazonRDSMySQLInstance
from Web.AdminConsole.Databases.Instances.add_cloud_db_instance import AzurePostgreSQLInstance, AzureMySQLInstance


class DBInstances:
    """This class provides the function or operations that can be performed on the DB Instances
    page under solutions in AdminConsole
    """

    class Types(Enum):
        """Available database types supported"""
        MSSQL = "SQL server"
        ORACLE = "Oracle"
        POSTGRES = "PostgreSQL"
        CLOUD_DB = "Cloud DB"
        DYNAMODB = "DynamoDB"
        DB2 = "DB2"
        MYSQL = "MySQL"
        RDS = "RDS"
        SYBASE = "Sybase"
        SYBASE_HADR = "Sybase HADR"
        REDSHIFT = "Redshift"
        INFORMIX = "Informix"
        SAP_HANA = "SAP HANA"
        ORACLE_RAC = "Oracle RAC"
        COSMOSDB_SQL = "Cosmos DB"
        COSMOSDB_CASSANDRA = "Cosmos DB (CASSANDRA API)"
        SPANNER = "Cloud Apps"
        DB2_MULTINODE = "DB2 MultiNode"
        DOCUMENTDB = "DocumentDB"
        SAP_MAXDB = "SAP for MaxDB"
        MULTINODE_DATABASE = "Multinode Database"
        AURORA_MYSQL = "Aurora MySQL"
        MARIA_DB = "MariaDB"
        AURORA_POSTGRES = "Aurora PostgreSQL"
        SAP_ORACLE = "SAP for Oracle"

    class InstantClonePanelTypes(Enum):
        """Enum to represent class for implementing instant clone panel"""
        ORACLE = "OracleInstantClone"
        POSTGRES = "PostgreSQLInstantClone"
        MYSQL = "MySQLInstantClone"

    class RestorePanelTypes(Enum):
        """Enum to represent classes for implementing restore panel"""
        MSSQL = "SQLRestorePanel"
        SPANNER = "SpannerRestorePanel"

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

        """
        self.admin_console = admin_console
        self.react_instances_table = Rtable(self.admin_console)
        self.__panel_dropdown = RDropDown(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.add_instance = add_instance.AddDBInstance(self.admin_console)
        self.admin_console.load_properties(self)
        self.props = self.admin_console.props
        self.__instant_clone_panel_map = {
            DBInstances.Types.ORACLE: DBInstances.InstantClonePanelTypes.ORACLE,
            DBInstances.Types.POSTGRES: DBInstances.InstantClonePanelTypes.POSTGRES,
            DBInstances.Types.MYSQL: DBInstances.InstantClonePanelTypes.MYSQL
        }
        self._restore_panel_map = {
            DBInstances.Types.MSSQL: DBInstances.RestorePanelTypes.MSSQL,
            DBInstances.Types.SPANNER: DBInstances.RestorePanelTypes.SPANNER
        }

    @PageService()
    def select_instance(self, database_type, instance_name, client_name=None):
        """Select the database instance in DB instances page

            Args:
                database_type   (DBInstances.Types) --  Use the enum to select any
                specific database

                instance_name   (str)               --  The name of the SQL instance to select

                client_name     (str)               --  Name of the client underwhich the instance
                is present

                    default: None

            Returns:
                (obj)   --      The SQL instance page object

        """
        if not isinstance(database_type, self.Types):
            raise Exception('Invalid database type')
        self.react_instances_table.set_default_filter('Type', database_type.value)
        self.react_instances_table.reload_data()
        if client_name:
            self.react_instances_table.access_link_by_column(client_name, instance_name)
        else:
            self.react_instances_table.access_link_by_column(instance_name, instance_name)

    @PageService(hide_args=True)
    def is_instance_exists(self, database_type, instance_name, client_name):
        """Check if instance exists

            Args:

                database_type            (str)  --  Database type

                instance_name            (str)  --  Instance Name

                client_name              (str)  --  Client Name
        """
        if not isinstance(database_type, self.Types):
            raise Exception('Invalid database type')
        self.react_instances_table.set_default_filter('Type', database_type.value)
        self.react_instances_table.is_entity_present_in_column('Server', client_name)
        self.react_instances_table.search_for(client_name)
        instances_data = self.react_instances_table.get_column_data('Name')
        return instance_name in instances_data

    @PageService(hide_args=True)
    def add_postgresql_instance(self, server_name, instance_name, plan, database_user, password,
                                port, binary_directory, lib_directory, archive_log_directory,
                                maintenance_db="postgres"):
        """Adds new postgresql instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  postgresql instance name

                plan                    (str)   --  Plan to be associated with the instance

                database_user           (str)   --  PostgreSQL user

                password                (str)   --  PostgreSQL user password

                port                    (str)   --  PostgreSQL port

                binary_directory        (str)   --  Binary directory path

                lib_directory           (str)   --  Library directory path

                archive_log_directory   (str)   --  archive log directory path

                maintenance_db          (str)   --  postgreSQL maintenance database name

                    default: Postgres



        """
        self.add_instance.add_postgresql_instance(
            server_name, instance_name, plan, database_user, password, port,
            binary_directory, lib_directory, archive_log_directory, maintenance_db=maintenance_db)

    @PageService(hide_args=True)
    def add_sapmaxdb_instance(self, server_name, instance_name, plan):
        """Adds new sap maxdb instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  sap maxdb instance name

                plan                    (str)   --  Plan to be associated with the instance

        """
        self.add_instance.add_sap_maxdb_instance(
            server_name, instance_name, plan)

    @PageService(hide_args=True)
    def add_db2_instance(self, server_name, instance_name, plan, db2_home, db2_username, db2_user_password,
                         pseudo_client_dpf=None, credential_name=None):
        """Adds new db2 instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  postgresql instance name

                plan                    (str)   --  Plan to be associated with the instance

                db2_home                (str)   --  db2 home path

                db2_username           (str)   --  db2 user name

                db2_user_password       (str)   --  db2 user password

                pseudo_client_dpf       (str)   -- DB2 DPF Pseudo Client Name

                credential_name         (str)   -- Name of the credential
                    default: None -- Meaning it is not a DPF Client

        """
        self.add_instance.add_db2_instance(
            server_name, instance_name, plan, db2_home, db2_username, db2_user_password, pseudo_client_dpf, credential_name)

    @PageService(hide_args=True)
    def add_multinode_database_instance(self, client_name, xbsa_clients, database_server, instance_name,
                                        database_name, plan):
        """
        Adds Multinode Database Instance
        Args:
            client_name           (str)  :  Name of the client under which instance to be created
            xbsa_clients          (list) :  List of hosts for Multinode Database instance
            database_server       (str)  :  Database server
            instance_name         (str)  :  Name of the instance to be created
            database_name         (str)  :  Database name for the instance
            plan                  (str)  :  Name of the plan that is to be associated with the instance
        """
        self.add_instance.add_multinode_database_instance(
            client_name=client_name, xbsa_clients=xbsa_clients,
            database_server=database_server, instance_name=instance_name,
            database_name=database_name, plan=plan)

    @PageService(hide_args=True)
    def add_mysql_instance(self, server_name, instance_name, plan,
                           database_user, password, binary_directory, log_directory,
                           config_directory, unix, socketfile_directory=None, unix_username=None,
                           nt_username=None, nt_password=None, port=None,
                           ssl_ca_file=None, xtra_backup_bin_path=None):
        """ Adds new MySQL database instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  MySQL instance name

                plan                    (str)   --  Plan to be associated with the instance

                database_user           (str)   --  MySQL user

                password                (str)   --  MySQL user password

                unix                    (bool)  --  True if server os is UNIX. Else false

                unix_username           (str)   --  UNIX user name (unix server specific)

                nt_username             (str)   --  NT username  (windows server specific)

                nt_password             (str)   --  NT password  (windows server specific)

                port                    (int)   --  Port  (windows server specific)

                socketfile_directory    (str)   --  Socket file directory  (unix server specific)

                    default: None

                binary_directory        (str)   --  Binary directory path

                log_directory           (str)   --  Log directory path

                config_directory        (str)   --  configuration file directory path

                ssl_ca_file             (str)   --  SSL CA file directory path

                    default: None

                xtra_backup_bin_path    (str)   --  XtraBackup bin path. If None, XtraBackup for
                                                    hot backup will not be enabled.

                    default: None

        """

        self.add_instance.add_mysql_instance(server_name=server_name,
                                             instance_name=instance_name,
                                             plan=plan, database_user=database_user,
                                             password=password,
                                             unix=unix, unix_username=unix_username,
                                             nt_username=nt_username, port=port,
                                             nt_password=nt_password,
                                             socketfile_directory=socketfile_directory,
                                             binary_directory=binary_directory,
                                             log_directory=log_directory,
                                             config_directory=config_directory,
                                             ssl_ca_file=ssl_ca_file,
                                             xtra_backup_bin_path=xtra_backup_bin_path)

    @WebAction()
    def __click_add_cloud_db(self):
        """Click on Cloud DB under add instance in Instances Page"""
        self.page_container.access_page_action(self.props['pageHeader.addInstance'])
        self.page_container.access_page_action(self.props['label.cloudDbService'])
        self.admin_console.wait_for_completion()

    @PageService(hide_args=True)
    def add_dynamodb_instance(self, cloud_account, plan, adjust_read_capacity=0, content=None):
        """
        Creates DynamoDB instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            adjust_read_capacity(int)   :   The value that needs to be set for
                                        adjust read capacity parameter

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }
        """
        self.__click_add_cloud_db()
        dynamodb_instance = DynamoDBInstance(self.admin_console)
        dynamodb_instance.create_instance(cloud_account, plan, adjust_read_capacity, content)

    @PageService(hide_args=True)
    def add_redshift_instance(
            self, cloud_account, plan, content='default',
            auth_type="IAM", access_node=None, credential_name=None):
        """
        Creates Redshift instance
        Args:
            cloud_account   (str):  The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one or more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }

                            Default value is 'default', default content set in UI will be used

            auth_type           (str) : Authentication type
                Possible values: IAM/ACCESS_KEY/STS

            access_node_name    (str)   :   Name of the access node

            credential_name     (str)   :   Credential name
                default:    None

        """
        self.__click_add_cloud_db()
        RedshiftInstance(self.admin_console).create_instance(
            cloud_account, plan, content, auth_type=auth_type, access_node=access_node, credential_name=credential_name)

    @PageService(hide_args=True)
    def add_documentdb_instance(
            self, cloud_account, plan, content='default',
            auth_type="IAM", access_node=None, credential_name=None):
        """
        Creates DocumentDB instance
        Args:
            cloud_account   (str):  The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one or more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }

                            Default value is 'default', default content set in UI will be used

            auth_type           (str) : Authentication type
                Possible values: IAM/ACCESS_KEY/STS

            access_node_name    (str)   :   Name of the access node

            credential_name     (str)   :   Credential name
                default:    None

        """
        self.__click_add_cloud_db()
        DocumentDBInstance(self.admin_console).create_instance(
            cloud_account, plan, content, auth_type=auth_type, access_node=access_node, credential_name=credential_name)

    @PageService(hide_args=True)
    def add_rds_instance(self, cloud_account, plan, content='default'):
        """
        Creates Amazon RDS instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                            configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide a list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }

                            Default value is 'default', default content set in UI will be used
        """
        self.__click_add_cloud_db()
        rds_instance = AmazonRDSInstance(self.admin_console)
        rds_instance.create_rds_instance(cloud_account, plan, content)

    @PageService(hide_args=True)
    def add_sybase_instance(self, server_name, instance_name, plan, sa_user_name,
                            password, unix, os_user_name=None, os_password=None):
        """
        Creates Sybase instance
        Args:
            server_name     (str):  Server name
            instance_name:  (str):  Name of instance to be created
            plan:           (str):  Plan name
            sa_user_name:   (str)   SA user name
            password:       (str): Password
            unix            (bool)  --  True if server os is UNIX. Else false
            os_user_name    (str): OS username
            os_password     (str): OS password
        """
        self.add_instance.add_sybase_instance(server_name=server_name,
                                              instance_name=instance_name, plan=plan,
                                              sa_user_name=sa_user_name, password=password,
                                              unix=unix, os_user_name=os_user_name,
                                              os_password=os_password)

    @PageService(hide_args=True)
    def add_sybasehadr_instance(self, plan, instance_name, nodes):
        """ Adds new Sybase HADR instance

        Args:
            plan(str):  Name of plan to be associated with Sybase hadr instance
            instance_name(str): Name of Sybase hadr Instance
            nodes(dict):
                {
                    name(str):          name of the node
                    SA_Username(str):   Name of sa user
                    Password(str):      sa user sybase password
                    OSUsername(str):    OS machine username
                    OSPassword(str):    OS user password
                    ASEserver(str):     Name of sybase Data server
                }

		"""
        self.add_instance.add_sybasehadr_instance(plan, instance_name, nodes)

    @PageService(hide_args=True)
    def add_gcp_postgresql_instance(self, cloud_account, plan, instance_name,
                                           database_user, password, access_node, credential_name):
        """
        Creates GCP PostgreSQL instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The GCP's PostgreSQL instance to be selected
            database_user   (str):  The username of PostreSQL User
            password        (str):  The password of PostgreSQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            credential_name (str):  The credential name that will be used for cloud account creation
        """
        self.__click_add_cloud_db()
        gcp_postgres_instance = GoogleCloudPlatformPostgreSQLInstance(self.admin_console)
        gcp_postgres_instance.create_instance(cloud_account, plan, instance_name,
                                           database_user, password, access_node, credential_name)

    @PageService(hide_args=True)
    def add_gcp_mysql_instance(self, cloud_account, plan, instance_name,
                                     database_user, password, access_node, credential_name):
        """
        Creates GCP MySQL instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The GCP's MySQL instance to be selected
            database_user   (str):  The username of MySQL User
            password        (str):  The password of MySQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            credential_name (str):  The credential name that will be used for cloud account creation
        """
        self.__click_add_cloud_db()
        gcp_mysql_instance = GoogleCloudPlatformMySQLInstance(self.admin_console)
        gcp_mysql_instance.create_instance(cloud_account, plan, instance_name,
                                           database_user, password, access_node, credential_name)

    @PageService(hide_args=True)
    def add_gcp_alloydb_instance(self, cloud_account, plan, instance_name,
                               database_user, password, access_node, credential_name, endpoint):
        """
        Creates GCP alloydb instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The GCP's alloydb instance to be selected
            database_user   (str):  The username of alloydb User
            password        (str):  The password of alloydb User
            access_node     (str):  The name of access node that will be used to create cloud account
            credential_name (str):  The credential name that will be used for cloud account creation
            endpoint        (str):  The endpoint that will be used for connection
        """
        self.__click_add_cloud_db()
        gcp_alloydb_instance = GoogleCloudPlatformAlloydbInstance(self.admin_console)
        gcp_alloydb_instance.create_instance(cloud_account, plan, instance_name,
                                           database_user, password, access_node, credential_name, endpoint)

    @PageService(hide_args=True)
    def add_alibaba_postgresql_instance(self, cloud_account, plan, instance_name, database_user, password, access_node, endpoint):
        """
        Creates Alibaba PostgreSQL instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Alibaba PostgreSQL instance to be selected
            database_user   (str):  The username of PostreSQL User
            password        (str):  The password of PostgreSQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            endpoint        (str):  The <IP:PORT> of database instance
        """
        self.__click_add_cloud_db()
        ali_postgres_instance = AlibabaPostgreSQLInstance(self.admin_console)
        ali_postgres_instance.create_instance(cloud_account, plan, instance_name, database_user, password, access_node, endpoint)

    @PageService(hide_args=True)
    def add_alibaba_mysql_instance(self, cloud_account, plan, instance_name, database_user, password, access_node, endpoint):
        """
        Creates Alibaba MySQL instance
        Args:
            cloud_account   (str): The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Alibaba MySQL instance to be selected
            database_user   (str):  The username of MySQL User
            password        (str):  The password of MySQL User
            endpoint        (str):  The <IP:PORT> of database instance
            access_node     (str):  The name of access node that will be used to create cloud account
        """
        self.__click_add_cloud_db()
        ali_mysql_instance = AlibabaMySQLInstance(self.admin_console)
        ali_mysql_instance.create_instance(cloud_account, plan, instance_name, database_user, password, access_node, endpoint)

    @PageService(hide_args=True)
    def add_amazonrds_postgresql_instance(self, cloud_account, plan, instance_name,
                                          database_user, password, access_node, credential_name):
        """
        Creates Amazon RDS PostgreSQL instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Amazon RDS PostgreSQL instance to be selected
            database_user   (str):  The username of PostreSQL User
            password        (str):  The password of PostgreSQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            credential_name (str):  The credential name that will be used for cloud account creation
        """
        self.__click_add_cloud_db()
        rds_postgres_instance = AmazonRDSPostgreSQLInstance(self.admin_console)
        rds_postgres_instance.create_instance(cloud_account, plan, instance_name,
                                              database_user, password, access_node, credential_name)

    @PageService(hide_args=True)
    def add_amazonrds_mysql_instance(self, cloud_account, plan, instance_name,
                                     database_user, password, access_node, credential_name):
        """
        Creates Amazon RDS MySQL instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Amazon RDS MySQL instance to be selected
            database_user   (str):  The username of MySQL User
            password        (str):  The password of MySQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            credential_name (str):  The credential name that will be used for cloud account creation
        """
        self.__click_add_cloud_db()
        rds_mysql_instance = AmazonRDSMySQLInstance(self.admin_console)
        rds_mysql_instance.create_instance(cloud_account, plan, instance_name,
                                           database_user, password, access_node, credential_name)

    @PageService(hide_args=True)
    def add_azure_postgresql_instance(self, **kwargs):
        """
        Creates Microsoft Azure PostgreSQL instance
        Keyword Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Azure PostgreSQL instance to be selected
            database_user   (str):  The username of PostreSQL User
            password        (str):  The password of PostgreSQL User
            access_node     (str):  The name of access node that will be used to create cloud account
            app_credential   (str): credential name of the app based authentication for cloud account creation
            ad_auth          (bool): False if ad_auth has to be disabled for DB instance
        """
        self.__click_add_cloud_db()
        azure_postgres_instance = AzurePostgreSQLInstance(self.admin_console)
        azure_postgres_instance.create_instance(**kwargs)

    @PageService(hide_args=True)
    def add_azure_mysql_instance(self, **kwargs):
        """
        Creates Microsoft Azure MySQL instance
        Keyword Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Microsoft Azure MySQL instance to be selected
            database_user   (str):  The username of MySQL User
            password        (str):  The password of MySQL User
            access_node      (str): Access Node name
            app_credential    (str): credential name of the app based authentication for cloud account creation
            ad_auth          (bool): False if ad_auth has to be disabled for DB instance
        """
        self.__click_add_cloud_db()
        azure_mysql_instance = AzureMySQLInstance(self.admin_console)
        azure_mysql_instance.create_instance(**kwargs)

    @PageService(hide_args=True)
    def add_azure_mariadb_instance(self, **kwargs):
        """
        Creates Microsoft Azure MariaDB instance
        Keyword Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                                configuring instance
            plan            (str):  The name of the plan that is to be associated with the instance
            instance_name   (str):  The Microsoft Azure MariaDB instance to be selected
            database_user   (str):  The username of MariaDB User
            password        (str):  The password of MariaDB User
            access_node      (str): Access Node name
            app_credential    (str): credential name of the app based authentication for cloud account creation
            ad_auth          (bool): False if ad_auth has to be disabled for DB instance
        """
        self.__click_add_cloud_db()
        azure_mariadb_instance = AzureMariaDBInstance(self.admin_console)
        azure_mariadb_instance.create_instance(**kwargs)

    @PageService()
    def access_databases_tab(self):
        """Clicks on 'Databases' tab in Databases page"""
        self.admin_console.access_tab(self.admin_console.props['label.databases'])

    @PageService()
    def access_instant_clones_tab(self):
        """Clicks on 'Instant clones' tab in Databases page"""
        self.admin_console.access_tab(self.admin_console.props['pageHeader.clones'])

    @PageService(hide_args=True)
    def add_informix_instance(self, server_name, instance_name, plan,
                              informix_username, informix_home, onconfig,
                              sqlhosts, is_windows_os, informix_password=None):
        """Adds new informix instance

            Args:
                server_name             (str)   --  Server name
                instance_name           (str)   --  informix instance name, INFORMIXSERVER
                plan                    (str)   --  Plan to be associated with the instance
                informix_username       (str)   --  informix user name
                informix_home           (str)   --  informix home directory, INFORMIXDIR
                onconfig                (str)   --  onconfig filename, ONCONFIG
                sqlhosts                (str)   --  sqlhosts file path, INFORMIXSQLHOSTS
                is_windows_os           (bool)  --  True if server OS is windows
                informix_password       (str)   --  informix user password

        """
        self.add_instance.add_informix_instance(
            server_name=server_name, instance_name=instance_name, plan=plan,
            informix_username=informix_username, informix_home=informix_home,
            onconfig=onconfig, sqlhosts=sqlhosts, is_windows_os=is_windows_os,
            informix_password=informix_password)

    @PageService()
    def access_instances_tab(self):
        """Clicks on 'Instances' tab in Databases page"""
        self.admin_console.access_tab(self.admin_console.props['pageHeader.instances'])

    @PageService(hide_args=True)
    def add_cosmosdb_sql_instance(self, cloud_account, access_node, plan, content='default'):
        """Creates new Azure CosmosDB SQL API instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            access_node     (str) : The access node used for running CosmosDB operations

            plan            (str):  The name of the plan

            content         (list or nested dict):  The content to be selected
                Default value is 'default', default content set in UI will be used

                            1. To set complete CosmosDB account as content:

                            Provide a list of strings of account names
                                Example: ['cosmos-account-1', cosmos-account-2]

                            2. To set one more databases and containers as content:

                            Provide a nested dictionary containing the account names as keys
                            and value as another dictionary whose keys are the database names
                            and values is a LIST of containers under the database
                                Example:
                                {
                                'cosmos-account-1': {
                                'database1':['container1', 'container2'],
                                'database2':['container3', 'container4']
                                        }
                                'cosmos-account-2':{
                                'database3': ['container5', 'container6'],
                                'database4': ['container7', 'container8']
                                        }
                                }

                            3. To set complete database as content:

                            Provide the nested dictionary same as above #2 but
                            in the nested dictionary, provide an empty LIST as value
                                Example:
                                    {
                                'cosmos-account-1': {
                                'database1':[],
                                        }
                                'cosmos-account-2':{
                                'database2': [],
                                'database3': []
                                        }
                                }
        """
        self.__click_add_cloud_db()
        CosmosDBSQLInstance(self.admin_console).create_instance(cloud_account, access_node, plan, content)

    @PageService(hide_args=True)
    def add_cosmosdb_cassandra_instance(self, regions, instance_name, cloud_account, access_nodes, plan,
                                        content='default', **kwargs):
        """Creates new Azure CosmosDB SQL API instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            access_node     (str) : The access node used for running CosmosDB operations

            plan            (str):  The name of the plan

            content         (list or nested dict):  The content to be selected
                Default value is 'default', default content set in UI will be used

                            1. To set complete CosmosDB account as content:

                            Provide a list of strings of account names
                                Example: ['cosmos-account-1', cosmos-account-2]

                            2. To set one more databases and containers as content:

                            Provide a nested dictionary containing the account names as keys
                            and value as another dictionary whose keys are the database names
                            and values is a LIST of containers under the database
                                Example:
                                {
                                'cosmos-account-1': {
                                'database1':['container1', 'container2'],
                                'database2':['container3', 'container4']
                                        }
                                'cosmos-account-2':{
                                'database3': ['container5', 'container6'],
                                'database4': ['container7', 'container8']
                                        }
                                }

                            3. To set complete database as content:

                            Provide the nested dictionary same as above #2 but
                            in the nested dictionary, provide an empty LIST as value
                                Example:
                                    {
                                'cosmos-account-1': {
                                'database1':[],
                                        }
                                'cosmos-account-2':{
                                'database2': [],
                                'database3': []
                                        }
                                }
            kwargs      (dict)  -- dict of keyword arguments as follows
                    subscription_id         (str)       --  cloud account subscription id
                    credential_name         (str)       --  credential name for azure cloud account
                    tenant_id               (str)       --  tenant id for azure cloud account
                    application_id          (str)       --  application id of azure cloud account
                    application_secret      (str)       --  application secret of azure cloud account
        """
        self.__click_add_cloud_db()
        CosmosDBCassandraInstance(self.admin_console).create_instance(regions, instance_name, cloud_account,
                                                                      access_nodes, plan, content, **kwargs)

    @PageService(hide_args=True)
    def add_oracle_instance(self, server_name, oracle_sid, plan, oracle_home,
                            connect_string, catalog_connect_string=None):
        """Adds new oracle instance

            Args:
                server_name             (str)   --  Server name
                oracle_sid              (str)   --  Oracle server SID
                plan                    (str)   --  Plan to be associated with the instance
                oracle_home             (str)   --  oracle home directory
                connect_string          (str)   --  Connect string for the server in the format:
                                                    <Username>/<Password>@<Service Name>
                catalog_connect_string  (str)   --  Connect string for catalog connect in format:
                                                    <Username>/<Password>@<Service Name>
                    default:    None

        """
        credentials, service_name = connect_string.split("@")
        username, password = credentials.split("/")
        catalog_username = None
        catalog_password = None
        catalog_service_name = None
        use_catalog_connect = False
        if catalog_connect_string:
            use_catalog_connect = True
            catalog_credentials, catalog_service_name = catalog_connect_string.split("@")
            catalog_username, catalog_password = catalog_credentials.split("/")
        self.add_instance.add_oracle_instance(
            server_name=server_name, oracle_sid=oracle_sid, plan=plan, oracle_home=oracle_home,
            username=username, password=password, service_name=service_name,
            use_catalog_connect=use_catalog_connect, catalog_username=catalog_username,
            catalog_password=catalog_password, catalog_service_name=catalog_service_name)

    @PageService(hide_args=True)
    def add_oracle_rac_instance(self, rac_instance_name, rac_cluster_name, rac_nodes, plan,
                                catalog_connect_string=None):
        """Adds new oracle rac instance

            Args:
                rac_instance_name       (str)   --  name of the instance
                rac_cluster_name        (str)   --  name of the cluster
                rac_nodes               (list)  --  list containing details of all the nodes
                plan                    (str)   --  Plan to be associated with the instance
                catalog_connect_string  (str)   --  Connect string for catalog connect in format:
                                                    <Username>/<Password>@<Service Name>
                    default:    None

        """
        catalog_username = None
        catalog_password = None
        catalog_service_name = None
        use_catalog_connect = False
        if catalog_connect_string:
            use_catalog_connect = True
            catalog_credentials, catalog_service_name = catalog_connect_string.split("@")
            catalog_username, catalog_password = catalog_credentials.split("/")
        self.add_instance.add_oracle_rac_instance(
            rac_instance_name=rac_instance_name, rac_cluster_name=rac_cluster_name,
            rac_nodes=rac_nodes, plan=plan, use_catalog_connect=use_catalog_connect,
            catalog_username=catalog_username, catalog_password=catalog_password,
            catalog_service_name=catalog_service_name)

    @PageService(hide_args=True)
    def add_saphana_instance(
            self, system_name, sid, plan, host_list, database_user=None,
            database_password=None, store_key=None, add_new_system=False):
        """Adds new SAP HANA instance

            Args:
                system_name         (str)   --  SAP Hana system name

                sid                 (str)   --  Instance Name

                plan                (str)   --  Plan name

                host_list           (list)  --  List of host for SAP HANA instance

                database_user       (str)   --  Database user name
                    default:None

                database_password   (str)   --  database passwrod
                    default:None

                store_key           (str)   --  Store key, needed only when HDB store key is selcted
                    default:None

                add_new_system      (bool)  --  Boolen value to specify if new system needs to be added
                    default: None

        """
        self.add_instance.add_saphana_instance(
            system_name, sid, plan, host_list, database_user,
            database_password, store_key, add_new_system)
        
    @PageService(hide_args=True)
    def add_sap_oracle_instance(self, server_name, oracle_sid, plan, oracle_home, connect_string, sap_data_home, sap_exe_path, use_sap_secure_store=False):
        """Adds new oracle instance

            Args:
                server_name             (str)   --  Server name
                oracle_sid              (str)   --  Oracle server SID
                plan                    (str)   --  Plan to be associated with the instance
                oracle_home             (str)   --  oracle home directory
                connect_string          (str)   --  Connect string for the server in the format:
                                                    <Username>/<Password>@<Service Name>
                sap_data_home           (str)   --  SAP Data Home
                sap_exe_path            (str)   --  SAP Exe Path
                use_sap_secure_store  (str)   --  Connect string for catalog connect in format:
                                                    <Username>/<Password>@<Service Name>
                    default:    None

        """
        credentials, service_name = connect_string.split("@")
        username, password = credentials.split("/")
                
        self.add_instance.add_sap_oracle_instance(
            server_name=server_name, oracle_sid=oracle_sid, plan=plan, oracle_home=oracle_home, 
            username=username, password=password, service_name=service_name,
            sap_data_home=sap_data_home, sap_exe_path=sap_exe_path, use_sap_secure_store=use_sap_secure_store)

    @PageService(hide_args=True)
    def add_gcp_spanner_instance(
            self,
            spanner_helper,
            plan,
            cloud_account=None,
            client_name=None
    ):
        """Adds new Cloud Spanner instance

            Args:

                spanner_helper          (obj:SpannerHelper)  --  SpannerHelper object

                plan                    (str)   --  Plan to be associated with the instance

                cloud_account           (str)   --  Name of cloud account for Spanner instance. Default is None.

                client_name             (str)   --  Name to create new cloud account. Default is None.

        """
        self.__click_add_cloud_db()
        gcp_spanner_instance = GoogleCloudPlatformSpannerInstance(self.admin_console)
        gcp_spanner_instance.create_instance(
            cloud_account,
            spanner_helper.instance_name,
            plan,
            client_name=client_name,
            account_id=spanner_helper.spanner_account_id,
            account_key=spanner_helper.spanner_key,
            access_node=spanner_helper.access_node
        )

    @PageService()
    def discover_instances(self, database_engine, server_name):
        """Discovers instances
            Args:
                database_engine (DBInstances.Types) --  Use the enum to select any
                                                        specific database
                server_name     (str):  Server name
        """
        self.page_container.access_page_action_from_dropdown('Discover instances')
        self.__panel_dropdown.select_drop_down_values(values=[database_engine.value],
                                                      drop_down_id="ddDbEngine",
                                                      partial_selection=True)
        self.__panel_dropdown.select_drop_down_values(values=[server_name],
                                                      drop_down_id="serverDropdown",
                                                      partial_selection=True)
        self.admin_console.click_by_id("btnDiscoverNow")

    @PageService()
    def backup(self, instance, backupset=None, subclient=None,
               backup_type=RBackup.BackupType.INCR,
               enable_data_for_incremental=False, cumulative=False, client=None, purge_binary_log=True):
        """
        Submits backup job from the subclient page
        Args:
            backup_type                 (RBackup.BackupType) -- backup type

            instance                    (str)               -- Name of instance

            backupset                   (str)               -- Name of backupset
                None

            subclient                   (str)               -- Name of subclient
                None

            enable_data_for_incremental (bool)              -- flag to check if
            data needs to be backed up during incremental
                default: False

            cumulative                  (bool)              -- flag to check for
            cumulative backup

            client                      (str)               -- Name of client as secondary entity for instance
            selection. Default is None.

            purge_binary_log            (bool)              -- To enable purge binary logs
            default: True

        Returns
            (str) -- Backup job id

        """
        self.react_instances_table.access_action_item(
            instance, self.admin_console.props['label.backup'], second_entity=client)
        if backupset is None and subclient is not None:
            backupset = instance
        return RBackup(self.admin_console).submit_backup(
            backup_type=backup_type, backupset_name=backupset, subclient_name=subclient,
            incremental_with_data=enable_data_for_incremental, cumulative=cumulative, purge_binary_log=purge_binary_log)

    @PageService()
    def _create_credentials(self, credential_name, account_name, password):
        """
       Method to create credential
        Args:
            credential_name                 (str):  Name of the account credential
            account_name                    (str):  Account name
            password                        (str):  password of the account

        """
        dialog = RModalDialog(self.admin_console, title="Add credential")
        dialog.fill_text_in_field("name", credential_name)
        dialog.fill_text_in_field("userAccount", account_name)
        dialog.fill_text_in_field("password", password)
        dialog.click_submit()

    @PageService()
    def _select_credential(self,credential_name):
        """
           Method to select created credential
            Args:
                credential_name                 (str):  Name of the account credential
        """
        self.__panel_dropdown.select_drop_down_values(values=credential_name,
                                                      drop_down_id='Credential')

    @PageService(hide_args=True)
    def add_server(self, database_type, server_name, username, password, plan,
                   unix_group=None, install_location=None, os_type="windows", db2_log_path=None, saved_cred=None, create_cred=None):
        """
        Method to add server of database type
            Args:
                database_type   (DBInstances.Types) --  Use the enum to select any
                                                        specific database

                server_name     (str)               --  Name of server

                username        (str)               --  Server username

                password        (str)               --  Server password

                plan            (str)               --  Plan to associate to the server

                unix_group      (str)               --  Unix group to associate the server to

                install_location(str)               --  Install location on server
                    default:    None

                os_type         (str)               --  "windows"/"unix"
                    default:    "windows"

                 db2_log_path(str)                   -- Location to store log files on server for DB2.
                    default:    None

                saved_cred      (str)               --  Name of existing credential
                    default:    None
                
                create_cred     (str)               -- Name of new credential to be created
                    default:    None

                saved_cred      (str)               --  Name of existing credential
                    default:    None
                
                create_cred     (str)               -- Name of new credential to be created
                    default:    None

                saved_cred      (str)               --  Name of existing credential
                    default:    None
                
                create_cred     (str)               -- Name of new credential to be created
                    default:    None


            Returns:    job id of add server job launched
        """
        self.page_container.access_page_action(self.props['label.installSoftware'])
        wizard = Wizard(self.admin_console)
        wizard.select_radio_card(database_type.value)
        self.admin_console.click_button(value="Next")
        wizard.select_plan(plan)
        self.admin_console.click_button(value="Next")
        self.admin_console.click_button(value='Add')
        if 'windows' in os_type.lower():
            self.admin_console.select_radio('0')
            if "\\" not in username:
                raise Exception("Include domain in username")
        else:
            self.admin_console.select_radio('1')
            if unix_group:
                self.admin_console.fill_form_by_id("unixGroup", unix_group)
        self.admin_console.fill_form_by_id("hostName", server_name)
        self.dialog.click_add()
        if saved_cred:
            self._select_credential(saved_cred)
        elif create_cred:
            self._create_credentials(create_cred, username, password)
        else:
            self.dialog.fill_text_in_field("userName", username)
            self.dialog.fill_text_in_field("password", password)
            self.dialog.fill_text_in_field("conformPassword", password)
        self.dialog.expand_accordion("Advanced options")
        if database_type is DBInstances.Types.DB2:
            if db2_log_path is None:
                raise Exception('Include Logs Path for DB2 database.')
            else:
                self.admin_console.fill_form_by_id("db2LogPath", db2_log_path)
        if install_location:
            self.admin_console.fill_form_by_id("installPath", install_location)
        self.admin_console.click_button(value="Save")
        self.admin_console.click_button(value="Next")
        self.admin_console.click_button(value="Finish", wait_for_completion=False)
        _jobid = self.admin_console.get_jobid_from_popup(wait_time=10)
        self.admin_console.wait_for_completion()
        return _jobid

    @PageService()
    def instant_clone(self, database_type, source_server, source_instance):
        """Method for accessing instant clone panel in instance details
        Args:
            database_type (Types):  Type of database should be one among the types defined
                                     in 'Types' enum in DBInstances.py file

            source_server   (str):  Source server

            source_instance (str):  Source instance to clone from
        Returns:
            Object (InstantClonePanelTypes): Object of class in InstantClonePanelTypes corresponding
                                        to database_type
        """
        agent_prop_map = {"Oracle": "agentType.oracle",
                          "Oracle RAC": "agentType.oracleRac",
                          "SAP HANA": "agentType.sapHana",
                          "PostgreSQL": "agentType.postgreSQL",
                          "DB2": "agentType.DB2",
                          "MySQL": "agentType.MySQL",
                          "Sybase": "agentType.Sybase",
                          "Informix": "agentType.Informix"}
        self.admin_console.click_button('Instant clone')
        if database_type.value == "Oracle" or database_type.value == "MySQL":
            radio_id = self.props[agent_prop_map[database_type.value]].upper()
        else:
            radio_id = self.props[agent_prop_map[database_type.value]]
        self.dialog.select_radio_by_id(radio_id)
        self.admin_console.click_button(value="Next")
        self.dialog.select_dropdown_values(values=[source_server], drop_down_id='sourceServer')
        self.dialog.select_dropdown_values(values=[source_instance], drop_down_id='sourceInstance')
        return globals()[self.__instant_clone_panel_map[database_type].value](self.admin_console)

    @PageService()
    def is_database_exists(self, database_type, client_name, database_name):
        """Check if database exists in Databases Tab

            Args:

                database_type            (str)  --  Database type

                client_name              (str)  --  Client Name

                database_name            (str)  --  Database Name
        """
        if not isinstance(database_type, self.Types):
            raise Exception('Invalid database type')
        self.react_instances_table.set_default_filter('Type', database_type.value)
        self.admin_console.refresh_page()
        self.react_instances_table.is_entity_present_in_column('Server', client_name)
        self.react_instances_table.search_for(client_name)
        database_data = self.react_instances_table.get_column_data('Name')
        return database_name in database_data

    @PageService()
    def access_restore(self, instance, client=None):
        """ Restore database(s) from instance list

        Args:

            instance (str)      --      Instance name

            client (str)        --      Client name. Default is None.

        """

        self.react_instances_table.access_action_item(
            instance,
            self.props['label.globalActions.restore'],
            second_entity=client
        )

    @PageService()
    def select_database_from_databases_tab(self, database_type, database_name, client_name=None):
        """
        Select the database from databases tab in instance page

        Args:
            database_type   (DBInstances.Types) --  Use the enum to select any
            specific database

            database_name   (str)               --  The name of the database to select

            client_name     (str)               --  Name of the client under which the instance
            is present
                default: None

        Returns:
            (obj)   --      The SQL database page object

        """
        self.access_databases_tab()

        if not isinstance(database_type, self.Types):
            raise Exception('Invalid database type')
        self.react_instances_table.set_default_filter('Type', database_type.value)
        self.admin_console.refresh_page()
        if client_name:
            self.react_instances_table.access_link_by_column(client_name, database_name)
        else:
            self.react_instances_table.access_link_by_column(database_name, database_name)

    @PageService(hide_args=True)
    def add_postgresql_cluster_instance(self, instance_name, nodes, plan, cluster_type,
                                        cluster_bin=None, cluster_conf=None):
        """
        Creates Multinode Database Instance
        Args:
            instance_name        (str)  : Name of the client under which instance to be created
            nodes                (list) : [node],
            plan                (str)  :  Name of the plan that is to be associated with the instance
            cluster_type        (str)  :  Type of cluster (native, EFM, patroni, rep_mgr)
            cluster_bin         (str)   : Bin dir of cluster (optional)
            cluster_conf        (str)   : Conf dir of cluster (optional)

        node: The nodes list is a list of dict of a node that contains the following
        node (dict):
            {
                server (str): The name of the server.
                password (str): The password for accessing the PostgreSQL server
                port (int): The port number on which the PostgreSQL server is running
                bin_dir (str): The directory where PostgreSQL binary files are located
                lib_dir (str): The directory where PostgreSQL library files are located
                archive_wal_dir (str): The directory where Write-Ahead Logging (WAL) files are archived
                cluster_bin (str): The path to the cluster binary (optional)
                cluster_conf (str): The path to the cluster configuration file (optional)
            }
        """
        self.add_instance.add_postgresql_cluster_instance(instance_name, nodes, plan, cluster_type,
                                                          cluster_bin, cluster_conf)



class DBInstance(ABC):
    """This class provides the functions or operations that can be performed in common
    on any DB Instance"""

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

        """
        self.admin_console = admin_console

    @property
    @abstractmethod
    def db_type(self):
        raise NotImplementedError


class _DBInstanceFeatures:
    class MigrationVendor(Enum):
        """Available Vendor types supported"""
        AZURE = "AZURE"

    def __init__(self, admin_console: AdminConsole, db_type):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

                db_type (str) -- Type of the DB instance

        """
        self.admin_console = admin_console
        self._db_type = db_type

    @PageService()
    def configure_migrate_to_cloud(self, vendor: MigrationVendor):
        """Starts the "Migrate to cloud" option of the instance and submits the form

            Args:
                vendor      (MigrationVendor)   --  The cloud vendor to migrate the SQL DB to.



             Returns:
                 MigrateToCloud   --      an implemented instance of MigrateToCloud

        """

        factory_dict = {
            "AZURE": {
                "SQL Server": MigrateSQLToAzure,
                "Oracle": MigrateOracleToAzure
            }
        }
        self.admin_console.access_menu_from_dropdown('Migrate to cloud')
        return factory_dict[vendor.value][self._db_type](self.admin_console)


class SQLInstance(DBInstances):

    def __init__(self, admin_console: AdminConsole):
        DBInstances.__init__(self, admin_console)
        self.SQL_AZ_INS_SUFFIX = 'database.windows.net'

    @property
    def db_type(self):
        return DBInstances.Types.MSSQL

    @PageService()
    def sql_backup(self, instance, subclient, backup_type, client=None, os_type=None):
        """ Backup subclient from instance list

        Args:
            instance (str)      --      Instance name

            subclient (str)     --      Subclient to backup

            backup_type (str)   --      Type of backup: "Full", "Differential", "Transaction_Log"

            client (str)        --      Name of client as secondary entity for instance selection. Default is None.

            os_type             --      OS type of on-prem server. Pass windows if it's a win server else pass unix

        """
        if not isinstance(backup_type, RBackup.BackupType):
            backup_type = RBackup.BackupType(backup_type.upper())

        self.admin_console.navigator.navigate_to_db_instances()
        self.react_instances_table.set_default_filter('Type', DBInstances.Types.MSSQL.value)
        instance = instance.lower()
        if self.SQL_AZ_INS_SUFFIX not in instance and os_type != "unix":
            instance = instance.upper()
        return self.backup(instance, subclient=subclient, backup_type=backup_type, client=client)

    @PageService()
    def sql_restore(self, instance, databases, restore_type, destination_instance=None, os_type=None, **kwargs):
        """ Restore database(s) from instance list

        Args:
            instance (str)      --      Instance name

            databases (list)    --      List of database(s) to restore

            restore_type (str)  --      Type of Restore "In Place", "Out of Place", "Restore to Disk"

            destination_instance (str/Optional) -- Destination to restore SQL DB to. Default is the source instance.

            os_type             --      OS type of on-prem server. Pass windows if it's a win server else pass unix

        Keyword Args:
            access_node (str)   --      Name of the access node for restore staging purposes

            staging_path (str)  --      Folder path on access node to stage database for restore

            destination_database_name (str) --  Name to restore database as

        """
        is_azure = False
        instance = instance.lower()
        if self.SQL_AZ_INS_SUFFIX in instance:
            is_azure = True
        if self.SQL_AZ_INS_SUFFIX not in instance and os_type != "unix":
            instance = instance.upper()

        self.admin_console.navigator.navigate_to_db_instances()

        self.access_restore(instance)
        self.select_content_for_restore(databases, search=databases[0][:-1])
        self.admin_console.click_button(value='Restore')

        if restore_type.lower() == "in place":
            if is_azure:
                if destination_instance is None:
                    raise Exception("Destination Instance not provided for Cloud restore!")
                return globals()[self._restore_panel_map[self.db_type].value](self.admin_console).restore(
                    destination_instance,
                    **kwargs
                )
            else:
                return globals()[self._restore_panel_map[self.db_type].value](self.admin_console).in_place_restore()
        else:
            raise Exception("Restore type [{0}] is an invalid restore type!".format(restore_type.lower()))

    @PageService()
    def select_content_for_restore(self, databases, search=None):
        """ Select content for the restore

        Args:

            databases (list)        --      List of database(s) to select for restore

            search (str, Optional)  --      Search term within the table to bring content into view

        """
        database_table = Rtable(self.admin_console)

        if search:
            self.admin_console.fill_form_by_id("searchInput", search + Keys.ENTER)
        database_table.select_rows(databases)


class OracleInstance(DBInstance, _DBInstanceFeatures):

    def __init__(self, admin_console: AdminConsole):
        DBInstance.__init__(self, admin_console)
        _DBInstanceFeatures.__init__(self, admin_console, self.db_type)

    @property
    def db_type(self):
        return "Oracle"


class SpannerInstance(DBInstances):

    def __init__(self, admin_console: AdminConsole):
        DBInstances.__init__(self, admin_console)

    @property
    def db_type(self):
        return DBInstances.Types.SPANNER

    @PageService()
    def spanner_restore(self, instance, databases, restore_type, client=None):
        """ Restore database(s) from instance list

        Args:
            instance (str)      --      Instance name

            databases (list)    --      List of database(s) to restore

            restore_type (str)  --      Type of Restore "In place", "Out of place"

            client (str)        --      Client name of the instance. Default is None.

        """

        self.access_restore(instance, client)
        self.select_content_for_restore(databases)
        self.admin_console.click_button(value='Restore')

        if restore_type.lower() == "in place":
            return globals()[self._restore_panel_map[self.db_type].value](self.admin_console).in_place_restore()
        else:
            raise Exception("Restore type [{0}] is an invalid restore type!".format(restore_type.lower()))

    @PageService()
    def select_content_for_restore(self, database_list):
        """ Select content for the restore

        Args:

            database_list (list)        --      List of database(s) to select for restore

        """
        database_table = Rtable(self.admin_console)
        database_table.select_rows(database_list)

    @PageService(hide_args=True)
    def add_spanner_instance(
            self,
            spanner_helper,
            plan,
            cloud_account=None,
            client_name=None
    ):
        """Adds new Cloud Spanner instance

            Args:

                spanner_helper          (:obj: 'SpannerHelper')   --  SpannerHelper object

                plan                    (str)   --  Plan to be associated with the instance

                cloud_account           (str)   --  Cloud Account (Client Name) for the Cloud Spanner instance.
                Default is None

                client_name             (str)   --  Server name. Default: None

        """
        self.add_gcp_spanner_instance(
            spanner_helper,
            plan,
            cloud_account,
            client_name
        )
