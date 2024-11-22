# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function for this testcase

    tear_down()             --  tear down method for this testcase

    perform_install()       --  Method to perform push install

    check_permissions()     --  Method to check if permission of CV directories are properly set

    delete_db2_instance()   --  Deletes DB2 Instance

    add_db2_instance()      --  Method to setup DB2 instance

    add_db2_backupset()     --  Method to setup DB2 Database

    add_subclient()         --  Method to setup subclient

    run_backup_restore()    --  Method to run backup and restore

    run()                   --  Main function for test case execution


Example Input:

    The values for username and password needs to be set in config.json in Install -> unix_client

"62807": {
            "client_hostname": "client hostname",
            "instance_name": "db2 instance name",
            "db2_username": "db2 instance username",
            "db2_user_password": "db2 instance password",
            "database_name": "Database Name",
            "storage_policy": "Storage Policy",
            "unix_group": "Unix Group"
        }

"""
import time
from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase
from Database.DB2Utils.db2helper import DB2
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing DB2 push install without DB group"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()

        self.name = "DB2 push install without DB group"
        self.install_helper = None
        self.machine_object = None
        self.machine_db2_object = None
        self.install_success_flag = False
        self.client = None
        self.tcinputs = {
            "client_hostname": None,
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "database_name": None,
            "storage_policy": None
        }
        self.subclient = None
        self.instance = None
        self.backupset = None
        self.dbhelper_object = None
        self.db2_group = None
        self.db2_logs = None
        self.db2_logs_base = None
        self.home_path = None
        self.config_json = None

    def setup(self):
        """setup function for this testcase"""
        self.dbhelper_object = dbhelper.DbHelper(self.commcell)
        self.config_json = config.get_config()
        self.machine_object = Machine(machine_name=self.tcinputs["client_hostname"],
                                      username=self.config_json.Install.unix_client.machine_username,
                                      password=self.config_json.Install.unix_client.machine_password)
        self.machine_db2_object = Machine(machine_name=self.tcinputs["client_hostname"],
                                          username=self.tcinputs["db2_username"],
                                          password=self.tcinputs["db2_user_password"])
        self.install_helper = InstallHelper(self.commcell, self.machine_object)
        self.db2_group = "db2iadm1" if len(self.tcinputs.get("unix_group", "")) == 0 else self.tcinputs.get("unix_group")
        self.db2_logs_base = "/opt/db2logs" if len(self.tcinputs.get("db2_logs", "")) == 0 \
                             else self.tcinputs.get("db2_logs")
        self.db2_logs = {
            "db2ArchivePath": self.machine_object.join_path(self.db2_logs_base, "Archive"),
            "db2RetrievePath": self.machine_object.join_path(self.db2_logs_base, "Retrieve"),
            "db2AuditErrorPath": self.machine_object.join_path(self.db2_logs_base, "Audit")
        }
        self.machine_object.create_directory(self.db2_logs_base, force_create=True)
        self.machine_object.execute_command(command=f"chgrp {self.db2_group} {self.db2_logs_base}")
        self.home_path = self.machine_db2_object.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", self.home_path)

    def tear_down(self):
        """ Tear down function to uninstall the client """
        if self.install_success_flag:
            self.install_helper.uninstall_client(True)
            self.machine_object.remove_directory(self.db2_logs_base)

    def perform_install(self):
        """ Method to perform push install """
        self.dbhelper_object.install_db_agent(
            'DB2_AGENT', self.machine_object, self.tcinputs['storage_policy'], db2_logs_location=self.db2_logs)
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()
        self.client = self.commcell.clients.get(self.tcinputs["client_hostname"])

    def check_permissions(self):
        """ Method to check if permission of CV directories and DB2 logs are properly set """
        self.dbhelper_object.check_permissions_after_install(self.client, self.db2_group)
        base_db2_log_group = self.machine_object.get_file_group(self.db2_logs_base)
        self.log.info('%s : %s', self.db2_logs_base, base_db2_log_group)
        arc_db2_log_group = self.machine_object.get_file_group(self.db2_logs["db2ArchivePath"])
        self.log.info('%s : %s', self.db2_logs["db2ArchivePath"], arc_db2_log_group)
        aud_db2_log_group = self.machine_object.get_file_group(self.db2_logs["db2AuditErrorPath"])
        self.log.info('%s : %s', self.db2_logs["db2AuditErrorPath"], aud_db2_log_group)
        ret_db2_log_group = self.machine_object.get_file_group(self.db2_logs["db2RetrievePath"])
        self.log.info('%s : %s', self.db2_logs["db2RetrievePath"], ret_db2_log_group)

        if not self.db2_group == base_db2_log_group == arc_db2_log_group == aud_db2_log_group == ret_db2_log_group:
            raise Exception(f"Group of CV Db2 Staging directories is not set to {self.db2_group}")

    def delete_db2_instance(self):
        """
        Deletes DB2 Instance
        """
        self.agent = self.client.agents.get("DB2")
        self.log.info("### Deleting DB2 Instance ###")
        instances = self.agent.instances
        if instances.has_instance(instance_name=self.tcinputs['instance_name']):
            self.log.info("Deleting instance from CS as it already exist!")
            instances.delete(self.tcinputs['instance_name'])
            instances.refresh()
            self.log.info("Sleeping for 10 seconds")
            time.sleep(10)
        else:
            self.log.info("Instance does not exists on CS.")

    def add_db2_instance(self):
        """
        Adds DB2 Instance
        Raises:
            Exception:
                If adding instance fails.
        """
        self.log.info("### Adding DB2 Instance ###")
        instances = self.agent.instances
        db2_instance_options = {
            'instance_name': self.tcinputs['instance_name'],
            'data_storage_policy': self.tcinputs['storage_policy'],
            'log_storage_policy': self.tcinputs['storage_policy'],
            'command_storage_policy': self.tcinputs['storage_policy'],
            'home_directory': self.home_path,
            'password': self.tcinputs['db2_user_password'],
            'user_name': self.tcinputs['db2_username']
        }
        instances.add_db2_instance(db2_options=db2_instance_options)
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        instances.refresh()
        self.instance = instances.get(self.tcinputs['instance_name'])

    def add_db2_backupset(self):
        """
        Adds DB2 Backupset
        """
        self.instance.refresh()
        self.log.info("### Adding DB2 Backupset ###")
        if self.instance.backupsets.has_backupset(backupset_name=self.tcinputs["database_name"]):
            self.instance.backupsets.delete(self.tcinputs["database_name"])
            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")
            self.instance.refresh()
        self.instance.backupsets.add(backupset_name=self.tcinputs["database_name"],
                                     storage_policy=self.tcinputs['storage_policy'])
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        self.instance.refresh()
        self.backupset = self.instance.backupsets.get(self.tcinputs["database_name"])

    def add_subclient(self):
        """
        Creates a subclient
        """
        self.log.info("### Creating Subclient ###")

        self.backupset.subclients.add(subclient_name=self.id,
                                      storage_policy=self.tcinputs['storage_policy'],
                                      description="DB2 Install Test")
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        self.subclient = self.backupset.subclients.get(subclient_name=self.id)

    def run_backup_restore(self):
        """ Method to run backup and restore """
        db2_helper_object = DB2(commcell=self.commcell,
                                client=self.client,
                                instance=self.instance,
                                backupset=self.backupset)
        db2_helper_object.update_db2_database_configuration1(cold_backup_path="/dev/null")

        db2_helper_object.run_backup(self.subclient, "FULL")
        db2_helper_object.run_backup(self.subclient, "INCREMENTAL")
        db2_helper_object.run_backup(self.subclient, "DIFFERENTIAL")

        self.log.info("***************Starting restore Job*****************")
        job = db2_helper_object.run_restore(self.backupset)
        self.log.info("Started the restore Job with Id:%s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run data only restore job with error: {job.delay_reason}"
            )
        self.log.info("Restore job is now completed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.perform_install()
            self.check_permissions()
            self.delete_db2_instance()
            self.add_db2_instance()
            self.add_db2_backupset()
            self.add_subclient()
            self.run_backup_restore()
        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
