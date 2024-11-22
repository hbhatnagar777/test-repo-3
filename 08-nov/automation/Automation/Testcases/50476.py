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
from cvpysdk.deployment.deploymentconstants import DownloadOptions as download_constants
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Install.softwarecache_validation import DownloadValidation
from Install.install_helper import InstallHelper
from Install.softwarecache_validation import RemoteCache
from Install.softwarecache_helper import SoftwareCache


class TestCase(CVTestCase):
    """Class for validating remote cache sync """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating remote cache sync"
        self.commcell = None
        self.options_selector = None
        self.download_val = None
        self.config_json = None

    def uninstall_client(self, client_dict):
        """uninstalls client"""
        for each_client in client_dict:
            if self.commcell.clients.has_client(each_client.hostname):
                machine_object = self.options_selector.get_machine_object(machine=each_client.hostname,
                                                                          username=each_client.username,
                                                                          password=each_client.password)
                install_helper = InstallHelper(self.commcell, machine_object)
                self.log.info("Cleaning up installed %s client", each_client.hostname)
                install_helper.uninstall_client()

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.download_val = DownloadValidation(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self.config_json = config.get_config()

    def run(self):
        """Main function for test case execution"""
        failed_clients = []
        failed_rc_clients = []

        data = self.config_json.Install.client_data

        self.uninstall_client(data.remote_cache_list)
        self.uninstall_client(data.client)
        self.uninstall_client(data.push_new_client)

        client_success = []
        # Install client to be associated to RC's in json file
        for each_client in data.client:
            if not self.commcell.clients.has_client(each_client.hostname):
                client_machine_object = self.options_selector.get_machine_object(machine=each_client.hostname,
                                                                                 username=each_client.username,
                                                                                 password=each_client.password)
                install_helper = InstallHelper(self.commcell, client_machine_object)
                self.log.info("Installing client to be associated to RC client %s", each_client.clientname)
                job = install_helper.install_software(client_computers=[each_client.hostname],
                                                      username=each_client.username,
                                                      password=each_client.password)

                if not job.wait_for_completion():
                    failed_clients.append(each_client.clientname)
                    self.log.info("%s Client installation Failed", each_client.clientname)
                else:
                    client_success.append(each_client.clientname)
                    self.log.info("%s Client installation Passed", each_client.clientname)

        client_group_name_list = []
        # creating a client Group for clients and adding clients to it
        self.log.info("-----------creating a client Group for clients and adding clients to it------------")
        for each_client in data.client:
            if each_client.clientname in client_success:
                client_group_name = f"{each_client.rc_clientname}_group"
                client_group_name_list.append(client_group_name)
                if self.commcell.client_groups.has_clientgroup(client_group_name):
                    if each_client.clientname not in self.commcell.client_groups.get(
                            client_group_name).associated_clients:
                        self.commcell.client_groups.get(client_group_name).add_clients(each_client.clientname)
                else:
                    self.commcell.client_groups.add(client_group_name, each_client.clientname)
        rc_client_success = []
        # Install RC's in json file
        for each_rc in data.remote_cache_list:
            if not self.commcell.clients.has_client(each_rc.hostname):
                self.log.info("Installing Remote cache client %s", each_rc.clientname)
                rc_machine_object = self.options_selector.get_machine_object(machine=each_rc.hostname,
                                                                             username=each_rc.username,
                                                                             password=each_rc.password)
                install_helper = InstallHelper(self.commcell, rc_machine_object)
                job = install_helper.install_software(client_computers=[each_rc.hostname],
                                                      username=each_rc.username,
                                                      password=each_rc.password)

                if not job.wait_for_completion():
                    failed_rc_clients.append(each_rc.clientname)
                    self.log.info("{0} RC Client installation Failed".format(each_rc.clientname))
                else:
                    rc_client_success.append(each_rc.clientname)
                    self.log.info("{0} Client installation Passed".format(each_rc.clientname))
                    self.commcell.refresh()
                    client_obj = self.commcell.clients.get(each_rc.hostname)
                    software_cache_obj = SoftwareCache(self.commcell, client_obj)
                    software_cache_obj.configure_remotecache()
                    software_cache_obj.remote_cache_obj.assoc_entity_to_remote_cache(
                        client_group_name=f"{each_rc.clientname}_group")
                    configured_os_pkg_list = {}
                    win_os = []
                    win_packages = []
                    unix_os = []
                    unix_packages = []
                    for os_id in each_rc.packages_to_sync[0]:
                        win_os.append(OSNameIDMapping(int(os_id)).name)
                    for os_id in each_rc.packages_to_sync[2]:
                        unix_os.append(OSNameIDMapping(int(os_id)).name)
                    for packages in each_rc.packages_to_sync[1]:
                        win_packages.append(WindowsDownloadFeatures(int(packages)).name)
                    for packages in each_rc.packages_to_sync[3]:
                        unix_packages.append(UnixDownloadFeatures(int(packages)).name)

                    if len(win_os) != 0:
                        for each in each_rc.packages_to_sync[0]:
                            configured_os_pkg_list[each] = each_rc.packages_to_sync[1]
                    if len(unix_os) != 0:
                        for each in each_rc.packages_to_sync[2]:
                            configured_os_pkg_list[each] = each_rc.packages_to_sync[3]
                    each_rc.configured_os_pkg_list = configured_os_pkg_list
                    # configuring packages to sync
                    software_cache_obj.configure_packages_to_sync(win_os,
                                                                  win_packages,
                                                                  unix_os,
                                                                  unix_packages)

        job_obj = self.commcell.download_software(
            options=download_constants.LATEST_HOTFIXES.value,
            os_list=[DownloadPackages.WINDOWS_32.value, DownloadPackages.WINDOWS_64.value,
                     DownloadPackages.UNIX_LINUX64.value,
                     DownloadPackages.UNIX_AIX.value
                     ],
            sync_cache=True)

        if not job_obj.wait_for_completion():
            self.log.info("Downloading job failed. Please check logs")
            raise Exception("Download job failed")

        push_job = self.commcell.push_servicepack_and_hotfix(client_computer_groups=client_group_name_list,
                                                             run_db_maintenance=False)

        if not push_job.wait_for_completion():
            self.log.info("Push job failed. Please check logs")
            raise Exception("Push job failed")

        # validating remote caches
        for each_rc in data.remote_cache_list:
            if each_rc.clientname in rc_client_success:
                rc_client_obj = self.commcell.clients.get(each_rc.hostname)
                remote_cache_val_obj = RemoteCache(
                    client_obj=rc_client_obj,
                    commcell=self.commcell)
                if bool(each_rc.configured_os_pkg_list):
                    remote_cache_val_obj.validate_remote_cache(each_rc.configured_os_pkg_list)
                else:
                    remote_cache_val_obj.validate_remote_cache(each_rc.configured_os_pkg_list, sync_all=True)
