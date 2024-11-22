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


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Preset: Full Backup and Full VM Restore"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing {} testcase".format(self.id))

            _backup_jobs = self.subclient.backup('FULL')
            if not (isinstance(_backup_jobs, list)):
                _backup_jobs = [_backup_jobs]
            for _backup_job in _backup_jobs:
                self.log.info("***** Starting backup Job : {0} *****".format(_backup_job.job_id))
                if not _backup_job.wait_for_completion():
                    raise Exception("Failed to run backup with error: {0}"
                                    .format(_backup_job.delay_reason))
            self.log.info("***** Backup job/jobs completed successfully *****")

            self.log.info("*****Full Vm out of place restore *****")
            _restore_job = self.subclient.full_vm_restore_out_of_place(
                proxy_client=self.tcinputs["Proxy_Client"],
                vcenter_client=self.tcinputs.get("Vcenter_Client", self.client.client_name),
                datastore=self.tcinputs["Datastore"],
                esx_host=self.tcinputs["Host"],
                network=self.tcinputs.get("Network"),
                power_on=False)
            self.log.info("***** Starting backup Job : {0} *****".format(_restore_job.job_id))
            if not _restore_job.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}"
                                .format(_restore_job.delay_reason))
            self.log.info("***** Restore completed successfully *****")

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
