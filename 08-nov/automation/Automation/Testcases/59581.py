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

    start_index_server_services()   --  Starts the services on the index server machines which were stopped

    stop_index_server_services()    --  Stops the index server machine services of all the VMs involved

"""

import time

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
        self.name = 'Indexing - VSA - IndexServer is down before backup'
        self.tcinputs = {
            'IndexServer_credentials': None
        }

        self._sc_vms = None
        self._cv_vms = {}
        self._stopped_services_clients = []
        self._index_server_creds = {}

        self.auto_subclient = None

    def setup(self):
        """Setup function of this test case"""

        self._sc_vms = self.subclient._get_vm_ids_and_names_dict()

        vm_guids, vm_names = self._sc_vms
        self.log.info(vm_guids)

        for vm_guid, vm_name in vm_guids.items():
            cv_vm = self.get_cv_vm_client(vm_guid)
            self.log.info(f'Source backup VM client name [{cv_vm["client"].client_name}]')

        self.prepare_index_server_creds()

    def run(self):
        """Run function of this test case

            Steps:

                1) Run SFULL first to fix the indexserver for the VM client
                2) Stop the index server services
                3) Run INC backup and verify if the backup type is INC and job completes successfully
                4) Start the index server services
                5) Query CS DB and verify if RFC afile is backed up
                6) Do guest files browse and verify if results are obtained.

        """
        backup_options = None

        try:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'SYNTHETIC_FULL'
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Stopping IndexServer services before backup **********')
            self.stop_index_server_services()

            self.log.info('********** Running INCREMENTAL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Checking if RFC afile is created **********')
            query = f'''select id from JMJobDataLink link
                join archFile afile on afile.jobId = link.childJobId
                where link.parentJobId = '{self.auto_subclient.backup_job.job_id}' and afile.fileType = 7'''

            self.csdb.execute(query)

            self.log.info(f'Query result [{self.csdb.rows}]. Query [{query}]')
            if not self.csdb.rows[0][0]:
                raise Exception(f'RFC afile is not created')

            self.log.info('RFC afile is created')

            self.log.info('********** Starting IndexServer services **********')
            self.start_index_server_services()

            self.log.info('********** Guest files browse of latest cycle **********')
            for vm_guid, vm_objs in self._cv_vms.items():
                files, files_details = self.subclient.browse(vm_path=vm_guid, vm_files_browse=True)
                self.log.info(files)
                self.log.info(files_details)
                if 'archiveFileId' not in str(files_details):
                    raise Exception('Cannot get results from guest files browse')

            self.log.info('Successfully did guest files browse')

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.start_index_server_services()

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

    def prepare_index_server_creds(self):
        """Prepares the index server machine credentials from the input config"""

        index_servers = self.tcinputs.get('IndexServer_credentials').split(';')
        for index_server_prop in index_servers:
            props = index_server_prop.split(',')
            if len(props) != 3:
                raise Exception(
                    'Please provide index server creds in format <name>,username,password;<name2>,username,password')

            self._index_server_creds[props[0]] = {
                'username': props[1],
                'password': props[2]
            }

        self.log.info(f'Index server credentials [{self._index_server_creds}]')

    def start_index_server_services(self):
        """Starts the services on the index server machines for which services were stopped"""

        for indexserver in self._stopped_services_clients:
            try:
                self.log.info(f'Starting service for index server client [{indexserver.client_name}]')

                if indexserver.client_name not in self._index_server_creds:
                    self.log.error('Cannot start services as username/password is not set for this machine')
                    continue

                indexserver_machine = Machine(
                    machine_name=indexserver.client_hostname,
                    username=self._index_server_creds[indexserver.client_name]['username'],
                    password=self._index_server_creds[indexserver.client_name]['password']
                )
                indexserver_machine.restart_all_cv_services()

            except Exception as exp:
                raise Exception(f'Failed to start services on the index server client [{exp}]')

        time.sleep(30)

    def stop_index_server_services(self):
        """Stops the index server machine services of all the VMs involved"""

        for vm_guid, vm_objs in self._cv_vms.items():
            vm_name = vm_objs['client'].client_name
            indexserver_client = vm_objs['indexserver_client']

            self.log.info('IndexServer is [%s] for [%s]', indexserver_client.client_name, vm_name)
            self.log.info('Stopping services on IndexServer MA [%s] [%s]',
                          indexserver_client.client_name, indexserver_client.instance)
            indexserver_client.stop_service(service_name=f'GxCVD({indexserver_client.instance})')
            self._stopped_services_clients.append(indexserver_client)
