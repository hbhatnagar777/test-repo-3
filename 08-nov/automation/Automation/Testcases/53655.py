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
from Laptop.laptophelper import LaptopHelper


class TestCase(CVTestCase):
    '''
    Scenario 1: verify that prescan operation will be trigger once newsubclient content added or new files added on disk
    by prescan process with subclient content list:%Documents%'%Desktop%'%Pictures%' %Office%'
        1: Adding subclient with monikers same as in plan
        2: Add new content from under Documents path and validate if backup triggered
        4: Content change: Add absolute path content and validate if backup triggered
        5. Add content office moniker and vaildate backup triggered
        6. Without any changes validate if backup didnt trigger any backup with same content.
        '''
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSevents/Folderwatcher validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self._entities = None
        self.runid = None
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

            from AutomationUtils.config import get_config
            laptop_config = get_config().Laptop
            client_data = laptop_config._asdict()['UserCentricClient']._asdict()
            client = client_data[machine.os_info].ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            subclient_name = "default"
            backupset_name = "defaultbackupset"
            FSHelper.populate_tc_inputs(self, False)
            test_path = self._utility.create_directory(machine)
            scan_type = ScanType.OPTIMIZED
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            if self.slash_format in '/':
                subclient_content = ['/%Documents%', '/%Desktop%', '/%Pictures%', '/%Music%', '/%MigrationAssistant%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
            else:
                subclient_content = [r'\%Documents%', r'\%Desktop%', r'\%Pictures%', r'\%Music%', r'\%MigrationAssistant%']
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
            self.log.info("Creating directories for the paths which will be added as content")
            abs_path = test_path + str(self.slash_format) + "abscontent"
            self._utility.create_directory(machine, abs_path)
            if self.slash_format in '/':
                documentspath = "/Users/cvadmin/Documents/Inc1"
                data_path = "/"
                library_path = "/Users/cvadmin/Library/Inc1"
                machine.generate_test_data(abs_path, hlinks = False, slinks = False, sparse = False,
                                           options = "-testuser root -testgroup wheel" )
            else:
                documentspath = "C:\\Users\\admin\\Documents\\Inc1"
                data_path = "C:\\"
                library_path = "C:\\Users\\admin\\Appdata\\Roaming\\Inc1"
                machine.generate_test_data(abs_path, hlinks = False, slinks = False, sparse = False)

            content_library_path1 = test_path + str(self.slash_format) + "Officecontent"
            self._utility.create_directory(machine, content_library_path1)
            file_path = content_library_path1 + str(self.slash_format) +"file1.txt"
            machine.create_file(file_path, "test")

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
            previous_job = _sch_helper_obj.automatic_schedule_wait()
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info("Add Incr data under documents path.")

            log.info("Adding data under Documents path: %s", str(documentspath))
            self._utility.create_directory(machine, documentspath)
            if self.slash_format in '/':
                machine.generate_test_data(documentspath, hlinks = False, slinks = False, sparse = False,
                                           options = "-testuser root -testgroup wheel" )
            else:
                machine.generate_test_data(documentspath, hlinks = False, slinks = False, sparse = False)

            # wait for for journals to get flushed
            if scan_type.value != ScanType.RECURSIVE.value:
                log.info("Waiting for journals to get flushed")
            log.info("Verify if a backup triggered")
            previous_job = LaptopHelper.verify_automatic_schedule_restore(self, documentspath, tmp_path, subclient_obj,
                                                                          machine,client_name, sch_obj,
                                                                          previous_job=previous_job, add_data=False,
                                                                          subclient_content=None, validate=True,
                                                                          cleanup=True)

            log.info("Add new content as absolute path")

            subclient_content.append(abs_path)
            content = [abs_path]

            subclient_obj.content = subclient_content
            log.info('Verify whether job triggered due to content change or not')
            previous_job = LaptopHelper.verify_automatic_schedule_restore(self, abs_path, tmp_path, subclient_obj,
                                                                  machine,client_name, sch_obj,
                                                                  previous_job=previous_job, newcontent=True, add_data=False,
                                                                  subclient_content=None, validate=True,
                                                                  cleanup=True)
            log.info("Add new content moniker 'Office'  as content")
            content_library = "/%Office%"
            subclient_content.append(content_library)
            content = [content_library]
            subclient_obj.content = subclient_content
            log.info("Verify whether job triggered due to content change or not")
            previous_job = LaptopHelper.verify_automatic_schedule_restore(self, content_library_path1, tmp_path, subclient_obj,
                                                                  machine,client_name, sch_obj,
                                                                  previous_job=previous_job, newcontent=True, add_data=False,
                                                                  subclient_content=None, validate=True,
                                                                  cleanup=True)

            log.info("Add some test data under content library moniker for Office as some text and doc files")
            content_library_path2 = test_path + str(self.slash_format) + "Oficecontent" + str(self.slash_format) + "dr2"
            self._utility.create_directory(machine, content_library_path2)
            file_path = content_library_path2 + str(self.slash_format) +"file2.txt"
            machine.create_file(file_path, "test")

            log.info('Verify whether job triggered')
            previous_job = LaptopHelper.verify_automatic_schedule_restore(self, content_library_path2, tmp_path, subclient_obj,
                                                                  machine,client_name, sch_obj,
                                                                  previous_job=previous_job, add_data=False,
                                                                  subclient_content=None, validate=True,
                                                                  cleanup=True)

            log.info('Add test/doc file under Library and check whether it is not triggering backup')
            self._utility.create_directory(machine, library_path)
            libraryfile_path = library_path + str(self.slash_format) +"file3.txt"
            machine.create_file(libraryfile_path, "test")
            log.info('Verify whether job is not triggered for text file in Library path')
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                if previous_job.num_of_files_transferred > 0:
                    log.info('run restore to check whether the text file in library path is backedup or not')
                    _ = CommonUtils(self).subclient_restore_from_job(
                        data_path,
                        tmp_path=tmp_path,
                        job=previous_job,
                        cleanup=True,
                        subclient=subclient_obj,
                        client=client_name,
                        validate=False)
                    data_path_leaf = ntpath.basename(library_path)
                    destination_path = machine.os_sep.join([tmp_path, data_path_leaf])
                    source_list = machine.get_meta_list(library_path)
                    source_list = set(source_list) - {'\n'}
                    destination_list = machine.get_meta_list(destination_path)
                    destination_list = set(destination_list) - {'\n'}
                    compare_list = list(set(source_list) - set(destination_list))
                    if set(compare_list) == source_list:
                        log.info("Job didnt backup the changed Library test file content ")
                    else:
                        raise Exception(" There is a improper data under Library getting backedup")

                else:
                    log.info ("backup triggered for Library path modification and didnt backup anything")
            else:
                log.info(" automatic job didnt trigger correctly in scheduled time")

            log.info("Verifying whether all the moniker files are not getting backedup without any changes")
            log.info("Verify whether job triggered due to content change or not")
            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)
            if previous_job:
                if previous_job.num_of_files_transferred > 0:
                    log.info("Run a restore if no change in backedup")
                    _ = CommonUtils(self).subclient_restore_from_job(
                        data_path,
                        tmp_path=tmp_path,
                        job=previous_job,
                        cleanup=True,
                        subclient=subclient_obj,
                        client=client_name,
                        validate=False)
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
            machine.remove_directory(library_path)
