# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import time
import datetime as dt
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.windows_machine import WindowsMachine



class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Open Stack backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Meditech backup check for Quiesce and UnQuiesce"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""
    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            client_name = self.tcinputs.get('ClientName')
            #remoteclient = self.tcinputs.get('Remotemachine')
            agent = self.tcinputs.get('AgentName')
            subclient_name = self.tcinputs.get('SubclientName')
            #InstanceName = self.tcinputs.get('InstanceName')
            backupset = self.tcinputs.get('BackupsetName')
            subclient_obj = CommonUtils(self.commcell).get_subclient(
                client_name, agent, backupset, subclient_name)
            self.log.info('-----Triggering backup job-----')
            try:
                job_obj = subclient_obj.backup("Incremental")
                self.log.info("-----Backup job triggered successfully-----")
            except Exception as err:
                self.log.exception("-----Triggering backup job failed-----")
                raise Exception
            time.sleep(1)
            job_obj._initialize_job_properties()
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run Incremental backup with error: {0}"
                                .format(job_obj.delay_reason))
            self._log.info("Backup job {0} completed".format(job_obj.job_id))
            self.log.info('-----Creating machine object for proxy machine-----')
            try:
                self.windows_machine = WindowsMachine(self.tcinputs['Remotemachine'], self.commcell)
                self.log.info("-----proxy machine connection object created successfully-----")
            except Exception as err:
                self.log.exception("-----Failed to create proxy machine connection object-----"
                                   +str(err))
                raise Exception
            self.log.info('-----Getting UnQuiesce and Quiesce log lines from vsbkp.log-----')
            log_file_name = ("vsbkp.log")
            search_term = 'MediTech UnQuiesce successful'
            search_term1 = 'MediTech Quiesce successful'
            try:
                unquiesce = self.windows_machine.get_logs_for_job_from_file(job_obj.job_id,
                                                                            log_file_name,
                                                                            search_term)
                quiesce = self.windows_machine.get_logs_for_job_from_file(job_obj.job_id,
                                                                          log_file_name,
                                                                          search_term1)
                self.log.info("-----searched successfully for log lines for unquiesce and quiesce-----")
            except Exception as err:
                self.log.exception("-----Failed to search UnQuiesce and quiesce from vsbkp.log-----")
                raise Exception
            self.log.info(quiesce+","+unquiesce)
            self.log.info('-----Extracting time stamp from the UnQuiesce and quiesce log lines-----')
            try:
                unquiesce_split = unquiesce.split(job_obj.job_id)
                quiesce_slipt = quiesce.split(job_obj.job_id)
                time1 = unquiesce_split[0]
                time2 = quiesce_slipt[0]
                FT_UnQuiesce = time1[-9:]
                FT_UnQuiesce = FT_UnQuiesce[:-1]
                FT_Quiesce = time2[-9:]
                FT_Quiesce = FT_Quiesce[:-1]
                self.log.info("-----Successfully extracted time stamp from log lines-----")
            except Exception as err:
                self.log.exception("-----Filed to extract time stamp from log lines-----")
                raise Exception
            self.log.info('-----Calculating time difference between  quiesce and unquiesce operations-----')
            try:
                start_dt = dt.datetime.strptime(FT_Quiesce, '%H:%M:%S')
                end_dt = dt.datetime.strptime(FT_UnQuiesce, '%H:%M:%S')
                diff = (end_dt - start_dt)
                diff = diff.seconds/60
                self.log.info("-----Successfully calculated time diff between quiesce and unquiesce operations------")
            except Exception as err:
                self.log.exception("-----Failed to calculate time diff between quiesce and unquiesce operations -----")
                raise Exception
            time.sleep(5)
            try:
                if diff > (0.15):
                    self.log.error("Time taken for quiesce and UnQuiesce is more than 9 sec" +str(diff))
                    raise Exception
            except Exception as err:
                self.log.exception("Quiesce and UnQuiesce took more than expected time in backup"
                                   +str(diff))
            self.log.info("Quiesce and UnQuiesce operations were performed in expected time for backup")
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
