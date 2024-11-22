# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Constants file for performing IntelliSnap operations

VSASNAPConstants is the only class defined in this file

VSASNAPConstants: constants class to perform IntelliSnap operations

VSASNAPConstants:

    __init__()                   --  initializes Snap constant object


    execute_query()              --  Executes SQL query

"""

from __future__ import unicode_literals
import json
from AutomationUtils.database_helper import get_csdb


class VSASNAPConstants(object):
    """Constants class to perform snap operations"""

    def __init__(self, commcell, tcinputs):
        """Initializes Snapconstants object

            Args:
                commcell        (object)    --  commcell object

                tcinputs        (object)    --  test case input object


        """

        self.commcell = commcell
        self._csdb = get_csdb()
        self.tcinputs = tcinputs

        self.get_controlhost_id = "SELECT RefId FROM SMHostAlias WHERE AliasName = '{a}'"
        self.get_gad_controlhost_id = """SELECT ControlHostID from SMControlHost where ControlHostId in
        (SELECT arrayID from SMConfigs where MasterConfigId =164 and ValueStr like '{a}') and SMArrayID like '{b}'"""
        self.get_master_config_id = """SELECT config.id FROM SMMasterConfigs AS config
                                            INNER JOIN SMVendor AS vendor ON config.VendorId = vendor.id		
                                            WHERE config.Name LIKE '{a}' AND vendor.Name LIKE '{b}'"""
        self.vplex_control_host = """SELECT ControlHostId,ReserveField2 FROM SMsnap WHERE SMSnapId
                                            IN (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId = {a})"""
        self.get_mount_control_host = """SELECT ControlHostId FROM SMsnap WHERE SnapStatus = 12 and SMSnapId in
                                            (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in 
                                            (SELECT SMVolumeId from SMVolume WHERE JobId = {a}))"""
        self.get_bkpcopy_mount_control_host = """
        SELECT ControlHostId from SMSnap where SMSnapId in 
        (SELECT SMSnapId FROM SMMountSnap WHERE SnapStatus = 12 and SMSnapId in 
        (SELECT SMSnapId FROM SMMountMap WHERE SMVolumeId in 
        (SELECT SMVolumeId from SMMountVolume WHERE MountJobId = {a})))"""
        self.get_bkpcopy_parent_jid = """select childJobId from JMJobWF where jobid = {a} and processedJobId = {b}"""
        self.get_mountvolume_id = "SELECT SMVolumeId FROM SMMountVolume WHERE MountjobID = {a} AND MountStatus = {b}"
        self.get_mounthost_id = "SELECT MountHostId FROM SMMountVolume WHERE MountJobId = {a} AND MountStatus = {b}"
        self.get_control_host = """SELECT ControlHostId FROM SMsnap WHERE SMSnapId in
                                            (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in 
                                            (SELECT SMVolumeId from SMVolume WHERE JobId = {a}))"""
        self.get_vendor_id = "SELECT Id FROM SMVendor WHERE Name = '{a}'"
        self.get_volume_id = "SELECT SMVolumeId FROM SMVolume WHERE (jobID = {a} or MasterJobId ={a}) AND CopyId = {b}"

        self.get_mount_path = "SELECT MountPath FROM SMVolume WHERE JobId = {a} AND CopyId = {b}"

        self.ocum_server = self.tcinputs.get('OCUMServerName', None)
        self.arrayname = self.tcinputs.get('ArrayName', None)
        self.arrayname2 = self.tcinputs.get('ArrayName2', None)
        self.config_update_level = "array"
        self.array_access_nodes_to_edit = self.tcinputs.get('array_access_nodes_to_edit_array', None)
        access_nodes = self.tcinputs.get('array_access_nodes_to_add_array', None)
        self.get_volumelist_id = "SELECT SMVolumeId FROM SMVolume WHERE (jobID in  {a}) AND CopyId = {b}"
        self.get_snap_id = """SELECT SMSnapId FROM SMsnap WHERE SMSnapId in
                                (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in 
                                (SELECT SMVolumeId from SMVolume WHERE (JobId in ({a}) or MasterJobId in ({a}))))"""
        self.get_snapengine_id = "SELECT SnapShotEngineId from SMSnapShotEngine  where \
                                                  SnapEngineName = '{a}'"
        self.get_backupcopy_status = "select materializationStatus from JMJobSnapshotStats where jobid in {a}"

        if access_nodes is not None:
            self.array_access_nodes_to_add = list(access_nodes.split(","))
        else:
            self.array_access_nodes_to_add = None

        self.is_ocum = False
        self.source_config = self.tcinputs.get('SourceSnapConfig', None)
        if isinstance(self.source_config, str):
            self.source_config = json.loads(self.source_config)
        self.target_config = self.tcinputs.get('TargetSnapConfig', None)
        if isinstance(self.target_config, str):
            self.target_config = json.loads(self.target_config)
        self.source_config_add_array = self.tcinputs.get('SourceSnapConfigAddArray', None)
        if isinstance(self.source_config_add_array, str):
            self.source_config_add_array = json.loads(self.source_config_add_array)
        self.target_config_add_array = self.tcinputs.get('TargetSnapConfigAddArray', None)
        if isinstance(self.target_config_add_array, str):
            self.target_config_add_array = json.loads(self.target_config_add_array)
        self.auto_subclient = None
        self.auto_instance = None
        self.auto_comcell = None
        self.auto_client = None
        self.secondary_copies = []
        self.mountpath_val = None
        self.proxy_client = self.tcinputs.get('ProxyMA', None)
        self.vsm_array_name1 = self.tcinputs.get('VSMArrayName1', None)
        self.vsm_array_name2 = self.tcinputs.get('VSMArrayName2', None)
        self.vsm_to_vsm = self.tcinputs.get('VSMtoVSM', None)

    def execute_query(self, query, my_options=None, fetch_rows='all'):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options      (dict)  -- options in the query
                default: None

                fetch_rows      (str)   -- By default return all rows, if not return one row
            Return:
                    str : first column of the sql output

        """
        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))

        if fetch_rows != 'all':
            return self._csdb.fetch_one_row()[0]
        return self._csdb.fetch_all_rows()
