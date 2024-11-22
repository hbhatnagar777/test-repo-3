# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Exchange Database Agent related operations.

This helper file contains  to create/update subclient and  run backup/restore.

ExchangeDbhelper:

        __init__()                              ---  initializes  Exchange Database helper object

        create_exchdbsubclient()                ---   creates new subclient. if the subcleint
        already exists, it deletes and creates a new one

        update_subclient()                      ---  updates properties of existing subclient

        run_backup()                            ---  Run backup on the testcase subclient

        run_restore_inplace()                   ---  Run in place restore

        run_restore_out_of_place()              ---  Run out of place restore
        
        delete_dbfile()                         ---  Deletes the files & folders in database 
        location
        
        copy_exchange_filenames()               ---  Copying log filenames to a temporary 
        text file

        replace_database_objects()              ---  Replaces the restored content with actual
        database content

        get_db_server_backup_dict()             ---  Gets a dictionary of database names and the
        servers used to back them up

        get_recovery_points()                   ---  Gets the mountpaths and sessionids for
        recovery points

"""
import os
import shutil
from AutomationUtils.constants import LOG_DIR
from cvpysdk.constants import AdvancedJobDetailType

class ExchangeDbHelper(object):
    """class to run exchange database operations """

    def __init__(self, tc_object):
        """Initialize instance of the ExchangeDBHelper class.

        Args:
            tc_object (Object) -- instance of test case class
        """
        self.tc_object = tc_object
        self.testcase_id = self.tc_object.id
        self.log = self.tc_object.log
        self.commcell = self.tc_object.commcell
        self.client = self.tc_object.client
        self.backupset = self.tc_object.backupset
        self.exch_clientname = self.tc_object.tcinputs['ClientName']
        self.storage_policy = self.tc_object.tcinputs['StoragePolicyName']

    def create_exchdbsubclient(self, subclient_name, database_name):
        """
        creates new subclient. if the subcleint already exists, it deletes and creates a new one

        Args:
            subclient_name  (str) -- name of the subclient

            database_name   (list) -- Name of the databases to add as subclient content

        Returns:
            None

        Raises:
            Exception - Any error occurred during Subclient creation
        """
        try:
            self.log.info('Creating Exchange Database SubClient "{0}"'.format(subclient_name))
            self.log.info("Checking if subclient {0} exists.".format(subclient_name))
            subclients_object = self.backupset.subclients
            if subclients_object.has_subclient(subclient_name):
                self.log.info(
                    "Subclient exists, deleting subclient {0}".format(subclient_name)
                    )
                subclients_object.delete(subclient_name)
            self.log.info("Creating subclient {0}".format(
                subclient_name))
            self.tc_object.subclient = (
                subclients_object.add(subclient_name, self.storage_policy))
            self.log.info(database_name)
            self.update_subclient(
                content=database_name)

        except Exception as excp:
            self.log.exception("An error while creating subclient")
            raise excp

    def update_subclient(self, content=None):
        """Updates subclient property of current
            testcase subclient with specified parameters

            Args:
                content (list)              -- content list
                        default: None

            Returns:
                None

            Raises:
                Exception - Any error occurred during Subclient Property update
        """
        try:
            self.log.info("Updating subclient content")
            self.log.info(content)
            if content is not None:
                self.tc_object.subclient.content = content
        except Exception as excp:
            self.log.error(
                'Subclient Update Failed with error: ' + str(excp)
            )
            raise excp

    def run_backup(self,
                   backup_level="Incremental"
                   ):
        """Initiates backup job with specified options
            on the current testcase subclient object
            and waits for completion.

            Args:
                backup_level        (str)   --  level of backup
                        Full / Incremental / Differential
                    default: Incremental

            Returns:
                object - instance of the Job class for this backup job

            Raises:
                Exception - Any error occurred while running backup or
                            backup didn't complete successfully.
        """
        try:
            self.log.info("Starting {0} Backup ".format(backup_level))
            job = self.tc_object.subclient.backup(
                backup_level)
            if job.backup_level is None:
                job_type = job.job_type
            else:
                job_type = job.backup_level
            self.log.info(
                "Waiting for completion of {0} backup with Job ID: {1}".format(
                    job_type, str(job.job_id)
                )
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup {1} with error: {2}".format(
                        job_type, str(job.job_id), job.delay_reason
                    )
                )

            if not job.status.lower() == "completed":
                raise Exception(
                    job_type + " job " + str(job.job_id) + " status"
                    " is not Completed, job has status: " + job.status
                )

            self.log.info(
                "Successfully finished {0} job {1}".format(
                    job_type, str(job.job_id)
                )
            )
            return job

        except Exception as excp:
            self.log.error(
                'Failed to run backup: ' + str(excp)
            )
            raise excp

    def run_restore_inplace(self, db_name, client=None, db_name_2=None):
        """Restores the database specified
            in the input paths list to the same location.

            Args:
                db_name     (str)       -- name of the database

                client      (object)    -- instance of Client class

            Returns:
                object - instance of the Job class for this restore job

            Raises:
                Exception - Any error occurred while running restore or
                            restore didn't complete successfully.
        """
        try:
            self.log.info(db_name)
            self.log.info("Running in place restore")
            subclients_object = self.tc_object._subclient
            if db_name_2 is None:
                path1 = "|Microsoft Information Store\\{0}|#12!|#12!".format(db_name)
            else:
                path1 = "|Microsoft Information Store\\{0}|#12!|Microsoft Information Store\\{1}|#12!".format(
                    db_name,
                    db_name_2
                )
            job = subclients_object.restore_in_place([path1], client)
            self.log.info(
                "Started restore in place job with job id: " + str(job.job_id)
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: " + job.delay_reason
                )

            if not job.status.lower() == "completed":
                raise Exception(
                    "Job status is not Completed, job has status: " + job.status
                )

            self.log.info("Successfully finished restore in place job")
            return job

        except Exception as excp:
            self.log.error(
                'Failed to run in place restore: ' + str(excp)
            )
            raise excp

    def run_restore_out_of_place(self, operation, db_name, dest_path, client=None):
        """Restores the database specified
           in the input paths list to the input client,
           at the specified destination location.

            Args:
                operation   (str)           -- Either to do a out of place with recovery or without recovery

                db_name     (str)           -- Name of the database for which restore has to be done

                dest_path   (str)           -- Path of the restore

                client      (str/object)    -- name of client or instance of client object

            Returns:
                object - instance of the Job class for this restore job

            Raises:
                Exception - Any error occurred while running restore
                            or restore didn't complete successfully.
        """
        try:
            self.log.info("Running out of place restore")
            subclients_object = self.tc_object._subclient
            if operation == "OOP":
                path = ("|Microsoft Information Store\\{0}|#12!Restore to Non-Exchange"
                        " Location <Out Of Place>|#12!{1}".format(
                            db_name, dest_path)
                       )
            elif operation == "OOPWR":
                path = ("|Microsoft Information Store\\{0}|#12!Restore to Non-Exchange"
                        " Location <Out Of Place, No Recover>>|#12!{1}".format(
                            db_name, dest_path)
                       )
            if client is None:
                client = self.exch_clientname
            job = subclients_object.restore_out_of_place(client, [path])
            self.log.info(
                "Started restore OOP job with job id: " + str(job.job_id)
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore OOP job with error: " + job.delay_reason
                )

            if not job.status.lower() == "completed":
                raise Exception(
                    "Job status is not Completed, job has status: " + job.status
                )

            self.log.info("Successfully finished restore OOP job")
            return job

        except Exception as excp:
            self.log.error(
                'Failed to run OOP restore: ' + str(excp)
            )
            raise excp

    def delete_dbfile(self, dest_path):
        """Delete the files and folders present in the database location

        Args:
            dest_path (str)         -   Path of the database location

        Returns:
            None
        
        Raises:
            Exception - Any error occurred deleting files

        """
        try:
            self.log.info("Deleting the files and folders present in the Database location")
            for files in os.listdir(dest_path):
                file_path = os.path.join(dest_path, files)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as excp:
            self.log.error(
                'Failed to delete files in database location: ' + str(excp)
            )
            raise excp

    def copy_exchange_filenames(self, db_path, output_file):
        """Copying log filenames to a temporary text file

        Args:
            db_path (str)       - logfile location of database

            output_file(str)    - output file which constains list of log file names

        Returns:
            output_path (str)   -  Returns the outfilepath which is used in test case
            
        Raises:
            Exception           - Any error occurred while copying filenames

        """
        try:
            output_path = os.path.join(LOG_DIR, output_file)
            self.log.info("Copying log file names and edb file name to a temp file")
            exclude_files = set(["ese.log", "eseutil.log", "exchmem.log"])
            file = open(output_path, 'w')
            onlyfiles = [f for f in os.listdir(db_path) if os.path.isfile(os.path.join(db_path, f))]
            for filenames in onlyfiles:
                if filenames not in exclude_files:
                    if str(filenames).split(".")[-1] == "log":
                        file.write(filenames + "\n")
            file.close()
            return output_path
        except Exception as excp:
            self.log.error(
                'Failed to copy logs files names of database: ' + str(excp)
            )
            raise excp

    def replace_database_objects(self, machine, db_path, database, files):
        """Replaces the restored content with actual database content

                Args:
                    machine             (obj)    - exchange member server machine object

                    db_path             (str)     - path of database on member server

                    database            (str)     - database name

                    files               (list)    - list of files to move



                Raises:
                    Exception           - Any error occurred while replacing database content

        """
        try:
            self.log.info(f'Deleting {database} contents on {machine}')
            machine.remove_directory(db_path)
            self.log.info(f'Creating database folder {db_path} to copy to again')
            machine.create_directory(db_path)
            self.log.info('Copying files from local to client machine')
            for f in files:
                machine.copy_from_local(f, db_path)

        except Exception as excp:
            self.log.error(
                'Failed to copy logs files names of database: ' + str(excp)
            )
            raise excp

    def get_db_server_backup_dict(self, job):
        """Gets a dictionary of database names and the servers used to back them up

                Args:
                    job (object)       - instance of job object

                Returns:
                    dict   -  Returns a dictionary of database backed up on which server

        """

        result = {}
        info_type = AdvancedJobDetailType.BKUP_INFO

        response = job.advanced_job_details(info_type)

        if response['bkpInfo'] is not None:
            response = response['bkpInfo']

            for item in response['exchDbInfo']['SourceDatabaseStats']:
                result[item.get('dbName')] = item.get('ExchangeServerName')

            return result
        else:

            raise Exception('Error fetching dictionary')

    def get_recovery_points(self, client_id, job_ids, instanceId=0, backupSetId=0, subClientId=0, appId=53):
        """Gets the recovery points for an Exchange DAG subclient.

            Args:
                client_id       (object) --     object of client id

                job_ids         (list)   --     list of recovery point job ids

                instanceId      (int)    --     instance id

                backupSetId     (int)    --     backupset id

                subClientId     (int)    --     subclient id

                appId           (int)    --     application id

            Returns:
                mountPaths      -       dict of mountPaths

                rpids           -       dict of recovery pointids

            Raises:
                SDKException:
                    if response is empty

                    if response is not success
        """
        if client_id is None:
            client_id = self.client.client_id
        url = self.client._services['GET_RECOVERY_POINTS'] % (
            client_id,
            instanceId,
            backupSetId,
            subClientId,
            appId
        )
        mountPaths, rpids = {}, {}
        flag, response = self.client._cvpysdk_object.make_request('GET', url)
        if flag:
            if response.json():
                response = response.json()

                if response.get('errorCode', 0) != 0:
                    error_message = response.json()['errorMessage']
                    o_str = 'Failed to fetch details.\nError: "{0}"'.format(error_message)
                    raise Exception(o_str)

                response = response.get('rpObjectList')
                for item in response:
                    if str(item['rpJobId']) in job_ids:
                        mountPaths[item['rpJobId']] = item['mountPath']
                        rpids[item['rpJobId']] = item['id']
                return mountPaths, rpids
            else:
                raise Exception(f'Response: {response}')
        else:
            raise Exception(f'Response: {response}')
