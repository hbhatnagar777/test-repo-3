# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the "Upgrade to indexing v2" workflow works as expected

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector

from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase

from Server.Workflow.workflowhelper import WorkflowHelper

from cvpysdk.policies.schedule_policies import OperationType


class TestCase(CVTestCase):
    """This testcase verifies that the workflow "Upgrade indexing v2" works as expected"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Upgrade to indexing V2'

        self.tcinputs = {
            "StoragePolicy": None,
            "SchedulePolicy": None
        }

        self.workflow = None
        self.cs_name = None
        self.cs = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:
            self.workflow = WorkflowHelper(self, 'Upgrade to IndexingV2')
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_help = IndexingHelpers(self.commcell)
            self.idx_tc = IndexingTestcase(self)

            self.options_selector = OptionsSelector(self.commcell)

            if self.agent.agent_name != 'file system':
                raise Exception('This testcase works only for File System agent')

            if self.idx_help.get_agent_indexing_version(self.client) == 'v2':
                self.log.error('Client is already in Indexing V2 mode, moving it to V1 mode')

                self.options_selector.update_commserve_db("""
                    update app_clientprop set attrVal = 0, created = 0 
                    where componentNameId = {0} and attrName = 'IndexingV2'
                """.format(self.client.client_id))

            if self.idx_help.get_agent_indexing_version(self.client) == 'v1':
                self.log.info('Client is in Indexing V1 mode')
            else:
                raise Exception('Failed to move client to Indexing V2 mode')

            self.backupset = self.idx_tc.create_backupset('uiv2_workflow', for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name='sc_uiv2_workflow',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs['StoragePolicy']
            )

            self.log.info('********** Creating testdata **********')
            self.idx_tc.new_testdata(self.subclient.content)

            self.backupset_guid = self.backupset.guid

            self.log.info('********** Assigning schedule to the subclient **********')
            self.schedule_policy = self.commcell.schedule_policies.get(self.tcinputs.get('SchedulePolicy'))
            self.schedule_policy.update_associations([{
                'clientName': self.client.client_name,
                'instanceName': 'DefaultInstanceName',
                'appName': self.agent.agent_name,
                'backupsetName': self.backupset.backupset_name,
                'subclientName': self.subclient.subclient_name
            }], OperationType.INCLUDE)

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Run full backup in indexing v1 mode
                2) Run upgrade to indexing workflow and verify if it completes successfully.
                3) Verify entry in app_indexdbinfo table

        """

        try:

            self.idx_tc.run_backup(self.subclient, backup_level='Full', verify_backup=False)

            self.workflow.execute({
                'Agent': 'FileSystem',
                'waitInfinitelyToUpgrade': 'true',
                'ignorePreUpgradeChecks': 'false',
                'choice': 'Clients',
                'noOfThreads': '10',
                'clientGroup': '',
                'clientList': self.client.client_name
            })

            if self.idx_help.get_agent_indexing_version(self.client) == 'v1':
                raise Exception('Client is still in Indexing V1 mode even after running the workflow')
            else:
                self.log.info('********** Client is moved to Indexing V2 **********')

            self.csdb.execute("""
                select id from App_IndexDBInfo where backupSetGUID = '{0}'
            """.format(self.backupset_guid))

            if self.csdb.fetch_one_row()[0] == '':
                raise Exception('Backupset level index information is not present in App_IndexDBInfo table')
            else:
                self.log.info('********** Backupset level index is created **********')

            self.log.info('********** Testcase completed successfully **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)
