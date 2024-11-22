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

    tear_down()     --  tear down function of this test case

"""
from threading import Thread
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from Install.install_validator import InstallValidator
from Install import installer_messages, installer_utils
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase : Push updates to existing client which is not reachable"""

    def __init__(self):
        """Initializes tset case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push updates to existing client which is not reachable"
        self.machine_obj = None
        self.windows_install_helper = None
        self.unix_install_helper = None
        self.config_json = None
        self.service_pack = None
        self.install_helper = None
        self.windows_machine = None
        self.unix_machine = None
        self.authcode = None
        self.status = constants.PASSED
        self.result_string = ""

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.authcode = self.commcell.enable_auth_code()

    def install_client(self, q, bootstrapper_install=True):
        """
        Interactively Install the client
        Args:
            q                       --  queue with details of the client machine and its helper file

            bootstrapper_install    --  bool value to determine if it's a bootstrapper install

        Returns:

        """
        try:
            self.log.info("Launched Thread to install client")
            client_machine = q
            client_helper = InstallHelper(self.commcell, client_machine)
            if client_machine.check_registry_exists("Session", "nCVDPORT"):
                client_helper.uninstall_client()

            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.authcode
            }

            self.log.info("Determining Media Path for Installation")
            media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack")
            if "{sp_to_install}" in media_path:
                if self.tcinputs.get("ServicePack") is None:
                    _service_pack = self.commcell.commserv_version
                else:
                    if '_' in _service_pack:
                        _service_pack = _service_pack.split('_')[0]
            _service_pack = _service_pack.lower().split('sp')[1]
            _minus_value = self.config_json.Install.minus_value
            if len(_service_pack) == 4:
                _service_pack_to_install = int(str(_service_pack)[:2]) - _minus_value
            else:
                _service_pack_to_install = int(_service_pack) - _minus_value
            self.log.info(f"Service pack to Install {_service_pack_to_install}")
            if '_' not in _service_pack:
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            if not bootstrapper_install:
                silent_install_dict.update({"mediaPath": media_path})
            self.log.info(f"Media Path used for Installation: {media_path}")
            self.log.info(f"Installing client on {client_machine.machine_name}")
            client_helper.silent_install(
                client_name=client_machine.machine_name,
                tcinputs=silent_install_dict,
                feature_release=_service_pack_to_install)

            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(client_machine.machine_name):
                client_obj = self.commcell.clients.get(client_machine.machine_name)
                if client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(
                    f"Client: {client_machine.machine_name} failed registering to the CS, Please check client logs")

            media_path = None if bootstrapper_install else media_path
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(
                client_obj.client_hostname, self, machine_object=client_machine,
                media_path=media_path if media_path else None, feature_release=_service_pack_to_install)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def run(self):
        """Main function for test case execution"""
        try:
            t1 = Thread(target=self.install_client, args=(self.windows_machine, True))
            t2 = Thread(target=self.install_client, args=(self.unix_machine,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.log.info("all Threads Executed successfully")

            client_machines = [self.windows_machine, self.unix_machine]
            for machine_obj in client_machines:
                client_obj = self.commcell.clients.get(machine_obj.machine_name)
                machine_obj.stop_all_cv_services()

                self.log.info(f"Pushing upgrades to the client: {client_obj.client_name}")
                job = client_obj.push_servicepack_and_hotfix()
                if job.wait_for_completion():
                    self.log.info("Job marked as completed/Failed")

                job_status = job.delay_reason
                self.log.info("JobFailingReason:%s", job_status)

                if installer_messages.QUPDATE_UNREACHABLE_CLIENT_UPDATE not in job_status and \
                        installer_messages.QINSTALL_CONNECTION_ERROR not in job_status:
                    self.log.error("Job Failed due to some other reason than the expected one.")
                    raise Exception(job_status)

                machine_obj.start_all_cv_services()

                job = job.resubmit()
                if job.wait_for_completion():
                    install_validation = InstallValidator(client_obj.client_hostname, self,
                                                          machine_object=machine_obj, is_push_job=True)
                    install_validation.validate_install()
                    self.log.info("Packages successfully installed on client machine")
                else:
                    job_status = job.delay_reason
                    self.log.error("JobFailingReason:%s", job_status)
                    raise Exception("Failed to Install packages")

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.windows_machine.start_all_cv_services()
        self.unix_machine.start_all_cv_services()
