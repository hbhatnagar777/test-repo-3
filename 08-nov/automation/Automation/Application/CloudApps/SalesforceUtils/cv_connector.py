# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main module for communicating with cvpysdk for all commvault related operations.

CvConnector class is defined in this file.

CvConnector: Performs Commvault related operations using cvpysdk

CvConnector:
    add_salesforce_client()             --  Creates new Salesforce pseudoclient in Commcell

    run_backup()                        --  Runs backup on subclient

    wait_for_automatic_full()           --  Waits for an already running full job to complete

    wait_for_job_suspend()              --  Waits for job to get suspended

    delete_client()                     --  Deletes client

    sync_db_name()                      --  Gets Sync DB name from Backupset

    get_access_node()                   --  Get machine object for access node

    check_if_file_exists()              --  Check if file exists on access node

    get_files_data_from_client()        --  Get files data from access node

    get_latest_job()                    --  Gets latest job id for the client

    convert_csv_string_to_data_dict()   --  converts input string to a dict of records

"""
import csv
import json
from time import sleep, time
from cvpysdk.instances.cloudapps.salesforce_instance import SalesforceInstance
from cvpysdk.backupsets.cloudapps.salesforce_backupset import SalesforceBackupset
from cvpysdk.subclients.cloudapps.salesforce_subclient import SalesforceSubclient
from AutomationUtils.machine import Machine
from cvpysdk.exception import SDKException
from .base import SalesforceBase


class CvConnector(SalesforceBase):
    """Class for performing Commvault operations"""

    def __get_cv_entities(self, client_name):
        """
        Gets client, instance, backupset and subclient object

        Args:
            client_name (str): Client Name

        Returns:
            tuple[cvpysdk.client.Client, SalesforceInstance, SalesforceBackupset, SalesforceSubclient]:
                Client, instance, backupset and subclient Commcell objects
        """
        self._commcell.clients.refresh()
        client = self._commcell.clients.get(client_name)
        instance = None
        try:
            instance = client.agents.get('Cloud Apps').instances.get("ORG1")
        except SDKException:
            instance = client.agents.get('Cloud Apps').instances.get(client_name)

        backupset = instance.backupsets.get(instance.backupsets.default_backup_set)
        subclient = backupset.subclients.get('default')
        return client, instance, backupset, subclient

    def add_salesforce_client(
            self,
            name,
            storage_policy=None,
            salesforce_options=None,
            db_options=None,
            **kwargs
    ):
        """
        Creates new Salesforce pseudoclient in commcell

        Args:
            name (str): Name of pseudoclient and instance
            storage_policy (str): Storage policy (Default is read from config)
            salesforce_options (dict): Salesforce options to override tcinputs/config
            db_options (dict): Database options to override tcinputs/config
            kwargs (dict): Keyword arguments

        Keyword Args:
            access_node (str): Access node name (Default is set in config file)
            cache_path (str): Download cache path on access node (Default is set in config file)

        Returns:
            tuple[cvpysdk.client.Client, SalesforceInstance, SalesforceBackupset, SalesforceSubclient]:
                Client, instance, backupset and subclient Commcell objects
        """
        if self._commcell.clients.has_client(name):
            raise Exception(f'Client with name {name} already exists in commcell')
        if not db_options:
            db_options = dict()
        if not salesforce_options:
            salesforce_options = dict()
        if 'db_type' in db_options:
            db_options['db_type'] = db_options['db_type'].value
        db_options['db_enabled'] = True
        infra_options = self.updated_infrastructure_options(**db_options)
        sf_options = self.updated_salesforce_options(**salesforce_options)
        self._log.info(f"Creating Salesforce pseudoclient {name}")
        self._commcell.clients.add_salesforce_client(
            client_name=name,
            access_node=kwargs.get('access_node', infra_options.access_node),
            salesforce_options=sf_options.__dict__,
            db_options=infra_options.__dict__,
            download_cache_path=kwargs.get('cache_path', infra_options.cache_path),
            storage_policy=storage_policy or self.storage_policy
        )
        self._log.info(f"Salesforce pseudoclient {name} created successfully")
        return self.__get_cv_entities(name)

    def __wait_for_job_completion(self, job):
        """
        Method that waits for completion of job

        Args:
            job (cvpysdk.job.Job):  Job Object
        """
        self._log.info(f"Job id is {job.job_id}. Waiting for completion")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run job: {job.job_id} with error: {job.delay_reason}")
        self._log.info(f"Successfully finished {job.job_id} job")

    def run_backup(self, subclient, backup_level="Incremental", wait_for_completion=True):
        """
        Runs backup on subclient

        Args:
            subclient (SalesforceSubclient): subclient object
            backup_level (str): "Full" or "Incremental"
            wait_for_completion (bool): If True, waits for job completion
                                        If False, returns job object without waiting for completion

        Returns:
            tuple[cvpysdk.job.Job, cvpysdk.job.Job]: Job object for the backup job, and Job object for automatic
                        incremental job if backup_level is "Full"

        Raises:
            Exception: If job fails
        """
        if not isinstance(subclient, SalesforceSubclient):
            raise Exception(f"The subclient parameter needs to be an object of type SalesforceSubclient, instead got "
                            f"{type(subclient)}")
        self._log.info(f"Running {backup_level} backup on subclient: {subclient.name}, backupset: "
                       f"{subclient._backupset_object.name} and instance: "
                       f"{subclient._instance_object.name}")
        sleep(60)
        job = subclient.backup(backup_level)
        if wait_for_completion:
            self.__wait_for_job_completion(job)
            if backup_level.lower() == "full":
                sleep(30)
                inc_job = subclient.find_latest_job()
                if inc_job.job_id == job.job_id:
                    self._log.error("Automatic incremental job not found")
                    return (job,)
                self._log.info("Automatic incremental job launched successfully")
                self.__wait_for_job_completion(inc_job)
                return job, inc_job
        return (job,)

    def wait_for_automatic_full(self, client_name):
        """
        Waits for an already running full job to complete

        Args:
            client_name (str): Name of Salesforce organization

        Returns:
            tuple[cvpysdk.job.Job, cvpysdk.job.Job]: Full job object and Incremental job object
        """
        _, _, _, subclient = self.__get_cv_entities(client_name)
        for _ in range(60):
            try:
                full_job = subclient.find_latest_job()
                break
            except SDKException:
                sleep(10)
        else:
            raise Exception(f"Job not found for {client_name}")
        self._log.info(f"Found full job id {full_job.job_id}")
        self.__wait_for_job_completion(full_job)
        sleep(10)
        inc_job = subclient.find_latest_job()
        if inc_job.job_id == full_job.job_id:
            self._log.error("Automatic incremental job not found")
            return (inc_job,)
        self._log.info("Automatic incremental job launched successfully")
        self.__wait_for_job_completion(inc_job)
        return full_job, inc_job

    def wait_for_job_suspend(self, job_id, timeout=15):
        """
        Waits for job to get suspended

        Args:
            job_id (int): Job id
            timeout (int): Time in minutes to wait before killing job if it goes into pending or waiting state

        Returns:
            None:

        Raises:
            Exception: If job is stuck in pending/waiting state or job finishes without suspend
        """
        job = self._commcell.job_controller.get(job_id)
        status_list = ['pending', 'waiting']
        start_time = time()
        previous_status = None

        while (status := job.status.lower()) != 'suspended':
            sleep(30)
            if status in status_list:
                if previous_status not in status_list:
                    start_time = time()
                elif (time() - start_time) / 60 >= timeout:
                    job.kill()
            previous_status = status
            if job.is_finished:
                raise Exception(f"Job finished with status {job.status}. Delay reason {job.delay_reason}")

    def delete_client(self, client_name):
        """
        Kill any running jobs and delete client

        Args:
            client_name (str): Client name

        Returns:
            None:
        """
        _, _, _, subclient = self.__get_cv_entities(client_name)
        latest_job = subclient.find_latest_job()
        if not latest_job.is_finished:
            latest_job.kill(True)
        self._commcell.clients.delete(client_name)

    def sync_db_name(self, client_name):
        """
        Gets name of sync db from backupset properties

        Args:
            client_name (str): Client name

        Returns:
            str: Sync DB name
        """
        _, _, backupset, _ = self.__get_cv_entities(client_name)
        return backupset.sync_db_name

    def get_access_node(self):
        """
        Get machine object for access node

        Returns:
            machine object
        """
        self._log.info(f"Establishing connection with access node: {self.infrastructure_options.access_node}")
        access_node = Machine(self.infrastructure_options.access_node, self._commcell)
        self._log.info("Connected to access node successfully")
        return access_node

    def get_files_data_from_client(self, file_paths):
        """
        Get files data from access node

        Args:
            file_paths: list of file paths

        Returns:
            list of data from the files
        """
        access_node = self.get_access_node()
        files_data = []
        for file_path in file_paths:
            self._log.info(f"Reading file at path: {file_path}")
            file_data = access_node.read_file(file_path)
            data = convert_csv_string_to_data_dict(file_data)
            self._log.info(f"Read {len(data)} records from {file_path.split('/')[-1]}")
            files_data.append(data)
        return files_data

    def check_if_file_exists(self, path):
        """
        Check if file exists on access node

        Returns:
            bool
        """
        access_node = self.get_access_node()
        return access_node.check_file_exists(path)

    def get_latest_job(self, client_name=None, job_filter="Backup,Restore"):
        """
        Gets latest job id for the client

        Args:
            client_name: Name of the client
            job_filter  (str): to specify type of job
                    default: 'Backup,Restore'
        Returns:
            latest job id
        """
        if client_name:
            _, _, _, subclient = self.__get_cv_entities(client_name)
            entity_dict = {
                "subclientId": int(subclient.subclient_id)
            }
            client_jobs = self._commcell.job_controller.all_jobs(
                client_name=client_name,
                job_filter=job_filter,
                entity=entity_dict
            )
            return str(max(client_jobs.keys()))
        else:
            jobs = json.loads(self._commcell.request("GET", f"/Job?jobFilter={job_filter}").text).get('jobs')
            return str(sorted(jobs, key=lambda x: x['jobSummary']['jobId'], reverse=True)[0]['jobSummary']['jobId'])

    def add_additional_key_on_access_node(self, key, value, client=None, **kwargs):
        """
        Adds additional key on access node

        Args:
            key: key to add
            value: value for the key
            client: Access node name
        Keyword Args:
            category (str): Category of the key (Default is 'CloudConnector')
            data_type (str): Data type of the key (Default is 'BOOLEAN')
        Returns:
            None
        """
        if not client:
            client = self.infrastructure_options.access_node
        access_node = self._commcell.clients.get(client)
        access_node.add_additional_setting(kwargs.get('category', 'CloudConnector'), key,
                                           kwargs.get('data_type', 'BOOLEAN'), value)

    def remove_additional_key_from_access_node(self, key, client=None, **kwargs):
        """
        Removes additional key from access node

        Args:
            key: key to delete
            client: Access node name
        Keyword Args:
            category (str): Category of the key (Default is 'CloudConnector')
        Returns:
            None
        """
        if not client:
            client = self.infrastructure_options.access_node
        access_node = self._commcell.clients.get(client)
        access_node.delete_additional_setting(kwargs.get('category', 'CloudConnector'), key)


def convert_csv_string_to_data_dict(csv_string):
    """
    converts input string to a dict of records

    Args:
        csv_string: string of records
    """
    values = csv_string.split('\n')
    values = [val.replace('\r', '') for val in values]
    values = [val.replace('"', '') for val in values]
    data = list(csv.DictReader(values, delimiter=','))
    return data
