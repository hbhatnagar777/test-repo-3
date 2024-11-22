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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.nfssnapbasicacceptance import NFSSnapBasicAcceptance
from NAS.NASUtils.nashelper import NASHelper
from base64 import b64encode
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing basic intellisnap operations to verify trueup"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("New Automation -NetApp CIFS/NFS snap - Basic acceptance Test for intellisnap operations with True up")
        self.show_to_user = True
        self.automount = False
        self.tcinputs = {
            "AgentName": None,
            "BackupsetName": None,
            "ClientName": None,
            "SubclientContent": None,
            "SubclientName": None,
        }

    def copy_test_data(self, sccontent, nfsobj, nas_helper, nas_client):
        """
        Copies test data to either CIFS share or NFS Share
        """
        if self.tcinputs['AgentName'] == "Windows File System":
            for x in range(len(sccontent)):
                nas_helper.copy_test_data(nas_client, sccontent[x])
        elif self.tcinputs['AgentName'] == "Linux File System":
            self.log.info("Trying to add test data under NFS mountpoint")
            nfsobj.sccontent = sccontent
            nfsobj.proxy = Machine(self.tcinputs['ProxyClient'], self.commcell)
            nfsobj.add_content()

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info(f"Started executing {self.id} testcase")
            self._log.info(
                "Will run below test case on: %s subclient", format(str(self.tcinputs['SubclientName']))
            )
            self._log.info("Number of data readers: " + str(self._subclient.data_readers))
            if self._subclient.data_readers != 3:
                self._log.info("Setting the data readers count to 3")
                self._subclient.data_readers = 3
            self._log.info("Get NAS Client object")
            self._nas_helper = NASHelper()
            self.nfsobj = NFSSnapBasicAcceptance(self)
            self.nas_client = self._nas_helper.get_nas_client(self._client, self._agent)

            self._log.info("Make a CIFS Share connection")
            self.nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )
            self.impersonate_user = self.tcinputs['CIFSShareUser']
            self.impersonate_password = b64encode(self.tcinputs['CIFSSharePassword'].encode()).decode()
            self.proxy = self.tcinputs['ProxyClient']
            filer_restore_location = (str(self.tcinputs.get('FilerRestoreLocation', None)))
            self.sccontent1 = self.tcinputs['SubclientContent'].split(",")

            if self.sccontent1[0][0] != '/':
                self._log.info("This subclient supports NFS Auto-mount")
                self.nfsobj.automount = True

            job = self._nas_helper.run_backup(self._subclient, "FULL")
            self.copy_test_data(self.sccontent1, self.nfsobj, self._nas_helper, self.nas_client)
            job = self._nas_helper.run_backup(self._subclient, "INCREMENTAL")
            self.copy_test_data(self.sccontent1, self.nfsobj, self._nas_helper, self.nas_client)
            job = self._nas_helper.run_backup(self._subclient, "INCREMENTAL")
            self._storage_policy = self._commcell.storage_policies.get(self._subclient.storage_policy)
            job = self._storage_policy.run_backup_copy()
            self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + str(job.delay_reason)
                )
            self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))
            job = self._nas_helper.run_backup(self._subclient, "SYNTHETIC_FULL")
            fs_options = {'impersonate_user': self.impersonate_user,
                          'impersonate_password': self.impersonate_password}
            self.sc_content_for_restore = []
            self.content = self.sccontent1
            for x in range(len(self.sccontent1)):
                self.sc_content_for_restore += [x]
                self.sc_content_for_restore[x] = ((self.sccontent1[x]).replace("\\\\", "\\\\UNC-NT_"))
            if self.tcinputs['AgentName'] == "Windows File System":
                self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
                job = self._subclient.restore_out_of_place(
                      self.proxy,
                      filer_restore_location,
                      self.sc_content_for_restore,
                      fs_options=fs_options)
                self._log.info(
                    "Started Restore out of place to filer job with Job ID: %d", job.job_id
                )
                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                    )
                self._log.info("Successfully finished Restore out of place to Filer")
                self._nas_helper.validate_filer_to_filer_restored_content(
                    self.nas_client, self.sccontent1, filer_restore_location
                )
            elif self.tcinputs['AgentName'] == "Linux File System":
                self.options_selector = OptionsSelector(self.commcell)
                self._log.info("*" * 10 + " Run out of place restore to Linux Client" + "*" * 10)
                if self.tcinputs.get('RestoreClient'):
                    linux_restore_client, linux_restore_location = \
                        self.nfsobj.get_restore_client(self.tcinputs.get('RestoreClient'))
                else:
                    linux_restore_client, linux_restore_location = \
                        self.options_selector.get_linux_restore_client()
                if self.nfsobj.automount:
                    path2 = []
                    content = self.sccontent1
                    for i in range(len(content)):
                        path1 = content[i].split(":")
                        temp2 = '/' + path1[0] + path1[1]
                        path2.append(temp2)
                    self.nfsobj.restorecontent = path2
                else:
                    self.nfsobj.restorecontent = self.sccontent1
                job = self._subclient.restore_out_of_place(
                    linux_restore_client.machine_name,
                    linux_restore_location,
                    self.nfsobj.restorecontent,
                    restore_data_and_acl=False
                )
                self._log.info(
                    "Started restore out of place to linux client job with Job ID: " + str(job.job_id)
                )

                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run restore out of place job with error: " + str(job.delay_reason)
                    )

                self._log.info("Successfully finished Restore out of place to linux client")
                destination_path = self.nfsobj.generate_dest_path(linux_restore_location)
                out = linux_restore_client.compare_folders(linux_restore_client,
                                                           self.sccontent1[0],
                                                           destination_path,
                                                           ignore_files=self._nas_helper.ignore_files_list,
                                                           ignore_folder=self._nas_helper.ignore_files_list)
                if out:
                    self._log.error(
                        "Restore validation failed. List of different files \n%s", format(str(out))
                    )
                    raise Exception(
                        "Restore validation failed. Please check logs for more details."
                    )

                self._log.info("Successfully validated restored content")

            self.copy_test_data(self._subclient.content, self.nfsobj, self._nas_helper, self.nas_client)
            snapjob = self._nas_helper.run_backup(self._subclient, "INCREMENTAL")
            job = self._storage_policy.run_backup_copy()
            self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + str(job.delay_reason)
                )
            self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))
            self._log.info(f"snap job id is {snapjob} and its type is {type(snapjob)}")
            job = self._nas_helper.get_bkpcpyjob_from_snapjob(snapjob)
            self._log.info(f"bkpcpy job id is {job} and its type is {type(job)}")
            maclient = self.commcell.clients.get(self.subclient.storage_ma)
            mamachine = Machine(maclient)
            ret_value = self._nas_helper.verify_trueup(mamachine, job[0])
            if ret_value != 0:
                self._log.info("verified true up is enabled from logs")
            else:
                raise Exception(
                    "Trueup is not enabled from logs, hence failing the TC"
                )

        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED