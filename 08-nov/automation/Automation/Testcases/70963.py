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
import random
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Smart Defaults Validation for Fresh Installation of Windows Client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.client_name = None
        self.subclient_obj = None
        self._service_pack_to_install = None
        self.name = "Smart Defaults Validation for Fresh Installation of Windows Client"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.media_path = None
        self.client_obj = None
        self.update_acceptance = False
        self.silent_install_dict = {}

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code()
        }
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def validate_smart_defaults(self):

        self.client = self.commcell.clients.get(self.machine_name)
        self.client_name = self.client.display_name
        agent_obj = self.client.agents.get('file system')
        agent_obj.backupsets.refresh()
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")
        backupset_obj.subclients.refresh()
        self.subclient_obj = backupset_obj.subclients.get("default")

        self.commcell.plans.refresh()

        self.log.info("Checking the subclient properties")
        self.subclient_obj.refresh()

        subclient_props = self.subclient_obj.properties

        if subclient_props["fsSubClientProp"]["followMountPointsMode"] == 1:
            self.log.info("Follow mount points is enabled")
        else:
            raise Exception("Follow mount points is not enabled")

        if subclient_props["fsSubClientProp"]["useGlobalFilters"] == 2:
            self.log.info("Use Cell level Policy is turned on by default")
        else:
            raise Exception("Use Cell level Policy is not turned on by default")

        if subclient_props["fsSubClientProp"]["isTrueUpOptionEnabledForFS"]:
            self.log.info("TrueUp Option is enabled")
        else:
            raise Exception("TrueUp is not enabled")

        if subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"] == 30:
            self.log.info("TrueUp days is set to 30")
        else:
            raise Exception(
                f'TrueUp days is set to {subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"]} \
                this should be 30 by default')

        if subclient_props["commonProperties"]["numberOfBackupStreams"] == 0:
            self.log.info("Optimal data readers are set")
        else:
            raise Exception("Optimal Data Readers are not set")

        if subclient_props["commonProperties"]["allowMultipleDataReaders"]:
            self.log.info("Allow multiple readers is set to True")
        else:
            raise Exception("Multiple data readers are not set")

        if subclient_props["commonProperties"]["storageDevice"]["applicableReadSize"] == 512:
            self.log.info("Application read size is on by default")
        else:
            raise Exception("Application read size not on by default ")

        if subclient_props["content"][0]["path"] == "\\":
            self.log.info("By default All content is given")
        else:
            raise Exception("By default All content is not given")

        if subclient_props["fsSubClientProp"]["backupSystemState"]:
            self.log.info("Backup SystemState is ON by default")
        else:
            raise Exception("Backup SystemState is not ON by default")

        # OS related sub client properties
        if subclient_props["fsSubClientProp"]["scanOption"] == 2:
            self.log.info("Scan Option is set to Optimized for Windows")
        else:
            raise Exception("Scan Option is not set to Optimized for Windows")

        if subclient_props["fsSubClientProp"]["useVSS"]:
            self.log.info("VSS is enabled")
        else:
            raise Exception("VSS is not enabled by default")

        self.log.info("Successfully verified the subclient properties")

    def run(self):
        """Run function of this test case"""
        try:
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)

            self.log.info("Determining Media Path for Installation")
            self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
            self._service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            if "{sp_to_install}" in self.media_path:
                self.media_path = self.media_path.replace("{sp_to_install}", self._service_pack_to_install)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            if self.media_path:
                self.silent_install_dict["mediaPath"] = self.media_path
                self.log.info(f"Media Path used for Installation: {self.media_path}")

            self.log.info(f"Installing fresh windows client on {self.machine_name}")
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()
            self.windows_helper.silent_install(
                client_name=self.id.replace(" ", "_") + "_" + str(random.randint(1000, 9999)),
                tcinputs=self.silent_install_dict, feature_release=_service_pack, packages=['FILE_SYSTEM'])

            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, Please check client logs")

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=self.media_path if self.media_path else None)
            install_validation.validate_install()
            if self.update_acceptance:
                self.install_helper.install_acceptance_update('Pass', '-', self.windows_machine.machine_name)

            self.validate_smart_defaults()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.windows_machine.machine_name,
                    self._service_pack_to_install.split('_R')[-1])

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.windows_machine)
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)
