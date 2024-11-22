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
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    add_ddb_backup_subclient()      --  Adds a ddb backup subclient

    run()                           --  run function of this test case

"""
import time
import os
from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing Basic test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "suspend resume DDBBackup - manual DDB Subclient"
        self.show_to_user = True
        self.tcinputs = {
            "MediaAgentName": None,
            "MountPath": None,
            "DedupStorePath": None,
            "ContentPath":None,
        }

    def setup(self):
        """setup method for the testcase"""
        self.common_util = CommonUtils(self)
        self.client_machine = Machine(self.client)
        self.cs_machine = Machine(self.commcell.commserv_client)
        self.ma_machine = Machine(self.tcinputs["MediaAgentName"], self.commcell)


    def add_ddb_backup_subclient(self, storage_policy_name, client_name):
        request_xml = """
                <App_CreateSubClientRequest>
                  <subClientProperties>
                    <subClientEntity>
                      <subclientName>DDBBackup</subclientName>
                      <backupsetName>defaultBackupSet</backupsetName>
                      <instanceName>DefaultInstanceName</instanceName>
                      <appName>File System</appName>
                      <clientName>{1}</clientName>
                    </subClientEntity>
                    <commonProperties>
                      <encryptionFlag>ENC_NETWORK_AND_MEDIA</encryptionFlag>
                      <storageDevice>
                        <dataBackupStoragePolicy>
                          <storagePolicyName>{0}</storagePolicyName>
                        </dataBackupStoragePolicy>
                      </storageDevice>
                    </commonProperties>
                    <fileSystemSubClient/>
                    <fsSubClientProp>            
                      <isDDBSubclient>true</isDDBSubclient>
                      <isManualDDBSubclient>true</isManualDDBSubclient>
                    </fsSubClientProp>
                    <hcSubclientProp/>
                    <analyticsSubclientProp/>
                    <cassandraProps/>
                  </subClientProperties>
                </App_CreateSubClientRequest>
                """.format(storage_policy_name, client_name)
        response = self.commcell._qoperation_execute(request_xml)
        print(response)

    def run(self):
        """main function for test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            sc_name = "sc_" + str(self.id)
            lib_name = "lib_" + str(self.id)
            sp_name = "sp_" + str(self.id)

            step_string = "0. Creating Library"
            self.log.info(step_string)
            disk = self.commcell.disk_libraries
            if disk.has_library(lib_name):
                self.log.info("Library already exists")
                lib_object = disk.get(lib_name)
            else:
                lib_object = disk.add(lib_name, self.tcinputs["MediaAgentName"],
                                      self.tcinputs["MountPath"])

            self.log.info("VALIDATING LIBRARY CREATION")
            disk.refresh()
            if disk.has_library(lib_object.library_name):
                self.log.info("LIBRARY VALIDATED")
            else:
                raise Exception("Library not created")

            step_string = "1. Creating Storage Policy"
            self.log.info(step_string)
            if self.commcell.storage_policies.has_policy(sp_name):
                sp_object = self.commcell.storage_policies.get(sp_name)
                sp_object.seal_ddb("Primary")
            else:
                self.commcell.storage_policies.add(sp_name, lib_name, self.tcinputs[
                    "MediaAgentName"], dedup_path=self.tcinputs["DedupStorePath"])
                self.commcell.storage_policies.refresh()
                sp_object = self.commcell.storage_policies.get(sp_name)
                sp_object.update_transactional_ddb(True, "Primary", "bdcmmtest03_9")
            self.log.info("Create new subclient")
            if self.backupset.subclients.has_subclient(sc_name):
                subclient = self.backupset.subclients.get(sc_name)
            else:
                subclient = self.backupset.subclients.add(sc_name, sp_object.storage_policy_name)
            self._subclient = subclient
            self.log.info("DedupeHelper Class")
            dedup = DedupeHelper(self)
            mm_helper = MMHelper(self)
            substore_id = dedup.get_sidb_ids(sp_object.storage_policy_id, "Primary")[1]
            self.log.info("substore id: {0}".format(substore_id))
            store_id = dedup.get_sidb_ids(sp_object.storage_policy_id, "Primary")[0]
            self.log.info("storeid : {0}".format(store_id))
            ddb_drive, ddb_path = os.path.splitdrive(self.tcinputs["DedupStorePath"])

            self.log.info("subclient")
            flag_vss = 0
            vss_string = ""
            resume_vss = 0
            resume_vss_i = 0
            mult_read = 0
            bkp_check = 0
            string1 = "Shadow Creation succeeded, ShadowId is "
            if self.backupset.subclients.has_subclient("DDBBackup"):
                self.log.info("Deleting pre existing DDBBackup subclient")
                self.backupset.subclients.delete("DDBBackup")
            else:
                self.log.info("no DDBBackup subclient")

            self.log.info("creating ddbbackup sublient")
            self.add_ddb_backup_subclient("systemSP", self.ma_machine.client_object.client_name)
            self.backupset.subclients.refresh()
            time.sleep(30)
            print(self.backupset.subclients.has_subclient("DDBBackup"))
            ddb_sub = self.backupset.subclients.get("DDBBackup")
            ddb_sub.allow_multiple_readers = True
            ddb_sub.data_readers = 10
            ddb_job = None
            subclient.content = [self.tcinputs["ContentPath"]]
            mm_helper.create_uncompressable_data(self.client.client_name, self.tcinputs["ContentPath"], 0.5, 2)
            # running first backup
            self.common_util.subclient_backup(subclient, "FULL")

            mm_helper.create_uncompressable_data(self.client.client_name, self.tcinputs["ContentPath"], 4, 4)
            second_backup = subclient.backup("Full")
            while not second_backup.is_finished:
                if not second_backup.phase == "Backup" and bkp_check < 1:
                    self.log.info("Not entered backup phase")
                    # bkp_check = 0
                elif not ddb_job:
                    ddb_job = ddb_sub.backup("FULL")
                    bkp_check = 1
                elif flag_vss == 0:
                    while flag_vss == 0:
                        self.log.info("checking for log line")
                        (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                         "clBackup.log",
                                                                         string1,
                                                                         str(ddb_job.job_id))
                        while not matched_string:
                            (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                             "clBackup.log",
                                                                             string1,
                                                                             str(ddb_job.job_id))
                        flag_vss = 1
                        self.log.info("found log line")
                        self.log.info("line: {0}".format(matched_line[0]))
                        ml1 = matched_line[0]
                        vss_string = ml1.split(" ")[-1]
                        self.log.info("vss string: {0}".format(vss_string))
                        ddb_job.pause(True)
                        time.sleep(20)
                        self._log.info("Now resuming ddb job")
                        ddb_job.resume(True)
                elif mult_read < 1:
                    while mult_read == 0:
                        string7 = "- clBackup.exe -j {0}".format(ddb_job.job_id)
                        self.log.info("checking for log line: {0}".format(string7))
                        (matched_line, matched_string) = dedup.parse_log(self.commcell.commserv_name,
                                                                         "JobManager.log",
                                                                         string7,
                                                                         str(ddb_job.job_id))
                        while not matched_string:
                            (matched_line, matched_string) = dedup.parse_log(self.commcell.commserv_name,
                                                                             "JobManager.log",
                                                                             string7,
                                                                             str(ddb_job.job_id))
                        mult_read = 1
                        line = matched_line[0].split("numstreams")[1]
                        self._log.info(line)
                        line = line.strip()
                        num_stre = int(line[0:2])
                        if num_stre == 10:
                            self._log.info("10 stream set")
                        else:
                            self._log.info("10 streams not set")

                elif resume_vss < 1:
                    while resume_vss == 0:
                        string2 = "Volume [{0}\\] not deleted yet, attach".format(ddb_drive)
                        self.log.info("checking for log line: {0}".format(string2))
                        (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                         "clBackup.log",
                                                                         string2,
                                                                         str(ddb_job.job_id))
                        while not matched_string:
                            (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                             "clBackup.log",
                                                                             string2,
                                                                             str(ddb_job.job_id))
                        resume_vss = 1
                elif resume_vss_i < 1:
                    while resume_vss_i == 0:
                        string3 = "Attached to shadow set {0}".format(vss_string)
                        self.log.info("checking for log line: {0}".format(string3))
                        (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                         "clBackup.log",
                                                                         string3,
                                                                         str(ddb_job.job_id))
                        while not matched_string:
                            (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"],
                                                                             "clBackup.log",
                                                                             string3,
                                                                             str(ddb_job.job_id))
                        resume_vss_i = 1
                        query = "select count(reservationid) from mmresourcetojob where jobid_l = {0}".format(str(
                            ddb_job.job_id))
                        self.csdb.execute(query)
                        f = self.csdb.fetch_one_row()
                        self._log.info("CSDB Reservations: {0}".format(str(f)))
                else:
                    self.log.info("waiting for backup to complete")

            sidb_ids = dedup.get_sidb_ids(sp_object.storage_policy_id, "Primary")
            string4 = "{0}-0-{1}-0".format(str(sidb_ids[0]), str(sidb_ids[1]))
            self._log.info("{0}".format(string4))
            string5 = "Quiesce"
            (matched_line, matched_string) = dedup.parse_log(self.tcinputs["MediaAgentName"], "SIDBEngine.log",
                                                             string4,
                                                             string5)
            if not matched_string:
                self._log.error("Quiesce fail")
            else:
                self._log.info("Quiesce done")

            if not ddb_job.wait_for_completion():
                self._log.info("waiting for ddb backup job to finish")

            ddb_sub.allow_multiple_readers = False
            time.sleep(60)
            query_final = "select LastSnapJobId from IdxSIDBSubStore where SIDBStoreId = {0}".format(store_id)
            self.csdb.execute(query_final)
            job_i = self.csdb.fetch_one_row()[0]
            self._log.info("Store: {0}".format(job_i))
            if str(job_i) == str(ddb_job.job_id):
                self._log.info("last job is same as ddb backup job run in the TC")
            else:
                raise Exception("DDBBackup job not updated in records")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            try:
                self.backupset.subclients.delete(sc_name)
                self.client_machine.remove_directory(self.tcinputs["ContentPath"])
            except Exception:
                self.result_string = "Some error in cleanup ||| {0}".format(self.result_string)
