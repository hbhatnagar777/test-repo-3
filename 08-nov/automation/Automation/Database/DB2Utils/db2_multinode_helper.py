# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Db2helper file for performing DB2 operations

DB2 is the only class defined in this file

DB2: Helper class to perform DB2 operations

DB2:
====
    __init__()                              -- initializes DB2 Helper object

    create_tablespace()                     -- creates sample tablespace

    backup_validation()                     -- validates backup image timestamp with db2
    history file

    restore_validation()                    -- validates restore job by checking if data restored
    is accessible or not

    update_db2_database_configuration1()    -- updates db2 db configurations

    get_db2_version()                       -- returns db2 application version

    get_db2_information()                   -- gets database list, db2 home directory for the
    given db2 instance

    third_party_command_backup()            -- used to trigger command line backup job for database

    third_party_command_restore()           -- triggers command line restore job for database

    third_party_command_rollforward()       -- triggers command line rollforward for database

    third_party_command_recover()           -- triggers command line recover database

    db2_archive_log()                       -- uses command line to archive db2 logs

    third_party_command()                   -- method to execute third party commands

    db2_cold_backup()                       -- triggers cold backup

    restore_from_cold_backup()              -- triggers restore from cold backup

    compare_db2_versions()                  -- compare db2 version

    get_datafile_locations()                -- Gets the datafile locations for all the nodes.

"""

import ibm_db
from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils.database_helper import Db2
from Database.DB2Utils.db2helper import DB2
from AutomationUtils import machine


class DB2MultiNode(DB2):
    """Helper class to perform DB2 operations"""

    def __init__(self, commcell, pseudo_client):
        """Initializes DB2helper object

            Args:
                commcell             (Commcell) --  Commcell object

                pseudo_client        (Client)   --  Pseudo Client object
        """
        self.is_pseudo_client = True
        self.log = logger.get_log()
        self.log.info('  Initializing db2 Helper ...')
        self.commcell = commcell
        self.client = pseudo_client
        self.instance = None
        self.backupset = None

        self._database = None
        self._hostname = None

        self._protocol = "TCPIP"
        self._db_user = None
        self._db_password = None

        self._db2_home_path = None
        self.machine_object = None
        self.machine_db2object = None
        self._port = None
        self._connection = None
        self.db2 = None
        self._pseudo_client_name = pseudo_client.display_name
        self._csdb = database_helper.get_csdb()

        self.db2cmd = None
        self.load_path = None
        self.platform = None
        self.db2_profile = ""
        self.simpana_instance = None
        self.simpana_base_path = None
        self.physical_client = None
        self.physical_client_objects_list = list()
        self.nodes = None

    def db2_instance_setter(self, instance_object, user, home_directory, backupset):
        """
        Sets instance values
        Args:
            instance_object (Instance): Object of instance class
            user    (username): User fot the instance
            home_directory  (str): Home Directory for instance
            backupset (Backupset) : Backupset object
        """
        self.instance = instance_object
        self._db_user = user
        self._db2_home_path = home_directory
        self.get_db2_password()
        self.log.info(" db2 user name is %s", self._db_user)
        self.backupset = backupset
        self._database = self.backupset.backupset_name.upper()
        self.client_connections()
        self.database_connection()

    def client_connections(self):
        """
        Creates client connections
        """
        query = f"Select attrVal as 'Physical Clients' from APP_InstanceProp where componentNameId in " \
                f"(SELECT instance FROM APP_Application where " \
                f"clientId=(SELECT id FROM APP_Client WHERE name = '{self._pseudo_client_name}')) " \
                f"and attrName='DB2 Partition Clients'"

        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            id_set = set()
            for client_id in cur[0].strip().split(' '):
                id_set.add(client_id.strip().split(',')[1].strip())
            self.log.info("Physical Clients Found: %s. Selecting catalog node client for operations.", cur[0])

            for client_id in id_set:
                query = f"select name from app_client where id={client_id}"
                self._csdb.execute(query)
                cur = self._csdb.fetch_one_row()
                client_name = cur[0]
                temp_physical_client = self.commcell.clients.get(name=client_name)
                self.physical_client_objects_list.append(temp_physical_client)
                self.log.info("Checking catalog node on client: %s", client_name)
                temp_machine_db2object = machine.Machine(temp_physical_client.client_hostname,
                                                         username=self._db_user,
                                                         password=self._db_password)
                output = temp_machine_db2object.execute_command(command=f'db2 connect to {self._database}; '
                                                                        f'db2 "values(current dbpartitionnum)"').output
                self.log.info("Output: %s", output)
                output = output.replace(' ', '').split('-----------')[1].split('\n')[1]

                if output == '0':
                    self.log.info("Catalog node found on: %s", client_name)
                    self.physical_client = temp_physical_client
                    self._hostname = self.physical_client.client_hostname

        self.machine_db2object = machine.Machine(
            self.physical_client.client_hostname,
            username=self._db_user,
            password=self._db_password)
        self.machine_object = machine.Machine(self.physical_client)

        self.db2cmd = "export DB2NODE=0;"
        self.platform = self.machine_object.os_info
        self.db2_profile = ""
        self.simpana_instance = self.physical_client.instance
        self.simpana_base_path = self.machine_object.get_registry_value(
            "Base", "dBASEHOME")
        self.load_path = "{0}/libDb2Sbt.so".format(self.simpana_base_path)
        self.get_db2_information()

    def database_connection(self, port=None):
        """
        Connects to Database
        Args:
            port    (str): Port to connect to
        """
        self._port = str(port) if port else self.get_database_port()

        self.db2 = Db2(
            self._database,
            self._hostname,
            self._port,
            self._protocol,
            self._db_user,
            self._db_password)
        self._connection = self.db2._connection

    def create_tablespace(self, datafiles, tblspace_name,
                          flag_recreate_tablespace):
        """
        Method to create tablespace

        Args:
            datafiles List (str)                  -- datafile location where tablespace can
            hold the physical file

            tblspace_name (str)             -- name of the tablespace

            flag_recreate_tablespace (bool)   -- flag to re-create tablespace if it exists

        Returns:
            False      -   method return false if drop tablespace fails or creation fails
        """
        if flag_recreate_tablespace:
            if not self.drop_tablespace(tblspace_name=tblspace_name):
                return False

            using_file_cmd = ""
            for node in self.nodes:
                using_file_cmd += f"USING (FILE '{datafiles[int(node)]+tblspace_name}_Full.dbf' 100M ) " \
                                  f"on dbpartitionnums ({int(node)})"

            cmd = "CREATE TABLESPACE {0} MANAGED BY DATABASE {1} AUTORESIZE NO ".format(tblspace_name, using_file_cmd)

            self.log.info(f"Tablespace create command: {cmd}")

            output = ibm_db.exec_immediate(self._connection, cmd)
            if output:
                self.log.info("Created tablespace successfully")
                return True
            else:
                self.log.info(
                    "tablespace is not created successfully :%s", output)
                return False

    def create_table2(self, datafiles, tablespace_name,
                      table_name, flag_recreate_tablespace):
        """ creates table in the given tablespace

            Args:

                datafiles                List(str)       -- datafile location

                tablespace_name         (str)       -- name of the tablespace

                table_name              (str)       -- name of the table

                flag_recreate_tablespace  (bool)      -- set flag to create or not the tablespace

            Returns:

                (bool)  - returns false if table creation fails

        """
        self.create_tablespace(
            datafiles, tablespace_name, flag_recreate_tablespace)

        cmd = "create table {0} (name varchar(30), ID decimal) in {1} ".format(
            table_name, tablespace_name)

        output = ibm_db.exec_immediate(self._connection, cmd)
        if output:
            self.log.info(
                "Created table successfully with table name %s ",
                table_name)
        else:
            self.log.info("table is not created successfully")
            return False

        cmd = "insert into {0} values('commvault', 1)".format(table_name)
        for _ in range(1, 10):
            output = ibm_db.exec_immediate(self._connection, cmd)

        self.log.info("Inserted rows into table successfully")
        return True

    def backup_validation(self, operation_type,
                          tablespaces_count, backup_time_stamp):
        """
        Validates if backup job is successful

        Args:

            operation_type      (str)   -- type backup job like full/incremental/delta

            tablespaces_count   (int)   -- tablespace count

            backup_time_stamp   (str)   -- backup image timestamp

        Raises:

            Exception:
                If job type ran is not correct.
                If there is a mismatch in number of tablespaces backedup.
                If tablespace backup is not successfull.

        """
        cmd = (
            "select operationtype, TBSPNAMES from sysibmadm.db_history "
            "where start_time =  '{0}' and "
            "operationtype in('F','N','I','O','D','E')".format(backup_time_stamp))
        self.log.info(cmd)
        stmt = ibm_db.exec_immediate(self._connection, cmd)
        tble_line = set()
        operation_set = set()
        while ibm_db.fetch_row(stmt) != False:
            tablespaces_temp = ibm_db.result(stmt, "TBSPNAMES")
            operation_set.add(ibm_db.result(stmt, 0))
            self.log.info(tablespaces_temp)
            for tablespace_temp in tablespaces_temp.split(','):
                tble_line.add(tablespace_temp.strip())

        self.log.info("table spaces backed up: '%s'", tble_line)
        self.log.info(
            "total table spaces: '%s'", tablespaces_count)
        self.log.info(
            "Types of backups: '%s'", operation_set)
        if ''.join(operation_set) == operation_type:
            self.log.info(
                "Correct backup type job ran  F - Offline   N - Online   I - "
                "Incremental offline  O - Incremental online D - Delta offline "
                "E - Delta online  Actual job type :%s , Ran job type: %s",
                operation_type,
                ''.join(operation_set))

        else:
            raise Exception("Correct backup type job is not ran. Actual job type:{0} Ran "
                            "Job Type: {1}".format(operation_type, ''.join(operation_set)))
        for db_tablespace in tablespaces_count:
            if str(tble_line).find(db_tablespace) >= 0:
                self.log.info(
                    "Table space backed up successfully : '%s'", db_tablespace)
            else:
                raise Exception(
                    "Table space was not able to back up successfully : '{0}'".format(
                        db_tablespace))
            self.log.info(
                " All Table space backed up successfully : '%s'", db_tablespace)

    def restore_validation(
            self,
            table_space,
            table_name,
            tablecount_full=None,
            tablecount_incr=None,
            tablecount_delta=None,
            storage_grps=None):
        """
        After restore it will check whether table space is accessible
        and checks the restore table data with original table data

        Args:

            table_space         (str)   --  name of the tablespace
            table_name          (str)   --  table name

            tablecount_full     (int)   --  number of rows in table during full backup
                default:    None

            tablecount_incr     (int)   --  number of rows in table during incremental backup
                default:    None

            tablecount_delta    (int)   --  number of rows in table during delta backup
                default:    None

            storage_grps         (list)   --  list of names of the storage groups
                default:    None

        Raises:

            Exception:
                if any table or tablespace is not restored successfully

        """
        cmd = "SELECT SERVICE_LEVEL FROM TABLE(SYSPROC.ENV_GET_INST_INFO())"
        self.log.info(cmd)
        stmt = ibm_db.exec_immediate(self._connection, cmd)
        output = ibm_db.fetch_assoc(stmt)
        self.log.info(output)

        self.log.info("DB2 version: %s", output['SERVICE_LEVEL'])
        if str(output['SERVICE_LEVEL']).find("v9.") >= 0:
            cmd = ("select ACCESSIBLE from  table(sysproc.snapshot_container('{0}',0)) tbl "
                   "where TABLESPACE_NAME = '{1}'".format(self._database, table_space))
            self.log.info(cmd)
        else:
            cmd = ("select ACCESSIBLE from  table(sysproc.SNAP_GET_CONTAINER_V91('{0}',0)) tbl"
                   " where TBSP_NAME = '{1}'".format(self._database, table_space))

            self.log.info(cmd)

        stmt = ibm_db.exec_immediate(self._connection, cmd)
        output = ibm_db.fetch_assoc(stmt)
        self.log.info(output)

        self.log.info("Accessible value %s", output['ACCESSIBLE'])
        if output['ACCESSIBLE'] == 0:
            self.log.info("Data is not restored")
            return False

        output = self.db2.get_table_content(f"{table_name}")

        if output != tablecount_full:
            output = self.db2.get_table_content(
                "{0}_PARTIAL".format(table_name))
            self.log.info(output)
            if output != tablecount_full:
                self.log.info(
                    "table %s_FULL or %s_PARTIAL is not restored correctly",
                    table_name, table_name)
                return False

        if tablecount_incr is not None:
            output = self.db2.get_table_content(
                "{0}_INCR".format(table_name))
            self.log.info(output)
            if output != tablecount_incr:
                self.log.info(
                    "table : %s_INCR is not restored correctly", table_name)
                return False

        if tablecount_delta is not None:
            output = self.db2.get_table_content(
                "{0}_DELTA".format(table_name))
            self.log.info(output)
            if output != tablecount_delta:
                self.log.info(
                    "table %s_DELTA is not restored correctly", table_name)
                return False

            self.log.info(
                "All tables are restored correctly from "
                "all backup images(full, incremental, delta)")

        if storage_grps:
            for storage_grp in storage_grps:
                cmd = f"select SGNAME from syscat.stogroups where SGNAME = '{storage_grp}'"
                stmt = ibm_db.exec_immediate(self._connection, cmd)
                stogrp = ibm_db.fetch_assoc(stmt)
                if stogrp:
                    stogrp = str(stogrp.items())
                    self.log.info("Storage Group exists : %s", stogrp)
                else:
                    self.log.info("Storage Group %s is not restored correctly", stogrp)
                    return False
        return True

    def update_db2_database_configuration1(self, cold_backup_path=None):
        """
        updates DB2 db configurations LOGARCHMETH1, LOGARCHOPT1, VENDOROPT, TRACKMOD parameters

        Args:
            cold_backup_path (str) -- Cold Backup Path
        """
        cmd = (
            "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using LOGARCHMETH1 "
            "''VENDOR:{1}/libDb2Sbt.so''')".format(
                self._database, self.simpana_base_path))
        self.log.info("Set LOGARCHMETH1 to CV %s", cmd)
        self.exec_immediate_method(cmd)

        cmd = (
            "CALL SYSPROC.ADMIN_CMD('update db cfg for {0} using LOGARCHOPT1 ''"
            "CvDpfClientName={1},CvInstanceName={2}''')".format(
                self._database,
                self._pseudo_client_name,
                self.simpana_instance))
        self.log.info("Set LOGARCHOPT1 options %s", cmd)
        self.exec_immediate_method(cmd)

        cmd = (
            "CALL SYSPROC.ADMIN_CMD('update db cfg for {0} using VENDOROPT ''CvDpfClientName={1},"
            "CvInstanceName={2}''')".format(
                self._database,
                self._pseudo_client_name,
                self.simpana_instance))
        self.log.info("Set VENDOROPT options %s", cmd)
        self.exec_immediate_method(cmd)

        cmd = "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using LOGARCHMETH2 OFF')".format(
            self._database)
        self.log.info("Set LOGARCHMETH2 OFF :%s", cmd)
        self.exec_immediate_method(cmd)

        cmd = "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using TRACKMOD ON')".format(
            self._database)
        self.log.info("Set TRACKMOD ON %s", cmd)
        self.exec_immediate_method(cmd)

        cmd = "{0} connect reset".format(self.db2cmd)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)
        output = cmd_output.formatted_output
        self.log.info("output: %s", output)

        self.disconnect_applications(self._database)

        if cold_backup_path:
            self.db2_cold_backup(cold_backup_path=cold_backup_path)
        self.reconnect()

    def get_db2_information(self):
        """
        gets information about db2home, db2 databases, simpana instance name, simpana base path

        Raises:
            Exception:
                if unable to get db2 information

        """
        self.log.info("Instance name is : %s", self.simpana_instance)

        self.log.info("Simpana Base Path : %s", self.simpana_base_path)
        db2_home_path = self._db2_home_path
        self.log.info("DB2 Home Path : %s", db2_home_path)

        self.db2_profile = "{0}/sqllib/db2profile".format(
            db2_home_path)
        self.db2cmd = "{0};db2".format(self.db2_profile)

        db2_database_list = self.list_database_directory()
        self.log.info("DB2 Database List is : %s", db2_database_list)

        self.nodes = self.get_list_of_nodes()
        self.log.info("DB2 Database Nodes List is : %s", self.nodes)

        return db2_home_path, db2_database_list, self.simpana_instance, self.simpana_base_path


    def get_list_of_nodes(self):
        """
        method to list all partition nodes

        Returns: (list) - list of partitioned nodes

        """
        cmd = f"cat {self._db2_home_path}/sqllib/db2nodes.cfg  | awk 'NR>=1{{print $1}}'"
        self.log.info(cmd)
        cmd_output = self.machine_db2object.execute_command(cmd)
        output = cmd_output.output.strip().split('\n')
        self.log.info("%s", output)
        return output


    def third_party_command_backup(self, backup_type, online=True):
        """
        Uses command line to submit backup job on database.

        Args:

            backup_type    (str)   -- backup job type like FULL, INCREMENTAL , DELTA
            online         (bool)  -- Online backup should be taken or not
                default: True

        Returns:

            str - backup image timestamp

        Raises:
            Exception:
                if incorrect backup type is given or if any issue in running the backup job

        """
        self.log.info(self.load_path)
        image_type = "online" if online else ""
        temp_db2cmd = f"{self.db2cmd} force application all;db2 deactivate db {self._database};db2 terminate; db2 "
        if "FULL" in backup_type.upper():
            cmd = f"{temp_db2cmd} backup db {self._database} on all nodes {image_type} load \"'{self.load_path}'\""
        elif "DEL" in backup_type.upper() or "DIF" in backup_type.upper():
            cmd = f"{temp_db2cmd} backup db {self._database} on all nodes {image_type} incremental delta" \
                  f" load \"'{self.load_path}'\""
        elif "INC" in backup_type.upper():
            cmd = f"{temp_db2cmd} backup db {self._database} on all nodes {image_type} incremental" \
                  f" load \"'{self.load_path}'\""
        else:
            raise Exception("Incorrect backup type entered")

        output = self.third_party_command(cmd)

        output = output.replace(" ", "")
        output = output.replace("\n", "")
        output = output.split(":")
        backup_time_stamp1 = output[1]

        return backup_time_stamp1.strip()

    def third_party_command_restore(
            self, backup_time, version, db_name=None, restore_cycle=False, online=True):
        """
        Uses command line to submit restore job on database

        Args:
            backup_time     (str)       -- backup image timestamp

            version         (Str)       -- db2 application version

            db_name         (str)       -- database name
                default: None

            restore_cycle   (bool)      -- whether to restore entire cycle of backup images or not
                    default: False

            online          (bool)      -- Backup image is online or not
                default: True

        Raises:

            Exception:
                if any issue occurs in triggering the cli restore

        """
        if not db_name:
            db_name = self._database
        for node_num in range(0, len(self.nodes)):
            is_greater = self.compare_db2_versions(version)
            if is_greater:
                num_sessions = 2 if online else 1
                self.log.info(self.load_path)
                if restore_cycle:
                    cmd = (
                        f"export DB2NODE={node_num}; db2 force application all; "
                        f"db2 deactivate db {db_name}; db2 terminate;"
                        f"db2 restore db {db_name} incremental automatic load \"'{self.load_path}'\" "
                        f"open {num_sessions} sessions taken at {backup_time} without prompting")
                else:
                    cmd = (
                        f"export DB2NODE={node_num}; db2 terminate; db2 force application all; "
                        f"db2 deactivate db {db_name}; db2 terminate;"
                        f"db2 restore db {db_name} load \"'{self.load_path}'\" "
                        f"open {num_sessions} sessions taken at {backup_time} without prompting")
                output = self.third_party_command(cmd)
            else:
                if restore_cycle:
                    cmd = (
                        f"export DB2NODE={node_num}; db2 terminate; db2 force application all; "
                        f"db2 deactivate db {db_name}; db2 terminate;"
                        f"db2 restore db {db_name} incremental automatic load \"'{self.load_path}'\" "
                        f" taken at {backup_time} without prompting")
                else:
                    cmd = (
                        f"export DB2NODE={node_num}; db2 terminate; db2 force application all; "
                        f"db2 deactivate db {db_name}; db2 terminate;"
                        f"db2 restore db {db_name} load \"'{self.load_path}'\" "
                        f"taken at {backup_time} without prompting")
                output = self.third_party_command(cmd)

            if (str(output).find("'Restore', 'is', 'successful") or str(
                    output).find("Restore is successful") >= 0) and str(output).find("SQL1035N") < 0:
                self.log.info("CLI restore is successful for node %s:%s", node_num, output)
            else:
                raise Exception(f"CLI restore is not successful for node {node_num}: {output}")

            self.third_party_command_rollforward(db_name=db_name)

    def third_party_command_rollforward(self, db_name=None):
        """
        Uses command line to Rollforward database
        Args:
            db_name (str) -- database name

        Raises:
            Exception:
                if commandline rollforward fails

        """
        if not db_name:
            db_name = self._database
        for node_num in range(0, len(self.nodes)):
            cmd = f"export DB2NODE=0;db2 force application all; db2 deactivate db {db_name};" \
                  f" db2 terminate; db2 \"rollforward db {db_name} to end of logs " \
                  f"on dbpartitionnums ({node_num}) and complete\""
            output = self.third_party_command(cmd)
            if str(output).find("'not', 'pending'") or str(
                    output).find("not pending") >= 0:
                self.log.info("Rollforward was successfull on node %s: %s", node_num, output)
            else:
                raise Exception(f"Rollforward is not successfull on node {node_num}: {output}")

    def third_party_command_recover(self, db_name=None):
        """
        Uses command line to recover database.
        Args:
            db_name (str) -- database name
        Raises:
            Exception:
                If command line recover fails
        """
        self.log.info(self.load_path)
        if not db_name:
            db_name = self._database
        cmd = f"export DB2NODE=0;db2 force application all; db2 deactivate db {db_name};" \
              f" db2 terminate; db2 recover database {db_name}"
        output = self.third_party_command(cmd)
        self.log.info("%s", output)
        if str(output).find("DB20000I") >= 0 > str(output).find("SQL1035N"):
            self.log.info("Recover was successful: %s", output)
        else:
            raise Exception(
                "Recover is not successful: {0}".format(output))

    def db2_archive_log(self, db_name=None, archive_number_of_times=1):
        """
        Uses command line to archive db2 logs.

        Args:
            archive_number_of_times (int)   -- log archival count
            db_name (str) -- database name
        Raises:
            Exception:
                If command line archive log fails
        """
        count = 1
        if not db_name:
            db_name=self._database
        while count <= archive_number_of_times:
            archive_cmd = "{0} archive log for db {1}".format(
                self.db2cmd, db_name)
            self.third_party_command(archive_cmd)
            count += 1

    def db2_cold_backup(self, cold_backup_path, db_name=None):
        """
        Takes DB2 cold backup

        Args:
            cold_backup_path (str) -- path on disk to backup db2 database

            db_name (str) -- database name

        Returns:
            str     -- cold backup image timestamp
            bool    -- true if cold backup is already taken

        Raises:
            Exception:
                if any issue occurs with cold backup
        """
        if not db_name:
            db_name = self._database
        self.log.info("Check if backup is already exists")

        cmd = "touch {0} timestamp.txt".format(cold_backup_path)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)
        self.log.info(cmd_output)
        output = cmd_output.formatted_output
        self.log.info(output)

        if str(output).find("Backup successful") >= 0:
            self.log.info("Cold backup is already taken")
            return True

        self.disconnect_applications(self._database)
        cmd = "{0} backup database {2} on all nodes to \"'{1}'\"".format(
            self.db2cmd, cold_backup_path, db_name)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)
        self.log.info(cmd_output)
        output = cmd_output.formatted_output
        self.log.info(output)
        output = self.third_party_command(cmd)

        if str(output).find("Backup successful") >= 0:
            self.log.info("Cold backup was successful")
        else:
            raise Exception("Cold backup was not successful. Please check")

        output = output.replace(" ", "")
        output = output.replace("\n", "")
        output = output.split(":")
        backup_time_stamp1 = output[1]

        return backup_time_stamp1

    def compare_db2_versions(self, vers1, vers2="10.5.0.8"):
        """
        Helper method that compares versions

        Args:
            vers1 (str) -- db2 application version for the given db2 instance
            vers2 (str) -- db2 application version to compare it with

        Returns:

              (bool)    --  be returns if db2 version is less than version 2

        """
        vers1 = vers1[5:]
        vers1 = vers1.split(".")
        vers1 = int(f"{vers1[0]}{vers1[1]}{vers1[2]}{vers1[3]}")
        vers2 = vers2.split(".")
        vers2 = int(f"{vers2[0]}{vers2[1]}{vers2[2]}{vers2[3]}")

        if vers2 <= vers1:
            self.log.info(
                "----------db2 version is greater than or equal to v10.5fp8------------")
            return True
        return False

    @property
    def instance_port(self):
        return self._port

    @property
    def num_nodes(self):
        return len(self.nodes)

    def set_log_threshold_on_clients(self, threshold):
        """
        updates physical client db2 threshold value

        Args:
            threshold    (int)   --  Threshold value
        """
        for client_object in self.physical_client_objects_list:
            self.log.info("Setting log threshold registry for Client: %s", client_object.display_name)
            client_object.add_additional_setting("Db2Agent", "sDb2ThresholdALFN", "STRING", str(threshold))

    def remove_log_threshold(self):
        """
        Removes log threshold
        """
        for client_object in self.physical_client_objects_list:
            self.log.info("Removing log threshold registry for Client: %s", client_object.display_name)
            client_object.delete_additional_setting("Db2Agent", "sDb2ThresholdALFN")

    def delete_tablespace_file(self, tablespace_name):
        """
        Deletes tablespace files
        tablespace_name (str) -- Tablespace name
        """
        datafiles = self.get_datafile_locations()
        for datafile in datafiles:
            self.machine_db2object.delete_file(f"{datafile}{tablespace_name}_Full.dbf")

    def get_datafile_locations(self):
        """
        Retrieves datafile locations.

        Returns:
            List [str]       --      tablespace locations.

        Raises:
            Exception: if tablespace is not found

        """

        try:
            datafile_locations = []
            for node in self.nodes:
                try:
                    cmd = f"select substr(PATH,1,70) as PATH from sysibmadm.DBPATHS where DBPARTITIONNUM={node} and TYPE ='DBPATH'"
                    self.log.info(cmd)
                    stmt = ibm_db.exec_immediate(self._connection, cmd)
                    datafile_location = ibm_db.fetch_assoc(stmt)
                    self.log.info(datafile_location)
                    for value in datafile_location.values():
                        datafile_locations.append(value.rstrip())
                        self.log.info("Data file Location is: %s", value)
                except Exception as excp:
                    raise Exception(
                    "Failed to get datafile with error: {0}".format(excp))
            return datafile_locations
        except Exception as excp:
            raise Exception(
                "Exception in get_datafile_location: {0}".format(excp))