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

    get_cv_vm_client()  --  Gets the CV client and backupset object for the given VM guid

    delete_index_server_cache() --  Deletes the Index DB, logs and RFC folder from the IndexServer's index cache

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper


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
        self.name = 'Indexing - VSA - Unavailability of Index DB, logs, RFC before backup'
        self.tcinputs = {}

        self._sc_vms = None
        self._cv_vms = {}
        self._index_servers = {}

        self.storage_policy = None
        self.auto_subclient = None

    def setup(self):
        """Setup function of this test case"""

        self._sc_vms = self.subclient._get_vm_ids_and_names_dict()

        vm_guids, vm_names = self._sc_vms
        self.log.info(vm_guids)

        for vm_guid, vm_name in vm_guids.items():
            cv_vm = self.get_cv_vm_client(vm_guid)
            self.log.info(f'Source backup VM client name [{cv_vm["client"].client_name}]')

    def run(self):
        """Run function of this test case

            Steps:

                1) Delete the index DB, logs, RFC folder from the index server MA
                2) Run INC backup
                3) Repeat step 1
                4) Run INC and SFULL backup (to do restore of index logs, playback etc)
                5) Verify if backup job completes as expected and job type is correct.
                6) Repeat step 1 and do restore of the VM
                7) Repeat step 1 and do guest files restore of the VM (to do RFC restore)

        """
        backup_options = None

        try:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info('********** Running INCREMENTAL backup **********')
            self.delete_index_server_cache()
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            self.delete_index_server_cache()

            # There is a restriction with the below API where we are unable to run SYNTH_FULL without INC before/after
            # with restore validation

            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'SYNTHETIC_FULL'
            backup_options.validation = False
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Running RESTORE from SYNTHETIC FULL job **********')
            self.delete_index_server_cache()

            # Guest file restore is not supported right now from automation. Going with full VM restore
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True

            self.auto_subclient.virtual_machine_restore(vm_restore_options)

            self.log.info('********** Browse from the SYNTHETIC FULL JOB **********')
            self.delete_index_server_cache()

            for vm_guid, vm_objs in self._cv_vms.items():
                files, files_details = self.subclient.browse(vm_path=vm_guid, vm_files_browse=True)
                self.log.info(files)
                self.log.info(files_details)
                if 'archiveFileId' not in str(files_details):
                    raise Exception('Cannot get results from guest files browse')

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if backup_options is not None:
                    self.auto_subclient.cleanup_testdata(backup_options)
            except Exception as e:
                self.log.error('Got exception while trying to do cleanup [%s]', e)

    def get_cv_vm_client(self, vm_guid):
        """Gets the CV client and backupset object for the given VM guid

            Args:
                vm_guid     (str)   --  The client GUID of the VM

            Returns:
                 dict   --  The dictionary which contains all the VM's client and backupset objects.

        """

        if vm_guid in self._cv_vms:
            return self._cv_vms[vm_guid]

        self.log.info(f'Getting CV client objects for the VM [{vm_guid}]')

        self.csdb.execute(f"select name from app_client where guid = '{vm_guid}'")
        row = self.csdb.fetch_one_row()

        if not row[0]:
            raise Exception(f'Cannot get client name for the VM with guid [{vm_guid}]. Result [{row}]')

        vm_name = row[0]

        self.log.info(f'CV VM name is [{vm_name}]')
        vm_client = self.commcell.clients.get(vm_name)
        vm_agent = vm_client.agents.get('Virtual Server')
        vm_bkset = vm_agent.backupsets.get(self.backupset.backupset_name)
        vm_indexserver_client = vm_bkset.index_server

        vm_objs = {
            'client': vm_client,
            'backupset': vm_bkset,
            'indexserver_client': vm_indexserver_client,
            'indexserver_ma': self.commcell.media_agents.get(vm_indexserver_client.client_name),
            'indexserver_machine': Machine(vm_indexserver_client)
        }

        self._cv_vms[vm_guid] = vm_objs
        return vm_objs

    def delete_index_server_cache(self):
        """Deletes the Index DB, logs and RFC folder from the IndexServer's index cache"""

        for vm_guid, vm_objs in self._cv_vms.items():
            vm_name = vm_objs['client'].client_name
            backupset_guid = vm_objs['backupset'].guid
            subclient_guid = vm_objs['backupset'].subclients.get('default').subclient_guid
            indexserver_client = vm_objs['indexserver_client']
            indexserver_ma = vm_objs['indexserver_ma']
            indexserver_machine = vm_objs['indexserver_machine']
            index_cache = indexserver_ma.index_cache_path

            self.log.info(f'***** Cleaning index cache for VM [{vm_name}] *****')
            self.log.info(f'Deleting the index DB, logs & RFC from MA [{indexserver_client.client_name}]')

            self.log.info(
                f'Backupset GUID [{backupset_guid}], VM Client [{vm_name}], Subclient GUID [{subclient_guid}]')

            index_db_path = indexserver_machine.join_path(index_cache, 'CvIdxDB', backupset_guid)
            index_logs_path = indexserver_machine.join_path(index_cache, 'CvIdxLogs', '2', backupset_guid)
            rfc_path = indexserver_machine.join_path(index_cache, 'RemoteFileCache', '2', subclient_guid)

            self.log.info(f'Index DB, logs path [{index_db_path}] [{index_logs_path}] [{rfc_path}]')

            if indexserver_machine.check_directory_exists(index_db_path):
                self.log.info(f'Deleting DB [{index_db_path}]')
                indexserver_machine.remove_directory(index_db_path)

            if indexserver_machine.check_directory_exists(index_logs_path):
                self.log.info(f'Deleting logs folder [{index_logs_path}]')
                indexserver_machine.remove_directory(index_logs_path)

            if indexserver_machine.check_directory_exists(rfc_path):
                self.log.info(f'Deleting logs folder [{rfc_path}]')
                indexserver_machine.remove_directory(rfc_path)

            self.log.info('Killing IndexServer and logmanager processes')
            indexserver_machine.kill_process(process_name='cvods')
