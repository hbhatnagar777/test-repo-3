# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to verify if catalog migration is copying all index db contents to new index cache path

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Deletes old index cache if test case passes
"""

import time
import traceback
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):

    """Testcase to verify if catalog migration is copying all index db contents
    to new index cache path"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Indexing - Catalog migration test cases"
        self.tcinputs = {
            "mediaAgentName": None
        }
        self.ignore_files_list = ['*.FCS', '.dbLog', 'IndexCacheCleanupReport.csv', '*.txt']
        self.ignore_folders_list = ['Locks', '*_pid', 'IdxProcLocks']

    def setup(self):
        """Setup function of this test case"""

        self.mediaagent_obj = self.commcell.media_agents.get(self.tcinputs['mediaAgentName'])
        self.mediaagent_machine_obj = Machine(self.tcinputs['mediaAgentName'], self.commcell)
        self.mediaagent_client_obj = self.commcell.clients.get(self.tcinputs['mediaAgentName'])
        self.indexinghelper_obj = IndexingHelpers(self.commcell)

    def run(self):
        """Main function for test case execution"""

        catalogmigration_timestamp = str(int(time.time()))

        try:

            path_sep = self.mediaagent_machine_obj.os_sep
            new_idxcache_folder = "catmig_test_{0}".format(catalogmigration_timestamp)

            self.log.info(self.mediaagent_obj.index_cache_path)
            self.log.info("Cache enabled: {0}".format(self.mediaagent_obj.index_cache_enabled))
            self.old_indexcache_path = self.indexinghelper_obj.get_index_cache(
                self.mediaagent_client_obj)
            self.log.info("Original index cache path : {0}" .format(self.old_indexcache_path))

            oldpath_split = self.old_indexcache_path.split(path_sep)
            new_idxcache_path = path_sep.join(oldpath_split[:-1]) + path_sep + new_idxcache_folder

            self.log.info("new index cache path is {0}" .format(new_idxcache_path))

            catalogmigration_job_obj = self.mediaagent_obj.change_index_cache(
                self.old_indexcache_path, new_idxcache_path)

            catalogmigration_jobid = catalogmigration_job_obj.job_id
            self.log.info("catalog migration job id {0}" .format(catalogmigration_jobid))

            catalogmigration_job_status = catalogmigration_job_obj.wait_for_completion()

            if not catalogmigration_job_status:

                raise Exception("Catalog Migration job with job id [{0}] failed."
                                .format(catalogmigration_jobid))

            cachepath_from_csdb = self.indexinghelper_obj.get_index_cache(
                self.mediaagent_client_obj)
            self.log.info("Expected new index cache path : {0}" .format(new_idxcache_path))
            self.log.info("Actual new index cache path (from CSdb) : {0}" .format(
                cachepath_from_csdb))

            if cachepath_from_csdb == new_idxcache_path:
                self.log.info("Index cache path has been updated successfully in CSdb")
            else:
                raise Exception("Index cache path has not been updated in CSdb")

            regpath = "Machines" + path_sep + self.tcinputs["mediaAgentName"]
            idxpath_regkey = "dFSINDEXCACHE"
            cachepath_from_registry = self.mediaagent_machine_obj.get_registry_value(
                regpath, idxpath_regkey)
            self.log.info("Actual new index cache path (from registry) : {0}" .format(
                cachepath_from_registry))

            if cachepath_from_registry == new_idxcache_path:
                self.log.info("Index cache path has been updated successfully in registry")
            else:
                raise Exception("Index cache path has not been updated in registry")

            indexcache_diff = self.mediaagent_machine_obj.compare_folders(
                self.mediaagent_machine_obj, self.old_indexcache_path, new_idxcache_path,
                ignore_files=self.ignore_files_list, ignore_folder=self.ignore_folders_list)

            self.log.info("Index cache diff : {0} " .format(indexcache_diff))

            if not indexcache_diff:
                self.log.info("Catalog migration has successfully migrated all contents "
                              "of index cache")

            else:

                if indexcache_diff == ['IndexCacheCleanupReport.csv']:
                    self.log.info("IndexCacheCleanupReport was not copied to new index cache.")

                elif indexcache_diff == ['CvIdxDB\\.dbLog']:
                    self.log.info("CvIdxDB\\.dbLog was not copied to new index cache.")

                elif set(indexcache_diff) == {'CvIdxDB\\.dbLog', 'IndexCacheCleanupReport.csv'}:
                    self.log.info("[CvIdxDB\\.dbLog, IndexCacheCleanupReport.csv] was not copied to new index cache")

                else:
                    raise Exception("Catalog migration has failed to migrate some contents of index cache")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: {0}' .format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def tear_down(self):
        """Cleans the old index cache directory"""

        if self.status == constants.PASSED:
            try:
                self.log.info('Removing old index cache')
                self.log.info('Waiting for 2 minutes for log manager process to shutdown before deleting old directory')
                time.sleep(120)
                self.mediaagent_machine_obj.remove_directory(self.old_indexcache_path)
            except Exception as e:
                self.log.error('Failed to delete old index cache directory')
