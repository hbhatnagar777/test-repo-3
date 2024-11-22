# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Validate NFS objectstore for Data aging rule for deleted items

"""
import sys
import time

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.NFSObjectStore.nfs_data_aging_helper import NfsDataAgingHelper
from Server.NFSObjectStore.nfs_solr_query import ObjectstoreSolrHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing verification test for RPO feature is enabled trough reg key"""
    NUM_OF_TEST_FILES = 10

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate NFS objectstore for Data aging rule for deleted items"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.retval = 0
        self.tcinputs = {
            'NFSServerHostName': None,
            'ClientHostName': None,
            'ClientUserName': None,
            'ClientPassword': None,
            'SolrCloudName': None,
            'DaysToRetainDeletedItems': None,
            'IndexServerClientName': None
        }
        self.nfsutil_obj = None
        self.nfs_server_obj = None
        self.objstore_test_path = None
        self.test_server_path = None
        self.index_server_machine_obj = None
        self.server = None
        self.job_controller = None
        self.schedule_policy = None
        self.data_aging_helper = None
        self.nfs_solr_helper = None
        self.test_file_pattern = None
        self.file_details = {}

    def setup(self):
        """ Setup function of this test case """
        try:
            self.log.info("executing testcase")

            self.server = ServerTestCases(self)
            self.data_aging_helper = NfsDataAgingHelper(self.commcell,
                                                        self.tcinputs['IndexServerClientName'])

            self.log.info("add consider_retention_days_as_mins reg key on index server host")
            self.data_aging_helper.add_consider_retention_days_as_mins()

            self.nfs_solr_helper = ObjectstoreSolrHelper(self, self.tcinputs['SolrCloudName'])
            self.test_file_pattern = "file_" + str(self.id) + "_"

            self.nfsutil_obj = NFSutils(self.tcinputs['ClientHostName'],
                                        self.tcinputs['ClientUserName'],
                                        self.tcinputs['ClientPassword'],
                                        self.id,
                                        self.commcell)
            self.objstore_test_path = self.nfsutil_obj.machine_obj.join_path(
                self.nfsutil_obj.mount_dir,
                'folder1')

            self.nfs_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs.get('storagePolicy'))

            self.log.info("update job idle time out")
            self.nfs_server_obj.update_job_idle_timeout()

            self.log.info("Creating Object Store : %s", self.nfsutil_obj.Obj_store_name)
            share_path = self.nfs_server_obj.create_nfs_objectstore(
                self.nfsutil_obj.Obj_store_name,
                self.nfs_server_obj.storage_policy,
                self.tcinputs['SolrCloudName'],
                self.tcinputs['NFSServerHostName'],
                self.tcinputs['ClientHostName'],
                squashing_type="NO_ROOT_SQUASH",
                min_days_retain_deleted=self.tcinputs['DaysToRetainDeletedItems'],
                delete_if_exists=True)

            self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                         self.tcinputs['NFSServerHostName'],
                                                         share_path)
            self.log.info("NFS objectstore mounted successfully on %s",
                          self.nfsutil_obj.mount_dir)
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("getting subclient ID for objectstore")
            self.commcell.refresh()
            application_id = self.nfs_server_obj.get_objectstore_subclient_id(
                self.nfsutil_obj.Obj_store_name)
            self.log.info("objectstore subclient id %s", application_id)

            files_to_create = [self.test_file_pattern + str(i) for i in range(self.NUM_OF_TEST_FILES)]
            self.log.info("list of files to be created in objectstore: %s", files_to_create)
            self.data_aging_helper.create_files_wait_for_job_complete(
                files_to_create,
                self.nfsutil_obj.machine_obj,
                self.objstore_test_path,
                self.nfsutil_obj.Obj_store_name)

            # collect checksum for created files
            check_sum_before_delete = self.data_aging_helper.get_files_checksum(
                self.nfsutil_obj.machine_obj,
                self.objstore_test_path,
                files_to_create)
            self.log.info("collect latest core and extent core index details for created files")
            arch_file_map_before_delete = self.nfs_solr_helper.collect_archfile_details(
                application_id,
                files_to_create)
            self.log.info("archfile id for created files %s before delete",
                          arch_file_map_before_delete)

            # delete random files in objectstore
            self.log.info("deleting %s random files in files created",
                          int(self.NUM_OF_TEST_FILES/2))
            deleted_files = self.data_aging_helper.delete_files_in_objectstore(
                self.nfsutil_obj.machine_obj,
                self.objstore_test_path,
                files_to_create)
            self.log.info("deleted files %s", deleted_files)

            # wait for min_days_retain_deleted seconds to age the data
            self.log.info("wait for %s minutes to age the data",
                          self.tcinputs['DaysToRetainDeletedItems'])
            time.sleep(60 * int(self.tcinputs['DaysToRetainDeletedItems']))

            # additional 2 minutes
            time.sleep(120)

            self.data_aging_helper.validate_nfs_pruner_thread(self,
                                                              deleted_files,
                                                              application_id)

            self.log.info("check for is_visible flag set to true for non deleted items")
            non_deleted_files = list(set(files_to_create) - set(deleted_files))
            self.nfs_solr_helper.check_is_visisble(non_deleted_files,
                                                   'latest',
                                                   application_id)

            self.log.info("validate deleted items are marked as isPruned true")
            self.nfs_solr_helper.validate_is_pruned(deleted_files, application_id)

            # run Synthetic Full Backup
            self.data_aging_helper.run_synthetic_full(
                self.nfsutil_obj.Obj_store_name,
                policy_name="synth_full_objectstore_2_"+str(self.id))

            deleted_afiles = []
            for file_name, afiles in arch_file_map_before_delete.items():
                if file_name in deleted_files:
                    deleted_afiles.extend(afiles)

            deleted_afiles = list(set(deleted_afiles))
            self.log.debug("deleted afiles list %s", deleted_afiles)

            arch_file_map_after_delete = self.nfs_solr_helper.collect_archfile_details(
                application_id,
                files_to_create)
            self.log.info("archfileId after deleting files %s", arch_file_map_after_delete)

            # check if afileid is updated correctly after synth full Job
            self.nfs_solr_helper.validate_afiles_after_synthfull(
                self,
                arch_file_map_before_delete,
                arch_file_map_after_delete,
                deleted_files,
                non_deleted_files,
                deleted_afiles)

            self.data_aging_helper.update_archfile_space_reclamation()

            # run data aging
            da_job = self.commcell.run_data_aging('Primary', self.nfs_server_obj.storage_policy)
            self._log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception("Failed to run data aging with error: {0}".format(
                    da_job.delay_reason))
            self._log.info("Data aging job completed.")

            self.log.info("Check that the old Afile is not present"
                          "in ArchFileSpaceReclamation table")
            self.data_aging_helper.validate_afiles_cleared(self)

            self.log.info("validate details of deleted items in index is cleared")
            self.nfs_solr_helper.validate_deleted_items_index(deleted_files, application_id)

            # collect checksum for non deleted files
            check_sum_after_delete = self.data_aging_helper.get_files_checksum(
                self.nfsutil_obj.machine_obj,
                self.objstore_test_path,
                non_deleted_files)

            self.data_aging_helper.compare_checksum(check_sum_before_delete,
                                                    check_sum_after_delete)
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.data_aging_helper.remove_consider_retention_days_as_mins()
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=[self.nfsutil_obj.mount_dir])
        self.nfs_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
