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
from AutomationUtils.machine import Machine
from Install import installer_constants, installer_messages, installer_utils
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase : Push updates when the cache status is invalid."""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push updates when the cache status is invalid."
        self.cs_machine = None
        self.sw_cache_helper = None
        self.config_json = None
        self.authcode = None
        self.install_helper = None
        self.windows_machine = None
        self.unix_machine = None
        self.result_string = ""
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.cs_machine = Machine(self.commcell.commserv_hostname, self.commcell)
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.authcode = self.commcell.enable_auth_code()
        self.sw_cache_helper = self.commcell.commserv_cache

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
                client_helper.uninstall_client(delete_client=False)

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

            flag = self.cs_machine.update_registry(
                key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
                value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"),
                data=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("data"),
                reg_type=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("reg_type"))
            if not flag:
                self.log.error("Failed to stop the automatic download process from push install ")
                raise Exception("Failed to create a Registry Key")

            # Deleting the present SoftwareCache
            try:
                self.sw_cache_helper.delete_cache()
                self.sw_cache_helper.commit_cache()
            except Exception:
                if self.cs_machine.check_directory_exists(
                        self.cs_machine.join_path(self.sw_cache_helper.get_cs_cache_path(), "CVMedia")):
                    raise Exception("Unable to delete SW cache")
            version_info = self.commcell.version.split(".")
            build_sp = version_info[0] + "." + version_info[1]
            trans_id = self.cs_machine.get_registry_value("UpdateBinTransactions", "SPTranID").split("_")[1]
            failed_reason = \
                installer_messages.QINSTALL_PKG_INFO_MISSING_AFTER_DOWNLOAD.replace("Build.SPversion", build_sp)
            failed_reason = failed_reason.replace("transId", trans_id)

            client_machines = [self.windows_machine, self.unix_machine]
            for machine_obj in client_machines:
                client_obj = self.commcell.clients.get(machine_obj.machine_name)
                job = client_obj.push_servicepack_and_hotfix()

                if job.wait_for_completion(10):
                    raise Exception("Packages successfully installed on the machine even when the cache is invalid")

                job_status = job.delay_reason

                if failed_reason not in job_status:
                    self.log.error("Job Failed due to some other reason than the expected one.")
                    raise Exception(job_status)

                self.log.info("JobFailingReason:%s", job_status)

            self.cs_machine.remove_registry(
                key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
                value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"))
            for machine_obj in client_machines:
                client_obj = self.commcell.clients.get(machine_obj.machine_name)
                job = client_obj.push_servicepack_and_hotfix()
                if job.wait_for_completion():
                    self.log.info("Packages successfully installed on the client")
                    self.log.info("Starting install validation")
                    install_validation = InstallValidator(
                        client_obj.client_hostname, self, machine_object=machine_obj,
                        cu_version=installer_utils.get_cu_from_cs_version(self.commcell), is_push_job=True)
                    install_validation.validate_install()
                else:
                    job_status = job.delay_reason
                    self.log.error(f"Failed to Push Install packages to the client: {client_obj.client_name}")
                    raise Exception(job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.cs_machine.remove_registry(
            key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
            value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"))
