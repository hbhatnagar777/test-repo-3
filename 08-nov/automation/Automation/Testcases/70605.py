# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import os

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA GCP backup and Restore to AzureRM test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Google cloud Full Snap Backup and Restore to AzureRM Cases"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONGCCLOUD
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {
            "ProjectID": None
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Snap Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            try:
                azure_client = self.tcinputs["DestinationClient"]
                self.client = self.commcell.clients.get(azure_client)
                self.agent = self.client.agents.get('Virtual Server')
                self.instance = self.agent.instances.get('Azure Resource Manager')
                self.backupset = self.instance.backupsets.get('defaultBackupSet')
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

                # perform VMConversion
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(dest_auto_subclient, self)

                try:
                    VirtualServerUtils.decorative_log("FULL VM out of Place restores from GCP snap to Azure RM")
                    vm_restore_options.power_on_after_restore = True
                    vm_restore_options.in_place_overwrite = True
                    restore_job = auto_subclient.subclient.full_vm_conversion_azurerm(azure_client,
                                                                                      resource_group=vm_restore_options.Resource_Group,
                                                                                      storage_account=vm_restore_options.Storage_account,
                                                                                      overwrite=vm_restore_options.in_place_overwrite,
                                                                                      power_on=vm_restore_options.power_on,
                                                                                      proxy_client=vm_restore_options.proxy_client,
                                                                                      restore_as_managed=True,
                                                                                      subnetId=self.tcinputs.get(
                                                                                          "SubnetId"),
                                                                                      datacenter=self.tcinputs.get(
                                                                                          "region"))

                    if not restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run VM  restore  job with error: " +
                            str(restore_job.delay_reason)
                        )

                    raise Exception(
                        "Snap restores not supported for conversion but it was success. Job Id: %s" % restore_job.job_id)

                except Exception as exp:
                    self.log.info(str(exp))

                try:
                    VirtualServerUtils.decorative_log("FULL VM out of Place restores from GCP backup copy to Azure RM")
                    # Passing copy_precedence=2 to browse from backup_copy
                    restore_job = auto_subclient.subclient.full_vm_conversion_azurerm(azure_client,
                                                                                      resource_group=vm_restore_options.Resource_Group,
                                                                                      storage_account=vm_restore_options.Storage_account,
                                                                                      overwrite=vm_restore_options.in_place_overwrite,
                                                                                      power_on=vm_restore_options.power_on,
                                                                                      copy_precedence=2,
                                                                                      proxy_client=vm_restore_options.proxy_client,
                                                                                      restore_as_managed=True,
                                                                                      subnetId=self.tcinputs.get(
                                                                                          "SubnetId"),
                                                                                      datacenter=self.tcinputs.get(
                                                                                          "region"))

                    if not restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run VM  restore  job with error: " +
                            str(restore_job.delay_reason)
                        )

                    self.log.info(
                        "Restore completed successfully from GCP backup copy with Job Id: %s" % restore_job.job_id)

                except Exception as exp:
                    self.test_individual_status = False
                    self.test_individual_failure_message = str(exp)

            except Exception as exp:
                log.error('Failed with error: ' + str(exp))
                self.result_string = str(exp)
                self.status = constants.FAILED


        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if not self.test_individual_status:
                    self.result_string = self.test_individual_failure_message
                    self.status = constants.FAILED

                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
