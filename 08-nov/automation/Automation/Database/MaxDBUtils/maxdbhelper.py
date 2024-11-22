"""Helper file for performing MaxDB operations

MaxDBHelper is the only class defined in this file

MaxDBHelper: Helper class to perform MaxDB operations

MaxDBHelper:
============
    __init__()                          --  initializes MaxDBHelper object.

    maxdb_server_operation()            --  Method to perform MaxDB operation on server.

    get_backint_medium_name()           --  Method to get MaxDB medium names to run backups.

    make_dbadmin()                      --  This method makes database to admin mode
    to run/backups and restores

    make_dbonline()                     --  This method makes database to online state
    to run/backups and restores

    run_offline_backups()               --  This method helps in running backups in offline mode.

    run_online_backups()                --  This method helps in running backups in online mode.

    create_and_validate_data()          --  This method creates, appends and verifies data for maxdb instance


"""
from AutomationUtils import logger, constants
from AutomationUtils import machine


class MaxDBHelper(object):
    """Helper class to perform MaxDBHelper operations"""

    def __init__(
            self,
            commcell,
            instance,
            hostname,
            dbmclipath,
            user_name,
            password,
            dba_user,
            dba_password):
        """Initialize the MaxDB object.

            Args:
                commcell        (obj)  --  Commcell object

                instance        (obj)  --  instance object

                hostname        (str)  --  Hostname of the client machine

                dbmclipath      (str)  --  dbmclipath contains commands required to run backup and restores

                user_name       (str)  --  user_name is used to perform administrator tasks like backups
                                           and restore.

                password        (str)  --  password is used to perform administrator tasks like backups
                                           and restores.

                dba_user        (str)  --  The DBA user creates/verifies data on the MaxDB instance

                dba_password    (str)  --  The DBA password creates/verifies data on the MaxDB instance

            Returns:
                object - instance of MaxDBHelper class

        """
        self._hostname = hostname
        self._commcell = commcell
        self._instance = instance
        self.user_name = user_name
        self.password = password
        self.dba_user = dba_user
        self.dba_password = dba_password
        self.dbmclipath = dbmclipath
        self.machine_object = machine.Machine(
            self._hostname, self._commcell)
        self.log = logger.get_log()
        self.data = {
            'DBMCLIPATH': self.dbmclipath,
            'USERNAME': self.user_name,
            'PASSWORD': self.password,
            'DBA_USER': self.dba_user,
            'DBA_PASSWORD': self.dba_password,
            'FULL_MEDIUM': 'Temp_medium',
            'INC_MEDIUM': 'Temp_medium',
            'LOG_MEDIUM': 'Temp_medium',
            'INSTANCE': self._instance,
            'OPERATION': 'NOT SET'
        }

    def maxdb_server_operation(self, operation):
        """ Method to perform MaxDB server specific operations\
                    like get status/change status/ start backup restore.
            Args:
                operation (str) -- operation is the dbmcli cmd argument to perform database task

            Returns:
                str - string is returned based of execution of dbmcli command on MaxDB server
        """
        try:
            if "windows" in self.machine_object.os_info.lower():
                self.data['OPERATION'] = operation
                output = self.machine_object.execute_script(
                    constants.WINDOWS_MAXDB_SERVER_OPERATIONS,
                    self.data)
                return output.formatted_output
            else:
                self.data['OPERATION'] = operation
                output = self.machine_object.execute_script(
                    constants.UNIX_MAXDB_SERVER_OPERATIONS,
                    self.data)
                return output.formatted_output
        except Exception:
            raise Exception("Unable to run max db server operation")

    def maxdb_data_operation(self, cmd):
        """ This method performs data creation or validation operations using the
        sdbfill command to create or validate data

        Args:
                cmd (str) -- cmd is the dbmcli cmd argument to perform database task

            Returns:
                str - string is returned based of execution of dbmcli command on MaxDB server
        """
        try:
            if "windows" in self.machine_object.os_info.lower():
                self.data['OPERATION'] = cmd
                output = self.machine_object.execute_script(
                    constants.WINDOWS_MAXDB_DATA_OPERATIONS,
                    self.data)
                return output.formatted_output
            else:
                self.data['OPERATION'] = cmd
                output = self.machine_object.execute_script(
                    constants.UNIX_MAXDB_DATA_OPERATIONS,
                    self.data)
                return output.formatted_output
        except Exception:
            raise Exception("Unable to run maxdb data creation or validation")

    def get_backint_medium_name(self):
        """
            This function gets backint medium for all data and log backups

        """
        try:
            output = self.maxdb_server_operation('get_medium')
            mediums = output.split('/')
            if len(mediums) == 3:
                self.data['FULL_MEDIUM'] = mediums[0]
                self.data['INC_MEDIUM'] = mediums[1]
                self.data['LOG_MEDIUM'] = mediums[2]
        except Exception:
            raise Exception("Unable to get medium names for backup")

    def make_dbadmin(self):
        """
            This function Changes database state to admin mode,
            this make database ready for offline backup and restores

            Returns:
                str - Ok is returned after the command is completed.
        """
        try:
            output = self.maxdb_server_operation('db_admin')
            return output
        except Exception:
            raise Exception("Unable to change db state to admin mode")

    def make_dbonline(self):
        """
            This function Changes database state to online mode,
            this make database ready for online backup and restores

            Returns:
                str - Ok is returned after the command is completed.
        """
        try:
            output = self.maxdb_server_operation('db_online')
            return output
        except Exception:
            raise Exception("Unable to change db state to online mode")

    def run_offline_backups(self, backup_type):
        """
            This function is used to run database backups in admin mode.

            Args:
                backup_type (str) -- Specifies offline backup type job which needs to performed on MaxDB server

        """
        try:
            self.get_backint_medium_name()
            db_state = self.make_dbadmin()
            if db_state.lower() == 'ok':
                if "full" in backup_type.lower():
                    self.log.info("Full backup will be launched for maxdb instance ")
                    output = self.maxdb_server_operation('offline_full')
                elif "inc" in backup_type.lower():
                    self.log.info("Incremental backup will be launched for maxdb instance ")
                    output = self.maxdb_server_operation('offline_inc')
                else:
                    self.log.info("backup type is not specified correctly")
            else:
                self.log.info("Unable to change database status to admin mode")
        except Exception:
            raise Exception("Unable to run backup job for MaxDB instance")

    def run_online_backups(self, backup_type):
        """
            This function is used to run database backups in online mode.

            Args:
                backup_type (str) -- Specifies online backup type job which needs to performed on MaxDB server
        """
        try:
            self.get_backint_medium_name()
            db_state = self.make_dbonline()
            if db_state.lower() == 'ok':
                if "full" in backup_type.lower():
                    self.log.info("Full backup will be launched for maxdb instance ")
                    output = self.maxdb_server_operation('online_full')
                elif "inc" in backup_type.lower():
                    self.log.info("Incremental backup will be launched for maxdb instance ")
                    output = self.maxdb_server_operation('online_inc')
                else:
                    self.log.info("log backup will be launched for maxdb instance")
                    output = self.maxdb_server_operation('log_backup')
        except Exception:
            raise Exception("Unable to run backup job for MaxDB instance")

    def create_and_validate_data(self, optype, startrecordcount, finishrecordcount):
        """
            This method is used to create/append data to maxdb instance.

            Args:
                optype (str) -- Specifies create/append and check for sdbfill command

                startrecordcount(int) -- Initial value for data manipulation

                finishrecordcount(int) -- End value for data manipulation

        """
        try:
            cmd = ("sdbfill {0} {1} {2} {3}"
                   " 10000 0 {4} {5} {6} ".format(self._instance, optype,
                                                  str(startrecordcount),
                                                  str(finishrecordcount),
                                                  self.dba_user, self.dba_password, self._hostname))
            output = self.maxdb_data_operation(cmd)
        except Exception:
            raise Exception("Unable to create data for MaxDB instance")

    def getbackupextids(self, bkpmedium):
        """
              This method returns valid Backup Extids for restore.

              Args:
                bkpmedium (str) -- backup medium name is verified in the last job

              Returns:
                str - ext backup ids are returned

        """
        try:
            operation = 'GetBackupExtIDs'
            output = self.maxdb_server_operation(operation)
            file_cnt = self.machine_object.read_file(output)
            lines = file_cnt.splitlines()
            last_str = lines[-1]
            bkp_id = last_str.split('|')[0]
            bkp_extid = None
            if bkpmedium.casefold() in last_str.casefold():
                self.log.info("Backup job details are updated in dbm.ebf file")
                validlines = []
                for extid in lines:
                    if bkp_id in extid:
                        validlines.append(extid.rsplit('|')[2])
                bkp_extid = ', '.join(validlines)
            return bkp_extid
        except Exception:
            raise Exception("Unable to return valid backup extids ")

    # noinspection SpellCheckingInspection
    def recoverdata(self, recovertype, recoverop, backupextid):
        """
            This method performs restore for maxbd instance

            Args:
                recovertype (str) -- Specifies recovery type either recover_start/recover_replace

                recoverop(str) -- Specifies type of the restore which is being beformed.

                backupextid(str) -- Specifies restore the pipe name which is being restored.
        """
        try:
            cmd = "dbmcli -d {0} -u {1),{2} -uUTL -c ".format(self._instance, self.user_name, self.password)
            if recoverop.lower() == "start":
                cmd = "recover_start "
            if recoverop.lower() == "replace":
                cmd += "recover_replace "
            if recovertype.casefold() == "full":
                cmd += "{0} ExternalBackupID \" {1}\" ".format(self.data['FULL_MEDIUM'], backupextid)
            if recovertype.casefold() == "inc":
                cmd += "{0} ExternalBackupID \" {1}\" ".format(self.data['INC_MEDIUM'], backupextid)
            if recovertype.casefold() == "log":
                cmd += "{0} ExternalBackupID \" {1}\" ".format(self.data['LOG_MEDIUM'], backupextid)
            output = self.maxdb_data_operation(cmd)
        except Exception:
            raise Exception("Unable to  perform {0} restore ". format(recoverop))
