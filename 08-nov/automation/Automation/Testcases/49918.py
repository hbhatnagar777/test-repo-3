# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from Install.bootstrapper_helper import BootstrapperHelper
from Install.install_helper import InstallHelper
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install import installer_utils, installer_constants
from AutomationUtils.machine import Machine
from AutomationUtils import logger, config, constants
from Install.update_helper import UpdateHelper


class TestCase(CVTestCase):
    """Class for executing Download and Install service pack and hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Copy Software from Bootstrapper Downloaded Media"
        self.install_helper = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.config_json = None
        self.service_pack = None
        self.cs_machine = None
        self.bootstrapper_obj = None
        self.sw_cache_helper = None
        self.update_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine)

    def get_service_pack_to_install(self, minus_value=0):
        """
        This method determines the service pack and it's path for Installation
        Returns: None
        """
        self.log.info("Determining Media Path for Installation")
        media_path = self.config_json.Install.media_path
        _service_pack = self.tcinputs.get("ServicePack")
        if '_' in _service_pack:
            _service_pack = _service_pack.split('_')[0]
        _service_pack = _service_pack.lower().split('sp')[1]
        _service_pack = int(_service_pack) - int(minus_value)
        self.log.info(f"Service pack to Install {_service_pack}")
        _service_pack = installer_utils.get_latest_recut_from_xml(_service_pack)
        media_path = media_path.replace("{sp_to_install}", _service_pack)
        self.service_pack = _service_pack
        self.log.info(f"Media identified: {self.service_pack}")
        self.tcinputs.update({"mediaPath": media_path})

    def run(self):
        """Main function for test case execution"""
        try:

            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=self.config_json.Install.commserve_client.webserver_username,
                                     commcell_password=self.config_json.Install.commserve_client.cs_password)
            self.sw_cache_helper = self.commcell.commserv_cache
            self.update_helper = UpdateHelper(self.commcell)

            self.log.info("downloading Windows media using bootstrapper")
            self.get_service_pack_to_install()
            self.bootstrapper_obj = BootstrapperHelper(feature_release=self.service_pack,
                                                       machine_obj=self.cs_machine,
                                                       bootstrapper_download_os="Windows,Unix")
            self.log.info("Downloading Media using Bootstrapper")
            self.bootstrapper_obj.extract_bootstrapper()
            self.bootstrapper_obj.download_payload_from_bootstrapper()

            self.log.info("Performing a copysoftware using Bootstrapper downloaded media")
            self.log.info("Populating CS Cache from Booststrapper Downloaded Media")
            self.log.info("Starting Copy Software Job")
            _media_path = self.bootstrapper_obj.remote_drive + installer_constants.WINDOWS_BOOTSTRAPPER_DOWNLOADPATH
            job_obj = self.commcell.copy_software(_media_path)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Copy Software Job Successful")
            else:
                raise Exception("Copy Software job failed")
            self.log.info("Copy Software Job Successful")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.cs_machine)
