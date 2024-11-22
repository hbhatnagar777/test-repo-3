# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    pre_upgrade_steps()         --  run data operations prior to upgrade

    upgrade_steps()             --  perform the upgrade of cv

    post_upgrade_validations()  --  validates required functionality after upgrade is finished

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this case

Sample JSON:
    "67859": {
        "ClientName"    : "Name of Client",
        "AgentName"     : "File System",
        "ServicePack"   : TargeSPNumber,
        "CSHostName"    : "FQDN for the cs",
        "CSMachineUsername" : "credentials for cs machine login",
        "CSMachinePassword" : "credentials for cs machine login",
        "MediaAgentName" : "Datamover MA on Library which is used by CommServeDR Storage Policy"
        *** optional ***
        "CUPack"            : HPKNumber
    }

Note:
    - Populate CoreUtils/Templates/config.json/
        "Install":"download_server": to the download server that the cs is pointing.
"""
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Install import installer_utils
from Install.update_helper import UpdateHelper
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions


class TestCase(CVTestCase):
    """Class for executing Push Service Pack upgrades of CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()

        self.name = "Upgrade Automation - Encrypt DR Backup Copy"
        self.tcinputs = {
            "ServicePack": None,
            "CSHostName": None,
            "CSMachineUsername": None,
            "CSMachinePassword": None,
            "MediaAgentName":None
        }
        # self.config_json = None
        self.cs_machine = None

        self.storage_policy = None
        self.storage_policy_copy = None

        self.dr_obj = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.update_helper = None
        self.install_helper = None
        self.dr_jobs_list = []

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # self.config_json = config.get_config()
        self.log.info("Setting up testcase variables and objects")
        self.cs_machine = Machine(machine_name=self.tcinputs.get('CSHostName'),
                                  username=self.tcinputs.get('CSMachineUsername'),
                                  password=self.tcinputs.get('CSMachinePassword'))

        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.install_helper = InstallHelper(self.commcell)
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)

        self.dr_obj = self.commcell.disasterrecovery

    def pre_upgrade_steps(self):
        """
        Run Data operations prior to upgrade
        """
        self.log.info("Starting pre upgrade steps")

        self.log.info("Disabling Encryption on CommserveDR Policy Primary Copy")
        self.storage_policy = self.commcell.storage_policies.get("CommserveDR")
        self.storage_policy_copy = self.storage_policy.get_copy("Primary")
        self.storage_policy_copy.set_encryption_properties(plaintext=True)

        self.log.info("Running DR Backup now")
        self.dr_obj.backup_type = 'full'
        self.dr_jobs_list.append(self.dr_obj.disaster_recovery_backup())
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) started. Waiting for it to complete.")
        if not self.dr_jobs_list[-1].wait_for_completion():
            raise Exception(
                f"Failed to run DR backup job(Id: {self.dr_jobs_list[-1].job_id})"
                f" with JPR: {self.dr_jobs_list[-1].delay_reason}")
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) completed.")

        self.log.info("Enabling Encryption on CommserveDR Policy Primary Copy: GOST 256")
        self.storage_policy = self.commcell.storage_policies.get("CommserveDR")
        self.storage_policy_copy = self.storage_policy.get_copy("Primary")
        self.storage_policy_copy.set_encryption_properties(
                    re_encryption=True, encryption_type="GOST", encryption_length=256)

        self.log.info("Running DR Backup now")
        self.dr_obj.backup_type = 'full'
        self.dr_jobs_list.append(self.dr_obj.disaster_recovery_backup())
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) started. Waiting for it to complete.")
        if not self.dr_jobs_list[-1].wait_for_completion():
            raise Exception(
                f"Failed to run DR backup job(Id: {self.dr_jobs_list[-1].job_id})"
                f" with JPR: {self.dr_jobs_list[-1].delay_reason}")
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) completed.")

    def upgrade_steps(self):
        """
        Perform the Upgrade of CV
        """
        self.log.info("Fetching details of latest recut for SP: %s and starting download software job",
                      self.tcinputs.get('ServicePack'))
        _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get('ServicePack'))
        latest_cu = 0
        if not self.tcinputs.get('CUPack'):
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
        job_obj = self.commcell.download_software(
            options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
            os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value],
            service_pack=self.tcinputs.get("ServicePack"),
            cu_number=self.tcinputs.get('CUPack', latest_cu))
        self.log.info("Download Software Job: %s started", job_obj.job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Download Software Job: %s failed with JPR: %s", job_obj.job_id, job_obj.delay_reason)
        self.log.info("Download Software Job: %s completed", job_obj.job_id)

        self.log.info(f"Starting Service pack upgrade of CS from SP %s to %s",
                      str(self.commcell.commserv_version), self.tcinputs.get('ServicePack'))
        self.update_helper.push_sp_upgrade(client_computers=[self.commcell.commserv_name])
        self.log.info("SP upgrade of CS successful")

        self.log.info("Checking Readiness of the CS machine")
        _commserv_client = self.commcell.commserv_client
        if _commserv_client.is_ready:
            self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Check Readiness Failed")
            raise Exception("Check readiness for CS after upgrade.")

        self.log.info(f"Starting Service pack upgrade of MA {self.tcinputs.get('MediaAgentName')} from SP %s to %s",
                      str(self.commcell.commserv_version), self.tcinputs.get('ServicePack'))
        self.update_helper.push_sp_upgrade(client_computers=[self.tcinputs.get('MediaAgentName')])
        self.log.info("SP upgrade of MAs successful")

    def post_upgrade_validations(self):
        """
        Validates required functionality after upgrade is finished
        """
        self.log.info("Starting Validations post Upgrade")

        self.log.info("Running DR Backup now")
        self.dr_obj.backup_type = 'full'
        self.dr_jobs_list.append(self.dr_obj.disaster_recovery_backup())
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) started. Waiting for it to complete.")
        if not self.dr_jobs_list[-1].wait_for_completion():
            raise Exception(
                f"Failed to run DR backup job(Id: {self.dr_jobs_list[-1].job_id})"
                f" with JPR: {self.dr_jobs_list[-1].delay_reason}")
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) completed.")

        self.log.info("Changing Encryption on CommserveDR Policy Primary Copy: DES3 192")
        self.storage_policy_copy.set_encryption_properties(
            re_encryption=True, encryption_type="DES3", encryption_length=192)

        self.log.info("Running DR Backup now")
        self.dr_obj.backup_type = 'full'
        self.dr_jobs_list.append(self.dr_obj.disaster_recovery_backup())
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) started. Waiting for it to complete.")
        if not self.dr_jobs_list[-1].wait_for_completion():
            raise Exception(
                f"Failed to run DR backup job(Id: {self.dr_jobs_list[-1].job_id})"
                f" with JPR: {self.dr_jobs_list[-1].delay_reason}")
        self.log.info(f"DR Backup Job(Id: {self.dr_jobs_list[-1].job_id}) completed.")

        self.storage_policy_copy._copy_properties["copyFlags"]["archiveCheckBitmap"] = 1
        self.storage_policy_copy._set_copy_properties()

        self.log.info("Running Data Verification on CommserveDR Primary Copy")
        dv1_job = self.storage_policy.run_data_verification(copy_name='Primary', jobs_to_verify='ALL')
        if not dv1_job.wait_for_completion() or dv1_job.status.lower() != 'completed':
            raise Exception(
                f"DV1 job(Id: {dv1_job.job_id}) did not complete with any errors. JPR: {dv1_job.delay_reason}")
        self.log.info(f"DV1 Job(Id: {dv1_job.job_id}) completed without any errors.")

        self.log.info("All Validations completed")

    def run(self):
        """Main function for test case execution"""
        try:
            self.pre_upgrade_steps()
            self.upgrade_steps()
            self.post_upgrade_validations()
        except Exception as exp:
            self.log.error('TC Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging.")
        else:
            self.log.info("TC Passed.")
