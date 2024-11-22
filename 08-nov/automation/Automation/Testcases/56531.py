# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "56531": {
          "cloud_account": "XXXX",
          "plan": "XXXX",
          "access_key": "XXXX",
          "secret_key": "XXXX",
          "rds_instance": "XXXX",
          "region": "US East (Virginia) (us-east-1)"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    wait_for_job_completion()    --  Waits for completion of job and gets the object once job completes

    submit_backup()     --  Submits Amazon RDS backup and validates it

    submit_restore()    --  Submits restore of RDS instance

    check_cluster_state()   --  Check's the cluster state is it ready to start

    start_rds_cluster()     --  Starts the RDS cluster

    delete_cluster()    --  Deletes the cluster

    validate_rds_instance()     --  Validates if RDS instance was created successfully after restore

    cleanup()       --  Delete the Instances and subclients created by test case

    run()           --  run function of this test case

    tear_down()     --  Tear down method of this test case
"""
from time import sleep
from cvpysdk import job
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVException
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Admin Console: Amazon RDS- Basic acceptance test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command center: Acceptance test case for Amazon RDS"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.rds_helper = None
        self.rds_subclient = None
        self.db_instance_details = None
        self.region = ""
        self.is_available = None
        self.is_cluster = None
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None,
            "rds_instance": None,
            "region": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.RDS
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.rds_subclient = SubClient(self.admin_console)
            self.rds_helper = AmazonRDSCLIHelper(
                access_key=self.tcinputs['access_key'], secret_key=self.tcinputs['secret_key'])
            self.region = self.tcinputs['region'].split()[-1][1:-1]
            self.delete_rds_db(check_presence=True)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self):
        """Submits Amazon RDS backup and validates it"""
        bkp = self.rds_subclient.backup(backup_type=RBackup.BackupType.FULL)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of RDS instance group failed")
        job_obj = job.Job(self.commcell, bkp)
        if job_obj.size_of_application <= 0:
            raise CVTestStepFailure("Backup validation failed, size of application is zero")

    @test_step
    def submit_restore(self, instance_name):
        """Submits restore of RDS instance
        Args:
            instance_name   (str)   --  The name of RDS instance to restore

        Returns:
            (str)   --  Name of the snapshot that was used by restore
        """
        self.rds_subclient.access_restore()
        mapping_dict = {
            self.region: [instance_name]
        }
        restore_panel_obj = self.rds_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default', rds_agent=True)
        jobid = restore_panel_obj.restore(instance_name + 'restored')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")
        self.admin_console.refresh_page()
        self.admin_console.select_hyperlink(self.region)
        snapshot = self.rds_subclient.get_items_in_browse_page('Snapshot name')
        return snapshot[0]

    def check_db_state(self, region, db):
        """
        Check's the cluster state is it ready to start
        """
        if cluster_present := self.rds_helper.is_cluster_present(
                region, db, availability=False):
            cluster_available_state = self.rds_helper.is_cluster_present(
                region, db)
            self.is_cluster = True
            if cluster_present and cluster_available_state:
                self.is_available = True
            return cluster_present, cluster_available_state, self.is_cluster
        elif instance_present := self.rds_helper.is_instance_present(
                region, db, availability=False):
            instance_available_state = self.rds_helper.is_instance_present(
                region, db)
            self.is_cluster = False
            if instance_present and instance_available_state:
                self.is_available = True
            return instance_present, instance_available_state, self.is_cluster
        else:
            self.log.error(f"Cluster or instance {db} not found")
            raise CVException(f"Cluster or instance {db} not found")

    @test_step
    def start_rds_db(self):
        """ Start RDS DB instance/cluster """
        try:
            is_present, is_available, is_cluster = self.check_db_state(self.region, self.tcinputs.get("rds_instance"))
            if is_present and not is_available:
                if is_cluster:
                    self.rds_helper.start_rds_cluster(
                        region=self.region,
                        cluster_identifier=self.tcinputs.get("rds_instance")
                    )
                else:
                    self.rds_helper.start_rds_instance(
                        region=self.region,
                        instance_identifier=self.tcinputs.get("rds_instance")
                    )
        except CVException as exp:
            raise CVTestStepFailure(exp)

    def delete_rds_db(self, check_presence=False):
        """
        Deletes the cluster

        Args:
            check_presence (bool) -- Check if cluster is present before deleting
        """
        try:
            is_present, _, is_cluster = self.check_db_state(self.region, self.tcinputs['rds_instance'] + 'restored')
        except CVException as exp:
            if check_presence:
                return
            else:
                raise exp
        if is_cluster:
            self.rds_helper.delete_aurora_cluster(self.tcinputs['rds_instance'] + 'restored',
                                                  self.region)
        else:
            self.rds_helper.delete_cluster(self.tcinputs['rds_instance'] + 'restored', self.region)

    @test_step
    def validate_rds_instance(self, instance_name):
        """Waits for 8 minutes after restore and validates if RDS instance
        was created successfully after restore and status is available.

        Args:
            instance_name   (str)   --  The name of RDS instance to validate
        """
        sleep(480)
        instances = self.rds_helper.discover_region_clusters(
            region=self.region)
        if instance_name not in instances[self.region]:
            raise CVTestStepFailure("Instance not found after restore or not in available state")

    @test_step
    def cleanup(self, created_snapshot):
        """Delete the Instances and subclients created by test case
        Delete the RDS snapshot created during backup

        Args:
            created_snapshot    (str)-- Name of snapshot to be deleted
        """
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'RDS',
                                               self.tcinputs['cloud_account'])

        self.db_instance_details.delete_instance()
        self.rds_helper.delete_snapshot(created_snapshot, self.region, is_cluster_snapshot=self.is_cluster)

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            self.start_rds_db()
            instance_name = self.tcinputs['rds_instance']
            content = {f"{self.rds_helper.convert_region_codes_to_names(self.region)}"
                       f" ({self.region})": [f"{instance_name}(DB Cluster)" if self.is_cluster else instance_name]}
            self.database_instance.add_rds_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'], content=content)
            self.db_instance_details.click_on_entity('default')
            self.submit_backup()
            self.admin_console.refresh_page()
            created_snapshot = self.submit_restore(instance_name)
            self.validate_rds_instance(instance_name + 'restored')
            self.cleanup(created_snapshot)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Delete the restored RDS instance"""
        self.delete_rds_db()
