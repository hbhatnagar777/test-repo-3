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

    run()                           --  run function of this test case

"""
import time
from cvpysdk.policies.storage_policies import StoragePolicyCopy
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.idautils import CommonUtils

class TestCase(CVTestCase):
    """Class for executing Basic test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MS DDB Base Case"
        self.show_to_user = True
        self.tcinputs = {
            "MediaAgentName": None,
            "MountPath": None,
            "DedupStorePath": None,
            "SqlSaPassword": None,
        }

    def run(self):
        """main function for test case"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            sc_name = "sc_" + str(self.id)
            lib_name = "lib_" + str(self.id)
            sp_name = "sp_" + str(self.id)
            self.log.info("Creating machine class instances for all machines")
            client_machine = Machine(self.client.client_name, self.commcell)
            cs_machine = Machine(self.tcinputs["CSClientName"], self.commcell)
            ma_machine = Machine(self.tcinputs["MediaAgentName"], self.commcell)
            self.common_util = CommonUtils(self)
            client_instance = ma_machine.client_object.instance
            self.log.info("Instance: {0}".format(client_instance))

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
            query = """update IdxSIDBSubStore set ExtendedFlags = 1 where SubStoreId = {0}""".format(substore_id)
            mm_helper.execute_update_query(query)
            self.csdb.execute("""SELECT extendedflags
                                FROM IdxSIDBSubStore
                                WHERE SubStoreId = {0}""".format(substore_id))
            rflag = self.csdb.fetch_one_row()

            if rflag[0] == '1':
                self.log.info("Validated setting of ms")
            else:
                self.log.error("MS not set on db")

            script_for_ms = '-sn SetDDBMarkAndSweepInterval -si "SET" -si {0} -si "1"'.format(str(substore_id))
            self.commcell._qoperation_execscript(script_for_ms)
            job_list = []
            subclient.content = [self.tcinputs["ContentPath"]]

            for i in range(10):
                if i % 2 == 0:
                    mm_helper.create_uncompressable_data(self.client.client_name, self.tcinputs["ContentPath"], 0.5, 2)
                    job_list += [self.common_util.subclient_backup(subclient, "FULL")]
                else:
                    job_list += [self.common_util.subclient_backup(subclient, "FULL")]
            dump_path = self.tcinputs["ContentPath"] + "\\primary.csv"

            primary_dump = dedup.get_sidb_dump(self.tcinputs["MediaAgentName"], "Primary", store_id, dump_path)

            dump_path = self.tcinputs["ContentPath"] + "\\secondary.csv"

            secondary_dump = dedup.get_sidb_dump(self.tcinputs["MediaAgentName"], "Secondary", store_id, dump_path)

            self.log.info("No of records in Primary: {0}".format(len(primary_dump.split("\r\n"))))
            self.log.info("No of records in Secondary: {0}".format(len(secondary_dump.split("\r\n"))))
            sp_copy = StoragePolicyCopy(self.commcell, sp_object.storage_policy_name, "primary")
            #
            for job in job_list:
                self.log.info("Deleting job : {0}".format(job.job_id))
                sp_copy.delete_job(job.job_id)

            cs_machine.update_registry("MediaManager", "MMPruneProcessIntervalMin", data=1,
                                       reg_type="DWord")
            for i in range(3):
                self.commcell.run_data_aging()
            self.log.info("Waiting after data aging ")

            time.sleep(180)

            dump_path = self.tcinputs["ContentPath"] + "\\primary1.csv"

            primary_dump_1 = dedup.get_sidb_dump(self.tcinputs["MediaAgentName"], "Primary", store_id, dump_path)
            dump_path = self.tcinputs["ContentPath"] + "\\secondary1.csv"
            secondary_dump_1 = dedup.get_sidb_dump(self.tcinputs["MediaAgentName"], "Secondary", store_id, dump_path)

            self.log.info("No of records in Primary: {0}".format(len(primary_dump_1.split("\r\n"))))
            self.log.info("No of records in Secondary: {0}".format(len(secondary_dump_1.split("\r\n"))))

            if len(primary_dump_1.split("\r\n")) == 3 and len(secondary_dump_1.split("\r\n")) == 3:
                self.log.info("VALIDATED: ALL RECORDS CLEARED")
            else:
                raise Exception("ALL RECORDS NOT CLEARED")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            try:
                self.backupset.subclients.delete(sc_name)
                client_machine.remove_directory(self.tcinputs["ContentPath"])
            except BaseException:
                self.result_string = "Some error in cleanup ||| {0}".format(self.result_string)
