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
"63144": {
            "SrcClientName": "client_name",
			"SrcDb2InstallPath": "db2_install_path",
            "SrcDb2UserGroup": "Db2 User Group",
            "DestinationClientName": "client_name",
            "DestinationDb2InstallPath": "db2_install_path",
            "DestDb2UserGroup": "Db2 User Group",
            "StoragePolicy": "Storage Policy Name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down method to cleanup the entities

    prerequisite_setup_test_case()              --  Uninstalling existing clients and removing log directories

    add_database_on_destination()               --  Adding database on client

    find_unused_port_instance()                 --  Find unused port for instance creation

    add_src_key_to_destination()                --  Add Encryption Key from SRC to Destination

    add_db2_instance()                          --  Adds DB2 Instance

    add_db2_backupset()                         --  Adds DB2 Backupset

    add_subclient()                             --  Creates a subclient

    verify_db2_backupset_properties()           --  Verify backupset properties

    compare_properties()                        --  Compares two values for a given property

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

    recreate_db2_logs_dir()                     --  Recreates DB2 log directory from all nodes.

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.database_helper import Db2
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from cvpysdk.subclient import Subclients


class TestCase(CVTestCase):
    """ DB2 Encryption ACCT TestCase """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DB2 Encryption ACCT"
        self.src_client_conn = None
        self.dest_client_conn = None
        self.src_client_db2_conn = None
        self.dest_client_db2_conn = None
        self.destination_port = None
        self.src_port = None
        self.src_agent = None
        self.src_instance = None
        self.dest_agent = None
        self.dest_instance = None
        self.db2_instance_name = None
        self.db2_database = None
        self.db2_username = None
        self.db2_user_password = None
        self.src_backupset = None
        self.dest_backupset = None
        self.src_subclient = None
        self.src_db2_logs_dir = None
        self.dest_db2_logs_dir = None
        self.src_client = None
        self.dest_client = None
        self.tablespace_name = None
        self.table_name = None
        self.table = None
        self.tablespace_count = None
        self.table_content_full = None
        self.tablespace_list = None
        self.datafile = None
        self.src_db2_helper = None
        self.dest_db2_helper = None
        self.dest_db2_path = None
        self.src_db2_path = None
        self.dbpath = None

        self.tcinputs = {
            "SrcClientName": None,
			"SrcDb2InstallPath": None,
            "SrcDb2UserGroup": None,
            "DestinationClientName": None,
            "DestinationDb2InstallPath": None,
            "DestDb2UserGroup": None,
            "StoragePolicy": None
        }

    def setup(self):
        """ Initial configuration for the test case.

            Raises:
                Exception:
                    If test case initialization is failed.
        """

        try:
            self.src_client_conn = Machine(machine_name=self.tcinputs['SrcClientName'],
                                           commcell_object=self.commcell)

            self.dest_client_conn = Machine(machine_name=self.tcinputs['DestinationClientName'],
                                                   commcell_object=self.commcell)

            self.src_client = self.commcell.clients.get(self.tcinputs['SrcClientName'])
            self.dest_client = self.commcell.clients.get(self.tcinputs['DestinationClientName'])

            self.tablespace_name = f"TS{self.id}"
            self.table_name = f"TBL{self.id}"
            self.src_db2_path = self.tcinputs["SrcDb2InstallPath"]
            self.dest_db2_path = self.tcinputs["DestinationDb2InstallPath"]
            self.db2_instance_name = 'encins'
            self.db2_database = 'ENCDB'
            self.db2_username = 'encins'
            self.db2_user_password = 'Commvault@123100'

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
        self.src_agent, self.src_instance = self.add_db2_instance(client_obj=self.src_client)
        self.dest_agent, self.dest_instance = self.add_db2_instance(client_obj=self.dest_client)
        self.src_backupset = self.add_db2_backupset(instance_obj=self.src_instance)
        self.add_subclient()
        self.add_subclient(only_log=True)
        self.src_db2_helper = DB2(commcell=self.commcell,
                                    client=self.src_client,
                                    instance=self.src_instance,
                                    backupset=self.src_backupset)

        time.sleep(5)
        self.src_db2_helper.update_db2_database_configuration1(cold_backup_path='/dev/null')
        time.sleep(5)
        self.src_db2_helper.update_db2_database_configuration1(cold_backup_path='/dev/null')
        
        self.restart_db2_services(client_db2_conn=self.src_client_db2_conn)

        self.db2_gui_backups()
        self.src_db2_helper.db2_archive_log(db_name=self.db2_database, archive_number_of_times=10)
        self.db2_gui_backups(log_backup=True)

        self.verify_db2_backupset_encryption_properties()

        self.db2_gui_restore()

        cli_timestamp = self.db2_command_line_backups()
        self.db2_command_line_restore(timestamp=cli_timestamp, encrypt=False)

    def restart_db2_services(self, client_db2_conn):
        time.sleep(5)
        client_db2_conn.execute_command(command="db2 force application all")
        time.sleep(3)
        client_db2_conn.execute_command(command=f"db2 deactivate db {self.db2_database}")
        client_db2_conn.execute_command(command="db2 terminate")
        self.src_db2_helper.disconnect_applications()
        time.sleep(3)
        client_db2_conn.execute_command(command='db2stop')
        time.sleep(3)
        client_db2_conn.execute_command(command='db2start')
        time.sleep(5)
        self.src_db2_helper.reconnect()

    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.log.info("### Prerequisite setup for test case ###")
        self.verify_db2_version()
        self.src_db2_logs_dir = self.get_db2_logs_dir(client=self.src_client_conn)
        self.dest_db2_logs_dir = self.get_db2_logs_dir(client=self.dest_client_conn)
        self.recreate_db2_logs_dir(client=self.src_client_conn, 
                                   logs_path_dict=self.src_db2_logs_dir,
                                   db2_group=self.tcinputs["SrcDb2UserGroup"])
        self.recreate_db2_logs_dir(client=self.dest_client_conn, 
                                   logs_path_dict=self.dest_db2_logs_dir,
                                   db2_group=self.tcinputs["DestDb2UserGroup"])
        self.delete_db2_instance_on_client(client_conn=self.src_client_conn, db2_install_path=self.src_db2_path)
        self.delete_db2_instance_on_client(client_conn=self.dest_client_conn, db2_install_path=self.dest_db2_path)
        self.src_port = self.find_unused_port_instance(client_conn=self.src_client_conn)
        self.destination_port = self.find_unused_port_instance(client_conn=self.dest_client_conn)
        self.src_client_db2_conn = self.create_db2_instance_on_client(client_conn=self.src_client_conn,
                                                                      db2_group=self.tcinputs["SrcDb2UserGroup"],
                                                                      db2_install_path=self.src_db2_path,
                                                                      port=self.src_port)
        self.dest_client_db2_conn = self.create_db2_instance_on_client(client_conn=self.dest_client_conn,
                                                                       db2_group=self.tcinputs["DestDb2UserGroup"],
                                                                       db2_install_path=self.dest_db2_path,
                                                                       port=self.destination_port)
        self.enable_encryption_on_instance(client_db2_conn=self.src_client_db2_conn)
        self.add_database_on_client(client_conn=self.src_client_db2_conn)
        self.enable_encryption_on_instance(client_db2_conn=self.dest_client_db2_conn)
        self.add_src_key_to_destination()
        
    def verify_db2_version(self):
        """
        Verify source and destination db2 versions
        """
        src_version_cmd = f"db2ls | grep -i '{self.src_db2_path}' | awk 'NR>=1{{print $2}}'"
        source_version = self.src_client_conn.execute_command(command=src_version_cmd).output.strip()
        self.log.info("Source Version: %s" % source_version)
        destination_version_cmd = f"db2ls | grep -i '{self.dest_db2_path}' | awk 'NR>=1{{print $2}}'"
        destination_version = self.dest_client_conn.execute_command(command=destination_version_cmd).output.strip()
        self.log.info("Destination Version: %s" % destination_version)
        source_version = source_version.split('.')
        destination_version = destination_version.split('.')
        for version_index in range(0, len(source_version)):
            if int(source_version[version_index]) < int(destination_version[version_index]):
                raise Exception("Destination DB2 Version Higher than Source. Cannot proceed with the test case")


    def create_db2_instance_on_client(self, client_conn, db2_group, db2_install_path, port):
        """
        Creates instance on client
        """
        useradd_cmd = f"useradd -g {db2_group} {self.db2_username}"

        self.log.info(f"Creating user command: {useradd_cmd}")
        output = client_conn.execute_command(command=useradd_cmd)
        self.log.info(output.output)
        password_cmd = f"echo \"{self.db2_username}:{self.db2_user_password}\" | chpasswd"
        client_conn.execute_command(command=password_cmd)

        remove_instance_list = f"{db2_install_path}/instance/db2iset -d {self.db2_instance_name}"
        self.log.info(remove_instance_list)
        output = client_conn.execute_command(command=remove_instance_list)
        self.log.info(output.output)
        self.log.info("### Creating DB2 Instance ###")
        create_instance_cmd = f"{db2_install_path}/instance/db2icrt -u db2fenc1 -p {port} " \
                              f"{self.db2_username}" \

        self.log.info(f"Creating Instance command: {create_instance_cmd}")
        output = client_conn.execute_command(command=create_instance_cmd)
        self.log.info(output.output)
        client_db2_conn = Machine(machine_name=client_conn.machine_name,
                                  commcell_object=self.commcell,
                                  username=self.db2_username,
                                  password=self.db2_user_password)
        return client_db2_conn

    def delete_db2_instance_on_client(self, client_conn, db2_install_path):
        """
        Prepares client for restore
        Raises:
            Exception:
                If adding instance fails on CommServ.
        """
        self.log.info("### Preparing client for restore ###")
        password_cmd = f"echo \"{self.db2_username}:{self.db2_user_password}\" | chpasswd"
        if client_conn.check_user_exist(username=self.db2_username):
            self.log.info("### Dropping DB2 Instance ###")
            client_conn.execute_command(command=password_cmd)
            temp_client_conn = Machine(machine_name=client_conn.machine_name,
                                       commcell_object=self.commcell,
                                       username=self.db2_username,
                                       password=self.db2_user_password)

            output = temp_client_conn.execute_command(command=f"db2 connect reset;db2 deactivate db {self.db2_database}")
            self.log.info(output.output)
            output = temp_client_conn.execute_command(command="db2stop")
            self.log.info(output.output)
            drop_instance_cmd = f"{db2_install_path}/instance/db2idrop {self.db2_instance_name}"
            self.log.info(drop_instance_cmd)
            output = client_conn.execute_command(command=drop_instance_cmd)
            self.log.info(output.output)
            temp_client_conn.disconnect()
            self.log.info("### Deleting and adding user ###")
            client_conn.delete_users(users=[self.db2_username])

        time.sleep(5)
        # default_encrypted_password = get_config().DB2.password
        # user_id = self.client_node1_conn.execute_command(command=f"id -u {self.tcinputs['db2_username']}").output

    def enable_encryption_on_instance(self, client_db2_conn):
        """
        Enabling encryption
        """
        cmd = "export LD_LIBRARY_PATH=$HOME/sqllib/lib64/gskit:$LIBPATH"
        self.log.info(f"Command: {cmd}")
        output = client_db2_conn.execute_command(command=cmd)
        self.log.info(output.output)
        cmd = "export PATH=$HOME/sqllib/gskit/bin:$PATH"
        self.log.info(f"Command: {cmd}")
        output = client_db2_conn.execute_command(command=cmd)
        self.log.info(output.output)

        client_db2_conn.create_directory(directory_name=f"/home/{self.db2_username}/encinfo")

        cmd = f"gsk8capicmd_64 -keydb -create -db '/home/{self.db2_username}/encinfo/dbkeystore.db' -pw \"'{self.db2_user_password}'\" -strong -type pkcs12 -stash"
        self.log.info(f"Command: {cmd}")
        output = client_db2_conn.execute_command(command=cmd)
        self.log.info(output.output)

        cmd = f"db2 update dbm config using KEYSTORE_LOCATION /home/{self.db2_username}/encinfo/dbkeystore.db KEYSTORE_TYPE PKCS12"
        self.log.info(f"Command: {cmd}")
        output = client_db2_conn.execute_command(command=cmd)
        self.log.info(output.output)

        self.log.info(f"Command: db2start")
        output = client_db2_conn.execute_command(command="db2start")
        self.log.info(output.output)

    def add_database_on_client(self, client_conn):
        """
        Adding database on instance
        """
        self.log.info("Adding database on instance")
        create_db = f"db2 create db {self.db2_database} encrypt"
        self.log.info(f"Create database: {create_db}")
        output = client_conn.execute_command(command=create_db)
        self.log.info(output.output)

    def add_src_key_to_destination(self):
        """
        Export key for source db
        """
        self.src_client_db2_conn.create_directory(directory_name=f'/home/{self.db2_username}/exportpath', force_create=True)
        self.dest_client_db2_conn.create_directory(directory_name=f'/home/{self.db2_username}/exportpath', force_create=True)
        
        keys_list_cmd=f'gsk8capicmd_64 -cert -list -db /home/{self.db2_username}/encinfo/dbkeystore.db -stashed'
        keys_list = self.src_client_db2_conn.execute_command(command=keys_list_cmd).output
        self.log.info("Key list: %s", keys_list)
        keys_list = keys_list.split('#')
        label = None
        for key in keys_list:
            if self.db2_database.lower() in key.lower():
                label = key.replace('\n', ' ').strip()
                break
        self.log.info("Label : %s", label)
        if not label:
            self.log.info('DB is not encrypted!!')
            raise Exception('DB is not encrypted')

        
        export_cmd = f'gsk8capicmd_64 -cert -export -db /home/{self.db2_username}/encinfo/dbkeystore.db -stashed -label \
        {label} -target /home/{self.db2_username}/exportpath/mykeystore1F.raw -target_type pkcs12 -target_pw "\'{self.db2_user_password}\'"'
        
        self.src_client_db2_conn.execute_command(command=export_cmd)

        files_list = self.src_client_db2_conn.execute_command(command=f'ls /home/{self.db2_username}/exportpath/').output.strip().split('\n')
        self.log.info('Files to export: %s', files_list)

        for file in files_list:
            self.log.info('Exporting File: %s', file.strip())
            self.src_client_db2_conn.copy_file_between_two_machines(src_file_path=f'/home/{self.db2_username}/exportpath/{file.strip()}', 
                                                                    destination_machine_conn=self.dest_client_db2_conn, 
                                                                    destination_file_path=f'/home/{self.db2_username}/exportpath/{file.strip()}')

        import_cmd = f'gsk8capicmd_64 -cert -import -db /home/{self.db2_username}/exportpath/mykeystore1F.raw -pw "\'{self.db2_user_password}\'" -stashed \
        -target /home/{self.db2_username}/encinfo/dbkeystore.db -target_type pkcs12'

        self.dest_client_db2_conn.execute_command(command=import_cmd)

        self.log.info("Checking if key was exported!")

        keys_list_cmd=f'gsk8capicmd_64 -cert -list -db /home/{self.db2_username}/encinfo/dbkeystore.db -stashed'
        keys_list = self.dest_client_db2_conn.execute_command(command=keys_list_cmd).output
        self.log.info("Key list: %s", keys_list)
        keys_list = keys_list.split('#')
        label = None
        for key in keys_list:
            if self.db2_database.lower() in key.lower():
                label = key.replace('\n', ' ').strip()
                break
        self.log.info("Label : %s", label)
        if not label:
            self.log.info('DB key is not exported!!')
            raise Exception('DB key is not exported!!')

    def find_unused_port_instance(self, client_conn):
        """
        Find unused port for instance creation
        """
        self.log.info("Finding unused port between 50000 to 50100")
        final_port = "50000"
        for port in range(50000, 50100):
            port_usage_cmd = f"netstat -anp | grep ':{port}'"
            output = client_conn.execute_command(command=port_usage_cmd)
            self.log.info(f"For port {port}: {output.output}")
            if len(output.output.strip()) == 0:
                final_port = str(port)
                self.log.info(f"Unused Port is: {final_port}")
                break
        return final_port

    def add_db2_instance(self, client_obj):
        """
        Adds DB2 Instance
        Raises:
            Exception:
                If adding instance fails.
        """
        self.log.info("### Adding DB2 Instance ###")
        try:
            agent = client_obj.agents.get('DB2')
            if not agent.instances.has_instance(instance_name=self.db2_instance_name):
                db2_instance_options = {
                    'instance_name': self.db2_instance_name,
                    'data_storage_policy': self.tcinputs['StoragePolicy'],
                    'log_storage_policy': self.tcinputs['StoragePolicy'],
                    'command_storage_policy': self.tcinputs['StoragePolicy'],
                    'home_directory': f'/home/{self.db2_username}',
                    'password': self.db2_user_password,
                    'user_name': self.db2_username
                }
                agent.instances.add_db2_instance(db2_options=db2_instance_options)
                agent.instances.refresh()
            return agent, agent.instances.get(self.db2_instance_name)
        except Exception as exp:
            self.log.info(exp)

    def add_db2_backupset(self, instance_obj, db_name=None):
        """
        Adds DB2 Backupset
        """
        backupset = None
        if not db_name:
            db_name = self.db2_database
        try:
            self.log.info("### Adding DB2 Backupset ###")
            if not instance_obj.backupsets.has_backupset(backupset_name=db_name):
                instance_obj.backupsets.add(backupset_name=db_name,
                                        storage_policy=self.tcinputs['StoragePolicy'])
            instance_obj.refresh()
            backupset = instance_obj.backupsets.get(backupset_name=db_name)
        except Exception as exp:
            self.log.info(exp)
        return backupset

    def add_subclient(self, only_log=False):
        """
        Creates a subclient
        Args:
            only_log (bool): Create only log subclient or not
        """
        subclient_name = f"{self.id}logsub" if only_log else f"{self.id}sub"
        self.log.info("### Creating Subclient ###")
        self.src_backupset.refresh()
        if not self.src_backupset.subclients.has_subclient(subclient_name=subclient_name):
            self.src_backupset.subclients.add(subclient_name=subclient_name,
                                              storage_policy=self.tcinputs['StoragePolicy'],
                                              description="DB2 Encryption ACCT-1 Subclient")

        if only_log:
            log_subclient = Subclients(class_object=self.src_backupset).get(subclient_name=subclient_name)
            log_subclient.disable_backupdata()
            self.log.info("Log Backup subclient created.")
        else:
            self.subclient = Subclients(class_object=self.src_backupset).get(subclient_name=subclient_name)

    def verify_db2_backupset_encryption_properties(self):
        """
        Verify backupset properties
        """
        self.log.info("### Verifying DB2 Backupset Properties ###")
        csdb_encr_values = self.src_db2_helper.get_database_encropts_csdb()
        client_encr_values = self.src_db2_helper.get_database_encropts_client()

        self.log.info("Expected Values -> Encrlib: %s, Encropts: %s", client_encr_values['DB2 Encryption Library'], client_encr_values['DB2 Encryption Options'])
        self.log.info("CSDB Values -> Encrlib: %s, Encropts: %s", csdb_encr_values['DB2 Encryption Library'], csdb_encr_values['DB2 Encryption Options'])

        if client_encr_values['DB2 Encryption Library'] != csdb_encr_values['DB2 Encryption Library']:
            raise AssertionError("Encryption Library is not set for Backupset as expected!!")
        if client_encr_values['DB2 Encryption Options'] != csdb_encr_values['DB2 Encryption Options']:
            raise AssertionError("Encryption Options is not set for Backupset as expected!!")

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

    def prepare_data_on_client(self, table_type, create_tablespace=False):
        """
        Prepares data on client
        Args:
            table_type (str) -- Backup for which table is needed
            create_tablespace (bool) -- Need to create tablespace or not
                default: False
        """
        self.datafile = self.src_db2_helper.get_datafile_location()
        self.src_db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}",
                                          flag_create_tablespace=create_tablespace)
        if create_tablespace:
            self.table_data = self.src_db2_helper.prepare_data(
                                                        table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}")

    def db2_gui_backups(self, log_backup=False):
        """
        Perform All DB2 Backups
        Args:
            log_backup (bool): Run only log backup
        """
        self.log.info("### Running GUI Backups ###")
        self.src_backupset.refresh()
        if log_backup:
            log_subclient = Subclients(class_object=self.src_backupset).get(subclient_name=f"{self.id}logsub")
            log_backup_job = log_subclient.backup(backup_level="FULL")
            self.wait_for_job(job_object=log_backup_job)
        else:
            self.prepare_data_on_client(table_type="FULL", create_tablespace=True)
            full_backup_job = self.src_db2_helper.run_backup(subclient=self.subclient,
                                                             backup_type="FULL")
            self.wait_for_job(job_object=full_backup_job)
            self.validate_backup_job(backup_job_object=full_backup_job)

            self.restart_db2_services(client_db2_conn=self.src_client_db2_conn)

            self.prepare_data_on_client(table_type="INCR")

            incr_backup_job = self.src_db2_helper.run_backup(subclient=self.subclient,
                                                             backup_type="INCREMENTAL")
            self.wait_for_job(job_object=incr_backup_job)
            self.validate_backup_job(backup_job_object=incr_backup_job)

            self.restart_db2_services(client_db2_conn=self.src_client_db2_conn)

            self.prepare_data_on_client(table_type="DEL")

            diff_backup_job = self.src_db2_helper.run_backup(subclient=self.subclient,
                                                             backup_type="DIFFERENTIAL")
            self.wait_for_job(job_object=diff_backup_job)
            self.validate_backup_job(backup_job_object=diff_backup_job)

            self.restart_db2_services(client_db2_conn=self.src_client_db2_conn)

    def db2_gui_restore(self):
        """
        Runs DB2 GUI Restore
        """
        self.log.info("### Out of place restore ###")
        self.src_backupset.refresh()
        self.dest_client_db2_conn.create_directory(directory_name=f'/home/{self.db2_username}/stogrp')
        self.dest_client_db2_conn.create_directory(directory_name=f'/home/{self.db2_username}/tbspace')
        redirect_storage_group = {'IBMSTOGROUP': f'/home/{self.db2_username}/stogrp'}
        restore_job = self.src_backupset.restore_out_of_place(dest_client_name=self.dest_client.client_name,
                                                              dest_instance_name=self.dest_instance.instance_name,
                                                              dest_backupset_name=self.src_backupset.backupset_name,
                                                              target_path=f'/home/{self.db2_username}/',
                                                              redirect_enabled=True,
                                                              redirect_tablespace_path=f'/home/{self.db2_username}/tbspace',
                                                              redirect_storage_group_path=redirect_storage_group,
                                                              rollforward=True,
                                                              restore_incremental=False)
        self.wait_for_job(restore_job)

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.src_client.display_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job_object=job)

        self.validate_restore_job(table_name=self.table_name)

    def db2_command_line_backups(self):
        """
        Running command line backups
        """
        self.log.info("### Running CLI Backups ###")
        self.src_db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"{self.table}_CLI_FULL",
                                          flag_create_tablespace=False)
        backup_timestamp = self.src_db2_helper.third_party_command_backup(db_name=self.src_backupset.backupset_name.upper(),
                                                                          backup_type="FULL")
        self.validate_backup_job(cli_job=True, timestamp=backup_timestamp, job_type="full")

        self.src_db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"{self.table}_CLI_INCR",
                                          flag_create_tablespace=False)
        backup_timestamp = self.src_db2_helper.third_party_command_backup(db_name=self.backupset.backupset_name.upper(),
                                                                          backup_type="INCREMENTAL")
        self.validate_backup_job(cli_job=True, timestamp=backup_timestamp, job_type="incremental")

        self.src_db2_helper.create_table2(datafile=self.datafile,
                                          tablespace_name=self.tablespace_name,
                                          table_name=f"{self.table}_CLI_DELTA",
                                          flag_create_tablespace=False)
        backup_timestamp = self.src_db2_helper.third_party_command_backup(db_name=self.backupset.backupset_name.upper(),
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
            self.src_db2_helper.backup_validation(operation_type=exp_operation_type[job_type.lower()],
                                              tablespaces_count=self.table_data[1],
                                              backup_time_stamp=timestamp)
        else:
            backup_time_stamp, _ = self.src_db2_helper.get_backup_time_stamp_and_streams(jobid=backup_job_object.job_id)

            self.log.info("### Running Backup Validation ###")
            time.sleep(30)
            self.src_db2_helper.backup_validation(operation_type=exp_operation_type[backup_job_object.backup_level.lower()],
                                                  tablespaces_count=self.table_data[1],
                                                  backup_time_stamp=backup_time_stamp)
            self.log.info("Successfully ran %s backup." % backup_job_object.backup_level)

    def db2_command_line_restore(self, timestamp, encrypt):
        """
        Performing command line restore
        Args:
            timestamp (str): Timestamp to perform restore to.
        Raises:
            Exception:
                If command line restore or rollforward fails.
        """
        self.log.info("### Command Line Out of place restore ###")
        redirect_tablespace = {
            self.tablespace_name: f'/home/{self.db2_username}/tbspace/TSCLI_Full.dbf'}
        restore_dir = f'/home/{self.db2_username}/'
        load_path = self.dest_client_conn.get_registry_value("Base", "dBASEHOME")
        self.dest_client_db2_conn.execute_command(command="db2 force application all")
        self.dest_client_db2_conn.execute_command(command=f"db2 deactivate db {self.backupset.backupset_name}")
        self.dest_client_db2_conn.execute_command(command="db2 terminate")
        name = f"{self.src_backupset.backupset_name.upper()}E" if encrypt else f"{self.src_backupset.backupset_name.upper()}NE"
        if encrypt:

            restore_cmd = "db2 restore db %s incremental automatic load \"'%s'\" open 2 sessions " \
                        "OPTIONS 'CvSrcDbName=%s,CvSrcDB2InstanceName=%s,CvSrcClientName=%s,CvClientName=%s,CvInstanceName=%s'"\
                        "taken at %s on %s into %s REDIRECT without prompting" % (self.src_backupset.backupset_name.upper(),
                                                                                    load_path+'/libDb2Sbt.so',
                                                                                    self.src_backupset.backupset_name.upper(),
                                                                                    self.db2_instance_name,
                                                                                    self.src_client_conn.get_hardware_info()['MachineName'],
                                                                                    self.dest_client_conn.get_hardware_info()['MachineName'],
                                                                                    self.dest_client.instance,
                                                                                    timestamp,
                                                                                    restore_dir,
                                                                                    self.src_backupset.backupset_name.upper())
        else:
            restore_cmd = "db2 restore db %s incremental automatic load \"'%s'\" open 2 sessions " \
                        "OPTIONS 'CvSrcDbName=%s,CvSrcDB2InstanceName=%s,CvSrcClientName=%s,CvClientName=%s,CvInstanceName=%s'"\
                        "taken at %s NO ENCRYPT on %s into %s REDIRECT without prompting" % (self.src_backupset.backupset_name.upper(),
                                                                                    load_path+'/libDb2Sbt.so',
                                                                                    self.src_backupset.backupset_name.upper(),
                                                                                    self.db2_instance_name,
                                                                                    self.src_client_conn.get_hardware_info()['MachineName'],
                                                                                    self.dest_client_conn.get_hardware_info()['MachineName'],
                                                                                    self.dest_client.instance,
                                                                                    timestamp,
                                                                                    restore_dir,
                                                                                    self.src_backupset.backupset_name.upper())

        self.log.info("Restore Command: %s" % restore_cmd)
        restore_output = self.dest_client_db2_conn.execute_command(command=restore_cmd)

        if str(restore_output.output).lower().find("restore database command completed successfully") >= 0:
            self.log.info(f"CLI restore is successful :{restore_output.output}")
        else:
            raise Exception("CLI restore is not successful : %s" % restore_output.output)

        get_table_space_id = "db2 connect to %s; db2 \"SELECT tbsp_id FROM TABLE(MON_GET_TABLESPACE('',-2)) where" \
                             " tbsp_name='%s'\"" % (self.src_backupset.backupset_name.upper(), self.tablespace_name)
        tablespace_id = self.src_db2_helper.third_party_command(cmd=get_table_space_id).strip().split('\n')[-3].strip()

        redirect_tablespace_cmd = "db2 \"set tablespace containers for %s using (file '%s' 25600)\"" \
                                  % (tablespace_id, redirect_tablespace[self.tablespace_name])
        self.log.info(redirect_tablespace_cmd)
        redirect_set = self.dest_client_db2_conn.execute_command(command=redirect_tablespace_cmd)
        self.log.info(redirect_set.output)

        restore_continue_cmd = f"db2 restore db {self.src_backupset.backupset_name.upper()} CONTINUE"
        self.log.info(restore_continue_cmd)
        restore_continue = self.dest_client_db2_conn.execute_command(command=restore_continue_cmd)

        if str(restore_continue.output).lower().find("restore database command completed successfully") >= 0:
            self.log.info(f"CLI restore is successful :{restore_continue.output}")
        else:
            raise Exception(f"CLI restore is not successful : {restore_continue.output}")

        self.update_destination_db_config_restore(db_name=name)

        rollforward_cmd = f"db2 rollforward db {self.src_backupset.backupset_name.upper()} to end of logs and stop"
        self.log.info(rollforward_cmd)
        rollforward_output = self.dest_client_db2_conn.execute_command(command=rollforward_cmd)

        if str(rollforward_output.output).find("'not', 'pending'") or \
                str(rollforward_output.output).find("not pending") >= 0:
            self.log.info(f"Rollforward was successful: {rollforward_output.output}")
        else:
            raise Exception(f"Rollforward is not successful: {rollforward_output.output}")

        time.sleep(20)
        self.validate_restore_job(table_name=f"{self.table_name}_CLI", encrypt=encrypt, dest_db=name)

    def update_destination_db_config_restore(self, db_name):
        """
        Updating Destination Client Config for Rollforward
        """
        machine_name = self.dest_client_conn.get_hardware_info()['MachineName']
        self.log.info(f"### Updating db2 database configs properties on node {machine_name} ###")

        commvault_instance = self.dest_client.instance
        base_cmd = f"db2 update db cfg for {db_name} using "
        opt_cfg = "\"'CvSrcDbName=%s,CvSrcClientName=%s,CvClientName=%s,CvInstanceName=%s'\"" \
                  % (self.src_backupset.backupset_name.upper(), self.src_client_conn.get_hardware_info()['MachineName'], 
                    machine_name, commvault_instance)

        cmd = f"{base_cmd}LOGARCHOPT1 {opt_cfg}"
        self.log.info(f"Set LOGARCHOPT1 options {cmd}")
        output = self.dest_client_db2_conn.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

        cmd = f"{base_cmd}VENDOROPT {opt_cfg}"
        self.log.info(f"Set VENDOROPT options {cmd}")
        output = self.dest_client_db2_conn.execute_command(command=cmd)
        self.log.info(f"Output: {output.output}")

    def validate_restore_job(self, table_name, encrypt, dest_db=None):
        """
        Validates Restore Jobs
        Args:
            table_name (str): Table name to verify on destination after restore
        """
        
        self.commcell.refresh()
        self.dest_client.refresh()
        dest_backupset = self.add_db2_backupset(instance_obj=self.dest_instance, db_name=dest_db)
        dest_db2_helper = DB2(commcell=self.commcell,
                                client=self.dest_client,
                                instance=self.dest_instance,
                                backupset=dest_backupset)
        dest_db2_helper.restore_validation(table_space=self.tablespace_name,
                                            table_name=f"SCHEMAFULL.{table_name}",
                                            tablecount_full=self.table_data[0])

        if encrypt:
            dest_enc = dest_db2_helper.get_database_encropts_client()
            src_enc = self.src_db2_helper.get_database_encropts_client()

            self.compare_properties("DB2 Encryption Options", src_enc["DB2 Encryption Options"], dest_enc["DB2 Encryption Options"])
            self.compare_properties("DB2 Encryption Library", src_enc["DB2 Encryption Library"], dest_enc["DB2 Encryption Library"])
        self.log.info("Verified Restore.")
        dest_db2_helper.disconnect_applications()

    def log_archiving_test(self):
        """
        Perform Log Archive 50 times and verify if command line log backup is run
        """
        self.log.info("Performing Log Archive 50 times and verify if command line log backup is run")
        current_file = self.src_db2_helper.get_active_logfile()[1]
        self.src_db2_helper.db2_archive_log(self.src_backupset.backupset_name.upper(), 50)
        new_active_log_file = self.src_backupset.get_active_logfile()[1]
        if new_active_log_file == current_file:
            raise Exception("Archiving Log Failed")
        time.sleep(10)
        all_jobs = self.commcell.job_controller.finished_jobs(client_name=self.src_client.client_name,
                                                              lookup_time=0.02,
                                                              job_filter="Backup")
        for job_id in all_jobs:
            if 'application' in all_jobs[job_id]['operation'].lower() and \
                    'restore' in all_jobs[job_id]['operation'].lower():
                continue
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)

    def get_db2_logs_dir(self, client):
        """
        Get DB2 logs directory on given client
        """
        archive_location = client.get_registry_value(key='Db2Agent',
                                                     value='sDB2_ARCHIVE_PATH')
        audit_location = client.get_registry_value(key='Db2Agent',
                                                   value='sDB2_AUDIT_ERROR_PATH')
        retrieve_location = client.get_registry_value(key='Db2Agent',
                                                      value='sDB2_RETRIEVE_PATH')
        return {
            "db2ArchivePath": f"/{archive_location}/{self.db2_instance_name}",
            "db2RetrievePath": f"/{retrieve_location}/retrievePath/{self.db2_instance_name}",
            "db2AuditErrorPath": f"/{audit_location}/"
        }

    def recreate_db2_logs_dir(self, client, logs_path_dict, db2_group):
        """
        Recreate DB2 log directory from destination node.
        """
        self.log.info("### Remove existing DB2 log directory from all nodes and recreating ###")
        for _, dirs in logs_path_dict.items():
            self.log.info(f"Recreating {dirs}")
            client.create_directory(directory_name=dirs, force_create=True)
            client.execute_command(command=f"chmod -R 777 {dirs}")
            client.execute_command(command=f"chgrp -R "
                                           f"{db2_group} {dirs}")

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.log.info("### Teardown for the test case 60897 ###")
        try:
            self.src_db2_helper.disconnect_applications()
            self.src_client_conn.disconnect()
            self.src_client_db2_conn.disconnect()
            self.dest_client_conn.disconnect()
            self.dest_client_db2_conn.disconnect()
        except Exception as _:
            pass
        finally:
            self.status = constants.PASSED
            self.log.info("******TEST CASE PASSED****")
