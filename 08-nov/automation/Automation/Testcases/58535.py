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

    run()           --  run function of this test case

    stop_MA_service()       --  Stop MediaAgent(GxMMM) service before recall.

    validate_recall_from_secondary()    -- Validates through log that files were recalled from secondary.

    start_MA_service()      --  Start MediaAgent(GxMMM) service after recall.

    restart_library_service()       --  Restart MediaAgent(GxMLM) service before recall.

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.machine import Machine
import datetime
import time


class TestCase(CVTestCase):
    """Class to verify recall from secondary."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "To verify recall from secondary."
        self.show_to_user = True
        self.base_folder_path = None
        self.OPHelper = None
        self.MAHelper = None
        self.is_nas_turbo_type = False
        self.sp = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "SecondaryCopyName": None,
            "SecondaryCopyLibraryName": None,
            "SecondaryMAName": None,
            "PrimaryMAName": None,
            "PrimaryCopyName": None
        }

    def stop_MA_service(self):
        """
            Stop MediaAgent(GxMMM) service before recall.
        """
        if "linux" not in self.commcell.clients.get(self.tcinputs['PrimaryMAName']).os_info.lower():
            client_instance = self.commcell.clients.get(self.tcinputs['PrimaryMAName']).instance
            service_name = 'GxMMM({})'.format(client_instance)
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).stop_service(service_name)
            return True
        else:
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).stop_service()

    def start_MA_service(self):
        """
            Start MediaAgent(GxMMM) service after recall.
        """
        if "linux" not in self.commcell.clients.get(self.tcinputs['PrimaryMAName']).os_info.lower():
            client_instance = self.commcell.clients.get(self.tcinputs['PrimaryMAName']).instance
            service_name = 'GxMMM({})'.format(client_instance)
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).start_service(service_name)
            return True
        else:
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).start_service()

    def restart_library_service(self):
        """
            Restart MediaAgent(GxMLM) service before recall.
        """
        if "linux" not in self.commcell.clients.get(self.tcinputs['PrimaryMAName']).os_info.lower():
            client_instance = self.commcell.clients.get(self.tcinputs['PrimaryMAName']).instance
            service_name = 'GxMLM({})'.format(client_instance)
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).restart_service(service_name)
            return True
        else:
            self.commcell.clients.get(self.tcinputs['PrimaryMAName']).restart_service()

    def validate_recall_from_secondary(self, copy_id):
        # 2020-06-03 02:36:23.428395
        lastMinsDateTime = datetime.datetime.now() - datetime.timedelta(minutes=10)

        # 06/03 02:36:23
        timestamp = str(lastMinsDateTime.strftime('%m/%d %H:%M:%S'))

        # Year is lost as it not logged in CS logs.
        # 1900-06-03 02:36:23
        past_10_minutes = datetime.datetime.strptime(timestamp, '%m/%d %H:%M:%S')
        search_term = 'CopyId - ' + str(copy_id)
        self.log.info(search_term)
        if self.is_nas_turbo_type:
            proxy_machine = Machine(machine_name=self.tcinputs.get("ProxyClient"),
                                    commcell_object=self.commcell)
            log_lines = proxy_machine.get_logs_for_job_from_file(log_file_name='ClMgrS.log',
                                                                 search_term=search_term)
        else:
            log_lines = self.OPHelper.client_machine.get_logs_for_job_from_file(log_file_name='ClMgrS.log',
                                                                                search_term=search_term)

        if log_lines is not None:
            for log_line in log_lines.split("\r\n"):
                logs = list(log_line.split())
                result_log_time = str(logs[2] + " " + logs[3])
                log_timestamp = datetime.datetime.strptime(result_log_time, '%m/%d %H:%M:%S')
                if past_10_minutes < log_timestamp:
                    self.log.info("Found the secondary copy id in clmgrs logs in last 10 minutes")
                    return True
        self.log.info("The files are not recalled from Secondary MA")
        return False

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.MAHelper = MMHelper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.MAHelper.configure_storage_policy(storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                               library_name=self.tcinputs.get('PrimaryCopyLibraryName'),
                                               ma_name=self.tcinputs.get('PrimaryMAName'))
        self.sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyName'))
        self.MAHelper.configure_secondary_copy(sec_copy_name=self.tcinputs.get('SecondaryCopyName'),
                                               storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                               library_name=self.tcinputs.get('SecondaryCopyLibraryName'),
                                               ma_name=self.tcinputs.get('SecondaryMAName'))

        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.base_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.base_folder_path])

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%', '%Audio%']}
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Configure Primary and Secondary copy. 
        2. Run Archiving Job on primary. 
        3. Run Auxcopy job. 
        4. Stop GxMMM Services on Primary Media Agent, perform Recall and Validate that file is recalled from secondary copy.
        5. Start services and delete jobs from primary. 
        6. Delete all archiving jobs and Run Data Aging. 
        7. Run Recall and Validate that file is recalled from secondary copy.
        """

        try:
            job = self.OPHelper.run_archive(repeats=3)

            time.sleep(300)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            # Commented below lines as Aux copy job is ran automatically now.
            # self.log.info("Start Running Aux Copy")
            # aux_job = self.sp.run_aux_copy(storage_policy_copy_name=self.tcinputs.get('SecondaryCopyName'),
            #                                media_agent=self.tcinputs.get('PrimaryMAName'))
            # if aux_job.wait_for_completion():

            # self.log.info("Completed Running Aux Copy")

            self.log.info('Stopping services for ' + str(
                self.commcell.clients.get(self.tcinputs['PrimaryMAName']).client_name))
            self.stop_MA_service()
            self.restart_library_service()
            time.sleep(30)
            try:
                self.log.info('Trying recall from secondary as primary is offline.')
                try:
                    self.OPHelper.recall(org_hashcode=[self.OPHelper.org_hashcode[0]],
                                         path=self.OPHelper.client_machine.join_path(self.base_folder_path,
                                                                                     self.OPHelper.test_file_list[0][
                                                                                         0]))
                except Exception:
                    self.log.info("Trying one more recall")
                    time.sleep(120)

                self.OPHelper.recall(org_hashcode=[self.OPHelper.org_hashcode[0]],
                                     path=self.OPHelper.client_machine.join_path(self.base_folder_path,
                                                                                 self.OPHelper.test_file_list[0][
                                                                                     0]))

                self.log.info('Recall Success')
            except Exception:
                raise Exception("Recall failed.")
            finally:
                self.log.info('Starting services for ' + str(
                    self.commcell.clients.get(self.tcinputs['PrimaryMAName']).client_name))
                self.start_MA_service()
                time.sleep(30)

            if not self.validate_recall_from_secondary(self.sp.get_copy(self.tcinputs.get('SecondaryCopyName'))
                                                               .get_copy_id()):
                raise Exception("The files are not recalled from secondary storage.")
            self.log.info("The files are recalled from Secondary MA")
            self.log.info("Deleting archive jobs")

            self.sp.get_copy(self.tcinputs.get('PrimaryCopyName')).delete_job(job_id=job[0].job_id)
            self.sp.get_copy(self.tcinputs.get('PrimaryCopyName')).delete_job(job_id=job[1].job_id)
            self.sp.get_copy(self.tcinputs.get('PrimaryCopyName')).delete_job(job_id=job[2].job_id)
            time.sleep(240)

            self.log.info("Deleted all archiving jobs, started running data aging")

            if self.commcell.run_data_aging().wait_for_completion():
                time.sleep(240)
                self.log.info("Data aging completed. Restarting Library services")
                self.restart_library_service()
                time.sleep(120)
                try:
                    self.OPHelper.recall()
                except Exception:
                    self.log.info("Trying one more recall")
                    time.sleep(120)
            self.OPHelper.recall()

            if not self.validate_recall_from_secondary(self.sp.get_copy(self.tcinputs.get('SecondaryCopyName'))
                                                       .get_copy_id()):
                raise Exception("The files are not recalled from secondary storage.")
            self.log.info("The files are recalled from Secondary MA")

            self.log.info('Recall from secondary passed.')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Recall from secondary failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
