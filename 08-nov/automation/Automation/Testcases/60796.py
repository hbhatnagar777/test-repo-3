# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    create_resources()      -- creates the required resources/ defines
                                paths for this testcase

    run_full_backup_job() -- for running a full backup job

    ddb_subclient_load()    -- sets the ddb subclient variable
                                from MA of our testcase

    prune_records_after_ddb_backup()    -- This function will prune
                                        records after DDB backup job has completed.

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase verifies
Non-MemDB Reconstruction with Skip DDB Validation for cloud library using GDSP

input json file arguments required:
ways to use cloud library in TC -
1. Give the pre-created cloud library as input under library_name.
2. Mention cloudlib input as 'yes' and give credentials for creating cloud library.

                        ** this is a cloud lib only testcase **
                            either supply a pre-created cloud library
                            or create a cloud library.

                        "60796": {
                                    "ClientName": "",
                                    "AgentName": "File System",
                                    "MediaAgentName": ""
                                }

                        "library_name": name of the Library to be reused
                        "dedup_path": path where dedup store to be created


                        * enter the cloud library credentials *
                        if you want to create a cloud library
                        in the input file for the testcase
                        "S3Region": None,
                        "S3CloudBucket": None,
                        "S3AccessKey":None,
                        "S3SecretKey":None,
                        "CloudVendor":None
                        note --
                                ***********************************
                                if library_name_given then reuse_library
                                else:
                                    create cloud library using supplied credentials
                                    for CloudVendor, refer to mediagentconstants.py

                                if dedup_path_given -> use_given_dedup_path
                                else it will auto_generate_dedup_path
                                ***********************************

Design Steps:
1. clean up previous run config, Create resources.
2. config GDSP, dependent SP SC, DB + cloud library.

regular recon:
        1. backups J1 & J2 before DDB backup
        2. DDB backup
        3. backup J3 after DDB backup
        4. prune J2 after DDB backup
        5. regular recon
        6. Validate regular recon
        7. restore J1

full recon:
        1. run backup J1
        2. run full recon
        3. validate full recon
        4. validate DDB Validation is not skipped
"""

import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Non-MemDB Reconstruction with Skip DDB Validation" \
                    " for cloud library using GDSP"

        self.tcinputs = {
            "MediaAgentName": None
        }

        self.dedup_store_path = None

        self.content_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.storage_policy_id = None
        self.global_sidb_id = None
        self.global_substore_id = None

        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_lib = False
        self.is_user_defined_dedup = False

        self.global_storage_policy = None
        self.ddbbackup_subclient = None

    def setup(self):
        """sets up the variables to be used in testcase"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        suffix = str(self.tcinputs["MediaAgentName"])[
            1:] + str(self.tcinputs["ClientName"])[1:]
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = "{0}_lib{1}".format(str(self.id), suffix)
        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

    def previous_run_clean_up(self):
        """
        delete previous run items

        Args:
            None

        Returns:
            None
        """

        self.log.info("********* previous run clean up **********")
        try:
            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("storage policy deleted")
            else:
                self.log.info("storage policy does not exist.")

            if self.commcell.storage_policies.has_policy(
                    "global_" + self.storage_policy_name):
                self.commcell.storage_policies.delete(
                    "global_" + self.storage_policy_name)
                self.log.info("global storage policy deleted")
            else:
                self.log.info("global storage policy does not exist.")

            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.info("clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def create_resources(self):
        """
        creates the required resources/ defines paths for this testcase

        Args:
            None

        Returns:
            None

        """
        # create the required resources for the testcase
        # get the drive path with required free space
        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)

        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (
            drive_path_media_agent, self.id)

        # creating testcase directory, mount path, content path, dedup
        # store path
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info(
                "existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.tcinputs["dedup_path"], self.id)
        elif not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        # if user defined library exists don't create new else create new library
        if self.commcell.disk_libraries.has_library(self.tcinputs.get("library_name", "library does not exist")):
            self.log.info("user defined library already exists - checking if it is"
                          " a cloud library - %s",self.tcinputs.get("library_name"))
            lib = self.commcell.disk_libraries.get(self.tcinputs.get("library_name"))
            if lib.library_properties.get("model").lower() == "cloud":
                self.log.info("the supplied library is a cloud library")
                pass
            else:
                raise ValueError("the pre-existing library supplied is not a cloud library")

        else:
            # create library
            # the library creation will be cloud

            # by default amazon s3 cloud
            self.library = self.mm_helper.configure_cloud_library(
                self.library_name,
                self.tcinputs["MediaAgentName"],
                self.tcinputs["S3CloudBucket"],
                self.tcinputs["S3Region"] +
                "//" +
                self.tcinputs["S3AccessKey"],
                self.tcinputs["S3SecretKey"],
                self.tcinputs["CloudVendor"])

        # create global SP
        self.global_storage_policy = self.dedup_helper.configure_global_dedupe_storage_policy(
            "global_" + self.storage_policy_name,
            self.library_name,
            self.tcinputs["MediaAgentName"],
            self.dedup_store_path,
            self.tcinputs["MediaAgentName"])

        # create dependent SP
        self.log.info("check SP: %s", self.storage_policy_name)
        if not self.commcell.storage_policies.has_policy(
                self.storage_policy_name):
            self.log.info("adding dependent Storage policy...")
            self.storage_policy = self.commcell.storage_policies.add(
                self.storage_policy_name,
                global_policy_name="global_" + self.storage_policy_name)
            self.log.info("Dependent storage policy config done.")
        else:
            self.log.info("Dependent Storage policy exists!")

        # use the global storage policy object
        # from it get the global storage policy id
        # get the sidb store id and sidb sub store id
        # self.storage_policy_id = self.storage_policy._get_storage_policy_id()
        return_list = self.dedup_helper.get_sidb_ids(
            self.global_storage_policy.storage_policy_id, "Primary_Global")
        self.global_sidb_id = int(return_list[0])
        self.global_substore_id = int(return_list[1])

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(
            self.backupset_name, self.agent)

        # create subclient
        self.subclient = self.mm_helper.configure_subclient(
            backupset_name = self.backupset_name, subclient_name = self.subclient_name,
            storage_policy_name = self.storage_policy_name)

    def run_full_backup_job(self, iteration=1,
                            different_subclient=None,
                            partial_return=False):
        """
            run a full backup job

            Args
                iteration       1(default)
                                number to control and keep track of backup jobs count

                different_subclient         (subclient object)
                                            if the backup job is not
                                            to be run on the default
                                            subclient object of the
                                            testcase.

                partial_return              (False, default)
                                            if True will return job object
                                            before completion of the job.

            Returns
                an object of running full backup job
        """

        if different_subclient is not None:
            self.log.info(
                "starting backup job on subclient: %s",
                different_subclient.name)
            job = different_subclient.backup("FULL")

        else:
            # generate unique random data for the testcase
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.client_machine.join_path(
                        self.content_path, "J" + str(iteration)), 1.0, 1):
                self.log.info(
                    "generated unique data for subclient: %s at location: %s",
                    self.subclient.name,
                    self.client_machine.join_path(
                        self.content_path,
                        "J" + str(iteration)))
            else:
                raise Exception("couldn't generate unique data")

            # add subclient content
            self.log.info(
                "add all the generated files as content to the subclient: %s",
                self.subclient.name)
            self.subclient.content = [self.content_path]

            self.log.info(
                "Starting backup job %d on subclient: %s",
                iteration,
                self.subclient.name)
            job = self.subclient.backup("FULL")

        self.log.info("Backup job id: %s", str(job.job_id))

        if partial_return:
            return job

        if not job.wait_for_completion():
            if job.status.lower() == "completed":
                self.log.info("job %s complete", job.job_id)
            else:
                raise Exception(
                    "Job {0} Failed with {1}".format(
                        job.job_id, job.delay_reason))
        return job

    def ddb_subclient_load(self):
        """
        sets the ddb subclient variable from MA of our testcase

        Args:
            None

        Returns:
            None

        Raises:
            Exceptions
                if DDBBackup subclient does not exist.

        """
        # check if DDBBackup subclient exists, if it doesn't fail the testcase
        default_backup_set = self.commcell.clients.get(
            self.tcinputs.get("MediaAgentName")).agents.get(
                "File System").backupsets.get(
                    "defaultBackupSet")

        if default_backup_set.subclients.has_subclient("DDBBackup"):
            self.log.info("DDBBackup subclient exists")
            self.log.info(
                "Storage policy associated with the DDBBackup subclient is %s",
                default_backup_set.subclients.get("DDBBackup").storage_policy)
            self.ddbbackup_subclient = default_backup_set.subclients.get(
                "DDBBackup")
        else:
            raise Exception("DDBBackup Subclient does not exist:FAILED")

    def prune_records_after_ddb_backup(self, job):
        """
        This function will prune records after DDB backup job has completed.

        Args:
            job     - Job object from previous code execution.

        Returns:
            None
        """
        pruning_done = False
        self.log.info("set the mmprune process interval to two minutes")
        self.mm_helper.update_mmconfig_param(
            param_name='MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', nmin=2, value=2)

        self.log.info("deleting Job - ID: %s", job.job_id)
        sp_copy = self.storage_policy.get_copy("primary")
        sp_copy.delete_job(job.job_id)
        self.log.info("deleted jobID: %s", job.job_id)

        self.log.info("trying to get the records pruned")
        for i in range(10):
            self.log.info("data aging + sleep for 60 seconds: RUN %s", (i + 1))

            job = self.mm_helper.submit_data_aging_job()

            self.log.info("Data Aging job: %s", str(job.job_id))
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info("job %s complete", job.job_id)
                else:
                    raise Exception(
                        f"Job {job.job_id} Failed with {job.delay_reason}")
            matched_lines = self.dedup_helper.validate_pruning_phase(self.global_sidb_id,
                                                                     self.tcinputs['MediaAgentName'], phase=2)

            if matched_lines:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 2 pruning on sidb - {self.global_sidb_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"No phase 2 pruning activity on sidb - {self.global_sidb_id} yet. Checking after 60 seconds")
                time.sleep(60)

        
        if not pruning_done:
            self.log.error("Pruning is not over even after 10 minutes")

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            self.create_resources()

            # run the first backup job
            first_job = self.run_full_backup_job(iteration=1)
            self.log.info("first backup job - jobID: %s", first_job.job_id)

            # run the second backup job
            second_job = self.run_full_backup_job(iteration=2)
            self.log.info("second backup job - jobID: %s", second_job.job_id)

            # run DDB backup
            self.ddb_subclient_load()
            ddb_backup_job = self.run_full_backup_job(
                different_subclient=self.ddbbackup_subclient)
            self.log.info("DDB backup job - jobID: %s", ddb_backup_job.job_id)

            # run third backup job to add records after DDB backup job
            third_job = self.run_full_backup_job(iteration=3)
            self.log.info(
                "third backup job to add records after DDB backup job - third jobID: %s",
                third_job.job_id)

            self.log.info("prune J2 after DDB backup -- prune records")
            self.prune_records_after_ddb_backup(second_job)

            self.log.info(
                "######################## Regular Recon Job ########################")
            # run a backup job
            sidb_up_job = self.run_full_backup_job(iteration=00, partial_return=True)
            self.log.info("started a backup job to initialize sidb process: jobID - %s",
                          sidb_up_job.job_id)

            # check in logs sidb process is up
            if sidb_up_job:
                # time.sleep(5)
                self.log.info('check whether sidb2 process started for'
                              ' the engine due to job or not?')
                running_sidb_list = self.dedup_helper.is_sidb_running(engine_id=str(self.global_sidb_id),
                                                                      ddbma_object=self.commcell.clients.get(
                                                                          self.tcinputs.get("MediaAgentName")))
                # if no process running for the engine ID mentioned - empty list returned

                # we have only one partition for this engine
                # objective is to have sidb2 process in running state
                # chances are backup job will cause it to be
                # running but if other factors do affect it
                # we are not concerned about that

                count = 0
                while not running_sidb_list:
                    running_sidb_list = self.dedup_helper.is_sidb_running(engine_id=str(self.global_sidb_id),
                                                                          ddbma_object=self.commcell.clients.get(
                                                                              self.tcinputs.get("MediaAgentName")))
                    time.sleep(1)
                    count += 1

                    if count == 180:
                        self.log.error("did not find running SIDB2 process for DDB %d",
                                       self.global_sidb_id)
                        raise Exception("could not start sidb process"
                                        " during backup job under 1*180 secs")

            else:
                raise Exception("backup job to start sidb2 process on DDB - could not run properly")

            pid = []
            for pid_tuple in running_sidb_list:
                pid.append(pid_tuple[1])
                self.log.info("got the (groupnumber,pid,jobid) tuple: %s", pid_tuple)

            self.log.info("verified from OS PID list sidb"
                          " process is up for current DDB")
            # then kill the sidb process
            for process_id in pid:
                self.log.info("killing the sidb process for %d engine with pid %d",
                              self.global_sidb_id, process_id)
                self.media_agent_machine.kill_process(process_id=process_id)

            # resume the job, pass over exception
            try:
                time.sleep(30)
                self.log.info("resuming the backup job after killing sidb process")
                sidb_up_job.resume()
            except Exception:
                pass

            # wait for recon job to start
            recon_job = self.dedup_helper.poll_ddb_reconstruction(
                sp_name="global_" + self.storage_policy_name, copy_name="Primary_Global")
            self.log.info(
                "recon job was run: recon jobID - %s",
                recon_job.job_id)

            # resume the job, pass over exception
            try:
                time.sleep(30)
                self.log.info("resuming the backup job after killing sidb process")
                sidb_up_job.resume()
            except Exception:
                pass

            if not sidb_up_job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error:{0}".format(sidb_up_job.delay_reason)
                )

            error_flag = []

            # doing validations
            # check if the job is a regular recon type job or not
            self.log.info(">>>>>Validation 1: is Regular recon job?")
            recon_type = self.dedup_helper.get_reconstruction_type(recon_job.job_id)
            if recon_type == "Regular Reconstruction":
                self.log.info("Recon job was a regular reconstruction job")
                self.log.info("SUCCESS:PASS")
            else:
                self.log.error(
                    "Recon job was not a regular reconstruction job")
                error_flag += ['Recon job was not a regular reconstruction job']

            # since it is regular recon, DDB validation is supposed to happen
            # why?
            # at end stage of regular recon, archfiles in csdb validated with ddb
            # whatever archfiles present in ddb and not in csdb - means to be
            # pruned

            # DDB validation should not be skipped
            self.log.info(
                ">>>>Validation 2: is DDB validation skipped? [yes: Fail, no: Pass] -"
                " DDB validation should not be skipped")
            matched_lines, matched_strings = self.dedup_helper.parse_log(
                self.commcell.commserv_hostname,
                'LibraryOperation.log',
                'Skip Pruning phase and go to DDB verify',
                single_file=False,
                jobid=recon_job.job_id)
            if len(matched_lines) > 0:
                self.log.info(
                    "DDB Validation was NOT skipped for regular recon: Pass")
            else:
                self.log.error("Validation phase was skipped!!")
                error_flag += ["DDB Validation phase was skipped!!"]

            # run restore for J1
            # try to run restore job on content backed up by J1

            # restore job done here to make sure only J2
            # was pruned and J1 was not touched.
            self.log.info("running restore job")
            restorejob = self.subclient.restore_in_place([self.client_machine.join_path(self.content_path, "J1")])
            # unconditional overwrite is true
            self.log.info("restore job: " + restorejob.job_id)
            if not restorejob.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        restorejob.delay_reason))
            self.log.info("restore job completed")

            self.log.info(
                "######################## Full Recon Job ########################")

            # full recon:
            # 1. run backup J1 (first for Full recon section)
            # 2. run full recon
            # 3. validate full recon
            # 4. validate DDB Validation is not skipped

            # run the fourth backup job
            first_job_full_recon = self.run_full_backup_job(iteration=4)
            self.log.info(
                "first backup job for full recon section - jobID: %s",
                first_job_full_recon.job_id)

            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 15, 30)

            self.log.info("wait for sidb to go down")
            if self.dedup_helper.wait_till_sidb_down(
                    str(self.global_sidb_id), self.commcell.clients.get(
                        self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d"
                              " has gone down", self.global_sidb_id)
            else:
                self.log.error("sidb process for engine %d did"
                               " not go down under the wait period", self.global_sidb_id)
                raise Exception("sidb process did not go"
                                " down under the wait period")

            self.dedup_helper.mark_substore_for_recovery(storage_policy_name="global_" + self.storage_policy_name,
                                                         copy_name="Primary_Global", store_id=self.global_sidb_id)
            self.log.info("GDSP DDB has been marked for recovery")




            # rationale is already done above with killing sidb and checking DDB marked maintenance

            # time added here unlike above because
            # we are calling specially full recon instead of polling like above
            time.sleep(30)

            self.storage_policy.run_recon(
                copy_name="Primary_Global",
                sp_name="global_" +
                self.storage_policy_name,
                store_id=str(
                    self.global_sidb_id),
                full_reconstruction=1)

            recon_job = self.dedup_helper.poll_ddb_reconstruction(
                sp_name="global_" + self.storage_policy_name, copy_name="Primary_Global")
            self.log.info(
                "recon job was run: recon jobID - %s",
                recon_job.job_id)

            # doing validations
            # check if the job is a FULL recon type job or not
            self.log.info(">>>>>Validation 1: is FULL recon job?")
            recon_type = self.dedup_helper.get_reconstruction_type(recon_job.job_id)
            if recon_type == "Full Reconstruction":
                self.log.info("Recon job was a Full Reconstruction job")
                self.log.info("SUCCESS:PASS")
            else:
                self.log.error("Recon job was not a Full Reconstruction job")
                error_flag += ['Recon job was not a Full Reconstruction job']

            # since it is Full Reconstruction, DDB validation is NOT supposed
            # to happen

            # DDB validation should be skipped
            self.log.info(
                ">>>>Validation 2: is DDB validation skipped? [yes: Pass, no: Fail]")
            matched_lines, matched_strings = self.dedup_helper.parse_log(
                self.commcell.commserv_hostname,
                'LibraryOperation.log',
                'Skip Pruning phase and go to DDB verify',
                single_file=False,
                jobid=recon_job.job_id)
            if not matched_lines:
                self.log.info(
                    "DDB Validation was skipped for FULL recon: Pass")
            else:
                self.log.error("DDB Validation phase was NOT skipped!!")
                error_flag += ["DDB Validation phase was NOT skipped!!"]

            # run restore for J4
            # try to run restore job on content backed up by J4

            self.log.info("running restore job")
            restorejob = self.subclient.restore_in_place([self.client_machine.join_path(self.content_path, "J4")])
            # unconditional overwrite is true
            self.log.info("restore job: " + restorejob.job_id)
            if not restorejob.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        restorejob.delay_reason))
            self.log.info("restore job completed")

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.info(error_flag)
                raise Exception(f"testcase failed: {error_flag}")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all items created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.log.info("setting back the "
                          "mmprune process interval to 60 mins")
            self.mm_helper.update_mmconfig_param(
                param_name='MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', nmin=10, value=60)
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)
            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            self.previous_run_clean_up()

            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library deleted")
                else:
                    self.log.info("Library does not exist.")
            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
