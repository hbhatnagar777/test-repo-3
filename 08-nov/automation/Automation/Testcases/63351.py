# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies if extent validation is made during VSA backup job

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  Run function of this test case

    set_content()           --  Copies the subclient content and sets it for another subclient

    delete_index()          --  Deletes index DB, logs for the all the VMs

    run_backup()            --  Runs a backup job on the virtual server client

    run_restore()           --  Runs and verifies VSA restore job

    backup_skipped_extents()    --  Checks logs to see if the extents are missed by vsbkp process

    check_missing_extents_identified()  --  Checks logs to see if the missing extents are identified

    verify_extent_bitmap()      --  Checks if the extent bitmap file is present in the index DB

"""

from cvpysdk.constants import VSAObjects

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper

from Indexing.validation.vsa_features import VSAFeatures
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


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
        self.name = 'Indexing - VSA - Extent validation'
        self.tcinputs = {
            'StoragePolicy': None,
            'CopySubclientContentFrom': None,
            'ProxyClient': None,
            'MissingExtentsDir': None
            # 'TestdataSize': None # Size of the testdata in KB. Default: 1024
        }

        self.auto_subclient = None
        self.idx_vsa = None
        self.storage_policy = None
        self.proxy_client = None
        self.proxy_machine = None

    def setup(self):
        """Setup function of this test case"""

        if '/' not in self.tcinputs.get('CopySubclientContentFrom'):
            raise Exception('Invalid value for CopySubclientContentFrom. Format <backupsetname>/<subclientname>')

        self.proxy_client = self.commcell.clients.get(self.tcinputs.get('ProxyClient'))
        self.proxy_machine = Machine(self.proxy_client)
        self.cl_machine = self.proxy_machine

        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)

        backupset_name = '63351_extent_valid'

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        if self.agent.backupsets.has_backupset(backupset_name):
            self.log.info('Backupset [%s] already exists. Deleting it', backupset_name)
            self.agent.backupsets.delete(backupset_name)

        self.log.info('Creating backupset [%s]', backupset_name)
        self.backupset = self.agent.backupsets.add(backupset_name)

        self.log.info('Getting default subclient')
        self.subclient = self.backupset.subclients.get('default')
        self.subclient.storage_policy = self.tcinputs.get('StoragePolicy')

        self.log.info('Setting content for the subclient')
        self.set_content()

        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
        self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

        self.idx_vsa = VSAFeatures(self.auto_subclient, self)

        self.testdata_size = self.tcinputs.get('TestdataSize', 1024)

    def run(self):
        """Run function of this test case

            Steps:
                1) Set registry key to not backup certain extents
                2) Run FULL backup and verify extents are missed to backup
                3) Run INC backup and verify extents are missed to backup
                4) Start synthetic full backup. Job should fail with proper JPR
                5) Remove registry key set
                6) Run INC backup. Verify extents are not skipped and skipped extents are backed up.
                7) Run and verify restore job
                8) Run synthetic full backup again
                9) Run INC backup
                10) Delete index DB
                11) Run INC and restore again.

        """
        self.log.info('***** Setting sDoNotBackupExtentsFolderPath registry key on proxy *****')
        self.proxy_machine.create_registry(
            'VirtualServer', 'sDoNotBackupExtentsFolderPath',
            self.tcinputs.get('MissingExtentsDir'), 'String'
        )

        self.log.info('********** Running FULL backup **********')
        self.run_backup('FULL')

        if not self.backup_skipped_extents():
            raise Exception('Extents are not missed though registry key is set')
        self.log.info('Extents are missed to backup as expected since registry key is set')

        self.idx_vsa.initialize_vms(collect_vm_info=False)
        self.idx_vsa.initialize_index_dbs()

        self.verify_extent_bitmap()

        self.log.info('********** Running INCREMENTAL 1 backup **********')
        self.run_backup('INCREMENTAL')
        self.check_missing_extents_identified()

        if not self.backup_skipped_extents():
            raise Exception('Extents are not missed though registry key is set')
        self.log.info('Extents are missed to backup as expected since registry key is set')
        self.log.info('Note: INC job will still skip backing up the missing extents since registry key is set')

        self.log.info('********** Running SYNTHETIC FULL backup **********')
        sfull_job = self.subclient.backup('SYNTHETIC_FULL')
        self.log.info('Started synthetic full job [%s]', sfull_job.job_id)
        if sfull_job.wait_for_completion():
            raise Exception('Synthetic full job completed with missing extents')

        # JPR is set on the parent job
        self.log.info('Synthetic full job [%s] failed as expected', sfull_job.job_id)
        self.log.info('JPR [%s]', sfull_job.pending_reason)
        if 'Mismatch detected in block'.lower() not in sfull_job.pending_reason.lower():
            raise Exception('Synthetic full backup does not have the JPR as expected')

        self.log.info('***** Deleting sDoNotBackupExtentsFolderPath registry key on proxy *****')
        self.proxy_machine.remove_registry('VirtualServer', 'sDoNotBackupExtentsFolderPath')

        self.log.info('********** Running INCREMENTAL 2 backup **********')
        self.run_backup('INCREMENTAL')
        self.check_missing_extents_identified()

        if self.backup_skipped_extents(attempts=5):
            raise Exception('Extents are missed without any registry key set')
        self.log.info('INC job backed up the missing the extents')

        self.verify_extent_bitmap()

        self.log.info('********** Running RESTORE 1 **********')
        self.run_restore()

        self.log.info('********** Running SYNTHETIC FULL backup AGAIN **********')
        self.run_backup('SYNTHETIC_FULL')

        self.log.info('********** Running INCREMENTAL 3 backup **********')
        self.run_backup('INCREMENTAL')

        try:
            self.check_missing_extents_identified(attempts=5)
        except Exception as e:
            self.log.error('Missing extents are NOT FOUND [%s]', e)
        else:
            raise Exception('Missing extents are FOUND which is not expected')

        self.delete_index()

        self.log.info('********** Running INCREMENTAL 4 backup **********')
        self.run_backup('INCREMENTAL')

        try:
            self.check_missing_extents_identified(attempts=5)
        except Exception as e:
            self.log.error('Missing extents are NOT FOUND [%s]', e)
        else:
            raise Exception('Missing extents are FOUND which is not expected')

        self.log.info('********** Running RESTORE 2 **********')
        self.run_restore()

    def set_content(self):
        """Copies the subclient content and sets it for another subclient"""

        # Setting dummy content to create the property in the subclient prop table
        self.subclient.content = [
            [
                {
                    'type': VSAObjects.VMName,
                    'display_name': '_dummy_vm_'
                }
            ]
        ]

        copy_subclient_ip = self.tcinputs.get('CopySubclientContentFrom').split('/')
        copy_backupset = self.instance.backupsets.get(copy_subclient_ip[0])
        copy_subclient = copy_backupset.subclients.get(copy_subclient_ip[1])

        query = f'''
        update APP_SubClientProp set attrVal = (select top 1 attrVal 
        from APP_SubClientProp where componentNameId='{copy_subclient.subclient_id}' and 
        attrName = 'Virtual Server Dyanimc Content' and modified = 0) 
        where componentNameId = '{self.subclient.subclient_id}' and attrName = 'Virtual Server Dyanimc Content' 
        and modified = 0
        '''

        self.idx_tc.options_help.update_commserve_db(query, log_query=True)
        self.subclient.refresh()

    def delete_index(self):
        """Deletes index DB, logs for the all the VMs"""

        for vm_name, vm_info in self.idx_vsa.vms.items():
            self.log.info('***** Deleting index for [%s] *****', vm_name)
            vm_db = self.idx_vsa.vms[vm_name]['index_db']

            self.log.info('Deleting DB')
            vm_db.delete_db()

            try:
                self.log.info('Restarting IndexServer services [%s]', vm_db.index_server.client_name)
                vm_db.index_server.restart_services()
            except Exception as e:
                self.log.error('Got exception while trying to restart services [%s]', e)

    def run_backup(self, backup_type):
        """Runs a backup job on the virtual server client

            Args:
                backup_type     (str)       --      The type of backup to run

            Returns:
                None

        """

        backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
        backup_options.backup_type = backup_type
        backup_options.advance_options['testdata_size'] = self.testdata_size
        skip_discovery = False

        # Do not run INC before/after synthetic job and do not create testdata before backup
        if backup_type.lower() == 'synthetic_full':
            backup_options.run_incr_before_synth = False
            backup_options.incr_level = ''
            skip_discovery = True

        self.auto_subclient.backup(backup_options, skip_discovery=skip_discovery)

    def run_restore(self):
        """Runs and verifies VSA restore job"""

        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_subclient, self)
        vm_restore_options.power_on_after_restore = True
        vm_restore_options.unconditional_overwrite = True

        self.auto_subclient.virtual_machine_restore(vm_restore_options)

    def backup_skipped_extents(self, attempts=20):
        """Checks logs to see if the extents are missed by vsbkp process

            Args:
                attempts        (int)   --      Number of attempts to look at the logs

            Returns:
                (bool)      --      True if logs are identified, False otherwise

        """

        log_lines = self.idx_tc.check_log_line(
            self.proxy_client, self.proxy_machine, 'vsbkp.log',
            [self.auto_subclient.backup_job.job_id, 'has been skipped from backup per registry settings'],
            attempts=attempts
        )

        if not isinstance(log_lines, list):
            self.log.info('No log lines found')
            self.log.info(log_lines)

        return log_lines

    def check_missing_extents_identified(self, attempts=20):
        """Checks logs to see if the missing extents are identified"""

        for vm_name in self.idx_vsa.vms:
            self.log.info('***** Checking missing block log line for VM [%s] *****', vm_name)
            log_lines = self.idx_tc.check_log_line(
                self.proxy_client, self.proxy_machine, 'vsbkp.log',
                [self.auto_subclient.backup_job.job_id, vm_name, 'Disk', 'is missing', 'blocks'],
                attempts=attempts
            )

            if not log_lines:
                raise Exception('Missing extents are not detected by incremental job')

            self.log.info('Missing extents are detected by the INCREMENTAL job')

    def verify_extent_bitmap(self):
        """Checks if the extent bitmap file is present in the index DB"""

        for vm_name, vm_info in self.idx_vsa.vms.items():
            self.log.info('***** Getting extent bitmap files for [%s] *****', vm_name)
            vm_db = self.idx_vsa.vms[vm_name]['index_db']
            extent_view_path = vm_db.isc_machine.join_path(vm_db.db_path, 'EXTENTVIEW')

            self.log.info('Scanning path [%s]', extent_view_path)
            extent_view_items = vm_db.isc_machine.scan_directory(extent_view_path)
            found_bitmap = False

            if not extent_view_items:
                raise Exception('Unable to get contents of the index DB')

            for item in extent_view_items:
                if 'ExtentBitmap' in item['path']:
                    found_bitmap = True
                    self.log.info('Found bitmap')
                    self.log.info(item)

            if not found_bitmap:
                raise Exception('ExtentBitmap file not found in the index')

    def tear_down(self):
        """Tear down routine"""

        if self.proxy_machine:
            try:
                self.log.info('***** Deleting sDoNotBackupExtentsFolderPath registry key on proxy *****')
                self.proxy_machine.remove_registry('VirtualServer', 'sDoNotBackupExtentsFolderPath')
            except Exception as e:
                self.log.error('Failed to delete sDoNotBackupExtentsFolderPath at the end of the run [%s]', e)
