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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerConstants
from AutomationUtils import constants

class TestCase(CVTestCase):
    """Class for executing VMConversion from Hyper-V To AzureRM"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Conversion from AzureRM to Azurestack"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Destination_Virtualization_client" : ""}

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.log.info(
                "-------------------Initialize helper objects------------------------------------"
                )
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            # """
            self.log.info(
                "----------------------------------------Backup-----------------------------------"
                )
            backup_option = OptionsHelper.BackupOptions(auto_subclient)
            backup_job = auto_subclient.subclient.backup(backup_option.backup_type,
                                                         backup_option.run_incr_before_synth,
                                                         backup_option.incr_level,
                                                         backup_option.collect_metadata,
                                                         backup_option.advance_options)

            if not backup_job.wait_for_completion():
                raise Exception(
                    "Failed to run backup with error: " +
                    str(backup_job.delay_reason))

            self.log.info("Backup completed successfully with Job Id: %s" %backup_job.job_id)

            # """

            self.log.info("--------------------VMConversion to AzureRM---------------------")

            azure_client = self.tcinputs["Destination_Virtualization_client"]
            self.client = self.commcell.clients.get(azure_client)
            self.agent = self.client.agents.get('Virtual Server')
            instancekeys = next(iter(self.agent.instances.all_instances))
            self.instance = self.agent.instances.get(instancekeys)
            backupsetkeys = next(iter(self.instance.backupsets.all_backupsets))
            self.backupset = self.instance.backupsets.get(backupsetkeys)
            sckeys = next(iter(self.backupset.subclients.all_subclients))
            self.subclient = self.backupset.subclients.get(sckeys)
            dest_auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            dest_auto_client = VirtualServerHelper.AutoVSAVSClient(dest_auto_commcell, self.client)
            dest_auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                dest_auto_client, self.agent, self.instance)
            dest_auto_backupset = VirtualServerHelper.AutoVSABackupset(dest_auto_instance,
                                                                       self.backupset)
            dest_auto_subclient = VirtualServerHelper.AutoVSASubclient(dest_auto_backupset,
                                                                       self.subclient)

            #perform VMConversion
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(dest_auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.in_place_overwrite = True
            restore_job = auto_subclient.subclient.full_vm_conversion_azurerm(azure_client,
                                               resource_group=vm_restore_options.Resource_Group,
                                               storage_account=vm_restore_options.Storage_account,
                                               overwrite=vm_restore_options.in_place_overwrite,
                                               power_on=vm_restore_options.power_on)

            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run VM  restore  job with error: " +
                    str(restore_job.delay_reason)
                )

            self.log.info("Restore completed successfully with Job Id: %s" %restore_job.job_id)

            vm_names_dict = {}
            for each_vm in auto_subclient.vm_list:
                vm_names_dict["Delete" + each_vm] = each_vm

            dest_auto_subclient.hvobj.update_hosts()
            dest_auto_subclient.hvobj.VMs = list(vm_names_dict.keys())
            for each_vm in dest_auto_subclient.hvobj.VMs:
                dest_auto_subclient.hvobj.VMs[each_vm].update_vm_info('Basic', os_info=True, force_update=True)
                restore_obj = dest_auto_subclient.hvobj.VMs[each_vm]

                if re.match(VirtualServerConstants.Ip_regex, "%s" % restore_obj.IP):
                    raise Exception("The IP address of the restored VM is not of the proper format"
                                    ". Boot validation failed.")


        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
