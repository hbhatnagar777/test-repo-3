# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils, VMHelper
from AutomationUtils import constants
import time

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Open Stack backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Openstack volumesnapshot restore quota validation"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            self.hvobj = auto_backupset.auto_vsainstance.hvobj
            self.hvobj.destination_project_name = self.tcinputs.get(
                'destination_project_name', None)
            self.hvobj.Source_Security_Grp = self.tcinputs.get(
                'Source_Security_Grp', None)
            self.hvobj.DestinationZone = self.tcinputs.get(
                'DestinationZone', None)
            projectname = self.tcinputs.get('destination_project_name', None)
            project_name = self.tcinputs.get('project_name', None)
            self.log.info(
                '---Getting config values before setting quota----')
            try:
                vm_details1 = []
                for each_vm in self.subclient._vmContent['children']:
                    osobj = VMHelper.OpenStackVM(self.hvobj, each_vm['displayName'])
                    osobj.update_vm_info()
                    vm_details1.append(osobj.ram)
                    vm_details1.append(osobj.vmflavor)
                    vm_details1.append(osobj.vcpus)
                    vm_details1.append(osobj.DiskList)
                self.log.info('successfully got config values')
            except Exception as err:
                self.log.error('---getting config values failed---')
                raise Exception
            self.log.info(
                '---Getting config values before setting quota----')
            try:
                for each_vm in self.subclient._vmContent['children']:
                    ram1 = self.hvobj.OpenStackHandler.get_ram(each_vm['displayName'])
                    flavor1 = self.hvobj.OpenStackHandler.get_vmflavor(each_vm['displayName'])
                    vcpus1 = self.hvobj.OpenStackHandler.get_vcpus(each_vm['displayName'])
                    uuid1 = self.hvobj.OpenStackHandler.get_uuid(each_vm['displayName'])
                    vmdetails1 = self.hvobj.OpenStackHandler.get_instance_details(uuid1)
                self.log.info('successfully got config values')
            except Exception as err:
                self.log.error('---getting config values failed---')
                raise Exception
            self.log.info("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            self.log.info(
                '-----Getting volume limits for a project-----')
            try:
                quotalimit1 = self.hvobj.OpenStackHandler.get_volume_limits(project_name)
                self.log.info('Got volume snapshot quota limits for the project'+str(project_name))
            except Exception as err:
                self.log.error(
                    'Failed to get volume snapshot quota limits for the project'+str(project_name))
                raise Exception
            self.log.info('-----setting volume snapshot quota limits for a project-----')
            try:
                self.hvobj.OpenStackHandler.set_quota_volume_snapshot(project_name)
                self.log.info(
                    'set volume snapshot quota limits for the project successfully'+str(project_name))
            except Exception as err:
                self.log.error(
                    'Failed to set volume snapshot quota limits for the project'+str(project_name))
                raise Exception
            try:
                self.log.info(
                    "-" * 15 + " FULL VM out of Place restores " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                self.hvobj.OpenStackHandler.projectName = self.hvobj.destination_project_name
                vm_restore_options.dest_client_hypervisor.OpenStackHandler.projectName = self.hvobj.destination_project_name
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            self.log.info(
                '---deleting restored VM and volume from openstack server to free space----')
            try:
                for each_vm in self.subclient._vmContent['children']:
                    uuid = self.hvobj.OpenStackHandler.get_uuid("del"+each_vm['displayName'])
                    volumelist = self.hvobj.OpenStackHandler.get_volume_attachments(uuid)
                    self.hvobj.OpenStackHandler.delete_vm("del"+each_vm['displayName'])
                    time.sleep(60)
                for each_vol in volumelist:
                    volumelistfin = each_vol['id']
                    self.hvobj.OpenStackHandler.delete_volume(volumelistfin)
                    self.log.info('delete volume and instance successfully')
            except Exception as err:
                self.log.error('delete volume and instance failed')
                raise Exception
            self.log.info(
                '---Reseting back volume limits for a project to original limits----')
            try:
                self.hvobj.OpenStackHandler.reset_volume_limits(project_name)
                self.hvobj.OpenStackHandler.reset_volumesnapshot_limits(project_name)
                self.hvobj.OpenStackHandler.reset_volumesnapsize_limits(project_name)
                self.log.info(
                    'Reseting volume quota limits for the project successfully'+str(project_name))
            except Exception as err:
                self.log.error(
                    'Failed to reset volume quota limits for the project'+str(project_name))
                raise Exception
            self.log.info('---checking source VM existence ----')
            try:
                listinstances = self.hvobj.OpenStackHandler.get_instance_list()
                for each_vm in self.subclient._vmContent['children']:
                    if each_vm['displayName'] not in listinstances.keys():
                        raise Exception
                self.log.info('---source VM  present on Openstack server----')
            except Exception as err:
                self.log.error('source VMs not on Openstack server')
                raise Exception
            self.log.info(
                '---Getting config values after restore job----')
            try:
                vm_details2 = []
                for each_vm in self.subclient._vmContent['children']:
                    print("true")
                    osobj = VMHelper.OpenStackVM(self.hvobj, each_vm['displayName'])
                    osobj.update_vm_info()
                    vm_details2.append(osobj.ram)
                    vm_details2.append(osobj.vmflavor)
                    vm_details2.append(osobj.vcpus)
                    vm_details2.append(osobj.DiskList)
                self.log.info('successfully got config values')
            except Exception as err:
                self.log.error('---getting config values failed---')
                raise Exception
            self.log.info('--config validation---')
            try:
                if  vm_details1 == vm_details2:
                    self.log.info("------config validation passed----")
            except Exception as err:
                self.log.error('---config validation failed---')
                raise Exception
            self.log.info('---validating if volume limits are set to original limits----')
            try:
                quotalimit2 = self.hvobj.OpenStackHandler.get_volume_limits(project_name)
                if quotalimit1 == quotalimit2:
                    self.log.info('Validation successful')
            except Exception as err:
                self.log.error(
                    '---Quota limits are not set to original limits---'+str(project_name))
                raise Exception
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED