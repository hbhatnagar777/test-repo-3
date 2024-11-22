# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate CV Appliance Media download using BootStrapper and copy software functionality.

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
from Install.installer_constants import REMOTE_FILE_COPY_LOC, UNIX_REMOTE_FILE_COPY_LOC


class TestCase(CVTestCase):
    """Download software using 3rd option giving specific SP- Service pack and Hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Appliance Media Download using Windows Bootstrapper and Copy Software"
        self.config_json = None
        self.validation_helper = None
        self.latest_cu = None
        self.machine_obj = None
        self.service_pack_to_install = None
        self.appliance_list = None
        self.bootstrapper_obj = None
        self.download_inputs = None
        self.cs_machine = None
        self.tcinputs = {
                'ServicePack': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.cs_machine = Machine(self.commcell.commserv_name, self.commcell)
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
            self.log.info("Starting Bootstrapper Download for Windows Appliance media")
            self.appliance_list = 'WINDOWS_APPLIANCE'
            self.download_inputs['download_type'] = ['windowsospatches', 'mssqlpatches']
            media_path = self.bootstrapper_obj.download_payload_from_bootstrapper(download_inputs=self.download_inputs)
            if media_path:
                self.log.info("Bootstrapper Download Job Successful")
            else:
                raise Exception("Bootstrapper Download Job Failed")
            self.log.info("Starting Download Validation")
            self.validation_helper = DownloadValidation(
                commcell=self.commcell, media=self.service_pack_to_install, machine_obj=self.machine_obj)
            self.validation_helper.validate_cv_appliance_media_for_bootstrapper(self.appliance_list, media_path)
            self.log.info("Download validation for Bootstrapper Download Successful")

            self.log.info("Copying media from controller to CS")
            if 'windows' in self.cs_machine.os_info.lower():
                _remote_path = REMOTE_FILE_COPY_LOC
            else:
                _remote_path = UNIX_REMOTE_FILE_COPY_LOC
            _remote_path = self.cs_machine.join_path(_remote_path, 'ApplianceMedia')
            self.cs_machine.copy_from_local(media_path, _remote_path)

            self.log.info("Starting Copy Software Job")
            job_obj = self.commcell.copy_software(media_loc=_remote_path)

            if job_obj.wait_for_completion():
                self.log.info("Copy Software Job Successful")
            else:
                raise Exception("Copy Software job failed")

            self.log.info("Starting Validation of CV Appliance Media")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id, media=media_path)
            self.validation_helper.validate_cvappliance_media(validate_rc=True)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
