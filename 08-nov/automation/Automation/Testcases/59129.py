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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
from AutomationUtils.windows_machine import WindowsMachine




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Open Stack backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Open stack guest size check validation"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            VirtualServerUtils.decorative_log("----------Starting Backup Job----------")
            try:
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.vsa_discovery(backup_options, dict())
                self.log.info("----------Starting Backup Job----------")
                bkpobj = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
                bkpobj.backup_folder_name = backup_options.backup_type
                if not backup_options.testdata_path:
                    bkpobj.testdata_path = VirtualServerUtils.get_testdata_path(
                        bkpobj.controller_machine)
                    self.testdata_path = bkpobj.testdata_path
                bkpobj.timestamp = self.testdata_path.rpartition('\\')[-1]
                self.timestamp = bkpobj.timestamp
                bkpobj.cleanup_testdata(backup_options)
                bkpobj.vsa_discovery(backup_options, extra_options={})
                backup_jobs = self.subclient.backup()
                if not backup_jobs.wait_for_completion():
                    raise Exception("Failed to run VM   job with error: "
                                    +str(backup_jobs.delay_reason))
                VirtualServerUtils.decorative_log("Back up job completed successfully")
            except Exception as err:
                self.log.exception("-----Triggering backup job failed-----")
                raise Exception
            VirtualServerUtils.decorative_log('Creating machine object for proxy machine')
            try:
                self.proxy_list = self.subclient.subclient_proxy
                self.proxymachine1 = WindowsMachine(self.proxy_list[0], self.commcell)
                VirtualServerUtils.decorative_log(
                    "proxy machine connection object created successfully")
            except Exception as err:
                self.log.exception("-----Failed to create proxy machine connection object-----")
                raise Exception
            VirtualServerUtils.decorative_log('Getting sizes from vsbkp.log')
            log_file_name = ("vsbkp.log")
            search_term = 'VMInfo [0] Allocated Size [0] Provisioned Size'
            search_term1 = 'Total guest size for VM'
            try:
                sizeline = self.proxymachine1.get_logs_for_job_from_file(backup_jobs.job_id, log_file_name, search_term)
                sizeline1 = self.proxymachine1.get_logs_for_job_from_file(backup_jobs.job_id, log_file_name, search_term1)
                VirtualServerUtils.decorative_log(
                    "searched successfully  log lines from vsbkp.log")
            except Exception as err:
                self.log.exception(
                    "-----Failed to search log lines from vsbkp.log-----")
                raise Exception
            VirtualServerUtils.decorative_log(sizeline+","+sizeline1)
            VirtualServerUtils.decorative_log('Extracting  sizes from log lines')
            try:
                sizeline = sizeline.split()
                size1 = sizeline[24]
                size1 = size1.replace('[', '').replace(']', '').replace(',', '')
                size2 = sizeline[21]
                size2 = size2.replace('[', '').replace(']', '').replace(',', '')
                VirtualServerUtils.decorative_log("sizes got successfully from the log line")
            except:
                self.log.exception("-----Failed to --get the sizes from the log lines---")
            try:
                VirtualServerUtils.decorative_log('validating the if corrected size has been considered')
                output1 = int(size1) ^ ((int(size1) ^ int(size2)) & -(int(size1) < int(size2)))
                sizeline1 = sizeline1.split()
                output2 = sizeline1[14]
                output2 = output2.replace('[', '').replace(']', '').replace(',', '')
                if output1 == int(output2):
                    VirtualServerUtils.decorative_log('validation succeeded')
            except Exception as exp:
                self.log.exception("-----validation failed---")
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
