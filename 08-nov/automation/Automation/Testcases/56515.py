# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the workflow "Change index cache config" works as expected and verifies the configs.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import traceback
import time
import random

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase

from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """This testcase verifies that the workflow "Change index cache config" works as expected"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Workflow - Change index cache configuration'
        self.tcinputs = {
            'MediaAgent': None,
            'IndexCachePath': None
        }

        self.workflow = None
        self.old_ic_path = None
        self.new_ic_path = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:
            self.workflow = WorkflowHelper(self, 'ChangeIndexCacheConfig')
            self.media_agent = self.commcell.clients.get(self.tcinputs.get('MediaAgent'))
            self.ma_machine = Machine(self.media_agent, self.commcell)

            self.idx_help = IndexingHelpers(self.commcell)
            self.idx_tc = IndexingTestcase(self)

            self.new_ic_path = self.ma_machine.os_sep.join([
                self.tcinputs.get('IndexCachePath'), 'IC_' + str(int(time.time()))
            ])

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Get existing index cache config.
                2) Generate new index cache config to be changed.
                3) Run workflow to set the index cache config.
                4) Verify if index cache config has been changed.
                5) Verify if new index cache directory is created.

        """

        try:

            old_config = self.idx_help.get_index_cache_config(self.media_agent)
            self.log.info('Index cache config before change {0}'.format(old_config))
            self.old_ic_path = old_config.get('index_cache_path', None)

            expected_config = {
                'min_space': random.randint(10, 30) * 1024,
                'alert_space': random.randint(10, 30) * 1024,
                'age_days': random.randint(1, 30),
                'cleanup_percent': random.randint(91, 99),
                'index_cache_path': self.new_ic_path
            }

            self.log.info('Index cache config will be changed to {0}'.format(expected_config))

            self.workflow.execute({
                'clientGroupName': '',
                'clientName': {
                    'mediaAgentId': self.media_agent.client_id,
                    'mediaAgentName': self.media_agent.client_name
                },
                'UpdateProperties': 'true',
                'updateIndexCachePath': 'true',
                'newIcdPath': self.new_ic_path,
                'nParallelMigrations': '2',
                'indexRetentionDays': expected_config['age_days'],
                'freeSpaceAlert': int(expected_config['alert_space']/1024),
                'indexOfflineSpace': int(expected_config['min_space']/1024),
                'cleanupUntillSpace': 100-expected_config['cleanup_percent']
            })

            new_config = self.idx_help.get_index_cache_config(self.media_agent)
            self.log.info('Index cache config after change {0}'.format(new_config))

            self.log.info('********** Verifying if the index cache config has been changed **********')

            mismatch_info = False
            for name, value in expected_config.items():
                if name in new_config:

                    has_changed = str(new_config[name]) == str(expected_config[name])

                    if has_changed:
                        self.log.info('Index cache config [{0}] has changed - PASS'.format(name))
                    else:
                        self.log.info('Index cache config [{0}] has not changed - FAIL'.format(name))
                        mismatch_info = True

            if mismatch_info:
                raise Exception('There is a mismatch in index cache config')

            self.log.info('********** Verifying if the index cache path has been migrated **********')
            if not self.ma_machine.check_directory_exists(self.new_ic_path):
                raise Exception('The new index cache directory is not seen in the MA')
            else:
                self.log.info('New index cache directory is present in the MA')

            self.log.info('********** Testcase completed successfully **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Cleans the old index cache directory"""

        if self.status == constants.PASSED:
            try:
                self.log.info('Deleting old index cache path [%s]', self.old_ic_path)
                self.log.info('Waiting for 2 minutes for log manager process to shutdown before deleting old directory')
                time.sleep(120)
                self.ma_machine.remove_directory(self.old_ic_path)
            except Exception as e:
                self.log.error('Failed to delete old index cache directory [%s]', e)
