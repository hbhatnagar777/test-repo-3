# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate incremental after changing the storage policy.

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
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify Incremental Backup after changing Storage policy"
        self.helper = None
        self.backupset = None
        self.subclient = None
        self.machine = None
        self.test_path = None
        self.client_machine = None
        self.slash_format = ""
        self.restore_path = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "StoragePolicyName": None,
            "StoragePolicyName2": None,
            "TestPath": None
        }

    def setup(self):
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.machine = Machine(self.client)

    def run(self):
        try:
            self.log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            """
            If the given two inputs for StoragePolicy is same then fail the testcase.
            """
            if (self.tcinputs["StoragePolicyName2"] == self.tcinputs["StoragePolicyName"]):
                self.log.error("The two storage policies are same.")
                self.status = constants.FAILED
            else:
                slash_format = self.slash_format
                sc_name = '_'.join(('subclient', str(self.id)))
                """
                Creating a subclient using StoragePolicyName
                """
                self.helper.create_subclient(name=sc_name, storage_policy=self.tcinputs["StoragePolicyName"],
                                             content=[self.tcinputs["TestPath"]])
                subclient_content = [self.machine.join_path(self.test_path, sc_name)]
                run_path = self.machine.join_path(subclient_content[0], str(self.runid))
                full_con_path = self.machine.join_path(run_path, "full")
                inc_con_path = self.machine.join_path(run_path, "inc")
                restore_path_full = self.machine.join_path(self.test_path,"cvauto_tmp_full",sc_name,str(self.runid))
                restore_path_incr = self.machine.join_path(self.test_path, "cvauto_tmp_incr", sc_name, str(self.runid))

                full_content_run_path = run_path
                full_content_tmp_path = self.machine.join_path(self.test_path,"cvauto_tmp_incr")

                self.helper.generate_testdata(file_extensions=['.txt'], path=full_con_path)
                job_full = self.helper.run_backup(backup_level="Full", wait_to_complete=True)[0]
                """
                Changing the storage policy from StoragePolicyName to StoragePolicyName2
                """
                self.log.info("Changing the storage policy from to %s", self.tcinputs["StoragePolicyName2"])
                self.helper.update_subclient(storage_policy=self.tcinputs["StoragePolicyName2"])
                self.log.info("Change done")
                self.helper.add_new_data_incr(incr_path=inc_con_path, slash_format=self.slash_format)
                job_incr = self.helper.run_backup(backup_level="Incremental", wait_to_complete=True)[0]

                self.helper.run_restore_verify(
                    slash_format,
                    full_con_path,
                    restore_path_full, "full", job_full)
                self.log.info("..Restore for FULL Job is validated..")

                self.helper.run_restore_verify(
                    slash_format,
                    inc_con_path,
                    restore_path_incr, "inc", job_incr)
                self.log.info("..Restore for INCR Job is validated..")

                self.helper.run_restore_verify(
                    slash_format,
                    full_content_run_path,
                    full_content_tmp_path, str(self.runid))

                self.log.info("..Restore for all data is validated..")

                if self.cleanup_run:
                    self.client_machine.remove_directory(self.test_path)
                    self.log.info('Deleting backupset: %s', self.backupset_name)
                    self.instance.backupsets.delete(self.backupset_name)

        except Exception as excp:
            self.log.info("Failed with error %s", excp)
            self.status = constants.FAILED