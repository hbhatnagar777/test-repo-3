# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

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
from Install import installer_utils, installer_constants
from Install.softwarecache_validation import DownloadValidation
from Install.bootstrapper_helper import BootstrapperHelper
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping


class TestCase(CVTestCase):
    """Download software using 3rd option giving specific SP- Service pack and Hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Download reduced media using linux bootstrapper"
        self.config_json = None
        self.os_to_download = None
        self.sw_cache_helper = None
        self.validation_helper = None
        self.latest_cu = None
        self.service_pack_to_install = None
        self.job_controller = None
        self.machine_obj = None
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
        self.os_to_download = []
        _sp_to_download = self.tcinputs.get('ServicePack') if self.tcinputs.get('ServicePack') else ''
        self.latest_cu = 'CU' + str(installer_utils.get_latest_cu_from_xml(
            installer_utils.get_latest_recut_from_xml(_sp_to_download)))
        self.machine_obj = Machine()
        self.service_pack_to_install = installer_utils.get_latest_recut_from_xml(_sp_to_download)
        self.log.info(f"Service Pack used for Installation: {_sp_to_download}")
        self.bootstrapper_obj = BootstrapperHelper(self.service_pack_to_install, self.machine_obj)
        self.bootstrapper_obj.extract_bootstrapper()
        self.download_inputs = {
            "download_type": "",
            "download_full_kit": True
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Starting Bootstrapper Download for Unix media")
            self.download_inputs['download_type'] = 'unix'
            self.os_to_download = [OSNameIDMapping.UNIX_LINUX86.value]
            self.download_inputs['binary_set_id'] = [installer_constants.BinarySetIDMapping.UNIX_LINUX86.value]
            media_path = self.bootstrapper_obj.download_payload_from_bootstrapper(download_inputs=self.download_inputs)
            if media_path:
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info("Starting download validation")
            self.validation_helper = DownloadValidation(
                commcell=self.commcell, os_to_download=self.os_to_download,
                media=self.service_pack_to_install, cu_pack=self.latest_cu, machine_obj=self.machine_obj)
            self.validation_helper.bootstrapper_download_validation(media_path)
            self.log.info("Download validation for bootstrapper download successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
