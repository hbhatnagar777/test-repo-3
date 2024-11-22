# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase

from Indexing.testcase import IndexingTestcase

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
        self.name = 'Indexing - Change of IndexServer to MA Other than Datapath'

        self.storage_policy = None
        self.idx_tc = None
        self.index_server = None
        self.cl_machine = None

        self.tcinputs = {
            'StoragePolicy': None,
            'IndexServer': None,
            'ClientName': None,
            'AgentName': None,
        }


    """Setup function of this test case"""
    def setup(self):
        try:
            self.log.info('Started setup %s testcase', self.id)
            self.index_server = self.commcell.clients.get(self.tcinputs.get('IndexServer'))

            # Set EnableIdxSrvrSwitch : 0
            self.log.info('Setting EnableIdxSrvrSwitch to 0')
            self.commcell.add_additional_setting('CommServDB.GxGlobalParam', 'EnableIdxSrvrSwitch', 'INTEGER', '0')

            self.storage_policy = self.commcell.storage_policies.get(
                self.tcinputs.get('StoragePolicy'))

            # Is IndexServer IN DataPath?
            query = "SELECT * FROM archGroupCopy as agc JOIN MMDataPath as mmdp ON agc.id = mmdp.CopyId WHERE agc.archGroupID = " + self.storage_policy.storage_policy_id + " AND mmdp.HostClientId = " + self.index_server.client_id
            self.log.debug(query)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()

            if rows == [['']]:
                self.log.info("Index Server NOT found in DataPath")
            else:
                raise Exception("Index Server FOUND in DataPath")

            self.cl_machine = Machine(self.client, self.commcell)
            self.idx_tc = IndexingTestcase(self)
            self.backupset = self.idx_tc.create_backupset('idx_outside_datapath_56562')
            self.subclient = self.idx_tc.create_subclient(
                name="56562",
                backupset_obj=self.backupset,
                storage_policy=self.storage_policy.name
            )
            self.idx_tc.new_testdata(self.subclient.content)

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    """Run function of this test case"""
    def run(self):
        try:
            self.log.info('Started executing %s testcase' % self.id)

            # Start full backup
            self.log.info("Starting full backup for 56562 Subclient")
            job = self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=False)

            # Default Index Server
            self.subclient.refresh()
            default_index = self.subclient.index_server
            self.log.info('Default Index Server: [%s]', self.subclient.index_server.name)

            # Change Index Server
            # CS DB Update App_IndexDBInfo
            # UPDATE App_IndexDBInfo set currentIdxServer = 4 WHERE dbName = 'guid'
            query = "UPDATE App_IndexDBInfo SET currentIdxServer = "+ self.index_server.client_id +" WHERE dbName = '" + self.subclient.subclient_guid + "'"
            self.log.debug('Query: %s', query)
            self.idx_tc.options_help.update_commserve_db(query)

            # Check Index Server
            self.subclient.refresh()
            index_server = self.subclient.index_server.name
            self.log.info('Index Server: [%s]', index_server)

            # Run Full / Synth / Browse (verify_backup = true)
            job = self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=False)
            job = self.idx_tc.run_backup(self.subclient, 'Synthetic_full', verify_backup=True)

            self.subclient.refresh()
            index_server2 = self.subclient.index_server.name
            if index_server == index_server2:
                self.log.info('PASS: Index Server stayed the same! Was [%s] is [%s]' % (index_server, index_server2))
            else:
                raise Exception("Index Server changed during backup! Was [%s] is [%s]" % (index_server, index_server2))

            # Remove additional settings
            self.log.info('Removing EnableIdxSrvrSwitch')
            self.commcell.delete_additional_setting('CommServDB.GxGlobalParam', 'EnableIdxSrvrSwitch')

            # Revert to default Index Server
            self.log.info('Setting Index Server back to default index server [%s]',
                default_index.name)
            query = "UPDATE App_IndexDBInfo SET currentIdxServer = "+ default_index.client_id + " WHERE dbName = '" + self.subclient.subclient_guid + "'"
            self.log.debug('Query: %s', query)
            self.idx_tc.options_help.update_commserve_db(query)
            self.subclient.refresh()

            self.log.info('Verifying Browse / Restore and Index Server switch')
            self.idx_tc.run_backup(self.subclient, 'Synthetic_full', verify_backup=True)
            self.idx_tc.verify_browse_restore(self.backupset, options=None)

            self.subclient.refresh()
            new_index_server = self.subclient.index_server.name
            if new_index_server != index_server2:
                self.log.info('PASS: Index Server is in data path: [%s]', self.subclient.index_server.name)
            else:
                raise Exception('FAIL: Index Server [%s] is not in data path', new_index_server)

        except Exception as exp:
            self.log.exception(exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    """Tear down function of test case"""
    def tear_down(self):
        self.log.info('Started teardown %s testcase', self.id)
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
