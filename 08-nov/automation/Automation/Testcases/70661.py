# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import time
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.update_helper import UpdateHelper


class TestCase(CVTestCase):
    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.name = "Download and Installation of latest Updates"
        self.config_json = None
        self.status = None
        self.commcell = None
        self.job_obj_controller = None
        self.cs_machine = None
        self._client_group_obj = None
        self.client_group = None
        self.tcinputs = {
            'ServicePack': None,
            'client_computer_groups': None,
            'Kill_Active_jobs': None,
            'CSHostName': None,
            'CSPassword': None,
            'CSMachineUsername': None,
            'CSMachinePassword': None

        }
        self.update_helper = None
        self.is_Kill_Active_job = False

    def setup(self):
        """
        Method to setup test variables
        """
        self.log.info("Setup Started")
        self.config_json = config.get_config()
        self.log.info("Creating Smoke Test CS Machine")
        self.commcell = Commcell(webconsole_hostname=self.tcinputs.get("CSHostName"),
                                 commcell_username=DEFAULT_COMMSERV_USER,
                                 commcell_password=self.tcinputs.get("CSPassword"),
                                 verify_ssl=False)
        self.cs_machine = Machine(
            machine_name=self.tcinputs.get("CSHostName"),
            username=self.tcinputs.get("CSMachineUsername"),
            password=self.tcinputs.get("CSMachinePassword"))
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)
        self.job_obj_controller = self.commcell.job_controller
        self._client_group_obj = self.commcell.client_groups.get(self.tcinputs.get("client_computer_groups")[0])
        self.client_group = self.tcinputs.get("client_computer_groups")
        self.is_Kill_Active_job = True if str(self.tcinputs.get('Kill_Active_jobs')).lower() == "true" else False
        self.log.info("Setup Completed")

    def run(self):
        '''The run operation will perform a readiness check of the CS and then Starts the Download Job,
        the installation of the CS and installation of the clients will be performed.
        The readiness will be checked for all of the clients and the running jobs will be killed for a fresh run of the Jobs without
        intrupts'''
        try:
            self.log.info("Logging into CS")
            self.log.info("Checking Readiness of the CS machine")
            commserv_client = self.commcell.commserv_client
            if commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Commcell Readiness failed.")
                raise Exception("Commcell Readiness Failed")

            self.log.info("Starting to Download")
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            job_dwn = self.commcell.download_software(options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                                                      os_list=[package.value for package in DownloadPackages],
                                                      service_pack=self.tcinputs.get("ServicePack"),
                                                      cu_number=latest_cu, sync_cache=True
                                                      )
            self.log.info("Job %s Started", job_dwn.job_id)
            if job_dwn.wait_for_completion():
                self.log.info("Download software Job with job id %s completed successfully", job_dwn.job_id)
            else:
                self.log.error("Download software Job with job id %s Failed", job_dwn.job_id)
                raise Exception("Download software Job with job id %s Failed", job_dwn.job_id)
            self.log.info("Starting to Push Upgrade for CommCerve")
            self.update_helper.push_sp_upgrade(client_computers=[self.commcell.commserv_name])
            self.log.info("Successfully Completed Push Upgrade for CommCerve")
            time.sleep(20)
            self.log.info("Starting to Push Upgrade for the clients in %s clients", str(self.client_group))
            self.update_helper.push_sp_upgrade(client_computer_groups=self.client_group)
            self.log.info("Successfully Completed Push Upgrade for the %s clients", str(self.client_group))
            self.log.info("Checking readiness of Clients in %s.", str(self.client_group))
            failedClients = []
            for each_client in self._client_group_obj.associated_clients:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info("Check Readiness of Client is successful for %s", each_client)
                    else:
                        failedClients.append(each_client)
                        self.log.error("Check Readiness of Client is Failed for %s", each_client)
            if len(failedClients) >= 1:
                self.log.error("Check Readiness of Client is Failed for %s", str(failedClients))
                raise Exception("The clients " + str(failedClients) + " has been failed")
            if self.is_Kill_Active_job:
                self.log.info("Stared Killing Active Jobs")
                for jobid, job_data in self.job_obj_controller.active_jobs().items():
                    try:
                        if job_data['operation'] not in ['Disaster Recovery Backup', 'Data Aging']:
                            self.job_obj_controller.get(jobid).kill(wait_for_job_to_kill=True)
                            self.log.info("Kill job status for jobid %s is Killed.", str(jobid))

                    except:
                        self.log.error("Kill job failed for job id %s", str(jobid))
                self.log.info("Active jobs Kill Completed")
            self.log.info("Testcase Completed the run")

            self.result_string = "Download and Installation completed for the CS " + str(
                self.commcell.commserv_name) + " all the clients in " + str(self.client_group)
            self.status = constants.PASSED
        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = "Failed with an error: " + str(exp)
            self.status = constants.FAILED
