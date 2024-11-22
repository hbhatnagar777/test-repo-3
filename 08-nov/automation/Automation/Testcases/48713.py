# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from cvpysdk.commcell import Commcell
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Push Additional Packages to Unix Client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push Additional Packages to Unix Client"
        self.config_json = None
        self.unix_machine = None
        self.unix_hostname = None
        self.installer_flags = None
        self.unix_helper = None
        self.client_obj = None
        self.update_acceptance = False
        self.media_path = None
        self.install_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.unix_hostname = self.unix_machine.machine_name
        self.installer_flags = {
            "allowMultipleInstances": False
        }
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def run(self):
        """Main function for test case execution"""
        try:
            if not self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                raise Exception("No Commvault Instance found on the machine!!")
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()
            # Get Install Helper Object to Push Software
            self.unix_helper = InstallHelper(self.commcell, self.unix_machine)

            # Pushing Packages from CS to the client
            self.log.info(f"Starting a Push Install Job on the Machine: {self.unix_hostname}")
            push_job = self.unix_helper.install_software(
                client_computers=[self.unix_hostname],
                features=['MEDIA_AGENT'],
                username=self.config_json.Install.unix_client.machine_username,
                password=self.config_json.Install.unix_client.machine_password,
                install_flags=self.installer_flags
            )

            self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
            if push_job.wait_for_completion():
                self.log.info("Push Upgrade Job Completed successfully")

            else:
                job_status = push_job.delay_reason
                self.log.error(f"Job failed with an error: {job_status}")
                raise Exception(job_status)

            # Refreshing the Client list to me the New Client Visible on GUI
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            # Check if the services are up on Client and is Reachable from CS
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.unix_hostname):
                self.client_obj = self.commcell.clients.get(self.unix_hostname)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of client successful")
            else:
                self.log.info("Check Readiness Failed")

            # Install Validation to check if the Client Installation went fine
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.unix_hostname, self, machine_object=self.unix_machine,
                                                  package_list=[UnixDownloadFeatures.MEDIA_AGENT.value],
                                                  is_push_job=True)
            install_validation.validate_install()
            if self.update_acceptance:
                self.install_helper.install_acceptance_update('Pass', '-', self.unix_machine.machine_name)

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                _service_pack = installer_utils.get_latest_recut_from_xml("SP" + str(self.commcell.commserv_version))
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.unix_machine.machine_name,
                    _service_pack.split('_R')[-1])

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.unix_machine)
        if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
            self.unix_helper.uninstall_client(delete_client=False)
