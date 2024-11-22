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
from AutomationUtils.mailer import Mailer
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Scheduler import schedulerhelper
from Laptop.laptophelper import LaptopHelper


class TestCase(CVTestCase):
    '''
        Scenario 1: verify the PST file evaluation in FileScan'
                    'FileScan should pick the PST file which has the actual content change in it.
        Pre requirement: 1. pst file path that is given in the answer file should be under documents path and opened
                            in Outlook.'
                        2. Configure a rule that email with subject 'test pstevaluation' goes to folder in pst file'

            1: Adding subclient with Desktop,Documents moniker
            2: Modify pst file by sending email to the email id is specified in receiver in config file.
            3: Vaildate if backup triggered.
            4: Validate if no backup triggered when no changes made to pst file

    '''

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PST evaluation validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.DATAPROTECTION
        self.tcinputs = {
            "pstfilepath": None
        }
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
        pstfilepath = self.tcinputs['pstfilepath']
        receiver = self.tcinputs['receiver']
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self, False)
            self.log.info("Started executing %s testcase", str(self.id))
            machine = Machine(client_name, self._commcell)
            from AutomationUtils.config import get_config
            client = get_config().Laptop.UserCentricClient.ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            subclient_name = "default"
            test_path = self._utility.create_directory(machine)
            pstfilename = pstfilepath.split(self.slash_format)[-1]
            pstfolder = pstfilepath.replace(pstfilename, '')
            pstfolder = pstfolder.rstrip(self.slash_format)
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', pstfolder]
            subclient_obj.content = subclient_content
            subclient_obj.filter_content = ['\%Temporary Files (Windows)%', "*.drivedownload"]
            tmp_path = (
                test_path
                + str(self.slash_format)
                + 'cvauto_tmp'
                + str(self.slash_format)
                + subclient_name
                + str(self.slash_format)
                + str(self.runid)
                )

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
            if not previous_job:
                raise Exception(" automatic job didnt trigger in scheduled time")

            log.info('Job triggered for new subclient content case')

            log.info('Send email in such a way that , it goes to the pst file that is opened in outlook file')
            log.info('Sending email with subject Test PST evaluation')

            mail = Mailer({'receiver':receiver}, commcell_object=self.commcell)
            mail.mail("Test PST Evaluation", "This is a test email")

            log.info('Verify whether backup triggered for the pst file modification')
            previous_job = LaptopHelper.verify_automatic_schedule_restore(self, pstfolder, tmp_path, subclient_obj,
                                                                          machine,client_name, sch_obj,
                                                                          previous_job=previous_job, add_data=False,
                                                                          subclient_content=None, validate=False,
                                                                          cleanup=False)

            compare_source = pstfolder
            data_path_leaf = ntpath.basename(pstfolder)
            dest_path = machine.os_sep.join([tmp_path, data_path_leaf + "_restore"])
            compare_destination = machine.os_sep.join([dest_path, data_path_leaf])

            log.info("""Executing backed up content validation:
                        Source: [{0}], and
                        Destination [{1}]""".format(compare_source, compare_destination))

            result, diff_output = machine.compare_meta_data(compare_source, compare_destination, dirtime=False)

            log.info("Performing meta data comparison on source and destination")
            if not result:
                log.error("Meta data comparison failed")
                log.error("Diff output: \n{0}".format(diff_output))
                raise Exception("Meta data comparison failed")
            log.info("Meta data comparison successful")

            log.info(" Verify no backup is triggered when no email is sent to the pst file which is in open state")

            previous_job = _sch_helper_obj.automatic_schedule_wait(previous_job)

            if previous_job:
                if previous_job.num_of_files_transferred > 0:
                    raise Exception(" automatic job improperly triggered in scheduled time")
            log.info("Job didnt backup pst file for no modified data")

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            machine.remove_directory(test_path)
            machine.remove_directory(tmp_path)
            self._schedule_creator.cleanup_schedules()
            machine.remove_directory(dest_path)

