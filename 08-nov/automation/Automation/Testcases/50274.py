# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform Inline & Parallel copy case for Aux copy

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _validate_inline_copy()     --  validates inline copy functionality by checking for job status on secondary copy in
                                    JMJobDataStats

    _get_stream_reader_id()     --  gets StreamReaderId is used for reading for both copies in ArchJobStreamStatus

    _validate_parallel_copy()   --  validates inline copy functionality by checking that same StreamReaderId is used for
                                    reading for both copies in ArchJobStreamStatus

    _cleanup()                  --  cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

TcInputs to be passed in JSON File:
    "50274": {
        "ClientName"    : "Name of a Client - Content to be BackedUp will be created here",
        "AgentName"     : "File System",
        "MediaAgentName": "Name of a MediaAgent - we create Libraries here"
    }
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Inline & Parallel copy case for Aux copy"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.pool_name = None
        self.plan_name = None
        self.plan = None
        self.pool = None
        self.subclient = None
        self.backupset = None
        self.backupset_name = None
        self.subclient_name = None
        self.mountpath = None
        self.partition_path = None
        self.content_path = None
        self.dedupehelper = None
        self.library_name = None
        self.mmhelper = None
        self.common_util = None
        self.ma_machine = None
        self.client_machine = None

    def _validate_inline_copy(self, job_id, copy_id):
        """
        validates inline copy functionality by checking for job status on secondary copy in JMJobDataStats
        Args:
            job_id (int) -- backup job id to check in table

            copy_id (int) -- copy id to validate on
        Return:
            (Bool) True if status of job is 100
            (Bool) False if not
        """

        query = """select status from JMJobDataStats where jobId = {0} and archGrpCopyId = {1}
        """.format(job_id, copy_id)
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: {0}".format(cur))
        if cur != ['']:
            if int(cur[0]) == 100:
                return True
        return False

    def _get_stream_reader_id(self, copy_id):
        """
        Gets StreamReaderId is used for reading for both copies in ArchJobStreamStatus
        Args:
            copy_id (list) -- copy id
        Return:
            list of reader id
        """

        query = """select distinct StreamReaderId from ArchJobStreamStatusHistory where DestCopyId = {0}""".format(copy_id)
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: {0}".format(cur))
        if cur != ['']:
            return cur
        self._log.error("No entries present")
        raise Exception("Unable to fetch reader id")

    def _validate_parallel_copy(self, copy_id_list):
        """
        validates inline copy functionality by checking that same StreamReaderId is used for reading for both copies
            in ArchJobStreamStatus
        Args:
            copy_id_list (list) -- list of copy id to validate on
        Return:
            (Bool) True if StreamReaderIds are same
            (Bool) False if not
        """

        if self._get_stream_reader_id(copy_id_list[0]) == self._get_stream_reader_id(copy_id_list[1]):
            return True
        return False

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete bkupset
            self.log.info(f"Deleting BackupSet: {self.backupset_name} if exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backup_set = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backup_set.subclients.get(self.subclient_name)
                if self.backup_set.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f"Deleted BackupSet: {self.backupset_name}")

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info(f"Deleting plan  {self.plan_name}")
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info(f"Deleting pool  {self.pool_name}")
                self.commcell.storage_pools.delete(self.pool_name)

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging()
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job [{data_aging_job.job_id}] has failed with {data_aging_job.delay_reason}.")
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")

        except Exception as exp:
            self.log.error(f"Error encountered during cleanup : {exp}")
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)
        self.pool_name = f'{self.id}_pool'
        self.plan_name = f'{self.id}_plan'
        self.backupset_name = f'{self.id}_BS'
        self.subclient_name = f'{self.id}_SC'

        self.ma_machine, ma_path = self.mmhelper.generate_automation_path(self.tcinputs['MediaAgentName'], 25*1024)
        self.client_machine, client_path = self.mmhelper.generate_automation_path(self.client.client_name, 25*1024)

        self.mountpath = self.ma_machine.join_path(ma_path, 'MP')
        self.partition_path = self.ma_machine.join_path(ma_path, 'DDB')

        self.content_path = self.client_machine.join_path(client_path, 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        self._cleanup()

    def run(self):
        """Run function of this test case"""

        try:
            self.log.info(f"Creating the pool [{self.pool_name}]")
            self.commcell.storage_pools.add(self.pool_name, self.mountpath,
                                            self.tcinputs['MediaAgentName'],
                                            [self.tcinputs['MediaAgentName'], self.tcinputs['MediaAgentName']],
                                            [self.ma_machine.join_path(self.partition_path, 'Dir'), self.ma_machine.join_path(self.partition_path, 'Copy_Dir')])
            self.log.info(f"Pool [{self.pool_name}] Created.")

            # creation of plan
            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.commcell.plans.refresh()
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            # disabling the schedule policy
            self.plan.schedule_policies['data'].disable()

            # Enable MA side dedupe  on client
            self.client.set_dedup_property('clientSideDeduplication', 'OFF')

            # Set retention of 0day 1cycle
            self.log.info("Setting Retention on Primary Copy")
            sp_dedup_primary_obj = self.plan.storage_policy.get_copy("Primary")
            self.log.info("Got Primary Copy")
            retention = (1, 1, -1)
            self.log.info("Setting retention")
            sp_dedup_primary_obj.copy_retention = retention
            sp_dedup_primary_obj.copy_client_side_dedup = False

            # Enable encryption on Primary copy
            encryption = (True, 'BLOWFISH', 128, False)
            sp_dedup_primary_obj.copy_reencryption = encryption

            # create first non-dedupe secondary copy
            self.log.info("Adding first non dedup copy")
            copy1_non_dedupe = f'{self.id}_copy1_nondedupe'
            self.plan.storage_policy.create_secondary_copy(copy_name=copy1_non_dedupe, library_name=self.pool_name, media_agent_name=self.tcinputs['MediaAgentName'])
            self.log.info("Added second non dedup copy")
            copy1_non_dedupe_obj = self.plan.storage_policy.get_copy(copy1_non_dedupe)

            # create first non-dedupe secondary copy
            self.log.info("Adding second non dedup copy")
            copy2_non_dedupe = f'{self.id}_copy2_nondedupe'
            self.plan.storage_policy.create_secondary_copy(copy_name=copy2_non_dedupe, library_name=self.pool_name, media_agent_name=self.tcinputs['MediaAgentName'])
            self.log.info("Added second non dedup copy")
            copy2_non_dedupe_obj = self.plan.storage_policy.get_copy(copy2_non_dedupe)

            # Removing association with System Created Automatic Auxcopy schedule
            self.log.info("Removing association with System Created Autocopy schedule on above created copy")
            self.mmhelper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy1_non_dedupe)
            self.mmhelper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy2_non_dedupe)

            # add backupset
            self.log.info(f"Adding the backup set [{self.backupset_name}]")
            self.backupset = self.mmhelper.configure_backupset(self.backupset_name)
            self.log.info(f"Backup set Added [{self.backupset_name}]")

            # add subclient
            self.log.info(f"Adding the subclient set [{self.subclient_name}]")
            self.subclient = self.backupset.subclients.add(self.subclient_name)
            self.log.info(f"Subclient set Added [{self.subclient_name}]")

            # Add plan and content to the subclient
            self.log.info("Adding plan to subclient")
            self.subclient.plan = [self.plan, [self.content_path]]
            self.subclient.enable_backup()
            self.log.info("Added plan to subclient")

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=10 on Subclient")
            self.subclient.allow_multiple_readers = True
            self.subclient.data_readers = 10

            # Create unique content
            self.log.info(f"Generating Data at {self.content_path}")
            if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(100 * 1024),
                                                          files=10):
                self.log.error(f"unable to Generate Data at {self.content_path}")
                raise Exception(f"unable to Generate Data at {0}".format(self.content_path))
            self.log.info(f"Generated Data at {self.content_path}")

            # Validate inline copy functionality
            # Enable parallel copy
            copy1_non_dedupe_obj.set_parallel_copy(True)

            # Enable inline copy
            copy1_non_dedupe_obj.set_inline_copy(True)

            # Enable parallel copy
            copy2_non_dedupe_obj.set_parallel_copy(True)

            # Enable inline copy
            copy2_non_dedupe_obj.set_inline_copy(True)

            # Backup Job J1
            job1_obj = self.common_util.subclient_backup(self.subclient, "full")
            time.sleep(60)


            # Backup Job J2
            job2_obj = self.common_util.subclient_backup(self.subclient, "full")

            # validating inline copy for job1 on copy1
            if self._validate_inline_copy(int(job1_obj.job_id), int(copy1_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 1st Backup on copy1 was success")
            else:
                self.log.error("Inline copy for 1st Backup on copy1 failed")
                raise Exception("Inline copy for 1st Backup on copy1 failed")

            # validating inline copy for job1 on copy2
            if self._validate_inline_copy(int(job1_obj.job_id), int(copy2_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 1st Backup on copy2 was success")
            else:
                self.log.error("Inline copy for 1st Backup on copy2 failed")
                raise Exception("Inline copy for 1st Backup on copy2 failed")

            #   validating inline copy for job2 on copy1
            if self._validate_inline_copy(int(job2_obj.job_id), int(copy1_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 2st Backup on copy1 was success")
            else:
                self.log.error("Inline copy for 2st Backup on copy1 failed")
                raise Exception("Inline copy for 2st Backup on copy1 failed")

            #   validating inline copy for job2 on copy2
            if self._validate_inline_copy(int(job2_obj.job_id), int(copy2_non_dedupe_obj.copy_id)):
                self.log.info("Inline copy for 2st Backup on copy2 was success")
            else:
                self.log.error("Inline copy for 2st Backup on copy2 failed")
                raise Exception("Inline copy for 2st Backup on copy2 failed")

            # picking jobs for recopy on both copies and running parallel copy

            #   Picking jobs J1 and J2 for recopy on copy1
            copy1_non_dedupe_obj.recopy_jobs(job1_obj.job_id + ", " + job2_obj.job_id)
            time.sleep(60)

            #   Picking jobs J1 and J2 for recopy on copy2
            copy2_non_dedupe_obj.recopy_jobs(job1_obj.job_id + ", " + job2_obj.job_id)

            # Run Aux copy Job
            auxcopy_job = self.plan.storage_policy.run_aux_copy()
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has started.")
            if not auxcopy_job.wait_for_completion():
                self.log.error(f"Auxcopy job [{auxcopy_job.job_id}] has failed with {auxcopy_job.delay_reason}.")
                raise Exception("Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has completed.")

            # Validate parallel copy functionality

            if self._validate_parallel_copy([copy1_non_dedupe_obj.copy_id, copy2_non_dedupe_obj.copy_id]):
                self.log.info("SUCCESS  Result :Pass for Parallel copy as streamReaderId for both copies is same")
            else:
                self.log.error("Fail for parallel copy as Stream Readers did not match for both copies")
                raise Exception("Fail for parallel copy as Stream Readers did not match for both copies")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""

        # revert back dedupe default setting on client
        self.client.set_dedup_property('clientSideDeduplication', 'USE_SPSETTINGS')

        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self._cleanup()

        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
