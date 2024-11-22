# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    create_dest_helper_object() --  creates object of OracleHelper class for clone

    create_sample_data()        --  creates sample data in the database

    enable_snapshot_option()    --  enables snapshot option for subclient

    add_oracle_instance()       --  method to add oracle instance

    run_backup()                --  method to run backup

    run_instant_clone()         --  method to run instant clone job and validate test data on clone

    create_orapwdfile()         --  method to create orapwd file for clone

    validate()                  --  method to validate test data on clone

    delete_clone()              --  method to delete the oracle instant clone

    cleanup()                   --  method to clean up testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59632":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "DestinationClient": "client",
                          "DestinationInstance": "instance",(optional, default: "snpclone")
                          "Plan": "plan",                   (optional, default: plan associated to source instance)
                          "SnapEngine": "NetApp",            (optional, default: "NetApp")
                          "DestinationOracleHome": "destinationoraclehome"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.Instances.instant_clone import InstantClone
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
from Database.dbhelper import DbHelper
from AutomationUtils import machine


class TestCase(CVTestCase):
    """ Class for executing instant clone for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle IDA Command Center - Instant clone from Snap backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59632'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'DestinationClient': None,
            'DestinationOracleHome': None}
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.dest_oracle_helper_object = None
        self.dest_client = None
        self.destination_instance_name = self.tcinputs.get("DestinationInstance") or "snpclone"
        self.dest_instance = None
        self.snap_engine = self.tcinputs.get("SnapEngine") or "NetApp"
        self.snapshot_enabled = None
        self.dbhelper_object = None
        self.instant_clone = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE
        self.dbhelper_object = DbHelper(self.commcell)
        self.instant_clone = InstantClone(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def navigate_to_instance(self, instance_name, client_name):
        """Navigates to Instance page
            Args:
                instance_name: Instance Name
                client_name: Client Name
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(
            DBInstances.Types.ORACLE, instance_name, client_name)

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.instance = self.client.agents.get("oracle").instances.get(self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def create_dest_helper_object(self):
        """Creates destination instance oracle helper object"""
        self.dest_client = self.commcell.clients.get(self.tcinputs["DestinationClient"])
        self.dest_instance = self.dest_client.agents.get("oracle").instances.get(
            self.destination_instance_name)
        self.dest_oracle_helper_object = OracleHelper(
            self.commcell, self.dest_client, self.dest_instance)
        self.dest_oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.dest_oracle_helper_object.check_instance_status()

    @test_step
    def create_sample_data(self):
        """Creates sample data in the database"""
        self.oracle_helper_object.create_sample_data(self.tablespace_name)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")

    @test_step
    def enable_snapshot_option(self):
        """Enables snapshot option for subclient"""
        self.subclient_page.enable_snapshot(snap_engine=self.snap_engine,
                                            proxy_node=self.tcinputs["ClientName"],
                                            backup_copy_interface="RMAN")

    @test_step
    def add_oracle_instance(self):
        """Method to add the oracle instance"""
        connect_string = f"sys/{self.oracle_helper_object.ora_sys_password}@{self.destination_instance_name}"
        plan = self.tcinputs.get("Plan") or \
               self.instance.properties['planEntity']['planName']
        self.navigator.navigate_to_db_instances()
        self.database_instances.add_oracle_instance(server_name=self.tcinputs["DestinationClient"],
                                                    oracle_sid=self.destination_instance_name,
                                                    plan=plan,
                                                    oracle_home=self.tcinputs["DestinationOracleHome"],
                                                    connect_string=connect_string)

    @test_step
    def run_backup(self, backup_type):
        """ method to run backup"""
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
        else:
            self.log.info("Incremental Backup")
        job_id = self.subclient_page.backup(backup_type=backup_type)
        self.log.info("Backup job started")
        self.wait_for_job_completion(job_id)
        self.log.info("Backup job completed")
        if "native" in self.snap_engine.lower():
            self.log.info(
                ("Native Snap engine is being run. Backup "
                 "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            backup_copy_job = self.dbhelper_object.get_backup_copy_job(job_id)
            self.log.info("Job ID of backup copy Job is: %s", backup_copy_job.job_id)
        else:
            self.subclient = self.instance.subclients.get("default")
            self.log.info(
                "Running backup copy job for storage policy: %s",
                self.subclient.storage_policy)
            self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)
        return job_id

    @test_step
    def run_instant_clone(self):
        """ method to run instant clone"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        instant_clone_panel = self.db_instance_details.instant_clone(database_type=self.database_type)
        job_id = instant_clone_panel.instant_clone(
            destination_client=self.tcinputs["DestinationClient"],
            instance_name=self.destination_instance_name,
            recover_to="Most recent backup",
            clone_retention={"hours": 1}, overwrite=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Clone completed")

    @test_step
    def create_orapwdfile(self):
        """
        Method creates the orapwd file on the destination client and executes it
        """
        destination_client = self.commcell.clients.get(self.tcinputs["DestinationClient"])
        destination_machine_obj = machine.Machine(destination_client)
        dir_path = destination_machine_obj.join_path(destination_client.install_directory, "base", "orclscripts")
        if not destination_machine_obj.check_directory_exists(dir_path):
            destination_machine_obj.create_directory(dir_path)
        orapwd_creation_script_path = destination_machine_obj.join_path(dir_path, "createorapwd.sh")
        helper_script_path = destination_machine_obj.join_path(dir_path, "helper.sh")
        orapwd_creation_content = ['#!/bin/bash',
                                   f'export ORACLE_HOME={self.tcinputs["DestinationOracleHome"]}',
                                   f'export ORACLE_SID={self.destination_instance_name}',
                                   f'export PATH={self.tcinputs["DestinationOracleHome"]}/bin:$PATH',
                                   f'orapwd file={self.tcinputs["DestinationOracleHome"]}/dbs'
                                   f'/orapw{self.destination_instance_name} '
                                   f'password={self.oracle_helper_object.ora_sys_password} '
                                   f'entries=10',
                                   'exit 0']
        helper_srcipt_content = ['#!/bin/bash',
                                 f'/bin/su -c \\"{orapwd_creation_script_path}\\" - oracle',
                                 'exit 0']
        for line in orapwd_creation_content:
            destination_machine_obj.append_to_file(orapwd_creation_script_path, line)
        for line in helper_srcipt_content:
            destination_machine_obj.append_to_file(helper_script_path, line)
        destination_machine_obj.execute_command(f'chmod +x {orapwd_creation_script_path}')
        destination_machine_obj.execute_command(f'chmod +x {helper_script_path}')
        destination_machine_obj.execute_command(f'sh {helper_script_path}')

    @test_step
    def validate(self):
        """Method validates the created test data on the clone"""
        self.log.info("Validating Backed up content")
        self.dest_oracle_helper_object.validation(tablespace_name=self.tablespace_name, num_of_files=1,
                                                  table="CV_TABLE_01", records=10)
        self.log.info("Validation Successful.")

    @test_step
    def delete_clone(self):
        """Method to delete the oracle instant clone"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.access_instant_clones_tab()
        self.instant_clone.select_clone_delete(instance_name=self.destination_instance_name)

    @test_step
    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.snapshot_enabled is not None and not self.snapshot_enabled:
            self.navigate_to_instance(self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
            self.db_instance_details.click_on_entity('default')
            self.subclient_page.disable_snapshot()
        if self.dest_oracle_helper_object:
            self.navigate_to_instance(self.destination_instance_name,
                                      self.tcinputs["DestinationClient"])
            self.db_instance_details.delete_instance()
            self.delete_clone()
            destination_client = self.commcell.clients.get(self.tcinputs["DestinationClient"])
            destination_machine_obj = machine.Machine(destination_client)
            dir_path = destination_machine_obj.join_path(destination_client.install_directory, "base", "orclscripts")
            orapwd_creation_script_path = destination_machine_obj.join_path(dir_path, "createorapwd.sh")
            helper_script_path = destination_machine_obj.join_path(dir_path, "helper.sh")
            destination_machine_obj.delete_file(orapwd_creation_script_path)
            destination_machine_obj.delete_file(helper_script_path)
            destination_machine_obj.delete_file(f'{self.tcinputs["DestinationOracleHome"]}'
                                                f'/dbs/orapw{self.destination_instance_name}')

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_instance(self.tcinputs["InstanceName"],
                                      self.tcinputs["ClientName"])
            self.log.info("Generating Sample Data for test")
            self.create_helper_object()
            self.create_sample_data()
            self.log.info("Preparing for Backup.")
            self.db_instance_details.click_on_entity('default')
            self.snapshot_enabled = self.subclient_page.is_snapshot_enabled()
            self.subclient_page.disable_snapshot()
            self.enable_snapshot_option()
            self.run_backup(RBackup.BackupType.FULL)
            self.run_instant_clone()
            self.create_orapwdfile()
            self.add_oracle_instance()
            self.create_dest_helper_object()
            self.validate()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
