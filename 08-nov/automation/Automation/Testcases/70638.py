# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  Initialize TestCase class

    setup()                                 --  Setup function of this test case

    run()                                   --  Run function of this test case

    verify_client_properties()              --  Verifies all the properties for the client and
                                                runs a backup

"""
import time
import datetime
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """
    This testcase verifies that all the default options for indexing are as expected whenever a
    client is newly installed and also when it's reinstalled or repaired.

    Steps:
    1) Install a client with FS packages.
    2) Verify if all the indexing default properites are set like below.
    a) client is in indexing v2 mode
    b) verify if client's indexing v2 creation time is correct.
    c) Client is set to subclient level index
    d) Index pruning settings are set to 2 cycles
    f) Run a FULL backup and confirm if indexserver association is added to app_indexdbinfo table.

    3) Deconfigure and reconfigure the client.
    4) Verify #2

    5) Repair the client.
    6) Verify #2

"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = 'Indexing - Install & resinstall Client verifications'

        self.tcinputs = {
            'InstallClientName': None,
            'InstallClientHostName': None,
            'InstallClientUserName': None,
            'InstallClientPassword': None,
            'StoragePolicy': None
        }
        self.idx_help = None
        self.client = None
        self.clientname = None
        self.agent = None
        self.installusername = None
        self.installpassword = None
        self.backupset = None
        self.subclient = None
        self.idx_tc = None
        self.cl_machine = None

    def setup(self):
        """All testcase objects have been initialized in this method"""
        self.idx_help = IndexingHelpers(self.commcell)
        self.clientname = self.tcinputs['InstallClientName']
        self.installusername = self.tcinputs['InstallClientUserName']
        self.installpassword = self.tcinputs['InstallClientPassword']

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""
        testcase_passed = False
        try:
            self.log.info('Running install job...')
            push_job = self.commcell.install_software(
                client_computers=[self.tcinputs['InstallClientHostName']],
                windows_features=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                username=self.installusername,
                password=b64encode(self.installpassword.encode()).decode()

            )
            self.log.info('Client install job: %s', push_job.job_id)
            if not push_job.wait_for_completion():
                raise Exception(
                    f'Failed to run install client job with error: {push_job.delay_reason}')
            self._log.info('Client: %s installed.', self.clientname)
            self.verify_client_properties()

            self.log.info('Releasing the Client license for client- %s', self.clientname)
            self.client.release_license()
            self.log.info('Client license is released')
            self.log.info('Waiting before reconfiguring client.')
            time.sleep(100)
            self.log.info('Reconfiguring the Client license for %s', self.clientname)
            self.client.reconfigure_client()
            self.log.info('Client license is reconfigured')
            self.verify_client_properties()

            self.log.info('** Starting Repair Install for client %s **', self.clientname)
            repair_job = self.client.repair_software(
                username=self.installusername,
                password=b64encode(self.installpassword.encode()).decode())

            if not repair_job.wait_for_completion():
                raise Exception(
                    'Failed to repair client software for %s.', self.clientname
                )
            self.log.info('Client %s is repaired successfully.', self.clientname)
            self.verify_client_properties()
            testcase_passed = True

        except Exception as exp:
            testcase_passed = False
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if testcase_passed:
                retire_job = self.client.retire()
                self.log.info('Testcase is passed and finally uninstalling client.')
                if not retire_job.wait_for_completion():
                    raise Exception(f"Uninstall job failed with error: {retire_job.delay_reason}")
                self.log.info('Client is retired finally.')
                if self.commcell.clients.has_client(self.clientname):
                    self.log.info('Deleting Client %s from commcell.', self.clientname)
                    self.commcell.clients.delete(client_name=self.clientname)
                    self.log.info('Client is deleted from commcell.')
                # Refreshing the clients associated with the commcell Object
                self.commcell.clients.refresh()
            else:
                self.log.info('Testcase is failed so client is not retired finally.')

    def verify_client_properties(self):
        """Verifies all the index properties for the client and runs a backup"""
        self.log.info('** Verifying all index properties for the client **')

        self.log.info('Refreshing Client List on the CS')
        self.commcell.refresh()
        self.client = self.commcell.clients.get(self.clientname)
        self.cl_machine = Machine(self.client)
        self.agent = self.client.agents.get('File System')
        self.idx_tc = IndexingTestcase(self)

        self.log.info('** Verifying Indexing version for the client is V2. **')
        if self.idx_help.get_agent_indexing_version(self.client) == 'v2':
            self.log.info('Client is in indexing v2 mode')
        else:
            raise Exception('Error - This testcase is only applicable to V2 indexing client.')
        client_id = self.client.client_id
        self.csdb.execute(f"""
                                select created from app_clientprop where componentNameId = 
                                '{client_id}' and attrname = 'IndexingV2'
                            """)
        result = int(self.csdb.fetch_one_row()[0])
        self.log.info('Time for creation of IndexingV2 is %s',
                      datetime.datetime.fromtimestamp(result))
        if datetime.date.today()-datetime.date.fromtimestamp(result) <= datetime.timedelta(days=1):
            self.log.info('The time for creation is verified.')
        else:
            raise Exception('ERROR-- Time for creation of Indexing V2 is incorrect.')

        self.log.info('** Checking if client is created with subclient level index **')
        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if indexing_level == 'subclient':
            self.log.info('Indexing Level is subclient level which is expected')
        else:
            raise Exception('ERROR-- Indexing level is not subclient.')

        self.backupset = self.idx_tc.create_backupset(
            name='70638_install',
            for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='install_sc1',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

        self.log.info('** Checking default pruning settings for the client. **')

        self.csdb.execute(f"""select id from APP_Application where 
                          subclientName='{self.subclient.name}'""")

        compid = self.csdb.fetch_one_row()[0]
        self.log.info('Component id for pruning data is %s', compid)
        self.csdb.execute(f"""select attrVal from APP_SubClientProp where 
                          componentNameId={compid} and attrName='IndexPruning_DBRetentionCycle'""")
        pruneprop = int(self.csdb.fetch_one_row()[0])
        if pruneprop == 2:
            self.log.info('Index Pruning is set to 2 cycles as expected.')
        else:
            raise Exception('ERROR-- Index pruning is set to %s cycles', pruneprop)

        self.log.info('************* Running backup job *************')
        self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['New', 'Full'],
            verify_backup=True
        )
        self.log.info('Full Backup Job completed successfully')

        self.log.info('** Checking Index server association for the Full job. **')
        self.csdb.execute(f"""select currentIdxServer from App_IndexDBInfo where 
                          dbName='{self.subclient.subclient_guid}'""")
        idxserver_id = self.csdb.fetch_one_row()[0]
        self.log.info('Idxserver id that is associated- %s', idxserver_id)
        if idxserver_id == '':
            raise Exception(
                'Error-- No IndexServer is associated with client')
        self.csdb.execute(f"select name from APP_Client where id={idxserver_id}")
        idxserver_name = self.csdb.fetch_one_row()[0]
        self.log.info('IndexServer [%s] is associated with subclient and present in csdb.',
                      idxserver_name)
