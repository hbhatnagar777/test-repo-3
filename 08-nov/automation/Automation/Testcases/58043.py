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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Install import installer_constants, installer_messages
from Install.install_helper import InstallHelper
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions


class TestCase(CVTestCase):
    """Negative Testcase : Push software when the cache doesn't have specific OS of the client."""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push software when the cache doesn't have specific OS of the client."
        self.cs_machine = None
        self.sw_cache_helper = None
        self.machine_objects = None
        self.job_controller = None
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Initializes test case class object"""
        self.cs_machine = Machine(machine_name=self.commcell.commserv_hostname,
                                  commcell_object=self.commcell)
        install_helper = InstallHelper(self.commcell)
        self.job_controller = JobController(self.commcell)
        self.machine_objects = install_helper.get_machine_objects(type_of_machines=2)[0]
        self.sw_cache_helper = self.commcell.commserv_cache

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)
            self.log.info("Deleting the Software cache")
            try:
                self.sw_cache_helper.delete_cache()
                self.sw_cache_helper.commit_cache()
            except Exception:
                if self.cs_machine.check_directory_exists(
                        self.cs_machine.join_path(self.sw_cache_helper.get_cs_cache_path(), "CVMedia")):
                    raise Exception("Unable to delete SW cache")
            _os_to_download = [DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value]
            self.log.info("Starting Download Software Job")
            job_obj = self.commcell.download_software(options=DownloadOptions.LATEST_HOTFIXES.value,
                                                      os_list=_os_to_download)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")

            # Restricting download from the job.
            flag = self.cs_machine.update_registry(
                key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
                value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"),
                data=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("data"),
                reg_type=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("reg_type"))

            if not flag:
                self.log.error("Failed to stop the automatic download process from push install ")
                raise Exception("Failed to create a Registry Key")

            # Deleting the present SoftwareCache and preserving CACHE Status Valid
            try:
                self.sw_cache_helper.delete_cache()
            except Exception:
                if self.cs_machine.check_directory_exists(
                        self.cs_machine.join_path(self.sw_cache_helper.get_cs_cache_path(), "CVMedia")):
                    raise Exception("Unable to delete SW cache")
            version_info = self.commcell.version.split(".")
            build_sp = version_info[0] + "." + version_info[1]
            reg_key = "UpdateBinTran" if 'windows' in self.cs_machine.os_info.lower() else "UpdateBinTransactions"
            key  = 'SP_Transaction' if 'windows' in self.cs_machine.os_info.lower() else 'SPTranID'
            registry =  self.cs_machine.get_registry_value(reg_key, key)
            trans_id = self.cs_machine.get_registry_value(reg_key, key).split("_")[1]

            failed_reason = \
                installer_messages.QINSTALL_PKG_INFO_MISSING_AFTER_DOWNLOAD.replace("Build.SPversion", build_sp)
            failed_reason = failed_reason.replace("transId", trans_id)

            # for client_machine in self.machine_objects:
            client_machine = self.machine_objects
            install_helper = InstallHelper(self.commcell, client_machine)
            if client_machine.check_registry_exists("Session", "nCVDPORT"):
                install_helper.uninstall_client()
            job_install = install_helper.install_software(
                client_computers=[install_helper.client_host],
                features=['FILE_SYSTEM', 'MEDIA_AGENT'])

            if job_install.wait_for_completion(5):
                raise Exception("Software installed when the specific OS did not exist in the SW Cache")

            job_status = job_install.delay_reason
            if failed_reason not in job_status:
                self.log.error("Job Failed due to some other reason than the expected one.")
                raise Exception(job_status)

            self.log.info("JobFailingReason:%s", job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # Updating the registry to download from the Install job
        self.cs_machine.remove_registry(
            key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
            value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"))
