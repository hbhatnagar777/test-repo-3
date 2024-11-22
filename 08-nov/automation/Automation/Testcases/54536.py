# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate CVAppliance Media using Download Software

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, config, constants
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import DownloadValidation
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages
from Web.AdminConsole.Helper import adminconsoleconstants
from AutomationUtils.database_helper import CommServDatabase


class TestCase(CVTestCase):
    """Testcase : Validate CVAppliance Media using Download Software"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Validate CVAppliance Media using Download Software"
        self.log = None
        self.config_json = None
        self.download_helper = None
        self.validation_helper = None
        self.sw_cache_helper = None
        self.schedule_patten = {}
        self.cs_machine_obj = None
        self.job_controller = None
        self.job_mgt = None

    def setup(self):
        """Setup function of this test case"""
        self.log = logger.get_log()
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=self.config_json.Install.commserve_client.webserver_username,
                commcell_password=self.config_json.Install.commserve_client.cs_password)
        self.job_controller = JobController(self.commcell)
        self.download_helper = SoftwareCache(self.commcell)
        self.sw_cache_helper = self.commcell.commserv_cache

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Killing active download jobs in CS")
            for jid, data in self.job_controller.active_jobs().items():
                if data['operation'] == 'Download Software':
                    self.job_controller.get(jid).kill(wait_for_job_to_kill=True)

            self.log.info("Checking if CV Appliance Media clients are enabled")
            if self.check_for_cv_appliance_clients_enabled():
                self.log.info("CV Appliance media will be downloaded")

            else:
                self.log.error("CV Appliance pacthes are no enabled for the eligible clients. "
                               "CV Appliance Media wont be downloaded")
                raise Exception("Found no clients pertaining CV Appliance media to be downloaded")

            self.log.info("Starting Download Job")
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])

            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")

            self.log.info("Starting Validation of CV Appliance Media")
            self.validation_helper = DownloadValidation(self.commcell, job_id=job_obj.job_id,
                                                        download_option=adminconsoleconstants.DownloadOptions.LATEST_SP.value,
                                                        os_to_download=[DownloadPackages.WINDOWS_64.value,
                                                                        DownloadPackages.UNIX_LINUX64.value])
            self.validation_helper.download_validation()
            self.validation_helper.validate_cvappliance_media(validate_rc=True)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def check_for_cv_appliance_clients_enabled(self):
        """Returns true if atleast one client is enabled for CV Appliance Media"""
        csdb = CommServDatabase(self.commcell)
        mssql_versions = []

        query = "select version from simInstalledThirdPartyCU where enabled = 1 and type = 1"
        csdb.execute(query)
        db_response = csdb.fetch_all_rows()
        for count in range(len(db_response)):
            if db_response[count][0] != "":
                mssql_versions.append(db_response[count][0])

        windows_versions = []
        query = "select version from simInstalledThirdPartyCU where enabled = 1 and type = 2"
        self.csdb.execute(query)
        db_response = self.csdb.fetch_all_rows()
        for count in range(len(db_response)):
            if db_response[count][0] != "":
                windows_versions.append(db_response[count][0])

        if mssql_versions or windows_versions:
            return True

        else:
            return False

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("reverting protocol type to HTTPS")
        self.download_helper.set_protocol_type("HTTPS")
