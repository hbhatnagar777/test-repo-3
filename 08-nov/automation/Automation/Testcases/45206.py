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
from AutomationUtils import logger, constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from MediaAgents.MAUtils.mahelper import DedupeHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "basic MA side dedupe case"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MEDIAAGENT
        self.feature = self.features_list.MEDIAMANAGEMENT
        self.show_to_user = True
        self.client_machine = None
        self.opt_selector = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentUsername": None,
            "MediaAgentPassword": None,
            "MediaAgentName": None,
            "MountPath": None,
            "DedupeStorePath":None,
            "RestorePath":None
        }
        self.content_path = None

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()

        self.client_machine = machine.Machine(
            self.tcinputs["ClientName"], self.commcell)
        self.opt_selector = OptionsSelector(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            libraryName = str(self.id) + "_lib"
            storagePolicyName = str(self.id) + "_SP"
            backupsetName = str(self.id) + "_BS"
            subclientName = str(self.id) + "_SC"
            #self._csdb = database_helper.CommServDatabase(self._commcell)
            dict_prim = {}
            dict_sec = {}
            storage_policy = None
            self._log.info(self.name)

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
                self._log.info("Storage policy exists! ")
                self._log.info("creating storage policy object...")
            storage_policy = self.commcell.storage_policies.get(storagePolicyName)
                #storage_policy.sealDDB(storagePolicyName,'Primary')
            self._log.info("Storage policy config done.")

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
            drive_path_client = self.opt_selector.get_drive(
                self.client_machine)
            self.content_path = "%s%s%s"%(drive_path_client,
                                          self.client_machine.os_sep,
                                          self.id)
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists, deleting")
                self.client_machine.remove_directory(self.content_path)

            self.client_machine.create_directory(self.content_path)
            self.log.info("content path created")

            # generate content for subclient
            self.client_machine.generate_test_data(
                self.content_path, dirs=1, files=10, file_size=1 * 1024 * 100)
            self.log.info("generated content for subclient")

            self._log.info("creating subclient object: "+subclientName )
            self._subclient = self._backupset.subclients.get(subclientName)
            self._log.info("setting subclient content to: "+ self.content_path)
            self._subclient.content = [self.content_path]
            self._log.info("Subclient config done.")

            #enable encyption
            self._log.info("enabling encryption on client")
            self.client.set_encryption_property("ON_CLIENT", key="4",key_len="256")
            self._log.info("enabling encryption on client: Done")

            #enabling client side cache
            self._log.info("disabling client side dedupe")
            self.client.set_dedup_property("clientSideDeduplication","OFF")
            self._log.info("disabled client side dedupe: Done")

            # initialize dedupehelper class
            dedupe = DedupeHelper(self)

            # Run FULL backup
            self._log.info("Running full backup...")
            dict_nw_transfer = {}
            for iterator in range(1,3):
                job = self._subclient.backup("FULL")
                self._log.info("Backup job: "+str(job.job_id))
                try:
                    if not job.wait_for_completion():
                        time.sleep(10)
                        if job.status.lower() == "completed":
                            self._log.info("job {0} complete".format(job.job_id))
                        else:
                            raise Exception("Job {0} Failed with {1}".format(job.job_id, job.delay_reason))
                except:
                    pass
                if job.status.lower() == "completed":
                    self._log.info("job {0} complete".format(job.job_id))
                else:
                    raise Exception("Job {0} Failed with {1}".format(job.job_id, job.delay_reason))
                self._log.info("Backup job completed.")

                #validations
                self._log.info("*************** Validations ****************")
                log_file="clBackup.log"
                log_path = self.client.install_directory+'\\Log Files'
                config_strings_clbackup = ['sigWhere[1]','isClientSideDedupEnabled - No','sigScheme[4]','compressWhere[0]','encType[2]','CVSingleInstTarget[1]']
                error_flag = []
                self._log.info("CASE 1: IS MA SIDE SIGNATURE GENERATION ENABLED?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file, config_strings_clbackup[
                                                                      0],job.job_id)
                if matched_line:
                    self._log.info("Result: Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: "+config_strings_clbackup[0]]

                self._log.info("CASE 2: IS CLIENT SIDE DEDUPE DISABLED?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file,
                                                                  config_strings_clbackup[1], job.job_id)
                if matched_line:
                    self._log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[1]]

                self._log.info("CASE 3: IS SIGNATURE SCHEME 4?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file,
                                                                  config_strings_clbackup[2], job.job_id)
                if matched_line:
                    self._log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[2]]

                self._log.info("CASE 4: IS COMPRESSION ENABLED ON CLIENT?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file,
                                                                  config_strings_clbackup[3], job.job_id)
                if matched_line:
                    self._log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[3]]

                self._log.info("CASE 5: IS ENCRYPTION TYPE 2?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file,
                                                                  config_strings_clbackup[4], job.job_id)
                if matched_line:
                    self._log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[4]]

                self._log.info("CASE 6: IS SINGLE INSTANCE TARGET ENABLED?")
                (matched_line, matched_string) = dedupe.parse_log(self.client.client_hostname,
                                                                  log_file,
                                                                  config_strings_clbackup[5], job.job_id)
                if matched_line:
                    self._log.info("Result :Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: " + config_strings_clbackup[5]]

                self._log.info("-------- validating: N/W TRANSFER BYTES -----------")
                network_bytes = dedupe.get_network_transfer_bytes(job.job_id)
                self._log.info("Network transferred bytes: "+network_bytes)
                dict_nw_transfer[iterator] = network_bytes
                if iterator == 2 and dict_nw_transfer[iterator]==dict_nw_transfer[iterator-1]:
                    self._log.info("Network transfer rate validation: Pass")
                else:
                    if iterator == 1:
                        self._log.info("validation will be done at the end of next iterator")
                    else:
                        self._log.error("Network transfer bytes validation: Fail")
                        error_flag += ["Network transfer bytes validation: Fail"]

                self._log.info("CASE 7: DID DEDUPE OCCUR? PRIMARY OBJECTS OF 1st BACKUP == SECONDARY OBJECTS OF 2nd BACKUP")
                P = dedupe.get_primary_objects(job.job_id)
                self._log.info("Primary objects: "+str(P))
                dict_prim[iterator] = P
                S = dedupe.get_secondary_objects(job.job_id)
                self._log.info("Secondary objects: "+str(S))
                dict_sec[iterator] = S
                if iterator == 2 and dict_sec[iterator] == dict_prim[iterator-1] and dict_prim[iterator] == dict_sec[iterator-1]:
                    self._log.info("Dedupe validation: Pass")
                else:
                    if iterator == 1:
                        self._log.info("validation will be done at the end of next iteration")
                    else:
                        self._log.error("Dedupe validation: Fail")
                        error_flag += ["Dedupe validation: Fail"]

                if error_flag:
                    raise Exception(
                        error_flag
                    )

            #restore
            self._log.info("running restore job")
            restorejob = self._subclient.restore_out_of_place(self.tcinputs["MediaAgentName"],self.tcinputs["RestorePath"],[self.content_path],True,True)
            self._log.info("Restore job: "+restorejob.job_id)
            try:
                if not restorejob.wait_for_completion():
                    time.sleep(10)
                    if restorejob.status.lower() == "completed":
                        self._log.info("job {0} complete".format(restorejob.job_id))
                    else:
                        raise Exception("Failed to run FULL backup with error: {0}".format(restorejob.delay_reason))
            except:
                pass
            if restorejob.status.lower() == "completed":
                self._log.info("job {0} complete".format(restorejob.job_id))
            else:
                raise Exception("Failed to run FULL backup with error: {0}".format(restorejob.delay_reason))
            self._log.info("restore job completed")

            #age data
            #self._log.info("delete job - incomplete code here.")

            #default setting
            self._log.info("default client dedupe prop setting..")
            self.client.set_dedup_property("clientSideDeduplication","USE_SPSETTINGS")

            #cleanup


        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self._log.info("********* cleaning up ***********")
                self._agent.backupsets.delete(backupsetName)
                self.commcell.storage_policies.delete(storagePolicyName)
            except:
                self._log.info("something went wrong while cleanup.")
                pass

    def tear_down(self):
        """Tear down function of this test case"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory exists, deleting")
            self.client_machine.remove_directory(self.content_path)
        if self.client_machine.check_directory_exists(self.tcinputs["RestorePath"]):
            self.log.info("restore path directory exists, deleting")
            self.client_machine.remove_directory(self.tcinputs["RestorePath"])
