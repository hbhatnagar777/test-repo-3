# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Main helper file for communicating with CvPySDK for performing
    operations related to a Dynamics 365 client.

CVD365Operations is the only class defined in this file

    CVD365Operations: Class for performing operations operations related to a Dynamics 365 client.

    CVD365Operations:
        __init__(cvdynamics_obj)        --      Init function for the class

        backupset                       --      Property object denoting the backup set instance corresponding
                                                    to the Dynamics 365 client
        subclient                       --      Property object denoting the sub client instance corresponding
                                                    to the Dynamics 365 client
        client                          --      Property object denoting the Dynamics 365 client.

        discover_environments           --      Discover environments for a Dynamics 365 client
        discover_tables                 --      Discover tables for a Dynamics 365 client
        associate_environment           --      Associate environment to a Dynamics 365 client
        associate_tables                --      Associate individual tables to a Dynamics 365 client
        run_d365_client_backup          --      Run backup for a Dynamics 365 client
        run_d365_environment_backup     --      Run backup for particular environments associated to a Dynamics 365 client
        run_d365_tables_backup          --      Run backup for particular set of tables associated to a Dynamics 365 client
        wait_for_discovery_to_complete  --      WAit for the discovery process to complete on the access node
        wait_for_job_completion         --      Wait for a particular job to complete
        run_inplace_restore             --      Run in-place restore for specified content
        delete_d365_client              --      Deleting the specified Dynamics 365 client
        run_and_verify_licensing        --      Method to run and verify d365 licensing.
        run_out_of_place_restore        --      Run out-of-place restore fpr specified content
        submit_client_index_retention   --      Run retention for the Index Server
"""

from AutomationUtils.machine import Machine
import Application.Dynamics365.constants as dynamics365_constants
import time
from Web.Common.page_object import TestStep


class CVD365Operations:
    """ Class for operations on a Dynamics 365 client"""
    test_step = TestStep()

    def __init__(self, cvdynamics_obj):
        self.tc_object = cvdynamics_obj.tc_object
        self.dynamics_obj = cvdynamics_obj
        self.commcell = self.tc_object.commcell
        self.tc_inputs = self.tc_object.tcinputs
        self.log = self.tc_object.log
        self.client_name = cvdynamics_obj.client_name

        self.app_name = self.__class__.__name__

        self._client = None
        self.plans = self.commcell.plans
        self.log.info("Logger initialized for CVD365Operations")
        self._discovered_environments: dict = dict()
        self._discovered_tables: dict = dict()

    @property
    def backupset(self):
        """Returns backup-set comm-cell object."""
        return self.dynamics_obj.backupset

    @property
    def subclient(self):
        """Returns sub-client comm-cell object"""
        return self.dynamics_obj.subclient

    @property
    def client(self):
        """Treats the client as a read-only attribute."""
        return self.dynamics_obj.client

    @property
    def instance(self):
        """Return the instance comm-cell object"""
        return self.dynamics_obj.instance

    def discover_environments(self):
        """
            Method to discover environments for a Dynamics 365 client.

            Returns:
                discovered_tables       (dict)--    Dictionary of discovered environments

        """
        self.log.info("Discovering Environments for the Dynamics 365 Client: {}".format(self.client_name))

        self._discovered_environments = self.subclient.discover_environments()

        self.log.info("Discovered Environments: {}".format(self._discovered_environments))
        return self._discovered_environments

    def discover_tables(self):
        """
            Method to discover tables for a Dynamics 365 CRM client.

            Returns:
                discovered_tables       (dict)--    Dictionary of discovered tables

        """
        self.log.info("Discovering Tables for the Dynamics 365 Client")

        self._discovered_tables = self.subclient.discover_tables()
        self.log.info("Discovered Tables: {}".format(self._discovered_tables))

        return self._discovered_tables

    @test_step
    def associate_environment(self, environment_names: list = None, plan_name: str = None):
        """
            Method to associate the list of environments to a Dynamics 365 client.

            Arguments:
                environment_names         (list)--        List of environments to be associated
                    List format:
                        list of strings, with each string corresponding to the environments display name, in lower case

                    If None:
                        the environment list from TC-Inputs through CVDynamics365 object is picked up

                plan_name           (str)--         Name of the Dynamics 365 PLan to be used for association
                    If None:
                        the plan name from TC-Inputs through CVDynamics365 object is picked up
        """
        if plan_name is None:
            plan_name = self.dynamics_obj.d365plan

        if environment_names is None:
            environment_names = self.dynamics_obj.d365instances

        self.log.info("Associating Environments: {}".format(environment_names))
        self.log.info("Using Dynamics 365 Plan: {}".format(plan_name))
        self.log.info("Client: {}".format(self.client_name))

        self.subclient.set_environment_associations(environments_name=environment_names, plan_name=plan_name)

        self.log.info("Successfully Associated Environments to the Dynamics 365 client")
        self.log.info("Waiting for Discovery to Complete")
        self.wait_for_discovery_to_complete()
        self.log.info("Discovery Process Ended Successfully")
        self.subclient.refresh()

    @test_step
    def associate_tables(self, tables_list: list = None, plan_name: str = None):
        """
            Method to associate the list of tables to a Dynamics 365 CRM client.

            Arguments:
                tables_list         (list)--        List of tables to be associated
                    List format:
                        list of tuples, with each tuple, of the form: "environment_name","table_name"
                            where environment name if the name of the environment to which the table belongs to
                        Sample input:
                            [ ("account", "testenv1") , ("note", "testenv2") , ("attachments", "testenv1")]

                    If None:
                        the tables list from TC-Inputs through CVDynamics365 object is picked up

                plan_name           (str)--         Name of the Dynamics 365 PLan to be used for association
                    If None:
                        the plan name from TC-Inputs through CVDynamics365 object is picked up
        """
        if plan_name is None:
            plan_name = self.dynamics_obj.d365plan

        if tables_list is None:
            tables_list = self.dynamics_obj.d365tables
        self.log.info("Associating Tables: {}".format(tables_list))
        self.log.info("Using Dynamics 365 Plan: {}".format(plan_name))
        self.log.info("Client: {}".format(self.client_name))
        self.subclient.set_table_associations(tables_list=tables_list, plan_name=plan_name)
        self.subclient.refresh()
        self.log.info("Successfully Associated Tables to the Dynamics 365 client")

    @test_step
    def run_d365_client_backup(self, skip_playback_check: bool = False):
        """
            Run a backup for all the content associated with the Dynamics 365 client

            Returns:
                 backup_job          (Job)--     Instance of CVPySDK.job denoting that backup job
        """
        self.log.info("Running a backup for the Dynamics Client: {}".format(self.client_name))
        try:
            _bkp_job = self.subclient.backup()
            self.log.info("Backup Job started with Job ID: {}".format(_bkp_job.job_id))

            self.wait_for_job_completion(job=_bkp_job)

            if not skip_playback_check:
                self.log.info("Checking if items in the backup job got played successfully")
                self.dynamics_obj.solr_helper.check_all_items_played_successfully(job_id=_bkp_job.job_id)
                self.log.info("Verified Index Construction of items in backup job")
            return _bkp_job

        except Exception as excp:
            self.log.exception("An Exception occurred while running backup for selected Dynamics 365 Environments")
            raise excp

    @test_step
    def run_d365_environment_backup(self, environments_list: list = None):
        """
            Method to run a backup for the specified environments for a Dynamics 365 client.

            Arguments:
                environments_list             (list)--    List of environments to be backed up
                    List format:
                        list of strings, with each string corresponding to the environments display name,

            Returns:
                backup_job          (Job)--     Instance of CVPySDK.job denoting that backup job
        """
        if environments_list is None:
            environments_list = self.dynamics_obj.d365instances
        self.log.info("Running a Dynamics 365 Backup")
        self.log.info("Running a backup for the following environments: {}".format(environments_list))

        try:
            _bkp_job = self.subclient.backup_environments(environments_list=environments_list)

            self.log.info("Backup Job started with Job ID: {}".format(_bkp_job.job_id))

            self.wait_for_job_completion(job=_bkp_job)

            self.log.info("Checking if items in the backup job got played successfully")
            self.dynamics_obj.solr_helper.check_all_items_played_successfully(job_id=_bkp_job.job_id)
            self.log.info("Verified Index Construction of items in backup job")
            return _bkp_job
        except Exception as excp:
            self.log.exception("An Exception occurred while running backup for selected Dynamics 365 Environments")
            raise excp

    @test_step
    def run_d365_tables_backup(self, tables_list: list = None):
        """
            Method to run a backup for the specified tables for a Dynamics 365 client.

            Arguments:
                tables_list             (list)--    List of tables to be backed up
                    List format:
                        list of tuples, with each tuple, of the form: "environment_name","table_name"
                            where environment name if the name of the environment to which the table belongs to
                        Sample input:
                            [ ("testenv1" , "account") , ("testenv2","note") , ("testenv1","attachments")]

            Returns:
                backup_job          (Job)--     Instance of CVPySDK.job denoting that backup job
        """
        if tables_list is None:
            tables_list = self.dynamics_obj.d365tables

        self.log.info("Running a Dynamics 365 Backup")
        self.log.info("Running a backup for the following tables: {}".format(tables_list))

        try:
            _bkp_job = self.subclient.backup_tables(tables_list=tables_list)

            self.log.info("Backup Job started with Job ID: {}".format(_bkp_job.job_id))

            self.wait_for_job_completion(job=_bkp_job)

            self.log.info("Checking if items in the backup job got played successfully")
            self.dynamics_obj.solr_helper.check_all_items_played_successfully(job_id=_bkp_job.job_id)
            self.log.info("Verified Index Construction of items in backup job")
            return _bkp_job

        except Exception as excp:
            self.log.exception("An Exception occurred while running backup for selected Dynamics 365 Tables")
            raise excp

    @test_step
    def wait_for_discovery_to_complete(self):
        """
            Wait for the discovery to stop on the access node
        """
        access_node = Machine(machine_name=self.dynamics_obj.instance.access_node,
                              commcell_object=self.commcell)
        result = access_node.wait_for_process_to_exit(
            process_name=dynamics365_constants.DISCOVER_PROCESS_NAME,
            time_out=1800,
            poll_interval=60)
        if not result:
            raise Exception('Dynamics 365 Discovery process did not complete in the stipulated time')

    @test_step
    def wait_for_job_completion(self, job):
        """
            Method to wait for the job to complete
            Arguments:
                job     (int)--     JOb to wait for
        """
        self.log.info("Waiting for Job with Job ID: {} to complete".format(job.job_id))
        job.wait_for_completion()

        if (job.status not in
                ["Committed", "Completed", "Completed w/ one or more errors",
                 "Completed w/ one or more warnings"]):
            raise Exception(f'Job {job.job_id} did not complete successfully')
        else:
            self.log.info(f'Job {job.job_id} completed successfully')

    @test_step
    def run_inplace_restore(self,
                            restore_content: list = None,
                            restore_path: list = None,
                            is_environment: bool = False,
                            overwrite: bool = True,
                            job_id: int = None):
        """
            Method to run in- place restore for the content specified.

            Arguments:
                restore_content         (str)--     List of the content to restore
                    If content is environment,
                        List format:
                            list of strings, with each string corresponding to the environments display name, in lower case

                    If content is tables:
                        List format:
                            list of tuples, with each tuple, of the form: "environment_name","table_name"
                                where environment name if the name of the environment to which the table belongs to
                        Sample input:
                            [ ("testenv1" , "account") , ("testenv2","note") , ("testenv1","attachments")]

                restore_path            (list)--    List of the paths of the items to restore
                    Instead of passing, the restore content, restore path can be passed
                    Restore path, is the path for each item, that is to be restored.
                        Path is returned by the browse operation

                is_environment          (bool)--    Whether to content to be restored is a table or an environment
                overwrite               (bool)--    Skip or overwrite content
                job_id                  (int)--     Job ID for point in time restores
            Returns:
                _restore_job            (object)--  Object of CvPySDK.Job for the restore job
        """
        _restore_job = self.subclient.restore_in_place(restore_content=restore_content, restore_path=restore_path,
                                                       is_environment=is_environment, overwrite=overwrite,
                                                       job_id=job_id)
        self.log.info("Restore Job started with Job ID: {}".format(_restore_job.job_id))

        self.wait_for_job_completion(_restore_job)
        self.log.info("Dynamics 365 restore job with Job ID:{} completed".format(_restore_job.job_id))
        return _restore_job

    @test_step
    def delete_d365_client(self, client_name: str = None):
        """
            Method to delete the specified Dynamics 365 client.

            Arguments:
                client_name         (str)--     Name of the client to delete
                    If None:
                        Uses the client name from CVDynamics365.
        """
        if client_name is None:
            client_name = self.client_name

        if self.commcell.clients.has_client(client_name):
            self.log.info('Client: {} exists deleting it'.format(client_name))
            self.commcell.clients.delete(client_name)

    @test_step
    def run_and_verify_licensing(self, lic_added_user=None, lic_removed_user=None):
        """
            Method to run and verify d365 licensing.
            Arguments:
                lic_added_user      (str)   --      Username of the user to which license is added
                lic_removed_user    (str)   --      Username of the user from which license is removed

            Returns:
                Bool : True if verification successful, False otherwise
        """

        self.log.info("Waiting for 60s before launching licensing thread")
        time.sleep(60)
        self.log.info("Running d365 licensing operation")
        self.subclient.launch_d365_licensing()

        self.log.info("Verifying d365 licensing")
        if self.dynamics_obj.csdb_operations.get_licensing_info(int(self.instance.instance_id), lic_added_user,
                                                                lic_removed_user):
            return True
        return False

    @test_step
    def run_out_of_place_restore(self,
                                 restore_content: list = None,
                                 restore_path: list = None,
                                 is_environment: bool = False,
                                 overwrite: bool = True,
                                 job_id: int = None,
                                 destination_environment: str = str()):
        """
            Method to run out of place restore for the content specified.

            Arguments:
                restore_content         (str)--     List of the content to restore
                    If content is environment,
                        List format:
                            list of strings, with each string corresponding to the environments display name, in lower case

                    If content is tables:
                        List format:
                            list of tuples, with each tuple, of the form: "environment_name","table_name"
                                where environment name if the name of the environment to which the table belongs to
                        Sample input:
                            [ ("testenv1" , "account") , ("testenv2","note") , ("testenv1","attachments")]

                restore_path            (list)--    List of the paths of the items to restore
                    Instead of passing, the restore content, restore path can be passed
                    Restore path, is the path for each item, that is to be restored.
                        Path is returned by the browse operation

                is_environment          (bool)--    Whether to content to be restored is a table or an environment
                overwrite               (bool)--    Skip or overwrite content
                job_id                  (int)--     Job ID for point in time restores
                destination_environment (str)--     Destination environment to be selected for OOP restore
            Returns:
                _restore_job            (object)--  Object of CvPySDK.Job for the restore job
        """
        self.log.info("Running OOP Restore for: {} with destination as: {}".format(restore_content,
                                                                                   destination_environment))
        _restore_job = self.subclient.restore_out_of_place(restore_content=restore_content, restore_path=restore_path,
                                                           is_environment=is_environment, overwrite=overwrite,
                                                           job_id=job_id,
                                                           destination_environment=destination_environment)
        self.log.info("OOP Restore Job started with Job ID: {}".format(_restore_job.job_id))

        self.wait_for_job_completion(_restore_job)
        self.log.info("Dynamics 365 restore job with Job ID:{} completed".format(_restore_job.job_id))
        return _restore_job

    @test_step
    def submit_client_index_retention(self, index_server_client_id):
        """
            Make the API call to process the retention on the Index Server

          Args:
                index_server_client_id (int)  --  client id of index server

        """
        try:
            self.log.info("Processing index retention")
            self.subclient.process_index_retention(index_server_client_id)
            self.log.info("Waiting for retention to process")
            time.sleep(120)
            self.log.info("Processed index retention")
        except Exception as exception:
            self.log.exception("An error occurred while processing index retention")
            raise exception

    def get_plan_obj(self, plan_name):
        """"Returns plan object of the given plan name

                Args :

                    plan_name (str)     --  name of the plan

                Returns:

                    plan_obj            --  plan class object

        """
        if self.commcell.plans.has_plan(plan_name):
            return self.commcell.plans.get(plan_name)
        else:
            raise Exception(
                'Plan: "{0}" does not exist in the Commcell'.format('plan_name')
            )

    @test_step
    def move_client_job_results(self):
        """
            Move the job results directory for a Dynamics 365 Client.
        """
        _new_directory: str = self.tc_inputs.get("NewJobResultsDirectory").get("Path")
        _user_name: str = self.tc_inputs.get("NewJobResultsDirectory").get("Username")
        _password: str = self.tc_inputs.get("NewJobResultsDirectory").get("Password")

        self.log.info("Moving Job Results directory for client: {} to path: {} with LSA: {}".format(self.client_name,
                                                                                                    _new_directory,
                                                                                                    _user_name))
        self.client.change_dynamics365_client_job_results_directory(new_directory_path=_new_directory,
                                                                    username=_user_name, password=_password)
