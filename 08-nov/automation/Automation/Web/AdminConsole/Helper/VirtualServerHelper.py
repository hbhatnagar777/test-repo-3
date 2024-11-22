# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run VSA
AdminConsole Automation test cases.

Class:

    AdminConsoleVirtualServer()

    VMWareAdminConsole() -> AdminConsoleVirtualServer()

    HyperVAdminConsole() -> AdminConsoleVirtualServer()

    OracleCloudAdminConsole() -> AdminConsoleVirtualServer()

    AliCloudAdminConsole() -> AdminConsoleVirtualServer()

    OracleCloudInfrastructureAdminConsole() -> AdminConsoleVirtualServer()

    GoogleCloudAdminConsole() -> AdminConsoleVirtualServer()

"""

import os
import time
import re
import socket
import zipfile

from abc import ABCMeta, abstractmethod
import ast
import random
from collections import OrderedDict
import xmltodict
from selenium.common import NoSuchElementException, ElementClickInterceptedException

from AutomationUtils.constants import TEMP_DIR, VIRTUAL_SERVER_TESTDATA_PATH
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from cvpysdk.job import Job
from cvpysdk.job import JobController
from cvpysdk.policies.storage_policies import StoragePolicies
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.Components.dialog import RBackup as Backup
from Web.Common.exceptions import CVWebAutomationException
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.recovery_targets import RecoveryTargets, TargetDetails
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard as Dashboard, \
    RVirtualizationDashboard as VirtualizationDashboard
from Web.AdminConsole.VSAPages.enduser_fullvmrestore import EndUserFullVMRestore
from Web.AdminConsole.VSAPages.enduser_guestfiles_restore import EndUserGuestFilesRestoreSelectFolder
from Web.AdminConsole.VSAPages.guest_files_restore_select_folder import GuestFilesRestoreSelectFolder
from Web.AdminConsole.VSAPages.guest_files_restore_select_volume import GuestFilesRestoreSelectVolume
from Web.AdminConsole.VSAPages.manage_content import ManageContent
from Web.AdminConsole.VSAPages.virtual_machine_files_restore import VirtualMachineFilesRestore
from Web.AdminConsole.VSAPages.configure_vsa_replication_group import ConfigureVSAReplicationGroup
from Web.AdminConsole.VSAPages.disk_level_restore import DiskLevelRestore
from Web.AdminConsole.VSAPages.full_vm_restore import FullVMRestore
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.live_mount import LiveMount
from Web.AdminConsole.VSAPages.replication_target_details import ReplicationTargetDetails
from Web.AdminConsole.VSAPages.replication_targets import ReplicationTargets
from Web.AdminConsole.VSAPages.select_restore import SelectRestore
from Web.AdminConsole.VSAPages.virtual_machines import VirtualMachines
from Web.AdminConsole.VSAPages.vm_details import VMDetails
from Web.AdminConsole.VSAPages.vsa_search_restore import VsaSearchRestore
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails
from Web.AdminConsole.VSAPages.vm_group_file_restore import VMGroupFileRestore
from AutomationUtils import logger, cvhelper, constants, machine
from AutomationUtils import config
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerConstants, OptionsHelper
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSACommcell
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type, RestoreType, HypervisorDisplayName
from VirtualServer.VSAUtils.VirtualServerUtils import get_restore_channel, get_push_install_attempt, get_push_job_id, \
    get_stored_disks, vcloud_df_to_rules, decorative_log
from VirtualServer.VSAUtils import VirtualServerHelper
from . import OptionsHelperMapper
from .LoadModule import load_module
from Web.AdminConsole.AdminConsolePages.server_groups import ServerGroups
from Web.AdminConsole.AdminConsolePages.RecentDownload import RecentDownload
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import DropDown, PanelInfo
from Web.Common.page_object import PageService
import xml.etree.ElementTree as ET
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.VSAPages.instance_configuraton_file_restore import InstanceConfigurationFilesRestore
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails

from ..Components.core import TreeView


class AdminConsoleVirtualServer:
    """ Adminconsole helper for VSA agent """

    __metaclass__ = ABCMeta

    def __new__(cls, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize the object based in instance_type

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the cs DB object

        """

        hv_type = VirtualServerConstants.hypervisor_type
        if instance.instance_name.lower() == hv_type.MS_VIRTUAL_SERVER.value.lower():
            return object.__new__(HyperVAdminConsole)
        elif instance.instance_name.lower() == hv_type.VIRTUAL_CENTER.value.lower():
            return object.__new__(VMwareAdminConsole)
        elif instance.instance_name.lower() == hv_type.Oracle_Cloud_Classic.value.lower():
            return object.__new__(OracleCloudAdminConsole)
        elif instance.instance_name.lower() == hv_type.Alibaba_Cloud.value.lower():
            return object.__new__(AlibabaCloudAdminConsole)
        elif instance.instance_name.lower() == hv_type.AZURE_V2.value.lower():
            return object.__new__(AzureRMAdminConsole)
        elif instance.instance_name.lower() == hv_type.AMAZON_AWS.value.lower():
            return object.__new__(AmazonAdminConsole)
        elif instance.instance_name.lower() == hv_type.Vcloud.value.lower():
            return object.__new__(VcloudAdminConsole)
        elif instance.instance_name.lower() == hv_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower():
            return object.__new__(OracleCloudInfrastructureAdminConsole)
        elif instance.instance_name.lower() == hv_type.Google_Cloud.value.lower():
            return object.__new__(GoogleCloudAdminConsole)
        elif instance.instance_name.lower() == hv_type.Nutanix.value.lower():
            return object.__new__(NutanixAdminConsole)
        elif instance.instance_name.lower() == hv_type.Fusion_Compute.value.lower():
            return object.__new__(FusionComputeAdminConsole)
        elif instance.instance_name.lower() == hv_type.Xen.value.lower():
            return object.__new__(XenAdminConsole)
        else:
            raise Exception("The given Hypervisor has not been automated yet")

    def __init__(self, instance, browser=None, commcell=None, csdb=None, **kwargs):
        """
        A class that represents the VSA functions that can be performed for AdminConsole
            Automation

        Args:
            instance    (object)   --  the instance object

            browser      (object)   --  the browser object

            commcell    (object)   --  the commcell object

            csdb        (object)   --  the commcell database object

        """

        if not browser:
            raise Exception('Driver', -1)
        self.driver = browser.driver
        self.is_metallic = False
        self.log = logger.get_log()
        self.testcase_obj = None
        self.csdb = csdb
        self._login_obj = None
        self.hvobj = None
        self.instance_obj = instance
        self.subclient_obj = None
        self.commcell = commcell
        self._client = None
        self._agent = None
        self._backupset = None
        self._subclient = None
        self._auto_vsa_subclient = None
        self._hypervisor = None
        self._destination_datastore = None
        self._destination_host = None
        self.destination_region = None
        self._instance = instance.instance_name
        self._co_ordinator = None
        self._coordinator_vm_obj = None
        self._server = None
        self._vms = None
        self._content = None
        self._restore_proxy = None
        self._restore_path = None
        self._restore_client = None
        self._agentless_vm = None
        self.vm_path = None
        self._destination_vm_object = None
        self.restore_destination_client = None
        self._restore_instance_type = instance.instance_name
        self._inplace_overwrite = False
        self._power_on_vm_after_restore = True
        self._overwrite_vm = False
        self._vm_restore_prefix = "DeleteMe_AC_"
        self._restore_from_job = None
        self.user_name = None
        self.password = None
        self.image_option = None
        self.private_image = None
        self.visibility_type = None,
        self.publisher_type = None,
        self.offer_type = None,
        self.plan_type = None,
        self.version = None,
        self.vm_tags = None
        self._storage_policy = None
        self._storage_profile = None
        self.run_aux = False
        self.aux_copy = "aux"
        self.admin_creds = {}
        self._ci_enabled = False
        self._verify_ci = False
        self.backup_method = "Regular"
        self.download_directory = None
        self.indexing_v2 = False
        self.recovery_target = None
        self.backup_job = None
        self._backup_job_obj = None
        self.timestamp = None
        self._azure_cross_region_restore = False
        self.cluster_obj = None
        self.restore_network = None
        self._snapshot_rg = None
        self._server_group = None
        self._resource_pool = None
        self.one_click_node_obj = None
        self.config = config.get_config()
        self.admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
        self.navigator = self.admin_console.navigator
        self.recovery_targets_obj = RecoveryTargets(self.admin_console)
        self.target_details_obj = TargetDetails(self.admin_console)
        self.replication_group_obj = ReplicationGroup(self.admin_console)
        self.content_obj = ManageContent(self.admin_console)
        self.restore_vol_obj = GuestFilesRestoreSelectVolume(self.admin_console)
        self.restore_files_obj = GuestFilesRestoreSelectFolder(self.admin_console)
        self.enduser_restore_files_obj = EndUserGuestFilesRestoreSelectFolder(self.admin_console)
        self.enduser_fullvm_obj = EndUserFullVMRestore(self.admin_console)
        self.vm_files_restore_obj = VirtualMachineFilesRestore(self.admin_console)
        self.full_vm_restore_obj = FullVMRestore(self.admin_console)
        self.disk_level_restore_obj = DiskLevelRestore(self.admin_console)
        self.hypervisor_ac_obj = Hypervisors(self.admin_console)
        self.vsa_sc_obj = VsaSubclientDetails(self.admin_console)
        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
        self.vm_groups_obj = VMGroups(self.admin_console)
        self.select_restore_obj = SelectRestore(self.admin_console)
        self.virtual_machines_obj = VirtualMachines(self.admin_console)
        self.vm_details_obj = VMDetails(self.admin_console)
        self.vsa_search_obj = VsaSearchRestore(self.admin_console)
        self.configure_vsa_replication_group_obj = ConfigureVSAReplicationGroup(self.admin_console)
        self.recovery_target_obj = ReplicationTargets(self.admin_console)
        self.recovery_target_details_obj = ReplicationTargetDetails(self.admin_console)
        self.live_mount_obj = LiveMount(self.admin_console)
        self.vm_group_file_restore_obj = VMGroupFileRestore(self.admin_console)
        self.recent_download = RecentDownload(self.admin_console)
        self.instance_config_file_restore_obj = InstanceConfigurationFilesRestore(self.admin_console)

        self.jobs = load_module(
            'Jobs',
            constants.AUTOMATION_DIRECTORY +
            '\\Web\\AdminConsole\\AdminConsolePages'
        )
        self.job_obj = self.jobs.Jobs(self.admin_console)
        self.pg_cont_obj = PageContainer(self.admin_console)
        self.bkpcpy_jobid = """select childJobId from JMJobWF where processedjobid={a}"""
        self.job_status = ["completed"]
        self.expected_job_errors = []

        # backup options
        self._backup_type = Backup.BackupType.FULL
        self.granular_recovery = True
        self._testdata_path = None
        self.testdata_paths = []
        self.backup_folder_name = None
        self.cleanup_testdata_before_backup = True
        self._agentless_dict = None
        self.generate_testdata = True
        self.skip_testdata = False
        self._copy_name = None
        self._copy_precedence = 0
        self.controller_machine = machine.Machine(socket.gethostname(), commcell)
        self.validate_workload = False  # This is for backup workload validation
        self.validate_cbt = False
        self.skip_snapshot_validation = False
        self.validate_restore_workload = False  # This is for restore workload validation
        self.restore_validation_options = {}
        self._do_restore_validation_options = {}
        self._restore_job = None
        self.restore_job_id = None
        self.proxy_obj = {}
        self._restore_options = None
        self._vm_storage_policy = "Datastore Default"
        self.validate_vm_storage_policy = False
        self._conversion_restore = False
        self.metallic_ring_info = kwargs.get("metallic_ring_info", None)
        self.kwargs = kwargs
        self._validation_skip_all = False
        self._validation = True
        self.snap_restore = None
        self._validate_browse_ma_and_cp = False
        self._browse_ma = None
        self._browse_ma_id = None
        self.elastic_plan_region = None
        self.test_file_versions = False
        self.cleanup_versions_file = False
        self.file_versions_folder = "TestFileVersions"
        self.version_file_name = "autoTestFileVersion"
        self.version_file_path = None
        self.previous_backup_timestamp = None
        self._is_indexing_v2 = None
        self.run_discovery = True
        self.vm_setting_options = {}
        self.vm_disk_filter_options = {}
        self.vm_group_disk_filters = {}
        self.rep_target_dict = {}
        self._auto_vsa_client = None
        self.passkey = None
        self.run_pre_backup_config_checks = self.config.Virtualization.run_vm_config_check \
            if hasattr(self.config.Virtualization, "run_vm_config_check") else True
        self.pre_backup_config_checks = VirtualServerConstants. \
            get_pre_backup_validation_checks(instance.instance_name)
        self.validate_testdata_on_live_mount = False
        self.refresh_vmgroup_content = True
        self._csdb = csdb
        self.__rtable = Rtable(self.admin_console)
        self.rmodal_dialog = RModalDialog(self.admin_console)
        self.jobs_obj = Jobs(self.admin_console)
        self.job_details_obj = JobDetails(self.admin_console)
        self._dest_auto_vsa_instance = None
        self.secondary_snap_copy_name = """select name from archGroupCopy where archgroupid=(select id from archGroup
                    where name='{a}') and isSnapCopy=1 and name!='Primary snap' and copy=3"""
        self.secondary_snap_restore = None
        self.aux_copy_job = """SELECT jobid FROM JMAdminJobInfoTable WITH (NOLOCK) WHERE archGrpName = '{a}' and 
                                optype=104 order by jobid desc"""
        self.auxcopy_post_job_run = """select jobId from jmadminjobstatstable where archGrpName = '{a}' and 
                                optype=104 order by jobid desc"""
        self.offline_bkpcpy_jobid = """select max(jobid) from JMJobWF where applicationid = 
                        (select id from APP_Application where subclientName='{a}')"""
        self.plan_obj = Plans(self.admin_console)
        self.plandetails_obj = PlanDetails(self.admin_console)
        self.controlhostid = """Select controlhostid from SMSnap where UniqueIdentifier like '%{a}%' """
        self.arrayname = """Select SMArrayId from SMControlhost where controlhostid = '{b}' """

    @property
    def restore_from_job(self):
        """
        Returns backup jobID to be restored, if set
        Returns:
            value   (String):   value of job id
        """
        return self._restore_from_job

    @restore_from_job.setter
    def restore_from_job(self, value):
        """Sets value to backup job Id to be used for restore
        Args: value (String): backupjobID
        """
        if value:
            self._restore_from_job = value

    @property
    def azure_cross_region_restore(self):
        """
        Returns if cross region restore or not
        Returns:
            true/false     (boolenan):  value of _cross_region_restore

        """
        return self._azure_cross_region_restore

    @azure_cross_region_restore.setter
    def azure_cross_region_restore(self, value):
        """
        Sets the value of  cross region restore fro Azure

        Args:
            true/false   (boolean): value for cross region restore
        """
        self._azure_cross_region_restore = value
        self.skip_testdata = value
        if value:
            self.generate_testdata = False
        else:
            self.generate_testdata = True

    @property
    def conversion_restore(self):
        """
        Returns True if the instance is used as a destination in a conversion restore or False otherwise.

        Returns:
            _conversion_restore     (bool)  -- True if this instance is a target for conversion restore.
        """
        return self._conversion_restore

    @conversion_restore.setter
    def conversion_restore(self, value):
        """
        Sets the instance for conversion restore.

        Args:
            value   (bool)  -- True/False
        """
        self._conversion_restore = value

    @property
    def copy_name(self):
        """
        Returns the copy name for restore

        Returns:
            _copy_name      (str)  --  Copy name

        """
        if not self._copy_name:
            self._copy_name = "Automatic"
        return self._copy_name

    @copy_name.setter
    def copy_name(self, value):
        """
        Sets the copy for restore

        Args:
            value   (str)  --  Copy name

        """
        self._copy_name = value
        self._copy_precedence = self.storage_policy.get_copy_precedence(value.lower())

    @property
    def copy_precedence(self):
        """
        Returns the copy precedence for restore

        Returns:
            _copy_precedence      (int)  --  Copy _copy_precedence

        """
        return self._copy_precedence

    @property
    def browse_ma(self):
        """
        Returns the browse ma for restore

        Returns:
           _browse_ma      (str)  -- Browse ma

        """
        if not self._browse_ma:
            self._browse_ma = self.subclient_obj.storage_ma
            self._browse_ma_id = self.subclient_obj.storage_ma_id
        return self._browse_ma

    @browse_ma.setter
    def browse_ma(self, value):
        """
        Sets the browse ma for restore

        Args:
            value   (str)  --  Browse ma

        """
        self._browse_ma = value
        self._browse_ma_id = self.commcell.clients.get(value).client_id

    @property
    def browse_ma_id(self):
        """
        Returns the browse ma id for restore

        Returns:
           _browse_ma_id      (str)  -- Browse ma ID

        """
        return self._browse_ma_id

    @property
    def backup_type(self):
        """
        Returns the backup type

        Returns:
            _backup_type    (backupType enum)   --  the backup level in Backup.BackupType

        """
        return self._backup_type

    @backup_type.setter
    def backup_type(self, value):
        """
        Sets the backup level of the subclient

        Args:
            value    (str)   --  the level of backup to be run on the subclient

        """
        try:
            for data in Backup.BackupType:
                if data.name == value.upper():
                    self._backup_type = data
                    break
        except Exception:
            type_list = [data.name for data in Backup.BackupType]
            raise CVWebAutomationException(f"backup type : {value}, isn't "
                                           f"among the types in [{type_list}]")
        self.backup_folder_name = value

    @property
    def collect_metadata(self):
        """
        Returns the metadata collection property

        Returns:
            granular_recovery   (bool)   --   true / false for collecting metadata

        """
        return self.granular_recovery

    @collect_metadata.setter
    def collect_metadata(self, value):
        """
        Sets the metadata collection property

        Args:
            value    (bool)  --  True / False for collecting metadata during backup

        """
        self.granular_recovery = value

    @property
    def client(self):
        """ Returns the client object. """

        if self._client is None:
            self._client = self.commcell.clients.get(self.hypervisor)
        return self._client

    @property
    def backupset(self):
        """ Returns the backupset object. """

        if self._backupset is None:
            self._backupset = self.subclient_obj._backupset_object
        return self._backupset

    @property
    def agent(self):
        """ Returns the agent object. """

        if self._agent is None:
            self._agent = self.subclient_obj._agent_object
        return self._agent

    @property
    def testdata_path(self):
        """
        Returns the testdata path

        Returns:
            testdata_path  (str)   --  the location where testdata needs to be copied

        """
        return self._testdata_path

    @testdata_path.setter
    def testdata_path(self, value):
        """
        Sets the testdata path where files needs to be copied before backup

        Args:
            value    (str)   --  the location for copying test data

        """
        self._testdata_path = value

    @property
    def subclient(self):
        """
        Returns the subclient name

        Returns:
            subclient  (str)   --  the name of the subclient to be backed up or restored

        """
        return self._subclient

    @subclient.setter
    def subclient(self, value):
        """
        Sets the subclient name

        Args:
            value    (str)   --  the name of the subclient to be backed up or restored

        """
        self._subclient = value

    @property
    def hypervisor(self):
        """
        Returns the hypervisor name

        Returns:
            hypervisor  (str)   --  the name of the hypervisor

        """
        return self._hypervisor

    @hypervisor.setter
    def hypervisor(self, value):
        """
        Sets the hypervisor name

        Args:
            value   (str)   --  the name of the hypervisor

        """
        self._hypervisor = value

    @property
    def destination_datastore(self):
        """
        Returns the datastore name

        Returns:
             datastore (str) --  the name of the datastore
        """
        return self._destination_datastore

    @destination_datastore.setter
    def destination_datastore(self, value):
        """
        Sets the datastore name

        Args:
             value (str) --  the name of the hypervisor
        """
        self._destination_datastore = value

    @property
    def destination_host(self):
        """
        Returns the destination host ip

        Returns:
             destination_host destination_host (str) --  the ip of the destination host
        """
        return self._destination_host

    @destination_host.setter
    def destination_host(self, value):
        """
        Sets the destinnation host ip

        Args:
             value (str) --  the ip of the destination host
        """
        self._destination_host = value

    @property
    def restore_proxy(self):
        """
        Returns the restore proxy name or None if it doesn't

        Returns:
            restore_proxy  (str)   --  the name of the restore proxy

        """
        if self._restore_proxy is None:
            return None
        if isinstance(self._restore_proxy, str) and self._restore_proxy == "Automatic":
            return self._restore_proxy
        elif self._restore_proxy:
            return self._restore_proxy.machine_name
        else:
            return None

    @property
    def restore_proxy_display_name(self):
        """
        Returns the restore proxy display name if it is set else None

        Returns:
            restore_proxy_display_name  (str)   --  the display name of the restore proxy

        """
        if self._restore_proxy is None:
            return None
        if isinstance(self._restore_proxy, str) and self._restore_proxy == "Automatic":
            return self._restore_proxy
        elif self._restore_proxy:
            return self.commcell.clients.get(self._restore_proxy.machine_name).display_name
        else:
            return None

    @restore_proxy.setter
    def restore_proxy(self, value):
        """
        Sets the restore proxy value

        Args:
            value   (str / obj / tuple)  -- the restore proxy value to be set

        """
        if isinstance(value, str):
            if value.lower() == "automatic":
                self._restore_proxy = "Automatic"
            else:
                self._restore_proxy = machine.Machine(value, self.commcell)
        elif isinstance(value, machine.Machine):
            self._restore_proxy = value
        elif isinstance(value, tuple):
            self.restore_destination_client = value[0]
            self._restore_proxy = machine.Machine(value[1])
        else:
            raise Exception("Please pass the correct type for the restore proxy value")
        if not (isinstance(self._restore_proxy, str) and self._restore_proxy == "Automatic"):
            if self._restore_proxy.os_info.lower() == "windows":
                _storage = self._restore_proxy.get_storage_details()
                for drive in _storage:
                    if isinstance(_storage[drive], dict):
                        self.restore_path = drive + ":\\"
                        break
            else:
                self.restore_path = '/tmp'

    @property
    def restore_client(self):
        """
        Returns the restore client name

        Returns:
            restore_client  (str)   --  the name of the restore client

        """
        return self._restore_client

    @restore_client.setter
    def restore_client(self, value):
        """
        Sets the restore client value

        Args:
            value   (str)   --   the name of the restore client

        """
        self._restore_client = value

    @property
    def dest_client_name(self):
        """
        Returns the restore client name

        Returns:
            restore_client  (str)   --  the name of the restore client

        """
        return self._restore_client

    @property
    def restore_path(self):
        """
        Returns the restore path location

        Returns:
            restore_path  (str)   --  the location to restore to

        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """
        Sets the restore path

        Args:
            value   (str)   --   the path where files are to be restored

        """
        self._restore_path = value

    @property
    def restore_options(self):
        """
        Returns the restore options object

        Returns:
            restore_options (OptionsHelper.FUllVMRestoreOptions)
        """
        return self._restore_options

    @restore_options.setter
    def restore_options(self, value):
        """
        Sets the restore_options object to be used during restore validation

        Args:
             value (OptionsHelper.FUllVMRestoreOptions)
        """
        self._restore_options = value

    @property
    def agentless_vm(self):
        """
        Returns the agentless name

        Returns:
            agentless_vm  (str)   --  the name of the agentless VM where files needs to be
                                           restored to

        """
        return self._agentless_vm

    @agentless_vm.setter
    def agentless_vm(self, value):
        """
        Sets the agentless VM where the backed up files are to be restored during agentless restore

        Args:
            value   (str)   --  the name of the agentless VM

        Raises:
            Exception:
                if the type of the input variable is not a str

        """

        if '//' in value:
            self.vm_path = value.split('//')
            value = self.vm_path[-1]

        if isinstance(value, str):
            self._agentless_vm = value
            if self.restore_client is None:
                self.restore_client = self.hypervisor

            if self.restore_client == self.hypervisor:
                if self.hvobj.instance_type.lower() == hypervisor_type.AMAZON_AWS.value.lower() \
                        and self.destination_region is not None:
                    self.hvobj.aws_region = self.destination_region
                self.restore_destination_client = self.hvobj
            else:
                self.restore_destination_client, \
                    self._restore_instance_type = self._create_hypervisor_object(
                    self.restore_client
                )

            if value not in self._vms:
                self.restore_destination_client.VMs = self._agentless_vm
                self.restore_destination_client.VMs[value].update_vm_info('All', True, True)

        else:
            raise Exception("Please pass the correct type for the agentless vm variable")

    @property
    def instance(self):
        """
        Returns the instance name

        Returns:
            instance  (str)   --  the name of the instance

        """
        return self._instance

    @instance.setter
    def instance(self, value):
        """
        Sets the instance name

        Args:
            value   (str)   -- the name of the instance

        """
        self._instance = value

    @property
    def co_ordinator(self):
        """
        Returns the coordinator name

        Returns:
            co_ordinator  (str)   --  the name of the first proxy in the instance

        """
        if self._co_ordinator:
            return self._co_ordinator.machine_name
        return None

    @co_ordinator.setter
    def co_ordinator(self, value):
        """
        Sets the co-ordinator of the client

        Args:
            value   (str)   --   the name of the co-ordinator proxy client

        """
        self._co_ordinator = machine.Machine(value, self.commcell)

    @property
    def server(self):
        """
        Returns the server name

        Returns:
            server  (str)   --  the name of the server where commands will be executed

        """
        return self._server

    @server.setter
    def server(self, value):
        """
        Sets the server name

        Args:
            value   (str)    --  sets the name of the server

        """
        self._server = value

    @property
    def content(self):
        """
        Returns the content

        Returns:
            VMs  (str)   --  the list of VMs to be backed up and restored

        """
        return self._vms

    @content.setter
    def content(self, value):
        """
        Sets the content of the subclient

        Args:
            value   (str)   --  like    [VM]=startswith=test*,test1
                                        [VM] - represent type
                                                        like [DNS],[HN]
                                        startswith  represent equality in admin console
                                                like endswith,equals
                                        test* - include all VM starts with test
                                               adding dynamic content in admin console
                                        , - to include multiple content
                                        test1 -  non-dynamic content

        """
        self._content = value
        self.set_subclient_content()

    @property
    def power_on_after_restore(self):
        """
        Returns the power on after restore variable

        Returns:
            power_on_vm_after_restore  (bool)   --  True / False to power on the VM
                                                          after restore

        """
        return self._power_on_vm_after_restore

    @power_on_after_restore.setter
    def power_on_after_restore(self, value):
        """
        Sets the power on after restore variable

        Args:
            value   (bool)  -- True / False to power on the VM after restore

        """
        self._power_on_vm_after_restore = value

    @property
    def unconditional_overwrite(self):
        """
        Returns the unconditional overwrite variable

        Returns:
            overwrite_vm  (bool)   --  True / False to overwrite the VM during restore

        """
        return self._overwrite_vm

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        Sets the unconditional overwrite variable

        Args:
            value   (bool)  --  True / False to overwrite the VM during restore

        """
        self._overwrite_vm = value

    @property
    def vm_restore_prefix(self):
        """
        Returns the prefix to be attached to the restore VM name

        Returns:
            vm_restore_prefix  (str)   --  the prefix to tbe attached to the restore VM name

        """
        return self._vm_restore_prefix

    @vm_restore_prefix.setter
    def vm_restore_prefix(self, value):
        """
        Sets the prefix to be attached to the restore VM name

        Args:
            value   (str)    --  the prefix to be attached to the restore VM name

        """
        self._vm_restore_prefix = value

    @property
    def full_vm_in_place(self):
        """
        Returns the full VM in place variable

        Returns:
            inplace_overwrite  (bool)   --  True / False to do an inplace restore

        """
        return self._inplace_overwrite

    @full_vm_in_place.setter
    def full_vm_in_place(self, value):
        """
        Sets the full VM inplace variable

        Args:
            value   (bool)  --  True / False to do an inplace restore

        """
        self._inplace_overwrite = value

    @property
    def storage_profile(self):
        """
        Gets the vCloud Storage Profile

        returns:
            storage_profile  (str)  --  vCloud Storage Profile

        """
        return self._storage_profile

    @storage_profile.setter
    def storage_profile(self, value):
        """
            Sets the vCloud Storage Profile

            Args:
                value   (str)   --  vCloud Storage Profile
        """
        self._storage_profile = value

    @property
    def storage_policy(self):
        """
        Returns the storage policy sdk object

        Returns:
            storage_policy  (object):   the object of the storage policy class

        """
        return self._storage_policy

    @storage_policy.setter
    def storage_policy(self, value):
        """
        Sets the storage policy value

        Args:
            value   (str):   name of the storage policy

        Returns:
            None

        """
        if not isinstance(value, str):
            raise Exception("The storage policy name should be a string")
        policies = StoragePolicies(self.commcell)
        if self.elastic_plan_region:
            value += '-' + self.elastic_plan_region
        try:
            self._storage_policy = policies.get(value)
        except:
            self.log.info("eliminating regions and search")
            for policy in policies.all_storage_policies.keys():
                if value in policy:
                    self._storage_policy = policies.get(policy)

    @property
    def ci_enabled(self):
        """
        Returns the ci flag whether it is enabled or disabled

        Returns:
            ci_enabled  (bool): whether content indexing is enabled or not

        """
        return self._ci_enabled

    @ci_enabled.setter
    def ci_enabled(self, value):
        """
        enables / disables content indexing

        Args:
            value   (bool):     enable / disable content indexing

        """
        if not isinstance(value, bool):
            raise Exception("The content indexing value should be True / False")
        self._ci_enabled = value

    @property
    def verify_ci(self):
        """
        Returns the ci flag whether it is enabled or disabled

        Returns:
            ci_enabled  (bool): whether content indexing is enabled or not

        """
        return self._verify_ci

    @verify_ci.setter
    def verify_ci(self, value):
        """
        enables / disables content indexing

        Args:
            value   (bool):     enable / disable content indexing

        """
        if not isinstance(value, bool):
            raise Exception("The content indexing value should be True / False")
        self._verify_ci = value

    @property
    def vms(self):
        """
        Returns the list of all VMs in the subclient content

        Returns:
            vms (list): list of all VMs in subclient content

        """
        return self._vms

    @property
    def auto_vsa_subclient(self):
        """ Returns the auto vsa subclient object. """
        if self._auto_vsa_subclient is None:
            from VirtualServer.VSAUtils import VirtualServerHelper
            auto_commcell = AutoVSACommcell(self.commcell, self.csdb, **self.kwargs)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance_obj,
                                                                  self.testcase_obj.tcinputs, **self.kwargs)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            self._auto_vsa_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient_obj)
        return self._auto_vsa_subclient

    @auto_vsa_subclient.setter
    def auto_vsa_subclient(self, value):
        """
        Sets the auto vsa subclient object.

        Args:
            value   (object)    -- An AutoVSASubclient Object.
        """
        self._auto_vsa_subclient = value

    @property
    def dest_auto_vsa_instance(self):
        """ Returns the destination client auto vsa instance object """

        if self._dest_auto_vsa_instance is None:
            from VirtualServer.VSAUtils import VirtualServerHelper
            auto_commcell = AutoVSACommcell(self.commcell, self.csdb)
            if self.restore_client:
                _client = self.commcell.clients.get(self.restore_client) if not self.recovery_target else \
                    self.commcell.recovery_targets.get(self.restore_client)
            else:
                _client = self.client
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, _client)
            _agent = _client.agents.get(self.testcase_obj.tcinputs['AgentName']) if not self.recovery_target else \
                self.commcell.clients.get(_client.destination_hypervisor).agents.get(self.testcase_obj.tcinputs['AgentName'])
            if "DestinationInstance" in self.testcase_obj.tcinputs:
                _instance = _agent.instances.get(self.testcase_obj.tcinputs['DestinationInstance'])
            else:
                _instance = _agent.instances.get(self.testcase_obj.tcinputs['InstanceName'])
            self._dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, _agent, _instance, self.testcase_obj.tcinputs, **self.kwargs)

        return self._dest_auto_vsa_instance

    @property
    def auto_vsa_client(self):
        """ Returns the auto vsa client object """

        if self._auto_vsa_client is None:
            from VirtualServer.VSAUtils import VirtualServerHelper
            AutoVSACommcell_obj = AutoVSACommcell(self.commcell, self.csdb)
            client = self.commcell.clients.get(self.hypervisor)
            self._auto_vsa_client = VirtualServerHelper.AutoVSAVSClient(AutoVSACommcell_obj, client)
        return self._auto_vsa_client

    @auto_vsa_client.setter
    def auto_vsa_client(self, value):
        """
        Sets the auto vsa client object

        Args:
            value   (object)    --  AutoVSAVSClient Object.
        """
        self._auto_vsa_client = value

    @property
    def backup_job_obj(self):
        if self.backup_job is not None:
            self._backup_job_obj = JobController(self.commcell).get(self.backup_job)
        return self._backup_job_obj

    @property
    def coordinator_vm_obj(self):
        """ Returns the VM object of the coordinator. """
        if self._coordinator_vm_obj:
            return self._coordinator_vm_obj
        try:
            if self.hvobj and self.co_ordinator:
                vm_name = self.hvobj.get_vmname_by_ip(self._co_ordinator.ip_address)
                self._coordinator_vm_obj = HypervisorVM(self.hvobj, vm_name)
                return self._coordinator_vm_obj
        except Exception as exp:
            self.log.exception("Failed to get the proxy VM object: %s", str(exp))
            raise exp

    @property
    def restore_job(self):
        """ Returns a cvpydsk Job object for the restore job. """
        if self._restore_job is None:
            self._restore_job = Job(self.commcell, self.restore_job_id)
        return self._restore_job

    @property
    def snapshot_rg(self):
        """
        Returns the RG for taking snapshot in

        Returns:
            snapshot_rg     (str):  value of snapshot RG

        """
        return self._snapshot_rg

    @snapshot_rg.setter
    def snapshot_rg(self, value):
        """
        Sets the RG for taking snapshot in

        Args:
            value   (str):  value for snapshot RG
        """
        self._snapshot_rg = value

    @property
    def validation_skip_all(self):
        """
        Returns if all the validation are to be skipped

        Returns:
            validation_skip_all     (bool):  whether to skip all validation or not.

        """
        return self._validation_skip_all

    @validation_skip_all.setter
    def validation_skip_all(self, value):
        """
        Sets whether it should skip all the validations

        Args:
            value   (bool):  whether to skip all validation or not.
        """
        self._validation_skip_all = value

    @property
    def validation(self):
        """
        Returns if the backup validations are to be skipped

        Returns:
            validation     (bool):  whether to skip validation or not.

        """
        return self._validation

    @validation.setter
    def validation(self, value):
        """
        Sets whether it should skip the backup validations

        Args:
            value   (bool):  whether to skip backup validation or not.
        """
        self._validation = value

    @property
    def is_indexing_v2(self):
        """
        Checks whether the client is indexing v1 or v2.

        Returns:
            _is_indexing_v2     (bool):  Whether the client is indexing v1 or v2.
                                (None):  If the subclient is not initialized.
        """
        if self._is_indexing_v2 is None and self.auto_vsa_subclient is not None:
            self._is_indexing_v2 = self.auto_vsa_subclient.auto_vsaclient.isIndexingV2
        return self._is_indexing_v2

    @property
    def server_group(self):
        """
        Returns the Server Group name

        Returns:
            hypervisor  (str)   --  the name of the Server Group

        """

        return self._server_group

    @server_group.setter
    def server_group(self, value):
        """
        Sets the server Group name

        Args:
            value   (str)   --  the name of the Server Group

        """
        self._server_group = value

    @property
    def resource_pool(self):
        """
        Returns the Resource Pool name

        Returns:
            hypervisor  (str)   --  the name of the Resource Pool

        """
        return self._resource_pool

    @resource_pool.setter
    def resource_pool(self, value):
        """
        Sets the Resource Pool name

        Args:
            value   (str)   --  the name of the Resource Pool

        """
        self._resource_pool = value

    def _set_agentless_dict(self, agentless_dict):
        """
        Sets the agentless VM where the backed up files are to be restored during agentless restore for individual VMs

        Args:
            agentless_dict   (dict)   -- VMname :  the name of the agentless VM

        Raises:
            Exception:
                iffails to set agentless VM

        """
        self._agentless_dict = agentless_dict
        self.agentless_vm = self._agentless_dict[next(iter(self._agentless_dict))]

    def __deepcopy__(self, temp_obj):
        """
        over ride deepcopy method to copy every attribute of an object to other

        Args:
            temp_obj    (object)   --  the object to be copied

        Raises:
            Exception:
                if deep copy fails to set the object

        """
        try:
            cls = temp_obj.__class__
            result = cls.__new__(cls, temp_obj.hvobj, temp_obj.vm_name)
            for key, value in temp_obj.__dict__.items():
                setattr(result, key, value)
            return result

        except Exception as exp:
            self.log.exception("Failed to deepcopy Exception: %s", str(exp))
            raise exp

    def _create_hypervisor_object(self, client_name=None):
        """
        Create Hypervisor Object

        Args:
            client_name  (str)   --  the name of the client to create the hypervisor
                                                object for
                    default :   None

        Raises:
            Exception:
                if initialization fails in creating object

        Returns:
            hvobj   (object)   --  the object of the hypervisor class of the corresponding instance

            instance_name   (str)    --  the instance name

        """
        try:
            if client_name is None:
                client_name = self.hypervisor
                instance = self.instance_obj
            else:
                client = self.commcell.clients.get(client_name)
                agent = client.agents.get('Virtual Server')
                instance_keys = next(iter(agent.instances._instances))
                instance = agent.instances.get(instance_keys)

            self.creds = {}
            host_machine1 = socket.gethostbyname_ex(socket.gethostname())[2][0]
            host_machine2 = instance.co_ordinator
            server_host_name = instance.server_host_name
            self.password = ''
            self._compute_credentials(client_name)
            self.user_name = self.creds.get('Virtual Server User', "").strip()
            _password = self.creds.get('Virtual Server Password', None)
            if _password:
                if self.is_metallic:
                    self.password = cvhelper.format_string(self.metallic_commcell, _password.strip())
                else:
                    self.password = cvhelper.format_string(self.commcell, _password.strip())

            if instance._instance_name == hypervisor_type.AZURE.value.lower() or \
                    instance._instance_name == hypervisor_type.AZURE_V2.value.lower():
                id1 = self.creds.get('Azure Subscription Id', '').strip()
                id2 = self.creds.get('Azure Tenant Id', '').strip()
                _password1 = (self.password,
                              id1,
                              id2)
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password1, instance._instance_name,
                                   self.commcell, host_machine2)
            elif instance._instance_name == hypervisor_type.Alibaba_Cloud.value.lower():
                self.password = self.creds.get('Alibaba Cloud Secret Key')
                self.password = cvhelper.format_string(self.commcell, self.password.strip())
                self.user_name = self.creds.get('Alibaba Cloud Access Key')
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, instance._instance_name,
                                   self.commcell, host_machine1)
            elif instance._instance_name == hypervisor_type.Vcloud.value.lower() and int(self.creds.get('org_client')):
                server_host_name = self.creds.get('server_host_name')
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, instance._instance_name,
                                   self.commcell, host_machine1, org_client=self.creds.get('org_client'))
            elif instance._instance_name == hypervisor_type.AMAZON_AWS.value.lower():
                if self.is_metallic:
                    _password2 = (self.creds.get(
                        'Virtual Server User',
                        cvhelper.format_string(self.metallic_commcell,
                                               self.creds.get('Amazon Center Access Key', '').strip())),
                                  cvhelper.format_string(
                                      self.metallic_commcell,
                                      self.creds.get(
                                          'Virtual Server Password',
                                          self.creds.get('Amazon Center Secret Key', '')).strip()))
                else:
                    _password2 = (self.creds.get(
                        'Virtual Server User',
                        cvhelper.format_string(self.commcell,
                                               self.creds.get('Amazon Center Access Key', '').strip())),
                                  cvhelper.format_string(
                                      self.commcell,
                                      self.creds.get(
                                          'Virtual Server Password',
                                          self.creds.get('Amazon Center Secret Key', '')).strip()))
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password2, instance._instance_name,
                                   self.commcell, host_machine1, region=self.region, is_tenant = self.is_tenant,
                                   **self.kwargs)
            elif instance._instance_name == hypervisor_type.Google_Cloud.value.lower():
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, instance._instance_name,
                                   self.commcell, host_machine2,
                                   project_id=self.testcase_obj.tcinputs['ProjectID'],
                                   vm_custom_metadata=self.testcase_obj.tcinputs.get('vmCustomMetadata', []),
                                   service_account=self.testcase_obj.tcinputs.get('service_account', ""))
            elif instance._instance_name == hypervisor_type.MS_VIRTUAL_SERVER.value.lower() or \
                    instance._instance_name == hypervisor_type.OPENSTACK.value.lower():
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, instance._instance_name,
                                   self.commcell, host_machine2)
            elif instance._instance_name.lower() == \
                    hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower():
                '''
                We are going to pass all variables as part of a dict in the username field
                itself since there are not enough fields to hypervisor class
                and password will be passed as an empty string.
                You can see the dict def below
                '''
                server_host_name = instance.server_name
                try:
                    oci_private_key_file_path = self.config.Virtualization.oci.private_key_file_path
                except Exception as exp:
                    self.log.warning(exp)
                    self.log.info("Unable to get oci_private_key_file_path from config.json, reading from testcase.json")
                    oci_private_key_file_path = self.testcase_obj.tcinputs['oci_private_key_file_path']
                self.creds['Oracle Cloud Infrastructure Private File Path'] = oci_private_key_file_path
                self.server_host_name = server_host_name
                oci_dict = {'oci_tenancy_id': self.creds['Oracle Cloud Infrastructure Tenancy Id'].strip(),
                            'oci_user_id': self.creds['Oracle Cloud Infrastructure User Id'].strip(),
                            'oci_finger_print': self.creds['Oracle Cloud Infrastructure Finger Print'].strip(),
                            'oci_private_key_file_path': self.creds['Oracle Cloud Infrastructure Private File Path'].strip(),
                            'oci_private_key_password': self.password,
                            'oci_region_name': self.creds['Oracle Cloud Infrastructure Region Name'].strip()
                            }
                if self.is_metallic:
                    oci_dict['oci_private_key_password'] = cvhelper.format_string(
                        self.metallic_commcell,
                        self.creds['Oracle Cloud Infrastructure Private Key Password'].strip())
                hvobj = Hypervisor(server_host_name, oci_dict, '',
                                   self._instance.lower(), self.commcell, host_machine1)
            elif instance._instance_name.lower() == hypervisor_type.Nutanix.value.lower():
                _password3 = (self.password, self.creds['Virtual Server Host'].strip())
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password3, instance._instance_name.lower(),
                                   self.commcell, host_machine2)
            else:
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, instance._instance_name,
                                   self.commcell, host_machine1)
            return hvobj, instance.instance_name

        except Exception as exp:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s", str(exp))
            raise exp

    def _compute_credentials(self, client_name):
        """Compute the credentials required to call the server

        Args:
            client_name (str)   --   the name of the client whose credentials are
                                            to be obtained

        Raises:
            Exception:
                if compute credentials fails to get the credentials from the database


        """
        try:
            _query = "select attrName, attrVal from app_Instanceprop where componentNameid =( \
                                  select TOP 1 instance  from APP_Application where clientId= ( \
                                  Select TOP 1 id from App_Client where name = '%s' UNION Select TOP 1 id from App_Client where displayName = '%s') and appTypeId = '106' and \
                                 attrName in %s)" % (client_name, client_name, VirtualServerConstants.attr_name)
            if self.is_metallic:
                from cvpysdk.commcell import Commcell
                from AutomationUtils.database_helper import CommServDatabase
                if self.metallic_ring_info:
                    temp_commcell = Commcell(self.metallic_ring_info['commcell'],
                                             commcell_username=self.metallic_ring_info['user'],
                                             commcell_password=self.metallic_ring_info['password'])

                    temp_csdb = CommServDatabase(temp_commcell)
                    temp_csdb.execute(_query)
                    _results = temp_csdb.fetch_all_rows()
                    self.metallic_commcell = temp_commcell
            else:
                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
            if not _results:
                raise Exception("An exception occurred getting server details")
            '''
            Added below code to differentiate in compute creds for OCI from others.
            Original was wihtout the if/else 
            '''
            for rows in _results:
                self.creds[rows[0]] = rows[1]
            self.creds['org_client'] = self.creds.get('Amazon Admin Instance Id', 0)
            if int(self.creds.get('Amazon Admin Instance Id', 0)) > 0:
                _query = '''select attrName, attrVal from app_Instanceprop where componentNameid=(
                                                                      select TOP 1 attrVal from app_Instanceprop where componentNameid=
                                                                      (select TOP 1 instance  from APP_Application where clientId=
                                                                      (Select TOP 1 id from App_Client where name = '%s') and appTypeId = '106'
                                                                      and attrName in ('Amazon Admin Instance Id')))
                                                                      and attrName in %s''' % (client_name, VirtualServerConstants.attr_name)

                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
                if not _results:
                    raise Exception("An exception occurred in getting admin hypervisor credentials")
                for rows in _results:
                    self.admin_creds[rows[0]] = rows[1]
                if self._instance.lower() == hypervisor_type.Vcloud.value.lower():
                    self.creds['server_host_name'] = self.admin_creds['Virtual Server Host']
            if int(self.creds.get('Virtual Server Credential Assoc Id', 0)) > 0:
                _query = '''select userName, password, credentialInfo from APP_Credentials join APP_CredentialAssoc 
                        on APP_Credentials.credentialId = APP_CredentialAssoc.credentialId and 
                        APP_CredentialAssoc.assocId = %s''' % (self.creds['Virtual Server Credential Assoc Id'])
                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
                if not _results:
                    raise Exception("An exception occurred in getting hypervisor credentials from "
                                    " the saved credentials")

                if self._instance.lower() == hypervisor_type.AZURE_V2.value.lower() and _results[0][1] != '':
                    _cred_info_dict = xmltodict.parse(_results[0][2])
                    self.creds['Azure Tenant Id'] = \
                        _cred_info_dict['App_AdditionalCredInfo']['azureCredInfo']['@tenantId']
                elif self._instance.lower() == hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower() and \
                        _results[0][2] != '':
                    _cred_info_dict = xmltodict.parse(_results[0][2])
                    self.creds['Oracle Cloud Infrastructure Finger Print'] = _results[0][0]
                    self.creds['Oracle Cloud Infrastructure Tenancy Id'] = \
                        _cred_info_dict['App_AdditionalCredInfo']['oracleCredentialInfo']['@tenancyOCID']
                    self.creds['Oracle Cloud Infrastructure User Id'] = \
                        _cred_info_dict['App_AdditionalCredInfo']['oracleCredentialInfo']['@userOCID']
                self.creds['Virtual Server User'] = _results[0][0]
                self.creds['Virtual Server Password'] = _results[0][1]
                return self.creds

        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting credentials for Compute Credentials  %s", err)
            raise err

    @staticmethod
    def _get_disk_list(disk_list=None):
        """
        Gets the names of the disks to be restored

        Args:
            disk_list    (list)  --  the list containing all the disks to be restored

        Returns:
            final_disk_list     (list)  --  the list of disk names to be restored

        """
        try:
            final_disk_list = []
            if not disk_list:
                raise Exception("The disk list is empty. Please check the logs.")
            for disk in disk_list:
                final_disk_list.append(disk.split("\\")[-1])
            return final_disk_list
        except Exception as exp:
            raise exp

    def _navigate_to_vmgroup(self):
        """
        Navigates to VM group details page to submit backup
        """
        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])

    def _navigate_to_vm(self, vm_name):
        """
        Navigates to VM details page
        """
        self.navigator.navigate_to_virtual_machines()
        self.virtual_machines_obj.open_vm(vm_name)

    def _navigate_to_vm_restore(self, vm_name):
        """
        Navigates to the individual VM page to trigger restore from VM level

        Args:
            vm_name     (str):   the name of the VM to restore

        Raises:
            Exception:
                if the restore page from VM level could not be opened

        """
        self.navigator.navigate_to_virtual_machines()
        self.virtual_machines_obj.open_vm(vm_name)
        self.vm_details_obj.vm_restore()

    def _navigate_to_active_mounts(self, vm_name):
        """
        Navigates to the individual VM to access active mounts from VM level

        Args:
            vm_name     (str):   the name of the VM

        Raises:
            Exception:
                if the Active Mounts page from VM level could not be opened

        """
        self.navigator.navigate_to_virtual_machines()
        self.virtual_machines_obj.action_list_mounts(vm_name)

    def delete_live_mount(self, vm_name):
        """
            Navigates to the individual VM to delete active mounts from VM level

            Args:
                vm_name     (str):   the name of the VM

            Raises:
                Exception:
                    if the Active Mounts page from VM level could not be opened

        """
        self._navigate_to_active_mounts(vm_name)
        return self.virtual_machines_obj.delete_active_live_mount(vm_name)

    def logout_command_center(self):
        """
        Logs out of the command center session
        """
        try:
            elements = self.driver.find_elements(By.XPATH, "//a[@class='modal__close-btn']")
            for element in elements:
                element.click()
                self.admin_console.wait_for_completion()
            self.navigator.logout()
        except Exception as exp:
            self.log.error("Could not logout of command center")
            raise exp

    def _end_user_restore_job(self, vm_list):
        """
        Submits a restore job with the given inputs for end user

          Args:
            vm_list     (list):    VMs to restore

          Raises:
            ValueError: If vm_list is not a list or is empty.
        """
        if not isinstance(vm_list, list) or not vm_list:
            raise ValueError("vm_list must be a non-empty list")
        self.restore_job_id = self.enduser_fullvm_obj.enduser_full_vm_restore(
            vm_list[0],
            inplace=self.full_vm_in_place,
            power_on=self.power_on_after_restore,
            over_write=self.unconditional_overwrite,
            restore_prefix=str(self.vm_restore_prefix)
        )

        job_details = self.get_job_status(self.restore_job_id)

    def end_user_full_vm_restore(self):
        """
            Performs full VM restore at VM level as end user
                Raises:
                    Exception:
                        if full VM restore or validation fails

        """
        if self.restore_client is None:
            self.restore_client = self.hypervisor
            self.restore_destination_client = self.hvobj
        elif self.commcell.clients.has_client(self.restore_client) and not self.restore_destination_client:
            self.restore_destination_client, \
                self._restore_instance_type = self._create_hypervisor_object(self.restore_client)
        for _vm in self._vms:
            self._navigate_to_vm_restore(_vm)
            self.select_restore_obj.select_full_vm_restore()
            self._end_user_restore_job([_vm])

        for _vm in self._vms:
            if self.full_vm_in_place:
                restore_vm = _vm
            else:
                restore_vm = str(self.vm_restore_prefix) + _vm
            self.vm_restore_validation(_vm, restore_vm)

    def get_all_vms(self):
        """
        Get the list of all VMs from the vmgroup content

        Raises:
            Exception:
                if it fails to get the list of all VMs in the vmgroup content from adminconsole

        """
        try:
            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            if self.subclient_obj:
                try:
                    proxies = self.subclient_obj._get_subclient_proxies()
                    for proxy in proxies:
                        try:
                            self.co_ordinator = proxy
                            break
                        except Exception as exp:
                            self.log.warning(exp)
                            pass
                except Exception as exp:
                    pass
            try:
                if self.is_metallic and self.instance.lower() != hypervisor_type.AZURE.value.lower():
                    proxy_list = self.instance_obj.associated_clients
                    self.co_ordinator = proxy_list[0]
            except:
                pass
            if not self._co_ordinator and not self.is_metallic:
                proxy_panel_list = self.hypervisor_details_obj.proxy_info()
                proxy_list = []
                for member in proxy_panel_list:
                    proxy_group = re.search("(.+)\(group\)$", member)
                    dn = re.search("(.+)_DN$", member)
                    if proxy_group:
                        proxy_group = proxy_group.group(1).strip()
                        if self.commcell.client_groups.has_clientgroup(proxy_group):
                            client_group = self.commcell.client_groups.get(proxy_group)
                            proxy_list.extend(client_group.associated_clients)
                    elif dn:
                        proxy_list.append(dn.group(1))
                    else:
                        proxy_list.append(member)
                for proxy in list(dict.fromkeys(proxy_list)):
                    try:
                        self.co_ordinator = proxy
                        break
                    except Exception as exp:
                        self.log.warning(exp)
                        pass
            if not self.restore_proxy == "Automatic":
                if not self.co_ordinator:
                    if self.auto_vsa_subclient.auto_vsainstance.kwargs.get('BYOS') != False:
                        raise Exception("Failed to reach all the access nodes specified at the Hypervisor and VM group level")
                    else:
                        self.log.info("Coordinator is %s", self.co_ordinator)
            if not self.conversion_restore:
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                self.vsa_sc_obj.manage_content()
                self._vms = self.content_obj.preview().keys()
                if not self.is_metallic:
                    self.storage_policy = self.vsa_sc_obj.get_plan()
                if self.snapshot_rg is not None:
                    _snapshot_rg_set = self.get_snapshot_rg()

                    if not _snapshot_rg_set:
                        self.set_snapshot_rg()
                    elif _snapshot_rg_set.lower() != self.snapshot_rg.lower() and \
                            self.backup_type == Backup.BackupType.INCR:
                        raise Exception("Changing RG in incremental will result in automation CBT validation failure")

        except Exception as exp:
            self.log.exception("Exception while getting all the VMs "
                               "in the subclient content: %s", str(exp))
            raise exp

    def set_subclient_content(self):
        """
        Set the content for the given subclient

        Raises:
            Exception:
                if it fails to set the subclient content via admin console

        """
        try:
            self.log.info("Setting the subclient content")

            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.manage_content()

            content = ast.literal_eval(self._content)
            if "vm" in content.keys():
                self.content_obj.add_vm(content["vm"])
            if "rule" in content.keys():
                rules_list = content["rule"]
                for rule in rules_list:
                    rule_type, expression, name = rule.split(":")
                    self.content_obj.add_rule(rule_type, expression, name)

        except Exception as exp:
            self.log.exception("Exception while setting subclient content: %s", str(exp))
            raise exp

    def vsa_discovery(self):
        """
        VSA discovery to copy all test data

        Raises:
            Exception:
                if the discovery fails

        """
        try:
            VirtualServerUtils.decorative_log("Creating Hypervisor and VM objects")
            if not self.backup_folder_name:
                if isinstance(self.backup_type, str):
                    self.backup_folder_name = self.backup_type
                else:
                    self.backup_folder_name = self.backup_type.name

            if self.refresh_vmgroup_content:
                self.get_all_vms()

            if not self.hvobj:
                self.hvobj = self._create_hypervisor_object()[0]            
            for each_vm in self._vms:
                if each_vm not in self.hvobj.VMs:
                    self.log.info("Creating object for VM %s", each_vm)
                    self.hvobj.VMs = each_vm
                self.log.info(":: line 1948 :: invoking update_vm_info for %s",self.hvobj.VMs[each_vm]) #del
                self.hvobj.VMs[each_vm].update_vm_info('All', os_info=True, force_update=True)
                self.log.info("Update VM info done successfully :: line 1949")  #del
                self.log.info("Copying configuration to auto_vsa_subclient object for the VM {0}".format(each_vm))
                self.auto_vsa_subclient.hvobj.VMs[each_vm] = self.__deepcopy__(self.hvobj.VMs[each_vm])
            
            if self.run_pre_backup_config_checks:
                # Run pre backup configuration checks
                self.auto_vsa_subclient. \
                    check_configuration_before_backup(self.pre_backup_config_checks)
            
            
            ##### UNCOMMENT BELOW BLOCK #####
            # if not self.azure_cross_region_restore:
            #     self.log.info("In Testdata generation")
            #     if not self.testdata_path:
            #         self.testdata_path = VirtualServerUtils.get_testdata_path(
            #             self.controller_machine)
            #         self.timestamp = self.testdata_path.rpartition('\\')[-1]
            #     if self.testdata_path not in self.testdata_paths:
            #         self.testdata_paths.append(self.testdata_path)

            #     if self.cleanup_testdata_before_backup:
            #         self.cleanup_testdata()

            #     if self.generate_testdata:
            #         generate = self.controller_machine.generate_test_data(self.testdata_path)
            #         self.log.info("Generating TestData at path: {}".format(self.testdata_path))
            #         if not generate:
            #             raise Exception(generate)

            #     if self.test_file_versions:
            #         file_name = self.version_file_name + ".txt"
            #         self.version_file_path = VirtualServerUtils.get_version_file_path(self.hvobj.machine)
            #         version_file_path = self.controller_machine.join_path(self.version_file_path, self.timestamp)
            #         self.log.info("Generating file versions data at path: {}".format(version_file_path))
            #         generate = self.controller_machine.generate_test_data(
            #             version_file_path, dirs=0, files=1, file_size=100, levels=0,
            #             ascii_data_file=True, **{'custom_file_name': file_name})

            #         if not generate:
            #             raise Exception(generate)

        #     for _vm in self._vms:

        #         if not self.validation and self.validation_skip_all:
        #             VirtualServerUtils.decorative_log("Validation set to skip all: "
        #                                               "skipping testdata creation and copying")
        #             return

        #         if not self.azure_cross_region_restore and not self.skip_testdata:
        #             for _drive in self.hvobj.VMs[_vm].drive_list.values():
        #                 self.log.info("Copying Testdata to Drive %s", _drive)
        #                 self.hvobj.copy_test_data_to_each_volume(
        #                     _vm, _drive, self.backup_folder_name, self.testdata_path)
        #             if self.ci_enabled:
        #                 _drive = next(iter(self.hvobj.VMs[_vm].drive_list.values()))
        #                 self.hvobj.copy_content_indexing_data(_vm, _drive, self.backup_folder_name)
        #             if self.test_file_versions:
        #                 # file_name = self.backup_type.name + "_" + self.version_file_name + "1.txt"
        #                 file_name = self.version_file_name + "1.txt"
        #                 _drive = next(iter(self.hvobj.VMs[_vm].drive_list.values()))
        #                 version_file_path = self.controller_machine.join_path(self.version_file_path,
        #                                                                       self.timestamp,
        #                                                                       "files_with_custom_name",
        #                                                                       file_name)
        #                 self.hvobj.VMs[_vm].copy_version_file_data(version_file_path, _drive,
        #                                                            self.file_versions_folder, file_name,
        #                                                            self.version_file_name + ".txt")

        except Exception as exp:
            self.log.exception("Exception while copying test data: %s", str(exp))
            raise exp

    def _submit_backup_job(self, vm_list=None):
        """
                Submits a backup job with the given inputs
                Args:
                    vm_list     (list):    VMs to backup

        """
        auto_commcell_obj = AutoVSACommcell(self.commcell, self.csdb)
        common_utils = CommonUtils(auto_commcell_obj.commcell)
        if self.backup_type == Backup.BackupType.SYNTH:
            _bc_types = [Backup.BackupType.INCR, Backup.BackupType.SYNTH]
        else:
            _bc_types = [self.backup_type]
        for _bc_type in _bc_types:

            _backup_jobs = self.vsa_sc_obj.backup_now(_bc_type)
            if not isinstance(_backup_jobs, list):
                _backup_jobs = [_backup_jobs]
            for _backup_job in _backup_jobs:
                self.backup_job = _backup_job
                job_details = self.get_job_status(self.backup_job)

            if _bc_type == Backup.BackupType.SYNTH and self.backup_method.lower() == "regular":
                self.backup_job = auto_commcell_obj.get_vm_parentjob(self.backup_job, 7)
                if self.backup_job_obj.backup_level.lower() == "synthetic full":
                    self.indexing_v2 = True
                else:
                    self.verify_synth_full_backup()

            if self.backup_method.lower() == "snap" and _bc_type != Backup.BackupType.SYNTH:
                self.log.info("Backup Type is not Synthfull, looking for backup copy job")
                bkpcopy_job = self.storage_policy.run_backup_copy()
                self.log.info(f"Backup Copy Job ID returned is: {0}", bkpcopy_job)
                retry = 0
                while retry < 5:
                    try:
                        time.sleep(30)
                        bkpcopy_job = common_utils.get_backup_copy_job_id(
                            self.backup_job)
                        self.backupcopy_job = Job(self.commcell, bkpcopy_job)
                        self.log.info("Backup Copy Job ID : {0}".format(bkpcopy_job))
                        break

                    except Exception:
                        time.sleep(30)
                        retry = retry + 1
                job_details = self.get_job_status(bkpcopy_job)

            if _bc_type != Backup.BackupType.SYNTH and self.ci_enabled:
                retry = 3
                while retry >= 0:
                    file_indexing_job_id = self.auto_vsa_subclient.get_in_line_file_indexing_job()
                    if file_indexing_job_id:
                        break
                    time.sleep(30)
                    retry -= 1
                file_indexing_job = self.get_job_status(file_indexing_job_id)

                if self.verify_ci:
                    file_indexing_job_details = self.auto_vsa_subclient. \
                        get_file_indexing_job_details(file_indexing_job_id)

                    for guid in file_indexing_job_details.keys():
                        child_backup_job_id = file_indexing_job_details[guid][0]
                        vm_guid = guid
                        self.log.info("Validate Archive Files")
                        # self.auto_vsa_subclient.validate_file_indexing_archive_files(child_backup_job_id)

        if self.run_aux and len(self.storage_policy.copies) > 1:
            if self.storage_policy.aux_copies:
                self.aux_copy = self.storage_policy.aux_copies[0]
                aux_job = self.storage_policy.run_aux_copy(self.aux_copy)
                aux_job = aux_job.job_id
                job_details = self.get_job_status(aux_job)

        if not self.validation and self.validation_skip_all:
            self.log.info("Backup Validation set to be SKIPPPED")
            return

        OptionsHelperMapper.BackupOptionsMapping(self). \
            validate_backup(vm_list=vm_list, vm_group_disk_filters=self.vm_group_disk_filters)

    def backup(self, vm_level=False):
        """
        Run backup for the given subclient from admin console

        Raises:
            Exception:
               If backup job does not complete successfully

        """
        try:
            if self.run_discovery:
                self.vsa_discovery()

            if self.vm_setting_options:
                self.log.info("Applying input backup settings for all the VMs. Backup setting options : [{0}]".format(
                    self.vm_setting_options))
                self.setup_vm_settings()
                self._navigate_to_vmgroup()

            if self.vm_disk_filter_options:
                self.log.info("Applying input disk filters for all the VMs. Disk Filter options : [{0}]".format(
                    self.vm_disk_filter_options))
                self.setup_vm_disk_filters()
                self._navigate_to_vmgroup()

            if self.vm_group_disk_filters:
                self.log.info("Defining disk filters for VM Group object. [{}]".format(self.vm_group_disk_filters))

                if self.instance == hypervisor_type.Vcloud.value:
                    self.vm_groups_obj.setup_disk_filters(vcloud_df_to_rules(self.vm_group_disk_filters))
                else:
                    self.vm_groups_obj.setup_disk_filters(self.vm_group_disk_filters)

            VirtualServerUtils.decorative_log("Running backup for the subclient")

            if vm_level:
                self.log.info("VM level backup")
                for vm in self.hvobj.VMs:
                    self._navigate_to_vm(vm)
                    self._submit_backup_job([vm])
            else:
                self._submit_backup_job()

        except Exception as exp:
            self.log.exception("Exception while submitting backup: %s", str(exp))
            raise exp

    def mount_snap(self, jobid):
        """
        Mount the vsa snapshot to the esx
        Args:
            jobid      (string):     Recent ran jobid of the backup
        Returns:
              mount_jobid : jobid of mount operation
        """
        self.log.info("Going to mount the vsa snapshot")
        self._navigate_to_vmgroup()
        self.pg_cont_obj.access_page_action_from_dropdown('List snapshots')
        self.log.info(f"job_id {jobid}")
        self.__rtable.access_action_item(jobid, "Mount")
        self.rmodal_dialog.click_submit(wait=False)
        self.admin_console.click_button_using_text('Yes')
        mount_jobid = self.admin_console.get_jobid_from_popup()
        job_details = self.get_job_status(mount_jobid)
        if not job_details:
            raise Exception("mount job Failed. check logs")
        return mount_jobid

    def unmount_snap(self, job_id):
        """
        Unmounts the snap with the given jobid
        Args :
            job_id   (string)    -- jobid to be unmounted
        Returns:
              unmount_jobid : jobid of unmount operation
        """
        self.log.info("Going to Unmount the vsa snapshot")
        self._navigate_to_vmgroup()
        self.pg_cont_obj.access_page_action_from_dropdown('List snapshots')
        self.log.info(f"job_id {job_id}")
        self.__rtable.reload_data()
        self.__rtable.access_action_item(job_id, "Unmount")
        self.rmodal_dialog.click_submit(wait=False)
        unmount_jobid = self.admin_console.get_jobid_from_popup()
        job_details = self.get_job_status(unmount_jobid)
        if not job_details:
            raise Exception("unmount job Failed. check logs")
        return unmount_jobid

    def delete_snap(self, jobid):
        """
        delete the vsa snapshot to the esx
        Args:
            jobid      (string):     Recent ran jobid of the backup
        Returns:
              delete_jobid : jobid of delete operation
        """
        self.log.info("*"*20 + "Going to delete the vsa snapshot" + "*"*20)
        self._navigate_to_vmgroup()
        self.pg_cont_obj.access_page_action_from_dropdown('List snapshots')
        self.log.info(f"job_id {jobid}")
        self.__rtable.access_action_item(jobid, "Delete")
        self.rmodal_dialog.click_submit(wait=False)
        delete_jobid = self.admin_console.get_jobid_from_popup()
        job_details = self.get_job_status(delete_jobid)
        if not job_details:
            raise Exception("mount job Failed. check logs")
        return delete_jobid

    def delete_snap_array(self, jobid):
        """
        delete the vsa snapshot from array management
        Args:
            jobid   (string) :  Recent jobid of the vsa snap backup

        Returns:
            delete_jobid : jobid of the delete operation
        """

        self.log.info("Going to delete the vsa snapshot from Array Management level")
        self.navigator.navigate_to_arrays()
        self.controlhost_id = self.execute_query(self.controlhostid, {'a': jobid})
        self.array_name = self.execute_query(self.arrayname, {'b': controlhost_id[0][0]})
        self.__rtable.access_link(self.array_name[0][0])
        self.pg_cont_obj.click_on_button_by_text('List snapshots')
        self.log.info(f"job_id {jobid}")
        self.__rtable.search_for(jobid)
        self.__rtable.select_all_rows()
        self.admin_console.click_button_using_text("Delete")
        self.rmodal_dialog.click_button_on_dialog("Delete")
        delete_jobid = self.admin_console.get_jobid_from_popup()
        job_details = self.get_job_status(delete_jobid)
        if not job_details:
            raise Exception("delete job Failed. check logs")
        return delete_jobid


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

    def wait_for_job_completion(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    def backup_copy(self):
        """
        Run Backup copy offline from VM Group level
        Return:
             Backupcopy jobid
        Raises:
            Exception:
                        If backupcopy job does not complete successfully
        """
        try:
            VirtualServerUtils.decorative_log("Running backup copy for the subclient")
            self._navigate_to_vmgroup()
            self.pg_cont_obj.access_page_action_from_dropdown('Run backup copy')
            self.admin_console.click_button('Yes')
            try:
                bkpcpy_jobid = self.admin_console.get_jobid_from_popup()
                self.log.info("Successfully started Backup copy job : {0}".format(bkpcpy_jobid))
                job_status = self.wait_for_job_completion(bkpcpy_jobid)
            except Exception as exp:
                self.log.info(f"Backupcopy jobid from Toaster Message is incorrect or not found,"
                              f"Getting Backupcopy jobid from DB")
                time.sleep(5)
                bkpcpy_jobid = self.execute_query(self.offline_bkpcpy_jobid, {'a': self.subclient})
                if bkpcpy_jobid in [[[]], [['']], ['']]:
                    exp = "BackupCopy Job ID not found"
                    raise Exception(exp)
                bkpcpy_jobid = bkpcpy_jobid[0][0]
                self.log.info(f"Running Backupcopy is with Job ID:{bkpcpy_jobid} at Copy Level")
                job_status = self.wait_for_job_completion(bkpcpy_jobid)
            if not job_status:
                exp = "Backup copy Job ID {0} didn't succeed".format(bkpcpy_jobid)
                raise Exception(exp)
            self.log.info(f"Job id {bkpcpy_jobid} backup job at Copy Level Successful")
            return bkpcpy_jobid

        except Exception as exp:
            raise CVTestStepFailure(f'Backup copy operation failed : (exp)')

    def run_auxiliary_copy(self, plan_name=None, copy_name=None):
        """
        Run Auxiliary copy from plan level
            plan_name(str) : name of the plan
            copy_name(str) : name of the copy
        """
        try:
            self.log.info("*" * 20 + "Running Auxiliary Copy job" + "*" * 20)
            self.plan_obj.select_plan(plan_name)
            self.admin_console.access_tab(self.admin_console.props['label.nav.storagePolicy'])
            self.plandetails_obj.run_auxiliary_copy(copy_name)
            job = self.execute_query(self.aux_copy_job, {'a': plan_name})
            if job in [[[]], [['']], ['']]:
                time.sleep(500)
                self.log.info("Please wait for sometime to get auxcopy jobid post job completion")
                job = self.execute_query(self.auxcopy_post_job_run, {'a': plan_name})
                if job in [[[]], [['']], ['']]:
                    raise Exception("Aux Copy Job ID not found")
            job = int(job[0][0])
            self.log.info("Successfully started aux copy job : {0}".format(job))
            job_status = self.wait_for_job_completion(job)
            job_obj = Job(self.commcell, job)
            job_completion_status = job_obj.status
            if not job_status:
                exp = "Aux Copy Job ID {0} didn't succeed".format(job)
                raise Exception(exp)
            if job_completion_status != 'Completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors".format(job))
        except Exception as exp:
            raise CVTestStepFailure(f'Aux Copy operation failed : {exp}')

    def change_source_for_backupcopy(self, plan_name, copy_name):
        """
            Method to change source for backupcopy to a particular copy under a plan
                Args:
                    plan_name(str): Name of the Plan
                    copy_name (str): Name of the copy
        """
        self.log.info("*" * 20 + "Changing Source for Backup copy for a particular copy level" + "*" * 20)
        self.plan_obj.select_plan(plan_name)
        self.plandetails_obj.change_source_for_backupcopy(copy_name)

    def get_client_name_from_display_name(self, display_name):
        """
        Returns the Client name from Display Name of the Client

        Args:
            display_name      (string):     Display name of the client

        Returns:
            Client name

        Raises:
            Exception:
                If failed to retrieve the server details
        """

        _query = "select name from APP_Client where displayName=\'%s\'" % display_name
        self.csdb.execute(_query)
        _results = self.csdb.fetch_all_rows()
        if not _results or len(_results) > 1:
            raise Exception("An exception occurred in getting the server details for %s" % display_name)
        return _results[0][0]

    def get_job_status_from_jobspage(self, job_id):
        """
        Get the status of the given job ID

        Args:
            job_id   (str)   --  the job id whose status should be collected

        """
        try:
            self.log.info("Getting the status for the job %s", job_id)
            return self.job_obj.job_completion(job_id)
        except Exception as exp:
            self.log.exception("Exception occurred in getting the job status: %s", str(exp))
            raise exp

    def verify_synth_full_backup(self):
        """
        Verify whether synth full job is triggered after incremental backup

        Raises:
            Exception:
                if it fails to obtain the synth full job ID

        """
        try:
            self.log.info("Getting the synth full job ID")
            _query = "Select jobId from JMBkpJobInfo where bkpLevel=64 and applicationId=(" \
                     "select id from App_Application where subclientName='{0}' and clientId=(" \
                     "select id from App_Client where displayName='{1}'))".format(self.subclient,
                                                                                  self.hypervisor)

            self.csdb.execute(_query)
            job_id = str(self.csdb.fetch_one_row()[0])

            job_details = self.get_job_status(job_id)
            if job_details['Status'].lower() != 'completed':
                raise Exception("Exception occurred during synth full job."
                                "Please check the logs for more details.")
        except Exception as exp:
            self.log.exception("Exception occurred while getting the synth full job ID:"
                               " %s", str(exp))
            raise exp

    def fs_testdata_validation(self, dest_client, dest_path, testdata_path=None, file_restore=False):
        """
        Validates the testdata restored

        Args:
            dest_client      (object)       --  the machine class object of the client where
                                                the testdata was restored to

            dest_path        (str)   --  the path in the destination client where the
                                                testdata was restored to

            testdata_path    (basetring)    --  the path of the testdata in the source client.

            file_restore     (bool)         --  Whether this is a file restore from vm or not.

        Raises:
            Exception:
                if test data validation fails

        """
        if not testdata_path:
            testdata_path = self.testdata_path
        if not self.validation:
            self.log.info("Validation is being skipped.")
            return

        try:
            if self.indexing_v2 and self.backup_type.value == Backup.BackupType.SYNTH:
                self.log.info("Skipping test data validation since there is no backup")
                return

            self.log.info("Validating the testdata")
            if file_restore:
                matching = self.controller_machine.compare_files(dest_client, testdata_path, dest_path)
                if matching:
                    self.log.info("Validation completed successfully")
                else:
                    self.log.exception("Checksum match failed for source and destination. %s",
                                       matching)
                    raise Exception("File comparison failed for source {0} and destination "
                                    "{1}".format(testdata_path, dest_path))
                return
            else:
                difference = self.controller_machine.compare_folders(dest_client,
                                                                     testdata_path,
                                                                     dest_path)
            if difference:
                self.log.exception("Checksum mismatch failed for source and destination. %s",
                                   difference)
                raise Exception("Folder comparison failed for source {0} and destination "
                                "{1}".format(testdata_path, dest_path))

            self.log.info("Validation completed successfully")
        except Exception as exp:
            self.log.exception("Exception occurred during testdata validation. %s", str(exp))
            raise exp

    def file_level_restore(self, vm_level=False):
        """
        File level restore to guest agent in the commcell

        Args:
            vm_level    (bool):     Performs file level restore to guest agent from VM level

        Raises:
            Exception:
                if the file level restore fails

        """
        try:
            if not self.validation and self.validation_skip_all:
                VirtualServerUtils.decorative_log("Validation set to skip all: skipping File Level restore")
                return

            VirtualServerUtils.decorative_log("Performing file level restore to guest agent")

            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            for _vm in self._vms:
                if self.instance == hypervisor_type.AZURE_V2.value.lower() and self.hvobj.VMs[_vm].is_encrypted:
                    continue

                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    if self.hvobj.VMs[_vm].guest_os.lower() != 'windows':
                        _drive_for_validation = _drive.strip().split("/")
                        _drive_for_validation = (self._restore_proxy.join_path(*_drive_for_validation)).strip("\\")
                    else:
                        _drive_for_validation = _drive
                    restore_path = self._restore_proxy.join_path(
                        self.restore_path, "AdminConsole", _vm, _drive_for_validation)
                    restore_path = restore_path.replace('//', '/')
                    validate_path = self._restore_proxy.join_path(
                        restore_path, self.backup_type.name, "TestData", self.timestamp)

                    if self._restore_proxy.check_directory_exists(restore_path):
                        self._restore_proxy.remove_directory(restore_path)

                    if self.ci_enabled:
                        self.navigator.navigate_to_virtual_machines()
                        self.virtual_machines_obj.open_vm(_vm)
                        self.vm_details_obj.vm_search_content(self.backup_folder_name)
                        self.vsa_search_obj.search_for_content(
                            file_name=self.backup_folder_name, contains=_drive,
                            include_folders=True)
                        self.vsa_search_obj.select_data_type("Folder")
                        self.vsa_search_obj.validate_contains(self.backup_folder_name,
                                                              name=True)
                        self.vsa_search_obj.validate_contains(_drive, name=False,
                                                              folder=True)
                    else:
                        if not vm_level:
                            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                            self.vsa_sc_obj.restore()
                        else:
                            self._navigate_to_vm_restore(_vm)

                        self.select_restore_obj.latest_backups()
                        self.select_restore_obj.select_guest_files()
                        self.configure_restore_settings()

                        if "/" in _folder:
                            self.restore_vol_obj.select_volume(_vm, _folder)
                        else:
                            self.restore_vol_obj.select_volume(_vm, _drive)

                    self.restore_job_id = self.restore_files_obj.submit_guest_agent_restore(
                        [self.backup_type.name], restore_path, self.restore_proxy_display_name
                    )
                    job_details = self.get_job_status(self.restore_job_id)
                    if not job_details:
                        raise Exception("Restore job failed. Please check the logs")

                    self.guest_files_restore_validation(_vm, self._restore_proxy, validate_path)

        except Exception as exp:
            self.log.exception("Exception occurred during file level restore. %s", str(exp))
            raise exp

    def guest_files_restore(self, in_place=False, vm_level=False, end_user=False, restore_via_cv_tools=False,
                            push_expected=False):
        """
        File level restore to source VM

        Args:
            in_place                (bool):     if the files should be restored to the source path
            vm_level                (bool):     if the restore should be initiated from VM level
            end_user                (bool):     if the restore is initiated by end user
            restore_via_cv_tools    (bool):     if registry key bRestoreViaCVTools is enabled.
            push_expected           (bool):     if 'Commvault Tools are being pushed' is expected. Refer Project 1910

        Raises:
            Exception:
                if the file level restore fails

        """
        if not self.validation and self.validation_skip_all:
            VirtualServerUtils.decorative_log("Validation set to skip all: skipping Guest File restore")
            return

        VirtualServerUtils.decorative_log("Guest File Restore Started")
        self.log.info(
            "Parameters: in_place= {}, vm_level={}, end_user={}, restore_via_cv_tools = {} push_expected={}".format(
                in_place, vm_level, end_user, restore_via_cv_tools, push_expected))
        try:
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            for _vm in self._vms:
                self.agentless_vm = _vm

                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    if in_place:
                        restore_path = _folder
                        validate_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            restore_path, self.backup_type.name, "TestData", self.timestamp)
                    else:
                        restore_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            _folder, "AdminConsole", self.agentless_vm, _drive)
                        validate_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            restore_path, self.backup_type.name, "TestData", self.timestamp)

                    if self.hvobj.VMs[_vm].machine.check_directory_exists(restore_path):
                        if restore_path != _folder:
                            self.hvobj.VMs[_vm].machine.remove_directory(restore_path)

                    if restore_path != _folder:
                        self.hvobj.VMs[_vm].machine.create_directory(restore_path)

                    if self.ci_enabled:
                        self.navigator.navigate_to_virtual_machines()
                        self.virtual_machines_obj.open_vm(_vm)
                        self.vm_details_obj.vm_search_content(self.backup_folder_name)
                        self.vsa_search_obj.search_for_content(
                            file_name=self.backup_folder_name, contains=_drive,
                            include_folders=True)
                        self.vsa_search_obj.select_data_type("Folder")
                        self.vsa_search_obj.validate_contains(self.backup_folder_name,
                                                              name=True)
                        self.vsa_search_obj.validate_contains(_drive, name=False,
                                                              folder=True)
                    else:
                        if not vm_level:
                            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                            self.vsa_sc_obj.restore()
                        else:
                            self._navigate_to_vm_restore(_vm)

                        self.configure_restore_settings()
                        self.select_restore_obj.latest_backups()
                        self.select_restore_obj.select_guest_files()
                        if "/" in _folder:
                            self.restore_vol_obj.select_volume(_vm, _folder)
                        else:
                            self.restore_vol_obj.select_volume(_vm, _drive)

                    if not end_user:
                        self.restore_job_id = self.restore_files_obj.submit_this_vm_restore(
                            [self.backup_type.name], self.agentless_vm,
                            self.restore_proxy,
                            self.hvobj.VMs[_vm].machine.username,
                            self.hvobj.VMs[_vm].machine.password,
                            restore_path
                        )
                    else:
                        self.restore_job_id = self.enduser_restore_files_obj.enduser_files_restore(
                            [self.backup_type.name], self.agentless_vm,
                            self.hvobj.VMs[_vm].machine.username,
                            self.hvobj.VMs[_vm].machine.password,
                            restore_path
                        )

                    # Refer project 1910.
                    if restore_via_cv_tools:

                        self.log.info("Guest File Restore was run with the `restore_via_cv_tools` flag.")
                        # Check if a push install job was initiated.

                        if push_expected:
                            _push_job_id, _error_desc = get_push_job_id(self.restore_job, csdb=self.csdb)

                            if not _push_job_id:
                                raise Exception('Encountered the following error while checking for a push-install job.'
                                                ' Disable the push_expected flag to ignore this error. \n' + _error_desc)

                            push_job_details = self.get_job_status(_push_job_id)

                            if not push_job_details:
                                raise Exception(
                                    "Push Install Job {} failed. Check logs for more details.".format(_push_job_id))

                    job_details = self.get_job_status(self.restore_job_id)

                    if restore_via_cv_tools:
                        # Regardless, job should go through the agent, since push install job should only be skipped if agent is already present.
                        _restore_channel, _description = get_restore_channel(self.restore_job,
                                                                             destination_vm=self.agentless_vm,
                                                                             dest_vm_credentials=self.dest_vm_creds,
                                                                             commcell=self.commcell)
                        if not _restore_channel:
                            raise Exception(str(_description))
                        else:
                            self.log.info(_description)

                    if not job_details:
                        raise Exception("Agentless restore job failed. Please check the logs")

                    self.guest_files_restore_validation(_vm, self.hvobj.VMs[_vm].machine, validate_path)
        except Exception as exp:
            self.log.exception("Exception occurred during agentless restore. %s", str(exp))
            raise exp

    def __random_file_for_testdata(self, vm_name, drive, backup_folder=None, timestamp=None):
        """
        Return a random file name and its path in the testdata.

        Args:
            vm_name         (str) -- The VM name.

            drive           (str) -- The Drive name.

            backup_folder   (str) -- The backup folder name in source.

            timestamp       (str) -- The timestamp to look for in soruce path.

        Returns:
            file_name               (str) -- Name of the random file.

            testfile_path           (str) -- The testdata path.

            restore_path            (str) -- The restore path.

            restored_file_path      (str) -- The restored file path.

            download_file_path      (str) -- The downloaded file path.

            select_path             (str) -- The file path to be selected in restore page.
        """
        dir_path = 'dir' + str(random.choice(range(1, 3)))
        file_path = 'regular'
        file_name = 'regularfile' + str(random.choice(range(1, 6)))

        if not timestamp:
            timestamp = self.timestamp

        testdata_path = self.controller_machine.join_path(
            *self.testdata_path.split(self.controller_machine.os_sep)[:-1], timestamp)

        testfile_path = self.controller_machine.join_path(testdata_path, dir_path,
                                                          file_path, file_name)

        restore_path = self._restore_proxy.join_path(self.restore_path, "AdminConsole", vm_name, timestamp)

        restored_file_path = self._restore_proxy.join_path(restore_path, file_name)

        download_file_path = self.controller_machine.join_path(
            *testdata_path.split(self.controller_machine.os_sep)[:-4], 'temp', file_name)

        if not backup_folder:
            backup_folder = self.backup_type.name

        select_path = self._restore_proxy.join_path(
            backup_folder, "TestData", timestamp,
            dir_path, file_path, file_name)

        return file_name, testfile_path, restore_path, restored_file_path, download_file_path, select_path

    def ctree_file_search_restore(self, download=False):
        """
        File level restore and download from VM page.

        Args:
            download                      (boolean)       --  Whether to check file downloads or not.

        Raises:
            Exception:
                if the file restore or download fails.

        """
        if not self.ci_enabled:
            raise Exception("Content Indexing is not available. File Search is not possible")

        VirtualServerUtils.decorative_log("Performing file restore from VM")

        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator

        for _vm in self._vms:
            try:
                if self.hvobj.VMs[_vm].guest_os.lower() == 'linux':
                    _drive = next(iter(self.hvobj.VMs[_vm].drive_list.items()))[1]
                else:
                    _drive = next(iter(self.hvobj.VMs[_vm].drive_list.items()))[0]
                file_name, testdata_path, restore_path, restored_file_path, \
                    download_file_path, select_path = self.__random_file_for_testdata(_vm, _drive)
                if self.hvobj.VMs[_vm].guest_os.lower() == 'linux':
                    if _drive != '/':
                        select_path = _drive + '\\' + select_path
                        select_path = select_path.replace("/", "\\")
                else:
                    select_path = _drive + ':\\' + select_path

                if self._restore_proxy.check_directory_exists(restore_path):
                    self._restore_proxy.remove_directory(restore_path)

                self.navigator.navigate_to_virtual_machines()
                self.virtual_machines_obj.open_vm(_vm)
                self.vm_details_obj.vm_search_content(file_name)
                self.admin_console.wait_for_completion()

                restore_job = self.restore_files_obj.submit_file_restore_from_vm(_drive,
                                                                                 [select_path], restore_path, self.restore_proxy)

                job_details = self.get_job_status(restore_job)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                self.fs_testdata_validation(self._restore_proxy, restored_file_path,
                                            testdata_path=testdata_path, file_restore=True)
                self._restore_proxy.remove_directory(restore_path)

                if download:
                    # Delete if a file with the same name already exists.
                    if self.controller_machine.check_file_exists(download_file_path):
                        self.controller_machine.delete_file(download_file_path)

                    self.restore_files_obj.submit_file_restore_from_vm(_drive, [select_path], restore_path,
                                                                       self.restore_proxy, download=download)

                    wait_time = 1000  # in seconds.
                    for time_taken in range(0, wait_time, 10):
                        if self.controller_machine.check_file_exists(download_file_path):
                            self.log.info("File downloaded successfully at the location '%s'", download_file_path)
                            break
                    else:
                        raise Exception('File not downloaded within the time limit given')

                    self.fs_testdata_validation(self.controller_machine, download_file_path,
                                                testdata_path=testdata_path, file_restore=True)

            except Exception as exp:
                self.log.exception("Exception occurred during file restore or download for %s.\n%s", _vm, str(exp))
                raise exp

    def ci_validate_deleted_items(self):
        """Validates serach and restore of deleted items."""
        if self.previous_backup_timestamp is None:
            return

        VirtualServerUtils.decorative_log("Validating search and restore of deleted items")

        backup_folder = "FULL"
        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator

        for _vm in self._vms:
            try:
                _drive, _folder = next(iter(self.hvobj.VMs[_vm].drive_list.items()))

                testdata_path = self.controller_machine.join_path(
                    *self.testdata_path.split(self.controller_machine.os_sep)[:-1], self.previous_backup_timestamp)
                restore_path = self._restore_proxy.join_path(self.restore_path, "AdminConsole", _vm,
                                                             self.previous_backup_timestamp)
                if self._restore_proxy.check_directory_exists(restore_path):
                    self._restore_proxy.remove_directory(restore_path)
                self._navigate_to_vm_restore(_vm)
                self.select_restore_obj.latest_backups()
                self.select_restore_obj.select_guest_files()
                self.restore_files_obj.enable_deleted_items()
                self.restore_vol_obj.select_volume(_vm, _folder)

                restore_job = self.restore_files_obj.submit_file_restore_from_vm(_drive, [backup_folder], restore_path,
                                                                                 self.restore_proxy, deleted_items=True)

                job_details = self.get_job_status(restore_job)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")
                validation_path = self._restore_proxy. \
                    join_path(restore_path, backup_folder, "TestData", self.previous_backup_timestamp)

                self.fs_testdata_validation(self._restore_proxy, validation_path,
                                            testdata_path=testdata_path)

                self.log.info("Search and restore of deleted items validated successfully.")
                self._restore_proxy.remove_directory(restore_path)
            except Exception as exp:
                self.log.exception("Exception occurred during file restore or download for %s.\n%s", _vm, str(exp))
                raise exp

    def ci_validate_file_versions(self):
        """Validates search and restore of different file versions."""
        if self.previous_backup_timestamp is None:
            return

        VirtualServerUtils.decorative_log("Validating search and restore of file versions")

        backup_folder = "FULL"
        self.version_file_path = VirtualServerUtils.get_version_file_path(self.hvobj.machine)
        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator

        for _vm in self._vms:
            try:
                _drive, _folder = next(iter(self.hvobj.VMs[_vm].drive_list.items()))

                testdata_path = self.controller_machine.join_path(self.version_file_path, self.timestamp,
                                                                  "files_with_custom_name", self.version_file_name)
                testdata_path += "1.txt"
                restore_path = self._restore_proxy.join_path(self.restore_path, "AdminConsole", _vm,
                                                             "FileVersion1")
                if self._restore_proxy.check_directory_exists(restore_path):
                    self._restore_proxy.remove_directory(restore_path)
                restored_file_path = self._restore_proxy.join_path(restore_path, self.version_file_name) + ".txt"
                file_name = self.version_file_name + ".txt"

                self._navigate_to_vm_restore(_vm)
                self.select_restore_obj.latest_backups()
                self.select_restore_obj.select_guest_files()
                self.restore_files_obj.enable_file_versions()
                self.restore_vol_obj.select_volume(_vm, _folder)
                self.restore_vol_obj.select_volume(_vm, self.file_versions_folder)

                restore_job = self.restore_files_obj.submit_file_restore_from_vm(_drive, [file_name],
                                                                                 restore_path,
                                                                                 self.restore_proxy,
                                                                                 versions=True)

                job_details = self.get_job_status(restore_job)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                self.fs_testdata_validation(self._co_ordinator, restored_file_path,
                                            testdata_path=testdata_path, file_restore=True)
                self._restore_proxy.remove_directory(restore_path)
                self.log.info("Latest version of the file validated successfully.")

                testdata_path = self.controller_machine.join_path(self.version_file_path,
                                                                  self.previous_backup_timestamp,
                                                                  "files_with_custom_name",
                                                                  self.version_file_name + "1")
                testdata_path += ".txt"
                restore_path = self._restore_proxy.join_path(self.restore_path, "AdminConsole",
                                                             _vm,
                                                             "FileVersion2")
                restored_file_path = self._restore_proxy.join_path(restore_path, file_name)

                restore_job = self.restore_files_obj.submit_file_restore_from_vm(_drive, [file_name],
                                                                                 restore_path,
                                                                                 self.restore_proxy,
                                                                                 versions=True,
                                                                                 show_versions=True)

                job_details = self.get_job_status(restore_job)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                self.fs_testdata_validation(self._co_ordinator, restored_file_path,
                                            testdata_path=testdata_path, file_restore=True)

                self.log.info("Previous version of the file validated successfully.")

                self.log.info("Search and restore of file versions validated successfully.")
                self._restore_proxy.remove_directory(restore_path)
            except Exception as exp:
                self.log.exception("Exception occurred during file restore or download for %s.\n%s", _vm, str(exp))
                raise exp

    def solr_file_search_restore(self):
        """
        Performs file search from VM Group page.

        Raises:
            Exceptions:
                If the file search fails.
        """
        if not self.ci_enabled:
            raise Exception("Content Indexing is not available. File Search is not possible")

        VirtualServerUtils.decorative_log("Performing file restore from VM Group")

        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator

        for _vm in self._vms:
            try:
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                drive_list = self.hvobj.VMs[_vm].drive_list
                if self.hvobj.VMs[_vm].guest_os.lower() == 'linux':
                    _drive = drive_list[random.choice(list(drive_list.keys()))]
                else:
                    _drive = random.choice(list(drive_list.keys()))

                file_name, testdata_path, restore_path, restored_file_path, \
                    download_file_path, select_path = self.__random_file_for_testdata(_vm, _drive)
                if self.hvobj.VMs[_vm].guest_os.lower() == 'linux':
                    if _drive != '/':
                        select_path = _drive + '\\' + select_path
                        select_path = select_path.replace("/", "\\")
                else:
                    select_path = _drive + ':\\' + select_path
                if self._restore_proxy.check_directory_exists(restore_path):
                    self._restore_proxy.remove_directory(restore_path)
                restore_job = self.vm_group_file_restore_obj.restore_file(_vm, file_name, select_path,
                                                                          self.restore_proxy, restore_path)
                job_details = self.get_job_status(restore_job)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                self.fs_testdata_validation(self._restore_proxy, restored_file_path,
                                            testdata_path=testdata_path, file_restore=True)
            except Exception as exp:
                self.log.exception("Exception occurred during file restore or download for %s.\n%s", _vm, str(exp))
                raise exp

    def agentless_restore(self, vm_level=False, vm_path=None):
        """
        File level restore to VM in server which does not have Content Store installed

        Args:
            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if the restore to a VM without content store fails

        """
        try:
            if not self.validation and self.validation_skip_all:
                VirtualServerUtils.decorative_log("Validation set to skip all: agentless File Level restore")
                return

            VirtualServerUtils.decorative_log("Restoring data to an agentless VM")

            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            for _vm in self._vms:
                if not self._agentless_dict:
                    self._agentless_dict = {_vm: self._agentless_vm}
                elif not self._agentless_dict.get(_vm, None):
                    self._agentless_dict[_vm] = self._agentless_vm

                self._destination_vm_object = self.restore_destination_client.VMs[
                    self._agentless_dict[_vm]]
                destination_drive = list(self._destination_vm_object.drive_list.keys())[0]
                destination_folder = self._destination_vm_object.drive_list[destination_drive]

                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    if self.hvobj.VMs[_vm].guest_os.lower() != 'windows':
                        _drive_for_validation = _drive.strip().split("/")
                        _drive_for_validation = (self._destination_vm_object.machine.join_path
                                                 (*_drive_for_validation)).strip("\\")
                    else:
                        _drive_for_validation = _drive
                    restore_path = self._destination_vm_object.machine.join_path(
                        destination_folder, "AdminConsole", _vm, _drive_for_validation)

                    validate_path = self._destination_vm_object.machine.join_path(
                        restore_path, self.backup_type.name, "TestData", self.timestamp)

                    if self._destination_vm_object.machine.check_directory_exists(
                            restore_path):
                        self._destination_vm_object.machine.remove_directory(restore_path)

                    self._destination_vm_object.machine.create_directory(restore_path)

                    if self.ci_enabled:
                        self.navigator.navigate_to_virtual_machines()
                        self.virtual_machines_obj.open_vm(_vm)
                        self.vm_details_obj.vm_search_content(self.backup_folder_name)
                        self.vsa_search_obj.search_for_content(
                            file_name=self.backup_folder_name, contains=_drive,
                            include_folders=True)
                        self.vsa_search_obj.select_data_type("Folder")
                        self.vsa_search_obj.validate_contains(self.backup_folder_name,
                                                              name=True)
                        self.vsa_search_obj.validate_contains(_drive, name=False,
                                                              folder=True)
                    else:
                        if not vm_level:
                            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                            self.vsa_sc_obj.restore()
                        else:
                            self._navigate_to_vm_restore(_vm)

                        self.configure_restore_settings()
                        self.select_restore_obj.latest_backups()
                        self.select_restore_obj.select_guest_files()

                        if "/" in _folder:
                            self.restore_vol_obj.select_volume(_vm, _folder)
                        else:
                            self.restore_vol_obj.select_volume(_vm, _drive)

                    if self._destination_vm_object.instance_type == "amazon":
                        self.restore_job_id = self.restore_files_obj.submit_other_vm_restore(
                            [self.backup_type.name], self.restore_proxy,
                            self.restore_client, self._agentless_dict[_vm],
                            self._destination_vm_object.machine.username,
                            self._destination_vm_object.machine.password,
                            restore_path,
                            self._destination_vm_object.availability_zone,
                            self._destination_vm_object.aws_region
                        )
                    else:
                        self.restore_job_id = self.restore_files_obj.submit_other_vm_restore(
                            [self.backup_type.name], self.restore_proxy,
                            self.restore_client, self._agentless_dict[_vm],
                            self._destination_vm_object.machine.username,
                            self._destination_vm_object.machine.password,
                            restore_path, self.vm_path
                        )

                    job_details = self.get_job_status(self.restore_job_id)

                    self.guest_files_restore_validation(_vm, self._destination_vm_object.machine, validate_path)
        except Exception as exp:
            self.log.exception("Exception occurred during agentless restore. %s", str(exp))
            raise exp

    def disk_validation(self, vm_obj, disk_restore_destination):
        """
        Performs Disk Validation by mounting the restored disk on the Host

        Args:

            vm_obj                      (object)       --  instance of the VM class

            disk_restore_destination    (str)   --   restore path of all the disk

        Raises:
            Exception:
                if validation fails

        """
        try:
            self.log.info("Performing disk validation")
            _drive_letter = None

            if self.restore_client != self.hypervisor:
                self.restore_destination_client = self._create_hypervisor_object(
                    self.restore_client
                )
            else:
                self.restore_destination_client = self.hvobj

            _list_of_disks = self.restore_destination_client.get_disk_in_the_path(
                disk_restore_destination)

            _vm_disk_list = vm_obj.disk_list
            if not _vm_disk_list:
                raise Exception(
                    "Cannot validate the Disk as we cannot find the disk attached to the VM")

            if not ((_list_of_disks is None) or (_list_of_disks == [])):
                _final_mount_disk_list = []
                for each_disk in _vm_disk_list:
                    each_disk_name = os.path.basename(each_disk).split(".")[0]
                    for disk_path in _list_of_disks:
                        if each_disk_name in disk_path:
                            _final_mount_disk_list.append(disk_path)
            else:
                raise Exception(
                    "The Disk cannot be validated as we cannot find disk with Hypervisor"
                    " extension, could be converted disk")

            if not _final_mount_disk_list:
                _final_mount_disk_list = _list_of_disks

            for _file in _final_mount_disk_list:
                self.log.info("Validation Started For Disk :[%s]", _file)
                _file = disk_restore_destination + "\\" + _file
                _drive_letter = self.restore_destination_client.mount_disk(vm_obj, _file)
                if _drive_letter != -1:
                    for each_drive in _drive_letter:
                        dest_folder_path = VirtualServerConstants.get_folder_to_be_compared(
                            self.backup_type.name, each_drive)
                        self.log.info("Folder comparison started...")
                        time.sleep(5)
                        self.fs_testdata_validation(
                            self.restore_destination_client.machine, dest_folder_path)
                else:
                    self.log.error("ERROR - Error mounting VMDK %s", _file)
                    raise Exception("Exception at Mounting Disk ")

                self.restore_destination_client.un_mount_disk(vm_obj, _file)

        except Exception as exp:
            if _drive_letter and _drive_letter != -1:
                self.restore_destination_client.un_mount_disk(vm_obj, _file)
            self.log.exception("Exception occurred during disk validation. Please check the logs.")
            raise exp

    def disk_level_restore(self, vm_level=False):
        """
        Disk level restore to another VM in the server

        Args:
            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if the disk level restore or validation fails

        """
        try:
            self.log.info("*" * 10 + "Performing disk level restore" + "*" * 10)
            for _vm in self._vms:
                if not vm_level:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
                else:
                    self._navigate_to_vm_restore(_vm)
                self.select_restore_obj.select_disk_restore()
        except Exception as exp:
            self.log.exception("Exception occurred during Attach disk restore. %s", str(exp))
            raise exp

    def virtual_machine_files_restore(self, vm_level=False):
        """
        Disks restores to a client in the commcell

        Args:
            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if the virtual machine files restore or validation fails

        """
        try:
            VirtualServerUtils.decorative_log("Performing virtual machine files restore")
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            if self.restore_client is None:
                self.restore_client = self.hypervisor

            for _vm in self._vms:
                restore_path = self._restore_proxy.join_path(
                    self.restore_path, "AdminConsole", _vm)

                # Clearing the restore path
                if self._restore_proxy.check_directory_exists(restore_path):
                    self._restore_proxy.remove_directory(restore_path)

                disks = self._get_disk_list(self.hvobj.VMs[_vm].disk_list)
                if not vm_level:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
                else:
                    self._navigate_to_vm_restore(_vm)
                self.select_restore_obj.select_vm_files()

                self.restore_job_id = self.vm_files_restore_obj.vm_files_restore(
                    _vm,
                    disks,
                    self.restore_proxy,
                    restore_path
                )

                job_details = self.get_job_status(self.restore_job_id)

                if self.validation:
                    self.disk_validation(self.hvobj.VMs[_vm], restore_path)
                else:
                    self.log.info("Validation is being skippped.")

        except Exception as exp:
            self.log.exception("Exception occurred during Virtual Machine Files restore."
                               " %s", str(exp))
            raise exp

    @abstractmethod
    def full_vm_restore(self):
        """
        Performs Full VM restore
        """
        self.log.info("Performing full VM restore")

    def attach_disk_restore(self):
        """
        Performs attach_disk_restore
        """
        self.log.info("Performing attach_disk_restore")

    def vm_restore_validation(self, vm_name, restore_vm, restore_options=None):
        """
        Validates the full VM restore job

        Args:
            vm_name          (str)   --  the name of the source VM that was backed up

            restore_vm       (str)   --  the name of the restored VM

            restore_options  (dict)         --  the restore options in the form of dict

        Raises:
            Exception:
                if full VM / instance restore validation fails

        """
        if not self.validation:
            self.log.info("Validation is being skipped.")
            return

        try:
            VirtualServerUtils.decorative_log("Validating full VM restore")
            OptionsHelperMapper.RestoreOptionsMapping(self). \
                validate_restore(vm_name, restore_vm, restore_options)


        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore validation. %s", str(exp))
            raise exp

    def vm_conversion_restore_validation(self, vm_name, restore_vm, restore_options=None):
        """
                Validates the full VM conversion restore job.

                Args:
                    vm_name          (str)   --  the name of the source VM that was backed up

                    restore_vm       (str)   --  the name of the restored VM

                    restore_options  (dict)         --  the restore options in the form of dict
                Raises:
                    Exception:
                        if full VM / instance restore validation fails

                """
        if not self.validation:
            self.log.info("Validation is being skipped.")
            return

        try:
            VirtualServerUtils.decorative_log("Validating full VM restore")
            OptionsHelperMapper.RestoreOptionsMapping(self). \
                validate_conversion_restore(vm_name, restore_vm, restore_options)

        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore validation. %s", str(exp))
            raise exp

    def cleanup_testdata(self):
        """
        Cleans up testdata that is copied from each vm in the subclient

        Raises:
            Exception:
                if clean up of testdata from the backup VMs fails

        """
        try:
            self.log.info("Testdata cleanup from subclient started")
            if not self.backup_folder_name:
                self.backup_folder_name = self.backup_type.name
            if self.azure_cross_region_restore:
                self.log.info("No need for cleanup testdata in Azure cross region restore")
            else:

                if self._vms:
                    for _vm in self._vms:
                        self.log.info("VM selected is %s", _vm)
                        if not self.hvobj.VMs.get(_vm):
                            continue
                        if self.cleanup_versions_file:
                            _drive = next(iter(self.hvobj.VMs[_vm].drive_list.values()))
                            _file_versions_folder = self.hvobj.VMs[_vm].machine.join_path(_drive,
                                                                                          self.file_versions_folder)
                            self.log.info("Cleaning up %s", _file_versions_folder)
                            if self.hvobj.VMs[_vm].machine.check_directory_exists(_file_versions_folder):
                                self.hvobj.VMs[_vm].machine.remove_directory(_file_versions_folder)

                        if self.cleanup_testdata_before_backup:
                            for name, _drive in self.hvobj.VMs[_vm].drive_list.items():
                                for folder_name in ["FULL", "INCR", "SYNTH"]:
                                    _testdata_path = self.hvobj.VMs[_vm].machine.join_path(_drive,
                                                                                           folder_name)
                                    self.log.info("Cleaning up %s", _testdata_path)
                                    if self.hvobj.VMs[_vm].machine.check_directory_exists(
                                            _testdata_path):
                                        self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
                        else:
                            for _drive in self.hvobj.VMs[_vm].drive_list.values():
                                _testdata_path = self.hvobj.VMs[_vm].machine.join_path(_drive, self.backup_folder_name)
                                self.log.info("Cleaning up %s", _testdata_path)
                                if self.hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                                    self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)

            self.log.info("Cleaning testdata in the controller")

            if self.test_file_versions:
                if self.cleanup_versions_file:
                    self.controller_machine.remove_directory(self.version_file_path)
                    os_sep = self.controller_machine.os_sep
                    _previous_testdata_path = self.controller_machine.join_path(*self.testdata_path.split(os_sep)[:-1],
                                                                                self.previous_backup_timestamp)
                    self.controller_machine.remove_directory(_previous_testdata_path)
                else:
                    self.log.info("Skipping testdata cleanup in the controller")
                    return

            if not self.testdata_paths:
                self.testdata_paths = [self.testdata_path]
            for _path in self.testdata_paths:
                self.controller_machine.remove_directory(_path)
        except Exception as exp:
            self.log.exception(
                "Exception while doing cleaning up test data directory: %s", str(exp))
            raise exp

    def search_and_download(self):
        """
        Searches for and downloads content

        Returns:

        """
        if not self.ci_enabled:
            raise Exception("Content Indexing is not enabled. Search will be live browse")

        for _vm in self._vms:
            for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                self.navigator.navigate_to_virtual_machines()
                self.virtual_machines_obj.open_vm(_vm)
                self.vm_details_obj.vm_search_content(self.backup_folder_name)
                self.vsa_search_obj.search_for_content(
                    file_name=self.backup_folder_name, contains=_drive,
                    include_folders=True)
                self.vsa_search_obj.select_data_type("Folder")
                self.vsa_search_obj.validate_contains(self.backup_folder_name,
                                                      name=True)
                self.vsa_search_obj.validate_contains(_drive, name=False,
                                                      folder=True)
                self.restore_files_obj.download_content([self.backup_type.name])

                WebDriverWait(self.driver, 600).until(EC.invisibility_of_element_located(
                    (By.ID, "download-tracker")
                ))

                if not self.controller_machine.check_file_exists(
                        self.download_directory) and not os.listdir(self.download_directory):
                    raise Exception("Download could not be completed.")

                if self.validation:
                    files = self.controller_machine.get_files_in_path(self.download_directory)
                    for file in files:
                        with zipfile.ZipFile(file, 'r') as zip_file:
                            zip_file.extractall(self.download_directory)

                        validate_path = self.controller_machine.join_path(self.download_directory,
                                                                          self.backup_type.name,
                                                                          "TestData",
                                                                          self.timestamp)
                        self.fs_testdata_validation(self.controller_machine, validate_path)
                else:
                    self.log.info("Validation is being skipped.")
                break

    def ci_download_file(self):
        """
        Searches for and downloads a file

        Returns:

        """

        files_path = VirtualServerUtils.get_content_indexing_path(self.controller_machine)
        file_path_beforebackup = ''.join(self.controller_machine.get_files_in_path(files_path)[0])
        file = os.path.split(file_path_beforebackup)[1]
        download_folder = os.path.expanduser("~" + "/Downloads/")
        file_path_afterdownload = self.controller_machine.join_path(download_folder, file)

        if not self.ci_enabled:
            raise Exception("Content Indexing is not enabled. Search will be live browse")

        for _vm in self._vms:
            self.navigator.navigate_to_virtual_machines()
            self.virtual_machines_obj.open_vm(_vm)
            self.vm_details_obj.vm_search_content(file)
            self.vsa_search_obj.select_data_type(file)
            self.restore_files_obj.download_content([file], select_one=True)

            WebDriverWait(self.driver, 600).until(EC.invisibility_of_element_located(
                (By.ID, "download-tracker")))

            if not self.controller_machine.check_file_exists(file_path_afterdownload):
                raise Exception("Download could not be completed.")

            if self.validation:
                self.log.info("Validating file checksum")
                try:
                    if file in os.listdir(download_folder):
                        file_path_afterdownload = self.controller_machine.join_path(download_folder, file)

                    self.controller_machine.compare_files(self.controller_machine, file_path_beforebackup,
                                                          file_path_afterdownload)
                    self.log.info("File checksum validation completed successfully")
                    self.controller_machine.delete_file(file_path_afterdownload)
                except Exception as exp:
                    self.log.error("File checksum failed %s", str(exp))
            else:
                self.log.info("Validation is being skipped.")

    def get_job_status(self, job_id, expected_state="completed"):
        """
        Returns the job status via SDK. To be used as a workaround when facing issues with
        job progress in Command Center.

        Args:
            job_id             (str) : Job ID whose status has to be checked.

            expected_state      (str/list) : Expected Job state
                                        Default : "completed"
        Returns:
            Job Status
        """
        job_obj = JobManager(job_id, self.commcell)
        job_status = job_obj.wait_for_state(expected_state, time_limit=20000)
        if isinstance(expected_state, str):
            expected_state = [expected_state]
        if "completed w/ one or more errors" in expected_state:
            error_validation = job_obj.validate_job_errors(expected_errors = self.expected_job_errors)
            if not error_validation:
                return False
        return job_status

    def post_restore_clean_up(self, source_vm=False, status=False):
        """
        Cleans up VM and its resources after out-of-place restore.

        Args:
            source_vm (bool): Whether the source VM has to be powered off or not.
            status (bool): Whether the test case has passed or failed.

        Raises:
            Exception: If unable to clean up VM and its resources.
        """
        try:
            for each_vm in self._vms:
                if self.hvobj.VMs.get(each_vm):
                    if source_vm:
                        self.log.info("Powering off VM {0}".format(each_vm))
                        self.hvobj.VMs[each_vm].power_off()

                if self.restore_destination_client:
                    restore_vm_name = str(self.vm_restore_prefix) + str(each_vm)

                    if hasattr(self.restore_destination_client, 'check_vms_exist'):
                        exists = self.restore_destination_client.check_vms_exist([restore_vm_name])
                    else:
                        exists = True

                    if exists:
                        if restore_vm_name not in self.restore_destination_client.VMs:
                            self.restore_destination_client.VMs[restore_vm_name] = restore_vm_name

                        if status:
                            self.log.info("Cleaning up VM {0}".format(restore_vm_name))
                            self.restore_destination_client.VMs[restore_vm_name].clean_up()
                        else:
                            self.log.info("Powering off VM {0}".format(restore_vm_name))
                            self.restore_destination_client.VMs[restore_vm_name].power_off()
                    else:
                        self.log.info("Performed an In-place restore. VM {0} does not exist".format(restore_vm_name))

        except Exception as err:
            self.log.exception("Exception while cleaning up VM resources: " + str(err))
            raise err

    def post_conversion_clean_up(self, source_vm=False, status=False):

        """
            Cleans up VM and its resources after out of place restore

            Args:
                    source_vm                       (bool): whether  source vm has to be powered
                                                            off or not
                    status                          (bool) : whether the tc has passed ot failed
            Raises:
             Exception:
                If unable to clean up VM and its resources
        """
        try:
            for each_vm in self._vms:
                restored_vm = self.vm_restore_prefix + each_vm
                if self.hvobj.VMs.get(each_vm, None):
                    if source_vm:
                        self.log.info("Powering off VM {0}".format(each_vm))
                        self.hvobj.VMs[each_vm].power_off()
                    if status:
                        self.log.info("Cleaning up VM {0}".format(restored_vm))
                        self.restore_destination_client.VMs[restored_vm].clean_up()
                    else:
                        self.log.info("Powering off VM {0}".format(restored_vm))
                        self.restore_destination_client.VMs[restored_vm].power_off()
                else:
                    self.hvobj.VMs = restored_vm
                    if status:
                        self.log.info("Cleaning up VM {0}".format(restored_vm))
                        self.restore_destination_client.VMs[restored_vm].clean_up()
                    else:
                        self.log.info("Powering off VM {0}".format(restored_vm))
                        self.restore_destination_client.VMs[restored_vm].power_off()
        except Exception as err:
            self.log.exception(
                "Exception while doing cleaning up VM resources: " + str(err))
            raise err

    def populate_proxy_obj(self, proxy, proxy_ip):
        if self.instance.lower() == hypervisor_type.MS_VIRTUAL_SERVER.value.lower() and proxy not in self.proxy_obj:
            self.proxy_obj[proxy] = self.hvobj.get_cluster_storage(proxy_ip)
        else:
            self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)

    def get_proxies(self, job_type='restore'):
        '''
                Creating a dictionary of proxy name as key and proxy location details as value
                Args:
                job_type        (str): Type of job - backup/restore

        '''
        self.log.info("Creating a dictionary of proxy name as key and proxy location details as value")
        sub_proxies = self.subclient_obj._get_subclient_proxies()
        instance_proxies = self.instance_obj._get_instance_proxies()
        auto_commcell_obj = AutoVSACommcell(self.commcell, self.csdb)
        self.proxy_obj = {}

        if job_type.lower() == 'backup':
            if not sub_proxies:
                for proxy in instance_proxies:
                    proxy_ip = auto_commcell_obj.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
            else:
                for proxy in sub_proxies:
                    proxy_ip = auto_commcell_obj.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
        else:
            is_recovery_target = self.commcell.recovery_targets.has_recovery_target(self.restore_client)

            # Restore to same hypervisor
            if (not is_recovery_target and self.restore_client == self.hypervisor) or \
                    (is_recovery_target and self.recovery_target.destination_hypervisor == self.hypervisor):
                for proxy in instance_proxies:
                    proxy_ip = auto_commcell_obj.get_hostname_for_client(proxy)
                    self.populate_proxy_obj(proxy, proxy_ip)
                for proxy in sub_proxies:
                    proxy_ip = auto_commcell_obj.get_hostname_for_client(proxy)
                    self.populate_proxy_obj(proxy, proxy_ip)
            else:
                # Restore to different hypervisor
                if not is_recovery_target:
                    if self.commcell.clients.has_client(self.restore_client):
                        different_vcenter_client = self.commcell.clients.get(self.restore_client)
                    else:
                        self.log.error("Destination hypervisor client with the given name : {} doesn't exist"
                                       .format(self.restore_client))
                        raise Exception('Validation failed')
                else:
                    # Restore to hypervisor associated with the Recovery target
                    different_vcenter_client = self.commcell.clients.get(self.recovery_target.destination_hypervisor)

                destination_agent = different_vcenter_client.agents.get('Virtual Server')
                destination_instance_obj = destination_agent.instances.get(self._restore_instance_type)
                destination_instance_proxies = destination_instance_obj._get_instance_proxies()

                for proxy in destination_instance_proxies:
                    proxy_ip = auto_commcell_obj.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.restore_destination_client.get_proxy_location(proxy_ip)

    def full_vm_conversion_restore(self, restore_obj):
        try:
            VirtualServerUtils.decorative_log("Performing Full VM Conversion restore from {0} to {1}"
                                              .format(self.instance, restore_obj.instance))
            self.conversion_restore = True
            self.restore_obj = restore_obj
            self.restore_obj.get_all_vms()

            self.restore_obj.hvobj, self._restore_instance_type = self.restore_obj. \
                _create_hypervisor_object(self.restore_client)
            self.restore_destination_client = self.restore_obj.hvobj

            if self._restore_proxy is None:
                self.restore_proxy = self.restore_obj._co_ordinator

            self.restore_obj.backup_folder_name = self.backup_folder_name
            self.restore_obj.timestamp = self.timestamp
            self.restore_obj.testdata_path = self.testdata_path
            self.restore_obj.testdata_paths = self.testdata_paths
            self.restore_obj.source_hvobj = self.hvobj
            self.restore_obj.conversion_restore = True

            self.restore_obj._vms = self._vms
            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.restore()
            if self.run_aux:
                self.select_restore_obj.select_source_and_media_agent(source=self.restore_obj.aux_copy)
            self.select_restore_obj.select_full_vm_restore()

            self.restore_obj.full_vm_restore()
            for _vm in self._vms:
                # Check which hypervisors need this VM Name Sanitization
                restore_vm = self.restore_obj.vm_restore_prefix + _vm.replace(' ', '').replace('_', '')
                self.vm_conversion_restore_validation(_vm, restore_vm, self.restore_obj._full_vm_restore_options.get(_vm, {}))
        except Exception as exp:
            self.log.exception("Exception occurred during full VM conversion restore. %s", str(exp))
            raise exp

    def create_access_node(self, prov_hypervisor, proxy_name, proxy_os, vm_size, entry_point='hypervisor',
                           hypervisor_display_name='Microsoft Azure', infrastructure_type='Virtualization',
                           region=None):
        """
        submits job for creating new infrastructure machine to be used as access node
        Args:
            prov_hypervisor         (str): Provisioning hypervisor to be used for new access node creation
            proxy_name              (str): Name of the new access node
            proxy_os                (str): OS of the new access node
            entry_point             (str): Entry point for creating access node
            region                  (str): Region of the new access node
            hypervisor_display_name (str): Hypervisor being used
            infrastructure_type     (str): Infrastructure Type to be selected

        Raises:
            Exception:
                if it fails to submit create access node request from adminconsole

        """
        try:
            _panel_dropdown_obj = DropDown(self.admin_console)

            if entry_point.lower() == 'hypervisor':
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_create_access_node_dialog()
                self.admin_console.wait_for_completion()

            elif entry_point.lower() == 'server group':
                _servergroups = ServerGroups(self.admin_console)

                self.navigator.navigate_to_server_groups()
                _servergroups.open_create_access_node_dialog(self.server_group)
                self.admin_console.wait_for_completion()
                _panel_dropdown_obj.select_drop_down_values(index=1, values=[infrastructure_type])

            elif entry_point.lower() == 'resource pool':
                _table_obj = Table(self.admin_console)
                self.navigator.navigate_to_resource_pool()
                _table_obj.access_link(self.resource_pool)
                self.admin_console.click_button_using_text('Create access node')
                self.admin_console.wait_for_completion()

            create_access_node_dialog = RModalDialog(self.admin_console, "Create access node")
            try:
                create_access_node_dialog.select_dropdown_values(drop_down_id="workflowType",
                                                                 values=[infrastructure_type])
            except ElementClickInterceptedException:
                self.admin_console.log.info("Virtualization selected by default, moving ahead")
                self.admin_console.click_on_base_body()
                pass

            if proxy_os.lower() == 'unix':
                create_access_node_dialog.select_radio_by_id(radio_id='linux')
            else:
                create_access_node_dialog.select_radio_by_id(radio_id=proxy_os.lower())

            self.admin_console.log.info(f"OS selected for on-demand Access node: {proxy_os}")

            create_access_node_dialog.fill_text_in_field(element_id="vmName", text=proxy_name)
            self.admin_console.log.info(f"entered name on-demand Access node: {proxy_name}")

            create_access_node_dialog.select_dropdown_values(drop_down_id="hypervisorsDropdown",
                                                             values=[prov_hypervisor])
            self.admin_console.log.info("Provisioning Hypervisor set for on-demand Access node")

            if hypervisor_display_name == HypervisorDisplayName.AMAZON_AWS.value:
                current_zone = self.admin_console.driver.find_element(By.ID, 'availabilityZone').get_attribute(
                    'value')
                create_access_node_dialog.click_button_on_dialog(aria_label='Browse')
                self.admin_console.wait_for_completion(wait_time=500)
                availability_zone_modal = RModalDialog(admin_console=self.admin_console,
                                                       title='Select availability zone')
                zone_tree_view = TreeView(self.admin_console, xpath=availability_zone_modal.base_xpath)
                zone_tree_view.select_items(items=[self.zone])
                if current_zone == self.zone:
                    availability_zone_modal.click_cancel()
                else:
                    availability_zone_modal.click_submit()

                self.admin_console.log.info("Selected AWS Zone for on-demand Access node")

            else:
                create_access_node_dialog.select_dropdown_values(drop_down_id="azureRegionDropdown",
                                                                 values=[self.region])
                self.admin_console.log.info("Selected Azure region for on-demand Access node")

            create_access_node_dialog.select_dropdown_values(drop_down_id="instanceType",
                                                             values=[vm_size])
            self.admin_console.log.info("Selected VM size/Instance Type for Azure/AWS on-demand Access node")

            self.admin_console.log.info("Submitting job for creating access node")
            create_access_node_dialog.click_submit(wait=False)

            vmm_jobid = self.admin_console.get_jobid_from_popup(hyperlink=True, wait_time=0)

            self.admin_console.log.info(
                "VM Management Job ID for creating on-demand Access Node: {} is {}".format(proxy_name, vmm_jobid))
            job_details = self.get_job_status(vmm_jobid)
            if job_details:
                self.hvobj = self._create_hypervisor_object()[0]
                self.one_click_node_obj = self.hvobj.to_vm_object(proxy_name)
                self.commcell.refresh()

                if hypervisor_display_name == HypervisorDisplayName.AMAZON_AWS.value:
                    self.commcell.refresh()
                    client = self.commcell.clients.get(proxy_name)
                    proxy_ip = client.client_hostname
                    self.one_click_node_obj.machine = machine.Machine(proxy_ip, self.commcell)

                self._navigate_to_vmgroup()
                self.vsa_sc_obj.update_access_node(proxy_name=proxy_name)

        except Exception as exp:
            raise CVWebAutomationException("Exception while submitting create access node request: %s", str(exp))

    def cleanup_access_node(self, proxy_name):
        """
        Clean up access node from commcell and its VM resource

        Args:
            proxy_name              (str): Name of the new access node

        Raises:
            Exception:
                if it fails to clean up access node

        """
        try:
            self.log.info("Retiring new Access node from Commcell")
            self.commcell.refresh()

            self.one_click_node_obj.power_on()
            client_obj = self.commcell.clients.get(proxy_name)
            retire_job = client_obj.retire()
            if retire_job is not None:
                self.log.info("Uninstall Job: {} started for retiring Access node client: {}".format(
                    retire_job.job_id if retire_job.job_id else "N/A", proxy_name
                ))

                if retire_job.wait_for_completion():
                    self.log.info("New Access Node:- {} retired from Commcell".format(proxy_name))
                    self.commcell.refresh()
            else:
                self.log.info("No retire job found for retiring Access node client: {}".format(proxy_name))

            self.log.info("New Access Node:- {} retired from Commcell".format(proxy_name))
            self.commcell.refresh()
            if self.commcell.clients.has_client(proxy_name):
                self.commcell.clients.delete(proxy_name)
                self.commcell.refresh()

            self.log.info("Access node: {} retired from commcell, deleting VM from Azure/AWS Portal".format(proxy_name))
            self.one_click_node_obj.clean_up()

            return True
        except Exception as exp:
            self.log.exception("Exception while submitting create access node request: %s", str(exp))
            raise exp

    @property
    def validate_browse_ma_and_cp(self):
        """
        Returns the value for browse ma and copy validation
        Returns:
            _validate_browse_ma_and_cp              (bool) : True if browse ma and copy validation is enabled

        """

        return self._validate_browse_ma_and_cp

    @validate_browse_ma_and_cp.setter
    def validate_browse_ma_and_cp(self, value):
        """
        Sets the value for Browse MA and Copy validation
        Args:
            value               (bool) : Enable or disable browse ma / copy validation

        """

        self._validate_browse_ma_and_cp = value

    def validate_guest_file_restore_proxy(self, job_id):
        """
        Checks if the proxy used for guest file restore is the first proxy listed at the hypervisor level.

        Args:
        job_id (str): The ID of the job to validate.

        Returns:
        bool: True if the proxy used for the guest file restore matches the first proxy listed at the hypervisor level,
              False otherwise
        """
        self.navigator.navigate_to_virtualization()
        self.navigator.navigate_to_hypervisors()
        self.__rtable.access_link(self.hypervisor)
        self.hyp_access_nodes = self.hypervisor_details_obj.proxy_info()

        self.job_obj.access_job_by_id(job_id)
        self.association_details = self.job_details_obj.get_association_details()

        if self.association_details.get('Destination') == self.hyp_access_nodes[0]:
            return True
        return False

    def guest_files_restore_validation(self, source_vm, destination_vm, destination_path):
        """
            Validate the Guest files Restore

            Args:
                source_vm                    (str)     --   The source vm used in restore

                destination_vm              (object)   --  the machine class object of the client where
                                            the testdata was restored to

                destination_path            (str)   --  the path in the destination client where the
                                                testdata was restored to

            Raises:
                Exception:
                    If Validation fails

        """

        try:
            self.fs_testdata_validation(destination_vm, destination_path)
            if self.validate_browse_ma_and_cp:
                self.auto_vsa_subclient.browse_ma_and_cp_validation(source_vm,
                                                                    RestoreType.GUEST_FILES.value,
                                                                    proxy=self.restore_proxy,
                                                                    job_id=self.restore_job_id,
                                                                    browse_ma_id=str(self.browse_ma_id),
                                                                    browse_ma=self.browse_ma,
                                                                    copy_precedence=str(self.copy_precedence))

                self.log.info('Browse MA and Copy Validation Passed for MA [{}] and Copy [{}]'.format(self.browse_ma,
                                                                                                      self.copy_name))
            if self.restore_proxy == "Automatic":
                if self.validate_guest_file_restore_proxy(self.restore_job_id):
                    self.log.info('Correct proxy selected for the guest file restore under the Automatic access node '
                                  'option.')
                else:
                    self.log.exception('Incorrect proxy was selected for the guest file restore under the Automatic '
                                       'access node option.')
        except Exception as exp:
            self.log.exception("Exception in guest files restore validation. %s", str(exp))
            raise exp

    def configure_restore_settings(self):
        """
            Configures the restore options : browse ma and copy
            Raises:
                Exception:
                    If failed to configure restore settings

        """

        try:
            if self.run_aux:
                self.copy_name = self.aux_copy
            elif self.snap_restore:
                for _copyname, _values in self.storage_policy.copies.items():
                    if _values['isSnapCopy'] and _values['copyPrecedence'] == 1:
                        self.copy_name = _copyname
            elif self.secondary_snap_restore:
                self.copy_name = self.execute_query(self.secondary_snap_copy_name, {'a': self.storage_policy.storage_policy_name})[0][0]
            elif self.snap_restore is not None:
                self.copy_name = "primary"
            self.select_restore_obj.select_source_and_media_agent(source=self._copy_name, media_agent=self._browse_ma)
        except Exception as exp:
            self.log.exception("Failed to configure restore settings. %s", str(exp))
            raise exp

    def setup_vm_settings(self):
        """
            Configures backup settings for each VM

            raises:
                Exception:
                    If there is a failure in setting up the VM backup settings

        """
        try:
            if self.vm_setting_options:
                for _vm in self._vms:
                    self._navigate_to_vm(_vm)
                    self.vm_details_obj.set_vm_settings(self.vm_setting_options)
        except Exception as exp:
            raise Exception("Failure in setting up the VM backup settings".format(exp))

    def setup_vm_disk_filters(self):
        """
            Configures disk filters for each VM

            raises:
                Exception:
                    If there is a failure in setting up the VM disk filters
        """
        try:
            if self.vm_disk_filter_options:
                for _vm in self._vms:
                    self._navigate_to_vm(_vm)
                    self.vm_details_obj.set_vm_disk_filters(self.vm_disk_filter_options)
        except Exception as exp:
            raise Exception("Failure in setting up the VM disk filters".format(exp))

    def get_target_summary(self, target):
        """
            Gets the target details dict from the Recovery Target details page

            Args:
                target  (str): Name of the target

            Returns:
                target_summary  (dict) : Target details
        """
        self.navigator.navigate_to_replication_targets()
        self.recovery_targets_obj.access_target(target)
        return self.target_details_obj.get_target_summary()

    def verify_entity_details(self, validate_input, entity_details):
        """
        Compares the given two dicts and checks if they are equal

        Args:
            validate_input           (dict):  dict of details to be validated
            entity_details          (dict):  dict of entity(hypervisor/vmgroup) details

        Returns True, if validation is successful
        """
        for input_key in validate_input.keys():
            if input_key == "admin_hypervisor" and validate_input.get('vcloud_organization'):
                continue
            if input_key not in entity_details.keys():
                self.log.info(f"Detail of {input_key} is not present.")
                return False
            else:
                validate_value = validate_input[input_key]
                entity_value = entity_details[input_key]
                if type(validate_value) == type(entity_value):
                    if isinstance(validate_value, list) and set(validate_value) == set(entity_value):
                        self.log.info(f"Detail of {input_key} matches value: {validate_value}.")
                    elif validate_value == entity_value:
                        self.log.info(f"Detail of {input_key} matches value: {validate_value}.")
                else:
                    self.log.error(f"Detail {input_key} don't match expected: {value}, found: {entity_value}")
                    return False
        return True

    @PageService()
    def validate_hypervisor(self, hypervisor_name, validate_input):
        """
        Validates the hypervisor with the given set of inputs

        validate_input      (dict)  -Dict of details to validate
                                    {"vendor": "Amazon Web Services",
                                                "server_name": "TC_test",
                                                "proxy_list": ['Proxy_1'],
                                                "auth_type": 'Auth_type',
                                                "credential": 'Credential',
                                                "tag_name": 'Tag_Name',
                                                "frel": 'file enabler',
                                                "regions": 'Regions',
                                                "vm_group_name": "TC_test_vmgroup",
                                                "plan": 'Plan'}

        Returns True, if the validation is successful
        """
        self.hypervisor_ac_obj.select_hypervisor(hypervisor_name)
        hypervisor_details = self.hypervisor_details_obj.fetch_hypervisor_details(validate_input["vendor"])
        # vm_content validate
        if "vm_group_name" in validate_input.keys():
            self.hypervisor_details_obj.open_subclient(validate_input["vm_group_name"])
            vm_group_content = self.vsa_sc_obj.get_vm_group_content()
            hypervisor_details["vm_content"] = list(vm_group_content)
            if 'vm_content' in validate_input:
                if 'Rule' in validate_input['vm_content'] and \
                        'Instance name or pattern' in validate_input['vm_content']['Rule'] and \
                        'Equals' in validate_input['vm_content']['Rule']['Instance name or pattern']:
                    desired_value = validate_input['vm_content']['Rule']['Instance name or pattern']['Equals'][0]
                    validate_input["vm_content"] = [desired_value] if desired_value is not None else []
        if self.hypervisor_ac_obj.ssl_check:
            for hyp, ssl in self.hypervisor_ac_obj.ssl_check.items():
                self.hypervisor_details_obj.validate_ssl_check(hyp, ssl)
        if not self.verify_entity_details(validate_input, hypervisor_details):
            raise Exception("Hypervisor validation failed")

    @PageService()
    def validate_vmgroup(self, vmgroup_name, validate_input, content_rule=False):
        """
        Validates the vmgroup with the given set of inputs

        vmgroup_name        (str)   -Name of the vm group

        validate_input      (dict)  -Dict of details to validate
                                    {"vm_group_name": "TC_test_vmgroup",
                                            "vm_content": "content",
                                            "plan": 'Plan',
                                            "tag_name": 'Tag_name,
                                            "number_of_readers":No Of Readers,
                                            "Proxy_list": Proxy list}
        content_rule        (boolean) -Whether validation has to be done on content or on rule
                                        True - content is a rule
                                        False - If Vms are manually added

        Returns True, if the validation is successful
        """
        self.vm_groups_obj.select_vm_group(vmgroup_name)
        vmgroup_details = self.vsa_sc_obj.fetch_vmgroup_details(content_rule=content_rule)
        if not self.verify_entity_details(validate_input, vmgroup_details):
            raise Exception("VM group validation failed")

    def instance_configuration_file_restore(self, destination, destination_machine, restore_path, validation=True):
        """
        Restores the instance configuration files , used for amazon network and instance config files

        destinations              (str)   -Names of the proxy to be entered in restore options

        destination_machines     (machine)  - machine object of the machine to which files are being restored to perform validation

        restore_path             (str) -  path to which files are to be restored

        validation                (bool) - validation should be performed or not

        raise exception if restore job failed or if files not found in the restore path after restore
        """
        try:
            VirtualServerUtils.decorative_log("Performing instance configuration files restore")
            if destination_machine is None:
                destination_machine = self._co_ordinator
            for _vm in self._vms:
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                self.vsa_sc_obj.restore()
                self.select_restore_obj.select_vm_files()
                vm_guid = self.hvobj.VMs[_vm].guid
                files = [vm_guid + "_NetworkConfig.json", vm_guid + "_InstanceConfig.xml"]
                self.restore_job_id = self.instance_config_file_restore_obj.vm_instance_configuration_files_restore(_vm,
                                                                                                                    destination, restore_path)
                job_details = self.get_job_status(self.restore_job_id)
                if validation:
                    for file in files:
                        file_path = restore_path + "\\" + file if 'windows' in destination_machine.os_info.lower() \
                            else restore_path + "/" + file
                        if not destination_machine.check_file_exists(file_path):
                            raise Exception("File restore validation failed as file not found in given path")
            VirtualServerUtils.decorative_log("Instance configuration files successfully restored")
        except Exception:
            raise Exception("Failed to restore instance configuration files")


class VMwareAdminConsole(AdminConsoleVirtualServer):
    """
    VMware class to perform VMware related adminconsole tasks
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize any VMware related variables

        Args:
            instance        (object)    --  the instance class object

            driver          (object)    --  the browser driver object

            commcell        (object)    --  the commcell object

            csdb            (object)    --  the commserve DB object

        """

        super(VMwareAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self.dest_client_vm = None
        self._disk_provisioning = "Thin"
        self._transport_mode = "Auto"
        self._live_recovery = False
        self._live_recovery_options = dict.fromkeys(['redirect_datastore', 'delay_migration'])
        self.nfs_datastores = {}
        self.redirect_datastores = {}
        self._different_vcenter = False
        self._different_vcenter_info = {}
        self._full_vm_restore_options = {}
        self._custom_attributes_to_add = {}
        self._custom_attributes_to_remove = {}
        self._tags_to_add = {}
        self._tags_to_remove = {}
        self.datastore = None
        self.select_live_recovery_restore_type = False
        self.is_destination_host_cluster = False
        self.is_destination_ds_cluster = False
        self._disk_ds_options = None
        self._destination_vm = None
        self.source_hvobj = None

    @property
    def live_recovery(self):
        """
        Returns the live recovery enable/disable option

        Returns:
            _live_recovery     (bool)  --  True / False to enable or disable live recovery

        """
        return self._live_recovery

    @live_recovery.setter
    def live_recovery(self, value):
        """
        Sets the live recovery option during restore

        Args:
            value   (bool)  --  True / False to enable or disable live recovery during restore

        """
        self._live_recovery = value

    @property
    def live_recovery_options(self):
        """
        Returns the dict containing the live recovery options

        Returns:
            _live_recovery_options     (dict)  --  dict containing the live recovery options

        """
        return self._live_recovery_options

    @property
    def redirect_datastore(self):
        """
        Returns the redirect datatore option

        Returns:
            _live_recovery_options['redirect_datastore']   (str)   --  the name of the
                                                                        datastore where writes
                                                                        will be redirected

        """
        return self._live_recovery_options['redirect_datastore']

    @redirect_datastore.setter
    def redirect_datastore(self, value):
        """
        Sets the redirect datastore option for live recovery

        Args:
            value   (str)    --  the name of the datastore to redirect writes during live
                                            recovery restore

        """
        self._live_recovery_options['redirect_datastore'] = value

    @property
    def delay_migration(self):
        """
        Returns the delay migration value

        Returns:
            _live_recovery_options['delay_migration']  (int)   --  the amount of time in hrs
                                                                    the migration has to be
                                                                    delayed

        """
        return self._live_recovery_options['delay_migration']

    @delay_migration.setter
    def delay_migration(self, value):
        """
        Sets the delay migration hours

        Args:
            value   (str / int)    --    the no of hours the migration has to be delayed
                                                during live recovery

        """
        self._live_recovery_options['delay_migration'] = str(value)

    @property
    def transport_mode(self):
        """
        Returns the transport mode to be used for restore

        Returns:
            _transport_mode    (str)   --  the transport mode to be used for restore
                    default:    Auto

        """
        return self._transport_mode

    @transport_mode.setter
    def transport_mode(self, value):
        """
        Sets the transport mode to be used for restore

        Args:
            value   (str)    --  the transport mode to be used

        """
        self._transport_mode = value

    @property
    def disk_provisioning(self):
        """
        Returns the disk provisioning option to be used during restore

        Returns:
            _disk_provisioning     (str)   --  the type of disk provisioning to be used
                                                      during restore
                        default :   Thin

        """
        return self._disk_provisioning

    @disk_provisioning.setter
    def disk_provisioning(self, value):
        """
        Sets the disk provisioning option

        Args:
            value   (str)    --  the disk provisioning to be used for the disks in the
                                        restore VM

        """
        self._disk_provisioning = value

    @property
    def different_vcenter(self):
        """
        Returns the option to restore to a different vcenter or not

        Returns:
            full_vm_restore_options['different_vCenter']   (bool)  --  restore to a different
                                                                        new vcenter

        """
        return self._different_vcenter

    @different_vcenter.setter
    def different_vcenter(self, value):
        """
        Sets the different vcenter flag

        Args:
            value   (str)    --  if a different vcenter has to be used during restore

        """
        self._different_vcenter = value

    @property
    def different_vcenter_info(self):
        """
        Returns the information about the new vcenter client to create during restore

        Returns:
            _different_vcenter_info (dict)   --  different vcenter username and password

        """
        return self._different_vcenter_info

    @property
    def different_vcenter_name(self):
        """
        Returns the name of the new vcenter to restore to

        Returns:
            _different_vcenter_info['vcenter_hostname']   (str)  --  name of the new vcenter

        """
        return self._different_vcenter_info['vcenter_hostname']

    @different_vcenter_name.setter
    def different_vcenter_name(self, value):
        """
        Sets the name of the different vcenter

        Args:
            value   (str)    --  the name of the different vcenter to be used during restore

        """
        self._different_vcenter_info['vcenter_hostname'] = value

    @property
    def different_vcenter_username(self):
        """
        Returns the username of the new vcenter to restore to

        Returns:
            _different_vcenter_info['vcenter_username'] (str)  --  username of the
                                                                            new vcenter

        """
        return self._different_vcenter_info['vcenter_username']

    @different_vcenter_username.setter
    def different_vcenter_username(self, value):
        """
        Sets the different vcenter user name

        Args:
            value   (str)    --  the username for the different vcenter

        """
        self._different_vcenter_info['vcenter_username'] = value

    @property
    def different_vcenter_password(self):
        """
        Returns the password of the new vcenter to restore to

        Returns:
            _different_vcenter_info['vcenter_password']   (str)  --  password of the
                                                                            new vcenter

        """
        return self._different_vcenter_info['vcenter_password']

    @different_vcenter_password.setter
    def different_vcenter_password(self, value):
        """
        Sets the password for the different vcenter

        Args:
            value   (str)    --  the password of the different vcenter

        """
        self._different_vcenter_info['vcenter_password'] = value

    @property
    def vm_storage_policy(self):
        """
        Returns the VM Storage Policy

        Returns:
            _vm_storage_policy   (str)  --  VM Storage Policy

        """
        return self._vm_storage_policy

    @vm_storage_policy.setter
    def vm_storage_policy(self, value):
        """
        Sets the VM Storage Policy

        Args:
            value   (str)  --  VM Storage Policy

        """
        self._vm_storage_policy = value

    @property
    def custom_attributes_to_add(self):
        """
        Returns the custom attributes to be added to the restored VMs

        Returns:
            _custom_attributes_to_add    (dict)  --  the custom attributes to be added to the restored VMs
        """
        return self._custom_attributes_to_add

    @custom_attributes_to_add.setter
    def custom_attributes_to_add(self, value):
        """
        Sets the custom attributes to be added to the restored VMs

        Args:
            value   (List of Ordered Dicts/Dict)  --  the custom attributes to be added to the restored VMs
            If the input is read from .json it is a list of Ordered Dicts, else it is a dict
        """
        if isinstance(value, list):
            for ca_val in value:
                if not isinstance(ca_val, OrderedDict):
                    raise Exception(f"Invalid input '{ca_val}' specified for custom_attributes_to_add. Input should be a list of Ordered Dicts")
                for ca, val in ca_val.items():
                    self._custom_attributes_to_add[ca] = val
        if isinstance(value, dict):
            self._custom_attributes_to_add = value

    @property
    def custom_attributes_to_remove(self):
        """
        Returns the custom attributes to be removed from the restored VMs

        Returns:
            _custom_attributes_to_remove    (dict)  --  the custom attributes to be removed from the restored VMs
        """
        return self._custom_attributes_to_remove

    @custom_attributes_to_remove.setter
    def custom_attributes_to_remove(self, value):
        """
        Sets the custom attributes to be removed from the restored VMs

        Args:
            value (List of Ordered Dicts/Dict)  --  the custom attributes to be removed from the restored VMs
            If the input is read from .json it is a list of Ordered Dicts, else it is a dict
        """
        if isinstance(value, list):
            for ca_val in value:
                if not isinstance(ca_val, OrderedDict):
                    raise Exception(f"Invalid input '{ca_val}' specified for custom_attributes_to_remove. Input should be a list of Ordered Dicts")
                for ca, val in ca_val.items():
                    self._custom_attributes_to_remove[ca] = val
        if isinstance(value, dict):
            self._custom_attributes_to_remove = value

    @property
    def tags_to_add(self):
        """
        Returns the tags to be added to the restored VMs

        Returns:
            _tags_to_add    (dict)  --  the tags to be added to the restored VMs
        """
        return self._tags_to_add

    @tags_to_add.setter
    def tags_to_add(self, value):
        """
        Sets the tags to be added to the restored VMs

        Args:
            value   (List of Ordered Dicts of Lists/Dict)  --  the tags to be added to the restored VMs
            If the input is read from .json it is a list of Ordered Dicts of Lists, else it is a dict
            Ordered Dict Form [{Tag_Category: [Tags]}], Dict Format {Tag_Category: [Tags]}
        """
        if isinstance(value, list):
            for tag_category_tags in value:
                if not isinstance(tag_category_tags, OrderedDict):
                    raise Exception(f"Invalid input '{tag_category_tags}' specified for tags_to_add. Input should be a list of Ordered Dicts")
                for tag_category, tags in tag_category_tags.items():
                    if not isinstance(tags, list):
                        raise Exception(f"Invalid input '{tags}' specified for tags_to_add. Input should be a list")
                    self._tags_to_add[tag_category] = tags
        if isinstance(value, dict):
            self._tags_to_add = value
        self.restore_validation_options['tags_to_add'] = self._tags_to_add

    @property
    def tags_to_remove(self):
        """
        Returns the tags to be removed from the restored VMs

        Returns:
            _tags_to_remove    (dict)  --  the tags to be removed from the restored VMs
        """
        return self._tags_to_remove

    @tags_to_remove.setter
    def tags_to_remove(self, value):
        """
        Sets the tags to be removed from the restored VMs

        Args:
            value   (List of Ordered Dicts of Lists/Dict)  --  the tags to be removed from the restored VMs
            If the input is read from .json it is a list of Ordered Dicts of Lists, else it is a dict
            Ordered Dict Form [{Tag_Category: [Tags]}], Dict Format {Tag_Category: [Tags]}
        """
        if isinstance(value, list):
            for tag_category_tags in value:
                if not isinstance(tag_category_tags, OrderedDict):
                    raise Exception(f"Invalid input '{tag_category_tags}' specified for tags_to_remove. Input should be a list of Ordered Dicts")
                for tag_category, tags in tag_category_tags.items():
                    if not isinstance(tags, list):
                        raise Exception(f"Invalid input '{tags}' specified for tags_to_remove. Input should be a list")
                    self._tags_to_remove[tag_category] = tags
        if isinstance(value, dict):
            self._tags_to_remove = value
        self.restore_validation_options['tags_to_remove'] = self._tags_to_remove

    @property
    def disk_ds_options(self):
        """
        Returns the disk options for restore
        """
        return self._disk_ds_options

    @disk_ds_options.setter
    def disk_ds_options(self, options):
        """
        Sets the disk-datastore mapping options for restore of VMs
        Args:
            options (dict)  --  VM disk and datastore mapping
                                Ex :
                                    {
                                    'VM1' : {
                                            'VM1.vmdk' : 'DS1'
                                            'VM1_1.vmdk' : 'DS2'
                                    },
                                    'VM2' : {
                                            'VM2.vmdk' : 'DS1'
                                            'VM2_1.vmdk' : 'DS2'
                                    }
                                    }
        """
        if options:
            for input_vm in options:
                for _vm in self._vms:
                    if input_vm.lower() == _vm.lower():
                        options[_vm] = options.pop(input_vm)
                    else:
                        raise Exception('VM [{}] not found in the VM group'.format(input_vm))
            for _vm in options:
                _vm_option = {disk.lower(): ds.lower() for disk, ds in options[_vm].items()}
                options[_vm] = _vm_option
            self._disk_ds_options = options

    @property
    def destination_vm(self):

        return self._destination_vm

    @destination_vm.setter
    def destination_vm(self, vm):

        self._destination_vm = vm

    def _get_nfs_datastore_name(self, restore_vm):
        """
        Gets the NFS datastore name in the given ESX

        Args:
            restore_vm   (str)   --  the name of the restored VM

        Raises:
            Exception:
                if it fails to get the name of the NFS datastore that are mounted

        """
        try:
            self.log.info("Getting the name of the 3DFS datastore where VM is mounted")
            datastore_list = self.restore_destination_client.VMs[restore_vm].datastores
            for datastore in datastore_list:
                datastore = datastore.strip()
                if '_GX_' in datastore:
                    self.nfs_datastores[restore_vm] = datastore
                    break
            if self.nfs_datastores.get(restore_vm):
                self.log.info(
                    "The 3DFS datastore for the VM {0} is {1}".format(restore_vm, self.nfs_datastores[restore_vm]))
            else:
                self.log.warning("No 3dfs datastore mounted for the VM {0}".format(restore_vm))
        except Exception as exp:
            raise Exception("Failure in retrieving the 3dfs datastore".format(str(exp)))

    def _get_redirect_writes_datastore_name(self, restore_vm):
        """
        Gets the Redirect writes datastore name for the given VM

        Args:
            restore_vm   (str)   --  the name of the restored VM

        Returns:
            datastore   (str)   --  Redirect writes datastore name

        Raises:
            Exception:
                if it fails to get the name of the Redirect writes datastore that is mounted

        """
        try:
            self.log.info("Getting the name of the Redirect writes datastore where VM is mounted")
            datastore_list = self.restore_destination_client.VMs[restore_vm].datastores
            for datastore in datastore_list:
                datastore = datastore.strip()
                if self.nfs_datastores.get(restore_vm) and '_GX_' not in datastore:
                    self.redirect_datastores[restore_vm] = datastore
                    break
            if self.redirect_datastores.get(restore_vm):
                self.log.info(
                    "The redirect writes datastore for the VM {0} is {1}".format(restore_vm, self.redirect_datastores[restore_vm]))
            else:
                self.log.warning("No redirect writes datastore mounted for the VM {0}".format(restore_vm))
        except Exception as exp:
            raise Exception("Failure in retrieving the redirect writes datastore".format(str(exp)))

    def live_recovery_validation(self, restore_vm):
        """
        Validates the live VM recovery job

        Args:
            restore_vm  (str)   :   the name of the restored VM

        Raises:
             Exception:
                if validation failed

        """
        if not self.validation:
            self.log.info("Validation is being skipped.")
            return

        try:
            self.log.info("Starting live VM recovery validation")

            if self.nfs_datastores.get(restore_vm):
                self.auto_vsa_client.vmware_live_mount_validation([str(self.restore_job_id)],
                                                                  self.restore_destination_client,
                                                                  self.nfs_datastores[restore_vm],
                                                                  media_agent=self.auto_vsa_subclient._browse_ma)
            elif not (self.snap_restore or self.secondary_snap_restore):
                raise Exception("No 3dfs datastore was mounted for the VM {0}".format(restore_vm))

            if self.redirect_datastore:
                if self.redirect_datastores.get(restore_vm):
                    redirect_ds_exists = self.restore_destination_client.check_ds_exist(
                        [self.redirect_datastores[restore_vm]]
                    )
                else:
                    raise Exception("No redirect writes datastore was mounted for the VM {0}".format(restore_vm))
                if redirect_ds_exists:
                    raise Exception(
                        "Redirect writes datastore is not unmounted yet. Cleanup failed for Datastore : [{}] of VM : "
                        "[{}]".format(self.redirect_datastores[restore_vm], restore_vm))

            if self.destination_datastore and self.restore_destination_client.VMs[restore_vm].datastore != \
                    self.destination_datastore and not self.full_vm_in_place:
                if self.is_destination_ds_cluster:
                    _ds = self.hvobj.get_datastore_from_cluster(self.destination_datastore)
                    if _ds != self.restore_destination_client.VMs[restore_vm].datastore:
                        raise Exception("Something went wrong during migration. Wrong destination"
                                        " datastore [{0}] was selected from the cluster. Datastore with most free space"
                                        ":[{1}]".format(self.restore_destination_client.VMs[restore_vm].datastore, _ds))
                else:
                    raise Exception("Something went wrong during migration. The destination datastore [{0}] is wrong. "
                                    "Input destination datastore is [{1}]".format(
                        self.restore_destination_client.VMs[restore_vm].datastore,
                        self.destination_datastore))
            self.log.info("Live VM recovery validation completed successfully")
        except Exception as exp:
            raise Exception("Live VM recovery validation failed. {0}".format(str(exp)))

    def _set_vm_restore_options(self):
        """
        Sets the VM restore options for each VM to be restored
        Raises:
            Exception:
                if there is any exception in setting the restore options

        """
        if self.conversion_restore:
            for each_vm in self._vms:
                self.restore_destination_client.VMs[each_vm] = self.__deepcopy__(
                    self.source_hvobj.VMs[each_vm])
        else:
            for each_vm in self._vms:
                self.restore_destination_client.VMs[each_vm] = self.__deepcopy__(
                    self.hvobj.VMs[each_vm])

        if not self.recovery_target:
            _host = ""
            _datastore = ""
            for _vm in self._vms:
                _vm = self.vm_restore_prefix + _vm
                _restored_vm = self.restore_destination_client.find_vm(_vm)
                if _restored_vm[0]:
                    if _restored_vm[0] == 'Multiple':
                        self.log.exception("%s is present in multiple ESX", _vm)
                        raise Exception
                    if _host:
                        if _host != _restored_vm[1]:
                            _org = self.restore_destination_client.find_esx_parent(_host)
                            _new = self.restore_destination_client.find_esx_parent(_restored_vm[1])
                            if "domain" in _org[0] and _new[0]:
                                if _org[1] == _new[1]:
                                    continue
                            self.log.exception("Restore vms are existing in multiple ESX. Please clean and rerun")
                            raise Exception
                    _host = _restored_vm[1]
                    _datastore = _restored_vm[2]

            if _host:
                if self.testcase_obj.tcinputs.get('Network') and (
                        self.testcase_obj.tcinputs.get('Host') == _host or self.destination_host == _host):
                    _network = self.testcase_obj.tcinputs["Network"]
                else:
                    _network = self.restore_destination_client._get_host_network(_host)
            else:
                if (("Datastore" not in self.testcase_obj.tcinputs.keys()) or
                    ("Host" not in self.testcase_obj.tcinputs.keys())) and \
                        not (self.destination_host and self.destination_datastore):
                    resources = self.restore_destination_client.compute_free_resources(self._vms)
                    _host = resources[1][0]
                    _datastore = resources[0]
                    _network = resources[4]
                else:
                    _datastore = self.destination_datastore or self.testcase_obj.tcinputs.get("Datastore")
                    _host = self.destination_host or self.testcase_obj.tcinputs.get("Host")
                    if 'Network' in self.testcase_obj.tcinputs.keys():
                        _network = self.testcase_obj.tcinputs["Network"]
                    else:
                        _network = self.restore_destination_client._get_host_network(_host)

            for _vm in self._vms:
                if self.is_metallic:
                    source_vm = self.hvobj.VMs[_vm]
                    _host = source_vm.esx_host
                    _datastore = source_vm.datastore
                self._full_vm_restore_options[_vm]['network'] = {}
                self._full_vm_restore_options[_vm]['network']['destination'] = _network
                self._full_vm_restore_options[_vm]['host'] = _host
                self._full_vm_restore_options[_vm]['datastore'] = _datastore
                self._full_vm_restore_options[_vm]['disk_ds_options'] = self.disk_ds_options
                if self.resource_pool:
                    self._full_vm_restore_options[_vm]['respool'] = self.resource_pool
                else:
                    self._full_vm_restore_options[_vm]['respool'] = "/"
                self._full_vm_restore_options[_vm]['prefix'] = self.vm_restore_prefix
                self._full_vm_restore_options[_vm]['disk_option'] = self.disk_provisioning
                if self._vm_storage_policy:
                    self._full_vm_restore_options[_vm]['vm_storage_policy'] = self._vm_storage_policy
                else:
                    self._full_vm_restore_options[_vm]['vm_storage_policy'] = "Datastore Default"
                if self.custom_attributes_to_add:
                    self._full_vm_restore_options[_vm]['custom_attributes_to_add'] = self.custom_attributes_to_add
                if self.custom_attributes_to_remove:
                    self._full_vm_restore_options[_vm]['custom_attributes_to_remove'] = self.custom_attributes_to_remove
                if self.tags_to_add:
                    self._full_vm_restore_options[_vm]['tags_to_add'] = self.tags_to_add
                if self.tags_to_remove:
                    self._full_vm_restore_options[_vm]['tags_to_remove'] = self.tags_to_remove
        else:
            for _vm in self._vms:
                if self.custom_attributes_to_add:
                    self._full_vm_restore_options[_vm]['custom_attributes_to_add'] = self.custom_attributes_to_add
                if self.custom_attributes_to_remove:
                    self._full_vm_restore_options[_vm]['custom_attributes_to_remove'] = self.custom_attributes_to_remove
                if self.tags_to_add:
                    self._full_vm_restore_options[_vm]['tags_to_add'] = self.tags_to_add
                if self.tags_to_remove:
                    self._full_vm_restore_options[_vm]['tags_to_remove'] = self.tags_to_remove

    def _submit_restore_job(self, vm_list):
        """
        Submits a restore job with the given inputs
        Args:
            vm_list     (list):    VMs to restore

        """
        if self.live_recovery and (self.snap_restore or self.secondary_snap_restore):
            for _vm in vm_list:
                _restore_vm = self.vm_restore_prefix + _vm
                if self.restore_destination_client.check_vms_exist([_restore_vm]):
                    self.restore_destination_client.VMs = _restore_vm
                    self.restore_destination_client.VMs[_restore_vm].delete_vm()
        self.restore_job_id = self.full_vm_restore_obj.full_vm_restore(
            vm_list,
            self.full_vm_in_place,
            proxy=self.restore_proxy,
            destination_server=self.restore_client,
            vm_info=self._full_vm_restore_options,
            different_vcenter=self.different_vcenter,
            different_vcenter_info=self.different_vcenter_info,
            disk_prov=self.disk_provisioning,
            transport_mode=self.transport_mode,
            power_on=self.power_on_after_restore,
            over_write=self.unconditional_overwrite,
            live_recovery=self.live_recovery,
            live_recovery_options=self.live_recovery_options,
            restore_to_recovery_target = True if self.recovery_target else False,
            passkey=self.passkey,
            live_recovery_restore_type=self.select_live_recovery_restore_type
        )

        if self.live_recovery:
            # vMotion is delayed by minimum 5 mins only for streaming
            if not self.snap_restore:
                time.sleep(300)
            # Copy testdata when the VM is migrating
            for _vm in vm_list:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = self.vm_restore_prefix + _vm
                self.log.info("Setting Restore Destination Client")

                retry = 0
                while retry < 20:
                    try:
                        self.restore_destination_client.VMs = restore_vm
                        self.log.info("Collecting properties of destination client")
                        self.restore_destination_client.VMs[restore_vm].update_vm_info('All',
                                                                                       True, True)
                        break
                    except Exception as err:
                        self.log.info("Exception occurred while updating VM info : {}".format(err))
                        self.log.info("VM Info couldn't be updated. Trying again. Try No {0}".format(retry))
                        time.sleep(120)
                        retry = retry + 1

                for _drive in self.hvobj.VMs[_vm].drive_list.values():
                    self.log.info("Copying TDFS data to Drive %s", _drive)
                    self.restore_destination_client.copy_test_data_to_each_volume(
                        restore_vm, _drive, "TDFSDataToTestWrite", self.testdata_path)
                    self.log.info("Done copying TDFS data")

                self._get_nfs_datastore_name(restore_vm)
                self._get_redirect_writes_datastore_name(restore_vm)

        job_details = self.get_job_status(self.restore_job_id)

    def live_mount(self, recovery_target):
        """
        performs Live Mount for each VM in subclient

        Args:
            recovery_target (string):    name of the Recovery target

        Raises:
            Exception:
                if Live Mount or Validation Fails

        """
        try:
            try:
                if not self.rep_target_dict:
                    self.rep_target_dict = self.get_target_summary(recovery_target)
            except Exception as exp:
                self.log.exception("Exception occurred during getting summary/accessing recovery target. %s", str(exp))
                raise exp

            if self.run_aux:
                self.copy_name = self.aux_copy
            elif self.snap_restore:
                self.copy_name = self.storage_policy.snap_copy
            elif self.run_auxiliary_copy == True:
                self.copy_name = self.execute_query(self.secondary_snap_copy_name, {'a': self.storage_policy.storage_policy_name})[0][0]
            else:
                self.copy_name = "Primary"

            vm_names = []
            live_mount_jobs = []
            for _vm in self._vms:
                self._navigate_to_vm_restore(_vm)
                self.select_restore_obj.select_live_mount()
                if self.rep_target_dict['Destination network'] == "Not Connected":
                    self.rep_target_dict['Destination network'] = "Original network"

                live_mount_job_id = self.live_mount_obj.submit_live_mount(recovery_target,
                                                                          self.rep_target_dict['Destination network'],
                                                                          self.copy_name,
                                                                          self.passkey)
                if not self.get_job_status(live_mount_job_id):
                    self.log.exception("Exception occurred during Live Mount Job")
                    raise Exception

                vm_names.append(_vm)
                live_mount_jobs.append(live_mount_job_id)

                if self.rep_target_dict['Migrate VMs'] == 'Yes':

                    # Wait for 5 mins so that the live mounted VM is booted up and running
                    time.sleep(300)

                    self.auto_vsa_client.rep_target_summary = self.rep_target_dict
                    restore_vm = self.auto_vsa_client.get_mounted_vm_name(_vm)

                    self.log.info("Setting Restore Destination Client")
                    self.restore_destination_client.VMs = restore_vm

                    retry = 0
                    while retry < 5:
                        try:

                            self.log.info("Collecting properties of destination client")
                            self.restore_destination_client.VMs[restore_vm].update_vm_info('All',
                                                                                           True, True)
                            break
                        except Exception as err:
                            self.log.info("VM Info couldn't be updated. Trying again. Try No {0}".format(retry))
                            time.sleep(120)
                            retry = retry + 1

                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        self.log.info("Copying TDFS data to Drive %s", _drive)
                        self.restore_destination_client.copy_test_data_to_each_volume(
                            restore_vm, _drive, "TDFSDataToTestWrite", self.testdata_path)
                        self.log.info("Done copying TDFS data")

                    self._get_nfs_datastore_name(restore_vm)
            return vm_names, live_mount_jobs

        except Exception as exp:
            self.log.exception("Exception occurred during Live Mount. %s", str(exp))
            raise exp

    def full_vm_restore(self, vm_level=False):
        """
        Performs full VM restore for a VMware subclient

        Args:
            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if full VM restore or validation fails

        """
        try:
            VirtualServerUtils.decorative_log("Performing VMware Full VM restore")

            if self._restore_proxy is None and self._co_ordinator:
                self.restore_proxy = self._co_ordinator

            if self.full_vm_in_place:
                self.disk_provisioning = "Original"

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                if self.different_vcenter:
                    host_machine = socket.gethostbyname_ex(socket.gethostname())[2][0]
                    _hvobj = Hypervisor([self.different_vcenter_name],
                                        self.different_vcenter_username,
                                        self.different_vcenter_password,
                                        self.instance_obj.instance_name.lower(),
                                        self.commcell, host_machine)
                    self.restore_destination_client = _hvobj
                else:
                    self.restore_destination_client = self.hvobj
            elif self.commcell.clients.has_client(self.restore_client):
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)
            else:
                if self.commcell.recovery_targets.has_recovery_target(self.restore_client):
                    self.recovery_target = self.commcell.recovery_targets.get(self.restore_client)
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.recovery_target.destination_hypervisor)
                    self.vm_restore_prefix = self.recovery_target._vm_prefix
            self._full_vm_restore_options = dict.fromkeys(self._vms, {})
            self._set_vm_restore_options()
            if self.validate_restore_workload:
                for _vm in self._vms:
                    self.restore_validation_options[_vm] = {'host': self._full_vm_restore_options[_vm]['host'],
                                                            'datastore': self._full_vm_restore_options[_vm][
                                                                'datastore']}

            if vm_level:
                for _vm in self._vms:
                    self._navigate_to_vm_restore(_vm)
                    self.configure_restore_settings()
                    if self.select_live_recovery_restore_type:
                        self.select_restore_obj.select_live_recovery()
                    else:
                        self.select_restore_obj.select_full_vm_restore()
                    self._submit_restore_job([_vm])
            else:
                if self.restore_from_job:
                    """restores from job page of command center"""
                    self.navigator.navigate_to_jobs()
                    self.job_obj.view_jobs_of_last_3_months()
                    self.job_obj.job_restore(self.restore_from_job, search=True)
                else:
                    if not self.conversion_restore:
                        self.navigator.navigate_to_hypervisors()
                        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                        self.vsa_sc_obj.restore()
                        self.select_restore_obj.select_full_vm_restore()

                self.configure_restore_settings()

                self._submit_restore_job(self._vms)

            if self.validation_skip_all:
                self.log.info("Skipping all validation as self.validation_skip_all is set to True")
                return

            if not self.conversion_restore:
                for _vm in self._vms:
                    if self.full_vm_in_place:
                        restore_vm = _vm
                    else:
                        restore_vm = self.vm_restore_prefix + _vm
                    self.vm_restore_validation(_vm, restore_vm, restore_options=self._full_vm_restore_options[_vm])

                    if self.live_recovery:
                        source_obj = self.hvobj.VMs[_vm]
                        restore_obj = self.restore_destination_client.VMs[restore_vm]
                        for each_drive in source_obj.drive_list:
                            dest_location = restore_obj.machine.join_path(
                                source_obj.drive_list[each_drive],
                                "TDFSDataToTestWrite",
                                "TestData",
                                self.timestamp)
                            self.fs_testdata_validation(
                                self.restore_destination_client.VMs[restore_vm].machine, dest_location)
                        self.live_recovery_validation(restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore. %s", str(exp))
            raise exp

    def conversion_validation(self, restore_obj, source_vm, restore_vm, restore_option):
        """
        Performs validation for VM restore to OCIinstance fromVMWare
        Args:
            restore_obj    (vsa object):     for VMware to Oci conversion ,pass OCi object
            source_vm     : name of source vm
            restore_vm  : name of restored vm
            restore_option : restore hypervisor properties
        Raises:
            Exception:
                if validation fails
        """
        if not self.validation:
            self.log.info("Validation is being skipped.")
            return

        VirtualServerUtils.decorative_log("Validating full VM restore")
        time.sleep(120)
        restore_obj.hvobj.update_hosts()
        self.hvobj.VMs[source_vm].update_vm_info('All', True, True)
        source_obj = self.hvobj.VMs[source_vm]
        if self.power_on_after_restore:
            restore_obj.hvobj.VMs = restore_vm
            attempt = 1
            while attempt < 5:
                restore_obj.hvobj.VMs[restore_vm].update_vm_info('All', True, True)
                restore_vm_obj = restore_obj.hvobj.VMs[restore_vm]
                if restore_vm_obj.ip is not None:
                    attempt = 5
                else:
                    self.log.info("Attempt number %s failed. Waiting for 2 mins for VM to"
                                  "come up", str(attempt))
                    time.sleep(120)
                    attempt += 1
        dest = restore_vm_obj.VmConversionValidation(restore_vm_obj)
        if dest.conversion_validation(restore_option):
            self.log.info("config validation is successful")
        else:
            self.log.error("error while configuration validation")
            raise Exception("Error while configuration validation")
        if (not (re.match(VirtualServerConstants.Ip_regex, "%s" % restore_vm_obj.ip)) and
                restore_vm_obj.ip is not None):
            for each_drive in source_obj.drive_list:
                dest_location = source_obj.machine.join_path(
                    source_obj.drive_list[each_drive],
                    self.backup_type.name, "TestData",
                    self.timestamp)
                self.fs_testdata_validation(
                    restore_vm_obj.machine, dest_location)
        else:
            self.log.info(
                "This is Linux VM and the destination Ip is not proper ,"
                "so no Data Validation cannot be performed")

    def setup_backup_validation(self, backup_validation_options):
        """
        Setting up details for backup validation

        Args:
            backup_validation_options   (dict):     Username, password etc options needed
                                                    for backup validation

        Raises:
            Exception:
                If setting backup validation fails
        """
        try:
            VirtualServerUtils.decorative_log("Setting up Backup validation")
            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])

            if backup_validation_options.get('snap_copy'):
                backup_validation_options['copy_name'] = self.storage_policy.snap_copy
            else:
                backup_validation_options['copy_name'] = "Primary"

            self.vsa_sc_obj.set_backup_validation(backup_validation_options)
        except Exception as exp:
            self.log.exception("Exception occurred during setting validation backup. %s", str(exp))
            raise exp

    def run_validate_backup_vmgroup(self, backup_validation_options):
        """
        Trigger backup validation from vm group level

        Args:
            backup_validation_options   (dict):     Recovery target etc needed for validation backup validation

        """
        VirtualServerUtils.decorative_log("Running Validate Backup from vm group")
        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
        backup_validation_job = self.vsa_sc_obj.run_validate_backup(
            recovery_point=backup_validation_options.get('recovery_point'))
        if not backup_validation_options.get('report_validation'):
            self.validate_backup(backup_validation_options, backup_validation_job)
            # Add the key to have minimum of 15 mins of wait time before the job gets over
        else:
            job_details = self.get_job_status(backup_validation_job, "failed")
            if not job_details:
                raise Exception("Backup validation job not in expected state -> [Failed]")

    def run_validate_backup_vm(self, backup_validation_options):
        """
        Trigger backup validation from vm level

        Args:
            backup_validation_options   (dict):     Recovery target etc needed for validation backup validation

        """
        VirtualServerUtils.decorative_log("Running Validate Backup from vm level")
        for each_vm in self._vms:
            self.navigator.navigate_to_virtual_machines()
            self.virtual_machines_obj.open_vm(each_vm)
            backup_validation_job = self.vm_details_obj.run_validate_backup()
            self.validate_backup(backup_validation_options, backup_validation_job, each_vm)
            # Add the key to have minimum of 15 mins of wait time before the job gets over

    def run_validate_backup_schedule(self, backup_validation_options):
        """
        Validating and triggering backup validation from backup schedule

        Args:
            backup_validation_options   (dict):     Recovery target etc needed for validation backup validation

        Raises:
            Exception:
                Exception in running job from schedule
        """
        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
        self.vsa_sc_obj.schedule_backup_validation(only_schedule=True, after_time=300)
        self.log.info("Sleeping for 6 mins for schedule to trigger")
        time.sleep(360)
        job_controller = self.commcell.job_controller
        vm_jobs = job_controller.all_jobs(client_name=None, job_filter='VM_Management')
        for _job in vm_jobs:
            _job_detail = job_controller.get(_job)
            if _job_detail.details['jobDetail']['generalInfo']['jobStartedFrom'] == 'Scheduled':
                if _job_detail.details['jobDetail']['generalInfo']['scheduleName'] == self.driver.session_id:
                    self.log.info("{} was started by schedule".format(_job))
                    self.validate_backup(backup_validation_options, str(_job))
                    return
        raise Exception("Backup validation job not triggered")

    def fail_backup_validation_job(self, backup_validation_job):
        """
        Fails Backup validation job

        Args:
            backup_validation_job      (string):     backup validation job

        Raises:
            Exception:
                If deleting the vms failed
        """
        try:
            time.sleep(300)
            vm_list = [*self._vms]
            for each_vm in vm_list:
                dest_vm = each_vm + '_LM_' + backup_validation_job
                self.hvobj.VMs = dest_vm
                if self.hvobj.check_vms_exist([dest_vm]):
                    self.log.info("--- Deleting the VM {} ---".format(dest_vm))
                    restore_obj = self.hvobj.VMs[dest_vm]
                    restore_obj.backup_validation()
                    restore_obj.delete_vm()
                    time.sleep(30)
                    self.log.info("--- Deleted VM {} Successfully ---".format(dest_vm))
        except Exception as exp:
            self.log.exception("Exception occurred deletion of LM vms %s", str(exp))
            raise exp

    def validate_backup(self, backup_validation_options, backup_validation_job, each_vm=None):
        """
        Runs and validates Backup validation job and status

        Args:
            backup_validation_options   (dict):     Recovery target etc needed for validation backup validation

            backup_validation_job      (string):     backup validation job

            each_vm                    (string):     Vm for which backup validation has been run

        Raises:
            Exception:
                If running and validating backup validation fails
        """
        try:
            if each_vm:
                vm_list = [each_vm]
            else:
                vm_list = [*self._vms]
            if backup_validation_options.get('recovery_target'):
                target_details = self.get_target_summary(backup_validation_options['recovery_target'])
                target_client_DN = target_details['Destination hypervisor']
                target_client = self.get_client_name_from_display_name(target_client_DN)
                dest_client = self._create_hypervisor_object(target_client)[0]
                target_esx = target_details['Destination host']
                media_agent = target_details['MediaAgent']
            else:
                dest_client = self.hvobj
                media_agent = self.auto_vsa_subclient._browse_ma

            start_time = time.time()
            VirtualServerUtils.decorative_log("sleeping for 5 mins so that all the vms are mounted and booted")
            time.sleep(300)
            # Commenting out validation of output of script for now
            # if backup_validation_options.get('unc_path'):
            #     output_file = os.path.split(backup_validation_options['unc_path'])[0] + '\\automation_out.txt'
            #     line = open(output_file).readline()
            #     # Will correct this log better
            #     if 'This file is created via automation' in line:
            #         self.log.info("Custom script executed properly")
            #     else:
            #         raise Exception("Custom script didn't ran")
            _job = JobManager(backup_validation_job, self.commcell)
            if _job.job.status.lower() in (
                    'killed', 'completed', 'completed w/ one or more errors', 'failed'):
                raise Exception(
                    "The Backup validation job has either failed/killed or completed too early."
                    "Please check the vm management log")
            no_of_vms_mounted = 0
            mounted_data_stores = []
            mounted_vm_list = []
            for each_vm in vm_list:
                dest_vm = each_vm + '_LM_' + backup_validation_job
                mounted_vm_list.append(dest_vm)
                dest_client.VMs = dest_vm
                if dest_client.check_vms_exist([dest_vm]):
                    no_of_vms_mounted = no_of_vms_mounted + 1
                    if no_of_vms_mounted > 5:
                        raise Exception("Maximum number of mounted vms is 5")
                    self.log.info("--- Validation for vm {} ---".format(dest_vm))
                    restore_obj = dest_client.VMs[dest_vm]
                    restore_obj.backup_validation()
                    mounted_data_stores.append(restore_obj.datastore)
                    if restore_obj.power_state == 'poweredOn':
                        self.log.info("VM: {} is powered on".format(dest_vm))
                        if restore_obj.tools != 'running':
                            raise Exception("Boot up properly failed")
                        self.log.info("VM: {} booted properly".format(dest_vm))
                    else:
                        raise Exception("Power on failed")
                    if backup_validation_options.get('recovery_target'):
                        if restore_obj.esx_host == target_esx:
                            self.log.info("VM recovery target validated: {}".format(target_esx))
                    else:
                        if restore_obj.esx_host == self.hvobj.VMs[each_vm].esx_host:
                            self.log.info("Source VM ESX validated")
                    if self.validate_testdata_on_live_mount:
                        retry = 0
                        while retry < 5:
                            try:
                                self.log.info("Collecting properties of destination client")
                                restore_obj.update_vm_info('All', True, True)
                                break
                            except Exception as err:
                                self.log.info("VM Info couldn't be updated. Trying again. Try No {0}".format(retry))
                                time.sleep(240)
                                retry = retry + 1

                        for each_drive in restore_obj.drive_list:
                            dest_location = restore_obj.machine.join_path(
                                restore_obj.drive_list[each_drive],
                                self.backup_folder_name, "TestData",
                                self.timestamp)
                            self.fs_testdata_validation(
                                restore_obj.machine, dest_location)

            if len(vm_list) < 5:
                if not no_of_vms_mounted == len(vm_list):
                    raise Exception("All vms are not mounted")
            else:
                if no_of_vms_mounted < 5:
                    raise Exception("Total number of vms mounted at a time should be 5.")
            unique_datastores = (list(set(mounted_data_stores)))
            self.log.info('backup_validation_job: {0} backup_job: {1}'.
                          format(backup_validation_job, self.backup_job))
            if self.get_job_status(backup_validation_job):
                job_controller = self.commcell.job_controller
                _job_detail = job_controller.get(backup_validation_job)
                if _job_detail.job_type != 'Virtual Machine Management':
                    raise Exception("Job type should be Virtual Machine Management")
                self.log.info("{} job is of Virtual Machine Management".format(backup_validation_job))

            if backup_validation_options.get('snap_copy') is not None:
                found, log_line = VirtualServerUtils.find_log_lines(cs=self.commcell,
                                                                    client_name=self.commcell.commserv_name,
                                                                    log_file="VMManagement.log",
                                                                    search_term="bIsVMValidationForSnap [1]",
                                                                    job_id=backup_validation_job)
                if found:
                    is_snap_validation = True
                else:
                    is_snap_validation = False
                if backup_validation_options['snap_copy']:
                    if is_snap_validation:
                        self.log.info("Backup Validation was performed using Snap copy".format(backup_validation_job))
                    else:
                        raise Exception("Snap copy was not used for Backup Validation")
                else:
                    if is_snap_validation:
                        raise Exception("Backup Validation was performed using Snap copy".format(backup_validation_job))
                    else:
                        self.log.info("Backup Validation was performed using Backup copy".format(backup_validation_job))

            if backup_validation_options.get('retain_vms'):
                from VirtualServer.VSAUtils import VirtualServerHelper
                AutoVSACommcell_obj = AutoVSACommcell(self.commcell, self.csdb)
                AutoVSACommcell_obj.validate_lab_creation(backup_validation_job)
                client = self.commcell.clients.get(self.hypervisor)
                AutoVSAVSClient_obj = VirtualServerHelper.AutoVSAVSClient(AutoVSACommcell_obj, client)
                isolated_network = True if target_details.get('Configure isolated network') == 'Yes' else False
                AutoVSAVSClient_obj.rep_target_summary = target_details
                AutoVSAVSClient_obj.live_mount_migration = True if target_details['Migrate VMs'] == 'Yes' else False
                AutoVSAVSClient_obj.live_unmount_validation(vm_list, mounted_vm_list, dest_client,
                                                            isolated_network=isolated_network, start_time=start_time)

            VirtualServerUtils.decorative_log("Checking if the Vms are deleted")
            for each_vm in vm_list:
                dest_vm = each_vm + '_LM_' + backup_validation_job
                self.log.info("--- Verifying Cleanup of the vm: {} ---".format(dest_vm))
                if dest_client.check_vms_exist([dest_vm]):
                    raise Exception('VMs is not cleaned up')
                self.log.info("VM:{} is cleaned".format(dest_vm))

            VirtualServerUtils.decorative_log("Checking if the Datastores are deleted")
            for ds in unique_datastores:
                self.auto_vsa_client.vmware_live_mount_validation([str(backup_validation_job)],
                                                                  dest_client,
                                                                  ds,
                                                                  media_agent=media_agent)

            if not (backup_validation_options.get('recovery_point') or backup_validation_options.get('retain_vms')):
                # validating for status for each vm
                VirtualServerUtils.decorative_log("Validating the backup validation results")
                for each_vm in vm_list:
                    self.navigator.navigate_to_virtual_machines()
                    self.virtual_machines_obj.open_vm(each_vm)
                    details = self.vm_details_obj.backup_validation_results()
                    if not (details['Boot status'] == 'Success'
                            and details['Last validation job ID'] == backup_validation_job
                            and details['Backup validated'] == self.backup_job):
                        self.log.error("failure in backup validation of vm{} : {}".format(each_vm, details))
                        raise Exception("failure in backup validations")
                    else:
                        self.log.info("Backup validation verified for vm {}".format(each_vm))
                    script_result = self.vm_details_obj.backup_validation_scripts()
                    if not script_result:
                        if backup_validation_options.get('agent') or backup_validation_options.get(
                                'unc_path_win') or backup_validation_options.get('unc_path_unix'):
                            self.log.error("VM {} has agent installed or custom script added. "
                                           "Script result is empty".format(each_vm))
                            raise Exception("failure in backup validations")
                    else:
                        for _script_status in script_result:
                            if _script_status[1] == 'Success':
                                self.log.info("Name: {}  Script status: {}".format(_script_status[0],
                                                                                   _script_status[1]))
                            else:
                                raise Exception("Name: {}  Failure reason: {}".format(_script_status[0],
                                                                                      _script_status[2]))
        except Exception as exp:
            self.log.exception("Exception occurred during validation backup %s", str(exp))
            raise exp

    def backup_validation_report_validation(self, testcase_obj, test_status):
        """
        Validates Report and the actual data is correct

        Args:
            testcase_obj   (object):     Testcase object

            test_status     (string):       Status of the validation job

        Raises:
            Exception:
                If Report data mismatches

        """
        try:
            self.navigator.navigate_to_dashboard()
            board = Dashboard(testcase_obj.admin_console)
            board.navigate_to_given_dashboard('Virtualization')
            vm_pane_entities = board._get_entity_titles(VirtualizationDashboard.pane_vms.value)

            if VirtualizationDashboard.entity_validation_failed.value in vm_pane_entities:
                board.access_details_page(VirtualizationDashboard.pane_vms.value,
                                          VirtualizationDashboard.entity_validation_failed.value)
                viewer_obj = viewer.CustomReportViewer(testcase_obj.admin_console)
                table_obj = viewer.DataTable("VM Details")
                viewer_obj.associate_component(table_obj)
                _data = table_obj.get_table_data()
                report = [dict(zip(_data, t)) for t in zip(*_data.values())]
                vms_in_vm_group = [*self._vms]
                # A VM listed in the report but not part of VM group can be in validation failed state
                # which can cause the VALIDATION FAILED entity to show up in the VM pane
                other_vm_validation_failure = False
                for _vm in report:
                    if _vm['VM Name'] in vms_in_vm_group:
                        self.navigator.navigate_to_virtual_machines()
                        _vm_name = _vm['VM Name']
                        self.virtual_machines_obj.open_vm(_vm_name)
                        details = self.vm_details_obj.backup_validation_results()
                        if details['Boot status'].lower() == 'success':
                            details['Boot status'] = 'Passed'
                        if not (details['Boot status'] == _vm['Boot status']
                                and details['Last validation job ID'] == _vm['Last Validation Job ID']
                                and details['Backup validated'] == _vm['Validated Backup Job ID']):
                            self.log.error("failure in backup validation of vm{} : {}".format(_vm, details))
                            raise Exception("failure in backup validations")
                    else:
                        if _vm['Failure Reason']:
                            other_vm_validation_failure = True
                self.log.info("Report matches for all the VMs")
                if test_status == 'success':
                    if not other_vm_validation_failure:
                        self.log.error("VALIDATION FAILED should not be visible "
                                       "when there is a NO failed backup validation job")
                        raise Exception("Report validation failed")
            else:
                self.log.info("VALIDATION FAILED entity not found in the VMs pane")
                if test_status == 'failed':
                    self.log.error("VALIDATION FAILED should  be visible "
                                   "when there is a failed backup validation job")
                    raise Exception("Report validation failed")
        except Exception as exp:
            self.log.exception("Exception occurred during report validation %s", str(exp))
            raise exp

    def get_replication_job(self, replication_group_name=None):
        """
        Return Live Sync job in progress for the replication group
        Args:
            replication_group_name: Name of replication Group

        Returns: JOB ID

        """
        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        replication_job_id = self.replication_group_details_obj.get_replication_job()
        return replication_job_id

    def validate_status(self, status_list, value):
        """
        Validate values in status list
        Raises:
             Exception:
                If validation fails
        """
        for status in status_list:
            if status.lower() != value:
                return False
        return True

    def validate_live_sync(self, replication_group_name=None, live_sync_direct=False):
        """
                Validates Live Sync functionality for VMW.

                Args:
                    replication_group_name (str):     Name of the replication group, if not set,
                    a replication group is automatically set
                    live_sync_direct (bool) :   true if it is a live sync direct validation

                Raises:
                    Exception:
                        If validation fails.

        """
        try:
            live_sync_options = {"live_sync_direct": live_sync_direct}
            OptionsHelperMapper.RestoreOptionsMapping.validate_live_sync(replication_group_name, live_sync_options)
            self.log.info('Validation completed successfully')
        except Exception as exp:
            self.log.error(exp)
            raise Exception("Failed to complete live sync validation.")

    def guest_file_download(self, files, browse_folder="", end_user=False, vm_without_download_permission=[]):
        """
            Performs guest file download and validates it.
            if you are doing single file, multiple file or multiple file and folder download then
            run create_testdata_for_guest_file_download() first then guest_file_downlaod
            else it will check the download for FULL, INCR folder

            Args:
                files (list) : list of files to be downloaded
                browse_folder (str) : Location where files are present
                end_user (bool) : if end user creds are used
                vm_without_download_permission (list) :  list of vm's does not have download permission

            Raises:
                Exception:
                    If guest file download fails.
        """
        try:
            for _vm in self._vms:
                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():

                    destination_folder = TEMP_DIR
                    testdata_path = VIRTUAL_SERVER_TESTDATA_PATH + "\\TestFolder"
                    browse_folder = ""
                    self.controller_machine.remove_directory(destination_folder)
                    self.controller_machine.create_directory(destination_folder)

                    # Initialize flags
                    single_file = False
                    multiple_file = False
                    mutiple_file_and_folder = False

                    # Count the number of ".txt" files and non-text entries
                    txt_count = 0
                    non_txt_count = 0

                    for entry in files:
                        if entry.endswith(".txt"):
                            txt_count += 1
                        else:
                            non_txt_count += 1

                    # Check the conditions and set the flags
                    if len(files) == 1 and txt_count == 1:
                        single_file = True

                    if len(files) > 1 and txt_count == len(files):
                        multiple_file = True

                    if len(files) > 1 and non_txt_count > 0:
                        mutiple_file_and_folder = True

                    if end_user:
                        self._navigate_to_vm_restore(_vm)
                    else:
                        self.navigator.navigate_to_hypervisors()
                        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                        self.vsa_sc_obj.restore()

                    if self.backup_method == "SNAP":
                        self.configure_restore_settings()

                    self.select_restore_obj.select_guest_files()
                    self.select_restore_obj.latest_backups()

                    if _folder == "/":
                        self.restore_vol_obj.select_volume(_vm, _folder)
                    else:
                        self.restore_vol_obj.select_volume(_vm, _drive)

                    try:
                        self.restore_job_id = self.restore_files_obj.download_guest_file_content(files, browse_folder,
                                                                                                 _vm,
                                                                                                 vm_without_download_permission)
                    except NoSuchElementException as e:
                        if "Download Button Not Found" in str(e):
                            if _vm in vm_without_download_permission:
                                break
                        raise NoSuchElementException("Download Button Not Found")

                    if _vm in vm_without_download_permission:
                        self.log.info(f'{_vm} do not have download permission, But download button is present');
                        raise Exception("Download but should not be there as vm do not have permission")

                    if self.restore_job_id and not (self.restore_job_id == 1 or self.restore_job_id == 2):
                        self.get_job_status(self.restore_job_id)

                    if single_file:
                        if self.restore_job_id and not (self.restore_job_id == 1 or self.restore_job_id == 2):
                            self.restore_files_obj.select_download()

                        self.admin_console.wait_for_completion(wait_time=3000)
                        testdata_path = self.controller_machine.join_path(testdata_path, files[0])
                        destination_path = self.controller_machine.join_path(destination_folder, files[0])
                        self.fs_testdata_validation(self.controller_machine, destination_path, testdata_path,
                                                    file_restore=True)

                    elif multiple_file:
                        if self.restore_job_id and not (self.restore_job_id == 1 or self.restore_job_id == 2):
                            self.restore_files_obj.select_download()
                        self.admin_console.wait_for_completion(wait_time=3000)

                        destination_path = self.controller_machine.join_path(destination_folder, "EXTRACT")
                        self.controller_machine.create_directory(destination_path, force_create=True)

                        downloaded_file = os.listdir(destination_folder)
                        self.controller_machine.unzip_zip_file(destination_folder + "\\" + downloaded_file[0],
                                                               destination_path)

                        self.fs_testdata_validation(self.controller_machine, destination_path + '\\' + files[0],
                                                    testdata_path + '\\' + files[0], file_restore=True)

                        self.fs_testdata_validation(self.controller_machine, destination_path + '\\' + files[1],
                                                    testdata_path + '\\' + files[1], file_restore=True)

                    elif mutiple_file_and_folder:
                        self.admin_console.wait_for_completion(wait_time=3000)
                        downloaded_file = os.listdir(destination_folder)
                        destination_path = self.controller_machine.join_path(destination_folder, "EXTRACT")
                        self.controller_machine.create_directory(destination_path, force_create=True)

                        if downloaded_file:
                            self.controller_machine.unzip_zip_file(destination_folder + "\\" + downloaded_file[0],
                                                                   destination_path)
                        else:
                            self.admin_console.click_recent_downloads()
                            item = self.recent_download.download_recent_item()
                            self.controller_machine.unzip_zip_file(destination_folder + "\\" + item + ".zip",
                                                                   destination_path)

                        self.fs_testdata_validation(self.controller_machine, destination_path,
                                                    testdata_path=testdata_path)

                    else:
                        self.admin_console.wait_for_completion(wait_time=3000)
                        downloaded_file = os.listdir(destination_folder)
                        destination_path = self.controller_machine.join_path(destination_folder, "EXTRACT")
                        self.controller_machine.create_directory(destination_path, force_create=True)

                        if downloaded_file:
                            self.controller_machine.unzip_zip_file(destination_folder + "\\" + downloaded_file[0],
                                                                   destination_path)
                        else:
                            self.admin_console.click_recent_downloads()
                            item = self.recent_download.download_recent_item()
                            self.controller_machine.unzip_zip_file(destination_folder + "\\" + item + ".zip",
                                                                   destination_path)

                        self.fs_testdata_validation(self.controller_machine, destination_path + '\\'
                                                    + self.backup_type.name + '\\TestData\\' + self.timestamp)


        except Exception as exp:
            self.log.exception("Error in guest file download. %s", str(exp))
            raise exp

    def create_testdata_for_guest_file_download(self):
        """
            Generate test data for guest file download.
            Raises:
                Exception:
                    If test data generation fails.
        """
        try:
            guest_file_testdata_path = VIRTUAL_SERVER_TESTDATA_PATH + "\\TestFolder"
            testdata_file1 = guest_file_testdata_path + "\\test1.txt"
            testdata_file2 = guest_file_testdata_path + "\\test2.txt"
            testdata_folder1 = guest_file_testdata_path + "\\folder1"
            testdata_file3 = testdata_folder1 + "\\test3.txt"

            self.controller_machine.create_directory(guest_file_testdata_path, force_create=True)
            self.controller_machine.create_directory(testdata_folder1, force_create=True)

            self.controller_machine.create_file(testdata_file1, "Random Test Data For Text1")
            self.controller_machine.create_file(testdata_file2, "Random Test Data For Text2")
            self.controller_machine.create_file(testdata_file3, "Random Test Data For Text3")

            for _vm in self._vms:
                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    self.hvobj.copy_test_data_to_each_volume(_vm, _drive + ":", "TESTFOLDER", guest_file_testdata_path)

        except Exception as exp:
            self.log.exception("Error in create_testdata_for_guest_file_download. %s", str(exp))
            raise exp

    def modify_testdata_for_guest_file_download(self, file_name):
        """
        Modify File inside testdata generated using create_testdata_for_guest_file_download()
        Raises:
            Exception:
                if file not exist or if file not get modified
        """
        try:
            guest_file_testdata_path = VIRTUAL_SERVER_TESTDATA_PATH + "\\TestFolder"
            testdata_file1 = guest_file_testdata_path + "\\" + file_name

            if not self.controller_machine.check_file_exists(testdata_file1):
                raise Exception(f"{testdata_file1} File Not Exist")

            self.controller_machine.modify_content_of_file(testdata_file1, content="ModifiedFile")

            for _vm in self._vms:
                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    self.hvobj.copy_test_data_to_each_volume(_vm, _drive + ":", "TESTFOLDER", guest_file_testdata_path)

        except Exception as exp:
            self.log.exception("Error in create_testdata_for_guest_file_download. %s", str(exp))
            raise exp

    def attach_disk_restore(self):
        """
        Performs attach disk restore for VMware VM
        """
        VirtualServerUtils.decorative_log("Performing Attach Disk Restore")

        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator
        if self._restore_client is None:
            self.restore_client = self.hypervisor
            self.restore_destination_client = self.hvobj
        else:
            if not self.restore_destination_client:
                self.restore_destination_client, \
                    self._restore_instance_type = self._create_hypervisor_object(self.restore_client)

        for _vm in self._vms:
            destination_vm = self.destination_vm if self.destination_vm else _vm
            self.restore_destination_client.VMs = destination_vm
            destination_vm_obj = self.restore_destination_client.VMs[destination_vm]
            destination_ds = self.destination_datastore if self.destination_datastore else self.hvobj.VMs[
                _vm].datastore
            disks = list(map(lambda x: x.split('/')[-1], destination_vm_obj.disk_list))
            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.restore()
            self.select_restore_obj.select_disk_restore()
            self.restore_job_id = self.disk_level_restore_obj. \
                vmware_attach_disk_restore(_vm, destination_vm, self.restore_client, self.restore_proxy, disks,
                                           destination_ds)
            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Attach disk restore job failed.")
            destination_vm_obj.update_vm_info('All', True, True)
            post_restore_disks = list(map(lambda x: x.split('/')[-1], destination_vm_obj.disk_list))
            self.attach_disk_restore_validation(_vm, disks, post_restore_disks)

    def end_user_attach_disk_restore(self):
        """
        Performs attach disk restore for VMware VM as end user
        """
        VirtualServerUtils.decorative_log("Performing End User Attach Disk Restore")
        self.restore_client = self.hypervisor
        self.restore_destination_client = self.hvobj
        for _vm in self._vms:
            destination_vm = self.destination_vm if self.destination_vm else _vm
            destination_vm_obj = self.restore_destination_client.to_vm_object(destination_vm)
            disks = destination_vm_obj.disk_list
            self._navigate_to_vm_restore(_vm)
            self.select_restore_obj.select_disk_restore()
            self.restore_job_id = self.disk_level_restore_obj.vmware_attach_disk_restore(_vm, destination_vm,
                                                                                         end_user=True)
            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Attach disk restore job failed.")
            post_restore_disks = destination_vm_obj.disk_list
            self.attach_disk_restore_validation(_vm, disks, post_restore_disks)

    def attach_disk_restore_validation(self, vm, before_disk_list, after_disk_list):
        """
        Performs attach disk restore validation for VMware VM

        Args:
            vm  (str):      Destination VM
            before_disk_list    (list):   List of disks before restore
            after_disk_list     (list):     List of disks after restore

        Raises:
            Exception:
                If attach disk restore validation fails
        """
        try:
            _before_restore = len(before_disk_list)
            self.log.info("No of disks before restore: {}".format(_before_restore))
            _after_restore = len(after_disk_list)
            self.log.info("No of disks after restore: {}".format(_after_restore))
            if _after_restore / _before_restore == 2:
                self.log.info("Disk restore validation complete")
            else:
                raise Exception("Disk restore validation failed")
            if not self.restore_destination_client.VMs[vm].delete_disks():
                self.log.exception("Deletion of attached disk failed. clean the disks manually")
                raise Exception("Failed to delete the disks")

        except Exception as exp:
            self.log.exception("Exception in disks validation %s", str(exp))
            raise exp


class HyperVAdminConsole(AdminConsoleVirtualServer):
    """
    Hyper-V class to perform Hyper-V related adminconsole tasks
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize any Hyper-V related variables

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the cs DB object

        """
        super(HyperVAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._register_to_failover = False
        self._restore_location = None
        self._restore_host = None
        self.restore_options = {}
        self.restore_path = None

    @property
    def register_to_failover(self):
        """
        Returns the register to failover option

        Returns:
            register_to_failover   (bool)  --  True / False to register to failover cluster

        """
        return self._register_to_failover

    @register_to_failover.setter
    def register_to_failover(self, value):
        """
        Sets the register to failover option

        Args:
            value   (bool)  --  True / False to register the VM to failover after restore

        """
        self._register_to_failover = value

    @property
    def restore_location(self):
        """
        Returns the restore location, hyper-v default folder or new folder or original location

        Returns:
            restore_location   (str)   --  the location to restore the VM to

        """
        return self._restore_location

    @restore_location.setter
    def restore_location(self, value):
        """
        Sets the location to restore the VM to

        Args:
            value   (str)    --  the location where the VM should be restored

        """
        self._restore_location = value

    @property
    def restore_host(self):
        """
        Returns the hyper-v host machine where restored VM is to be hosted

        Returns:
            restore_host   (str)   --  the host to restore the VM to

        """
        return self._restore_host

    @restore_host.setter
    def restore_host(self, value):
        """
            Sets the host to restore the VM to

            Args:
                value   (str)    --  the host where the VM should be restored

        """
        self._restore_host = value

    def full_vm_restore(self):
        """
        Perform full VM restore for hyper-V

        Raises:
            Exception:
                if full VM restore or validation fails

        """
        try:
            VirtualServerUtils.decorative_log("Performing Full VM Restore")

            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator
            if self._restore_host is None:
                self.restore_host = self._co_ordinator.machine_name

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj

            elif self.commcell.clients.has_client(self.restore_client):
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)

            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.restore()
            self.select_restore_obj.select_full_vm_restore()
            if self.full_vm_in_place:
                self.restore_location = "Original folder"
                self.restore_path = None
                self.vm_restore_prefix = None
                self.unconditional_overwrite = True

            if self.restore_location is None:
                self.restore_location = "Hyper-V default folder"
                hostname = self.restore_host.rsplit('_')[0]
                self.restore_path = self.hvobj.get_hyperv_default_folder(hostname)


            if self.restore_location == "Select a folder":
                if not self.restore_path:
                    raise Exception("The restore path was not provided")

            self.restore_options = dict.fromkeys(self._vms, {})
            self._set_hyperv_vm_restore_options()

            self._submit_restore_job(self.vms)

            if self.validate_restore_workload:
                self.restore_validation_options['restore_path'] = self.restore_path

            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Restore job failed. Please check the logs")

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = str(self.vm_restore_prefix) + _vm
                self.vm_restore_validation(_vm, restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during Hyper-v Full VM restore. %s", str(exp))
            raise exp

    def _submit_restore_job(self, vm_list):

        self.restore_job_id = self.full_vm_restore_obj.hv_full_vm_restore(
            vm_list,
            destination_client=self.restore_client,
            destination_proxy=self.restore_proxy,
            power_on=self.power_on_after_restore,
            overwrite_instance=self.unconditional_overwrite,
            in_place=self.full_vm_in_place,
            restore_prefix=self.vm_restore_prefix,
            instance_options=self._restore_options
        )

        job_details = self.get_job_status(self.restore_job_id)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def _set_hyperv_vm_restore_options(self):


        for each_vm in self.vms:
            self.restore_options[each_vm]['restore_path'] = self.restore_path
            self.restore_options[each_vm]['prefix'] = self.vm_restore_prefix
            self.restore_options[each_vm]['location'] = self.restore_location
            self.restore_options[each_vm]['full_vm_in_place'] = self.full_vm_in_place
            self.restore_options[each_vm]['restore_host'] = self.restore_host
            self.restore_options[each_vm]['restore_proxy'] = self.restore_proxy
            self.restore_options[each_vm]['overwrite'] = self.unconditional_overwrite
            if self.restore_network:
                self.restore_options[each_vm]['network'] = self.restore_network



class OracleCloudAdminConsole(AdminConsoleVirtualServer):
    """
    This module is for performing Oracle Cloud related actions from AdminConsole
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initializes the Oracle Cloud related inputs

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the cs DB object

        """

        super(OracleCloudAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._user_account = None
        self._security_groups = None
        self._ssh_keys = None
        self._networks = None
        self._instance_shape = "Auto"

    @property
    def instance_shape(self):
        """
        Returns the instance shape option

        Returns:
            _instance_shape     (str)    --  the shape to be used for the restore instance

        """
        return self._instance_shape

    @instance_shape.setter
    def instance_shape(self, value):
        """
        Sets the instance shape option

        Args:
            value   (str)    --  the instance shape to be used for the restore VMs

        """
        if not isinstance(value, str):
            raise Exception("The instance shape should be a string")
        self._instance_shape = value

    @property
    def user_account(self):
        """
        Returns the user account name

        Returns:
            _user_account   (str)    --  the name of the user account to restore to

        """
        return self._user_account

    @user_account.setter
    def user_account(self, value):
        """
        Sets the user account

        Args:
            value   (str)    --  the user account where the instances are to be restored

        """
        if not isinstance(value, str):
            raise Exception("The user account name should be a string")
        self._user_account = value

    @property
    def security_groups(self):
        """
        Returns the security groups

        Returns:
            _security_groups    (list)  --  list of all security groups to be associated with
                                            the restored instances

        """
        return self._security_groups

    @security_groups.setter
    def security_groups(self, value):
        """
        Sets the security groups

        Args:
            value   (list)  --  list of all security groups to be associated with the
                                restored instances

        """
        if isinstance(value, list):
            self._security_groups = value
        elif isinstance(value, str):
            self._security_groups = [value]
        else:
            raise Exception("The security group should either be a list or string.")

    @property
    def ssh_keys(self):
        """
        Returns the ssh keys

        Returns:
            _ssh_keys   (list)  --  list of all ssh keys to be associated with instances

        """
        return self._ssh_keys

    @ssh_keys.setter
    def ssh_keys(self, value):
        """
        Sets the ssh keys

        Args:
            value   (list)  --  list of all ssh keys to be associated with the restored instances

        """
        if isinstance(value, list):
            self._ssh_keys = value
        elif isinstance(value, str):
            self._ssh_keys = [value]
        else:
            raise Exception("The ssh keys should either be a list or string.")

    @property
    def networks(self):
        """
        Returns the networks list

        Returns:
            _networks   (list)  --  list of all networks to be attached to instances

        """
        return self._networks

    @networks.setter
    def networks(self, value):
        """
        Sets the networks list

        Args:
            value   (list)  --  list of all networks to be attached to the restored instances

        """
        if isinstance(value, list):
            self._networks = value
        elif isinstance(value, str):
            self._networks = [value]
        else:
            raise Exception("The networks should either be a list or string.")

    def _set_restore_options(self):
        """
        Sets the restore options for full VM restore

        Raises:
            Exception:
                if there is any error in setting the restore options

        """
        try:
            self.log.info("Setting the restore options")
            dest_vm = list(self._vms)[0]

            if not self.user_account:
                self.user_account = self.hvobj._get_instance_user_name(dest_vm)

            if not self.security_groups:
                self.security_groups = self.hvobj._get_security_list_of_instance(dest_vm)

            if not self.ssh_keys:
                self.ssh_keys = self.hvobj._get_ssh_keys_of_instance(dest_vm)

        except Exception as exp:
            raise Exception("An error occurred while setting the restore options. "
                            "{0}".format(str(exp)))

    def full_vm_restore(self):
        """
        Full instance restore of Oracle Cloud instances

        Raises:
            Exception:
                if full instance restore or validation fails

        """
        try:
            self.log.info("Restoring the Oracle Cloud Instance")
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)

            self._set_restore_options()

            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.restore()
            self.select_restore_obj.select_full_vm_restore()

            self.restore_job_id = self.full_vm_restore_obj.opc_full_vm_restore(
                self._vms,
                self.restore_proxy,
                self.restore_client,
                self.power_on_after_restore,
                self.vm_restore_prefix,
                self.user_account,
                self.instance_shape,
                self.networks,
                self.security_groups,
                self.ssh_keys
            )

            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Restore job failed. Please check the logs")

            for _vm in self._vms:
                restore_vm = self.vm_restore_prefix + _vm
                self.vm_restore_validation(_vm, restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during Oracle Cloud Full VM restore."
                               " %s", str(exp))
            raise exp


class AlibabaCloudAdminConsole(AdminConsoleVirtualServer):
    """
    Class for Ali Cloud related operations to be done in admin console
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initializes the Oracle Cloud related inputs

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the cs DB object

        """

        super(AlibabaCloudAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._full_vm_restore_options = None
        self.restore_proxy_input = None

    def _set_instance_restore_options(self):
        """
        Sets the restore options for each instance to be restored

        Raises:
            Exception:
                if there is any exception in setting the restore options

        """
        availability_zone, network, security_groups = self.hvobj.compute_free_resources(
            self.restore_proxy)
        for vm in self._vms:
            # instance_type will always come from the backup VM
            # availability_zone, network and security_groups will be obtained from proxy

            self._full_vm_restore_options[vm]['availability_zone'] = availability_zone
            self._full_vm_restore_options[vm]['instance_type'] = self.hvobj.VMs[vm].instance_type
            self._full_vm_restore_options[vm]['network'] = network
            self._full_vm_restore_options[vm]['security_groups'] = security_groups

    def _submit_restore_job(self, vm_list):
        """
        Submits a restore job with the given inputs

        Args:
            vm_list     (list):    VMs to restore

        """
        self.restore_job_id = self.full_vm_restore_obj.ali_cloud_full_vm_restore(
            vm_list,
            destination_client=self.restore_client,
            destination_proxy=self.restore_proxy,
            power_on=self.power_on_after_restore,
            overwrite_instance=self.unconditional_overwrite,
            in_place=self.full_vm_in_place,
            restore_prefix=self.vm_restore_prefix,
            instance_options=self._full_vm_restore_options
        )

        job_details = self.get_job_status(self.restore_job_id)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def full_vm_restore(self, vm_level=False):
        """
        Runs a full instance restore of Alibaba cloud instances

        Args:
            vm_level    (bool):     if the VM should be restored from the VM level

        """
        try:
            if self.restore_proxy_input is not None:
                self.restore_proxy = machine.Machine(self.restore_proxy_input, self.commcell)
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)

            proxy_info = self.hvobj.to_vm_object(self.restore_proxy)
            self.log.info("Collecting proxy disk count before restore for HotAdd validation")
            proxy_before_restore_disks_count = proxy_info.storage_disks()['TotalCount']
            self.log.info('disk count : %s ', str(proxy_before_restore_disks_count))
            self._full_vm_restore_options = {vm: dict() for vm in self._vms}
            self._set_instance_restore_options()

            if vm_level:
                for _vm in self._vms:
                    self._navigate_to_vm_restore(_vm)
                    self.select_restore_obj.select_full_vm_restore()
                    self._submit_restore_job([_vm])
            else:
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                self.vsa_sc_obj.restore()
                self.select_restore_obj.select_full_vm_restore()
                self._submit_restore_job(self.vms)

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = self.vm_restore_prefix + _vm
                self.vm_restore_validation(_vm, restore_vm)

            self.log.info("Collecting proxy disk count after restore for HotAdd validation")
            proxy_after_restore_disks_count = proxy_info.storage_disks()['TotalCount']
            self.log.info('disk count : %s ', str(proxy_after_restore_disks_count))
            try:
                assert proxy_before_restore_disks_count == proxy_after_restore_disks_count
                self.log.info('Hot Add validation successful')
            except:
                self.log.exception("HotAdd Validation failed")

        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore. %s", str(exp))
            raise exp


class NutanixAdminConsole(AdminConsoleVirtualServer):
    """
    Class for Nutanix related operations to be done in admin console
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initializes the Oracle Cloud related inputs

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the CS DB object

        """

        super(NutanixAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._full_vm_restore_options = None
        self.restore_options = {}
        self.restore_proxy_input = None
        self._restore_network = None
        self._storage_container = None

    @property
    def restore_network(self):
        """
        Returns the restore network name

        Returns:
            restore_network  (str)   --  the NIC for the restored VM

        """
        return self._restore_network

    @property
    def storage_container(self):
        """
        Returns the restore storage container

        Returns:
            storage_container  (str)   --  the storage container to restore the VM to

        """
        return self._storage_container

    @restore_network.setter
    def restore_network(self, value):
        """
                Sets the Restore NIC

                Args:
                    value   (str)    --  the NIC name

                """
        self._restore_network = value

    @storage_container.setter
    def storage_container(self, value):
        """
                Sets the storage container

                Args:
                    value   (str)    --  container name

                """
        self._storage_container = value

    def full_vm_restore(self):
        """
        Perform full VM restore for Nutanix AHV

        Raises:
            Exception:
                if full VM restore or validation fails

        """
        try:
            VirtualServerUtils.decorative_log("Performing Full VM Restore")
            if self.restore_proxy_input is not None:
                self.restore_proxy = self.restore_proxy_input

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj

            elif self.commcell.clients.has_client(self.restore_client):
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(self.restore_client)

            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            # self.hard_refresh()
            self.vsa_sc_obj.restore()
            self.select_restore_obj.select_full_vm_restore()

            if self.full_vm_in_place:
                self.vm_restore_prefix = None
                self.unconditional_overwrite = True

            self.restore_options = dict.fromkeys(self._vms, {})
            self._set_nutanixahv_vm_restore_options()

            self._submit_restore_job(self.vms)

            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Restore job failed. Please check the logs")

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = self.vm_restore_prefix + _vm
                self.log.info("sleeping 4 minutes for the vms to be up, before restore validation")
                time.sleep(240)
                self.vm_restore_validation(_vm, restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during Nutanix AHV Full VM restore. %s", str(exp))
            raise exp

    def _submit_restore_job(self, vm_list):

        self.restore_job_id = self.full_vm_restore_obj.nutanixahv_full_vm_restore(
            vm_list,
            destination_client=self.restore_client,
            destination_proxy=self.restore_proxy,
            power_on=self.power_on_after_restore,
            overwrite_instance=self.unconditional_overwrite,
            in_place=self.full_vm_in_place,
            instance_options=self.restore_options,
            restore_network=self.restore_network,
            storage_container=self.storage_container,
            restore_prefix=self.vm_restore_prefix
        )

        job_details = self.get_job_status(self.restore_job_id)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def _set_nutanixahv_vm_restore_options(self):

        for each_vm in self.vms:
            self.restore_options[each_vm]['full_vm_in_place'] = self.full_vm_in_place
            self.restore_options[each_vm]['restore_proxy'] = self.restore_proxy
            self.restore_options[each_vm]['overwrite'] = self.unconditional_overwrite
            if self.restore_network:
                self.restore_options[each_vm]['network'] = self.restore_network
            if self.storage_container:
                self.restore_options[each_vm]['storageContainer'] = self.storage_container


class AzureRMAdminConsole(AdminConsoleVirtualServer):
    """
    Azure RM class to perform AzureRM related adminconsole tasks
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize any Azure RM related variables

        Args:
            instance    (object):  object of the instance class

            driver      (object):  the browser object

            commcell    (object):  an instance of the commcell class

            csdb        (object): the cs DB object

        """
        super(AzureRMAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)

        self._full_vm_restore_options = {}
        self._resource_group = None
        self._storage_account = None
        self._region = None
        self._vm_size = None
        self._network_interface = None
        self._security_group = None
        self._create_public_ip = False
        self._managed_vm = None
        self._disk_type = None
        self._availability_zone = None
        self._disk_encryption_type = None
        self._vm_tags = None
        self._azure_key_vault = None
        self.new_vm = None
        self.azure_user_name = None
        self.azure_password = None
        self.extension_restore_policy = None

    @property
    def resource_group(self):
        """
        Returns the live resource_group

        Returns:
            resource_group     (str):    value of resource group

        """
        return self._resource_group

    @resource_group.setter
    def resource_group(self, value):
        """
        Sets the value of  resource_group

        Args:
            value   (str):  value for resource_group
        """
        self._resource_group = value

    @property
    def managed_vm(self):
        """
        Returns the live Managed VM value

        Returns:
            managed_     (bool): True / False to enable or disable managed_vm
        """
        if self._managed_vm is None:
            return True
        return self._managed_vm

    @managed_vm.setter
    def managed_vm(self, value):
        """
        Sets the  Managed VM value

        Args:
            value   (bool)  :  value for managed_v
        """
        self._managed_vm = value

    @property
    def create_public_ip(self):
        """
        Returns the live create public IP value

        Returns:
            create_public_ip     (bool): True / False to enable or disable Create Public IP
        """
        return self._create_public_ip

    @create_public_ip.setter
    def create_public_ip(self, value):
        """
        Sets the  create public IP value

        Args:
            value   (bool)  :  value for _create_public_ip
        """
        self._create_public_ip = value

    @property
    def disk_type(self):
        """
        Returns the disk type

        Returns:
            disk_type   (str): value of _disk_type
        """
        if self._disk_type is None:
            self._disk_type = "Original"

        return self._disk_type

    @disk_type.setter
    def disk_type(self, value):
        """
        Sets the disk type value

        Args:
            value   (str):  value for _disk_type
        """
        self._disk_type = value

    @property
    def storage_account(self):
        """
        Returns the live storage_account
        Returns:
            storage_account     (st):  value of storage_account

        """
        return self._storage_account

    @property
    def region(self):
        """
        Returns the live region
        Returns:
            region     (st):  value of region

        """
        return self._region

    @storage_account.setter
    def storage_account(self, value):
        """
        Sets the value of  storage_account

        Args:
            value   (str): value for storage_account
        """
        self._storage_account = value

    @region.setter
    def region(self, value):
        """
        Sets the value of  region

        Args:
            value   (str): value for region
        """
        self._region = value

    @property
    def vm_size(self):
        """
        Returns the live vmsize

        Returns:
            vmsize     (str):  value of vm_size

        """
        return self._vm_size

    @vm_size.setter
    def vm_size(self, value):
        """
        Sets the live vmsize

        Args:
            value   (str):  value for vmsize
        """
        self._vm_size = value

    @property
    def network_interface(self):
        """
        Returns the live network inerface

        Returns:
            network_interface     (bool):  True / False to enable or disable live recovery

        """
        if self._network_interface is None:
            self._network_interface = "--Auto Select--"

        return self._network_interface

    @network_interface.setter
    def network_interface(self, value):
        """
        Sets the live network inerface
        Args:
            value  (str): value for network_interface
        """
        self._network_interface = value

    @property
    def security_group(self):
        """
        Returns the live security_group

        """
        if self._security_group is None:
            self._security_group = "--Auto Select--"

        return self._security_group

    @security_group.setter
    def security_group(self, value):
        """
        Sets value of security_group
        Args:
            value   (str):  value for security_group
        """
        self._security_group = value

    @property
    def availability_zone(self):
        """
        Returns the live Availability Zone

        Returns:
            vmsize     (str):  value of availability_zone

        """
        if self._availability_zone is None:
            self._availability_zone = "Auto"

        return self._availability_zone

    @availability_zone.setter
    def availability_zone(self, value):
        """
        Sets the live Availability Zone

        Args:
            value   (str):  value for availability_zone
        """
        self._availability_zone = value

    @property
    def disk_encryption_type(self):
        """
        Returns the disk encryption type

        Returns:
            disk encryption type     (str):  encryption type

        """
        if not self._disk_encryption_type:
            self._disk_encryption_type = 'Original'

        return self._disk_encryption_type

    @disk_encryption_type.setter
    def disk_encryption_type(self, value):
        """
        Sets disk encryption type

        Args:
            value   (str):  encryption type
        """
        self._disk_encryption_type = value

    @property
    def vm_tags(self):
        """
        Returns the vm tags

        Returns:
            vm tags    (list):  vm tags

        """
        return self._vm_tags

    @vm_tags.setter
    def vm_tags(self, value):
        """
        Sets vm tags

        Args:
            value   (list):  vm tags
        """
        self._vm_tags = value

    @property
    def azure_key_vault(self):
        """
        Returns Azure key vault name

        Returns:
            azure_key_vault    (str):  Azure key vault for ADE

        """
        return self._azure_key_vault

    @azure_key_vault.setter
    def azure_key_vault(self, value):
        """
        Sets Azure key vault

        Args:
            value   (str):  Azure key vault for ADE
        """
        self._azure_key_vault = value

    def get_snapshot_rg(self):
        """
        Gets custom RG set on the VM Group

        Raises:
            Exception:
                if getting RG for snapshot from VM Group fails

        """
        try:
            VirtualServerUtils.decorative_log("Getting details from VM Group Settings")
            vm_group_details = self.vsa_sc_obj.azure_snapshot_settings(get_settings=True)

            if vm_group_details["Custom resource group for disk snapshots"].lower() != "default":
                snapshot_rg = vm_group_details["Custom resource group for disk snapshots"]

                self.log.info("Found Custom RG: {} from CC, checking value in DB".format(snapshot_rg))
                query = "select attrVal from APP_SubClientProp where attrName like '%VS Custom Snapshot " \
                        "Resource Group%' and componentNameId={}".format(self.subclient_obj.subclient_id)
                self.csdb.execute(query)

                if snapshot_rg != self.csdb.fetch_one_row()[0]:
                    raise Exception("Custom RG value set in CS DB: {} doesn't match with what shown in CC: {}"
                                    .format(self.csdb.fetch_one_row()[0], snapshot_rg))

                else:
                    self.log.info("Custom RG: {} is set correctly in DB".format(snapshot_rg))

                return snapshot_rg

            return None

        except Exception as exp:
            self.log.exception("Exception while Setting Custom Snapshot RG: %s", str(exp))
            raise exp

    def set_snapshot_rg(self):
        """
        Sets custom RG for azure backup snapshots

        Raises:
            Exception:
                if setting RG for snapshot fails

        """
        try:
            if self.snapshot_rg is not None:
                VirtualServerUtils.decorative_log("Setting custom RG for snapshot")
                self.vsa_sc_obj.azure_snapshot_settings(custom_snapshot_rg=self.snapshot_rg)

                self.log.info("Checking Custom RG set correctly in CS DB")
                query = "select attrVal from APP_SubClientProp where attrName like '%VS Custom Snapshot " \
                        "Resource Group%' and componentNameId={}".format(self.subclient_obj.subclient_id)

                self.csdb.execute(query)

                if not self.snapshot_rg == self.csdb.fetch_one_row()[0]:
                    self.log.exception("Custom RG value not set correctly in CS DB")

        except Exception as exp:
            self.log.exception("Exception while Setting Custom Snapshot RG: %s", str(exp))
            raise exp

    def _set_azure_vm_restore_options(self):
        """
                Sets the VM restore options for each VM to be restored

                Raises:
                    Exception:
                        if there is any exception in setting the restore options
        """

        try:
            _vm_list = []
            for _vm in self._vms:
                _vm_list.append(_vm)
                if (self.storage_account and self.resource_group) is None:
                    self.resource_group, self.storage_account, self.location = self.hvobj. \
                        compute_free_resources(_vm_list)
                if self.vm_size is None:
                    self.vm_size = self.hvobj.VMs[_vm].vm_size

                self._full_vm_restore_options[_vm]['resource_group'] = self.resource_group
                self._full_vm_restore_options[_vm]['storage_account'] = self.storage_account
                self._full_vm_restore_options[_vm]['vm_size'] = self.vm_size
                self._full_vm_restore_options[_vm]['security_group'] = self.security_group
                self._full_vm_restore_options[_vm]['network_interface'] = self.network_interface
                self._full_vm_restore_options[_vm]["availability_zone"] = self.availability_zone
                self._full_vm_restore_options[_vm]["create_public_ip"] = self.create_public_ip
                self._full_vm_restore_options[_vm]["disk_encryption_type"] = self.disk_encryption_type
                self._full_vm_restore_options[_vm]["vm_tags"] = self.vm_tags
                self._full_vm_restore_options[_vm]["extension_restore_policy"] = self.extension_restore_policy

                if self.conversion_restore and self.disk_encryption_type == "Original":
                    self._full_vm_restore_options[_vm]["disk_encryption_type"] = \
                        "(Default) Encryption at-rest with a platform-managed key"

                if not self.conversion_restore and self.azure_key_vault is None and self.hvobj.VMs[_vm].is_encrypted:
                    self._full_vm_restore_options[_vm]['azure_key_vault'] = self.hvobj.VMs[_vm].encryption_info[
                        "keyVaultName"]
                elif not self.conversion_restore and self.hvobj.VMs[_vm].is_encrypted and self.azure_key_vault:
                    self._full_vm_restore_options[_vm]['azure_key_vault'] = self.azure_key_vault
                if self._managed_vm is not None:
                    self._full_vm_restore_options[_vm]['managed_vm'] = self.managed_vm
                elif self.conversion_restore:
                    self._full_vm_restore_options[_vm]['managed_vm'] = True
                else:
                    self._full_vm_restore_options[_vm]['managed_vm'] = self.hvobj.VMs[_vm].managed_disk
                if self.region or not self.full_vm_in_place:
                    self._full_vm_restore_options[_vm]['region'] = self.region
                elif not self.conversion_restore:
                    self._full_vm_restore_options[_vm]['region'] = self.hvobj.VMs[_vm].region
                self._full_vm_restore_options[_vm]['disk_option'] = self.disk_type

        except Exception as exp:
            self.log.exception("Exception occurred during setting restore options")
            raise exp

    def _submit_restore_job(self, vm_list):
        """
            Submits a restore job with the given inputs
            Args:
                vm_list     (list):    VMs to restore

        """

        self.configure_restore_settings()
        self.select_restore_obj.select_full_vm_restore()
        self.restore_job_id = self.full_vm_restore_obj.azure_full_vm_restore(
            vm_list,
            self.restore_proxy,
            self.restore_client,
            self.full_vm_in_place,
            self._full_vm_restore_options,
            self.extension_restore_policy,
            self._create_public_ip,
            self.unconditional_overwrite,
            self.power_on_after_restore,
            self.managed_vm,
            restore_prefix=self.vm_restore_prefix
        )

        job_details = self.get_job_status(self.restore_job_id,
                                          expected_state=['completed', 'completed w/ one or more errors'])
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def full_vm_restore(self, vm_level=False):
        """
                Performs full VM restore for a Azure RM

                Raises:
                    Exception:
                        if full VM restore or validation fails

                """
        try:
            self.log.info("*" * 10 + "Performing full VM restore" + "*" * 10)

            if self._restore_proxy is None and self._co_ordinator is not None:
                self.restore_proxy = self._co_ordinator
            if self._restore_client is None or self.full_vm_in_place:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)

            self._full_vm_restore_options = {vm: {} for vm in self._vms}
            self._set_azure_vm_restore_options()

            self.vm_restore_prefix = 'DEL'
            if not self.conversion_restore:
                if vm_level:
                    for _vm in self._vms:
                        self._navigate_to_vm_restore(_vm)
                        self._submit_restore_job([_vm])
                elif self.restore_from_job:
                    """ Restores from given job"""
                    self.navigator.navigate_to_jobs()
                    self.job_obj.view_jobs_of_last_3_months()
                    self.job_obj.job_restore(self.restore_from_job, search=True)
                else:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
            self._submit_restore_job(self._vms)

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = self.vm_restore_prefix + _vm
                if not self.azure_cross_region_restore and not self.conversion_restore:
                    self.vm_restore_validation(_vm, restore_vm, self._full_vm_restore_options[_vm])
                if self.azure_cross_region_restore:
                    location = self.hvobj.VMs[_vm].get_vm_location(self.resource_group, restore_vm)
                    if location == ''.join(self.region.split()).lower():
                        self.log.info("Region validation successful. Location = %s" % location)
                    else:
                        self.log.info(
                            "Region validation failed because input region = %s and restored VM region = %s" % (
                                ''.join(self.region.split()).lower(), location))

        except Exception as exp:
            self.log.exception("Exception occurred during Azure Full VM restore. %s", str(exp))
            raise exp

    def attach_disk_restore(self, attach_disks_to, vm_level=False):
        """
           Performs attach disk restore for an Azure RM
           Args:

                attach_disks_to (str) : Disks has to be attached to existing Virtual Machine or new Virtual Machine or same Virtual Machine

                vm_level      (bool)       :  if the restore should be initiated from VM level

           Raises:
               Exception:
                   if attach disk restore or validation fails
        """
        _destination_vm_list = []
        _total_disk_attached_list = []
        _after_disk_list = []

        try:
            self.log.info("*" * 10 + "Performing attach disk operation" + "*" * 10)

            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator
            if self._restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.commcell.clients.has_client(self.restore_client):
                    raise Exception("The destination client is not a client in the Commserve")
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)

            for vm_name in self._vms:
                if self.hvobj.VMs[vm_name].is_encrypted:
                    continue

                _disks = []
                _disks_to_attached = self.hvobj.VMs[vm_name].get_data_disk_info()

                # Prev attached data disk might be chosen to restore, this will fail as disk not in backup
                _disks_to_attached = [disk for disk in _disks_to_attached if
                                      not (disk['name'] in _total_disk_attached_list)]

                if not _disks_to_attached:
                    continue

                if not vm_level:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
                else:
                    self._navigate_to_vm_restore(vm_name)
                self.configure_restore_settings()
                self.select_restore_obj.select_disk_restore()

                for disk in _disks_to_attached:
                    _disks.append(disk["name"])
                    _total_disk_attached_list.append((self.vm_restore_prefix + disk["name"]).lower())
                if attach_disks_to == 'Other virtual machine':
                    _destination_vm_list.append(self.agentless_vm)
                    _destination_vm_disk_list = self.restore_destination_client.VMs[self.agentless_vm]. \
                        get_data_disk_info()

                    if not (self.storage_account and self.resource_group and self.region):
                        self.resource_group, self.storage_account, self.region = self.restore_destination_client. \
                            compute_free_resources(_destination_vm_list)

                    azure_attach_disk_options = {
                        'virtual_machine': vm_name,
                        'disks': _disks,
                        'attach_disks_to': attach_disks_to,
                        'destination_server': self.restore_client,
                        'destination_proxy': self.restore_proxy,
                        'storage_account': self.storage_account,
                        'disk_name': self.vm_restore_prefix,
                        'destination_vm': self.agentless_vm
                    }
                    self.restore_job_id = self.disk_level_restore_obj.azure_attach_disk(azure_attach_disk_options)
                elif attach_disks_to == 'My virtual machine':
                    _destination_vm_disk_list = self.restore_destination_client.VMs[vm_name]. \
                        get_data_disk_info()
                    azure_attach_disk_options = {
                        'virtual_machine': vm_name,
                        'disks': _disks,
                        'attach_disks_to': attach_disks_to,
                        'disk_name': self.vm_restore_prefix
                    }
                    self.restore_job_id = self.disk_level_restore_obj.azure_attach_disk(azure_attach_disk_options)
                else:
                    self.inst_display_name = "Attach-Disk-Restore-" + vm_name
                    _destination_vm_list.append(self.inst_display_name)
                    _before_disk_list = self.hvobj.VMs[vm_name].get_data_disk_info()
                    azure_attach_disk_options = {
                        'virtual_machine': vm_name,
                        'disks': _disks,
                        'attach_disks_to': attach_disks_to,
                        'destination_server': self.restore_client,
                        'destination_proxy': self.restore_proxy,
                        'resource_group': self.resource_group,
                        'storage_account': self.storage_account,
                        'vm_display_name': self.inst_display_name,
                        'region': self.region,
                        'availability_zone': self.availability_zone,
                        'security_group': self.security_group,
                        'image_option': self.image_option,
                        'visibility_type': self.visibility_type,
                        'publisher_type': self.publisher_type,
                        'offer_type': self.offer_type,
                        'plan_type': self.plan_type,
                        'version': self.version,
                        'image': self.private_image,
                        'username': self.azure_user_name,
                        'password': self.azure_password,
                        'power_on': self.power_on_after_restore
                    }
                    self.restore_job_id = self.disk_level_restore_obj.azure_attach_disk(azure_attach_disk_options)
                job_details = self.get_job_status(self.restore_job_id)

                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                if attach_disks_to == "New virtual machine":
                    if job_details:
                        self.new_vm = self.hvobj.to_vm_object(self.inst_display_name)
                        after_disk_info = self.new_vm.get_data_disk_info()

                        for each_disk in after_disk_info:
                            _after_disk_list.append(each_disk["name"])

                        if len(_after_disk_list) == len(_before_disk_list):
                            self.log.info(
                                "Successfully validated the disks for the Attach disk restore to the new Virtual Machine")
                            self.new_vm.delete_vm()
                            self.log.info("Terminated the Restored VM")
                        else:
                            raise Exception("Validation Failed while comparing the length of the disks")
                elif attach_disks_to == 'My virtual machine':
                    if job_details:
                        after_disk_info = self.restore_destination_client.VMs[vm_name]. \
                            get_data_disk_info()
                        for each_disk in after_disk_info:
                            _after_disk_list.append(each_disk["name"])

                        self.attach_disks_validation(_destination_vm_disk_list, _total_disk_attached_list,
                                                     _after_disk_list)
                else:
                    if job_details:
                        after_disk_info = self.restore_destination_client.VMs[self.agentless_vm]. \
                            get_data_disk_info()
                        for each_disk in after_disk_info:
                            _after_disk_list.append(each_disk["name"])

                self.attach_disks_validation(_destination_vm_disk_list, _total_disk_attached_list,
                                            _after_disk_list)
        except Exception as exp:
            self.log.exception("Exception occurred in Attach disk operation %s", str(exp))
            raise exp

    def attach_disks_validation(self, before_dest_data_disk, attached_disk_info,
                                after_dest_disk):
        """
        Performs a attach disk  restore Validation
        Args:
            before_dest_data_disk    (list):     list of datadisks before attach disk restore

            attached_disk_info       (list):     disks attached

            after_dest_disk          (list):      list of data disks after attach disk restore

        """
        try:
            before_length = len(before_dest_data_disk)
            self.log.info("No of disks before restore", before_length)
            after_length = len(after_dest_disk)
            self.log.info("No of disks after restore", after_length)
            attached_length = len(attached_disk_info)
            self.log.info("total no of disks attached", attached_length)
            if before_length + attached_length != after_length:
                raise Exception("No of disks attached validation is successfull")

            for attached_name in attached_disk_info:
                if not attached_name in attached_disk_info:
                    raise Exception("Attach Disk Restore validation failed")
            self.log.info("Disk validation is succesfull")
        except Exception as exp:
            self.log.exception("Exception in disks validation %s", str(exp))
            raise exp


class AmazonAdminConsole(AdminConsoleVirtualServer):
    """
    Amazon class to perform Amazon related adminconsole tasks
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize any Amazon related variables

        Args:
            instance        (object)    --  the instance class object

            driver          (object)    --  the browser driver object

            commcell        (object)    --  the commcell object

            csdb            (object)    --  the commserve DB object

        """

        super(AmazonAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self.new_instance = None
        self._full_vm_restore_options = {}
        self.display_destination_server = None
        self.vol_restore_prefix = 'Restored_'
        self.vm_restore_prefix = 'Del'
        self._ami = None
        self._availability_zone = None
        self._auto_select_instance_type = True
        self._ec2_instance_type = None
        self._instance_boot_mode = None
        self._network = None
        self._vpc = None
        self._subnet = None
        self._region = None
        self._auto_select_security_grp = None
        self._security_group = None
        self._existing_instance = None
        self._volumetype = None
        self._volumeEdit = False
        self._iops = None
        self._throughput = None
        self._encryptionKey = None
        self._encryptionKeyArn = None
        self._overwrite_vm = True
        self._destination_region = None
        self._transport_mode = 'Automatic (default)'
        self.disks_to_be_attached = []
        self._restore_source_network = False
        self._aws_vpc_recovery_validation = False

    @property
    def disks_to_be_attached(self):
        """
        Returns the disk names which needs to be attached.

        Returns:
             Disks (str)   --  the name of the Disks

        """
        return self._disks_to_be_attached

    @disks_to_be_attached.setter
    def disks_to_be_attached(self, value):
        """
        Sets the Disk name

        Args:
            value   (str)   --  the name of the Disk name

        """
        self._disks_to_be_attached = value

    @property
    def existing_instance(self):
        """
        Returns the existing instance name

        Returns:
            existing_instance  (str)   --  the existing instance name

        """
        return self._existing_instance

    @existing_instance.setter
    def existing_instance(self, value):
        """
        Sets the existing instance name

        Args:
            value   (str)   --  the existing instance name

        """
        self._existing_instance = value

    @property
    def region(self):
        """
        Returns the region name

        Returns:
            region  (str)   --  the name of the region
        """
        return self._region

    @region.setter
    def region(self, value):
        """
        Sets the security group name

        Args:
            value   (str)   --  the name of the region

        """
        self._region = value

    @property
    def vpc(self):
        """
        Returns the vpc name

        Returns:
            vpc  (str)   --  the name and id of the vpc
        """
        return self._vpc

    @vpc.setter
    def vpc(self, value):
        """
        Sets the vpc name

        Args:
            value   (str)   --  the name and id of the vpc

        """
        self._vpc = value

    @property
    def subnet(self):
        """
        Returns the subnet name

        Returns:
            subnet  (str)   --  the subnet name and ID
        """
        return self._subnet

    @subnet.setter
    def subnet(self, value):
        """
        Sets the subnet value

        Args:
            value   (str)   --  the subnet name and id

        """
        self._subnet = value

    @property
    def volumeEdit(self):
        """
        Returns the volumeEdit

        Returns:
            volumeEdit  (bool)   --  if True Validates Volume Options with the input / False validates with the source
        """
        return self._volumeEdit

    @volumeEdit.setter
    def volumeEdit(self, value):
        """
        Sets the volumeEdit

        Args:
            value   (bool)   --  if True Validates Volume Options with the input / False validates with the source

        """
        self._volumeEdit = value

    @property
    def volumetype(self):
        """
        Returns the volumetype

        Returns:
            region  (str)   --  the name of the volumetype
        """
        return self._volumetype

    @volumetype.setter
    def volumetype(self, value):
        """
        Sets the volumetype

        Args:
            value   (str)   --  the name of the volumetype

        """
        if self.volumeEdit:
            self.restore_validation_options["volumetype"] = value
        self._volumetype = value

    @property
    def iops(self):
        """
        Returns the iops

        Returns:
            iops  (str)   --  the name of the iops
        """
        return self._iops

    @iops.setter
    def iops(self, value):
        """
        Sets the iops

        Args:
            value   (str)   --  the value of iops

        """
        if self.volumeEdit:
            self.restore_validation_options["iops"] = value
        self._iops = value

    @property
    def source(self):
        """
        Returns the source name

        Returns:
            source  (str)   --  the name of the source

        """
        return self._source

    @source.setter
    def source(self, value):
        """
        Sets the source name

        Args:
            value    (str)   --  the name of the source

        """
        self._source = value

    @property
    def throughput(self):
        """
        Returns the throughput

        Returns:
            region  (str)   --  the value of throughput
        """
        return self._throughput

    @throughput.setter
    def throughput(self, value):
        """
        Sets the throughput

        Args:
            value   (str)   --  the value of the throughput

        """
        if self.volumeEdit:
            self.restore_validation_options["throughput"] = value
        self._throughput = value

    @property
    def encryptionKey(self):
        """
        Returns the encryptionKey

        Returns:
            region  (str)   --  the name of the encryptionKey
        """
        return self._encryptionKey

    @encryptionKey.setter
    def encryptionKey(self, value):
        """
        Sets the encryptionKey

        Args:
            value   (str)   --  the name of the encryptionKey

        """
        if self.volumeEdit:
            self.restore_validation_options["encryptionKey"] = value
        self._encryptionKey = value

    @property
    def security_group(self):
        """
        Returns the security group name

        Returns:
            security_group  (str)   --  the name of the security group

        """
        return self._security_group

    @security_group.setter
    def security_group(self, value):
        """
        Sets the security group name

        Args:
            value   (str)   --  the name of the security group

        """
        self._security_group = value

    @property
    def auto_select_security_grp(self):
        """
        Returns the auto_select_security_grp's value

        Returns:
            auto_select_security_grp  (bool)   --  if security group should be auto selected

        """
        return self._auto_select_security_grp

    @auto_select_security_grp.setter
    def auto_select_security_grp(self, value):
        """
        Sets the auto_select_security_grp's value

        Args:
            value   (str)   --  if security group should be auto selected

        """
        self._auto_select_security_grp = value

    @property
    def network(self):
        """
        Returns the network

        Returns:
            network  (str)   --  the name of the network

        """
        return self._network

    @network.setter
    def network(self, value):
        """
        Sets the network name

        Args:
            value   (str)   --  the name of the network

        """
        self._network = value

    @property
    def ec2_instance_type(self):
        """
        Returns the instance type

        Returns:
            ec2_instance_type  (str)   --  the instance type

        """
        return self._ec2_instance_type

    @ec2_instance_type.setter
    def ec2_instance_type(self, value):
        """
        Sets the ec2_instance_type name

        Args:
            value   (str)   --  the instance type

        """
        self._ec2_instance_type = value

    @property
    def instance_boot_mode(self):
        """
        Returns the Instance boot mode

        Returns:
            instance boot mode

        """
        return self._instance_boot_mode

    @instance_boot_mode.setter
    def instance_boot_mode(self, value):
        """
        Sets the Instance boot mode name

        Args:
            value   (str)   --  Instance boot mode value

        """
        self._instance_boot_mode = value

    @property
    def vm_tags(self):
        """
        Returns the vm tags

        Returns:
            tags for the instance

        """
        return self._vm_tags

    @vm_tags.setter
    def vm_tags(self, value):
        """
        Sets the vm tags

        Args:
            value   (str)   -- Instance tags

        """
        self._vm_tags = value

    @property
    def auto_select_instance_type(self):
        """
        Returns the auto_select_instance_type's value

        Returns:
            auto_select_instance_type  (bool)   --  if instance type should be auto selected

        """
        return self._auto_select_instance_type

    @auto_select_instance_type.setter
    def auto_select_instance_type(self, value):
        """
        Sets the auto_select_instance_type's value

        Args:
            value   (bool)   --  if instance type should be auto selected

        """
        self._auto_select_instance_type = value

    @property
    def availability_zone(self):
        """
        Returns the availability_zone

        Returns:
            availability_zone  (str)   --  the name of the availability zone

        """
        return self._availability_zone

    @availability_zone.setter
    def availability_zone(self, value):
        """
        Sets the availability_zone name

        Args:
            value   (str)   --  the name of the availability zone

        """
        self._availability_zone = value

    @property
    def ami(self):
        """
        Returns the ami name

        Returns:
            ami  (str)   --  the name of the ami

        """
        return self._ami

    @ami.setter
    def ami(self, value):
        """
        Sets the ami name

        Args:
            value   (str)   --  the name of the ami

        """
        self._ami = value

    @property
    def vol_restore_prefix(self):
        """
        Returns the prefix to be attached to the restore VM name

        Returns:
            vm_restore_prefix  (str)   --  the prefix to tbe attached to the restore VM name

        """
        return self._vol_restore_prefix

    @vol_restore_prefix.setter
    def vol_restore_prefix(self, value):
        """
        Sets the prefix to be attached to the restore VM name

        Args:
            value   (str)    --  the prefix to be attached to the restore VM name

        """
        self._vol_restore_prefix = value

    @property
    def encryptionKeyArn(self):
        """
        Returns the encryptionKeyArn

        Returns:
            encryptionKeyArn  (str)   --  the Arn of the encryptionKey
        """
        return self._encryptionKeyArn

    @encryptionKeyArn.setter
    def encryptionKeyArn(self, value):
        """
        Sets the encryptionKeyArn

        Args:
            value   (str)   --  the Arn of the encryptionKey

        """
        if self.volumeEdit:
            self.restore_validation_options["encryptionKeyArn"] = value
        self._encryptionKeyArn = value

    @property
    def unconditional_overwrite(self):
        """
        Returns the unconditional overwrite variable

        Returns:
            overwrite_vm  (bool)   --  True / False to overwrite the VM during restore

        """
        return self._overwrite_vm

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        Sets the unconditional overwrite variable

        Args:
            value   (bool)  --  True / False to overwrite the VM during restore

        """
        self._overwrite_vm = value

    @property
    def destination_region(self):
        """
        Returns the destination region name

        Returns:
            region  (str)   --  the destination region name
        """
        return self._destination_region

    @destination_region.setter
    def destination_region(self, value):
        """
        Sets the destination region

        Args:
            value   (str)   --  the destination region name

        """
        self._destination_region = value

    @property
    def transport_mode(self):
        """
        Returns the transport mode to be used for restore

        Returns:
            _transport_mode    (str)   --  the transport mode to be used for restore
                    default:    Auto

        """
        return self._transport_mode

    @transport_mode.setter
    def transport_mode(self, value):
        """
        Sets the transport mode to be used for restore

        Args:
            value   (str)    --  the transport mode to be used

        """
        self._transport_mode = value

    @property
    def restore_source_network(self):
        """
        Returns whether source network is to be used for restore

        Returns:
                value   (bool)  --  True / False to restore source vm's network during restore

        """
        return self._restore_source_network

    @restore_source_network.setter
    def restore_source_network(self, value):
        """
        Sets whether source network is to be used for restore

        Args:
            value   (bool)    --  True / False to use source vm network during restore

        """
        self._restore_source_network = value

    @property
    def aws_vpc_recovery_validation(self):
        """
        Returns whether the recovered vpc, subnet, security groups and nics are to be validated or not

        Returns:
                value   (bool)  --  True / False to validate restored network entities

        """
        return self._aws_vpc_recovery_validation

    @aws_vpc_recovery_validation.setter
    def aws_vpc_recovery_validation(self, value):
        """
        Sets whether restored network is to be validated or not

        Args:
            value   (bool)    --  True / False to validate restored network entities

        """
        self._aws_vpc_recovery_validation = value

    def _set_aws_vm_restore_options(self):
        """
                Sets the VM restore options for each VM to be restored

                Raises:
                    Exception:
                        if there is any exception in setting the restore options
        """

        try:
            if self.conversion_restore:
                if self.availability_zone is None:
                    self.availability_zone = self.coordinator_vm_obj.availability_zone
                if self.region is None:
                    self.region = self.coordinator_vm_obj.aws_region
                if self.volumetype is None:
                    self.volumetype = "gp3"
                if self.encryptionKey is None:
                    self.encryptionKey = "Auto"
                if self.iops is None:
                    self.iops = None
                if self.throughput is None:
                    self.throughput = None
                if self.vpc is None:
                    self.vpc = self.coordinator_vm_obj.vpc
                if self.subnet is None:
                    self.subnet = self.coordinator_vm_obj.subnet
                if self.network is None:
                    self.network = "New Network Interface"
            self._full_vm_restore_options = dict((_all_vms, dict()) for _all_vms in self._vms)
            for _vm in self._vms:
                if self.availability_zone is None:
                    self.availability_zone = self.hvobj.VMs[_vm].availability_zone
                if self.security_group is None:
                    self.security_group = "--Auto Select--"
                if self.network is None:
                    self.network = "New Network Interface"
                if self.region is None:
                    self.region = self.hvobj.VMs[_vm].aws_region
                if self.volumeEdit is None:
                    self.volumeEdit = False
                if self.volumetype is None:
                    self.volumetype = None
                if self.iops is None:
                    self.iops = None
                if self.throughput is None:
                    self.throughput = None
                if self.encryptionKey is None:
                    self.encryptionKey = None
                    self.encryptionKeyArn = None
                if self.ec2_instance_type is None:
                    self.ec2_instance_type = "Automatic"
                if self.vpc is None:
                    self.vpc = self.hvobj.VMs[_vm].vpc
                if self.subnet is None:
                    self.subnet = self.hvobj.VMs[_vm].subnet
                self._full_vm_restore_options[_vm]['Instancetype'] = self.ec2_instance_type
                self._full_vm_restore_options[_vm]['availability_zone'] = self.availability_zone
                self._full_vm_restore_options[_vm]['encryptionKey'] = self.encryptionKey
                self._full_vm_restore_options[_vm]['encryptionKeyArn'] = self.encryptionKeyArn
                self._full_vm_restore_options[_vm]['volumetype'] = self.volumetype
                self._full_vm_restore_options[_vm]['security_group'] = self.security_group
                self._full_vm_restore_options[_vm]['network_interface'] = self.network
                self._full_vm_restore_options[_vm]['Instancename'] = "Del" + _vm.replace(' ', '_')
                self._full_vm_restore_options[_vm]['region'] = self.region
                self._full_vm_restore_options[_vm]['vpc'] = self.vpc
                self._full_vm_restore_options[_vm]['subnet'] = self.subnet
                self._full_vm_restore_options[_vm]['iops'] = self.iops
                self._full_vm_restore_options[_vm]['throughput'] = self.throughput
                self._full_vm_restore_options[_vm]['volumeEdit'] = self.volumeEdit
                self._full_vm_restore_options[_vm]['restore_source_network'] = self.restore_source_network
                self._full_vm_restore_options[_vm]['aws_vpc_recovery_validation'] = self.aws_vpc_recovery_validation
                if self.conversion_restore and \
                        self.source_hvobj.instance_type == hypervisor_type.VIRTUAL_CENTER.value.lower():
                    if not self.source_hvobj.VMs[_vm].guest_credentials:
                        self.source_hvobj.VMs[_vm].authenticate_vm_session()
                        self._full_vm_restore_options[_vm]["ip"] = self.source_hvobj.VMs[
                            _vm].ip
                        self._full_vm_restore_options[_vm]["username"] = self.source_hvobj.VMs[
                            _vm].guest_credentials.username
                        self._full_vm_restore_options[_vm]["password"] = self.source_hvobj.VMs[
                            _vm].guest_credentials.password

        except Exception as exp:
            self.log.exception("Exception occurred during setting restore options")
            raise exp

    def attach_disk_restore(self, attach_vol_to, vm_level=False):
        """
        Attach disk restore

        Args:
            attach_vol_to (str) : Disk has to be attached to existing instance or new instance or same instance

            vm_level      (bool)       :  if the restore should be initiated from VM level

        Raises:
            Exception:
                if the Attach disk restore or validation fails
        """
        _destination_vm_list = []
        _after_disk_list = []
        _before_disk_list = []

        try:
            self.log.info("*" * 10 + "Performing disk level restore" + "*" * 10)
            _destination_vm_list.append(self._vms)

            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator
            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.commcell.clients.has_client(self.restore_client):
                    raise Exception("The destination client is not a client in the Commserve")
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(self.restore_client)
            for _vm in self._vms:
                _destination_vm_disk_list = self.restore_destination_client.VMs[_vm].disk_list
                if len(self.disks_to_be_attached) == 0:
                    # self.attach_to_disk is the no of disks to be attached to the instance which is given from the tc_inputs
                    self.disks_to_be_attached = self.restore_destination_client.VMs[_vm].disk_list
                elif len(self.disks_to_be_attached) > 1:
                    self.disks_to_be_attached = self.disks_to_be_attached.split(',')
                disks_to_be_attached = self.disks_to_be_attached
                disks_remaining = []
                # Creating a list of remaining disks after selection of the disk which we need to restore
                for disk in _destination_vm_disk_list:
                    if not (disk in disks_to_be_attached):
                        disks_remaining.append(disk)
                # removing the disks which are selected to restore
                for disk in disks_remaining:
                    if disk in _destination_vm_disk_list:
                        _destination_vm_disk_list.remove(disk)
                if not disks_to_be_attached:
                    continue
                if not vm_level:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
                else:
                    self._navigate_to_vm_restore(_vm)
                self.configure_restore_settings()
                self.select_restore_obj.select_disk_restore()
                _before_disk_list = self.restore_destination_client.VMs[_vm].disk_list
                if attach_vol_to == 'Other Instance':
                    if self.existing_instance is None:
                        raise Exception("Restore to Other Instance is not given by user")
                    self.restore_job_id = self.disk_level_restore_obj.aws_attach_disk_restore(
                        _vm,
                        disks_to_be_attached,
                        attach_vol_to,
                        self.hypervisor,
                        self.restore_client,
                        self.existing_instance,
                        self.vm_restore_prefix,
                        self.availability_zone
                    )
                elif attach_vol_to == 'My Instance':
                    self.restore_job_id = self.disk_level_restore_obj.aws_attach_disk_restore(
                        _vm,
                        disks_to_be_attached,
                        attach_vol_to,
                        self.hypervisor,
                        self.restore_client,
                        self.existing_instance,
                        self.vm_restore_prefix
                    )
                else:
                    if self.ami is None:
                        raise Exception("Ami is mandatory for new instance restore")
                    inst_display_name = self.vm_restore_prefix + _vm
                    self.restore_job_id = self.disk_level_restore_obj.aws_attach_disk_restore(
                        _vm, disks_to_be_attached,
                        attach_vol_to,
                        self.restore_client,
                        self.restore_proxy,
                        vol_prefix=self.vol_restore_prefix,
                        power_on=self.power_on_after_restore,
                        overwrite=self.unconditional_overwrite,
                        inst_display_name=inst_display_name,
                        ami=self.ami,
                        available_zone=self.availability_zone,
                        auto_select_instance_type=self.auto_select_instance_type,
                        ins_type=self.ec2_instance_type,
                        network=self.network,
                        auto_select_security_grp=self.auto_select_security_grp,
                        security_group=self.security_group)
                job_details = self.get_job_status(self.restore_job_id)
                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")
                if attach_vol_to == "New Instance":
                    self.new_instance = self.hvobj.to_vm_object(inst_display_name)
                    _after_disk_list = self.new_instance.disk_list
                    if len(_after_disk_list) == len(_before_disk_list):
                        self.log.info(
                            "Successfully validated the disks for the Attach disk restore to the new instance")
                        self.new_instance.delete_vm()
                        self.log.info("Terminated the Restored VM")
                    else:
                        raise Exception("Validation Failed while comparing the length of the disks")
                elif attach_vol_to == 'My Instance':
                    _after_disk_list = self.restore_destination_client.VMs[_vm].disk_list
                    if len(_before_disk_list) + 1 == len(_after_disk_list):
                        self.log.info(
                            "Successfully validated the disks from the Attach disk restore to the new instance")
                    else:
                        raise Exception("Validation Failed while comparing the disk names")
                else:
                    self.other_instance = self.hvobj.to_vm_object(self.existing_instance)
                    _after_disk_list = self.other_instance.disk_list
                    if(len(_after_disk_list) == 4):
                        self.log.info(
                            "Successfully validated the disks from the Attach disk restore to the new instance")
                    else:
                        raise Exception("Validation Failed while comparing the disk names")
        except Exception as exp:
            self.log.exception("Exception occurred during Attach disk restore. %s", str(exp))
            raise exp

    def attach_disk_restore_aws_to_azure(self, attach_disks_to,vsa_obj_azure, vm_level = False):
        """
           Performs attach disk restore for AWS VM to Azure VM

           Raises:
               Exception:
                   if attach disk restore or validation fails
        """
        _destination_vm_list = []
        _total_disk_attached_list = []
        _after_disk_list = []

        try:
            self.log.info("*" * 10 + "Performing attach disk operation" + "*" * 10)
            self.restore_obj = vsa_obj_azure

            if self._restore_proxy is None:
                self.restore_proxy = "Automatic"

            if not self.commcell.clients.has_client(self.restore_client):
                raise Exception("The destination client is not a client in the Commserve")
            if self.restore_obj.restore_hvobj is None:
                self.restore_obj.restore_hvobj, \
                    self._restore_instance_type = self.restore_obj._create_hypervisor_object(
                    self.restore_client)

            for _vm in self._vms:
                _destination_vm_disk_list = self.hvobj.VMs[_vm].disk_list
                if len(self.disks_to_be_attached) == 0:
                    # self.attach_to_disk is the no of disks to be attached to the instance which is given from the tc_inputs
                    self.disks_to_be_attached = self.hvobj.VMs[_vm].disk_list
                elif len(self.disks_to_be_attached) > 1:
                    self.disks_to_be_attached = self.disks_to_be_attached.split(',')
                disks_to_be_attached = self.disks_to_be_attached
                disks_remaining = []

                for disk in _destination_vm_disk_list:
                    if not (disk in disks_to_be_attached):
                        disks_remaining.append(disk)
                # removing the disks which are selected to restore
                for disk in disks_remaining:
                    if disk in _destination_vm_disk_list:
                        _destination_vm_disk_list.remove(disk)
                if not disks_to_be_attached:
                    continue
                if not vm_level:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()

                else:
                    self._navigate_to_vm_restore(_vm)
                self.configure_restore_settings()
                self.select_restore_obj.select_disk_restore()

                _before_disk_list = self.hvobj.VMs[_vm].disk_list

                self.inst_display_name = "Attach-Disk-Restore-" + _vm
                aws_to_azure_attach_disk_options = {
                    'virtual_machine': _vm,
                    'disks': disks_to_be_attached,
                    'attach_disks_to': attach_disks_to,
                    'destination_server': self.restore_client,
                    'destination_proxy': self.restore_proxy,
                    'resource_group': self.resource_group,
                    'storage_account': self.storage_account,
                    'vm_display_name': self.inst_display_name,
                    'region': self.destination_region,
                    'availability_zone': self.availability_zone,
                    'security_group': self.security_group,
                    'image_option': self.image_option,
                    'visibility_type': self.visibility_type,
                    'publisher_type': self.publisher_type,
                    'offer_type': self.offer_type,
                    'plan_type': self.plan_type,
                    'version': self.version,
                    'image': self.private_image,
                    'username': self.azure_user_name,
                    'password': self.azure_password,
                    'power_on': self.power_on_after_restore,
                    'restore_as' : self.restore_as
                }
                self.restore_job_id = self.disk_level_restore_obj.azure_attach_disk(aws_to_azure_attach_disk_options)
                job_details = self.get_job_status(self.restore_job_id)

                if not job_details:
                    raise Exception("Restore job failed. Please check the logs")

                if job_details:
                    self.new_vm = self.restore_obj.restore_hvobj.to_vm_object(self.inst_display_name)
                    _after_disk_list = self.new_vm.disk_list

                    if len(_after_disk_list)-1 == len(_before_disk_list):
                        self.log.info(
                            "Successfully validated the disks for the Attach disk restore to the new Azure Virtual Machine")
                        self.new_vm.delete_vm()
                        self.log.info("Terminated the Restored VM")
                    else:
                        raise Exception("Validation Failed while comparing the length of the disks")
        except Exception as exp:
            self.log.exception("Exception occurred in Attach disk operation %s", str(exp))
            raise exp

    def _submit_restore_job(self, vms_list, destination_server):
        """
        submit the restore job and track the jobs
        Args:
            vms_list (str/list) : vms to be restored
        """
        self.restore_job_id = self.full_vm_restore_obj.amazon_full_vm_restore(vms_list,
                                                                              self._full_vm_restore_options,
                                                                              self.full_vm_in_place,
                                                                              restore_as=hypervisor_type.AMAZON_AWS.value,
                                                                              proxy=self.restore_proxy,
                                                                              destination_server=destination_server,
                                                                              transport_mode=self.transport_mode,
                                                                              power_on=self.power_on_after_restore,
                                                                              over_write=self.unconditional_overwrite)
        job_details = self.get_job_status(self.restore_job_id)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def full_vm_restore(self, vm_level=False):
        """
        Full vm restore

        Args:

            vm_level      (bool)       :  if the restore is vm level or for subclient

        Raises:
            Exception:
                if the full vm restore or validation fails
        """
        try:
            self.log.info("Restoring the Amazon Instance")
            if self._restore_proxy is None and self._co_ordinator is not None:
                self.restore_proxy = self._co_ordinator

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(
                        self.restore_client)
            self._set_aws_vm_restore_options()
            destination_server = self.display_destination_server if self.display_destination_server else self.restore_client

            if vm_level:
                for _vm in self._vms:
                    self._navigate_to_vm_restore(_vm)
                    self.configure_restore_settings()
                    self.select_restore_obj.select_full_vm_restore()
                    self._submit_restore_job([_vm], destination_server)
            else:
                if not self.conversion_restore:
                    self._navigate_to_vmgroup()
                    self.vsa_sc_obj.restore()
                    self.select_restore_obj.select_full_vm_restore()
                self.configure_restore_settings()
                self._submit_restore_job(self._vms, destination_server)

            if not self.conversion_restore:
                for _vm in self._vms:
                    if self.full_vm_in_place:
                        restore_vm = _vm
                    else:
                        restore_vm = self.vm_restore_prefix + _vm
                    self.vm_restore_validation(_vm, restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore. %s", str(exp))
            raise exp

    @PageService()
    def validate_vmgroup(self, vmgroup_name, validate_input):
        """
        Validates the vmgroup with the given set of inputs

        vmgroup_name        (str)   -Name of the vm group

        validate_input      (dict)  -Dict of details to validate
                                    {"vm_group_name": "TC_test_vmgroup",
                                            "vm_content": "content",
                                            "plan": 'Plan'}

        Returns True, if the validation is successful
        """
        self.vm_groups_obj.select_vm_group(vmgroup_name)
        vmgroup_details = self.vsa_sc_obj.fetch_vmgroup_details()
        if not self.verify_entity_details(validate_input, vmgroup_details):
            raise Exception("VM group validation failed")


class VcloudAdminConsole(AdminConsoleVirtualServer):
    """
       Vcloud class to perform Vcloud related adminconsole tasks
       """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initialize any vCloud VM related variables

        Args:
            instance    (object):  object of the instance class

            driver      (object):  the browser object

            commcell    (object):  an instance of the commcell class

            csdb        (object): the cs DB object

        """
        super(VcloudAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)

        self._full_vm_restore_options = {}
        self._organization = None
        self._org_vdc = None
        self._vapp_name = None
        self._network_setting = False
        self._source_network = None
        self._destination_network = None
        self._destination_vapp = None
        self._destination_vdc = None
        self._new_vapp = False

        self._associated_vcenters = None

        self._storage_policy = None

        self._vm_restore_prefix = 0
        self._owner = None

    @property
    def organization(self):
        """
        Returns the  organization

        Returns:
            organization     (str):    value of organization

        """
        return self._organization

    @organization.setter
    def organization(self, value):
        """
        Sets the value of  organization

        Args:
            value   (str):  value for organization
        """
        self._organization = value

    @property
    def org_vdc(self):
        """
        Returns the live org_vdc value

        Returns:
            org_vdc     (str): True / False to enable or disable managed_vm
        """
        return self._org_vdc

    @org_vdc.setter
    def org_vdc(self, value):
        """
        Sets the org_vdc value

        Args:
            value     :  org_vdc
        """
        self._org_vdc = value

    @property
    def owner(self):
        """
        Returns the owner value

        Returns:
            owner    (str): value of _owner_name
        """
        return self._owner

    @owner.setter
    def owner(self, value):
        """
        Sets the owner value

        Args:
            value     :  value of owner name
        """
        self._owner = value

    @property
    def vapp_name(self):
        """
        Returns the live vapp_name
        Returns:
            storage_account     (str):  value of vapp_name

        """
        return self._vapp_name

    @vapp_name.setter
    def vapp_name(self, value):
        """
        Sets the value of  vapp_name

        Args:
            value   (str): value for _vapp_name
        """
        self._vapp_name = value

    @property
    def network_setting(self):
        """
        Returns the live _network_setting

        Returns:
            vmsize     (str):  value of vm_size

        """
        return self._network_setting

    @network_setting.setter
    def network_setting(self, value):
        """
        Sets the live _network_setting

        Args:
            value   (str):  value for vmsize
        """
        self._network_setting = value

    @property
    def source_network(self):
        """
        Returns the live source_network

        Returns:
            network_interface     (bool):  True / False to enable or disable live recovery

        """
        return self._source_network

    @source_network.setter
    def source_network(self, value):
        """
        Sets the live _source_network
        Args:
            value  (str): value for _source_network
        """
        self._source_network = value

    @property
    def destination_network(self):
        """
        Returns the live security_group

        """
        return self._destination_network

    @destination_network.setter
    def destination_network(self, value):
        """
        Sets value of _destination_network
        Args:
            value   (str):  value for _destination_network
        """
        self._destination_network = value

    @property
    def destination_vapp(self):
        """
        Returns the value of Destination Vapp

        """
        return self._destination_vapp

    @destination_vapp.setter
    def destination_vapp(self, value):
        """
        Sets value of _destination_Vapp
        Args:
            value   (str):  value for _destination_Vapp
        """
        self._destination_vapp = value

    @property
    def new_vapp(self):
        """
        Returns the value of Destination Vapp

        """
        return self._new_vapp

    @new_vapp.setter
    def new_vapp(self, value):
        """
        Sets value of _destination_Vapp
        Args:
            value   (str):  value for _destination_Vapp
        """
        self._new_vapp = value

    @property
    def associated_vcenters(self):
        if not self._associated_vcenters:
            self._associated_vcenters = []
            query = """select attrVal from app_instanceprop where attrName = 'Vs Member vCenters' and 
                            componentNameId = (select max(instance) from APP_Application 
                                where clientId = (select id from App_Client where displayName = '{}'))""" \
                .format(self.hypervisor)
            self.csdb.execute(query)
            csdb_res = self.csdb.fetch_all_rows()[0][0]

            for vc_client in xmltodict.parse(csdb_res)['App_MemberServers']['memberServers']:
                self._associated_vcenters.append((vc_client['client']['@clientId'], vc_client['client']['@clientName']))

        return self._associated_vcenters

    def _set_vcloud_vm_restore_options(self):
        """
                Sets the VM restore options for each VM to be restored

                Raises:
                    Exception:
                        if there is any exception in setting the restore options
        """

        try:
            for _vm in self._vms:
                if (self.vapp_name and self.source_network) is None:
                    self.vapp_name, self.source_network = self.hvobj. \
                        compute_free_resources(self._vms)
                if self.destination_vapp is not None:
                    if self.new_vapp:
                        self.vapp_name = str(self.vm_restore_prefix) + self.destination_vapp
                    else:
                        self.vapp_name = self.destination_vapp
                if self.destination_network is None:
                    self.destination_network = self.source_network
                if self.storage_profile is None:
                    self.storage_profile = self.hvobj.VMs[_vm].storage_profile

                self._full_vm_restore_options[_vm].update({
                    'organization': self._organization,
                    'org_vdc': self._destination_vdc or self.org_vdc,
                    'vapp_name': self.vapp_name,
                    'source_network': self.source_network,
                    'destination_network': self.destination_network,
                    'storage_profile': self.hvobj.VMs[_vm].storage_profile,
                    'owner': self.owner
                })

        except Exception as exp:
            self.log.exception("Exception occurred during setting restore options")
            raise exp

    def attach_disk_restore(self, disk_storage_policy=None, end_user=False):
        """
        Performs attach disk restore for vCloud.

        Args:
            disk_storage_policy     (str)   -       name of the storage policy for destination disk
            end_user                (bool)  -       True if end user restore

        Raises:
            Exception:
                if unable submit attach disk restore or error during gathering necessary parameters.

        """

        self.log.info("Attempting attach disk restore")
        try:
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            if self._restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(self.restore_client)

            access_node = self._restore_proxy
            destination_hypervisor = self._restore_client

            self.log.info("Using {} as access node and {} as destination hypervisor".format(access_node,
                                                                                            destination_hypervisor))

            # loop over vms
            for each_vm in self._vms:
                self.log.info("Getting disks for VM {}".format(each_vm))

                _disks_to_attach = get_stored_disks(vm_guid=self.hvobj.VMs[each_vm].guid, subclient=self.subclient_obj)
                _disks_to_attach_obj = [disk for disk in self.hvobj.VMs[each_vm].disk_config.values()]

                destination_vm_path = self.destination_vm_path.split("/")

                if not end_user:
                    self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                    self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                    self.vsa_sc_obj.restore()
                else:
                    self._navigate_to_vm_restore(each_vm)

                self.select_restore_obj.select_disk_restore()

                self.log.info("Submitting attach disk restore for VM {}".format(each_vm))

                # Get list of disks before restore job on the destination VM
                if end_user:
                    dest_vm = each_vm
                else:
                    dest_vm = destination_vm_path[-1]
                self.hvobj.VMs = dest_vm
                self.hvobj.VMs[dest_vm].get_disk_info()
                pre_restore_disks = self.hvobj.VMs[dest_vm].disk_config

                self.restore_job_id = self.disk_level_restore_obj. \
                    vcloud_attach_disk_restore(source_vm=each_vm, disk_list=_disks_to_attach,
                                               destination_vm_path=destination_vm_path,
                                               destination_hypervisor=destination_hypervisor,
                                               access_node=access_node, disk_storage_profile=disk_storage_policy,
                                               end_user=end_user)

                job_details = self.get_job_status(self.restore_job_id)

                if not job_details:
                    raise Exception("Failed to submit attach disk restore job. Check logs.")

                self.auto_vsa_subclient.vcloud_attach_disk_validation(
                    destination_vm=dest_vm,
                    disks_to_attach=_disks_to_attach_obj,
                    pre_restore_disks=pre_restore_disks,
                    disk_storage_policy=disk_storage_policy)

        except Exception as exp:
            self.log.exception("Exception occurred during attach disk restore: %s", str(exp))
            raise exp

    def full_vm_restore(self, vm_level=False, standalone=False):
        """
                Performs full VM restore for a vCloud VM
                restored as Standalone if value passed as true

                Raises:
                    Exception:
                        if full VM restore or validation fails


        """
        try:
            self.log.info("*" * 10 + "Performing full VM restore" + "*" * 10)
            self.hvobj.vcloud_auth_token = self.hvobj.check_for_login_validity()
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator
            if self._restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj
            else:
                if not self.restore_destination_client:
                    self.restore_destination_client, \
                        self._restore_instance_type = self._create_hypervisor_object(self.restore_client)

            self._full_vm_restore_options = dict.fromkeys(self._vms, {})
            self._set_vcloud_vm_restore_options()
            if self.org_vdc is None:
                raise Exception("Org_vdc is none.")

            if vm_level:
                for _vm in self._vms:
                    self._navigate_to_vm_restore(_vm)
                    self.select_restore_obj.select_full_vm_restore()

            else:
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                self.vsa_sc_obj.restore()
                self.select_restore_obj.select_full_vm_restore()

            self.restore_job_id = self.full_vm_restore_obj.vcloud_full_vm_restore(
                self._vms,
                self.restore_proxy,
                self.restore_client,
                self.full_vm_in_place,
                self._full_vm_restore_options,
                self.org_vdc,
                power_on=True,
                overwrite=True,
                restore_vapp=True,
                standalone=standalone,
                restore_prefix=str(self.vm_restore_prefix)
            )

            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Restore job failed. Please check the logs")

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = str(self.vm_restore_prefix) + _vm
                attempt = 0
                while attempt < 3:
                    self.log.info("attempt =" + str(attempt))
                    try:
                        self.vm_restore_validation(_vm, restore_vm, self._full_vm_restore_options[_vm])
                        break
                    except:
                        attempt = attempt + 1
                        time.sleep(60)
                if attempt >= 3:
                    self.vm_restore_validation(_vm, restore_vm)
            self._vm_restore_prefix += 1
        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore. %s", str(exp))
            raise exp

    def post_restore_clean_up(self, source_vm=False, status=False, disk_restore=False):

        """
            Cleans up vCloud VMs and its resources after out of place restore

        Args:
                    source_vm                       (bool): whether  source vm has to be powered
                                                            off or not
                    status                          (bool) : whether the tc has passed ot failed
        Raises:
             Exception:
                If unable to clean up VM and its resources
        """

        if disk_restore:
            try:
                from VirtualServer.VSAUtils.VirtualServerUtils import vcloud_bridge_vm

                restore_vm_name = self.testcase_obj.tcinputs['DestinationVM'].split("/")[-1]
                if restore_vm_name not in self.restore_destination_client.VMs.keys():
                    self.restore_destination_client.VMs = restore_vm_name

                # Create a vCenter VM from the source vCloud VM. Call delete_disks() function.
                # Clean up logic will first try to delete the disks using vCloud APIs.
                # In case that fails, we fallback to the use of vCenter SDK.
                vcloud_vm = self.restore_destination_client.VMs[restore_vm_name]

                vcenter_vm = vcloud_bridge_vm(self, vcloud_vm)
                vcenter_vm.delete_disks()
            except Exception as exp:
                self.log.info("Error deleting attached disks to destination VM: {}".format(str(exp)))

            return

        try:
            for each_vm in self._vms:
                if self.hvobj.VMs.get(each_vm, None):
                    if source_vm:
                        self.log.info("Powering off VM {0}".format(each_vm))
                        self.hvobj.VMs[each_vm].power_off()
                if self.restore_destination_client:
                        for prefix in range(0, int(self.vm_restore_prefix)):
                            restore_vm_name = str(prefix) + str(each_vm)
                            if restore_vm_name not in self.restore_destination_client.VMs.keys():
                                self.restore_destination_client.VMs = restore_vm_name
                        if status:
                            self.log.info("Cleaning up VM {0}".format(restore_vm_name))
                            self.restore_destination_client.VMs[restore_vm_name].clean_up()
                        else:
                            self.log.info("Powering off VM {0}".format(restore_vm_name))
                            self.restore_destination_client.VMs[restore_vm_name].power_off()

        except Exception as err:
            self.log.exception(
                "Exception while doing cleaning up VM resources: " + str(err))
            raise err



    def retire_associated_vcenters(self):
        """
        Retires associated vcenter accounts.
        """
        associated_vcenters = self.hypervisor_details_obj.get_associated_vcenters()
        for vcenter in associated_vcenters:
            self.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(vcenter)



class OracleCloudInfrastructureAdminConsole(AdminConsoleVirtualServer):
    """
    Oracle Cloud Infrastructure class to perform functions specific to Oracle Cloud Infrastructure.
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        super(OracleCloudInfrastructureAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._region = None
        self._availability_domain = None
        self._compartment_id = None
        self._compartment_path = None
        self._shape = None
        self._vcn = None
        self._subnet = None
        self._staging_bucket = None
        self._tags = None
        self._set_default_do_restore_validation_options()

    @property
    def region(self):
        """
        Returns the region

        Returns:
            region  (str)   --  the name of the region
        """
        return self._region

    @region.setter
    def region(self, value):
        """
        Sets the region

        Args:
            value   (str)   --  the name of the region
        """
        self._region = value

    @property
    def availability_domain(self):
        """
        Returns the availability_domain

        Returns:
            availability_domain  (str)   --  the name of the availability domain
        """
        return self._availability_domain

    @availability_domain.setter
    def availability_domain(self, value):
        """
        Sets the availability_domain
        If Cross AD restore is to be validated, set do_restore_validation_options['CrossAD_Restore'] to True in the testcase.py file & the AD to restore to in the testcase.py file

        Args:
            value   (str)   --  the name of the availability domain
        """
        if self.do_restore_validation_options['CrossAD_Restore']:
            self.restore_validation_options['CrossAD_AvailabilityDomain'] = value
        self._availability_domain = value

    @property
    def compartment_id(self):
        """
        Returns the OCID of the compartment

        Returns:
            compartment_id  (str)   --  the id of the compartment
        """
        return self._compartmeny_id

    @compartment_id.setter
    def compartment_id(self, value):
        """
        Sets the OCID of the compartment. Must set this parameter or set compartment_path if you want to restore to a compartment that is not that the same as the source VMs.

        Args:
            value   (str)   --  the name of the compartment
        """
        self._compartment_id = value

    @property
    def compartment_path(self):
        """
        Returns the compartment_path. The list containing the path from the root(region) to the compartment of the Virtual Server Object

        Returns:
            compartment_path  (list)   --  the list containing the path from the root(region) to the compartment of the Virtual Server Object
        """
        return self._compartment_path

    @compartment_path.setter
    def compartment_path(self, value):
        """
        Sets the compartment_path. The list containing the path from the root(region) to the compartment of the Virtual Server Object
        In case of Cross AD restore, please set the AD in the testcase.py file. This AD will replace the AD in the source VMs compartment path

        Args:
            value   (list)   --  the list containing the path from the root(region) to the compartment of the Virtual Server Object
        """
        if self.availability_domain is not None:
            value[1] = self.availability_domain

        self._compartment_path = value

    @property
    def shape(self):
        """
        Returns the shape

        Returns:
            shape  (str)   --  the name of the shape
        """
        return self._shape

    @shape.setter
    def shape(self, value):
        """
        Sets the shape

        Args:
            value   (str)   --  the name of the shape
        """
        self._shape = value

    @property
    def vcn(self):
        """
        Returns the vcn

        Returns:
            vcn  (str)   --  the name of the vcn
        """
        return self._vcn

    @vcn.setter
    def vcn(self, value):
        """
        Sets the vcn. Please ensure that the VCN is present in the compartment and region that the VMs are being restored to.

        Args:
            value   (str)   --  the name of the vcn
        """
        self._vcn = value

    @property
    def subnet(self):
        """
        Returns the subnet

        Returns:
            subnet  (str)   --  the name of the subnet
        """
        return self._subnet

    @subnet.setter
    def subnet(self, value):
        """
        Sets the subnet. Please ensure that the subnet is present in the compartment and region that the VMs are being restored to.

        Args:
            value   (str)   --  the name of the subnet
        """
        self._subnet = value

    @property
    def staging_bucket(self):
        """
        Returns the staging_bucket

        Returns:
            staging_bucket  (str)   --  the name of the staging_bucket
        """
        return self._staging_bucket

    @staging_bucket.setter
    def staging_bucket(self, value):
        """
        Sets the staging_bucket. Must be specified if the restore is conversion restore. Staging must be present in the compartment that the VMs are being restored to.

        Args:
            value   (str)   --  the name of the staging_bucket
        """
        self._staging_bucket = value

    @property
    def tags(self):
        """
        Returns the tags that are going to be added to the restored VMs. These tags wont be added to the VMs if the VM already has a tag with the same tag_namespace and tag_key

        Returns:
            tags (dict of dict)  -- {tag_namespace: {tag_key: tag_value}}
        """
        return self._tags

    @tags.setter
    def tags(self, value):
        """
        Sets the tags that are going to be added to the restored VMs. These tags wont be added to the VMs if the VM already has a tag with the same tag_namespace and tag_key
        If the added tags are to be validated post restore, set do_restore_validation_options['tags'] to True in the testcase.py file

        Args:
            value   (List of Ordered Dicts of List Ordered Dicts) -- [OrderedDict([(tag_namespace,[OrderedDict([(tag_key1,tag_value)]),OrderedDict([(tag_key2,tag_value)])])])]
        """
        tag_dict = {tag_namespace:{tag_key:tag_value for key_pair in tag_key_pair_list for tag_key,tag_value in key_pair.items()} for namespace_list in value for tag_namespace,tag_key_pair_list in namespace_list.items()}
        self.restore_validation_options['tags'] = tag_dict
        self._tags = tag_dict

    @property
    def do_restore_validation_options(self):
        """
        Returns the dictionary of  {option: True/False} for which validation has to be performed post restore

        Returns:
            do_restore_validation_options  (dict)   --  the dictionary of  {option: True/False} for which validation has to be performed post restore
        """
        return self._do_restore_validation_options

    @do_restore_validation_options.setter
    def do_restore_validation_options(self, do_restore_validation_dict):
        """
        Sets the options for which validation has to be perfomed post restore
        Currently validated options are:
            1. 'tags' -> True if you want to validate the tags of the restored VMs
            2. 'CrossAD_Restore' -> True if you want to validate the Cross AD restore

        Args:
        do_restore_validation_dict (dict)  --  the dictionary of  {option: True/False} for which validation has to be performed post restore
        """
        valid_keys = {'CrossAD_Restore'}
        if not isinstance(do_restore_validation_dict, dict):
            raise Exception(f"Invalid input '{do_restore_validation_dict}' specified for validation_options. Input should be a dictonary of {{Option: True/False}} pairs")
        for key, value in do_restore_validation_dict.items():
            if key not in valid_keys:
                raise Exception(f"Invalid option '{key}' specified for validation. Valid keys are {valid_keys}")
            if value not in [True, False]:
                raise Exception(f"Invalid value '{value}' specified for validation. Value must be a boolean variable.")
            self._do_restore_validation_options[key] = value

    def _set_default_do_restore_validation_options(self):
        """
        Sets validation of all options to False by default
        Currently validated options are:
            1. 'CrossAD_Restore' -> True if you want to validate the Cross AD restore
        """
        keys = ['CrossAD_Restore']
        for key in keys:
            self._do_restore_validation_options[key] = False

    def _set_oci_full_vm_restore_options(self):
        """
                Sets the VM restore options for each VM to be restored

                Raises:
                    Exception:
                        if there is any exception in setting the restore options
        """
        try:
            if self.conversion_restore:
                if self.availability_domain is None:
                    self.availability_domain = self.coordinator_vm_obj.availability_domain
                if self.compartment_path is None:
                    self.compartment_path = self.coordinator_vm_obj.compartment_path
                if self.shape is None:
                    self.shape = self.coordinator_vm_obj.shape
                if self.vcn is None:
                    self.vcn = self.coordinator_vm_obj.vcn
                if self.subnet is None:
                    self.subnet = self.coordinator_vm_obj.subnet

            self._full_vm_restore_options = dict((_all_vms, dict()) for _all_vms in self._vms)
            for _vm in self._vms:
                if self.compartment_path is None:
                    self.compartment_path = self.hvobj.VMs[_vm].compartment_path
                if self.availability_domain is None:
                    self.availability_domain = self.hvobj.VMs[_vm].availability_domain
                if self.shape is None:
                    self.shape = self.hvobj.VMs[_vm].shape
                if self.vcn is None:
                    self.vcn = self.hvobj.VMs[_vm].vcn
                if self.subnet is None:
                    self.subnet = self.hvobj.VMs[_vm].subnet
                self._full_vm_restore_options[_vm]['compartment_path'] = self.compartment_path
                self._full_vm_restore_options[_vm]['availability_domain'] = self.availability_domain
                self._full_vm_restore_options[_vm]['shape'] = self.shape
                self._full_vm_restore_options[_vm]['vcn'] = self.vcn
                self._full_vm_restore_options[_vm]['subnet'] = self.subnet
                if self.staging_bucket:
                    self._full_vm_restore_options[_vm]['staging_bucket'] = self.staging_bucket
                if self.tags:
                    self._full_vm_restore_options[_vm]['tags'] = self.tags
        except Exception as exp:
            self.log.exception("Exception occurred during setting restore options")
            raise exp

    def _submit_restore_job(self, vm_list):
        """
        Submit the restore job and track the jobs

        Args:
            vm_list (str/list) : vm/vms to be restored
        """
        self.restore_job_id = self.full_vm_restore_obj.oci_full_vm_restore(
            vms=vm_list,
            proxy=self.restore_proxy,
            destination_server=self.restore_client,
            power_on=self.power_on_after_restore,
            in_place=self.full_vm_in_place,
            over_write=self.unconditional_overwrite,
            vm_restore_options=self._full_vm_restore_options,
            restore_prefix=self.vm_restore_prefix,
            restore_as=hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value,
        )
        job_details = self.get_job_status(self.restore_job_id,self.job_status)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

    def full_vm_restore(self, vm_level=False):
        """
        Performs full VM Restore for Oracle Cloud Infrastructure(OCI)
        Args:
            vm_level: Enable vm_level restore

        Returns:

        """
        try:
            if self.do_restore_validation_options['CrossAD_Restore']:
                if self.restore_proxy is None:
                    self.log.info("Restore Proxy not set. Setting it to the coordinator VM %s", self.co_ordinator)
                else:
                    self.log.info("Restore Proxy set to %s", self.restore_proxy)
            if self.restore_proxy is None:
                self.restore_proxy = self._co_ordinator
            self.restore_validation_options['Restore_Proxy'] = self.restore_proxy
            self.restore_destination_client = self.hvobj
            self.restore_client = self.hypervisor
            self._set_oci_full_vm_restore_options()
            if vm_level:
                for _vm in self._vms:
                    try:
                        self._navigate_to_vm_restore(_vm)
                        self.select_restore_obj.select_full_vm_restore()
                    except Exception as exp:
                        self.log.info(exp)
                    self._submit_restore_job(_vm)
            else:
                try:
                    if not self.conversion_restore:
                        self._navigate_to_vmgroup()
                        self.vsa_sc_obj.restore()
                        self.select_restore_obj.select_full_vm_restore()
                except Exception as exp:
                    raise Exception(exp)
                self._submit_restore_job(self._vms)
            if self.conversion_restore:
                return
            for vm_name in self._vms:
                restore_vm_name = vm_name if self.full_vm_in_place else self.vm_restore_prefix + vm_name
                try:
                    self.vm_restore_validation(vm_name, restore_vm_name)
                except Exception as exp:
                    self.log.info(f"VM restore validation failed for VM: {vm_name}")
                    raise exp

        except Exception as exp:
            self.log.exception(
                "Exception occurred during OCI Full VM restore. %s", str(exp))
            raise exp

    def validate_live_sync(self, replication_group_name=None):
        """
                Validate Live Sync function, validates the live sync operation.
                Args:
                    replication_group_name (str)   --   Name of the replication group,
                    if not set, a replication group is automatically configured.
                Raises:
                    Exception:
                        If the validation fails
        """
        vm_backupgroup = self.subclient
        vm_instance = self.hvobj.VMs[list(self.hvobj.VMs)[0]]
        replication_target_name = "Automation_Replication_Target"
        created_replication_group = False
        dict_vals = {
            'hypervisor': self._hypervisor,
            'replication_group_name': "Automation_Replication_Group",
            'vm_backupgroup': vm_backupgroup,
            'replication_target': replication_target_name,
            'proxy': self._co_ordinator.machine_name,
            'compartment': vm_instance.compartment_name,
            'datastore': vm_instance.datastore,
            'vcn': vm_instance.vcn_name,
            'shape': vm_instance.instance_size,
            'vm_name': vm_instance.vm_name,
            'subnet_name': self.oci_subnet_name if self.oci_subnet_name else None
        }
        self.navigator.navigate_to_replication_groups()
        if not replication_group_name:
            self.replication_group_obj.configure_ls_replication_group()
            self.configure_replication_group_obj.select_live_sync()
            self.configure_vsa_replication_group_obj.configure_vsa_replication_group(dict_vals)
            replication_group_name = "Automation_Replication_Group"
            created_replication_group = True
        self.replication_group_obj.access_group(replication_group_name)
        replication_job_id = self.replication_group_details_obj.get_replication_job()
        time.sleep(30)
        try:
            self.log.info(f"Getting status for the job {replication_job_id}")
            job_details = self.get_job_status(replication_job_id)
            if job_details['Status'] not in ["Completed", "Completed w/ one or more errors"]:
                raise Exception("Replication job failed. Please check the logs")
        except Exception as exp:
            self.log.exception(
                "Exception occurred in getting the job status: %s", str(exp))
            raise exp
        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        sync_status = self.replication_group_details_obj.get_sync_status()
        assert self.validate_status(sync_status, "in sync"), "Sync status is not 'In Sync'"
        self.restore_destination_client = self.hvobj
        source_vms, destination_vms = \
            self.replication_group_details_obj.get_source_and_destination()
        for vm_name in self.hvobj.VMs.keys():
            if vm_name in source_vms or vm_name in destination_vms:
                self.hvobj.VMs[vm_name].machine.close()
        for vm_index in range(len(source_vms)):
            vm_restore_name = destination_vms[vm_index]
            source_vm_name = source_vms[vm_index]
            if vm_restore_name[-3:] == "_DN":
                vm_restore_name = vm_restore_name[:-3]
            if source_vm_name[-3:] == "_DN":
                source_vm_name = source_vm_name[:-3]
            try:
                self.vm_restore_validation(source_vm_name, vm_restore_name)
            except Exception as exp:
                self.log.info("VM restore validation failed for VM: {}".format(source_vms[vm_index]))
                raise exp
        for vm_name in self.hvobj.VMs.keys():
            if vm_name in destination_vms:
                self.hvobj.VMs[vm_name].vm_power_off()
        if created_replication_group:
            self.log.info("Deleting Replication Group")
            self.navigator.navigate_to_replication_groups()
            self.replication_group_obj.delete_group(replication_group_name)
            self.recovery_target_obj.navigate_to_replication_targets()
            self.recovery_target_obj.action_delete(replication_target_name)

    def perform_unplanned_failover(self, source_vms):
        """
        Perform Unplanned failover
        Args:
            source_vms: List of source VMs to perform failover

        Returns: Job ID of failover job

        """
        job_id = self.replication_group_details_obj.unplanned_failover(source_vms)
        return job_id

    def perform_planned_failover(self, source_vms):
        """
        Perform planned failover
        Args:
            source_vms: List of source VMs to perform failover

        Returns: Job ID of failover job

        """
        job_id = self.replication_group_details_obj.planned_failover(source_vms)
        return job_id

    def validate_unplanned_failover(self, replication_group_name):
        """
         Validate Planned Failover.

          Args:
              replication_group_name (str)   --   Name of the replication group,
                if not set, a replication group is automatically configured.

          Raises:
              Exception:
              If the validation fails
        """
        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        source_vms, destination_vms = \
            self.replication_group_details_obj.get_source_and_destination()
        job_id = self.perform_unplanned_failover(source_vms)
        time.sleep(15)
        failover_status = self.replication_group_details_obj.get_failover_status()
        assert self.validate_status(failover_status, "failover in progress"), "Failover status not valid"

        try:
            self.log.info("Getting status for the job %s", job_id)
            job_details = self.get_job_status(job_id)
            if not job_details:
                raise Exception("Failover job failed. Please check the logs")

        except Exception as exp:
            self.log.exception(
                "Exception occurred in getting the job status: %s", str(exp))
            raise exp
        if not self.hvobj:
            self.hvobj = self._create_hypervisor_object()[0]
        for vm_index in range(len(source_vms)):
            source_vm = source_vms[vm_index]
            destination_vm = destination_vms[vm_index]
            if source_vm[-3:] == "_DN":
                source_vm = source_vm[:-3]
            if destination_vm[-3:] == "_DN":
                destination_vm = destination_vm[:-3]
            instance_source = self.hvobj.get_vm_property(source_vm)
            instance_destination = self.hvobj.get_vm_property(destination_vm)
            assert instance_source['power_state'] == "STOPPED" and \
                   instance_destination['power_state'] == "RUNNING"
            self.log.info("Source VM is POWERED OFF and Destination VM is RUNNING")
        self.log.info("Unplanned failover validation successful")

    def validate_planned_failover(self, replication_group_name):
        """
        Validate Planned Failover
        Args:
              replication_group_name (str)   --   Name of the replication group

        Raises:
            Exception:
              If the validation fails
        """
        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        recovery_target_name = self.replication_group_details_obj.get_recovery_target()
        self.recovery_target_obj.navigate_to_replication_targets()
        self.recovery_target_obj.select_replication_target(recovery_target_name)

        destination_client_name = self.recovery_target_obj.get_destination_hypervisor()

        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)

        source_vms, destination_vms = \
            self.replication_group_details_obj.get_source_and_destination()
        if not self.hvobj:
            self.hvobj = self._create_hypervisor_object()[0]
        if not self.testdata_path:
            self.testdata_path = VirtualServerUtils.get_testdata_path(self.hvobj.machine)
        checksum_lst = []
        self._vms = []
        for vm_name in source_vms:
            if vm_name[-3:] == "_DN":
                vm_name = vm_name[:-3]
            if vm_name not in self.hvobj.VMs:
                self.hvobj.VMs = vm_name
                self._vms.append(vm_name)
                self.cleanup_testdata()
            self.hvobj.VMs[vm_name].machine.generate_test_data(self.testdata_path)
            checksum_lst.append(self.hvobj.VMs[vm_name].machine.get_checksum_list(self.testdata_path))
        if destination_client_name[-3:] == "_DN":
            destination_client_name = destination_client_name[:-3]
        self.destination_client = self._create_hypervisor_object(destination_client_name)[0]

        # Validating successfull completion of job
        job_id = self.perform_planned_failover(source_vms)
        time.sleep(15)
        failover_status = self.replication_group_details_obj.get_failover_status()
        assert self.validate_status(failover_status, "failover in progress"), "Failover status not valid"
        try:
            self.log.info("Getting status for the job %s", job_id)
            job_details = self.get_job_status(job_id)
            if not job_details:
                raise Exception("Failover job failed. Please check the logs")
        except Exception as exp:
            self.log.exception(
                "Exception occurred in getting the job status: %s", str(exp))
            raise exp

        # Checksum list on destination
        dest_checksum_lst = []
        for vm_name in destination_vms:
            if vm_name[-3:] == "_DN":
                vm_name = vm_name[:-3]
            self.destination_client.VMs = vm_name
            dest_vm = self.destination_client.VMs[vm_name]
            dest_vm.vm_power_on()
            dest_checksum_lst.append(dest_vm.machine.get_checksum_list(self.testdata_path))

        # Testdata validation
        assert checksum_lst == dest_checksum_lst
        self.log.info("Testdata Validation Completed Successfully.")

        # Config Validation
        for source_vm_name, dest_vm_name in zip(source_vms, destination_vms):
            if source_vm_name[-3:] == "_DN":
                source_vm_name = source_vm_name[:-3]
            if dest_vm_name[-3:] == "_DN":
                dest_vm_name = dest_vm_name[:-3]
            source_vm = self.hvobj.VMs[source_vm_name]
            dest_vm = self.destination_client.VMs[dest_vm_name]
            _source = self.auto_vsa_subclient.VmValidation(source_vm)
            _dest = self.auto_vsa_subclient.VmValidation(dest_vm)
            self.log.info("Powering off source and destination VMs")
            source_vm.vm_power_off()
            dest_vm.vm_power_off()

            assert _source == _dest, "Failed while config validation"
        self.log.info("Config Validation Successfull")

    def validate_failback(self, replication_group_name):
        """
        Validate Failback.

         Args:
              replication_group_name (str)   --   Name of the replication group

         Raises:
             Exception:
                If the validation fails
        """
        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        source_vms, destination_vms = \
            self.replication_group_details_obj.get_source_and_destination()

        failover_status = self.replication_group_details_obj.get_failover_status()
        assert self.validate_status(failover_status, "failover complete"), "Failover status not valid"

        job_id = self.replication_group_details_obj.failback(source_vms)
        try:
            self.log.info("Getting status for the job %s", job_id)
            job_details = self.get_job_status(job_id)
            if not job_details:
                raise Exception("Failback job failed. Please check the logs")

        except Exception as exp:
            self.log.exception(
                "Exception occurred in getting the job status: %s", str(exp))
            raise exp
        if not self.hvobj:
            self.hvobj = self._create_hypervisor_object()[0]
        for vm_index in range(len(source_vms)):
            source_vm = source_vms[vm_index]
            destination_vm = destination_vms[vm_index]
            if source_vm[-3:] == "_DN":
                source_vm = source_vm[:-3]
            if destination_vm[-3:] == "_DN":
                destination_vm = destination_vm[:-3]
            instance_source = self.hvobj.get_vm_property(source_vm)
            instance_destination = self.hvobj.get_vm_property(destination_vm)
            assert instance_source['power_state'] == "RUNNING" and \
                   instance_destination['power_state'] == "STOPPED"
            self.log.info("Source VM is RUNNING and Destination VM is POWERED OFF")
        self.log.info("Failback validation successful")

        self.navigator.navigate_to_replication_groups()
        self.replication_group_obj.access_group(replication_group_name)
        failover_status = self.replication_group_details_obj.get_failover_status()

        assert self.validate_status(failover_status, ""), "Failover status not valid"
        self.log.info("Failback validation successfull")

    def validate_status(self, status_list, value):
        """
        Validates the status

        Args:
            status_list: a list
            value: a value

        Returns: boolean

        """
        for status in status_list:
            if status.lower() != value:
                return False
        return True


class GoogleCloudAdminConsole(AdminConsoleVirtualServer):
    """
    Google Cloud class to perform functions specific to Google Cloud.
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        super(GoogleCloudAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)

        self._full_vm_restore_options = {}
        self._zone_name = None
        self._project_id = None
        self._network = None
        self._subnet = None
        self._machine_type = None
        self._custom_metadata = None
        self._service_account_email = None

    @property
    def custom_metadata(self):
        """
        Return the custom metadata

        Returns:
            zone     (dic):  Custom Metadata
        """
        return self._custom_metadata

    @custom_metadata.setter
    def custom_metadata(self, value):
        """
        Sets the value of custom metadata

        Args:
            value     (dic):   dictionary of Custom Metadata
        """
        self._custom_metadata = value

    @property
    def zone_name(self):
        """
        Return the vm zone

        Returns:
            zone     (str):  Zone location
        """
        return self._zone_name

    @zone_name.setter
    def zone_name(self, value):
        """
        Sets the value of zone

        Args:
            value     (str):   zone location
        """
        self._zone_name = value

    @property
    def machine_type(self):
        """
        Return the machine_type

        Returns:
        machine_type   (str):  Zone location
        """
        return self._machine_type

    @machine_type.setter
    def machine_type(self, value):
        """
        Sets the value of zone

        Args:
        value     (str):   zone location
        """
        self._machine_type = value

    @property
    def project_id(self):
        """
        Return the project id of the VM

        Returns:
            project_id     (str):  VM Project ID
        """
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        """
        Sets the value of project

        Args:
            value     (str):   vm project
        """
        self._project_id = value

    @property
    def network(self):
        """
        Return the list of network name attached to the VM

        Returns:
            network     (str):  network list
        """
        return self._network

    @network.setter
    def network(self, value):
        """
        Sets the value of network

        Args:
            value     (str):   VM network
        """
        self._network = value

    @property
    def subnet(self):
        """
        Return the list of subnetwork name attached to the VM

        Returns:
            subnet     (str):  subnetwork
        """
        return self._subnet

    @subnet.setter
    def subnet(self, value):
        """
        Sets the value of subnet

        Args:
            value     (str):   VM subnetwork
        """
        self._subnet = value

    # def _set_google_vm_restore_options(self):
    #     """
    #             Sets the VM restore options for each VM to be restored

    #             Raises:
    #                 Exception:
    #                     if there is any exception in setting the restore options
    #     """

    #     try:
    #         self._vm_list = []
    #         for _vm in self._vms:
    #             self._vm_list.append(_vm)
    #             if self.zone_name is None:
    #                 self.vm_size = self.hvobj.VMs[_vm].zone_name
    #             if self.project_id is None:
    #                 self.project_id = self.hvobj.VMs[_vm].project_name
    #             if self.network is None:
    #                 self.network = self.hvobj.VMs[_vm].nic[0]
    #             if self.subnet is None:
    #                 self.subnet = self.hvobj.VMS[_vm].subnet[0]
    #             if self.custom_metadata is None:
    #                 self.custom_metadata = self.hvobj.VMs[_vm].vm_custom_metadata
    #             if self.machine_type is None:
    #                 self.machine_type = "Auto select"

    #             self._full_vm_restore_options[_vm]['zone_name'] = self.zone_name
    #             self._full_vm_restore_options[_vm]['project_id'] = self.project_id
    #             self._full_vm_restore_options[_vm]['network'] = self.network
    #             self._full_vm_restore_options[_vm]['subnet'] = self.subnet
    #             self._full_vm_restore_options[_vm]['machine_type'] = self.machine_type
    #             self._full_vm_restore_options[_vm]['custom_metadata'] = self.custom_metadata


    #     except Exception as exp:
    #         self.log.exception("Exception occurred during setting restore options")
    #         raise exp

    #     self._full_vm_restore_options = {}
    #     self._zone_name = None
    #     self._project_id = None
    #     self._network = None
    #     self._subnet = None
    #     self._machine_type = None
    #     self._custom_metadata = None
    #     self._service_account_email = None


    @property
    def service_account_email(self):
        """
        Return the custom metadata

        Returns:
            Service Account     (str):  Service Account Email
        """
        return self._service_account_email

    @service_account_email.setter
    def service_account(self, value):
        """
        Sets the value of custom metadata

        Args:
            value     (str):   Service Account
        """
        self._service_account_email = value

    @property
    def custom_metadata(self):
        """
        Return the custom metadata

        Returns:
            Custom Metadata     (dic):  Custom Metadata
        """
        return self._custom_metadata

    @custom_metadata.setter
    def custom_metadata(self, value):
        """
        Sets the value of custom metadata

        Args:
            value     (dic):   dictionary of Custom Metadata
        """
        self._custom_metadata = value

    @property
    def zone_name(self):
        """
        Return the vm zone

        Returns:
            zone     (str):  Zone location
        """
        return self._zone_name

    @zone_name.setter
    def zone_name(self, value):
        """
        Sets the value of zone

        Args:
            value     (str):   zone location
        """
        self._zone_name = value

    @property
    def machine_type(self):
        """
        Return the machine_type

        Returns:
        machine_type   (str):  Zone location
        """
        return self._machine_type

    @machine_type.setter
    def machine_type(self, value):
        """
        Sets the value of zone

        Args:
        value     (str):   zone location
        """
        self._machine_type = value

    @property
    def project_id(self):
        """
        Return the project id of the VM

        Returns:
            project_id     (str):  VM Project ID
        """
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        """
        Sets the value of project

        Args:
            value     (str):   vm project
        """
        self._project_id = value

    @property
    def network(self):
        """
        Return the list of network name attached to the VM

        Returns:
            network     (str):  network list
        """
        return self._network

    @network.setter
    def network(self, value):
        """
        Sets the value of network

        Args:
            value     (str):   VM network
        """
        self._network = value

    @property
    def subnet(self):
        """
        Return the list of subnetwork name attached to the VM

        Returns:
            subnet     (str):  subnetwork
        """
        return self._subnet

    @subnet.setter
    def subnet(self, value):
        """
        Sets the value of subnet

        Args:
            value     (str):   VM subnetwork
        """
        self._subnet = value

    def _set_google_vm_restore_options(self):
        """
                Sets the VM restore options for each VM to be restored

                Raises:
                    Exception:
                        if there is any exception in setting the restore options
        """

        try:
            self._vm_list = []
            self.log.info("serv email = {0}".format(self.service_account_email)) #del
            for _vm in self._vms:
                self._vm_list.append(_vm)
                if self.zone_name is None:
                    #modify
                    self.zone_name = self.hvobj.VMs[_vm].zone_name
                if self.project_id is None:
                    self.project_id = self.hvobj.VMs[_vm].project_name
                if self.network is None:
                    self.network = self.hvobj.VMs[_vm].nic[0]
                if self.subnet is None:
                    self.subnet = self.hvobj.VMs[_vm].subnet[0] #mod
                if self.custom_metadata is None:
                    self.custom_metadata = self.hvobj.VMs[_vm].vm_custom_metadata
                if self.machine_type is None:
                    self.machine_type = "Auto select"
                if self.service_account_email is None:
                    self.service_account =  self.hvobj.get_specified_service_account(self.project_id)
                else:
                    self.service_account = self.hvobj.get_specified_service_account(self.project_id, self.service_account_email)

                self._full_vm_restore_options[_vm]['zone_name'] = self.zone_name
                self._full_vm_restore_options[_vm]['project_id'] = self.project_id
                self._full_vm_restore_options[_vm]['network'] = self.network
                self._full_vm_restore_options[_vm]['subnet'] = self.subnet
                self._full_vm_restore_options[_vm]['machine_type'] = self.machine_type
                self._full_vm_restore_options[_vm]['custom_metadata'] = self.custom_metadata
                self._full_vm_restore_options[_vm]['service_account'] = self.service_account


        except Exception as exp:
            self.log.exception("Exception occurred during setting restore options")
            raise exp

    def full_vm_restore(self):
        """
                                Performs full VM restore for a Google Cloud VM

        Raises:
            Exception:
                if full VM restore or validation fails

        """

        try:
            self.log.info("*" * 10 + "Performing full VM restore" + "*" * 10)

            if self._restore_proxy is None:
                self.restore_proxy = "Automatic"

            if self.restore_client is None:
                self.restore_client = self.hypervisor
                self.restore_destination_client = self.hvobj

            self._full_vm_restore_options = dict.fromkeys(self._vms, {})
            self._set_google_vm_restore_options()

            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
            self.vsa_sc_obj.restore()
            self.select_restore_obj.select_full_vm_restore()
            self.vm_restore_prefix = self.vm_restore_prefix.lower().replace("_", "")
            self.validate_restore_workload = True
            self.restore_job_id = self.full_vm_restore_obj.google_cloud_full_vm_restore(
                self._vm_list,
                self.restore_client,
                self._zone_name,
                self._project_id,
                self._subnet,
                self._network,
                self.vm_restore_prefix,
                self.full_vm_in_place,
                self._full_vm_restore_options,
                self.restore_proxy,
                self.power_on_after_restore,
                self.unconditional_overwrite,
            )
            job_details = self.get_job_status(self.restore_job_id)
            if not job_details:
                raise Exception("Restore job failed. Please check the logs")
            for _vm in self._vms:
                restore_vm = self.vm_restore_prefix + _vm
                self.vm_restore_validation(_vm, restore_vm)

        except Exception as exp:
            self.log.exception("Exception occurred during Google Cloud VM restore. %s", str(exp))
            raise exp

    def guest_files_restore(self, in_place=False, vm_level=False):
        """
        File level restore to source VM

        Args:
            in_place    (bool):     if the files should be restored to the source path

            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if the file level restore fails

        """
        try:
            if self._restore_proxy is None:
                self.restore_proxy = self._co_ordinator

            for _vm in self._vms:
                self.agentless_vm = _vm

                for _drive, _folder in self.hvobj.VMs[_vm].drive_list.items():
                    if in_place:
                        restore_path = _folder
                        validate_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            restore_path, self.backup_type.name, "TestData", self.pid)
                    else:
                        restore_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            _folder, "AdminConsole", self.agentless_vm, _drive)
                        validate_path = self.hvobj.VMs[self.agentless_vm].machine.join_path(
                            restore_path, self.backup_type.name, "TestData", self.pid)

                    if self.hvobj.VMs[_vm].machine.check_directory_exists(restore_path):
                        if restore_path != _folder:
                            self.hvobj.VMs[_vm].machine.remove_directory(restore_path)

                    if self.ci_enabled:
                        self.navigator.navigate_to_virtual_machines()
                        self.virtual_machines_obj.open_vm(_vm)
                        self.vm_details_obj.vm_search_content(self.backup_folder_name)
                        self.vsa_search_obj.search_for_content(
                            file_name=self.backup_folder_name, contains=_drive,
                            include_folders=True)
                        self.vsa_search_obj.select_data_type("Folder")
                        self.vsa_search_obj.validate_contains(self.backup_folder_name,
                                                              name=True)
                        self.vsa_search_obj.validate_contains(_drive, name=False,
                                                              folder=True)
                    else:
                        if not vm_level:
                            self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                            self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                            self.vsa_sc_obj.restore()
                        else:
                            self._navigate_to_vm_restore(_vm)

                        self.configure_restore_settings()
                        self.select_restore_obj.select_guest_files()
                        self.select_restore_obj.latest_backups()
                        if _folder == "/":
                            self.restore_vol_obj.select_volume(_vm, _folder)
                        else:
                            self.restore_vol_obj.select_volume(_vm, _drive)

                    self.restore_job_id = self.restore_files_obj.submit_google_cloud_vm_restore(
                        [self.backup_type.name.upper()], self.agentless_vm,
                        self.restore_proxy,
                        self.hvobj.VMs[_vm].machine.username,
                        self.hvobj.VMs[_vm].machine.password,
                        restore_path
                    )
                    self.get_job_status(self.restore_job_id)
                    self.guest_files_restore_validation(self._restore_proxy, validate_path)
        except Exception as exp:
            self.log.exception("Exception occurred during guest files restore. %s", str(exp))
            raise exp


class FusionComputeAdminConsole(AdminConsoleVirtualServer):
    """
    Class for performing FusionCompute Specific Tasks from AdminConsole.
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initializes the XenServer related inputs

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the CS DB object

        """
        super(FusionComputeAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self.datastore = None
        self._full_vm_restore_options = {}

    def _set_restore_options(self):
        """
        Populates full_vm_restore_options for restore jobs.
        """
        for _vm in self._vms:
            self._full_vm_restore_options[_vm]["datastore"] = self.datastore
            self._full_vm_restore_options[_vm]["destination_host"] = self.destination_host

    def full_vm_restore(self):
        """
        Submit and validate Full VM restore job.
        """
        if self._restore_proxy is None:
            self.restore_proxy = self._co_ordinator
        if self._restore_client is None:
            self.restore_client = self.hypervisor
            self.restore_destination_client = self.hvobj
        else:
            if not self.restore_destination_client:
                self.restore_destination_client, \
                    self._restore_instance_type = self._create_hypervisor_object(self.restore_client)

        if not (self.datastore and self.destination_host):
            self.datastore, self.destination_host = self.hvobj.compute_free_resources(self._vms)

        self._full_vm_restore_options = dict.fromkeys(self._vms, {})
        self._set_restore_options()

        self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
        self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
        self.vsa_sc_obj.restore()
        self.select_restore_obj.select_full_vm_restore()

        self.restore_job_id = self.full_vm_restore_obj.fusioncompute_full_vm_restore(
            self._vms,
            self.restore_proxy,
            self.restore_client,
            self.full_vm_in_place,
            self._full_vm_restore_options,
            self.power_on_after_restore,
            self._overwrite_vm,
            self.vm_restore_prefix,
        )

        job_details = self.get_job_status(self.restore_job_id)
        if not job_details:
            raise Exception("Restore job failed. Please check the logs")

        for _vm in self._vms:
            if self.full_vm_in_place:
                restore_vm = _vm
            else:
                restore_vm = str(self.vm_restore_prefix) + _vm
            attempt = 0
            while attempt < 3:
                self.log.info("attempt =" + str(attempt))
                try:
                    self.vm_restore_validation(_vm, restore_vm, self._full_vm_restore_options[_vm])
                    break
                except:
                    attempt = attempt + 1
                    time.sleep(60)
            if attempt >= 3:
                self.vm_restore_validation(_vm, restore_vm)

class XenAdminConsole(AdminConsoleVirtualServer):
    """
    Class for XenServer related operations to be done in admin console
    """

    def __init__(self, instance, driver=None, commcell=None, csdb=None, **kwargs):
        """
        Initializes the XenServer related inputs

        Args:
            instance    (object)   --  object of the instance class

            driver      (object)   --  the browser object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the CS DB object

        """

        super(XenAdminConsole, self).__init__(instance, driver, commcell, csdb, **kwargs)
        self._full_vm_restore_options = None
        self.restore_proxy_input = None


    def full_vm_restore(self, vm_level=False):
        """
        Performs full VM restore for a XenServer subclient

        Args:
            vm_level    (bool):     if the restore should be initiated from VM level

        Raises:
            Exception:
                if full VM restore or validation fails

        """
        try:
            VirtualServerUtils.decorative_log("Performing XenServer Full VM restore")

            if self._restore_proxy is None and self._co_ordinator:
                self.restore_proxy = self._co_ordinator

            self.restore_client = self.hypervisor
            self.restore_destination_client = self.hvobj

            self._full_vm_restore_options = dict.fromkeys(self._vms, {})
            self._set_vm_restore_options()

            if self.restore_from_job:
                """restores from job page of command center"""
                self.navigator.navigate_to_jobs()
                self.job_obj.view_jobs_of_last_3_months()
                self.job_obj.job_restore(self.restore_from_job, search=True)
            else:
                self.navigator.navigate_to_hypervisors()
                self.hypervisor_ac_obj.select_hypervisor(self.hypervisor)
                self.hypervisor_details_obj.open_subclient(self.subclient, self.testcase_obj.tcinputs['BackupsetName'])
                self.vsa_sc_obj.restore()
            self.select_restore_obj.select_full_vm_restore()

            self._submit_restore_job(self._vms)

            for _vm in self._vms:
                if self.full_vm_in_place:
                    restore_vm = _vm
                else:
                    restore_vm = self.vm_restore_prefix + _vm
                self.vm_restore_validation(_vm, restore_vm, restore_options=self._full_vm_restore_options[_vm])

        except Exception as exp:
            self.log.exception("Exception occurred during full VM restore. %s", str(exp))
            raise exp

    def _submit_restore_job(self, vm_list):
        """
        Submits a restore job with the given inputs
        Args:
            vm_list     (list):    VMs to restore

        """
        self.restore_job_id = self.full_vm_restore_obj.xen_full_vm_restore(
            vm_list,
            self.full_vm_in_place,
            proxy=self.restore_proxy,
            destination_server=self.restore_client,
            vm_info=self._full_vm_restore_options,
            power_on=self.power_on_after_restore,
            over_write=self.unconditional_overwrite,
            dest_target=False,
        )

        job_details = self.get_job_status(self.restore_job_id)

    def _set_vm_restore_options(self):
        """
        Sets the VM restore options for each VM to be restored
        Raises:
            Exception:
                if there is any exception in setting the restore options

        """
        for each_vm in self._vms:
            self.restore_destination_client.VMs[each_vm] = self.__deepcopy__(
                self.hvobj.VMs[each_vm])

        _host = ""
        _datastore = ""
        for _vm in self._vms:
            _vm = 'DeleteMe_AC_' + _vm
            _restored_vm = self.restore_destination_client.find_vm(_vm)
            if _restored_vm[0]:
                if _restored_vm[0] == 'Multiple':
                    self.log.exception(f"{_vm} is present in multiple hosts")
                    raise Exception
                _host = _restored_vm[1]
                _datastore = _restored_vm[2]

        if _host:
            if (self.testcase_obj.tcinputs.get('network') and (self.testcase_obj.tcinputs.get('xen_server') == _host or self.destination_host == _host)):
                _network = self.testcase_obj.tcinputs["network"]
            else:
                _network = self.restore_destination_client._get_host_network(_host)
        else:
            if ("storage" not in self.testcase_obj.tcinputs.keys()) and not (self.destination_host and self.destination_datastore):
                resources = self.restore_destination_client.compute_free_resources(self._vms)
                _host = resources[0]
                _datastore = resources[1]
            else:
                _datastore = self.testcase_obj.tcinputs.get("storage")
                _host = self.testcase_obj.tcinputs.get("xen_server")
                _network = self.testcase_obj.tcinputs["network"]

        for _vm in self._vms:
            self._full_vm_restore_options[_vm]['network'] = {}
            self._full_vm_restore_options[_vm]['network']['destination'] = _network
            self._full_vm_restore_options[_vm]['host'] = _host
            self._full_vm_restore_options[_vm]['datastore'] = _datastore
            self._full_vm_restore_options[_vm]['prefix'] = self.vm_restore_prefix
