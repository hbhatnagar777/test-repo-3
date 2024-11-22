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
    __init__()          --  initialize TestCase class

    _run_backup()       --  initiates backup job

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Wild Card content for Subclient Content and Filter"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Isilon - Wild Cards for Subclient Content and Filter"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "SubclientContent": None,
            "SubclientFilter": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None,
            "AgentName":None,
            "BackupsetName":None,
            "SubclientName":None,
            "ClientName":None
        }

    def _run_backup(self, backup_type):
        """Initiates backup job and waits for completion"""
        self.log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type)
        self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run {backup_type} backup job with error: {job.delay_reason}"
            )
        return job

    def validate_filter(self, job, ptrn1, ptrn2):
        """Validates both SC and filter wildcards are sent to filer properly
            Args:
                job          : job object for which wildcards are validated

                ptrn1 (list) : Contains last part of SC content with wildcard

                ptrn2 (list) : Contains last part of Filter content with wildcard

            Return:
                0 : If pattern is not sent properly

                1 : If pattern is sent properly
        """
        self.log.info("Validate whether the wildcard pattern and filters are sent to file server properly")
        self.MAClient = self.commcell.clients.get(self.subclient.storage_ma)
        self.MAMachine = Machine(self.MAClient)
        line1 = self.MAMachine.get_logs_for_job_from_file(job.job_id, "NasBackup.log", r"ENV \[FILES\]=")
        line2 = self.MAMachine.get_logs_for_job_from_file(job.job_id, "NasBackup.log", r"ENV \[EXCLUDE\]=")
        self.log.info(f"line1 is {line1}")
        self.log.info(f"line2 is {line2}")
        self.log.info(f"Subclient content pattern is {ptrn1}")
        self.log.info(f"Filter content pattern is {ptrn2}")
        for item in ptrn1:
            if item in line1:
                for item1 in ptrn2:
                    if item1 in line2:
                        self.log.info(f"Filter wildcard {item1} is present")
                    else:
                        self.log.info(f"Filter wildcard {item1} is missing")
                        return 0
            else:
                self.log.info("SC Wildcard not sent properly")
                return 0
        self.log.info("Wildcard content is sent to filer as expected")
        return 1
        
    def get_sub_dir(self, win_rest_client, win_rest_loc, sccontent_parent):
        """ Selects one of the restored path and is used for further operations
            Args:
                win_rest_client  (obj)  : Windows destination client object

                win_rest_loc (str)      : Windows destination path

                sccontent_parent (list) : Contains parent path of sc wildcard

            Return:
                path1  (str)  : Windows destination path of the selected dir

                sccontent_new : Content path of selected folder on file server
        """
        path1 = win_rest_loc + "\\" + (sccontent_parent[0].split("/"))[-1]
        self.log.info(f"Get the list of folders under restore path {path1}")
        rest_items = win_rest_client.get_folders_in_path(path1, recurse=False)
        self.log.info(f"Restored folders are {rest_items}")
        selected_fol = rest_items[0].split("\\")[-1]
        sccontent_new = sccontent_parent[0] + "/" + selected_fol
        self.log.info(f"New SC content {sccontent_new}")
        return path1, sccontent_new

    def _get_copy_precedence(self, storage_policy, storage_policy_copy):
        """Returns the copy precedence value"""
        self.csdb.execute(
            "select copy from archGroupCopy where archGroupId in (select id from archGroup where \
            name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
        cur = self.csdb.fetch_one_row()
        return cur[0]

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._nas_helper = NASHelper()

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            options_selector = OptionsSelector(self.commcell)

            if 'SubclientContent' in self.tcinputs:
                subclient_content = self.tcinputs['SubclientContent']

                # Check if subclient content is list
                if not isinstance(subclient_content, list):
                    subclient_content = subclient_content.split(",")

                # set subclient content
                self.log.info("*" * 10 + " Set Subclient Content " + "*" * 10)
                self.log.info(f"Subclient content to set:{subclient_content}")
                self.subclient.content = subclient_content

            else:
                self.log.info("Reading subclient content from object")
                subclient_content = self.subclient.content

            if 'SubclientFilter' in self.tcinputs:
                subclient_filter = self.tcinputs['SubclientFilter']

                # Check if subclient filter is list
                if not isinstance(subclient_filter, list):
                    subclient_filter = subclient_filter.split(",")

                # set subclient filter
                self.log.info("*" * 10 + " Set Subclient Filter " + "*" * 10)
                self.log.info(f"Subclient Filter to set: {subclient_filter}")
                self.subclient.filter_content = subclient_filter

            else:
                self.log.info("Reading subclient filter content from object")
                subclient_filter = self.subclient.filter_content

            new_filter_content = []
            for filter_content in subclient_filter:
                self.log.info(f"filter content is {filter_content}")
                new_filter_content.append(str(filter_content).split("/")[-1])
                self.log.info(new_filter_content)
            self.filter = new_filter_content
            sc_content_pattern = []
            for item in subclient_content:
                sc_content_pattern.append(item.split("/")[-1])
            self.log.info(f"Found last part of subclient filter: {new_filter_content}")
            self.log.info(sc_content_pattern)

            self.log.info("Get NAS client object")
            nas_client = self._nas_helper.get_nas_client(self.client, self.agent)
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )
            self.log.info(f"Will run below test case on: {self.subclient} subclient")

            # check the data readers count
            self.log.info("*" * 10 + " Make Subclient Data readers to 1 to disable Multistream " + "*" * 10)
            self.log.info(f"Number of data readers: {self.subclient.data_readers}")
            if self.subclient.data_readers != 3:
                self.log.info("Setting the data readers count to 1")
                self.subclient.data_readers = 1

            if self.subclient.is_intelli_snap_enabled:
                self.log.info("Disabling Intellisnap on subclient.")
                self.subclient.disable_intelli_snap()

            # run full backup
            job= self._run_backup("FULL")
            val = self.validate_filter(job, sc_content_pattern, new_filter_content)
			
            if not val:
                raise Exception(
                    "Filters are not sent properly " 
                )


            filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])
            restore_content=[]
            sccontentparent=[]
            for item in self.subclient.content:
                res=(item.split("/"))
                res="/".join(res[:-1])
                sccontentparent.append(res)

			#Only first content path is restored and validated	
            restore_content.append(sccontentparent[0])
            self.log.info(restore_content)
            windows_restore_client, windows_restore_location = \
            options_selector.get_windows_restore_client()

            self.log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)

            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, restore_content
            )
            self.log.info(
               f"Started Restore out of place to Windows client job with Job ID:{job.job_id}"
            )
			
            if not job.wait_for_completion():
                raise Exception(
                    f"Failed to run restore out of place job with error:{job.delay_reason}"
                )
            path1, sccontent_new = self.get_sub_dir(windows_restore_client,
                                                    windows_restore_location,
                                                    sccontentparent)
            sclist = []
            sclist.append(sccontent_new)              

            self._nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, path1, sclist, filter_content=self.filter
            )
			
            volume_path, _ = nas_client.get_path_from_content(sccontent_new)
            self._nas_helper.copy_test_data(nas_client, volume_path)

            self._run_backup("INCREMENTAL")
            volume_path, _ = nas_client.get_path_from_content(sccontent_new)
            self._nas_helper.copy_test_data(nas_client, volume_path)
            
            self._run_backup("DIFFERENTIAL")

            self.log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
            job = self.subclient.restore_out_of_place(
                self.client.client_name,
                filer_restore_location,
                sclist)

            self.log.info(
                f"Started Restore out of place to filer job with Job ID:{job.job_id} "
            )

            if not job.wait_for_completion():
               raise Exception(
                    f"Failed to run restore out of place job with error: {job.delay_reason}"
                )

            self.log.info("Successfully finished OOP restore to filer")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, path1, sclist, filer_restore_location
            )

            # check if intellisnap is enabled at client level
            if not self.client.is_intelli_snap_enabled:
                self.log.info("Intelli Snap is not enabled for client, enabling it.")
                self.client.enable_intelli_snap()

            self.log.info("Intelli Snap for client is enabled.")

            # Check if intellisnap is enabled at subclient level
            if not self.subclient.is_intelli_snap_enabled:
                self.log.info("Intelli snap is not enabled at subclient level, enabling it.")
                self.subclient.enable_intelli_snap("Dell EMC Isilon Snap")

            self.log.info("Intelli Snap for subclient is enabled.")

            self._run_backup("FULL")

            volume_path, _ = nas_client.get_path_from_content(sccontent_new)
            self._nas_helper.copy_test_data(nas_client, volume_path)

            self._run_backup("INCREMENTAL")
            volume_path, _ = nas_client.get_path_from_content(sccontent_new)
            self._nas_helper.copy_test_data(nas_client, volume_path)

            self._run_backup("DIFFERENTIAL")

            storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            storage_policy_copy = "Primary"

            self.log.info("*" * 10 + "Running backup copy now" + "*" * 10)

            job = storage_policy.run_backup_copy()
            self.log.info(f"Backup copy workflow job id is : {job.job_id}")
            if not job.wait_for_completion():
                raise Exception(
                    f"Failed to run backup copy with error:{job.delay_reason}"
                )
            self.log.info(f"Successfully finished backup copy workflow Job {job.job_id}")

            if job.status != 'Completed':
                raise Exception(
                    f"job: {job.job_id} for Backup copy operation is completed with errors, Reason: {job.delay_reason}"
                )

            copy_precedence = self._get_copy_precedence(
                self.subclient.storage_policy, storage_policy_copy
            )
            job = self.subclient.restore_out_of_place(self.client.client_name,
                                                       filer_restore_location,
                                                       sclist,
                                                       copy_precedence=int(copy_precedence),
                                                       )
            self.log.info(
                f"Started Restore out of place to filer job with Job ID: {job.job_id}"
            )
            if not job.wait_for_completion():
                raise Exception(
                    f"Failed to run restore out of place job with error:{job.delay_reason}"
                )
            self.log.info("Successfully finished Restore out of place to Filer from backupcopy")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, path1, sclist, filer_restore_location
            )


        except Exception as exp:
            self.log.error(f'Failed with error:{exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED
