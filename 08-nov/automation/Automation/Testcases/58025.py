# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Validate NFS objectstore for basic disk pruning

"""
import sys
import time
import datetime

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.NFSObjectStore.nfs_pruning_helper import NFSPrunerHelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing NFS objectstore pruning test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "validate NFS objectstore pruning test case"
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
            'NFS_Cache_DiskName': None,
            'NFSCacheMountDir': None
        }
        self.nfsutil_obj = None
        self.nfs_server_obj = None
        self.objstore_test_path = None
        self.test_server_path = None
        self.index_server_machine_obj = None
        self.server = None
        self.job_controller = None
        self.schedule_policy = None
        self.nfs_pruner_helper = None
        self.pruner_timeout = 2
        self.pruner_timeout_dontrun = 600
        self.tmp_data_path = None
        self.watermark_saved = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.server = ServerTestCases(self)

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

        self.nfs_pruner_helper = NFSPrunerHelper(self)
        self.watermark_saved = self.nfs_pruner_helper.get_high_watermark(self)

        # to avoid running pruner in between creating test data
        # for effective validation we set very high value
        # so that pruner don't run
        self.nfs_pruner_helper.update_pruner_timeout(
            self.pruner_timeout_dontrun,
            restart_services=True)

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
            delete_if_exists=True)

        self.commcell.refresh()

        self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                     self.tcinputs['NFSServerHostName'],
                                                     share_path)
        self.log.info("NFS objectstore mounted successfully on %s",
                      self.nfsutil_obj.mount_dir)

    def run(self):
        """Main function for test case execution"""
        try:
            self.nfs_server_obj.nfs_serv_machine_obj.set_logging_debug_level("3dnfs",
                                                                             level='6')

            (data_tobe_written, new_hwm) = self.nfs_pruner_helper.calculate_test_data_size(
                self.tcinputs['NFS_Cache_DiskName'],
                self)

            self.tmp_data_path = self.nfs_pruner_helper.write_data_dev_zero(
                self.tcinputs['NFSCacheMountDir'],
                int(data_tobe_written/2))

            self.nfsutil_obj.create_test_data_objecstore(
                int(data_tobe_written/2),
                self.nfsutil_obj.machine_obj,
                self.objstore_test_path,
                self.nfsutil_obj.Obj_store_name)

            self.nfs_pruner_helper.verify_watermark_crossed(
                new_hwm,
                self.tcinputs['NFS_Cache_DiskName'])

            self.nfs_pruner_helper.update_pruner_timeout(
                self.pruner_timeout,
                restart_services=False)

            self.nfs_pruner_helper.update_high_watermark(new_hwm)
            
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime(
                '%m/%d %H:%M:%S')
            time.sleep(self.pruner_timeout)

            self.nfs_pruner_helper.verify_pruner_completed(timestamp,
                                                           max_attempt=5)

            self.nfs_pruner_helper.verify_watermark_restored(
                new_hwm,
                self.tcinputs['NFS_Cache_DiskName'])
        except Exception as excp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.nfs_server_obj.nfs_serv_machine_obj.set_logging_debug_level(
            "3dnfs",
            level=0)

        self.nfs_pruner_helper.remove_pruner_timeout_reg()

        if self.nfs_server_obj.nfs_serv_machine_obj.check_directory_exists(
                self.tmp_data_path):
            self.nfs_server_obj.nfs_serv_machine_obj.remove_directory(
                self.tmp_data_path)
        self.nfsutil_obj.obj_store_cleanup(mounted_paths=[self.nfsutil_obj.mount_dir])
        self.nfs_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)

        self.nfs_pruner_helper.update_high_watermark(self.watermark_saved)
