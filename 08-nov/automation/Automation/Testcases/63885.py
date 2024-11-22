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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    install_fs()    --  Installs base FS package on client

    install_ws()    --  Installs webserver package on client

    validate_tppm() --  Validates whether dynamic tppm worked or not

    set_tppm_settings() --  sets tppm settings on webserver client

    tear_down()     --  tear down function of this test case

"""
import time

from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures

from AutomationUtils.config import get_config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.tppm_helper import WebServerTPPM
from dynamicindex.utils import constants as dynamic_constants
from Install.install_helper import InstallHelper
from Install.silent_install_helper import SilentInstallHelper
from dynamicindex.vm_manager import VmManager

_CONFIG_DATA = get_config().DynamicIndex.WindowsHyperV


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
        self.name = "Webserver TPPM : Validate dynamic TPPM on fresh Windows webserver client"
        self.tcinputs = {
            "commcellUsername": None,
            "EncryptPassword": None,
            "WebServerClient": None
        }
        self.vm_helper = None
        self.tppm_helper = None
        self.cs_machine_obj = None
        self.client_machine_obj = None
        self.tppm_commcell = None
        self.client_machine_obj_cred = None
        self.tppm_file_path = 'c:\\Tppm_Windows_Setup.txt'

    def install_ws(self):
        """Installs web server package on client"""
        self.log.info("Going to install webserver package on client")
        install_inputs = {
            "csClientName": self.commcell.commserv_client.client_name,
            "csHostname": self.commcell._commserv_hostname,
            "commservePassword": self.tcinputs['EncryptPassword'],
            "instance": "Instance001",
            "commserveUsername": self.tcinputs['commcellUsername'],
            "revertsnap": True,
            "machineobj": self.client_machine_obj_cred
        }

        silent_helper = SilentInstallHelper.create_installer_object(_CONFIG_DATA.VmName,
                                                                    f"SP{self.commcell.commserv_version}",
                                                                    self.client_machine_obj,
                                                                    install_inputs)
        self.client_machine_obj.username = _CONFIG_DATA.VmUsername
        self.client_machine_obj.password = _CONFIG_DATA.VmPassword
        silent_helper.silent_install(
            packages_list=[
                getattr(
                    WindowsDownloadFeatures,
                    dynamic_constants.WEB_SERVER).value,
                getattr(
                    WindowsDownloadFeatures,
                    dynamic_constants.WEB_CONSOLE).value],
            is_revert=True)

    def install_fs(self):
        """Installs file system package on new client"""

        self.vm_helper.check_client_revert_snap(
            hyperv_name=_CONFIG_DATA.HyperVName,
            hyperv_user_name=_CONFIG_DATA.HyperVUsername,
            hyperv_user_password=_CONFIG_DATA.HyperVPassword,
            snap_name="PlainOS",
            vm_name=_CONFIG_DATA.VmName)
        self.log.info("Revert snap is successful")
        self.commcell.clients.refresh()
        self.vm_helper.populate_vm_ips_on_client(
            config_data=_CONFIG_DATA,
            clients=[
                self.commcell.commserv_client.client_name,
                self.tcinputs['WebServerClient']])
        self.client_machine_obj_cred = Machine(machine_name=_CONFIG_DATA.VmName, username=_CONFIG_DATA.VmUsername,
                                               password=_CONFIG_DATA.VmPassword)
        windows_helper = InstallHelper(commcell=self.commcell, machine_obj=self.client_machine_obj_cred)
        self.log.info(
            f"Starting a Push Install Job on the Machine for FS package [{str(windows_helper)}]: {_CONFIG_DATA.VmName}")
        push_job = windows_helper.install_software(
            client_computers=[_CONFIG_DATA.VmName],
            features=[dynamic_constants.FILE_SYSTEM_PACKAGE],
            username=_CONFIG_DATA.VmUsername,
            password=_CONFIG_DATA.VmPassword)
        self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
        if not push_job.wait_for_completion():
            raise Exception("Push Job didn't complete successfully for FS Package")
        self.log.info(f"Push job completed. Refreshing clients")
        self.commcell.clients.refresh()

    def validate_tppm(self):
        """Validates whether dynamic tppm worked or not"""
        if not self.tppm_helper.validate_firewall_entry():
            raise Exception(f"TPPM entry is not found for this webserver in app_firewalltppm table")
        self.client_machine_obj.set_logging_debug_level(service_name=dynamic_constants.DM2_WEB_LOG, level='10')
        time.sleep(120)
        if self.tppm_helper.is_sql_port_open():
            self.log.info(f"Webserver is able to ping CS sql port. Start firewall on CS")
            self.cs_machine_obj.start_firewall()
            time.sleep(120)
            self.log.info("Restarting IIS & Waiting for 3mins")
            self.client_machine_obj_cred.restart_iis()
            time.sleep(200)
            if self.tppm_helper.is_sql_port_open():
                raise Exception(f"Webserver is able to ping CS sql port even after CS firewall start")
        self.log.info("Webserver is not able to ping CS sql port. Try login for user")
        try:
            self.tppm_commcell = Commcell(
                _CONFIG_DATA.VmName,
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
        except Exception:
            raise Exception("Login fails for new webserver. Dynamic TPPM didn't kick in")
        self.log.info("User login worked. Try finding tppm related log lines in dm2web.log")

    def set_tppm_settings(self):
        """adds tppm settings on webserver client"""
        self.tppm_helper = WebServerTPPM(commcell=self.commcell, client_name=_CONFIG_DATA.VmName)
        self.tppm_helper.cs_firewall_setup()
        # Set additional settings to enable tppm
        self.client_machine_obj.remove_registry(key=dynamic_constants.COMMSERV_REG_KEY,
                                                value=dynamic_constants.WEB_SERVER_ENABLE_TPPM_KEY)
        self.log.info(f"Updating new webserver with TPPM key - {_CONFIG_DATA.VmName}")
        result = self.client_machine_obj.create_registry(
            key=dynamic_constants.COMMSERV_REG_KEY,
            value=dynamic_constants.WEB_SERVER_ENABLE_TPPM_KEY,
            data="True",
            reg_type="String")
        if not result:
            raise Exception(f"Failed to set tppm enable registry key on new webserver - {_CONFIG_DATA.VmName}")
        self.log.info("Doing IIS Reset and waiting for 5mins for webserver to come up")
        self.client_machine_obj_cred.restart_iis()
        time.sleep(300)

    def setup(self):
        """Setup function of this test case"""
        self.log.info(f"Setting up test environment")
        # clear the older tppm file if any
        controller = Machine()
        if controller.check_file_exists(file_path=self.tppm_file_path):
            controller.delete_file(file_path=self.tppm_file_path)
        self.vm_helper = VmManager(self)
        self.cs_machine_obj = Machine(
            machine_name=self.commcell.commserv_client.client_name,
            commcell_object=self.commcell)
        self.log.info(f"Stopping Firewall on CS")
        self.cs_machine_obj.stop_firewall()

        # install FS
        self.install_fs()

        self.client_machine_obj = Machine(machine_name=_CONFIG_DATA.VmName, commcell_object=self.commcell)

        # Install webserver
        self.install_ws()

        # Enable tppm
        self.set_tppm_settings()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Webserver installation finished. Going to verify tppm entry in table for this client")
            self.validate_tppm()
            self.tppm_helper.validate_tppm_in_log()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        controller = Machine()
        if self.status == constants.PASSED:
            self.log.info(f"Dynamic TPPM is enabled and working on this webserver - {_CONFIG_DATA.VmName}")
            controller.create_file(file_path=self.tppm_file_path, content="TPPM Success")
            self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                       hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                       hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                       vm_name=_CONFIG_DATA.VmName)
        else:
            self.log.info(f"Removing the file = [{self.tppm_file_path}] as dynamic TPPM setup case failed")
            if controller.check_file_exists(file_path=self.tppm_file_path):
                controller.delete_file(file_path=self.tppm_file_path)
