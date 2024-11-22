from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Instances file has the functions to operate on instance page in Big data.

Instances:

    access_instance                   --     Accesses specified instance

    access_server                     --     Accesses specified server

    access_restore                    --     Accesses specified restore page

    access_backup_history             --     Access backup history of specified instance

    access_restore_history            --     Access restore history of specified instance

    add_data_center                   --     Add data center

    add_cassandra_server              --     adds cassandra server

    add_couchbase_server              --     adds couchbase server

    add_splunk_server                 --     adds splunk server

    add_mongodb_server                --      adds mongoDB server

    create_mongodb_instance           --     Creates MongoDB pseudoclient instance

    create_mongodb_instance           --     Creates MongoDB instance

    delete_instance_name              --     Deletes specified instance

    add_hadoop_server                 --     Add hadoop server

CassandraServer:

    set_name                         --     Sets name field

    select_gateway_node              --     Sets gateway node

    set_gateway_java_path            --    Sets gateway java path

    set_cql_host                     --    Sets CQL host address

    set_jmx_port                     --    Sets jmx port number

    enable_cql                       --    Enables CQL

    enable_jmx                       --    Enables JMX

    enable_ssl                       --    Enables SSL

    expand_authentication_settings   --    Expands authentication settings


CouchbaseServer:

    add_couchbase_parameters         --     Add couchbase parameters in the client creation form

    save                             --     Click Save

SplunkServer:

    set_name                         --     Sets name field

    select_master_node               --     Selects master node

    set_url                          --     Sets URL field

    set_user_name                    --     Sets user name

    set_password                     --     Sets password

    set_confirm_password             --     Sets confirm password field

    select_plan                       --    Selects plan

HadoopServer:

    add_hadoop_parameters            --     Add hadoop parameters in the client creation form

    save                             --     Click Save

MongoDBServer:

    set_name                         --      Set MongoDB instance name

    select_master_node               --      Select master node

    set_port_number                  --      Select port number

    set_os_username                  --      Select OS username

    select_plan                      --      Select plan

    set_bin_file_path                --      Select binary path

    save                             --      Save details

    set_db_username                  --      Set DB username

    set_db_password                  --      Set DB password

    expand_authentication_settings   --      Expand authentication settings

RMongoDBServer:

    select_mongodb                      --      Select MongoDB instance

    set_name                         --      Set MongoDB instance name

    select_master_node               --      Select master node

    set_port_number                  --      Select port number

    set_os_username                  --      Select OS username

    select_plan                      --      Select plan

    set_bin_file_path                --      Select binary path

    save                             --      Save details

    set_db_username                  --      Set DB username

    set_db_password                  --      Set DB password

"""
import time
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import DropDown, ModalPanel, RDropDown, RModalPanel
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.page_container import PageContainer
from selenium.webdriver.common.by import By


class Instances:
    """
    Instances class has the functions to operate on instance page in Big data.
    """

    def __init__(self, admin_console):
        self.__driver = admin_console.driver
        self.driver = None
        self._admin_console = admin_console
        self._admin_console.load_properties(self)
        self.__table = Rtable(admin_console)
        self.__rmodaldialog = RModalDialog(admin_console)
        self.__wizard = Wizard(admin_console)
        self.browse = RContentBrowse(admin_console)

    @PageService()
    def access_instance(self, instance):
        """
        Access instance
        Args:
            instance                         (String)       --    Instance name
        """
        self.__table.access_link(instance)

    @PageService()
    def access_server(self, server_name):
        """
        Access server
        Args:
            server_name                     (String)       --     Server name
        """
        self.__table.access_link_by_column(server_name, 'Server name')

    @PageService()
    def add_cassandra_server(self):
        """Add cassandra server"""
        self.__table.access_toolbar_menu('Add cluster')
        self.__wizard.select_radio_button(id='CASSANDRA')
        self.__wizard.click_next()
        return CassandraServer(self._admin_console)

    @PageService()
    def add_couchbase_server(self):
        """Add couchbase server"""
        self.__table.access_toolbar_menu('Add cluster')
        self.__wizard.select_radio_button(id='COUCHBASE')
        self.__wizard.click_next()
        return CouchbaseServer(self._admin_console)

    @PageService()
    def add_mongodb_server(self):
        """Add mongodb server"""
        self.__table.access_toolbar_menu(self._admin_console.props['action.addCluster'])
        return RMongodbServer(self._admin_console)


    @PageService()
    def create_mongodb_instance(self, master_node, name="testcase_pseudoclient",
                                db_user="cv_root", db_pwd="#####",
                                os_name=None, plan=None, port_number=None, bin_path=None):
        """
        Creates  a mongodb instance
        Args:
            name                         (String)         --     name for Mongodb server
            master_node                  (String)         --     master_node for mongodb server
            port_number                  (String)         --     port number
            os_name                      (String)         --     os user name
            plan                         (String)         --     plan name
            bin_path                     (String)         --     binary file path
            db_user                      (String)         --    database username
            db_pwd                       (String)         --    database password
        """
        _mongodb_server = self.add_mongodb_server()
        _mongodb_server.select_mongodb()
        _mongodb_server.select_plan(plan)
        _mongodb_server.set_name(name)
        _mongodb_server.select_master_node(master_node)
        self._admin_console.wait_for_completion()
        if bin_path is not None:
            _mongodb_server.set_bin_file_path(bin_path)
        if os_name is not None:
            _mongodb_server.set_os_username(os_name)
        if port_number is not None:
            _mongodb_server.set_port_number(port_number)
        self._admin_console.wait_for_completion()
        if db_user and db_pwd is not None:
            _mongodb_server.set_db_username(db_user)
            _mongodb_server.set_db_password(db_pwd)
        self.__wizard.click_next()
        self._admin_console.wait_for_completion()
        _mongodb_server.save()
        self._admin_console.check_error_message(raise_error=True)

    @PageService()
    def add_hadoop_server(self):
        """Add hadoop server"""
        self.__table.access_toolbar_menu('Add cluster')
        self._admin_console.access_sub_menu("Hadoop")
        return HadoopServer(self._admin_console)

    @PageService()
    def add_splunk_server(self):
        """Add splunk server"""

        self.__table.access_toolbar_menu(self._admin_console.props['action.addCluster'])
        self.__wizard.select_radio_button(id='SPLUNK')
        self.__wizard.click_next()
        return SplunkServer(self._admin_console)

    @PageService()
    def add_cockroachdb_server(self):
        """Add cassandra server"""
        self.__table.access_toolbar_menu('Add cluster')
        self.__wizard.select_radio_button(id='COCKROACHDB')
        self.__wizard.click_next()
        return CockroachDBServer(self._admin_console)

    @PageService()
    def add_yugabytedb_server(self):
        """Add yugabytedb server"""
        self.__table.access_toolbar_menu('Add cluster')
        self.__wizard.select_radio_button(id='YUGABYTEDB')
        self.__wizard.click_next()
        return YugabyteDBServer(self._admin_console)

    @PageService()
    def access_backup_history(self, instance):
        """
        Access backup history
        Args:
            instance                       (String)       --     Instance name
        """
        self.__table.access_action_item(instance, 'Backup history')

    @PageService()
    def access_restore_history(self, instance):
        """Access restore history
        Args:
            instance                       (String)       --     Instance name
        """
        self.__table.access_action_item(instance, 'Restore history')

    @PageService()
    def add_data_center(self, instance):
        """Add data center
        Args:
            instance                       (String)       --     Instance name
        """
        self.__table.access_action_item(instance, 'Add data center')

    @PageService()
    def access_restore(self, instance='default'):
        """Access restore of specified instance
        Args:
            instance                   (String)          --     Instance name
        """
        self.__table.access_action_item(instance, 'Restore')
        self._admin_console.wait_for_completion()

    @PageService()
    def access_backup(self, instance='default'):
        """Access restore of specified instance
        Args:
            instance                   (String)          --     Instance name
        """
        self.__table.access_action_item(instance, 'Backup')
        self._admin_console.wait_for_completion()

    @PageService()
    def is_instance_exists(self, instance):
        """Check if instance exists"""
        return self.__table.is_entity_present_in_column('Name', instance)

    @PageService()
    def delete_instance_name(self, instance):
        """Delete instance
        Args:
            instance                       (String)       --     Instance name
        """
        self.__table.access_action_item(instance, 'Retire')
        self._admin_console.fill_form_by_id("confirmText", "RETIRE")
        self._admin_console.click_button_using_text("Retire")
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()

        if self.is_instance_exists(instance):
            self.__table.access_action_item(instance, 'Delete')
            self._admin_console.fill_form_by_id("confirmText", "DELETE")
            self._admin_console.click_button_using_text("Delete")
            self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()


class CassandraServer(ModalPanel):
    """Add cassandra server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__dropdown = DropDown(admin_console)
        self.__wizard = Wizard(admin_console)

    def _click_expand(self, label):
        """"expand authentication"""
        xpath = f"//h3[contains(text(),'{label}')]"
        self._admin_console.click_by_xpath(xpath)

    @PageService()
    def add_cassandra_server(
            self,
            instanceparam,
            ssl=False,
            jmx=True,
            cql=True):
        """
        Select Plan
        Args:
            instanceparam(dict)          --    cassandra instnace configuration parameter
        """
        self.__wizard.select_plan(instanceparam['planname'])
        self.__wizard.click_next()
        self._admin_console.log.info(
            "cluser name:  %s",
            instanceparam['clustername'])
        self.__wizard.fill_text_in_field(
            id='clusterName', text=instanceparam['clustername'])
        self.__wizard.select_drop_down_values(
            id='accessNodeDropdown', values=[
                instanceparam['node']])
        self.__wizard.fill_text_in_field(
            id='configFilePath',
            text=instanceparam['configfilepath'])
        self.__wizard.fill_text_in_field(
            id='cqlAuthenticationPort',
            text=instanceparam['cqlport'])
        self.__wizard.fill_text_in_field(
            id='jmxPort', text=instanceparam['jmxport'])
        self.__wizard.click_next()

        if cql:
            self._click_expand('CQL')
            self.__wizard.fill_text_in_field(
                id='cqlUsername', text=instanceparam['cqlusername'])
            self.__wizard.fill_text_in_field(
                id='cqlPassword', text=instanceparam['cqlpassword'])
            self._click_expand('CQL')
        if jmx:
            self._click_expand('JMX')
            self.__wizard.fill_text_in_field(
                id='jmxUsername', text=instanceparam['jmxusername'])
            self.__wizard.fill_text_in_field(
                id='jmxPassword', text=instanceparam['jmxpassword'])
            self._click_expand('JMX')
        if ssl:
            self._click_expand('SSL')
            self.__wizard.fill_text_in_field(
                id='keyStore', text=instanceparam['keystore'])
            self.__wizard.fill_text_in_field(
                id='keyStorePass', text=instanceparam['keystorepassword'])
            self.__wizard.fill_text_in_field(
                id='trustStore', text=instanceparam['truststore'])
            self.__wizard.fill_text_in_field(
                id='trustStorePass', text=instanceparam['truststorepassword'])
            self._click_expand('SSL')
        self.__wizard.click_next()
        self.__wizard.click_finish()

    @PageService()
    def set_name(self, name):
        """
        Set name
        Args:
            name                           (String)         -- Set name for Cassandra server
        """
        self._admin_console.fill_form_by_id('name', name)

    @PageService()
    def select_gateway_node(self, node):
        """Select gateway node
        Args:
            node                           (String)         --     Set name for Cassandra server
        """
        self.__dropdown.select_drop_down_values(drop_down_id='cassandraClients', values=[node])

    @PageService()
    def set_gateway_java_path(self, path):
        """Set gateway java path
        Args:
            path                          (String)         --     Set gateway path
        """
        self._admin_console.fill_form_by_id('javaHome', path)

    @PageService()
    def set_cql_host(self, host_name):
        """Set sql host
        Args:
            host_name                    (String)         --      Set host name
        """
        self._admin_console.fill_form_by_id('ipAddress', host_name)

    @PageService()
    def select_plan(self, plan_name):
        """Select plan
         Args:
            plan_name                    (String)         --      select plan
        """
        self.__dropdown.select_drop_down_values(drop_down_id='plan', values=[plan_name])

    @PageService()
    def set_config_file_path(self, conf_file_path):
        """Set config file path
         Args:
            conf_file_path                (String)        --      set config file path
        """
        self._admin_console.fill_form_by_id('configFilePath', conf_file_path)

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.click_button('Save')
        self._admin_console.click_button('OK')

    @PageService()
    def set_cql_port(self, port):
        """Set CQL port number
         Args:
            port                           (String)       --     set CQL port number
        """
        self._admin_console.fill_form_by_id('gatewayCQLPort', port)

    @PageService()
    def set_jmx_port(self, port):
        """Set JMX port number
         Args:
            port                           (String)       --     set JMX port number
        """
        self._admin_console.fill_form_by_id('port', port)

    @PageService()
    def enable_cql(self, user_name, password):
        """Enable cql"""
        self._admin_console.fill_form_by_id(
            element_id='CQLUsername', value=user_name)
        self._admin_console.fill_form_by_id(
            element_id='CQLPassword', value=password)

    @PageService()
    def enable_jmx(self, user_name, password):
        """Enable jmx"""
        self._admin_console.fill_form_by_id(
            element_id='JMXUsername', value=user_name)
        self._admin_console.fill_form_by_id(
            element_id='JMXPassword', value=password)

    @PageService()
    def enable_ssl(self, keystore, keystorepwd, truststore, truststorepwd):
        """Enable ssl"""
        self._admin_console.fill_form_by_id(
            element_id='keyStore', value=keystore)
        self._admin_console.fill_form_by_id(
            element_id='keyStorePass', value=keystorepwd)
        self._admin_console.fill_form_by_id(
            element_id='trustStore', value=truststore)
        self._admin_console.fill_form_by_id(
            element_id='trustStorePass', value=truststorepwd)

    @PageService()
    def expand_authentication_settings(self):
        """Expand authentication settings"""
        self._expand_accordion('Authentication settings')


class CouchbaseServer(ModalPanel):
    """Add couchbase server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__rdropdown = RDropDown(admin_console)

    @PageService()
    def add_couchbase_parameters(self, name, access_nodes, port, username, password, staging_type,
                                 credentials, service_host, staging_path, plan_name):
        """Add couchbase parameters in the client creation form

                    Args:
                        name            (str)   -- name of couchbase server

                        access_nodes    (list)   -- access nodes to be selected

                        port            (str)   -- couchbase port

                        username        (str)   -- username to connect to cluster

                        password        (str)   -- password to connect to cluster

                        staging_type    (str)   -- select staging type s3 or file system

                        credentials     (str)   -- s3 credentials

                        service_host    (str)   -- service host endpoint

                        staging_path    (str)   -- path where data is to be staged

                        plan_name       (str)   -- server plan name

                """
        self._admin_console.fill_form_by_id('clusterName', name)
        self.__rdropdown.select_drop_down_values(drop_down_id='accessNodeDropdown', values=access_nodes)
        self._admin_console.fill_form_by_id('portNumber', port)
        self._admin_console.fill_form_by_id('userName', username)
        self._admin_console.fill_form_by_name('password', password)
        if staging_type == "S3":
            self._admin_console.select_radio(value='S3')
            self._admin_console.driver.find_element(By.XPATH, "//div[@id='authenticationType']").click()
            self._admin_console.driver.find_element(By.XPATH, "//span[text()='Access and secret keys']").click()
            self.__rdropdown.select_drop_down_values(drop_down_id='credentials', values=[credentials])
            self._admin_console.fill_form_by_id('serviceHost', service_host)
        else:
            self._admin_console.select_radio(value='File System')
        self._admin_console.fill_form_by_name('path', staging_path)
        self.__rdropdown.select_drop_down_values(drop_down_id='couchbasePlan', values=[plan_name])

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.click_button('Save')


class MongodbServer(ModalPanel):
    """Add Mongodb server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__dropdown = DropDown(admin_console)

    @PageService()
    def set_name(self, name):
        """
        Set name
        Args:
            name                           (String)         -- Set name for Mongodb server
        """
        self._admin_console.fill_form_by_name('clientName', name)

    @PageService()
    def select_master_node(self, master_node):
        """Select master node
        Args:
            master_node                           (String)         --     Set master_node for mongodb server
        """
        self.__dropdown.select_drop_down_values(drop_down_id='mongoDBClients', values=[master_node])

    @PageService()
    def set_port_number(self, port_number):
        """Set port number
        Args:
            port_number                          (String)         --     Set port number
        """
        if port_number is not None:
            self._admin_console.fill_form_by_id('portNumber', port_number)

    @PageService()
    def set_os_username(self, os_name):
        """Set os user name
        Args:
            os_name                    (String)         --      Set os user name
        """
        if os_name is not None:
            self._admin_console.fill_form_by_id('osUserName', os_name)

    @PageService()
    def select_plan(self, plan_name):
        """Select plan
         Args:
            plan_name                    (String)         --      select plan
        """
        self.__dropdown.select_drop_down_values(drop_down_id="plan", values=[plan_name])

    @PageService()
    def set_bin_file_path(self, bin_file_path):
        """Set binary file path
         Args:
            bin_file_path                (String)        --      set binary file path
        """
        if bin_file_path is not None:
            self._admin_console.fill_form_by_name('binPathConfigured', bin_file_path)

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.click_button('Save')

    @PageService()
    def set_db_username(self, db_username):
        """Set db user name
         Args:
            db_username                           (String)       --     set db username
        """
        self._admin_console.fill_form_by_id('dbUsername', db_username)

    @PageService()
    def set_db_password(self, db_password):
        """Set db password
         Args:
            db_password                         (String)       --     set db password
        """
        self._admin_console.fill_form_by_id('dbPassword', db_password)

    @PageService()
    def expand_authentication_settings(self):
        """Expand authentication settings"""
        self._expand_accordion(self._admin_console.props['heading.additionalSettings'])


class RMongodbServer(ModalPanel):
    """Add Mongodb server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__wizard = Wizard(admin_console)
        self.__rdropdown = RDropDown(admin_console)

    @PageService()
    def select_mongodb(self):
        """
        Select MongoDB instance creation
        """
        self.__wizard.select_radio_button(id="MONGODB")
        self.__wizard.click_next()

    @PageService()
    def set_name(self, name):
        """
        Set name
        Args:
            name                           (String)         -- Set name for Mongodb server
        """

        self.__wizard.fill_text_in_field(id="clusterName", text=name)

    @PageService()
    def select_master_node(self, master_node):
        """Select master node
        Args:
            master_node                           (String)         --     Set master_node for mongodb server
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='accessNodeDropdown',values=[master_node])


    @PageService()
    def set_port_number(self, port_number):
        """Set port number
        Args:
            port_number                          (String)         --     Set port number
        """
        if port_number is not None:
            self.__wizard.fill_text_in_field(id="portNumber", text=port_number)
            self.__wizard.click_next()

    @PageService()
    def set_os_username(self, os_name):
        """Set os user name
        Args:
            os_name                    (String)         --      Set os user name
        """
        if os_name is not None:
            self.__wizard.fill_text_in_field(id="osUsername", text=os_name)


    @PageService()
    def select_plan(self, plan_name):
        """Select plan
         Args:
            plan_name                    (String)         --      select plan
        """

        self.__wizard.select_plan(plan_name)
        self.__wizard.click_next()

    @PageService()
    def set_bin_file_path(self, bin_file_path):
        """Set binary file path
         Args:
            bin_file_path                (String)        --      set binary file path
        """
        if bin_file_path is not None:
            self.__wizard.fill_text_in_field(id="binaryPath", text=bin_file_path)

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.click_button("Finish")
        self._admin_console.wait_for_completion()

    @PageService()
    def set_db_username(self, db_username):
        """Set db user name
         Args:
            db_username                           (String)       --     set db username
        """
        self.__wizard.fill_text_in_field(id="username", text=db_username)

    @PageService()
    def set_db_password(self, db_password):
        """Set db password
         Args:
            db_password                         (String)       --     set db password
        """
        self.__wizard.fill_text_in_field(id="password", text=db_password)
        self.__wizard.click_next()
        self._admin_console.wait_for_completion()


class SplunkServer:
    """Add Splunk server"""

    def __init__(self, admin_console):
        self.__driver = admin_console.driver
        self.navigator = None
        self.dialog = None
        self._admin_console = admin_console
        self._admin_console.load_properties(self)
        self.__wizard = Wizard(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.panel = RModalPanel(admin_console)
        self.page_container = PageContainer(admin_console)
        self.treeview = TreeView(admin_console)
        self.core = TreeView(admin_console)
        self.dialog = RBackup(admin_console)
        self.backup_type = None

    @PageService()
    def add(self, inputs):
        """
         Sets up configuration based on the provided inputs.
         Args :
             inputs      (dict)    --    Dictionary containing configuration parameters.
             Example input dictionary:
             inputs ={
                  'Plan':'Splunk-Automation-Plan',
                  'Name' :'YourClusterName,
                  'Master_node:'Node1',
                   Uri:'https://vb-splunk.master.url',
                   Username:'your_username',
                   Password:'your_password',
                   Nodes:['Node2','Node3'],
                   Indexes:["_audit"],
                   Backup_type:"FULL/INCREMENTAL"
                    }
        """
        self.select_plan(inputs['Plan'])
        self.set_name(inputs['Name'])
        self.select_master_node(inputs['Master_node'])
        self.set_splunk_master_url(inputs['Uri'])
        self.set_user_name(inputs['Username'])
        self.set_password(inputs['Password'])
        self.set_confirm_password(inputs['Password'])
        self.select_nodes(inputs['Nodes'])
        self.add_content(inputs['Indexes'])
        self._admin_console.wait_for_completion()
        self._admin_console.click_button("Next")
        self._admin_console.wait_for_completion()
        self._admin_console.click_button("Finish")
        self._admin_console.wait_for_completion()

    @PageService()
    def backup(self, backup_type):
        """
          backup
          Args:
              backup_type               (string)       --     backup_type-->FULL/INCREMENTAL
        """
        self.page_container.access_page_action('Backup')
        backup_type_upper = backup_type.upper()
        value = getattr(RBackup.BackupType, backup_type_upper, None)
        if value is not None:
            job_id = self.dialog.submit_backup(backup_type=value)
            self._admin_console.wait_for_completion()
            return job_id

    @PageService()
    def set_name(self, name):
        """
        Set name
        Args:
            name                            (String)      --    Set name for splunk server
        """
        self._admin_console.fill_form_by_id('clusterName', name)

    @PageService()
    def select_master_node(self, master_node):
        """Select master node
        Args:
            master_node                     (String)      --     select master node
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='accessNodeDropdown', values=[master_node])

    @PageService()
    def set_splunk_master_url(self, uri):
        """Set URL
        Args:
            uri                            (String)      --      set url
        """
        self._admin_console.fill_form_by_id('masterURI', uri)

    @PageService()
    def set_user_name(self, username):
        """
        Set user name
        Args:
            username                      (String)      --      set user name
        """
        self._admin_console.fill_form_by_id('username', username)

    @PageService()
    def set_password(self, password):
        """
        Set password
        Args:
            password                      (String)       --      set password
        """
        self._admin_console.fill_form_by_id('password', password)

    @PageService()
    def set_confirm_password(self, password):
        """
        Set confirm password
        Args:
            password                      (String)     --        set confirm password string
        """
        self._admin_console.fill_form_by_id('confirmPassword', password)
        self.__wizard.click_next()

    @PageService()
    def select_plan(self, plan_name):
        """
        Select plan
        Args:
            plan_name                       (String)     --       Select plan
        """
        self.__wizard.select_plan(plan_name)
        self.__wizard.click_next()

    @PageService()
    def select_nodes(self, nodes):
        """Select node
        Args:
            nodes                              [List]     --     select  nodes
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='accessNodeDropdown', values=nodes)
        self._admin_console.wait_for_completion()
        self.__wizard.click_button("Next")
        self._admin_console.wait_for_completion()

    def add_content(self, indexes):
        self.__wizard.click_button("Add")
        time.sleep(10)
        self._admin_console.wait_for_completion()
        self._admin_console.click_button("Browse")
        self._admin_console.wait_for_completion()
        self.core.select_items(indexes)
        self._admin_console.click_button("Save")


class HadoopServer(ModalPanel):
    """Add Hadoop server"""

    def __init__(self, admin_console):
        """Initialize object for HadoopServer class.

            Args:
                admin_console       (obj)   -- admin_console object
            Returns:
                object - instance of HadoopServer class

        """
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__modalpanel = ModalPanel(admin_console)

    @PageService()
    def add_hadoop_parameters(self, name, access_nodes, hdfs_user, plan_name):
        """Add hadoop parameters in the client creation form

            Args:
                name            (str)   -- name of hadoop server

                access_nodes    (list)  -- list of access nodes to select

                hdfs_user       (str)   -- hadoop user

                plan_name       (str)   -- plan name to select

        """
        self._admin_console.fill_form_by_id('name', name)
        self.__dropdown.select_drop_down_values(drop_down_id='dataAccessNodes', values=access_nodes)
        self._admin_console.fill_form_by_id('hdfsUser', hdfs_user)
        self.__dropdown.select_drop_down_values(drop_down_id="plan", values=[plan_name])

    @PageService()
    def save(self):
        """Click save"""
        self.__modalpanel.submit()


class CockroachDBServer(RModalPanel):
    """Add cockroachDB server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__wizard = Wizard(admin_console)
        self.__rmodalpanel = RModalPanel(admin_console)
        self.__rdropdown = RDropDown(admin_console)

    def _click_expand(self, label):
        """"expand authentication"""
        xpath = f"//h3[contains(text(),'{label}')]"
        self._admin_console.click_by_xpath(xpath)

    @PageService()
    def add_cockroachdb_instance(self, instanceparam):
        """
        Select Plan
        Args:
            instanceparam(dict)      --    cockroachdb instance configuration parameter
        """
        self.__wizard.select_drop_down_values(
            id='accessNodeDropdown',
            values=instanceparam['accessnodes'])
        self.__wizard.click_button("NEXT")
        self.__wizard.select_plan(instanceparam['planname'])
        self.__wizard.click_next()

        self.__wizard.fill_text_in_field(
            id='clusterName', text=instanceparam['clustername'])
        self.__wizard.fill_text_in_field(
            id='hostName', text=instanceparam['cockroachdbhost'])
        self.__wizard.fill_text_in_field(
            id='portNumber', text=instanceparam['cockroachdbport'])
        self.__wizard.select_radio_button(id='toggleFetchCredentialsDb')
        self.__wizard.fill_text_in_field(
            id='userNameDb', text=instanceparam['dbusername'])
        self.__wizard.fill_text_in_field(
            id='passwordDb', text=instanceparam['dbpassword'])

        xpath = "//button/div[contains(text(), 'Cancel')]"
        self._admin_console.scroll_into_view(xpath)
        if instanceparam['useiamrole']:
            self.__wizard.select_drop_down_values(
                id='authenticationType', values=["IAM role"])
        else:
            listcredentials = self.__rdropdown.get_values_of_drop_down(
                'credentials')
            if instanceparam['s3credential'] not in listcredentials:
                self.__wizard.click_add_icon(index=0)
                self.__rmodalpanel.fill_input(
                    text=instanceparam['s3credential'], id='name')
                self.__rmodalpanel.fill_input(
                    text=instanceparam['awsaccesskey'], id='accessKeyId')
                self.__rmodalpanel.fill_input(
                    text=instanceparam['awssecretkey'], id='secretAccessKey')
                self.__rmodalpanel.save()
            self.__wizard.select_drop_down_values(
                id='credentials', values=[
                    instanceparam['s3credential']])

        self.__wizard.fill_text_in_field(
            id='serviceHost', text=instanceparam['s3servicehost'])
        self.__wizard.fill_text_in_field(
            id='path', text=instanceparam['s3stagingpath'])

        if instanceparam['usessl']:
            self._admin_console.scroll_into_view(xpath)
            self._click_expand('SSL')
            self.__wizard.fill_text_in_field(
                id='sslRootCert', text=instanceparam['sslrootcert'])
            self.__wizard.fill_text_in_field(
                id='sslCert', text=instanceparam['sslcert'])
            self.__wizard.fill_text_in_field(
                id='sslKey', text=instanceparam['sslkey'])

        self.__wizard.click_button("NEXT")


class YugabyteDBServer(RModalPanel):
    """Add yugabyteDB server"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__wizard = Wizard(admin_console)
        self.__rmodalpanel = RModalPanel(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__rbrowse = RContentBrowse(admin_console)

    @PageService()
    def add_yugabytedb_parameters(self, access_nodes, plan_name, yugabytedb_server_name, yugabytedb_host,
                                  api_token, universe_name, storage_config, credential, sqldbname, cqldbname):
        """Add yugabyte parameters in the client creation form

                    Args:

                        access_nodes                (list)   -- access nodes to be selected

                        plan_name                   (str)    -- server plan name

                        yugabytedb_server_name      (str)    -- name of yugabytedb server

                        yugabytedb_host             (str)    -- yugabytedb host IP

                        api_token                   (str)    -- api token of the yugabytedb admin user

                        universe_name               (str)    -- name of the universe to be backed up and restored

                        storage_config              (str)    -- storage config to be used for backups and restores

                        credential                  (str)    -- credential to be used

                        sqldbname                   (str)    -- name of the ysql database

                        cqldbname                   (str)    -- name of the ycql database

                """

        self.__wizard.select_drop_down_values(id='accessNodeDropdown', values=access_nodes)
        self.__wizard.click_button("NEXT")
        self.__wizard.select_plan(plan_name)
        self.__wizard.click_next()
        self.__wizard.fill_text_in_field(id='universeName', text=yugabytedb_server_name)
        self.__wizard.fill_text_in_field(id='dbHost', text=yugabytedb_host)
        self.__wizard.fill_text_in_field(id='apiToken', text=api_token)
        self.__wizard.click_button("NEXT")
        self.__wizard.select_drop_down_values(id='universeList', values=[universe_name])
        self.__wizard.select_drop_down_values(id='customerConfig', values=[storage_config])
        self.__wizard.select_drop_down_values(id='credentials', values=[credential])
        self.__rmodalpanel.save()
        time.sleep(30)
        self.__wizard.click_next()
        time.sleep(30)
        self.__wizard.click_button('Add')
        self._admin_console.click_button('Browse')
        time.sleep(30)
        self.__rbrowse.select_content([sqldbname, cqldbname])
        self._admin_console.click_button('Save')
        self.__wizard.click_next()
        self.__wizard.click_button("Finish")