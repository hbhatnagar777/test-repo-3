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
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Install.softwarecache_validation import RemoteCache
from Install.softwarecache_validation import DownloadValidation


class TestCase(CVTestCase):
    """Class for validating remote cache sync """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validating remote cache sync"
        self.commcell = None
        self.download_val = None
        self.config_json = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.download_val = DownloadValidation(self.commcell)
        self.config_json = config.get_config()

    def run(self):
        """Main function for test case execution"""
        data = self.config_json.Install.client_data

        self.download_val.revision_id, self.download_val.transaction_id, self.download_val.service_pack = self.download_val.get_sp_info(
            self.commcell.commserv_version)

        job_obj = self.commcell.download_software(
            options=download_constants.SERVICEPACK_AND_HOTFIXES.value,
            os_list=[DownloadPackages.WINDOWS_32.value, DownloadPackages.WINDOWS_64.value,
                     DownloadPackages.UNIX_LINUX64.value,
                     DownloadPackages.UNIX_AIX.value
                     ],
            service_pack=self.commcell.commserv_version,
            cu_number=int(self.download_val.get_latest_cu_pack().split("CU")[1]))

        if not job_obj.wait_for_completion():
            self.log.info("Downloading job failed. Please check logs")
            raise Exception("Download job failed")

        rc_client_list = []
        for each_rc in data.remote_cache_list:
            if self.commcell.clients.has_client(each_rc.hostname):
                rc_client_list.append(each_rc.clientname)

        self.log.info("Launching a push update job on all Remote cache clients %s: ", rc_client_list)
        rc_push_job = self.commcell.push_servicepack_and_hotfix(client_computers=rc_client_list,
                                                                run_db_maintenance=False,
                                                                maintenance_release_only=True)
        if not rc_push_job.wait_for_completion():
            self.log.info("Push job failed. Please check logs")
            raise Exception("Push job failed")

        client_list = []
        for each_client in data.client:
            if self.commcell.clients.has_client(each_client.hostname):
                client_list.append(each_client.clientname)

        self.log.info("Launching a push update job on all clients associated to RC %s: ", client_list)
        clients_push_job = self.commcell.push_servicepack_and_hotfix(
            client_computers=client_list, run_db_maintenance=False, maintenance_release_only=True)

        if not clients_push_job.wait_for_completion():
            self.log.info("Push job failed. Please check logs")
            raise Exception("Push job failed")

        for each_rc in data.remote_cache_list:
            if self.commcell.clients.has_client(each_rc.hostname):
                configured_os_pkg_list = {}
                if len(each_rc.packages_to_sync[0]) != 0:
                    for each in each_rc.packages_to_sync[0]:
                        configured_os_pkg_list[each] = each_rc.packages_to_sync[1]
                if len(each_rc.packages_to_sync[2]) != 0:
                    for each in each_rc.packages_to_sync[2]:
                        configured_os_pkg_list[each] = each_rc.packages_to_sync[3]
                rc_client_obj = self.commcell.clients.get(each_rc.hostname)
                remote_cache_val_obj = RemoteCache(
                    client_obj=rc_client_obj,
                    commcell=self.commcell)
                if bool(configured_os_pkg_list):
                    remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list)
                else:
                    remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)
