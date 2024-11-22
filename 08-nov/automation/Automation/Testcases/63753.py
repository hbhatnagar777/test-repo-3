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

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.JobManager.jobmanager_helper import JobManager
from cvpysdk.job import Job
import time


class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - Indexing V2 - JM Suspend/Kill Parent and Child VM Jobs scenarios"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None
        }
        self.ind_status = True
        self.failure_msg = ''

    def get_child_jobs(self, parent_job_id):
        """ Get vm child jobs for a parent job, retry every 7 seconds for 10 attempts

                    Args:
                        parent_job_id        (str)    -- VSA parent job ID for subclient

                    Returns:
                        List    -- List of strings for child vm job IDs

                    Raises:
                        Exception if :

                            - No child jobs found even after 10 attempts
                """
        vm_child_jobs = ['']
        retry = 0
        while not vm_child_jobs[0] and retry < 10:
            _query = f"select childJobId from jmjobdatalink where parentJobId={parent_job_id}"
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            vm_child_jobs = [row[0] for row in _results]
            retry += 1
            time.sleep(7)

        if retry == 10:
            raise Exception("Couldn't fetch child jobs even after 10 attempts. Please check if child jobs were "
                            "generated for parent job - " + str(parent_job_id))
        self.log.info("Parent Job Id :{0} -> Child job per VMs :{1}".format(parent_job_id, vm_child_jobs))
        return vm_child_jobs

    def check_child_job_status(self, vm_child_jobs, expect_state):
        """ Validate all vm child job's status against a list of expected values

                    Args:
                        vm_child_jobs        (list)    -- List of VSA backup child jobs
                        expect_state         (list/str) -- String or list of strings with expected state for child jobs

                    Returns:
                        None

                    Raises:
                        Exception if :

                            - Unable to validate child job status
                """
        try:
            for childJob in vm_child_jobs:
                child_job_obj = Job(self.commcell, childJob)
                child_job_manager = JobManager(_job=child_job_obj, commcell=self.commcell)
                child_job_manager.validate_job_state(expected_state=expect_state)
        except Exception as exp:
            self.log.exception("Exception occurred in getting the job status: %s", str(exp))
            raise exp

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Running First Backup job on Parent subclient")
            parent_job_obj = self.subclient.backup(backup_level="FULL")
            parent_job_manager = JobManager(_job=parent_job_obj, commcell=self.commcell)

            try:
                self.log.info("Waiting for 20 seconds for child jobs to generate before suspending Parent job")
                time.sleep(20)
                self.log.info("Trying to suspend Parent Backup job")
                job_status = parent_job_manager.modify_job(
                    set_status="suspend", wait_for_state=True, hardcheck=True)

            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp

            self.log.info("Waiting for 60 seconds.")
            time.sleep(60)
            self.log.info("Checking if all Child jobs were suspended fine")
            vm_child_jobs = self.get_child_jobs(parent_job_obj.job_id)
            self.check_child_job_status(vm_child_jobs, expect_state='suspended')
            self.log.info("All Child jobs were suspended fine")

            try:
                self.log.info("Trying to resume Parent job")
                job_status = parent_job_manager.modify_job(
                    set_status="resume", wait_for_state=True, hardcheck=True)

            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp

            time.sleep(20)
            self.log.info("Waited for 20 seconds. Checking if all Child jobs were resumed fine")
            self.check_child_job_status(vm_child_jobs, expect_state=['running', 'waiting'])
            self.log.info("All Child jobs were resumed and running/waiting fine")

            try:
                self.log.info("Trying to kill Parent job")
                job_status = parent_job_manager.modify_job(
                    set_status="kill", wait_for_state=True, hardcheck=True)

            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp

            retry = 0
            while retry < 3:
                retry += 1
                time.sleep(20)
                self.log.info("Waited for 20 seconds. Checking if all Child jobs were killed fine")
                try:
                    self.check_child_job_status(vm_child_jobs, expect_state='killed')
                    self.log.info("All Child jobs were killed fine")
                    break
                except Exception as exp:
                    self.log.info("Attempt %s failed for Checking child jobs killed or not", str(retry))

            time.sleep(10)
            self.log.info("Running Second Backup job on Parent subclient")
            parent_job_obj2 = self.subclient.backup(backup_level="FULL")
            parent_job_manager2 = JobManager(_job=parent_job_obj2, commcell=self.commcell)

            try:
                self.log.info("Trying to kill Child Backup jobs")
                vm_child_jobs2 = self.get_child_jobs(parent_job_obj2.job_id)
                for childjobid in vm_child_jobs2:
                    try:
                        _ = JobManager(childjobid, commcell=self.commcell).modify_job(set_status="kill")
                    except Exception as exp:
                        self.log.info("Unable to kill Child job %s. Checking if it was completed/failed before "
                                      "we tried to kill it", str(childjobid))
                        try:
                            self.check_child_job_status([childjobid], expect_state=['completed', 'failed',
                                                                                    'completed w/ one or more errors'])
                        except Exception as exp2:
                            raise([exp, exp2])
                        else:
                            self.log.info("Child job %s was completed/failed before killing. Continuing."
                                          , str(childjobid))
                self.log.info("All child jobs killed fine (or completed/failed before attempting kill)")

            except Exception as exp:
                self.log.exception("Exception occurred in getting the job status: %s", str(exp))
                raise exp

            time.sleep(30)
            self.log.info("Waited for 30 seconds. Checking if parent job got killed fine")
            parent_job_manager2.validate_job_state(expected_state='killed')
            self.log.info("Parent job was killed automatically by killing all child jobs.")
            self.log.info("Tests completed.")

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.ind_status = False
            self.failure_msg = str(exp)

        finally:
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
