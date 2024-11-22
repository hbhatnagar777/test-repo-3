# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate FS Quota and backups

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initializes in this method

    update_quota_limit()             -- updates quota limit for the given user to the given value

    get_quota()                      --  Gets quota limit of the given user

    run()                            --  Contains the core testcase logic and it is the one executed

    tear_down()                      --  Cleans the data created for Indexing validation
"""

from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):

    """Verify FS Quota and backups"""

    def __init__(self):
        """Initializes the TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Indexing - FS Quota and backups"
        self.tcinputs = {
            'StoragePolicy': None,
            'User': None,
        }
        self.storage_policy = None
        self.index_class_obj = None
        self.cl_machine = None
        self.indexingtestcase = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.indexing_level = None
        self.indexing_version = None
        self.user = None
        self.incr_job_obj = None

    def setup(self):
        """All testcase objects are initializes in this method"""
        try:
            self.cl_machine = Machine(self.client)

            # Storage policy & User
            self.storage_policy = self.tcinputs.get('StoragePolicy')
            self.user = self.tcinputs.get('User')

            self.log.info(" Storage policy is: {0}".format(self.storage_policy))
            self.log.info(" User is: {0}".format(self.user))

            # Indexing class object initialization
            self.index_class_obj = IndexingHelpers(self.commcell)
            self.indexingtestcase = IndexingTestcase(self)

            self.log.info("Creating backupset and subclient..")
            self.backupset_obj = self.indexingtestcase.create_backupset(
                name='backupset_fs_quota',
                for_validation=False)

            self.subclient_obj = self.indexingtestcase.create_subclient(
                name="sc1_quota",
                backupset_obj=self.backupset_obj,
                storage_policy=self.storage_policy,
                register_idx=False)

            self.log.info("Subclient content is: {0}".format(self.subclient_obj.content))

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def update_quota_limit(self, user, desired_quota_limit_value):
        """Checks for the presence of the index logs
          Args:
              user       (string) --  user for whom quota needs to be updated
              desired_quota_limit_value (int) -- desired quota limit value to be updated
          Returns:
              Nothing

          Raises:
              Exception:
                  if failed to update quota limit for the given user
          """
        try:
            self.log.info(f"Updating fs quota limit 'FSQuotaLimit' value to {desired_quota_limit_value} "
                          f"for the given user {user}")
            self.indexingtestcase.options_help.update_commserve_db(f"""
                update UMUsersProp set attrval={desired_quota_limit_value} where attrname like 'FSQuotaLimit' 
                and componentNameId in (select id from UMUsers where name like '{user}')""")

            self.log.info(f"Updated fs quota limit 'FSQuotaLimit' value to {desired_quota_limit_value} "
                          f"for the given user {user}")

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def get_quota(self, user):
        """Checks for the presence of the index logs
          Args:
              user     (string) --  user for whom quota limit needs to be checked

          Returns:
              quota limit of the given user

          Raises:
              Exception:
                  if failed to get quota limit for the given user
          """
        try:
            self.csdb.execute(f"""
                        select attrVal from UMUsersProp where componentNameId in 
                                (select id from UMUsers where name like '{user}') and attrname like 'FSQuotaLimit'
                         """)

            quota_limit = self.csdb.fetch_one_row()[0]

            return quota_limit

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Verify quota limit for the given user and update it to 20 GB
            2 - Run backups Full & Incremental
            3 - Update quota limit to 10 bytes for the given user
            4 - Run backups Incremental & Synthetic full
            5 - Incremental backup should fail, but we should not see any issue with the synthetic full backup
            6 - Update quota limit to 20 GB again
            7 - Run backups Incremental & Synthetic full and we should not see
                   any issue with any of these backup jobs
        """
        try:
            # Starting the testcase
            self.log.info("Started executing {0} testcase ".format(self.id))

            self.log.info(f"Checking quota of user {self.user}")
            user_quota = self.get_quota(self.user)
            self.log.info(f" FS Quota limit is: {user_quota} Bytes ")

            self.log.info(f"Updating user {self.user} quota limit to 20GB..")
            self.update_quota_limit(user=self.user, desired_quota_limit_value=21474836480)

            self.log.info(f"Checking quota of user {self.user}")
            user_quota = self.get_quota(self.user)
            self.log.info(f"FS Quota limit is: {user_quota} Bytes ")

            # Checking client's Indexing version (v1 or v2)
            self.log.info("Checking client's Indexing version v1 or v2 ")
            self.indexing_version = self.index_class_obj.get_agent_indexing_version(
                self.client,
                agent_short_name=None
            )
            self.log.info("Indexing Version is: {0}".format(self.indexing_version))
            if self.indexing_version == 'v1':
                raise Exception("This is V1 client ")

            # Checking if it is backupset level index or subclient level index
            self.log.info("Checking if it is backupset level index or subclient level index")
            self.indexing_level = self.index_class_obj.get_agent_indexing_level(self.agent)
            self.log.info("Agent Index Level is: {0}".format(self.indexing_level))

            self.log.info('************* Running backup jobs *************')

            self.indexingtestcase.run_backup_sequence(
                subclient_obj=self.subclient_obj,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full', 'Edit', 'Incremental', 'Edit'])

            self.log.info('************* Changing user quota limit to 10 bytes and running backups *************')

            self.log.info(f"Updating user {self.user} quota limit to 10 bytes..")
            self.update_quota_limit(user=self.user, desired_quota_limit_value=10)

            self.log.info(f"Checking quota of user {self.user}")
            user_quota = self.get_quota(self.user)
            self.log.info(f"FS Quota limit is: {user_quota} Bytes ")

            try:
                job_failed = False
                self.indexingtestcase.run_backup(
                    self.subclient_obj,
                    backup_level='Incremental',
                    verify_backup=False,
                    restore=False)
            except Exception as job_start_exp:
                self.log.exception(job_start_exp)
                error_string = str(job_start_exp)
                if error_string.find('have exceeded their quota') != -1:
                    self.log.info("Job failed as expected")
                    job_failed = True
                else:
                    raise Exception("Job failed but not due to insufficient quota...")

            if not job_failed:
                raise Exception('Job completed even when there is not sufficient quota and this is not expected')

            self.indexingtestcase.run_backup(
                self.subclient_obj,
                backup_level='Synthetic_full',
                verify_backup=False,
                restore=False)

            self.log.info('************* Changing user quota value to 20 GB and running backups *************')
            self.log.info(f"Updating user {self.user} quota limit to 20GB..")
            self.update_quota_limit(user=self.user, desired_quota_limit_value=21474836480)

            self.log.info(f"Checking quota of user {self.user}")
            user_quota = self.get_quota(self.user)
            self.log.info(f"FS Quota limit is: {user_quota} Bytes ")

            self.indexingtestcase.run_backup_sequence(
                subclient_obj=self.subclient_obj,
                steps=['Edit', 'Incremental', 'Synthetic_full'])

        except Exception as exp:
            self.log.error("Test case failed with error: {0}".format(exp))
            self.log.exception(exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Reverts user quota limit to 20 GB """
        try:
            self.log.info('************* Changing user quota value to 20GB and running backups *************')
            self.log.info(f"Updating user {self.user} quota limit to 20GB..")
            self.update_quota_limit(user=self.user, desired_quota_limit_value=21474836480)

            self.log.info(f"Checking quota of user {self.user}")
            user_quota = self.get_quota(self.user)
            self.log.info(f"FS Quota limit is: {user_quota} Bytes ")

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)
