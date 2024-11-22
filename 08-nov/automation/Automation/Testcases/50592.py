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

"""
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Install.install_helper import InstallHelper
from Install.softwarecache_validation import DownloadValidation
from Install.install_validator import InstallValidator


class TestCase(CVTestCase):
    """Class for validating remote cache sync """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating remote cache sync"
        self.commcell = None
        self.options_selector = None
        self.download_val = None
        self.config_json = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.download_val = DownloadValidation(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self.config_json = config.get_config()

    def run(self):
        """Main function for test case execution"""
        data = self.config_json.Install.client_data

        failed_clients = []
        client_success = []
        additional_packages = []
        for each_client in data.client:
            if 'additional_packages' in each_client._fields:
                additional_packages.append(each_client)
        for each_rc in data.remote_cache_list:
            if 'additional_packages' in each_rc._fields:
                additional_packages.append(each_rc)

        for each_client in additional_packages:
            if self.commcell.clients.has_client(each_client.hostname):
                client_machine_object = self.options_selector.get_machine_object(machine=each_client.hostname,
                                                                                 username=each_client.username,
                                                                                 password=each_client.password)
                install_helper = InstallHelper(self.commcell, client_machine_object)
                self.log.info("Installing client to be associated to RC client %s", each_client.clientname)

                if client_machine_object.os_info == "WINDOWS":
                    features = [WindowsDownloadFeatures(int(each_client.additional_packages)).name]
                else:
                    features = [UnixDownloadFeatures(int(each_client.additional_packages)).name]

                # installing additional packages using RC
                job = install_helper.install_software(client_computers=[each_client.clientname],
                                                      username=each_client.username,
                                                      password=each_client.password,
                                                      features=features)

                if not job.wait_for_completion():
                    failed_clients.append(each_client.clientname)
                    self.log.info("%s Client installation Failed", each_client.clientname)
                else:
                    client_success.append(each_client.clientname)
                    self.log.info("%s Client installation Passed", each_client.clientname)

        for each_client in client_success:
            validate = InstallValidator(each_client, self)
            validate.validate_install()
