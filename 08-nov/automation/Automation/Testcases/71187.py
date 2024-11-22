# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
from Install.softwarecache_helper import SoftwareCache
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Class for verifying the Retire Client Option when data is associated with the client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Retire Client - Retire client when client is offline."
        self.config_json = None
        self.commcell = None
        self.client = None
        self.windows_machine = None
        self.install_helper = None
        self.rc_client = None
        self.result_string = ""
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.windows_machine = install_helper.get_machine_objects(1)[0]

    def run(self):
        """Main function for test case execution"""
        self.install_helper = InstallHelper(self.commcell, self.windows_machine)

        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.install_helper.uninstall_client(delete_client=True)

        self.log.info(f"Creating {self.windows_machine.os_info} client")
        if self.commcell.is_linux_commserv:
            # Configuring Remote Cache Client to Push Software to Windows Client
            self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                          "Direct push Installation to Windows Client")
            rc_client_name = self.config_json.Install.rc_client.client_name
            if self.commcell.clients.has_client(rc_client_name):
                self.rc_client = self.commcell.clients.get(rc_client_name)
        job = self.install_helper.install_software(
            features=['FILE_SYSTEM', 'MEDIA_AGENT'],
            sw_cache_client=self.rc_client.client_name if self.rc_client else None)
        if not job.wait_for_completion():
            raise Exception(f"{self.windows_machine.os_info} Client installation Failed")
        self.commcell.clients.refresh()

        install_validation = InstallValidator(
            self.windows_machine.machine_name, self, machine_object=self.windows_machine,
            package_list=[WindowsDownloadFeatures.MEDIA_AGENT.value], is_push_job=True)
        install_validation.validate_install()

        try:
            self.client = self.commcell.clients.get(self.config_json.Install.windows_client.machine_host)
            software_cache_obj = SoftwareCache(self.commcell, self.client)

            entities = ScheduleCreationHelper(self.commcell)
            entity_properties = entities.entities_setup(client_name=self.client.client_name)

            # Associate data with client.
            self.log.info("Associating back up data with the given client.")
            subclient_object = entity_properties['subclient']['object']
            Idautils = CommonUtils(self)
            Idautils.subclient_backup(subclient_object)

            self.client.stop_service()

            # Perform the Retire client Operation and wait for the job to complete.
            self.log.info("Will perform Retire operation now on client %s.", self.client.client_name)
            job = self.client.retire()
            if not job.wait_for_completion():
                raise Exception(f"Uninstall job failed with error: {job.delay_reason}")

            # Refreshing the clients associated with the commcell Object
            self.commcell.clients.refresh()

            self.log.info("validating client deconfiguration")
            query = f"select specialClientFlags from APP_Client where name like '{self.client.client_name}'"
            self.csdb.execute(query)
            self.log.info("Checking if specialClientFlags is updated")
            value = int(self.csdb.fetch_one_row()[0])
            if value != 2:
                raise Exception("specialClientFlags was not updated")

            self.log.info("Check if packages are removed from DB table")
            try:
                software_cache_obj.get_packages(client_id=self.client.client_id)
                raise Exception("Packages are not removed from SimInstalledPackages table."
                                "Client Retire failed. Please check logs")
            except Exception:
                self.log.info("No rows found in the table for this client."
                              "Packages are removed successfully from SimInstalledPackages table")

            self.log.info("Test case to retire a client when client is offline")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.install_helper.uninstall_client(self.windows_machine.machine_name)
            install_validation.validate_uninstall()


