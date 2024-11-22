# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
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
import random

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants, qcconstants


class TestCase(CVTestCase):
    """Class for executing Basic Restore Integrity test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Hyper-V Restore Integrity Test Case"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info(
                "-------------------Initialize helper objects------------------------------------"
                )
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            # auto_instance.FBRMA = "fbrhv"
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            job_history = auto_subclient._get_all_backup_jobs()

            jobs_to_restore = []
            for cycle in job_history.keys():
                if '64' in job_history[cycle].keys():
                    job_to_restore = list((job_history[cycle]['64']).keys())[0]
                    selective_job = random.choice(job_history[cycle]['64'][job_to_restore])
                elif '1' in job_history[cycle].keys():
                    job_to_restore = list((job_history[cycle]['1']).keys())[0]
                    selective_job = random.choice(job_history[cycle]['1'][job_to_restore])

                jobs_to_restore.append(job_to_restore)
                jobs_to_restore.append(selective_job)
                if '2' in job_history[cycle].keys():
                    job_to_restore = random.choice(list((job_history[cycle]['2']).keys()))
                    selective_job = random.choice(job_history[cycle]['2'][job_to_restore])
                    jobs_to_restore.append(job_to_restore)
                    jobs_to_restore.append(selective_job)

            try:
                jobs_to_restore.remove('0')
            except ValueError:
                pass

            for job in jobs_to_restore:
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.restore_backup_job = job
                log.info("*" * 10 + "Submitting full VM restore for job {0} ".format(
                    str(job)) + "*" * 10)
                auto_subclient.virtual_machine_restore(vm_restore_options)

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
