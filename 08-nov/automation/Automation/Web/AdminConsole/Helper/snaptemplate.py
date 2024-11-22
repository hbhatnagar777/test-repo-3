# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This Module provides methods to run different template for Snap Operations

Class : SnapTemplate

Functions:
    cleanup()           : To cleanup entities created during execution
    create_entities()   : To create required entities like Plans, Subclient etc
    snaptemplate1()     : Template for Snap Test Cases

"""
import random
import time
import string
import glob
import os
import datetime
from datetime import date
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import get_csdb
from FileSystem.FSUtils.fshelper import FSHelper
from cvpysdk.policies.storage_policies import StoragePolicies
from cvpysdk.policies.storage_policies import StoragePolicyCopy
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays, Engine
from Web.AdminConsole.Helper.array_helper import ArrayHelper
#from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient , FsAgent
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.Components.panel import Backup , RModalPanel, RDropDown
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.dropdown import CVDropDown
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from cvpysdk.job import Job

class SnapTemplate(object):
    """ SnapTemplate Class for Snap Cases"""
    test_step = TestStep()

    def __init__(self, testcase, admin_console):

        """Initializing the Test case file"""
        self.admin_console = admin_console
        self.tcinputs = testcase.tcinputs
        self.commcell = testcase.commcell
        self.testcase = testcase
        self.machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.testcase.client_machine = self.machine
        self.client = testcase.client
        self.csdb = get_csdb()
        self.policies = StoragePolicies(self.commcell)
        self.plan_obj = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.fs_servers = FileServers(self.admin_console)
        self.fs_subclient = FsSubclient(self.admin_console)
        self.fs_scdetails = FsSubclientDetails(self.admin_console)
        self.fs_rscdetails = Subclient(self.admin_console)
        self.fs_agent = FsAgent(self.admin_console)
        self.fs_helper = FSHelper(self.testcase)
        self.arrays = Arrays(self.admin_console)
        self.engine = Engine(self.admin_console, self.csdb)
        self.arrayhelper = ArrayHelper(self.admin_console)
        self.planhelper = PlanMain(self.admin_console)
        self.log = testcase.log
        self.navigator = self.admin_console.navigator
        self._csdb = get_csdb()
        self._region = None
        self.multisite = None
        self._control_host = None
        self.inc_job_id = None
        self.lock = self.tcinputs.get('lock', False)
        self._storagepool_name = {'pri_storage': self.tcinputs['StoragePoolName'],
                                  'snap_pri_storage': self.tcinputs['StoragePoolName']}
        self.string = self.tcinputs['SnapEngine'].replace("/", "").replace(" ", "").replace("(", "").replace(")", "")
        self.random_string = ''.join([random.choice(string.ascii_letters) for _ in range(3)])
        if self.lock:
            self._plan_name = "CC_AutoPlan_{0}_{1}_{2}".format(self.string, self.testcase.id, self.random_string)
        else:
            self._plan_name = "CC_AutoPlan_{0}_{1}".format(self.string, self.testcase.id)
        self._subclient_name = "CC_AutoSC_{0}_{1}".format(self.string, self.testcase.id)
        self._backupset_name = 'defaultBackupSet'
        self.out_restore_path = "C:\\AutomationRestore{0}".format(self.string)
        self.restore_path = None
        self.path = None
        self.download_path = os.path.join(self.client.install_directory, 'Automation', 'temp')
        self.storage_policy = None
        self.snap_primary = "Primary snap"
        self.primary = "Primary"
        self.first_node_copy = None
        self.second_node_copy = None
        self.job_completion_status = None
        self.job_delay_reason = None
        self.type = self.tcinputs.get('ReplicationType', False)
        self.additional_storage = {
            'Add': True,
            'default_replica': True,
            'cloud_copy': False,
            'storage_name': self.first_node_copy,
            'source_copy': self.snap_primary,
            'storage_pool': self.tcinputs['StoragePoolName'],
            'copy_type': "vault",
            'snap_engine': self.tcinputs['SnapEngine'],
            'cloud_snap_engine': self.tcinputs.get('cloud_snap_engine', None),
            'mappings': {'src_svm': self.tcinputs.get('PrimaryArray', None),
                         'dest_svm': self.tcinputs.get('SecondaryArray', None)}
        }
        self._snapshot_options = {'snap_recovery_points': '3',
                                  'sla_hours': '2',
                                  'sla_minutes': '30'}
        if self.machine.os_info == 'UNIX':
            self.separator = "/"
        else:
            self.separator = "\\"
        self.testdata_dir = []
        self.get_sp = """SELECT DISTINCT AG.name FROM archGroup AG JOIN archGroupCopy AGC ON AG.id = AGC.archGroupId
                                                    WHERE AG.name LIKE '{a}'"""
        self.get_sp_list = """SELECT DISTINCT AG.name FROM archGroup AG JOIN archGroupCopy AGC ON AG.id = AGC.archGroupId
                            WHERE AG.name LIKE '%{a}%' AND AGC.name ='Primary' AND (AGC.startTime * -1 ) < dbo.GetUnixTime(getdate()-3)"""
        self.get_array_name = """SELECT SCH.SMArrayId FROM SMControlHost SCH
                                    WITH (NOLOCK) JOIN SMSnap SS ON SS.ControlHostId  = SCH.ControlHostId 
                                    JOIN SMVolSnapMap SVM ON SVM.SMSnapId  = SS.SMSnapId JOIN SMVolume SV
                                    ON SV.SMVolumeId = SVM.SMVolumeId WHERE SV.JobId = {a} AND SV.CopyId = {b}"""
        self.get_SMMountvolume = "select * from SMMountVolume  WITH (NOLOCK) where MountJobId = {a}"
        self.pruneflag_status = """ SELECT Pruneflags FROM SMVOLUME WITH (NOLOCK) where jobid = {a} """
        self.get_SMVOLUME = """ SELECT * FROM SMVOLUME WITH (NOLOCK) where jobid = {b}"""
        self.aux_copy_job = """SELECT jobid FROM JMAdminJobInfoTable WITH (NOLOCK) WHERE archGrpName = '{a}' and 
                        	                                optype=104 order by jobid desc"""
        self.auxcopy_post_job_run = """select jobId from jmadminjobstatstable where archGrpName = '{a}' and 
                        	                                optype=104 order by jobid desc"""
        self.get_snap_creation_time = """SELECT CreationTime FROM SMVolume WHERE JobId = {a}"""
        self.get_snap_expiry_time = """SELECT PropValue FROM SMSnapProps WHERE SMSnapId in 
                                    (SELECT SMSnapId FROM SMVolSnapMap WHERE SMVolumeId in (SELECT SMVolumeId FROM SMVolume WHERE JobId = {a}))"""
        self.get_copy_retention_days = """SELECT retentionDays FROM ArchAgingRule WHERE CopyId = {a}"""
        self.get_immutable_snap_flag_on_job_for_copy = """SELECT vol.CopyId, Vol.VolumeFlags & CAST(274877906944 as BIGINT), 
                                                        snap.SnapFlags & CAST (9007199254740992 AS BIGINT) FROM SMVolSnapMap map
                                                        inner join SMVolume vol on map.SMVolumeId = vol.SMVolumeId
                                                        inner join SMSnap snap on map.SMSnapId = snap.SMSnapId
                                                        where vol.jobid= {a} and vol.CopyId = {b}"""

        self.add_engine_val = False
        if self.tcinputs.get('ControlHost', None):
            self._array_vendor = self.tcinputs['ArrayVendor']
            self._array_name = self.tcinputs['ArrayName']
            self._username = self.tcinputs['ArrayUser']
            self._password = self.tcinputs['ArrayPassword']
            self._control_host = self.tcinputs['ControlHost']
            self._controllers = self.tcinputs.get('Controllers', None)
            self._snap_config = self.tcinputs.get('SnapConfig', None)
            self._credential_name = self.tcinputs.get('CredentialName', None)
            self.add_engine_val = True

        self.get_SMMountVolume = """SELECT FROM SMMOUNTVOLUME where jobid = {a}"""
        self.primary = "Primary"
        self.model_panel = Backup(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.rmodal_dialog = RModalDialog(self.admin_console)
        self.backupjobid = """select childJobId from JMJobWF where processedjobid={a}"""
        self.rmodal_panel = RModalPanel(self.admin_console)
        self.rdropdown = RDropDown(self.admin_console)
        self.get_recon_status = """SELECT jobdescription from JMjobstats where jobid = {a}"""
        self.offline_bkpcpy_jobid = """select max(jobid) from JMJobWF where applicationid = 
                (select id from APP_Application where subclientName='{a}')"""
        self.offline_bkpcpy_plan_jobid = """select max(jobid) from JMJobWF where archGroupId = 
                (select id from archGroup where name='{a}')"""

    @property
    def storagepool_name(self):
        """Return Storage Pool Name"""
        return self._storagepool_name

    @storagepool_name.setter
    def storagepool_name(self, value):
        """Set Storage Pool name"""
        self._storagepool_name = value

    @property
    def plan_name(self):
        """Return Plan Name"""
        return self._plan_name

    @plan_name.setter
    def plan_name(self, value):
        """Set Plan name"""
        self._plan_name = value

    @property
    def subclient_name(self):
        """Return Subclient Name"""
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """Set Subclient Name"""
        self._subclient_name = value

    @property
    def backupset_name(self):
        """Return BackupSet Name"""
        return self._backupset_name

    @backupset_name.setter
    def backupset_name(self, value):
        """Set BackupSet Name"""
        self._backupset_name = value

    @property
    def snapshot_options(self):
        """Return Snap options"""
        return self._snapshot_options

    @snapshot_options.setter
    def snapshot_options(self, value):
        """Set Snap options"""
        self._snapshot_options = value

    def wait_for_job_completion(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def spcopy_obj(self, copy_name):
        """ Create storage Policy Copy object
        Arg:
            copy_name        (str)         -- Copy name
        """
        spcopy = StoragePolicyCopy(self.commcell, self.storage_policy, copy_name)
        return spcopy
    
    def delete_subclient(self):
        """Delete Subclient"""
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.fs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        if self.fs_rscdetails.is_subclient_exists(self.subclient_name, self.backupset_name):
            self.fs_rscdetails.delete_subclient(subclient_name=self.subclient_name,
                                                backupset_name=self.backupset_name,
                                                )
            self.admin_console.wait_for_completion()
            if self.fs_rscdetails.is_subclient_exists(self.subclient_name, self.backupset_name):
                raise CVTestStepFailure('Subclient still exists. Please check manually.')
            else:
                self.log.info("Subclient deleted successfully.")

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""
        try:
            self.delete_subclient()

            if self.type:
                if self.lock:
                    self.log.info("*" * 20 + "Not attempting to delete Snap copies as Compliance or Immutable lock is enabled")
                else:
                    self.log.info("Deleting: %s Configuration for secondary snap copies", self.type)
                    self.navigator.navigate_to_plan()
                    if self.plan_obj.is_plan_exists(self.plan_name):
                        self.plan_obj.select_plan(self.plan_name)
                        self.snap_copy_deletion(self.type)
                        self.log.info("Successfully Deleted: %s Configuration for secondary snap copies", self.type)
                        self.admin_console.wait_for_completion()

                    else:
                        self.log.info("No such plan configuration exists")

            self.navigator.navigate_to_plan()
            plan_name = "AutoPlan_{0}_{1}".format(self.string, self.testcase.id)
            sp_list = self.execute_query(self.get_sp_list, {'a': plan_name})
            self.log.info("Storage Policies/Plans to be deleted: {0}".format(sp_list))    
            if self.lock:
                self.log.info("*" * 20 + "attempting to delete 3 days old Plans as locked jobs would have aged by now")
                # Delete the 3 days old plans which exist due to previous locked test cases.
                if sp_list in [[[]], [['']], ['']]:
                    self.log.info("Unable to delete plans, query returned none")
                else:
                    self.log.info("Going to delete plans: {0}".format(sp_list))
                    for i in range(len(sp_list)):
                        if self.plan_obj.is_plan_exists(sp_list[i][0]):
                            self.plan_obj.delete_plan(sp_list[i][0])
                            self.admin_console.wait_for_completion()
                            if self.plan_obj.is_plan_exists(sp_list[i][0]):
                                raise CVTestStepFailure('Plan still exists. Please check why deletion of plan is failing')
                            else:
                                self.log.info(f"Plan: {sp_list[i][0]} deleted successfully.")

            else:
                if self.plan_obj.is_plan_exists(self.plan_name):
                    self.plan_obj.delete_plan(self.plan_name)
                    self.admin_console.wait_for_completion()
                    if self.plan_obj.is_plan_exists(self.plan_name):
                        raise CVTestStepFailure('Plan still exists. Please check manually')
                    else:
                        self.log.info(f"Plan: {self.plan_name} deleted successfully.")

            self.policies.refresh()
            if self.lock:
                self.log.info("*" * 20 + "attempting to delete 3 days old storage policies as locked jobs would have aged by now")
                # Delete the 3 days old storage policies which exist due to previous locked test cases.
                if sp_list in [[[]], [['']], ['']]:
                    self.log.info("Unable to delete Storage policies, query returned none")
                else:
                    self.log.info("Going to delete Storage policies: {0}".format(sp_list))
                for i in range(len(sp_list)):
                    try:
                        self.policies.delete(sp_list[i][0])
                        self.log.info("deleted storage policy: %s", sp_list[i][0])
                    except Exception as e:
                        self.log.info("storage policy deletion failed with error" + str(e))
                        self.log.info("treating it as soft failure")
            else:
                sp = self.execute_query(self.get_sp, {'a': self.plan_name})
                if not (sp in [[[]], [['']], ['']]):
                    self.log.info(f"Deleting storage policy: {sp}")
                    try:
                        self.policies.delete(self.plan_name)
                    except Exception as e:
                        self.log.info("deleting Storage policy failed with err: " + str(e))
                        self.log.info("treating it as soft failure")

            if self.machine.check_directory_exists(self.out_restore_path):
                self.log.info(f"Clean up Outplace Restore Directory: {self.out_restore_path}")
                self.remove_dir(drive='C:\\', path=self.out_restore_path)

            self.log.info("Cleanup has completed successfully.")

        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup entities failed with error : {exp}')

    @test_step
    def snap_copy_creation(self, replica_type):
        """To create copies for the given replication types"""

        try:
            if replica_type == "pv_replica":
                self.first_node_copy = "Vault/Replica"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.log.info("Creating Vault Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created Vault Copy: %s", self.first_node_copy)

            elif replica_type == "pm_replica":
                self.first_node_copy = "PM"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['copy_type'] = "mirror"
                self.log.info("Creating Mirror Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created Mirror Copy: %s", self.first_node_copy)

            elif replica_type == "pvm_replica":
                self.first_node_copy = "PV"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.log.info("Creating First Node Vault Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created First node Vault Copy: %s", self.first_node_copy)

                self.second_node_copy = "Pri-VM"
                self.additional_storage['storage_name'] = self.second_node_copy
                self.additional_storage['source_copy'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['copy_type'] = "mirror"
                self.additional_storage['mappings']['src_svm'] = self.tcinputs.get('SecondaryArray', None)
                self.additional_storage['mappings']['dest_svm'] = self.tcinputs.get('TertiaryArray', None)
                self.log.info("Creating Second Node Mirror Copy: %s", self.second_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created Second Node Mirror Copy: %s", self.second_node_copy)

            elif replica_type == "pmv_replica":
                self.first_node_copy = "PM"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['copy_type'] = "mirror"
                self.log.info("Creating First Node Mirror Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created First Node Mirror Copy: %s", self.first_node_copy)

                self.second_node_copy = "Pri-MV"
                self.additional_storage['storage_name'] = self.second_node_copy
                self.additional_storage['source_copy'] = self.first_node_copy
                self.additional_storage['default_replica'] = True
                self.additional_storage['copy_type'] = "vault"
                self.additional_storage['mappings']['src_svm'] = self.tcinputs.get('SecondaryArray', None)
                self.additional_storage['mappings']['dest_svm'] = self.tcinputs.get('TertiaryArray', None)
                self.log.info("Creating Second Node Vault Copy: %s", self.second_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created second node Vault Copy: %s", self.second_node_copy)

            elif replica_type == "pmm_replica":
                self.first_node_copy = "PM"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['copy_type'] = "mirror"
                self.log.info("Creating First Node Mirror Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created First Node Mirror Copy: %s", self.first_node_copy)

                self.second_node_copy = "Pri-MM"
                self.additional_storage['storage_name'] = self.second_node_copy
                self.additional_storage['source_copy'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['copy_type'] = "mirror"
                self.additional_storage['mappings']['src_svm'] = self.tcinputs.get('SecondaryArray', None)
                self.additional_storage['mappings']['dest_svm'] = self.tcinputs.get('TertiaryArray', None)
                self.log.info("Creating Second Node Mirror Copy: %s", self.second_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created Second Node Mirror Copy: %s", self.second_node_copy)

            elif replica_type == "pvv_replica":
                self.first_node_copy = "PV"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.log.info("Creating First Node Vault Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created First node Vault Copy: %s", self.first_node_copy)

                self.second_node_copy = "Pri-VV"
                self.additional_storage['storage_name'] = self.second_node_copy
                self.additional_storage['source_copy'] = self.first_node_copy
                self.additional_storage['default_replica'] = False
                self.additional_storage['mappings']['src_svm'] = self.tcinputs.get('SecondaryArray', None)
                self.additional_storage['mappings']['dest_svm'] = self.tcinputs.get('TertiaryArray', None)
                self.log.info("Creating Second Node Vault Copy: %s", self.second_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created Second node Vault Copy: %s", self.second_node_copy)

            elif replica_type == "pv_cloud":
                self.first_node_copy = "NetApp_Cloud"
                self.additional_storage['storage_name'] = self.first_node_copy
                self.additional_storage['cloud_copy'] = True
                self.log.info("Creating NetApp Cloud Copy: %s", self.first_node_copy)
                self.plan_details.edit_server_plan_storage_pool(self.additional_storage, edit_storage=False, snap=True)
                self.log.info("Successfully created NetApp Cloud Copy: %s", self.first_node_copy)

        except Exception as exp:
            raise CVTestStepFailure(f'Create Snap Copies failed with error : {exp}')

    @test_step
    def snap_copy_deletion(self, replica_type):
        """To Delete copies for the given replication types"""

        try:
            if replica_type == "pv_replica":
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Vault Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Vault Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pm_replica":
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Mirror Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Mirror Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pvm_replica":
                if self.second_node_copy is not None:
                    if self.plan_details.is_copy_present(self.second_node_copy):
                        self.log.info("Deleting Second Node Mirror Copy: %s", self.second_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.second_node_copy)
                        self.log.info("Successfully deleted Second node Mirror Copy: %s", self.second_node_copy)
                        time.sleep(300)
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Vault Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Vault Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pmv_replica":
                if self.second_node_copy is not None:
                    if self.plan_details.is_copy_present(self.second_node_copy):
                        self.log.info("Deleting Second Node Vault Copy: %s", self.second_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.second_node_copy)
                        self.log.info("Successfully deleted Second node Vault Copy: %s", self.second_node_copy)
                        time.sleep(300)
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Mirror Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Mirror Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pmm_replica":
                if self.second_node_copy is not None:
                    if self.plan_details.is_copy_present(self.second_node_copy):
                        self.log.info("Deleting Second Node Mirror Copy: %s", self.second_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.second_node_copy)
                        self.log.info("Successfully deleted Second node Mirror Copy: %s", self.second_node_copy)
                        time.sleep(300)
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Mirror Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Mirror Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pvv_replica":
                if self.second_node_copy is not None:
                    if self.plan_details.is_copy_present(self.second_node_copy):
                        self.log.info("Deleting Second Node Vault Copy: %s", self.second_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.second_node_copy)
                        self.log.info("Successfully deleted Second node Vault Copy: %s", self.second_node_copy)
                        time.sleep(300)
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Node Vault Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted First node Vault Copy: %s", self.first_node_copy)
                        time.sleep(300)

            elif replica_type == "pv_cloud":
                if self.first_node_copy is not None:
                    if self.plan_details.is_copy_present(self.first_node_copy):
                        self.log.info("Deleting First Cloud Copy: %s", self.first_node_copy)
                        self.plan_details.delete_server_plan_storage_copy(self.first_node_copy)
                        self.log.info("Successfully deleted Cloud Copy: %s", self.first_node_copy)
                        time.sleep(300)

        except Exception as exp:
            raise CVTestStepFailure(f'Delete Snap Copies failed with error : {exp}')

    @test_step
    def create_entities(self):
        """To create required entities for test case"""
        try:
            # To create a new plan
            self.log.info("Adding a new plan: %s", self.plan_name)
            self.navigator.navigate_to_plan()
            self.plan_obj.create_server_plan(plan_name=self.plan_name,
                                             storage=self.storagepool_name,
                                             snapshot_options=self.snapshot_options)
            self.navigator.navigate_to_plan()
            self.log.info("successfully created plan: %s", self.plan_name)
            time.sleep(20)
            self.policies.refresh()
            self.storage_policy = self.policies.get(self.plan_name)
            # To add secondary snap copy configuration
            if self.type:
                self.log.info("Creating: %s Configuration for secondary snap copies", self.type)
                self.plan_obj.select_plan(self.plan_name)
                self.snap_copy_creation(self.type)
                self.log.info("Successfully created: %s Configuration for secondary snap copies", self.type)

            # To add a new Subclient
            self.log.info("Adding a new subclient %s", self.subclient_name)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab("Subclients")
            self.fs_rscdetails.add_subclient(subclient_name=self.subclient_name,
                                             plan_name =self.plan_name,
                                             backupset_name=self.backupset_name,
                                             contentpaths= self.tcinputs['SubclientContent'].split(','),
                                             define_own_content=True)

            self.log.info(f"Checking whether Subclient:{self.subclient_name} is Present under the list of subclients")
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.wait_for_completion()
            self.admin_console.access_tab("Subclients")
            if self.subclient_name in self.rtable.get_column_data("Name", True):
                self.log.info("Created a new subclient %s", self.subclient_name)
            else:
                raise Exception(
                    "Failed: Subclient Content already present on another subclient,check other subclients content")

            self.fs_rscdetails.access_subclient(subclient_name=self.subclient_name,
                                                backupset_name=self.backupset_name
                                               )
            self.admin_console.wait_for_completion(600)
            self.fs_rscdetails.enable_snapshot_engine(enable_snapshot=True,
                                                     engine_name=self.tcinputs['SnapEngine'])

        except Exception as exp:
            raise CVTestStepFailure(f'Create entities failed with error : {exp}')

    @test_step
    def verify_backup(self, backup_type):
        """Verify Snapbackup"""
        try:
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.access_tab("Subclients")
            jobid = self.fs_rscdetails.backup_subclient(subclient_name=self.subclient_name,
                                                        backupset_name=self.backupset_name,
                                                       backup_type=backup_type)
            job_status = self.wait_for_job_completion(jobid)
            if not job_status:
                exp = "{0} Snap Job ID {1} didn't succeed".format(backup_type, jobid)
                raise Exception(exp)
            return jobid
        except Exception as exp:
            raise CVTestStepFailure(f'Snapbackup operation failed : {exp}')

    @test_step
    def verify_backupcopy(self):
        """Verify Backup Copy"""
        try:
            job = self.storage_policy.run_backup_copy()
            self.log.info("Successfully started Backup copy job : {0}".format(job.job_id))
            job_status = self.wait_for_job_completion(job.job_id)
            if not job_status:
                exp = " Backup Copy Job ID {0} didn't succeed".format(job.job_id)
                raise Exception(exp)
            if job.status != 'Completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                        job.job_id, job.delay_reason))
        except Exception as exp:
            raise CVTestStepFailure(f'Backup Copy operation failed : {exp}')

    @test_step
    def verify_auxcopy(self, plan_name=None, copy_name=None):
        """
        Verify Aux Copy
           plan_name(str):None =  name of the plan
           copy_name(str):None =   name of the particular copy under a plan
        """
        try:
            self.log.info("*" * 20 + "Running Auxiliary Copy job" + "*" * 20)
            self.plan_obj.select_plan(plan_name)
            self.admin_console.access_tab(self.admin_console.props['label.nav.storagePolicy'])
            self.plan_details.run_auxiliary_copy(copy_name)
            job = self.execute_query(self.aux_copy_job, {'a': plan_name})
            if job in [[[]], [['']], ['']]:
                self.log.info("Please wait for sometime to get auxcopy jobid post job completion")
                time.sleep(500)
                job = self.execute_query(self.auxcopy_post_job_run, {'a': plan_name})
            if job in [[[]], [['']], ['']]:
                raise Exception("Aux Copy Job ID not found")
            job = int(job[0][0])
            self.log.info("Successfully started aux copy job : {0}".format(job))
            job_status = self.wait_for_job_completion(job)
            job_completion_status = self.get_job_status(job)
            if not job_status:
                exp = "Aux Copy Job ID {0} didn't succeed".format(job)
                raise Exception(exp)
            if job_completion_status != 'Completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors".format(job))
        except Exception as exp:
            raise CVTestStepFailure(f'Aux Copy operation failed : {exp}')

    @test_step
    def verify_restore(self, storage_copy_name=None, restore_aux_copy=False, inplace=False):
        """Verify Restore
        """
        try:
            if inplace:
                self.restore_path = None
            else:
                dir_name = "Res_" + ''.join([random.choice(string.ascii_letters) for _ in range(3)])
                self.restore_path = str(self.out_restore_path + '\\' + dir_name)
                self.machine.create_directory(self.restore_path)
                self.log.info("Successfully Created directory: {0}".format(self.restore_path))
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.access_tab("Subclients")
            rjobid = self.fs_rscdetails.restore_subclient(subclient_name=self.subclient_name,
                                                          backupset_name=self.backupset_name,
                                                         restore_aux_copy=restore_aux_copy,
                                                         storage_copy_name=storage_copy_name,
                                                         destination_path=self.restore_path)
            time.sleep(10)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)
        except Exception as exp:
            raise CVTestStepFailure(f'Restore operation failed : {exp}')

    def get_download_folder(self, file_type):
        """ Gets the download folder
            file_type(str): extension type of the file.
        """
        newest_file_type = max(
            glob.iglob(os.path.join(self.download_path, '*.{0}'.format(file_type))),
            key=os.path.getctime)
        return newest_file_type

    def select_files(self, content):
        """ selects few files in the path
            Args:
                content   (str): from where files to select
        """
        self.log.info("%s selects few files from specified folder %s", "*" * 8, "*" * 8)
        files = self.machine.get_files_in_path(content)
        count = 0
        sel_files = []
        for path in files:
            count += 1
            if count % 2 == 0:
                sel_files.append(path)
        return sel_files

    @test_step
    def restore_from_different_pages(self, jobid=None, fs_client_details_page=False,
                                     download_items=False, restore_by_job=False,
                                     restore_selected_items=False, search_and_restore_files=False,
                                     fs_subclient_details_page=False):
        """Verify Restore from different command center pages
            Args:
                job_id: string: job id
        """

        dir_name = "Res_" + ''.join([random.choice(string.ascii_letters) for _ in range(3)])
        self.restore_path = str(self.out_restore_path + '\\' + dir_name)
        self.machine.create_directory(self.restore_path)
        self.log.info("Successfully Created directory: {0}".format(self.restore_path))
        self.navigator.navigate_to_file_servers()
        self.fs_servers.access_server(self.tcinputs['ClientName'])
        recovery_point = date.today().strftime("%d-%B-%Y")

        #restore from client details page - fsagent\restore_recovery_points
        if fs_client_details_page:
            self.log.info("%s restore to be tried from client details page using recovery points %s", "*" * 8, "*" * 8)
            self.fs_subclient.access_subclient_tab()
            rjobid = self.fs_agent.restore_recovery_points(backupset_name=self.backupset_name,
                                                           recovery_time=recovery_point,
                                                           restore_path=self.restore_path)
            time.sleep(10)
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

        #fsagent\fssubclient\download_selected_items
        if download_items:
            self.log.info("%s Selecting items and downloading from FS subclient %s", "*" * 8, "*" * 8)
            drive = self.tcinputs['SubclientContent']
            if len(drive) < 4:
                directory_path = drive[:-1] + 'Test'
            else:
                directory_path = drive + self.separator + 'Test'
            if self.machine.check_directory_exists(directory_path):
                self.machine.remove_directory(directory_path)
            self.machine.create_directory(directory_path)
            file_path = directory_path + self.separator + 'textfile.txt'
            file_content = 'New file is created'
            self.machine.create_file(file_path, file_content)
            file_path1 = directory_path + self.separator + 'textfile.doc'
            self.machine.create_file(file_path1, file_content)
            file_path2 = drive[:-1] + 'filetext.docx'
            file_content1 = 'New doc file is created'
            self.machine.create_file(file_path2, file_content1)
            self.inc_job_id = self.verify_backup(Backup.BackupType.INCR)
            self.fs_subclient.access_subclient_tab()
            rjobid = self.fs_subclient.download_selected_items(subclient_name=self.subclient_name,
                                                               backupset_name=self.backupset_name,
                                                               download_files=[directory_path, file_path2],
                                                               file_system='Windows')
            self.admin_console.wait_for_completion()
            self.log.info("sleeping 5 minutes for download to complete")
            time.sleep(300)
            self.log.info("%s Validating downloaded content %s", "*" * 8, "*" * 8)
            path = self.get_download_folder('zip')
            self.fs_helper.validate_download_files(
                backup_files={os.path.basename(file_path): file_content,
                              os.path.basename(file_path1): file_content,
                              os.path.basename(file_path2): file_content1},
                download_path=path)
            self.log.info("Successfully validated downloaded content from path: {0}".format(path))
            self.unmount_snap(self.inc_job_id, self.snap_primary)

        #fsagent\fssubclient\restore_subclient_by_job
        if restore_by_job:
            self.log.info("%s Restoring from FS subclient using Job ID %s", "*" * 8, "*" * 8)
            self.fs_subclient.access_subclient_tab()
            rjobid = self.fs_subclient.restore_subclient_by_job(backupset_name=self.backupset_name,
                                                                subclient_name=self.subclient_name,
                                                                job_id=jobid,
                                                                dest_client=None,
                                                                restore_path=self.restore_path)
            self.log.info("Successfully started restore job: {0}".format(rjobid))
            job_status = self.wait_for_job_completion(rjobid)
            if not job_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)
            return rjobid

        #fsagent\fssubclient\restore_selected_items
        if restore_selected_items:
            self.log.info("%s Restore from FS Subclient for selected items %s", "*" * 8, "*" * 8)
            self.fs_subclient.access_subclient_tab()
            select_files = self.select_files(os.path.join(self.path, 'dir1', 'regular'))
            rjobid = self.fs_subclient.restore_selected_items(backupset_name=self.backupset_name,
                                                              subclient_name=self.subclient_name,
                                                              del_file_content_path=None,
                                                              selected_files=select_files,
                                                              restore_path=self.restore_path,
                                                              file_system='Windows')
            self.log.info("Successfully started restore job: {0}".format(rjobid))
            job_status = self.wait_for_job_completion(rjobid)
            if not job_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

            self.log.info("%s Validating selected files restore %s", "*" * 8, "*" * 8)
            self.fs_helper.validate_restore_for_selected_files(backup_files=select_files,
                                                               restore_path=self.restore_path)
            self.log.info("%s Successfuly Validated selected files restore %s", "*" * 8, "*" * 8)
            return rjobid

        #fsagent\fssubclient\search_and_restore_files
        if search_and_restore_files:
            self.log.info("%s Restore from FS Subclient by Searching the files %s", "*" * 8, "*" * 8)
            hash = {}
            file_name = "regularfile1"
            file_path = os.path.join(self.path, 'dir1', 'regular', 'regularfile1')
            hash[str(file_path)] = self.machine.get_file_hash(file_path)
            self.fs_subclient.access_subclient_tab()
            rjobid = self.fs_subclient.search_and_restore_files(backupset_name=self.backupset_name,
                                                                subclient_name=self.subclient_name,
                                                                file_name=file_name,
                                                                restore_path=self.restore_path)
            self.log.info("Successfully started restore job: {0}".format(rjobid))
            job_status = self.wait_for_job_completion(rjobid)
            if not job_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

            self.log.info("%s Validating searched file restore %s", "*" * 8, "*" * 8)
            self.outplace_validate(hash, self.restore_path)
            self.log.info("%s Successfuly Validated searched file restore %s", "*" * 8, "*" * 8)
            return rjobid

        #restore from subclient details page - fssubclientdetails\restore_recovery_points
        if fs_subclient_details_page:
            self.log.info("%s restore from FS subclient details page using recovery point %s", "*" * 8, "*" * 8)
            self.fs_subclient.access_subclient(backupset_name=self.backupset_name,
                                               subclient_name=self.subclient_name)
            rjobid = self.fs_scdetails.restore_recovery_points(recovery_time=recovery_point,
                                                               restore_path=self.restore_path)
            time.sleep(10)
            self.log.info("Successfully started restore job: {0}".format(rjobid))
            rjob_status = self.wait_for_job_completion(rjobid)
            if not rjob_status:
                exp = "Restore Job ID {0} didn't succeed".format(rjobid)
                raise Exception(exp)

    def remove_dir(self, drive, path):
        """Remove directory using robocopy cmd """
        if self.machine.os_info.upper() == 'WINDOWS':
            if not self.machine.check_directory_exists(f"{drive[:-1]}\\empty"):
                self.machine.create_directory(f"{drive[:-1]}\\empty")
            self.machine.execute_command(
                f"cmd.exe /c robocopy {drive[:-1]}\\empty {path} /purge")
            self.machine.execute_command(
                f"cmd.exe /c robocopy {drive[:-1]}\\empty {path}\\_source /purge")
            self.machine.remove_directory(path)
            self.machine.remove_directory(f'{drive[:-1]}\\empty')
        else:
            self.machine.remove_directory(path)

    @test_step
    def add_test_data(self):
        """add test data in subclient for verification"""
        try:
            hash = {}
            self.testdata_dir = []
            for drive in self.tcinputs['SubclientContent'].split(','):

                if self.machine.is_directory(drive) == 'True':
                    self.separator = "\\"
                    if self.machine.os_info == 'UNIX':
                        self.separator = "/"
                    if len(drive) < 4:
                        self.path = str(drive + "TestData")
                    else:
                        self.path = str(drive + self.separator + "TestData")

                    self.log.info("test data folder  is  {0}".format(self.path))
                    if self.machine.check_directory_exists(self.path):
                        self.log.info(
                            "TestData Folder already exists under {0}, deleting it and creating"
                            " new one!!".format(drive)
                        )
                        self.remove_dir(drive, self.path)
                    else:
                        self.log.info(
                            "TestData Folder does not exists under {0}, creating one!!".format(drive)
                        )
                    self.machine.create_directory(self.path)
                    self.machine.generate_test_data(self.path)
                    hash[str(drive)] = self.machine.get_folder_hash(self.path)
                    self.testdata_dir.append(drive.split(self.separator)[-1])
                    self.log.info("Created TestData Folder under {0}".format(drive))
            return hash
        except Exception as exp:
            raise CVTestStepFailure(f'Test Data generation failed : {exp}')

    @test_step
    def update_test_data(self, mode):
        """
        Update method to edit or add more test data
        Args:
            mode      --  mode values can be 'edit' or 'delete'
        """
        hash = {}
        if mode == 'edit':
            for drive in self.tcinputs['SubclientContent'].split(','):

                if self.machine.is_directory(drive) == 'True':
                    separator = "\\"
                    if self.machine.os_info == 'UNIX':
                        separator = "/"
                    if len(drive) < 4:
                        test_path = str(drive + "TestData")
                    else:
                        test_path = str(drive + separator + "TestData")
                    self.machine.modify_test_data(test_path, rename=True, modify=True)
                    hash[str(drive)] = self.machine.get_folder_hash(test_path)
                    self.log.info("Successfully Modified data at: {0}".format(test_path))
                else:
                    self.log.info("No data modified")
            return hash
        if mode == 'add':
            for drive in self.tcinputs['SubclientContent'].split(','):
                if self.machine.is_directory(drive) == 'True':
                    separator = "\\"
                    if self.machine.os_info == 'UNIX':
                        separator = "/"
                    if len(drive) < 4:
                        test_path = str(drive + "TestData")
                    else:
                        test_path = str(drive + separator + "TestData")
                    incr_path = test_path + separator + "IncrData"+"".join([random.choice(string.ascii_letters)
                                                                            for _ in range(3)])

                    self.machine.create_directory(incr_path)
                    self.machine.generate_test_data(incr_path)
                    hash[str(drive)] = self.machine.get_folder_hash(test_path)
                    self.log.info(f"Successfully added more testdata at:{test_path}")

            return hash

    @test_step
    def inplace_validate(self, source_hash):
        """Compare two directories
            Args:
                source_hash: hash value of source data,
        """
        try:
            restore_location = self.tcinputs['SubclientContent'].split(',')
            for drive in restore_location:
                if self.machine.is_directory(drive) == 'True':
                    if len(drive) < 4:
                        path = str(drive + "TestData")
                    else:
                        path = str(drive + "\\TestData")
                        if self.machine.os_info == 'UNIX':
                            path = str(drive + "/TestData")

                    dest_hash = self.machine.get_folder_hash(path)
                    if dest_hash == source_hash[drive]:
                        self.log.info("Verified for %s", drive)
                        continue
                    raise CVTestStepFailure("Restore may have failed/skipped some files")
            self.log.info("Restore validation success")
        except Exception as exp:
            raise CVTestStepFailure(f'Validating Test Data failed : {exp}')

    @test_step
    def outplace_validate(self, source_hash, out_restore_location):
        """Compare two directories
            Args:
                source_hash: hash value returned from add_test_data(),
                out_restore_location: str: Data restore path"""
        try:
            source_files = self.tcinputs['SubclientContent'].split(',')
            separator = '\\'
            if self.machine.os_info == 'UNIX':
                separator = '/'
            if not out_restore_location:
                self.log.info("Please provide outplace restore path. \n Doing Inplace Validation"
                              " as no outplace path was provided.")
                self.inplace_validate(source_hash)
            else:
                out_restore_location = out_restore_location.replace('/', separator)
                for drive in source_files:
                    if self.machine.is_directory(drive) == 'True':
                        folder = drive.split(separator)[-1]
                        if self.machine.os_info.lower() == 'windows' and len(folder)<3:
                            folder = ''
                        dest_drive = str(out_restore_location + separator + folder)
                        if self.machine.os_info.lower() == 'windows' and len(out_restore_location) == 3:
                            dest_drive = str(out_restore_location + folder)
                        path = str(dest_drive + separator + "TestData")
                        if folder == "":
                            path = str(dest_drive + "TestData")
                        dest_hash = self.machine.get_folder_hash(path)
                        self.log.info(f"Source: {drive + separator + 'TestData'}, destination: {path}")
                        if dest_hash == source_hash[drive]:
                            self.log.info("Verified for %s", drive)
                            continue
                        raise CVTestStepFailure("Restore may have failed/skipped some Files")
                self.log.info("Restore validation success")
        except Exception as exp:
            raise CVTestStepFailure(f'Validating Test Data failed : {exp}')

    def get_job_status(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = Job(self.commcell, jobid)
        return job_obj.status
    
    def get_job_delay_reason(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = Job(self.commcell, jobid)
        return job_obj.delay_reason

    @test_step
    def delete_snap(self, job_id, copy_name):
        """
            Deletes the single snap or multiple snaps, after restore is complete
            Args:
                job_id: string: job id
                copy_name: string: name of the copy

            Note: all snaps should belongs single array
                If subclient content has different volumes locations then same jobid is created for different volumes snaps,
               if subclient content has only one job (1 volume location) then delete operation done at array level else
             if subclient content has more than one jobs (multiple volume location) with same jobid then delete operation done at plan level
        """
        try:
            spcopy = self.spcopy_obj(copy_name)
            self.navigator.navigate_to_arrays()
            self.log.info(f"job_id {job_id}, copy_id {spcopy.copy_id}, copy: {spcopy}")
            if type(job_id) == str or type(job_id) == int:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id, 'b': spcopy.copy_id})
            else:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id[0], 'b': spcopy.copy_id})
            self.arrays.action_list_snaps(array_name_list[0][0])
            if type(job_id) == str or type(job_id) == int:
                self.rtable.apply_filter_over_column(column_name="Job ID", filter_term=job_id)
                if self.rtable.get_total_rows_count(job_id) == 1:
                    # if subclient content has only one job (one volume location) then delete operation done at array level
                    delete_jobid = self.arrays.delete_snaps(job_id)
                else:
                    # if subclient content has more than one jobs (multiple volume location) coming from same array with same jobid
                    # then delete operation done at plan level
                    delete_jobid = self.delete_multiple_snaps_plan_level(job_id, copy_name, plan_name=self.plan_name)
            else:
                # if jobid as list of different jobs from different subclients then delete snap from array level
                delete_jobid = self.arrays.delete_snaps(job_id)
            job_status = self.wait_for_job_completion(delete_jobid)
            self.job_completion_status = self.get_job_status(delete_jobid)
            self.job_delay_reason = self.get_job_delay_reason(delete_jobid)
            if self.job_completion_status != "Completed":
                exp = "Snap delete Job ID {0} failed with error {1}".format(delete_jobid, self.job_delay_reason)
                raise Exception(exp)
            self.log.info(f"Snap delete Job ID {delete_jobid} succeeded for snap jobid {job_id}")
        except Exception as exp:
            raise CVTestStepFailure(f'deleting snap failed for jobid {job_id}: {exp}')

    @test_step
    def mount_snap(self, job_id, copy_name):
        """
        Mounts the single snap or multiple snaps, after snap job is complete
        Args:
            job_id:  str()single jobid or list()multiple jobids
            copy_name: string: name of the copy
        Note: all snaps should belongs single array
            If subclient content has different volumes locations then same jobid is created for different volumes snaps,
            if subclient content has only one job (1 volume location) then mount operation done at array level else
            if subclient content has more than one jobs (multiple volume location) with same jobid then mount operation done at
                    subclient level
        """
        try:
            spcopy = self.spcopy_obj(copy_name)
            self.navigator.navigate_to_arrays()
            self.log.info(f"job_id {job_id}, copy_id {spcopy.copy_id}, copy: {spcopy}")
            if type(job_id) == str or type(job_id) == int:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id, 'b': spcopy.copy_id})
            else:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id[0], 'b': spcopy.copy_id})
            self.arrays.action_list_snaps(array_name_list[0][0])
            dir_name = "Mount_" + ''.join([random.choice(string.ascii_letters) for _ in range(3)]) + self.string
            if self.machine.os_info == 'UNIX':
                separator = "/"
                mount_path = str('/' + dir_name)
            else:
                mount_path = str("C:" + '\\' + dir_name)
            self.machine.create_directory(mount_path)
            self.log.info("Successfully Created Mount Path: {0}".format(mount_path))
            if type(job_id) == str or type(job_id) == int:
                self.rtable.apply_filter_over_column(column_name="Job ID", filter_term=job_id)
                if self.rtable.get_total_rows_count(job_id) == 1:
                    # if subclient content as one volume location then mount will run form array level
                    mount_jobid = self.arrays.mount_snap(job_id, self.tcinputs['ClientName'], mount_path)
                else:
                    # if subclient content as more than one volumes location and volumes coming from same array
                    # which as same jobid for all the snaps then mount will run form subclient level
                    mount_jobid = self.mount_multiple_snaps_subclient_level(job_id, mount_path, copy_name,
                                                                            clientname=self.tcinputs[
                                                                                'ClientName'],
                                                                            backupsetname=self.backupset_name,
                                                                            subclientname=self.subclient_name)
            else:
                # if jobid as list of different jobs from different subclients then mount snap from array level
                mount_jobid = self.arrays.mount_snap(job_id, self.tcinputs['ClientName'], mount_path)
            job_status = self.wait_for_job_completion(mount_jobid)
            job_completion_status = self.get_job_status(mount_jobid)
            if job_completion_status != "Completed":
                exp = "Snap Job ID {0} didn't succeed".format(mount_jobid)
                raise Exception(exp)
            self.log.info(f"Mount snap successful for snap jobid {job_id}")

        except Exception as exp:
            raise CVTestStepFailure(f'mounting snap failed for jobid {job_id}: {exp}')

    @test_step
    def unmount_snap(self, job_id, copy_name):
        """
     Unmounts the single snap or multiple snaps, after snap job is complete
        Args:
            job_id: string: job id(single) or list: multiple jobids
            array_name: string: array name
            Note: all snaps should belongs single array
        """

        try:
            spcopy = self.spcopy_obj(copy_name)
            self.navigator.navigate_to_arrays()
            self.log.info(f"job_id {job_id}, copy_id {spcopy.copy_id}, copy: {spcopy}")
            if type(job_id) == str or type(job_id) == int:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id, 'b': spcopy.copy_id})
            else:
                array_name_list = self.execute_query(self.get_array_name, {'a': job_id[0], 'b': spcopy.copy_id})
            self.arrays.action_list_snaps(array_name_list[0][0])
            jobid = self.arrays.unmount_snap(job_id, self.plan_name, copy_name)
            job_status = self.wait_for_job_completion(jobid)
            job_completion_status = self.get_job_status(jobid)
            if job_completion_status != "Completed":
                exp = "Snap Job ID {0} didn't succeed".format(jobid)
                raise Exception(exp)
            self.log.info(f"Unmount snap successful for snap jobid {job_id}")
        except Exception as exp:
            raise CVTestStepFailure(f'unmounting snap failed for jobid {job_id}: {exp}')

    def revert_snap(self, job_id):
        """
            Reverts volume based on given snap job id at subclient level
        Args:
            job_id : job id of snap
        """
        try:
            self.log.info("*"*20 + "Revert operation started at Subclient Level" + "*"*20)
            revert_jobid = self.revert_snap_subclient_level(job_id=job_id,
                                                            clientname=self.tcinputs['ClientName'],
                                                            backupsetname=self.backupset_name,
                                                            subclientname=self.subclient_name)
            self.log.info("Running Revert Operation is with Job ID:{0}".format(revert_jobid))
            job_status = self.wait_for_job_completion(revert_jobid)
            if not job_status:
                exp = "Revert Operation with Job ID: {0} didn't succeed".format(revert_jobid)
                raise Exception(exp)
            self.log.info("Job id: {0} Revert Operation Successful".format(job_id))

        except Exception as exp:
            raise CVTestStepFailure(f'Revert Operation Failed with error: {exp}')

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

    def validation_instant_clone(self, job_id=None):
        """"To validate FS Instant Clone"""
        try:
            SMMountVolume = self.execute_query(self.get_SMMountvolume, {'a': job_id})
            self.log.info(f"Mount Vols from db: {SMMountVolume}")
            if '59' in SMMountVolume:
                self.log.info("Instant Clone mount succeeded.")
            else:
                exp = "Please check the mount status for Instant Clone Job. Mount Status unsuccessful."
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'FS Instant Clone validation failed for {job_id}: {exp}')

    def validation_spool_copy(self, job_id=None):
        """To validate Spool Copy for Snap"""
        try:
            self.snap_status = self.execute_query(self.pruneflag_status, {'a': job_id})
            self.snap_status = self.snap_status[0][0]
            if self.snap_status == 3 or 4:
                self.log(f'The job is pruned in the copy')
            else:
                exp = "Please check the prune status as job is still not aged"
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'validation for spool copy failed for {job_id}: {exp}')

    def mount_multiple_snaps_subclient_level(self, jobid: str, mount_path: str, copy_name, clientname: str,
                                             backupsetname: str, subclientname: str) -> str:
        """
            Args:
                jobid (str) : jobid
                mount_path(str) : mount path
                copy_name(str) : copy name
                clientname(str) : client name
                backupsetname(str) : backupset name
                subclientname(str) : subclient name
            Returns:
                Mount_job_id : jobid of multiple mount snaps

            Note: Mounting multiple snaps at Subclient level with same jobid (if subclient has subclientcontent from Different volumes)
        """
        self.log.info("*" * 20 + "Mounting Multiple Snaps at Subclient level" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.fs_servers.access_server(clientname)
        self.admin_console.access_tab("Subclients")
        mount_job_id = self.fs_rscdetails.mount_multiple_snap(jobid, mount_path, copy_name, self.plan_name, clientname,
                                                              subclientname, backupsetname)
        return mount_job_id


    def delete_multiple_snaps_plan_level(self, job_id: str, copy_name: str, plan_name: str) ->str:
        """
            Args:
                job_id(str) : job id
                copy_name(str) : copy name
                plan_name(str) : plan name
            Returns:
                  delete_job_id: job id of multiple delete snaps

            Note:Deleting multiple snaps at plan level with same jobid (if subclient has subclientcontent from Different volumes)
        """
        self.log.info("*"*20 + "Deleting Multiple Snaps at Plan level" + "*"*20)
        self.plan_obj.select_plan(plan_name)
        self.admin_console.access_tab(self.admin_console.props['label.nav.storagePolicy'])
        delete_job_id = self.plan_details.delete_multiple_snaps_plan_level(job_id, copy_name)
        return delete_job_id

    def revert_snap_subclient_level(self, job_id, clientname, backupsetname, subclientname):
        """
        Args:
            job_id(str) : job id of snap
            clientname(str) :client name
            backupsetname(str) : backupset name
            subclientname(str) : subclient name
        return:
            jobid: jobid of revert operation

        Note: if you have multiple volumes snap with same job id which occurs at subclient content has muliptle volumes
        locations then this revert will Reverts all the volumes.
        """
        self.log.info("*" * 20 + "Revert Snap at Subclient level" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.fs_servers.access_server(clientname)
        self.admin_console.access_tab("Subclients")
        jobid = self.fs_rscdetails.revert_snap(job_id, subclientname, backupsetname)
        return jobid

    def run_offline_backup_copy_subclient_level(self):
        """
             Run backup Copy at Subclient Level
        """
        try:
            self.log.info("*" * 20 + "offline backup copy initiation at Subclient" + "*" * 20)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.access_tab("Subclients")
            self.fs_rscdetails.run_offline_backup_copy(subclient_name=self.subclient_name,
                                                       backupset_name=self.backupset_name)
            try:
                backupjobid = self.admin_console.get_jobid_from_popup()
                self.log.info(f"Running Backupcopy is with Job ID:{backupjobid}")
                job_status = self.wait_for_job_completion(backupjobid)
            except Exception as exp:
                self.log.info(f"Backupcopyjobid from Toaster Message is incorrect or not found,"
                              f"Getting Backupcopy jobid from DB")
                time.sleep(5)
                backupjobid = self.execute_query(self.offline_bkpcpy_jobid, {'a': self.subclient_name})
                if backupjobid in [[[]], [['']], ['']]:
                    exp = "BackupCopy Job ID not found"
                    raise Exception(exp)
                backupjobid = backupjobid[0][0]
                self.log.info(f"Running Backupcopy is with Job ID:{backupjobid}")
                job_status = self.wait_for_job_completion(backupjobid)
            if not job_status:
                exp = f"Snap Job ID {backupjobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {backupjobid} offline backup job Successful")
        except Exception as exp:
            raise CVTestStepFailure(f'Run offline backup copy at Subclient Level failed with error : {exp}')

    def run_inline_backup_copy(self)-> str:
        """
             Run inline backup copy at subclient

             Return: Snap job id
        """
        try:
            self.log.info("*" * 20 + "inline backup copy initiation" + "*" * 20)
            self.navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.fs_servers.access_server(self.tcinputs['ClientName'])
            self.admin_console.access_tab("Subclients")
            jobid = self.fs_rscdetails.run_inline_backup_copy(subclientname=self.subclient_name,
                                                              backupsetname=self.backupset_name)
            self.log.info(f"Running Snap backup is with Job ID:{jobid}")
            job_status = self.wait_for_job_completion(jobid)
            time.sleep(30)
            backupjobid = self.execute_query(self.backupjobid, {'a': jobid})
            backupjobid = backupjobid[0][0]
            if not job_status:
                exp = f"Snap Job ID {jobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {jobid} Snap backup job Successful")
            self.log.info(f"Running Backup copy is with Job ID:{backupjobid}")
            time.sleep(5)
            backup_job_status = self.wait_for_job_completion(backupjobid)
            if not backup_job_status:
                exp = f"Backup Copy Job ID {backupjobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {backupjobid} Backup job Successful")
            return jobid
        except Exception as exp:
            raise CVTestStepFailure(f'Run inline backup copy failed with error : {exp}')

    def run_backup_copy_at_copy_level(self):
        """
             Run backup Copy at Copy Level under plan
        """
        try:
            self.log.info("*" * 20 + "Running Backup copy at Copy Level" + "*" * 20)
            self.plan_obj.select_plan(self.plan_name)
            self.admin_console.access_tab(self.admin_console.props['label.nav.storagePolicy'])
            self.plan_details.run_offline_backup_copy()
            try:
                backupjobid = self.admin_console.get_jobid_from_popup()
                self.log.info(f"Running Backupcopy is with Job ID:{backupjobid}")
                job_status = self.wait_for_job_completion(backupjobid)
            except Exception as exp:
                self.log.info(f"Backupcopy jobid from Toaster Message is incorrect or not found,"
                              f"Getting Backupcopy jobid from DB")
                time.sleep(5)
                backupjobid = self.execute_query(self.offline_bkpcpy_plan_jobid, {'a': self.plan_name})
                if backupjobid in [[[]], [['']], ['']]:
                    exp = "BackupCopy Job ID not found"
                    raise Exception(exp)
                backupjobid = backupjobid[0][0]
                self.log.info(f"Running Backupcopy is with Job ID:{backupjobid} at Copy Level")
                job_status = self.wait_for_job_completion(backupjobid)
            if not job_status:
                exp = f"Snap Job ID {backupjobid} didn't succeed"
                raise Exception(exp)
            self.log.info(f"Job id {backupjobid} backup job at Copy Level Successful")
        except Exception as exp:
            raise CVTestStepFailure(f'Run backup copy at Copy level failed with error : {exp}')


    def reconcile_snapshots(self, arrayname):
        """
        Run reconcile operation
        """
        try:
            self.log.info("Running Reconcilation Operation" + "*" * 20)
            self.navigator.navigate_to_arrays()
            recon_jobid = self.arrays.reconcile_snapshots(arrayname)
            job_status = self.wait_for_job_completion(recon_jobid)
            if not job_status:
                exp = f"Recon Job id {recon_jobid} didn't succeed"
                raise Exception(exp)
            recon_status = self.execute_query(str(self.get_recon_status), {'a': recon_jobid})
            recon_status = recon_status[0][0]
            if recon_status == 'Snap Reconciliation Completed Successfully':
                self.log.info("Job id: {0} Reconcilation Operation Successful".format(recon_jobid))
            else:
                exp = "Reconcilation Operation with Job ID: {0} didn't succeed".format(recon_jobid)
                raise Exception(exp)

        except Exception as exp:
            raise CVTestStepFailure(f'Reconcilation Operation Failed with error: {exp}')

    def enable_compliance_lock(self, plan, copy):
        """
        Enable Compliance Lock
        Args:
            plan : str : plan name
            copy : str : copy name
        """
        self.log.info("*" * 20 + "Enabling Compliance Lock on copy [%s] of plan [%s]" % (copy, plan))
        self.plan_obj.select_plan(plan)
        self.plan_details.enable_compliance_lock(copy)
        self.log.info("*" * 20 + "Compliance Lock enabled successfully")

    def validate_disable_compliance_lock(self, plan, copy):
        """
        Validate disable Compliance lock is not allowed
        Args:
            plan : str : plan name
            copy : str : copy name
        """
        self.log.info("*" * 20 + "Validating disable Compliance Lock is not allowed on copy [%s] of plan [%s]" % (copy, plan))
        self.plan_obj.select_plan(plan)
        self.plan_details.disable_compliance_lock(copy)
        self.log.info("*" * 20 + "Successfully validated disable Compliance Lock is not allowed")

    def validate_changing_retention_type_on_compliance_lock(self, plan, copy):
        """
        Validate changing retention type on Compliance lock copy is not allowed
        Args:
            plan : str : plan name
            copy : str : copy name
        raises:
            CVTestStepFailure : If Changing retention type on Compliance lock copy is allowed
        """
        self.log.info(
            "*" * 20 + 
            "Validating changing retention type on Compliance lock copy is not "
            "allowed on copy [%s] of plan [%s]" % (copy, plan)
        )
        notification_text = self.planhelper.modify_retention_on_copy(
            plan, copy, 2, jobs=True
        )
        if notification_text:
            self.log.info("Notification text: %s" % notification_text)
            self.log.info(
                "*" * 20 + 
                "Successfully validated changing retention type on Compliance "
                "lock copy is not allowed"
            )
        else:
            raise CVTestStepFailure(
                "*" * 20 + 
                "Changing retention type on Compliance lock copy is allowed"
            )
            
    def _execute_retention_modification_steps(self, plan, copy):
        """Executes retention modifications as mentioned in test case steps

            Args:
                plan    (str)   - Plan name
                copy    (str)   - Copy name
        """
        self.log.info("*" * 20 + 'Executing retention modification steps for plan %s and copy %s' % (plan, copy))

        # Retention is considered from dependent copy, say set retention as 1day
        self._validate_basic_retention(plan, copy, 1)

        # Try increasing retention to 2 days, it should be successful
        self._set_and_validate_basic_retention(plan, copy, 2)

        # Try reducing basic retention from 2 to 1 Days, it should return error
        self._set_and_validate_basic_retention(plan, copy, 1)

        self.log.info("*" * 20 + 'Successfully Validated retention modification on Locked copy')

    def _validate_basic_retention(self, plan, copy, ret_days):
        """Validate retention period on copy

            Args:
                plan    (str)   - Plan name / Pool name
                copy    (str)   - Copy name
                ret_days (int)  - Number of retention days set

            Raises:
                CVTestStepFailure   - If retention period not as expected
        """
        retention_days = self._get_basic_retention_period(plan, copy)
        self.log.info('Retention set: %s, expected: %s' % (retention_days, ret_days))
        if retention_days == ret_days:
            self.log.info("*" * 20 + 'Retention days is correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))
        else:
            raise CVTestStepFailure("*" * 20 + 'Retention days was not correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))
        
    def _get_basic_retention_period(self, plan, copy):
        """To get retention set on copy from archAgingRule table for given plan/pool and copy

            Args:
                plan    (str)   - Plan name / Pool name
                copy    (str)   - Copy name

            Returns:
                int             -  retention days set on the copy

            Raises:
                Exception   - If unable to fetch retention period
        """

        query = f"""SELECT  AAR.retentionDays
                    FROM    archAgingRule AAR WITH (NOLOCK)
                    INNER JOIN      archGroupCopy AGC WITH (NOLOCK)
                            ON      AAR.copyId = AGC.id
                    INNER JOIN      archGroup AG WITH (NOLOCK)
                            ON      AGC.archGroupId = AG.id
                    WHERE   AG.name = '{plan}'
                    AND     AGC.name = '{copy}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        results = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', results[0])
        if results[0] != '':
            return int(results[0])
        raise Exception('Unable to fetch retention period')
    
    def _set_and_validate_basic_retention(self, plan, copy, new_ret_days):
        """To set retention on copy for given plan and copy

            Args:
                plan          (str)   - Plan name
                copy          (str)   - Copy name
                new_ret_days  (int)   - New retention period (in days)
        """
        old_ret_days = self._get_basic_retention_period(plan, copy)
        change = 'Increasing' if old_ret_days < new_ret_days else 'Reducing'

        self.log.info('%s retention from %s days to %s days' % (change, old_ret_days, new_ret_days))
        self.planhelper.modify_retention_on_copy(plan, copy, new_ret_days, 'Day(s)')
        if change == 'Increasing':
            self.log.info("*" * 20 + '... %s retention should be successful' % change)
            self.log.info("*" * 20 + '... validating changes')
            self._validate_basic_retention(plan, copy, new_ret_days)
        else:
            self.log.info("*" * 20 + '... %s retention should not be allowed' % change)
            self.log.info("*" * 20 + '... validating no changes are made')
            self._validate_basic_retention(plan, copy, old_ret_days)

            # Close dialog, it was not closed by plan helper
            self.admin_console.click_button(self.admin_console.props['action.cancel'])

    def enable_immutable_snap(self, plan, copy):
        """
        Enable immutable Snap
        Args:
            plan : str : plan name
            copy : str : copy name
        """
        self.log.info("*" * 20 + "Enabling immutable Snap on copy[%s] of plan [%s]" % (copy, plan))
        self.plan_obj.select_plan(plan)
        self.plan_details.enable_immutable_snap(copy)
        self.log.info("*" * 20 + "immutable snap enabled successfully")

    def validate_disable_immutable_snap(self, plan, copy):
        """
        Validate disable immutable snap is not allowed
        Args:
            plan : str : plan name
            copy : str : copy name
        """
        self.log.info("*" * 20 + "Validating disable immutable snap is not allowed on copy [%s] of plan [%s]" % (copy, plan))
        self.plan_obj.select_plan(plan)
        self.plan_details.disable_immutable_snap(copy)
        self.log.info("*" * 20 + "Successfully validated disable immutable snap is not allowed")

    def validate_immutable_snap_on_jobs_retention(self, plan, copy):
        """
        Validate immutable snap on Jobs retention
        Args:
            plan : str : plan name
            copy : str : copy name
        """
        self.log.info("*" * 20 + "Validating immutable snap on Jobs retention on copy [%s] of plan [%s]" % (copy, plan))
        try:
            self.plan_obj.select_plan(plan)
            self.plan_details.enable_immutable_snap(copy)
        except Exception as exp:
            if exp.__str__() == "failed to enable Immutable Snapshot":
                self.log.info("*" * 20 + "immutable snap on jobs retention validated successfully")

    def validate_delete_snap_on_locked_snap(self, jobid, copy_name):
        """
        Validate delete operation on locked snap

        Args:
            jobid : str : job id
            copy_name : str : copy

        Raises:
            CVTestStepFailure : If delete snap operation on locked snap succeeds
        """
        self.log.info("*" * 20 + "Validating delete operation on locked snap")
        try:
            self.delete_snap(jobid, copy_name)
            if self.job_completion_status == "Completed":
                self.log.info("Delete Snap of Job ID: {0} succeeded".format(jobid))
                raise Exception(
                    "*" * 20 +
                    "Compliance/Immutable Locked snaps should not be deleted, "
                    "Raising the exception"
                )
        except Exception:
            if self.job_delay_reason and "Compliance lock is enabled on snap copy" in self.job_delay_reason:
                self.log.info(
                    "Deleting snap failed for jobid: {0} with error: {1}".format(
                        jobid, self.job_delay_reason
                    )
                )
                self.log.info(
                    "*" * 20 + "Delete operation on locked snap validated successfully"
                )
            elif self.job_delay_reason and "Compliance lock is enabled on snap copy" not in self.job_delay_reason:
                raise Exception(
                    "*" * 20 +
                    "Delete operation on locked snap failed with some other error: {0}".format(
                        self.job_delay_reason
                    )
                )
            else:
                raise Exception(
                    "*" * 20 +
                    "Delete Snap of Job ID: {0} succeeded, Compliance/Immutable Locked snaps should not be deleted".format(
                        jobid
                    )
                )

    def validate_delete_job_on_locked_copy(self, plan, copy, jobid):    
        """
        Validate delete job operation on Compliance/Immutable locked copy.

        Args:
            plan: str: plan name
            copy: str: copy name
            jobid: str: job id

        Raises:
            CVTestStepFailure: If delete job operation on locked copy succeeds
        """
        self.log.info("*" * 20 + "Validating delete JOB operation on locked copy: {0}".format(copy))
        self.plan_obj.select_plan(plan)
        notification_text = self.plan_details.delete_job_on_locked_copy(copy, jobid)
    
        if notification_text and "Manual deletion of jobs from a worm storage policy is not allowed" in notification_text:
            self.log.info(
                "*" * 20 + 
                "Delete job operation on Compliance/Immutable locked copy validated successfully, "
                "Notification text: {0}".format(notification_text)
            )
        elif notification_text and "Manual deletion of jobs from a worm storage policy is not allowed" not in notification_text:
            raise CVTestStepFailure(
                "*" * 20 + 
                "Validation of Delete job operation on Compliance/Immutable locked copy failed, "
                "Notification text: {0}".format(notification_text)
            )
        else:
            raise CVTestStepFailure(
                "*" * 20 + 
                "Job deleted successfully, Validation of Delete job operation on Compliance/Immutable locked copy failed, "
                "Notification text: {0}".format(notification_text)
            )

    def validate_delete_copy_on_locked_copy(self, plan, copy):
        """
        Validate delete copy operation on Compliance/Immutable locked copy.

        Args:
            plan : str : plan name
            copy : str : copy name

        Raises:
            CVTestStepFailure : If delete copy operation on locked copy succeeds
        """

        self.log.info(
            "*" * 20 + "Validating delete copy operation on Compliance/Immutable "
            "locked copy: %s", copy
        )
        self.navigator.navigate_to_plan()
        if self.plan_obj.is_plan_exists(plan):
            self.plan_obj.select_plan(plan)
            if self.plan_details.is_copy_present(copy):
                self.log.info(
                    "Deleting Compliance/Immutable locked Copy: %s", copy
                )
                self.plan_obj.select_plan(plan)
                notification_text = self.plan_details.delete_server_plan_storage_copy(copy)
                if notification_text and "Manual deletion of jobs from a worm storage policy is not allowed" in notification_text:
                    self.log.info(
                        "*" * 20 + "Delete copy operation on Compliance/Immutable "
                        "locked copy validated successfully, Notification text: {0}"
                        .format(notification_text)
                    )
                elif notification_text and "has been deleted successfully" in notification_text:
                    raise CVTestStepFailure(
                        "*" * 20 + "Copy deleted successfully, Validation of Delete "
                        "Copy operation on Compliance/Immutable locked copy failed, "
                        "Notification text: {0}".format(notification_text)
                    )
                else:
                    raise CVTestStepFailure(
                        "*" * 20 + "Validation of Delete job operation on Compliance/"
                        "Immutable locked copy failed, notification: {0}"
                        .format(notification_text)
                    )

    def validate_delete_plan_of_locked_copy(self, plan):
        """
        Validate delete plan of locked copy

        Args:
            plan : str : plan name

        Raises:
            CVTestStepFailure : If delete plan operation on locked copy succeeds
        """
        self.log.info("*" * 20 + "Validating delete plan of locked copy")
        self.log.info("*" * 20 + "Deleting subclient before deleting plan")
        self.delete_subclient()

        if not self.plan_obj.is_plan_exists(plan):
            raise CVTestStepFailure("Plan does not exists")
        else:
            notification_text = self.plan_obj.delete_plan(plan, wait=False, raise_error=False)
            if notification_text and "compliance lock enabled" in notification_text:
                self.log.info(
                    "*" * 20 + "Delete plan of locked copy validated successfully, "
                    "notification: {0}".format(notification_text)
                )
            elif notification_text and "The plan was successfully deleted" in notification_text:
                raise CVTestStepFailure(
                    "*" * 20 + "Plan deleted successfully, Validation of Delete plan of "
                    "locked copy failed, notification: {0}".format(notification_text)
                )
            else:
                raise CVTestStepFailure(
                    "*" * 20 + "Validation of Delete plan of locked copy failed, "
                    "notification: {0}".format(notification_text)
                )

    def validate_immutable_snap_flag_and_expiry_time(self, jobid, copy_name):
        """
        Validate immutable snap flag and expiry time
        Args:
            jobid : str : job id
            copy_name : str : copy name
        """
    
        # Create sp copy object
        spcopy = self.spcopy_obj(copy_name)
        self.log.info(
            "*" * 20 + 
            "Validate if immutable flag is set on the job: %s in copy: %s" % 
            (jobid, copy_name)
        )
        immutable_flag = self.execute_query(
            self.get_immutable_snap_flag_on_job_for_copy, {'a': jobid, 'b': spcopy.copy_id}
        )
        if immutable_flag in [[[]], [['']], ['']]:
            raise Exception(
                "*" * 20 + 
                "Immutable flag is not set on the job: %s in copy: %s, Raising the exception" % 
                (jobid, copy_name)
            )
        else:
            for i in range(len(immutable_flag)):
                if immutable_flag[i][0] == spcopy.copy_id:
                    self.log.info(
                        "*" * 20 + 
                        "Immutable flag is set on the job: %s in copy: %s" % 
                        (jobid, copy_name)
                    )
                else:
                    raise Exception(
                        "*" * 20 + 
                        "Immutable flag is not set on the job: %s in copy: %s, Raising the exception" % 
                        (jobid, copy_name)
                    )
    
        self.log.info("*" * 20 + "Validating immutable snap expiry time")
        self.log.info(
            "Fetching snap creation time for job: %s and retention set on the copy: %s" % 
            (jobid, copy_name)
        )
        creation_time = self.execute_query(self.get_snap_creation_time, {'a': jobid})
        retention_days = self.execute_query(self.get_copy_retention_days, {'a': spcopy.copy_id})
        self.log.info("Snap Creation Time: %s" % creation_time[0][0])
        self.log.info("Retention Days: %s" % retention_days[0][0])
        self.log.info("Fetching snap expiry time set in the DataBase")
        db_expiry_time = self.execute_query(self.get_snap_expiry_time, {'a': jobid})
        self.log.info("Expiry Time from DB: %s" % db_expiry_time[0][0])
        if creation_time in [[[]], [['']], ['']]:
            raise Exception(
                "*" * 20 + 
                "Creation time fetched from the DB is empty, Raising the exception"
            )
        if retention_days in [[[]], [['']], ['']]:
            raise Exception(
                "*" * 20 + 
                "Creation time fetched from the DB is empty, Raising the exception"
            )
        if db_expiry_time in [[[]], [['']], ['']]:
            raise Exception(
                "*" * 20 + 
                "expiry time fetched from the DB is empty, Raising the exception"
            )
        self.log.info("Calculating expiry time based on snap creation time and retention days")
        expiry_time = int((datetime.datetime.fromtimestamp(
            int(creation_time[0][0])
        ) + datetime.timedelta(days=int(retention_days[0][0]))).timestamp())
        self.log.info("Calculated Expiry time: %s" % expiry_time)
        if not int(db_expiry_time[0][0]) >= expiry_time:
            raise Exception(
                "*" * 20 + 
                "Immutable snap expiry time is not set correctly, Raising the exception"
            )
        else:
            self.log.info("*" * 20 + "Immutable snap expiry time validated successfully")

    def snaptemplate1(self):
        """Main function for test case execution"""
        self.cleanup()
        if self.add_engine_val:
            self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password, self._control_host,
                               self._controllers, self._snap_config)
        if self.multisite is True:
            self.arrayhelper.edit_general()
        self.create_entities()
        source_test_data = self.add_test_data()

        # Run Full Snapbackup, Inline backup copy , Mount , Unmount and Restore
        full_job_id = self.run_inline_backup_copy()
        self.mount_snap(full_job_id, self.snap_primary)
        self.unmount_snap(full_job_id, self.snap_primary)
        self.verify_restore(
            storage_copy_name=self.snap_primary, restore_aux_copy=False, inplace=True)
        self.inplace_validate(source_test_data)
        # Run INCR Snapbackup, Offline Backup copy and Restore
        source_test_data2 = self.update_test_data(mode='add')
        inc_job_id = self.verify_backup(Backup.BackupType.INCR)
        self.run_offline_backup_copy_subclient_level()
        self.verify_restore(storage_copy_name=self.primary, restore_aux_copy=False)
        self.outplace_validate(source_test_data2, self.restore_path)
        # Run INCR Snap backup and restore from offline backup copy at copy level
        source_test_data3 = self.update_test_data(mode='add')
        inc_job_id_2 = self.verify_backup(Backup.BackupType.INCR)
        self.run_backup_copy_at_copy_level()
        self.verify_restore(storage_copy_name=self.primary, restore_aux_copy=False)
        self.outplace_validate(source_test_data3, self.restore_path)
        # Deleting snaps
        self.delete_snap(full_job_id, self.snap_primary)
        self.delete_snap(inc_job_id, self.snap_primary)
        self.delete_snap(inc_job_id_2, self.snap_primary)

        if self.add_engine_val:
            self.arrayhelper.action_delete_array()

    def snaptemplate2(self):
        """Main function for Replication test case execution"""
        self.cleanup()
        if self.add_engine_val:
            self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password, self._control_host,
                               self._controllers, self._snap_config)
        self.create_entities()
        source_test_data = self.add_test_data()
        # Run Full Snapbackup, Mount - Unmount and Restore
        full_job_id = self.verify_backup(Backup.BackupType.FULL)
        # Run aux copy
        self.verify_auxcopy(self.plan_name)
        #mount from first node copy
        self.mount_snap(full_job_id, self.first_node_copy)
        self.unmount_snap(full_job_id, self.first_node_copy)
        time.sleep(30)
        if self.type not in ["pv_replica", "pm_replica"]:
            #mount from second node copy
            self.mount_snap(full_job_id, self.second_node_copy)
            self.unmount_snap(full_job_id, self.second_node_copy)
        time.sleep(30)
        # Inplace Restore from first node copy
        self.verify_restore(
            storage_copy_name=self.first_node_copy, restore_aux_copy=True, inplace=True)
        self.inplace_validate(source_test_data)
        # Inplace Restore from Second node copy
        if self.type not in ["pv_replica", "pm_replica"]:
            self.verify_restore(
                storage_copy_name=self.second_node_copy, restore_aux_copy=True, inplace=True)
            self.inplace_validate(source_test_data)
        # Run INCR Snapbackup and Restore
        source_test_data2 = self.update_test_data(mode='add')
        inc_job_id = self.verify_backup(Backup.BackupType.INCR)
        # Run aux copy
        self.verify_auxcopy(self.plan_name)
        # Outplace Restore from first node copy
        self.verify_restore(
            storage_copy_name=self.first_node_copy, restore_aux_copy=True)
        self.outplace_validate(source_test_data2, self.restore_path)
        # Outplace Restore from Second node copy
        if self.type not in ["pv_replica", "pm_replica"]:
            self.verify_restore(
                storage_copy_name=self.second_node_copy, restore_aux_copy=True)
            self.outplace_validate(source_test_data2, self.restore_path)
        #verify delete snapshots
        inc2_job_id = self.verify_backup(Backup.BackupType.FULL)
        self.verify_auxcopy(self.plan_name)
        # deleting snaps from second node copy
        if self.type in ["pvv_replica", "pmv_replica"]:
            self.delete_snap(full_job_id, self.second_node_copy)
        # deleting snaps from first node copy
        if self.type in ["pv_replica", "pvm_replica", "pvv_replica"]:
            self.delete_snap(full_job_id, self.first_node_copy)
        # deleting snaps from primary
        self.delete_snap(full_job_id, self.snap_primary)
        if self.add_engine_val:
            self.arrayhelper.action_delete_array()

    def snaptemplate3(self):
        """
        Main function to run FS based Instant Clone and validate
        """
        self.cleanup()
        if self.add_engine_val:
            self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password,
                                   self._control_host,
                                   self._controllers, self._snap_config)
        self.create_entities()
        source_test_data = self.add_test_data()
        full_job_id = self.verify_backup(Backup.BackupType.FULL)
        # bkp_jdetails = self.jobs.job_completion(full_job_id)
        # if not bkp_jdetails['Status'] == 'Completed':
        #     raise Exception("Backup job {0} did not complete successfully".format(full_job_id))
        self.log.info("Running Test Clone now")
        self.navigator.navigate_to_file_servers()
        self.fs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.access_tab("Subclients")
        self.fs_subclient.select_instant_clone(self.subclient_name)
        jobid = self.fs_agent.instant_clone(self.tcinputs['CloneMountPath'])
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            exp = "Instant Clone Job ID {0} didn't succeed".format(jobid)
            raise Exception(exp)
        self.validation_instant_clone(jobid)

    def snaptemplate4(self, credentials = True):
        """
        Main function to run FS Backup copy using Spool Retention, modifying Plan related values.
        """
        self.cleanup()
        self.navigator.navigate_to_arrays()
        if credentials is not None:
            if self.add_engine_val:
             self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password, self._control_host,
                                    self._controllers,self._credential_name,self._snap_config)
        self.create_entities()
        self.planhelper.modify_retention_on_copy(self.plan_name, self.snap_primary, 0, 'Day(s)', snap_copy=True)
        source_test_data = self.add_test_data()
        # Running Full Snap Backup
        full_job_id = self.verify_backup(Backup.BackupType.FULL)
        # Run Backup Copy For Full Snap Backup
        backup_copy_id = self.verify_backupcopy()
        # Run Validation Spool copy
        self.validation_spool_copy()           

    def snaptemplate5(self):
        """
        Main function to verify Compliance lock on snap copies
        """
        self.cleanup()
        if self.add_engine_val:
            self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password, self._control_host,
                               self._controllers, self._snap_config)
        self.create_entities()

        #modify retention on primary snap copy and primary copy to 1day
        self.planhelper.modify_retention_on_copy(self.plan_name, self.snap_primary, 1, 'Day(s)', snap_copy=True)
        self.planhelper.modify_retention_on_copy(self.plan_name, self.primary, 1, 'Day(s)')
        if self.type:
            #modify retention on first node copy to 1day
            self.planhelper.modify_retention_on_copy(self.plan_name, self.first_node_copy, 1, 'Day(s)')

        #enable compliance lock on Primary snap copy and primary copy
        self.enable_compliance_lock(self.plan_name, self.snap_primary)
        self.enable_compliance_lock(self.plan_name, self.primary)
        if self.type:
            #enable compliance lock on first node copy
            self.enable_compliance_lock(self.plan_name, self.first_node_copy)

        #validate disable compliance lock on Primary snap copy and primary copy
        self.validate_disable_compliance_lock(self.plan_name, self.snap_primary)
        self.validate_disable_compliance_lock(self.plan_name, self.primary)
        if self.type:
            #validate disable compliance lock on first node copy
            self.validate_disable_compliance_lock(self.plan_name, self.first_node_copy)

        #validate changing retention type on compliance lock snap copy is not allowed
        self.validate_changing_retention_type_on_compliance_lock(self.plan_name, self.snap_primary)
        if self.type:
            #validate changing retention type on compliance lock first node copy is not allowed
            self.validate_changing_retention_type_on_compliance_lock(self.plan_name, self.first_node_copy)

        #Run steps to validate retention modification on compliance lock copies
        self._execute_retention_modification_steps(self.plan_name, self.snap_primary)
        self._execute_retention_modification_steps(self.plan_name, self.primary)
        if self.type:
            self._execute_retention_modification_steps(self.plan_name, self.first_node_copy)

        #Run snap backup, backup copy and aux copy
        source_test_data = self.add_test_data()
        full_job_id = self.run_inline_backup_copy()
        if self.type:
            # Run aux copy
            self.verify_auxcopy(self.plan_name)

        #validate snap delete operation on locked snap
        self.validate_delete_snap_on_locked_snap(full_job_id, self.snap_primary)
        if self.type:
            self.validate_delete_snap_on_locked_snap(full_job_id, self.first_node_copy)

        #validate delete job operation on locked copy
        self.validate_delete_job_on_locked_copy(self.plan_name, self.snap_primary, full_job_id)
        self.validate_delete_job_on_locked_copy(self.plan_name, self.primary, full_job_id)
        if self.type:
            self.validate_delete_job_on_locked_copy(self.plan_name, self.first_node_copy, full_job_id)

        #validate delete copy operation on locked copy
        if self.type:
            self.validate_delete_copy_on_locked_copy(self.plan_name, self.first_node_copy)
        else:
            self.validate_delete_copy_on_locked_copy(self.plan_name, self.snap_primary)

        #validate delete plan of locked copy
        self.validate_delete_plan_of_locked_copy(self.plan_name)

    def snaptemplate6(self):
        """
        Main function to verify Immutable snap for supported engines
        """

        self.cleanup()
        if self.add_engine_val:
            self.engine.add_engine(self._array_vendor, self._array_name, self._username, self._password, self._control_host,
                               self._controllers, self._snap_config)
        self.create_entities()

        if self.tcinputs['SnapEngine'] == "INFINIDAT InfiniSnap":
            self.log.info("Running Immutable Snap test using INFINIDAT Array")
            #Verify we cannot enable immutable snap on jobs based retention
            self.validate_immutable_snap_on_jobs_retention(self.plan_name, self.snap_primary)
            if self.type:
                self.validate_immutable_snap_on_jobs_retention(self.plan_name, self.first_node_copy)

            #modify retention on primary snap copy and Vault/Replica copy to 1day
            self.planhelper.modify_retention_on_copy(self.plan_name, self.snap_primary, 1, 'Day(s)', snap_copy=True)
            if self.type:
                #modify retention on first node copy to 1day
                self.planhelper.modify_retention_on_copy(self.plan_name, self.first_node_copy, 1, 'Day(s)', snap_copy=True)

            #enable Immutable snap lock on Primary snap copy and Replica copy
            self.enable_immutable_snap(self.plan_name, self.snap_primary)
            if self.type:
                #enable Immutable snap lock on first node copy
                self.enable_immutable_snap(self.plan_name, self.first_node_copy)

            #validate disable immutable and compliance lock on Primary snap copy and replica copy
            self.validate_disable_compliance_lock(self.plan_name, self.snap_primary)
            self.validate_disable_immutable_snap(self.plan_name, self.snap_primary)
            if self.type:
                #validate disable immutable and compliance lock on first node copy
                self.validate_disable_compliance_lock(self.plan_name, self.first_node_copy)
                self.validate_disable_immutable_snap(self.plan_name, self.first_node_copy)

            #Run steps to validate retention modification on immutable lock copies
            self._execute_retention_modification_steps(self.plan_name, self.snap_primary)
            if self.type:
                self._execute_retention_modification_steps(self.plan_name, self.first_node_copy)

            #Run snap backup, backup copy and aux copy
            source_test_data = self.add_test_data()
            full_job_id = self.run_inline_backup_copy()
            if self.type:
                # Run aux copy
                self.verify_auxcopy(self.plan_name)

            #validate immutable snap flag and expiry time
            self.validate_immutable_snap_flag_and_expiry_time(full_job_id, self.snap_primary)
            if self.type:
                self.validate_immutable_snap_flag_and_expiry_time(full_job_id, self.first_node_copy)

            #validate snap delete operation on locked snap
            self.validate_delete_snap_on_locked_snap(full_job_id, self.snap_primary)
            if self.type:
                self.validate_delete_snap_on_locked_snap(full_job_id, self.first_node_copy)

            #validate delete job operation on locked copy
            self.validate_delete_job_on_locked_copy(self.plan_name, self.snap_primary, full_job_id)
            if self.type:
                self.validate_delete_job_on_locked_copy(self.plan_name, self.first_node_copy, full_job_id)

            #validate delete copy operation on locked copy
            if self.type:
                self.validate_delete_copy_on_locked_copy(self.plan_name, self.first_node_copy)
            else:
                self.validate_delete_copy_on_locked_copy(self.plan_name, self.snap_primary)
            #validate delete plan of locked copy
            self.validate_delete_plan_of_locked_copy(self.plan_name)

        if self.tcinputs['SnapEngine'] == "NetApp":
            self.log.info("Running Immutable Snap test using NetApp Array")
            #Verify we cannot enable immutable snap on jobs based retention
            if self.type:
                #changing retention to 3 jobs
                self.planhelper.modify_retention_on_copy(self.plan_name, self.first_node_copy, 3, jobs=True)
                self.validate_immutable_snap_on_jobs_retention(self.plan_name, self.first_node_copy)

            #modify retention on Vault/Replica copy to 1 day
            if self.type:
                self.planhelper.modify_retention_on_copy(self.plan_name, self.first_node_copy, 1, 'Day(s)', snap_copy=True)

            #enable Immutable snap lock on Vault/Replica copy
            if self.type:
                self.enable_immutable_snap(self.plan_name, self.first_node_copy)

            #validate disable immutable and compliance lock on Vault/Replica copy
            if self.type:
                self.validate_disable_compliance_lock(self.plan_name, self.first_node_copy)
                self.validate_disable_immutable_snap(self.plan_name, self.first_node_copy)

            #Run steps to validate retention modification on immutable lock Vault/Replica copy
            if self.type:
                self._execute_retention_modification_steps(self.plan_name, self.first_node_copy)

            #Run snap backup, backup copy and aux copy
            source_test_data = self.add_test_data()
            full_job_id = self.run_inline_backup_copy()
            if self.type:
                # Run aux copy
                self.verify_auxcopy(self.plan_name)

            #validate immutable snap flag and expiry time
            if self.type:
                self.validate_immutable_snap_flag_and_expiry_time(full_job_id, self.first_node_copy)

            #validate snap delete operation on locked snap
            if self.type:
                self.validate_delete_snap_on_locked_snap(full_job_id, self.first_node_copy)

            #validate delete job operation on locked copy
            if self.type:
                self.validate_delete_job_on_locked_copy(self.plan_name, self.first_node_copy, full_job_id)

            #validate delete copy operation on locked copy
            if self.type:
                self.validate_delete_copy_on_locked_copy(self.plan_name, self.first_node_copy)

            #validate delete plan of locked copy
            self.validate_delete_plan_of_locked_copy(self.plan_name)
