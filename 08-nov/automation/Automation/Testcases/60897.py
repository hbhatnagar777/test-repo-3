# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"60897": {
            "DomainHost": None,
            "DomainName": None,
            "Instance_Name": None,
            "Backupset_Name": None,
            "Node1HostName": None,
            "Node2HostName": None,
            "InstallClientUsername": None,
            "InstallClientPassword": None,
            "db2_username": None,
            "db2_user_password": None,
            "storage_policy": None,
            "db2_logs_dir": None,
            "db2_home_directory": None,
            "DestinationClientHostName": None,
            "DestinationClientUserName": None,
            "DestinationClientPassword": None,
            "DestinationDB2InstalledPath": /opt/ibm/db2/V11.1,
            "DestinationDB2ClientGroup": "dba"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down method to cleanup the entities

    prerequisite_setup_test_case()              --  Uninstalling existing clients and removing log directories

    prepare_clients_for_restore()               --  Prepares client for restore

    standby_takeover()                          --  Performs Takeover operation on standby node

    add_database_on_destination()               --  Adding database on client

    find_unused_port_instance()                 --  Find unused port for instance creation

    get_hadr_nodes_and_connect_status()         --  Gets Primary node and Secondary Node and Check if connected

    add_entries_to_host_file()                  --  Add entries to host file on all nodes

    install_db2_ida()                           --  Install DB2 IDA on Client

    create_cluster_client()                     --  Creates Cluster Client

    add_db2_instance()                          --  Adds DB2 Instance

    add_db2_backupset()                         --  Adds DB2 Backupset

    add_subclient()                             --  Creates a subclient

    verify_db2_instance_properties()            --  Verify instance properties

    verify_db2_backupset_properties()           --  Verify backupset properties

    compare_properties()                        --  Compares two values for a given property

    update_db2_database_configuration()         --  Updating db2 database log and vendor properties on client

    update_config1()                            --  Updating Configuration Commands

    prepare_db2_data()                          --  Preparing data on DB2 database

    db2_gui_backups()                           --  Perform all types of DB2 Backups

    db2_gui_restore()                           --  Performs GUI Restore

    db2_command_line_backups()                  --  Running command line backups

    db2_command_line_restore()                  --  Performing command line restore

    wait_for_job()                              --  Waits for given job to complete

    validate_backup_job()                       --  Validates Backup Jobs

    update_destination_db_config_restore()      --  Updating Destination Client Config for restore

    validate_restore_job()                      --  Validates Restore Jobs

    log_archiving_test()                        --  Perform Log Archive and verify if command line log backup runs

    load_copy_operation()                       --  Performing Load Copy Operation

    verify_log_archiving_node_failover()        --  Verifies Log Archive and Restore behaviour on Node Failover

    verify_primary_and_secondary_node()         --  Verify if Primary and Secondary are same

    recreate_db2_logs_dir()                     --  Recreates DB2 log directory from all nodes.

    retire_and_delete_client()                  --  Retires and Deletes Client

"""

import time
from base64 import b64encode
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from cvpysdk.subclient import Subclients
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """ DB2 HADR ACCT-1 TestCase """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DB2 HADR ACCT-1"
        self.client_node1_conn = None
        self.client_node2_conn = None
        self.client_node1_db2_conn = None
        self.client_node2_db2_conn = None
        self.destination_client_conn = None
        self.destination_client_db2_conn = None
        self.destination_port = None
        self.agent = None
        self.instance = None
        self.backupset = None
        self.subclient = None
        self.primary_node = None
        self.standby_node = None
        self.db2_logs_dir = None
        self.node1_client = None
        self.node2_client = None
        self.destination_client = None
        self.cluster_client = None
        self.instances = None
        self.tablespace_name = None
        self.table = None
        self.tablespace_count = None
        self.table_content_full = None
        self.tablespace_list = None
        self.datafile = None
        self.db2_helper = None
        self.db2_path = None
        self.dbpath = None

        self.tcinputs = {
            "DomainHost": None,
            "DomainName": None,
            "Instance_Name": None,
            "Backupset_Name": None,
            "Node1HostName": None,
            "Node2HostName": None,
            "InstallClientUsername": None,
            "InstallClientPassword": None,
            "db2_username": None,
            "db2_user_password": None,
            "storage_policy": None,
            "db2_home_directory": None,
            "DestinationClientHostName": None,
            "DestinationClientUserName": None,
            "DestinationClientPassword": None,
            "DestinationDB2InstalledPath": None,
            "DestinationDB2ClientGroup": None
        }

    def setup(self):
        """ Initial configuration for the test case.

            Raises:
                Exception:
                    If test case initialization is failed.
        """

        try:
            self.client_node1_conn = Machine(machine_name=self.tcinputs['Node1HostName'],
                                             commcell_object=self.commcell,
                                             username=self.tcinputs['InstallClientUsername'],
                                             password=self.tcinputs['InstallClientPassword'])

            self.client_node2_conn = Machine(machine_name=self.tcinputs['Node2HostName'],
                                             commcell_object=self.commcell,
                                             username=self.tcinputs['InstallClientUsername'],
                                             password=self.tcinputs['InstallClientPassword'])

            self.client_node1_db2_conn = Machine(machine_name=self.tcinputs['Node1HostName'],
                                                 commcell_object=self.commcell,
                                                 username=self.tcinputs['db2_username'],
                                                 password=self.tcinputs['db2_user_password'])

            self.client_node2_db2_conn = Machine(machine_name=self.tcinputs['Node2HostName'],
                                                 commcell_object=self.commcell,
                                                 username=self.tcinputs['db2_username'],
                                                 password=self.tcinputs['db2_user_password'])

            self.destination_client_conn = Machine(machine_name=self.tcinputs['DestinationClientHostName'],
                                                   commcell_object=self.commcell,
                                                   username=self.tcinputs['DestinationClientUserName'],
                                                   password=self.tcinputs['DestinationClientPassword'])

            self.tablespace_name = "TS60897"
            self.table = "TBL60897"
            self.db2_path = self.tcinputs["DestinationDB2InstalledPath"]

            self.prerequisite_setup_test_case()

        except Exception as exception:
            raise Exception(exception) from Exception

    def run(self):
        """
        Main method to run test case
        Raises:
            Exception:
                If cluster client or any associated client is not ready.
        """
        # self.install_db2_ida(client_hostnames=[self.tcinputs['Node1HostName'],
        #                                        self.tcinputs['Node2HostName'],
        #                                        self.tcinputs['DestinationClientHostName']])

        self.commcell.refresh()

        self.node1_client = self.commcell.clients.get(self.tcinputs['Node1HostName'])
        self.node2_client = self.commcell.clients.get(self.tcinputs['Node2HostName'])
        self.destination_client = self.commcell.clients.get(self.tcinputs['DestinationClientHostName'])
        self.log.info('Install Directory for %s %s' % (self.tcinputs['Node1HostName'],
                                                       self.node1_client.install_directory))
        self.log.info('Install Directory for %s %s' % (self.tcinputs['Node2HostName'],
                                                       self.node2_client.install_directory))

        if not self.node1_client.is_ready:
            raise Exception(f"{self.node1_client.display_name} Client not ready!!")
        if not self.node2_client.is_ready:
            raise Exception(f"{self.node2_client.display_name} Client not ready!!")

        self.create_cluster_client()

        self.log.info("Sleeping for 500 seconds to let cluster client get ready.")
        time.sleep(500)

        self.restart_client_services()

        self.client_node1_conn.start_all_cv_services()
        self.client_node2_conn.start_all_cv_services()
        self.log.info("Sleeping for 2 minutes")
        time.sleep(120)

        self.add_db2_instance()
        self.commcell.refresh()
        self.verify_db2_instance_properties()
        self.backupset = self.add_db2_backupset(instance=self.instance)
        self.verify_db2_backupset_properties()

        self.add_subclient()

        self.commcell.refresh()
        self.cluster_client.refresh()
        self.instance.refresh()
        self.backupset.refresh()

        self.primary_node, self.standby_node = self.get_hadr_nodes_and_connect_status()
        self.update_db2_database_configuration()

        self.db2_gui_backups()

        self.db2_gui_restore()

        backup_timestamp = self.db2_command_line_backups()
        self.add_subclient(only_log=True)
        self.db2_gui_backups(log_backup=True)

        self.db2_helper.reconnect()

        self.db2_command_line_restore(timestamp=backup_timestamp)

        self.log_archiving_test()
        self.verify_log_archiving_node_failover()

        self.load_copy_operation(create_data=True)

        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)

        self.standby_takeover()

        self.restart_client_services()

        self.cluster_client = self.commcell.clients.get(self.tcinputs['DomainHost'])

        number_attempts = 1
        while number_attempts <= 10:
            if self.cluster_client.is_ready:
                self.log.info("Cluster Client is Ready!")
                break
            self.log.info(f"Client not ready after attempt number {number_attempts}!")
            number_attempts += 1
            time.sleep(20)
        else:
            raise Exception(f"{self.cluster_client.display_name} Cluster Client not ready!!")

        self.db2_helper.reconnect()

        self.db2_gui_backups()

        self.db2_gui_restore()

        backup_timestamp = self.db2_command_line_backups()
        self.db2_gui_backups(log_backup=True)

        self.db2_command_line_restore(timestamp=backup_timestamp)

        self.log_archiving_test()
        self.verify_log_archiving_node_failover()

        self.load_copy_operation()

    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.log.info("### Prerequisite setup for test case ###")
        self.retire_and_delete_client(self.tcinputs['DomainHost'], cluster_client=True)
        # self.retire_and_delete_client(self.tcinputs['Node1HostName'])
        # self.retire_and_delete_client(self.tcinputs['Node2HostName'])
        # self.retire_and_delete_client(self.tcinputs['DestinationClientHostName'])
        self.verify_db2_version()
        self.get_destination_db2_logs_dir()
        self.recreate_destination_db2_logs_dir()
        archive_db2diag_cmd = f"{self.tcinputs['db2_home_directory']}/sqllib/bin/db2diag -A " \
                              f"{self.tcinputs['db2_home_directory']}/sqllib/db2dump/DIAG0000/db2diag.log"
        output = self.client_node1_conn.execute_command(command=archive_db2diag_cmd).output
        self.log.info("Archiving db2diag on Node 1: %s" % output)
        output = self.client_node2_db2_conn.execute_command(command=archive_db2diag_cmd).output
        self.log.info("Archiving db2diag on Node 2: %s" % output)

    def verify_db2_version(self):
        """
        Verify source and destination db2 versions
        """
        source_version = self.client_node1_db2_conn.execute_command(command="db2level").output.strip()
        source_version = source_version.split('\n')[3].split("\"")[1].split()[1][1:]
        self.log.info("Source Version: %s" % source_version)
        destination_version_cmd = f"db2ls | grep -i '{self.db2_path}' | awk 'NR>=1{{print $2}}'"
        destination_version = self.destination_client_conn.execute_command(command=destination_version_cmd).output.strip()
        self.log.info("Destination Version: %s" % destination_version)
        source_version = source_version.split('.')
        destination_version = destination_version.split('.')
        for version_index in range(0, len(source_version)):
            if int(source_version[version_index]) < int(destination_version[version_index]):
                raise Exception("Destination DB2 Version Higher than Source. Cannot proceed with the test case")

    def restart_client_services(self):
        """
        Restart client services
        """
        self.client_node1_conn.kill_process(
            process_id=self.client_node1_conn.get_process_id(
                process_name=f'{self.node1_client.install_directory}/Base/cvd')[0])
        self.client_node1_conn.kill_process(
            process_id=self.client_node1_conn.get_process_id(
                process_name=f'{self.node1_client.install_directory}/Base/cvfwd')[0])
        self.client_node2_conn.kill_process(
            process_id=self.client_node2_conn.get_process_id(
                process_name=f'{self.node2_client.install_directory}/Base/cvd')[0])
        self.client_node2_conn.kill_process(
            process_id=self.client_node2_conn.get_process_id(
                process_name=f'{self.node2_client.install_directory}/Base/cvfwd')[0])

    def prepare_clients_for_restore(self):
        """
        Prepares client for restore
        Raises:
            Exception:
                If adding instance fails on CommServ.
        """
        self.log.info("### Preparing client for restore ###")
        self.add_entries_to_host_file()
        password_cmd = f"echo \"{self.tcinputs['db2_username']}:{self.tcinputs['db2_user_password']}\" | chpasswd"
        if self.destination_client_conn.check_user_exist(username=self.tcinputs['db2_username']):
            self.log.info("### Dropping DB2 Instance ###")
            self.destination_client_conn.execute_command(command=password_cmd)
            self.destination_client_db2_conn = Machine(machine_name=self.tcinputs['DestinationClientHostName'],
                                                       commcell_object=self.commcell,
                                                       username=self.tcinputs['db2_username'],
                                                       password=self.tcinputs['db2_user_password'])

            output = self.destination_client_db2_conn.execute_command(command=f"db2 connect reset;db2 deactivate db {self.tcinputs['Backupset_Name']}")
            self.log.info(output.output)
            output = self.destination_client_db2_conn.execute_command(command="db2stop")
            self.log.info(output.output)
            drop_instance_cmd = f"{self.db2_path}/instance/db2idrop {self.tcinputs['db2_username']}"
            self.log.info(drop_instance_cmd)
            output = self.destination_client_conn.execute_command(command=drop_instance_cmd)
            self.log.info(output.output)
            self.destination_client_db2_conn.disconnect()
            self.log.info("### Deleting and adding user ###")
            self.destination_client_conn.delete_users(users=[self.tcinputs['db2_username']])

        time.sleep(5)
        # default_encrypted_password = get_config().DB2.password
        # user_id = self.client_node1_conn.execute_command(command=f"id -u {self.tcinputs['db2_username']}").output
        useradd_cmd = f"useradd -g {self.tcinputs['DestinationDB2ClientGroup']} {self.tcinputs['db2_username']}"

        self.log.info(f"Creating user command: {useradd_cmd}")
        output = self.destination_client_conn.execute_command(command=useradd_cmd)
        self.log.info(output.output)
        self.destination_client_conn.execute_command(command=password_cmd)

        remove_instance_list = f"{self.db2_path}/instance/db2iset -d {self.tcinputs['db2_username']}"
        self.log.info(remove_instance_list)
        output = self.destination_client_conn.execute_command(command=remove_instance_list)
        self.log.info(output.output)
        self.log.info("### Creating DB2 Instance ###")
        self.destination_port = self.find_unused_port_instance()
        create_instance_cmd = f"{self.db2_path}/instance/db2icrt -u db2fenc1 -p {self.destination_port} " \
                              f"{self.tcinputs['db2_username']}" \

        self.log.info(f"Creating Instance command: {create_instance_cmd}")
        output = self.destination_client_conn.execute_command(command=create_instance_cmd)
        self.log.info(output.output)
        self.destination_client_db2_conn = Machine(machine_name=self.tcinputs['DestinationClientHostName'],
                                                   commcell_object=self.commcell,
                                                   username=self.tcinputs['db2_username'],
                                                   password=self.tcinputs['db2_user_password'])
        output = self.destination_client_db2_conn.execute_command(command="db2start")
        self.log.info(output.output)
        self.add_database_on_destination()
        self.log.info("Adding instance for Destination Client")
        time.sleep(10)
        self.destination_client.refresh()
        agent = self.destination_client.agents.get('DB2')
        instances = agent.instances
        if instances.has_instance(instance_name=self.tcinputs['Instance_Name']):
            self.log.info("Deleting instance from CS as it already exist!")
            instances.delete(self.tcinputs['Instance_Name'])
            instances.refresh()
            time.sleep(10)
        home_path = self.destination_client_db2_conn.execute_command(command='echo $HOME').output.strip()
        db2_instance_options = {
            'instance_name': self.tcinputs['Instance_Name'],
            'data_storage_policy': self.tcinputs['storage_policy'],
            'log_storage_policy': self.tcinputs['storage_policy'],
            'command_storage_policy': self.tcinputs['storage_policy'],
            'home_directory': home_path,
            'password': self.tcinputs['db2_user_password'],
            'user_name': self.tcinputs['db2_username']
        }
        try:
            instances.add_db2_instance(db2_options=db2_instance_options)
        except Exception as exp:
            self.log.info(exp)

    def standby_takeover(self):
        """
        Performs Takeover operation on standby node
        Raises:
            Exception:
                If takeover command fails.
        """
        takeover_cmd = self.standby_node.execute_command(command=f"db2 TAKEOVER HADR ON DB "
                                                                 f"{self.tcinputs['Backupset_Name']}")
        self.primary_node, self.standby_node = self.get_hadr_nodes_and_connect_status()
        self.log.info(takeover_cmd.output)
        if "completed successfully" not in takeover_cmd.output.lower():
            raise Exception("Takeover Command Failed!!")
        self.log.info("Sleeping for 600 seconds after Takeover operation to recreate tunnel.")
        time.sleep(600)
        self.verify_primary_and_secondary_node()

    def add_database_on_destination(self):
        """
        Adding database on client
        """
        self.log.info("Adding database on instance")
        self.destination_client_conn.create_directory(directory_name=f"/{self.tcinputs['Backupset_Name'].lower()}",
                                                      force_create=True)
        self.destination_client_conn.create_directory(directory_name=f"/{self.tcinputs['Backupset_Name'].lower()}"
                                                                     f"/dbpath",
                                                      force_create=True)
        self.destination_client_conn.create_directory(directory_name=f"/{self.tcinputs['Backupset_Name'].lower()}/db",
                                                      force_create=True)
        self.destination_client_conn.execute_command(command=f"chown -R {self.tcinputs['db2_username']} "
                                                             f"/{self.tcinputs['Backupset_Name'].lower()}")
        self.destination_client_conn.execute_command(command=f"chgrp -R {self.tcinputs['DestinationDB2ClientGroup']} "
                                                             f"/{self.tcinputs['Backupset_Name'].lower()}")
        self.destination_client_conn.execute_command(command=f"chmod -R 777 /{self.tcinputs['Backupset_Name'].lower()}")
        create_db = f"db2 create db {self.tcinputs['Backupset_Name']} " \
                    f"on '/{self.tcinputs['Backupset_Name'].lower()}/db/' " \
                    f"dbpath on '/{self.tcinputs['Backupset_Name'].lower()}/dbpath/'"
        self.log.info(f"Create database: {create_db}")
        output = self.destination_client_db2_conn.execute_command(command=create_db)
        self.log.info(output.output)

    def find_unused_port_instance(self):
        """
        Find unused port for instance creation
        """
        self.log.info("Finding unused port between 50000 to 50100")
        final_port = "50000"
        for port in range(50000, 50100):
            port_usage_cmd = f"netstat -anp | grep ':{port}'"
            output = self.destination_client_conn.execute_command(command=port_usage_cmd)
            self.log.info(f"For port {port}: {output.output}")
            if len(output.output.strip()) == 0:
                final_port = str(port)
                self.log.info(f"Unused Port is: {final_port}")
                break
        return final_port

    def get_hadr_nodes_and_connect_status(self):
        """
        Gets Primary node and Secondary Node and Check if connected.
        Raises:
            Exception:
                If Primary and Standby nodes are not connected.
        """

        primary_node = self.client_node2_db2_conn
        standby_node = self.client_node1_db2_conn

        hadr_role_command = f"db2pd -hadr -db {self.tcinputs['Backupset_Name'].upper()} | grep -iE ' HADR_ROLE '"
        hadr_status_output = self.client_node1_db2_conn.execute_command(command=hadr_role_command)
        if "primary" in hadr_status_output.output.lower():
            primary_node = self.client_node1_db2_conn
            standby_node = self.client_node2_db2_conn

        hadr_connect_command = f"db2pd -hadr -db {self.tcinputs['Backupset_Name'].upper()} " \
                               f"| grep -iE ' HADR_CONNECT_STATUS '"
        hadr_status_output = self.client_node1_db2_conn.execute_command(command=hadr_connect_command)

        self.log.info("Primary hostname: %s" % primary_node.ip_address)
        self.log.info("Secondary hostname: %s" % standby_node.ip_address)

        if "disconnected" in hadr_status_output.output.lower():
            raise Exception("Primary and Secondary are Not Connected")

        return primary_node, standby_node

    def add_entries_to_host_file(self):
        """
        Add entries to host file on all nodes
        """
        self.log.info("### Adding entries into host files on all nodes ###")
        node1_host_file = self.client_node1_conn.read_file(file_path='/etc/hosts')
        node2_host_file = self.client_node2_conn.read_file(file_path='/etc/hosts')
        destination_host_file = self.destination_client_conn.read_file(file_path='/etc/hosts')
        node1_machine_name = self.client_node1_conn.get_hardware_info()['MachineName']
        node2_machine_name = self.client_node2_conn.get_hardware_info()['MachineName']
        destination_machine_name = self.destination_client_conn.get_hardware_info()['MachineName']

        if self.tcinputs['DestinationClientHostName'] not in node1_host_file:
            self.client_node1_conn.add_host_file_entry(ip_addr=self.destination_client_conn.ip_address,
                                                       hostname=destination_machine_name)

        if self.tcinputs['DestinationClientHostName'] not in node2_host_file:
            self.client_node2_conn.add_host_file_entry(ip_addr=self.destination_client_conn.ip_address,
                                                       hostname=destination_machine_name)

        if self.tcinputs['DomainHost'] not in destination_host_file:
            self.destination_client_conn.add_host_file_entry(ip_addr=self.tcinputs['DomainHost'],
                                                             hostname=self.tcinputs['DomainName'])
        if self.tcinputs['Node1HostName'] not in destination_host_file:
            self.destination_client_conn.add_host_file_entry(ip_addr=self.client_node1_conn.ip_address,
                                                             hostname=node1_machine_name)
        if self.tcinputs['Node2HostName'] not in destination_host_file:
            self.destination_client_conn.add_host_file_entry(ip_addr=self.client_node2_conn.ip_address,
                                                             hostname=node2_machine_name)

    def create_cluster_client(self):
        """
        Creates Cluster Client
        """
        self.log.info("### Creating Cluster Client ###")
        self.cluster_client = self.commcell.clients.create_pseudo_client(client_name=self.tcinputs['DomainName'],
                                                                         client_hostname=self.tcinputs['DomainHost'],
                                                                         client_type="unix cluster")

        properties = self.cluster_client.properties
        properties['clusterClientProperties']['clusterGroupAssociation'] = [
            {
                "clientId": int(self.node1_client.client_id),
                "clientName": self.node1_client.display_name,
            },
            {
                "clientId": int(self.node2_client.client_id),
                "clientName": self.node2_client.display_name,
            }
        ]
        properties['clusterClientProperties']['configuredAgents'] = [
            {
                "osType": "Unix",
                "NoApplicationRequired": True,
                "ComponentName": "DB2 Agent",
                "ComponentId": 1207
            }
        ]
        properties['client']['jobResulsDir']['path'] = self.node1_client.job_results_directory

        self.cluster_client.update_properties(properties_dict=properties)
        time.sleep(5)

        self.commcell.refresh()
        self.cluster_client = self.commcell.clients.get(self.tcinputs['DomainHost'])

        self.log.info("Cluster Client Creation Successful!!")

    def add_db2_instance(self):
        """
        Adds DB2 Instance
        Raises:
            Exception:
                If adding instance fails.
        """
        self.log.info("### Adding DB2 Instance ###")
        try:
            self.agent = self.cluster_client.agents.get('DB2')
            self.instances = self.agent.instances
            if not self.agent.instances.has_instance(instance_name=self.tcinputs['Instance_Name']):
                db2_instance_options = {
                    'instance_name': self.tcinputs['Instance_Name'],
                    'data_storage_policy': self.tcinputs['storage_policy'],
                    'log_storage_policy': self.tcinputs['storage_policy'],
                    'command_storage_policy': self.tcinputs['storage_policy'],
                    'home_directory': self.tcinputs['db2_home_directory'],
                    'password': self.tcinputs['db2_user_password'],
                    'user_name': self.tcinputs['db2_username']
                }
                self.instances.add_db2_instance(db2_options=db2_instance_options)
                self.instances.refresh()
            self.instance = self.instances.get(self.tcinputs['Instance_Name'])
        except Exception as exp:
            self.log.info(exp)

    def add_db2_backupset(self, instance):
        """
        Adds DB2 Backupset
        """
        backupset = None
        try:
            self.log.info("### Adding DB2 Backupset ###")
            if not instance.backupsets.has_backupset(backupset_name=self.tcinputs['Backupset_Name']):
                instance.backupsets.add(backupset_name=self.tcinputs['Backupset_Name'],
                                        storage_policy=self.tcinputs['storage_policy'])
            instance.refresh()
            backupset = instance.backupsets.get(backupset_name=self.tcinputs['Backupset_Name'])
        except Exception as exp:
            self.log.info(exp)
        return backupset

    def add_subclient(self, only_log=False):
        """
        Creates a subclient
        Args:
            only_log (bool): Create only log subclient or not
        """
        subclient_name = "loghadrsub" if only_log else "hadrsub"
        self.log.info("### Creating Subclient ###")
        self.backupset.refresh()
        if not self.backupset.subclients.has_subclient(subclient_name=subclient_name):
            self.backupset.subclients.add(subclient_name=subclient_name,
                                          storage_policy=self.tcinputs['storage_policy'],
                                          description="HADR ACCT-1 Subclient")

        if only_log:
            log_subclient = Subclients(class_object=self.backupset).get(subclient_name=subclient_name)
            log_subclient.disable_backupdata()
            self.log.info("Log Backup subclient created.")
        else:
            self.subclient = Subclients(class_object=self.backupset).get(subclient_name=subclient_name)

    def verify_db2_instance_properties(self):
        """
        Verify instance properties
        """
        self.log.info("### Verifying DB2 Instance Properties ###")
        storage_policy = self.instance.properties['db2Instance']['DB2StorageDevice']
        self.compare_properties(property_name="Client Name",
                                expected=self.cluster_client.display_name,
                                received=self.instance.properties['instance']['clientName'])
        self.compare_properties(property_name="Data Storage Policy",
                                expected=self.tcinputs['storage_policy'],
                                received=storage_policy['dataBackupStoragePolicy']['storagePolicyName'])
        self.compare_properties(property_name="Log Storage Policy",
                                expected=self.tcinputs['storage_policy'],
                                received=storage_policy['logBackupStoragePolicy']['storagePolicyName'])
        self.compare_properties(property_name="Command Line Storage Policy",
                                expected=self.tcinputs['storage_policy'],
                                received=storage_policy['commandLineStoragePolicy']['storagePolicyName'])

    def verify_db2_backupset_properties(self):
        """
        Verify backupset properties
        """
        self.log.info("### Verifying DB2 Backupset Properties ###")
        properties = self.backupset.properties
        self.compare_properties(property_name="Backupset Name",
                                expected=self.tcinputs['Backupset_Name'].upper(),
                                received=properties['backupSetEntity']['backupsetName'])
        self.compare_properties(property_name="Client Name",
                                expected=self.cluster_client.display_name,
                                received=properties['backupSetEntity']['clientName'])
        self.compare_properties(property_name="Instance Name",
                                expected=self.tcinputs['Instance_Name'],
                                received=properties['backupSetEntity']['instanceName'])
        self.compare_properties(property_name="Storage Policy",
                                expected=self.tcinputs['storage_policy'],
                                received=properties['db2BackupSet']['dB2DefaultIndexSP']['storagePolicyName'])

    @staticmethod
    def compare_properties(property_name, expected, received):
        """
        Compares two values for a given property
        Args:
            property_name (str): Name of property to verify
            expected (str): Expected Value
            received (str): Received Value
        Raises:
            Exception:
                If received property value is not similar to expected value.
        """
        if expected != received:
            raise Exception(f"Expected {property_name}: {expected} \n "
                            f"Received {property_name}: {received}")

    def update_db2_database_configuration(self):
        """
        Updating db2 database logging properties on client
        """
        self.log.info("### Updating db2 database configuration on nodes ###")
        self.client_node1_conn.create_registry(key="Db2Agent",
                                               value="nPerformanceMode",
                                               data="1")
        self.client_node2_conn.create_registry(key="Db2Agent",
                                               value="nPerformanceMode",
                                               data="1")
        self.update_config1(db2_node=self.primary_node)
        self.update_config1(db2_node=self.standby_node)

        cmd = f"db2 deactivate db {self.tcinputs['Backupset_Name']}"
        self.log.info(f"Deactivating Standby Database: {cmd}")
        output = self.standby_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"db2 stop hadr on db {self.tcinputs['Backupset_Name']}"
        self.log.info(f"Stopping HADR on Standby Database: {cmd}")
        output = self.standby_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        self.log.info(f"Stopping HADR on Primary Database: {cmd}")
        output = self.primary_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"db2 deactivate db {self.tcinputs['Backupset_Name']}"
        self.log.info(f"Deactivating Database on Standby Node: {cmd}")
        output = self.standby_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        self.log.info(f"Deactivating Database on Primary Node: {cmd}")
        output = self.primary_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"db2 start hadr on db {self.tcinputs['Backupset_Name']} as standby"
        self.log.info(f"Starting HADR on Standby Database: {cmd}")
        output = self.standby_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"db2 start hadr on db {self.tcinputs['Backupset_Name']} as primary"
        self.log.info(f"Starting HADR on Primary Database: {cmd}")
        output = self.primary_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        self.verify_primary_and_secondary_node()

    def update_config1(self, db2_node):
        """
        Updating Configuration Commands
        Args:
            db2_node (Machine): Machine to execute commands on
        """
        self.log.info(f"### Updating db2 database configs properties on node"
                      f" {db2_node.get_hardware_info()['MachineName']} ###")

        commvault_instance = db2_node.instance
        commvault_base_path = db2_node.get_registry_value("Base", "dBASEHOME")

        base_cmd = f"db2 update db cfg for {self.tcinputs['Backupset_Name']} using "
        vendor_path = "\"'VENDOR:%s/libDb2Sbt.so'\"" % commvault_base_path
        opt_cfg = "\"'CvClientName=%s,CvInstanceName=%s'\"" % (self.tcinputs['DomainName'], commvault_instance)

        cmd = f"{base_cmd}LOGARCHMETH1 {vendor_path}"
        self.log.info(f"Set LOGARCHMETH1 options {cmd}")
        output = db2_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"{base_cmd}LOGARCHOPT1 {opt_cfg}"
        self.log.info(f"Set LOGARCHOPT1 options {cmd}")
        output = db2_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"{base_cmd}VENDOROPT {opt_cfg}"
        self.log.info(f"Set VENDOROPT options {cmd}")
        output = db2_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"{base_cmd}TRACKMOD ON"
        self.log.info(f"Set TRACKMOD options {cmd}")
        output = db2_node.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

    def prepare_db2_data(self):
        """
        Preparing data on DB2 database
        """
        self.log.info("### Preparing data on DB2 database ###")
        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.cluster_client,
                              instance=self.instance,
                              backupset=self.backupset)

        self.datafile = self.db2_helper.get_datafile_location()
        self.db2_helper.create_table2(datafile=self.datafile,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"{self.table}_FULL",
                                      flag_create_tablespace=True)
        table_data = self.db2_helper.prepare_data(table_name=f"{self.table}_FULL")
        self.table_content_full, self.tablespace_list, self.tablespace_count = table_data
        self.log.info(f"Prepare Data Values: {self.table_content_full} {self.tablespace_list} {self.tablespace_count}")

        if f"{self.datafile}{self.tablespace_name}_Full.dbf.ORG":
            self.primary_node.delete_file(f"{self.datafile}{self.tablespace_name}_Full.dbf.ORG")

    def db2_gui_backups(self, log_backup=False):
        """
        Perform All DB2 Backups
        Args:
            log_backup (bool): Run only log backup
        """
        self.log.info("### Running GUI Backups ###")
        self.prepare_db2_data()
        self.backupset.refresh()
        if log_backup:
            log_subclient = Subclients(class_object=self.backupset).get(subclient_name="loghadrsub")
            log_backup_job = log_subclient.backup(backup_level="FULL")
            self.wait_for_job(job_object=log_backup_job)
        else:
            full_backup_job = self.db2_helper.run_backup(subclient=self.subclient,
                                                         backup_type="FULL")
            self.wait_for_job(job_object=full_backup_job)
            self.validate_backup_job(backup_job_object=full_backup_job)

            self.db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"{self.table}_INCR",
                                          flag_create_tablespace=False)

            incr_backup_job = self.db2_helper.run_backup(subclient=self.subclient,
                                                         backup_type="INCREMENTAL")
            self.wait_for_job(job_object=incr_backup_job)
            self.validate_backup_job(backup_job_object=incr_backup_job)

            self.db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"{self.table}_DELTA",
                                          flag_create_tablespace=False)

            diff_backup_job = self.db2_helper.run_backup(subclient=self.subclient,
                                                         backup_type="DIFFERENTIAL")
            self.wait_for_job(job_object=diff_backup_job)
            self.validate_backup_job(backup_job_object=diff_backup_job)

    def db2_gui_restore(self):
        """
        Runs DB2 GUI Restore
        """
        self.log.info("### Out of place restore ###")
        self.backupset.refresh()
        self.prepare_clients_for_restore()

        redirect_tablespace = {
            'TS60897': f'/{self.tcinputs["Backupset_Name"].lower()}/dbpath/{self.tcinputs["Instance_Name"]}'
                       f'/NODE0000/SQL00001/TS60897_Full.dbf'}
        redirect_storage_group = {'IBMSTOGROUP': f'/{self.tcinputs["Backupset_Name"].lower()}/db'}
        restore_job = self.backupset.restore_out_of_place(dest_client_name=self.destination_client.client_name,
                                                          dest_instance_name=self.instance.instance_name,
                                                          dest_backupset_name=self.backupset.backupset_name,
                                                          target_path=f"/{self.tcinputs['Backupset_Name'].lower()}"
                                                                      f"/dbpath",
                                                          redirect_enabled=True,
                                                          redirect_tablespace_path=redirect_tablespace,
                                                          redirect_storage_group_path=redirect_storage_group,
                                                          rollforward=True,
                                                          restore_incremental=False)
        self.wait_for_job(restore_job)

        self.validate_restore_job(table_name=self.table)

    def db2_command_line_backups(self):
        """
        Running command line backups
        """
        self.log.info("### Running CLI Backups ###")
        self.db2_helper.create_table2(datafile=self.datafile,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"{self.table}_CLI_FULL",
                                      flag_create_tablespace=False)
        backup_timestamp = self.db2_helper.third_party_command_backup(db_name=self.backupset.backupset_name.upper(),
                                                                      backup_type="FULL")
        self.validate_backup_job(cli_job=True, timestamp=backup_timestamp, job_type="full")

        self.db2_helper.create_table2(datafile=self.datafile,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"{self.table}_CLI_INCR",
                                      flag_create_tablespace=False)
        backup_timestamp = self.db2_helper.third_party_command_backup(db_name=self.backupset.backupset_name.upper(),
                                                                      backup_type="INCREMENTAL")
        self.validate_backup_job(cli_job=True, timestamp=backup_timestamp, job_type="incremental")

        self.db2_helper.create_table2(datafile=self.datafile,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"{self.table}_CLI_DELTA",
                                      flag_create_tablespace=False)
        backup_timestamp = self.db2_helper.third_party_command_backup(db_name=self.backupset.backupset_name.upper(),
                                                                      backup_type="DELTA")
        self.validate_backup_job(cli_job=True, timestamp=backup_timestamp, job_type="delta")
        return backup_timestamp

    def wait_for_job(self, job_object):
        """
        Waits for Job method
        Args:
            job_object (Job): Job object to wait for.
        Raises:
            Exception:
                If Job fails to complete.
        """
        self.log.info(f"Waiting for {job_object.job_type} Job to Complete (Job Id: {job_object.job_id})")
        if not job_object.wait_for_completion():
            raise Exception(f"{job_object.job_type} Job Failed with reason: {job_object.delay_reason}")

    def validate_backup_job(self, backup_job_object=None, cli_job=False, timestamp=None, job_type=None):
        """
        Validates Backup Jobs
        Args:
            backup_job_object (Job): Backup Job Object
            cli_job (bool): If jb given is CLI job
            timestamp (str): If cli job then timestamp returned
            job_type (str): If given job is full, incremental or delta
        """
        exp_operation_type = {'full': 'N',
                              'incremental': 'O',
                              'delta': 'E'}
        if cli_job:
            self.db2_helper.backup_validation(operation_type=exp_operation_type[job_type.lower()],
                                              tablespaces_count=self.tablespace_list,
                                              backup_time_stamp=timestamp)
        else:
            backup_time_stamp, _ = self.db2_helper.get_backup_time_stamp_and_streams(jobid=backup_job_object.job_id)

            self.log.info("### Running Backup Validation ###")
            time.sleep(30)
            self.db2_helper.backup_validation(operation_type=exp_operation_type[backup_job_object.backup_level.lower()],
                                              tablespaces_count=self.tablespace_list,
                                              backup_time_stamp=backup_time_stamp)
            self.log.info("Successfully ran %s backup." % backup_job_object.backup_level)

    def db2_command_line_restore(self, timestamp):
        """
        Performing command line restore
        Args:
            timestamp (str): Timestamp to perform restore to.
        Raises:
            Exception:
                If command line restore or rollforward fails.
        """
        self.log.info("### Command Line Out of place restore ###")
        self.prepare_clients_for_restore()
        redirect_tablespace = {
            'TS60897': f'/{self.tcinputs["Backupset_Name"].lower()}/dbpath/{self.tcinputs["Instance_Name"]}'
                       f'/NODE0000/SQL00001/TS60897_Full.dbf'}
        restore_dir = f'/{self.tcinputs["Backupset_Name"].lower()}/dbpath/'
        self.update_destination_db_config_restore(log=False)
        load_path = self.destination_client_conn.get_registry_value("Base", "dBASEHOME")

        self.destination_client_db2_conn.execute_command(command="db2 force application all")
        self.destination_client_db2_conn.execute_command(command=f"db2 deactivate db {self.backupset.backupset_name}")
        self.destination_client_db2_conn.execute_command(command="db2 terminate")

        restore_cmd = "db2 restore db %s incremental automatic load \"'%s'\" open 2 sessions " \
                      "taken at %s on %s into %s REDIRECT without prompting" % (self.backupset.backupset_name.upper(),
                                                                                load_path+'/libDb2Sbt.so',
                                                                                timestamp,
                                                                                restore_dir,
                                                                                self.backupset.backupset_name.upper())
        self.log.info("Restore Command: %s" % restore_cmd)
        restore_output = self.destination_client_db2_conn.execute_command(command=restore_cmd)

        if str(restore_output.output).lower().find("restore database command completed successfully") >= 0:
            self.log.info(f"CLI restore is successful :{restore_output.output}")
        else:
            raise Exception("CLI restore is not successful : %s" % restore_output.output)

        get_table_space_id = "db2 connect to %s; db2 \"SELECT tbsp_id FROM TABLE(MON_GET_TABLESPACE('',-2)) where" \
                             " tbsp_name='%s'\"" % (self.backupset.backupset_name.upper(), "TS60897")
        tablespace_id = self.db2_helper.third_party_command(cmd=get_table_space_id).strip().split('\n')[-3].strip()

        redirect_tablespace_cmd = "db2 \"set tablespace containers for %s using (file '%s' 25600)\"" \
                                  % (tablespace_id, redirect_tablespace['TS60897'])
        self.log.info(redirect_tablespace_cmd)
        redirect_set = self.destination_client_db2_conn.execute_command(command=redirect_tablespace_cmd)
        self.log.info(redirect_set.output)

        restore_continue_cmd = f"db2 restore db {self.backupset.backupset_name.upper()} CONTINUE"
        self.log.info(restore_continue_cmd)
        restore_continue = self.destination_client_db2_conn.execute_command(command=restore_continue_cmd)

        if str(restore_continue.output).lower().find("restore database command completed successfully") >= 0:
            self.log.info(f"CLI restore is successful :{restore_continue.output}")
        else:
            raise Exception(f"CLI restore is not successful : {restore_continue.output}")

        self.update_destination_db_config_restore()

        rollforward_cmd = f"db2 rollforward db {self.backupset.backupset_name.upper()} to end of logs and stop"
        self.log.info(rollforward_cmd)
        rollforward_output = self.destination_client_db2_conn.execute_command(command=rollforward_cmd)

        if str(rollforward_output.output).find("'not', 'pending'") or \
                str(rollforward_output.output).find("not pending") >= 0:
            self.log.info(f"Rollforward was successful: {rollforward_output.output}")
        else:
            raise Exception(f"Rollforward is not successful: {rollforward_output.output}")

        time.sleep(20)
        self.validate_restore_job(table_name=f"{self.table}_CLI")

    def update_destination_db_config_restore(self, log=True):
        """
        Updating Destination Client Config for restore
        Args:
            log (bool): If log parameters need to be updated
        """
        machine_name = self.destination_client_conn.get_hardware_info()['MachineName']
        self.log.info(f"### Updating db2 database configs properties on node {machine_name} ###")

        commvault_instance = self.destination_client_conn.instance
        base_cmd = f"db2 update db cfg for {self.tcinputs['Backupset_Name'].upper()} using "
        opt_cfg = "\"'CvSrcDbName=%s,CvSrcClientName=%s,CvClientName=%s,CvInstanceName=%s'\"" \
                  % (self.tcinputs['Backupset_Name'], self.tcinputs['DomainName'], machine_name, commvault_instance)

        if log:
            cmd = f"{base_cmd}LOGARCHOPT1 {opt_cfg}"
            self.log.info(f"Set LOGARCHOPT1 options {cmd}")
            output = self.destination_client_db2_conn.execute_command(command=cmd)
            self.log.info(f"Output: {output.output}")

        cmd = f"{base_cmd}VENDOROPT {opt_cfg}"
        self.log.info(f"Set VENDOROPT options {cmd}")
        output = self.destination_client_db2_conn.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

    def validate_restore_job(self, table_name):
        """
        Validates Restore Jobs
        Args:
            table_name (str): Table name to verify on destination after restore
        """

        self.commcell.refresh()
        self.destination_client.refresh()
        agent = self.destination_client.agents.get('DB2')
        instance = agent.instances.get(self.instance.instance_name)
        backupset = self.add_db2_backupset(instance=instance)
        dest_db2helper = DB2(commcell=self.commcell,
                             client=self.destination_client,
                             instance=instance,
                             backupset=backupset,
                             port=self.destination_port)
        dest_db2helper.restore_validation(table_space="TS60897",
                                          table_name=table_name,
                                          tablecount_full=self.table_content_full)
        self.log.info("Verified Restore.")

    def log_archiving_test(self):
        """
        Perform Log Archive 50 times and verify if command line log backup is run
        """
        self.log.info("Performing Log Archive 50 times and verify if command line log backup is run")
        current_file = self.db2_helper.get_active_logfile()[1]
        self.db2_helper.db2_archive_log(self.backupset.backupset_name.upper(), 50)
        new_active_log_file = self.db2_helper.get_active_logfile()[1]
        if new_active_log_file == current_file:
            raise Exception("Archiving Log Failed")
        time.sleep(10)
        all_jobs = self.commcell.job_controller.finished_jobs(client_name=self.cluster_client.client_name,
                                                              lookup_time=0.02,
                                                              job_filter="Backup")
        for job_id in all_jobs:
            if 'application' in all_jobs[job_id]['operation'].lower() and \
                    'restore' in all_jobs[job_id]['operation'].lower():
                continue
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)

    def load_copy_operation(self, create_data=False):
        """
        Performing Load Copy Operation
        Args:
            create_data (bool): Flag to check if we need to create data on nodes
        Raises:
            Exception:
                 - If Load Copy Command Fails.
                 - If Data after load copy does not matches on Primary
                 - If Load copy completion is not written to db2diag meaning load copy failed.
        """
        self.log.info("Starting Load Copy Operation")
        self.primary_node.execute_command(command=f"db2 connect to {self.backupset.backupset_name}")
        self.primary_node.execute_command(command="db2 drop table test")
        self.primary_node.execute_command(command="db2 "
                                                  "\"create table test(roll int not null, name char(30), class char)\"")
        for i in range(1, 6):
            self.primary_node.execute_command("db2 \"insert into test values(%s,'Test VALUE%s', '%s')\""
                                              % (i, i, chr(i+ord('A'))))
        self.log.info("Created table with temp data. Starting Load Copy.")

        load_content = ('1000,"USER1","A"\n'
                        '2000,"USER2","B"\n'
                        '3000,"USER3","C"\n'
                        '4000,"USER4","D"\n'
                        '5000,"USER5","E"\n'
                        '6000,"USER6","F"\n'
                        '7000,"USER7","G"\n'
                        '8000,"USER8","H"'
                        )

        if create_data:
            self.primary_node.create_file(file_path=f"{self.tcinputs['db2_home_directory']}/data.del",
                                          content=load_content)
            self.standby_node.create_file(file_path=f"{self.tcinputs['db2_home_directory']}/data.del",
                                          content=load_content)

        commvault_base_path = self.primary_node.get_registry_value("Base", "dBASEHOME")
        vendor_path = "\"'%s/libDb2Sbt.so'\"" % commvault_base_path
        load_copy_cmd = "db2 \"load from data.del of del replace into test copy yes load '%s'\"" % vendor_path
        self.log.info(f"Load Copy Command: {load_copy_cmd}")
        output = self.primary_node.execute_command(command=load_copy_cmd)
        self.log.info(f"Load Copy Output: {output.output}")
        self.log.info("Sleeping for 100 seconds to let load copy complete")
        time.sleep(100)

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.cluster_client.client_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)
        time.sleep(10)

        db2_diag_path = f"{self.tcinputs['db2_home_directory']}/sqllib/db2dump/DIAG0000/db2diag.log"
        self.log.info(f"Getting load copy completion info from standby: {db2_diag_path}")
        output = self.standby_node.find_lines_in_file(file_path=db2_diag_path,
                                                      words=["load copy restore completed successfully"])
        self.log.info(output)
        if "load copy restore completed successfully" not in ' '.join(output).lower():
            raise Exception("Load Copy Operation Failed!!")
        table_content_check = self.db2_helper.third_party_command(cmd="db2 connect to %s;db2 \"select * from test\""
                                                                      % self.backupset.backupset_name)
        self.log.info(table_content_check)
        for row in load_content.split('\n'):
            for column in row.strip().split(','):
                if column.strip().replace('"', '') not in table_content_check:
                    raise Exception("Data Not Verified. Load copy is not successful!!")

        if str(len(load_content.split())) not in table_content_check.strip().split('\n')[-1]:
            raise Exception("Data Not Verified. Load copy is not successful!!")

    def verify_log_archiving_node_failover(self):
        """
        Verifies Log Archive and Restore behaviour on Node Failover
        Raises:
            Exception:
                - If deactivate command fails on standby.
                - If Logs are not restored to standby node on activation
        """
        self.log.info("Starting Node Failover Test")
        for i in range(0, 50):
            self.db2_helper.db2_archive_log(self.backupset.backupset_name.upper(), 1)
            if i == 15:
                deactivate_db_cmd = f"db2 connect reset; db2 deactivate db {self.backupset.backupset_name}"
                output = self.standby_node.execute_command(command=deactivate_db_cmd)
                self.log.info(f"Deactivate standby: {output.output}")
        time.sleep(10)
        self.log.info("Log Archive Done.")
        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.cluster_client.client_name)
        for job_id in all_jobs:
            if job_id:
                job = self.commcell.job_controller.get(job_id)
                self.wait_for_job(job)

        primary_log_cmd = f"db2pd -hadr -db {self.backupset.backupset_name.upper()} | grep 'PRIMARY_LOG_FILE' | " \
                          f"awk 'NR>=1{{print $3}}'"
        primary_log_file = self.primary_node.execute_command(command=primary_log_cmd)
        self.log.info(f"{primary_log_cmd}: {primary_log_file.output}")

        standby_log_cmd = f"db2pd -hadr -db {self.backupset.backupset_name.upper()} | grep 'STANDBY_LOG_FILE' | " \
                          f"awk 'NR>=1{{print $3}}'"
        standby_log_file = self.primary_node.execute_command(command=standby_log_cmd)
        self.log.info(f"{standby_log_cmd}: {standby_log_file.output}")

        if primary_log_file.output.strip() == standby_log_file.output.strip():
            output = self.standby_node.execute_command(command=f"db2 connect reset;"
                                                               f"db2 activate db {self.backupset.backupset_name}")
            self.log.info("Activating DB before Exit: %s" % output.output)
            raise Exception("Deactivate standby failed!!")

        output = self.standby_node.execute_command(command=f"db2 connect reset;"
                                                           f"db2 activate db {self.backupset.backupset_name}")
        self.log.info("Activate standby DB: %s" % output.output)
        self.log.info("Sleeping for 200 seconds to let log restore on standby complete.")
        time.sleep(200)
        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.cluster_client.client_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)
        self.log.info("Sleeping for 100 seconds to let log playing on standby complete.")
        time.sleep(100)

        primary_log_file = self.primary_node.execute_command(command=primary_log_cmd)
        self.log.info(f"{primary_log_cmd}: {primary_log_file.output}")

        standby_log_file = self.primary_node.execute_command(command=standby_log_cmd)
        self.log.info(f"{standby_log_cmd}: {standby_log_file.output}")

        if primary_log_file.output.strip() != standby_log_file.output.strip():
            raise Exception("Log Files not copied to standby and Restore did not run!!")

    def verify_primary_and_secondary_node(self):
        """
        Verify if Primary and Secondary are same
        Raises:
            Exception:
                If Primary or Standby nodes are not similar to detected ones.
        """
        self.log.info("### Verifying if primary and secondary nodes are same ###")
        primary, standby = self.get_hadr_nodes_and_connect_status()
        if primary.ip_address != self.primary_node.ip_address:
            raise Exception("Primary nodes are not same.")
        if standby.ip_address != self.standby_node.ip_address:
            raise Exception("Standby nodes are not same.")

    def get_destination_db2_logs_dir(self):
        """
        Get DB2 logs directory on destination
        """
        archive_location = self.destination_client_conn.get_registry_value(key='Db2Agent',
                                                                           value='sDB2_ARCHIVE_PATH')
        audit_location = self.destination_client_conn.get_registry_value(key='Db2Agent',
                                                                         value='sDB2_AUDIT_ERROR_PATH')
        retrieve_location = self.destination_client_conn.get_registry_value(key='Db2Agent',
                                                                            value='sDB2_RETRIEVE_PATH')
        self.db2_logs_dir = {
            "db2ArchivePath": f"/{archive_location}/{self.tcinputs['Instance_Name']}",
            "db2RetrievePath": f"/{retrieve_location}/retrievePath/{self.tcinputs['Instance_Name']}",
            "db2AuditErrorPath": f"/{audit_location}/"
        }

    def install_db2_ida(self, client_hostnames):
        """
        Install DB2 IDA on Client
        Args:
            client_hostnames (list): List of client to install DB2 IDA to.
        """
        self.log.info("### Installing DB2 ida on Clients ###")
        install_job = self.commcell.install_software(client_computers=client_hostnames,
                                                     unix_features=[UnixDownloadFeatures.DB2_AGENT.value,
                                                                    UnixDownloadFeatures.MEDIA_AGENT.value],
                                                     username=self.tcinputs['InstallClientUsername'],
                                                     password=b64encode(
                                                         self.tcinputs['InstallClientPassword'].encode()).decode(),
                                                     install_path="/opt/commvault/",
                                                     log_file_loc="/var/log/commvault/",
                                                     storage_policy_name=self.tcinputs['storage_policy'],
                                                     db2_logs_location=self.db2_logs_dir)

        self.log.info(f"Install job: {install_job.job_id}")
        self.wait_for_job(job_object=install_job)
        self.log.info("### Installation Complete ###")

    def recreate_destination_db2_logs_dir(self):
        """
        Recreate DB2 log directory from destination node.
        """
        self.log.info("### Remove existing DB2 log directory from all nodes and recreating ###")
        for _, dirs in self.db2_logs_dir.items():
            self.log.info(f"Recreating {dirs}")
            self.destination_client_conn.create_directory(directory_name=dirs, force_create=True)
            self.destination_client_conn.execute_command(command=f"chmod -R 777 {dirs}")
            self.destination_client_conn.execute_command(command=f"chgrp -R "
                                                                 f"{self.tcinputs['DestinationDB2ClientGroup']} {dirs}")

    def retire_and_delete_client(self, client_hostname, cluster_client=False):
        """
        Retires and Deletes Client
        """
        if self.commcell.clients.has_client(client_hostname):
            client_name = self.commcell.clients.get(client_hostname).name
            retire_job = self.commcell.clients.get(client_name).retire()
            if not cluster_client:
                self.log.info(f"Retire job: {retire_job.job_id} for {client_name}")
                self.wait_for_job(job_object=retire_job)
            time.sleep(10)
            self.commcell.refresh()
            if self.commcell.clients.has_client(client_hostname):
                self.commcell.clients.delete(client_name)
            self.log.info(f"{client_name} has been retired and deleted.")
            self.commcell.refresh()
        else:
            self.log.info(f"{client_hostname} has already been retired and deleted.")

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.log.info("### Teardown for the test case 60897 ###")
        try:
            self.standby_takeover()

            self.client_node1_conn.disconnect()
            self.client_node2_conn.disconnect()
            self.client_node1_db2_conn.disconnect()
            self.client_node2_db2_conn.disconnect()
            self.destination_client_db2_conn.disconnect()
            self.destination_client_conn.disconnect()
        except Exception as _:
            pass
        finally:
            self.status = constants.PASSED
            self.log.info("******TEST CASE PASSED****")
