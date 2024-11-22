# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for datacube sync

    SyncHelper:
        __init__(testcase)          --  Initialize the DcubesyncHelper object

        setdcubesync_registry(current_time,client_id,totalhours,enablesync)
                                    -- Set sync related registry on CS


        getsyncxml_bycsrestart(datasource_id) -- Get sync xml for the given datasource id

        getcorestats(self,core_name,index_server)
                                    -- Get the stats for the given data source core

        verifysyncxml(self,sync_xml,corestats,lastsynctime,facetstats=None,maxstats=None)
                                            -- verify the sync xml for the datasource

        execute_metering_sp()       --  Executes the license metering stored procedure for Activate solutions

        validate_metering()         --  Validates metering for SDG/FSO


"""
import datetime
import time
import xmltodict
from cvpysdk.activateapps.constants import TargetApps

from AutomationUtils.config import get_config
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.machine import Machine
from dynamicindex.utils import constants as dynamic_constants

_CS_CONFIG_DATA = get_config().SQL


class SyncHelper():

    """ contains helper class for datacube sync
        """

    def __init__(self, tc_object):
        self.commcell = tc_object.commcell
        self.csdb = tc_object.csdb
        self.log = tc_object.log
        self.dssync_regname = "nLastDCubeSyncTime"
        self.dssync_disablereg = "nDCubeSyncDisable"
        self.dssync_regtype = "DWord"
        self.testcase = tc_object

    def set_dcube_sync_registry(self, current_time, client_id, totalhours, enablesync):
        """Set datacube sync related registry keys on given client id (CS)

                Args:
                    current_time(datetime) --  Now time
                    client_id(int)         --  id of client.
                    totalhours(int)        --  Total hours which needs to set behind
                    enablesync(boolean)    -- to enable sync or not

                Raises
                    Exception on failure

                """
        self.log.info("Current Epoch time : " + str(int(current_time.timestamp())))
        oneday_ago = current_time - datetime.timedelta(hours=totalhours)
        oneday_ago_epoch = int(oneday_ago.timestamp())
        self.log.info("Going to set nLastDCubeSyncTime as 24 hrs behind : %s",
                      str(oneday_ago_epoch))
        self.cs_machineobj = Machine(self.commcell.clients.get(client_id), self.commcell)
        reg_key = "CommServe"
        update_success = self.cs_machineobj.update_registry(
            reg_key, self.dssync_regname, oneday_ago_epoch, self.dssync_regtype)
        if not update_success:
            self.log.info("Unable to set datacube sync registry. Abort")
            raise Exception("Unable to set datacube sync registry. Abort")

        # Make sure below registry is not set
        if enablesync:
            update_success = self.cs_machineobj.create_registry(
                reg_key, self.dssync_disablereg, "0", self.dssync_regtype)
        else:
            update_success = self.cs_machineobj.create_registry(
                reg_key, self.dssync_disablereg, "1", self.dssync_regtype)

        if not update_success:
            self.log.info("Unable to set datacube disable sync registry. Abort")
            raise Exception("Unable to set datacube disable sync registry. Abort")

    def get_syncxml_by_csrestart(self, datasource_id, restart_required=True):
        """Returns the sync xml for the given datasource id

                Args:
                    datasource_id(str)   --  id of the datasource

                    restart_required(bool)  --  Whether to do restart of service before collecting sync xml

                Returns

                    str              -- status xml of the datasource


                Raises

                    Exception on failure


                """
        self.dsprop_query = "select PropertyValue from SEDataSourceproperty " \
                            "where PropertyId=107 and DataSourceId= %s"
        self.cs_clientobj = self.commcell.commserv_client
        if restart_required:
            self.log.info("Going to restart all services on CS")
            try:
                self.cs_clientobj.restart_services(wait_for_service_restart=True, timeout=15, implicit_wait=10)
            except Exception:
                print("Warning for recycle services")
            self.log.info("Waiting for 10 Mins")
            time.sleep(600)
        _query = (self.dsprop_query % datasource_id)
        self.log.info("Querying CS DB to get status info properties")
        self.csdb.execute(_query)
        statusxml = self.csdb.fetch_one_row()
        statusxml = ''.join(str(x) for x in statusxml)
        self.log.info("Status xml from CS db : " + str(statusxml))
        if statusxml is None:
            raise Exception("Status xml is empty. Datacube sync didnt happen within stipulated time!!!")
        return statusxml

    def get_core_stats(self, core_name, index_server, is_fso=True, ds_name=None, ds_id=None):
        """Returns the stats for given data source core

                        Args:
                            core_name (str)       --  Core Name of the data source

                            is_fso  (bool)        --  Specifies whether stats collection is for FSO or SDG DS

                            ds_name (int)         --  Specified data source name for multinode collection

                            ds_id   (int)         --  Specifies data source ID for multinode collection

                        Returns

                            dict              -- containing all stats

                        Raises

                            Exception on failure


        """
        ds_dict = None
        if ds_name:
            if ds_id:
                ds_dict = {dynamic_constants.DATA_SOURCE_NAME_KEY: ds_name,
                           dynamic_constants.DATA_SOURCE_ID_KEY: ds_id}
            else:
                ds_dict = {dynamic_constants.DATA_SOURCE_NAME_KEY: ds_name}
        self.log.info(f"DataSource Details to be used : {ds_dict}")
        stats_query = {
            dynamic_constants.STATS_PARAM: 'true',
            dynamic_constants.STATS_FIELD_SET_PARAM: dynamic_constants.SIZE_SOLR_KEY,
            dynamic_constants.ROWS_PARAM: 0
        }
        tot_select_dict = {**dynamic_constants.QUERY_NON_DELETE_ITEMS, **dynamic_constants.QUERY_FILE_CRITERIA}
        index_server_obj = self.commcell.index_servers.get(index_server)
        resp = index_server_obj.execute_solr_query(
            core_name=core_name, select_dict=tot_select_dict if ds_dict is None else {
                **ds_dict, **tot_select_dict}, op_params=stats_query)
        tot_sum_value = \
            resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][
                dynamic_constants.SIZE_SOLR_KEY][
                dynamic_constants.SUM_PARAM]
        tot_count_value = \
            resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][
                dynamic_constants.SIZE_SOLR_KEY][
                dynamic_constants.COUNT_PARAM]
        success_select_dict = {
            **dynamic_constants.QUERY_FILE_CRITERIA,
            **dynamic_constants.QUERY_CISTATE_ITEMSTATE_SUCCESS}
        resp = index_server_obj.execute_solr_query(
            core_name=core_name,
            select_dict=success_select_dict if ds_dict is None else {**ds_dict, **success_select_dict},
            op_params=stats_query)
        success_sum_value = \
            resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][
                dynamic_constants.SIZE_SOLR_KEY][
                dynamic_constants.SUM_PARAM]
        success_count_value = \
            resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][
                dynamic_constants.SIZE_SOLR_KEY][
                dynamic_constants.COUNT_PARAM]
        tot_sensitive_file = 0
        success_sensitive_file = 0
        if not is_fso:
            self.log.info("Collecting SDG Based sync stats for sensitive files")
            tot_sensitive_select_dict = {**dynamic_constants.QUERY_NON_DELETE_ITEMS,
                                         **dynamic_constants.QUERY_SENSITIVE_FILES}
            resp = index_server_obj.execute_solr_query(
                core_name=core_name,
                select_dict=tot_sensitive_select_dict if ds_dict is None else {**ds_dict, **tot_sensitive_select_dict},
                op_params=dynamic_constants.QUERY_ZERO_ROWS)
            tot_sensitive_file = resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]
            success_sensitive_select_dict = {
                **dynamic_constants.QUERY_CISTATE_ITEMSTATE_SUCCESS,
                **dynamic_constants.QUERY_SENSITIVE_FILES}
            resp = index_server_obj.execute_solr_query(
                core_name=core_name, select_dict=success_sensitive_select_dict if ds_dict is None else {
                    **ds_dict, **success_sensitive_select_dict}, op_params=dynamic_constants.QUERY_ZERO_ROWS)
            success_sensitive_file = resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]

        stats = {
            dynamic_constants.SYNC_TOTAL_PARAM: {
                dynamic_constants.NUM_FOUND_PARAM: tot_count_value,
                dynamic_constants.SIZE_SOLR_KEY: tot_sum_value,
                dynamic_constants.SENSITIVE_DOCS_PARAM: tot_sensitive_file},
            dynamic_constants.SYNC_SUCCESS_STATE_PARAM: {
                dynamic_constants.NUM_FOUND_PARAM: success_count_value,
                dynamic_constants.SIZE_SOLR_KEY: success_sum_value,
                dynamic_constants.SENSITIVE_DOCS_PARAM: success_sensitive_file
            }
        }
        self.log.info(f"Sync Stats formed - {stats}")
        return stats

    def verify_sync_xml(self, sync_xml, core_stats, is_fso=True, facet_stats=None):
        """verifies sync xml for the given corestats

                Args:
                    syncxml(str)      --  sync xml of datasource
                    corestats(dict)   -- core stats of data source
                    facetstats(dict)  -- FS facet stats
                    is_fso(bool)      -- denotes whether for FSO or SDG DataSources

                Returns:
                    True if success

                Raises

                    Exception on mismatch of sync xml data
        """
        self.log.info("Going to validate sync xml with core stats")
        sync_jobj = xmltodict.parse(sync_xml)
        total_json = sync_jobj['StatusInfo']['Total']
        success_state_json = sync_jobj['StatusInfo']['SuccessState']

        # total stats validation
        actual_val = int(total_json['@Documents'])
        expected_val = int(core_stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.NUM_FOUND_PARAM])
        if actual_val == expected_val:
            self.log.info("Total Docs matched : " + str(actual_val))
        else:
            raise Exception("Total Docs mismatched Actaul<{0}> Expected<{1}> "
                            .format(actual_val, expected_val))

        actual_val = int(total_json['@SizeAnalyzedInBytes'])
        expected_val = int(core_stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.SIZE_SOLR_KEY])
        if actual_val == expected_val:
            self.log.info("TotalSizeInBytes matched : " + str(actual_val))
        else:
            raise Exception("TotalSizeInBytes mismatched Actaul<{0}> Expected<{1}> "
                            .format(actual_val, expected_val))

        # success state validation

        actual_val = int(success_state_json['@Documents'])
        expected_val = int(core_stats[dynamic_constants.SYNC_SUCCESS_STATE_PARAM][dynamic_constants.NUM_FOUND_PARAM])
        if actual_val == expected_val:
            self.log.info("Success Docs matched : " + str(actual_val))
        else:
            raise Exception("Success Docs mismatched Actaul<{0}> Expected<{1}> "
                            .format(actual_val, expected_val))

        actual_val = int(success_state_json['@SizeAnalyzedInBytes'])
        expected_val = int(core_stats[dynamic_constants.SYNC_SUCCESS_STATE_PARAM][dynamic_constants.SIZE_SOLR_KEY])
        if actual_val == expected_val:
            self.log.info("Success state TotalSizeInBytes matched : " + str(actual_val))
        else:
            raise Exception("Success State TotalSizeInBytes mismatched Actaul<{0}> Expected<{1}> "
                            .format(actual_val, expected_val))

        # Sensitive files validation
        if is_fso:
            if int(total_json['@SensitiveDocuments']) or int(success_state_json['@SensitiveDocuments']):
                raise Exception(
                    f"Sensitive files[{total_json['@SensitiveDocuments']}] cant be present for FSO data source. Please check")
        else:
            actual_val = int(total_json['@SensitiveDocuments'])
            expected_val = int(core_stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.SENSITIVE_DOCS_PARAM])
            if actual_val == expected_val:
                self.log.info("Total Sensitive files count matched : " + str(actual_val))
            else:
                raise Exception("Total Sensitive files count mismatched Actaul<{0}> Expected<{1}> "
                                .format(actual_val, expected_val))

            actual_val = int(success_state_json['@SensitiveDocuments'])
            expected_val = int(core_stats[dynamic_constants.SYNC_SUCCESS_STATE_PARAM]
                               [dynamic_constants.SENSITIVE_DOCS_PARAM])
            if actual_val == expected_val:
                self.log.info("Success State Sensitive files count matched : " + str(actual_val))
            else:
                raise Exception("Success State Sensitive files count mismatched Actaul<{0}> Expected<{1}> "
                                .format(actual_val, expected_val))

        # user count validation
        if facet_stats is not None:
            self.log.info("Facetstats is not None. consider it as FS Datasource")
            actual_val = int(
                total_json['@Users'])
            expected_val = int(facet_stats[dynamic_constants.SYNC_TOTAL_PARAM]['Users'])
            if actual_val == expected_val:
                self.log.info("Total UsersCount matched : " + str(actual_val))
            else:
                raise Exception("Total UsersCount mismatched Actaul<{0}> Expected<{1}> "
                                .format(actual_val, expected_val))

            actual_val = int(
                success_state_json['@Users'])
            expected_val = int(facet_stats[dynamic_constants.SYNC_SUCCESS_STATE_PARAM]['Users'])
            if actual_val == expected_val:
                self.log.info("Success State UsersCount matched : " + str(actual_val))
            else:
                raise Exception("Success State UsersCount mismatched Actaul<{0}> Expected<{1}> "
                                .format(actual_val, expected_val))

        return True

    def execute_metering_sp(self, solutions):
        """executes stored procedure to get activate metering for solutions

                Args:

                    solutions       (Enum)       -- Enum from TargetApps[cvpysdk/activateapps/constants.py]

                returns:

                    obj -   DBResponse Object

        """
        ss_name_suffix = ""
        if 'windows' in self.commcell.commserv_client.os_info.lower():
            ss_name_suffix = dynamic_constants.DB_FIELD_COMMVAULT
        conn_str = self.commcell.commserv_hostname + ss_name_suffix
        self.log.info(f"CS Sql connection String - {conn_str}")
        _mssql = MSSQL(conn_str,
                       _CS_CONFIG_DATA.Username,
                       _CS_CONFIG_DATA.Password,
                       dynamic_constants.DB_FIELD_COMMSERV,
                       use_pyodbc=False)
        self.log.info("MSSql object initialized to CS")
        values = (1, solutions.value, 1, 1)
        db_resp = _mssql.execute_storedprocedure(
            "LicGetUsageForDCSolutions", values)
        _mssql.close()
        self.log.info(f"SP Response Returned [{len(db_resp.rows)}] rows.")
        self.log.info(f"Columns - [{db_resp.columns}] ")
        self.log.info(f"Row Data - [{db_resp.rows}]")
        return db_resp

    def validate_metering(self, metering_data, ds_id, stats, is_fso=True, client_id=None):
        """Validates metering data for fso/sdg against input stats

            Args:

                metering_data list(dict)  -- Metering data got from License SP execution

                ds_id       (int)       --  Data Source ID

                stats       (dict)      --   Data source stats

                is_fso      (bool)      --   denotes whether this is FSO or SDG

                client_id   (str)       --   Associated client id of data source

            Returns:

                None

            Raises:

                    Exception:

                        if stats mismatch
        """
        found = False
        for entry in metering_data:
            if entry[dynamic_constants.ASSOCIATED_DS_PARAM] == ds_id:
                found = True
                self.log.info(f"Found Metering info for Data Source [{ds_id}] - {entry}")
                if entry[dynamic_constants.SENSITIVE_DOCS_PARAM] != stats[dynamic_constants.SYNC_TOTAL_PARAM][
                        dynamic_constants.SENSITIVE_DOCS_PARAM]:
                    raise Exception(
                        f"Sensitive docs count mismatched. Expected [{stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.SENSITIVE_DOCS_PARAM]}] Actual [{entry[dynamic_constants.SENSITIVE_DOCS_PARAM]}]")
                if entry[dynamic_constants.DOCUMENTS_PARAM] != stats[dynamic_constants.SYNC_TOTAL_PARAM][
                        dynamic_constants.NUM_FOUND_PARAM]:
                    raise Exception(
                        f"Total docs count mismatched. Expected [{stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.NUM_FOUND_PARAM]}] Actual [{entry[dynamic_constants.DOCUMENTS_PARAM]}]")
                if entry[dynamic_constants.SIZE_IN_BYTES_PARAM] != stats[dynamic_constants.SYNC_TOTAL_PARAM][
                        dynamic_constants.SIZE_SOLR_KEY]:
                    raise Exception(
                        f"Size in bytes mismatched. Expected [{stats[dynamic_constants.SYNC_TOTAL_PARAM][dynamic_constants.SIZE_SOLR_KEY]}] Actual [{entry[dynamic_constants.SIZE_IN_BYTES_PARAM]}]")
                if is_fso and entry[dynamic_constants.SOLUTION_TYPE_PARAM] != TargetApps.FSO.value:
                    raise Exception(
                        f"Solution type mismatched - Expected [{TargetApps.FSO.value}] Actual [{entry[dynamic_constants.SOLUTION_TYPE_PARAM]}]")
                if not is_fso:
                    if entry[dynamic_constants.SOLUTION_TYPE_PARAM] != TargetApps.SDG.value:
                        raise Exception(
                            f"Solution type mismatched - Expected [{TargetApps.SDG.value}] Actual [{entry[dynamic_constants.SOLUTION_TYPE_PARAM]}]")
                if entry[dynamic_constants.ASSOCIATED_DS_TYPE_PARAM] != 'file':
                    raise Exception(f"Datasource type was wrong - {entry[dynamic_constants.ASSOCIATED_DS_TYPE_PARAM]}")
                if client_id:
                    if int(entry[dynamic_constants.ENTITY_ID_PARAM]) != int(client_id):
                        raise Exception(
                            f"Client ID not matched for data source. Expected [{client_id}] Actual [{entry[dynamic_constants.ENTITY_ID_PARAM]}]")
                self.log.info("Metering Validation Success")
                break
        if not found:
            raise Exception(f"Expected data source details are not found in metering SP results")
