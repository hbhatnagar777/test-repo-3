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
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    navigate_to_oracle_instance()           --  function to navigate to oracle instance

    create_source_oracle_helper()           --  Creates the source oracle helper object

    create_destination_oracle_helper()      --  Creates the destination oracle helper object

    add_subclient()                         --  adds a new subclient on source instance

    enable_snapshot_imagecopy()             --  method to enable volumecopy with imagecopy

    wait_for_job_completion()               --  waits for the job completion

    run_backup()                            --  method to run the backup

    run_instant_clone()                     --  method to run the instant clone

    create_orapwdfile()                     --  method to create orapwd file for clone

    run_instant_clone_from_details_page()   --  method to run clone from details page

    validate()                              --  method to validate test data on clone

    delete_oracle_instance()                --  method to delete oracle instnace

    add_oracle_instance()                   --  method to add oracle instance

    cleanup()                               --  method to remove scripts, files and subclient created

    run()                                   --  run function for this test case

    Input Example:

    "testCases":
            {
                "62648":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "ImageCopyPath": "/ImageCopy",
                          "AgentName": "oracle",
                          "DestinationClient": "client",
                          "Plan" : "plan",
                          "ClientSysUsername" : "Username",
                          "ClientSysPassword" : "Password",
                          "SnapshotEngine" : "Netapp",
                          "OraPassword" : "orapassword",
                          "DestinationClientName": "client",
                          "DestinationInstanceName" : "Clonedb",
                          "DestinationOracleHome" : "destinationoraclehome"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from cvpysdk.policies.storage_policies import StoragePolicy
from Database.dbhelper import DbHelper
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.Instances.instant_clone import InstantClone
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.adminconsole = None
        self.browser = None
        self.dbhelper_obj = None
        self.dbinstance_obj = None
        self.dbinstancedetails_obj = None
        self.destination_client_obj = None
        self.destination_instance_obj = None
        self.destination_oracle_helper = None
        self.instantclone_obj = None
        self.name = "Instant Clone with Image copy + Block Level"
        self.subclient_obj = None
        self.navigator = None
        self.source_oracle_helper = None
        self.tablespace_name = "CV_62648"
        self.subclientname = self.tablespace_name
        self.tcinputs = {
            'InstanceName': None,
            'ClientName': None,
            'DestinationOracleHome': None
        }

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.adminconsole.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                self.inputJSONnode["commcell"]["commcellPassword"])
        self.navigator = self.adminconsole.navigator
        self.dbinstance_obj = DBInstances(self.adminconsole)
        self.dbinstancedetails_obj = DBInstanceDetails(self.adminconsole)
        self.subclient_obj = SubClient(self.adminconsole)
        self.dbhelper_obj = DbHelper(self.commcell)
        self.instantclone_obj = InstantClone(self.adminconsole)

    @test_step
    def navigate_to_oracle_instance(self, instancename, clientname):
        """Navigates to oracle instance
        Args:
            instancename: Instance name
            clientname:   Client name
        """
        self.navigator.navigate_to_db_instances()
        self.dbinstance_obj.select_instance(DBInstances.Types.ORACLE,
                                            instancename,
                                            clientname)

    @test_step
    def create_source_oracle_helper(self):
        """
        Creates the source oracle obj
        """
        self.source_oracle_helper = OracleHelper(commcell=self.commcell, db_host=self.client,
                                                 instance=self.instance, sys_user=self.tcinputs["ClientSysUsername"],
                                                 sys_password=self.tcinputs["ClientSysPassword"])
        self.source_oracle_helper.db_connect()

    @test_step
    def create_destination_oracle_helper(self):
        """
        Method to create the destination oracle helper
        """
        self.destination_client_obj = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
        self.destination_instance_obj = self.commcell.clients.get(self.tcinputs["DestinationClientName"]).\
            agents.get("oracle").instances.get(self.tcinputs["DestinationInstanceName"])
        self.destination_oracle_helper = OracleHelper(commcell=self.commcell, db_host=self.destination_client_obj,
                                                      instance=self.destination_instance_obj)
        self.destination_oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)

    @test_step
    def add_subclient(self):
        """
        Adds a new subclient
        """
        add_subclient_obj = self.dbinstancedetails_obj.click_add_subclient(DBInstances.Types.ORACLE)
        add_subclient_obj.add_subclient(self.subclientname,
                                        self.tcinputs["Plan"],
                                        selective_online_full=False)

    @test_step
    def enable_snapshot_imagecopy(self):
        """
        Enables sublcient with Block level and image copy
        """
        self.subclient_obj.enable_snapshot(self.tcinputs["SnapshotEngine"],
                                           self.tcinputs["ClientName"],
                                           self.tcinputs["ImageCopyPath"])
        self.adminconsole.refresh_page()

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def run_backup(self, backuptype):
        """
        Method to run the backup
        """
        job_id = self.subclient_obj.backup(backup_type=backuptype)
        self.log.info("Snap backup is running")
        self.wait_for_job_completion(job_id)
        self.log.info("Snap backup is completed")
        if "native" == self.tcinputs["SnapshotEngine"].lower():
            self.log.info("As Engine is native the backupcopy will run inline")
            job_id = self.dbhelper_obj.get_backup_copy_job(job_id).job_id
        else:
            self.log.info("Running backupcopy job for the storage policy %s", self.tcinputs["Plan"])
            storage_policy_obj = StoragePolicy(commcell_object=self.commcell,
                                               storage_policy_name=self.tcinputs["Plan"])
            job_id = storage_policy_obj.run_backup_copy().job_id
        self.wait_for_job_completion(job_id)

    @test_step
    def run_instant_clone(self):
        """
        Method to run the instant clone
        """
        self.log.info("Preparing for the instant clone.")
        self.navigator.navigate_to_db_instances()
        self.dbinstance_obj.access_instant_clones_tab()
        instant_clone_panel = self.dbinstance_obj.instant_clone(database_type=DBInstances.Types.ORACLE,
                                                                source_server=self.tcinputs["ClientName"],
                                                                source_instance=self.tcinputs["InstanceName"])
        job_id = instant_clone_panel.instant_clone(
            destination_client=self.tcinputs["DestinationClientName"],
            instance_name=self.tcinputs["DestinationInstanceName"],
            oracle_home=self.tcinputs["DestinationOracleHome"],
            clone_retention={"hours": 1}, overwrite=True)
        self.log.info("Instant clone job is running")
        self.wait_for_job_completion(job_id)
        self.log.info("Instant clone job is completed")
        
    @test_step
    def create_orapwdfile(self):
        """
        Method creates the orapwd file on the destination client and executes it
        """
        destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
        destination_machine_obj = machine.Machine(destination_client)
        dir_path = destination_machine_obj.join_path(destination_client.install_directory, "base", "orclscripts")
        if not destination_machine_obj.check_directory_exists(dir_path):
            destination_machine_obj.create_directory(dir_path)
        orapwd_creation_script_path = destination_machine_obj.join_path(dir_path, "createorapwd.sh")
        helper_script_path = destination_machine_obj.join_path(dir_path, "helper.sh")
        orapwd_creation_content = ['#!/bin/bash',
                                   f'export ORACLE_HOME={self.tcinputs["DestinationOracleHome"]}',
                                   f'export ORACLE_SID={self.tcinputs["DestinationInstanceName"]}',
                                   f'export PATH={self.tcinputs["DestinationOracleHome"]}/bin:$PATH',
                                   f'orapwd file={self.tcinputs["DestinationOracleHome"]}/dbs'
                                   f'/orapw{self.tcinputs["DestinationInstanceName"]} '
                                   f'password={self.tcinputs["OraPassword"]} '
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
    def run_instant_clone_from_details_page(self):
        """
        Method to run the instant clone from the instant details page
        """
        self.navigator.navigate_to_db_instances()
        self.dbinstance_obj.select_instance(database_type=DBInstances.Types.ORACLE,
                                            instance_name=self.tcinputs["InstanceName"],
                                            client_name=self.tcinputs["ClientName"])
        instant_clone_panel = self.dbinstancedetails_obj.instant_clone(DBInstances.Types.ORACLE)
        self.log.info("After the post clone")
        job_id = instant_clone_panel.instant_clone(
            destination_client=self.tcinputs["DestinationClientName"],
            instance_name=self.tcinputs["DestinationInstanceName"],
            oracle_home=self.tcinputs["DestinationOracleHome"],
            clone_retention={"hours": 1}, overwrite=True)
        self.log.info("Instant clone job is running")
        self.wait_for_job_completion(job_id)
        self.log.info("Instant clone job is completed")

    @test_step
    def validate(self):
        """
        Method validates the created test data on the clone
        """
        self.log.info("Validating the test data on the clone")
        self.destination_oracle_helper.validation(tablespace_name=self.tablespace_name, num_of_files=1,
                                                  table="CV_TABLE_01", records=10)
        self.log.info("Validation is successful")

    @test_step
    def delete_oracle_instance(self):
        """
        Method to remove the oracle instance
        """
        self.navigate_to_oracle_instance(self.tcinputs["DestinationInstanceName"],
                                         self.tcinputs["DestinationClientName"])
        self.dbinstancedetails_obj.delete_instance()

    @test_step
    def delete_clone(self):
        """
        Method to delete the oracle instant clone
        """
        self.navigator.navigate_to_db_instances()
        self.dbinstance_obj.access_instant_clones_tab()
        self.instantclone_obj.select_clone_delete(instance_name=self.tcinputs["DestinationInstanceName"])

    @test_step
    def add_oracle_instance(self):
        """
        Method to add the oracle instance
        """
        connect_string = f"sys/{self.tcinputs['OraPassword']}@{self.tcinputs['DestinationInstanceName']}"
        self.navigator.navigate_to_db_instances()
        self.dbinstance_obj.add_oracle_instance(server_name=self.tcinputs["DestinationClientName"],
                                                oracle_sid=self.tcinputs["DestinationInstanceName"],
                                                plan=self.tcinputs["Plan"],
                                                oracle_home=self.tcinputs["DestinationOracleHome"],
                                                connect_string=connect_string)

    @test_step
    def cleanup(self):
        """
        Removes the test case created scripts, files and the subclient
        """
        self.navigate_to_oracle_instance(self.tcinputs["InstanceName"],
                                         self.tcinputs["ClientName"])
        self.dbinstancedetails_obj.click_on_entity(self.tablespace_name)
        self.subclient_obj.delete_subclient()
        destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
        destination_machine_obj = machine.Machine(destination_client)
        dir_path = destination_machine_obj.join_path(destination_client.install_directory, "base", "orclscripts")
        orapwd_creation_script_path = destination_machine_obj.join_path(dir_path, "createorapwd.sh")
        helper_script_path = destination_machine_obj.join_path(dir_path, "helper.sh")
        destination_machine_obj.delete_file(orapwd_creation_script_path)
        destination_machine_obj.delete_file(helper_script_path)
        destination_machine_obj.delete_file(f'{self.tcinputs["DestinationOracleHome"]}'
                                            f'/dbs/orapw{self.tcinputs["DestinationInstanceName"]}')

    def run(self):
        """Method for test case execution"""
        try:
            self.create_source_oracle_helper()
            self.source_oracle_helper.create_sample_data(tablespace_name=self.tablespace_name)
            self.navigate_to_oracle_instance(instancename=self.tcinputs["InstanceName"],
                                             clientname=self.tcinputs["ClientName"])
            self.add_subclient()
            self.enable_snapshot_imagecopy()
            self.run_backup(Backup.BackupType.FULL)
            self.run_instant_clone()
            self.create_orapwdfile()
            self.add_oracle_instance()
            self.create_destination_oracle_helper()
            self.validate()
            self.delete_oracle_instance()
            self.delete_clone()
            self.run_instant_clone_from_details_page()
            self.add_oracle_instance()
            self.create_destination_oracle_helper()
            self.validate()
            self.delete_oracle_instance()
            self.delete_clone()
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)