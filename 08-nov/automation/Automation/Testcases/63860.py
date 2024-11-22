# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""

non dedupe pruning over UNC network share mountpath using domain credentials




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

This testcase verifies if non dedup pruning occurs successfully over UNC

testcase will generate content to be backed up and then delete
it after the run is over.

input json file arguments required:

                        "ClientName": "name of the client machine as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve",
                        "username": username for access to the share,
                        "password": pwd for access to the share

"""

# Design Steps:
# 1.  Create network share on remote ma using input credentials
# 2.  create credential in credential manager
# 3.  add mountpath with this network share and credential
# 4.  create non dedup storage policy
# 5.  create subclient and associate above SP to it.
# 6.  Run a full backup.  Save the chunkids created by the backup.  Get the full path to the chunks.
# 7.  Change pruning interval to 2 minutes.
# 8.  Delete the backup job.
# 9.  confirm after wait period that mmdeletedaf entries for chunkids get removed
# 10. confirm existence check fails for the chunk files and chunkmap_trailer files


import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import config
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "non dedup pruning over network share mountpath "
        self.tcinputs = {
            "MediaAgentName": None,
            "username": None,
            "password": None
        }

        self.mount_path = None
        self.mount_location = None
        self.content_path = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.opt_selector = None
        self.storage_policy_id = None
        self.testcase_path = None
        self.client_machine = None
        self.media_agent_machine1 = None
        self.media_agent_obj1 = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.drive_path_media_agent = None
        self.media_agent_path = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.error_flag = None
        self.sql_username = None
        self.sql_password = None
        self.MA_name_FQDN = None
        self.storage_pool_name = None
        self.storage_pool = None

    def setup(self):
        """Setup function of this test case"""

        self.opt_selector = OptionsSelector(self.commcell)
        self.backupset_name = '%s_BS_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.subclient_name = '%s_SC_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.storage_pool_name = '%s_POOL_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))
        self.storage_policy_name = '%s_SP_%s' % (str(self.id), self.tcinputs.get("MediaAgentName"))

        # create client source content path to be used as subclient content
        self.client_machine = machine.Machine(self.client, self.commcell)
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25 * 1024)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        # create mediaagent path to be used as mountpath
        self.media_agent_obj1 = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))
        self.media_agent_machine1 = machine.Machine(self.tcinputs.get("MediaAgentName"), self.commcell)
        self.MA_name_FQDN = self.media_agent_machine1.client_object.client_hostname
        self.drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine1, 25 * 1024)
        self.testcase_path_media_agent = self.media_agent_machine1.join_path(self.drive_path_media_agent,
                                                                             f'test_{self.id}')
        self.media_agent_path = self.media_agent_machine1.join_path(self.testcase_path_media_agent, f"mount_path")

        self.error_flag = []
        self.mm_helper = mahelper.MMHelper(self)

        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:
            # disable ransomware protection so mountpath cleanup works
            self.log.info("disabling ransomware protection intentionally on MA and sleeping for 1 minute")
            self.media_agent_obj1.set_ransomware_protection(False)
            time.sleep(60)

            if self.media_agent_machine1.check_directory_exists(self.media_agent_path):
                self.media_agent_machine1.unshare_directory(f'share_{self.id}')
            if self.media_agent_machine1.check_directory_exists(self.testcase_path_media_agent):
                self.media_agent_machine1.remove_directory(self.testcase_path_media_agent)
            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
            if self.commcell.storage_pools.has_storage_pool(
                    self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
            if self.commcell.credentials.has_credential(self.id):
                self.commcell.credentials.delete(self.id)
            # re-enable ransomware protection
            self.log.info("re-enabling ransomware protection intentionally on MA")
            self.media_agent_obj1.set_ransomware_protection(True)
            time.sleep(10)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_full_backup_job(self):
        """
            run a full backup job

            Returns ->
                an object of full backup job which has been started just now
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

            self.log.info("Started executing testcase %s", self.id)

            # creating mountpath, creating share
            if not self.media_agent_machine1.check_directory_exists(self.media_agent_path):
                self.media_agent_machine1.create_directory(self.media_agent_path)
            self.media_agent_machine1.share_directory(f'share_{self.id}',
                                                      self.media_agent_path, user=self.tcinputs.get("username"))
            self.mount_location = f"\\\\{self.MA_name_FQDN}\\share_{self.id}"

            # creating credential in credential manager
            if not self.commcell.credentials.has_credential(self.id):
                self.commcell.credentials.add("windows", self.id, self.tcinputs.get("username"),
                                              self.tcinputs.get("password"), "cred for automation TC 63860")

            # creating non dedup storage pool
            self.log.info(f"Configuring storage pool {self.storage_pool_name}")
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mount_location,
                                                                    self.tcinputs['MediaAgentName'],
                                                                    ddb_ma=None, dedup_path=None,
                                                                    credential_name=self.id)

            self.storage_policy = self.commcell.policies.storage_policies.add(
                                storage_policy_name=self.storage_policy_name, global_policy_name=self.storage_pool_name,
                                global_dedup_policy=False)

            # create backupset and subclient
            self.opt_selector.create_uncompressable_data(self.client.client_name, self.content_path, size=1,
                                                         num_of_folders=1, delete_existing=True)
            self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name, self.subclient_name, f"{self.storage_policy_name}",
                self.content_path, self.agent)

            # run full backup
            job = self.run_full_backup_job()

            # get chunk list and full path to them from completed full backup job
            storage_policy_copy = self.storage_policy.get_copy("Primary")
            chunk_ids = []
            chunk_fullpath = []
            os_sep = self.media_agent_machine1.os_sep
            chunk_list = self.mm_helper.get_chunks_for_job(job.job_id)

            for itr in range(len(chunk_list)):
                chunk_ids.append(int(chunk_list[itr][3]))
                chunk_fullpath.append(chunk_list[itr][0] + os_sep + chunk_list[itr][1] + os_sep +
                                      'CV_MAGNETIC' + os_sep + chunk_list[itr][2] + os_sep + 'CHUNK_' +
                                      chunk_list[itr][3])
                chunk_fullpath.append(chunk_list[itr][0] + os_sep + chunk_list[itr][1] + os_sep +
                                      'CV_MAGNETIC' + os_sep + chunk_list[itr][2] + os_sep + 'CHUNKMAP_TRAILER_' +
                                      chunk_list[itr][3])
            self.log.info(
                "got the list of chunks belonging to the job %s",
                job.job_id)
            self.log.info("Here is the list of full paths to each chunk and chunkmap trailer file: %s", chunk_fullpath)

            # delete backup job
            storage_policy_copy.delete_job(job.job_id)
            self.log.info(
                "Deleted job from %s with job id %s" %
                (self.storage_policy_name, job.job_id))
            self.log.info("Deleted chunk ids %s", chunk_ids)
            # after deletion of job, the chunk ids should be moved to
            # MMdeletedAF table

            # set pruning thread time interval
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=2)

            # run dataaging
            data_aging_job = self.mm_helper.submit_data_aging_job(
                copy_name="Primary",
                storage_policy_name=self.storage_policy_name,
                is_granular=True, include_all=False,
                include_all_clients=True,
                select_copies=True,
                prune_selected_copies=True)
            if not data_aging_job.wait_for_completion():
                raise Exception(
                    f"Failed to run Data Aging Job (Job Id: {data_aging_job.job_id}) \
                    due to error {data_aging_job.delay_reason}")
            self.log.info("sleeping for 10 minutes to allow pruning to run twice")
            time.sleep(600)

            # validate that chunks from backup job have been removed from mmdeletedaf table
            chunklist_string = ','.join(str(itr) for itr in chunk_ids)
            query = """SELECT archchunkid
                            FROM mmdeletedaf
                            WHERE archchunkid in ({0})
                            """.format(chunklist_string)
            self.log.info("EXECUTING QUERY: %s", query)
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            self.log.info("query results: %s", result)

            if result[0][0] == '':
                self.log.info("Verified all nondedup chunks were deleted from mmdeletedaf")
            else:
                self.log.error("Result: Failed")
                self.error_flag += ["chunks in mmdeletedaf"]
                raise Exception(f"testcase failed: [{self.error_flag}]")

            # confirm that chunk files were physically deleted
            for itr in chunk_fullpath:
                self.log.info("this is path being checked: " + str(itr))
                if self.media_agent_machine1.check_file_exists(chunk_fullpath):
                    self.log.error("Result: Failed")
                    self.error_flag += ["chunk files still exist"]
                    raise Exception(f"testcase failed: [{self.error_flag}]")
                else:
                    self.log.info("chunk file successfully deleted")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all the resources and settings created for this testcase"""
        self.log.info("Tear down function of this test case")
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')
        try:

            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.log.info("setting back the mmprune process interval to 1hr")

            # set pruning thread time interval
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=60)

            # unconditional cleanup
            self.log.info("running unconditional cleanup")
            self.previous_run_clean_up()

        except Exception as exp:
            self.log.info("clean up ERROR %s", exp)
