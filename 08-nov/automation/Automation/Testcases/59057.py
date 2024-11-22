# -*- coding: utf-8 -*-

# ----------------------------------------------------------d--------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    Input Example:

        "testCases":
            {
                "": {
                    "masterHostname": "<Master hostname>",
                    "port": <port number of mongos/mongod>,
                    "replSet": "<replica set name>",
                    "dbUser": "<MongoDB user>",
                    "dbPassword": "<MongoDB password>",
                    "clientName": "<client naame>",
                    "pseudo_client_name": "<pseudo client name>",
                    "osName": "<OS username>",
                    "plan": "<plan name>",
                    "snap_retention": {"retention_value": "0", "period" : "Day(s)"},
                    "snap_rpo": {"hours": "<hours>", "minutes": "<minutes>"},
                    "database_rpo": {"hours": "<hours>", "minutes": "<minutes>"},
                    "binPath": "<MongoDB binary path>",
                    "engine_name": "<Snap engine>"
                    }
            }
"""
import time
import copy
from cvpysdk.job import JobController

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.idautils import CommonUtils

from Database.MongoDBUtils.mongodbhelper import MongoDBHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Verify PIT in place restore for mongodb"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.instances = None
        self.overview = None
        self.restore_obj = None
        self.mongo = None
        self.port = None
        self.masterhostname = None
        self.generated_data = []
        self.restore_list = None
        self.restore_node_list = None
        self.replica_set_list = None
        self.mongos_start = None
        self.mongod_list = None
        self.replicaset_or_shard = None
        self.start_time_list = None
        self.end_time_list = None
        self.tcinputs = {
            'masterHostname': None,
            'port': None,
            'replSet': None,
            'clientName': None,
            'dbUser': None,
            'dbPassword': None,
            'pseudo_client_name': None,
            'osName': None,
            'plan': None,
            'snap_retention': None,
            'snap_rpo': None,
            'database_rpo': None,
            'binPath': None,
            'engine_name': None
        }

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.start_time_list = []
            self.end_time_list = []
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser,
                                              self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_plan()
            Plans(self.admin_console).select_plan(self.tcinputs['plan'])
            time.sleep(30)
            plan_details = PlanDetails(self.admin_console)
            # plan_details.edit_snapshot_options(
            # self.tcinputs['snap_rpo'],retention_period=self.tcinputs['snap_retention'])
            plan_details.edit_database_options(self.tcinputs['database_rpo'])
            self.log.info('Database RPO is set in plan '
                          '' + str(self.tcinputs['plan']) + ' to '
                          + str(self.tcinputs['database_rpo']))
            self.navigator.navigate_to_big_data()
            self.instances = Instances(self.admin_console)
            # deletion if instance exists
            if self.instances.is_instance_exists(self.tcinputs['pseudo_client_name']):
                self.delete_monogodb_instance()
            self.overview = Overview(self.admin_console)
            self.restore_obj = Restores(self.admin_console)
            database_helper.set_csdb(CommServDatabase(self.commcell))
            self.port = int(self.tcinputs['port'])
            self.masterhostname = self.tcinputs['masterHostname']
            self.mongo = MongoDBHelper(self.commcell,
                                       self.masterhostname, self.port, self.tcinputs['dbUser'],
                                       self.tcinputs['dbPassword'],
                                       replset=self.tcinputs['replSet'] or None,
                                       bin_path=self.tcinputs['binPath'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def _update_job_time(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

        Returns:  Job start and end time
        """
        job_obj = self.commcell.job_controller.get(jobid)
        start_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['jobStartTime']))
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        self.start_time_list.append(start_time)
        self.end_time_list.append(end_time)
        self.log.info('For job ID:'
                      '' + str(jobid) + ' start time is '
                      + start_time + ' and end time is ' + end_time)

    def _backup(self):
        """starts full backup"""
        cutils = CommonUtils(self.commcell)
        time.sleep(5)
        self.admin_console.click_button("OK")
        snap_job_id = self.admin_console.get_jobid_from_popup()
        time.sleep(5)
        snap_job = self.commcell.job_controller.get(snap_job_id)
        self.log.info("Wait for [%s] job to complete", str(snap_job))
        if snap_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Snap job completed with job id:[%s]", snap_job_id)
        else:
            err_str = "[%s] job id for snap backup job failed" % snap_job_id
            raise CVTestStepFailure(err_str)
        time.sleep(5)
        self.log.info("Running inline backup copy")
        backupcopy_job_id = cutils.get_backup_copy_job_id(snap_job_id)
        backupcopy_job = self.commcell.job_controller.get(backupcopy_job_id)
        self.log.info("Wait for [%s] job to complete", str(backupcopy_job))
        if backupcopy_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Backup copy job completed with job id:[%s]", backupcopy_job_id)
        else:
            err_str = "[%s] job id for backup copy job failed" % backupcopy_job_id
            raise CVTestStepFailure(err_str)
        self._update_job_time(snap_job_id)
        return backupcopy_job_id

    def _restore(self):
        """starts a restore"""
        self.log.info("start restore in place")
        self.overview.restore_all()
        time.sleep(10)
        self.restore_obj.restore_in_place()
        restore_job_id = self.admin_console.get_jobid_from_popup()
        restore_job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Wait for [%s] job to complete", str(restore_job))
        if restore_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("restore job completed with job id:[%s]", restore_job)
        else:
            err_str = "[%s] job id for restore job failed" % restore_job
            raise CVTestStepFailure(err_str)
        self.log.info("Done with restore in place")

    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        conf = self.overview.access_configuration()
        time.sleep(5)
        conf.discover_nodes()
        self.log.info("Discovered nodes successfully")
        nodetable = Table(self.admin_console)
        clientlist = nodetable.get_column_data('Name')
        portlist = nodetable.get_column_data('Port number')
        servertypelist = nodetable.get_column_data('Server type')
        self.log.info("Discovery validation from csdb")
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        if self.mongo.validate_discovery_of_nodes(mongodb_server_name,
                                                  portlist, clientlist, servertypelist):
            self.log.info("Discovery validation is successful")
        else:
            self.log.info("Discovery validation failed")
        self.log.info("Editing engine")
        conf.edit_snapshot_engine(self.tcinputs["engine_name"])
        self.log.info("Successfully edited")
        self.replicaset_or_shard = \
            self.mongo.check_shardedcluster_or_replicaset(mongodb_server_name)
        self.replica_set_list = conf.get_replica_set_list()
        self.generated_data.append(self.mongo.generate_test_data(database_prefix='PITFull',
                                                                 num_dbs=1, num_col=2, num_docs=5))
        self.log.info(str(self.generated_data))
        self.log.info("Generated data...")
        conf.access_backup()
        temp_job = self._backup()
        for iteration in range(2):
            self.log.info("Generating data to trigger an incremental job")
            temp = {}
            temp = copy.deepcopy(self.generated_data[iteration])
            temp.update(self.mongo.generate_test_data(database_prefix='PITInc'+str(iteration),
                                                      num_dbs=1, num_col=2, num_docs=5))
            self.log.info("Temp data generated in this iteration:"+str(temp))
            self.log.info("Generated Data...")
            self.generated_data.append(temp)
            log_rpo = dict(self.tcinputs['database_rpo'])
            time.sleep(int(log_rpo['hours']) * 3600 + int(log_rpo['minutes']) * 60 + 60)
            job_controller_object = JobController(self.commcell)
            while job_controller_object.active_jobs(mongodb_server_name) != {}:
                self.log.info("Active jobs are present for {0}".format(mongodb_server_name))
                self.log.info("Waiting for all the active jobs to be completed.")
                time.sleep(60)
            jobid_list = list(job_controller_object.finished_jobs(
                mongodb_server_name, job_filter='Backup').keys())
            job = job_controller_object.get(jobid_list[0])
            if job.job_id > temp_job and job.backup_level == "Incremental":
                self.log.info("Successfully ran incremental job [%s]", job)
                temp_job = job.job_id
                self._update_job_time(temp_job)
            else:
                err_str = "No incremental job was triggered"
                raise CVTestStepFailure(err_str)
        conf.disable_backup()
        self.log.info("Data generated is " + str(self.generated_data))

    @test_step
    def shutdown_servers_and_restore_by_time(self, from_time, to_time):
        """get start commands,shutdown servers and starts restore"""
        conf = self.overview.access_configuration()
        if self.replicaset_or_shard == 1:
            self.log.info("A sharded cluster")
            self.mongos_start = self.mongo.get_mongos_start_command_from_csdb()
        self.log.info("shutting down replica set")
        self.mongod_list = self.mongo.get_mongod_start_command_from_csdb()
        self.mongo.shutdown_server_and_cleanup_using_command()
        self.log.info("replica set are offline")
        conf.access_overview()
        self.admin_console.tile_select_hyperlink("Recovery point", "Restore")
        browse = Browse(self.admin_console)
        from_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                  time.localtime(time.mktime(
                                      time.strptime(from_time, '%d-%B-%Y-%I-%M-%p')) - 60))
        to_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                time.localtime(time.mktime(
                                    time.strptime(to_time, '%d-%B-%Y-%I-%M-%p')) + 60))
        self.log.info("Perform restore in backup range: " + from_time + " to " + to_time)
        browse.show_backups_by_date_range(from_time=from_time, to_time=to_time)
        # Nodes the data is being restored to
        self.restore_list = browse.get_column_data("Backup host:port")
        self.log.info(self.restore_list)
        self.restore_node_list = browse.get_restore_nodelist()
        self._restore()

    @test_step
    def validation_post_restore(self, generated_data):
        """Restore database validation based on size and count"""
        restore_client, restore_port = [], []
        for _ in self.restore_list:
            temp = _.split("::")
            restore_client.append(temp[0])
            restore_port.append(int(temp[1]))
        if self.replicaset_or_shard == 1:
            self.log.info("Disable authentication in mongos")
            tempmongos_cmd = self.mongo.disable_authentication_mongos(self.mongos_start)
            self.log.info("Start mongos without authentication")
            self.mongo.start_mongos_server(tempmongos_cmd)
            if self.mongo.validate_restore(generated_data, self.masterhostname, self.port):
                self.log.info("Validation of restored data is successful")
        else:
            if self.mongo.validate_restore(generated_data, restore_client[0], restore_port[0]):
                self.log.info("Validation of restored data is successful")

    @test_step
    def shutdown_and_restart_servers(self):
        """shutting down restored servers and starting original servers"""
        self.log.info("Shutting down the restored nodes")
        self.mongo.shutdown_server_using_kill_command()
        self.log.info("Restored nodes are offline")
        time.sleep(120)
        self.log.info("Starting replica set nodes")
        self.mongo.start_mongod_services(self.mongod_list)
        self.log.info("Initiating replica set and its members")
        self.mongo.initiate_replicaset_or_shard(self.restore_node_list, self.replica_set_list)
        if self.replicaset_or_shard == 1:
            self.log.info("starting mongos with authentication")
            self.mongo.start_mongos_server(self.mongos_start)

    @test_step
    def delete_monogodb_instance(self):
        """Delete mongodb instance"""
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        self.log.info("deleting [%s] instance", mongodb_server_name)
        self.navigator.navigate_to_big_data()
        self.instances.delete_instance_name(mongodb_server_name)
        self.browser.driver.refresh()
        if self.instances.is_instance_exists(mongodb_server_name):
            raise CVTestStepFailure("[%s] mongoDB server is not getting deleted" %
                                    mongodb_server_name)
        self.log.info("Deleted [%s] instance successfully", mongodb_server_name)

    def run(self):
        """Run function of this test case
        Create mongoDb instance
        access configuration and discover nodes
        In configuration page:
            get client list,port list
            check weather we are dealing with sharded cluster or replicaset
            get replica set list and mongos list
            Generate data and start full backup
            generate data and wait for incremental backup1 post Log RPO time
            generate data and start incremental backup2 post Log RPO time
        After backup,
            Get mongo start commands for replica set and sharded cluster
            Shut down and clean up the replica set list and sharded cluster
        Navigate to overview page,
            Select restore with specific browse range(end time of full backup,
            end time of incremental backup 1, end time incremental backup2)
        In restore page:
            get restore node list --- the ports we will start in the end
            get restored nodes list --- the ports the data is being restored to
            start in place restore
        After restore,
            For sharded cluster, disable authentication and start mongos to validate restored data
            For replica set, validate restored data
        After validation on each restore case one after the other,
            shutdown the restored nodes
            start replicaset nodes and initiate replica set
            For sharded cluster, shutdown mongos and start mongos(with authentication)
        """
        try:
            self.log.info("creating pseudo client")
            self.instances.create_mongodb_instance(master_node=self.tcinputs['clientName'],
                                                   name=self.tcinputs['pseudo_client_name'],
                                                   os_name=self.tcinputs['osName'],
                                                   db_user=self.tcinputs['dbUser'],
                                                   db_pwd=self.tcinputs['dbPassword'],
                                                   plan=self.tcinputs['plan'],
                                                   bin_path=self.tcinputs['binPath'],
                                                   port_number=self.port)
            self.log.info("successfully created pseudo client")
            self.discover_and_backup()
            time.sleep(90)
            for iteration in range(3):
                self.navigator.navigate_to_big_data()
                self.instances.access_instance(self.tcinputs['pseudo_client_name'])
                self.shutdown_servers_and_restore_by_time(
                    self.start_time_list[0], self.end_time_list[iteration])
                self.log.info("Data generated is "+str(
                    self.generated_data[iteration])+" in iteration:"+str(iteration))
                self.validation_post_restore(self.generated_data[iteration])
                self.shutdown_and_restart_servers()
            self.delete_monogodb_instance()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
