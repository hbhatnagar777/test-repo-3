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
        Scenario 1: verify that prescan with all modifying/removing  operations will be'
                    'picked as modified files and trigger a backup googledrive Path from googledrive moniker.
        Pre requirement : googledrive should be configured and googledrive path should be given in the inputs.

            1: Adding subclient with googledrive moniker along with plan monikers.
            2: Modify files and validate if it triggers a backup
            3: Renaming files and validate if it triggers a backup
            4: Removing folder and validate if it triggers a backup

    '''

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "googledrive moniker prescan validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.DATAPROTECTION
        self.tcinputs = {
            "googledrivePath": None
        }
        self.runid = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None
        self.googledrivePath = None

    def setup(self):
        """Setup function of this test case"""
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        googledrivePath = self.tcinputs['googledrivePath']

        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self, False)
            self.log.info("Started executing %s testcase", str(self.id))
            machine = Machine(client_name, self._commcell)
            googledrivePath = googledrivePath + self.slash_format + "Inc1"

            from AutomationUtils.config import get_config
            laptop_config = get_config().Laptop
            client_data = laptop_config._asdict()['UserCentricClient']._asdict()
            client = client_data[machine.os_info].ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)


            subclient_name = "default"
            test_path = self._utility.create_directory(machine)
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            if self.slash_format in '/':
                subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', '/%GoogleDrive%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
            else:
                subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', '\%GoogleDrive%']
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

            self._utility.create_directory(machine, googledrivePath)
            if self.slash_format in '/':
                machine.generate_test_data(googledrivePath, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup wheel")
            else:
                machine.generate_test_data(googledrivePath, hlinks=False, slinks=False, sparse=False)


            log.info(" verify if a backup triggered")

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
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info('Job triggered for new subclient content case')

            log.info("modifying files case started")
            machine.modify_test_data(googledrivePath, modify=True)
            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                log.info('Job triggered for adding new content case')
            else:
                raise Exception("automatic job didnt trigger in scheduled time")
            self._utility.sleep_time(20, "Wait for index play back to finish")
            log.info("Run a restore of the incremental backup data and verify correct data is restored.")

            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=googledrivePath,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("Dont add/modify any data to check if backup is not triggered or not")

            log.info("Verify whether job triggered due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                if previous_job.num_of_files_transferred > 0:
                    raise Exception(" automatic job improperly triggered in scheduled time")

            log.info('Job didnt trigger for no modified data')


            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            machine.remove_directory(googledrivePath)
            machine.remove_directory(test_path)
            machine.remove_directory(tmp_path)
            self._schedule_creator.cleanup_schedules()
