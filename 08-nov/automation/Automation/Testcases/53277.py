# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    get_auxcopy_attr()              -- gets attributes for an auxcopy job

    check_auxcopy_resubmit()        -- checks if flag to resubmit an auxcopy job is set

    run()                           --  run function of this test case

    tear_down()                     --  tear down function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.idautils import CommonUtils
import time


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """Batching for auxcopy : the job limit set is
                    LESS than the number of jobs to process"""
        self.tcinputs = {
            "MediaAgentName": None,
            "DedupeStorePath": None,
            "ContentPath": None,
            "MountPath": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.mmhelper_obj = MMHelper(self)
        self.common_util = CommonUtils(self)

    def get_auxcopy_attr(self, auxcopy_job_id):
        """gets number of rows with auxcopy resubmit attribut
        Args:
            auxcopy_job_id (str)  --  auxcopy job id

        Returns:
            (int) - number of rows

        """
        query = """select distinct jobId
                    from JMJobOptions
                    where attributeId in (69,70)
                    and JobID = {0}""".format(auxcopy_job_id)
        self.log.info("Running query : \n{0}".format(query))
        self.csdb.execute(query)
        if self.csdb.fetch_one_row()[0]:
            return int(self.csdb.fetch_one_row()[0])
        else:
            return 0

    def check_auxcopy_resubmit(self, copy_id):
        """gets number of rows with auxcopy resubmit attribut
        Args:
            copy_id (str)  --  copy id

        """
        timer = 30
        while timer > 0:
            timer -= 1
            if timer == 0:
                raise Exception("""Auxcopy job did not start after 5 minutes.
                                Failing testcase""")
            query = """select jobId
                    from JMAdminJobInfoTable
                    where opType = 104 and archGrpCopyID =  {0}
                    """.format(str(copy_id))
            self.log.info("Running query : \n{0}".format(query))
            self.csdb.execute(query)
            aux_job = self.csdb.fetch_one_row()[0]
            if aux_job is "":
                time.sleep(10)
            else:
                self.log.info("Auxcopy job started. Waiting for it to complete.")
                break

            if not aux_job.wait_for_completion():
                raise Exception(
                    "Failed to run auxcopy with error: {0}".format(aux_job.delay_reason)
                )
            if aux_job.status.lower() == "completed":
                self.log.info("job {0} successful".format(aux_job.job_id))
            else:
                raise Exception(
                    "Failed to run auxcopy with error: {0}".format(aux_job.delay_reason)
                )
            self.log.info("Auxcopy job completed")

    def run(self):
        """Run function of this test case"""
        try:
            storage_policy_name = str(self.id) + "_SP"
            backupset_name = str(self.id) + "_BS"
            subclient_name = str(self.id) + "_SC"
            copy_name = str(self.id) + "_dedupe_copy"
            generate_data_at = self.client_machine.join_path(self.tcinputs["ContentPath"], ("newData"))
            library_name = str(self.id) + "_lib"
            total_jobs_to_copy = 10
            flag = 0
            job_list = []
            param = "QueueConflictingAuxCopyJobs"
            self.log.info("""Batching for auxcopy :
                           the job limit set is LESS than the number of jobs to process""")

            # enable queuing of auxcopy jobs
            self.log.info("Enabling QueueConflictingAuxCopyJobs param")
            # getting current value for this param
            self.log.info("Getting current value for this param")
            # setting param value to 1 to enable if not already
            if self.mmhelper_obj.get_global_param_value(param) != 1:
                self.log.info("Need to enable this param as current value is 0")
                self.commcell.add_additional_setting(
                    "CommServDB.GxGlobalParam", param, "INTEGER", "1")
                self.log.info("""VALIDATION :
                               Check if QueueConflictingAuxCopyJobs param is enabled.""")
                if self.mmhelper_obj.get_global_param_value(param) != 1:
                    raise Exception("""VALIDATION FAILED :
                                    Failed to enable QueueConflictingAuxCopyJobs param""")
                self.log.info("QueueConflictingAuxCopyJobs param enabled.")
            else:
                flag = 1
                self.log.info("QueueConflictingAuxCopyJobs param is already enabled")

            # Check backupset if exits and create if not present
            if self.agent.backupsets.has_backupset(backupset_name):
                self.log.info(" Backupset exists!")
            else:
                self.log.info("Creating Backupset.")
                self.agent.backupsets.add(backupset_name)
                self.log.info("Backupset creation completed.")

            backupset_obj = self.agent.backupsets.get(backupset_name)

            # Check library if exits and create if not present
            if self.commcell.disk_libraries.has_library(library_name):
                self.log.info("Library  exists!")
            else:
                self.log.info("Creating Library.")
                self.commcell.disk_libraries.add(library_name,
                                                 self.tcinputs["MediaAgentName"],
                                                 self.tcinputs["MountPath"])
                self.log.info("Library creation completed.")

            # Check SP if exits and create if not present
            if self.commcell.storage_policies.has_policy(storage_policy_name):
                self.log.info("Storage policy exists!")
            else:
                self.log.info("Creating Storage policy")
                self.commcell.storage_policies.add(storage_policy_name,
                                                   library_name,
                                                   self.tcinputs["MediaAgentName"])
                self.log.info("Storage policy creation completed.")
            sp_obj = self.commcell.policies.storage_policies.get(storage_policy_name)
            sp_copy_obj_1 = sp_obj.get_copy("Primary")

            # Check SP copy if exits and create if not present
            if sp_obj.has_copy(copy_name):
                self.log.info("Storage policy copy exists!")
            else:
                self.log.info("Creating dedupe copy")
                sp_obj.create_dedupe_secondary_copy(copy_name,
                                                    library_name,
                                                    self.tcinputs["MediaAgentName"],
                                                    self.tcinputs["DedupeStorePath"],
                                                    self.tcinputs["MediaAgentName"])
                self.log.info("Dedupe secondary copy creation completed ")
            sp_copy_obj_2 = sp_obj.get_copy(copy_name)

            # Check SC if exits and create if not present
            if backupset_obj.subclients.has_subclient(subclient_name):
                self.log.info("Subclient exists!")
                subclient_obj = backupset_obj.subclients.get(subclient_name)
            else:
                self.log.info("Creating subclient")
                subclient_obj = backupset_obj.subclients.add(subclient_name, storage_policy_name)
                self.log.info("Subclient creation completed")
                # add subclient content
                self.log.info("Adding subclient content to backup")
                self.log.info("""Setting subclient content to:{0}
                               """.format(self.tcinputs["ContentPath"]))
                subclient_obj.content = [self.tcinputs["ContentPath"]]
                self.log.info("Adding subclient content completed.")

            self.log.info("CASE 1: PARAM ENABLED AND JOB LIMIT IS LESS")

            # running 14 backups
            for i in range(0, 14):
                self.log.info("Running backup : Iteration = {0}".format(str(i+1)))
                job_list.append(self.common_util.subclient_backup(subclient_obj, 'FULL', True))
                self.log.info("""Generating content for subclient at: {0}
                               """.format(generate_data_at))
                self.client_machine.generate_test_data(generate_data_at)
            self.log.info("Completed running backups")

            self.log.info("Running auxcopy with job limit set to 10")
            aux_job1 = sp_obj.run_aux_copy("", self.tcinputs["MediaAgentName"], use_scale=True,
                                           total_jobs_to_process=total_jobs_to_copy)
            self.log.info("Auxcopyjob {0} launched.".format(str(aux_job1.job_id)))
            if not aux_job1.wait_for_completion():
                raise Exception(
                    "Failed to run auxcopy with error: {0}".format(aux_job1.delay_reason)
                )
            self.log.info("Auxcopy job completed")

            self.log.info("***Starting validations***")
            #  get primary and secondary copy ids
            primary_copy_id = self.mmhelper_obj.get_copy_id(storage_policy_name, "Primary")
            secondary_copy_id = self.mmhelper_obj.get_copy_id(storage_policy_name, copy_name)

            self.log.info("VALIDATION 1: CHECKING NUMBER OF JOBS PICKED BY THE AUXCOPY JOB")
            num_jobs_picked = self.mmhelper_obj.get_jobs_picked_for_aux(aux_job1.job_id)
            if num_jobs_picked == total_jobs_to_copy:
                self.log.info("""VALIDATION 1 SUCCESSFUL: NUMBER OF JOBS PICKED BY THE AUXCOPY JOB
                               IS EQUAL TO TOTAL JOBS TO BE COPIED""")
            else:
                raise Exception("""VALIDATION 1 FAILED :NUMBER OF JOBS PICKED BY THE AUXCOPY JOB
                               IS NOT EQUAL TO TOTAL JOBS TO BE COPIED""")

            self.log.info("""VALIDATION 2:
                           CHECKING IF JOBS PRESENT IN TO BE COPIED STATE ON SECONDARY COPY""")
            jobs_to_be_copied = self.mmhelper_obj.get_to_be_copied_jobs(secondary_copy_id)
            if jobs_to_be_copied > 0:
                self.log.info("""VALIDATION 2 SUCCESSFUL:
                                THERE ARE JOBS PRESENT IN TO BE COPIED STATE ON SECONDARY COPY""")
            else:
                raise Exception(""""VALIDATION 2 FAILED:
                                THERE ARE NO JOBS PRESENT IN TO BE COPIED
                                STATE ON SECONDARY COPY""")

            self.log.info("VALIDATION 3: CHECKING IF ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE SET")
            flags_set = self.get_auxcopy_attr(aux_job1.job_id)
            if flags_set > 0:
                self.log.info(
                    "VALIDATION 3 SUCCESSFUL: ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE SET")
            else:
                raise Exception(
                    "VALIDATION 3 FAILED: ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE NOT SET")

            # waiting for resubmit auxcopy job
            self.log.info("waiting for resubmit auxcopy job")
            self.check_auxcopy_resubmit(str(primary_copy_id))

            #  get AF size on secondary copy
            self.log.info("VALIDATION 4: CHECKING ARCHFILE SIZE ON DESTINATION")
            primary_copy_af_size = self.mmhelper_obj.get_archive_file_size(str(primary_copy_id))
            secondary_copy_af_size = self.mmhelper_obj.get_archive_file_size(str(secondary_copy_id))
            if primary_copy_af_size == secondary_copy_af_size:
                self.log.info("""VALIDATION 4 SUCCESSFUL:
                               ARCHFILE SIZE ON SOURCE COPY AND SECONDARY COPY IS SAME""")
            else:
                raise Exception("""VALIDATION 4 FAILED:
                                ARCHFILE SIZE ON SOURCE COPY AND SECONDARY COPY IS NOT SAME""")

            self.log.info("CASE 1 COMPLETED: PARAM ENABLED AND JOB LIMIT IS LESS")

            self.log.info("\n*****************************************************************\n")

            self.log.info("CASE 2: PARAM DISABLED AND JOB LIMIT IS LESS")
            # recopy jobs
            self.log.info("Recopying jobs on secondary copy")
            for job in job_list:
                sp_copy_obj_2.recopy_jobs(str(job.job_id))

            # disable queuing of auxcopy jobs
            self.log.info("Disabling QueueConflictingAuxCopyJobs param")
            self.commcell.add_additional_setting(
                "CommServDB.GxGlobalParam", param, "INTEGER", "0")
            self.log.info(" VALIDATION : Check if QueueConflictingAuxCopyJobs param is disabled.")
            if self.mmhelper_obj.get_global_param_value(param) != 0:
                raise Exception("""VALIDATION FAILED :
                                Failed to disable QueueConflictingAuxCopyJobs param""")
            self.log.info("QueueConflictingAuxCopyJobs is set to 0")
            self.log.info("Running auxcopy with job limit set to 10")
            aux_job1 = sp_obj.run_aux_copy("", self.tcinputs["MediaAgentName"], use_scale=True,
                                           total_jobs_to_process=total_jobs_to_copy)
            self.log.info("Auxcopyjob {0} launched.".format(str(aux_job1.job_id)))
            if not aux_job1.wait_for_completion():
                raise Exception(
                    "Failed to run auxcopy with error: {0}".format(aux_job1.delay_reason)
                )
            self.log.info("Auxcopy job completed")

            self.log.info("***Starting validations***")

            self.log.info("VALIDATION 1: CHECKING NUMBER OF JOBS PICKED BY THE AUXCOPY JOB")
            num_jobs_picked = self.mmhelper_obj.get_jobs_picked_for_aux(aux_job1.job_id)
            if num_jobs_picked == total_jobs_to_copy:
                self.log.info("""VALIDATION 1 SUCCESSFUL: NUMBER OF JOBS PICKED BY THE AUXCOPY JOB
                               IS LESS THAN TOTAL JOBS TO BE COPIED""")
            else:
                raise Exception("""VALIDATION 1 FAILED :NUMBER OF JOBS PICKED BY THE AUXCOPY JOB
                               IS LESS THAN TOTAL JOBS TO BE COPIED""")

            self.log.info("VALIDATION 2: CHECKING IF JOBS PRESENT IN TO BE COPIED STATE ON "
                           "SECONDARY COPY")
            jobs_to_be_copied = self.mmhelper_obj.get_to_be_copied_jobs(secondary_copy_id)
            if jobs_to_be_copied > 0:
                self.log.info("VALIDATION 2 SUCCESSFUL: THERE ARE JOBS PRESENT IN TO BE COPIED "
                               "STATE ON SECONDARY COPY")
            else:
                raise Exception(
                    "VALIDATION 2 FAILED: THERE ARE NO JOBS PRESENT IN TO BE COPIED "
                    "STATE ON SECONDARY COPY")

            self.log.info("VALIDATION 3: CHECKING IF ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE SET")
            flags_set = self.get_auxcopy_attr(aux_job1.job_id)
            if flags_set > 0:
                self.log.info(
                    "VALIDATION 3 SUCCESSFUL: ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE SET")
            else:
                raise Exception(
                    "VALIDATION 3 FAILED: ATTRIBUTES TO RESUBMIT AUXCOPY JOB ARE NOT SET")

            # waiting for resubmit auxcopy job
            self.log.info("waiting for resubmit auxcopy job")
            self.check_auxcopy_resubmit(str(primary_copy_id))

            #  get AF size on secondary copy
            self.log.info("VALIDATION 4: CHECKING ARCHFILE SIZE ON DESTINATION")
            primary_copy_af_size = self.mmhelper_obj.get_archive_file_size(str(primary_copy_id))
            secondary_copy_af_size = self.mmhelper_obj.get_archive_file_size(str(secondary_copy_id))
            if primary_copy_af_size == secondary_copy_af_size:
                self.log.info("""VALIDATION 4 SUCCESSFUL:
                               ARCHFILE SIZE ON SOURCE COPY AND SECONDARY COPY IS SAME""")
            else:
                raise Exception("""VALIDATION 4 FAILED :
                                ARCHFILE SIZE ON SOURCE COPY AND SECONDARY COPY IS NOT SAME""")

            self.log.info("CASE 2 COMPLETED: PARAM DISABLED AND JOB LIMIT IS LESS")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: {0}'.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.log.info("********************** CLEANUP STARTING *************************")
            if flag == 1:
                self.log.info("Setting back original param value to 0")
                self.commcell.add_additional_setting(
                    "CommServDB.GxGlobalParam", param, "INTEGER", "0")
                self.log.info("""VALIDATION:
                               Check if QueueConflictingAuxCopyJobs param is disabled.""")
                if self.mmhelper_obj.get_global_param_value(param) != 0:
                    raise Exception("""VALIDATION FAILED :
                                    Failed to disable QueueConflictingAuxCopyJobs param""")
            else:
                self.log.info("No need to modify back")

            # cleanup - deleted all jobs and delete data generated here
            self.log.info("Deleting backups from both copies for cleanup")
            for job in job_list:
                sp_copy_obj_1.delete_job(job.job_id)
                sp_copy_obj_2.delete_job(job.job_id)

            self.log.info("Running Data Ageing")
            self.commcell.run_data_aging()

            self.log.info("Deleting subclient content generated.")
            self.mmhelper_obj.remove_content(generate_data_at, self.client_machine,
                                        num_files=None)
            self.log.info("********************** CLEANUP COMPLETED *************************")
