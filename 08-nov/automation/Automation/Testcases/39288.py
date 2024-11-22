# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
     __init__()      --  initialize TestCase class

     run()           --  run function of this test case

 """
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """TestCase for Aix 1-Touch Backup and Recovery
        This test case does the following
        Step1, Create backupset/Instance for this testcase if it doesn't exist.
        Step2, Create a subclient with onetouch option Enabled
        Step3,  Run an Incremental 1-touch Backup but if it is a new
                       client the first backup runs as Full.
        Step4, Run 1-touch restore job and trigger the restore on the destination machine.
        Step5, Verify the restore completed successfully.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Aix 1-Touch Backup and Recovery"
        self.applicable_os = self.os_list.AIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.tcinputs = {
            'StoragePolicyName': None,
            'ClientName': None,
            'ClientHostname': None,
            'UserName': None,
            'Password': None,
            "automaticClientReboot": None,
            "clone": None,
            "dns_suffix": None,
            "dns_ip": None,
            "clone_machine_gateway": None,
            "clone_machine_netmask": None,
            "clone_ip_address": None,
            "clone_client_hostname": None,
            "clone_client_name": None,
            "onetouch_server_directory": None,
            "onetouch_server": None,
            "backup_onetouch": None
        }

    def run(self):
        """"Runs Aix 1-Touch Backup And Restore"""
        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         backup_onetouch=self.tcinputs['backup_onetouch'],
                                         onetouch_server=self.tcinputs['onetouch_server'],
                                         onetouch_server_directory=self.tcinputs['onetouch_server_directory'])

            if self.tcinputs['backup_onetouch']:
                self.log.info("Starting the Aix 1-touch Backup")
                self.helper.run_onetouch_backup('Incremental')
            last_backup_job = self.subclient.find_latest_job(include_active=False, lookup_time=720)
            self.tcinputs['backup_onetouch_job'] = last_backup_job.job_id
            self.tcinputs['fromTime'] = last_backup_job.start_timestamp
            self.tcinputs['toTime'] = last_backup_job.end_timestamp
            self.tcinputs['run_FS_restore'] = True

            self.log.info("Triggering the Aix -1touch restore Job")
            self.log.info("{0}".format(self.tcinputs))
            restore_job = self.backupset.run_bmr_aix_restore(**self.tcinputs)
            self.log.info("started Aix 1-touch restore with Job_ID: %s ", str(restore_job.job_id))
            if not restore_job.wait_for_completion():
                raise Exception("Aix 1-touch restore failed with error :{0}"
                                .format(restore_job.delay_reason))
            else:
                if self.tcinputs['clone']:
                    self.log.info("Aix 1-Touch restore completed successfully")
                    self.log.info("Test Case Executed Successfully")
                dest_machine = self.tcinputs['ClientHostname']
                machine = Machine(dest_machine, self.commcell)
                result = machine.execute_command("df")
                self.log.info(sorted(result.formatted_output))
                self.log.info("machine logged in successfully after completion of 1-touch restore")
                self.log.info("Aix 1-Touch restore completed successfully")
                self.log.info("Test Case Executed Successfully")

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("Test Case Failed")
            self.status = constants.FAILED
            self.result_string = str(excp)
