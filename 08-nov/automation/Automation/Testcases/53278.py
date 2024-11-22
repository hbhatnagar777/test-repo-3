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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import os

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Testcase for Synthetic Full and cloud"
        self.tcinputs = {
            "MediaAgentName": None,
            "DedupeStorePath": None,
            "ContentPath": None,
            "RestorePath": None,
            "DiskLibraryName": None,
            "PowerShellScript": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.mmhelper_obj = MMHelper(self)


    def run(self):
        """Run function of this test case"""
        try:
            sp_name = str(self.id) + "_SP"
            backupset_name = str(self.id) + "_BS"
            subclient_name = str(self.id) + "_SC"
            restore_files_list = [self.tcinputs["GenerateDataAt"]]
            info_file_name = "info_" + str(self.id) + ".txt"
            look_ahead_reader_regkey = "DataMoverUseLookAheadLinkReader"
            testcase_path = self.locateTestcase(self.id)
            testcase_path = testcase_path[2:]
            automation_path = os.path.dirname(str(testcase_path))
            info_file_path = os.path.join(automation_path, "MediaAgents\\MAUtils", info_file_name)
            restore_path_with_lookahead = self.tcinputs["RestorePath"] + "_withLookAhead"
            restore_path_without_lookahead = self.tcinputs["RestorePath"] + "_withOutLookAhead"
            flag = 0
            failure = 0
            failure_list = []
            synth_string = None
            common_util = CommonUtils(self)

            self.log.info("Testcase for Synthetic Full and cloud")

            # delete exiting and create new data folder
            self.client_machine.remove_directory(self.tcinputs["GenerateDataAt"])
            self.client_machine.create_directory(self.tcinputs["GenerateDataAt"])

            # Check backupset if exits and create if not present
            if self._agent.backupsets.has_backupset(backupset_name):
                self.log.info(" Backupset exists!")
            else:
                self.log.info("Creating Backupset.")
                self._agent.backupsets.add(backupset_name)
                self.log.info("Backupset creation completed.")
            backupset_obj = self._agent.backupsets.get(backupset_name)

            # Check dedupe SP if exits and create new if not
            if self.commcell.storage_policies.has_policy(sp_name):
                self.log.info("Storage policy exists!")
            else:
                self.log.info("Creating Storage policy")
                self.commcell.storage_policies.add(sp_name, self.tcinputs["DiskLibraryName"],
                                                   self.tcinputs["MediaAgentName"],
                                                   self.tcinputs["DedupeStorePath"])
                self.log.info("Storage policy creation completed.")

            # Check SC if exits and create if not present
            if backupset_obj.subclients.has_subclient(subclient_name):
                self.log.info("Subclient exists!")
            else:
                self.log.info("Creating subclient")
                backupset_obj.subclients.add(subclient_name, sp_name)
                self.log.info("Subclient creation completed")
                # add subclient content
                subclient_obj = backupset_obj.subclients.get(subclient_name)
                self.log.info("""Setting subclient content to: {0}
                               """.format(self.tcinputs["ContentPath"]))
                subclient_obj.content = [self.tcinputs["ContentPath"]]
                self.client_machine.generate_test_data(self.tcinputs["GenerateDataAt"], dirs=3, files = 1000,
                                                       file_size = 2000)
                self.log.info("Adding subclient content completed.")
            subclient_obj = backupset_obj.subclients.get(subclient_name)

            if not os.path.isfile(info_file_path):
                self.log.info("Running full backup..")
                # running Full backup
                common_util.subclient_backup(subclient_obj, 'FULL')

            else:
                self.log.info("""No need to run full backup.
                               Continuing with incremental and synth full backups.""")
            # running Incremental backup
            self.log.info("""Generating content for subclient at: {0}
                           """.format(self.tcinputs["GenerateDataAt"]))
            # Creating content
            self.client_machine.generate_test_data(self.tcinputs["GenerateDataAt"], dirs=3, files=1000,
                                                   file_size=2000)

            common_util.subclient_backup(subclient_obj)

            # run synth full backup
            synth_job_obj = common_util.subclient_backup(subclient_obj, "synthetic_full")
            synth_job_summary = synth_job_obj.summary
            start_time_synth = synth_job_summary['jobStartTime']
            end_time_synth = synth_job_summary['lastUpdateTime']
            synth_time_taken = int(end_time_synth) - int(start_time_synth)
            self.log.info(
                "Time taken by synthfull job : {0}".format(str(synth_time_taken)))
            # read previous duration for synth full and if it is more then fail the case
            # else continue
            if os.path.isfile(info_file_path):
                fopen = open(info_file_path, "r")
                flines = fopen.readlines()
                fopen.close()
                self.log.info("""Value to compare time taken to
                               complete synth full job saved at : {0}
                               """.format(info_file_path))
                self.log.info(
                    "Threshold for synth full job : {0}".format(str(flines[1])))
                if synth_time_taken > int(flines[1]):
                    failure = 1
                    failure_string = """Time taken by synthfull job
                                     EXCEEDS the threshold. Failing testcase."""
                    failure_list.append(failure_string)
                    self.log.error(failure_string)
                else:
                    self.log.info(
                        "Time taken by synthfull job DOESN'T EXCEED the threshold. Continuing.. ")
            else:
                self.log.info(
                    """No threshold value present. Looks like a new synthfull for the subclient.
                    Saving the time duration for completing the synth full job in : {0}""".format(
                        info_file_path))
                fopen = open(info_file_path, "w")
                fopen.write(str(synth_job_obj.job_id))
                fopen.write("\n")
                fopen.write(str(synth_time_taken))
                fopen.close()

            # delete new restore created in previous run
            self.client_machine.remove_directory(restore_path_with_lookahead)
            self.client_machine.create_directory(restore_path_with_lookahead)
            self.client_machine.remove_directory(restore_path_without_lookahead)
            self.client_machine.create_directory(restore_path_without_lookahead)

            # move ahead with restore
            self.log.info("Running restore with look ahead reader")
            # Check if look ahead reader is enabled
            cs_machine = Machine(self.commcell._commserv_name, self.commcell)
            if cs_machine.get_registry_value("MediaAgent", look_ahead_reader_regkey) != '1':
                #CR:   maybe it has to go under MediaAgent and not MediaAgent
                self.log.info("Need to enable look ahead reader")
                cs_machine.update_registry("MediaAgent", look_ahead_reader_regkey, data=1,
                                           reg_type="DWord")
                self.log.info("VALIDATION: check if look ahead reader is enabled.")
                # CR: lookahead reader enabling must be verified from cvd logs of MA
                if cs_machine.get_registry_value("MediaAgent", look_ahead_reader_regkey) != '1':
                    raise Exception("Failed to enable look ahead reader.")
            self.log.info("Look ahead reader is enabled.")



            restore_job = common_util.subclient_restore_out_of_place(restore_path_with_lookahead, restore_files_list,
                                                            subclient=subclient_obj)

            self.log.info("Restore job {0} completed.".format(str(restore_job.job_id)))
            self.log.info("Restored data at location {0} on client {1}".format(
                restore_path_with_lookahead, self.client.client_name))
          
            restore_job_summary = restore_job.summary
            start_time_restore = restore_job_summary['jobStartTime']
            end_time_restore = restore_job_summary['lastUpdateTime']
            restore_time_taken = end_time_restore - start_time_restore
            self.log.info("""Time taken(in seconds) to complete restore
                           (w/ look ahead reader) is : {0}
                           """.format(str(restore_time_taken)))

            # disable look ahead reader
            self.log.info("Disabling look ahead reader by setting regKey value : {0}".format(
                look_ahead_reader_regkey))
            # CR: Same as above, regkey is in the wrong place
            cs_machine.update_registry("MediaAgent", look_ahead_reader_regkey, data=0,
                                       reg_type="DWord")

            # CR: Same as above, regkey is in the wrong place
            # check if registry key value was set correctly
            if cs_machine.get_registry_value("MediaAgent", look_ahead_reader_regkey) == '0':
                self.log.info("Look ahead reader key is disabled")
                flag = 1
            else:
                raise Exception("Error disabling look ahead reader")

            self.log.info("Running a restore without look ahead reader")

            restore_job_obj = common_util.subclient_restore_out_of_place(restore_path_without_lookahead,
                                                                     restore_files_list, subclient = subclient_obj)


            self.log.info("Restore job {0} completed.".format(str(restore_job_obj.job_id)))
            self.log.info("Restored data at location {0} on client {1}".format(
                restore_path_without_lookahead, self.client.client_name))
            restore_job_summary = restore_job_obj.summary
            start_time_restore = restore_job_summary['jobStartTime']
            end_time_restore = restore_job_summary['lastUpdateTime']
            restore_time_taken = end_time_restore - start_time_restore
            self.log.info("Time taken to complete restore (w/o look ahead reader) is : {0}".format(
                str(restore_time_taken)))
            if failure == 1:
                synth_string = "Synthetic Full Exceeded Threshold"

            self.log.info("Testcase completed successfully")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: {0}'.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.log.info("********************** CLEANUP STARTING *************************")
            if synth_string:
                self.result_string = "{0} ||| {1}".format(synth_string, self.result_string)

            if flag == 1:
                # registry key was disabled. We should enable it back
                self.log.info("""Enabling back look ahead reader by setting regKey value :
                               {0}""".format(look_ahead_reader_regkey))
                # CR: Clean up under MA and not MM
                cs_machine.update_registry("MediaAgent", look_ahead_reader_regkey,
                                           data=1, reg_type="DWord")
                # verifying if registry key value is set properly
                # CR: Clean up under MA and not MM
                if (cs_machine.get_registry_value("MediaAgent",
                                                  look_ahead_reader_regkey) == '1'):
                    self.log.info("Registry enabled back")
                else:
                    raise Exception("Error enabling registry")

            self.log.info("Deleting subclient content generated.")
            self.mmhelper_obj.remove_content(self.tcinputs["GenerateDataAt"], self.client_machine,
                                        num_files=None)
            self.log.info("********************** CLEANUP COMPLETED *************************")

