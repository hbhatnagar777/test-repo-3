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

import time
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install.install_validator import InstallValidator
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.update_helper import UpdateHelper
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from Install import installer_utils


class TestCase(CVTestCase):
    """Testcase: Installing latest maintanence release on non root CS """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Installing latest maintanence release on non root CS"
        self.update_helper = None
        self.config_json = None
        self.cs_machine = None
        self.commcell = None
        self.tcinputs = {
            'ServicePack': None
        }

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
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)

    def run(self):
        """Main function for test case execution"""
        try:
            # Determing the media
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))

            # Updating to the latest maintenance release
            self.log.info("Downloading and Installing latest updates on CS")
            self.update_helper.push_maintenance_release(
                client_computers=[self.commcell.commserv_name], 
                download_software=True)
            
            #Creating the commcell object after updating
            self.log.info("Login to Commcell after CS Upgrade")
            time.sleep(600)
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
            
            # Performing check readiness
            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")
                raise Exception(f"Check readiness of {self.commcell.commserv_name} failed")

            # Validaitng the update
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(
                _commserv_client.client_hostname, 
                self,
                machine_object=self.cs_machine, 
                package_list=[UnixDownloadFeatures.COMMSERVE.value],
                feature_release=_sp_transaction, 
                is_push_job=True)
            install_validation.validate_install(
                **{"validate_nonroot_services": True,
                   "validate_nonroot_install": True})

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
