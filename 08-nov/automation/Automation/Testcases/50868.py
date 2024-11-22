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
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.softwarecache_validation import DownloadValidation
from Install.softwarecache_helper import SoftwareCache
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions, OSNameIDMapping


class TestCase(CVTestCase):
    """Download software using 3rd option giving specific SP- Service pack and Hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download software using 3rd option giving specific SP- Service pack and Hotfixes"
        self.config_json = None
        self.os_to_download = None
        self.sw_cache_helper = None
        self.validation_helper = None
        self.latest_cu = None
        self.sp_to_download = None
        self.job_controller = None
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.job_controller = JobController(self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache
        self.os_to_download = [DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value]
        self.sp_to_download = self.tcinputs.get('ServicePack') if self.tcinputs.get('ServicePack') else ''
        self.latest_cu = installer_utils.get_latest_cu_from_xml(installer_utils.get_latest_recut_from_xml(
            self.sp_to_download))
        _software_cache_helper = SoftwareCache(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            self.log.info("Deleting the Software cache")
            try:
                self.sw_cache_helper.delete_cache()
                self.sw_cache_helper.commit_cache()
            except Exception:
                pass
            self.log.info("Starting Download Software Job")
            if self.sp_to_download == '':
                self.log.info("Downloading CS SP since SP to download is empty")
                self.sp_to_download = self.commcell.commserv_version
            self.log.info(f"SP to download : {self.sp_to_download}")
            self.log.info(f"CU to download : {self.latest_cu}")
            job_obj = self.commcell.download_software(options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                                                      os_list=self.os_to_download,
                                                      service_pack=self.sp_to_download, cu_number=self.latest_cu)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")
            self.log.info("Starting download validation")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id,
                                                        download_option=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                                                        os_to_download=[OSNameIDMapping.WINDOWS_64.value,
                                                                     OSNameIDMapping.UNIX_LINUX64.value],
                                                        service_pack=self.sp_to_download,
                                                        cu_pack=self.latest_cu)
            self.validation_helper.download_validation()
            self.log.info("Download validation for automation download successful")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
