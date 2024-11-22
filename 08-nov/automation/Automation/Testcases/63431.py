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
    __init__()                    -- initialize TestCase class
    setup()                       -- setup method for test case
    tear_down()                   -- tear down method for test case
    run()                         -- run function of this test case
    set_backup_to_disk_cache()    -- Sets log backup to disk cache option for the plan
    navigate_to_source_subclient()       -- Navigates to details page for default subclient
    create_source_ifx_helper_obj()      -- Creates informix helper object for source instance
    create_destination_ifx_helper_obj() -- Creates informix helper object for destination instance
    wait_for_job_completion()     -- Wait for completion of job and check job status
    run_backup()                  -- Submit backup and return backup job id
    restore_and_validate()        -- Submit restore, validate data restored and return job id
    feature_validation()          -- Confirm the restore used right source
    run_sweep_job()               -- Runs sweep job and returns sweep job id
    get_client_list()             -- Gets list of client IDs for which entries need to be
    deleted from APP_clientAccessControl table

Input Example:
    "testCases":
        {
            "63431":
                    {
                        "ClientName": "client_name",
                        "AgentName": "informix",
                        "InstanceName": "instance_name",
                        "BackupsetName": "default",
                        "SubclientName": "default",5
                        "UserName":"username",
                        "SourceInformixServiceName": "port_number",
                        "SourceInformixDBPassword": "password",
                        "DestinationClientName": "dest_client_name",
                        "DestinationInstanceName": "dest_instance_name",
                        "DestinationInformixServiceName": "port_number",
                        "DestinationInformixDBPassword": "password",
                        "TestDataSize": [2, 10, 100]
                    }
        }
Put password value as empty for linux clients.
Provide DomainName also in UserName for windows clients.
Provide port to which informix server listens using ipv4 address in InformixServiceName
TestDataSize should be list in order: [database_count, tables_count, row_count]
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import InformixSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing informix cross machine restore after deleting access control entries"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Informix cross machine restore from command center after deleting access control entries"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'UserName': None,
            'SourceInformixServiceName': None,
            'SourceInformixDBPassword': None,
            'TestDataSize': [],
            'DestinationClientName': None,
            'DestinationInstanceName': None,
            'DestinationInformixServiceName': None,
            'DestinationInformixDBPassword': None
            }
        self.db_instance = None
        self.db_instance_details = None
        self.subclient_page = None
        self.source_informix_helper_obj = None
        self.destination_informix_helper_obj = None
        self.dbhelper_object = None
        self.destination_client = None
        self.destination_instance = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.subclient_page = InformixSubclient(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)
        self.destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
        destination_agent = self.destination_client.agents.get('informix')
        self.destination_instance = destination_agent.instances.get(
            self.tcinputs["DestinationInstanceName"])
        self.create_source_ifx_helper_obj()
        self.navigate_to_source_subclient()
        self.subclient_page.edit_content('EntireInstance')

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.source_informix_helper_obj:
            self.source_informix_helper_obj.delete_test_data()
        if self.destination_informix_helper_obj:
            self.destination_informix_helper_obj.delete_test_data()

    @test_step
    def set_backup_to_disk_cache(self, enable=True):
        """Sets log backup to disk cache option for the plan
        Args:
            enable (bool) -- True to enable log backup to disk cache option
                             for the plan. Default is true
        Raises:
            CVTestStepFailure exception:
            If log backup to disk cache option is not set as intended
        """
        self.navigator.navigate_to_plan()
        self.admin_console.wait_for_completion()
        plans = Plans(self.admin_console)
        plans.select_plan(self.instance.properties["planEntity"]["planName"])
        self.admin_console.wait_for_completion()
        plan_details = PlanDetails(self.admin_console)
        if enable:
            plan_details.edit_database_options(use_disk_cache=True)
            if not self.source_informix_helper_obj.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not enabled")
            self.log.info("Switch log to prepare for log only backup")
            self.source_informix_helper_obj.cl_switch_log(
                self.client.client_name,
                self.client.instance,
                self.source_informix_helper_obj.base_directory)
            self.log.info("Run log only backup to ensure pending sweep job complete")
            self.source_informix_helper_obj.cl_log_only_backup(
                self.client.client_name,
                self.client.instance,
                self.source_informix_helper_obj.base_directory)
        else:
            plan_details.edit_database_options(use_disk_cache=False)
            if self.source_informix_helper_obj.is_log_backup_to_disk_enabled():
                raise CVTestStepFailure("Log backup to disk cache is not disabled")

    @test_step
    def navigate_to_source_subclient(self):
        """Opens details page for default subclient"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.select_instance(DBInstances.Types.INFORMIX,
                                    self.instance.instance_name,
                                    self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('default')

    @test_step
    def create_source_ifx_helper_obj(self):
        """Creates object of informix helper class for source instance
        and does test data generation"""
        source_agent = self.client.agents.get('informix')
        source_instance = source_agent.instances.get(self.tcinputs['InstanceName'])
        self.source_informix_helper_obj = InformixHelper(
            self.commcell,
            source_instance,
            'default',
            self.client.client_hostname,
            self.tcinputs['InstanceName'],
            source_instance.informix_user,
            self.tcinputs['SourceInformixDBPassword'],
            self.tcinputs['SourceInformixServiceName']
        )
        self.log.info("Populate the informix server with"
                      "test data size=%s", self.tcinputs['TestDataSize'])
        self.source_informix_helper_obj.populate_data(scale=self.tcinputs['TestDataSize'])

    @test_step
    def create_destination_ifx_helper_obj(self):
        """Creates object of informix helper class for destination instance"""
        self.destination_informix_helper_obj = InformixHelper(
            self.commcell,
            self.destination_instance,
            'default',
            self.destination_client.client_hostname,
            self.tcinputs["DestinationInstanceName"],
            self.destination_instance.informix_user,
            self.tcinputs['DestinationInformixDBPassword'],
            self.tcinputs['DestinationInformixServiceName']
        )

    @test_step
    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status
        Args:
            job_id (str) -- job id
        Raises:
            CVTestStepFailure exception:
            If job does not complete successfully """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def run_backup(self):
        """Adds more rows to tab1, collect metadata, submit full backup,
        wait for completion and returns the metadata and backup jobid
        Returns:
            metadata_backup (str)--  metadata collected during backup
            job_id (str) -- backup job id
        """
        self.source_informix_helper_obj.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        self.log.info("Collect metadata from server")
        metadata_backup = self.source_informix_helper_obj.collect_meta_data()
        full_jobid = self.subclient_page.backup(RBackup.BackupType.FULL)
        self.wait_for_job_completion(full_jobid)
        return metadata_backup, full_jobid

    @test_step
    def restore_and_validate(self, metadata_backup):
        """ Submit restore and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
        Returns:
            job_id (int) -- restore job id
        Raises:
            CVTestStepFailure exception:
            If validation fail for restored data
        """
        self.create_destination_ifx_helper_obj()
        self.destination_informix_helper_obj.stop_informix_server()
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.INFORMIX,
            self.tcinputs["InstanceName"],
            self.tcinputs["ClientName"])
        self.db_instance_details.access_restore()
        self.log.info("Perform physical only restore")
        restore_panel = self.subclient_page.restore_folders(
            DBInstances.Types.INFORMIX, all_files=True)
        job_id = restore_panel.informix_restore(
            'EntireInstance',
            destination_client=self.tcinputs["DestinationClientName"],
            destination_instance=self.tcinputs["DestinationInstanceName"],
            logical=False, config_files=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Perform logical only restore")
        restore_panel = self.subclient_page.restore_folders(
            DBInstances.Types.INFORMIX, all_files=True)
        job_id = restore_panel.informix_restore(
            'EntireInstance',
            destination_client=self.tcinputs["DestinationClientName"],
            destination_instance=self.tcinputs["DestinationInstanceName"],
            physical=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Making server online and validating data")
        self.destination_informix_helper_obj.bring_server_online()
        self.log.info("Metadata collected during backup=%s", metadata_backup)
        self.create_destination_ifx_helper_obj()
        metadata_restore = self.destination_informix_helper_obj.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise CVTestStepFailure("Data validation failed")
        return int(job_id)

    @test_step
    def feature_validation(self, restore_jobid, sweep_jobid=None):
        """ Method to validate restore with disk cache feature
        Args:
            restore_jobid(int) --  Job id of the restore job
            sweep_jobid(int)   --  Job id of the sweep job
        Raises:
            CVTestStepFailure exception:
            If restore is not from expected media location
        """
        machine_object = machine.Machine(self.destination_client)
        if sweep_jobid:
            output = machine_object.get_logs_for_job_from_file(
                job_id=str(restore_jobid), log_file_name="IFXXBSA.log", search_term="IdaUtilBrowse")
            afileid = self.source_informix_helper_obj.get_afileid(sweep_jobid, "4")
            if str(afileid) in output:
                self.log.info("Logs were restored from swept job.Feature validation completed")
            else:
                raise CVTestStepFailure("Restore is not from swept job."
                                        "Output is {0}".format(output))
        else:
            output = machine_object.get_logs_for_job_from_file(
                job_id=str(restore_jobid), log_file_name="IFXXBSA.log",
                search_term="Successful DataServer API search")
            if "Successful DataServer API search" in output:
                self.log.info("Logs were restored from disk cache.Feature validation completed")
            else:
                raise CVTestStepFailure("No log is restored from disk cache."
                                        "Output is {0}".format(output))

    @test_step
    def run_sweep_job(self, full_jobid):
        """ Method to run sweep job and get the sweep job id
        Args:
            full_jobid(str) -- job id of the full backup
        Returns:
            last_job(int)   -- job id of the sweep job
        """
        machine_object = machine.Machine(self.client)
        output = machine_object.get_logs_for_job_from_file(
            job_id=full_jobid, log_file_name="IFXXBSA.log",
            search_term="DataServer context initialized successfully")
        media_agent = output.split()[-1].split("*")[1]
        self.source_informix_helper_obj.run_sweep_job_using_regkey(media_agent)
        last_job = self.dbhelper_object._get_last_job_of_subclient(
            self.backupset.subclients.get('(command line)'))
        return last_job

    @test_step
    def get_client_list(self):
        """ Method to get the list of client IDs for which
        access control table entries are deleted
        Returns:
            client_list(list) -- list of IDs of clients """
        client_list = [int(self.client.client_id), int(self.destination_client.client_id)]
        ma_names = self.dbhelper_object.get_ma_names(self.subclient.storage_policy)
        for ma in ma_names:
            client_list.append(int(self.commcell.clients.get(ma).client_id))
        self.log.info("ClientIDs for which entries are deleted:{0}".format(client_list))
        return client_list

    def run(self):
        """ Main function for test case execution """
        try:
            if 'planEntity' not in self.instance.properties:
                raise Exception('Ensure instance is associated with a plan')
            client_list = self.get_client_list()
            metadata_backup, full_jobid = self.run_backup()
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            self.restore_and_validate(metadata_backup)
            self.log.info("Regular cross machine restore completed.")
            self.set_backup_to_disk_cache()
            self.navigate_to_source_subclient()
            metadata_backup, full_jobid = self.run_backup()
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            restore_jobid = self.restore_and_validate(metadata_backup)
            self.feature_validation(restore_jobid)
            self.log.info("Cross machine restore of logs in cache completed")
            sweep_jobid = self.run_sweep_job(full_jobid)
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            restore_jobid = self.restore_and_validate(metadata_backup)
            self.feature_validation(restore_jobid, sweep_jobid)
            self.log.info("Cross machine restore of swept logs completed")
            self.set_backup_to_disk_cache(enable=False)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
