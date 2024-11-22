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
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Conversion from Azure to Hyper-V"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Virtual server]- Conversion from Azure to Hyper-V from Incr backup"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'DestinationClient': None,
            'Network': None}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("-----VMConversion from Azure to Hyperv-V------")
            hyperv_client = self.tcinputs["DestinationClient"]
            self.client = self.commcell.clients.get(hyperv_client)
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
            vm_restore_options.unconditional_overwrite = True
            restore_job = auto_subclient.subclient.full_vm_conversion_hyperv(hyperv_client,
                                                                             proxy_client=vm_restore_options.proxy_client,
                                                                             DestinationPath=vm_restore_options.destination_path,
                                                                             overwrite=vm_restore_options.unconditional_overwrite,
                                                                             vm_to_restore=auto_subclient.vm_list,
                                                                             power_on=vm_restore_options.power_on,
                                                                             destination_network=self.tcinputs["Network"])

            if not restore_job.wait_for_completion():
                raise Exception("Failed to run VM  restore  job with error: "
                                +str(restore_job.delay_reason))

            VirtualServerUtils.decorative_log("Restore completed successfully with Job Id: %s"
                                              %restore_job.job_id)

            vm_names_dict = {}
            for each_vm in auto_subclient.vm_list:
                vm_names_dict["del"+each_vm] = each_vm

            dest_auto_subclient._backed_up_vms = vm_names_dict.keys()
            for each_vm in auto_subclient.vm_list:
                auto_subclient.vm_restore_validation(each_vm, "del"+each_vm, vm_restore_options)

        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED