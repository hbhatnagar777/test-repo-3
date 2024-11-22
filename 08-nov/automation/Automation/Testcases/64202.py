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
from cvpysdk.commcell import Commcell
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install.update_helper import UpdateHelper
from Install.softwarecache_validation import SoftwareCache, RemoteCache
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, constants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Testcase :  Push SP Upgrade of  windows and unix RCs with Akamai sync enabled"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Akamai based remote cache sync specific packages windows, Linux"
        self.windows_machine = None
        self.unix_machine = None
        self.windows_helper = None
        self.unix_helper = None
        self.config_json = None
        self.organization_helper = None
        self.company = None
        self.authcode = None
        self.update_helper = None
        self.client_group = "Akamai RC specific pkg sync"
        self.tcinputs = {
            'ServicePack': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_windows_3.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_windows_3.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_windows_3.password)
        self.unix_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_unix_3.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_unix_3.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_unix_3.password)
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.company = self.config_json.Install.rc_automation.company
        self.unix_helper = InstallHelper(self.commcell, self.unix_machine)
        self.authcode = self.commcell.enable_auth_code()
        self.update_helper = UpdateHelper(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:

            win_os_to_sync = ["WINDOWS_64"]
            unix_os_to_sync = ["UNIX_LINUX64"]
            win_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT", "VIRTUAL_SERVER"]
            unix_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT", "VIRTUAL_SERVER"]

            # Configuring the clients as RC's
            _windows_client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
            _unix_client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
            for each_client in [_windows_client_obj, _unix_client_obj]:
                self.log.info(f"Configuring {each_client.client_name} as Remote Cache")
                _cache_obj = SoftwareCache(self.commcell, each_client)
                _cache_obj.configure_remotecache()
                _cache_obj.configure_packages_to_sync(win_os_to_sync, win_packages_to_sync,
                                                      unix_os_to_sync, unix_packages_to_sync)

            # Creating a new client group and adding the clients to it
            clients = [_windows_client_obj.client_name, _unix_client_obj.client_name]
            self.log.info(f"Adding clients {clients} to the Client group {self.client_group}")
            if not self.commcell.client_groups.has_clientgroup(self.client_group):
                self.commcell.client_groups.add(
                    self.client_group, clients)
            else:
                _client_group_obj = self.commcell.client_groups.get(self.client_group)
                _client_group_obj.add_clients(clients)

            # Enabling Akamai based download
            _client_group_obj = self.commcell.client_groups.get(self.client_group)
            _client_group_prop = _client_group_obj.properties
            _client_group_prop['forceClientSideDownload'] = 1
            _client_group_obj.update_properties(_client_group_prop)

            # Validating if Akamai download is enabled
            is_enabled = _client_group_obj.properties.get('forceClientSideDownload')
            if is_enabled:
                self.log.info(f"Akamai sync is successfully enabled on the client "
                              f"group  {self.client_group}")
            else:
                raise Exception(f"Enabling Akamai sync on client group "
                                f"{self.client_group} failed")

            # Push SP upgrade on client group
            job_obj = self.commcell.sync_remote_cache(client_list=clients)

            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Syncing clients")
            else:
                raise Exception("Sync job failed!!")

            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computer_groups=[self.client_group], reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info("Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")

            self.log.info("Initiating Check Readiness from the CS")
            for each_client in [self.windows_machine.machine_name, self.unix_machine.machine_name]:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info("Check Readiness of Client is successful")
                else:
                    self.log.error("Client failed Registration to the CS")
                    raise Exception(
                        f"Client: {each_client} failed registering to the CS,"
                        f" Please check client logs")

                self.log.info(f"Starting Upgrade Validation of client {each_client}")
                install_validation = InstallValidator(each_client, self, is_push_job=True)
                install_validation.validate_install()

            # Validating the sync
            for each_client in [_windows_client_obj, _unix_client_obj]:
                _rc_obj = RemoteCache(each_client, self.commcell)
                self.log.info(f"Starting Remote cache validation for {each_client.client_name}")
                configured_os_pkg_list = {}
                query = f"select OSId, PackagesinCache from PatchUAContentConfig where " \
                        f"UAClientId = '{each_client.client_id}' and PackagesinCache != ''"
                self.csdb.execute(query)
                for each_row in self.csdb.fetch_all_rows():
                    pkgs = each_row[1].split(',')
                    pkgs = ' '.join(pkgs).split()
                    configured_os_pkg_list[int(each_row[0])] = list(map(int, pkgs))
                _rc_obj.validate_remote_cache(configured_os_pkg_list)

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        pass
