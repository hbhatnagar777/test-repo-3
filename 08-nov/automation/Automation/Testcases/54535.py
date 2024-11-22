# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Install.update_helper import WindowsUpdateHelper
from Install.install_validator import WindowsValidator
from cvpysdk.clientgroup import ClientGroup


class TestCase(CVTestCase):
    """Validate CVAppliance OS patches"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate CVAppliance OS and MSSQL Patches"
        self.config_json = None
        self.windows_patching_group = None
        self.mssql_patching_group = None
        self.update_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.windows_patching_group = ClientGroup(self.commcell, "Windows updates patching clients")
        self.mssql_patching_group = ClientGroup(self.commcell, "MSSQL updates patching clients")
        self.update_helper = WindowsUpdateHelper(self.commcell, machine_obj=None)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info(self.windows_patching_group.associated_clients)
            self.log.info(f"Starting push upgrade job for client group: {self.windows_patching_group.name}")
            self.update_helper.push_sp_upgrade(client_computer_groups=[self.windows_patching_group.name])
            self.log.info(f"Starting push upgrade job for client group: {self.windows_patching_group.name}")
            self.update_helper.push_sp_upgrade(client_computer_groups=[self.mssql_patching_group.name])

            for client_name in self.windows_patching_group.associated_clients:
                client_obj = self.commcell.clients.get(client_name)
                client_hostname = client_obj.client_hostname
                package_list = []
                for data in client_obj.properties['client']['versionInfo']['PatchStatus']:
                    package_list.append(int(data['packageInfo']['packageId']))

                self.log.info(f"Validating Windows Updates installed on {client_hostname}")
                install_validator = WindowsValidator(machine_name=client_hostname, commcell_object=self.commcell,
                                                     package_list=package_list, is_push_job=True)
                install_validator.validate_install()
                install_validator.validate_installed_windows_kb_updates()

            for client_name in self.mssql_patching_group.associated_clients:
                client_obj = self.commcell.clients.get(client_name)
                client_hostname = client_obj.client_hostname
                package_list = [int(x) for x in client_obj.agents.all_agents.values()]

                self.log.info(f"Validating MSSQL Updates installed on {client_hostname}")
                install_validator = WindowsValidator(machine_name=client_hostname, commcell_object=self.commcell,
                                                     package_list=package_list, is_push_job=True)
                install_validator.validate_install()
                install_validator.validate_mssql_patches()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
