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
    __init__()      --  initialize TestCase class

    init_tc()         --  Initial configuration for test case

    setup()         --  setup function of this test case

    _backup()       --  backup of MongoDB Atlas cluster

    _restore()      --  restore of MongoDB Atlas cluster

    add_backup_content_cluster()   -- Add backup content to cluster and add test data

    validation_post_restore()  --  Validation of test data post restore

    delete_mongodb_atlas_cluster_cloud_account() -- function to delete cloud account

    add_backup_content_cluster()  --add backup content for cluster

    delete_mongodb_atlas_cluster_cloud_account() --  delete MongoDB Atlas cluster cloud account

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Bigdata.clouddbinstances import CloudDBInstances, MongoDBAtlasInstances
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from Database.MongoDBUtils.mongodbhelper import MongoDBHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Verify MongoDB Atlas cluster in place restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.clouddbinstances = None
        self.mongodbinstance = None
        self.overview = None
        self.restore_obj = None
        self.mongo = None
        self.port = None
        self.access_node_name = None
        self.cluster_name = None
        self.generated_data = None
        self.backup_db_size = None
        self.connection_string = None
        self.generated_data = None
        self.cloud_account_instance = None
        self.plan_name = None
        self.create_new_cloud_account = None
        self.create_new_credential = None
        self.credential_name = None
        self.username = None
        self.password = None
        self.project_name = None
        self.dbprefix = "as" + str(int(time.time()))
        self.tcinputs = {
            'access_node_name': None,
            'cluster_name': None,
            'project_name': None,
            'connection_string': None,
            'cloud_account_instance': None,
            'plan': None,
            'create_new_cloud_account': None,
            'create_new_credential': None,
            'credential_name': None,
            'username': None,
            'password': None
        }

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.overview = Overview(self.admin_console)
            self.restore_obj = Restores(self.admin_console)
            database_helper.set_csdb(CommServDatabase(self.commcell))
            self.access_node_name = str(self.tcinputs['access_node_name'])
            self.cluster_name = str(self.tcinputs['cluster_name'])
            self.cloud_account_instance = str(self.tcinputs['cloud_account_instance'])
            self.connection_string = str(self.tcinputs['connection_string'])
            self.plan_name = str(self.tcinputs['plan'])
            self.create_new_cloud_account = int(self.tcinputs['create_new_cloud_account'])
            self.create_new_credential = int(self.tcinputs['create_new_credential'])
            self.credential_name = str(self.tcinputs['credential_name'])
            self.username = str(self.tcinputs['username']) or None
            self.password = str(self.tcinputs['password']) or None
            self.project_name = str(self.tcinputs['project_name'])
            self.clouddbinstances = CloudDBInstances(self.admin_console)
            self.mongodbinstance = MongoDBAtlasInstances(self.admin_console)
            self.mongo = MongoDBHelper(self.commcell, self.access_node_name, connectionstring=self.connection_string,
                                       atlas=1)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def _backup(self):
        """starts full backup"""
        self.mongodbinstance.access_backup('default')
        snap_job_id = self.admin_console.get_jobid_from_popup()
        snap_job = self.commcell.job_controller.get(snap_job_id)
        self.log.info("Wait for [%s] job to complete", str(snap_job))
        if snap_job.wait_for_completion(500):  # wait for max 500 seconds
            self.log.info("Snap job completed with job id:[%s]", snap_job_id)
        else:
            err_str = "[%s] job id for snap backup job failed" % snap_job_id
            raise CVTestStepFailure(err_str)

    def _restore(self):
        """starts a restore"""
        self.log.info("Dropping the test data generated with database prefix " + self.dbprefix)
        self.mongo.delete_test_data(prefix=self.dbprefix)
        self.log.info("start restore in place")
        self.mongodbinstance.access_restore('default')
        self.overview.restore_all()
        time.sleep(10)
        self.mongodbinstance.in_place_restore_mongodb_atlas_cluster()
        restore_job_id = self.admin_console.get_jobid_from_popup()
        restore_job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Wait for [%s] job to complete", str(restore_job))
        if restore_job.wait_for_completion(500):  # wait for max 500 seconds
            self.log.info("restore job completed with job id:[%s]", restore_job)
        else:
            err_str = "[%s] job id for restore job failed" % restore_job
            raise CVTestStepFailure(err_str)
        self.log.info("Done with restore in place")

    @test_step
    def add_backup_content_cluster(self):
        """Discover clusters and add it to the subclient content , generates data and run backup"""
        self.mongodbinstance.select_add_backup_content('default')
        self.admin_console.wait_for_completion()
        self.mongodbinstance.add_cluster_to_backup_content(self.project_name, self.cluster_name)
        self.generated_data = self.mongo.generate_test_data(database_prefix='atlastest')
        self.log.info("Generated data...")

    @test_step
    def delete_test_data(self):
        """Delete test data generated before backup"""
        self.mongo.delete_test_data(prefix='atlastest')
        self.log.info("Deleted test data...")

    @test_step
    def validation_post_restore(self):
        """Restore database validation"""
        try:
            new_mongo = MongoDBHelper(self.commcell, self.access_node_name, connectionstring=self.connection_string,
                                      atlas=1)
            if new_mongo.validate_restore(self.generated_data, self.access_node_name, self.port):
                self.log.info("Validation of restored data is successful")
            else:
                raise "Validation failed"
        except Exception as exp:
            handle_testcase_exception(self, exp)

    @test_step
    def delete_mongodb_atlas_cluster_cloud_account(self):
        """Delete mongodb atlas cluster instance and cloud account if it exists"""
        mongodb_cloud_account = self.tcinputs['cloud_account_instance']
        self.log.info("deleting [%s] MongoDB atlas cluster instance", mongodb_cloud_account)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.clouddbinstances.delete_mongodb_atlas_cluster_cloud_account(mongodb_cloud_account)
        self.browser.driver.refresh()
        if self.clouddbinstances.is_instance_exists(mongodb_cloud_account):
            raise CVTestStepFailure("[%s] mongoDB server is not getting deleted" %
                                    mongodb_cloud_account)
        self.log.info("Deleted [%s] instance successfully", mongodb_cloud_account)

    def run(self):
        """Run function of this test case
        Check if MongoDB Atlas already exists, if yes delete it
        Create mongoDD Atlas cluster instance
        Discover the projects and DB clusters in it. Add the DB cluster to the subclient content.
        Backup the MongoDB Atlas cluster
        Delete the test data generated.
        Restore the MongoDB Atlas cluster.
        Validate the data restored.
        """

        try:
            self.log.info("Check if the instance with cloud account name already exists, if yes delete it")
            self.log.info(str(self.create_new_cloud_account) + "create_cloud_account")
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            if self.clouddbinstances.is_mongodb_atlas_cloud_account_exists(self.cloud_account_instance):
                self.clouddbinstances.delete_mongodb_atlas_cluster_cloud_account(self.cloud_account_instance)
            self.clouddbinstances.create_mongodb_atlas_cluster(self.cloud_account_instance,
                                                               self.access_node_name, self.credential_name,
                                                               self.plan_name,
                                                               int(self.create_new_cloud_account),
                                                               self.create_new_credential
                                                               , self.username, self.password)
            self.log.info("successfully created MongoDB Atlas cluster")
            self.add_backup_content_cluster()
            self._backup()
            self._restore()
            self.validation_post_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
