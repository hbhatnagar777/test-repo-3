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
import time
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "dedupe dash copy case"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MEDIAAGENT
        self.feature = self.features_list.DEDUPLICATION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentUsername": None,
            "MediaAgentPassword": None,
            "MediaAgentName": None,
            "MountPath": None,
            "DedupeStorePath":None,
            "ContentPath":None,
            "RestorePath":None,
            "secCopyDDBPath":None
        }

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            libraryName = str(self.id) + "_lib"
            storagePolicyName = str(self.id) + "_SP"
            backupsetName = str(self.id) + "_BS"
            subclientName = str(self.id) + "_SC"
            secCopyName = str(self.id) + "_Sec"
            self._csdb = database_helper.CommServDatabase(self._commcell)
            dict_prim = {}
            dict_sec = {}
            self._log.info(self.name)

            #dedupe.setup_environment(libraryName,storagePolicyName)
            self._log.info("********* previous run cleaning up ***********")
            try:
                self._agent.backupsets.delete(backupsetName)
                self.commcell.storage_policies.delete(storagePolicyName)
            except:
                self._log.info("previous run(if any) cleanup errors")
                pass

            # create library
            self._log.info("check library: "+libraryName)
            if not self.commcell.disk_libraries.has_library(libraryName):
                self._log.info("adding Library...")
                self.commcell.disk_libraries.add(libraryName,self.tcinputs["MediaAgentName"],self.tcinputs["MountPath"],self.tcinputs["MediaAgentUsername"],self.tcinputs["MediaAgentPassword"]) #self.commcell.commserv_name.encode()
            else:
                self._log.info("Library exists!")
            self._log.info("Library Config done.")

            #create SP
            self._log.info("check SP: "+storagePolicyName)
            if not self.commcell.storage_policies.has_policy(storagePolicyName):
                self._log.info("adding Storage policy...")
                self.commcell.storage_policies.add(storagePolicyName,libraryName,self.tcinputs["MediaAgentName"],self.tcinputs["DedupeStorePath"]+str(time.time()))
            else:
                self._log.info("Storage policy exists!")
            self._log.info("Storage policy config done.")

            self._log.info("creating storage policy "+ storagePolicyName +" object")
            storage_policy = self.commcell.storage_policies.get(storagePolicyName)


            #create secondary copy
            self._log.info("check secondary copy:"+secCopyName)
            if not storage_policy.has_copy(secCopyName):
                self._log.info("adding secondary copy...")
                storage_policy.create_dedupe_secondary_copy(secCopyName,libraryName,self.tcinputs["MediaAgentName"],self.tcinputs["secCopyDDBPath"]+str(time.time()),self.tcinputs["MediaAgentName"], 1, 0, 0)
            else:
                self._log.info("secondary copy exists!")
            self._log.info("Secondary copy cofig done.")
            sec_copy_object = storage_policy.get_copy(secCopyName)
            sec_copy_object.copy_reencryption=(True, "SERPENT", 256)

            #create BS
            self._log.info("check BS: "+ backupsetName)
            #client = self.commcell.clients.get(self.tcinputs["ClientName"])
            #agent = client.agents.get(self.tcinputs["AgentName"])
            if not self._agent.backupsets.has_backupset(backupsetName):
                self._log.info("adding Backupset...")

                self._agent.backupsets.add(backupsetName)
            else:
                self._log.info("Backupset exists!")
            self._log.info("Backupset config done.")

            #create SC
            self._log.info("check SC: "+subclientName)
            self._log.info("creating backupset object: "+backupsetName)
            self._backupset = self._agent.backupsets.get(backupsetName)
            if not self._backupset.subclients.has_subclient(subclientName):
                self._log.info("adding Subclient...")
                self._subclient = self._backupset.subclients.add(subclientName,storagePolicyName)
            else:
                self._log.info("Subclient exists!")

            #add subclient content
            self._log.info("creating subclient object: "+subclientName )
            self._subclient = self._backupset.subclients.get(subclientName)
            self._log.info("setting subclient content to: "+ str([self.tcinputs["ContentPath"]]))
            self._subclient.content = [self.tcinputs["ContentPath"]]
            self._log.info("Subclient config done.")

            #enable encyption
            self._log.info("enabling encryption on client")
            self.client.set_encryption_property("ON_CLIENT", key="2", key_len="256")
            self._log.info("enabling encryption on client: Done")

            # initialize dedupehelper class
            dedupe = DedupeHelper(self)

            # Run FULL backup
            self._log.info("Running full backup...")
            self._log.info("1st Backup")
            job1 = self._subclient.backup("FULL")
            self._log.info("Backup job: "+str(job1.job_id))
            if not job1.wait_for_completion():
               raise Exception(
                   "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
               )
            self._log.info("Backup job completed.")

            iterator = 1

            #run auxcopy
            self._log.info("Running Auxcopy job...")
            auxjob1 = storage_policy.run_aux_copy(secCopyName,self.tcinputs["MediaAgentName"])
            self._log.info("Auxcopy job: "+str(auxjob1.job_id))
            if not auxjob1.wait_for_completion():
                raise Exception(
                    "Failed to run Auxcopy with error: {0}".format(auxjob1.delay_reason)
                )
            #validations
            self._log.info("*************** Validations ****************")
            log_file = "AuxCopy.log"
            log_path = self.client.install_directory + '\\Log Files'
            config_strings_auxcopy = ['Using 10.0 readless mode','OpenChunkSpecific: Enabling Auxcopy Readless for Copy', 'Enc. Type [4]', 'encryptionType [CV_DECRYPT_AND_ENCRYPT]']
            error_flag = []
            self._log.info("CASE 1: AUXCOPY SHOULD NOT USE 10.0 READLESS MODE")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"] , log_file,
                                                              config_strings_auxcopy[0], auxjob1.job_id)
            if matched_line:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[0]]
            else:
                self._log.info("Result: Pass")

            self._log.info("CASE 2: IS AUXCOPY READLESS ENABLED FOR COPY?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[1], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[1]]

            self._log.info("CASE 3: IS ENCRYPTION TYPE BLOWFISH?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[2], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[2]]

            self._log.info("CASE 4: IS [CV_DECRYPT_AND_ENCRYPT] SELECTED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[3], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[3]]

            self._log.info(r"CASE 5: DID DEDUPE OCCUR? [1st AUXCOPY PRI RECS == 2nd AUXCOPY SEC RECS]")
            data = dedupe.get_primary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Primary Objects :" + str(data))
            data1 = dedupe.get_secondary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Secondary Objects :" + str(data1))
            dict_prim[iterator] = data
            dict_sec[iterator] = data1
            if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] and dict_prim[iterator] == dict_sec[
                        iterator - 1]:
                self._log.info("Dedupe validation:SUCCESS")
            else:
                if iterator == 1:
                    self._log.info("validation will be done at the end of next iterator")
                else:
                    self._log.error("Dedupe validation:FAILED")
                    error_flag += ["failed to validate Dedupe"]

            if error_flag:
                raise Exception(
                    error_flag
                )

            self._log.info("2nd Backup")
            job1 = self._subclient.backup("FULL")
            self._log.info("Backup job: " + str(job1.job_id))
            if not job1.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
                )
            self._log.info("Backup job completed.")

            iterator += 1

            #run auxcopy
            self._log.info("Running Auxcopy job...")
            auxjob1 = storage_policy.run_aux_copy(storagePolicyName,self.tcinputs["MediaAgentName"])
            self._log.info("Auxcopy job: "+str(auxjob1.job_id))
            if not auxjob1.wait_for_completion():
                raise Exception(
                    "Failed to run Auxcopy with error: {0}".format(auxjob1.delay_reason)
                )
            #validations
            self._log.info("*************** Validations ****************")
            log_file = "AuxCopy.log"
            #log_path = self.client.install_directory + '\\Log Files'
            config_strings_auxcopy = ['Using 10.0 readless mode','OpenChunkSpecific: Enabling Auxcopy Readless for Copy', 'Enc. Type [4]', 'encryptionType [CV_DECRYPT_AND_ENCRYPT]']
            error_flag = []
            self._log.info("CASE 1: AUXCOPY SHOULD NOT USE READLESS 10.0 MODE")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[0], auxjob1.job_id)
            if matched_line:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[0]]
            else:
                self._log.info("Result: Pass")

            self._log.info("CASE 2: IS AUXCOPY READLESS FOR COPY ENABLED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[1], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[1]]

            self._log.info("CASE 3: IS ENCRYPTION TYPE 4?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[2], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: IS ENCRYPTION OPTION [CV_DECRYPT_AND_ENCRYPT] ENABLED?"]

            self._log.info("CASE 4: encryptionType [CV_DECRYPT_AND_ENCRYPT]")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_auxcopy[3], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_auxcopy[3]]

            self._log.info(r"CASE 5: DID DEDUPE OCCUR? [1st AUXCOPY PRI RECS == 2nd AUXCOPY SEC RECS]")
            data = dedupe.get_primary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Primary Objects :" + str(data))
            data1 = dedupe.get_secondary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Secondary Objects :" + str(data1))
            dict_prim[iterator] = data
            dict_sec[iterator] = data1
            if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] and dict_prim[iterator] == dict_sec[
                        iterator - 1]:
                self._log.info("Dedupe validation:SUCCESS")
            else:
                if iterator == 1:
                    self._log.info("validation will be done at the end of next iterator")
                else:
                    self._log.error("Dedupe validation:FAILED")
                    error_flag += ["failed to validate Dedupe"]

            if error_flag:
                raise Exception(
                    error_flag
                )

            #restore
            self._log.info("running restore job")
            restorejob = self._subclient.restore_out_of_place(self.tcinputs["MediaAgentName"],self.tcinputs["RestorePath"],[self.tcinputs["ContentPath"]],True,True)
            self._log.info("Restore job: "+restorejob.job_id)
            if not restorejob.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(restorejob.delay_reason)
                )
            self._log.info("restore job completed")

            #seal primary and secondary stores
            self._log.info("sealing primary and secondary stores")
            storage_policy.seal_ddb('Primary')
            time.sleep(30)
            storage_policy.seal_ddb(secCopyName)

            self._log.info("### dash copy case ###")
            pid1 = 0
            pid2 = 0
            # Run FULL backup
            self._log.info("Running full backup...")
            self._log.info("1st Backup")
            job1 = self._subclient.backup("FULL")
            self._log.info("Backup job: "+str(job1.job_id))
            if not job1.wait_for_completion():
               raise Exception(
                   "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
               )
            self._log.info("Backup job completed.")

            iterator = 1

            #run auxcopy
            self._log.info("Running Dashcopy job...")
            auxjob1 = storage_policy.run_aux_copy(storagePolicyName,self.tcinputs["MediaAgentName"],True)
            self._log.info("Auxcopy job: "+str(auxjob1.job_id))
            if not auxjob1.wait_for_completion():
                raise Exception(
                    "Failed to run Auxcopy with error: {0}".format(auxjob1.delay_reason)
                )
            #validations
            self._log.info("*************** Validations ****************")
            log_file = "CVJobReplicatorODS.log"
            config_strings_cvods = ['Using 10.0 readless mode',
                                      'OpenChunkSpecific: Enabling Auxcopy Readless for Copy', 'Encryption Type [4]',
                                      'encryptionType [CV_DECRYPT_AND_ENCRYPT]','Initializing Coordinator', 'Initializing Controller','[Coordinator] Number of streams allocated for the agent','[Reader_1] Initializing Worker Thread','[Coordinator] Initializing Coordinator:']
            error_flag = []
            self._log.info("CASE 1: IS DASHCOPY USING 10.0 READLESS MODE?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[0], auxjob1.job_id)
            if matched_line:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[0]]
            else:
                self._log.info("Result: Pass")

            self._log.info("CASE 2:IS AUXCOPY READLESS FOR COPY ENABLED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[1], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[1]]

            self._log.info("CASE 3: IS ENCRYPTION TYPE 4?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[2], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[2]]

            self._log.info("CASE 4: IS ENCRUPTION OPTION [CV_DECRYPT_AND_ENCRYPT] ENABLED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[3], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[3]]

            self._log.info("CASE 5: IS COORDINATOR INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[4], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[4]]

            self._log.info("CASE 6: IS CONTROLLER INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[5], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[5]]

            self._log.info("CASE 7: ARE STREAMS ALLOCATED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[6], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[6]]

            self._log.info("CASE 8: IS WORKER THREAD INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[7], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[7]]

            self._log.info("CASE 9: GET CVODS PROCESS ID")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[8], auxjob1.job_id)
            if matched_line:
                pid1 = str(matched_string[0]).split(" ")[0]
                self._log.info("CVODS Process ID: "+str(pid1))
            else:
                error_flag += ["failed to find: " + config_strings_cvods[8]]

            self._log.info(r"CASE 10: DID DEDUPE OCCUR? [1st AUXCOPY PRI RECS == 2nd AUXCOPY SEC RECS]")
            data = dedupe.get_primary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Primary Objects :" + str(data))
            data1 = dedupe.get_secondary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Secondary Objects :" + str(data1))
            dict_prim[iterator] = data
            dict_sec[iterator] = data1
            if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] and dict_prim[iterator] == dict_sec[
                        iterator - 1]:
                self._log.info("Dedupe validation:SUCCESS")
            else:
                if iterator == 1:
                    self._log.info("validation will be done at the end of next iterator")
                else:
                    self._log.error("Dedupe validation:FAILED")
                    error_flag += ["failed to validate Dedupe"]

            self._log.info("CASE 11: Archchunktoreplicate status")
            query = 'select distinct status from archchunktoreplicate where adminjobid = '+auxjob1.job_id
            self.csdb.execute(query)
            cur = self.csdb.fetch_all_rows()
            self._log.info("result: " + str(cur))
            err = 0
            for item in cur[0]:
                print(str(item))
                if int(item) != 2:
                    err = 1
            if err == 0:
                self._log.info("all chunks status 2 : pass")
            else:
                self._log.error("all chunks status not 2: Fail")
                error_flag += ["all chunks status not 2"]

            if error_flag:
                raise Exception(
                    error_flag
                )

            self._log.info("2nd Backup")
            job1 = self._subclient.backup("FULL")
            self._log.info("Backup job: " + str(job1.job_id))
            if not job1.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
                )
            self._log.info("Backup job completed.")

            iterator += 1

            # run auxcopy
            self._log.info("Running Auxcopy job...")
            auxjob1 = storage_policy.run_aux_copy(storagePolicyName, self.tcinputs["MediaAgentName"],True)
            self._log.info("Auxcopy job: " + str(auxjob1.job_id))
            if not auxjob1.wait_for_completion():
                raise Exception(
                    "Failed to run Auxcopy with error: {0}".format(auxjob1.delay_reason)
                )
            # validations
            self._log.info("*************** Validations ****************")
            error_flag = []
            self._log.info("CASE 1: DASH COPY SHOULD NOT USE 10.0 READLESS MODE")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[0], auxjob1.job_id)
            if matched_line:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[0]]
            else:
                self._log.info("Result: Pass")

            self._log.info("CASE 2: IS AUXCOPY READLESS FOR COPY ENABLED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[1], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[1]]

            self._log.info("CASE 3: IS ENCRYPTION TYPE 4?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[2], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[2]]

            self._log.info("CASE 4: IS ENCRYPTION OPTION [CV_DECRYPT_AND_ENCRYPT] ENABLED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[3], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[3]]

            self._log.info("CASE 5: IS COORDINATOR INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[4], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[4]]

            self._log.info("CASE 6: IS CONTROLLER INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[5], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[5]]

            self._log.info("CASE 7: ARE STREAMS ALLOCATED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[6], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[6]]

            self._log.info("CASE 8: IS COORDINATOR WORKER THREAD INITIALIZED?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[7], auxjob1.job_id)
            if matched_line:
                self._log.info("Result: Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: " + config_strings_cvods[7]]

            self._log.info("CASE 9: GET CVODS PROCESS ID. ARE CVODS PROCESS IDs FROM PREVIOUS AND CURRENT JOB SAME?")
            (matched_line, matched_string) = dedupe.parse_log(self.tcinputs["MediaAgentName"], log_file,
                                                              config_strings_cvods[8], auxjob1.job_id)
            if matched_line:
                pid2 = str(matched_string[0]).split(" ")[0]
                self._log.info("Process ID: "+str(pid2))
            else:
                error_flag += ["failed to find: " + config_strings_cvods[8]]

            if pid1 != pid2:
                self._log.error("Process ID mismatch for dash copy jobs: Fail")
                error_flag += ["Process ID mismatch for dash copy jobs: Fail"]
            else:
                self._log.info("CASE 9: PASS")

            self._log.info(r"CASE 10: DID DEDUPE OCCUR? [1st AUXCOPY PRI RECS == 2nd AUXCOPY SEC RECS]")
            data = dedupe.get_primary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Primary Objects :" + str(data))
            data1 = dedupe.get_secondary_objects_sec(job1.job_id, secCopyName)
            self._log.info("Secondary Objects :" + str(data1))
            dict_prim[iterator] = data
            dict_sec[iterator] = data1
            if iterator == 2 and dict_sec[iterator] == dict_prim[iterator - 1] and dict_prim[iterator] == dict_sec[
                        iterator - 1]:
                self._log.info("Dedupe validation:SUCCESS")
            else:
                if iterator == 1:
                    self._log.info("validation will be done at the end of next iterator")
                else:
                    self._log.error("Dedupe validation:FAILED")
                    error_flag += ["failed to validate Dedupe"]

            self._log.info("CASE 11: IS CHUNK STATUS IN ARCHCHUNKTOREPLICATE = 2?")
            query = 'select distinct status from archchunktoreplicate where adminjobid = ' + auxjob1.job_id
            self._log.info("QUERY: "+ query)
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            self._log.info("result: " + str(cur[0]))
            if int(cur[0]) == 2:
                self._log.info("all chunks status 2 : pass")
            else:
                self._log.error("all chunks status not 2: Fail")
                error_flag += ["all chunks status not 2"]

            if error_flag:
                raise Exception(
                    error_flag
                )

            #age data
            self._log.info("delete job - incomplete code here.")

            #cleanup
            try:
                self._log.info("********* cleaning up ***********")
                self._agent.backupsets.delete(backupsetName)
                self.commcell.storage_policies.delete(storagePolicyName)
            except:
                self._log.info("something went wrong while cleanup.")
                pass

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        pass
