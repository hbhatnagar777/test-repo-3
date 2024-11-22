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

    update_reg_keys() --  updates required  registry keys

    verify_logs() --  verifies logs to conclude

"""
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

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
        self.name = "Verify Basic Validation for Follow Mount Point from logs"
        self.client_machine = None
        self.helper = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName":None
        }

    def setup(self):
        """Setup function of this test case"""
        self.fs_helper = FSHelper(self)
        self.fs_helper.populate_tc_inputs(self,mandatory=False)
        self.test_path = self.tcinputs["TestPath"]
        self.client_machine = Machine(self.client)
        self.cs_machine = Machine(self.commcell.commserv_client)

    def is_mountpath_parameter_passed(self, job:object) -> bool:
        """
            Verifies from job manager log if mountpath parameter is passed or not for the job.
            Args:
                  job (job object) - job object for backup function.
        """
        matched_line = self.cs_machine.get_logs_for_job_from_file(job_id = job.job_id,
                                                                  log_file_name="JobManager.log",
                                                                  search_term="-mountPath")
        if matched_line:
            self.log.info("Mount Parameter Passed")
            self.log.info(f"Verified by Log Line : {matched_line}")
            return True
        else:
            self.log.info("Mount Parameter Not Passed")
            return False

    def run(self):
        """Run function of this test case"""
        try:
            #Configuring seperator based on OS
            os_sep = self.client_machine.os_sep
            if self.test_path.endswith(os_sep):
                self.test_path = self.test_path.rstrip(os_sep)
            
            #Creating a backupset
            self.log.info(
                "Create a backupset for the scenarios if not already present."
            )
            backupset_name = "backupset_" + self.id
            self.fs_helper.create_backupset(backupset_name, delete=True)
            self.backupset_name = backupset_name

            #Configuring paths for backups
            self.log.info("Configuring paths for backups")
            sc_name = "_".join(("subclient", str(self.id)))
            subclient_content = [self.client_machine.join_path(self.test_path, sc_name)]
            run_path = self.client_machine.join_path(subclient_content[0], str(self.runid))
            full_con_path = self.client_machine.join_path(run_path, "full")
            inc_con_path = self.client_machine.join_path(run_path, "inc")

            #Creating a subclient
            self.log.info("Creating subclient")
            self.fs_helper.create_subclient(
                name=sc_name,
                storage_policy=self.tcinputs["StoragePolicyName"],
                content=subclient_content,
                allow_multiple_readers=True,
            )

            #Verify MP option is on
            #Value should be 1 
            self.log.info("Verifying Follow MP option is set correctly")
            follow_mp_option = self.subclient.properties["fsSubClientProp"]["followMountPointsMode"] 
            if not follow_mp_option :
                self.log.info("Follow MP option is not set")
                raise Exception("Follow MP option is not set")
            self.log.info("Follow MP option is set correctly")
            
            #Adding data for backup
            self.log.info("Add Data for Full Backup.")
            self.client_machine.generate_test_data(full_con_path)

            #Running backup for subclient
            job_id = self.helper.run_backup(backup_level="Full", wait_to_complete=True)[0]

            if not self.is_mountpath_parameter_passed(job_id):
                raise Exception("-mouthpath parameter is not passed")
            self.log.info("-mouthpath parameter is passed")
            
            #Adding data for incremental backups
            self.log.info("Add data for the INCREMENTAL Backup")
            self.client_machine.generate_test_data(inc_con_path)

            #Turning off Follow MP option
            d = {"fsSubClientProp" : { "followMountPointsMode" : 0 }}
            self.subclient.update_properties(d)
            self.commcell.refresh()

            #Verify MP option is off
            #Value should be 0
            follow_mp_option = self.subclient.properties["fsSubClientProp"]["followMountPointsMode"] 
            if follow_mp_option :
                self.log.info("Follow MP option is on and not changed")
                raise Exception("Follow MP option is on and not changed")
            self.log.info("Follow MP option is updated correctly")

            #Running incr backup for subclient
            job_id = self.helper.run_backup(backup_level="Incremental", wait_to_complete=True)[0]

            if self.is_mountpath_parameter_passed(job_id):
                raise Exception("-mouthpath parameter is passed despite being off is subclient property")
            self.log.info("-mouthpath parameter is not passed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        
        finally:
            if self.cleanup_run:
                self.log.info("Deleting and cleaning up")
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.backupset_name)
