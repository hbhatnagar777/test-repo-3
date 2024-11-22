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
import time
import datetime
import random
import re
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.organizationhelper import OrganizationHelper
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils, installer_constants
from Install.installer_constants import DEFAULT_COMMSERV_USER, \
    DEFAULT_LOG_DIRECTORY_WINDOWS, REMOTE_FILE_COPY_LOC
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from exchangelib import Configuration, OAuth2Credentials, OAUTH2, Identity, Build, Version


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Windows client installation with two factor " \
                    "authentication enabled on CS [SIMCALLWRAPPER]"
        self.company = None
        self.user_password = None
        self.user_email = None
        self.organization_helper = None
        self.config_json = None
        self.organization_id = None
        self.client_name = None
        self.client_hostname = None
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.config_json = None
        self.machine_name = None
        self.client_obj = None
        self.silent_install_dict = {}
        self.tcinputs = {}

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
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.client_hostname = self.config_json.Install.windows_client.machine_host
        self.client_name = self.config_json.Install.windows_client.client_name
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
            # deleting client if it already exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)
            self.log.info(f"Starting Installation of client on {self.client_hostname}")
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
            self.log.info(f"Installing fresh windows client on {self.machine_name}")
            client_name = self.client_name.replace(" ", "_") + "_" + str(random.randint(1000, 9999))
            self.windows_helper.silent_install(client_name=client_name,
                                               tcinputs=self.silent_install_dict,
                                               feature_release=_service_pack,
                                               packages=['FILE_SYSTEM'])

            # Registering client with commcell
            self.log.info(f"Starting registration of client [{self.client_name}] "
                          f"on {self.commcell.webconsole_hostname}"
                          )
            install_directory = installer_constants.DEFAULT_INSTALL_DIRECTORY_WINDOWS
            sim_path = self.windows_machine.join_path(install_directory, 'Base',
                                                      'SIMCallWrapper.exe')
            # Command to execute simcallwrapper
            sim_command = "-OpType 1000 -CSHost {0} -clientname {1} -user {2} -password {3} " \
                          "-output C:\\output.xml".format(self.commcell.webconsole_hostname,
                                                         self.client_name, self.user_email,
                                                         self.user_password)
            self.log.info(f"Registering the client [{self.client_name}] on "
                          f"{self.commcell.webconsole_hostname} "
                          f"without pin")
            command = f"cmd.exe /c '{sim_path}' {sim_command}"
            # Fetching the timestamp when the mail was sent
            present_date = datetime.datetime.now()
            sent_time = int(datetime.datetime.timestamp(present_date))
            self.windows_machine.execute_command(command)
            output_path = "C:\\output.xml"
            file_output = self.windows_machine.read_file(output_path)
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
                identity=Identity(
                    primary_smtp_address=self.config_json.Install.tfa_details.primary_smtp_address))
            configuration = Configuration(credentials=credentials, auth_type=OAUTH2,
                                          version=Version(Build(15, 1, 2, 3)),
                                          service_endpoint='https://outlook.office365.com/EWS/exchange.asmx')
            pin = self.organization_helper.get_tfa_pin(configuration,
                                self.config_json.Install.tfa_details.primary_smtp_address,
                                                       sent_time)

            if pin:
                # Adding the pin to password and executing the simcallwrapper command again
                new_password = str(self.user_password) + str(pin)
                sim_command = "-OpType 1000 -CSHost {0} -clientname " \
                              "{1} -user {2} -password {3} " \
                              "-output C:\\output.xml".format(self.commcell.webconsole_hostname,
                                                             self.client_name,
                                                             self.user_email, new_password)
                command = f"cmd.exe /c '{sim_path}' {sim_command}"
                self.log.info(f"Registering the client [{self.client_name}] on "
                              f"{self.commcell.webconsole_hostname} "
                              f"with pin")
                self.windows_machine.execute_command(command)
                time.sleep(180)
                self.log.info("Refreshing Client List on the CS")
                self.commcell.refresh()

                self.log.info("Initiating Check Readiness from the CS")
                if self.commcell.clients.has_client(self.machine_name):
                    self.client_obj = self.commcell.clients.get(self.machine_name)
                    if self.client_obj.is_ready:
                        self.log.info("Check Readiness of Client is successful")
                    self.log.info(f"Successfully registered client {self.client_name} on "
                                  f"{self.commcell.webconsole_hostname}")
                else:
                    self.log.error("Client failed Registration to the CS")
                    raise Exception(f"Client: {self.client_name} failed registering to the "
                                    f"CS, Please check client logs"
                                    )
            else:
                raise Exception(f"Mail not found in {self.user_email}")

            self.log.info("Starting Two Factor Authentication Validation")
            self.log.info(f"Validating if two factor authentication is enabled on "
                          f"{self.company} in "
                          f"{self.commcell.webconsole_hostname}")
            tfa_validation = OrganizationHelper(self.commcell, self.company)
            status = tfa_validation.get_tfa_status(self.commcell, self.organization_id)
            if status:
                self.log.info("Two factor Authentication validation successful")
            else:
                raise Exception("Two factor authentication in not enabled")
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(
                self.client_hostname,
                self,
                machine_object=self.windows_machine,
                package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                media_path=media_path if media_path else None)
            install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            try:
                installer_utils.collect_logs_after_install(self, self.windows_machine)
                if self.windows_machine.check_directory_exists(DEFAULT_LOG_DIRECTORY_WINDOWS):
                    self.windows_machine.copy_folder(DEFAULT_LOG_DIRECTORY_WINDOWS,
                                                     REMOTE_FILE_COPY_LOC)
                    self.windows_machine.rename_file_or_folder(
                        self.windows_machine.join_path(REMOTE_FILE_COPY_LOC, "Log_Files"),
                        self.id + self.windows_machine.get_system_time())
            except Exception as exp:
                self.log.info("Unable to copy the logs", exp)

        # deleting the client
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=True)
