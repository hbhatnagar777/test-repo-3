# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that folder size is correct when a cycle is aged and jobs are ran after that

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that folder size is correct when a cycle is aged and jobs are ran
    after that"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Folder size - Cycle is aged'
        self.show_to_user = False

        self.tcinputs = {
            'StoragePolicyName': None
        }

        self.backupset = None
        self.subclient = None
        self.storage_policy = None

        self.cl_machine = None
        self.cl_delim = None
        self.idx_tc = None
        self.idx_help = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.backupset_name = self.tcinputs.get('Backupset', 'FSV_age_first_cycle')
            self.subclient_name = self.tcinputs.get('Subclient', self.id)
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')

            self.cl_machine = Machine(self.client, self.commcell)
            self.cl_delim = self.cl_machine.os_sep

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name)

            self.subclient = self.idx_tc.create_subclient(
                name=self.subclient_name,
                backupset_obj=self.backupset,
                storage_policy=self.storagepolicy_name
            )

            self.storage_policy = self.commcell.policies.storage_policies.get(
                self.storagepolicy_name)

            self.storage_policy_copy = self.storage_policy.get_copy('Primary')

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                - Run FULL => INC => SFULL => INC
                - Age first cycle
                - Run INC => SFULL

            Validations:
                - Find after every backup job
                - Recursive browse with folder size verification at the end
                - Quota size computed

        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            sc_content = self.subclient.content

            self.idx_tc.new_testdata(sc_content)
            job1 = self.idx_tc.run_backup(self.subclient, 'full')

            self.idx_tc.edit_testdata(sc_content)
            job2 = self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('********** VERIFICATION 1 - Browse cycle 1 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient_name,
                'operation': 'browse',
                'show_deleted': False,
                'path': self.cl_delim,
                '_verify_size': 'yes',
                'restore': {'do': False}
            })

            self.idx_tc.run_backup(self.subclient, 'synthetic_full')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('Aging first two jobs ran')
            self.log.info('Deleting FULL job [{0}]'.format(job1.job_id))
            self.storage_policy_copy.delete_job(job1.job_id)

            self.log.info('Deleting INC job [{0}]'.format(job2.job_id))
            self.storage_policy_copy.delete_job(job2.job_id)

            self.idx_tc.cv_ops.data_aging(storage_policy=self.storagepolicy_name, sp_copy=None)

            # Mark the jobs as aged in validation DB
            self.backupset.idx.do_after_data_aging([job1.job_id, job2.job_id])
            time.sleep(60)

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('********** VERIFICATION 2 - Browse cycle 2 after aging **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient_name,
                'operation': 'browse',
                'show_deleted': False,
                'path': self.cl_delim,
                '_verify_size': 'yes',
                'restore': {'do': False}
            })

            self.idx_tc.run_backup(self.subclient, 'synthetic_full')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('********** VERIFICATION 3 - Browse cycle 3 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient_name,
                'operation': 'browse',
                'show_deleted': False,
                'path': self.cl_delim,
                '_verify_size': 'yes',
                'restore': {'do': False}
            })

            self.idx_help.verify_quota_size(self.backupset, self.cl_machine)

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        self.backupset.idx.cleanup()
