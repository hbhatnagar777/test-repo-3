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

    setup_instance()    --  Method to setup Sybase instance

    run_backup_restore()--  Method to run backup and restore

    run()               --  Main function for test case execution

    Example Input:

    "65607":
            {
                    "ServerName": "VEDSYB",
			        "Plan": "cs_plan1",
					"SA_Username": "sa",
					"Password": "sybase",
					"OSUsername": "sybase",
					"OSPassword": "sybase",
					"SybaseASE":"ASE-16_0",
					"SybaseOCS":"OCS-16_0",
					"SybaseHome":"/home/sap",
					"ConfigurationFile":"/home/sap/ASE-16_0/VEDSYB.cfg",
					"SharedMemoryDirectory":"/home/sap/ASE-16_0",
					"BlockSize":"64"
					"MasterKeyPassword":"sybase"

            }
"""

from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing Sybase push install without DB group"""
    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Sybase push install without DB group"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.install_helper = None
        self.machine_object = None
        self.client_hostname = None
        self.install_success_flag = False
        self.client = None
        self.config_json = config.get_config()
        self.tcinputs = {
            "ServerName": None,
            "Plan": None,
            "SA_Username": None,
            "Password": None,
            "OSUsername": None,
            "OSPassword": None,
            "SybaseASE": None,
            "SybaseOCS": None,
            "SybaseHome": None,
            "ConfigurationFile": None,
            "SharedMemoryDirectory": None,
            "BlockSize": None,
            "MasterKeyPassword": None

        }
        self.subclient = None
        self.instance_object = None
        self.dbhelper_object = None
        self.install_inputs = None
        self.instance_name = None
        self.subclient = None
        self.database_name = "DB65607"

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
        if self.install_success_flag:
            self.install_helper.uninstall_client(True)
        self.log.info("Teardown")

    def perform_install(self):
        """ Method to perform push install """

        self.dbhelper_object.install_db_agent(
            'SYBASE', self.machine_object, self.tcinputs['Plan'])
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()

    def check_permissions(self):
        """ Method to check if permission of CV directories are properly set """
        self.client = self.commcell.clients.get(self.client_hostname)
        self.dbhelper_object.check_permissions_after_install(self.client, "sybase")

    def setup_instance(self):
        """ Method to set up sybase instance """

        agent = self.client.agents.get('Sybase')

        self.install_inputs = {
                            'instance_name': self.tcinputs['ServerName'],
                            'sybase_ocs': self.tcinputs['SybaseOCS'],
                            'sybase_ase': self.tcinputs['SybaseASE'],
                            'backup_server': self.tcinputs["BackupServerName"],
                            'sybase_home': self.tcinputs["SybaseHome"],
                            'config_file': self.tcinputs["ConfigurationFile"],
                            'enable_auto_discovery': True,
                            'shared_memory_directory': self.tcinputs["SharedMemoryDirectory"],
                            'storage_policy': self.tcinputs["Plan"],
                            'sa_username': self.tcinputs["SA_Username"],
                            'sa_password': self.tcinputs["Password"],
                            'localadmin_username': self.tcinputs["OSUsername"],
                            'localadmin_password': self.tcinputs["OSPassword"],
                            'masterkey_password': self.tcinputs["MasterKeyPassword"]
                            }
        self.instance_object = agent.instances.add_sybase_instance(self.install_inputs)
        self.log.info("Created sybase instance for %s ",self.tcinputs["ServerName"])
        agent.instances.refresh()
        self.sybase_helper = SybaseHelper(self.commcell,self.instance_object,self.client)
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)
        self.subclient = self.instance_object.subclients.get('default')
        self.sybase_helper.csdb = self.csdb
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()

    def run_backup_restore(self):
        """Method to run backup restore"""
        user_tables = ["T65607_FULL","T65607_TL"]
        self.log.info("Full Backup")
        self.sybase_cv_helper.sybase_populate_data(self.database_name, user_tables[0])
        status,full_job_table_list=self.sybase_helper.get_table_list(self.database_name)
        full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, backup_type='full',syntax_check=True,
                                                               db=[self.database_name])
        full_job_endtime=self.sybase_cv_helper.get_end_time_of_job(full_job)
        self.log.info("Full job : %s completed", full_job.job_id)
        self.sybase_cv_helper.single_table_populate(self.database_name,user_tables[1])
        restore_status = self.sybase_cv_helper.single_database_restore(self.database_name,
                                                                     user_table_list=user_tables[:1],
                                                                     expected_table_list=full_job_table_list,
                                                                     timevalue=full_job_endtime)
        if not restore_status:
            raise Exception(
                "Failed to run restore job with error %s",restore_status
            )
        self.log.info("Successfully finished restore job")

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








