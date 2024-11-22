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
from Laptop.laptoputils import LaptopUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Monikers [Documents] Acceptance test"
        self.applicable_os = self.os_list.WINDOWS
        self.utility = None
        self.machine_object = None
        self.cloud_object = None
        self.server_obj = None
        self.subclient_object = None
        self.utils = None
        self.laptop_utils = None

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
        self.laptop_utils = LaptopUtils(self)
        self.subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
        self.subclient_object.content = ['\%Documents%']

    def run(self):
        """Main function for test case execution"""
        try:

            self._log.info("Started executing {0} testcase".format(self.id))
            subclient_id = self.subclient_object.subclient_id
            status_list = cloudlaptop_constants.STATUS
            backup_wait_time = 60

        # -------------------------------------------------------------------------------------
        #
        #    SCENARIO-1:
        #       - Documents moniker validation with new data
        #    SCENARIO-2:
        #       - Documents moniker validation with Modified data
        #    SCENARIO-3:
        #       - Documents moniker validation with renamed data
        #    SCENARIO-4:
        #       - Remove %Documents moniker and validate backup
        # -------------------------------------------------------------------------------------
            documents_path = "C:\\Users\\admin\\Documents\\IncData"
            scenarios_list = ['SCENARIO-1', 'SCENARIO-2', 'SCENARIO-3', 'SCENARIO-4']
            each_scenario = 0
            while each_scenario < len(scenarios_list):
                if scenarios_list[each_scenario] == 'SCENARIO-1':
                # -------------------------------------------------------------------------------------
                    self.server_obj.log_step("""

                    SCENARIO-1:
                        - Add new content under Documents path
                        - Verify backup triggered after newcontent added and backup completed successfully
                        - Restore the data verify new content backed up or not

                    """, 100)

                # -------------------------------------------------------------------------------------
                    while True:

                        # ------ read the registry to check the run status of previous run ---- #
                        self._log.info("***** Reading the RunStatus value from registry *****")
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
                                           .format(self.tcinputs['ClientName'], backup_wait_time))
                            self.utility.sleep_time(backup_wait_time)

                        # -- Status: 0 - means currently no backup job is running --#
                        elif status_value == '0':

                            self._log.info("Adding data under Documents path: %s", str(documents_path))
                            self.laptop_utils.create_file(self.machine_object, documents_path, files=5)
                            self.cloud_object.wait_for_incremenatl_backup(self.machine_object)
                            self.cloud_object.source_dir = documents_path
                            self.cloud_object.subclient_content_dir = documents_path
                            self.cloud_object.out_of_place_restore(self.machine_object, self.subclient_object, cleanup=False)
                            self._log.info("***** Validation of backup with new content completed successfully *****")
                            each_scenario = each_scenario+1
                            break

                        # -- Status: 6 indicates previous backup job failed -- #
                        elif status_value == '6':
                            last_job_id = self.utility.check_reg_key(self.machine_object, "LaptopCache\\" + subclient_id, "JobID")
                            raise Exception("Last backup job [{0}] failed on client [{1}] . Please check the logs"
                                            .format(last_job_id, self.client.client_name))
                        else:
                            raise Exception("Unknown phase status on client [{0}]" .format(self.client.client_name))


                    if scenarios_list[each_scenario] == 'SCENARIO-2':
                    # -------------------------------------------------------------------------------------
                        self.server_obj.log_step("""

                        SCENARIO-2:
                            - Modify the files under Documents path
                            - Verify backup triggered after files modified and backup completed successfully
                            - Restore the data verify modified data backed up or not

                        """, 100)

                    # -------------------------------------------------------------------------------------
                    while True:

                        # ------ read the registry to check the run status of previous run ---- #
                        self._log.info("***** Reading the RunStatus value from registry *****")
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
                                           .format(self.tcinputs['ClientName'], backup_wait_time))
                            self.utility.sleep_time(backup_wait_time)

                        # -- Status: 0 - means currently no backup job is running --#
                        elif status_value == '0':

                            self._log.info("Modifying test data under Documents path: %s", str(documents_path))
                            self.machine_object.modify_test_data(documents_path, modify=True)
                            self.cloud_object.wait_for_incremenatl_backup(self.machine_object)
                            self.cloud_object.source_dir = documents_path
                            self.cloud_object.subclient_content_dir = documents_path
                            self.cloud_object.out_of_place_restore(self.machine_object, self.subclient_object, cleanup=False)
                            self._log.info("***** Validation of backup with modified data completed successfully *****")
                            each_scenario = each_scenario+1
                            break

                        # -- Status: 6 indicates previous backup job failed -- #
                        elif status_value == '6':
                            last_job_id = self.utility.check_reg_key(self.machine_object, "LaptopCache\\" + subclient_id, "JobID")
                            raise Exception("Last backup job [{0}] failed on client [{1}] . Please check the logs"
                                            .format(last_job_id, self.client.client_name))
                        else:
                            raise Exception("Unknown phase status on client [{0}]" .format(self.client.client_name))


                    if scenarios_list[each_scenario] == 'SCENARIO-3':
                    # -------------------------------------------------------------------------------------
                        self.server_obj.log_step("""

                        SCENARIO-3:
                            - Rename all files under Documents path
                            - Verify backup triggered after files renamed and backup completed successfully
                            - Restore the data verify renamed data backed up or not

                        """, 100)
                    # -------------------------------------------------------------------------------------

                        while True:

                            # ------ read the registry to check the run status of previous run ---- #
                            self._log.info("***** Reading the RunStatus value from registry *****")
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
                                               .format(self.tcinputs['ClientName'], backup_wait_time))
                                self.utility.sleep_time(backup_wait_time)

                            # -- Status: 0 - means currently no backup job is running --#
                            elif status_value == '0':

                                self._log.info("Rename the test data under Documents path: %s", str(documents_path))
                                self.laptop_utils.create_file(self.machine_object, documents_path, files=5)
                                self.machine_object.modify_test_data(documents_path, rename=True)
                                self.cloud_object.wait_for_incremenatl_backup(self.machine_object)
                                self.cloud_object.source_dir = documents_path
                                self.cloud_object.subclient_content_dir = documents_path
                                self.cloud_object.out_of_place_restore(self.machine_object, self.subclient_object, cleanup=True)
                                self._log.info("***** Validation of backup with renamed data completed successfully *****")
                                each_scenario = each_scenario+1
                                break

                            # -- Status: 6 indicates previous backup job failed -- #
                            elif status_value == '6':
                                last_job_id = self.utility.check_reg_key(self.machine_object, "LaptopCache\\" + subclient_id, "JobID")
                                raise Exception("Last backup job [{0}] failed on client [{1}] . Please check the logs"
                                                .format(last_job_id, self.client.client_name))
                            else:
                                raise Exception("Unknown phase status on client [{0}]" .format(self.client.client_name))


                    if scenarios_list[each_scenario] == 'SCENARIO-4':
                    # -------------------------------------------------------------------------------------
                        self.server_obj.log_step("""

                        SCENARIO-4:
                            - Remove %Documents moniker from subclient content and add some test under documents
                            - Wait for the backup job finished as per interval
                            - Perform browse and verify above content backed up or not
                                [added file under documents path should not be backed up]

                        """, 100)
                    # -------------------------------------------------------------------------------------

                        while True:

                            # ------ read the registry to check the run status of previous run ---- #
                            self._log.info("***** Reading the RunStatus value from registry *****")
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
                                               .format(self.tcinputs['ClientName'], backup_wait_time))
                                self.utility.sleep_time(backup_wait_time)

                            # -- Status: 0 - means currently no backup job is running --#
                            elif status_value == '0':

                                self.subclient_object.content = ['\%Music%'] # overwriting documents moniker with music
                                dont_backup_path = "C:\\Users\\admin\\Documents\\Dont_backup"
                                self._log.info("Adding test data under Documents path: %s", str(dont_backup_path))
                                self.laptop_utils.create_file(self.machine_object, dont_backup_path, files=5)
                                self.cloud_object.wait_for_incremenatl_backup(self.machine_object)
                                browse_result = self.subclient_object.browse(path=dont_backup_path)
                                if browse_result[0] or browse_result[1]: # brwose returns tuple of list and dictioanry values
                                    raise Exception("Data backed up after [Documents Moniker] removed [{0}]" .format(browse_result))
                                self._log.info("*** Validation of backup after [Documents Moniker] removal completed successfully ****")
                                self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
                                each_scenario = each_scenario+1
                                break

                            # -- Status: 6 indicates previous backup job failed -- #
                            elif status_value == '6':
                                last_job_id = self.utility.check_reg_key(self.machine_object, "LaptopCache\\" + subclient_id, "JobID")
                                raise Exception("Last backup job [{0}] failed on client [{1}] . Please check the logs"
                                                .format(last_job_id, self.client.client_name))
                            else:
                                raise Exception("Unknown phase status on client [{0}]" .format(self.client.client_name))

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            try:
                restore_path = 'C:\\Commvault_Automation\\TestData'
                self.machine_object.remove_directory(documents_path)
                self.machine_object.remove_directory(restore_path)
                self.machine_object.remove_directory(dont_backup_path)
            except Exception as error:
                self.log.info("Failed to cleanup subclient content {0}".format(error))

