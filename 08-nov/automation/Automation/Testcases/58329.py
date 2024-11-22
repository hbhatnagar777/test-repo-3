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
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    corrupt_sfile       --  function to corrupt an SFILE at a given offset

    get_chunk_status    --  function to parse the csv dump and list good and bad blocks

    validate_bad_chunk  --  function to validate if the nad block has the offset that was corrupted

    run()           --  run function of this test case


"""

import re
# import os
# import zipfile
import random
import pandas as pd
import win32security
import ntsecuritycon as con

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils

from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Block-level Health check during DDB Verification"
        self.tcinputs = {
            "MediaAgentName": None,
            "DedupeStorePath1": None,
            "DedupeStorePath2": None,
            "ContentPath": None,
            "MountPath": None
        }
        self.dedupehelper = None
        self.mmhelper = None
        self.common_util = None
        self.cs_machine = None
        self.client_machine = None

    def setup(self):
        """Setup function of this test case"""
        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self.cs_machine = Machine(self.commcell.commserv_name, self.commcell)

    def corrupt_sfile(self, volume, chunk, offset):
        file_name = "F:\\Automation\\58329\\Library\\MP1\\X2S3TX_06.11.2020_13.10\\CV_MAGNETIC\\V_{0}\\CHUNK_{1}" \
                    "\\SFILE_CONTAINER_001".format(volume, chunk)
        self.log.info("File name: %s", file_name)
        user_y, domain, perm_type = win32security.LookupAccountName("", "Everyone")
        self.log.info("Domain name: %s",domain)
        self.log.info("Permission type: %s",perm_type)
        sd = win32security.GetFileSecurity(file_name, win32security.DACL_SECURITY_INFORMATION)
        dacl = sd.GetSecurityDescriptorDacl()
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user_y)
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(file_name, win32security.DACL_SECURITY_INFORMATION, sd)
        dummy_data_16bytes = bytes("ThisIsCorruption", 'ascii')
        file = open(file_name, "r+b")
        file.seek(offset)
        file.write(dummy_data_16bytes)
        file.close()

    def get_chunk_status(self, dump_path, chunk_id, sfile_id):

        data = pd.read_csv(dump_path, index_col=False,
                           usecols=[' chunkId ', ' id ', ' flags ', ' objMetaOffset '])
        d_f = pd.DataFrame(data)
        # filter only related to only chunk_id
        chunk_data = d_f.loc[(d_f[' chunkId '] == chunk_id)]
        bad_chunks = []
        good_chunks = []
        for index, row in chunk_data.iterrows():
            # look for specific sfile_id
            if (row[' objMetaOffset '] >> 32) == sfile_id:
                self.log.info("Corrupt chunk index in list is: %s",index)
                if row[' flags '] & 1024:
                    # add id to good chunks
                    good_chunks.append(row[' id '])
                else:
                    # add id to bad chunks
                    bad_chunks.append(row[' id '])
        return good_chunks, bad_chunks

    def validate_bad_chunk(self, dump_path, bad_chunk_id, offset):

        data = pd.read_csv(dump_path, index_col=False, usecols=[' id ', ' size ', ' objMetaOffset '])
        d_f = pd.DataFrame(data)
        bad_chunk_data = d_f.loc[(d_f[' id '] == bad_chunk_id)]
        self.log.info(type(bad_chunk_data))
        obj_meta_offset = int(bad_chunk_data[' objMetaOffset '].iloc[0])
        size = int(bad_chunk_data[' size '].iloc[0])
        # below print is debug print, remove if unnecessary
        self.log.info(obj_meta_offset, size)
        if (obj_meta_offset & 0xFFFFFFFF) <= offset <= (obj_meta_offset & 0xFFFFFFFF) + size:
            status = True
            return status
        raise Exception("Offset and bad block comparision failed")

    def run(self):
        """Run function of this test case"""
        try:
            sp_name = str(self.id) + "_SP"
            backupset_name = str(self.id) + "_BS"
            subclient_name = str(self.id) + "_SC"
            library_name = str(self.id) + "_lib"
            copy_name = str(self.id) + "_case2_copy"
            job_list = []
            self.log.info("Started executing %s testcase", self.id)

            # Setup test environment
            # Check backupset if exits and create if not present
            if self.agent.backupsets.has_backupset(backupset_name):
                self.log.info("Backupset exists!")
            else:
                self.log.info("Creating Backupset.")
                self.agent.backupsets.add(backupset_name)
                self.log.info("Backupset creation completed.")
            backupset_obj = self.agent.backupsets.get(backupset_name)

            # check if library exists
            self.log.info("check library: %s", library_name)
            if not self.commcell.disk_libraries.has_library(library_name):
                self.log.info("adding Library...")
                self.commcell.disk_libraries.add(library_name, self.tcinputs["MediaAgentName"],
                                                 self.tcinputs["MountPath"])
            else:
                self.log.info("Library exists!")
            self.log.info("Library Config done.")

            # Check SP if exits and create if not present
            if self.commcell.storage_policies.has_policy(sp_name):
                self.log.info("Storage policy exists!")
            else:
                self.log.info("Creating Storage policy")
                self.commcell.storage_policies.add(sp_name, library_name,
                                                   self.tcinputs["MediaAgentName"])
                self.log.info("Storage policy creation completed.")
            sp_obj = self.commcell.policies.storage_policies.get(sp_name)

            # create dedupe copy
            if sp_obj.has_copy(copy_name):
                self.log.info("Copy exits!!")
            else:
                self.log.info("Creating dedupe copy")
                sp_obj.create_dedupe_secondary_copy(copy_name,
                                                    library_name,
                                                    self.tcinputs["MediaAgentName"],
                                                    self.tcinputs["DedupeStorePath2"],
                                                    self.tcinputs["MediaAgentName"])
                self.log.info("Dedupe secondary copy creation completed. ")

            # Check SC if exits and create if not present
            if backupset_obj.subclients.has_subclient(subclient_name):
                self.log.info("Subclient exists!")
                subclient_obj = backupset_obj.subclients.get(subclient_name)
            else:
                self.log.info("Creating subclient")
                subclient_obj = backupset_obj.subclients.add(subclient_name, sp_name)
                self.log.info("Subclient creation completed")
                # add subclient content
                self.log.info("Adding subclient content to backup")
                self.log.info("""Setting subclient content to: %s
                               """, self.tcinputs["ContentPath"])
                subclient_obj.content = [self.tcinputs["ContentPath"]]
                self.log.info("Adding subclient content completed.")

            # run backups
            for i in range(0, 2):
                self.log.info("Running backup : Iteration = %s", str(i+1))
                job_list.append(self.common_util.subclient_backup(subclient_obj, 'FULL', True))


            # run DV2
            self.log.info("""Running DDB Verification job on %s
                            """, sp_name)
            storage_policy = self.commcell.storage_policies.get(sp_name)
            sp_id = storage_policy.storage_policy_id
            job = storage_policy.run_ddb_verification('Primary', 'Full', 'DDB_VERIFICATION')
            self.log.info("DDB Verification job: %s", str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run DDB Verification Job: %s", job.delay_reason)
            # listing all the datamovers MAs initiated
            log_f = r'AuxCopyMgr.log'
            log_l = r'Started AuxCopy process on mediaAgent'
            (matched_line, matched_string) = self.dedupehelper.parse_log(
                self.commcell.commserv_name,
                log_f,
                log_l,
                job.job_id)
            self.log.info("Matched line is: %s",matched_line)
            self.log.info("Matched sting is: %s",matched_string)
            malist = []
            for line in matched_line:
                self.log.info(line)
                result = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                malist += [result]
            self.log.info(malist)
            chunkinfo = []
            mpid_list = []
            volid_list = []
            chunkid_list = []

            # checking if the mountpaths are local to MA
            for media_agent in malist:

                # collecting all the chunks verified by each MA
                log_f = r'DataVerf.log'
                log_l = r'Going to validate Sfile for chnk'

                (matched_line, matched_string) = self.dedupehelper.parse_log(media_agent, log_f, log_l, job.job_id)

                for line in matched_line:
                    self.log.info(line)
                    result = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                    chunkinfo += [result]

                split = []
                for chunks in chunkinfo:
                    split = re.split(',', chunks)
                    mpid_list += [split[0]]
                    volid_list += [split[1].strip()]
                    chunkid_list += [split[2].strip()]

            # randomly picking a chunk to corrupt
            corrupt_chunk = random.choice(chunkid_list)
            corrupt_offset = 16*(random.randint(10, 1000))
            self.log.info("Chunk to be corrupted is: %s at offset: %s", corrupt_chunk, corrupt_offset)
            chunk_index = chunkid_list.index(corrupt_chunk)
            volume = volid_list[chunk_index]

            # corrupting the chunk
            self.corrupt_sfile(volume, corrupt_chunk, corrupt_offset)
            self.log.info("Chunk has been corrupted")

            # running DV2 again
            job = storage_policy.run_ddb_verification('Primary', 'Full', 'DDB_VERIFICATION')
            self.log.info("DDB Verification job: %s", str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run DDB Verification Job: %s", job.delay_reason)

            # get sidbstore id for the copy
            sidb = self.dedupehelper.get_sidb_ids(sp_id, 'Primary')
            self.log.info("The SIDBStoreID and SIDBSubStoreID for Primary copy is: %s", sidb)

            # dump Primary table after DV2 job completes
            dump_path = "F:\\Automation\\58329\\Dump\\PrimaryCopy\\primary.csv"
            self.log.info("The primary dump will be created on at: %s", dump_path)
            self.dedupehelper.get_sidb_dump(self.tcinputs["MediaAgentName"], 'primary', sidb[0], dump_path, split=0)
            self.log.info("The primary dump created")

            # getting block status
            self.log.info("Checking for the block status on the primary dump")
            good, bad = self.get_chunk_status(dump_path, int(corrupt_chunk), 1)
            self.log.info("good chunks: %s", good)
            self.log.info("bad chunks: %s", bad)

            # verify if the correct block was marked bad
            status = self.validate_bad_chunk(dump_path, bad[0], corrupt_offset)
            if status is True:
                self.log.info("Corrupted offset and the bad block match. Case passed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
