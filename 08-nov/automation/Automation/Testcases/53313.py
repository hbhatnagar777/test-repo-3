# -*- coding: utf-8 -*-

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

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing conversion from VMWare to HyperV"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware to Hyper-V - Snap BackupCopy - Windows Proxy - FULL - cvpysdk - 53313"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONORACLEVM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Destination_Virtualization_client": "",
            "Destination_network": ""
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            # """
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_type = "FULL"
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("VMWare Conversion to Hyperv")

            self.tcinputs["DestinationClient"] = self.tcinputs["Destination_Virtualization_client"]
            dest_auto_subclient = VirtualServerUtils.destination_subclient_initialize(self)
            host_dict = {}
            proxy_list = dest_auto_subclient.auto_vsainstance.proxy_list
            for each_proxy in proxy_list:
                host_name = dest_auto_subclient.auto_commcell.get_hostname_for_client(each_proxy)
                host_dict[each_proxy] = host_name

            _datastore_dict = dest_auto_subclient.auto_vsainstance.hvobj._get_datastore_priority_list(proxy_list,
                                                                                                      host_dict)
            _resource = [key for key, value in _datastore_dict.items()][0]

            # perform VMConversion
            dest_network = self.tcinputs["Destination_network"]
            self.tcinputs["RestoreHyperVServer"] = self.tcinputs.get("RestoreHyperVServer", _resource.split("-")[0])
            self.tcinputs["DestinationPath"] = self.tcinputs.get("DestinationPath", _resource.split("-")[1])
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(
                dest_auto_subclient, dest_auto_subclient.auto_vsainstance.tcinputs)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.in_place_overwrite = True

            cc_precedence = [int(auto_subclient.auto_commcell.find_snap_copy_id(
                auto_subclient.storage_policy_id)), (int(auto_subclient.auto_commcell.find_primary_copy_id(
                auto_subclient.storage_policy_id)))]

            for each_preceedence in cc_precedence:
                for each_vm in auto_subclient.vm_list:
                    # """
                    restore_job = auto_subclient.subclient.full_vm_conversion_hyperv(
                        vm_to_restore=each_vm,
                        hyperv_client=self.tcinputs["DestinationClient"],
                        DestinationPath=vm_restore_options.destination_path,
                        proxy_client=vm_restore_options.proxy_client,
                        destination_network=dest_network,
                        copy_precedence=each_preceedence
                    )

                    if not restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run VM  restore  job with error: " + str(restore_job.delay_reason))

                    self.log.info(
                        "Restore completed successfully with Job Id: %s" %
                        restore_job.job_id)
                    # """

                    dest_auto_subclient.vm_conversion_validation(auto_subclient, vm_restore_options,
                                                                 backup_options.backup_type)

        except Exception as exp:
            log.exception(
                "Exception details: {0}".format(exp))
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            auto_subclient.post_restore_clean_up(vm_restore_options, status=self.status)
