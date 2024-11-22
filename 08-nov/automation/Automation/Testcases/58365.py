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

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    backup_job_with_neg_function()  -- decorator
    which runs "FULL" backup job and calls the negative
    function

    complete_backup_job()   -- decorator
    which takes over the executed backup jobs, calls the
    reverse functions

    restore_job_check_files()   -- runs a restore job
    and checks if the restored content is the same as
    original content.

    sidb_kill()     -- kills the sidb2 process

    cvd_kill()      -- kills the cvd process

    cvmountd_kill()     -- kills the cvmountd process

    media_agent_disable()   -- disables the media agent

    media_agent_maintenance_mark()  -- marks media agent for maintenance

    make_library_disabled()     -- disables the library

    media_agent_enable()        -- enables the mediaagent

    media_agent_maintenance_unmark()    -- unmark the media agent for maintenance

    make_library_enabled()      -- enables the library

    empty_pass_complete_job()   -- filler function for job execution

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

basic idea of the test case:
checks whether the negative case scenarios for media
agent are being resolved in the expected way as well as
verify if the media_agent_anomaly functions are working
or not.

validations used:
DDb verification job
Restored content comparison with original content
resuming back up jobs after the process are killed/go down
automatic start of the killed processes


input json file arguments required:

                        "ClientName": "name of the client machine without as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve"

                        # client and media agent machine should be different to
                        # make sure for test

Design steps:
1.	Kill sidb on MA
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writting)
c.	Kill sidb2 (we need to kill on DDB MA)
d.	Backup should go pending and in the background a data reconstruction job runs
f.	Make sure no errors
g.	Run DV2 job to verify DDB and backup content are good
i.	Make sure not chunk are marked bad

2.	Kill cvd on MA
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writing)
c.	Kill cvd (we need to kill on DDB MA and Data mover MA)
d.	Backup should go pending
e.	Bring cvd online
f.	Resume backup
g.	Make sure no errors
h.	Run restore to make backup content is good
i.	Compare restore content against backup content

3.	Kill cvmountd on MA
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writing)
c.	Kill CvMountD (we need to kill on Data mover MA)
d.	Backup should be in pending state
e.	Bring CvMoundD online
f.	Resume backup
g.	Make sure no errors
h.	Run restore to make backup content is good
i.	Compare restore content against backup content

4.	MA disable
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writing)
c.	Disable MA
d.	Make sure backup is not progressing
e.	Enable MA
f.	Resume backup
g.	Make sure no errors
h.	Run restore to make backup content is good
i.	Compare restore content against backup content

5.	MA maintenance
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writing)
c.	Disable MA
d.	Make sure backup is not progressing
e.	Enable MA
f.	Resume backup
g.	Make sure no errors
h.	Run restore to make backup content is good
i.	Compare restore content against backup content

6.	Library disable
a.	Run backup with 1 GB content
b.	While in backup phase (make sure chunks have started writing)
c.	Disable library
d.	Make sure backup is not progressing
e.	Enable library
f.	Resume backup
g.	Make sure no errors
h.	Run restore to make backup content is good
i.	Compare restore content against backup content


"""
import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from AutomationUtils.cvanomaly_management import CVAnomalyManagement



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
        self.name = """negative case scenarios for media agent 
        and verification of the media_agent_anomaly functions"""
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.media_agent_anomaly = None
        self.job = None

    def setup(self):
        """assign values to variables for testcase"""
        self.library_name = str(self.id) + "_lib"
        self.storage_policy_name = str(self.id) + "_SP"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

        self.media_agent_anomaly = CVAnomalyManagement().get_anomaly_handler(
            'media_agent', commcell_object=self.commcell, machine=self.tcinputs["MediaAgentName"])

    def previous_run_clean_up(self):
        """deletes items from the previous run of the testcase"""
        self.log.info("********* previous run clean up **********")
        try:
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(
                    self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def backup_job_with_neg_function(func):
        """starts the backup job and executes the required negative function

            Arguments
                func - the negative function which you want to execute
            Returns
                job - a job object with job in progress
        """
        def inner(*args):
            # start the backup job
            self = args[0]
            self.log.info("Starting FULL backup job")
            job = self.subclient.backup("FULL")
            # back up job started
            self.log.info("Backup job: %s", str(job.job_id))
            # now look if chunks have been started to be created

            self.log.info("Verify if chunk creation has started")
            query = """ select archChunkId
                                    from archChunkMapping
                                    where archFileId
                                    in (select id
                                        from archFile
                                        where jobId={0})""".format(job.job_id)
            self.log.info("EXECUTING QUERY %s", query)
            any_chunks_till_now = False
            upper_limit = 0
            # continue checking till even a single chunk is created but max
            # total try time = 360 seconds
            while not any_chunks_till_now and upper_limit < 180:
                time.sleep(2)  # wait for 2 second periods
                upper_limit += 1
                self.csdb.execute(query)
                chunks = self.csdb.fetch_all_rows()
                self.log.info(f"upper limit {upper_limit} chunks are {chunks}")
                any_chunks_till_now = bool(chunks[0][0])
                # make sure there is atleast one chunk which has been created
                # because archChunkId is PK, thus can check only first result
                if any_chunks_till_now:
                    # now call process killing functions
                    self.log.info("chunks till now are %s", str(chunks))
                    func(*args)     # some function
            if not any_chunks_till_now and upper_limit == 60:
                raise Exception("upper_limit of tries crossed and no chunk created till now")
            return job
        return inner

    def complete_backup_job(func):
        """completes the backup job started earlier. Also disables the negative setting if required
        """
        def inner(*args):
            # the back up should go to pending state
            self = args[0]
            time.sleep(3)
            self.log.info("status after 3 seconds sleep %s", self.job.status)

            self.log.info("pause here, the job should go to waiting state")
            self.log.info(
                "status before going to pause is %s",
                self.job.status)
            self.job._wait_for_status("waiting")
            self.log.info("status after the pause is %s", self.job.status)
            self.log.info("job status is %s", self.job.status)

            func(*args)

            if not self.job.wait_for_completion(timeout=50):
                # the timeout period changed to 50 minutes
                # the service should start automatically
                # the job should resume
                # the jobs should complete
                # if the job fails, fail the testcase
                raise Exception(
                    "Job {0} Failed with {1}".format(
                        self.job.job_id, self.job.delay_reason))
            self.log.info("job %s complete", self.job.job_id)
        return inner

    def restore_job_check_files(self):
        """checks and compares if the restored files are same as original content
            Arguments
                cpath - str - content path
                rpath - str - restored files path

            Returns
                bool    - True      - if the files are same after restore
                        - False     - if the files are not same after restore
        """
        self.log.info("running restore job")
        r_path = self.client_machine.join_path(
            self.restore_path, time.strftime("%d%m%Y-%H%M%S"))
        restorejob = self.subclient.restore_out_of_place(
            self.client.client_name,
            r_path,
            [self.content_path], True, True)
        self.log.info("restore job: %s", restorejob.job_id)
        if not restorejob.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(
                    restorejob.delay_reason))
        self.log.info("restore job completed")
        r_path = self.client_machine.join_path(
            r_path, "content_path")
        self.log.info("checking if the restored content is same as original")
        self.log.info("comparing folder hash values")
        diff_files = self.client_machine.compare_folders(
            self.client_machine, self.content_path, r_path)
        restored_files_same = False
        if not diff_files:
            restored_files_same = True
        return restored_files_same

    @backup_job_with_neg_function
    def sidb_kill(self):
        """kills the sidb2 process"""
        self.log.info("killing sidb process")
        result = self.media_agent_anomaly.kill_sidb_media_agent()
        self.log.info(str(result))

    @backup_job_with_neg_function
    def cvd_kill(self):
        """kills the cvd process"""
        self.log.info("killing cvd process")
        try:
            result = self.media_agent_anomaly.kill_communications_media_agent()
        except Exception as exp:
            if "Response was not success" not in str(exp):
                self.log.info("cvd process not killed")
                raise Exception(str(result))
            self.log.info("cvd process killed")

    @backup_job_with_neg_function
    def cvmountd_kill(self):
        """kills cvmountd process"""
        self.log.info("killing cvmountd process")
        result = self.media_agent_anomaly.kill_media_mount_manager()
        self.log.info(str(result))

    @backup_job_with_neg_function
    def media_agent_disable(self):
        """disables the media agent"""
        self.log.info("disable the media agent")
        self.media_agent_anomaly.enable_media_agent(False)
        self.log.info(
            "MediaAgent %s disabled",
            self.media_agent_anomaly.media_agent_object.media_agent_name)

    @backup_job_with_neg_function
    def media_agent_maintenance_mark(self):
        """media agent offline for maintenance"""
        self.log.info("mark the media agent offline for maintenance")
        self.media_agent_anomaly.offline_for_maintenance(True)
        self.log.info(
            "MediaAgent %s marked offline for maintenance",
            self.media_agent_anomaly.media_agent_object.media_agent_name)

    @backup_job_with_neg_function
    def make_library_disabled(self):
        """disables the library of this testcase"""
        result = self.media_agent_anomaly.library_enable(
            self.library_name, False)
        self.log.info(str(result))

    @complete_backup_job
    def media_agent_enable(self):
        """enables the media agent """
        self.log.info("enable the media agent")
        self.media_agent_anomaly.enable_media_agent()
        self.log.info(
            "MediaAgent %s enabled",
            self.media_agent_anomaly.media_agent_object.media_agent_name)

    @complete_backup_job
    def media_agent_maintenance_unmark(self):
        """brings media agent back online after maintenance"""
        self.log.info("unmark the media agent offline for maintenance")
        self.media_agent_anomaly.offline_for_maintenance(False)
        self.log.info(
            "MediaAgent %s UNmarked offline for maintenance",
            self.media_agent_anomaly.media_agent_object.media_agent_name)

    @complete_backup_job
    def make_library_enabled(self):
        """enables the library"""
        result = self.media_agent_anomaly.library_enable(
            self.library_name, True)
        self.log.info(str(result))

    @complete_backup_job
    def empty_pass_complete_job(self):
        """filler function"""
        self.log.info("Service should come up automatically")

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            # create the required resources for the testcase
            # get the drive path with required free space

            drive_path_client = self.opt_selector.get_drive(
                self.client_machine)
            drive_path_media_agent = self.opt_selector.get_drive(
                self.media_agent_machine)

            # creating testcase directory, mount path, content path, dedup
            # store path
            self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
            self.testcase_path_media_agent = "%s%s" % (
                drive_path_media_agent, self.id)

            self.mount_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "mount_path")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

            self.content_path = self.client_machine.join_path(
                self.testcase_path_client, "content_path")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists")
            else:
                self.client_machine.create_directory(self.content_path)
                self.log.info("content path created")

            self.restore_path = self.client_machine.join_path(
                self.testcase_path_client, "restore_path")
            if self.client_machine.check_directory_exists(self.restore_path):
                self.log.info("restore path directory already exists")
            else:
                self.client_machine.create_directory(self.restore_path)
                self.log.info("restore path created")

            # create library
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.tcinputs["MediaAgentName"], self.mount_path)

            # create SP
            self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.library_name,
                self.tcinputs["MediaAgentName"],
                self.dedup_store_path)

            # create backupset
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)

            # generate content for subclient
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, 1, 1):
                self.log.info(
                    "generated content for subclient %s",
                    self.subclient_name)

            # create subclient and add subclient content
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)

            error_flag = []
            self.log.info("VALIDATIONS AND CHECKS BEGIN")
            self.log.info("******************************************")
            self.log.info("******************************************")

            self.log.info("validate sidb2 process failure")
            self.log.info("******************************************")
            # mid back up job kill sidb2 process
            self.job = self.sidb_kill()
            # state waiting, recon should take up, automatically proceed
            self.empty_pass_complete_job()

            # now run data verification job
            self.log.info("run ddb verification job")
            ddb_job = self.storage_policy.run_ddb_verification(
                "primary", "FULL", "DDB_VERIFICATION")
            if not ddb_job.wait_for_completion():
                raise Exception(
                    "DDB Job {0} Failed with {1}".format(
                        ddb_job.job_id, ddb_job.delay_reason))
            self.log.info("DDB job %s complete", ddb_job.job_id)
            # no exceptions here, case passes
            self.log.info("sidb2 process verified")

            self.log.info("******************************************")
            self.log.info("validate cvmountd process failure")
            self.log.info("******************************************")
            # mid back up kill cvmountd process
            self.job = self.cvmountd_kill()
            self.empty_pass_complete_job()

            self.log.info(
                "run restore and compare the restored content with original content")
            if self.restore_job_check_files():
                self.log.info(
                    "restored content is same as the original content")
            else:
                self.log.info("restored content is not same as"
                              " original content for cvmountd process case")
                error_flag += ["restore content not same as"
                               " original content for cvmountd process case"]

            self.log.info("******************************************")
            self.log.info("validate cvd process failure")
            self.log.info("******************************************")
            # mid back up kill cvd process
            self.job = self.cvd_kill()
            self.empty_pass_complete_job()

            self.log.info(
                "run restore and compare the restored content with original content")
            if self.restore_job_check_files():
                self.log.info(
                    "restored content is same as the original content")
            else:
                self.log.info(
                    "restored content is not same as original content for cvd process case")
                error_flag += ["restore content not same as original content for cvd process case"]

            self.log.info("******************************************")
            self.log.info("validate disabled media agent scenario")
            self.log.info("******************************************")
            # mid back up job Media agent is disabled
            self.job = self.media_agent_disable()
            # after job goes to pending state, re enable the media agent
            # then proceed with the job, resume backup
            self.media_agent_enable()

            self.log.info(
                "run restore and compare the restored content with original content")
            if self.restore_job_check_files():
                self.log.info(
                    "restored content is same as the original content")
            else:
                self.log.info("restored content is not same as original"
                              " content for media agent disabled scenario")
                error_flag += ["restore content not same as original "
                               "content for media agent disabled scenario"]

            self.log.info("******************************************")
            self.log.info(
                "validate media agent offline marked for maintenance scenario")
            self.log.info("******************************************")
            # mid back up job Media agent is marked for maintenance, it goes
            # offline
            self.job = self.media_agent_maintenance_mark()
            # after job goes to pending state, un mark the media agent for maintenance
            # then proceed with the job, resume backup
            self.media_agent_maintenance_unmark()

            self.log.info(
                "run restore and compare the restored content with original content")
            if self.restore_job_check_files():
                self.log.info(
                    "restored content is same as the original content")
            else:
                self.log.info("restored content is not same as original content for "
                              "media agent offline marked for maintenance scenario")
                error_flag += ["restore content not same as original content for "
                               "media agent offline marked for maintenance scenario"]


            # commented out library disabled part in runs till library qscript calls is fixed.

            self.log.info("******************************************")
            self.log.info("validate disabled library scenario")
            self.log.info("******************************************")
            # mid back up job library is disabled
            self.job = self.make_library_disabled()
            # after job goes to pending state, mark the library as enabled
            # then proceed with the job, resume backup
            self.make_library_enabled()

            self.log.info("run restore and compare the restored content with original content")
            if self.restore_job_check_files():
                self.log.info("restored content is same as the original content")
            else:
                self.log.info("restored content is not same as"
                              " original content for disabled library scenario")
                error_flag += ["restore content not same as original"
                               " content for disabled library scenario"]

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.error(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted the restored data.")
            else:
                self.log.info("Restore directory does not exist.")

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

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted")
            else:
                self.log.info("Library does not exist.")
            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
