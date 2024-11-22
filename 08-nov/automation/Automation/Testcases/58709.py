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

    delete_index_second_copy()  --  Deletes the index cache DB and logs in the secondary copy MA

    get_cv_vm_client()  --  Gets the CV client and backupset object for the given VM guid

    validate_restore_2nd_copy() --  Verifies if the VM is restored from secondary copy by accessing the testdata
    folder created as part of INC 1 job

    tear_down()     --  tear down function of this test case

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
        self.name = 'Indexing - VSA - Browse and restore of VM from secondary copy'
        self.tcinputs = {
            'IndexServer_username': None,
            'IndexServer_password': None,
            'SecondaryCopyName': None
        }

        self._sc_vms = None
        self._cv_vms = {}
        self._stopped_services_clients = []

        self.storage_policy = None
        self.secondary_copy = None
        self.sec_copy_precedence = None
        self.sec_ma = None
        self.sec_ma_client = None
        self.sec_ma_machine = None
        self.sec_ma_indexcache = None
        self.auto_subclient = None

    def setup(self):
        """Setup function of this test case"""
        self.storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
        secondary_copy_name = self.tcinputs.get('SecondaryCopyName')

        if not self.storage_policy.has_copy(secondary_copy_name):
            raise Exception(f'Secondary copy [{secondary_copy_name}] does not exits in the storage policy')

        self.secondary_copy = self.storage_policy.get_copy(secondary_copy_name)
        self.sec_copy_precedence = self.secondary_copy.get_copy_Precedence()
        self.log.info('Secondary copy [%s] precedence is [%s]', secondary_copy_name, self.sec_copy_precedence)

        self.sec_ma_client = self.commcell.clients.get(self.secondary_copy.media_agent)
        self.sec_ma = self.commcell.media_agents.get(self.secondary_copy.media_agent)
        self.sec_ma_machine = Machine(self.sec_ma_client)
        self.sec_ma_indexcache = self.sec_ma.index_cache_path

        self._sc_vms = self.subclient._get_vm_ids_and_names_dict()

        vm_guids, vm_names = self._sc_vms
        self.log.info(vm_guids)

        for vm_guid, vm_name in vm_guids.items():
            cv_vm = self.get_cv_vm_client(vm_guid)
            self.log.info(f'Source backup VM client name [{cv_vm["client"].client_name}]')

        self.delete_index_second_copy()

    def run(self):
        """Run function of this test case

            Steps:

                1) Run INC backup for the Vcenter subclient
                2) Note down the testdata folder created for this job
                3) Run AUX copy
                4) Clear previous testdata and run another INC job
                5) Run SFULL job to create a new cycle
                5) Stop the services on indexsserver MA
                6) Run restore from secondary copy
                7) Verify if VM is restored from 2nd copy by looking at testdata folder
                8) Restart indexserver services

        """
        backup_options = None

        try:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info('********** Running 1st INCREMENTAL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'

            self.auto_subclient.backup(backup_options)
            inc1_job = self.auto_subclient.backup_job
            inc1_job_folder = self.auto_subclient.timestamp

            self.log.info(f'INC 1 job [{inc1_job}]')
            self.log.info(f'INC 1 had backed up folder [{inc1_job_folder}]')

            self.log.info('********** Running AUX copy **********')
            aux_copy_job = self.storage_policy.run_aux_copy()
            self.log.info(f'Waiting for AuxCopy job [{aux_copy_job.job_id}] to complete')
            if not aux_copy_job.wait_for_completion():
                raise Exception('AuxCopy failed with error: {0}'.format(aux_copy_job.delay_reason))

            self.log.info('********** Running 2nd INCREMENTAL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.validation = False
            backup_options.validation_skip_all = False
            backup_options.backup_type = 'INCREMENTAL'

            self.auto_subclient.backup(backup_options)
            inc2_job = self.auto_subclient.backup_job
            inc2_job_folder = self.auto_subclient.timestamp

            self.log.info(f'INC 2 job [{inc2_job}]')
            self.log.info(f'INC 2 backed up folder [{inc2_job_folder}]')

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'SYNTHETIC_FULL'
            backup_options.incr_level = ''
            backup_options.validation = False

            self.auto_subclient.backup(backup_options)

            self.log.info('********** Stopping services on IndexServer MAs **********')
            vm_guids, vm_names = self._sc_vms
            for vm_guid, vm_name in vm_guids.items():
                cv_vm = self.get_cv_vm_client(vm_guid)
                indexserver_client = cv_vm['backupset'].index_server

                self.log.info(f'Stopping services on IndexServer MA [{indexserver_client.client_name}]')
                self._stopped_services_clients.append(indexserver_client)

                indexserver_client.stop_service(service_name='GxCVD(Instance001)')

            self.log.info('********** Running RESTORE from copy precedence [%s] **********', self.sec_copy_precedence)

            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.copy_precedence = self.sec_copy_precedence

            self.auto_subclient.virtual_machine_restore(vm_restore_options)

            self.log.info('********** VALIDATION - Checking if VM is restored from secondary copy **********')
            self.validate_restore_2nd_copy(vm_restore_options, inc1_job_folder)

            self.log.info("Successfully restored VM from secondary copy and validated")

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            for indexserver in self._stopped_services_clients:
                try:
                    self.log.info(f'Starting service for index server client [{indexserver.client_name}]')

                    indexserver_machine = Machine(
                        machine_name=indexserver.client_hostname,
                        username=self.tcinputs.get('IndexServer_username'),
                        password=self.tcinputs.get('IndexServer_password')
                    )
                    indexserver_machine.restart_all_cv_services()

                except Exception as exp:
                    self.log.error(f'Failed to start services on the index server client [{exp}]')

            try:
                if backup_options is not None:
                    self.auto_subclient.cleanup_testdata(backup_options)
            except Exception as e:
                self.log.error('Got exception while trying to do cleanup [%s]', e)

    def delete_index_second_copy(self):
        """Deletes the index cache DB and logs in the secondary copy MA"""

        self.log.info(f'***** Deleting the index DB and logs from MA [{self.sec_ma_client.client_name}] *****')

        for vm_guid, vm_objs in self._cv_vms.items():
            client = vm_objs['client'].client_name
            backupset_guid = vm_objs['backupset'].guid
            self.log.info(f'Backupset GUID [{backupset_guid}], VM Client [{client}]')

            index_db_path = self.sec_ma_machine.join_path(self.sec_ma_indexcache, 'CvIdxDB', backupset_guid)
            index_logs_path = self.sec_ma_machine.join_path(self.sec_ma_indexcache, 'CvIdxLogs', '2', backupset_guid)

            self.log.info(f'Index DB, logs path [{index_db_path}] [{index_logs_path}]')

            if self.sec_ma_machine.check_directory_exists(index_db_path):
                self.log.info(f'Deleting DB [{index_db_path}]')
                self.sec_ma_machine.remove_directory(index_db_path)

            if self.sec_ma_machine.check_directory_exists(index_logs_path):
                self.log.info(f'Deleting logs folder [{index_logs_path}]')
                self.sec_ma_machine.remove_directory(index_logs_path)

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

        vm_objs = {
            'client': vm_client,
            'backupset': vm_bkset
        }

        self._cv_vms[vm_guid] = vm_objs
        return vm_objs

    def validate_restore_2nd_copy(self, restore_options, inc1_job_folder):
        """Verifies if the VM is restored from secondary copy by accessing the testdata folder created as
        part of INC 1 job

            Args:
                restore_options     (obj)   --  The OptionsHelper.FullVMRestoreOptions object for which restore started

                inc1_job_folder     (str)   --  The timestamp of the INC1 testdata

        """

        dest_vms = restore_options.dest_client_hypervisor.get_all_vms_in_hypervisor()
        folder_verified = False

        for vm_name in self.auto_subclient.vm_list:
            dest_vm_name = 'del' + vm_name
            self.log.info(f'Validating for source VM [{vm_name}]')
            self.log.info(f'Validating for destination VM [{dest_vm_name}]')

            if dest_vm_name not in dest_vms:
                raise Exception('VM not found in the destination restored host')

            dest_vm_obj = restore_options.dest_client_hypervisor.to_vm_object(dest_vm_name)
            dest_vm_obj.update_vm_info('All', os_info=True, force_update=True)

            for drive in dest_vm_obj.drive_list.values():
                self.log.info(f'Drive [{drive}]')
                testdata_path = dest_vm_obj.machine.join_path(drive, 'INCREMENTAL', 'TestData')
                self.log.info(f'Looking for folder under directory in restored VM [{testdata_path}]')

                all_items = dest_vm_obj.machine.get_folder_or_file_names(testdata_path, filesonly=False)
                self.log.info(f'All files/folders in testdata folder [{all_items}]')

                if inc1_job_folder not in all_items:
                    raise Exception('Directory is not present in the restored VM')

                folder_verified = True

        if folder_verified:
            self.log.info('Verified - VM is restored from 2nd copy')
        else:
            raise Exception('Unable to validate the restored VM')

    def tear_down(self):
        """Tear down function of this test case"""
        pass
