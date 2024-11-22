# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test caseajain@cvautomation.onmicrosoft.com


TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""


import datetime
import time
import requests
from flask import Flask
import threading
from AutomationUtils import logger, config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.custom_package import CustomPackageCreation
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine
from Install.installer_constants import REMOTE_FILE_COPY_LOC, DEFAULT_LOG_DIRECTORY_WINDOWS, DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.install_custom_package import InstallCustomPackage
from exchangelib import Configuration, OAuth2Credentials, OAUTH2, Identity, Build, Version
from Install import installer_utils
from Server.organizationhelper import OrganizationHelper
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Windows Interactive Installation with two factor authentication enabled on CS"
        self.company = None
        self.user_password = None
        self.user_email = None
        self.organization_helper = None
        self.config_json = None
        self.organization_id = None
        self.service_pack = None
        self.client = None
        self.client_host = None
        self.password = None
        self.username = None
        self.client_obj = None
        self.remote_credentials = None
        self.client_machine = None
        self.commcell = None
        self.controller_machine = None
        self.custom_package_generator = None
        self.config_json = None
        self.machine_name = None
        self.instance = None
        self.log = None
        self.install_helper = None
        self.windows_machine = None
        self.windows_helper = None
        self.tcinputs = {
            "ServicePack": None
        }
        self.cs_password = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.company = self.config_json.Install.mastercs.tenants.tfa.company_name
        self.user_password = self.config_json.Install.mastercs.tenants.tfa.user_password
        self.user_email = self.config_json.Install.mastercs.tenants.tfa.user_email
        self.organization_helper = OrganizationHelper(self.commcell)
        self.log = logger.get_log()
        self.config_json = config.get_config()
        self.client_machine = Machine()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.remote_credentials = {"remote_clientname": self.config_json.Install.windows_client.machine_host,
                                   "remote_username": self.config_json.Install.windows_client.machine_username,
                                   "remote_userpassword": self.config_json.Install.windows_client.machine_password,
                                   "remote_client_os_name": "Windows"}
        self.install_helper = InstallHelper(self.commcell)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.machine_name
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.username = self.config_json.Install.windows_client.machine_username
        self.password = self.config_json.Install.windows_client.machine_password
        self.client_host = self.config_json.Install.windows_client.machine_host
        self.client = self.config_json.Install.rc_client.client_name
        self.controller_machine = Machine()

    def run(self):
        """Run function of this test case"""
        try:
            # enabling two-factor authentication at company level
            self.organization_helper = OrganizationHelper(self.commcell, self.company)
            self.organization_id = self.organization_helper.company_id
            self.organization_helper.enable_tfa(self.commcell, self.organization_id)

            # Deleting the client if it already exists
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)
            self.log.info(f"Starting Installation of client on {self.client_host}")
            self.log.info("Determining Media Path for Installation")
            media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
                else "SP" + str(self.commcell.commserv_version)
            if "{sp_to_install}" in media_path:
                _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            self.log.info(f"Media Path used for Installation: {media_path}")
            self.service_pack = _service_pack
            self.custom_package_generator = CustomPackageCreation(self.commcell,
                                                                  self.service_pack,
                                                                  self.client_machine,
                                                                  self.remote_credentials)

            # Generating the JSON for Custom Package
            self.log.info("Generating JSON for custom package creation")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"CustomPackageDir": self.id})

            # Creating the Custom Package with Interactive Installer
            self.custom_package_generator.create_custom_package()

            # Generating the JSON for Custom Package Installation
            controller_ip = self.controller_machine.ip_address
            self.log.info("Generating JSON for custom package installation")
            self.custom_package_generator.generate_json_for_custom_package(
                **{"CommserveName": self.commcell.webconsole_hostname,
                   "commcellPassword": self.config_json.Install.mastercs.tenants.tfa.user_password,
                   "commcellUser": self.config_json.Install.mastercs.tenants.tfa.user_email,
                   "clientName": self.client,
                   "ClientHostName": self.client_host,
                   "IsInstallingFromCustomPackage": True,
                   "installOption": "Install packages on this computer",
                   "IsToDownload": False,
                   "CreateNewInstance": True,
                   "enable_two_FA": True,
                   "token_URL": 'http://' + str(controller_ip) + ':5000/get_pin'
                   })

            # creating a Flask app
            app = Flask('MyService')

            @app.route('/get_pin')
            def get():
                present_date = datetime.datetime.now()
                sent_time = int(datetime.datetime.timestamp(present_date))
                self.log.info("Waiting for the code to come into the mailbox")
                # Fetching the pin from mail
                credentials = OAuth2Credentials(client_id=self.config_json.Install.tfa_details.client_id,
                                                client_secret=self.config_json.Install.tfa_details.client_secret,
                                                tenant_id=self.config_json.Install.tfa_details.tenant_id,
                                                identity=Identity(primary_smtp_address=
                                                self.config_json.Install.tfa_details.primary_smtp_address))
                configuration = Configuration(credentials=credentials,
                                              auth_type=OAUTH2,
                                              version=Version(Build(15, 1, 2, 3)),
                                              service_endpoint='https://outlook.office365.com/EWS/exchange.asmx')
                self.organization_helper = OrganizationHelper(self.commcell, self.company)
                pin = self.organization_helper.get_tfa_pin(configuration,
                                                           self.config_json.Install.tfa_details.primary_smtp_address,
                                                           sent_time)
                if pin:
                    self.log.info("Successfully sent pin")
                    return str(pin)
                else:
                    raise Exception(f"Mail not found in {self.user_email}")

            @app.route('/stop_server', methods=['GET'])
            def stop_server():
                return "Successfully closed the connection"

            def run_flask():
                self.log.info("Starting the Flask server")
                app.run(host="0.0.0.0")

            flask_thread = threading.Thread(target=run_flask)
            flask_thread.start()
            time.sleep(30)

            # Installing the custom package
            self.log.info("Installing the custom package")
            self.install_helper = InstallCustomPackage(self.commcell, self.remote_credentials)
            self.install_helper.install_custom_package(f"{REMOTE_FILE_COPY_LOC}\\{self.id}\\WinX64",
                                                       self.commcell.commcell_username,
                                                       self.config_json.Install.cs_machine_password,
                                                       None,
                                                       **{"dir_name": "CustomPackageLOC",
                                                          "custom_package_flag": True,
                                                          "self.id": self.id})

            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")

            self.log.info("Starting Two Factor Authentication Validation")
            self.log.info(f"Validating if two factor authentication is enabled on {self.company} in "
                          f"{self.commcell.webconsole_hostname}")
            tfa_validation = OrganizationHelper(self.commcell, self.company)
            status = tfa_validation.get_tfa_status(self.commcell, self.organization_id)
            if status:
                self.log.info("Two factor Authentication validation successful")
            else:
                raise Exception("Two factor authentication in not enabled")
            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_host, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  media_path=media_path if media_path else None)
            install_validation.validate_install(validate_sp_info_in_db=False)

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == "FAILED":
            try:
                if self.windows_machine.check_directory_exists(DEFAULT_LOG_DIRECTORY_WINDOWS):
                    self.windows_machine.copy_folder(DEFAULT_LOG_DIRECTORY_WINDOWS, REMOTE_FILE_COPY_LOC)
                    self.windows_machine.rename_file_or_folder(
                        self.windows_machine.join_path(REMOTE_FILE_COPY_LOC, "Log_Files"),
                        self.id + self.windows_machine.get_system_time())
            except Exception as exp:
                self.log.info("Unable to copy the logs", exp)

        # Deleting the client
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=False)

        # stopping the flask server
        def stop_flask():
            url = "http://127.0.0.1:5000/stop_server"
            requests.get(url=url)
        stop_thread = threading.Thread(target=stop_flask)
        stop_thread.start()
