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




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Open Stack backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Openstack vcpus quota validation"
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
            projectname = self.tcinputs.get(
                'destination_project_name', None)
            project_name = self.tcinputs.get(
                'project_name', None)
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
            self.log.info('---Resetting  quota limits for a project to original limits----')
            try:
                self.hvobj.OpenStackHandler.reset_quota_limits(project_name)
                self.hvobj.OpenStackHandler.reset_volume_limits(project_name)
                self.hvobj.OpenStackHandler.reset_volumesnapshot_limits(project_name)
                self.hvobj.OpenStackHandler.reset_volumesnapsize_limits(project_name)
                self.log.info('Reset  quota limits for the project successfully'+str(project_name))
            except Exception as err:
                self.log.error('Failed to reset  quota limits for the project'+str(project_name))
                raise Exception
            self.log.info('-----Getting quota limits for a project-----')
            try:
                quotalimit1 = self.hvobj.OpenStackHandler.get_quota_limits(project_name)
                self.log.info('Got vcups quota limits for the project'+str(project_name))
            except Exception as err:
                self.log.error('Failed to get vcups quota limits for the project'+str(project_name))
                raise Exception
            self.log.info('-----setting vcups quota limits for a project-----')
            try:
                for each_vm in self.subclient._vmContent['children']:
                    self.hvobj.OpenStackHandler.set_quota_vcpus(projectname, each_vm['displayName'])
                    self.log.info(
                        'set vcups quota limits for the project successfully'+str(project_name))
            except Exception as err:
                self.log.error(
                    'Failed to set vcups quota limits for the project'+str(project_name))
                raise Exception
            self.log.info("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            try:
                self.log.info(
                    "-" * 15 + " FULL VM out of Place restores " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                self.hvobj.OpenStackHandler.projectName = self.hvobj.destination_project_name
                vm_restore_options.dest_client_hypervisor.OpenStackHandler.projectName = self.hvobj.destination_project_name
                vm_restore_job = self.subclient.full_vm_restore_out_of_place(
                    vm_to_restore=vm_restore_options.auto_subclient.vm_list,
                    power_on=vm_restore_options.power_on_after_restore,
                    destination_client=vm_restore_options._destination_pseudo_client,
                    proxy_client=vm_restore_options.proxy_client,
                    copy_precedence=vm_restore_options.copy_precedence,
                    datastore=vm_restore_options.restoreObj["Datastore"],
                    securityGroups=vm_restore_options.restoreObj["securityGroups"],
                    esx_host=vm_restore_options.restoreObj["esxHost"],
                    esx_server=vm_restore_options.restoreObj["esxServerName"],
                    datacenter=vm_restore_options.restoreObj["Datacenter"],
                    cluster=vm_restore_options.restoreObj["Cluster"])
                if vm_restore_job:
                    self.log.info("Restore job is : " + str(vm_restore_job.job_id))
                    if vm_restore_job.wait_for_completion():
                        raise Exception("VM restore job {0} completed even after quota limit exceeded: {1}".format(
                            vm_restore_job.job_id, vm_restore_job.delay_reason))
                    else:
                        self.log.info("VM restore job {0} failed as expected: {1}".format(
                            vm_restore_job.job_id, vm_restore_job.delay_reason))
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            self.log.info("checking for failure reason on database")
            for each_vm in auto_subclient.vm_list:
                query = "SELECT attrVal from APP_VMProp where attrName = 'vmFailureReason' " \
                     "and  jobId = "+vm_restore_job.job_id+" and vmclientid = (select id from app_client where name = '"+each_vm+"')"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
            failurereason = 'Could not create VM, Quota exceeded for cores'
            if output != ():
                if failurereason not in output[0][0]:
                    self.log.error('---Failed reason not updated on Database--')
                    raise Exception
            self.log.info('--Failed reason updated on the Database')
            self.log.info('---Reseting back quota limits for a project to original limits----')
            try:
                self.hvobj.OpenStackHandler.reset_quota_limits(project_name)
                self.log.info(
                    'Reseting vcpus quota limits for the project successfully'+str(project_name))
            except Exception as err:
                self.log.error(
                    'Failed to reset vcpus quota limits for the project'+str(project_name))
                raise Exception
            self.log.info(
                '---checking source VM existence ----')
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
            self.log.info(
                '---validating if quota limits are set to original limits----')
            try:
                quotalimit2 = self.hvobj.OpenStackHandler.get_quota_limits(project_name)
                if quotalimit1 == quotalimit2:
                    self.log.info('Validation successful')
            except Exception as err:
                self.log.error('---Quota limits are not set to original limits---'+str(project_name))
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
