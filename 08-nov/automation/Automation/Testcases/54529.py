# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
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
import os
import re
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerConstants, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing VMConversion from VMware To Google Cloud"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Conversion from VMware to Google Cloud"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONGCCLOUD
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Destination_Virtualization_client": ""}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Full VM Backup")
            backup_option = OptionsHelper.BackupOptions(auto_subclient)
            for vm in auto_subclient.hvobj.VMs:
                auto_subclient.hvobj.VMs[vm].update_vm_info(prop='All')
            backup_job = auto_subclient.subclient.backup(backup_option.backup_type,
                                                         backup_option.run_incr_before_synth,
                                                         backup_option.incr_level,
                                                         backup_option.collect_metadata,
                                                         backup_option.advance_options)
            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run backup with error: " +
                    str(backup_job.delay_reason))
            self.log.info("Backup completed successfully with Job Id: {}".format(backup_job.job_id))

            VirtualServerUtils.decorative_log("VMConversion to Google Cloud")
            # create SDK and vshelper objects
            google_cloud_client = self.tcinputs["Destination_Virtualization_client"]
            self.client = self.commcell.clients.get(google_cloud_client)
            self.agent = self.client.agents.get('Virtual Server')
            instancekeys = next(iter(self.agent.instances.all_instances))
            self.instance = self.agent.instances.get(instancekeys)
            backupsetkeys = next(iter(self.instance.backupsets.all_backupsets))
            self.backupset = self.instance.backupsets.get(backupsetkeys)
            self.subclient = self.backupset.subclients.get(self.tcinputs.get('sckey'))
            dest_auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            dest_auto_client = VirtualServerHelper.AutoVSAVSClient(dest_auto_commcell, self.client)
            dest_auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                dest_auto_client, self.agent, self.instance)
            dest_auto_backupset = VirtualServerHelper.AutoVSABackupset(dest_auto_instance,
                                                                       self.backupset)
            dest_auto_subclient = VirtualServerHelper.AutoVSASubclient(dest_auto_backupset,
                                                                       self.subclient)

            # perform VMConversion
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(dest_auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            restore_job = auto_subclient.subclient.full_vm_conversion_googlecloud(google_cloud_client,
                                                                                  esx_host=self.tcinputs.get('esx_host'),
                                                                                  vcenter_client=self.tcinputs.get('vcenter_client'),
                                                                                  esx_server=self.tcinputs.get('esx_server'),
                                                                                  vmSize=self.tcinputs.get('vmsize'),
                                                                                  nics=self.tcinputs.get('nics'),
                                                                                  datacenter=self.tcinputs.get('datacenter'),
                                                                                  projectId=self.tcinputs.get('ProjectID'),
                                                                                  overwrite=vm_restore_options.in_place_overwrite,
                                                                                  power_on=vm_restore_options.power_on)

            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run VM  restore  job with error: " +
                    str(restore_job.delay_reason)
                )
            self.log.info("Restore completed successfully with Job Id: {}".format(restore_job.job_id))

            vm_names_dict = {}
            for each_vm in auto_subclient.vm_list:
                vm_names_dict[each_vm.lower().replace("_", "")] = each_vm

            dest_auto_subclient._backed_up_vms = vm_names_dict.keys()
            for each_vm in auto_subclient.vm_list:
                auto_subclient.vm_restore_validation(each_vm, each_vm.lower().replace("_", ""), vm_restore_options, "All")



        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
