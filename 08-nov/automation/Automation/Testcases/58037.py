# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
This is a template test case to trigger backup job

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""
import time
from cvpysdk.job import Job, JobController

from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.idautils import CommonUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Components.browse import Browse
from Database.MongoDBUtils.mongodbhelper import MongoDBHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of File System backup and Restore test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Verify out of place restore for mongodb"
        self.admin_console = None
        self.browser = None
        self.navigator = None
        self.mongodb_helper = None
        self.mongodb_inst = None
        self.mongodb_s_list = None
        self.mongodb_daemon_start = None
        self.overview = None
        self.master_node = None
        self.mongodb_client_name = None
        self.restore_obj = None
        self.client_port_map = None
        self.data_files = None
        self.des_port = None
        self.des_host = None
        self.db_user = None
        self.db_pwd = None
        self.generated_data = None
        self.data_files_details = None
        self.replica_set_or_shard = None
        self.mongodb_s_start = None
        self.replica_set_list = None
        self.replica_set = None
        self.restore_list = None
        self.restore_nodelist = None
        self.backup_data_size = None
        self.browse_obj = None
        self.tcinputs = {
            "master_node": None,
            "pseudo_client_name": None,
            "des_host": None,
            "des_port": None,
            "db_user": None,
            "db_pwd": None,
            "os_name": None,
            "data_files_details": None,
            "replica_set": None,
            "engine_name": None,
            "bin_path": None,
            "plan": None
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
            self.navigator.navigate_to_big_data()
            self.mongodb_inst = Instances(self.admin_console)
            if self.mongodb_inst.is_instance_exists(self.tcinputs['pseudo_client_name']):
                self.delete_mongodb_instance()
            self.overview = Overview(self.admin_console)
            self.restore_obj = Restores(self.admin_console)
            database_helper.set_csdb(CommServDatabase(self.commcell))
            self.master_node = self.tcinputs['master_node']
            self.mongodb_client_name = self.tcinputs['pseudo_client_name']
            self.des_host = self.tcinputs['des_host']
            self.des_port = self.tcinputs['des_port']
            self.db_user = self.tcinputs['db_user']
            self.db_pwd = self.tcinputs['db_pwd']
            self.data_files_details = self.tcinputs['data_files_details']
            self.replica_set = self.tcinputs['replica_set']
            self.browse_obj = Browse(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Pre-requisites for this test case"""
        self.init_tc()
        self.log.info("Initializing pre-requisites")

    def _backup(self):
        """starts full backup"""
        common_utils = CommonUtils(self.commcell)
        self.admin_console.click_button("OK")
        snap_job_id = self.admin_console.get_jobid_from_popup()
        snap_job = self.commcell.job_controller.get(snap_job_id)
        self.log.info("Wait for [%s] job to complete", str(snap_job))
        if snap_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Snap Backup job completed with job id:[%s]", snap_job_id)
        else:
            err_str = "[%s] job id for backup job failed" % snap_job_id
            raise CVTestStepFailure(err_str)
        self.log.info("Running inline backup copy")
        backup_copy_job_id = common_utils.get_backup_copy_job_id(snap_job_id)
        backup_copy_job = self.commcell.job_controller.get(backup_copy_job_id)
        self.log.info("Wait for [%s] job to complete", str(backup_copy_job))
        if backup_copy_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Backup Copy job completed with job id:[%s]", backup_copy_job_id)
        else:
            err_str = "[%s] job id for backup job failed" % backup_copy_job_id
            raise CVTestStepFailure(err_str)

    def _restore(self):
        """starts a restore"""
        self.overview.restore_all()
        self.log.info("Starting Restore Out of place module")
        self.log.info("Destination cluster chosen [%s]", self.mongodb_client_name)
        self.restore_obj.restore_out_of_place(self.mongodb_client_name, self.data_files)

        restore_job_id = self.admin_console.get_jobid_from_popup()
        restore_job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Wait for [%s] job to complete", str(restore_job))
        if restore_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("restore job completed with job id:[%s]", restore_job_id)
        else:
            err_str = "[%s] job id for restore job failed" % restore_job_id
            raise CVTestStepFailure(err_str)
        self.log.info("Done with restore out of place")

    def generate_default_data_files_details(self, browse_obj, clt_prt, data_files_details=None):
        """ generates data_files_details to be filled at time of restore out of place
            browse_obj : Browse Object
            cl : Dictionary where key is port and value is host name
            data_files_details : user enter this data_files_details
        """
        data_files = browse_obj.get_column_data("Replica set")
        host_port = browse_obj.get_column_data("Backup host:port")
        default_data_files = {}
        for i, data in enumerate(data_files):
            host = host_port[i].split('::')[0]
            port = host_port[i].split('::')[1]
            default_data_files[data] = {'Hostname': host, 'Port Number': port}

        for i, data in enumerate(data_files):
            default_data_files[data]['Hostname'] = \
                clt_prt[default_data_files[data_files[i]]['Port Number']]

        if data_files_details is not None:
            for i in data_files_details.keys():
                if i in default_data_files.keys():
                    default_data_files[i] = data_files_details[i]

        self.log.info('FINAL details for restore : ')
        self.log.info(default_data_files)

        return default_data_files

    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        dis = self.overview.access_configuration()
        self.log.info("Switched to Configuration TAB")
        dis.discover_nodes()
        self.admin_console.driver.refresh()
        time.sleep(30)
        self.log.info("Nodes discovered successfully")

        node_table = Table(self.admin_console)
        client_list = node_table.get_column_data('Name')
        self.log.info("client_list fetched [%s]", client_list)
        port_list = node_table.get_column_data('Port number')
        self.log.info("port_list fetched [%s]", port_list)
        server_type_list = node_table.get_column_data('Server type')
        self.log.info("Server type fetched [%s]", server_type_list)

        self.client_port_map = {}
        for i, port in enumerate(port_list):
            self.client_port_map[port] = client_list[i]

        # for mongodb (sharded cluster) case
        # self.mongodb_helper = MongoDBHelper(self.commcell, self.master_node, self.des_port,
        #                                     self.db_user, self.db_pwd,
        #                                     bin_path=self.tcinputs['bin_path'])

        # for replica set case pass one more argument as self.replica_set
        self.mongodb_helper = MongoDBHelper(self.commcell, self.master_node, self.des_port,
                                            self.db_user, self.db_pwd,
                                            replset=self.replica_set,
                                            bin_path=self.tcinputs['bin_path'])

        self.log.info("Mongodb Helper Object created successfully")

        if self.mongodb_helper.validate_discovery_of_nodes(self.mongodb_client_name, port_list,
                                                           client_list, server_type_list):
            self.log.info("Discovery of Nodes validation successful")
        else:
            self.log.info("Discovery of Nodes validation unsuccessful")
        self.admin_console.driver.refresh()
        time.sleep(15)
        dis.edit_snapshot_engine(self.tcinputs["engine_name"])
        self.log.info("Snapshot Engine edited")
        self.replica_set_or_shard = \
            self.mongodb_helper.check_shardedcluster_or_replicaset(self.mongodb_client_name)
        if self.replica_set_or_shard == 0:
            self.log.info("Replica set Discovered")
        else:
            self.log.info("Sharded Cluster Discovered")

        self.replica_set_list = dis.get_replica_set_list()
        self.log.info("Replica set List generated successfully")
        self.log.info(self.replica_set_list)
        self.generated_data = self.mongodb_helper.generate_test_data()
        self.log.info("Data Populated successfully")
        self.log.info("[%s]", self.generated_data)

        # this phase is to check whether there is an active job associated
        #     with the client or not, if there then it will kill

        job_controller_object = JobController(self.commcell)
        active_jobs = job_controller_object.active_jobs(self.mongodb_client_name)
        self.log.info('active jobs for client = %s', active_jobs)
        if active_jobs:
            for i in active_jobs:
                j = Job(self.commcell, i)
                j.kill(wait_for_job_to_kill=True)
                print("job ", active_jobs, " killed")

        time.sleep(10)

        self.log.info("Backup starting........")
        dis.access_backup()
        self._backup()
        self.log.info("Backup successfully completed")
        self.log.info('BACKUP finished.........')
        self.backup_data_size = self.mongodb_helper.get_db_server_size()
        self.log.info('Getting Db Size after backup : %s', self.backup_data_size)

    @test_step
    def shutdown_servers_and_restore(self):
        """get start commands,shutdown servers and starts restore"""
        self.log.info("Restore part starts........")
        conf = self.overview.access_configuration()
        conf.access_overview()
        self.overview.access_restore(self.mongodb_client_name)
        self.log.info("Accessed Restore ")
        time.sleep(15)
        self.data_files = self.generate_default_data_files_details(self.browse_obj,
                                                                   self.client_port_map)
        self.log.info("Generate data files details (user's passed)")
        self.log.info("data files details : ")
        self.log.info(self.data_files)
        self.restore_list = self.browse_obj.get_column_data("Backup host:port")
        self.log.info(" Restore List = ")
        self.log.info(self.restore_list)
        self.restore_nodelist = self.browse_obj.get_restore_nodelist()
        self.log.info("Restore NodeList generated successfully")
        self.log.info(self.restore_nodelist)

        if self.replica_set_or_shard == 1:
            self.log.info("A sharded cluster")
            self.mongodb_s_start = self.mongodb_helper.get_mongos_start_command_from_csdb()
            self.log.info("mongodb sharded servers start commands generated successfully from CSDB")
            self.log.info(self.mongodb_s_start)

        self.mongodb_daemon_start = self.mongodb_helper.get_mongod_start_command_from_csdb()
        self.log.info("mongodb daemon servers start commands generated successfully from CSDB")
        self.log.info(self.mongodb_daemon_start)
        self.log.info('Shutting down mongodb servers..............')
        self.mongodb_helper.shutdown_server_and_cleanup_using_command()
        self.log.info("Mongodb servers successfully shutdown with db path cleaned up")
        self._restore()

    @test_step
    def validation_post_restore(self):
        """Restore database validation based on size and count"""
        restore_client, restore_port = [], []
        for _ in self.restore_list:
            data = _.split("::")
            restore_client.append(data[0])
            restore_port.append(int(data[1]))

        if self.replica_set_or_shard == 0:
            self.log.info("Validate Restore , Replica set")
            k = list(self.data_files.keys())[0]
            des_host = self.data_files[k]['Hostname']
            des_cl_machine = self.commcell.clients.get(des_host)
            des_host = str(des_cl_machine.client_hostname)
            des_port = int(self.data_files[k]['Port Number'])
            self.log.info('Validation Started')
            self.log.info('Destination Host = ')
            self.log.info(des_host)
            self.log.info('Destination Port = ')
            self.log.info(des_port)
            self.log.info('Auto generated data list = ')
            self.log.info(self.generated_data)
            self.log.info("Validation Started")
            mongodb_helper_2 = MongoDBHelper(self.commcell, des_host, des_port, '', '')
            self.log.info("Mongodb Helper successfully created")
            restore_data_size = mongodb_helper_2.get_db_server_size()
            self.log.info("db size get...")
            if self.backup_data_size == restore_data_size:
                self.log.info("Validation of db server size is Successful")
            else:
                self.log.info("Validation of db server size is Unsuccessful")

            if self.mongodb_helper.validate_restore(self.generated_data, des_host, des_port):
                self.log.info("Validation of Restored Data is successful")
            else:
                self.log.info("Validation of Restored Data is unsuccessful")

        else:
            mongodb_s_cmd = self.mongodb_helper.disable_authentication_mongos(self.mongodb_s_start)
            self.log.info("authentication disabled for mongodb sharded cluster ")
            self.mongodb_helper.start_mongos_server(mongodb_s_cmd)
            self.log.info("Mongodb sharded cluster server started without authentication enable")
            mongodb_helper_2 = MongoDBHelper(self.commcell, self.des_host, self.des_port, '', '')
            self.log.info("Validation of Restore started")
            restore_data_size = mongodb_helper_2.get_db_server_size()
            if self.backup_data_size == restore_data_size:
                self.log.info("Validation of db server size is successful")
            else:
                self.log.info("Restore db size is not equal to backed up db server size")

            if self.mongodb_helper.validate_restore(self.generated_data,
                                                    self.des_host,
                                                    self.des_port):
                self.log.info("Validation of Restored Data is successful")
            else:
                self.log.info("Validation of Restored Data is unsuccessful")

    @test_step
    def shutdown_and_restart_servers(self):
        """shutting down restored servers and starting original servers"""
        self.log.info("Shutting down the restored nodes")
        self.mongodb_helper.shutdown_server_using_kill_command()
        time.sleep(15)
        self.log.info("Restored nodes are offline")
        self.log.info("Starting replica set nodes")
        self.mongodb_helper.start_mongod_services(self.mongodb_daemon_start)
        self.log.info("Initiating replica set and its members")
        time.sleep(15)
        self.mongodb_helper.initiate_replicaset_or_shard(self.restore_nodelist,
                                                         self.replica_set_list)

        if self.replica_set_or_shard == 1:
            self.log.info("starting mongodb sharded cluster with authentication")
            self.mongodb_helper.start_mongos_server(self.mongodb_s_start)

    @test_step
    def delete_mongodb_instance(self):
        """Delete mongodb instance"""
        mongodb_client_name = self.tcinputs['pseudo_client_name']
        self.log.info("deleting [%s] instance", mongodb_client_name)
        self.navigator.navigate_to_big_data()
        self.mongodb_inst.delete_instance_name(mongodb_client_name)
        self.browser.driver.refresh()
        if self.mongodb_inst.is_instance_exists(mongodb_client_name):
            raise CVTestStepFailure("[%s] mongodb server is not getting deleted" %
                                    mongodb_client_name)
        self.log.info("Deleted [%s] instance successfully", mongodb_client_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Creating Mongodb pseudo client")
            self.mongodb_inst.create_mongodb_instance(master_node=self.master_node,
                                                      name=self.mongodb_client_name,
                                                      os_name=self.tcinputs['os_name'],
                                                      db_user=self.db_user,
                                                      db_pwd=self.db_pwd,
                                                      plan=self.tcinputs['plan'],
                                                      port_number=self.des_port,
                                                      bin_path=self.tcinputs['bin_path'])
            self.log.info("Mongodb pseudo client created successfully")
            self.discover_and_backup()
            self.shutdown_servers_and_restore()
            self.validation_post_restore()
            self.shutdown_and_restart_servers()
            self.log.info('Deleting pseudo client ')
            self.delete_mongodb_instance()
            self.log.info('Deletion success !!!')

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Clean up function for this test case"""
        self.log.info("Performing cleanup")
