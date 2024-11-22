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

    kill_active_jobs()  --  Method to kill the active jobs running for the client

    perform_install()   --  Method to perform push install

    check_permissions() --  Method to check if permission of CV directories are properly set

    create_hana_client()--  Method to create hana pseudo client

    setup_instance()    --  Method to setup hana instance

    run_backup()        --  Method to run backup and restore

    run()               --  Main function for test case execution

Example Input:

    "62821":
            {
                    "SID":"",
                    "storagePolicy":"",
                    "DatabaseUserName":"",
                    "DatabasePassword":""
            }

"""
from time import time
from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database import dbhelper

class TestCase(CVTestCase):
    """Class for executing PGSQL push install without DB group"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "SAP HANA push install without DB group"
        self.hana_helper = None
        self.install_helper = None
        self.machine_object = None
        self.client_hostname = None
        self.install_success_flag = False
        self.client = None
        self.config_json = config.get_config()
        self.tcinputs = {
            'SID': None,
            'storagePolicy': None,
            'DatabaseUserName': None,
            'DatabasePassword': None
        }
        self.subclient = None
        self.agent = None
        self.instance = None
        self.dbhelper_object = None
        self.pseudo_client_name = None
        self.instance_created = None
        self.pseudo_client_created = None

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
        self.pseudo_client_name = f"automation_{int(time())}"

    def tear_down(self):
        """ Tear down function to uninstall the client """
        if self.instance_created:
            self.log.info("Deleting the instance")
            self.kill_active_jobs()
            self.agent.instances.delete(self.tcinputs['SID'])
        if self.pseudo_client_created:
            self.log.info("Deleting the pseudo client")
            self.commcell.clients.delete(self.pseudo_client_name)
        if self.install_success_flag:
            self.log.info("Uninstalling the client")
            self.install_helper.uninstall_client(True)

    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        self.commcell.refresh()
        active_jobs = self.commcell.job_controller.active_jobs(self.pseudo_client_name)
        self.log.info("Active jobs for the client:%s", active_jobs)
        if active_jobs:
            for job in active_jobs:
                self.log.info("Killing Job:%s", job)
                self.commcell.job_controller.get(job).kill(True)
            active_jobs = self.commcell.job_controller.active_jobs(self.pseudo_client_name)
            if active_jobs:
                self.kill_active_jobs()
            self.log.info("All active jobs are killed")
        else:
            self.log.info("No Active Jobs found for the client.")

    def perform_install(self):
        """ Method to perform push install """
        self.dbhelper_object.install_db_agent(
            'SAPHANA', self.machine_object, self.tcinputs['storagePolicy'])
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()

    def check_permissions(self):
        """ Method to check if permission of CV directories are properly set """
        self.client = self.commcell.clients.get(self.client_hostname)
        self.dbhelper_object.check_permissions_after_install(self.client, "sapsys")

    def create_hana_client(self):
        """ Method to create hana pseudo client """
        self.log.info("creating hana pseudo client")
        self.commcell.clients.create_pseudo_client(self.pseudo_client_name, client_type="sap hana")
        self.pseudo_client_created = True
        self.commcell.refresh()
        self.log.info("created hana pseudo client")

    def setup_instance(self):
        """ Method to set up sap hana instance """
        self.log.info("Creating instance")
        self.client = self.commcell.clients.get(self.pseudo_client_name)
        self.agent = self.client.agents.get('SAP HANA')
        self.agent.instances.add_sap_hana_instance(
            sid=self.tcinputs['SID'],
            hana_client_name=self.client_hostname,
            db_user_name=self.tcinputs['DatabaseUserName'],
            db_password=self.tcinputs['DatabasePassword'],
            storage_policy=self.tcinputs['storagePolicy'])
        self.instance_created = True
        self.log.info("Instance got created")
        self.agent.instances.refresh()
        self.instance = self.agent.instances.get(self.tcinputs['SID'])
        backupset = self.instance.backupsets.get(self.tcinputs['SID'])
        self.subclient = backupset.subclients.get('default')
        self.subclient.refresh()

    def run_backup(self):
        """ Method to run backup and restore """
        backup_job = self.subclient.backup('Full')
        self.log.info("Started Full backup with Job ID: %s", backup_job.job_id)
        if not backup_job.wait_for_completion():
            raise Exception(
                f"Failed to run Full backup job with error: {backup_job.delay_reason}"
            )
        time.sleep(60)

    def run(self):
        """ Main function for test case execution """

        try:
            self.perform_install()
            self.check_permissions()
            self.create_hana_client()
            self.setup_instance()
            self.run_backup()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
