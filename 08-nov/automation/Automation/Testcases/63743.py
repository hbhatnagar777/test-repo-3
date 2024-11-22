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

from cvpysdk.deployment.deploymentconstants import DownloadPackages, UnixDownloadFeatures, WindowsDownloadFeatures
from cvpysdk.deployment.deploymentconstants import DownloadOptions
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.update_helper import UpdateHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install import installer_utils
from Install.softwarecache_helper import SoftwareCache
import time
from Install.install_validator import InstallValidator
from AutomationUtils import logger, config
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Download and Install service pack and hotfixes"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push SP Upgrade of Linux CS"
        self.install_helper = None
        self.update_helper = None
        self.tcinputs = {
            'ServicePack': None,
            'MediaPath': None
        }
        self.download_helper = None
        self.config_json = None
        self.cs_machine = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.log = logger.get_log()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(self.commcell)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)
        self.download_helper = SoftwareCache(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            # calls the Download job
            # self.download_helper.point_to_internal()
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            job = self.commcell.download_software(
                options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value],
                service_pack=self.tcinputs.get("ServicePack"),
                cu_number=latest_cu)
            self.log.info("Job %s started for downloading packages", job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run download job with error: " + job.delay_reason
                )

            if job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors please check the logs")

            self.log.info("Successfully finished Downloading packages")

            # calls the push service pack and hotfixes job for the CS
            self.update_helper.push_sp_upgrade(
                client_computers=[self.commcell.commserv_name]
            )

            self.log.info("Login to Commcell after CS Upgrade")
            time.sleep(600)
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)

            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")

            self.log.info("Starting Install Validation")
            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(_commserv_client.client_hostname, self,
                                                  machine_object=self.cs_machine, package_list=package_list,
                                                  feature_release=_sp_transaction, is_push_job=True)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
