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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Laptop.laptophelper import LaptopHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental,Differential
        This test case does the following
        Step 1 : Get default subclient
        Step 2 : Add incr data for the current run.
        Step 3 : Run an incr backup for the subclient
                 and verify it completes without failures.
        Step 4 : Run a restore of the full backup data
                 and verify correct data is restored.
        Step 5 : Run a synthfull job
        Step 6 : Add new data for the incremental -
                 we are going to rename set of files in sc.
                 This is to verify if trueup ran wiht phase 1
        Step 7: Add new data and run incremental to check if trueup phase2 ran
        Step 8: Add new data na drun incremental to check if trueup doesnt run again
        Step 9: Run restore and check if valid files are restored
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify Trueup on Laptop"
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
        }
        self.test_path = None
        self.slash_format = None
        self.runid = None

    def setup(self):
        """Setup function of this test case"""
        self._entities = CVEntities(self)
        self._utility = OptionsSelector(self._commcell)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        machine = self._utility.get_machine_object(client_name)

        try:
            # Initialize test case inputs
            if machine.os_info in 'UNIX':
                self.slash_format = '/'
            else:
                self.slash_format = '\\'
            client_obj = self.client
            subclient_obj = CommonUtils(self.commcell).get_subclient(client_name)
            self._backupset = CommonUtils(self.commcell).get_backupset(client_name)
            test_path = self._utility.create_directory(machine)
            tmp_path = (
                test_path
                +str(self.slash_format)
                +'cvauto_tmp'
                +str(self.slash_format)
                +str(self.runid)
                )
            laptop_helper = LaptopHelper(self)

            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")

            if machine.os_info in 'UNIX':
                subclient_content = ['/%Documents%', '/%Desktop%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
                desktop_path = "/Users/cvadmin/Desktop/Inc"
            else:
                subclient_content = [r'\%Documents%', r'\%Desktop%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%"]
                desktop_path = "C:\\Users\\admin\\desktop\\Inc"
            machine.create_directory(desktop_path)

            subclient_obj.content = subclient_content
            subclient_obj.filter_content = filter_content

            log.info('Step 2Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed".format(job_obj.job_id))

            log.info("Step3,  Run Synthfull job.")
            job_obj = subclient_obj.backup("Synthetic_full")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("SynthFUll Backup job {0} completed.".format(job_obj.job_id))

            log.info("Adding data under path: %s", desktop_path)

            if machine.os_info in 'UNIX':
                machine.generate_test_data(desktop_path, hlinks=False, slinks=False, sparse=False,
                                           options="-testuser root -testgroup admin")
            else:
                machine.generate_test_data(desktop_path, hlinks=False, slinks=False, sparse=False)
            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed.".format(job_obj.job_id))

            log.info("Checking trueup here also")
            log.info("validate Trueup function called.")
            retval = laptop_helper.validate_trueup(machine, client_obj, subclient_obj, 1, job_obj)
            if retval:
                log.info("True up ran for Incremental job as expected.")
            else:
                log.info("True up did not run for Full job as expected.")
                raise Exception("Failing test case")

            machine.modify_test_data(desktop_path, modify=True)
            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed.".format(job_obj.job_id))

            log.info("Checking trueup here also")
            log.info("validate Trueup function called.")
            retval = laptop_helper.validate_trueup(machine, client_obj, subclient_obj, 2, job_obj)
            if retval:
                log.info("True up ran for Incr phas2  as expected.")
            else:
                log.info("True up did not run for Full job as expected.")
                raise Exception("Failing test case")

            machine.modify_test_data(desktop_path, modify=True)
            log.info('Run an incremental job')
            job_obj = subclient_obj.backup("Incremental")
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}".format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed.".format(job_obj.job_id))
            _ = CommonUtils(self).subclient_restore_from_job(
                data_path=desktop_path,
                tmp_path=tmp_path,
                job=job_obj,
                cleanup=True,
                subclient=subclient_obj,
                client=client_name)
            str_query = ("select count(distinct(phase)) from JMBkpAtmptStats"
                         " with (NOLOCK) where status=1 and jobID={0}".format(job_obj.job_id))
            cur = self._utility.exec_commserv_query(str_query)
            # if count is one it means only one phase was ran else multiple phases were ran
            if cur[0][0] == '4':
                log.info("PostOp phase again ran")
                raise Exception("PostOp phase again ran")
            elif cur[0][0] == '3':
                log.info("Phases ran as expected")
            else:
                log.info("phases not ran expected, please check logs")
                raise Exception("phases not ran expected, please check logs")

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            machine.remove_directory(desktop_path)
            machine.remove_directory(test_path)
