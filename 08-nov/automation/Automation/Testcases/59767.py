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

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    create_helper_object()      --  creates object of OracleHelper class

    run_restore()               --  method to run restore and validate test data

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
        {
            "56592":
                {
                    "RacInstanceName": "name of the instance",
                    "RacClusterName": "name of the cluster",
                    "Plan": "plan to be used",
                        (optional, if instance is not already present)
                    "CatalogString": "username/password@servicename",
                        (optional, if instance is not already present in the above format)
                    "RacNodes": [{
                        "RacInstance": "name of the node instance",
                        "RacServer": "display name of rac server node",
                        "ConnectUsername": "username for connect string",
                        "ConnectPassword": "password for connect string",
                        "OracleHomeDir": "location of oracle home dir"
                    },{
                        "RacInstance": "name of the node instance",
                        "RacServer": "display name of rac server node",
                        "ConnectUsername": "username for connect string",
                        "ConnectPassword": "password for connect string",
                        "OracleHomeDir": "location of oracle home dir"
                    }]
                        (optional, if instance is not already present)
                }
        }


"""
import json
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper, OracleRACHelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1-Acceptance test for Oracle RAC on Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59767'
        self.database_type = None,
        self.tcinputs = {
            'RacClusterName': None,
            'RacInstanceName': None,
            }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.automation_instance = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE_RAC

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

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
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def add_instance(self):
        """Adds new instance"""
        required_inputs = [
            "RacInstance",
            "RacServer",
            "ConnectUsername",
            "ConnectPassword",
            "OracleHomeDir",
        ]
        input_nodes = self.tcinputs["RacNodes"]
        rac_nodes = json.loads(input_nodes) if isinstance(input_nodes, str) else input_nodes
        if not all(key in node for key in required_inputs for node in rac_nodes):
            raise CVTestStepFailure("Provide {0} for each node".format(", ".join(required_inputs)))

        catalog_string = self.tcinputs.get("CatalogString")
        self.log.info("Trying to create new instance with the provided inputs")
        self.database_instances.add_oracle_rac_instance(rac_instance_name=self.tcinputs["RacInstanceName"],
                                                        rac_cluster_name=self.tcinputs["RacClusterName"],
                                                        rac_nodes=rac_nodes,
                                                        plan=self.tcinputs["Plan"],
                                                        catalog_connect_string=catalog_string)
        self.automation_instance = True

        self.log.info("Selecting the newly created instance")
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def create_helper_object(self):
        """Creates oracle RAC helper object"""
        self.client = self.commcell.clients.get(self.tcinputs["RacClusterName"])
        self.instance = self.client.agents.get("oracle rac").instances.get(
            self.tcinputs["RacInstanceName"])
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["RacInstanceName"])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle RAC Restore completed")

    @test_step
    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.automation_instance:
            self.navigate_to_instance()
            self.db_instance_details.delete_instance()

    def run(self):
        """ Main function for test case execution """
        try:

            self.log.info(
                "#" * (10) + "  Oracle RAC Backup/Restore Operations  " + "#" * (10))

            self.log.info("Navigating to DB Instances page")
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()

            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE_RAC,
                                                          self.tcinputs["RacInstanceName"],
                                                          self.tcinputs["RacClusterName"]):
                self.log.info("Instance found")
                self.navigate_to_instance()
            else:
                self.log.info("Instance not found. Creating new instance")
                self.add_instance()
                self.log.info("Instance successfully created")

            self.log.info("Generating Sample Data for test")
            table_limit = 1
            num_of_files = 1
            row_limit = 10
            self.create_helper_object()
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")

            self.log.info("Preparing for Full Backup.")
            self.db_instance_details.click_on_entity('default')
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle RAC Full Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')

            self.log.info("Generating Sample Data for Incremental Backup")
            user = "{0}_user".format(self.tablespace_name.lower())
            self.oracle_helper_object.db_create_table(
                self.tablespace_name, "CV_TABLE_INCR_", user, table_limit)
            self.log.info("Successfully generated sample data for incremental backups")

            self.log.info("Preparing for Incremental Backup.")
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.INCR)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle RAC Incremental Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

            self.log.info("Cleaning up tablespace and data before restore")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

            self.log.info("Preparing for Oracle RAC Restore.")
            self.run_restore()

            self.log.info("Validating Backed up content")
            self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                 "CV_TABLE_01", row_limit)
            self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                 "CV_TABLE_INCR_01", row_limit)
            self.log.info("Validation Successful.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.log.info("Logging out of the admin console")
            AdminConsole.logout_silently(self.admin_console)
            self.log.info("Closing the browser")
            Browser.close_silently(self.browser)