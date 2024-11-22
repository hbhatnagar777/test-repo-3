# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase: Class for executing this test case

  __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case        

Sample Input:
    "65639": {
            "HostNames" : ["hostname"],
            "UserName" : "username",
            "Password" : "password",
            "OsType"   : "linux",
            "sshPortNumber" : 22,
        }

Note: 

1) To install MediaAgent on Windows from Command Center, windows machine should have a few prerequisites done.
The prerequisites are mentioned in the below link:

https://documentation.commvault.com/2023e/expert/prerequisites_for_installations_using_commcell_console.html

2) A fresh Machine is expected, that is a client already registered with CS shoudn't be given as input for this test case.

"""

import time

from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents
from Web.AdminConsole.Helper.MediaAgentHelper import MediaAgentHelper

from selenium.common.exceptions import NoSuchElementException

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()

        self.name = "[Command Center] Install MediaAgent and Add MediaAgent Role Validation"

        self.browser = None
        self.driver = None
        self.admin_console = None
        self.media_agents = None
        self.hostname = None
        self.username = None
        self.password = None
        self.os_type = None
        self.port_number = None
        self.saved_credential_name = None
        self.install_location = None
        self.reboot_if_required = None
        self.tcinputs = {
            'HostNames': None,
            'UserName': None,
            'Password': None,
            'OsType': None,
            # 'SoftwareCache' : None,
            # 'sshPortNumber' : 22
            # 'SavedCredentialName' : None,
            # 'InstallLocation' : None,
            # 'RebootIfRequired' : False
        }
        self.client_names = None
        self.client_ids = None

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.driver = self.browser.driver
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        self.init_tc()

        self.hostnames = self.tcinputs['HostNames']
        self.username = self.tcinputs['UserName']
        self.password = self.tcinputs['Password']
        self.os_type = self.tcinputs['OsType']

        self.saved_credential_name = self.tcinputs.get('SavedCredentialName')
        self.software_cache = self.tcinputs.get('SoftwareCache', None)
        self.port_number = self.tcinputs.get('sshPortNumber', 22)
        self.install_location = self.tcinputs.get('InstallLocation', None)
        self.reboot_if_required = self.tcinputs.get('RebootIfRequired', False)

        self.media_agents = MediaAgents(self.admin_console)
        self.media_agent_helper = MediaAgentHelper(self.admin_console)
        self.storage_helper = StorageMain(self.admin_console)
        self.mm_helper = MMHelper(self)
        self.servers = Servers(self.admin_console)

    def relogin_if_logged_out(self):
        """Relogin if logged out"""

        if self.admin_console._is_logout_page():
            self._log.info("Seems like Logged out from Command Centre due to timeout, relogging in")
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

    def get_client_names_and_ids_using_hostnames(self, ignore_entries=False):
        """"Returns the client name and id of the given hostnames"""

        name_and_ids = []
        entries_not_found = []

        for hostname in self.hostnames:
            query = f"""SELECT name,id
                            FROM APP_CLIENT
                            WHERE net_hostname='{hostname}'
                    """

            self._log.info("QUERY: %s", query)
            self.csdb.execute(query)
            query_res = self.csdb.fetch_one_row()
            self._log.info("RESULT: %s", query_res)

            if (query_res[0] == ''):
                entries_not_found.append(hostname)
            else:
                client_name = query_res[0].strip()
                client_id = query_res[1].strip()
                name_and_ids.append((client_name, client_id))
                self._log.info(f"Client {hostname} has Client Name : {client_name} and Id : {client_id}")

        if (not ignore_entries and len(entries_not_found) > 0):
            raise Exception(
                f"No entry in APP_CLIENT found for hostnames {entries_not_found}")

        return name_and_ids

    def install_media_agent(self):
        """Installs media agent and waits for job completion"""

        job_id = self.media_agent_helper.install_media_agent(self.hostnames, self.os_type,self.username, self.password, self.saved_credential_name, software_cache=self.software_cache,
                                                         port_number=self.port_number, install_location=self.install_location, reboot_if_required=self.reboot_if_required)
        job_obj = self.commcell.job_controller.get(job_id)

        try:
            self.mm_helper.wait_for_job_completion(job_obj,retry_interval=90,timeout=60)
        except Exception as e:
            self._log.error(f"Install MA Job with Job Id : {job_id} failed with error {e}")
            raise e

        self._log.info(f"Successfully installed Media Agent on [{self.hostnames}]")

    @test_step
    def install_ma_and_validate(self):
        """Install MA and validate"""

        self.install_media_agent()

        name_and_ids = self.get_client_names_and_ids_using_hostnames(ignore_entries=False)

        self.client_names = [name_and_id[0] for name_and_id in name_and_ids]
        self.client_ids = [name_and_id[1] for name_and_id in name_and_ids]

        self.validate_ma_entry_and_rolebitmask(self.client_ids)
        self.validate_ma_license_consumed(self.client_ids)
        self.validate_ma_reg_key(self.client_names)

    @test_step
    def add_ma_role_and_validate(self):
        """Add MA role and validate"""
        # the reason we are not using polling here and instead wait_time_for_table_reload is
        # because here we have to poll for if the Add MA Role btn exists or not and it becomes unnecessarily complicated

        self.media_agent_helper.add_ma_role(self.client_names,wait_time_for_table_reload=150)

        self.validate_ma_entry_and_rolebitmask(self.client_ids)
        self.validate_ma_license_consumed(self.client_ids)

    def add_disk_storage_to_media_agents(self, ma_names):
        """Adds a dedupe disk storage and associate all the given media agents with that disk storage"""

        # this function is helping us validate that after we add MA role does the MA appear while adding disk storage 

        for i,ma_name in enumerate(ma_names):
            storage_pool_name = f"{self.id}_SP_{i}"

            (ma_machine, ma_drive) = self.mm_helper.generate_automation_path(ma_name, 32)
            mount_path = ma_machine.join_path(ma_drive, "Automation", str(self.id), "MP")
            ddb_path = ma_machine.join_path(ma_drive, "Automation", str(self.id), "DDB")
            self._log.info(f"Mount Path for media agent {ma_name} : {mount_path}")
            self._log.info(f"DDB Path for media agent {ma_name} : {ddb_path}")

            self.storage_helper.add_disk_storage(storage_pool_name,ma_name,mount_path,deduplication_db_location=ddb_path)

    @test_step
    def add_disk_storage_to_ma_and_validate_direct_retire(self):
        """Add disk storage to media agents and validate"""

        self.add_disk_storage_to_media_agents(self.client_names)
        self.validate_retire_servers_failure(self.client_names)
        # since we added disk storage from UI let's update the commcell SDK object so that while cleanup_storage_pool() we can see the pool
        self.commcell.storage_pools.refresh()

    @test_step
    def retire_ma_and_validate(self):
        """Retire MA and validate"""

        self.media_agent_helper.retire_media_agents(self.client_names)

        self.validate_ma_entry_and_rolebitmask(self.client_ids,assert_failure = True)
        self.validate_ma_license_consumed(self.client_ids,assert_failure = True)

    @test_step
    def retire_ma_role_and_server(self):
        """ Retire from MA role then retire the client """

        self.media_agent_helper.retire_media_agents(self.client_names)
        self.retire_servers(self.client_names,select_from_all_server = True, wait_time_for_table_reload=60)

    def retire_servers(self, client_names,select_from_all_server, wait_time_for_table_reload=60):
        """Retire all the given clients"""

        # Here also we use wait_time_for_table_reload instead of polling mechanism because 
        # If MA role retired is reflected in UI then we can retire but we can't directly check that 
        # making polling complicated so we go with simple reload

        self.admin_console.navigator.navigate_to_servers()

        # we would need to reload the table so that it reloads and reflects the latest data otherwise causes issues sometimes
        if wait_time_for_table_reload > 0:
            time.sleep(wait_time_for_table_reload)
            self.servers.reload_data()

        for client_name in client_names:

            try:
                job_id = self.servers.retire_server(client_name, select_from_all_server,wait = False)
                self._log.info(f"Retiring Server [{client_name}], job id : {job_id}")
                job_obj = self.commcell.job_controller.get(job_id)
                try:
                    self.mm_helper.wait_for_job_completion(job_obj)
                except Exception as e:
                    self._log.error(f"Retire Server Job with Job Id : {job_id} failed with error {e}")
                    raise e
                self._log.info(f"Successfully retired server [{client_name}]")

            except NoSuchElementException as e:
                self._log.error(f"Retire option not found for Server {client_name}, so lets try using delete option")
                # We refresh the page because otherwise click gets intercepted becuase the action menu is opened (from retire_server())
                self.admin_console.refresh_page()
                self.servers.delete_server(client_name, select_from_all_server)
                self._log.info(f"Successfully deleted server [{client_name}]")
                                
            self.media_agent_helper._close_popup_if_present()

    def clean_env_for_testcase(self):
        """Cleans the environment for the test case"""

        # We are using cleanup_storage_policies() because if you retire a MA when it still has storage pool associated with it , then policy still exists but no pool
        self.cleanup_storage_policies()
        self.cleanup_clients()

    def cleanup_storage_policies(self):
        """Deletes storage policies that are created in this testcase"""

        for i in range(len(self.hostnames)):
            storage_policy_name = f"{self.id}_SP_{i}"
            self.mm_helper.delete_storage_policy(storage_policy_name)

    def cleanup_storage_pools(self):
        """Deletes the storage pools that are created in this testcase"""

        for i in range(len(self.hostnames)):
            storage_pool_name = f"{self.id}_SP_{i}"
            self.mm_helper.delete_storage_pool(storage_pool_name)

    def cleanup_clients(self):
        """ Retire all the clients provided in this test case for a clean start of the test case"""

        name_and_ids = self.get_client_names_and_ids_using_hostnames(ignore_entries=True)
        client_names = [name_and_id[0] for name_and_id in name_and_ids]

        for client_name in client_names:
            # You can't retire client who has storage associated directly , so first retire the MA role and then retire the client
            self.mm_helper.retire_media_agent(client_name,force=True)
            self.mm_helper.retire_client(client_name)

    def validate_retire_servers_failure(self, server_names):
        """Validate that retire servers fails for all the given clients"""

        timeout = 10 # minutes
        polling_interval = 30 # seconds
        
        self.admin_console.navigator.navigate_to_servers()

        for server_name in server_names:

            start_time = time.time()
            while True:
                if (time.time() - start_time) > timeout * 60:
                    raise Exception(f"Server not found in Servers Page (Infrastructure Filter) in {timeout} minutes")
            
                self.servers.reload_data()
                if (self.servers.is_client_exists(server_name)):
                    break
                time.sleep(polling_interval)

            try:
                self.servers.retire_server(server_name,select_from_all_server=False)
                # we are raising exception here because we are expecting retire server to fail
                raise Exception(f"Retire server didn't fail for server {server_name}")
            except CVWebAutomationException as e:
                if("Cannot retire" in str(e)):
                    self._log.info(f"retire server failed as expected with error msg '{e}' ")
                else:
                    raise e

    def validate_ma_entry_and_rolebitmask(self, client_ids,assert_failure = False):
        """validate if MA has entry in MMHost and default role bitmask is set for all given clients"""

        client_id_list = "', '".join(client_ids)

        query = f"""SELECT COUNT(1)
                        FROM MMHost
                        WHERE ClientId IN ('{client_id_list}')
                        and RolesBitMask & 512 = 512 
                """

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        query_res = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", query_res)

        if(assert_failure):
            if(query_res[0] != '0'):
                raise Exception("Few clients still have entry in MMHost table and Standard MA role set")
            else:
                self._log.info(f"All the given clients [{self.client_names}] entries have been removed from MMHost")

        else:
            if (query_res[0] != str(len(client_ids))):
                raise Exception("Few clients still don't have entry in MMHost table or Standard MA role set")
            else:
                self._log.info(f"All the given clients [{self.client_names}] have entry in MMHost and Standard MA role set")

    def validate_ma_license_consumed(self, client_ids,assert_failure = False):
        """Validate if MA license is consumed by all given clients"""

        MA_APP_TYPE = 1002

        client_id_list = "', '".join(client_ids)

        query = f"""SELECT COUNT(1)
                        FROM LicUsage
                        WHERE CId IN ('{client_id_list}')
                        and AppType = '{MA_APP_TYPE}'
                        and OpType = 'UnInstall'
                """

        self._log.info("QUERY: %s", query)
        self.csdb.execute(query)
        query_res = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", query_res)

        if(assert_failure):
            if(query_res[0] != str(len(client_ids))):
                raise Exception("Few clients still have the MA license consumed")
            else:
                self._log.info(f"As Expected None of the given clients [{self.client_names}] have consumed the MA license")

        else:
            if(query_res[0] != '0'):
                raise Exception("Few clients have not consumed the MA license")
            else:
                self._log.info(f"All the given clients [{self.client_names}] have consumed the MA license")

    def validate_ma_reg_key(self, client_names):
        """Validate if MA reg key Base/nPLATTYPE have bit 2 set for all windows clients"""

        # self.commcell.clients.refresh() updates clients list in our commcell obj, otherwise Machine() object creation can fail because it might not see that client
        self.commcell.clients.refresh()

        for client_name in client_names:
            machine = Machine(client_name, self.commcell)
            reg_key = int(machine.get_registry_value("Base", "nPLATTYPE"))

            self._log.info(f"Platform Type set on media agent [{client_name}] registry is {reg_key}")

            # check if 2nd bit of reg_key is set
            if not (reg_key & 2):
                raise Exception(f"MediaAgent Platform type is not set on media agent [{client_name}] registry")
            else:
                self._log.info(f"As Expected MediaAgent Platform type is set on media agent [{client_name}] registry")

    def run(self):

        try:
            self.clean_env_for_testcase()

            self.install_ma_and_validate()
            self.relogin_if_logged_out()
            self.retire_ma_and_validate()
            self.add_ma_role_and_validate()
            self.add_disk_storage_to_ma_and_validate_direct_retire()
            self.cleanup_storage_pools()
            self.retire_ma_role_and_server()

            self.browser.close_silently(self.browser)

        except Exception as e:
            handle_testcase_exception(self, e)
