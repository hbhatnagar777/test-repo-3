# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase and LogThread are the only classes defined in this file.

TestCase: Class for executing this test case,

LogThread: Class for logging possible exception within a thread.

TestCase:
    __init__()          --  initialize TestCase class

    clean_up()          --  entry point for clean up of this test case

    kill_jobs()         --  kill jobs function

    uninstall_clients() --  uninstall clients for this test case

    run()               --  run function of this test case
"""

import time
from threading import Thread
from datetime import datetime
from cvpysdk.job import Job
from AutomationUtils import cvhelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper
from Install.client_installation import Installation
from Application.Sharepoint.sharepointhelper import SharepointHelper


class LogThread(Thread):
    """Class for logging thread exceptions"""

    def __init__(self, log, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run
        self.log = log

    def _wrap_run(self):
        try:
            self._real_run()
        except:
            self.log.exception('Exception raised in LogThread.run')


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Sharepoint Farm Configuration Workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.workflow_name = "Configure SharePoint"

        self.workflow = None
        self.tcinputs = {
            "SharepointAdminUser": None,
            "SharepointAdminPassword": None,
            "SQLServerHostName": None,
            "SQLServerInstanceName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None,
            "StoragePolicyName": None
        }

        self.sphelper = None
        self.primary_member = None
        self.sharepoint_client = None
        self.sqlserver_hostname = None
        self.sql_client = None
        self.sqlinstance = None
        self.sqluser = None
        self.sqlpass = None
        self.spuser = None
        self.sppass = None
        self.sql_instance = None

    def clean_up(self, delete_only=False):
        """This function acts as clean up entry point for setup destruction

        Args:
            delete_only (bool, optional): Boolean value to only delete client from GUI client list.

        """
        self.log.info("*" * 10 + " Entering clean up phase " + "*" * 10)

        threads = []

        try:
            # refresh client list
            self.commcell.clients.refresh()

            for client in self.sphelper.sharepoint_client_members:
                if client in self.commcell.clients.all_clients:
                    if client == self.sql_client:
                        decrypted_pass = cvhelper.format_string(self.commcell, self.sqlpass)
                    else:
                        decrypted_pass = cvhelper.format_string(self.commcell, self.sppass)
                    if client == self.sharepoint_client.lower():
                        p_thread = LogThread(
                            self.log,
                            target=self.uninstall_clients,
                            args=(client, self.spuser, decrypted_pass),
                            kwargs={'delete_only': True}
                        )
                    else:
                        p_thread = LogThread(
                            self.log,
                            target=self.uninstall_clients,
                            args=(client, self.spuser, decrypted_pass),
                            kwargs={'delete_only': delete_only}
                        )
                    time.sleep(3)  # avoid collision during uninstall/delete
                    p_thread.start()
                    threads.append(p_thread)

            for p_thread in threads:
                p_thread.join()

        except Exception as excp:
            self.log.error("Exception raised in clean_up()\nError: '{0}'".format(excp))
            pass

    def kill_jobs(self, job_id):
        """This function kills a job and waits for it to be killed

        Args:
            job_id (str): Id of job to kill

        """
        try:
            job = Job(self.commcell, job_id)
            self.log.info("Killing active job [{0}]".format(job_id))
            job.kill(True)
        except Exception as excp:
            self.log.error("Failed to kill job [{0}] with error: {1}".format(job_id, excp))
            pass

    def uninstall_clients(self, client_name, client_user_name, client_password, delete_only=False, retry_attempt=3):
        """This function performs uninstall for all clients detected in the workflow

        Args:
            client_name (str): Client name
            client_user_name (str): User name of client machine
            client_password (str): Password of client machine user name
            delete_only (bool, optional): Boolean value to only delete client from GUI client list.
            retry_attempt (int, optional): Number of times to retry client deletion

        """

        try:
            # get list of active jobs for the client
            job_helper = self.commcell.job_controller
            job_list = job_helper.active_jobs(client_name)
            job_ids = list(job_list.keys())

            # kill any active jobs
            if job_ids:
                job_threads = []
                for job_id in job_ids:
                    job_thread = LogThread(
                        self.log,
                        target=self.kill_jobs,
                        args=(job_id,)
                    )
                    try:
                        job_thread.start()
                        job_threads.append(job_thread)
                    except Exception as excp:
                        self.log.error("Exception thrown killing job. Failed with error: {0}".format(excp))
                        pass

                for job_thread in job_threads:
                    job_thread.join()

            # uninstall package if required
            if not delete_only:
                # uninstall client dictionary
                install_dict = {
                    "client_name": client_name,
                    "client_host_name": client_name,
                    "client_user_name": client_user_name,
                    "client_password": client_password
                }

                install_helper = Installation.create_installer_object(install_dict, self.commcell)

                try:
                    self.log.info("Uninstalling client [{0}] software".format(client_name))
                    install_helper.uninstall_existing_instance()
                    self.log.info("Client [{0}] software has been deleted successfully.".format(client_name))
                except Exception as excp:
                    self.log.error("Exception thrown during client uninstall. Failed with error: {0}".format(excp))
                    pass

            self.log.info("Deleting client [{0}] from client list".format(client_name))
            while retry_attempt > 0:
                try:
                    self.commcell.clients.delete(client_name)
                    retry_attempt = 0
                except Exception:
                    retry_attempt -= 1
                    pass
            self.log.info("Client [{0}] has been deleted from the client list successfully.".format(client_name))

        except Exception as excp:
            self.log.error("Exception raised in uninstall_clients()\nError: '{0}'".format(excp))

    def run(self):
        """Main function for test case execution"""

        self.spuser = self.tcinputs["SharepointAdminUser"]
        self.sppass = self.tcinputs["SharepointAdminPassword"]
        self.sqlserver_hostname = self.tcinputs["SQLServerHostName"]
        self.sqlinstance = self.tcinputs["SQLServerInstanceName"]
        self.sqluser = self.tcinputs["SQLServerUser"]
        self.sqlpass = self.tcinputs["SQLServerPassword"]
        storagepolicy = self.tcinputs["StoragePolicyName"]

        self.sql_client = self.sqlserver_hostname.split(".")[0]

        if "\\" in self.sqlinstance:
            self.sql_instance = self.sqlinstance.split("\\")[1]
        else:
            self.sql_instance = self.sqlserver_hostname

        time1 = (datetime.now()).strftime("%H:%M:%S")
        sptime = time1.replace(":", "")
        self.sharepoint_client = "SharepointWF_{0}_{1}".format(self.id, sptime)

        self.sphelper = SharepointHelper(
            self,
            self.sharepoint_client,
            self.sql_client,
            self.sqlinstance,
            self.spuser,
            cvhelper.format_string(self.commcell, self.sqlpass)
        )

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.commcell.workflows.refresh()
            self.workflow = WorkflowHelper(self, self.workflow_name, deploy=False)

            # Start workflow execution
            wf_job = self.workflow.execute(
                {
                    "PseudoClientName": self.sharepoint_client,
                    "SQLServerName": self.sqlserver_hostname,
                    "SQLServerInstanceName": self.sql_instance,
                    "SQLUserName": self.sqluser,
                    "SQLPassword": self.sqlpass,
                    "SharePointAdminName": self.spuser,
                    "SharePointAdminPassword": self.sppass,
                    "StoragePolicy": storagepolicy
                },
                wait_for_job=False,
                hidden=True
            )

            while not wf_job.is_finished:
                if wf_job.status.lower() == 'running':
                    break
                time.sleep(3)  # need some time for workflow to begin and detect farm config.
            self.sphelper.spvalidate.get_sharepoint_members(self.sql_client, wf_job.job_id)

            if not wf_job.wait_for_completion():
                raise Exception("Workflow job execution {} with error {}".format(
                    wf_job.status, wf_job.delay_reason
                ))
                pass

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: {0}'.format(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.clean_up()

    def tear_down(self):
        """Tear down function"""
