# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for index server related operations

    IndexServerHelper:

        __init__()                              --      initialize the IndexServerHelper class

        _validate_cores_size_unix               --      Validates whether the size of each core in the core list matches between browse response
                                                        and source index directory.

        _create_load_balancing_db()             --      creates sqlite db tables with index server core stats from all nodes

        _pick_source_node_for_balancing()       --      pick source node for load balancing based on given DB

        _pick_dest_node_for_balancing()         --      pick destination node for load balancing based on given DB

        _validate_source_node_for_balancing()   --      Validates source node for load balancing operation has eligible cores to be moved

        restart_svc_all_index_nodes()           --      Restarts datacube service on all index server nodes

        get_cores_for_role()                    --      returns the core details for the given role

        validate_backup_size_with_src           --      validates folder size matches between browse response
                                                        and source index directory

        validate_backup_file_sizes_with_src_unix    --      validates file size matches between browse response
                                                            and source index directory for Unix index server

        validate_restore_data_with_browse       --      validates restored data size matches the browse response size


        update_roles                            --      configures required roles on index server

        run_full_backup                         --      Enables client/subclient backup & runs full backup on
                                                            default subclient on index server

        monitor_restore_job                     --      monitors the restore job

        init_subclient                          --      initialise the objects for client/backupset/subclient

        validate_data_in_core                   --      validates the file/folder count present in data source core

        delete_index_server                     --      Deletes the Index Server and removes Index directory

        check_solr_doc_count                    --      checks whether solr document count is matching or not with input

        create_index_server                     --      Creates a new Index server

        set_compute_folder_stats_key            --      Update/create compute folder stats key in registry

        filter_cores                            --      Returns 2 separate lists multinode and non multinode
                                                        routing cores

        get_new_index_directory                 --      Returns a valid index directory path on the
                                                            index server node machine

        get_eligible_cores_for_load_balancing   --      Returns dictionary with details of core eligible for load balancing

        get_eligible_cores_for_rebalancing      --      Returns dictionary with details of core eligible for rebalancing

        get_cores_details_for_load_balancing_validation --  Returns the source, destination, cores to move
                                                            (while Load Balancing), cores details before
                                                             load balancing operation.

        verify_load_balancing                   --      Verify Load Balancing operation & matches the document count
                                                        of moved cores

        set_unload_core_settings()              --      sets unload core additional settings on index server

        is_core_loaded()                        --      returns whether core is in loaded or unloaded state

        get_core_stats()                        --      returns core details from index server

        get_backup_files_details_from_is        --      Returns the List of files/folders from index server and
                                                        Dictionary of files/folders with metadata from index server
                                                        by doing browse on the index server backup job.

        get_files_qualified_for_incremental     --      Gets the files qualified for incremental by filtering out the
                                                        files to be ignored

        filter_files_from_is_browse_response    --      Filters the files out from folders and files from Index Server
                                                        Browse response and performs other required filtering operations
"""
import os
import sqlite3
from time import sleep
from datetime import datetime
import json

from cvpysdk.datacube.constants import IndexServerConstants

from AutomationUtils import logger
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import database_helper
from AutomationUtils.database_helper import CommServDatabase
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.constants import LAST_INDEX_SERVER_STATS_SYNC_TIME, CVD_SERVICE_NAME


class IndexServerHelper():
    """Helper class for index server operations"""

    def __init__(self, commcell_object, index_server_name):
        """Initialize the IndexServerHelper object"""
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.index_server_obj = self.commcell.index_servers.get(index_server_name)
        self.index_server_name = index_server_name
        self.sub_client = "default"
        self.is_sub_client_initialized = False
        self.client_obj = None
        self.agent_obj = None
        self.instance_obj = None
        self.subclient_obj = None
        self.options_selector_object = OptionsSelector(self.commcell)

    def restart_svc_all_index_nodes(self):
        """Restarts data cube service on all index server nodes in given index server

                Args:

                    None

                Returns:

                    None

                Exception:

                    if failed to restart service
        """
        nodes = self.index_server_obj.client_name
        for node in nodes:
            self.log.info(f"Restarting datacube on Index node : {node}")
            client_obj = self.commcell.clients.get(node)
            client_obj.restart_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
        self.log.info("Restart service done on all nodes. Waiting for 3mins for service to be up")
        sleep(180)

    def _pick_dest_node_for_balancing(self, db_path, src_client_id):
        """Pick destination node for load balancing operation based on given sqlite db

                Args:

                    db_path     (str)       --  Sqlite DB path

                    src_client_id   (str)   --  Client id of source node

                Returns:

                    str     --  Client ID picked as destination
        """
        from dynamicindex.utils.activateutils import ActivateUtils
        # to avoid picking node marked as critical, used action code = 1000 in below query
        pick_query = f"SELECT NodeClientId FROM autoScaleCoresStats S WHERE CanAccomodate = 1 AND ActionCode!=1000 AND NodeClientId <> {src_client_id} ORDER BY FreeSpacePercent DESC, TotalDocumentCount ASC limit 1"
        result = ActivateUtils().query_database(target_database=db_path, query=pick_query)
        for row in result['result']:
            dest_client_id = row['NodeClientId']
            return dest_client_id
        return 0

    def _validate_source_node_for_balancing(self, db_path, src_client_id):
        """Validates source node for load balancing operation has eligible cores to be moved

                        Args:

                            db_path     (str)       --  Sqlite DB path

                            src_client_id   (str)   --  Source node client id

                        Returns:

                            bool - contains valid cores or not for move
                """
        from dynamicindex.utils.activateutils import ActivateUtils
        # make sure picked client id has atleast one valid cores to be eligible for move
        select_query = f"select * from autoscaleCoresInfo where datamovable=1 and srcClientId={src_client_id} limit 1"
        result = ActivateUtils().query_database(target_database=db_path, query=select_query)
        if not result['result']:
            self.log.info(
                f"Picked Source node doesn't have any valid cores to be moved. Update Datamovable as zero for client id : {src_client_id}")
            update_query = f"UPDATE autoScaleCoresStats SET DataMovable = 0 WHERE NodeClientId = {src_client_id}"
            _ = ActivateUtils().execute_query(db_path=db_path, query=update_query, is_update=True)
            # reset canaccomdate flag for all nodes as we are repicking source node again
            update_query = f"UPDATE autoScaleCoresStats SET CanAccomodate = 1"
            _ = ActivateUtils().execute_query(db_path=db_path, query=update_query, is_update=True)
            return False
        return True

    def _pick_source_node_for_balancing(self, db_path):
        """Pick source node for load balancing operation based on given sqlite db

                Args:

                    db_path     (str)       --  Sqlite DB path

                Returns:

                    str     --  Client ID picked as source
        """
        from dynamicindex.utils.activateutils import ActivateUtils
        pick_query = f"SELECT NodeClientId FROM autoScaleCoresStats WHERE DataMovable = 1 ORDER BY ActionCode DESC, FreeSpacePercent ASC, TotalDocumentCount DESC limit 1"
        result = ActivateUtils().query_database(target_database=db_path, query=pick_query)
        for row in result['result']:
            src_client_id = row['NodeClientId']
            if self._validate_source_node_for_balancing(db_path=db_path, src_client_id=src_client_id):
                return src_client_id
            else:
                return self._pick_source_node_for_balancing(db_path=db_path)
        self.log.info(f"Not able to find any source client for load balancing")
        return 0

    def _create_load_balancing_db(
            self,
            index_size_limit_in_MB=5242880,
            index_item_counts=100000,
            src_free_disk_space_percent_limit=50,
            repick_core_num_days=90):
        """Populates sqlite db with index server core stats from all client nodes

                Args:

                    index_size_limit_in_MB      (int)       --  Minimum index size limit in MB for picking cores
                                                                    Default : 5GB

                    index_item_counts           (int)       --  Minimum items count for picking cores
                                                                    Default : 100K

                    src_free_disk_space_percent_limit (int) --  Free disk space limit check on source node (in percent)
                                                                    Default : 50%

                    repick_core_num_days        (int)       --  Minimum number of days before repicking same core for move
                                                                    Default : 90 Days

                Returns:

                      str       --  Sqlite DB Path
        """
        all_ds_id = []
        db_path = os.path.join(
            AUTOMATION_DIRECTORY,
            "Temp",
            f"LoadBalancing_{self.index_server_obj.cloud_id}_{self.index_server_name}.db")
        self.log.info(f"Load Balancing Automation db path - {db_path}")
        if os.path.exists(db_path):
            os.remove(db_path)
        # create table calls
        connection = sqlite3.connect(db_path)
        create_table_query = '''CREATE TABLE autoScaleCoresInfo (
                        coreName        nvarchar(1024),
                        coreStatus      integer,
                        srcClientId     int,
                        dsId            int,
                        coresSize       bigint,
                        DataMovable int default 1
                    );'''
        connection.execute(create_table_query)
        create_table_query = '''create table autoScaleCoresStats (
                        NodeClientId int,
                        TotalDocumentCount bigint,
                        TotalFreeSpace bigint,
                        TotalSpace bigint,
                        FreeSpacePercent int default 0,
                        ActionCode int default 0,
                        CanAccomodate int default 1,
                        DataMovable int default 1
                    );'''
        connection.execute(create_table_query)
        create_table_query = '''CREATE TABLE autoScaleCoresResult (
                        id	INTEGER PRIMARY KEY AUTOINCREMENT,
                        coreName        nvarchar(1024),
                        coreStatus      integer,
                        srcClientId     int,
                        dsId            int,
                        coresSize       bigint,
                        isStandAloneCore int default 0
                    );'''
        connection.execute(create_table_query)
        connection.commit()
        # fetch node stats from CS
        core_info_query = f"SELECT A.CoreName, A.Status, B.clientId, DS.dataSourceId, A.size FROM SEIndexServerNodeStats A JOIN DM2SearchServerCoreInfo B ON A.SearchServerCoreId = B.CoreId JOIN SECollectionInfo C ON B.clientId = C.clientId AND B.cloudId = C.cloudId JOIN SEDataSource DS ON DS.coreId = C.CoreId AND DS.dataSourceId = A.DataSourceId JOIN SEDataSourceRoute R ON A.DataSourceId = R.DataSourceId WHERE  B.cloudId = {self.index_server_obj.cloud_id} AND B.CloudType = 1 AND (A.size/(1024*1024) >= {index_size_limit_in_MB} OR A.ItemCount >= {index_item_counts}) AND A.status IN (0,1)"
        _, resultset = self.options_selector_object.exec_commserv_query(query=core_info_query)
        for data_row in resultset:
            insert_query = f'''insert into autoScaleCoresInfo(coreName,coreStatus,srcClientId,dsId,coresSize) values(
                    '{data_row[0]}',
                    {data_row[1]},
                    {data_row[2]},
                    {data_row[3]},
                    {data_row[4]}
                    )'''
            connection.execute(insert_query)
            all_ds_id.append(data_row[3])
        core_stats_query = f"SELECT DC.ClientId, ISNULL(SUM(NS.ItemCount), 0), ISNULL(MAX(DC.FreeSpace), 0), ISNULL(MAX(DC.TotalSpace), 0) FROM SEIndexServerNodeStats NS RIGHT JOIN DM2SearchServerCoreInfo DC ON DC.CoreId = NS.SearchServerCoreId AND DC.CloudType = 1 JOIN APP_CLIENT C ON DC.ClientId = C.Id AND C.status & (0x00002) = 0 WHERE DC.TotalSpace > 0 AND DC.CloudId = {self.index_server_obj.cloud_id} GROUP BY DC.ClientId"
        _, resultset = self.options_selector_object.exec_commserv_query(query=core_stats_query)
        for data_row in resultset:
            insert_query = f'''insert into autoScaleCoresStats(NodeClientId,TotalDocumentCount,TotalFreeSpace,TotalSpace) values(
                    {data_row[0]},
                    {data_row[1]},
                    {data_row[2]},
                    {data_row[3]}
                    )'''
            connection.execute(insert_query)
        connection.commit()

        # find index server node with critical flag and update back in db
        action_client_query = f"SELECT DISTINCT clientid FROM DM2SearchServerHealthInfo a WITH(NOLOCK) WHERE attrName = 'Action Code' AND attrVal = CONVERT(VARCHAR(10), 1000)"
        _, resultset = self.options_selector_object.exec_commserv_query(query=action_client_query)
        client_list = []
        for data_row in resultset:
            client_list.append(data_row[0])
        self.log.info(f"Clients found with Action code : 1000 (~Critical) in CS DB -- {client_list}")
        if client_list:
            update_query = f'''update autoScaleCoresStats set ActionCode = 1000 where NodeClientId in ({",".join(client_list)})'''
            self.log.info(f"Action code Update query - {update_query}")
            connection.execute(update_query)
            connection.commit()

        # update free space percentage for all index server nodes
        update_query = f'''update autoScaleCoresStats set FreeSpacePercent = ROUND(((TotalFreeSpace*1.0)/TotalSpace)*100 , 0)'''
        self.log.info(f"Free Space Percentage Update query - {update_query}")
        connection.execute(update_query)
        connection.commit()

        # update data movable flag for cores based on free space percent limit
        update_query = f'''UPDATE autoScaleCoresStats SET DataMovable = 0 WHERE FreeSpacePercent > {src_free_disk_space_percent_limit} AND ActionCode = 0'''
        self.log.info(f"Data Movable Update query for Free Space Percent - {update_query}")
        connection.execute(update_query)
        connection.commit()

        # no of days criteria check since last move
        # get property id value first and then Mark datamovable flag = 0 for all this cores as well
        performed_time = 0
        last_status = 0
        sql_query = f"SELECT PropertyId from SEProperty WHERE PropertyGuid = '50C23A5D-70EA-4BB7-81D6-22027BD82E16'"
        temp, last_status = self.options_selector_object.exec_commserv_query(query=sql_query)
        last_status = int(last_status[0][0])
        sql_query = f"SELECT PropertyId from SEProperty WHERE PropertyGuid = '1BC7C40D-1E4F-4809-8A85-E8786A93CB73'"
        temp, performed_time = self.options_selector_object.exec_commserv_query(query=sql_query)
        performed_time = int(performed_time[0][0])
        self.log.info(f"DataSource Id's for this Index server - {all_ds_id}")
        days_query = f"select T.dataSourceId from SEDataSource T " \
                     f"join SEDataSourceProperty DSP ON T.datasourceid = DSP.dataSourceId AND " \
                     f"DSP.propertyId = {performed_time} AND " \
                     f"CAST(DSP.propertyValue AS INT) > (dbo.GetUnixTime(GETUTCDATE()) - {repick_core_num_days} * 24 * 60 * 60) " \
                     f"JOIN SEDataSourceProperty DSP2 ON T.datasourceid = DSP2.dataSourceId AND " \
                     f"DSP2.propertyId = {last_status} AND  " \
                     f"CAST(DSP2.propertyValue AS INT) =4 where T.DataSourceId in ({','.join(all_ds_id)})"
        _, resultset = self.options_selector_object.exec_commserv_query(query=days_query)
        moved_cores = []
        for data_row in resultset:
            moved_cores.append(data_row[0])
        self.log.info(f"DataSource Id's moved in last n days criteria - {moved_cores}")
        if moved_cores:
            update_query = f'''UPDATE autoScaleCoresInfo SET DataMovable = 0 WHERE dsId in ({','.join(moved_cores)})'''
            self.log.info(
                f"Data Movable Update query for moved cores in last {repick_core_num_days} days - {update_query}")
            connection.execute(update_query)
            connection.commit()

        # sqlite connection close
        connection.close()
        return db_path

    def get_eligible_cores_for_load_balancing(
            self,
            src_client_id=None,
            dst_client_id=None,
            index_size_limit_in_MB=5242880,
            index_item_counts=100000,
            move_core_limit=25,
            repick_core_num_days=90,
            dst_free_disk_space_percent_limit=30,
            src_free_disk_space_percent_limit=50):
        """Returns eligible cores for load balancing from source client to destination client

                Args:

                    src_client_id               (int)       --  Client id of source node
                                                                    Default:None (Automatically selects it based on action code / Free space percentage / Document Count)

                    dst_client_id               (int)       --  Client id of destination node
                                                                    Default : None (Automatically selects it based on freespace available)

                    index_size_limit_in_MB      (int)       --  Minimum index size limit in MB for picking cores
                                                                    Default : 5GB

                    index_item_counts           (int)       --  Minimum items count for picking cores
                                                                    Default : 100K

                    move_core_limit             (int)       --  No of cores limit to be picked for move
                                                                    Default : 25 cores

                    repick_core_num_days        (int)       --  Minimum number of days before repicking same core for move
                                                                    Default : 90 Days

                    dst_free_disk_space_percent_limit (int) --  Free disk space limit check on destination node (in percent)
                                                                    Default : 30%

                    src_free_disk_space_percent_limit (int) --  Free disk space limit check on source node (in percent)
                                                                    Default : 50%

                Returns:

                      dict      --  containing eligible core details

                Raises:

                      Exception:

                            if src_client_ id is not valid

                            if dst_client_id is not valid

                            if it is not cvsolr

        """
        if self.index_server_obj.is_cloud:
            raise Exception(f"Index server is not CVSolr type")
        from dynamicindex.utils.activateutils import ActivateUtils
        database_helper.set_csdb(CommServDatabase(self.commcell))
        db_path = self._create_load_balancing_db(
            index_item_counts=index_item_counts,
            index_size_limit_in_MB=index_size_limit_in_MB,
            src_free_disk_space_percent_limit=src_free_disk_space_percent_limit,
            repick_core_num_days=repick_core_num_days)
        if not src_client_id:
            self.log.info(f"Picking Source client id as it is not passed")
            src_client_id = self._pick_source_node_for_balancing(db_path=db_path)
            if src_client_id == 0:
                raise Exception("Not able to find valid source node for load balancing operation")
        self.log.info(f"Source Client id - {src_client_id}")

        if not dst_client_id:
            self.log.info(f"Picking destination client id as it is not passed")
            dst_client_id = self._pick_dest_node_for_balancing(db_path=db_path, src_client_id=src_client_id)
            if dst_client_id == 0:
                raise Exception("Not able to find valid destination node for load balancing operation")
        self.log.info(f"Destination Client id - {dst_client_id}")

        retry = 0
        attempt = 0
        while True:
            insert_query = None
            attempt = attempt + 1
            if attempt > 50:
                raise Exception("Maximum attempts have reached in trying to determine source and destination node")
            # Source & destination node picked based on input or criteria logic.
            # proceed to populate autoscalecoresresult table
            if retry == 0:
                insert_query = f"INSERT INTO autoScaleCoresResult (coreName, coreStatus, srcClientId, dsId, coresSize) SELECT coreName, coreStatus, srcClientId, dsId, coresSize FROM autoScaleCoresInfo where srcClientId={src_client_id} and DataMovable = 1 ORDER BY coresSize DESC"
                self.log.info(f"Populating AutoscalecoresResult table with coresize descending(Bigger cores)")
            else:
                insert_query = f"INSERT INTO autoScaleCoresResult (coreName, coreStatus, srcClientId, dsId, coresSize) SELECT coreName, coreStatus, srcClientId, dsId, coresSize FROM autoScaleCoresInfo where srcClientId={src_client_id} and DataMovable = 1 ORDER BY coresSize"
                self.log.info(f"Populating AutoscalecoresResult table with coresize Ascending(Smaller Cores)")
            ActivateUtils().execute_query(db_path=db_path, query=insert_query, is_update=True)

            # delete alternate cores in results table so that we dont end up in moving all big cores in one shot
            delete_query = f"DELETE FROM autoScaleCoresResult WHERE id % 2 = 0  OR id > ({move_core_limit} *2)"
            ActivateUtils().execute_query(db_path=db_path, query=delete_query, is_update=True)

            # fetch total core size picked for move
            total_core_size = 0
            select_query = "SELECT sum(coresSize) as TotalCoreSize  from autoScaleCoresResult"
            result = ActivateUtils().query_database(target_database=db_path, query=select_query)
            for row in result['result']:
                total_core_size = int(row['TotalCoreSize'])
            self.log.info(f"Total core size at source for load balancing - {total_core_size}")

            # fetch free space available in destination node
            free_space_available = 0
            select_query = f"SELECT freeSpace from DM2SearchServerCoreInfo where clientId = {dst_client_id} AND cloudId = {self.index_server_obj.cloud_id}"
            _, resultset = self.options_selector_object.exec_commserv_query(query=select_query)
            for data_row in resultset:
                free_space_available = int(data_row[0])
            self.log.info(f"Total free space available in destination node - {free_space_available}")

            # criteria check to make sure we have free space left in destination after moving cores
            # in case if space is going less then limit, then remove the core from results table
            while total_core_size > 0 and (free_space_available -
                                           (dst_free_disk_space_percent_limit *
                                            free_space_available) /
                                           100) <= total_core_size:
                delete_query = f"delete FROM autoScaleCoresResult where rowid IN (Select rowid from autoScaleCoresResult limit 1)"
                ActivateUtils().execute_query(db_path=db_path, query=delete_query, is_update=True)
                self.log.info("Deleting top bigger core from autoScaleCoresResult table as it wont fit in destination")
                select_query = "SELECT sum(coresSize) as TotalCoreSize  from autoScaleCoresResult"
                result = ActivateUtils().query_database(target_database=db_path, query=select_query)
                for row in result['result']:
                    total_core_size = int(row['TotalCoreSize']) if row['TotalCoreSize'] else 0
                self.log.info(f"Re-calculated Total core size for load balancing - {total_core_size}")

            # check whether we got something to move or not
            self.log.info("Validating whether we got cores to move or not at source")
            select_query = f"SELECT * FROM autoScaleCoresResult limit 1"
            result = ActivateUtils().query_database(target_database=db_path, query=select_query)
            if not result['result']:
                self.log.info("No cores found to move at source. Processing repick logic")
                if retry == 0:  # no fit found for biggest cores. lets try for smaller cores
                    retry = 1
                else:  # we finished trying to fit both largest and smallest cores but could not fit anything
                    update_query = f"UPDATE autoScaleCoresStats SET CanAccomodate = 0 WHERE NodeClientId = {dst_client_id}"
                    ActivateUtils().execute_query(db_path=db_path, query=update_query, is_update=True)
                    self.log.info(f"Setting CanAccomdate flag = 0 for destination client : {dst_client_id}")
                    retry = 0
                    self.log.info(f"Reset flag set to 0")
                    self.log.info(f"Picking new destination client id")
                    dst_client_id = self._pick_dest_node_for_balancing(db_path=db_path, src_client_id=src_client_id)
                    if dst_client_id == 0:
                        raise Exception("Not able to find valid new destination node for load balancing operation")
                    self.log.info(f"New Destination Client id - {dst_client_id}")
                truncate_query = f"delete from autoScaleCoresResult"
                ActivateUtils().execute_query(db_path=db_path, query=truncate_query, is_update=True)
                self.log.info(f"Truncated autoScaleCoresResult Table")
            else:  # return all core details eligible for load balancing
                select_query = f"SELECT * FROM autoScaleCoresResult"
                result = ActivateUtils().query_database(target_database=db_path, query=select_query)
                self.log.info(f"Found cores to be moved from source to destination - {result}")
                return result

    def get_eligible_cores_for_rebalancing(
            self,
            src_client_id=None,
            dst_client_id=None,
            index_size_limit_in_MB=5242880,
            index_item_counts=100000,
            move_core_limit=25,
            repick_core_num_days=90,
            dst_free_disk_space_percent_limit=30):
        """Returns eligible cores for rebalancing from source client to destination client

                Args:

                    src_client_id               (int)       --  Client id of source node
                                                                    Default:None (Automatically selects it based on max shards size)

                    dst_client_id               (int)       --  Client id of destination node
                                                                    Default : None (Automatically selects it based on freespace available)

                    index_size_limit_in_MB      (int)       --  Minimum index size limit in MB for picking cores
                                                                    Default : 5GB

                    index_item_counts           (int)       --  Minimum items count for picking cores
                                                                    Default : 100K

                    move_core_limit             (int)       --  No of cores limit to be picked for move
                                                                    Default : 25 cores

                    repick_core_num_days        (int)       --  Minimum number of days before repicking same core for move
                                                                    Default : 90 Days

                    dst_free_disk_space_percent_limit (int) --  Free disk space limit check on destination node (in percent)
                                                                    Default : 30%

                Returns:

                      dict      --  containing eligible core details

                Raises:

                      Exception:

                            if src_client_ id is not valid

                            if dst_client_id is not valid

                            if it is not cvsolr

        """
        if self.index_server_obj.is_cloud:
            raise Exception(f"Index server is not CVSolr type")
        database_helper.set_csdb(CommServDatabase(self.commcell))
        output_dict = {}
        if src_client_id is None:
            # Automatically find source client id
            sql_query = f"SELECT top 1 A.CoreName, A.Status, B.clientId, DS.dataSourceId, A.size FROM SEIndexServerNodeStats A " \
                        f"JOIN DM2SearchServerCoreInfo B ON A.SearchServerCoreId = B.CoreId " \
                        f"JOIN SECollectionInfo C ON B.clientId = C.clientId AND " \
                        f"B.cloudId = C.cloudId JOIN SEDataSource DS ON DS.coreId = C.CoreId AND DS.dataSourceId = A.DataSourceId " \
                        f"JOIN SEDataSourceRoute R ON A.DataSourceId = R.DataSourceId WHERE  B.cloudId = {self.index_server_obj.cloud_id} AND " \
                        f"B.CloudType = 1 AND " \
                        f"A.status IN (0,1) ORDER BY A.size DESC"
            column_list, resultset = self.options_selector_object.exec_commserv_query(query=sql_query)
            src_client_id = int(resultset[0][2])
            self.log.info(f"Automatically Selected Source client id : {src_client_id}")
        if dst_client_id is None:
            # Automatically select destination node
            sql_query = f"SELECT TOP 1 clientId FROM DM2SearchServerCoreInfo WHERE " \
                        f"cloudId = {self.index_server_obj.cloud_id} AND CloudType = 1 AND " \
                        f"clientId != {src_client_id} ORDER BY FreeSpace DESC"
            column_list, resultset = self.options_selector_object.exec_commserv_query(query=sql_query)
            dst_client_id = int(resultset[0][0])
            self.log.info(f"Automatically Selected Destination client id : {dst_client_id}")
        output_dict['dstclientId'] = dst_client_id
        output_dict['srcclientId'] = src_client_id
        if src_client_id not in self.index_server_obj.client_id:
            raise Exception(f"Invalid source client id")
        if dst_client_id not in self.index_server_obj.client_id:
            raise Exception(f"Invalid destination client id")
        # Fetch eligible cores based on size and doc count. Make sure column selected in query and below list matches
        eligible_column_list = ['CoreName', 'Status', 'clientId', 'dataSourceId', 'size', 'ItemCount']
        sql_query = f"SELECT A.CoreName, A.Status, B.clientId, DS.dataSourceId, A.size, A.ItemCount FROM SEIndexServerNodeStats A " \
                    f"JOIN DM2SearchServerCoreInfo B ON A.SearchServerCoreId = B.CoreId " \
                    f"JOIN SECollectionInfo C ON B.clientId = C.clientId AND B.cloudId = C.cloudId " \
                    f"JOIN SEDataSource DS ON DS.coreId = C.CoreId AND DS.dataSourceId = A.DataSourceId " \
                    f"JOIN SEDataSourceRoute R ON A.DataSourceId = R.DataSourceId " \
                    f"WHERE  B.cloudId = {self.index_server_obj.cloud_id} AND B.clientId = {src_client_id} AND " \
                    f"B.CloudType = 1 AND " \
                    f"(A.size/(1024*1024) >= ({index_size_limit_in_MB}) OR A.ItemCount >= {index_item_counts}) AND  " \
                    f"{dst_client_id} != C.clientId AND A.status IN (0,1) ORDER BY A.size DESC"
        size_column_list, eligible_resultset = self.options_selector_object.exec_commserv_query(query=sql_query)
        self.log.info(f"Column list : {eligible_column_list}")
        self.log.info(f"Cores Matching Size & Doc count criteria - {eligible_resultset}")
        # get list of dsids
        eligible_dsids = []
        if len(size_column_list) > 1:
            for row in eligible_resultset:
                eligible_dsids.append(int(row[3]))
        self.log.info(f"List of Datasource id's Eligible after Source size / Doc Count : {eligible_dsids}")
        if not len(eligible_dsids) > 0:
            self.log.info("Cores are distributed evenly already. No cores found for index move")
            return {}
        # no of days criteria check since last move
        # get property id value first
        performed_time = 0
        last_status = 0
        sql_query = f"SELECT PropertyId from SEProperty WHERE PropertyGuid = '50C23A5D-70EA-4BB7-81D6-22027BD82E16'"
        temp, last_status = self.options_selector_object.exec_commserv_query(query=sql_query)
        last_status = int(last_status[0][0])
        sql_query = f"SELECT PropertyId from SEProperty WHERE PropertyGuid = '1BC7C40D-1E4F-4809-8A85-E8786A93CB73'"
        temp, performed_time = self.options_selector_object.exec_commserv_query(query=sql_query)
        performed_time = int(performed_time[0][0])
        sql_query = f"select T.DataSourceName, T.dataSourceId from SEDataSource T " \
                    f"join SEDataSourceProperty DSP ON T.datasourceid = DSP.dataSourceId AND " \
                    f"DSP.propertyId = {performed_time} AND " \
                    f"CAST(DSP.propertyValue AS INT) > (dbo.GetUnixTime(GETUTCDATE()) - {repick_core_num_days} * 24 * 60 * 60) " \
                    f"JOIN SEDataSourceProperty DSP2 ON T.datasourceid = DSP2.dataSourceId AND " \
                    f"DSP2.propertyId = {last_status} AND  " \
                    f"CAST(DSP2.propertyValue AS INT) =4 where T.DataSourceId in {tuple(eligible_dsids)}"
        repick_column_list, repick_resultset = self.options_selector_object.exec_commserv_query(query=sql_query)
        self.log.info(
            f"Cores Matching Repickdays criteria - {repick_resultset}. This cores will be removed from eligible list")
        repicked_dsids = []
        if len(repick_column_list) > 1:
            for row in repick_resultset:
                repicked_dsids.append(row[1])
        self.log.info(
            f"List of Datasource id's which got moved successfully in recent {repick_core_num_days} days : {repicked_dsids}")
        index_to_be_removed = []
        for ds_id in repicked_dsids:
            index = eligible_dsids.index(ds_id)
            index_to_be_removed.append(index)
            eligible_dsids.remove(ds_id)
        index_to_be_removed.sort(reverse=True)
        for index in index_to_be_removed:
            eligible_resultset.pop(index)
        self.log.info(f"List of Datasource id's Eligible after Repick num days check : {eligible_dsids}")
        # remove alternated eligible cores as we are not going to move all seq cores
        index_to_be_removed = []
        for i in range(0, len(eligible_dsids)):
            index = i + 1
            if index % 2 == 0:
                self.log.info(f"Removing Datasource with id : {eligible_dsids[i]} as it is Even core")
                index_to_be_removed.append(i)
            elif index > (move_core_limit * 2):
                self.log.info(
                    f"Removing Datasource with id : {eligible_dsids[i]} as it is beyond max core move limit")
                index_to_be_removed.append(i)
        # sort the list and then remove the index
        index_to_be_removed.sort(reverse=True)
        for index in index_to_be_removed:
            eligible_dsids.pop(index)
            eligible_resultset.pop(index)
        self.log.info(f"List of Datasource id's Eligible after Alternate core picks : {eligible_dsids}")
        # Freespace check on destination
        sql_query = f"SELECT freeSpace from DM2SearchServerCoreInfo where clientId = {dst_client_id} AND " \
                    f"cloudId = {self.index_server_obj.cloud_id}"
        space_column_list, space_resultset = self.options_selector_object.exec_commserv_query(query=sql_query)
        free_space = int(space_resultset[0][0])
        self.log.info(f"Destination client Index Directory FreeSpace : {free_space}")
        while True:
            cores_size = 0
            for ds_id in eligible_dsids:
                for row in eligible_resultset:
                    if int(ds_id) == int(row[eligible_column_list.index("dataSourceId")]):
                        self.log.info(f"DataSource Id {ds_id} matched for Space criteria. Adding it")
                        cores_size = cores_size + int(row[eligible_column_list.index("size")])
                        break
            self.log.info(f"Total core size for all eligible cores : {cores_size}")
            criteria = (free_space - (dst_free_disk_space_percent_limit * free_space / 100))
            if cores_size > 0 and criteria <= cores_size:
                self.log.info(f"Removing Top Node as free space criteria is not met on Destination")
                self.log.info(f"Criteria Valuation - {criteria}")
                self.log.info(f"Removing Data source id : {eligible_dsids[0]}")
                eligible_dsids.pop(0)
                eligible_resultset.pop(0)
                continue
            elif cores_size == 0:
                self.log.info("No valid cores found for index move due to space criteria")
                return {}
            break
        self.log.info(f"Final list of Eligible DataSource ids : {eligible_dsids}")
        for row in eligible_resultset:
            temp = {}
            for col in eligible_column_list:
                temp[col] = row[eligible_column_list.index(col)]
            output_dict[row[eligible_column_list.index('CoreName')]] = temp
        self.log.info(f"Final Eligible core details : {output_dict}")
        return output_dict

    def get_cores_details_for_load_balancing_validation(
            self,
            destination=None,
            index_size_limit_in_MB=5242880,
            index_item_counts=100000,
            move_core_limit=25,
            repick_core_num_days=90,
            dst_free_disk_space_percent_limit=30):
        """
        Returns the source, destination, cores to move (while Load Balancing),
        cores details before load balancing operation.

        Args:
            destination                 (str)       --  Name of the destination node.
            index_size_limit_in_MB      (str)       --  Minimum index size limit in MB for picking cores
            index_item_counts           (str)       --  Minimum items count for picking cores
            move_core_limit             (str)       --  No of cores limit to be picked for move
            repick_core_num_days        (str)       --  Minimum number of days before repicking same core for move
            dst_free_disk_space_percent_limit (str) --  Free disk space limit check on destination node (in percent)

        Raises:
            Exception:
                if Load Balancing is not required
        """
        destination_client_id = None
        if destination:
            index = self.index_server_obj.client_name.index(destination)
            destination_client_id = self.index_server_obj.client_id[index]
        self.log.info('Setting values of Load Balancing parameters')
        global_params = {dynamic_constants.INDEX_SIZE_LIMIT_IN_MB: index_size_limit_in_MB,
                         dynamic_constants.INDEX_ITEM_COUNTS: index_item_counts,
                         dynamic_constants.INDEX_MOVE_NUM_LIMIT: move_core_limit,
                         dynamic_constants.REPICK_CORES_NUM_DAYS: repick_core_num_days,
                         dynamic_constants.FREE_SPACE_CORES_LIMIT: dst_free_disk_space_percent_limit}
        for param in global_params:
            self.commcell.add_additional_setting(
                category=dynamic_constants.GX_GLOBAL_PARAM_CATEGORY, key_name=param,
                data_type='INTEGER', value=str(global_params[param]))
        output_dict = self.get_eligible_cores_for_rebalancing(
            dst_client_id=destination_client_id,
            index_size_limit_in_MB=global_params[dynamic_constants.INDEX_SIZE_LIMIT_IN_MB],
            index_item_counts=global_params[dynamic_constants.INDEX_ITEM_COUNTS],
            move_core_limit=global_params[dynamic_constants.INDEX_MOVE_NUM_LIMIT],
            repick_core_num_days=global_params[dynamic_constants.REPICK_CORES_NUM_DAYS],
            dst_free_disk_space_percent_limit=global_params[dynamic_constants.FREE_SPACE_CORES_LIMIT])
        if output_dict == {}:
            raise Exception("Cores are already distributed evenly. Load Balancing not required")
        self.log.info('Extracting Source, Destination & Cores to move from the output')
        source = self.index_server_obj.client_name[
            self.index_server_obj.client_id.index(output_dict[dynamic_constants.SOURCE_CLIENT_ID])]
        destination = self.index_server_obj.client_name[
            self.index_server_obj.client_id.index(output_dict[dynamic_constants.DESTINATION_CLIENT_ID])]
        cores_to_move = set()
        for key in output_dict:
            if key not in [dynamic_constants.SOURCE_CLIENT_ID, dynamic_constants.DESTINATION_CLIENT_ID]:
                cores_to_move.add(key)
        self.log.info('Getting Cores info before Operation (Only Source)')
        query_output = self.index_server_obj.get_all_cores(source)
        cores_details_before_operation = query_output[1]
        return source, destination, cores_to_move, cores_details_before_operation

    def verify_load_balancing(self, source, destination, cores_to_move, cores_details_before_operation):
        """
        Verify Load Balancing operation & matches the document count of moved cores
        Args:
            source  (str):  Name of the source node.
            destination (str):  Name of the destination node.
            cores_to_move   (list): List of cores to move while Load balancing.
            cores_details_before_operation  (dict): details of the cores before operation.

        Raises:
            Exception:
                if Core is not moved properly
                if Core is not removed from Source
                if Document count is not matching after Move operation
        """
        self.log.info('Getting Cores info after Operation (Both Source & Destination)')
        query_output = self.index_server_obj.get_all_cores(source)
        source_cores_after_operation = set(query_output[0])
        query_output = self.index_server_obj.get_all_cores(destination)
        destination_cores = set(query_output[0])
        cores_details_after_operation = query_output[1]
        self.log.info('Validating Moved Status & Document Count of each Core')
        for core in cores_to_move:
            if core not in destination_cores:
                raise Exception(f'Core {core} is not moved properly')
            if core in source_cores_after_operation:
                raise Exception(f'Core {core} is not removed from source but is present at destination.')
            self.log.info(f'Checking Doc Count of Core {core}')
            source_count = cores_details_before_operation[core]['index'][dynamic_constants.NUM_DOCS_PARAM]
            destination_count = cores_details_after_operation[core]['index'][dynamic_constants.NUM_DOCS_PARAM]
            if source_count == destination_count:
                self.log.info(f'Matched Source Count and Destination Count = {source_count}')
            else:
                raise Exception(f'For Core: {core}, Source Count {source_count} does not '
                                f'match Destination count {destination_count}')
        self.log.info("Verification of Load Balancing Operation Successful")
        self.log.info("Removing the global params")
        global_params = [dynamic_constants.INDEX_SIZE_LIMIT_IN_MB, dynamic_constants.INDEX_ITEM_COUNTS,
                         dynamic_constants.INDEX_MOVE_NUM_LIMIT, dynamic_constants.REPICK_CORES_NUM_DAYS,
                         dynamic_constants.FREE_SPACE_CORES_LIMIT]
        for param in global_params:
            self.commcell.delete_additional_setting(category='CommServeDB.GxGlobalParam', key_name=param)

    def check_solr_doc_count(self, solr_response, doc_count):
        """checks whether solr document count is matching or not with input

                Args:

                    solr_response       (dict)      --  Solr response JSON

                    doc_count           (int)       --  Document count to verify
                                                            if -1, then we check for condition solr_doc_count!=0

                Returns:

                    None

                Raises:

                    Exception:

                            if input data type is not valid

                            if document count mismatches
        """
        if not isinstance(solr_response, dict) or not isinstance(doc_count, int):
            raise Exception("Input data type is not valid")
        solr_doc_count = int(solr_response['response']['numFound'])
        self.log.info(f"Solr Response document count : {solr_doc_count}")
        if doc_count not in (-1, solr_doc_count):
            raise Exception(f"Document count mismatched. Expected : {doc_count} Actual : {solr_doc_count}")
        elif doc_count == -1 and solr_doc_count == 0:
            raise Exception(f"Document count mismatched. Expected doc count > zero but Actual : {solr_doc_count}")
        self.log.info(f"Document count matched as expected : {solr_doc_count}")

    def init_subclient(self):
        """Initialise the client/backupset/subclient object"""
        if not self.is_sub_client_initialized:
            self.client_obj = self.commcell.clients.get(self.index_server_name)
            self.agent_obj = self.client_obj.agents.get(IndexServerConstants.INDEX_SERVER_IDA_NAME)
            self.instance_obj = self.agent_obj.instances.get(IndexServerConstants.INDEX_SERVER_INSTANCE_NAME)
            self.subclient_obj = self.instance_obj.subclients.get(self.sub_client)
            self.is_sub_client_initialized = True
            self.log.info("Client/Agent/Instance/Subclient objects initialized")

    def filter_cores(self, core_list):
        """Returns separate multinode and non multinode routing cores

            Args:

                core_list (list)   --  A list of all the core names (str) for a particular node.

            Returns:

                    multinode_cores(list)       --  List containing multinode routing cores
                    non_multinode_cores(list)   --  List containing non multinode routing cores

             Raises:

                    Exception:

                        if input is not valid

                """
        if not isinstance(core_list, list):
            raise Exception("Input data type is not valid")
        multinode_cores = []
        non_multinode_cores = []
        for core in core_list:
            if not (isinstance(core, str)):
                raise Exception("Input data type is not valid")

            if IndexServerConstants.FSINDEX in core:
                multinode_cores.append(core)
            else:
                non_multinode_cores.append(core)
        self.log.info(f"Multinode cores : [{multinode_cores}] Non Multinode Cores : [{non_multinode_cores}]")
        return multinode_cores, non_multinode_cores

    def validate_data_in_core(self, data_source_obj, file_count, folder_count, file_criteria=None):
        """validates the file/folder count present in data source core matches with given count

                Args:

                    data_source_obj (object)    --  DataSource class object

                    file_count      (int)        --  total file count

                    folder_count    (int)        --  total folder count

                    file_criteria   (dict)       --  Dictionary containing search criteria and value for files
                                                            Acts as 'q' field in solr query

                Returns:

                    None

                Raises:

                    Exception:

                        if input is not valid

                        if there is mismatch in file/folder count

        """
        if not isinstance(file_count, int) or not isinstance(folder_count, int):
            raise Exception("Input data is not valid")
        self.log.info(f"File/Folder count to verify is : {file_count}/{folder_count}")
        if file_criteria is None:
            file_criteria = dynamic_constants.QUERY_FILE_CRITERIA
        else:
            file_criteria.update(dynamic_constants.QUERY_FILE_CRITERIA)
        self.log.info(f"File criteria formed : {file_criteria}")
        resp = self.index_server_obj.execute_solr_query(core_name=data_source_obj.computed_core_name,
                                                        select_dict=file_criteria)
        solr_files = int(resp['response']['numFound'])
        if solr_files != file_count:
            raise Exception(f"File count mismatched Expected : {file_count} Actual : {solr_files}")
        self.log.info("File count Matched!!! Total crawl count from data source : %s", solr_files)

        if folder_count != dynamic_constants.SKIP_FOLDER_CHECK:
            resp = self.index_server_obj.execute_solr_query(core_name=data_source_obj.computed_core_name,
                                                            select_dict=dynamic_constants.QUERY_FOLDER_CRITERIA)
            solr_folder = int(resp['response']['numFound'])
            if solr_folder != folder_count:
                raise Exception(f"Folder count mismatched Expected : {folder_count} Actual : {solr_folder}")
            self.log.info("Folder count Matched!!! Total crawl count from data source : %s", solr_folder)

    def monitor_restore_job(self, job_obj):
        """Monitors the restore job till it completes

                Args:

                    job_obj     (object)        --  instance of job class

                Returns:

                    None

                Raises:

                    Exception:

                        if job fails or threshold time reaches for job completion


        """

        self.log.info("Going to Monitor this restore job for completion : %s", job_obj.job_id)
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Index server restore failed. Please check logs")
            raise Exception("Index server restore failed. Please check logs")
        if job_obj.status.lower() != 'completed':
            raise Exception("Index server restore completed with error status. Please check logs")
        self.log.info("Index server restore job is finished")

    def run_full_backup(self):
        """ Enables client/subclient backup & runs full backup on default subclient

                Args:
                    None

                Returns:

                    str     --  job id

                Raises:
                    None
        """
        self.init_subclient()
        self.log.info("Enable backup at client and subclient level")
        if not self.client_obj.is_backup_enabled:
            self.client_obj.enable_backup()
        if not self.subclient_obj.is_backup_enabled:
            self.subclient_obj.enable_backup()

        self.log.info("Going to start FULL backup job for index server")
        job_obj = self.subclient_obj.run_backup()
        self.log.info("Going to Monitor this backup job for completion : %s", job_obj.job_id)
        backup_job_id = job_obj.job_id
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Index server backup failed. Please check logs")
            raise Exception("Index server backup failed. Please check logs")
        if job_obj.status.lower() != 'completed':
            raise Exception("Index server backup completed with error status. Please check logs")
        self.log.info("Index server backup job is finished")
        return backup_job_id

    def update_roles(self, index_server_roles):
        """ updates the index server roles with specified role list

                Args:

                    index_server_roles      (list)      --  list of index server roles

                Returns:
                    None

                Raises:
                    Exception:

                            if input data type is not valid

                            if failed to update roles

        """
        if not isinstance(index_server_roles, list):
            raise Exception("Input data type is not valid")

        update_roles = []
        update_required = False
        self.log.info("Setting up index server")
        self.log.info("Current roles defined in index server : %s", self.index_server_obj.role_display_name)
        for role in index_server_roles:
            if role not in self.index_server_obj.role_display_name:
                temp_role = IndexServerConstants.UPDATE_ADD_ROLE
                temp_role['roleName'] = role
                update_roles.append(temp_role)
                update_required = True

        if update_required:
            self.log.info("Required roles is not present. Calling role update on index server")
            self.log.info("Request Json : %s", update_roles)
            self.index_server_obj.update_role(update_roles)

    def validate_restore_data_with_browse(
            self,
            role_name,
            client_name,
            restore_path,
            backup_job_id,
            index_server_node=None,
            **kwargs):
        """ validate restored core folder size and browse core sizer matches or not

            Args:

                role_name                   (str)       --  role name whose cores size needs to be verified

                client_name                 (str)       --  client name where data has been restored

                restore_path                (str)       --  folder path in client where restored data is present

                backup_job_id               (str)       --  backup job id from where data has been restored

                index_server_node           (str)       --  index server client node name
                                                    if none, then first node from index server will be considered.
                kwargs                                  --  Additional Info
                ex -> core_list             (list)      --  List of cores name whose size needs to be verified
            Returns:

                True if size matches between restored data and browse
                False if size differs

            Raises:

                Exception:

                    if input data is not valid

                    if unable to verify size for cores

        """
        if index_server_node is None:
            index_server_node = self.index_server_obj.client_name[0]
        self.init_subclient()
        if not (isinstance(backup_job_id, str) or
                isinstance(role_name, str) or
                isinstance(client_name, str) or
                isinstance(restore_path, str)):
            raise Exception("Input data type is not valid")
        folder_list, data_from_index_server = self.subclient_obj.get_file_details_from_backup(
            roles=[role_name], include_files=False,
            job_id=backup_job_id, index_server_node=index_server_node, **kwargs)

        self.log.info("Browse response from index server : %s", data_from_index_server)
        self.log.info(f"Folder List - {folder_list}")
        src_machine_obj = Machine(commcell_object=self.commcell,
                                  machine_name=client_name)
        self.log.info("Created machine object for client : %s", client_name)
        self.log.info("Restored path : %s", restore_path)
        # node_os = 1 (windows node) | node_os = 0 (unix node)
        node_os = 1
        delimiter = "\\"
        if src_machine_obj.os_info.lower() == dynamic_constants.UNIX:
            node_os = 0
            delimiter = "/"

        for folder in folder_list:
            # if unix then skip this part
            if node_os == 1:
                if folder == f"{delimiter}{role_name}{delimiter}{index_server_node}":
                    self.log.info(f"Ignore root folder : {folder}")
                    continue
                if not (
                        folder.endswith(
                            dynamic_constants.BACKUP_CONF_DIR) or
                        folder.endswith(dynamic_constants.BACKUP_INDEX_DIR)):
                    self.log.info(f"Ignore root folder : {folder}")
                    continue
                # split folder and take only last two value which gives corename\<config/index folder>
            self.log.info("Validating folder : %s", folder)
            folder_split = folder.split(delimiter)
            modified_folder = f"{folder_split[-1]}"
            if node_os == 1:
                modified_folder = f"{folder_split[-2]}{delimiter}{folder_split[-1]}"
            self.log.info("Modified folder : %s", modified_folder)
            restored_folder = str(f"{restore_path}{delimiter}{modified_folder}")
            restored_folder = restored_folder.replace("{delimiter}{delimiter}", "{delimiter}")
            self.log.info("Restored folder path : %s", restored_folder)

            if node_os == 1:
                restored_folder_size = src_machine_obj.get_folder_size(folder_path=restored_folder,
                                                                       in_bytes=True)
            if node_os == 0:
                restored_folder_size = src_machine_obj.get_file_stats_in_folder(folder_path=restored_folder)

            browse_folder_size = data_from_index_server[folder]['size']
            self.log.info("Restore folder size : %s", restored_folder_size)
            self.log.info("Browse folder size : %s", browse_folder_size)
            if browse_folder_size != restored_folder_size:
                msg = f"Restore data size not matched with browse for folder : {folder}"
                self.log.info(msg)
                return False
            self.log.info("Folder size matched : %s", browse_folder_size)

        return True

    def validate_backup_size_with_src(self, role_name, job_id=0, backup_all_prop=False, index_server_node=None):
        """ validate core folder size in backup and source core size in index server matches or not

            Args:

                job_id                      (int)       --  job id on which browse will be done

                role_name                   (str)       --  role name whose core size needs to be verified

                backup_all_prop             (bool)      --  true if core.properties files are backed up and
                                                            need to be included during config size calculation
                                                            (default : False)
                  *** we are not backing up core.properties file for default cores.change this once it is backed up ***

                index_server_node           (str)       --  index server client node name
                                                    if none, then first node from index server will be considered.

            Returns:

                True if size matches between source and browse
                False if size differs

            Raises:

                Exception:

                    if input data is not valid

                    if unable to verify size for cores

        """
        if index_server_node is None:
            index_server_node = self.index_server_obj.client_name[0]
        self.init_subclient()
        if not isinstance(role_name, str):
            raise Exception("Input data type is not valid")
        folder_list, data_from_index_server = self.subclient_obj.get_file_details_from_backup(
            roles=[role_name], include_files=False,
            job_id=job_id)
        self.log.info("Browse response from index server : %s", data_from_index_server)
        self.log.info(f"Browse folder list : {folder_list}")
        src_machine_obj = None
        self.log.info("Creating machine object for client : %s", index_server_node)
        src_machine_obj = Machine(machine_name=index_server_node,
                                  commcell_object=self.commcell)

        analytics_dir = src_machine_obj.get_registry_value(commvault_key=dynamic_constants.ANALYTICS_REG_KEY,
                                                           value=dynamic_constants.ANALYTICS_DIR_REG_KEY)
        self.log.info("Index server Index directory is : %s", analytics_dir)
        core_list, core_details = self.get_cores_for_role(role_name=role_name)
        self.log.info("Cores got for validation from index server : %s", core_list)

        multinode_folder_count = 0
        dummy_folder = 1  # for root folder
        multinode_cores, non_multinode_cores = self.filter_cores(core_list)
        if len(multinode_cores) > 0:
            dummy_folder = dummy_folder + 1
            # Adding 1 for the parent folder in case of multinode cores found
            multinode_folder_count = len(multinode_cores)
            fsindex_parent_dir = f"{IndexServerConstants.FSINDEX}{self.index_server_obj.cloud_name}" \
                                 f"{IndexServerConstants.MULTINODE}"
            leader_node = self.index_server_obj.client_name[0]
            if index_server_node != leader_node:
                # For non leader cores, the default cores are not backed up.
                core_list = [core for core in core_list if core not in dynamic_constants.DATA_ANALYTICS_DEFAULT_CORES]

        self.log.info(f"IS Core list count : [{len(core_list)}] Browse Folder list count : [{len(folder_list)}] "
                      f"Multinode folder count: [{multinode_folder_count}] dummy folder count : [{dummy_folder}]")
        # Multiply by 4 as each core has 4 folders, Subtract the multi node folders
        # Add 2 (1 for dummy root folder and 1 for multinode cores root folder)
        if (len(core_list) * 4 - multinode_folder_count + dummy_folder) != len(folder_list):
            msg = f"Core list from browse and index server not matched. " \
                  f"Browse core count {(len(folder_list) + multinode_folder_count - dummy_folder) / 4}" \
                  f" index server core count {len(core_list)}"
            self.log.info(msg)
            return False
        self.log.info("Cores from browse and index server matched. No of cores : %s", len(core_list))

        for core in core_list:
            is_config_set = False
            conf_size = 0
            index_size = 0
            core_info = None
            browse_conf_dir = None
            browse_index_dir = None
            self.log.info("Validating core : %s", core)
            for details in core_details:
                if core in details:
                    if details[core]['name'] == core:
                        core_info = details[core]
                        break
            instance_dir = core_info['instanceDir']
            data_dir = f"{core_info['dataDir']}\\{dynamic_constants.BACKUP_INDEX_DIR}"
            self.log.info("Instance dir : %s", instance_dir)
            self.log.info("Data dir : %s", data_dir)
            index_size = src_machine_obj.get_folder_size(folder_path=data_dir, in_bytes=True)
            self.log.info("Source index size : %s", index_size)
            if f"\\{dynamic_constants.BACKUP_CONF_HOME}\\" in instance_dir:
                self.log.info("Size will be calculated based on ConfHome folder alone for : %s", core)
                conf_size = src_machine_obj.get_folder_size(folder_path=instance_dir,
                                                            in_bytes=True)
            elif f"\\{dynamic_constants.BACKUP_CONF_SETS}\\" in instance_dir:
                is_config_set = True
                instance_dir = f"{instance_dir}\\conf"
                self.log.info("Modified Instance dir for configsets: %s", instance_dir)
                self.log.info("Size will be calculated based on configset for : %s", core)
                conf_size = src_machine_obj.get_folder_size(folder_path=instance_dir,
                                                            in_bytes=True)
                if backup_all_prop:
                    core_prop = f"{analytics_dir}\\{dynamic_constants.BACKUP_CONF_HOME}\\{core}\\core.properties"
                    self.log.info("Core properties location : %s", core_prop)
                    core_prop_size = src_machine_obj.get_file_size(file_path=core_prop, in_bytes=True)
                    self.log.info("Core properties size : %s", core_prop_size)
                    conf_size = conf_size + core_prop_size
            self.log.info("Source Config size : %s", conf_size)
            if IndexServerConstants.FSINDEX in core:
                browse_conf_dir = f"\\{role_name}\\{index_server_node}\\{fsindex_parent_dir}" \
                                  f"\\{core}\\{dynamic_constants.BACKUP_CONF_DIR}"
                browse_index_dir = f"\\{role_name}\\{index_server_node}\\{fsindex_parent_dir}" \
                                   f"\\{core}\\{dynamic_constants.BACKUP_INDEX_DIR}"
            else:
                browse_conf_dir = f"\\{role_name}\\{index_server_node}\\{core}" \
                                  f"\\{core}\\{dynamic_constants.BACKUP_CONF_DIR}"
                browse_index_dir = f"\\{role_name}\\{index_server_node}\\{core}" \
                                   f"\\{core}\\{dynamic_constants.BACKUP_INDEX_DIR}"

            self.log.info("Browse config dir : %s", browse_conf_dir)
            self.log.info("Browse index dir : %s", browse_index_dir)
            if browse_conf_dir not in data_from_index_server or browse_index_dir not in data_from_index_server:
                raise Exception(f"Browse don't have required folder structure")
            browse_conf_size = data_from_index_server[browse_conf_dir]['size']
            browse_index_size = data_from_index_server[browse_index_dir]['size']
            # for config sets, don't compare the config folder sizes as it is default in all index servers
            if not is_config_set and conf_size != browse_conf_size:
                msg = f"Config size not matched. Source {conf_size} Browse {browse_conf_size}"
                self.log.info(msg)
                return False
            self.log.info("Config size matched. Size = %s", browse_conf_size)
            if index_size != browse_index_size:
                msg = f"Index size not matched. Source {index_size} Browse {browse_index_size}"
                self.log.info(msg)
                return False
            self.log.info("Index size matched. Size = %s", browse_index_size)
        return True

    def validate_backup_file_sizes_with_src_unix(self, role_name, job_id=0, index_server_node=None):
        """ Validates file size matches between browse response and source index directory for Unix index server

            Args:

                job_id                      (int)       --  job id on which browse will be done

                role_name                   (str)       --  role name whose core size needs to be verified

                index_server_node           (str)       --  index server client node name
                                                    if none, then first node from index server will be considered.

            Returns:

                True if size matches between source and browse
                False if size differs

            Raises:

                Exception:

                    if input data is not valid

                    if unable to verify size for cores

        """
        if index_server_node is None:
            index_server_node = self.index_server_obj.client_name[0]
        self.init_subclient()
        if not isinstance(role_name, str):
            raise Exception("Input data type is not valid")
        folder_list, data_from_index_server = self.subclient_obj.get_file_details_from_backup(
            roles=[role_name], job_id=job_id, index_server_node=index_server_node)
        self.log.info(f"Browse response from index server : {data_from_index_server}")
        self.log.info(f"Browse folder list : {folder_list}")

        core_list, core_details = self.get_cores_for_role(role_name=role_name, client_name=index_server_node)
        self.log.info(f"Cores got for validation from index server : {core_list}")

        folder_count = len(folder_list)
        multinode_cores, core_list = self.filter_cores(core_list)
        # The list core_list contains the non multinode cores only
        fsindex_multinode_core_count = len(multinode_cores)
        if fsindex_multinode_core_count > 0:
            # Adding the multinode cores folder. Subtracting 1 for parent folder of all the multinode cores
            folder_count = folder_count + fsindex_multinode_core_count - 1
            # Selecting The Leader Node (It is the first node in the node list of the index server)
            leader_node = self.index_server_obj.client_name[0]
            if index_server_node != leader_node:
                # For non leader cores, the default cores are not backed up.
                core_list = [core for core in core_list if core not in dynamic_constants.DATA_ANALYTICS_DEFAULT_CORES]

        if len(core_list) + fsindex_multinode_core_count != folder_count:
            msg = f"Core list from browse and index server not matched. " \
                  f"Browse core count {folder_count} index server core count {len(core_list)}"
            self.log.info(msg)
            return False
        self.log.info(f"Cores from browse and index server matched. No of cores : {len(core_list)}")

        if not self._validate_cores_size_unix(core_list, core_details, index_server_node, data_from_index_server,
                                              role_name):
            return False

        if fsindex_multinode_core_count > 0:
            fsindex_parent_dir = f"{IndexServerConstants.FSINDEX}{self.index_server_obj.cloud_name}" \
                                 f"{IndexServerConstants.MULTINODE}"
            roles_path = f"/{role_name}/{index_server_node}/{fsindex_parent_dir}"

            find_options = {'operation': 'browse', 'path': roles_path, 'job_id': job_id}

            # Getting file details from backup for the multinode routing cores
            folders_list, data_from_index_server = self.subclient_obj.find(find_options)

            if not self._validate_cores_size_unix(multinode_cores, core_details, index_server_node,
                                                  data_from_index_server, role_name, fsindex_parent_dir):
                return False

        return True

    def _validate_cores_size_unix(self, core_list, core_details, index_server_node, data_from_index_server, role_name,
                                  fsindex_parent_dir=None):
        """ Validates whether the size of each core in the core list matches between browse response
            and source index directory for unix index server

                    Args:

                        core_list            (list)      --  List consisting of all the core names to be validated

                        core_details         (dict)      --  dict containing details about cores

                        index_server_node    (str)       --  index server client node name

                        data_from_index_server (dict)    --  Dictionary of all the paths with additional metadata
                                                             retrieved from browse operation

                        role_name            (str)       --  role name whose core size needs to be verified

                        fsindex_parent_dir   (str)       --  Directory of the parent folder of the multinode cores
                                                            * Applicable only when multinode cores are present*
                                                            (default : None)

                    Returns:

                        True/False if validation is successful/unsuccessful
    """

        self.log.info(f"Creating machine object for client : {index_server_node}")
        src_machine_obj = Machine(machine_name=index_server_node,
                                  commcell_object=self.commcell)
        for core in core_list:
            core_info = None
            self.log.info(f"Validating core : {core}")
            for details in core_details:
                if core in details:
                    if details[core]['name'] == core:
                        core_info = details[core]
                        break
            instance_dir = core_info['instanceDir']
            data_dir = f"{core_info['dataDir']}{dynamic_constants.BACKUP_INDEX_DIR_UNIX}"
            self.log.info(f"Instance dir {instance_dir}")
            self.log.info(f"Data dir : {data_dir}")
            index_size = src_machine_obj.get_file_stats_in_folder(folder_path=data_dir)
            self.log.info(f"Source index size : {index_size}")

            conf_size = src_machine_obj.get_file_stats_in_folder(folder_path=instance_dir)
            self.log.info(f"Source conf size : {conf_size}")

            browse_dir = f"/{role_name}/{index_server_node}/{core}"
            if fsindex_parent_dir is not None:
                browse_dir = f"/{role_name}/{index_server_node}/{fsindex_parent_dir}/{core}"
            self.log.info(f"Browse dir : {browse_dir}")
            browse_dir_size = data_from_index_server[browse_dir]['size']

            if conf_size + index_size != browse_dir_size:
                msg = f"Size not matched. Source {conf_size + index_size} Browse {browse_dir_size}"
                self.log.info(msg)
                return False
            msg = f"Size matched for core {core}. Source {conf_size + index_size} Browse {browse_dir_size}"
            self.log.info(msg)
        return True

    def get_cores_for_role(self, role_name, client_name=None):
        """ Gets core names for the given role from index server

            Args:

                role_name                   (str)       --  role name

                client_name                 (str)       --  client node name
                    ***Applicable only for solr cloud mode or multi node Index Server***

            Returns:

                (list,dict)             -- list containing core names
                                        -- dict containing details about cores

            Raises:

                Exception:

                    if input data is not valid

                    if unable to get core details

        """
        if not isinstance(role_name, str):
            raise Exception("Input data type is not valid")
        self.log.info("Going to get core details from index server : %s", self.index_server_name)
        core_list, core_details = self.index_server_obj.get_all_cores(client_name=client_name)
        self.log.info("Core details : %s", core_list)
        self.log.info("Filtering out cores for role : %s", role_name)
        default_core = None
        dynamic_core = None
        filtered_list = []
        filtered_details = []
        if role_name == IndexServerConstants.ROLE_DATA_ANALYTICS:
            default_core = dynamic_constants.DATA_ANALYTICS_DEFAULT_CORES
            dynamic_core = dynamic_constants.DATA_ANALYTICS_DYNAMIC_CORES
        elif role_name == IndexServerConstants.ROLE_SYSTEM_DEFAULT:
            default_core = dynamic_constants.SYSTEM_DEFAULT_CORES
            dynamic_core = []
        else:
            raise Exception("Unable to determine default/dynamic cores for given role")
        self.log.info(f"Default core list : {default_core} Dynamic core list : {dynamic_core}")
        # filter logic
        for core in core_list:
            if core in default_core:
                filtered_list.append(core)
                filtered_details.append({core: core_details[core]})
                self.log.info("Adding default core : %s", core)
            else:
                for prefix in dynamic_core:
                    if str(core).startswith(prefix):
                        filtered_list.append(core)
                        filtered_details.append({core: core_details[core]})
                        self.log.info("Adding dynamic core : %s", core)
        self.log.info("Filtered cores : %s", filtered_list)
        self.log.info("Filtered cores details : %s", filtered_details)
        return filtered_list, filtered_details

    def get_backup_files_details_from_is(self, role_name, job_id=0, index_server_node=None):
        """ Gets files/folders details from index server backup job.

            Args:

                job_id                      (int)       --  job id on which browse will be done

                role_name                   (str)       --  role name whose backed up files will be returned

                index_server_node           (str)       --  index server client node name
                                                    if none, then first node from index server will be considered.

            Returns:

                List of files/folders from index server
                Dictionary of files/folders with metadata from index server

            Raises:

                Exception:

                    if input data is not valid


        """
        if index_server_node is None:
            index_server_node = self.index_server_obj.client_name[0]
        self.init_subclient()
        if not isinstance(role_name, str):
            raise Exception("Input data type is not valid")
        file_list, data_from_index_server = self.subclient_obj.get_file_details_from_backup(
            roles=[role_name], include_files=True,
            job_id=job_id)
        self.log.info("Browse response from index server : %s", data_from_index_server)
        self.log.info(f"Browse folder list : {file_list}")
        return file_list, data_from_index_server

    def get_files_qualified_for_incremental(self, fso_metadata, last_backup_time):
        """Gets the files qualified for incremental by filtering out the files to be ignored
         Args :
               fso_metadata         ([sqlite3.Row,sqlite3.Row]) --  FSO metadata from which we have to filter the
                                                                    files qualified for incremental.
               last_backup_time     (int)                       --  The unix timestamp of the last full backup

        Returns:
                Dictionary of filtered files qualified for incremental backup with file path as keys and file size
                 as value"""

        if fso_metadata is None:
            raise Exception("FSO Metadata cannot be None")
        files_qualified_for_inc = {}
        for item in fso_metadata:
            m_t = datetime.strptime(
                item[dynamic_constants.FSO_DASHBOARD_TABS_TO_VERIFY['ALL'][2]], '%B %d, %Y %I:%M:%S %p').timestamp()
            c_t = datetime.strptime(
                item[dynamic_constants.FSO_DASHBOARD_TABS_TO_VERIFY['ALL'][0]], '%B %d, %Y %I:%M:%S %p').timestamp()
            if m_t > last_backup_time or c_t > last_backup_time:
                files_qualified_for_inc[item[dynamic_constants.FSO_METADATA_FIELD_PATH]] = \
                    item[dynamic_constants.FSO_METADATA_FIELD_FILE_SIZE]

        self.log.info(f"Files Qualified For Incremental:- {files_qualified_for_inc}")

        files_qualified_for_inc_filtered = {}
        # Filtering out the system default cores like 'indexserverinfo', 'datasourceinfo' and '.tlog', '.lock' files
        files_to_be_ignored = [dynamic_constants.SYSTEM_DEFAULT_CORES[0], dynamic_constants.SYSTEM_DEFAULT_CORES[2],
                               dynamic_constants.COMPLIANCE_AUDIT_CORE, dynamic_constants.TLOG, dynamic_constants.LOCK]
        for path, size in files_qualified_for_inc.items():
            if not any(file in path for file in files_to_be_ignored):
                path_trimmed = ("\\".join(path.split("\\")[-3:]))
                if dynamic_constants.CORE_PROPERTIES in path:
                    path_trimmed = ("\\".join(path.split("\\")[-2:]))
                files_qualified_for_inc_filtered[path_trimmed] = size

        return files_qualified_for_inc_filtered

    def filter_files_from_is_browse_response(self, data_from_is):
        """Filters the files out from folders and files from Index Server Browse response and performs other required
        filtering operations (The browse response contains folders as well)
                 Args :
                       data_from_is : Dict of Browse Response from IS

                Returns:
                        Dictionary of filtered files from the index server browse response with file path as keys and
                         file size as value"""

        if data_from_is is None:
            raise Exception("Data from Index Server cannot be None")
        data_from_is_filtered = {}
        for path, data in data_from_is:
            if '.' in path or dynamic_constants.SEGMENTS in path:
                path_trimmed = ("\\".join(path.split("\\")[-3:]))
                if dynamic_constants.CORE_PROPERTIES in path:
                    path_trimmed = ("\\".join(path.split("\\")[-2:]))
                data_from_is_filtered[path_trimmed] = data['size']

        self.log.info(f"Files From Index Server Incremental Backup Browse : {data_from_is_filtered}")
        return data_from_is_filtered

    def delete_index_server(self):
        """Deletes the Index Server and removes Index directory from the Index node clients"""
        node_objects = []
        for node_name in self.index_server_obj.client_name:
            node_objects.append(self.index_server_obj.get_index_node(node_name))
        self.log.info("Deleting index server")
        self.commcell.index_servers.delete(self.index_server_name)
        self.log.info("Index server deleted")
        for node in node_objects:
            self.log.info(f"Deleting Index directory: {node.index_location} on client: {node.node_name}")
            node_machine = Machine(node.node_name, self.commcell)
            node_machine.remove_directory(node.index_location, 0)
            self.log.info("Index directory deleted")

    @staticmethod
    def create_index_server(commcell_object, index_server_name, index_server_node_names, index_directories,
                            index_server_roles, index_pool_name=None, is_cloud=False, cloud_param=None):
        """Creates a new Index server

            Args:
                commcell_object                 (object)    -   commcell object
                index_server_node_names         (list)  --  client names for index server node
                index_server_name               (str)   --  name for the index server
                index_directories               (list)  --  list of index locations for the index server
                                                                nodes respectively
                                                        For example:
                                                            [<path_1>] - same index location for all the nodes
                                                            [<path_1>, <path_2>, <path_3>] - different index
                                                            location for index server with 3 nodes
                index_server_roles              (list)  --  list of role names to be assigned
                index_pool_name                 (str)   --  name for the index pool to used by cloud index server
                cloud_param                     (list)  --  list of custom parameters to be parsed
                                                into the json for index server meta info
                                                [
                                                    {
                                                        "name": <name>,
                                                        "value": <value>
                                                    }
                                                ]
                is_cloud                        (bool)  --  if true then creates a cloud mode index server

            Returns:
                IndexServer() object of the newly created index server

        """
        log = logger.get_log()
        if commcell_object.index_servers.has(index_server_name):
            log.info("Index server exists, deleting and recreating")
            commcell_object.index_servers.delete(index_server_name)
        log.info("Creating new index server now")
        commcell_object.index_servers.create(index_server_name, index_server_node_names, index_directories,
                                             index_server_roles, index_pool_name, is_cloud, cloud_param)
        log.info("Index server created successfully")
        return commcell_object.index_servers.get(index_server_name)

    @staticmethod
    def set_compute_folder_stats_key(commcell_object, client_name, is_enabled=True):
        """Update/create compute folder stats key in registry

            Args:
                commcell_object             (object)    --  commcell object
                client_name                 (str)       --  index server node name
                is_enabled                  (bool)      --  if True then updates the key's value as true else false

            Returns:
                None

        """
        log = logger.get_log()
        if not commcell_object.clients.has_client(client_name):
            log.info("Provided Client does not exist")
            return
        set_value = ['false', 'true'][is_enabled]
        client_machine_obj = Machine(machine_name=client_name, commcell_object=commcell_object)
        config_exists = client_machine_obj.check_registry_exists(key=f"{dynamic_constants.SOLR_CONFIG_REG_KEY_PATH}")
        if config_exists:
            key_exists = client_machine_obj.check_registry_exists(key=f"{dynamic_constants.SOLR_CONFIG_REG_KEY_PATH}",
                                                                  value=dynamic_constants.SOLR_COMPUTE_FOLDER_STATS_KEY)
            if key_exists:
                log.info(f"Registry key exist updating the same key with string value : {set_value}")
                client_machine_obj.update_registry(key=f"{dynamic_constants.SOLR_CONFIG_REG_KEY_PATH}",
                                                   value=dynamic_constants.SOLR_COMPUTE_FOLDER_STATS_KEY,
                                                   data=set_value)
        else:
            log.info(f"Registry key does not exist creating new key with string value : {set_value}")
            client_machine_obj.create_registry(key=f"{dynamic_constants.SOLR_CONFIG_REG_KEY_PATH}",
                                               value=dynamic_constants.SOLR_COMPUTE_FOLDER_STATS_KEY,
                                               data=set_value, reg_type='String')
        log.info("Restarting DA service on Index node")
        commcell_object.clients.get(client_name).restart_service(dynamic_constants.ANALYTICS_SERVICE_NAME)
        log.info("Waiting for 120 seconds before resuming")
        sleep(120)

    @staticmethod
    def get_new_index_directory(commcell_object, index_node_name, custom_string=""):
        """Returns a valid index directory path on the index server node machine

            Args:
                commcell_object     (object)    -   Commcell object
                index_node_name     (str)       -   Index server node's client name
                custom_string       (str)       -   Custom string to be appended at the end of the folder name

            Returns:
                String  -   a valid index directory path

        """
        index_dir_folder_name = dynamic_constants.INDEX_DIRECTORY_DEFAULT_NAME % custom_string
        options_selector_object = OptionsSelector(commcell_object)
        drive_name = options_selector_object.get_drive(
            Machine(machine_name=index_node_name,
                    commcell_object=commcell_object))
        return f"{drive_name}{index_dir_folder_name}"

    def verify_job_completion(self, commcell_obj, operation):
        """
        Finds the job id & verifies if the given job completed or not

        Args:
            commcell_obj    (object):   Commcell Object
            operation       (str):  operation performed (to find the job id)
        """
        jobs_commcell_obj = commcell_obj.job_controller
        active_jobs = jobs_commcell_obj.active_jobs()
        self.log.info(f"Active Jobs While {operation} Operation {active_jobs}")
        job_id = None
        for item in active_jobs:
            if active_jobs[item]['operation'] == operation:
                job_id = item
                break
        if not job_id:
            self.log.info(f"Listing the finished jobs for last 1 hour to check if {operation} exist there")
            finished_jobs = jobs_commcell_obj.finished_jobs(lookup_time=1)
            self.log.info(f"Finished Jobs While {operation} Operation {finished_jobs}")
            for item in finished_jobs:
                if finished_jobs[item]['operation'] == operation:
                    job_id = item
                    break
        if not job_id:
            raise Exception(f"Cannot Find Job ID for Operation {operation}")
        if not jobs_commcell_obj.get(job_id).wait_for_completion():
            raise Exception(f"Operation {operation} doesn't completed properly")

    def invoke_index_server_stats_sync(self, index_server_nodes, usernames, passwords):
        """
        Invoke Index Server Stats Sync

        Args:
            index_server_nodes  (list): List of the Index Server Nodes
            usernames           (list): Username list to access the nodes
            passwords           (list): password list corresponding to each username

        """
        for index in range(len(index_server_nodes)):
            machine_obj = Machine(index_server_nodes[index],
                                  username=usernames[index],
                                  password=passwords[index])
            if machine_obj.check_registry_exists(key="Analytics", value=LAST_INDEX_SERVER_STATS_SYNC_TIME):
                machine_obj.remove_registry(key="Analytics", value=LAST_INDEX_SERVER_STATS_SYNC_TIME)
            machine_obj.kill_process("CVD")
            machine_obj.execute_command(f'Start-Service -Name "{CVD_SERVICE_NAME}"')
        self.log.info('Sleeping for 120 seconds')
        sleep(120)
        for index in range(len(index_server_nodes)):
            machine_obj = Machine(index_server_nodes[index],
                                  username=usernames[index],
                                  password=passwords[index])
            if not machine_obj.check_registry_exists(key="Analytics", value=LAST_INDEX_SERVER_STATS_SYNC_TIME):
                raise Exception("Invoking of Index Server Stats Sync Failed")
        self.log.info("Index Server Stats Sync Completed")

    def set_unload_core_settings(self, max_core_loaded='100', idle_core_timeout='1800', enabled=True):
        """sets unload core additional settings on index server

            Args:

                max_core_loaded         (str)       --  Maximum number of loaded cores in solr to start off with unload

                idle_core_timeout       (str)       --  seconds after which solr core would be considered as Idle core

                enabled                 (bool)      --  Specifies whether this feature is to enabled or disabled (default : True)

            Returns:

                 None

            Raises:

                Exception:

                    if failed to add additional settings
        """
        self.log.info(f"Setting maxloadedcores as [{max_core_loaded}] and idletimeout as [{idle_core_timeout}] secs")
        feature = 0
        if enabled:
            feature = 1
        nodes = self.index_server_obj.client_name
        for node in nodes:
            self.log.info(f"Working on Index node : {node}")
            machine_obj = Machine(machine_name=node, commcell_object=self.commcell)
            machine_obj.remove_registry(
                key=dynamic_constants.ANALYTICS_REG_KEY,
                value=dynamic_constants.IDLE_CORE_ENABLE_REG_KEY)
            machine_obj.remove_registry(
                key=dynamic_constants.ANALYTICS_REG_KEY,
                value=dynamic_constants.MAX_LOADED_CORE_REG_KEY)
            machine_obj.remove_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                        value=dynamic_constants.IDLE_CORE_TIMEOUT_REG_KEY)
            if enabled:
                update = machine_obj.create_registry(
                    key=dynamic_constants.ANALYTICS_REG_KEY,
                    value=dynamic_constants.MAX_LOADED_CORE_REG_KEY,
                    data=max_core_loaded,
                    reg_type=dynamic_constants.REG_STRING)
                if not update:
                    raise Exception(f"Failed to add Max loaded core registry key on node - {node}")
                update = machine_obj.create_registry(
                    key=dynamic_constants.ANALYTICS_REG_KEY,
                    value=dynamic_constants.IDLE_CORE_TIMEOUT_REG_KEY,
                    data=idle_core_timeout,
                    reg_type=dynamic_constants.REG_STRING)
                if not update:
                    raise Exception(f"Failed to add Idle timeout core registry key on node - {node}")
            else:
                update = machine_obj.create_registry(
                    key=dynamic_constants.ANALYTICS_REG_KEY,
                    value=dynamic_constants.IDLE_CORE_ENABLE_REG_KEY,
                    data=feature,
                    reg_type=dynamic_constants.REG_DWORD)
                if not update:
                    raise Exception(f"Failed to add Unload core feature enable registry key on node - {node}")

    def is_core_loaded(self, core_name):
        """returns whether core is in loaded or unloaded state

            Args:

                core_name           (str)       --  Core name to check load status

            Returns:

                bool    --  Specifies whether core is in loaded status or unloaded status

            Raises:

                Exception:

                    if failed to find core details
        """
        nodes = self.index_server_obj.client_name
        for node in nodes:
            self.log.info(f"Working on Index node : {node}")
            cores, core_details = self.index_server_obj.get_all_cores(client_name=node)
            if core_name in cores:
                self.log.info(f"Core[{core_name}] found in node[{node}]. Checking the status")
                if dynamic_constants.FIELD_START_TIME in core_details[core_name] and dynamic_constants.FIELD_UPTIME in \
                        core_details[core_name]:
                    self.log.info(
                        f"Core[{core_name}] is in loaded state with Uptime : [{core_details[core_name][dynamic_constants.FIELD_UPTIME]}]")
                    return True
                self.log.info(
                    f"Core[{core_name}] is in unloaded state")
                return False
        raise Exception(f"Core[{core_name}] not found in this index server nodes. Please check")

    def get_core_stats(self, core_name):
        """returns core stats from index server

            Args:

                core_name           (str)       --  Core name to get stats

            Returns:

                dict    --  core stats like uptime, start time etc

                    Example - {
                                  "name":"indexserverinfo",
                                  "instanceDir":"C:\\Program Files\\Commvault\\ContentStore\\CVAnalytics\\DataCube\\conf\\solr\\indexserverinfo",
                                  "dataDir":"C:\\Program Files\\Commvault\\AnalyticsIndex\\indexserverinfo\\",
                                  "config":"solrconfig.xml",
                                  "schema":"schema.xml",
                                  "startTime":"2023-04-12T08:17:41.911Z",
                                  "uptime":2900508,
                                  "index":{
                                    "numDocs":1546847,
                                    "maxDoc":2093395,
                                    "deletedDocs":546548,
                                    "indexHeapUsageBytes":328752,
                                    "version":807285,
                                    "segmentCount":20,
                                    "current":true,
                                    "hasDeletions":true,
                                    "directory":"org.apache.lucene.store.MMapDirectory:MMapDirectory@C:\\Program Files\\Commvault\\AnalyticsIndex\\indexserverinfo\\index lockFactory=org.apache.lucene.store.NativeFSLockFactory@63122be9",
                                    "segmentsFile":"segments_42iq",
                                    "segmentsFileSizeInBytes":1825,
                                    "userData":{
                                      "commitTimeMSec":"1681289969606",
                                      "commitCommandVer":"0"},
                                    "lastModified":"2023-04-12T08:59:29.606Z",
                                    "sizeInBytes":783287220,
                                    "size":"747 MB"
                            }

            Raises:

                Exception:

                    if failed to find core details
        """
        nodes = self.index_server_obj.client_name
        for node in nodes:
            self.log.info(f"Working on Index node : {node}")
            cores, core_details = self.index_server_obj.get_all_cores(client_name=node)
            if core_name in cores:
                self.log.info(f"Core[{core_name}] found in node[{node}]. Checking the status")
                if dynamic_constants.FIELD_START_TIME in core_details[core_name] and dynamic_constants.FIELD_UPTIME in \
                        core_details[core_name]:
                    self.log.info(
                        f"Core[{core_name}] is in loaded state with Uptime : [{core_details[core_name][dynamic_constants.FIELD_UPTIME]}]")
                else:
                    self.log.info(
                        f"Core[{core_name}] is in unloaded state")
                return core_details[core_name]
        raise Exception(f"Core[{core_name}] not found in this index server nodes. Please check")

    def read_thresholds(self, health_summary_info):
        """Read thresholds and segregate by indicator type
        Args:
            health_summary_info           (str)       --  Health summary string
        Returns:
            dict    --  returns type based indicator values
        """
        thresholds = {}
        try:
            payload = json.loads(health_summary_info)
            for name, value in dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS.items():
                self.log.info('Fetch thresholds for resource type [{}]'.format(
                    dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS[name]))
                thresholds[dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS[name]] = payload[value]['ThresholdValues']
        except Exception as error:
            self.log.error("Could not fetch heath indicators")
        return thresholds

    def wait_for_summary_doc_sync(self, extended_wait=False):
        """Wait for summary document generation"""
        import time
        interval = dynamic_constants.INDEX_SERVER_HEALTH_SUMMARY_DOC_TRIGGER_INTERVAL_IN_MINS * 60
        if extended_wait:
            interval = interval * 5
        self.log.info('Wait for indicators to sync for [{}] seconds'.format(
            interval))
        time.sleep(interval)

    def get_index_server_health_summary(self):
        """Fetch index server health indicator thresholds
         Returns:

                dict -- indicator thresholds
                dict -- action code and summary
        """
        import lxml.etree as et
        thresholds = {}
        action_code_summary = {}
        response = None
        action_code = None
        action_required = None
        health_summary_details = None
        try:
            # self.change_summary_doc_generation_configuration()
            response = self.index_server_obj.get_health_indicators()
            if response is not None:
                response = response.content
                xml = et.fromstring(response)
                for name, value in sorted(xml.items()):
                    if name == 'info':
                        health_summary_details = value
                    elif name == 'actionCode':
                        action_code = value
                    elif name == 'actionRequired':
                        action_required = value
                thresholds = self.read_thresholds(health_summary_details)
                action_code_summary[action_code] = action_required
            else:
                raise Exception('Invalid response from index server.')
            self.log.info("Indicators summary [{}]".format(thresholds))
            self.log.info("Action code summary [{}]".format(action_code_summary))
        except Exception as error:
            self.log.error("Could not fetch solr health summary due to [{}]".format(error))
            return thresholds, action_code_summary
        return thresholds, action_code_summary

    def poll_index_server_service(self, client_name, track_up=False, track_down=False):
        """Poll index server process when the service is coming up or down
        Args:
            client_name           (str)       --  Health summary string
            track_up              (bool)      -- track when service is coming up
            track_down            (bool)      -- track when service is going down

        Returns:
            bool    --  returns True/False
        """
        num_pings = 0
        max_pings = 1
        try:
            machine_obj = Machine(machine_name=client_name,
                                  commcell_object=self.commcell)
            if track_up:
                running = False
                while not running:
                    if machine_obj.is_process_running(dynamic_constants.ANALYTICS_PROCESS_NAME):
                        self.log.info('Index Server on client [{}] is up.'.format(client_name))
                        running = True
                    else:
                        if num_pings > max_pings:
                            return False
                        sleep(dynamic_constants.ANALYTICS_SERVICE_TIME_OUT)
                        num_pings = num_pings + 1
                if running:
                    return True
            elif track_down:
                self.log.info('Tracking if service is down')
                running = True
                while running:
                    if not machine_obj.is_process_running(dynamic_constants.ANALYTICS_PROCESS_NAME):
                        self.log.info('Index Server on client [{}] is down.'.format(client_name))
                        running = False
                    else:
                        if num_pings > max_pings:
                            return False
                    sleep(dynamic_constants.ANALYTICS_SERVICE_TIME_OUT)
                    num_pings = num_pings + 1
                if not running:
                    return True
        except Exception as error:
            self.log.error("Could not track index server service")
        return False

    def recycle_index_server(self, client_name):
        """Recycle and track index server service """
        try:
            self.log.info(f"Going to restart index server")
            client_obj = self.commcell.clients.get(client_name)
            machine_obj = Machine(machine_name=client_name,
                                  commcell_object=self.commcell)
            client_obj.restart_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
            sleep(dynamic_constants.ANALYTICS_SERVICE_TIME_OUT)
            if machine_obj.is_process_running(dynamic_constants.ANALYTICS_PROCESS_NAME):
                machine_obj.kill_process(process_name=dynamic_constants.ANALYTICS_PROCESS_NAME)
                self.poll_index_server_service(client_name, track_down=True)
            client_obj.start_service(dynamic_constants.ANALYTICS_SERVICE_NAME)
            self.poll_index_server_service(client_name, track_up=True)
        except Exception as error:
            self.log.error('Could not recycle index server [{}] due to [{}]'.format(client_name, error))

    def manage_index_server_access_control(self, enable=False, disable=False):
        """Disable access control so that non client controllers can make index server calls
        Args:
            enable           (bool)       --  Enable access control
            disable          (bool)      -- Disable access control

        Returns:
            bool    --  returns True/False
        """
        flag = None
        index_server_client = self.index_server_obj.client_name[0]
        try:
            if disable:
                self.log.info("Going to disable access control for index server node [{}]".format(
                    index_server_client))
                flag = "1"
            elif enable:
                self.log.info("Going to enable access control for index server node [{}]".format(
                    index_server_client))
                flag = "0"
            self.client_obj = self.commcell.clients.get(index_server_client)
            machine_obj = Machine(machine_name=index_server_client,
                                  commcell_object=self.commcell)
            machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                        value=dynamic_constants.ANALYTICS_DISABLE_ACCESS_CONTROL_REG_KEY,
                                        data=flag,
                                        reg_type=dynamic_constants.REG_STRING)
            self.recycle_index_server(index_server_client)
        except Exception as error:
            self.log.error("Failed to enable/disable access control due to [{}]".format(error))
            return False
        return True

    def set_index_server_health_environment(self):
        """Configure quartz scheduler with time interval"""
        self.log.info('Setting registry to expedite summary doc generation.')
        try:
            index_server_client = self.index_server_obj.client_name[0]
            self.client_obj = self.commcell.clients.get(index_server_client)
            machine_obj = Machine(machine_name=index_server_client,
                                  commcell_object=self.commcell)
            machine_obj.create_registry(key=dynamic_constants.SOLR_CONFIG_REG_KEY_PATH,
                                        value=dynamic_constants.INDEX_SERVER_HEALTH_RUN_SCHEDULER_AT_INTERVAL,
                                        data="true",
                                        reg_type=dynamic_constants.REG_STRING)
            machine_obj.create_registry(key=dynamic_constants.SOLR_CONFIG_REG_KEY_PATH,
                                        value=dynamic_constants.INDEX_SERVER_HEALTH_SUMMARY_DOC_TRIGGER_INTERVAL,
                                        data=str(1 * 60),
                                        reg_type=dynamic_constants.REG_STRING)
            self.manage_index_server_access_control(disable=True)
        except Exception as e:
            self.log.error('Could not set the configuration due to [{}]'.format(e))

    # Formula is (currentDiskSpaceFree < min(totalDiskCapacity * thresholdFreeDiskSpacePercentage / 100,
    #                                thresholdFreeDiskSpaceBytes) then alert
    def set_validate_disk_indicator(self):
        """Override disk health indicators"""

        index_server_client = self.index_server_obj.client_name[0]
        self.client_obj = self.commcell.clients.get(index_server_client)
        machine_obj = Machine(machine_name=index_server_client,
                              commcell_object=self.commcell)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_DISK_SPACE_PERCENTAGE,
                                    data=100,
                                    reg_type=dynamic_constants.REG_DWORD)
        self.recycle_index_server(index_server_client)

    def set_validate_cpu_indicator(self):
        """Override CPU health indicators"""
        index_server_client = self.index_server_obj.client_name[0]
        self.client_obj = self.commcell.clients.get(index_server_client)
        machine_obj = Machine(machine_name=index_server_client,
                              commcell_object=self.commcell)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_CPU_USAGE_MEDIAN_THRESHOLD,
                                    data=1,
                                    reg_type=dynamic_constants.REG_DWORD)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_MAX_CPU_CORES_THRESHOLD,
                                    data=32,
                                    reg_type=dynamic_constants.REG_DWORD)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_MAX_CPU_USAGE_THRESHOLD,
                                    data=1,
                                    reg_type=dynamic_constants.REG_DWORD)
        self.recycle_index_server(index_server_client)

    # INDEX_SERVER_HEALTH_MEM_USAGE_PERCENTAGE_THRESHOLD = 'heapMemUsagePercentageThreshold'
    # INDEX_SERVER_HEALTH_MEM_EXCEEDED_TIME = 'heapMemoryExceededTimes'
    # INDEX_SERVER_HEALTH_MEM_BYTES_THRESHOLD = 'thresholdHeapMemoryBytes'

    def set_validate_memory_indicator(self):
        """Override memory health indicators"""
        index_server_client = self.index_server_obj.client_name[0]
        self.client_obj = self.commcell.clients.get(index_server_client)
        machine_obj = Machine(machine_name=index_server_client,
                              commcell_object=self.commcell)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_MEM_USAGE_PERCENTAGE_THRESHOLD,
                                    data=1,
                                    reg_type=dynamic_constants.REG_DWORD)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_MEM_EXCEEDED_TIME,
                                    data=1,
                                    reg_type=dynamic_constants.REG_DWORD)
        machine_obj.create_registry(key=dynamic_constants.ANALYTICS_REG_KEY,
                                    value=dynamic_constants.INDEX_SERVER_HEALTH_MEM_BYTES_THRESHOLD,
                                    data=512,
                                    reg_type=dynamic_constants.REG_DWORD)
        self.recycle_index_server(index_server_client)

    def validate_default_indicators(self, indicator_type, indicator_name, indicator_value):
        """Validate default thresholds"""
        n_success = False
        self.log.info(
            'Validating  [{}] type indicator - Indicator name [{}] & value [{}]'.format(indicator_type, indicator_name,
                                                                                        indicator_value))
        if indicator_type == dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS['DISK']:
            if indicator_name in dynamic_constants.INDEX_SERVER_HEALTH_DISK_THRESHOLDS:
                if indicator_value == dynamic_constants.INDEX_SERVER_HEALTH_DISK_THRESHOLDS[indicator_name]:
                    n_success = True
        elif indicator_type == dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS['MEMORY']:
            if indicator_name in dynamic_constants.INDEX_SERVER_HEALTH_MEMORY_THRESHOLDS:
                if indicator_value == dynamic_constants.INDEX_SERVER_HEALTH_MEMORY_THRESHOLDS[indicator_name]:
                    n_success = True
        elif indicator_type == dynamic_constants.INDEX_SERVER_HEALTH_INDICATORS['CPU']:
            if indicator_name in dynamic_constants.INDEX_SERVER_HEALTH_CPU_THRESHOLDS:
                if indicator_value == dynamic_constants.INDEX_SERVER_HEALTH_CPU_THRESHOLDS[indicator_name]:
                    n_success = True
        else:
            self.log.info('Unknown indicator name [{}] or type [{}]'.format(indicator_name, indicator_type))
        return n_success

    def cleanup_monitoring(self, indicator_type):
        """
        Clean up monitoring documents for a specific resource type i.e disk, cpu and mem
        :return: True/False
        """
        try:
            query_dict = dict()
            query_dict['DocumentType'] = 'monitoring'
            query_dict['ResourceType'] = indicator_type
            self.log.info('Cleaning up monitoring documents for indicator [{}]'.format(indicator_type))
            self.index_server_obj.delete_docs_from_core(
                dynamic_constants.INDEX_SERVER_HEALTH_MONITORING_SOLR_COLLECTION, query_dict)
        except Exception as e:
            self.log.error('Could not cleanup monitoring')
            return False
        return True

    def check_and_remove_indicators(self, key_location, key_name):
        """Check and remove registry based indicators"""
        out = None
        try:
            self.log.info('Checking for key [{}] at [{}]'.format(key_name, key_location))
            index_server_client = self.index_server_obj.client_name[0]
            machine_obj = Machine(machine_name=index_server_client,
                                  commcell_object=self.commcell)
            out = machine_obj.check_registry_exists(key_location,
                                                    key_name)
            if out:
                self.log.info('Key [{}] exist. Removing from registry.'.format(key_name))
                out = machine_obj.remove_registry(key_location, key_name)
                if out:
                    self.log.info('Registry key is removed successfully')
                else:
                    raise Exception('Failed to remove the registry key [{}] from [{}]'.format(key_name, key_location))

        except Exception as error:
            self.log.error('Error : [{}]'.format(error))
