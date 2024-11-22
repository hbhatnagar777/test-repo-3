# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "56538": {
          "cloud_account": "XXXX",
          "plan": "XXXX",
          "access_key": "XXXX",
          "secret_key": "XXXX",
          "rds_instance": "XXXX",
          "source_region": "US East (Virginia) (us-east-1)",
          "destination_region": "Asia Pacific (Mumbai) (ap-south-1)",
          "snap_copy_library": "XXXXX" [storage pool for snap copy]
          "snap_copy_ma": "XXXXX" [corresponding Media Agent]
        }

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    setup()         --  Initial configuration for the test case

    add_instance()  --  Method to Delete existing instance, and then create new RDS instance

    check_cluster_state()   --  Check's the cluster state is it ready to start

    start_rds_cluster()     --  Starts the RDS cluster

    delete_rds_db()         --  Deletes the rds db

    create_secondary_snap_copy()--Creates secodary snap copy for input plan and enables replication

    wait_for_job_completion() --Waits for completion of job and gets the object once job completes

    submit_backup() --  Method to Submit Amazon RDS backup and validates it

    get_snapshot_name() --  Method to Get name of the backup snapshot from browse page

    submit_restore()    --  Method Submit restore of RDS instance from destination region

    validate_rds_aux_snapshot()--   Method to validate if RDS snapshot is replicated

    validate_rds_instance()     --  Method to validate if RDS instance was created successfully
     after restore

    cleanup()          --  Method to delete instance and test data after testcase execcution

    tear_down()     --  Tear down method of this test case
"""
from time import sleep
from cvpysdk import job
from cvpysdk.policies.storage_policies import StoragePolicy
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import RDSSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVException
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Admin Console: Replication support  for RDS instances on command Center"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Replication support  for RDS instances on command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.rds_helper = None
        self.rds_subclient = None
        self.db_instance_details = None
        self.source_region = None
        self.destination_region = None
        self.storage_policy = None
        self.copy_name = None
        self.instance_created = None
        self.created_snapshot = None
        self.is_cluster = None
        self.is_available = None
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None,
            "rds_instance": None,
            "source_region": None,
            "destination_region": None,
            "snap_copy_library": None,
            "snap_copy_ma": None
        }

    def setup(self):
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
            self.database_type = DBInstances.Types.RDS
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.rds_subclient = RDSSubclient(self.admin_console)
            self.rds_helper = AmazonRDSCLIHelper(
                self.tcinputs['access_key'], self.tcinputs['secret_key'])
            self.source_region = self.tcinputs['source_region'].split()[-1][1:-1]
            self.destination_region = self.tcinputs['destination_region'].split()[-1][1:-1]
            self.storage_policy = StoragePolicy(self.commcell, self.tcinputs['plan'])
            self.delete_rds_db(check_presence=True)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_instance(self, content):
        """Deletes instance, if exists, and then creates new RDS instance"""
        info = "Checking if {0} instance exists".format("RDS")
        self.log.info(info)
        if self.database_instance.is_instance_exists(DBInstances.Types.CLOUD_DB, "RDS",
                                                     self.tcinputs['cloud_account']):
            self.log.info("Instance found")
            self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB,
                                                   'RDS', self.tcinputs['cloud_account'])
            self.db_instance_details.delete_instance()
        self.database_instance.add_rds_instance(
            self.tcinputs['cloud_account'], self.tcinputs['plan'], content=content)
        self.instance_created = True

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
            is_present, is_available, is_cluster = self.check_db_state(self.source_region,
                                                                       self.tcinputs.get("rds_instance"))
            if is_present and not is_available:
                if is_cluster:
                    self.rds_helper.start_rds_cluster(
                        region=self.source_region,
                        cluster_identifier=self.tcinputs.get("rds_instance")
                    )
                else:
                    self.rds_helper.start_rds_instance(
                        region=self.source_region,
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
            is_present, _, is_cluster = self.check_db_state(self.destination_region,
                                                            self.tcinputs['rds_instance'] + 'restored')
        except CVException as exp:
            if check_presence:
                return
            else:
                raise exp
        if is_cluster:
            self.rds_helper.delete_aurora_cluster(self.tcinputs['rds_instance'] + 'restored',
                                                  self.destination_region)
        else:
            self.rds_helper.delete_cluster(self.tcinputs['rds_instance'] + 'restored', self.destination_region)

    @test_step
    def create_secondary_snap_copy(self):
        """Creates secodary snap copy for input plan and enables replication
        Returns: Name of the secondary snap copy being used for replication
        """
        snap_copies = []
        for copy, value in self.storage_policy.copies.items():
            if value['isSnapCopy'] and value['active'] > 0:
                snap_copies.append(copy)
        if len(snap_copies) == 0:
            raise Exception('Ensure plan has a primary snapshot copy')
        if len(snap_copies) == 1:
            self.storage_policy.create_snap_copy(copy_name="secondary snap copy",
                                                 is_mirror_copy=False, is_snap_copy=True,
                                                 library_name=
                                                 self.tcinputs['snap_copy_library'],
                                                 media_agent_name=self.tcinputs['snap_copy_ma'],
                                                 source_copy=snap_copies[0],
                                                 is_replica_copy=True)
            self.log.info("Secondary snap copy created for plan %s", self.tcinputs['plan'])
            self.admin_console.refresh_page()
            self.copy_name = "secondary snap copy"
        else:
            self.log.info("Secondary snap copy exists")
        source = self.rds_helper.convert_region_codes_to_names(self.source_region)
        destination = self.rds_helper.convert_region_codes_to_names(self.destination_region)
        return self.rds_subclient.enable_replication(source, destination)['Secondary snap copy']

    @test_step
    def wait_for_job_completion(self, jobid, wait_time=30):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

            wait_time (int): Time to wait for job completion in minutes
                default: 30
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion(timeout=wait_time)

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
    def get_snapshot_name(self):
        """Gets name of the backup snapshot from browse page"""
        self.rds_subclient.access_restore()
        self.admin_console.select_hyperlink(self.source_region)
        snapshot = self.rds_subclient.get_items_in_browse_page('Snapshot name')
        self.admin_console.select_breadcrumb_link_using_text('default')
        return snapshot[-1]

    @test_step
    def submit_restore(self, instance_name, copy_name):
        """Submits restore of RDS instance from destination region
        Args:
            instance_name   (str)   --  The name of RDS instance to restore

        Returns:
            (str)   --  Name of the snapshot that was used by restore
        """
        self.rds_subclient.access_restore()
        mapping_dict = {
            self.destination_region: [instance_name]
        }
        restore_panel_obj = self.rds_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default', rds_agent=True, copy=copy_name)
        jobid = restore_panel_obj.restore(f"{instance_name}restored")
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")
        self.admin_console.refresh_page()

    @test_step
    def validate_rds_aux_snapshot(self, snapshot_name, region):
        """Waits for 8 minutes after aux and validates if RDS snapshot is replicated
        successfully after aux and status is available.

        Args:
            snapshot_name   (str)   --  name of rds instance snapshot
            region          (str)   --  region in which the snapshot is present
        """
        sleep(480)
        snapshot_name = f"copyof-{snapshot_name}"
        if not self.is_cluster:
            snapshot_replicated = self.rds_helper.is_snapshot_present(snapshot_name, region)
        else:
            snapshot_replicated = self.rds_helper.is_cluster_snapshot_present(snapshot_name, region)
        if snapshot_replicated:
            self.log.info("Snapshot successfully replicated to destination region")
        else:
            raise CVTestStepFailure("Snapshot not found replicated to destination region")

    @test_step
    def validate_rds_instance(self, instance_name, region):
        """Waits for 8 minutes after restore and validates if RDS instance
        was created successfully after restore and status is available.

        Args:
            instance_name   (str)   --  The name of RDS instance to validate
            region          (str)   --  region in which the instance is present
        """
        sleep(480)
        instances = self.rds_helper.discover_all_region_clusters(
            region=region)
        if instance_name not in instances[region]:
            raise CVTestStepFailure("Instance not found after restore or not in available state")

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case
        Delete the RDS snapshot created during backup
        """
        if self.instance_created:
            self.navigator.navigate_to_db_instances()
            self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB,
                                                   'RDS', self.tcinputs['cloud_account'])
            self.db_instance_details.delete_instance()
        if self.created_snapshot:
            self.rds_helper.delete_snapshot(self.created_snapshot, self.source_region,
                                            is_cluster_snapshot=self.is_cluster)
            self.rds_helper.delete_snapshot(f"copyof-{self.created_snapshot}",
                                            self.destination_region, is_cluster_snapshot=self.is_cluster)

    def run(self):
        """Main method to run test case"""
        try:
            self.start_rds_db()
            instance_name = self.tcinputs['rds_instance']

            content = {f"{self.rds_helper.convert_region_codes_to_names(self.source_region)} ({self.source_region})": [
                f"{instance_name}(DB Cluster)" if self.is_cluster else instance_name]}
            self.add_instance(content)
            self.db_instance_details.click_on_entity('default')
            copy_name = self.create_secondary_snap_copy()

            ma_name = self.storage_policy.get_copy(copy_name)._copy_properties[
                'mediaAgent']['mediaAgentName']
            self.submit_backup()

            common_utils = CommonUtils(self)
            aux_job = common_utils.aux_copy(self.storage_policy, copy_name, ma_name, wait=False)
            self.wait_for_job_completion(aux_job.job_id, wait_time=5)

            self.admin_console.refresh_page()

            self.created_snapshot = self.get_snapshot_name()
            self.validate_rds_aux_snapshot(self.created_snapshot, self.destination_region)

            self.admin_console.refresh_page()
            self.submit_restore(instance_name, copy_name)
            self.validate_rds_instance(f"{instance_name}restored", self.destination_region)

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Delete the restored RDS instance"""
        if self.copy_name:
            self.storage_policy.delete_secondary_copy(self.copy_name)
        self.delete_rds_db()
