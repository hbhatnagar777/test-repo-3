# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations
    for Dynamics 365 CRM Web AUTOMATON

Class:

    Dynamics365Helper()             --          Helper Class for Dynamics 365 Web Automation

Methods:

    dynamics365_apps()              --   Returns the instance of the Dynamics 365 Pages object representing
                                            the Page Object for the Dynamics 365 page

    create_dynamics365_client()     --  Create a Dynamics 365 CRM client
    verify_client_configuration_value()
                                    --  Verify the Configuration values for a Dynamics 365 client
    verify_no_content_configured()
                                    --  Verify that the Dynamics 365 client has no content configured
    verify_associated_instances()
                                    --  Verifies the instance associated with the Dynamics 365 client
    verify_tables_discovery()       --  Verify the Auto Discovery of tables
    verify_content_status()         --  Verify the status of the configured content
    verify_plan_association()       --  Verify that the plans are associated properly with the content
    run_d365_client_backup()        --  Run backup for a Dynamics 365 client
    wait_for_job_completion()       --  Wait for a particular job to complete
    run_restore()                   --  Run restore for the specified content in a Dynamics 365 CRM client
    wait_for_discovery_to_complete()
                                    --  Wait for the discovery task on the access node to complete
    initialize_sdk_objects_for_client()
                                    --  Initialize the SDK objects for the client
    delete_dynamics365_client()     --  Delete the Dynamics 365 client
    add_client_association()        --  Associate the specified content with a Dynamics 365 client
    get_tables_for_instance()       --  Get the tables in a Dynamics 365 Instance
    delete_dynamics365_plan()       --  Delete a Dynamics 365 Plan
    create_dynamics365_plan()       --  Create a Dynamics 365 Plan
    _validate_dynamics365plan_creation()
                                    --  Validate the creation of a Dynamics 365 Plan in the admin console
    get_items_associated_count()    --  Get number of items assocaited with the client
    delete_dynamics365_plan()       --  Delete a Dynamics 365 Plan
    _process_status_tab_stats*(     --  Process the job stats fetched from the job details
    verify_status_tab_for_job()     --  Verify that correct stats are populated in the job stats tab
                                        of job details page
    verify_backup_job_stats()       --  Verify that correct stats are populated for the backup job in the job
                                        stats tab of job details page
    navigate_to_client()            --  Navigate to the Dynamics 365 client page
    initiate_backup_for_dynamics365_content()
                                    --  Initiate backup for the selected Dynamics 365 content
    get_configured_content_list()   --  List of content configured with the client
"""

import collections
import time
import re
from datetime import datetime
from enum import Enum
import pytz

from Application.Dynamics365.d365web_api.d365_rec import Record
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from cvpysdk.job import Job
from Application.Dynamics365 import CVDynamics365
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Dynamics365Pages import constants
from Web.Common.exceptions import CVWebAutomationException, CVTestStepFailure
from Web.Common.page_object import TestStep
import Application.Dynamics365.constants as dynamics365_constants


class Dynamics365Helper:
    """
        Helper class for Dynamics 365 CRM related Web operations
    """
    test_step = TestStep()

    def __init__(self, admin_console, tc_object, is_react=False):
        """Constructor for Dynamics 365 Helper file"""
        self.tc_inputs = tc_object.tcinputs
        self.tc_object = tc_object
        self._admin_console = admin_console
        self._commcell = tc_object.commcell
        self.d365tables = list()
        self.d365instances = list()
        self.__is_react = is_react
        self.testcase_id = tc_object.id
        self.log = logger.get_log()
        self.d365_plan = self.tc_inputs.get("Dynamics365Plan")

        # Pass Tables if you need to back up only tables. Pass Tables as a list of 2 sized lists.
        # First element is the table name and second element is the instance name. For eg. [["table1", "instance1"]].
        if "Tables" in self.tc_inputs:
            for table, instance in self.tc_inputs.get("Tables", []):
                self.d365tables.append((table, instance))

        # Pass D365_Instance if you need to perform instance level backup.
        # Pass Instances as a string of instances separated by comma(,).
        if 'D365_Instance' in self.tc_inputs:
            self.d365instances = self.tc_inputs.get('D365_Instance').split(",")

        if 'D365_Instance_URL' in self.tc_inputs:
            self.d365instancesurl = self.tc_inputs.get('D365_Instance_URL').split(",")

        self.client_name = self.tc_inputs.get("Dynamics_Client_Name",
                                              dynamics365_constants.CLIENT_NAME % self.testcase_id)
        self.client_name += str(int(time.time()))
        self._cvd365_obj = None
        self._dynamics365apps: Dynamics365Apps = None
        self.__plans = None
        if 'cloud_region' in self.tc_inputs:
            self.cloud_region = self.tc_inputs.get('cloud_region')
        else:
            self.cloud_region = 1

    @property
    def dynamics365_apps(self):
        """ Object denoting the Dynamics 365 Page Class for Web Automation"""
        if self._dynamics365apps is None:
            self._dynamics365apps = Dynamics365Apps(tc_object=self.tc_object,
                                                    admin_console=self._admin_console,
                                                    is_react=self.__is_react)
        return self._dynamics365apps

    @property
    def plans(self):
        """ Object denoting the Dynamics 365 Page Class for Web Automation"""
        if self.__plans is None:
            self.__plans = Plans(admin_console=self._admin_console)
        return self.__plans

    @property
    def cvd365_obj(self):
        """Object denoting the CVDynamics365 helper class for Dynamics 365 automation"""
        if self._cvd365_obj is None:
            self._cvd365_obj = CVDynamics365(tc_object=self.tc_object)
        return self._cvd365_obj

    @property
    def d365api_helper(self):
        """Helper object for invoking Dynamics 365 CRM APIs"""
        return self.cvd365_obj.d365api_helper

    @test_step
    def create_dynamics365_client(self):
        """
            Method to create a Dynamics 365 Client
        """
        self.dynamics365_apps.create_dynamics365_app(client_name=self.client_name, cloud_region=self.cloud_region)
        self.log.info("Created Dynamics 365 CRM Client with Client Name: {}".format(self.client_name))
        self.cvd365_obj.client_name = self.client_name
        return self.client_name

    @test_step
    def verify_client_configuration_value(self, infra_pool=False):
        """
            Method to verify the configuration values of the Dynamics 365 Client that has been created

            Arguments:
                infra_pool      (bool)  --    If client was created using an infrastructure pool
            Returns:
                None                    --      If client configuration does match up with the expected values
            Raises:
                CVWebAutomationException--      If client configuration does not match with expected values
        """
        general_details = self.dynamics365_apps.get_client_general_configuration()

        if 'GlobalAdmin' in self.tc_inputs:
            global_admin = general_details['Global Administrator'].split('\n')[0]
            if not global_admin == self.tc_inputs['GlobalAdmin']:
                raise CVWebAutomationException("Global admin value is incorrect on configuration page")

        infra_details = self.dynamics365_apps.get_client_infrastructure_details()

        if self.tc_inputs['ServerPlan'] not in infra_details['Backup plan']:
            raise CVWebAutomationException("Server plan value is incorrect on client configuration page")

        if not infra_pool:
            if 'AccessNode' in self.tc_inputs:
                if isinstance(self.tc_inputs['AccessNode'], list):
                    access_node_details = infra_details['Access nodes'].split('\n')
                    proxies = [node.strip() for node in access_node_details[1].split(',')]
                    user_account = access_node_details[2]
                    shared_jrd = access_node_details[3]
                    if shared_jrd.find("JobResults") == -1:
                        shared_jrd = shared_jrd + "\\JobResults"
                    if len(proxies) != len(self.tc_inputs['AccessNode']):
                        raise CVWebAutomationException("Access node values on configuration page "
                                                       "do not match with supplied values")
                    else:
                        for node in self.tc_inputs['AccessNode']:
                            if node not in proxies:
                                raise CVWebAutomationException("Access nodes on the configuration page do not match "
                                                               "with the supplied values")
                    if user_account != self.tc_inputs['UserAccount']:
                        raise CVWebAutomationException("Local System Account is "
                                                       "incorrect on configuration page")
                    if shared_jrd != self.tc_inputs["UNCPath"] + "\\JobResults":
                        raise CVWebAutomationException("Shared Job Results Directory is "
                                                       "incorrect on configuration page")
                elif self.tc_inputs['AccessNode'] not in infra_details['Access nodes']:
                    raise CVWebAutomationException("Access node value is incorrect on configuration page")

            elif 'ClientGroup' in self.tc_inputs:
                access_node_details = infra_details['Access nodes'].split('\n')
                client_group = access_node_details[1]
                user_account = access_node_details[2]
                shared_jrd = access_node_details[3]
                if client_group != self.tc_inputs['ClientGroup']:
                    raise CVWebAutomationException('Client Group value on configuration page is not matching'
                                                   ' with the supplied values')
                if user_account != self.tc_inputs['UserAccount']:
                    raise CVWebAutomationException("Local System Account is incorrect on configuration page")
                if shared_jrd != self.tc_inputs["UNCPath"] + "\\JobResults":
                    raise CVWebAutomationException("Shared Job Results Directory is incorrect on configuration page")

            if self.tc_inputs['IndexServer'] not in infra_details['Index Server']:
                raise CVWebAutomationException("Index server value on configuration page is not matching "
                                               "with the supplied INdex Server value")

            if not int(
                    infra_details['Max streams'].split(' ')[0]) == constants.Dynamics365.MAX_STREAMS_COUNT.value:
                raise CVWebAutomationException("Max streams value is incorrect on configuration page")
        else:
            if not int(
                    infra_details['Max streams'].split('\n')[0]) == constants.Dynamics365.INFRA_POOL_MAX_STREAMS.value:
                raise CVWebAutomationException("Max streams value is incorrect on configuration page")
            if self.tc_inputs["Infra_Pool_Details"]["Index Server"] not in infra_details['Index server']:
                raise CVWebAutomationException("Index server value on configuration page is not matching with "
                                               "the Index Server value corresponding to the infrastructure pool")
            access_node_details = infra_details['Access nodes'].split('\n')
            client_group = access_node_details[1]
            user_account = access_node_details[2]
            shared_jrd = access_node_details[3]
            if client_group != self.tc_inputs["Infra_Pool_Details"]["Client_Group"]:
                raise CVWebAutomationException('Client Group value is incorrect on configuration page')
            if user_account != self.tc_inputs["Infra_Pool_Details"]["Shared_Dir_UserAcc"]:
                raise CVWebAutomationException("Account to access shared path is incorrect on configuration page")
            if shared_jrd != self.tc_inputs["Infra_Pool_Details"]["Shared_Dir_Path"]:
                raise CVWebAutomationException("Shared Job Results Directory is incorrect on configuration page")

    @test_step
    def verify_associated_instances(self, instances: list = None, all_instances: bool = False):
        """
            Method to verify that instances associated with the client

            Arguments:
                instances       (bool)--    List of instances to verify for
                all_instances   (bool)--    If All Instances verification is to be verifies
        """
        instance_list = self.dynamics365_apps.get_configured_instances()
        if instances:
            for instance in instances:
                if instance not in instance_list:
                    self.log.info("Instances list: {}".format(instance_list))
                    self.log.info("Instances passed: {}".format(instances))
                    raise CVWebAutomationException("Instance List on the Client Content Tab does "
                                                   "not match the passed Instances list")
            self.log.info(f'Added Instances verified: {instances}')

        elif all_instances:
            if instance_list[0].find(constants.Dynamics365.ALL_INSTANCES_CONTENT_NAME.value) == -1:
                self.log.info("Associated Content List: {}".format(instance_list))
                raise CVWebAutomationException("All Instances not associated to the client")
            self.log.info("Verified All Instances Association")

        else:
            if not collections.Counter(instance_list) == collections.Counter(self.d365instances):
                raise CVWebAutomationException("Instance list on the app page does "
                                               "not match the input file Instance list")
            self.log.info(f'Added Instances verified: {self.d365instances}')

    @test_step
    def verify_tables_discovery(self, instance_list: list, tables_dict: dict):
        """
            Method to verify that the auto-discovery has picked
                the correct set of tables for the instances

            Arguments:
                instance_list:       <list<str>>--   List of instances
                tables_dict:         <dict<list>>--  Dictionary containing actual list of tables
                                                        present on Dynamics 365 CRM
                    Dictionary format:
                        Key::   Instance name
                        Value:: List of tables  (Friendly Name)
        """
        discovered_tables = self.dynamics365_apps.get_tables_associated_for_instance(instance_list=instance_list)
        for instance in instance_list:
            env_tables = tables_dict[instance]
            discv_tables = discovered_tables[instance]
            if collections.Counter(discv_tables) != collections.Counter(env_tables):
                self.log.info("Discovered Tables: {}".format(discv_tables))
                self.log.info("Tables from API: {}".format(env_tables))
                self.log.exception("List of tables do not match")
                raise CVWebAutomationException("Auto discovered list of tables are not matching")

    @test_step
    def verify_content_status(self, status: constants.AssocStatusTypes, name: str, instance: str = str(),
                              is_instance: bool = False):
        """
        Verify the status of the content in the Command Center

        Args:
            status (str):   Status of the content
                            Valid values - Active, Disabled, Deleted
            name        (str)-      Name of content
            is_instance (bool)-     Is the content an instance
            instance    (str)-      If content is table, then the instance to which the table belongs to
        """
        content_status = self.dynamics365_apps.get_content_status(is_instance=is_instance, name=name,
                                                                  instance=instance)
        if content_status != status:
            raise CVWebAutomationException('Instance/ Table Status Verification Failed')
        self.log.info(f'Status of {name} Verified: {status}')

    @test_step
    def verify_plan_association(self, content: list = None, plan: str = None, is_instance: bool = False):
        """
            Verifies addition of tables and check if plan is associated correctly
            Args:
                is_instance:
                content     :
                plan (string):  Dynamics 365 plan to which table should be associated
        """
        if plan is None:
            plan = self.tc_inputs['Dynamics365Plan']

        if not is_instance:
            for table, instance in content:
                table_assoc_plan = self.dynamics365_apps.get_content_assoc_plan(is_instance=is_instance,
                                                                                name=table,
                                                                                instance=instance)
                if table_assoc_plan != plan:
                    raise CVWebAutomationException(f"Dynamics 365 Plan has not been "
                                                   f"associated to each table correctly "
                                                   f"--> {table} is associated to {table_assoc_plan} "
                                                   f"when it should be associated to {plan}")
        else:
            for instance in content:
                instance_assoc_plan = self.dynamics365_apps.get_content_assoc_plan(name=instance,
                                                                                   is_instance=is_instance)
                if instance_assoc_plan != plan:
                    raise CVWebAutomationException(f"Dynamics 365 Plan has not been "
                                                   f"associated to the instance correctly "
                                                   f"--> {instance} is associated to {instance_assoc_plan} "
                                                   f"when it should be associated to {plan}")

        self.log.info("Verified the association of the Tables/ instances to Dynamics 365 Plan")

    @test_step
    def run_d365_client_backup(self, full_backup: bool = False, client_level: bool = False,
                               is_metallic_env: bool = False):
        """
            Method to run the backup of a Dynamics 365 Client
            Arguments:
                full_backup         (bool):     Whether to run full backup for the client
                client_level        (bool)--    Whether to run a client level backup or a backupset level
                    If client level:
                        backup is initiated from the action menu item on the client listing page
                    if backupset_level  (client_level is False):
                        backup is initiated from the action menu on the client page
                is_metallic_env (bool):     Whether backup is run on a Metallic environment
        """
        job_id = self.dynamics365_apps.run_d365client_backup(full_backup=full_backup, client_level=client_level)
        self.log.info("Dynamics 365 CRM client backup job started with Job ID: {}".format(job_id))

        self.wait_for_job_completion(job_id=job_id)

        if not is_metallic_env:
            self.log.info("Checking if items in the backup job got played successfully")
            self.cvd365_obj.solr_helper.check_all_items_played_successfully(job_id=job_id)
            self.log.info("Verified Index Construction of items in backup job")

        else:
            time.sleep(150)  # for index reconstruction
        return job_id

    @test_step
    def wait_for_job_completion(self, job_id: int):
        """
            Method to wait for the job to complete
            Arguments:
                job_id      (int)--     Job ID to wait for
        """
        job = Job(self._commcell, job_id)
        self.log.info("Waiting for Job with Job ID: {} to complete".format(job_id))
        job.wait_for_completion()

        if (job.status not in
                ["Committed", "Completed", "Completed w/ one or more errors",
                 "Completed w/ one or more warnings"]):
            raise Exception(f'Job {job_id} did not complete successfully')
        else:
            self.log.info(f'Job {job_id} completed successfully')

    @test_step
    def run_restore(self, tables: list = None, restore_type: Enum = None, dest_instance: str = str(),
                    record_option: Enum = None, is_instance: bool = False, restore_level: str = None):
        """
            Run restore for the Dynamics 365 Client

            Args:
                is_instance:        If the content to be restored is an instance
                record_option:      Overwrite/ Skip option for records
                    Possible values:
                        constants.RESTORE_RECORD_OPTIONS
                dest_instance:      Destination instance for OOP restore
                restore_type:       Type of restore
                    Possible values:
                        constants.RESTORE_TYPES Enum
                tables:             List of tables to restore   (if any)
                restore_level:      Level of restore to be triggered, None for normal restore (default)

            Returns:
                job_details (dict): Details of the restore job
        """
        restore_job_id = self.dynamics365_apps.run_restore(tables=tables, restore_type=restore_type,
                                                           dest_instance=dest_instance, record_option=record_option,
                                                           is_instance=is_instance, restore_level=restore_level)
        self.log.info("Restore Job started with Job ID: {}".format(restore_job_id))

        self.wait_for_job_completion(restore_job_id)
        self.log.info("Dynamics 365 CRM restore job with Job ID:{} completed".format(restore_job_id))

    @test_step
    def wait_for_discovery_to_complete(self):
        """
            Wait for the discovery to stop on the access node
        """
        access_node = Machine(machine_name=self.tc_object.instance.access_node,
                              commcell_object=self._commcell)
        result = access_node.wait_for_process_to_exit(
            process_name=dynamics365_constants.DISCOVER_PROCESS_NAME,
            time_out=1800,
            poll_interval=60)
        if not result:
            raise Exception('Dynamics 365 Discovery process did not complete in the stipulated time')

    @test_step
    def initialize_sdk_objects_for_client(self):
        """
            Initialize the SDK objects for the Test case corresponding to the
            recently created client
        """
        self._commcell.refresh()
        self.log.info("Create Test case client object for: %s", self.client_name)
        self.tc_object._client = self.cvd365_obj.client

        self.log.info("Creating Agent object")
        self.tc_object._agent = self.cvd365_obj.agent

        self.log.info("Creating Instance object")
        self.tc_object._instance = self.cvd365_obj.instance

        self.log.info("Creating Backup Set object")
        self.tc_object._backupset = self.cvd365_obj.backupset

        self.log.info("Creating Sub client Object")
        self.tc_object._subclient = self.cvd365_obj.subclient

    @test_step
    def delete_dynamics365_client(self):
        """
            Delete the Dynamics 365 client
        """
        if not self._commcell.clients.has_client(self.client_name):
            self.log.exception("Client: {} not found in the commcell".format(self.client_name))
            raise CVWebAutomationException("Unable to delete client")
        self.dynamics365_apps.delete_dynamics365_app(app_name=self.client_name)

    @test_step
    def add_client_association(self, assoc_type: constants.D365AssociationTypes, instances: list = None,
                               tables: list = None, plan: str = None, all_instances: bool = False):
        """
            Method to add associations to a Dynamics 365 Client
            Args:
                assoc_type:         <Enum>:         Tye of Association
                    Allowed values:
                        constants.D365AssociationTypes.TABLE
                        constants.D365AssociationTypes.INSTANCE

                instances:          <LIST<STR>>:    List of Instances to associate
                tables:             <list>:         List of tables to associate
                    Format:
                        [
                            (table1, instance-of-table1), (table2, instance-of-table2)...
                        ]
                plan:               <str>:          Dynamics 365 Plan to be used for creating the association
                all_instances:      <bool>:         Whether to associate all instances

        """
        if plan is None:
            plan = self.d365_plan
        self.dynamics365_apps.add_association(assoc_type=assoc_type, instances=instances, tables=tables, plan=plan,
                                              all_instances=all_instances)

    @test_step
    def modify_client_association(self, instances: list = None,
                                  tables: list = None, plan: str = None, operation: str = str()):
        """
            Method to modify associations to a Dynamics 365 Client
            Args:
                instances:          <LIST<STR>>:    List of Instances
                tables:             <list>:         List of tables
                    Format:
                        [
                            (table1, instance-of-table1), (table2, instance-of-table2)...
                        ]
                plan:               <str>:          Dynamics 365 Plan to be used
                operation:          <str>:          OOperation to be performed on the selected content
                    Operation can be:
                        EXCLUDE:    Exclude from backup
                        INCLUDE:    Include in backup
                        DELETE:     Delete from content

        """
        if plan is None:
            plan = self.d365_plan

        if operation == "EXCLUDE":
            _op_func = self.dynamics365_apps.exclude_content
        elif operation == "INCLUDE":
            _op_func = self.dynamics365_apps.include_in_backup

        elif operation == "DELETE":
            _op_func = self.dynamics365_apps.delete_from_content
        else:
            raise CVWebAutomationException("Operation not supported")

        if not instances:
            for _table, _environment in tables:
                _op_func(name=_table, instance_name=_environment, is_instance=False)

        else:
            for _environment in instances:
                _op_func(name=_environment, is_instance=True)

    @test_step
    def get_tables_for_instance(self, instance_name: str):
        """Get the tables for a given instance"""
        try:
            tables = self.d365api_helper.get_tables_in_instance(instance_name=instance_name)
            tables = self.d365api_helper.get_friendly_name_of_tables(tables_dict=tables)
            return tables
        except Exception:
            raise CVTestStepFailure(f'Unable to obtain tables for Instance {instance_name}')

    @test_step
    def verify_client_associated_with_plan(self):
        """
            Method to verify that the client is associated with the plan
        """
        self.dynamics365_apps.is_app_associated_with_plan(client_name=self.client_name)

    @test_step
    def create_dynamics365_plan(self, retention_prop: dict = None):
        """
            Method to navigate to and create a Dynamics 365 Plan
            Arguments:
                retention_prop      (dict):     Dictionary of values to be
                                                    set as Dynamics 365 Retention
            Returns:
                plan_name           (str):      Name of the Dynamics 365 Plan created
        """
        _plan_name = "Dynamics365_Automation_Plan_" + str(int(time.time()))
        self.log.info("Creating Dynamics 365 Plan with plan name: {}".format(_plan_name))
        self._admin_console.navigator.navigate_to_plan()
        self.plans.create_dynamics365_plan(plan_name=_plan_name, retention=retention_prop)
        self.log.info("Created Dynamics 365 Plan with Plan Name: {}".format(_plan_name))
        self.d365_plan = _plan_name

        self.log.info("Validating if Plan details were set correctly")
        self._validate_dynamics365plan_creation(plan_name=_plan_name, retention_prop=retention_prop)
        return _plan_name

    @test_step
    def _validate_dynamics365plan_creation(self, plan_name, retention_prop=None):
        """
            Method to validate that the Dynamics 365 Plan was created with correct details
        Args:
            plan_name:          (str)--      Name of the Plan created
            retention_prop:     (dict)--    Retention propertied dictionary for the plan
                If None:
                    Retention is treated as Infinite

        Returns:
            None                    --      If plan details match up with the expected values
        Raises:
            CVWebAutomationException--      If plan details do not match with expected values
        """
        _plan_details = PlanDetails(self._admin_console)
        d365plan_info = _plan_details.plan_info(plan_type="Dynamics365")

        cr_plan_name = d365plan_info.get('PlanName')
        if plan_name != cr_plan_name:
            self.log.info("Plan Names do not match")
            self.log.info("Plan Name from the input: {}".format(plan_name))
            self.log.info("Plan Name from the plan Details Page: {}".format(cr_plan_name))
            raise CVWebAutomationException("Plan Names do not match!")

        d365plan_ret = d365plan_info.get("Retention").get("Retain deleted items for")
        if retention_prop is None:
            if d365plan_ret != 'Infinite':
                self.log.info("Retention value from plan details page: {}".format(d365plan_ret))
                self.log.info("Expected Retention Value: Infinite")
                raise CVWebAutomationException("Retention Value mismatch")
        else:
            ret_unit = retention_prop['ret_unit'].replace("(", "").replace(")", "")
            ret_prop_value = "{} {}".format(retention_prop['ret_period'], ret_unit)
            if ret_prop_value != d365plan_ret:
                self.log.info("Retention value from plan details page: {}".format(d365plan_ret))
                self.log.info("Expected Retention Value: {}".format(ret_prop_value))
                raise CVWebAutomationException("Retention Value mismatch")
        self.log.info("Dynamics 365 Plan creation verified")

    @test_step
    def delete_dynamics365_plan(self, plan_name: str):
        """
            Method to Delete a Dynamics 365 Plan
            Arguments:
                    plan_name       (str):      Name of the Dynamics 365 Plan
        """
        self._admin_console.navigator.navigate_to_plan()
        self.log.info("Deleting Dynamics 365 Plan with Plan Name: {}".format(plan_name))
        self.plans.delete_plan(plan_name=plan_name)

    @staticmethod
    def _process_status_tab_stats(stats):
        """Returns the status_tab_stats of status tab in job details page after processing them into dictionary
            Args:
                stats (str)         :  site stats of status tab in job details page
            Returns:
                stats_dict (dict)   :  dictionary of stats
        """
        status_tab_stats = re.findall('[0-9]* [a-z A-Z]*', stats)
        stats_dict = {}
        for stat in status_tab_stats:
            value, label = stat.split(" ", 1)
            stats_dict[label.strip()] = int(value)
        return stats_dict

    @test_step
    def verify_status_tab_for_job(self, job_id, status_tab_expected_stats):
        """Verifies status tab stats in job details page
            Args:
                job_id (str)                     : Job ID of the backup job
                status_tab_expected_stats (dict) : Expected stats of the status tab
                    Example:
                            {
                               "Total":2,
                               "Successful":2,
                               "Successful with warnings":0,
                               "Failed":0,
                               "Skipped":0,
                               "Suspended":0,
                               "To be processed":0
                            }
        """
        self.dynamics365_apps.jobs.access_job_by_id(job_id)
        self.dynamics365_apps._job_details.access_job_status_tab()
        status_tab_stats = self.dynamics365_apps._job_details.get_status_tab_stats()
        for label, value in status_tab_expected_stats.items():
            if not value == status_tab_stats[label]:
                raise CVWebAutomationException(f"Status tab stats are not validated\n"
                                               f"Expected Stats: {status_tab_expected_stats}\n"
                                               f"Actual Stats: {status_tab_stats}")

    @test_step
    def verify_backup_job_stats(self, job_id, status_tab_expected_stats=None):
        """
            Verify the content/ number of items processed by a backup job.
             Args:
                job_id (str)                     : Job ID of the backup job
                status_tab_expected_stats (dict) : Expected stats of the status tab
        """
        # sometimes displaying backup job on job page takes some time, so waiting for it
        time.sleep(90)
        self.dynamics365_apps.jobs.job_completion(job_id=job_id, skip_job_details=True)

        if status_tab_expected_stats:
            self.verify_status_tab_for_job(job_id=job_id, status_tab_expected_stats=status_tab_expected_stats)

    @test_step
    def get_items_associated_count(self, is_instance: bool = False):
        """
            Method to get a count of the total number of items associated with the client.
            Arguments:
                is_instance         (bool)  :     Whether to fetch the count for the number of associated instances
                    Default Value:
                        False               :     Fetch count of associated tables
        """
        if is_instance:
            config_count = self.dynamics365_apps.get_instances_configured_count()
        else:
            config_count = self.dynamics365_apps.get_tables_configured_count()
        return config_count

    @test_step
    def navigate_to_client(self, client_name=None):
        """Navigates to the Dynamcis 365 client page"""
        self._admin_console.navigator.navigate_to_dynamics365()
        self.dynamics365_apps.select_client(client_name)
        self._admin_console.wait_for_completion()

    @test_step
    def initiate_backup_for_dynamics365_content(self, content: list = None, is_instance: bool = False,
                                                is_metallic_env: bool = False):
        """
            Initiates backup for the given Tables/ Environments

            Args:
                is_instance     (bool):     Is the content passed, list of instances
                content:        (list):     List of content to be backed up
                    If Instances:
                        list of instance
                    If Tables
                        List of table tuples
                        Format:
                            [   (table1, instance1), (table2, instance2)    ]
                is_metallic_env (bool):     Whether backup is run on a Metallic environment

            Returns:
                job_id (str): Job ID of the initiated backup job
        """
        job_id = self.dynamics365_apps.initiate_backup(content=content, is_instance=is_instance)
        self.log.info("Dynamics 365 backup job started with Job ID: {}".format(job_id))

        self.wait_for_job_completion(job_id=job_id)

        if not is_metallic_env:
            self.log.info("Checking if items in the backup job got played successfully")
            self.cvd365_obj.solr_helper.check_all_items_played_successfully(job_id=job_id)
            self.log.info("Verified Index Construction of items in backup job")

        else:
            time.sleep(150)  # for index reconstruction

        return job_id

    @test_step
    def get_configured_content_list(self, instance: bool = False):
        """
            Method to get a list of the configured content

            Arguments:
                instance        (bool)--    Whether to get a list of the configured instances
        """
        return self.dynamics365_apps.get_configured_content(instance=instance)

    @test_step
    def verify_backup_health_report_stats(self, associated_tables_count: int, excluded_tables_count: int):
        """
            Verifies the stats in the backup health report with the expected stats

            Arguments:
                associated_tables_count:     (int):      Number of tables associated for backup
                excluded_tables_count:      (int):      Number of tables excluded from backup
        """
        self.navigate_to_client()
        _bkp_health_report = self.dynamics365_apps.get_backup_health_content()

        _bkp_health_backed_up = _bkp_health_report.get("backedup_tables")

        try:
            assert associated_tables_count - excluded_tables_count == int(_bkp_health_backed_up)
        except AssertionError:
            self.log.info("Backup Health Report Item Count mismatch")
            self.log.info("Tables Selected for Backup: {} | Backup Health Count: {}".format(
                associated_tables_count - excluded_tables_count,
                _bkp_health_backed_up))
            raise CVTestStepFailure("Count mismatch in Backup Health Report")

    @test_step
    def verify_client_overview_summary(self, last_bkp_job, associated_tables_count: int, removed_tables_count:int):
        """
            Verify the overview summary  and the client stats
            for the Dynamics 365 CRM Client.

            For Summary:
                Verify that the index status time is populated and greater than or equal to the last run backup job

            For stats:
                Tables: verify using tables associated to the environment and match with those
                Number of items: Items backed up so far.
                                Considering only one backup job, and equating that job items == items on page
        """
        self.log.info("Getting the Over View stats for the Client")
        _over_view_Stats = self.dynamics365_apps.get_client_summary_details()
        self.log.info("Over View stats for the Client : {}".format(_over_view_Stats))

        _bkp_job_time = int(last_bkp_job.start_timestamp)
        _index_update_time = _over_view_Stats.get('Index status')
        _date = _index_update_time.split(" ")[4][:-1:1]
        _time = re.findall('\d+:\d+ [AP]M', _index_update_time)[0]

        _hours, _minutes = datetime.strftime(datetime.strptime(_time, "%I:%M %p"), "%H:%M").split(":")

        _bkp_job_time = datetime.fromtimestamp(_bkp_job_time).astimezone()

        self.log.info("Last Backup time from Job Details: {} and Index Update "
                      "Time from UI: {}".format(_bkp_job_time, _index_update_time))

        assert int(_date) == int(_bkp_job_time.day) and int(_hours) >= int(_bkp_job_time.hour)
        self.log.info("Verified the Summary tab on the overview page")

        _client_stats_gui = self.dynamics365_apps.get_client_stats()
        self.log.info("Stats from Overview tab: {}".format(_client_stats_gui))

        assert associated_tables_count-removed_tables_count == int(_client_stats_gui.get('Tables Count'))
        self.log.info("Verified Number of tables count")

    @test_step
    def compare_and_restore_table_attributes(self, table_name: str, older_record: Record, newer_record: Record,
                                             primary_attribute: str):
        """
            Method to compare the attributes of a table in the Dynamics 365 CRM
            with the attributes of the table in the backup data

            Args:
                table_name:         (str)   :   Name of the table
                older_record:       (Record):   Record object of the older record
                newer_record:       (Record):   Record object of the newer record
                primary_attribute:  (str)   :   Primary attribute of the table
        """
        self.log.info("Comparing the attributes of the table: {} in the Dynamics 365 CRM with the ".format(table_name))
        compare_dict = self.dynamics365_apps.compare_table_attributes_with_live_data(table_name=table_name,
                                                                                     older_record=older_record,
                                                                                     primary_attribute=primary_attribute
                                                                                     )
        job_id = self.dynamics365_apps.restore_table_attributes()
        compare_dict.update({"Job ID": job_id})
        self.wait_for_job_completion(job_id=job_id)
        return compare_dict
