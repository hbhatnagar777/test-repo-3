# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Constants file for performing IntelliSnap operations

SNAPConstants is the only class defined in this file

SNAPConstants: constants class to perform IntelliSnap operations

SNAPHelper:

    __init__()                   --  initializes Snap constant object

    folder_name()                --  Generates a random sting with 3 charactor's

    execute_query()              --  Executes SQL query

"""

from __future__ import unicode_literals
import random
import string
import json
from enum import Enum
from AutomationUtils.database_helper import get_csdb


class ReplicationType(Enum):
    PV = "pv"
    PM = "pm"
    PVM = "pvm"
    PMV = "pmv"
    PMM = "pmm"
    PV_Replica = "pv_replica"
    PM_Replica = "pm_replica"
    PVM_Replica = "pvm_replica"
    PMV_Replica = "pmv_replica"
    PMM_Replica = "pmm_replica"
    PVV_Replica = "pvv_replica"
    PV_Replica_c2c = "pv_replica_c2c"

class SnapConfig_level(Enum):
    array = 3
    copy = 6
    subclient = 9
    client = 8

class SNAPConstants(object):
    """Constants class to perform snap operations"""


    def __init__(self, commcell, client, agent, tcinputs):
        """Initializes Snapconstants object

            Args:
                commcell        (object)    --  commcell object

                client          (object)    --  client object

                agent           (object)    --  agent object

                tcinputs        (dict)      --  Test case inputs dictionary

        """

        self.commcell = commcell
        self._csdb = get_csdb()
        self.client = client
        self.agent = agent
        self.tcinputs = tcinputs
        self.snap_automation_output = self.tcinputs.get('SnapAutomationOutput', None)
        self.storage_policy = None
        self.job_tracker = []
        self.fanout_copies_vault = []
        self.fanout_copies_mirror = []
        self.random = random.randint(1, 10)
        self.test_data_path = []
        self.source_path = []
        self.test_data_folder = []
        self.copy_content_location = []
        self.deleted_content_location = []
        self.jobid = None
        self.windows_restore_location = None
        self.snap_outplace_restore_location = None
        self.tape_outplace_restore_location = None
        self.mount_path = None
        self.disk_lib_loc = None
        self.snap_engine_at_array = self.tcinputs['SnapEngineAtArray']
        self.snap_engine_at_subclient = self.tcinputs['SnapEngineAtSubclient']
        self.ocum_server = self.tcinputs.get('OCUMServerName', '')
        self.prov_policy_vault = self.tcinputs.get('ProvisioningPolicyForVault', None)
        self.prov_policy_mirror = self.tcinputs.get('ProvisioningPolicyForMirror', None)
        self.resource_pool_vault = self.tcinputs.get('ResourcePoolForVault', None)
        self.resource_pool_mirror = self.tcinputs.get('ResourcePoolForMirror', None)
        self.resource_pool_pmm = self.tcinputs.get('ResourcePoolForPMM', None)
        self.problematic_data = self.tcinputs.get("ProblematicData", None)
        self.scale_data = self.tcinputs.get('ScaleData', None)
        self.string = self.folder_name(self.snap_engine_at_array)
        self.disk_lib_name = "Auto_Lib_"+self.string
        self.storage_policy_name = "Auto_SP_"+self.string
        self.subclient_name = "Auto_SC_"+self.string
        self.subclient_content = self.tcinputs.get('SubclientContent', " ").replace(" ", "")
        self.backupset = None
        self.backupset_name = "Auto_BS_"+self.string
        self.disk_lib = None
        self.mountpath_val = None
        self.windows_restore_client = None
        self.mount_status = None
        self.name = None
        self.inline_bkp_cpy = False
        self.skip_catalog = self.tcinputs.get('SkipCatalog', None)
        if self.skip_catalog == 'True':
            self.skip_catalog = True
        else:
            self.skip_catalog = False
        self.backup_level = 'FULL'
        self.aux_copy_name = "AuxCopy"
        self.snap_copy_name = "Snap"
        self.first_node_copy = None
        self.second_node_copy = None
        self.config_update_level = "array"
        self.fanout_count_pv = self.tcinputs.get('fanout_count_pv', 2)
        self.fanout_count_pm = self.tcinputs.get('fanout_count_pm', 2)
        self.source_config = self.tcinputs.get('SourceSnapConfig', None)
        self.selectiveRule = self.tcinputs.get('selectiveRule', None)
        if self.source_config and type(self.source_config) is not dict:
            self.source_config = json.loads(self.source_config)
        self.source_config_del = self.tcinputs.get('SourceSnapConfigDelete', None)
        if self.source_config_del and type(self.source_config_del) is not dict:
            self.source_config_del = json.loads(self.source_config_del)
        self.target_config = self.tcinputs.get('TargetSnapConfig', None)
        if self.target_config and type(self.target_config) is not dict:
            self.target_config = json.loads(self.target_config)
        self.source_config_add_array = self.tcinputs.get('SourceSnapConfigAddArray', None)
        if self.source_config_add_array and type(self.source_config_add_array) is not dict:
            self.source_config_add_array = json.loads(self.source_config_add_array)
        self.target_config_add_array = self.tcinputs.get('TargetSnapConfigAddArray', None)
        if self.target_config_add_array and type(self.target_config_add_array) is not dict:
            self.target_config_add_array = json.loads(self.target_config_add_array)
        self.primary_snapconfigs_to_validate = self.tcinputs.get('PrimarySnapConfigsToValidate', None)
        if self.primary_snapconfigs_to_validate and type(self.primary_snapconfigs_to_validate) is not dict:
            self.primary_snapconfigs_to_validate = json.loads(self.primary_snapconfigs_to_validate)
        self.secondary_snapconfigs_to_validate = self.tcinputs.get('SecondarySnapConfigsToValidate', None)
        if self.secondary_snapconfigs_to_validate and type(self.secondary_snapconfigs_to_validate) is not dict:
            self.secondary_snapconfigs_to_validate = json.loads(self.secondary_snapconfigs_to_validate)
        self.config_level = "array"
        self.snap_configs = None
        self.phase = ["SCAN", "CATALOG", "ARCHIVE INDEX"]
        self.revert_support = self.tcinputs.get('skip_revert')
        self.type = self.tcinputs.get('ReplicationType')
        self.is_ocum = False
        self.multisite = False
        self.arrayname = self.tcinputs.get('ArrayName', None)
        self.arrayname2 = self.tcinputs.get('ArrayName2', None)
        self.arrayname3 = self.tcinputs.get('ArrayName3', None)
        self.username = self.tcinputs.get('ArrayUserName', None)
        if self.username:
            self.password = self.tcinputs.get('ArrayPassword')
        self.c2c_target_vendor = self.tcinputs.get('C2CTargetVendorName', None)
        self.is_suspend_job = self.tcinputs.get('SuspendJob', False)
        self.is_kill_process = self.tcinputs.get('KillProcess', False)
        self.controlhost = self.tcinputs.get('ControlHost', None)
        self.array_access_nodes_to_edit = self.tcinputs.get('array_access_nodes_to_edit_array', None)
        if (self.array_access_nodes_to_edit is not None and
                type(self.array_access_nodes_to_edit) is not dict):
            self.array_access_nodes_to_edit = json.loads(self.array_access_nodes_to_edit)
        access_nodes = self.tcinputs.get('array_access_nodes_to_add_array', None)
        if access_nodes is not None:
            self.array_access_nodes_to_add = list(access_nodes.split(","))
        else:
            self.array_access_nodes_to_add = None

        if self.ocum_server is None or self.ocum_server == "":
            self.ocum_server = None

        self.entity_properties = {
            'target':
                {
                    'force': False,
                    'mediaagent': str(self.tcinputs['MediaAgent'])
                    },
            'disklibrary':
                {
                    'name': self.disk_lib_name,
                    'mount_path': self.disk_lib_loc
                    },
            'storagepolicy':
                {
                    'name': self.storage_policy_name,
                    'library': str(self.disk_lib_name),
                    'copy_name':self.aux_copy_name,
                    'ocum_server': self.ocum_server,
                    'retention_period': 10,
                    'number_of_streams': 50
                    },
            'backupset':
                {
                    'name': self.backupset_name,
                    'agent': self.agent.agent_name,
                    'client': self.client.client_name,
                    'instance': str(self.tcinputs['InstanceName'])
                    },
            'subclient':
                {
                    'agent' : self.agent.agent_name,
                    'name': self.subclient_name,
                    'content': self.subclient_content.split(","),
                    'instance': str(self.tcinputs['InstanceName']),
                    'storagepolicy': self.storage_policy_name,
                    'backupset': self.backupset_name,
                    'client': self.client.client_name
                    },
        }
        self.vplex_engine = self.tcinputs.get('vplex_engine', None)
        self.bkpset_name = self.tcinputs.get('BackupsetName', None)
        self.sc_name = self.tcinputs.get('SubclientName', None)
        self.proxy_client = self.tcinputs.get('ProxyMA', None)
        self.vsm_array_name1 = self.tcinputs.get('VSMArrayName1', None)
        self.vsm_array_name2 = self.tcinputs.get('VSMArrayName2', None)
        self.vsm_to_vsm = self.tcinputs.get('VSMtoVSM', None)
        self.delimiter = None
        self.job_based_retention = self.tcinputs.get('JobBasedRetention')
        self.restore_client = self.tcinputs.get('RestoreClient')
        if self.sc_name is not None:
            self.backupset = self.agent.backupsets.get(self.bkpset_name)
            self.subclient = self.backupset.subclients.get(self.sc_name)
            self.storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            self.snap_copy_name = "SELECT name FROM ArchGroupCopy WHERE ArchGroupId = {a} AND \
                                    copy = 1 AND isSnapCopy = 1"
            self.snap_copy_name = self.execute_query(
                self.snap_copy_name, {'a': self.storage_policy.storage_policy_id},
                fetch_rows='one')

        self.get_backup_copy_job = "SELECT childJobId FROM JMJobWF WHERE processedJobId = {a}"
        self.get_mount_path = "SELECT MountPath FROM SMVolume WHERE JobId = {a} AND CopyId = {b}"
        self.get_total_backup_size = "SELECT totalBackupSize FROM JMBkpStats WHERE jobID = {a}"
        self.get_volume_id = "SELECT SMVolumeId FROM SMVolume WHERE jobID = {a} AND CopyId = {b}"
        self.get_mount_control_host = """SELECT ControlHostId FROM SMsnap WHERE SnapStatus = 12 and SMSnapId in
                                    (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in 
                                    (SELECT SMVolumeId from SMVolume WHERE JobId = {a}))"""
        self.get_control_host = """SELECT ControlHostId FROM SMsnap WHERE SMSnapId in
                                    (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in 
                                    (SELECT SMVolumeId from SMVolume WHERE JobId = {a}))"""
        self.get_mount_status = "SELECT MountStatus FROM SMVolume WHERE JobId = {a}"
        self.fetch_job_ids = "SELECT JobId FROM SMVolume WHERE CopyId = {a}"
        self.get_volumeid_da = "SELECT SMVolumeId FROM SMVolume WHERE jobID = {a} AND CopyId = {b}"
        self.get_controlhost_id = "SELECT RefId FROM SMHostAlias WHERE AliasName = '{a}'"
        self.get_gad_controlhost_id = """SELECT ControlHostID from SMControlHost where ControlHostId in (SELECT arrayID from SMConfigs where MasterConfigId =164 and ValueStr like '{a}') and SMArrayID like '{b}'"""
        self.get_vendor_id = "SELECT Id FROM SMVendor WHERE Name = '{a}'"
        self.get_snap_count = """ SELECT snap.SMSnapId FROM SMVolume AS Vol
                                    INNER JOIN SMVolSnapMap AS map ON vol.SMVolumeId = map.SMVolumeId
                                    INNER JOIN SMSnap AS snap ON map.SMSnapId = snap.SMSnapId AND
                                    snap.ReserveField2 = {a} WHERE vol.JobId = {b} AND
                                    snap.ControlHostId IN ({c}, {d}) """
        self.vplex_control_host = """SELECT ControlHostId,ReserveField2 FROM SMsnap WHERE SMSnapId
                                    IN (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId = {a})"""
        self.current_mmconfig = "SELECT value FROM MMConfigs WHERE \
                                name LIKE '%MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES%'"
        self.get_master_config_id = """SELECT config.id FROM SMMasterConfigs AS config
                                    INNER JOIN SMVendor AS vendor ON config.VendorId = vendor.id		
                                    WHERE config.Name LIKE '{a}' AND vendor.Name LIKE '{b}'"""
        self.get_snapengine_id = "SELECT SnapShotEngineId from SMSnapShotEngine  where \
                                  SnapEngineName = '{a}'"
        self.sp_name = 'Auto_SP_' + str(self.tcinputs['SnapEngineAtArray']).replace("/", "").replace(" ", "").replace("(", "").replace(")","")
        self.get_sp = """SELECT G.name, V.jobid , C.name, V.MountStatus FROM SMVolume V, archGroupCopy C, archGroup G
                                                        WHERE V.copyId = c.id AND G.id = C.archGroupId AND G.id IN (SELECT   DISTINCT archgroupid FROM 
                                                        archgroupcopy WHERE (startTime) <= dbo.GetUnixTime(getdate()-1) AND archGroupId in 
                                                        (select id from archGroup WHERE NAME LIKE '%{a}%')) AND V.MountStatus = '{b}'"""
        self.indexserver_name = 'Auto_SP_' + str(self.tcinputs['SnapEngineAtArray']).replace("/", "").replace(" ","").replace("(", "").replace(")", "")
        self.get_indexserver_list = """SELECT AC.name AS clientName FROM App_Client AC WITH (NOLOCK) JOIN APP_ClientProp ACP WITH(NOLOCK)ON AC.id = ACP.componentNameId 
                                        AND attrName = 'Index Server Type' AND ACP.attrVal = 15 AND ACP.modified = 0 AND 
                                        (Created) <= dbo.GetUnixTime(getdate()-1) and AC.Name like '%{a}%_IndexServer'"""

        self.bkpset_name = 'auto_bs_' + str(self.tcinputs['SnapEngineAtArray']).replace("/", "").replace(" ", "").replace("(", "").replace(")","")
        self.get_bkpset_list = """SELECT DISTINCT NAME FROM APP_BackupsetName as bkp_name INNER JOIN APP_BackupSetProp
                                                                as bkp_prop on bkp_name.id = bkp_prop.componentNameId WHERE 
                                                                dbo.GetDateTime(bkp_prop.created) < = getdate() -1 AND bkp_name.name like '%{a}%'"""
        self.get_sp_list = """SELECT DISTINCT AG.name FROM archGroup AG JOIN archGroupCopy AGC ON AG.id = AGC.archGroupId
                                            WHERE AG.name LIKE '%{a}%' AND (AGC.startTime * -1 ) <= dbo.GetUnixTime(getdate()-1)"""
        self.lib_name = 'Auto_Lib_' + str(self.tcinputs['SnapEngineAtArray']).replace("/", "").replace(" ", "").replace("(", "").replace(")","")
        self.get_lib_list = """SELECT AliasName, Libraryid  FROM MMLibrary where (LibraryInstallTime) <= dbo.GetUnixTime(getdate()-1)
                                                     AND LibraryId in (select Libraryid from MMLibrary 
                                                                    WHERE AliasNAME LIKE '%{a}%')"""
        self.get_indexcache_location = "select attrVal from app_clientprop where componentNameId \
                                      in (select id from APP_Client where name like '{a}') and attrName like '%cache path%'"

        self.get_snap = """SELECT SMSnapId, UniqueIdentifier FROM SMsnap WITH (NOLOCK) WHERE SMSnapId in
                                    (SELECT SMSnapId FROM SMVolSnapMap WITH (NOLOCK) WHERE SMVolumeId in 
                                    (SELECT SMVolumeId from SMVolume WITH (NOLOCK) WHERE JobId = {a}))"""

        self.get_primary_vol = """SELECT SUBSTRING(svmMetaData,0, CHARINDEX('|',svmMetaData,0)) AS ArrayName,
                                SUBSTRING( SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)),
                                CHARINDEX('|',SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)), LEN(svmMetaData)),
                                CHARINDEX('|',SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)))) AS VolumeName
                                FROM
                                (SELECT SUBSTRING(MetaData,CHARINDEX('3#6|::|',MetaData,0)+LEN('3#6|::|'),LEN(MetaData)) AS svmMetaData,RefId
                                FROM SMMetaData WHERE RefType = 2 AND RefId = {a}) AS T1"""

        self.get_secondary_vol = """SELECT SUBSTRING(svmMetaData,0, CHARINDEX('|',svmMetaData,0)) AS ArrayName,
                                    SUBSTRING( SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)),
                                    CHARINDEX('|',SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)), LEN(svmMetaData)),
                                    CHARINDEX('|',SUBSTRING(svmMetaData,CHARINDEX('|',svmMetaData,0)+LEN('|'), LEN(svmMetaData)))) AS VolumeName
                                    FROM
                                    (SELECT SUBSTRING(MetaData,CHARINDEX('3#29|::|',MetaData,0)+LEN('3#29|::|'),LEN(MetaData)) AS svmMetaData,RefId
                                    FROM SMMetaData SMD JOIN SMSnap SMS ON SMD.RefId = SMS.SMSnapId and SMD.RefType = 2 JOIN SMVolSnapMap SMVS ON SMS.SMSnapId = SMVS.SMSnapId 
                                    JOIN SMVolume SMV ON SMVS.SMVolumeId = SMV.SMVolumeId WHERE SMV.JobId = {a} AND SMV.CopyId = {b}) AS T1"""

        self.get_cluster_details = """SELECT SS.SMSnapId, SS.UniqueIdentifier, SCH.ControlHostId, SCH.SnapVendorName, SCH.SMArrayId,
                                            SCH.SMHostUserName, SCH.SMHostPassword FROM SMControlHost SCH WITH (NOLOCK) JOIN App_VMToPMMap VM 
                                            ON SCH.ClientId  = VM.PMClientId JOIN SMControlHost SCI
                                            ON SCI.ClientId = VM.VMClientId JOIN SMSnap SS
                                            ON SS.ControlHostId  = SCI.ControlHostId JOIN SMVolSnapMap SVM
                                            ON SVM.SMSnapId  = SS.SMSnapId JOIN SMVolume SV
                                            ON SV.SMVolumeId = SVM.SMVolumeId WHERE SV.JobId = {a} and SV.CopyId = {b} """

        self.get_snap_status = """SELECT SnapStatus, UniqueIdentifier from  SMsnap WITH (NOLOCK) WHERE SMSnapId in
                                (SELECT SMSnapId FROM SMVolSnapMap WITH (NOLOCK) WHERE SMVolumeId in 
                                (SELECT SMVolumeId from SMVolume WITH (NOLOCK) WHERE JobId = {a}))"""

        self.get_hostalias = "SELECT AliasName FROM SMHostAlias WITH (NOLOCK) where RefId = {a}"  # {'a': controlhostid}

        self.get_backup_copy_jobid = "SELECT childJobId FROM JMJobWF WITH (NOLOCK) WHERE jobId = {a}"

        self.has_cluster = """SELECT VM.PMClientId from App_VMToPMMap VM WITH (NOLOCK) JOIN SMControlHost SCH
                                ON SCH.ClientId = VM.VMClientId JOIN SMSnap SS
                                ON SS.ControlHostId  = SCH.ControlHostId JOIN SMVolSnapMap SVM
                                ON SVM.SMSnapId  = SS.SMSnapId JOIN SMVolume SV
                                ON SV.SMVolumeId = SVM.SMVolumeId WHERE SV.JobId = {a} and SV.CopyId = {b}"""

        self.get_host_details = """SELECT SS.SMSnapId, SS.UniqueIdentifier, SCH.ControlHostId, SCH.SnapVendorName,
                                        SCH.SMArrayId, SCH.SMHostUserName, SCH.SMHostPassword FROM SMControlHost SCH 
                                        WITH (NOLOCK) JOIN SMSnap SS ON SS.ControlHostId  = SCH.ControlHostId 
                                        JOIN SMVolSnapMap SVM ON SVM.SMSnapId  = SS.SMSnapId JOIN SMVolume SV
                                        ON SV.SMVolumeId = SVM.SMVolumeId WHERE SV.JobId = {a} and SV.CopyId = {b}"""

        self.snap_copy_details = """SELECT sourceCopyId, isSnapCopy, isMirrorCopy from archGroupCopy where
                                    id = {a}"""
        self.get_snapconfig_value = """SELECT Config.ValueStr FROM SMMasterConfigs AS M_config
            INNER JOIN SMVendor AS vendor ON M_config.VendorId = vendor.id
            INNER JOIN SMConfigs AS config ON config.MasterConfigId = M_config.Id
            INNER JOIN SMControlHost AS controlhost ON config.ArrayId = controlhost.ControlHostId
            WHERE 
                M_config.Name = '{a}'
                AND vendor.Name = '{b}'
                AND controlhost.SMArrayId = '{c}'
                AND config.AssocType = {d}"""
        self.get_svm_name = """SELECT ACP.attrVal FROM APP_ClientProp AS ACP
            INNER JOIN SMControlHost AS SMC ON SMC.ClientId = ACP.componentNameId
            WHERE SMC.SMArrayId = '{a}' AND ACP.attrName = 'NAS vServer Name'"""

        self.check_trueup = """SELECT count(*) from JMMisc WITH (NOLOCK) where jobid = {a} 
                            and itemType = {b}"""
        self.get_backupcopied_jobs = """select jobId from JMJobSnapshotStats with (NOLOCK)
                    where appId = {a} and materializationStatus = 100"""
        self.get_auxcopied_jobs = """select jobId from JMJobDataStats with (NOLOCK)
                            where appId = {a} and archGrpCopyId = {b} and status = 100"""
        self.get_backupcopied_jobs_for_sp = """select jobId from JMJobSnapshotStats with (NOLOCK)
                                                    where archGrpId = {a} and materializationStatus = 100"""
        self.get_materialization_status_job = """select unPickReason from JMJobSnapshotStats with (NOLOCK)
                                                    where JobID = {a} and materializationStatus = 101"""

    def folder_name(self, backup_level):
        """ Returns random charactor's """

        backup_level = backup_level.replace("/", "").replace(" ", "").replace("(", "").replace(")", "")
        name = backup_level +"_"+''.join([random.choice(string.ascii_letters) for _ in range(3)])
        return name

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
