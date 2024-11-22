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
from Install.softwarecache_helper import SoftwareCache
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

        # creating a client Group for clients and adding pseudo clients to it
        self.log.info("-----------creating a client Group for clients and adding clients to it------------")
        for each_client in data.push_new_client:
            if not self.commcell.clients.has_client(each_client.hostname):
                _client = self.commcell.clients.create_pseudo_client(each_client.clientname,
                                                                     each_client.hostname,
                                                                     each_client.ostype)
                if not _client:
                    self.log.error("Failed to create the pseudo client %s.", each_client.clientname)
                self.log.info("Pseudo Client %s is created successfully.",
                              (each_client.clientname))
            client_obj = self.commcell.clients.get(each_client.rc_clientname)
            software_cache_obj = SoftwareCache(self.commcell, client_obj)
            software_cache_obj.remote_cache_obj.assoc_entity_to_remote_cache(
                client_name=each_client.clientname)
            client_machine_object = self.options_selector.get_machine_object(machine=each_client.hostname,
                                                                             username=each_client.username,
                                                                             password=each_client.password)
            install_helper = InstallHelper(self.commcell, client_machine_object)

            for packages in each_client.packages_to_install.split(','):
                if client_machine_object.os_info == "WINDOWS":
                    features = [WindowsDownloadFeatures(int(packages)).name]
                else:
                    features = [UnixDownloadFeatures(int(packages)).name]

            # installing clients using RC as source
            job = install_helper.install_software(client_computers=[each_client.clientname],
                                                  features=features,
                                                  username=each_client.username,
                                                  password=each_client.password)

            failed_clients = []
            client_success = []
            if not job.wait_for_completion():
                failed_clients.append(each_client.clientname)
                self.log.info("%s Client installation Failed", each_client.clientname)
            else:
                client_success.append(each_client.clientname)
                self.log.info("%s Client installation Passed", each_client.clientname)

        for each_client in client_success:
            validate = InstallValidator(each_client, self)
            validate.validate_install()
