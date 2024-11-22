# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object

    setup()             --  Setup function for this testcase

    tear_down()         --  tear down method for this testcase

    perform_install()   --  Method to perform push install

    check_permissions() --  Method to check if permission of CV directories are properly set

    setup_instance()    --  Method to setup informix instance

    run_backup_restore()--  Method to run backup and restore

    run()               --  Main function for test case execution


Example Input:

    "62789": {
                    "InformixDatabaseServerName": "ol_informix1210",
                    "InformixDatabaseOnConfigFileName": "onconfig.ol_informix1210",
                    "InformixDatabaseSqlHostFileLocation": "/opt/Informix_Software_Bundle/etc/sqlhosts.ol_informix1210",
                    "InformixDirectory": "/opt/Informix_Software_Bundle",
                    "StoragePolicyName": "CS_POLICY",
                    "InformixDatabaseUserName": "informix",
                    "InformixDatabasePassword":"",
                    "InformixServiceName": "9088"
                }

"""
from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing Informix push install without DB group"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()

        self.name = "Informix push install without DB group"
        self.informix_helper_object = None
        self.install_helper = None
        self.machine_object = None
        self.client_hostname = None
        self.install_success_flag = False
        self.client = None
        self.config_json = config.get_config()
        self.tcinputs = {
            'InformixDatabaseServerName': None,
            'InformixDatabaseOnConfigFileName': None,
            'InformixDatabaseSqlHostFileLocation': None,
            'InformixDirectory': None,
            'StoragePolicyName': None,
            'InformixDatabaseUserName': None,
            'InformixDatabasePassword':None,
            'InformixServiceName': None
        }
        self.subclient = None
        self.instance_object = None
        self.dbhelper_object = None


    def setup(self):
        """setup function for this testcase"""
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
        if self.install_success_flag:
            self.install_helper.uninstall_client(True)

    def perform_install(self):
        """ Method to perform push install """
        self.dbhelper_object.install_db_agent(
            'INFORMIX', self.machine_object, self.tcinputs['StoragePolicyName'])
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()

    def check_permissions(self):
        """ Method to check if permission of CV directories are properly set """
        self.client = self.commcell.clients.get(self.client_hostname)
        self.dbhelper_object.check_permissions_after_install(self.client, "informix")

    def setup_instance(self):
        """ Method to setup informix instance """
        agent = self.client.agents.get('informix')
        informix_options = {
            'instance_name': self.tcinputs['InformixDatabaseServerName'],
            'onconfig_file': self.tcinputs['InformixDatabaseOnConfigFileName'],
            'sql_host_file': self.tcinputs['InformixDatabaseSqlHostFileLocation'],
            'informix_dir': self.tcinputs['InformixDirectory'],
            'user_name': self.tcinputs['InformixDatabaseUserName'],
            'domain_name': '',
            'password': self.tcinputs['InformixDatabasePassword'],
            'storage_policy': self.tcinputs['StoragePolicyName'],
            'description': 'created from automation'
        }
        self.log.info("Informix Option JSON for Instance creation: %s", informix_options)
        self.instance_object = agent.instances.add_informix_instance(informix_options)
        self.log.info("Instance created")
        backupset = self.instance_object.backupsets.get('default')
        self.subclient = backupset.subclients.get('default')
        self.log.info("Modifying the log backup policy for instance")
        self.instance_object.log_storage_policy_name = self.tcinputs['StoragePolicyName']

    def run_backup_restore(self):
        """ Method to run backup and restore """
        self.log.info("Setting the backup mode of subclient to Entire Instance")
        self.subclient.backup_mode = "Entire_Instance"
        self.dbhelper_object.run_backup(self.subclient, "FULL")
        informix_helper_object = InformixHelper(
            self.commcell,
            self.instance_object,
            self.subclient,
            self.client.client_hostname,
            self.instance_object.instance_name,
            self.instance_object.informix_user,
            self.tcinputs['InformixDatabasePassword'],
            self.tcinputs['InformixServiceName'])
        informix_helper_object.stop_informix_server()
        ####################### Running restore ###########################
        db_space_list = sorted(informix_helper_object.list_dbspace())
        self.log.info("List of DBspaces in the informix server: %s", db_space_list)
        self.log.info("***************Starting restore Job*****************")
        job = self.instance_object.restore_in_place(
            db_space_list)
        self.log.info("started the restore Job with Id:%s",
                 job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run data only restore job with error: {0}".format(
                    job.delay_reason
                )
            )
        self.log.info("Restore job is now completed")
        informix_helper_object.bring_server_online()
        self.log.info("Informix server is now online")

    def run(self):
        """Main function for test case execution"""
        try:
            self.perform_install()
            self.check_permissions()
            self.setup_instance()
            self.run_backup_restore()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
