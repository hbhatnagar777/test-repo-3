# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2018 Commvault Systems, Inc.
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
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing conversion from VMWare to HyperV"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware to Hyper-V - Backup Copy - Unix Proxy - INCR and Synth - cvpysdk - 53314"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONORACLEVM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Destination_Virtualization_client": "",
            "Destination_network": "",
            "Destination_drive": ""
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info(
                "-------------------Initialize helper objects------------------------------------"
            )
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            # """
            log.info(
                "----------------------------------------Backup-----------------------------------")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            log.info(
                "--------------------VMWare Conversion to Hyperv---------------------")

            hyperv_client = self.tcinputs["Destination_Virtualization_client"]

            dest_auto_subclient = VirtualServerUtils.destination_subclient_initialize(self)

            # perform VMConversion
            dest_network = self.tcinputs["Destination_network"]
            dest_drive = self.tcinputs["Destination_drive"]
            esx_host = self.tcinputs["Esx_host"]
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(
                dest_auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.in_place_overwrite = True
            vm_restore_options.browse_from_backup_copy = True

            restore_job = auto_subclient.subclient.full_vm_conversion_hyperv(
                hyperv_client,
                hyperv_server=hyperv_client,
                esx_host=esx_host,
                destination_path=vm_restore_options.destination_path,
                overwrite=vm_restore_options.in_place_overwrite,
                power_on=vm_restore_options.power_on,
                network=dest_network,
                drive=dest_drive
            )

            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run VM  restore  job with error: " + str(restore_job.delay_reason))

            self.log.info(
                "Restore completed successfully with Job Id: %s" %
                restore_job.job_id)

            VirtualServerHelper.AutoVSASubclient.vm_conversion_validation(auto_subclient, dest_auto_subclient,
                                                                          vm_restore_options,
                                                                          backup_options.backup_type)

        except Exception as exp:
            log.exception(
                "Exception details: {0}".format(exp))
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
