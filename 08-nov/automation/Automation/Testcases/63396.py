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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""
import time
from Install import installer_utils
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Service pack upgrade with roles manager enabled (Unix)"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Service pack upgrade with roles manager enabled Unix"
        self.install_helper = None
        self.unix_machine = None
        self.unix_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.silent_install_dict = {}
        self.tcinputs = {}
        self.default_log_directory = None
        self.commcell = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.machine_name = self.unix_machine.machine_name
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code(),
        }

    def get_service_pack_to_install(self, MinusValue=0):
        """Function to get service pack"""
        _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
            else "SP" + str(self.commcell.commserv_version)

        # Reducing the service pack value if required
        _service_pack_reduced = int(_service_pack[2:]) - int(MinusValue)
        _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_reduced)
        return _service_pack_to_install

    def run(self):
        """Run function of this test case"""
        try:
            # Deleting a client if it exists
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=False)

            # Determining the media path for the installation
            _service_pack_to_install=self.get_service_pack_to_install(int(self.tcinputs["MinusValue"]))
            self.log.info(f"Service Pack used for Installation: {_service_pack_to_install}")

            # Installing the client
            self.log.info(f"Installing fresh unix client on {self.machine_name}")
            self.unix_helper.silent_install(
                client_name=self.id,
                tcinputs=self.silent_install_dict,
                feature_release=_service_pack_to_install,
                packages=['FILE_SYSTEM'])

            self.client_obj = self.commcell.clients.get(self.config_json.Install.unix_client.machine_host)

            # Installing current SP with Roles Manager and additional role of MediaAgent
            self.silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code(),
                "launchRolesManager": "1",
                "selectedRoles": [1301, 1101],
                "instance": self.client_obj.instance if self.client_obj.instance else "Instance001"
            }

            # Selecting Media Path for Current SP
            _service_pack_to_install = self.get_service_pack_to_install()
            self.log.info(f"Service Pack used for Installation: {_service_pack_to_install}")

            # Upgrading service pack with roles manager selected
            self.log.info(f"Installing custom package unix client on {self.machine_name}")
            self.unix_helper.silent_install(
                client_name=self.id,
                tcinputs=self.silent_install_dict,
                feature_release=_service_pack_to_install,
                packages=['FILE_SYSTEM_CORE'])

            # Checking Job Status from CS
            time.sleep(10)
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Install Software':
                    job_obj = self.job_controller.get(jid)
                    if job_obj.client_name==self.id:
                        self.log.info("Job %s started for installing packages", job_obj.job_id)
                        try:
                            job_obj.wait_for_completion()
                        except Exception:
                            self.log.error("Install job Failed")
                        if not job_obj.wait_for_completion():
                            raise Exception("Failed to run Install job with error: " + job_obj.delay_reason)
            
            # Refreshing cs client list and check readiness
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception("Client: %s failed registering to the CS, Please check client logs"
                                % self.machine_name)

            # Validating Install
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.unix_machine,
                                                  package_list=[UnixDownloadFeatures.MEDIA_AGENT.value,
                                                                UnixDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=None)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.unix_machine)
        if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
            self.unix_helper.uninstall_client(delete_client=True)
