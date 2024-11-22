# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import os

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.drorchestration.replicationmonitor import ReplicationMonitor
from AutomationUtils import constants
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VirtualServer-AdminConsole-ReplicationMonitor-PointInTimeFailover-UndoFailover"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.DRORCHESTRATION
        self.feature = self.features_list.DRORCHESTRATION
        self.show_to_user = True
        self.tcinputs = {
            "vmName": "",
            "VirtualizationClient": "",
            "approvalRequired": False,
            "initiatedfromMonitor": True
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.log.info(
                "-------------------Initialize ReplicationMonitor objects----------------\
                --------------------")

            replication_monitor = ReplicationMonitor(self.commcell, self.tcinputs)

            if isinstance(replication_monitor, ReplicationMonitor):

                failover_type_string = "PointInTimeFailover"


                self.log.info(
                    "----------------------------------------" +
                    failover_type_string + "-----------------------------------"
                )
                (job_id, task_id) = replication_monitor.point_in_time_failover()
                self.log.info(
                    failover_type_string +
                    " job launched with JobId: [" +
                    str(job_id) +
                    "] TaskId: [" +
                    str(task_id) +
                    "]")

                # wait for job till it is finished
                job_state = self.wait_for_job(job_id)
                if job_state:
                    # job Passed
                    try:
                        # do validations
                        is_passed = replication_monitor.validate_dr_orchestration_job(
                            job_id)

                        if is_passed:

                            self.log.info(
                                failover_type_string + " job: [" + str(job_id) + "] PASSED")

                            failover_type_string = "UndoFailover"

                            if isinstance(replication_monitor, ReplicationMonitor):
                                self.log.info(
                                    "----------------------------------------" +
                                    failover_type_string + "-----------------------------------"
                                )
                                (job_id, task_id) = replication_monitor.undo_failover()
                                self.log.info(
                                    failover_type_string +
                                    " job launched with JobId: [" +
                                    str(job_id) +
                                    "] TaskId: [" +
                                    str(task_id) +
                                    "]")

                                # wait for job till it is finished
                                job_state = self.wait_for_job(job_id)
                                if job_state:

                                    # do validations
                                    is_passed = replication_monitor.validate_dr_orchestration_job(
                                        job_id)

                                    if is_passed:
                                        self.log.info(
                                            failover_type_string + " job: [" + str(job_id) + "] PASSED")


                    except Exception as e:
                        self.log.error("Error occurred: " + str(e))
                        self.log.info(
                            failover_type_string + " job: [" + str(job_id) + "] FAILED")
                        raise Exception(failover_type_string + " job [" + str(
                            job_id) + "] Failed. Please check DROrchestration.log for \
                            failure reason")

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED



    def wait_for_job(self, job_id):
        """ Wait for Job with job Id"""

        try:

            # create job object and wait till it finished
            job = Job(self.commcell, job_id)
            job_state = job.wait_for_completion()
            self.log.info(" Job state: [" + str(job_state) + "]")
            if job_state:
                return True

            raise Exception(
                    " Job [" +
                    str(job_id) +
                    "] didn't launch. Please check testcase.log or CVD.log or EvMgrs.log \
                    for failure reason.")

        except Exception as e:
            self.log.error("Error occurred: " + str(e))
            raise Exception(str(e))


