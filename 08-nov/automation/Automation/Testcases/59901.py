# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    create_helper_object()      --  creates object of OracleHelper class

    run_backup()                --  method to run backup

    get_sequence()              --  method to get log sequence to restore

    run_restore()               --  method to run restore and validate test data

    validate_restore()          --  method to validate restore from RMAN restore log

    run()                       --  run function of this test case


Input Example:

    "testCases":
        {
            "59901":
                {
                    "ClientName": "RAC PseudoClient",
                    "InstanceName": "RAC Instance",
                    "AgentName": "Oracle RAC",
                    "SubclientName": "ArchiveLog"
                    'DestClient': "Destination Client",
                    'DestInstance': "Destination Oracle Instance",
                    'LogDest': "Restore Destination"
                }
        }


"""
import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from cvpysdk.cvpysdk import CVPySDK
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper, OracleRACHelper


class TestCase(CVTestCase):
    """ Class for executing Oracle Archive log cross machine restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle Archive log cross machine restore"
        self.tcinputs = {
            'ClientName': None,
            'AgentName': None,
            'InstanceName': None,
            'SubclientName': None,
            'DestClient': None,
            'DestInstance': None,
            'LogDest': None
            }
        self.oracle_helper_object = None
        self.cvpysdk_object = None
        self.dest_client = None
        self.backup_json = None
        self.restore_json = None

    def setup(self):
        """ Method to setup test variables """
        self.dest_client = self.commcell.clients.get(self.tcinputs.get("DestClient"))

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            dest_client_machine_obj = Machine(self.dest_client)
            path = dest_client_machine_obj.join_path(self.tcinputs.get("LogDest"), "1_*.dbf")
            files = dest_client_machine_obj.execute_command(f"ls {path}").output.split()
            for file in files:
                dest_client_machine_obj.delete_file(file)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def create_helper_object(self):
        """Creates oracle RAC helper object"""
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def run_backup(self):
        """ method to run backup"""
        job_obj = self.subclient.backup()
        self.log.info("backup job started:%s", job_obj.job_id)
        return job_obj.job_id

    @test_step
    def get_sequence(self, job_id):
        """ method to get log start and end sequence to restore"""
        backup_file = None
        nodes = self.oracle_helper_object.get_nodes()
        for node in nodes:
            node_obj = self.commcell.clients.get(node)
            try:
                backup_file = self.oracle_helper_object.fetch_rman_log(job_id, node_obj, "backup")
            except Exception as str_err:
                self.log.info("Unable to fetch backup RMAN log from node: %s, %s", node, str_err)
        if not backup_file:
            raise CVTestStepFailure("Failed to retrieve RMAN backup log from both nodes")
        split1 = backup_file.split("input archived log thread=1 sequence=", 1)
        startlsn = re.findall(r'\d+', split1[1])[0]
        if backup_file.count("input archived log thread=1 sequence=") == 1:
            endlsn=startlsn
        else:
            split2 = split1[1].rsplit("input archived log thread=1 sequence=", 1)
            endlsn = re.findall(r'\d+', split2[1])[0]
        self.log.info("start log sequence: %s", startlsn)
        self.log.info("end log sequence: %s", endlsn)
        return startlsn, endlsn

    @test_step
    def run_restore(self, startlsn, endlsn):
        """ method to run restore"""
        job_obj = self.instance.restore_in_place(dest_client_name=self.tcinputs.get("DestClient"),
                                                 dest_instance_name=self.tcinputs.get("DestInstance"),
                                                 db_password="", path=[f"SID: {self.tcinputs.get('InstanceName')}"],
                                                 restore_oracle_options_type="restore_archivelogs_norecover",
                                                 start_lsn=startlsn, end_lsn=endlsn,
                                                 log_dest=self.tcinputs.get("LogDest"))
        return job_obj.job_id

    @test_step
    def validate_restore(self, job_id):
        """ method to validate cross instance procedure is not applied for restore"""
        restore_file = self.oracle_helper_object.fetch_rman_log(job_id, self.dest_client, "restore")
        if re.search("NID", restore_file, re.IGNORECASE):
            raise CVTestStepFailure(
                "Cross instance restore procedure is applied for archive log restore without recover")
        self.log.info("NID is not used. Cross instance restore procedure is not"
                      " applied for archive log restore without recover")

    def run(self):
        """ Main function for test case execution """
        try:
            self.create_helper_object()
            job_id = self.run_backup()
            self.wait_for_job_completion(int(job_id))
            start_lsn, end_lsn = self.get_sequence(job_id)
            job_id = self.run_restore(start_lsn, end_lsn)
            self.wait_for_job_completion(int(job_id))
            self.validate_restore(job_id)

        except Exception as exp:
            handle_testcase_exception(self, exp)
