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
    '''feature description
       To verify whether edgedrive moniker content will backup the edgedrive path'''
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VErification of EdgeDrive moniker backup"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.helper = None
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
            FSHelper.populate_tc_inputs(self, False)
            entities = CVEntities(self)
            response_map = entities.create({
                'target':{'force': False},
                'backupset': {'name': "defaultbackupset"},
                'subclient': {'name': "default"}
            })
            subclient_content = response_map["subclient"]["content"][0]
            subclient_obj = response_map['subclient']['object']
            subclient_name = "default"
            FSHelper.populate_tc_inputs(self, False)
            test_path = self._utility.create_directory(machine)
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            log.info("Step2.1,Create subclient if it doesn't exist.")
            subclient_content = ['%Documents%', '%Desktop%']
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
                edgedrivepath = "/Users/cvadmin/EdgeDrive"
                subclient_content.append("/%EDGEDRIVE%")
            else:
                edgedrivepath = "C:\\Users\\admin\\Edge Drive"
                subclient_content.append("\%EDGEDRIVE%")
            edgedrivepath = edgedrivepath + self.slash_format + "Inc"
            log.info('Creating schedule if it doesnt exists')
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
            log.info("Step2.2,  Add new content as edge drive moniker")

            if self.slash_format in '/':
                machine.generate_test_data(edgedrivepath, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup wheel")
            else:
                machine.generate_test_data(edgedrivepath, hlinks=False, slinks=False, sparse=False)
            self.log.info("Setting subclient content as %s", subclient_content)
            subclient_obj.content = subclient_content

            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job, newcontent=True)
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info(
                "Step2.3,  Run a restore of the edegedrive moniker backup data"
                " and verify correct data is restored."
                )
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=edgedrivepath,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)
            log.info("Step2.4,  Add some test data under edge drive path")
            edgedrivepath2 = edgedrivepath + self.slash_format + "Inc1"
            if self.slash_format in '/':
                machine.generate_test_data(edgedrivepath2, dirs=1, files=1, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup wheel")
            else:
                machine.generate_test_data(edgedrivepath2, dirs=1, files=1, hlinks=False, slinks=False, sparse=False)

            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info("Step2.5,  Run a restore of the edge drive backup data and verify correct data is restored.")
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=edgedrivepath2,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            machine.remove_directory(tmp_path)
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self._schedule_creator.cleanup_schedules()
            machine.remove_directory(edgedrivepath)
