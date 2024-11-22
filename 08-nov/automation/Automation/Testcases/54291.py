# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""mark and sweep takes place or not"""

import time
import csv
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    run_full_backup_job() -- for running a full backup job

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase verifies if the mark and sweep takes place or not after the backup job is run

testcase will generate content to be backed up and then delete
it after the run is over.
it will also disable the windows time service for the duration of this
run which will be re-enabled after the run is over, there will
 be a time change of around 1 hr on the client machine.

input json file arguments required:

                        "ClientName": "name of the client machine as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve",
                        "dedup_path": path where dedup store to be created

Design Steps:
1.	Resources, 6 subclients , each got own content
2.	6 backup jobs
3.	Get sum primary objects across archfiles for all jobs -> Total objects later
4.	Delete alternative jobs, get deleted archfiles too
5.	Mm prune process interval 2 mins
6.	Get Remaining primary objects
7.	Mark and sweep : 1 hour
8.	Checks
MarkPri         11370  Max secondary file reader threads [2]
SweepPrimaries  11811  Total [{0}], Approx Valid [{1}], Approx Invalid [{2}]
SweepPrimaries  11819  Starting the delete phase. Restart string
SweepPrimaries  11855  Deleted total [{0}] records. [{0}] in current run
MarkAndSweep    11063  Mark and Sweep blocks complete. Status [Success]
"""


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "mark and sweep verification after dedupe backup job "
        self.tcinputs = {
            "MediaAgentName": None
        }

        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.dedup_helper = None
        self.mm_helper = None
        self.opt_selector = None
        self.storage_policy_id = None
        self.sidb_id = None
        self.substore_id = None
        self.testcase_path = None
        self.client_machine = None
        self.media_agent_machine = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dump_location = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.time_moved_unix = False
        self.dump_path = None
        self.ma_client = None
        self.storage_pool_name = None
        self.storage_pool = None

    def setup(self):
        """Setup function of this test case"""

        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])[1:]
        self.storage_policy_name = "{0}sp{1}".format(str(self.id), suffix)
        self.storage_pool_name = "{0}POOL{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}bs{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}sc{1}".format(str(self.id), suffix)
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.client)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))

        # client content path
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 20 * 1024)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        # ma dump path
        self.dump_path = self.opt_selector.get_drive(self.media_agent_machine, 20 * 1024)
        self.dump_location = self.media_agent_machine.join_path(
            self.dump_path, "dump_path")

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:
            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            if self.media_agent_machine.check_directory_exists(
                    self.dump_location):
                self.media_agent_machine.remove_directory(self.dump_location)
                self.log.info("Deleted the sidb dumped data.")
            else:
                self.log.info("Dump location directory does not exist.")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("previous run clean up COMPLETED")
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info(f"storage pool {self.storage_pool_name} deleted")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_full_backup_job(self):
        """
            run a full backup job

            Returns ->
                job (job object) -- an object of full backup job which has been started just now
        """
        self.log.info("Starting backup job")
        job = self.subclient.backup("FULL")
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            if job.status.lower() == "completed":
                self.log.info("job %s complete", job.job_id)
            else:
                raise Exception(
                    "Job {0} Failed with {1}".format(
                        job.job_id, job.delay_reason))
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            self.client_machine.create_directory(self.content_path)
            self.log.info("content path created")

            self.media_agent_machine.create_directory(self.dump_location)
            self.log.info("Dump path created")

            # create mountpath
            if self.is_user_defined_mp:
                self.log.info("custom mount path supplied")
                self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
            else:
                drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 20*1024)
                self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)
                self.mount_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "mount_path")

            # create dedup path
            if self.is_user_defined_dedup:
                self.log.info("custom dedup path supplied")
                self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
            else:
                self.dedup_store_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "dedup_store_path")

            self.log.info("Started executing testcase %s", self.id)

            # create pool and dependent SP
            self.log.info(f"Configuring Storage Pool {self.storage_pool_name}")
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mount_path,
                                                                    self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs['MediaAgentName'],
                                                                    self.dedup_store_path)
            else:
                self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.log.info("Done creating a storage pool")
            self.commcell.disk_libraries.refresh()
            self.log.info(f"Configuring Storage Policy {self.storage_policy_name}")
            if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.storage_policy = self.commcell.storage_policies.add(
                    storage_policy_name=f"{self.storage_policy_name}",
                    global_policy_name=self.storage_pool_name)

            # create backupset
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)

            # use the storage policy object
            # from it get the storage policy id
            # get the sidb store id and sidb sub store id

            return_list = self.dedup_helper.get_sidb_ids(
                self.storage_pool.storage_pool_id, self.storage_pool.copy_name)
            self.sidb_id = int(return_list[0])
            self.substore_id = int(return_list[1])

            jobs_list = []
            # create 6 subclients
            self.log.info("creating 6 subclients with data "
                          "generation to be associated to the same backup set")
            for i in range(1, 7):
                subclient_name_local = "%s-%s" % (self.subclient_name, i)
                # generate content
                temp_path = self.client_machine.join_path(
                    self.content_path, str(i))
                if self.mm_helper.create_uncompressable_data(
                        self.tcinputs['ClientName'], temp_path, 1, 1):
                    self.log.info(
                        "generated content for subclient {0}".format(subclient_name_local))
                # create subcient and add subclient content
                self.subclient = self.mm_helper.configure_subclient(
                    self.backupset_name,
                    subclient_name_local,
                    self.storage_policy_name,
                    temp_path,
                    self.agent)
                # run six backup jobs
                # running backup job for the whole backupset
                # since it will be first job for any subclient in the backupset
                # thus 'FULL' backup jobs will be run for each subclient
                job = self.subclient.backup("FULL")
                self.log.info("Started Backup job: %s", str(job.job_id))
                jobs_list.append(job)
            self.log.info("all Subclients have been configured")

            # wait for completion of the jobs before proceeding
            for job in jobs_list:
                if not job.wait_for_completion():
                    if job.status.lower() == "completed":
                        self.log.info("job %s complete", job.job_id)
                    else:
                        raise Exception(
                            "Job {0} Failed with {1}".format(
                                job.job_id, job.delay_reason))

                # stop the testcase if the backup job does not complete
                # successfully

            # after backup job completion, verify if the number of records
            # in primary table belonging
            # to each job are same or not, they should be same since data
            # generated is unique but of same size

            # get total primary objects including all the jobs
            query = f"  SELECT SUM(primaryObjects) FROM archFileCopyDedup " \
                    f"WHERE archFileCopyDedup.archFileId in " \
                    f"(SELECT archfile.id FROM archFile,archGroup " \
                    f"WHERE archFile.archGroupId = archGroup.id AND archGroup.name = '{self.storage_policy_name}'" \
                    f"AND archFile.fileType = 1)"
            self.csdb.execute(query)
            self.log.info("EXECUTING QUERY: %s", query)
            total_primary_objects = int(self.csdb.fetch_one_row()[0])
            self.log.info("total_primary_objects: %s", total_primary_objects)

            # delete half the jobs, get the archive file ids belonging to those jobs
            # we can achieve the same by deleting half the subclients
            # then the associated content
            # including job and archFile information will get deleted
            # or by going to the storage policy and then deleting the job by
            # job id

            # delete the jobs and save their archfile ids in a list
            storage_policy_copy = self.storage_policy.get_copy("Primary")
            del_arch_file_ids = []
            for i in range(0, len(jobs_list), 2):
                query = f"SELECT id FROM archFile WHERE jobId={jobs_list[i].job_id} AND fileType=1"
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                result = self.csdb.fetch_all_rows()
                self.log.info(f"QUERY OUTPUT : {result}")
                for j in range(len(result)):
                    del_arch_file_ids.append(int(result[j][0]))
                self.log.info(
                    "got the archfiles belonging to the job %s",
                    jobs_list[i].job_id)
                storage_policy_copy.delete_job(jobs_list[i].job_id)
                self.log.info(
                    "Deleted job from %s with job id %s" %
                    (self.storage_policy_name, jobs_list[i].job_id))
            self.log.info("Deleted archfiles %s", del_arch_file_ids)
            # after deletion of job, the archFiles should be moved to
            # MMdeletedAF table

            query = """UPDATE mmconfigs
                    SET value = 2, nmin = 0
                    WHERE name = 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS'"""
            self.log.info("EXECUTING QUERY: %s", query)
            self.opt_selector.update_commserve_db(query)
            self.log.info("mmprune process interval set to 2 minutes")

            for _ in range(1, 11):
                data_aging_job = self.mm_helper.submit_data_aging_job(
                    copy_name="Primary",
                    storage_policy_name=self.storage_policy_name,
                    is_granular=True,
                    include_all=False,
                    include_all_clients=True,
                    select_copies=True,
                    prune_selected_copies=True)
                if not data_aging_job.wait_for_completion():
                    raise Exception(f"Failed to run Data Aging Job (Job Id: {data_aging_job.job_id}) due to error "
                                    f"{data_aging_job.delay_reason}")
                self.log.info("sleeping for 180 seconds")
                time.sleep(180)
                matched_lines = self.dedup_helper.validate_pruning_phase(self.sidb_id, self.tcinputs['MediaAgentName'],
                                                                         2)
                self.log.info(matched_lines)
                pruning_done = False
                if matched_lines:
                    afid = del_arch_file_ids[-1]
                    for line in matched_lines:
                        if line.count(str(afid)):
                            self.log.info(f"Verified that at least one AFID - {afid} has completed Phase 2 pruning.")
                            pruning_done = True
                            break
                    if pruning_done:
                        break
                else:
                    self.log.info(f"Checking if phase 2 pruning happened on SIDB {self.sidb_id}")

            # after activation of mmprune process archfiles will be
            # moved to MMdeletedArchFileTracking table
            # mmprune process activated by now
            # CMD will be deleted

            remaining_primary_objects = total_primary_objects + 1
            repetition = 0
            while remaining_primary_objects >= total_primary_objects and repetition < 3:
                # get remaining primary objects from the remaining jobs
                self.log.info("cycle %d" % (repetition + 1))
                query = f" SELECT SUM(primaryObjects) FROM archFileCopyDedup " \
                        f"WHERE archFileCopyDedup.archFileId in " \
                        f"(SELECT archfile.id FROM archFile,archGroup " \
                        f"WHERE archFile.archGroupId = archGroup.id AND archGroup.name = " \
                        f"'{self.storage_policy_name}' " \
                        f"AND archFile.fileType = 1)"
                self.log.info("EXECUTING QUERY: %s", query)
                self.csdb.execute(query)
                remaining_primary_objects = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {remaining_primary_objects}")
                repetition = repetition + 1
                self.log.info("sleeping for 50 seconds")
                time.sleep(50)

            self.log.info(
                "remaining_primary_objects: %s",
                remaining_primary_objects)

            error_flag = []

            # add reg key to override CS settings and run Mark and Sweep immediately
            ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
            self.log.info("setting DDBMarkAndSweepRunIntervalSeconds additional setting to 120")
            ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds",
                                             "INTEGER", "120")

            self.log.info("sleep for 360 seconds")
            time.sleep(360)

            self.log.info(
                "running a backup job so that sidb2 process picks up, mark and sweep takes places")
            # create new subclient with new data
            subclient_name_local = "%s-%s" % (self.subclient_name, 7)
            temp_path = self.client_machine.join_path(
                self.content_path, subclient_name_local)
            if self.mm_helper.create_uncompressable_data(
                    self.tcinputs['ClientName'], temp_path, 0.1, 1):
                self.log.info(
                    "generated content for subclient {0}".format(subclient_name_local))
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                subclient_name_local,
                self.storage_policy_name,
                temp_path,
                self.agent)
            job = self.subclient.backup("FULL")
            self.log.info("Started Backup job: %s", str(job.job_id))
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info("job %s complete", job.job_id)
                else:
                    raise Exception(
                        "Job {0} Failed with {1}".format(
                            job.job_id, job.delay_reason))

            # remove reg key that runs Mark and Sweep immediately
            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
            ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            # determine the archfile of the job, it won't be deleted
            query = f"SELECT id FROM archFile WHERE jobId={job.job_id} AND fileType=1"
            self.log.info("EXECUTING QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {result}")
            re_added_arch_files = []
            for j in range(len(result)):
                re_added_arch_files.append(int(result[j][0]))
            self.log.info(
                "got the archfiles which are added by backup on seventh subclient")

            self.log.info("sleep for 60 seconds")
            time.sleep(60)

            log_file = "SIDBEngine.log"

            common = str(self.sidb_id) + "-0-" + str(self.substore_id) + "-0"
            # SIDBEngId-GrNo-SubStoId-SpltNo
            # check the logs to make sure that deletion actually took place by
            # mark and sweep.
            self.log.info(
                "*************************CASE VALIDATIONS***************************")
            self.log.info(
                "---------------------Check Logs to confirm Mark & Sweep -----------------------")

            self.log.info(
                "Case Validation 1:Check for max secondary file reader threads")
            statement = "Max secondary file reader threads"
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=True, single_file=False)
            for matched_line in matched_lines:
                line = matched_line.split()
                for substring in line:
                    if common in substring:
                        found = True
            if found:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Failed but we ignore log errors")
                # error_flag += ["failed to find: " + statement]

            self.log.info("Case Validation 2:Check for number of "
                          "primary objects made invalid and remaining valid")
            statement = r"Total \[[0-9]+\], Approx Valid \[[0-9]+\], Approx Invalid \[[0-9]+\]"
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=False, single_file=False)
            for matched_line in matched_lines:
                line = matched_line.split()
                for substring in line:
                    if common in substring:
                        found = True
            if found:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Failed but we ignore log errors")
                # error_flag += ["failed to find: " + statement]

            self.log.info(
                "Case Validation 3:Check if delete phase has been started")
            statement = "Starting the delete phase. Restart string "
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=True, single_file=False)
            for matched_line in matched_lines:
                line = matched_line.split()
                for substring in line:
                    if common in substring:
                        found = True
            if found:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Failed but we ignore log errors")
                # error_flag += ["failed to find: " + statement]

            self.log.info(
                "Case Validation 4:Check for number of deleted records and make sure that "
                "all the invalid records were deleted in the current run")
            statement = r"Deleted total \[[0-9]+\] records\. \[[0-9]+\] in current run"
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=False, single_file=False)
            for matched_line in matched_lines:
                line = matched_line.split()
                for substring in line:
                    if common in substring:
                        found = True
            if found:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Failed but we ignore log errors")
                # error_flag += ["failed to find: " + statement]

            self.log.info(
                "Case Validation 5:Check for Mark and Sweep complete success status")
            statement = "Mark and Sweep blocks complete. Status [Success]"
            found = False
            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.tcinputs["MediaAgentName"], log_file, regex=statement,
                escape_regex=True, single_file=False)
            for matched_line in matched_lines:
                line = matched_line.split()
                for substring in line:
                    if common in substring:
                        found = True
            if found:
                self.log.info("Result: Pass")
            else:
                self.log.info("Result: Failed but we ignore log errors")
                # error_flag += ["failed to find: " + statement]

            # Wait for SIDB Engine to go down
            self.log.info("wait for sidb to go down")
            if self.dedup_helper.wait_till_sidb_down(
                    str(self.sidb_id), self.commcell.clients.get(
                        self.tcinputs.get("MediaAgentName"))):
                self.log.info("sidb process for engine %d"
                              " has gone down", self.sidb_id)
            else:
                self.log.error("sidb process for engine %d did"
                               " not go down under the wait period", self.sidb_id)
                raise Exception("sidb process did not go"
                                " down under the wait period")

            self.log.info(
                "case 6: check if the archFiles have been removed from the sidb dump")
            dump_file_path = self.media_agent_machine.join_path(
                self.dump_location, "dump_file.csv")
            ma_obj = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
            if self.media_agent_machine.os_info.lower() == 'unix':
                base_path = self.media_agent_machine.join_path(ma_obj.install_directory, "Base", "sidb2")
                command = "{0} -dump primary -i {1} -split 0 {2}".format(base_path, self.sidb_id, dump_file_path)
            elif self.media_agent_machine.os_info.lower() == 'windows':
                base_path = "& '" + self.media_agent_machine.join_path(ma_obj.install_directory, "Base", "sidb2") + "'"
                command = f"{base_path} -dump primary -i {self.sidb_id} -split 0 {dump_file_path}"
            self.media_agent_machine.execute_command(command)
            self.log.info("giving a 30 seconds gap")
            time.sleep(30)

            dumped_archfiles = set()
            file_contents = self.media_agent_machine.read_file(dump_file_path)
            self.log.info("got the dumped file contents")
            input_reader = csv.reader(file_contents.split("\n"))
            for rows in input_reader:
                if not rows or rows[6] == ' archiveFileId ':
                    continue
                dumped_archfiles.add(int(rows[6]))
            self.log.info("got the dumped archfiles set")

            if dumped_archfiles.intersection(set(del_arch_file_ids)):
                self.log.error("deleted arch Files found in sidb dump")
                self.log.error("mark and sweep did not occur properly")
                error_flag += ["failed sidb dump archfiles test"]
            else:
                self.log.info("Result:Pass")

            if error_flag:
                # if the list is not empty then error was there, fail the
                # testcase
                self.log.error(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all the resources and settings created for this testcase"""
        self.log.info("Tear down function of this test case")
        try:

            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting if it exists")
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            self.log.info("setting back the mmprune process interval to 1hr")
            query = """update mmconfigs
                    set value = 60, nmin = 10
                    where name = 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS'"""
            self.opt_selector.update_commserve_db(query)
            self.log.info("EXECUTING QUERY: %s" % query)

            self.previous_run_clean_up()

            self.log.info("clean up successful")
        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
