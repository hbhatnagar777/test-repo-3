# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object

    setup()             --  Setup function for this testcase

    tear_down()         --  tear down method for this testcase

    perform_install()   --  Method to perform push install

    check_permissions() --  Method to check if permission of CV directories are properly set

    setup_instance()    --  Method to setup sybase instance

    run_backup()        --  Method to run backup and restore

    run()               --  Main function for test case execution

Example Input:

    "62820":
            {
                    'InstanceName': "",
                    'ServerName': "",
                    'SybaseASE': "",
                    'SybaseOCS': "",
                    'SybaseHome': "",
                    'ConfigFilePath': "",
                    'SharedMemoryDirectory': "",
                    'SybaseUnixUser': "",
                    'DatabaseUser': "",
                    'DatabasePassword': "",
                    'storagePolicy': ""
            }

"""
from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database import dbhelper
from Database.SybaseUtils.sybasehelper import SybaseHelper, SybaseCVHelper

class TestCase(CVTestCase):
    """Class for executing Sybase push install without DB group"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Sybase push install without DB group"
        self.sybase_helper = None
        self.install_helper = None
        self.machine_object = None
        self.client_hostname = None
        self.install_success_flag = False
        self.client = None
        self.config_json = config.get_config()
        self.tcinputs = {
            'InstanceName': None,
            'ServerName': None,
            'SybaseASE': None,
            'SybaseOCS': None,
            'SybaseHome': None,
            'ConfigFilePath': None,
            'SharedMemoryDirectory': None,
            'SybaseUnixUser': None,
            'DatabaseUser': None,
            'DatabasePassword': None,
            'storagePolicy': None
        }
        self.subclient = None
        self.agent = None
        self.instance = None
        self.dbhelper_object = None
        self.instance_created = None

    def setup(self):
        """ setup function for this testcase """
        self.dbhelper_object = dbhelper.DbHelper(self.commcell)
        username = self.config_json.Install.unix_client.machine_username
        password = self.config_json.Install.unix_client.machine_password
        self.client_hostname = self.config_json.Install.unix_client.machine_host
        if username == '' or password == '' or self.client_hostname == '':
            raise Exception('Please provide hostname/username/Password in config.json(Install.unix_client)')
        self.machine_object = Machine(self.client_hostname, self.commcell, username, password)
        self.install_helper = InstallHelper(self.commcell, self.machine_object)

    def tear_down(self):
        """ Tear down function to uninstall the client """
        if self.instance_created:
            self.log.info("Deleting the instance")
            self.agent.instances.delete(self.tcinputs['InstanceName'])
        if self.install_success_flag:
            self.log.info("Uninstalling the client")
            self.install_helper.uninstall_client(True)

    def perform_install(self):
        """ Method to perform push install """
        self.dbhelper_object.install_db_agent(
            'SYBASE', self.machine_object, self.tcinputs['storagePolicy'])
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()

    def check_permissions(self):
        """ Method to check if permission of CV directories are properly set """
        self.client = self.commcell.clients.get(self.client_hostname)
        self.dbhelper_object.check_permissions_after_install(self.client, "sybase")

    def setup_instance(self):
        """ Method to set up sybase instance """
        self.log.info("Creating instance")
        self.agent = self.client.agents.get('Sybase')
        sybase_options = {
            'instance_name': self.tcinputs['InstanceName'],
            'sybase_ocs': self.tcinputs['SybaseOCS'],
            'sybase_ase': self.tcinputs['SybaseASE'],
            'backup_server': self.tcinputs['ServerName'],
            'sybase_home': self.tcinputs['SybaseHome'],
            'config_file': self.tcinputs['ConfigFilePath'],
            'enable_auto_discovery': True,
            'shared_memory_directory': self.tcinputs['SharedMemoryDirectory'],
            'storage_policy': self.tcinputs['storagePolicy'],
            'sa_username': self.tcinputs['DatabaseUser'],
            'sa_password': self.tcinputs['DatabasePassword'],
            'localadmin_username': self.tcinputs['SybaseUnixUser']
        }
        self.agent.instances.add_sybase_instance(sybase_options)
        self.instance_created = True
        self.log.info("Instance got created")
        self.agent.instances.refresh()
        self.instance = self.agent.instances.get('VEDANTSYBASE')
        backupset = self.instance.backupsets.get('defaultDummyBackupSet')
        self.subclient = backupset.subclients.get('default')
        self.subclient.refresh()

    def run_backup_restore(self):
        """ Method to run backup and restore """
        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        sybase_cv_helper = SybaseCVHelper(self.sybase_helper)
        self.log.info("Running Full Backup")
        full_job = sybase_cv_helper.backup_and_validation(
            self.subclient, backup_type='full')
        self.log.info("Full job : %s completed", full_job.job_id)

    def run(self):
        """ Main function for test case execution """

        try:
            self.perform_install()
            self.check_permissions()
            self.setup_instance()
            self.run_backup_restore()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
