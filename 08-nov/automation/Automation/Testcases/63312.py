# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""
import datetime
import time
import re
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.organizationhelper import OrganizationHelper
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.installer_constants import DEFAULT_LOG_DIRECTORY_UNIX
from Install.installer_constants import UNIX_REMOTE_FILE_COPY_LOC
from cvpysdk.commcell import Commcell
from Install import installer_constants
from exchangelib import Configuration, OAuth2Credentials, OAUTH2, Identity, Build, Version


class TestCase(CVTestCase):
    """Testcase : Fresh Installation of Unix Client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Unix client installation with two factor authentication enabled on CS"
        self.company = None
        self.email = None
        self.c_name = None
        self.user_name = None
        self.user_password = None
        self.user_email = None
        self.organization_helper = None
        self.config_json = None
        self.organization_id = None
        self.install_helper = None
        self.unix_machine = None
        self.unix_helper = None
        self.client_hostname = None
        self.client_name = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.silent_install_dict = {}
        self.tcinputs = {}
        self.commcell = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.company = self.config_json.Install.mastercs.tenants.tfa.company_name
        self.user_password = self.config_json.Install.mastercs.tenants.tfa.user_password
        self.user_email = self.config_json.Install.mastercs.tenants.tfa.user_email
        self.organization_helper = OrganizationHelper(self.commcell)
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.client_hostname = self.config_json.Install.unix_client.machine_host
        self.client_name = self.config_json.Install.unix_client.client_name
        self.install_helper = InstallHelper(self.commcell)
        self.unix_machine = self.install_helper.get_machine_objects(type_of_machines=2)[0]
        self.machine_name = self.unix_machine.machine_name
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.silent_install_dict = {
            "csClientName": "",
            "csHostname": "",
            "authCode": None,
            "decoupledInstall": "1"
        }

    def run(self):
        """Run function of this test case"""
        try:
            # enabling two-factor authentication at company level
            self.organization_helper = OrganizationHelper(self.commcell, self.company)
            self.organization_id = self.organization_helper.company_id
            self.organization_helper.enable_tfa(self.commcell, self.organization_id)

            # installing client in decoupled mode
            # Deleting the client if it already exists
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                self.unix_helper.uninstall_client(delete_client=True)

            self.log.info("Determining Media Path for Installation")
            media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            if "{sp_to_install}" in media_path:
                _service_pack = _service_pack.split('_')[0] if '_' in _service_pack \
                    else _service_pack
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            self.log.info(f"Media Path used for Installation: {media_path}")
            if media_path:
                self.silent_install_dict.update({"mediaPath": media_path})

            self.log.info(f"Installing fresh unix client on {self.machine_name}")
            self.unix_helper.silent_install(
                client_name=self.client_name,
                tcinputs=self.silent_install_dict, packages=['FILE_SYSTEM'])

            # Registering client with commcell
            self.log.info(f"Starting registration of client on {self.commcell.webconsole_hostname}")
            install_directory = installer_constants.DEFAULT_INSTALL_DIRECTORY_UNIX
            sim_path = self.unix_machine.join_path(install_directory, 'Base', 'SIMCallWrapper')
            # Command to execute simcallwrapper
            sim_command = "-OpType 1000 -CSHost {0} -clientname {1} -clientHostname {2} " \
                          "-user {3} -password {4} -output /tmp/output.xml -restartServices".format(
                            self.commcell.webconsole_hostname, self.client_name, self.client_hostname,
                            self.user_email, self.user_password)
            self.log.info(f"Registering the client on {self.commcell.webconsole_hostname} "
                          f"without pin")
            command = f"'{sim_path}' {sim_command}"
            # Fetching the timestamp when the mail was sent
            present_date = datetime.datetime.now()
            sent_time = int(datetime.datetime.timestamp(present_date))
            self.unix_machine.execute_command(command)
            output_path = "/tmp/output.xml"
            file_output = self.unix_machine.read_file(output_path)
            output_message = re.findall('<(.*)SimError (.*?)/>', file_output)
            error = str(output_message).split(',')
            self.log.info(f"Registration failed with error {error[1]}")
            self.log.info("Waiting for the code to come into the mailbox")
            time.sleep(60)

            # Fetching the pin from mail
            credentials = OAuth2Credentials(
                client_id=self.config_json.Install.tfa_details.client_id,
                client_secret=self.config_json.Install.tfa_details.client_secret,
                tenant_id=self.config_json.Install.tfa_details.tenant_id,
                identity=Identity(primary_smtp_address=self.config_json.Install.tfa_details.primary_smtp_address))
            configuration = Configuration(credentials=credentials,
                                          auth_type=OAUTH2,
                                          version=Version(Build(15, 1, 2, 3)),
                                          service_endpoint='https://outlook.office365.com/EWS/exchange.asmx')
            pin = self.organization_helper.get_tfa_pin(configuration,
                                                       self.config_json.Install.tfa_details.primary_smtp_address,
                                                       sent_time)

            if pin:
                # Adding the pin to password and executing the simcallwrapper command again
                new_password = str(self.user_password) + str(pin)
                sim_command = "-OpType 1000 -CSHost {0} -clientname {1} -clientHostname " \
                              "{2} -user {3} -password {4} -output /tmp/output.xml " \
                              "-restartServices".format(self.commcell.webconsole_hostname,
                                                        self.client_name, self.client_hostname,
                                                        self.user_email, new_password)
                command = f"'{sim_path}' {sim_command}"
                self.log.info(f"Registering the client on {self.commcell.webconsole_hostname}"
                              f" with pin")
                self.unix_machine.execute_command(command)
                time.sleep(120)
                if self.commcell.clients.has_client(self.client_name):
                    self.log.info(f"Successfully registered client {self.client_name} on "
                                  f"{self.commcell.webconsole_hostname}")
                else:
                    self.log.error("Client failed Registration to the CS")
                    raise Exception(
                        f"Client: {self.client_name} failed registering to the CS, "
                        f"Please check client logs")
            else:
                raise Exception(f"Mail not found in {self.user_email}")

            self.log.info("Starting Two Factor Authentication Validation")
            self.log.info(f"Validating if two factor authentication is enabled on "
                          f"{self.company} in {self.commcell.webconsole_hostname}")
            tfa_validation = OrganizationHelper(self.commcell, self.company)
            status = tfa_validation.get_tfa_status(self.commcell, self.organization_id)
            if status:
                self.log.info("Two factor Authentication validation successful")
            else:
                raise Exception("Two factor authentication in not enabled")
            if not status:
                raise Exception("Two factor authentication in not enabled")
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(
                self.client_hostname,
                self,
                machine_object=self.unix_machine,
                package_list=[UnixDownloadFeatures.FILE_SYSTEM.value],
                media_path=media_path if media_path else None)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            try:
                if self.unix_machine.check_directory_exists(DEFAULT_LOG_DIRECTORY_UNIX):
                    self.unix_machine.copy_folder(DEFAULT_LOG_DIRECTORY_UNIX, UNIX_REMOTE_FILE_COPY_LOC)
                    self.unix_machine.rename_file_or_folder(
                        self.unix_machine.join_path(UNIX_REMOTE_FILE_COPY_LOC, "Log_Files"),
                        self.id + self.unix_machine.get_system_time())
            except Exception as exp:
                self.log.info("Unable to copy the logs", exp)

        # Deleting the client
        if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
            self.unix_helper.uninstall_client(delete_client=True)
