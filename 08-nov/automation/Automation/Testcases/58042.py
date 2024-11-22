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
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Install import installer_constants, installer_messages
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase :  Push Software when Cache is empty"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push Software when Cache is empty"
        self.cs_machine = None
        self.machine_objects = None
        self.sw_cache_helper = None
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.cs_machine = Machine(machine_name=self.commcell.commserv_hostname,
                                  commcell_object=self.commcell)
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()
        self.sw_cache_helper = self.commcell.commserv_cache

    def run(self):
        """Main function for test case execution"""
        try:
            flag = self.cs_machine.update_registry(
                key=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("key"),
                value=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("value"),
                data=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("data"),
                reg_type=installer_constants.DO_NOT_DOWNLOAD_FROM_INSTALL_JOB.get("reg_type")
            )
            if not flag:
                self.log.error("Failed to stop the automatic download process from push install ")
                raise Exception("Failed to create a Registry Key")

            # Deleting the present SoftwareCache
            try:
                self.sw_cache_helper.delete_cache()
                self.sw_cache_helper.commit_cache()
            except Exception:
                if self.cs_machine.check_directory_exists(
                        self.cs_machine.join_path(self.sw_cache_helper.get_cs_cache_path(), "CVMedia")):
                    raise Exception("Unable to delete SW cache")
            version_info = self.commcell.version.split(".")
            build_sp = version_info[0] + "." + version_info[1]
            trans_id = self.cs_machine.get_registry_value("UpdateBinTransactions", "SPTranID").split("_")[1]
            failed_reason = \
                installer_messages.QINSTALL_PKG_INFO_MISSING_AFTER_DOWNLOAD.replace("Build.SPversion", build_sp)
            failed_reason = failed_reason.replace("transId", trans_id)

            for platform in self.machine_objects:
                install_help = InstallHelper(self.commcell, platform)
                if platform.check_registry_exists("Session", "nCVDPORT"):
                    install_help.uninstall_client()
                job_install = install_help.install_software(
                    client_computers=[install_help.client_host],
                    features=['FILE_SYSTEM', 'MEDIA_AGENT']
                    )
                if job_install.wait_for_completion(5):
                    raise Exception(f"{install_help.client_host} "
                                    f"client is marked as installed even with cache being empty")

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
