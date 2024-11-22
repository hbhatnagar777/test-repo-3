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
    __init__()             --  Initialize TestCase class

    setup()         --  setup function of this test case

    run()                  --  run function of this test case

"""

"""
Provide necessary details on config.json

"Install" : {
....
"download_server": ""
....

"commserve_client": {
            "client_name": "",
            "machine_host": "",
            "machine_username": "",
            "machine_password": "",
            "sp_version": ""
        },

"unix_client": {
            "client_name": "",
            "machine_host": "",
            "machine_username": "",
            "machine_password": ""
        },

}
"""

import random
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from AutomationUtils import constants, config
from Install import installer_utils
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from Install.installer_constants import DEFAULT_COMMSERV_USER
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures


class TestCase(CVTestCase):
    """Class for executing
        Push Install FS Client without Storage Plan Configuration
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Push Install Unix FS Client without Storage Plan Configuration"
        self.unix_machine = None
        self.unix_hostname = None
        self.rc_client = None
        self.ClientName = None
        self.config_json = None
        self.unix_helper = None
        self.client_obj = None
        self.update_acceptance = False
        self.media_path = None
        self.install_helper = None
        self.fshelper = None

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.unix_hostname = self.unix_machine.machine_name
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def validate_smart_defaults(self):

        self.client = self.commcell.clients.get(self.unix_hostname)
        self.client_name = self.client.display_name

        agent_obj = self.client.agents.get('file system')
        agent_obj.backupsets.refresh()
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")
        backupset_obj.subclients.refresh()
        self.subclient_obj = backupset_obj.subclients.get("default")

        self.commcell.plans.refresh()


        self.log.info("Checking the subclient properties")
        self.subclient_obj.refresh()

        # Using local var to reduce mutliple requests
        subclient_props = self.subclient_obj.properties

        if subclient_props["fsSubClientProp"]["followMountPointsMode"] == 1:
            self.log.info("Follow mount points is enabled")
        else:
            raise Exception("Follow mount points is not enabled")

        if subclient_props["fsSubClientProp"]["useGlobalFilters"] == 2:
            self.log.info("Use Cell level Policy is turned on by default")
        else:
            raise Exception("Use Cell level Policy is not turned on by default")

        if subclient_props["fsSubClientProp"]["isTrueUpOptionEnabledForFS"]:
            self.log.info("TrueUp Option is enabled")
        else:
            raise Exception("TrueUp is not enabled")

        if subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"] == 30:
            self.log.info("TrueUp days is set to 30")
        else:
            raise Exception(
                f'TrueUp days is set to {subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"]} \
                this should be 30 by default')

        if subclient_props["commonProperties"]["numberOfBackupStreams"] == 0:
            self.log.info("Optimal data readers are set")
        else:
            raise Exception("Optimal Data Readers are not set")

        if subclient_props["commonProperties"]["allowMultipleDataReaders"]:
            self.log.info("Allow multiple readers is set to True")
        else:
            raise Exception("Multiple data readers are not set")

        if subclient_props["commonProperties"]["storageDevice"]["applicableReadSize"] == 512:
            self.log.info("Application read size on by default")
        else:
            raise Exception("Application read size not on by default ")

        # OS related subclient properties

        if "windows" in self.client.os_info.lower():

            if subclient_props["fsSubClientProp"]["scanOption"] == 2:
                self.log.info("Scan Option is set to Optimized for Windows")
            else:
                raise Exception("Scan Option is not set to Optimized for Windows")

            if subclient_props["fsSubClientProp"]["useVSS"]:
                self.log.info("VSS is enabled")
            else:
                raise Exception("VSS is not enabled by default")
        else:

            # idaType = 3

            if subclient_props["fsSubClientProp"]["scanOption"] == 1:
                self.log.info("Scan Option is set to Recursive for Unix")
            else:
                raise Exception("Scan Option is not Recusive for Unix")

            if subclient_props["fsSubClientProp"]["unixMtime"]:
                self.log.info("Unix Mtime is set")
            else:
                raise Exception("Unix Mtime is not set")

            if subclient_props["fsSubClientProp"]["unixCtime"]:
                self.log.info("Unix Ctime is set")
            else:
                raise Exception("Unix Ctime is not set")

            # Backup content check
            print(subclient_props["content"][0]["path"])
            if subclient_props["content"][0]["path"] == "/":
                self.log.info("By default All content is given")
            else:
                raise Exception("By default not All content is given")

        self.log.info("Successfully verfied the subclient properties")

    def run(self):
        """Main function for test case execution"""

        try:

            # Get Install Helper Object to Push Software
            self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()

            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=True)

            # Pushing Packages from CS to the client
            self.log.info(f"Starting a Push Install Job on the Machine: {self.unix_hostname}")
            push_job = self.unix_helper.install_software(
                client_computers=[self.unix_hostname],
                features=['FILE_SYSTEM'],
                username=self.config_json.Install.unix_client.machine_username,
                password=self.config_json.Install.unix_client.machine_password
            )

            self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
            if push_job.wait_for_completion():
                self.log.info("Push Upgrade Job Completed successfully")

            else:
                job_status = push_job.delay_reason
                self.log.error(f"Job failed with an error: {job_status}")
                raise Exception(job_status)

            # Refreshing the Client list to see the New Client Visible on GUI
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            # Check if the services are up on Client and is Reachable from CS
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.unix_hostname):
                self.client_obj = self.commcell.clients.get(self.unix_hostname)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of CS successful")
                    self.client_obj.display_name = self.name.replace(" ", "_") + "_" + str(
                        random.randint(1000, 9999))
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(
                    f"Client: {self.unix_hostname} failed registering to the CS, Please check client logs")

            # Install Validation to check if the Client Installation went fine
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.unix_hostname, self, machine_object=self.unix_machine,
                                                  package_list=[UnixDownloadFeatures.FILE_SYSTEM.value],
                                                  is_push_job=True)
            install_validation.validate_install()
            if self.update_acceptance:
                self.install_helper.install_acceptance_update('Pass', '-', self.unix_machine.machine_name)

            self.validate_smart_defaults()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                _service_pack = installer_utils.get_latest_recut_from_xml("SP" + str(self.commcell.commserv_version))
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.unix_machine.machine_name,
                    _service_pack.split('_R')[-1])

    def tear_down(self):

        """Tear down function of this test case"""

        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.unix_machine)
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=False)