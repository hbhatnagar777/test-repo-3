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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, constants
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.softwarecache_helper import SoftwareCache


class TestCase(CVTestCase):
    """Push repair to unix client when CVD is down"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push repair to unix client when CVD is down"
        self.config_json = None
        self.software_cache_obj = None
        self.machine_objects = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()

    def run(self):
        """Main function for test case execution"""
        try:
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if not self.commcell.clients.has_client(install_helper.client_host):
                    self.log.info("Creating {0} client".format(machine.os_info))
                    job = install_helper.install_software()
                    if not job.wait_for_completion():
                        raise Exception("{0} Client installation Failed".format(machine.os_info))

            self.commcell.clients.refresh()

            self.log.info("Push Repair to a unix client when CVD is down")
            unix_client = self.commcell.clients.get(
                self.config_json.Install.unix_client.machine_host)
            if unix_client.is_ready:
                unix_client.stop_service("GxCVD(Instance001)")

            install_helper = InstallHelper(self.commcell, unix_client)
            creds = install_helper.get_machine_creds
            job = unix_client.repair_software(
                username=creds[0],
                password=b64encode(creds[1].encode()).decode(),
                reboot_client=True
            )
            if not job.wait_for_completion():
                job_status = job.delay_reason
                self.log.error("Repair Job Failed")
                raise Exception(job_status)

            if unix_client.is_ready:
                install_validation = InstallValidator(unix_client.client_hostname, self)
                install_validation.validate_baseline()
                install_validation.validate_services()
                install_validation.validate_sp_version()
                self.log.info("Successfully repaired the client")
            else:
                raise Exception("Repair Failed. Please check logs")

            self.log.info("Push repair to a unix client via RC when CVD is down")
            self.log.info("Configuring windows client as Remote cache")
            rc_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)
            self.software_cache_obj = SoftwareCache(self.commcell, rc_client_obj)
            self.software_cache_obj.configure_remotecache()
            self.software_cache_obj.configure_packages_to_sync()
            self.log.info("Associating unix client to windows RC")
            self.commcell.assoc_entity_to_remote_cache(remote_cache_client_name=rc_client_obj.client_name,
                                                       client_name=unix_client.client_name)
            if unix_client.is_ready:
                unix_client.stop_service("GxCVD(Instance001)")

            creds = install_helper.get_machine_creds
            job = unix_client.repair_software(
                username=creds[0],
                password=b64encode(creds[1].encode()).decode(),
                reboot_client=True
            )
            if not job.wait_for_completion():
                job_status = job.delay_reason
                self.log.error("Repair Job Failed")
                raise Exception(job_status)

            if unix_client.is_ready:
                install_validation = InstallValidator(unix_client.client_hostname, self)
                install_validation.validate_baseline()
                install_validation.validate_services()
                install_validation.validate_sp_version()
                self.log.info("Successfully repaired the client")
            else:
                raise Exception("Repair Failed. Please check the logs")

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if self.commcell.clients.has_client(install_helper.client_host):
                    install_helper.uninstall_client(self.commcell.clients.get(install_helper.client_host))
