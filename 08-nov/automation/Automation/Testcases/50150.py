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

from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.update_helper import UpdateHelper
from Install import installer_utils
from cvpysdk.commcell import Commcell
from AutomationUtils import config, constants
from Install.installer_constants import DEFAULT_COMMSERV_USER


class TestCase(CVTestCase):
    """Class for executing Push Service pack upgrades to client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push Service Pack upgrades to clients"
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.unix_machine = None
        self.unix_helper = None
        self.update_helper = None
        self.config_json = None
        self.default_log_directory = None
        self.clientgrp = "SPUpgrade"
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
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]

        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.update_helper = UpdateHelper(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info(f"adding clients to the group {self.clientgrp}")
            if not self.commcell.client_groups.has_clientgroup(self.clientgrp):
                self.commcell.client_groups.add(
                    self.clientgrp, [self.commcell.clients.get(self.windows_machine.machine_name).client_name,
                                     self.commcell.clients.get(self.unix_machine.machine_name).client_name])
            else:
                _client_group_obj = self.commcell.client_groups.get(self.clientgrp)
                _client_group_obj.add_clients(
                    [self.commcell.clients.get(self.windows_machine.machine_name).client_name,
                     self.commcell.clients.get(self.unix_machine.machine_name).client_name], overwrite=True)

            # calls the push service pack and hotfixes job
            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computer_groups=[self.clientgrp], reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")

            self.log.info("Initiating Check Readiness from the CS")
            for each_client in [self.windows_machine.machine_name, self.unix_machine.machine_name]:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info("Check Readiness of Client is successful")
                else:
                    self.log.error("Client failed Registration to the CS")
                    raise Exception(
                        f"Client: {each_client} failed registering to the CS, Please check client logs")

                self.log.info("Starting Install Validation")
                install_validation = InstallValidator(each_client, self, is_push_job=True)
                install_validation.validate_install()

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            installer_utils.collect_logs_after_install(self, self.windows_machine)
            installer_utils.collect_logs_after_install(self, self.unix_machine)
