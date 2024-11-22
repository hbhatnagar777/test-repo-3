# -*- coding: utf-8 -*-s

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions or operations to create non cloud database instances

AddInstance:

    click_on_add_instance()             --   method to click on add instance in database page
    select_database_type()              --   Selects the database type
    add_postgresql_instance()           --   Adds new postgreSQL database instance
    add_sap_maxdb_instance()            --   Adds new SAP MaxDB instance
    add_mysql_instance()                --   Adds new MySQL database instance
    add_db2_instance()                  --   Adds new db2 instance
    add_sybase_instance()               --   Adds new Sybase instance
    add_sybasehadr_instance()           --   Adds new Sybase Hadr instance
    add_informix_instance()             --   Adds new Informix instance
    add_oracle_instance()               --   Adds new Oracle instance
    add_oracle_rac_instance()           --   Adds new Oracle RAC instance
    add_saphana_instance()              --   Adds new SAP HANA instance
    add_multinode_database_instance()   --   Adds new Multinode Database instance
    add_postgresql_cluster_instance()   --   Adds new postgresql cluster instance
    add_sap_oracle_instance()           --   Adds new SAP Oracle instance

"""
import time

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.page_container import PageContainer


class AddDBInstance:
    """This class provides the function or operations to create non cloud database instances
    """

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

        """
        self.__admin_console = admin_console
        self._panel_dropdown = RDropDown(self.__admin_console)
        self.page_container = PageContainer(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.props = self.__admin_console.props
        self.wizard = Wizard(admin_console)
        self.dialog = RModalDialog(admin_console)

    def click_on_add_instance(self, agent_name):
        """method to click on add instance in database page

            Args:
                agent_name  (str)   --  Agent name
        """
        self.page_container.access_page_action(self.props['pageHeader.addInstance'])
        self.page_container.access_page_action(self.props['label.dbServer'])
        self.select_database_type(agent_name)

    @PageService()
    def select_database_type(self, db_name=None):
        """Selects the database type
            Args:
                db_name  (str)   --  Database name

        """
        self.wizard.select_radio_button(db_name)
        self.wizard.click_next()
        self.__admin_console.wait_for_completion()

    @PageService(hide_args=True)
    def add_postgresql_instance(self, server_name, instance_name, plan,
                                database_user, password, port, binary_directory,
                                lib_directory, archive_log_directory, maintenance_db="postgres"):
        """ Adds new postgreSQL database instance

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
        self.click_on_add_instance(self.props['agentType.postgreSQL'])
        self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
        self.__admin_console.fill_form_by_id(element_id='instanceName', value=instance_name)
        self._panel_dropdown.select_drop_down_values(values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_id(element_id='databaseUser', value=database_user)
        self.__admin_console.fill_form_by_id(element_id='dbPassword', value=password)
        self.__admin_console.fill_form_by_id(element_id='confirmPassword', value=password)
        self.__admin_console.fill_form_by_id(element_id='MaintainenceDB', value=maintenance_db)
        self.__admin_console.fill_form_by_id(element_id='port', value=port)
        self.__admin_console.fill_form_by_id(element_id='binaryPath', value=binary_directory)
        self.__admin_console.fill_form_by_id(element_id='libPath', value=lib_directory)
        self.__admin_console.fill_form_by_id(element_id='archiveLogPath', value=archive_log_directory)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_sap_maxdb_instance(self, server_name, instance_name, plan):
        """ Adds new sapMaxDB database instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --   instance name

                plan                    (str)   --  Plan to be associated with the instance

        """
        self.click_on_add_instance(self.props['agentType.sapForMaxDb'])
        self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
        self.__admin_console.fill_form_by_id(element_id='instanceName', value=instance_name)
        self._panel_dropdown.select_drop_down_values(values=[plan], drop_down_id='planDropdown')
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_db2_instance(self, server_name, instance_name, plan, db2_home, db2_username, db2_user_password,
                         pseudo_client_dpf=None, credential_name=None):
        """ Adds new db2 database instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  db2 instance name

                plan                    (str)   --  Plan to be associated with the instance

                db2_home               (str)   --  db2 home path

                db2_username           (str)   --  db2 user name

                db2_user_password      (str)   --  db2 user password

                pseudo_client_dpf       (str)   -- DB2 DPF Pseudo Client Name

                credential_name         (str)   -- Credential Name

                    default: None -- Meaning it is not a DPF Client
        """
        if pseudo_client_dpf:
            self.click_on_add_instance(self.props['agentType.DB2DPF'])
            self.__admin_console.fill_form_by_name('clientName', pseudo_client_dpf)
            self.__admin_console.click_button_using_text("Add")
            time.sleep(5)
            self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
            self.__admin_console.fill_form_by_name('dbHome', db2_home)
            self.__admin_console.click_button_using_text("Save")
        else:
            self.click_on_add_instance(self.props['agentType.DB2'])
            self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
            self.__admin_console.fill_form_by_name('dbHome', db2_home)
            self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')

        time.sleep(5)
        self.__admin_console.fill_form_by_name('instanceName', instance_name)
        self._panel_dropdown.select_drop_down_values(
            values=[plan],
            drop_down_id='planDropdown')

        if credential_name in self._panel_dropdown.get_values_of_drop_down(drop_down_id='credentialsdbInstance'):
            self._panel_dropdown.select_drop_down_values(values=[credential_name], drop_down_id='credentialsdbInstance')
        else:
            self.__admin_console.click_button(id="addCredentialButton")
            self.dialog.fill_text_in_field("name", credential_name)
            self.dialog.fill_text_in_field("userName", db2_username)
            self.dialog.fill_text_in_field("password", db2_user_password)
            self.dialog.click_save_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_mysql_instance(self, server_name, instance_name, plan, database_user, password,
                           binary_directory, log_directory, config_directory, unix,
                           socketfile_directory=None, unix_username=None, nt_username=None,
                           nt_password=None, port=None, ssl_ca_file=None,
                           xtra_backup_bin_path=None):
        """ Adds new MySQL database instance

            Args:
                server_name             (str)   --  Server name

                instance_name           (str)   --  MySQL instance name

                plan                    (str)   --  Plan to be associated with the instance

                database_user           (str)   --  MySQL user

                password                (str)   --  MySQL user password

                socketfile_directory    (str)   --  Socket file directory psth

                binary_directory        (str)   --  Binary directory path

                log_directory           (str)   --  Log directory path

                config_directory        (str)   --  configuration file directory path

                unix                    (bool)  --  True if server os is UNIX. Else false

                unix_username           (str)   --  UNIX user name  (unix server specific)

                    default: None

                nt_username             (str)   --  NT username  (windows server specific)

                    default: None

                nt_password             (str)   --  NT password  (windows server specific)

                    default: None

                port                    (int)   --  Port  (windows server specific)

                    default: None

                ssl_ca_file             (str)   --  SSL CA file directory path

                    default: None

                xtra_backup_bin_path    (str)   --  XtraBackup bin path. If None, XtraBackup
                                                    for hot backup will not be enabled.

                    default: None

        """
        self.click_on_add_instance(self.props['agentType.MySQL'])
        self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
        self.__admin_console.fill_form_by_name('instanceName', instance_name)
        self._panel_dropdown.select_drop_down_values(values=[plan],
                                                     drop_down_id='planDropdown')
        self.__admin_console.expand_accordion(self.props['label.assets.database.connectionDetails'])
        self.__admin_console.fill_form_by_name('dbUsername', database_user)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        if unix:
            if unix_username:
                self.__admin_console.fill_form_by_name('UnixUsername', unix_username)
            if socketfile_directory:
                self.__admin_console.fill_form_by_name('SocketFile', socketfile_directory)
        else:
            if nt_username and nt_password:
                self.__admin_console.fill_form_by_name('NTUsername', nt_username)
                self.__admin_console.fill_form_by_name('NTPassword', nt_password)
            if port:
                self.__admin_console.fill_form_by_name('port', port)
        self.__admin_console.expand_accordion(self.props['label.configuration'])
        self.__admin_console.fill_form_by_name('BinaryDirectory', binary_directory)
        self.__admin_console.fill_form_by_name('LogDataDirectory', log_directory)
        self.__admin_console.fill_form_by_name('ConfigFile', config_directory)
        self.__admin_console.expand_accordion(self.props['label.assets.database.advancedOptions'])
        if ssl_ca_file:
            self.__admin_console.fill_form_by_name('SSLCAFile', ssl_ca_file)
        if xtra_backup_bin_path:
            self.__admin_console.enable_toggle(index=0)
            self.__admin_console.fill_form_by_name('XtraBackupPath', xtra_backup_bin_path)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_sybase_instance(self, server_name, instance_name, plan, sa_user_name,
                            password, unix, os_user_name=None, os_password=None):
        """ Adds new Sybase instance
        Args:
            server_name     (str):  Server name
            instance_name:  (str):  Name of instance to be created
            plan:           (str):  Plan name
            sa_user_name:   (str):  SA user name
            password:       (str):  Password
            unix            (bool): True if server os is UNIX. Else false
            os_user_name    (str):  OS username
            os_password     (str):  OS password
        """
        self.click_on_add_instance(self.props['agentType.Sybase'])
        self._panel_dropdown.select_drop_down_values(values=[server_name],
                                                     drop_down_id='cvClients')
        self.__admin_console.fill_form_by_id('instanceName', instance_name)
        self._panel_dropdown.select_drop_down_values(values=[plan],
                                                     drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_name('databaseUser', sa_user_name)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        if not unix:
            self.__admin_console.fill_form_by_name('username', os_user_name)
            self.__admin_console.fill_form_by_name('password', os_password)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_informix_instance(self, server_name, instance_name, plan,
                              informix_username, informix_home, onconfig,
                              sqlhosts, is_windows_os, informix_password=None):
        """ Adds new informix instance

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
        self.click_on_add_instance(self.props['agentType.Informix'])
        self._panel_dropdown.select_drop_down_values(values=[server_name], drop_down_id='cvClients')
        self.__admin_console.fill_form_by_id(element_id='instanceName', value=instance_name)
        self._panel_dropdown.select_drop_down_values(values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_id(element_id='dbUserName', value=informix_username)
        if is_windows_os and informix_password:
            if "\\" in informix_username:
                self.__admin_console.fill_form_by_id(element_id='dbPassword', value=informix_password)
            else:
                raise Exception("Domain name is missing in user name or password is not provided")
        self.__admin_console.fill_form_by_name('informixHome', informix_home)
        self.__admin_console.fill_form_by_name('onConfigFile', onconfig)
        self.__admin_console.fill_form_by_name('sqlHostFile', sqlhosts)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_oracle_instance(self, server_name, oracle_sid, plan, oracle_home,
                            username, password, service_name, use_catalog_connect,
                            catalog_username, catalog_password, catalog_service_name):
        """Adds new oracle instance

            Args:
                server_name             (str)   --  Server name
                oracle_sid              (str)   --  Oracle server SID
                plan                    (str)   --  Plan to be associated with the instance
                oracle_home             (str)   --  oracle home directory
                username                (str)   --  Oracle server username
                password                (str)   --  Oracle server password
                service_name            (str)   --  Oracle service name
                use_catalog_connect     (bool)  --  True if catalog connect is to be enabled
                catalog_username        (str)   --  Catalog username
                catalog_password        (str)   --  Catalog password
                catalog_service_name    (str)   --  Connect service name
        """

        self.click_on_add_instance(self.props['agentType.oracle'])
        self._panel_dropdown.select_drop_down_values(values=[server_name],
                                                     drop_down_id='cvClients')
        self.__admin_console.fill_form_by_name('instanceName', oracle_sid)
        self._panel_dropdown.select_drop_down_values(
            values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_name('oracleHome', oracle_home)
        self.__admin_console.fill_form_by_name('dbUserName', username)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        self.__admin_console.fill_form_by_name('serviceName', service_name)
        if use_catalog_connect:
            self.__admin_console.enable_toggle(index=0)
            self.__admin_console.fill_form_by_name('catalogUserName', catalog_username)
            self.__admin_console.fill_form_by_name('catalogPassword', catalog_password)
            self.__admin_console.fill_form_by_name('catalogInstanceName', catalog_service_name)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_oracle_rac_instance(self, rac_instance_name, rac_cluster_name, rac_nodes, plan, use_catalog_connect,
                                catalog_username, catalog_password, catalog_service_name):
        """Adds new oracle RAC instance

            Args:
                rac_instance_name       (str)   --  name of the instance
                rac_cluster_name        (str)   --  name of the cluster
                rac_nodes               (list)  --  list containing details of all the nodes
                plan                    (str)   --  Plan to be associated with the instance
                use_catalog_connect     (bool)  --  option to use catalog connect
                catalog_username        (str)   --  Catalog username
                catalog_password        (str)   --  Catalog password
                catalog_service_name    (str)   --  Connect service name

        """

        self.click_on_add_instance(self.props['agentType.oracleRac'])
        self._panel_dropdown.select_drop_down_values(values=[rac_cluster_name],
                                                     drop_down_id='cvClients')
        self.__admin_console.fill_form_by_name('instanceName', rac_instance_name)
        self._panel_dropdown.select_drop_down_values(
            values=[plan], drop_down_id='racCreateDatabase_isteven-multi-select_#4818')

        for node in rac_nodes:
            self.__admin_console.select_hyperlink("Add RAC instance")
            self._panel_dropdown.select_drop_down_values(values=[node['RacServer']], drop_down_id='cvClients')
            self.__admin_console.fill_form_by_name('instanceName', node['RacInstance'])
            self.__admin_console.fill_form_by_name('oracleHome', node['OracleHomeDir'])
            self.__admin_console.fill_form_by_name('dbUserName', node['ConnectUsername'])
            self.__admin_console.fill_form_by_name('dbPassword', node['ConnectPassword'])
            self.__admin_console.fill_form_by_name('dbInstanceName', node['RacInstance'])
            self.__admin_console.submit_form()

        if use_catalog_connect:
            self.__admin_console.enable_toggle(index=1)
            self.__admin_console.fill_form_by_name('catalogUserName', catalog_username)
            self.__admin_console.fill_form_by_name('catalogPassword', catalog_password)
            self.__admin_console.fill_form_by_name('catalogInstanceName', catalog_service_name)
        else:
            self.__admin_console.disable_toggle(index=1)
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_saphana_instance(
            self, system_name, sid, plan, host_list, database_user=None,
            database_password=None, store_key=None, add_new_system=False):
        """Adds new SAP HANA instance

            Args:
                system_name         (str)   --  SAP Hana system name

                sid                 (str)   --  Instance Name

                plan                (str)   --  Plan name

                host_list           (list)  --  list of host for SAP HANA instance

                database_user       (str)   --  Database user name
                    default: None

                database_password   (str)   --  database password
                    default: None

                store_key           (str)   --  Store key, needed only when HDB store key is selected
                    default: None

                add_new_system      (bool)  --  Boolen value to specify if new system needs to be added
                    default: None

        """
        self.click_on_add_instance(self.props['agentType.sapHana'])
        if not add_new_system:
            self._panel_dropdown.select_drop_down_values(values=[system_name], drop_down_id='cvClients')
        else:
            self.__admin_console.enable_toggle(toggle_id='newServer')
            self.__admin_console.fill_form_by_name('clientName', system_name)
        self.__admin_console.fill_form_by_name('instanceName', sid)
        self._panel_dropdown.select_drop_down_values(
            values=[plan], drop_down_id='planDropdown')
        self._panel_dropdown.select_drop_down_values(
            values=host_list, drop_down_id='hanaHostList', default_unselect=False)
        if database_user and database_password:
            self.__admin_console.fill_form_by_name('dbUsername', database_user)
            self.__admin_console.fill_form_by_name('dbPassword', database_password)
        elif store_key:
            self.__admin_console.select_radio(id='HDB')
            self.__admin_console.fill_form_by_name('hdbuserstorekey', store_key)
        else:
            raise Exception("Credentials are not provided")
        self.__admin_console.submit_form()

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
        self.click_on_add_instance(self.props['agentType.SybaseHADR'])
        self.wizard.select_plan(plan)
        self.wizard.click_next()
        self.wizard.fill_text_in_field(label='Instance name', text=instance_name)
        self.wizard.click_next()
        for node in nodes:
            self.wizard.click_button(name='Add')
            self.dialog.select_dropdown_values(drop_down_id='serverDropdown', values=[node.get('name')])
            self.dialog.fill_text_in_field(element_id='osPassword', text=node.get('OSPassword'))
            self.dialog.fill_text_in_field(element_id='osUserName', text=node.get('OSUsername'))
            self.dialog.fill_text_in_field(element_id='sybaseServerName', text=node.get('ASEserver'))
            self.dialog.fill_text_in_field(element_id='saUserName', text=node.get('SA_Username'))
            self.dialog.fill_text_in_field(element_id='saPassword', text=node.get('Password'))
            self.dialog.click_submit()
        self.wizard.click_next()
        self.wizard.click_button(name='Finish')

    @PageService(hide_args=True)
    def add_multinode_database_instance(self, client_name, xbsa_clients, database_server,
                                        instance_name, database_name, plan):
        """
        Creates Multinode Database Instance
        Args:
            client_name           (str)  :  Name of the client under which instance to be created
            xbsa_clients          (list) :  List of hosts for Multinode Database instance
            database_server       (str)  :  Database server
            instance_name         (str)  :  Name of the instance to be created
            database_name         (str)  :  Database name for the instance
            plan                  (str)  :  Name of the plan that is to be associated with the instance
        """
        self.click_on_add_instance(self.props['agentType.multiNode_DB'])
        self.__admin_console.fill_form_by_name('serverName', client_name)
        self._panel_dropdown.select_drop_down_values(values=xbsa_clients, drop_down_id='cvClients')
        self._panel_dropdown.select_drop_down_values(values=[database_server], drop_down_id='multiNodeServerType')
        self.__admin_console.fill_form_by_name('instanceName', instance_name)
        self.__admin_console.fill_form_by_name('databaseName', database_name)
        self._panel_dropdown.select_drop_down_values(values=[plan], drop_down_id='planDropdown')
        self.__admin_console.submit_form()

    @PageService(hide_args=True)
    def add_postgresql_cluster_instance(self, instance_name, nodes, plan, cluster_type,
                                        cluster_bin=None, cluster_conf=None):
        """
        Creates Multinode Database Instance
        Args:
            instance_name       (str)   : Name of the client under which instance to be created
            nodes               (list)  : [node],
            plan                (str)   :  Name of the plan that is to be associated with the instance
            cluster_type        (str)   :  Type of cluster (native, EFM, patroni, rep_mgr)
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
            }
        """
        self.click_on_add_instance(self.props['agentType.postgres_cluster'])
        self.wizard.select_plan(plan)
        self.wizard.click_next()
        self.wizard.fill_text_in_field(label='Instance name', text=instance_name)
        self._panel_dropdown.select_drop_down_values(values=[cluster_type], drop_down_id='clusterType')
        self.wizard.click_next()
        for node in nodes:
            self.wizard.click_button(name='Add')
            self.dialog.select_dropdown_values(drop_down_id='serverDropdown', values=[node.get('server')])
            self.dialog.fill_text_in_field(element_id='dbPassword', text=node.get('password'))
            self.dialog.fill_text_in_field(element_id='port', text=node.get('port'))
            self.dialog.fill_text_in_field(element_id='binaryPath', text=node.get('bin_dir'))
            self.dialog.fill_text_in_field(element_id='libPath', text=node.get('lib_dir'))
            self.dialog.fill_text_in_field(element_id='archiveLogPath', text=node.get('archive_wal_dir'))
            if cluster_type != 'Native replication':
                self.dialog.fill_text_in_field(element_id='clusterBinaryPath', text=cluster_bin)
                self.dialog.fill_text_in_field(element_id='clusterConfigFile', text=cluster_conf)
            self.dialog.click_submit()
        self.wizard.click_next()
        self.wizard.click_button(name='Finish')

    @PageService(hide_args=True)
    def add_sap_oracle_instance(self, server_name, oracle_sid, plan, oracle_home,
                            username, password, service_name, sap_data_home, sap_exe_path, use_sap_secure_store):
        """Adds new sap oracle instance

            Args:
                server_name             (str)   --  Server name
                oracle_sid              (str)   --  Oracle server SID
                plan                    (str)   --  Plan to be associated with the instance
                oracle_home             (str)   --  oracle home directory
                username                (str)   --  Oracle server username
                password                (str)   --  Oracle server password
                service_name            (str)   --  Oracle service name
                sap_data_home           (str)   --  sap data directory
                sap_exe_path            (str)   --  sap exe path
                use_sap_secure_store    (bool)  --  True sap secure is to be enabled
                
        """

        self.click_on_add_instance(self.props['agentType.SAP for Oracle'])
        self._panel_dropdown.select_drop_down_values(values=[server_name],
                                                     drop_down_id='cvClients')
        self.__admin_console.fill_form_by_name('instanceName', oracle_sid)
        self._panel_dropdown.select_drop_down_values(
            values=[plan], drop_down_id='planDropdown')
        self.__admin_console.fill_form_by_name('oracleHome', oracle_home)
        self.__admin_console.fill_form_by_name('dbUserName', username)
        self.__admin_console.fill_form_by_name('dbPassword', password)
        self.__admin_console.fill_form_by_name('serviceName', service_name)
        self.__admin_console.fill_form_by_name('sapDataPath', sap_data_home)
        self.__admin_console.fill_form_by_name('sapExeFolder', sap_exe_path)
        if use_sap_secure_store:
            self.__admin_console.enable_toggle(index=0)      
        self.__admin_console.submit_form()