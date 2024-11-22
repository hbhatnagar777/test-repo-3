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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from Install import installer_messages
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase : Push install a client with the wrong credentials"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push install a client with the wrong credentials"
        self.machine_obj = None
        self.config_json = None
        self.rc_client = None
        self.result_string = ""
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.machine_obj = install_helper.get_machine_objects()

    def run(self):
        """Main function for test case execution"""
        try:
            for platform in self.machine_obj:
                install_helper = InstallHelper(self.commcell, platform)
                if platform.check_registry_exists("Session", "nCVDPORT"):
                    install_helper.uninstall_client(delete_client=True)
                if self.commcell.is_linux_commserv and 'windows' in platform.os_info.lower():
                    # Configuring Remote Cache Client to Push Software to Windows Client
                    self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                                  "Direct push Installation to Windows Client")
                    rc_client_name = self.config_json.Install.rc_client.client_name
                    if self.commcell.clients.has_client(rc_client_name):
                        self.rc_client = self.commcell.clients.get(rc_client_name)
                job_with_wrong_credentials = install_helper.install_software(
                    client_computers=[install_helper.client_host],
                    features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                    username='WrongDomainName\\WrongUsername',
                    password="WrongPassword",
                    sw_cache_client=self.rc_client.client_name if self.rc_client else None)

                if job_with_wrong_credentials.wait_for_completion(5):
                    raise Exception(f"{install_helper.client_host} "
                                    f"client is marked as installed even with wrong credentials")

                job_status = job_with_wrong_credentials.delay_reason
                self.log.info("JobFailingReason:%s", job_status)
                status = False
                for msgs in [installer_messages.QINSTALL_BASE_PACKAGE_FAILED_GENERIC_WRONG_CREDENTIALS.replace(
                        "CLIENT_NAME", platform.machine_name),
                    installer_messages.QINSTALL_ERROR_LOGON.replace("CS_NAME", self.commcell.commserv_name),
                    installer_messages.QINSTALL_FAILED_TO_DETERMINE_PROCESSOR,
                    installer_messages.QINSTALL_FAILED_TO_COMPUTE_BINARY_SET.replace(
                        "CLIENT_NAME", install_helper.client_host).replace("CS_NAME",
                                                                           self.commcell.commserv_name)]:
                    if all(i[0] == i[1] for i in zip(job_status, msgs) if not i[0].isdigit()):
                        self.log.info("JobFailingReason:%s", job_status)
                        status = True
                if not status:
                    self.log.error("Job Failed due to some other reason than the expected one.")
                    raise Exception(job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
