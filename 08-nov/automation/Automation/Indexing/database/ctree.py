# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module which contains the CTree DB class, which is used to perform operation
and retrieve information for the Index DB. Please refer CTreeDB class for more information

CTreeDB: Helper class for CTree engine type index DB/logs in the index cache. It is to manipulate the index db and
logs by performing operations like checkpointing, compaction, reconstruction etc

CTreeDB:

    __init__                    --  Initializes the CTreeDB class.

    get_tables()                --  Allows to read the table records of the index DB. See usage section
    below for an example.

    get_table_path()            --  Returns the table path for the given DB view and component

    get_db_info_prop()          --  Gets one property value from the .dbInfo file of the DB

    get_logs_in_cache()         --  Returns the list of lg folder present in Index cache for the DB

    get_index_db_checkpoints()  --  Returns the list of index checkpoints made for the database

    get_index_db_live_log_checkpoints() -- Returns the list of live logs checkpointed for the DB

    get_rfc_folder_path()       --  Returns the RFC folder path on the RFC server for the job

    refresh()                   --  Refreshes this object by setting the index server client, index cache and all
    other FS paths related to the DB

    checkpoint_db()             --  Checkpoints the DB by running Index backup job.

    compact_db()                --  Compact the DB by running Index backup job.

    prune_db()                  --  Runs index pruning

    delete_db()                 --  Deletes the index DB from index cache

    rename_db()                 --  Renames the index db in index cache

    rename_logs()               --  Renames the index logs folder in index cache

    reconstruct_db()            --  Initiates reconstruction for the DB by renaming it and doing browse operation

    corrupt_db()                --  Corrupts the ArchiveFile table of the DB

    export_db()                 --  Exports the DB to CSV files

    delete_logs()               --  Deletes the action logs of the DB from the index cache

    delete_live_logs()          --  Deletes the live logs folder of the DB from the index cache


CTreeTable: This class is used to work with the CTree table records.

CTreeTable:

    __init__()                  --  Initialize the CTreeTable class

    rows                        --  The rows of the table in list of dictionaries format

    columns                     --  The columns of the table

    get_column()                --  Returns the value from all the rows for the given column name.

    filter_rows()               --  Filters the rows by the given column name and value

    refresh()                   --  Re-exports the index DB and refreshes the table rows and columns


ExportDB: This class uses idxCLI to export the index DB. It can be used to view the entries of the table

ExportDB:

    __init__()                  --  Initializes the ExportDB class

    export()                    --  Exports the CTreeDB to the CSV using IdxCLI to a temporary directory

    view_table()                --  Reads the exported tables and returns a list

    cleanup()                   --  Deletes the directory where the DB is exported

"""

import time
import threading
import re
import xmltodict

from cvpysdk.exception import SDKException

from AutomationUtils import logger
from AutomationUtils.database_helper import get_csdb
from AutomationUtils import machine
from AutomationUtils import commonutils

from Indexing.helpers import IndexingHelpers
from Indexing.tools.idxcli import IdxCLI


class CTreeDB(object):
    """This is a helper class for CTree engine type index DB/logs in the index cache.
    It is to manipulate the index db and logs by performing operations like checkpointing,
    compaction, reconstruction etc.

        Note: Do not use this class directly. Use index_db.get() to create an object.

        Usage:
            >>> from Indexing.database import index_db
            >>> idx_db = index_db.get('<backupset/subclient_pysdk_object>')
            >>> idx_db.compact_db()
            >>> idx_db.reconstruct_db()

    """

    def __init__(self, commcell, index_server, backupset_guid, db_guid, entity_obj):
        """Initializes the CTreeDB class.

            Args:
                commcell     (obj)   --      The CvPySDK commcell object

                index_server (obj)   --      The CvPySDK client object of the DB's index server MA

                backupset_guid (str) --      The backupset GUID of the DB

                db_guid       (str)  --      The DB GUID if the DB

                entity_obj    (obj)  --      The backupset/subclient CvPySDK object for which DB
                is created

            Returns:
                (obj)       -       The CTreeDB object

        """

        self.log = logger.get_log()
        self._commcell = commcell
        self._cs_db = get_csdb()
        self._idx_helper = IndexingHelpers(self._commcell)
        self._entity_obj = entity_obj

        self.backupset_guid = backupset_guid
        self.db_guid = db_guid

        # DB properties
        self.index_cache = None
        self.backupset_path = None
        self.db_path = None
        self.logs_path = None
        self.live_logs_path = None
        self.db_info_file = None
        self.job_stats_file = None
        self.exported_db = None
        self.is_sli = (backupset_guid != db_guid)

        self._index_server = None
        self._ib_clients = {}
        self._ib_jobs_passed = True
        self._idx_cli = None

        # Index server properties
        self.isc_machine = None
        self.isc_delim = None
        self.index_server = index_server

    @property
    def index_server(self):
        """Returns the Index Server CvPySDK client object of the DB"""

        return self._index_server

    @index_server.setter
    def index_server(self, obj):
        """Sets the Index Server client CvPySDK object for the DB

            Args:
                obj     (obj)   --      The CvPySDK object of the Index server client

            Returns:
                None

        """

        self._index_server = obj
        self.refresh()

    @property
    def db_info(self):
        """Returns the .dbInfo file of the DB in a dictionary structure"""

        self.log.info('Reading dbInfo file')

        if self.isc_machine.check_file_exists(self.db_info_file):
            contents = self.isc_machine.read_file(self.db_info_file)
            dbinfo_dict = xmltodict.parse(contents)
            return dbinfo_dict
        else:
            self.log.info('Db info file [{0}] does not exist'.format(self.db_info_file))
            return False

    @db_info.setter
    def db_info(self, value):
        """Saves the .dbInfo file contents to the DB

            Args:
                value     (dict)   --      The dictionary structure of the dbInfo file

            Returns:
                None

        """

        dbinfo_xml = xmltodict.unparse(value)

        self.log.info('Saving dbInfo file with content [{0}]'.format(
            dbinfo_xml
        ))

        self.isc_machine.create_file(self.db_info_file, dbinfo_xml)

    @property
    def db_state(self):
        """Returns the DB state properties from the CS DB"""

        self._cs_db.execute(
            """
                select * from IdxDbState where dbid = (
                    select id from App_IndexDBInfo
                    where backupsetguid = '{0}'
                    and dbname = '{1}'
                )
            """.format(self.backupset_guid, self.db_guid)
        )

        return self._cs_db.fetch_one_row()

    @property
    def db_exists(self):
        """Checks if the DB folder exists in the Index cache.

            Returns:
                True, If the DB folder exists in the index cache.

                False, Otherwise

        """

        return self.isc_machine.check_directory_exists(self.db_path)

    @property
    def index_backup_clients(self):
        """Returns the index backup clients for the DB in dictionary structure

            Returns:
                {
                    'client_name': {
                        'client': <cvpysdk_client_obj>,
                        'subclient': <cvpysdk_subclient_obj>
                    }
                }

        """

        client_names = self._idx_helper.get_index_backup_clients(self._entity_obj)

        for name in client_names:
            if name not in self._ib_clients:
                client_obj = self._commcell.clients.get(name)
                agent_obj = client_obj.agents.get('Big Data Apps')
                bkset_obj = agent_obj.backupsets.get('defaultBackupSet')
                sc_obj = bkset_obj.subclients.get('default')

                self._ib_clients[name] = {
                    'client': client_obj,
                    'subclient': sc_obj
                }

        return self._ib_clients

    @property
    def committed_transaction_id(self):
        """Returns the committed transaction ID for the DB from app_indexdbinfo table"""

        self._cs_db.execute("""
                select committedTransactionId from App_IndexDBInfo where dbName = '{0}'
            """.format(self.db_guid)
        )

        result = self._cs_db.fetch_one_row()

        if result[0]:
            return result[0]
        else:
            return 0

    @property
    def is_upto_date(self):
        """Does browse operation on the DB and checks whether it is up to date or not

            Returns:
                True, If complete browse results are returned without errors by browse.

                False, Otherwise

        """

        attempts = 1
        response = None

        while attempts <= 5:
            self.log.info('Checking upto date status. Attempt [{0}/5]'.format(attempts))
            try:
                dummy_var, response = self._entity_obj.browse({
                    '_raw_response': True
                })
                break
            except Exception as e:
                self.log.error('Browse request timed out/returned error. Error [{0}]'.format(e))
                attempts += 1
                time.sleep(10)
                continue

        if response is None:
            self.log.error('Browse response timed out multiple times')
            return False

        got_full_results = True
        browse_responses = response['browseResponses']
        self.log.info('Browse response {0}'.format(str(browse_responses)))

        for browse_response in browse_responses:
            resp_type = browse_response['respType']

            if resp_type == 2:
                got_full_results = False
                if 'messages' in browse_response:
                    self.log.warning('Got partial results: [{0}]'.format(
                        str(browse_response['messages'])))

            if resp_type == 3:
                got_full_results = False
                if 'messages' in browse_response:
                    self.log.warning('Got error message: [{0}]'.format(
                        str(browse_response['messages'])))

            if resp_type == 0 and got_full_results:
                self.log.info('Browse gave full results. DB is upto date')

        if got_full_results:
            self.log.info('DB is upto date')
            return True

        self.log.warning('DB is not yet upto date')
        return False

    @property
    def idx_cli(self):
        if self._idx_cli is None:
            self.log.info('Initializing idxCLI')
            self._idx_cli = IdxCLI(self.index_server)

        return self._idx_cli

    def _parallel_checkpoint(self, sc_obj):
        """Initiates index backup jobs in parallel for the DB"""

        try:

            job_obj = self._idx_helper.run_index_backup(sc_obj)

            self.log.info(
                'Index backup job [{0}] completed for index backup client [{1}]'.format(
                    job_obj.job_id, sc_obj._client_object.client_name
                ))

            if not self._idx_helper.verify_checkpoint(job_obj.job_id, self.db_guid):
                self._ib_jobs_passed = False

        except Exception as e:
            self.log.error('Failed to run index backup job [%s]', e)
            self._ib_jobs_passed = False

    def _set_registry_keys(self, reg_dict):
        """Sets Indexing registry keys given in the dict on the index server machine"""

        for key, val in reg_dict.items():
            self.log.info('Setting registry key [{0}={1}]'.format(key, val))
            self.isc_machine.create_registry('Indexing', key, val, 'DWord')

    def _delete_registry_keys(self, reg_dict):
        """Deletes the indexing registry keys on the index server machine"""

        for key in reg_dict:
            self.log.info('Deleting registry key [{0}]'.format(key))
            try:
                self.isc_machine.remove_registry('Indexing', key)
            except Exception as e:
                self.log.error('Failed to delete registry key [%s]. Error [%s]', key, e)

    def get_table(self, view=None, component=None, table='archiveFileTable'):
        """Allows to read the table records of the index DB. See usage section below for an example.

            Args:
                view        (str)   --  The name of the DB view

                component   (str)   --  The name of the component under the DB view

                table       (str)   --  The name of the table under the component without
                any extension (case insensitive)

            Returns:
                (obj) - The CTreeTable class object

            Usage:
                >>> from Indexing.database import index_db
                >>> test_db = index_db.get('<backupset/subclient>_obj')
                >>>
                >>> afile_table = test_db.get_table(table='archiveFileTable')
                >>> afile_table.rows  # Gets all the rows in the table
                >>> afile_table.get_columns('AFileID')  # Gets all the afile IDs in the table.
                >>>
                >>> afile_table.refresh()  # Re-exports the index DB with latest changes
                >>> afile_table.rows
                >>>
                >>> test_db.exported_db.cleanup()  # Delete the exported DB's CSV files

        """
        return CTreeTable(self, view, component, table)

    def get_table_path(self, view=None, component='default', table='VersionTable.dat'):
        """Returns the table path for the given DB view and component

            Args:
                view        (str)   --      The view name of the DB

                component   (str)   --      The component name under the view

                table       (str)   --      The table name under the component

            Returns:
                (str)       -       The FS path of the required table

        """

        path_list = [self.db_path, view, component, table]

        if view is None:
            path_list.pop(1)
            path_list.pop(1)

        return self.isc_delim.join(path_list)

    def get_db_info_prop(self, property_name):
        """Gets one property value from the .dbInfo file of the DB

            Args:
                property_name     (str)   --    The property of the DB for which value is required

            Returns:
                (str)       -       The value of the property

        """

        db_info = self.db_info
        attr_name = '@' + property_name

        if not isinstance(db_info, dict):
            self.log.error('Invalid dbInfo file')
            return False

        if attr_name in db_info['Indexing_DbProps']:
            prop_val = db_info['Indexing_DbProps'][attr_name]
            self.log.info('DBInfo {0} = {1}'.format(attr_name, prop_val))
            try:
                return int(prop_val)  # Return integer if possible
            except ValueError:
                return prop_val
        else:
            self.log.error('{0} is not present in dbInfo file [{1}]'.format(
                attr_name, str(db_info)
            ))
            return False

    def get_logs_in_cache(self, job_id_only=False):
        """Returns the list of lg folder present in Index cache for the DB

            Args:
                job_id_only     (bool)      --      Returns job ID only instead of J<job_id>

            Returns:
                (list)      -       List of job log folders. J<job_id> if job_id_only is False

        """

        all_dirs = self.isc_machine.get_folders_in_path(self.logs_path)
        job_logs = []

        for log_dir in list(all_dirs):
            match = re.search('J[0-9_a-zA-Z]+', log_dir)
            if match is not None:
                mid = match.group(0)

                if job_id_only:
                    mid = re.search('[0-9]+', mid).group(0)

                if mid not in job_logs:
                    job_logs.append(mid)

        return job_logs

    def get_index_db_checkpoints(self):
        """Returns the list of index checkpoints made for the database"""

        self._cs_db.execute("""
            select * from archFile
            left join App_IndexCheckpointInfo ici on ici.afileId = archfile.id
            where name like '%{0}%'
            order by archFile.id asc
        """.format(self.db_guid))

        return self._cs_db.fetch_all_rows(named_columns=True)

    def get_index_db_live_log_checkpoints(self):
        """Returns the list of live logs checkpointed for the DB"""

        self._cs_db.execute("""
            select * from archFile where name like 'IdxLiveLogs%{0}%'
        """.format(self.db_guid))

        return self._cs_db.fetch_all_rows(named_columns=True)

    def get_rfc_folder_path(self, rfc_server_machine,  job_id):
        """ RFC folder path of a job on it's rfc server
            Args:
                    rfc_server_machine (obj)   --    rfc server of the job

                    job_id             (int)   --   Job id of the backup job who's RFC folder path is needed

                Returns:
                    (str)      --      Path of the RFC folder for a given job
        """
        rfc_ma = self._commcell.media_agents.get(rfc_server_machine.machine_name)
        rfc_folder_path_for_job = rfc_server_machine.join_path(rfc_ma.index_cache_path, 'RemoteFileCache',
                                                       str(self._commcell.commcell_id), self.db_guid,
                                                       job_id)
        self.log.info('RFC folder path for the job: %s is %s', job_id, rfc_folder_path_for_job)

        return rfc_folder_path_for_job

    def refresh(self):
        """Refreshes this object by setting the index server client, index cache and
        all other FS paths related to the DB"""

        self.log.info('Refreshing IndexServer and IndexCache paths for the DB')

        self.isc_machine = machine.Machine(self._index_server.client_name, self._commcell)
        self.isc_delim = self.isc_machine.os_sep
        self.index_cache = self._idx_helper.get_index_cache(self._index_server)

        self.backupset_path = self.isc_delim.join([
            self.index_cache, 'CvIdxDB', self.backupset_guid
        ])

        self.db_path = self.isc_delim.join([
            self.backupset_path, self.db_guid
        ])

        self.logs_path = self.isc_delim.join([
            self.index_cache, 'CvIdxLogs', str(self._commcell.commcell_id), self.backupset_guid
        ])

        self.live_logs_path = self.isc_delim.join([
            self.index_cache, 'CvIdxLiveLogs', self.backupset_guid
        ])

        self.db_info_file = self.isc_delim.join([
            self.db_path, '.dbInfo'
        ])

        self.job_stats_file = self.isc_delim.join([
            self.db_path, 'JobStats.csv'
        ])

        self.log.info('***** Index DB details *****')
        self.log.info('Index server: [%s]', self.index_server.client_name)
        self.log.info('Index DB path: [%s]', self.db_path)
        self.log.info('Index logs path: [%s]', self.logs_path)
        self.log.info('Index level is SLI: [%s]', self.is_sli)

    def checkpoint_db(self, by_all_index_backup_clients=True, registry_keys=None):
        """Checkpoints the DB by running Index backup job.

            Args:
                by_all_index_backup_clients     (bool)   --    Decides whether to run index backup
                jobs for all the clients involved for the entity

                registry_keys  (dict/bool)  --   If (bool) and false, no registry keys will be
                                                set before running the operation

                                            --   If (dict), the registry keys in the dictionary
                                                 will be set

            Returns:
                (bool)      --      True, if checkpoint is launched and verified

                                    False, if checkpoint job did not start or verification failed

        """

        self._delete_registry_keys({
            'CHKPOINT_AFILES_AGED_MIN': 0,
            'COMPACTION_ENFORCE_DAYS': 0,
            'FULL_COMPACTION_MIN_PERCENT_AFILE_AGED': 0
        })

        checkpoint_reg_keys = {
            'CHKPOINT_ITEMS_ADDED_MIN': 0,
            'CHKPOINT_MIN_DAYS': 0
        }

        if isinstance(registry_keys, dict):
            commonutils.set_defaults(checkpoint_reg_keys, registry_keys)

        self.log.info('DB Info: [%s]', self.db_info)

        try:

            if not isinstance(registry_keys, bool) or registry_keys:
                self.log.info('Setting registry keys to force checkpoint DB')
                self._set_registry_keys(checkpoint_reg_keys)

            all_ib_clients = self.index_backup_clients
            ib_clients = {}

            if by_all_index_backup_clients:
                ib_clients = all_ib_clients
            else:
                ib_client = next(iter(all_ib_clients))
                ib_clients[ib_client] = all_ib_clients[ib_client]

            self.log.info('Selected Index backup clients are [{0}]'.format(
                str(ib_clients)
            ))

            threads = []
            self._ib_jobs_passed = True

            for ib_client, prop in ib_clients.items():
                sc_obj = prop['subclient']
                exe_thread = threading.Thread(
                    target=self._parallel_checkpoint,
                    args=(sc_obj,)
                )
                exe_thread.start()
                threads.append(exe_thread)
                time.sleep(60)

            for exe_thread in threads:
                exe_thread.join()

            if self._ib_jobs_passed:
                self.log.info('Index backup jobs completed successfully')
                return True
            else:
                self.log.error('One or more index backup/verification failed')
                return False

        finally:
            self._delete_registry_keys(checkpoint_reg_keys)

    def compact_db(self, registry_keys=None, total_attempts=3):
        """Compact the DB by running Index backup job.

            Args:
                registry_keys  (dict/bool)  --   If (bool) and false, no registry keys will be
                                                set before running the operation

                                            --   If (dict), the registry keys in the dictionary
                                                 will be set

                 total_attempts (int)       --   The number of attempts to take to check if
                                                 compaction has happened

            Returns:
                (bool)      --      True, if index backup job is launched and compaction completed

                                    False, if index backup job is not launched or compaction
                                    did not start

        """

        if ((self.is_sli and self.get_db_info_prop('checkpointDb') == 1)
                or self.get_db_info_prop('lastCheckPointTime') == 0):
            self.log.info('CheckpointDB flag is set or lastCheckpointTime is 0. Hence checkpointing DB first')
            self.checkpoint_db()

        self._delete_registry_keys({
            'CHKPOINT_ITEMS_ADDED_MIN': 0,
            'CHKPOINT_MIN_DAYS': 0,
            'CHKPOINT_ENFORCE_DAYS': 0,
            'CHKPOINT_ENFORCE_DAYS_UNCONDITIONALLY': 0
        })

        compaction_reg_keys = {
            'CHKPOINT_AFILES_AGED_MIN': 0,
            'COMPACTION_ENFORCE_DAYS': 0,
            'FULL_COMPACTION_MIN_PERCENT_AFILE_AGED': 0
        }

        if isinstance(registry_keys, dict):
            commonutils.set_defaults(compaction_reg_keys, registry_keys)

        self.log.info('DB Info: [%s]', self.db_info)

        try:

            self.log.info('Running compaction for DB')

            last_compaction_time = self.get_db_info_prop('lastCompactionTime')

            if last_compaction_time is False:
                self.log.error('Failed to get last compaction time for DB')
                return False

            self.log.info('Last compaction time for DB is [{0}]'.format(last_compaction_time))

            if not isinstance(registry_keys, bool) or registry_keys:
                self.log.info('Setting registry keys to force run compaction')
                self._set_registry_keys(compaction_reg_keys)

            ib_clients = self.index_backup_clients
            ib_client = next(iter(ib_clients))  # Get one index backup client

            self.log.info('Picked index backup client [{0}] to run Index backup job'.format(
                ib_client
            ))

            ib_subclient_obj = ib_clients[ib_client]['subclient']
            job_obj = self._idx_helper.run_index_backup(ib_subclient_obj)

            if not job_obj.job_id:
                self.log.error('Cannot start index backup job for the DB')
                return False

            self.log.info(
                'Index backup job [{0}] completed. Waiting for compaction to complete'.format(
                    job_obj.job_id
                ))

            compaction_check_attempts = 1
            new_compaction_time = 0

            while compaction_check_attempts <= total_attempts:
                self.log.info(
                    'Waiting 60 secs for compaction to complete. Attempt [{0}/{1}]'.format(
                        compaction_check_attempts, total_attempts
                    ))
                time.sleep(60)

                new_compaction_time = self.get_db_info_prop('lastCompactionTime')

                if new_compaction_time == last_compaction_time:

                    if compaction_check_attempts == total_attempts:
                        self.log.error('Attempts exhausted. Compaction did not run for the DB')
                        return False
                    else:
                        compaction_check_attempts += 1

                    self.log.warning(
                        'New compaction time is same as old compaction time.'
                    )
                else:
                    break

            self.log.info('Compaction completed for DB. New compaction time [{0}]'.format(
                new_compaction_time
            ))

            return True

        finally:
            self._delete_registry_keys(compaction_reg_keys)

    def prune_db(self, total_attempts=2):
        """Runs index pruning

            Args:
                 total_attempts (int)    --   The number of attempts to try pruning
                                              (new subclients take atleast 2 attempts)

            Returns:
                (bool)    --    True, if pruning was successful, else False

            Raises:
                Exception:
                    If index checkpoint or compaction fails

        """

        self.log.info('********* Running index pruning. *********')

        last_db_prune_time = self.get_db_info_prop('dbPruneTime')
        for attempt_number in range(1, total_attempts + 1):

            self.log.info(f'*********** Index pruning attempt: {attempt_number}/{total_attempts} ***********')
            self.log.info(f'Last dbPruneTime: {last_db_prune_time}')

            if not self.checkpoint_db(by_all_index_backup_clients=False, registry_keys=True):
                raise Exception('Checkpoint index failed for pruning.')
            if not self.compact_db(registry_keys=True):
                raise Exception('Compact index failed for pruning.')

            curr_db_prune_time = self.get_db_info_prop('dbPruneTime')
            self.log.info(f'Updated dbPruneTime: {curr_db_prune_time}')

            if curr_db_prune_time != last_db_prune_time:
                return True

        return False

    def delete_db(self):
        """Deletes the index DB from index cache"""

        self.idx_cli.do_delete_index_db(self.backupset_guid, self.db_guid)
        return True

    def rename_db(self):
        """Renames the index db in index cache

            Returns:
                (str)   --      The new path of the renamed DB

        """

        rename_path = self.backupset_path + '_' + str(int(time.time()))
        self.isc_machine.rename_file_or_folder(
            self.backupset_path, rename_path
        )
        return rename_path

    def rename_logs(self):
        """Renames the index logs folder in index cache

            Returns:
                (str)   --      The new path of the renamed index logs

        """

        rename_path = self.logs_path + '_' + str(int(time.time()))
        self.isc_machine.rename_file_or_folder(
            self.logs_path, rename_path
        )
        return rename_path

    def reconstruct_db(self, rename=True, total_browse_attempts=3, delete_logs=False):
        """Initiates reconstruction for the DB by renaming it and doing browse operation

            Args:
                rename      (bool)      --      Decides whether to rename/delete the DB

                total_browse_attempts (int)  -- The total number of browse attempts to be made
                to check if reconstruction is successful

                delete_logs (bool)      --      Decides whether to rename/delete the index logs

            Returns:
                (bool)      --      True, if reconstruction was initiated and browse verified
                                    that DB is upto date

                                    False, if reconstruction was not initiated or DB is stuck
                                    in not upto data state

        """

        self.log.info('Reconstructing DB')

        if rename:
            rename_path = self.rename_db()
            self.log.info('Renamed DB to [{0}]'.format(rename_path))
            if delete_logs:
                renamed_logs = self.rename_logs()
                self.log.info(f'Renamed index logs to [{renamed_logs}]')
        else:
            self.log.info('Deleting DB [{0}]'.format(self.db_path))
            self.delete_db()
            if delete_logs:
                self.log.info(f'Deleting index logs [{self.logs_path}]')
                self.delete_logs('all')

        self.log.info('Shutting down index server after delete/rename operation')
        self.idx_cli.do_tools_shutdown_index_server()

        browse_attempt = 1
        upto_date = False

        while browse_attempt <= total_browse_attempts:

            self.log.info(
                'Doing browse to trigger reconstruction for DB and '
                'check browse status. Attempt [{0}/{1}]'.format(
                    browse_attempt, total_browse_attempts
                ))

            upto_date = self.is_upto_date

            if upto_date:
                break

            if browse_attempt == total_browse_attempts:
                self.log.error(
                    'Attempts exhausted, browse still does not give full results')
                upto_date = False
                break
            else:
                browse_attempt += 1
                self.log.error('DB is not upto date. Waiting for 60 secs and trying again')
                time.sleep(60)
                continue

        if upto_date:
            self.log.info('DB is upto date. Reconstruction completed')
            return True
        else:
            self.log.error('DB is not upto date. Reconstruction failed')
            return False

    def corrupt_db(self):
        """Corrupts the ArchiveFile table of the DB

            Returns:
                (bool)      --      True, if DB was corrupted

                                    False, if DB corruption failed

        """

        afile_table = self.get_table_path(table='ArchiveFileTable.dat')

        try:
            self.log.info('Corrupting afile table [{0}]'.format(afile_table))
            self.isc_machine.create_file(afile_table, 'Corrupted afile table')
            return True

        except Exception:
            self.log.error('Failed to corrupt afile table')
            return False

    def export_db(self):
        """Exports the DB to CSV files.

            Note:
                To work with the tables, please use CTreeDB.get_tables() instead of this

            Returns:
                ExportTables (obj) to view the table entries
        """

        if self.exported_db is None:
            self.exported_db = ExportDB(self)

        return self.exported_db

    def delete_logs(self, action='all'):
        """Deletes the action logs of the DB from the index cache

            Args:
                action      (str)   --  If value is starts with J, it is considered a job id and
                that job folder is deleted from index cache

                                        If value is "all" all the logs of the DB will be deleted

            Returns:
                (bool)      --      True, if deletion is successful

                                    False, if deletion failed

        """

        try:
            if action == 'all':
                self.log.info('Deleting all logs for the DB from Index cache')
                self.isc_machine.remove_directory(self.logs_path)

            elif action.startswith('J'):
                job_logs_path = self.isc_delim.join([
                    self.logs_path, action
                ])
                self.log.info('Deleting jobs logs directory [{0}]'.format(job_logs_path))
                self.isc_machine.remove_directory(job_logs_path)

            else:
                self.log.error('Unsupported action to delete logs [{0}]'.format(action))
                return False

            return True

        except Exception:
            self.log.error('Failed to delete log from Index cache')
            return False

    def delete_live_logs(self):
        """Deletes the live logs folder of the DB from the index cache

            Returns:
                (bool)      --      True, if deletion is successful

                                    False, if deletion failed

        """

        try:
            self.log.info('Deleting live logs folder [{0}]'.format(self.live_logs_path))
            self.isc_machine.remove_directory(self.live_logs_path)
            return True
        except Exception as e:
            self.log.error('Failed to delete live logs folder [{0}]'.format(e))
            return False


class CTreeTable(object):
    """This class is used to work with the CTree table records. Use CTreeDB.get_table() to work with this class."""

    def __init__(self, db_obj: CTreeDB, view, component, table):
        """Initialize the CTreeTable class

            Args:
                db_obj      (obj)   --  The CTreeDB object

                view        (str)   --  The view name of the table

                component   (str)   --  The component name of the table

                table       (str)   --  The name of the table without extension
        """

        self.db_obj = db_obj
        self._view = view
        self._component = component
        self._table = table

        self._rows = None
        self._columns = None

        self.db_obj.export_db()

    @property
    def rows(self):
        """The rows of the table in list of dictionaries format"""

        if self._rows is None:
            self._rows = self.db_obj.exported_db.view_table(self._view, self._component, self._table)

        return self._rows

    @property
    def columns(self):
        """The columns of the table"""

        if self._columns is None:
            row_count = len(self.rows)
            if row_count == 0:
                return []
            else:
                first_row = self.rows[0]
                self._columns = list(first_row.keys())

        return self._columns

    def get_column(self, column):
        """Returns the value from all the rows for the given column name. Use IdxGUI on the MA to view the
        columns supported for every table.

            Args:
                column      (str)   --  The name of the column (case sensitive)

            Returns:
                List - List of column values

        """

        if column not in self.columns:
            raise Exception('Invalid column name provided [{0}]'.format(column))

        values = []
        for row in self.rows:
            if column in row:
                values.append(row[column])

        return values

    def filter_rows(self, column, value):
        """Filters the rows by the given column name and value

            Args:
                column      (str)   --  The name of the column to be filtered

                value       (str)   --  The value to be column

            Returns:
                List(Dict) - The rows matching the given column and its value

        """

        if column not in self.columns:
            raise Exception('Invalid column name provided [{0}]'.format(column))

        filtered_rows = []
        for row in self.rows:
            if column in row:
                if str(row[column]) == str(value):
                    filtered_rows.append(row)

        return filtered_rows

    def refresh(self):
        """Re-exports the index DB and refreshes the table rows and columns"""

        self.db_obj.exported_db.cleanup()
        self.db_obj.exported_db.export()
        self._rows = None
        self._columns = None


class ExportDB(object):
    """This class uses idxCLI to export the index DB. It can be used to view the entries of the table

        Note:
             Do not use this class directly, instead use the CTreeDB.export_db() to use this class

    """

    def __init__(self, db_obj: CTreeDB):
        """Initializes the ExportDB class

            Args:
                db_obj      (obj)   --      The CTreeDb object. Refer usage above for more instructions.

        """

        self.db_obj = db_obj
        self.exported_tables = None
        self.export_dir = None
        self.export()

    def export(self):
        """Exports the CTreeDB to the CSV using IdxCLI to a temporary directory

            Returns:
                None

            Raises:
                Exception when no table is exported.

        """

        self.export_dir = self.db_obj.isc_delim.join([
            self.db_obj.index_cache, 'Temp', 'automation_export'
        ])

        current_dir = self.db_obj.isc_delim.join([
            self.export_dir, commonutils.get_random_string(4)
        ])

        self.db_obj.log.info('Shutting down IndexServer before export operation')
        self.db_obj.idx_cli.do_tools_shutdown_index_server()
        time.sleep(30)

        self.db_obj.log.info('Exporting DB to CSV to directory [{0}]'.format(current_dir))
        self.exported_tables = self.db_obj.idx_cli.do_table_export_all_tables(self.db_obj.db_path, current_dir)

        self.db_obj.log.info('Exported tables [{0}]'.format(self.exported_tables))

        if not self.exported_tables:
            raise Exception('No table is exported')

    def view_table(self, view=None, component=None, table='archiveFileTable'):
        """Reads the exported tables and returns a list

            Args:
                view        (str)   --  The name of the DB view

                component   (str)   --  The name of the component under the DB view

                table       (str)   --  The name of the table under the component without
                any extension (case insensitive)

            Returns:
                (list(Dict))      --      List of dictionaries which are the records of the table.

            Usage:
                >>> img_table = export_obj.view_table(table='imagetable')  # Pass table name alone to view root table
                >>> version_table = export_obj.view_table(view='default', component='default', table='versiontable')
                >>>
                >>> for record in version_table:
                >>>     # Refer column names using idxGUI for the respective table (case sensitive)
                >>>     print(record['JobId'])

            Raises:
                Exception if incorrect view/table/component name provided

        """

        if table is None:
            raise Exception('No table name provided !')

        if view is not None and component is None:
            raise Exception('No component name is provided when view name is provided')

        table_name = table.lower() + '.csv'
        if view is None:
            table_path = [table_name]
        else:
            table_path = [view, component, table_name]

        table_path = self.db_obj.isc_delim.join(table_path)
        self.db_obj.log.info('Reading exported table CSV [{0}]'.format(table_path))

        if table_path in self.exported_tables:
            full_path = self.exported_tables[table_path]
            results = self.db_obj.isc_machine.read_csv_file(full_path)
            return self._clean_result(results)
        else:
            raise Exception('Table path does not exist in the exported list')

    def cleanup(self):
        """Deletes the directory where the DB is exported

            Returns:
                None

        """

        self.db_obj.log.info('Deleting the exported files [{0}]'.format(self.export_dir))
        self.db_obj.isc_machine.remove_directory(self.export_dir)

    @staticmethod
    def _clean_result(results_raw):
        """Trims the column name and values from the raw CSV table result"""

        results = []
        for row in results_raw:
            new_row = {}
            for column in row:
                val = row[column]
                column = column.strip()
                if column:
                    new_row[column] = val.strip()
            results.append(new_row)

        return results
