# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2019 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case




"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from MediaAgents.MAUtils.mahelper import MMHelper

import time


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "IBM i VTL Aux Copy basic test"
        self.tcinputs = {
            "RestoreClientPrimaryCopy_name": None,
            "RestoreClientPrimaryCopy_host": None,
            "RestoreClientSecondaryCopy_name": None,
            "RestoreClientSecondaryCopy_host": None,
            "StoragePolicyName": None,
            "TapeSizeGB": None,
            "TestPath": '/autotest/',
            "UserName": None,
            "Password": None
        }
        self.helper = None
        self.mmhelper = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_name = None
        self.content_path = None
        self.storage_policy = None
        self.primary_copy_id = None
        self.secondary_copy_id = None
        self.client_machine = None
        self.username = None
        self.password = None
        self.IBMiMode = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.log.info("Preparing test case {0} ({1})".format(self.id, self.name))

            self.backupset_name = 'backupset_' + str(self.id)
            self.subclient_name = 'subclient_' + str(self.id) + "_auxcopy"
            self.storage_policy_name = self.tcinputs["StoragePolicyName"]

            FSHelper.populate_tc_inputs(self)

            self.mmhelper = MMHelper(self)

            if self.tcinputs['TestPath'] is None:
                self.content_path = "/autotest/B" + str(self.id)
            else:
                if self.tcinputs['TestPath'][-1] == '/':
                    self.content_path = self.tcinputs['TestPath'] + "B" + str(self.id)
                else:
                    self.content_path = self.tcinputs['TestPath'] + "/B" + str(self.id)

        except Exception as exp:
            self.log.error('Failed to setup test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing test case {0}".format(self.id))
            self.log.info(self.name)

            # create backupset and subclient
            self.helper.create_backupset(self.backupset_name, delete=True)

            subclient_content = [self.content_path]

            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy_name,
                                         content=subclient_content,
                                         data_readers=1,
                                         allow_multiple_readers=False,
                                         delete=True)

            if self.IBMiMode == "VTLParallel":
                self.log.info("Enable multiple drives option for VTL Backup")
                self.helper.set_vtl_multiple_drives()

            # create data
            self.populateData()

            # note copy ids
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
            if self.storage_policy is None:
                raise Exception("Storage Policy {0} not found.".format(self.storage_policy_name))

            for copy in self.storage_policy.copies:
                copy_id = int(self.storage_policy.get_copy_precedence(copy))
                # copy_id = int(self.mmhelper.get_copy_id( self.storage_policy_name, copy ))
                self.log.info("For copy '{0}' copy_id is {1}".format(copy, copy_id))
                if copy != 'primary':
                    self.secondary_copy_id = copy_id
                    sec_copy_name = copy
                else:
                    self.primary_copy_id = copy_id
            if self.primary_copy_id is None:
                raise Exception(
                    "Unable to identify Primary copy. Primary copy must have name 'Primary'"
                )

            # Run 2 cycles
            for cycle in range(2):
                backup_job = 0
                # Run FULL backup
                self.log.info("Running full backup {0}...".format(cycle + 1))
                job = self.subclient.backup("FULL")
                self.log.info("Backup job: " + str(job.job_id))
                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run FULL backup with error: {0}".format(job.delay_reason)
                    )
                self.log.info("Backup job {0} completed.".format(job.job_id))
                backup_job = job.job_id

                self.log.info("VALIDATION: backup job {0} Primary Copy".format(backup_job))
                # validate backup
                retcode = self.validateData(self.primary_copy_id, self.tcinputs["RestoreClientPrimaryCopy_name"],
                                            self.tcinputs["RestoreClientPrimaryCopy_host"])
                if retcode:
                    self.log.info("Validation success")
                else:
                    raise Exception(
                        "Backup job {0} Primary Copy validation failed".format(backup_job)
                    )

                # Run aux copy
                # Aux Copy job can be already started by automatic schedule.
                # We must detect this and retry. We should start own Aux Copy job to be 
                # sure data from our job copied to secondary copy.
                self.log.info("Running Aux Copy job {0}...".format(cycle + 1))
                while True:
                    aux_job = self.storage_policy.run_aux_copy(sec_copy_name,
                                                               None,
                                                               True,
                                                               1)
                    self.log.info("Aux Copy job: " + str(aux_job.job_id))
                    aux_job.wait_for_completion()
                    if aux_job.summary['status'] == 'Completed':
                        self.log.info("Aux Copy job {0} finished.".format(aux_job.job_id))
                        break
                    if aux_job.summary.get('pendingReasonErrorCode') == '19:579':
                        # another job is already running
                        # will wait 5 minutes and retry again to be sure we copy data
                        self.log.info("Another Aux Copy job is running. Will retry in 5 minutes...")
                        time.sleep(300)
                    else:
                        raise Exception(
                            "Pending reason '" + aux_job.summary['pendingReasonErrorCode'] +
                            "' for Aux Copy job with error: {0}".format(aux_job.delay_reason)
                        )

                # validate copy
                self.log.info("VALIDATION: backup job Secondary Copy")
                retcode = self.validateData(self.secondary_copy_id, self.tcinputs["RestoreClientSecondaryCopy_name"],
                                            self.tcinputs["RestoreClientSecondaryCopy_host"])
                if retcode:
                    self.log.info("Validation success")
                else:
                    raise Exception(
                        "Backup job {0} Secondary Copy validation failed".format(backup_job)
                    )

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # cleanup
        try:
            self.log.info("********* cleaning up ***********")
        except Exception as e:
            self.log.info("something went wrong while cleanup.")
            pass

    def populateData(self):
        """
        Make sure data for backup present on source client.
        Make sure data size is 70% of the tape size.

        X dirs = tape size (bytes) * 0.6 / (2000k * 100 files)
        """

        create_data = False
        # size in MB = GB * 1.06 * 1024
        ibm_size = int(int(self.tcinputs["TapeSizeGB"]) * 1085.44)
        # +100 to make sure we get ceil( size/200)
        dir_count = int((ibm_size + 100) / 200)
        self.log.info("ibm_size needed is {0}MB".format(ibm_size))
        self.log.info("dir_count needed is {0}".format(dir_count))
        if self.client_machine.check_directory_exists(self.content_path):
            dir_size = int(self.client_machine.get_folder_size(self.content_path))
            self.log.info("Data directory {0} exists and size reported {1}MB".format(self.content_path, dir_size))
            if dir_size < ibm_size:
                self.log.info("Exiting data is too small")
                create_data = True
            else:
                self.log.info("Using exiting has sufficient size")
        else:
            self.log.info("Data not present")
            create_data = True

        if create_data:
            self.log.info("Adding data under path:" + self.content_path)
            self.log.info("{0} directories with 100 2MB files".format(dir_count))
            self.client_machine.generate_test_data(
                self.content_path,
                dirs=dir_count,
                files=100,
                file_size=2000,
                hlinks=False,
                slinks=False,
                hslinks=False,
                sparse=False,
            )

    def validateData(self, copy_id, restoreClientName, restoreClientHostname):
        """
        Validate copy by restoring data to restoreClientName
        Args:
            copy_id (int) -- Copy id to use for restore
            restoreClientName -- client name
            restoreClientHostname -- client FQDN

        Return:
            (Bool) True/False
        """

        target_machine = Machine(
            restoreClientHostname,
            self.commcell,
            username=self.username,
            password=self.password
        )

        if self.tcinputs['TestPath'] is None:
            tmp_path = "/autotest/R" + str(self.id)
        else:
            if self.tcinputs['TestPath'][-1] == '/':
                tmp_path = self.tcinputs['TestPath'] + "R" + str(self.id)
            else:
                tmp_path = self.tcinputs['TestPath'] + "/R" + str(self.id)

        target_machine.remove_directory(tmp_path)

        self.log.info("Run restore operation to {2} @ client '{0}' copy id {1}"
                      " and verify the returned results.".format(restoreClientName, copy_id, tmp_path))

        self.helper.restore_out_of_place(
            tmp_path,
            [self.content_path],
            restoreClientName,
            copy_precedence=copy_id,
            restore_ACL=False,
            preserve_level=0
        )

        self.log.info("Run Verify...")

        index_items, _ = self.helper.find_items_subclient()

        machine_items = target_machine.get_items_list(
            tmp_path,
            include_parents=True,
            include_folders=True
        )

        # convert object list to relative path
        prefix = self.content_path
        if prefix[-1] != '/': prefix = prefix + '/'
        index_items = list(filter(lambda x: not x.startswith(self.content_path),
                                  map(lambda x: x.replace(prefix, './'), index_items)))

        prefix = tmp_path
        if prefix[-1] != '/': prefix = prefix + '/'
        machine_items = list(filter(lambda x: not x.startswith(tmp_path),
                                    map(lambda x: x.replace(prefix, './'), machine_items)))

        if self.helper.compare_lists(index_items, machine_items):
            self.log.info(
                "Items from find operation matches with items on the machine"
            )
        else:
            self.log.info("backup:")
            self.log.info("{0}".format(index_items))
            self.log.info("restore:")
            self.log.info("{0}".format(machine_items))
            raise Exception(
                "Items from find operation doesn't match"
                " with items on the machine")

        return True
