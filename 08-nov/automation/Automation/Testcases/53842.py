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
    '''Scenario 1: verify that prescan operation will be trigger once newsubclient content added or new files added on
    disk by prescan process with subclient content list:%Documents%'%Desktop%'%Pictures%' %Office%'
        1: Adding subclient with monikers same as in plan
        2: Add new content from under Documents path and validate if backup triggered
        4: Content change: Add absolute path content and validate if backup triggered
        5. Add content office moniker and vaildate backup triggered
        6. Without any changes validate if backup didnt trigger any backup with same content.'''
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Prescan verification for Content Monikers like Desktop,Documents,Office"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.runid = None
        self.helper = None
        self._entities = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None
        self.storage_policy = None

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
            test_path = self._utility.create_directory(machine)
            helper = self.helper
            backupset_name = "backupset_" + self.id
            helper.create_backupset(backupset_name, True)
            scan_type = ScanType.OPTIMIZED
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            log.info("Step2.1,Create subclient if it doesn't exist.")
            subclient_name = ("subclient_"+ self.id + "_optimized")
            subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', '%Music%']
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
            else:
                documentspath = "C:\\Users\\admin\\Documents\\Inc1"
            log.info("Adding subclient with content")
            helper.create_subclient(name=subclient_name, storage_policy=self.storage_policy,
                                    content=subclient_content, scan_type=scan_type)
            log.info('Creating schedule if it doesnt exists')
            self._backupset = self._agent.backupsets.get(backupset_name)
            subclient_obj = self._backupset.subclients.get(subclient_name)
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

            log.info("Step2.2, Add Incr data under documents path.")

            log.info("Adding data under Documents path: %s", str(documentspath))
            machine.create_directory(documentspath)
            if self.slash_format in '/':
                helper.add_new_data_incr(documentspath, str(self.slash_format), scan_type, hlinks=False, slinks=False,
                                         sparse=False, options = '-testuser root -testgroup wheel')
            else:
                helper.add_new_data_incr(documentspath, str(self.slash_format), scan_type, hlinks=False, slinks=False,
                                         sparse=False)
            # wait for for journals to get flushed
            if scan_type.value != ScanType.RECURSIVE.value:
                log.info("Waiting for journals to get flushed")
            log.info("Step2.3 verify if a backup triggered")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            self._utility.sleep_time(20, "Wait for index play back to finish")
            log.info("Step2.4,  Run a restore of the incr backup data and verify correct data is restored.")

            CommonUtils(self).subclient_restore_from_job(
                data_path=documentspath,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("Step2.6,  Add new content as absolute path")
            abs_path = test_path + str(self.slash_format) + "abscontent"
            subclient_content.append(abs_path)
            machine.create_directory(abs_path)
            content = [abs_path]
            if self.slash_format in '/':
                helper.add_new_data_incr(abs_path, str(self.slash_format), scan_type, hlinks=False, slinks=False,
                                         sparse=False, options = '-testuser root -testgroup wheel')
            else:
                helper.add_new_data_incr(abs_path, str(self.slash_format), scan_type, hlinks=False, slinks=False,
                                         sparse=False)
            helper.update_subclient(content=content)
            log.info('Verify whether job triggered due to content change or not')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info(
                "Step2.8,  Run a restore of the incremental backup data"
                " and verify correct data is restored."
                )
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=abs_path,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)
            log.info("Step2.7,  Add new content moniker 'Office'  as content")
            content_library = "/%Office%"
            content_library_path1 = test_path + str(self.slash_format) + "Officecontent"
            subclient_content.append(content_library)
            machine.create_directory(content_library_path1)
            content = [content_library]
            file_path = content_library_path1 + str(self.slash_format) +"file1.txt"
            machine.create_file(file_path, "test")
            helper.update_subclient(content=content)
            log.info("Verify whether job triggered"
                     " due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")
            log.info('Wait for index play back to finish')
            self._utility.sleep_time(20, "Wait for index play back to finish")
            log.info("Run a restore of the incremental backup data, verify correct data is restored")
            CommonUtils(self).subclient_restore_from_job(
                data_path=content_library_path1, tmp_path=tmp_path,
                job=previous_job,
                cleanup=True, subclient=subclient_obj,
                client=client_name, validate=True)
            log.info("Step2.8,  Add some test data under content"
                     "library moniker for Office as some text and doc files")
            content_library_path2 = test_path + str(self.slash_format) + "Oficecontent" + str(self.slash_format) + "dr2"
            machine.create_directory(content_library_path2)
            file_path = content_library_path2 + str(self.slash_format) +"file2.txt"
            machine.create_file(file_path, "test")

            log.info('Verify whether job triggered')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info("Run a restore of the incremental backup data,verify correct data is restored.")
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=content_library_path2,
                tmp_path=tmp_path,
                job=previous_job,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name,
                validate=True)

            log.info("Verifying whether all the moniker files are not getting backedup without any changes")
            log.info("Verify whether job triggered due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if self.slash_format in '/':
                data_path = "/"
            else:
                data_path = "C:\\"
            if previous_job:
                log.info(
                    "Step2.8,  Run a restore if no change in backup data"
                    " and verify whether already backedup data is backedup or not."
                    )
                _ = CommonUtils(self).subclient_restore_from_job(
                    data_path,
                    tmp_path=tmp_path,
                    job=previous_job,
                    cleanup=True,
                    subclient=subclient_obj,
                    client=client_name,
                    validate=False)
                #machine_obj = self._utility.get_machine_object(client_name)
                data_path_leaf = ntpath.basename(content_library_path2)
                destination_path = machine.os_sep.join([tmp_path, data_path_leaf])
                source_list = machine.get_meta_list(content_library_path2)
                source_list = set(source_list) - {'\n'}
                destination_list = machine.get_meta_list(destination_path)
                destination_list = set(destination_list) - {'\n'}
                compare_list = list(set(source_list) - set(destination_list))
                if set(compare_list) == source_list:
                    log.info("Job didnt backup the changed office content again")
                else:
                    raise Exception(" There is a duplicate backup happened")
            else:
                log.info('Job didnt trigger without any changes successfully')

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            machine.remove_directory(tmp_path)
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:

            self._schedule_creator.cleanup_schedules()
            machine.remove_directory(documentspath)
            machine.remove_directory(abs_path)
            machine.remove_directory(content_library_path1)
            machine.remove_directory(content_library_path2)
