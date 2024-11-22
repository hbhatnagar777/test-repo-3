# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the workflow "Enable subclient level index" works as expected and verifies that the CS DB
entries are created correctly.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    teardown()                  --  Cleans the data created for Indexing validation

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector

from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase

from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """This testcase verifies that the workflow "Enable subclient level index" works as expected and verifies that the
    CS DB entries are created correctly."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Enable subclient index'
        self.tcinputs = {
            "StoragePolicy": None
        }

        self.workflow = None
        self.cs_name = None
        self.cs = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:
            self.workflow = WorkflowHelper(self, 'Enable Subclient Index')
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_help = IndexingHelpers(self.commcell)
            self.idx_tc = IndexingTestcase(self)

            self.options_selector = OptionsSelector(self.commcell)

            if self.agent.agent_name != 'file system':
                raise Exception('This testcase works only for File System agent')

            if self.idx_help.get_agent_indexing_version(self.client) == 'v1':
                raise Exception('Client FS agent is in indexing v1 mode. Cannot use this client')

            if self.idx_help.get_agent_indexing_level(self.agent) == 'subclient':
                self.log.info('Agent is in subclient level index mode. Moving it to backupset level index.')
                if self.idx_help.set_agent_indexing_level(self.agent, 'backupset'):
                    self.log.info('Agent has been moved to backupset level index')
                else:
                    raise Exception('Failed to set backupset level index for the agent')

            self.log.info('Deleting all old entries in app_indexdbinfo table')
            all_backupsets = self.agent.backupsets.all_backupsets

            for backupset_name, backupset_prop in all_backupsets.items():
                self.log.info('Deleting entry for backupset [{0}] from index db info table'.format(
                    backupset_prop['id']))
                self.options_selector.update_commserve_db("""
                    delete from app_IndexDBInfo where backupsetId = {0}
                """.format(backupset_prop['id']))

            self.backupset = self.idx_tc.create_backupset('sli_workflow', for_validation=True)

            self.subclient = self.idx_tc.create_subclient(
                name='sc_sli_workflow',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs['StoragePolicy']
            )

            self.log.info('Creating testdata')
            self.idx_tc.new_testdata(self.subclient.content)

            self.backupset_guid = self.backupset.guid
            self.subclient_guid = self.subclient.properties['subClientEntity']['subclientGUID']

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Run FULL backup in backupset level index mode.
                2) Run workflow and check if it completes successfully.
                3) Verify if subclient level index is enabled.
                4) Verify if subclient level index entry is seen in app_indexdbinfo table.

        """

        try:

            full_job = self.idx_tc.run_backup(self.subclient, backup_level='Full', verify_backup=True)

            self.log.info('********** Verifying if DB is created at backupset level **********')

            self.csdb.execute("""
                select id from App_IndexDBInfo where dbName = '{0}' and backupSetGUID = '{1}'
            """.format(self.backupset_guid, self.backupset_guid))

            if self.csdb.fetch_one_row()[0] == '':
                raise Exception('Backupset level index information is not present in App_IndexDBInfo table')
            else:
                self.log.info('Backupset level index is created')

            self.log.info('********** Running subclient level index workflow **********')

            self.workflow.execute({
                'choice': 'Clients',
                'clientList': {
                    'clientId': self.client.client_id,
                    'displayName': self.client.display_name,
                    'clientName': self.client.client_name
                },
                'clientGroup': '',
                'Agent': 'FileSystem',
                'waitInfinitely': 'true'
            })

            self.log.info('********** Verifying if agent level entry is created **********')

            if self.idx_help.get_agent_indexing_level(self.agent) != 'subclient':
                raise Exception('Subclient level index entry at app_idaprop table is not created')

            self.log.info('********** Verifying if DB is created at subclient level **********')

            self.csdb.execute("""
                select id from App_IndexDBInfo where dbName = '{0}' and backupSetGUID = '{1}'
            """.format(self.subclient_guid, self.backupset_guid))

            if self.csdb.fetch_one_row()[0] == '':
                raise Exception('Subclient level index information is not present in App_IndexDBInfo table')
            else:
                self.log.info('Subclient level index is created')

            try:
                self.idx_tc.verify_job_find_results(full_job, self.backupset.idx)
            except Exception:
                raise Exception('Browse/Find results gave incorrect results after browse from subclient level index')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
