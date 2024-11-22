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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing VMConversion from Amazon To Azure RM"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Conversion from Amazon to AzureRM from Streaming FULL backup"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Destination_Virtualization_client": "",
            "networkDisplayName": "",
            "Resourcegroup": "",
        }

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            # auto_subclient.validate_inputs(vm_check=True)
            VirtualServerUtils.decorative_log("Backup")
            backup_option = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_option)
            VirtualServerUtils.decorative_log("VMConversion to AzureRM")
            self.tcinputs["DestinationClient"] = self.tcinputs["Destination_Virtualization_client"]
            dest_auto_subclient = VirtualServerUtils.destination_subclient_initialize(self)

            # perform VMConversion
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(
                dest_auto_subclient, dest_auto_subclient.auto_vsainstance.tcinputs)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.in_place_overwrite = True
            vm_restore_options.source_client_hypervisor = auto_subclient.hvobj
            dest_auto_subclient.hvobj.subnet_id = (
                self.tcinputs['NetworkResourceGroup'], self.tcinputs['networkDisplayName'])

            subnetId = dest_auto_subclient.hvobj.subnet_id
            for vm in auto_subclient.vm_list:
                # """
                restore_job = auto_subclient.subclient.full_vm_conversion_azurerm(self.tcinputs["DestinationClient"],
                                                                                  resource_group=vm_restore_options.Resource_Group,
                                                                                  storage_account=vm_restore_options.Storage_account,
                                                                                  overwrite=vm_restore_options.in_place_overwrite,
                                                                                  power_on=vm_restore_options.power_on,
                                                                                  vm_to_restore=vm,
                                                                                  restore_as_managed=vm_restore_options.restoreAsManagedVM,
                                                                                  datacenter=vm_restore_options.datacenter,
                                                                                  networkDisplayName=self.tcinputs[
                                                                                      'networkDisplayName'],
                                                                                  networkrsg=self.tcinputs[
                                                                                      'NetworkResourceGroup'],
                                                                                  destsubid=dest_auto_subclient.hvobj.subscription_id,
                                                                                  subnetId=subnetId,
                                                                                  copy_precedence=0
                                                                                  )

                self.log.info("Conversion job is :{} ".format(restore_job.job_id))
                if not restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run VM  restore  job with error: " +
                        str(restore_job.delay_reason)
                    )
                if "one or more errors" in restore_job.status.lower():
                    self.log.error("Restore job completed with one or more errors")
                self.log.info("Restore completed successfully with Job Id: %s" % restore_job.job_id)
                # """
                dest_auto_subclient.vm_conversion_validation(auto_subclient,
                                                             vm_restore_options,
                                                             backup_option.backup_type)

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            auto_subclient.post_restore_clean_up(vm_restore_options, status=self.status)
