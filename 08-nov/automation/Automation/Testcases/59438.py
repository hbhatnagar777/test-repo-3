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
        "testCases":{
            "59438":
            {
            "masterHostname": "<Master hostname>",
            "port": "<port number of mongos/mongod>",
            "clientName": "<master node client name>",
            "pseudo_client_name": "<pseudo client name>",
            "plan": "<plan name>",
            "database_rpo": {"hours": "<hours>", "minutes": "<minutes>"},
            "dbUser": "<MongoDB user>"  (optional, use if mongodb user is configured),
            "dbPassword": "<MongoDB password>"  (optional, use if mongodb password is configured),
            "replSet": "<replica set name>"  (optional, use if running the tc for replica set),
            "osName": "<OS username>"   (optional, used for pseudo client creation),
            "binPath": "<MongoDB binary path>" (optional),
            "plan": "<plan name>"   (optional, required for client creation),
            "engine_name": "<Snap engine>"  (optional, default:Native),
            "validate_discovery": "<true/false>" (optional, cross checks with csdb)
            }
        }
"""
import copy
import time
from cvpysdk.job import JobController

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import PanelInfo
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
        self.name = "MongoDB IDA Command Center - ACCT1 PIT In Place Granular Restore With " \
                    "Overwrite"
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
        self.backup_hash = []
        self.replicaset_or_shard = None
        self.old_database_rpo = None
        self.start_time_list = None
        self.end_time_list = None
        self.tcinputs = {
            'masterHostname': None,
            'port': None,
            'clientName': None,
            'pseudo_client_name': None,
            'plan': None,
            'database_rpo': None
        }

    def _edit_plan(self, plan_reset=False):
        """Edits plan with given rpo"""
        self.navigator.navigate_to_plan()
        plan = self.tcinputs['plan']
        Plans(self.admin_console).select_plan(plan)
        plan_details = PlanDetails(self.admin_console)
        if not plan_reset:
            self.old_database_rpo = {"hours": "0", "minutes": "0"}
            rpo = PanelInfo(self.admin_console, "Database options").get_details()['Log backup RPO']
            rpo = rpo.split(" and ")
            for value in rpo:
                if "hour" in value:
                    self.old_database_rpo["hours"] = value.split()[0]
                elif "minute" in value:
                    self.old_database_rpo["minutes"] = value.split()[0]
            self.log.info(f"Current Database RPO for {plan} is: {self.old_database_rpo}")
            log_rpo = self.tcinputs['database_rpo']
            self.log.info(f"Database RPO for {plan} will be changed to: {log_rpo}")
        else:
            log_rpo = self.old_database_rpo
            self.log.info(f"Database RPO for {plan} will be changed back to old log rpo: {log_rpo}")
        plan_details.edit_database_options(log_rpo)
        self.log.info(f'Database RPO is set in plan {plan} to {log_rpo}')

    def setup(self):
        """Setup function of this test case"""
        self.start_time_list = []
        self.end_time_list = []
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self._edit_plan()
        self.navigator.navigate_to_big_data()
        self.instances = Instances(self.admin_console)
        self.overview = Overview(self.admin_console)
        self.restore_obj = Restores(self.admin_console)
        database_helper.set_csdb(CommServDatabase(self.commcell))
        self.port = int(self.tcinputs.get('port'))
        self.masterhostname = self.tcinputs['masterHostname']
        self.mongo = MongoDBHelper(self.commcell, self.masterhostname,
                                   self.port, self.tcinputs.get('dbUser') or '',
                                   self.tcinputs.get('dbPassword') or '',
                                   replset=self.tcinputs.get('replSet'),
                                   bin_path=self.tcinputs.get('binPath'))
        self.mongo.delete_test_data()

    def _update_job_time(self, job_id):
        """Updates job start time and end time
        Args:
            job_id   (int): Job id
        """
        job_obj = self.commcell.job_controller.get(job_id)
        start_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['jobStartTime']))
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        self.start_time_list.append(start_time)
        self.end_time_list.append(end_time)
        self.log.info(f"For job ID: {job_id} start time is {start_time} and end time is {end_time}")

    def _wait_for_job_completion(self, job_id):
        """wait till job gets completed
        Args:
            job_id     (int)      -- Job id
        """
        job_obj = self.commcell.job_controller.get(job_id)
        self.log.info("Wait for [%s] job to complete", str(job_obj.job_type))
        if job_obj.wait_for_completion():
            self.log.info("[%s] job completed with job id:[%s]", job_obj.job_type, job_id)
        else:
            err_str = "[%s] job id for [%s] failed" % (job_id, job_obj.job_type)
            raise CVTestStepFailure(err_str)

    def _backup(self):
        """starts full backup"""
        cutils = CommonUtils(self.commcell)
        self.admin_console.click_button("OK")
        self.log.info("Start snap backup")
        snap_job_id = self.admin_console.get_jobid_from_popup()
        self._wait_for_job_completion(snap_job_id)
        self.log.info("Done with Snap backup")
        time.sleep(5)
        self.log.info("Running inline backup copy")
        backupcopy_job_id = cutils.get_backup_copy_job_id(snap_job_id)
        self._wait_for_job_completion(backupcopy_job_id)
        self.log.info("Done with Backup copy")
        self._update_job_time(snap_job_id)
        return backupcopy_job_id

    def _restore(self):
        """starts a restore"""
        self.log.info("start restore in place")
        self.overview.restore_all()
        self.restore_obj.restore_in_place(overwrite=True)
        restore_job_id = self.admin_console.get_jobid_from_popup()
        self._wait_for_job_completion(restore_job_id)
        self.log.info("Done with restore in place")

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        if self.instances.is_instance_exists(self.tcinputs['pseudo_client_name']):
            self.log.info(f"Using the existing pseudo client: "
                          f"{self.tcinputs['pseudo_client_name']} to run the testcase")
            self.instances.access_instance(self.tcinputs['pseudo_client_name'])
        else:
            self.log.info("creating pseudo client")
            if not self.tcinputs.get('plan'):
                raise CVTestCaseInitFailure("Plan is required for creating new instance")
            self.instances.create_mongodb_instance(master_node=self.tcinputs['clientName'],
                                                   name=self.tcinputs['pseudo_client_name'],
                                                   os_name=self.tcinputs.get('osName'),
                                                   db_user=self.tcinputs.get('dbUser'),
                                                   db_pwd=self.tcinputs.get('dbPassword'),
                                                   plan=self.tcinputs['plan'],
                                                   bin_path=self.tcinputs.get('binPath'),
                                                   port_number=self.port)
            self.log.info("successfully created pseudo client")

    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        conf = self.overview.access_configuration()
        time.sleep(5)
        conf.discover_nodes()
        time.sleep(10)
        self.log.info("Discovered nodes successfully")
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        if self.tcinputs.get('validate_discovery'):
            nodetable = Table(self.admin_console)
            clientlist = nodetable.get_column_data('Name')
            portlist = nodetable.get_column_data('Port number')
            servertypelist = nodetable.get_column_data('Server type')
            self.log.info("Discovery validation from csdb")
            if self.mongo.validate_discovery_of_nodes(
                    mongodb_server_name, portlist, clientlist, servertypelist):
                self.log.info("Discovery validation is successful")
            else:
                self.log.info("Discovery validation failed")
                raise CVTestStepFailure("Discovery validation failed")
        if self.tcinputs.get("engine_name"):
            self.log.info("Editing engine")
            conf.edit_snapshot_engine(self.tcinputs["engine_name"])
            self.log.info("Successfully edited")
        self.generated_data.append(self.mongo.generate_test_data(database_prefix='PITFull',
                                                                 num_dbs=1, num_col=2, num_docs=5))
        self.backup_hash.append(self.mongo.get_data_hash(self.generated_data[-1]))
        self.log.info(str(self.generated_data))
        self.log.info("Generated data...")
        conf.access_backup()
        temp_job = self._backup()
        for iteration in range(2):
            self.log.info("Generating data to trigger an incremental job")
            temp = copy.deepcopy(self.generated_data[iteration])
            temp.update(self.mongo.generate_test_data(database_prefix='PITInc'+str(iteration),
                                                      num_dbs=1, num_col=2, num_docs=5))
            self.log.info("Temp data generated in this iteration:"+str(temp))
            self.log.info("Generated Data...")
            self.generated_data.append(temp)
            self.backup_hash.append(self.mongo.get_data_hash(self.generated_data[-1]))
            log_rpo = dict(self.tcinputs['database_rpo'])
            time.sleep(int(log_rpo['hours']) * 3600 + int(log_rpo['minutes']) * 60 + 60)
            job_controller_object = JobController(self.commcell)
            while job_controller_object.active_jobs(mongodb_server_name, job_filter="Backup") != {}:
                self.log.info("Active backup jobs are present for {0}".format(mongodb_server_name))
                self.log.info("Waiting for all the active backup jobs to be completed.")
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
    def restore_by_time_and_validate(self, from_time, to_time, iteration):
        """starts restore of databases based on time and validates
        Args:
            from_time       (str)       --  start time
            to_time         (str)       --  end time
            iteration       (int)       --  job iteration
        """
        conf = self.overview.access_configuration()
        conf.access_overview()
        self.admin_console.tile_select_hyperlink("Recovery point", "Restore")
        browse = Browse(self.admin_console)
        browse.switch_to_collections_view()
        from_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                  time.localtime(time.mktime(
                                      time.strptime(from_time, '%d-%B-%Y-%I-%M-%p')) - 60))
        to_time = time.strftime('%d-%B-%Y-%I-%M-%p',
                                time.localtime(time.mktime(
                                    time.strptime(to_time, '%d-%B-%Y-%I-%M-%p')) + 60))
        self.log.info("Perform restore in backup range: " + from_time + " to " + to_time)
        browse.show_backups_by_date_range(from_time=from_time, to_time=to_time)
        self._restore()
        if self.mongo.validate_restore(self.generated_data[iteration], self.tcinputs['clientName'],
                                       self.port, self.tcinputs.get('dbUser') or '',
                                       self.tcinputs.get('dbPassword') or '',
                                       backup_hash=self.backup_hash[iteration]):
            self.log.info("Validation of restored data is successful")
        else:
            self.log.info("Validation failed")

    def run(self):
        """
        Run function of this test case
        Create MongoDB instance if required
        access configuration and discover nodes
        In configuration page:
            Discover nodes
            Generate data and start full backup
            generate data and wait for incremental backup1 post Log RPO time
            generate data and start incremental backup2 post Log RPO time
        After backup navigate to overview page,
            Select restore with specific browse range(end time of full backup,
            end time of incremental backup 1, end time incremental backup2)
        In restore page:
            Select restore at database/collection level
            start in place restore with overwrite option enabled
        After each restore,
            validate restored data
        After validation,
            Delete generated data
        """
        try:
            self.access_or_create_client()
            self.discover_and_backup()
            time.sleep(90)
            pseudo_client = self.tcinputs['pseudo_client_name']
            for iteration in range(3):
                if iteration != 0:
                    self.admin_console.select_breadcrumb_link_using_text(pseudo_client)
                self.log.info(f"Data generated is {self.generated_data[iteration]} in iteration:"
                              f"{iteration}")
                self.restore_by_time_and_validate(self.start_time_list[0],
                                                  self.end_time_list[iteration], iteration)
            self.admin_console.select_breadcrumb_link_using_text(pseudo_client)
            conf = self.overview.access_configuration()
            conf.enable_backup()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.mongo.delete_test_data(prefix='PIT')
        self._edit_plan(plan_reset=True)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
