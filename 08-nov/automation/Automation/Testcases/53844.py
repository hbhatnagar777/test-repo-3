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
    __init__()            --  initialize TestCase class

    setup()               --  setup function of this test case

    run()                 --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server import serverhelper
from AutomationUtils.options_selector import OptionsSelector
from Laptop.CloudLaptop import cloudlaptophelper, cloudlaptop_constants
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate Backup functionality of a CloudLaptop"
        self.applicable_os = self.os_list.WINDOWS
        self.utility = None
        self.machine_object = None
        self.cloud_object = None
        self.server_obj = None
        self.subclient_object = None
        self.utils = None

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def setup(self):
        """ setup function of this test case """
        self.server_obj = serverhelper.ServerTestCases(self)
        self.cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
        self.utility = OptionsSelector(self._commcell)
        self.machine_object = self.utility.get_machine_object(self.tcinputs['ClientName'])
        self.utils = CommonUtils(self)
        self.subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])

        # adding some dummy content otherwise we can not remove the content added by testcase as part of clenaup
        self.subclient_object.content = ['\%Music%']

    def run(self):
        """Main function for test case execution"""
        try:

            self._log.info("Started executing {0} testcase".format(self.id))
            subclient_id = self.subclient_object.subclient_id
            status_list = cloudlaptop_constants.STATUS
        # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

                    1. Before start the backup , Check RunStatus of the registry key for previous failures

                    2. Proceed further based on RunStatus value:

                            2.1. IF RunStatus is in '1','2','3','4','5' indicates -"job is running"

                                  - Wait automatic schedule and check run status

                                  - if job status is not changed after retry interval exit program
                                            as job stuck in previous attempt

                            2.2. IF RunStatus is '0' indicates - "waiting for next attempt"

                                 - Validate incremental automatic schedule triggered backup

                                 - Validate all registry keys related to backup

                            2.3. IF RunStatus is '6' indicates - "Job failed in previous attempt"
                                  - Exit program with job failed message


            """, 200)

        # -------------------------------------------------------------------------------------
            osc_interval = self.cloud_object.get_osc_min_interval(self.subclient_object)
            backup_executed = False
            backup_wait_time = 60

            while True:
                # ------ read the registry to check the run status of previous run ---- #
                self._log.info("*** Reading the Rustatus value from registry***")
                status_value = self.utility.check_reg_key(
                    self.machine_object,
                    "LaptopCache\\" + subclient_id,
                    "RunStatus",
                    fail=False
                )
                # ------ check and wait for the backup status to be zero ---- #
                # -- Status: 1,2,3,4,5 - means currently backup job is running --#
                if status_value in status_list:
                    self._log.info("**** Currently Backup job is running on client [{0}]"
                                   "Waiting for [{1}] seconds for the backup job to be completed ***"
                                   .format(self.tcinputs['ClientName'], osc_interval))
                    self.utility.sleep_time(backup_wait_time)

                # -- Status: 0 - means currently no backup job is running --#
                elif status_value == '0':
                    self._log.info("*** validating new backup job on the client [{0}] ***".format(self.tcinputs['ClientName']))

                    self.cloud_object.incr_backup_and_restore(self.machine_object)

                    self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
                    backup_executed = True
                    break
                # -- Status: 6 indicates previous backup job failed -- #
                elif status_value == '6':
                    last_job_id = self.utility.check_reg_key(self.machine_object, "LaptopCache\\" + subclient_id, "JobID")
                    raise Exception("Last backup job [{0}] failed on client [{1}] . Please check the logs"
                                    .format(last_job_id, self.client.client_name))
                else:
                    raise Exception("Unknown phase status on client [{0}]" .format(self.client.client_name))
            if not backup_executed:
                raise Exception("Previous backup job stuck on client [{0}]. please check the logs"
                                .format(self.client.client_name))

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            try:
                self.subclient_object.content = ['\%Music%'] # overwriting / deleting absolate content added by testcase
            except Exception as error:
                self.log.info("Failed to cleanup subclient content {0}".format(error))

