# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
import ntpath
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from FileSystem.FSUtils.fshelper import ScanType, FSHelper
from Server.Scheduler import schedulerhelper


class TestCase(CVTestCase):
    '''feature description
    Scenario 1: verify that prescan operation will be trigger once newsubclient content added or new files added on disk
    by prescan process with subclient content list:%Documents%'%Desktop%'%Pictures%' %Office%'
    scenario 2: Adding/removing filters validation'''
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSevents/Folderwatcher filters validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.runid = None
        self._entities = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None

    def setup(self):
        """Setup function of this test case"""
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        machine = Machine(client_name, self._commcell)
        try:
            # Initialize test case inputs

            self.log.info("Started executing %s testcase", str(self.id))
            #client_machine = Machine(self.client, self._commcell)
            entities = CVEntities(self)
            response_map = entities.create({
                'target':{'force': False},
                'backupset': {'name': "defaultbackupset"},
                'subclient': {'name': "default"},
                'disklibrary': {'name': "fsevents_lib"},
                'storagepolicy': {'name': 'fsevents_sp',
                                  'library': 'fsevents_lib',
                                  'mediaagent': self.subclient.storage_ma}
            })
            subclient_content = response_map["subclient"]["content"][0]
            subclient_obj = response_map['subclient']['object']
            subclient_name = "default"
            backupset_name = "defaultbackupset"
            FSHelper.populate_tc_inputs(self, False)
            test_path = self._utility.create_directory(machine)
            scan_type = ScanType.OPTIMIZED
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            log.info( " Checking if the folderwatcher regkey is present or not")
            _ = self._utility.check_reg_key(machine, "FileSystemAgent", "nUseFolderWatcherPreScan", "1", True)
            subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', '%Music%']
            subclient_obj.content = subclient_content
            subclient_obj.filter_content = [""]
            tmp_path = (
                test_path
                + str(self.slash_format)
                + 'cvauto_tmp'
                + str(self.slash_format)
                + subclient_name
                + str(self.slash_format)
                + str(self.runid)
                )
            if self.slash_format in '/':
                documentspath = "/Users/cvadmin/Documents/"
            else:
                documentspath = "C:\\Users\\admin\\Documents\\"
            log.info('Creating schedule if it doesnt exists')
            self._backupset = response_map['backupset']['object']
            sch_obj = self._schedule_creator.create_schedule(
                'subclient_backup',
                schedule_pattern={
                    'freq_type': 'automatic',
                    'min_interval_hours': 0,
                    'min_interval_minutes': 2

                },
                subclient=subclient_obj,
                backup_type="Incremental",
                wait=False)
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            log.info("validating if backup triggered for subclient")
            previous_job = _sch_helper_obj.automatic_schedule_wait()
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')
            log.info("Adding data for filter content case")
            filter_data_content = [(documentspath +"test1"), (documentspath + "test2")]
            for contentpath in filter_data_content:
                log.info ("Adding data udner %s", contentpath )
                if self.slash_format in '/':
                    machine.generate_test_data(documentspath, hlinks = False, slinks = False, sparse = False,
                                           options = "-testuser root -testgroup wheel" )
                else:
                    machine.generate_test_data(documentspath, hlinks = False, slinks = False, sparse = False)
            filter_content = [documentspath + "test2"]
            log.info( "Adding filter content %s to the subclient", str(filter_content))
            subclient_obj.filter_content = filter_content

            log.info("Verify if a backup triggered")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')
            self._utility.sleep_time(20, "Wait for index play back to finish")
            log.info("Step2.4,  Run a restore of the incr backup data and verify correct data is restored.")

            CommonUtils(self).subclient_restore_from_job(
                data_path=filter_data_content[0],
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("adding/modifying data for filter content case")
            for contentpath in filter_data_content:
                log.info("Modifying data under %s", str(contentpath))
                machine.modify_test_data(contentpath, modify=True)

            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')
            log.info("Run a restore of the incremental backup dataand verify correct data is restored.")
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=filter_data_content[0],
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)
            log.info("Add incremental data for new wild card filter case")
            wildfilter_content = ["txt", "log"]
            machine.create_directory((filter_data_content[0] + self.slash_format + wildfilter_content[0]))
            machine.create_directory((filter_data_content[0] + self.slash_format + wildfilter_content[1]))
            for filecount in range(4):
                filepath = filter_data_content[0] + self.slash_format + wildfilter_content[0] + self.slash_format
                machine.create_file(filepath + "file" + str(filecount) + ".txt", "testdata")
            for filecount in range(4):
                filepath = filter_data_content[0] + self.slash_format + wildfilter_content[1] + self.slash_format
                machine.create_file(filepath + "file" + str(filecount) + ".log", "testdata")

            filter_content.append(filter_data_content[0] + self.slash_format + "*.log")
            log.info("Adding new wild card filter %s", (filter_data_content[0] + self.slash_format + "*.log"))
            subclient_obj.filter_content = filter_content
            log.info("Verify whether job triggered"
                     " due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')
            self._utility.sleep_time(20, "Wait for index play back to finish")
            log.info("Run a restore of the incremental backup dataand verify correct data is restored.")
            CommonUtils(self).subclient_restore_from_job(
                data_path=(filter_data_content[0] + self.slash_format + wildfilter_content[0]) , tmp_path=tmp_path,
                job=previous_job,
                cleanup=True, subclient=subclient_obj,
                client=client_name, validate=True)

            log.info("Add/Modify some test data for wild card filter case")
            for content_path in wildfilter_content:
                wild_filter_content = filter_data_content[0] + self.slash_format + content_path
                machine.modify_test_data(wild_filter_content, modify=True)

            log.info('Verify whether job triggered')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')

            log.info("Step2.8,  Run a restore of the incremental backup data and verify correct data is restored.")
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=(filter_data_content[0] + self.slash_format + wildfilter_content[0]),
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("Removing filter %s", filter_content[0])
            subclient_obj.filter_content = [filter_content[1]]
            log.info('Verify whether job triggered for removing filter case')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Job triggered for new subclient content case')

            log.info("Run a restore if removed filter content is backedup or not"
                )
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=filter_content[0],
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("No backup should trigger when no content or data is modified)")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                 raise Exception(" automatic job triggered without any changes")

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            machine.remove_directory(tmp_path)
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:

            self._schedule_creator.cleanup_schedules()
            machine.remove_directory(filter_data_content[0])
            machine.remove_directory(filter_data_content[1])

