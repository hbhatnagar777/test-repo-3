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

from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.update_helper import UpdateHelper
from Install.softwarecache_helper import SoftwareCache
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions


class TestCase(CVTestCase):
    """Class for executing Download and push latest hotfixes on CS"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download and sync of latest hotfixes on CS and remote caches"
        self.install_helper = None
        self.update_helper = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.download_helper = None
        self.config_json = None
        self.cs_machine = None
        self.commcell = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
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
            # Downloading latest hotfixes on CS and syncing selected RC's
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            self.log.info(latest_cu)
            job_obj = self.commcell.download_software(
                options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value],
                service_pack=self.tcinputs.get("ServicePack"),
                sync_cache_list=[
                    self.config_json.Install.rc_automation.rc_machines.rc_windows_1.hostname,
                    self.config_json.Install.rc_automation.rc_machines.rc_unix_1.hostname,
                    self.config_json.Install.rc_automation.rc_machines.rc_unix_2.hostname],
                sync_cache=True,
                cu_number=latest_cu)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
