# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from AutomationUtils.machine import Machine
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase
from Install import installer_utils
from Install.softwarecache_validation import DownloadValidation
from Install.bootstrapper_helper import BootstrapperHelper
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Download software using 3rd option giving specific SP- Service pack and Hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Appliance Media Download using Linux Bootstrapper"
        self.config_json = None
        self.validation_helper = None
        self.latest_cu = None
        self.machine_obj = None
        self.service_pack_to_install = None
        self.appliance_list = None
        self.bootstrapper_obj = None
        self.download_inputs = None
        self.status = None
        self.result_string = None
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        _sp_to_download = self.tcinputs.get('ServicePack') if self.tcinputs.get('ServicePack') else ''
        self.latest_cu = 'CU' + str(installer_utils.get_latest_cu_from_xml(
            installer_utils.get_latest_recut_from_xml(_sp_to_download)))
        self.machine_obj = Machine()
        self.service_pack_to_install = installer_utils.get_latest_recut_from_xml(_sp_to_download)
        self.log.info(f"Service Pack used for Installation: {_sp_to_download}")
        self.bootstrapper_obj = BootstrapperHelper(self.service_pack_to_install, self.machine_obj)
        self.bootstrapper_obj.extract_bootstrapper()
        self.download_inputs = {
            "download_type": ""
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Starting Bootstrapper Download for Unix Appliance media")
            self.log.warning("Support for silent Unix Appliance media download not added in installer!!!")
            self.log.info("Starting Bootstrapper Download for Windows Appliance media")
            self.appliance_list = 'WINDOWS_APPLIANCE'
            self.download_inputs['download_type'] = 'windows'
            self.download_inputs['packages'] = str(WindowsDownloadFeatures.FILE_SYSTEM.value)
            self.download_inputs['download_extra'] = [2, 3]
            media_path = self.bootstrapper_obj.download_payload_from_bootstrapper(download_inputs=self.download_inputs)
            if media_path:
                self.log.info("Download Job Successful")
            else:
                raise Exception("Download Job Failed")
            self.log.info("Starting Download Validation")
            appliance_media_path = media_path.replace('Windows', 'CVAppliance')
            self.validation_helper = DownloadValidation(
                commcell=self.commcell, media=self.service_pack_to_install, machine_obj=self.machine_obj)
            self.validation_helper.validate_cv_appliance_media(self.appliance_list, appliance_media_path)
            self.log.info("Download validation for Bootstrapper Download Successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
