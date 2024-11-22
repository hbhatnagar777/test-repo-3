# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for communicating with cvpysdk for all commvault related operations.

CvOperation class is defined in this file.

CvOperation: Performs Commvault related operations using cvpysdk

    __init__()              --  Initializes the CvOpetaion object by calling commcell object of cvpysdk.

    delete_client ()        --  Deletes the client present in the commcell

    add_exchange_plan()     --  Creates exchange plan
"""

from __future__ import unicode_literals

import time

from AutomationUtils import machine
from AutomationUtils.machine import Machine
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from . import constants as CONSTANT
from cvpysdk.job import JobController
from .constants import AD_MAILBOX_MONITORING_EXE


class CvOperation(object):
    """Class for performing Commvault operations"""

    def __init__(self, ex_object):
        """Initializes the CvOpetaion object by calling commcell object of cvpysdk.

                Args:
                    ex_object  (object)  --  instance of ExchangeMailbox class
                Returns:
                    object  --  instance of CvOperation class
        """

        self.tc_object = ex_object.tc_object
        self.ex_object = ex_object
        self.commcell = self.tc_object.commcell
        self.tcinputs = self.tc_object.tcinputs
        self.log = self.tc_object.log
        self.configuration_policies = self.commcell.policies.configuration_policies
        self.client_name = ex_object.client_name

        self.app_name = self.__class__.__name__  # Used for exception list

        self._client = None
        self.plans = self.commcell.plans
        self._BROWSE_MAILBOXES = None

    @property
    def backupset(self):
        """Returns backupset commcell object."""
        if self.client is not None:
            agent = self.client.agents.get(CONSTANT.AGENT_NAME)
            return agent.backupsets.get(self.ex_object.backupset_name)
        else:
            raise Exception('Please create exchange Mailbox client')

    @property
    def agent(self):
        if self.client is not None:
            return self.client.agents.get(CONSTANT.AGENT_NAME)
        else:
            raise Exception("Please create valid Exchange Mailbox client first")

    @property
    def subclient(self):
        """Returns subclient commcell object"""
        return self.backupset.subclients.get(self.ex_object.subclient_name)

    @property
    def client(self):
        """Treats the client as a read-only attribute."""
        try:
            if not self._client:
                if not self.client_name or not self.commcell.clients.has_client(self.client_name):
                    raise Exception("Client does not exist. Check the client name")
                self._client = self.commcell.clients.get(self.client_name)
            return self._client
        except Exception as err:
            self.log.exception("Exception while getting client object.")
            raise Exception(err)

    @client.setter
    def client(self, client):
        self._client = client

    def add_exchange_client(self):
        """Add Exchange Mailbox Client to commcell"""

        try:
            self.log.info('Creating Exchange Mailbox Client %s', self.client_name)
            if self.commcell.clients.has_client(self.client_name):
                self.log.info('Client exists. Deleting it and creating')
                self.commcell.clients.delete(self.client_name)
            self._client = self.commcell.clients.add_exchange_client(
                self.client_name, self.ex_object.index_server, self.ex_object.proxies,
                self.ex_object.server_plan, self.ex_object.recall_service,
                self.ex_object.job_results_directory, self.ex_object.exchange_server,
                self.ex_object.service_account_dict, self.ex_object.azure_app_key_secret,
                self.ex_object.azure_tenant_name, self.ex_object.azure_app_id,
                self.ex_object.environment_type, self.ex_object.backupset_type)
            return self._client
        except Exception as excp:
            self.log.exception("An error occurred while creating exchange mailbox client")
            raise excp

    def add_case_client(self):
        """Add case Client to commcell

            Returns:

                object  --  instance of Cvpysdk client """
        try:
            self.log.info('Creating Case Client %s', self.client_name)
            if self.commcell.clients.has_client(self.client_name):
                self.log.info('Client exists. Deleting it and creating')
                self.commcell.clients.delete(self.client_name)
            self._client = self.commcell.clients.add_case_client(
                self.client_name, self.ex_object.server_plan, self.ex_object.dc_plan,
                self.ex_object.hold_type)
            return self._client
        except Exception as excp:
            self.log.exception("An error occurred while creating case client")
            raise excp

    def get_policy_object(self, policy_name, policy_type):
        """Creates the policy object based on the type
            Args:
                policy_name (str)        --  name of the policy

                policy_type(str)         --  Archive/Cleanup/Retention/Journal
            Returns:
                object  --  instance of Archive/Cleanup/Retention/Journal policy

        """
        return self.configuration_policies.get_policy_object(
            policy_type, policy_name)

    def enable_ews_support(self, service_url):
        """
            This function enables support for EWS protocol to back up on-prem mailboxes
            Args:
                service_url (string) -- EWS Connection URL for your exchange server
            Returns: None
        """
        try:
            _agent = self.agent
            _agent.enable_ews_support_for_exchange_on_prem(ews_service_url=service_url)
        except Exception as excp:
            self.log.exception("EWS Support not enabled")
            raise excp

    def add_exchange_policy(self, policy_object):
        """Creates exchange policy.

            Args:
                policy_object (object)  --  policy object needs ro created.
            Returns:
                object  --  instance of Configuration policy

        """

        try:
            self.log.info(
                'Creating Exchange Policy %s ', policy_object.name)
            if self.configuration_policies.has_policy(policy_object.name):
                self.log.info(
                    'Policy exists. Deleting it and creating')
                self.configuration_policies.delete(policy_object.name)
            policy = self.configuration_policies.add_policy(
                policy_object)
            return policy
        except Exception as excp:
            self.log.exception("An error occurred while creating exchange exchange policy")
            raise excp

    def add_exchange_plan(self, plan_name=None, plan_sub_type=CONSTANT.EXCHANGE_PLAN_SUBTYPE, **kwargs):
        """Creates exchange plan.
                plan_name           (str)   --  Name of the plan

                plan_sub_type       (str)   --  Type of plan to add - ExchangeUser or ExchangeJournal
                        Default: ExchangeUser

                kwargs              (dict)  --  Optional parameters for creating a plan
                    Accepted Values:
                        retain_msgs_received_time           (int)   -- Retain messages based on received time
                        retain_msgs_deletion_time           (int)   -- Retain messages based on deletion time
                        enable_cleanup_archive_mailbox      (bool)  -- Enable cleanup on archive mailbox
                        cleanup_msg_older_than              (int)   -- Cleanup messages older than
                        cleanup_msg_larger_than             (int)   -- Cleanup messages larger than
                        enable_content_search               (bool)  -- Enable content indexing
                        enable_archive_on_archive_mailbox   (bool)  -- Enable archive on archived mailbox
                        create_stubs                        (bool)  -- Create stubs during cleanup
                        prune_stubs                         (bool)  -- Prune stubs during cleanup
                        prune_msgs                          (bool)  -- Prune messages during cleanup
                        number_of_days_src_pruning          (int)   -- Number of days for source pruning
                        include_msgs_older_than             (int)   -- Include messages older than for archiving
                        include_msgs_larger_than            (int)   -- Inlcude messages larger than for archiving

            Returns:
                Plan object of the created plan

        """

        try:
            plan_name = plan_name or CONSTANT.EXCHANGE_PLAN_NAME % self.tc_object.id
            self.log.info(
                'Creating Exchange Plan %s ', plan_name)
            if self.plans.has_plan(plan_name):
                self.log.info(
                    'Plan already exists. Deleting it and creating again')
                self.plans.delete(plan_name)
            return self.plans.add_exchange_plan(plan_name, plan_sub_type, **kwargs)

        except Exception as excp:
            self.log.exception("An error occurred while creating exchange plan")
            raise excp

    def run_backup(self, user_mailbox=True, post_backup_wait=False):
        """Runs backup for subclient object of cvpysdk
        """
        active_job_exists = True
        try:
            try:
                self.log.info("Getting already running backup job")
                job = self.get_auto_triggered_active_job(client_name=self.client_name)
            except Exception as excp:
                self.log.info("No active job exists")
                self.log.info("Checking if the already triggered job completed")
                job = self.get_latest_completed_job_for_client(client_name=self.client_name)
                if not job:
                    active_job_exists = False
                if not active_job_exists:
                    self.log.info('Running backup job.')
                    self.log.info('Running backup for client %s', self.client_name)
                    subclient = self.tc_object._subclient
                    job = subclient.backup()
                    self.log.info('Backup job started; job ID: %s', job.job_id)
            finally:
                self.check_job_status(job)
                if post_backup_wait:
                    time.sleep(60)
                if not user_mailbox:
                    solr = SolrHelper(self.ex_object, None, False)
                else:
                    solr = SolrHelper(self.ex_object)
                solr.check_all_items_played_successfully(job.job_id)
        except Exception as excp:
            self.log.exception("An error occurred while running backup")
            raise excp
        return job


    def run_pst_ingestion(self):
        """Runs pst ingestion for subclient object of cvpysdk

            Returns:
                Job object
        """
        try:
            self.log.info('Running PST Ingestion job for client %s', self.client_name)
            subclient = self.tc_object._subclient
            job = subclient.pst_ingestion()
            self.log.info('PST Ingestion job started; job ID: %s', job.job_id)
            self.check_job_status(job)
            self.log.info('PST Ingestion job completed')
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running PST Ingestion")
            raise excp

    def browse_mailboxes(self):
        """
            The following method is used to browse the mailboxes which are available on the client.
        """
        try:
            self.log.info("Browsing mailboxes available for restore")
            subclient = self.tc_object.subclient
            mailboxes = subclient.browse_mailboxes()
            self.log.info("Mailboxes : {0}".format(mailboxes))
            return mailboxes
        except Exception as excp:
            self.log.exception("Browsing operation failed")
            raise excp

    def run_restore(self,
                    paths=[r"\MB"],
                    overwrite=True,
                    journal_report=False,
                    oop=False,
                    destination_mailbox=None,
                    restore_as_stub=None,
                    recovery_point_id=None,
                    restore_selected_mailboxes=False,
                    source_mailboxes=None,
                    destination_mailbox_folder=None):
        """Runs restore for subclient object of cvpysdk
            Args:
                paths (List)                --  Mailbox/Folder path to restore
                    Default: [r"\MB"]

                overwrite(boolean)          --  set it True to rstore with overwrite
                    Default: True

                journal_report(boolean)     --  set it True to restore with journal recpeint
                    Default: False

                oop(boolean)            --  set it True to rstore out of place
                    Default: False

                destination_mailbox(str)--  Destination Mailbox to restore
                    Default: None

                restore_as_stub(dict)--  stub rules to stub items during restore
                    Default: None

                recovery_point_id(int)-- ID of the recovery point
                    Default: None

                restore_selected_mailboxes(bool)-- set it True if you want to restore selected mailboxes
                    Default:-False

                source_mailboxes(list) -- if restore_selected_mailboxes is True then provide the list of source mailbox (alias names) which are needed to be restored
                    Default:-None

                destination_mailbox_folder(str) -- Folder name in which you want to restore the content.
                    Default:-None
        """
        try:
            subclient = self.tc_object._subclient
            self.log.info('Running restore job.')
            self.log.info('Running restore for client %s', self.client_name)
            if oop:
                if restore_selected_mailboxes:
                    paths.clear()
                    users = self.tc_object.subclient.discover_users
                    for user in users:
                        for mailbox in source_mailboxes:
                            if user["aliasName"].lower() == mailbox.lower():
                                path = "\\MB\\{%s}" % user["user"]["userGUID"]
                                paths.append(path)
                paths, dictionary = self.tc_object.subclient.browse(paths)
                oop_source = paths
                users = self.tc_object.subclient.discover_users
                self.log.info('Setting source path for OOP restore as %s', oop_source)
                oop_destination = None
                for user in users:
                    if user['aliasName'].lower() == destination_mailbox.lower():
                        if destination_mailbox_folder:
                            oop_destination = (f'\\MB\\{user["displayName"]}\\{destination_mailbox_folder}{chr(18)}'
                                               f'{user["aliasName"]}{chr(18)}{user["smtpAdrress"]}')
                        else:
                            oop_destination = (f'\\MB\\{user["displayName"]}{chr(18)}'
                                               f'{user["aliasName"]}{chr(18)}{user["smtpAdrress"]}')
                        break
                if oop_destination is None:
                    raise Exception("Alias Name for destination mailbox not found")

                self.log.info(
                    'Setting destination path for OOP restore as %s' % str(oop_destination))
                job = subclient.out_of_place_restore(oop_source, oop_destination,
                                                     overwrite=overwrite)
            else:
                job = subclient.restore_in_place(
                    paths=paths,
                    overwrite=overwrite,
                    journal_report=journal_report,
                    restore_as_stub=restore_as_stub,
                    recovery_point_id=recovery_point_id)

            self.log.info('Restore job started; job ID: %s' % str(job.job_id))
            self.check_job_status(job)
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running restore")
            raise excp

    def disk_restore(self,
                     destination_dir,
                     destination_client,
                     paths=[r"\MB"],
                     journal_report=False,
                     overwrite=True):
        """Runs disk restore for subclient object of cvpysdk
            Args:
                destination_dir(str)    --  Destination path for restore

                destination_client(str) --  Destination client for restore

                paths (List)            --  Mailbox/Folder path to restore
                    Default: [r"\MB"]

                journal_report(boolean) --  set it True to restore with journal recipient
                    Default: False

                overwrite(boolean)      --  set it True to restore with overwrite
                    Default: True
        """
        try:
            subclient = self.tc_object._subclient
            paths, dictionary = self.tc_object.subclient.browse(paths)
            if not self.commcell.clients.has_client(destination_client.lower()):
                raise Exception("Client name %s not found" % str(destination_client.lower()))
            remote_machine = Machine(destination_client, self.commcell)
            remote_machine.remove_directory(destination_dir, 0)
            job = subclient.disk_restore(
                paths=paths, destination_client=destination_client,
                destination_path=destination_dir,
                overwrite=overwrite, journal_report=journal_report)
            self.log.info('Disk Restore job started; job ID: %s' % str(job.job_id))
            self.check_job_status(job)
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running restore")
            raise excp

    def run_content_indexing(self):
        """Runs content indexing for subclient object of cvpysdk
            Returns:
                Job object
        """

        try:
            self.log.info('Running content indexing job.')
            self.log.info('Running content indexing for client %s', self.client_name)
            subclient = self.tc_object._subclient

            job = subclient.subclient_content_indexing()
            self.log.info('Content indexing job started; job ID: %s', job.job_id)
            self.check_job_status(job)
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running content indexing")
            raise excp

    def cleanup(self):
        """Runs cleanup for subclient object of cvpysdk"""
        try:
            self.log.info('Running Cleanup job for client %s', self.client_name)
            subclient = self.tc_object._subclient

            job = subclient.cleanup()
            self.log.info('Cleanup job started; job ID: %s', job.job_id)
            self.check_job_status(job)
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running cleanup job")
            raise excp

    def index_copy(self):
        """Runs index copy for Case subclient object of cvpysdk"""
        try:
            self.log.info('Running Index copy job.')
            self.log.info('Running Index for client %s', self.client_name)
            job = self.subclient.index_copy()
            self.log.info('Index copy job started; job ID: %s', job.job_id)
            self.check_job_status(job)
        except Exception as excp:
            self.log.exception("An error occurred while running Index Copy")
            raise excp

    def check_job_status(self, job):
        """Checks the status of job until it is finished and
            raises exception on pending, failure etc.

                Args:
                    job (Object of job class of CVPySDK)"""
        self.log.info('%s started for subclient %s with job id: %s', job.job_type,
                      self.subclient.subclient_name, job.job_id)

        if not job.wait_for_completion():
            self.log.exception("Pending Reason %s", job.pending_reason)
            raise Exception

        self.log.info('%s job completed successfully.', job.job_type)

    def pst_restore(self,
                    destination_pst,
                    destination_client,
                    paths=[r"\MB"],
                    journal_report=False,
                    overwrite=True):
        """Runs pst restore for subclient object of cvpysdk
            Args:
                destination_pst(str)    --  Destination path for restore

                destination_client(str) --  Destination client for restore

                paths (List)            --  Mailbox/Folder path to restore
                    Default: [r"\MB"]

                journal_report(boolean) --  set it True to restore with journal recipient
                    Default: False

                overwrite(boolean)      --  set it True to restore with overwrite
                    Default: True
        """
        try:
            subclient = self.tc_object._subclient
            paths, dictionary = self.tc_object.subclient.browse(paths)
            if not self.commcell.clients.has_client(destination_client.lower()):
                raise Exception("Client name %s not found %s" % destination_client.lower())
            remote_machine = Machine(destination_client, self.commcell)
            if remote_machine.check_file_exists(destination_pst):
                remote_machine.delete_file(destination_pst)
            job = subclient.pst_restore(paths=paths, destination_client=destination_client,
                                        pst_path=destination_pst, overwrite=overwrite,
                                        journal_report=journal_report)
            self.log.info('PST Restore job started; job ID: %s' % str(job.job_id))
            self.check_job_status(job)
            return job
        except Exception as excp:
            self.log.exception("An error occurred while running restore")
            raise excp

    def run_admailbox_monitor(self):
        """ Runs ADMailboxMonitor process for the exchange client"""
        try:
            machine = Machine(self.ex_object.proxies[0], self.ex_object.commcell)
            self.log.info('Running ADMailboxMonitor for client %s', self.client_name)
            cmd = (f'{CONSTANT.AD_MAILBOX_MONITORING_EXE} -o autodiscover -refreshInterval 1 -a 2'
                   f' -c {self.commcell.clients.get(self.ex_object.client_name).client_id}:'
                   f'{self.ex_object.client_name}'
                   f' -cn {self.ex_object.proxies[0]} -vm {machine.instance}')
            self.log.info('Running ADMailboxMonitor with arguments: %s' % cmd)
            machine.execute_command(cmd)
        except Exception as excp:
            self.log.exception("An error occurred while running ADMailboxMonitor")
            raise excp

    def run_retention(self):
        """Runs the CvExAutomatedtask Process on the proxy"""
        try:
            machine = Machine(self.ex_object.proxies[0], self.ex_object.commcell)
            self.log.info("Running CvExAutomatedtask process on %s" % self.ex_object.proxies[0])
            command = (f'CvExAutomatedtask.exe -vm {machine.instance} -SubmitRet -IS '
                       f'{self.commcell.clients.get(self.ex_object.client_name).client_id}')
            machine.execute_command(command)
        except Exception as excp:
            self.log.exception("An error occurred while running retention")
            raise excp

    def backup_public_folders(self):
        """
            Function to backup the public folders of any Exchange Client
            Returns:
                job     (object)    -   Instance of Job class for
                                        Backup Job
        """
        active_job_exists = True
        job = None
        try:
            try:
                self.log.info("Getting already running backup job")
                job = self.get_auto_triggered_active_job(client_name=self.client_name)
            except Exception as excp:
                self.log.info("No active job exists")
                self.log.info("Checking if the already triggered job completed")
                job = self.get_latest_completed_job_for_client(client_name=self.client_name)
                if not job:
                    active_job_exists = False
                if not active_job_exists:
                    self.log.info('Starting Public Folders Backup')
                    subclient_content = [
                        {
                            "associationName": "All Public Folders",
                            "associationType": 12
                        }
                    ]
                    job = self.subclient.backup_generic_items(subclient_content=subclient_content)
                    self.log.info('Backup Job Started with Job ID: {}'.format(job.job_id))
            finally:
                self.check_job_status(job)
        except Exception as excp:
            self.log.info("There is some error running Backup Job.")
            raise excp
        return job


    def create_restore_point(self, mailbox_alias, b_job):
        """
            Method to create a restore point/ recovery point for an Exchange Mailbox

            Arguments:
                mailbox_alias       (str)--     Alias name of the mailbox for which
                                                recovery point has to be created
                b_job               (obj)--     Instance of Job class fot the backup
                                                job to which the recovery point has
                                                to be created

            Returns
                recovery_point_id   (int)--     ID of the recovery point which has been created
        """

        mailbox_guid = self.ex_object.csdb_helper.get_mailbox_guid(mailbox_list=[mailbox_alias])
        mailbox_smtp = mailbox_alias + "@" + self.ex_object.domain_name
        index_server = self.ex_object.index_server

        mailbox_prop = {
            'mailbox_smtp': mailbox_smtp,
            'mailbox_guid': mailbox_guid[mailbox_alias.lower()],
            'index_server': index_server
        }

        self.log.info(
            'Creating Recovery Point for mailbox: {} corresponding to backup job: {}'.format(
                mailbox_smtp, b_job.job_id))
        res_dict = self.subclient.create_recovery_point(
            mailbox_prop=mailbox_prop, job=b_job)

        recovery_point_job_id = res_dict.get('recovery_point_job_id', 0)
        recovery_point_id = res_dict.get('recovery_point_id', 0)

        recovery_point_job = self.commcell.job_controller.get(recovery_point_job_id)

        self.log.info(
            'Recovery Point Creation Started with Job ID: {}'.format(
                recovery_point_job.job_id))
        recovery_point_job.wait_for_completion()
        self.log.info('Recovery Point created with ID: {}'.format(recovery_point_id))

        return recovery_point_id

    def modify_backup_streams(self, stream_count: int):
        """
            Method to modify the number of backup streams used for backup

            Arguments:
                stream_count        (int)--     Number of backup streams to set
        """

        update_dict = {
            "exchangeDBSubClientProp": {
                "numberOfExchangeBackupStreams": stream_count
            }
        }
        self.tc_object.subclient.update_properties(properties_dict=update_dict)

    def get_automatic_ci_job(self, client=None):
        """Get the job details of the automatic CI job that gets kicked off after backup
        Will work only if there are no other CI jobs ran on the client
            Args:
                client(obj) -- Object of client class

            Returns:
                Object of the ci job
        """
        job_controller = JobController(self.commcell)
        jobs = job_controller.all_jobs(client_name=client.client_name if client else self.client.client_name)
        job_id = None
        for key, value in jobs.items():
            if value['operation'].lower() == 'content indexing':
                job_id = key
        if not job_id:
            self.log.info("------------No CI job found, running CI manually---------------")
            job_obj = self.run_content_indexing()
        else:
            job_obj = job_controller.get(int(job_id))
        self.check_job_status(job_obj)
        return job_obj

    def delete_client(self):
        """
        Deletes the client present in the commcell
            Raises:
                  If delete client fails
        """
        try:
            if self.client is not None:
                self.log.info(f"Trying to delete client with name [{self.client.name}]")
                self.commcell.clients.delete(self.client.name)
            self.log.info(f"Successfully deleted client with name [{self.client.name}]")
        except:
            self.log.exception("An error occurred while deleting the client")

    def wait_for_ad_mailbox_monitor(self):
        """Method to wait for the AD Mailbox Process to terminate on the access node."""
        _access_node = machine.Machine(machine_name=self.ex_object.server_name,
                                       commcell_object=self.ex_object.commcell)
        _access_node.wait_for_process_to_exit(process_name=AD_MAILBOX_MONITORING_EXE)
        self.log.info('AdMailBoxMonitor has finished executing on: {}'.format(_access_node.machine_name))

    def get_auto_triggered_active_job(self, client_name, time_limit=5, retry_interval=1):
        ''' Gives the first active job object that is running
        args:
        client_name : {str} client name on which to check the active job list

        returns
        job_obj (list)  : returns the first active job object '''

        time_limit = time.time()+time_limit*60
        jobcontroller = self.commcell.job_controller
        active_jobs = jobcontroller.active_jobs(client_name=client_name, job_filter="Archive")
        while not active_jobs:
            active_jobs = jobcontroller.active_jobs(client_name=client_name, job_filter="Archive")
            if not active_jobs:
                if time.time() >= time_limit:
                    raise Exception("Timed out waiting to get valid active jobs")
                else:
                    time.sleep(retry_interval)
        active_job_id = list(active_jobs.keys())[0]
        jm_obj = jobcontroller.get(active_job_id)
        return jm_obj

    def get_latest_completed_job_for_client(self, client_name):
        """
        Gets the latest completed job for client
        :param client_name: name of the client
        :return: latest complete job object
        """
        jobcontroller = self.commcell.job_controller
        completed_jobs = jobcontroller.finished_jobs(client_name=client_name, job_filter="Archive")
        jm_obj=None
        if completed_jobs:
            finished_job_id = list(completed_jobs.keys())[0]
            jm_obj = jobcontroller.get(finished_job_id)
        return jm_obj
