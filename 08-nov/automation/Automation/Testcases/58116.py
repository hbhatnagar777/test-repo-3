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
    __init__()             --  initialize TestCase class

    _run_backup()          --  starts the backup job

    _get_copy_precedence() --  returns the copy precedence value

    random_data_restore()  --  returns list of files & folders to be restored
 
    setup()                --  setup function of this test case 

    run()                  --  run function of this test case

Steps:
    1.Run Full backup

    2. Run Incremental backup

    3. Run Differential backup

    4. Now run NRE Restore to windows client by selecting some random files\folders

    5. Validate restored data and confirm whether logical seek is used

    6. Run inplace restore

    7. Validate restored data and confirm whether logical seek is used

    8. Run out of place restore to Filer

    9. Validate restored data and confirm whether logical seek is used

   10. Run inplace restore from Auxilary copy

   11. Validate restored data and confirm whether logical seek is used

"""
import random
import string
import os
import re

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "NewAutomation NetApp 7 mode - V2 - Windows MA -  Logical seek "\
            "during NDMP restore"
        self.tcinputs = {
            "AuxCopyMediaAgent": None,
            "AuxCopyLibrary": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None
        }

    def _run_backup(self, backup_type):
        """Starts backup job"""
        self.log.info("*" * 10 + " Starting Subclient %s Backup ", backup_type + "*" * 10)
        job = self.subclient.backup(backup_type)
        self.log.info("Started %s backup with Job ID: %s", backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(backup_type, job.delay_reason))
        return job

    def _get_copy_precedence(self, storage_policy, storage_policy_copy):
        """Returns the copy precedence value
           Args: 
               storage_policy      (str)  --  Storage policy name
      
               storage_policy_copy (str)  --  storage policy copy name
           
           Return:
                string : copy precedence value """

        self._csdb.execute(
            "select copy from archGroupCopy where archGroupId in (select id from archGroup where \
            name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
        cur = self._csdb.fetch_one_row()
        return cur[0]

    def random_data_restore(self, nas_client, content):
        """Returns random files\folders from a network locatio
           
            Args:
                nas_client       (obj)   --  nas client object

                content          (list)  --  list of subclient content paths

            Returns:
                rand_dirs        (list)  --  list of directories

                rand_files       (list)  --  list of files   """

        rand_dirs = []
        rand_files = []
        for vol in content:
            self.log.info("path getting iterated is %s", vol)
            network_path, _ = nas_client.get_path_from_content(vol)
            obj = os.scandir(path=network_path)
            dirs = []
            files = []
            for entry in obj:
                if entry.is_dir():
                    dirs += [entry.name]
                elif entry.is_file():
                    files += [entry.name]
            if len(dirs) > 2:
                dirs_rand = random.sample(dirs, k=2)
                for dir in dirs_rand:
                    if dir != '~snapshot':
                        rand_dirs.append(vol+'/'+dir)
                self.log.info("Final random dirs list is %s", rand_dirs)
            if len(files) > 2:
                files_rand = random.sample(files, k=2)
                for file in files_rand:
                    if (re.search('restore_symboltable', file) or re.search('rstab', file)) is None:
                        rand_files.append(vol+'/'+file)
                self.log.info("Final random files list is %s", rand_files)
        return rand_dirs, rand_files

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.commserver_name = self.commcell.commserv_name
        self._nas_helper = NASHelper()

    def run(self):
        """Executes basic acceptance test case"""
        self.log.info(
            "Will run below test case on: %s subclient", self.tcinputs['SubclientName']
        )
        options_selector = OptionsSelector(self.commcell)
        self.log.info("Number of data readers: %s ", self.subclient.data_readers)
        if self.subclient.data_readers != 3:
            self.log.info("Setting the data readers count to 3")
            self.subclient.data_readers = 3

        self.log.info("Get NAS Client object")
        nas_client = self._nas_helper.get_nas_client(self.client, self.agent, is_cluster=True)

        self.log.info("Make a CIFS Share connection")
        nas_client.connect_to_cifs_share(
            str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
        )

        self._run_backup("FULL")
        for content in self.subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)

        self._run_backup("INCREMENTAL")
        for content in self.subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)

        job = self._run_backup("DIFFERENTIAL")

        # create a random string
        #random_string = "".join([random.choice(string.ascii_letters) for _ in range(4)])
        random_string = options_selector.get_custom_str()

        storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
        storage_policy_copy = "SPCopy_" + random_string

        self.log.info(
            "Creating Storage Policy Copy %s ", storage_policy_copy
        )
        storage_policy.create_secondary_copy(
            storage_policy_copy, str(self.tcinputs['AuxCopyLibrary']),
            str(self.tcinputs['AuxCopyMediaAgent'])
        )
        self.log.info("Successfully created secondary copy")

        self.log.info("*" * 10 + " Run Aux Copy job " + "*" * 10)
        job = storage_policy.run_aux_copy(
            storage_policy_copy, str(self.tcinputs['AuxCopyMediaAgent'])
        )
        self.log.info("Started Aux Copy job with Job ID: %s ", job.job_id)

        if not job.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: "+ job.delay_reason)

        self.log.info("Successfully finished Aux Copy Job")

        size = nas_client.get_content_size(self.subclient.content)

        windows_restore_client, windows_restore_location = \
            options_selector.get_windows_restore_client(size=size)

        self.log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)
        self.restore_dirs, self.restore_files = self.random_data_restore(nas_client,
                                                                         self.subclient.content)
        self.restore_paths = self.restore_dirs + self.restore_files
        job = self.subclient.restore_out_of_place(
            windows_restore_client.machine_name, windows_restore_location, self.restore_paths
        )
        self.log.info(
            "Started Restore out of place to Windows client job with Job ID: %s", job.job_id
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: "+ job.delay_reason
            )

        self.log.info("Successfully finished Restore out of place to windows client")

        self._nas_helper.validate_windows_restored_content(
            nas_client, windows_restore_client, windows_restore_location, self.restore_dirs
        )
        self._nas_helper.validate_windows_restored_content(nas_client,
                                                           windows_restore_client,
                                                           windows_restore_location,
                                                           self.restore_files,
                                                           files=1
                                                          )

        self.MAClient = self.commcell.clients.get(self.subclient.storage_ma)
        self.MAMachine = Machine(self.MAClient)
        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Restore will seek pipeline using logical offset")
        self.log.info("%s", lslogline)

        if lslogline:
            self.log.info("Logical Seek is used during the restore job %s", job.job_id)
        else:
            raise Exception(
                "Logical seek is not used during restore job "+ job.job_id)

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Seeking pipeline to offset:")
        self.log.info("Offsets used during restore \n %s", lslogline)

        self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self.subclient.restore_in_place(self.restore_paths)
        self.log.info("Started restore in place job with Job ID: %s", job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error:"+ job.delay_reason
            )

        self.log.info("Successfully finished restore in place job")


        self._nas_helper.validate_filer_restored_content(nas_client,
                                                         windows_restore_client,
                                                         windows_restore_location,
                                                         self.restore_dirs
                                                        )
        self._nas_helper.validate_filer_restored_content(nas_client,
                                                         windows_restore_client,
                                                         windows_restore_location,
                                                         self.restore_files,
                                                         files=1
                                                        )

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Restore will seek pipeline using logical offset")
        self.log.info("%s", lslogline)

        if lslogline:
            self.log.info("Logical Seek is used during the restore job %s", job.job_id)
        else:
            raise Exception(
                "Logical seek is not used during restore job "+ job.job_id)

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Seeking pipeline to offset:")
        self.log.info("Offsets used during restore \n %s", lslogline)

        self.log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])

        job = self.subclient.restore_out_of_place(
            self.client.client_name,
            filer_restore_location,
            self.restore_paths)

        self.log.info(
            "Started Restore out of place to filer job with Job ID: %d", job.job_id
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error:"+ job.delay_reason
            )

        self.log.info("Successfully finished Restore out of place to Filer")

        self._nas_helper.validate_filer_restored_content(
            nas_client, windows_restore_client, windows_restore_location,
            self.restore_dirs, filer_restore_location
        )
        self._nas_helper.validate_filer_restored_content(
            nas_client, windows_restore_client, windows_restore_location,
            self.restore_files, filer_restore_location, files=1
        )

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Restore will seek pipeline using logical offset")
        self.log.info("%s", lslogline)

        if lslogline:
            self.log.info("Logical Seek is used during the restore job %s", job.job_id)
        else:
            raise Exception(
                "Logical seek is not used during restore job "+ job.job_id)

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Seeking pipeline to offset:")
        self.log.info("Offsets used during restore \n %s", lslogline)

        self.log.info("*" * 10 + " Run in place restore from copy " + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self.subclient.storage_policy, storage_policy_copy
        )

        job = self.subclient.restore_in_place(
            self.restore_paths, copy_precedence=int(copy_precedence)
        )

        self.log.info(
            "Started restore in place from copy job with Job ID: %s", job.job_id
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore from copy with error: "+ job.delay_reason
            )

        self.log.info("Successfully finished Restore in place from copy")


        self._nas_helper.validate_filer_restored_content(
            nas_client, windows_restore_client, windows_restore_location,
            self.restore_dirs
        )
        self._nas_helper.validate_filer_restored_content(
            nas_client, windows_restore_client, windows_restore_location,
            self.restore_files, files=1
        )

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Restore will seek pipeline using logical offset")
        self.log.info("%s", lslogline)

        if lslogline:
            self.log.info("Logical Seek is used during the restore job %s", job.job_id)
        else:
            raise Exception(
                "Logical seek is not used during restore job "+ job.job_id)

        lslogline = self.MAMachine.get_logs_for_job_from_file(
            job.job_id,
            "CVNdmpRemoteServer.log",
            "Seeking pipeline to offset:")
        self.log.info("Offsets used during restore \n %s", lslogline)

        self.log.info("Deleting Secondary copy")
        storage_policy.delete_secondary_copy(storage_policy_copy)
        self.log.info("Successfully deleted secondary copy")
