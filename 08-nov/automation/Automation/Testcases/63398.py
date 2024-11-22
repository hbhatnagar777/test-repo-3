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
from cvpysdk.job import JobController
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.softwarecache_validation import RemoteCache
from AutomationUtils.database_helper import CommServDatabase
from Install.installer_constants import DEFAULT_COMMSERV_USER


class TestCase(CVTestCase):
    """Testcase : Akamai Sync to Windows, linux RC"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Akamai Sync to Windows, linux RC"
        self.windows_machine = None
        self.unix_machine = None
        self.config_json = None
        self.csdb = None
        self.sw_cache_helper = None
        self.job_controller = None
        self.tcinputs = {}
        self.silent_install_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_windows_1.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_windows_1.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_windows_1.password)
        self.unix_machine = Machine(
            machine_name=self.config_json.Install.rc_automation.rc_machines.rc_unix_1.hostname,
            username=self.config_json.Install.rc_automation.rc_machines.rc_unix_1.username,
            password=self.config_json.Install.rc_automation.rc_machines.rc_unix_1.password)
        self.job_controller = JobController(self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache
        self.csdb = CommServDatabase(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            # Creating client objects
            _windows_client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
            _unix_client_obj = self.commcell.clients.get(self.unix_machine.machine_name)

            # Enabling Akamai download option
            for each_client in [_windows_client_obj, _unix_client_obj]:
                self.log.info(f"Enabling Akamai download option for client "
                              f"{each_client.client_name}")
                _client_prop = each_client.properties
                _client_prop['clientProps']['forceClientSideDownload'] = 1
                each_client.update_properties(_client_prop)

            # Starting a Download/Sync job
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)

            sync_cache_list = [_windows_client_obj.client_name, _unix_client_obj.client_name]

            # self.log.info("Starting a Sync job")
            job_obj = self.commcell.sync_remote_cache(client_list=sync_cache_list)

            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Sync job successful")
            else:
                raise Exception("Sync job failed")

            # Validating the Sync
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
