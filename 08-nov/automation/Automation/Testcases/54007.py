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
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Scheduler import schedulerhelper


class TestCase(CVTestCase):
    '''
        Scenario 1: verify that prescan with folder watcher enabled , all modifying/removing  operations will be'
                    'picked as modified files and trigger a backup

            1: Adding subclient with monikers same as in plan
            2: Modify files and validate if it triggers a backup
            3: Renaming files and validate if it triggers a backup
            4: Removing folder and validate if it triggers a backup

    '''

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSevents/Folderwatcher validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.runid = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None

    def setup(self):
        """Setup function of this test case"""
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        machine = Machine(client_name, self._commcell)
        try:
            # Initialize test case inputs
            self.log.info("Started executing %s testcase", str(self.id))

            from AutomationUtils.config import get_config
            client = get_config().Laptop.UserCentricClient.ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            subclient_name = "default"
            FSHelper.populate_tc_inputs(self, False)
            test_path = self._utility.create_directory(machine)
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            log.info("Add subclient with monikers same as in plan")
            if self.slash_format in '/':
                subclient_content = ['%Documents%', '%Desktop%', '%Pictures%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
            else:
                subclient_content = ['%Documents%', '%Desktop%', '%Pictures%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%", r"C:\Program Files",
                                  r"C:\Program Files (x86)", r"C:\Windows", "*.drivedownload"]

            subclient_obj.content = subclient_content
            subclient_obj.filter_content = filter_content
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
                documentspath = "/Users/cvadmin/Documents/Inc1"
                documentspath2 = "/Users/cvadmin/Documents/Inc2"
            else:
                documentspath = "C:\\Users\\admin\\Documents\\Inc1"
            log.info("Adding subclient with content")

            self._utility.create_directory(machine, documentspath)
            if self.slash_format in '/':
                machine.generate_test_data(documentspath, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup wheel")
            else:
                machine.generate_test_data(documentspath, hlinks=False, slinks=False, sparse=False)
            log.info("Creating schedule if it doesn't exists")
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
            if previous_job:
                log.info('Job triggered for new subclient content case')
            else:
                raise Exception(" automatic job didnt trigger in scheduled time")

            machine.modify_test_data(documentspath, modify=True)
            log.info(" verify if a backup triggered")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                log.info("Job triggered for incremental data under documents path case")
            else:
                raise Exception(" automatic job didnt trigger in scheduled time")

            # wait for index playback to finish
            self._utility.sleep_time(20, "Wait for index play back to finish")

            log.info(" Run a restore of the incr backup data and verify correct data is restored.")
            CommonUtils(self).subclient_restore_from_job(
                data_path=documentspath,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("renaming files case started")
            machine.modify_test_data(documentspath, rename=True)
            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                log.info('Job triggered for adding new content case')
            else:
                raise Exception("automatic job didnt trigger in scheduled time")

            log.info("Run a restore of the incremental backup data and verify correct data is restored.")

            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=documentspath,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            machine.remove_directory(documentspath)

            log.info("Verify whether job triggered due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info('Job triggered for adding new content case')

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            machine.remove_directory(documentspath)
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            machine.remove_directory(test_path)
            machine.remove_directory(tmp_path)
            self._schedule_creator.cleanup_schedules()

