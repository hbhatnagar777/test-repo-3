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
from AutomationUtils import constants, config
from Install import installer_messages
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase : Push updates to existing client with not enough disk space"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - Push updates to existing client with not enough disk space"
        self.windows_machine = None
        self.machine_obj = None
        self.windows_install_helper = None
        self.config_json = None
        self.extra_files_path = 'C:\\Temp'

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.windows_machine = install_helper.get_machine_objects(1)[0]
        self.windows_install_helper = InstallHelper(self.commcell, self.windows_machine)

    def run(self):
        """Main function for test case execution"""
        try:
            _minus_value = self.config_json.Install.minus_value
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_install_helper.uninstall_client()
            if len(str(self.commcell.commserv_version)) == 4:
                sp_to_install = "SP" + str(int(str(self.commcell.commserv_version)[:2]) - 2)
            else:
                sp_to_install = "SP" + str(self.commcell.commserv_version - _minus_value)
            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code()
            }

            self.windows_install_helper.silent_install(client_name="windows_client",
                                                       tcinputs=silent_install_dict,
                                                       feature_release=sp_to_install)

            windows_client = self.commcell.clients.get(self.windows_machine.machine_name)
            path = windows_client.install_directory.split(":")[0]
            available_drive_space = self.windows_machine.get_storage_details()[path]['available']
            self.extra_files_path = path + ":\\Temp"
            if available_drive_space > 500:
                # Filling up the drive with random files to make the drive to have less disk space
                file_size = (available_drive_space*1000/50)-1000
                flag = self.windows_machine.generate_test_data(file_path=self.extra_files_path, file_size=int(file_size),
                                                               dirs=5, files=10)
                if not flag:
                    raise Exception("Failed to fill up space")

            self.log.info("Sending updates to Windows Client")
            job_install = windows_client.push_servicepack_and_hotfix()
            if job_install.wait_for_completion(10):
                if self.windows_machine.check_directory_exists(self.extra_files_path):
                    self.windows_machine.remove_directory(self.extra_files_path)
                self.log.error("Installation Successful! Please provide a low space directory")
                raise Exception("Client Updates was Successful due to sufficient disk space")

            if self.windows_machine.check_directory_exists(self.extra_files_path):
                self.windows_machine.remove_directory(self.extra_files_path)

            job_status = job_install.delay_reason
            if not (installer_messages.QUPDATE_LOW_CACHE_SPACE in job_status):
                self.log.error("Job Failed due to some other reason than the expected one.")
                raise Exception(job_status)

            self.log.info("JobFailingReason:%s", job_status)
            job_install = job_install.resubmit()
            if job_install.wait_for_completion(5):
                install_validation = InstallValidator(windows_client.client_hostname, self,
                                                      machine_object=self.windows_machine,
                                                      is_push_job=True)
                install_validation.validate_install()
                self.log.info("Packages successfully installed on client machine")
            else:
                job_status = job_install.delay_reason
                self.log.error("Failed to Push Updates to the client:%s" % windows_client.client_name)
                raise Exception("JobFailingReason:%s", job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        if self.windows_machine.check_directory_exists(self.extra_files_path):
            self.windows_machine.remove_directory(self.extra_files_path)
