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
from base64 import b64encode
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from AutomationUtils import config
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Install.softwarecache_validation import RemoteCache
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for validating remote cache sync when install job is already running on the client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - Remote cache sync when install job is already running on the client"
        self.config_json = None
        self.unix_machine_obj = None
        self.software_cache_val_obj = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.unix_machine_obj = Machine(machine_name=self.config_json.Install.unix_client.machine_host,
                                        username=self.config_json.Install.unix_client.machine_username,
                                        password=self.config_json.Install.unix_client.machine_password)

    def run(self):
        """Main function for test case execution"""
        try:

            self.log.info("Restarting services of clients")
            self.unix_machine_obj.execute_command("commvault start")

            self.log.info("Pushing packages to unix client")
            install_job = self.commcell.install_software(
                client_computers=[self.config_json.Install.unix_client.machine_host],
                unix_features=[
                    UnixDownloadFeatures.ORACLE.value,
                    UnixDownloadFeatures.SQLSERVER.value
                ],
                username=self.config_json.Install.unix_client.machine_username,
                password=b64encode(self.config_json.Install.unix_client.machine_password.encode()).decode()
            )

            self.log.info("Start sync job while install is still running")
            job_obj = self.commcell.sync_remote_cache()
            if not job_obj.wait_for_completion():
                self.log.info("Download job failed. Details: %s", job_obj.delay_reason)
            else:
                raise Exception("Download job passed. Test case failed validating the negative case")

            windows_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)

            self.log.info("Validating cache for windows client to make sure sync completed successfully")
            self.software_cache_val_obj = RemoteCache(client_obj=windows_client_obj,
                                                      commcell=self.commcell)
            self.software_cache_val_obj.validate_remote_cache(configured_os_pkg_list=[],
                                                              sync_all=True)

        except Exception as exp:
            handle_testcase_exception(self, exp)
