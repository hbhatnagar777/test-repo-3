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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Conversion from AHV to VMware"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Virtual server]- AHV to VMware conversion from STREAMING Full job"
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {
            "Destination_Virtualization_client": "",
            "Destination_os_name": "",
            "DestinationInstance": ""}


    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            for vm in auto_subclient.hvobj.VMs:
                auto_subclient.hvobj.VMs[vm].update_vm_info('All', True, True)
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("-----VMConversion from AHV to VMware------")
            self.tcinputs["DestinationClient"] = self.tcinputs["Destination_Virtualization_client"]
            dest_auto_subclient = VirtualServerUtils.destination_subclient_initialize(self)

            #perform VMConversion
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(dest_auto_subclient, dest_auto_subclient.
                                                                    auto_vsainstance.tcinputs)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            restore_job = auto_subclient.subclient.full_vm_conversion_vmware(self.tcinputs["DestinationClient"],
                                                                             destination_os_name=
                                                                             self.tcinputs['Destination_os_name'],
                                                                             esx_host=vm_restore_options._host[0],
                                                                             datastore=vm_restore_options._datastore,
                                                                             overwrite=
                                                                             vm_restore_options.unconditional_overwrite,
                                                                             power_on=vm_restore_options.power_on,
                                                                             proxy_client=
                                                                             vm_restore_options.proxy_client,
                                                                             destination_network=
                                                                             vm_restore_options._network)

            if not restore_job.wait_for_completion():
                raise Exception("Failed to run VM  restore  job with error: "
                                + str(restore_job.delay_reason))
            VirtualServerUtils.decorative_log("Restore completed successfully with Job Id: %s"
                                              % restore_job.job_id)
            dest_auto_subclient.vm_conversion_validation(auto_subclient, vm_restore_options, backup_type="FULL")

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