# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test case to Verify backup content path exists in browser and restore report"""
import time
import os
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to Verify backup content path exists in browser and restore report"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify backup content path exists in browser and restore report"
        self.utils = TestCaseUtils(self)
        self.client_machine = None
        self._backupset_name = None
        self._subclient_name = None
        self.subclient_content_path = None
        self.bkp_content_temp_folder = None
        self.report_custom_name = "backup_job_summary_custom_name.HTML"
        self.report_saved_path = "c:\\automation_54384"
        self.tcinputs = {
            'storage_policy_name': None
        }

    def generate_data_for_backup(self):
        """Generate data for backup"""
        self.log.info("Generating data for backup")
        timestmap = str(time.strftime("%d-%m-%Y--%H.%M.%S"))
        self.client_machine = Machine(self.commcell.commserv_name, self.commcell)
        self.client_machine.set_encoding_type('utf8')
        self.bkp_content_temp_folder = "c:\\auto_tc_" + str(self.id) + "_bkp_conent"
        self.subclient_content_path = self.bkp_content_temp_folder + "\\auto_" + timestmap
        file_contents = "This is test file - " + timestmap
        file_name = "automation_test_data-" +timestmap
        file_path = self.client_machine.join_path(self.subclient_content_path, file_name)
        self.client_machine.create_directory(self.bkp_content_temp_folder, force_create=True)
        self.client_machine.create_directory(self.subclient_content_path, force_create=True)
        self.client_machine.create_file(file_path, file_contents)
        self.log.info("Generated data for backup")

    def create_backupset(self):
        """Create backupset"""
        # backup set will be created with the name: backupset_54384
        self._backupset_name = "backupset_" + str(self.id)
        self.log.info("Creating backupset [%s]", self._backupset_name)
        default_client_obj = self.commcell.clients.get(self.commcell.commserv_name)
        self._agent = default_client_obj.agents.get("file system")
        if self._agent.backupsets.has_backupset(self._backupset_name):
            self._agent.backupsets.delete(self._backupset_name)
        self._agent.backupsets.add(self._backupset_name)
        self._backupset = self._agent.backupsets.get(self._backupset_name)
        self.log.info("Backupset is created!")

    def create_subclients(self):
        """Create subclient"""
        # subclient will be created with the name: subclient_54384
        self._subclient_name = "subclient" + str(self.id)
        self.log.info("Creating subclient [%s]", self._subclient_name)
        self._subclient = self._backupset.subclients.add(self._subclient_name,
                                                         self.tcinputs["storage_policy_name"])
        self.log.info("setting subclient content to:%s ", self.subclient_content_path)
        self._subclient.content = [self.subclient_content_path]
        self.log.info("Subclient is created!")

    @test_step
    def run_backup_job(self):
        """Run backup job"""
        job_obj = self._subclient.backup("FULL")
        job_obj.wait_for_completion()

    @test_step
    def run_restore_job(self):
        """Run restore job"""
        restore_job_obj = self._subclient.restore_in_place(paths=[self.subclient_content_path])
        restore_job_obj.wait_for_completion()

    def init_tc(self):
        """
        Create data, backupset, subclient
        """
        try:
            self.generate_data_for_backup()
            self.create_backupset()
            self.create_subclients()
        except Exception as exep:
            raise CVTestCaseInitFailure("Test case is failed during initialization [%s]"
                                        % exep)

    def create_report_save_path_directory(self):
        """Create directory where report is saved"""
        self.log.info("create directory[%s] before running the reportwhere report should"
                      " be saved in machine[%s]", self.report_saved_path, self.commcell.commserv_name)
        self.client_machine.create_directory(self.report_saved_path, force_create=True)

    @test_step
    def validate_restore_report(self):
        """Run the restore report and verify it has backup content path in it"""
        self.create_report_save_path_directory()
        self.log.info("Run browse and restore report")
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?><TMMsg_CreateTaskReq><processinginstructioninfo><user _type_="13" userId="1" userName="admin"/><locale _type_="66" localeId="0"/><formatFlags continueOnError="0" elementBased="0" filterUnInitializedFields="0" formatted="0" ignoreUnknownTags="1" skipIdToNameConversion="1" skipNameToIdConversion="0"/></processinginstructioninfo><taskInfo><task initiatedFrom="1" ownerId="1" ownerName="admin" sequenceNumber="0" taskType="1"><taskFlags disabled="0"/></task><appGroup/><subTasks subTaskOperation="1"><subTask operationType="4004" subTaskType="1"/><options><adminOpts><reportOption allowDynamicContent="0" failedFilesThreshold="0" includeClientGroup="1" jobOption="0" showJobsWithFailedFailesOnly="0"><commonOpt dateFormat="mm/dd/yyyy" onCS="0" overrideDateTimeFormat="0" reportCustomName="" reportType="7720" summaryOnly="0" timeFormat="hh:mm:ss am/pm"><outputFormat isNetworkDrive="0" outputType="2" textDelimiter="&#x9; "/><savedTo ftpUploadLocation="Commvault Reports" isNetworkDrive="0" locationURL="%s" uploadAsCabinetFile="0"><reportSavedToClient _type_="3" clientId="2" clientName="%s" hostName=""/><ftpDetails/></savedTo><locale LCID="3081" _type_="66" displayString="English-Australia" locale="en-au" localeId="0" localeName="en"/></commonOpt><computerSelectionList includeAll="1"/><agentList _type_="4"><flags include="1"/></agentList><mediaAgentList _type_="11"><flags include="1"/></mediaAgentList><storagePolicyCopyList _type_="17" allCopies="1"/><timeRangeOption TimeZoneID="42" _type_="54" toTime="86400" type="13"/><jobSummaryReport filterOnSubClientDesc="0" groupBy="1" subClientDescription=""><jobOptions isCommserveTimeZone="1" isThroughputInMB="0" numberOfMostFreqErrors="0" sizeUnit="0"><jobStatus all="1"/><increaseInDataSize selected="0" value="10"/><decreaseInDataSize selected="0" value="10"/><retentionType basicRetention="0" extendedRetention="0" manualRetention="0" retentionAll="0"/></jobOptions><rptSelections IncludeMediaDeletedJobs="0" associatedEvent="0" description="1" failedObjects="1" failureReason="1" includeClientDescription="0" includePerformanceJobsOnly="0" initializingUser="0" jobAttempts="0" numberOfHours="0" restoredObjects="1" storagePolicy="0"/></jobSummaryReport></reportOption></adminOpts><commonOpts/></options></subTasks></taskInfo></TMMsg_CreateTaskReq>""" % (self.report_saved_path, self.commcell.commserv_name)
        response = self.commcell.execute_qcommand("qoperation execute", xml)
        time.sleep(10)

        self.log.info("Waiting for report job to complete")
        job_id = response.json()['jobIds'][0]
        job_obj = self.commcell.job_controller.get(job_id)
        job_obj.wait_for_completion()
        self.log.info("Get all the files(Reports) from directory[%s] to read the report",
                      self.report_saved_path)
        file_list = self.client_machine.get_files_in_path(self.report_saved_path)
        if not file_list:
            raise CVTestStepFailure("Report is not found in location")
        self.log.info("Report found:%s", str(file_list))

        # Read the report file, and verify backed up file exists in report
        report_file_path = os.path.join(self.report_saved_path, file_list[0])
        report_file_contents = self.client_machine.read_file(report_file_path)
        if self.subclient_content_path in report_file_contents:
            self.log.info("File path exists in browse and restore report!")
            return
        raise CVTestStepFailure("subclient content path[%s] is not present restore "
                                "report[%s] content" % (self.subclient_content_path, file_list))

    def cleanup_configuration(self):
        """Delete backup set, backup content, report saved directory"""
        self._agent.backupsets.delete(self._backupset_name)
        self.client_machine.remove_directory(self.report_saved_path)
        self.client_machine.remove_directory(self.bkp_content_temp_folder)

    @test_step
    def verify_protected_files_exisits_in_report(self):
        """Enable protected objects option in selection tab and verify files are listed in report.
        """
        #  Generate the backup job summary report
        self.create_report_save_path_directory()
        reports = self.commcell.reports
        reports.backup_job_summary.select_local_drive(self.report_saved_path)
        reports.backup_job_summary.select_protected_objects()
        reports.backup_job_summary.set_report_custom_name(self.report_custom_name)
        job_id = reports.backup_job_summary.run_report()

        #  Wait to report job to complete.
        job_obj = self.commcell.job_controller.get(job_id)
        job_obj.wait_for_completion()
        self.log.info("Get all the files(Reports) from directory[%s] to read the report",
                      self.report_saved_path)
        file_list = self.client_machine.get_files_in_path(self.report_saved_path)

        # Verify custom name is set to generate report
        report_found = False
        for each_file in file_list:
            if self.report_custom_name in each_file:
                report_found = True
                break
        if not report_found:
            raise CVTestStepFailure("Report file [%s] with custom name is found")
        self.log.info("Report found:%s", str(file_list))

        # open the file and verify the protected file is present in report.
        report_file_path = os.path.join(self.report_saved_path, file_list[0])
        report_file_contents = self.client_machine.read_file(report_file_path)
        if self.subclient_content_path in report_file_contents:
            self.log.info("Protected files are present in report %s" % report_file_path)
            return
        raise CVTestStepFailure("Protected file path [%s] is not present report[%s] content"
                                % (self.subclient_content_path, file_list))

    def run(self):
        try:
            self.init_tc()
            self.run_backup_job()
            self.verify_protected_files_exisits_in_report()
            self.run_restore_job()
            self.validate_restore_report()
            self.cleanup_configuration()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
