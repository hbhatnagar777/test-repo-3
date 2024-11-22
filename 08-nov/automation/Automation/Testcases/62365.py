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

from logging import error
import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Reports.utils import TestCaseUtils
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from AutomationUtils.options_selector import OptionsSelector
from Server.NFSObjectStore.nfs_solr_query import ObjectstoreSolrHelper
from Server.NFSObjectStore.nfs_data_aging_helper import NfsDataAgingHelper

"""
verify flush queries are flushed correctly when index services come back online
************************
1. create an HFS share.
2. turn off the Idx services.
3. dump data in share.
4. get the file names of the testdata we had dumped.
5. now turn on the services. and wait for few mins. check if collect file is empty.
6. query to idx server for all 3 collections with application_id --> get all the file names.
7. compare the files with file name. (for latestcore collection, version core, and extendcore (excude folders) )
8. if all the values are matched then pass else raise exception.
"""


# collect_archfile_details use this method to compare the no. of files  in arch_file_map and total no. of files in share.


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Index Server Flush"
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.network_store_helper = None
        self.test_dir_name = 'folder1'
        self.tcinputs = {
            "NFSServerHostName": None,
            "clientHostname": None,
            "clientUsername": None,
            "clientPassword": None,
            "SolrCloudName": None,
            "idxServerClient": None,
            "indexServer": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                    self.tcinputs['clientUsername'],
                                    self.tcinputs['clientPassword'],
                                    self.id,
                                    self.commcell)

        if self.nfsutil_obj.machine_obj.os_info.lower() != "windows" and self.tcinputs['clientHostname'] == self.tcinputs['idxServerClient']:
            # following exception is added because in Linux stoping service for single entity is not possible
            raise Exception(
                "In Linux Machine File server and Index server can't be on same machine")

        self.nfs_solr_helper = ObjectstoreSolrHelper(
            self, self.tcinputs['SolrCloudName'])
        self.data_aging_helper = NfsDataAgingHelper(self.commcell,
                                                    self.tcinputs['idxServerClient'])

        self.objstore_test_path = self.nfsutil_obj.machine_obj.join_path(
            self.nfsutil_obj.mount_dir,
            'folder1')
        self.utils = TestCaseUtils(self)
        self.nfs_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                        self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword'],
                                        self.tcinputs.get('storagePolicy'))
        self.log.info("Creating Object Store : %s",
                      self.nfsutil_obj.Obj_store_name)
        self.local_tst_path = self.nfsutil_obj.machine_obj.join_path(
                                                                self.nfsutil_obj.automation_temp_dir,
                                                                'localtestdir',
                                                                self.test_dir_name)
        nfs_server_name = self.tcinputs['NFSServerHostName'].split('.')[0]
        client_host_name = self.tcinputs['clientHostname'].split('.')[0]
        share_path = self.nfs_server_obj.create_nfs_objectstore(
            self.nfsutil_obj.Obj_store_name,
            self.nfs_server_obj.storage_policy,
            self.tcinputs['indexServer'],
            nfs_server_name,
            client_host_name,
            squashing_type="NO_ROOT_SQUASH",
            delete_if_exists=True)

        self.nfsutil_obj.machine_obj.mount_nfs_share(self.nfsutil_obj.mount_dir,
                                                     self.tcinputs['NFSServerHostName'],
                                                     share_path)
        self.log.info("NFS objectstore mounted successfully on %s",
                      self.nfsutil_obj.mount_dir)

    def get_files(self, dir_info):
        """This function returns the list of all the files from a directory

        Args:
            dir_info (dict): output of scan directory function
        """
        files = set()
        delimiter = '\\' if self.nfsutil_obj.machine_obj.os_info.lower() == "windows" else "//"
        for file in dir_info:
            if file['type'] == 'file' and file['size'] != '0':
                files.add(file['path'].split(delimiter)[-1])
        return list(files)

    def run(self):
        """Run function of this test case"""
        try:
            for operation in ["stop"]: # "kill",
                self.nfsutil_obj.machine_obj.generate_test_data(self.local_tst_path,
                                                                hlinks=False)
                self.log.info("Created test data on path {0}".format(self.local_tst_path))
                dir_info = self.nfsutil_obj.machine_obj.scan_directory(
                                    self.local_tst_path)
                req_files = self.get_files(dir_info)
                self.log.info("copying test data from local path to nfs mount path")
                self.nfsutil_obj.machine_obj.copy_folder(self.local_tst_path,
                                                        self.nfsutil_obj.mount_dir,
                                                        optional_params='p')
                if operation == "stop":
                    self.data_aging_helper.stop_cv_service_wait()
                    time.sleep(60)
                    self.data_aging_helper.start_cv_service_wait()
                    time.sleep(60)
                else :
                    self.log.info("Killing 3dnfsd process")
                    self.nfsutil_obj.machine_obj.kill_process(process_name="3dnfsd") # kill 3dfs service
                    self.log.info("Sleeping for 6 mins to wait for 3dnfs to wake up again")
                    time.sleep(60*6) # cvd need 5 min to wake up 3dnfsd process
                # self.log.info(dir_info)
                
                self.nfsutil_obj.check_objectstore_backup_job(
                    self.nfsutil_obj.Obj_store_name)
                
                output = self.nfs_solr_helper.collect_archfile_details(application_id=(
                    self.nfs_server_obj.get_objectstore_subclient_id(self.nfsutil_obj.Obj_store_name)), req_files_list=req_files)
                raise_error = False
                for file in output:
                    if output[file]:
                        self.log.info("Archieve file ID for file" + file + " is " + str(output[file]))
                    else:
                        raise_error = True
                        self.log.error("No Archieve file ID recieved for file " + file)
                if not raise_error:
                    self.log.info("All collect files are flushed successfully")
                else:
                    Exception("All collect files are not flushed successfully")
                
                self.nfsutil_obj.compare_snapshot(self.local_tst_path,
                                                  self.objstore_test_path)
                self.nfsutil_obj.delete_files_in_path(self.local_tst_path)
                self.log.info("files under directory {0} deleted successfully".format(
                                                                            self.local_tst_path))
                self.nfsutil_obj.delete_files_in_path(self.objstore_test_path)
                self.log.info("files under directory {0} deleted successfully".format(
                                                                            self.objstore_test_path))

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.data_aging_helper.start_cv_service_wait()
        self.nfsutil_obj.obj_store_cleanup(
            mounted_paths=[self.nfsutil_obj.mount_dir])
        self.nfs_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
