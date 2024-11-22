# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: This test case verifies vm provisioning setting is functional and enabling auto-scale works from a Tenant Account
TestCase: Class for executing this test case

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.AutoScaleUtils import AutoScaleValidation
from VirtualServer.VSAUtils.VirtualServerHelper import (
    AutoVSACommcell,
    AutoVSAVSClient,
    AutoVSAVSInstance,
    AutoVSABackupset,
    AutoVSASubclient
)
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from VirtualServer.VSAUtils import VsaTestCaseUtils, OptionsHelper


class TestCase(CVTestCase):
    """This class is used to validate auto-scale settings for Snap Backup"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()

        self.vsa_commcell = None
        self.name = "Command Center : Auto scale configuration for Streaming Backup from Tenant Account"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAMAZON,
                                                          self.features_list.DATAPROTECTION)
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.hypervisor_details = None
        self.hypervisor_page = None
        self.vm_provisioning_options = None
        self.auto_scale_obj = None
        self.auto_scale_jobs = None
        self.is_tenant = True
        self.utils = TestCaseUtils(self)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            decorative_log("Initializing browser objects")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            decorative_log("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.wait_for_completion()

            self.hypervisor_page = Hypervisors(self.admin_console)
            self.hypervisor_details = HypervisorDetails(self.admin_console)

            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)

            self.vm_provisioning_options = {'server_group': self.tcinputs.get('ServerGroup', None),
                                            'iam_role': self.tcinputs.get('IAMRole', None),
                                            'vm_size': self.tcinputs.get('VMSize', None),
                                            'create_public_ip': self.tcinputs.get('CreatePublicIP', None),
                                            'default_vpc': self.tcinputs.get('DefaultVPC', None),
                                            'system_default_settings': self.tcinputs.get('SetAsSystemDefaultSetting',
                                                                                         None),
                                            'availability_zone': self.tcinputs.get('AvailabilityZone', None),
                                            'proxy_os': self.tcinputs.get('ProxyOperatingSystem'),
                                            'custom_image': self.tcinputs.get("CustomImage", None),
                                            'VPC': self.tcinputs.get("VPC", None),
                                            'security_group': self.tcinputs.get("SecurityGroup", None),
                                            'subnet': self.tcinputs.get("Subnet", None),
                                            'AccessNodeSettings': self.tcinputs.get("AccessNodeSettings", None),
                                            'NetworkGateway': self.tcinputs.get("NetworkGateway", None),
                                            'AutoScaleMaxNoOfVMs': self.tcinputs.get("AutoScaleMaxNoOfVMs", None),
                                            'AutoScaleNodeOS': self.tcinputs.get("AutoScaleNodeOS", None),
                                            'AZSpecificInfo': self.tcinputs.get("AZSpecificInfo", []),
                                            'HypervisorName': self.tcinputs.get("InstanceName", None)
                                            }

            self.client = self.commcell.clients.get(self.tcinputs['ClientName'])
            self.agent = self.client.agents.get(self.tcinputs['AgentName'])
            self.instance = self.agent.instances.get(self.tcinputs['InstanceName'])
            self.backupset = self.instance.backupsets.get(self.tcinputs['BackupsetName'])
            self.subclient = self.backupset.subclients.get(self.tcinputs['SubclientName'])

            self.auto_vsa_client = AutoVSAVSClient(self.vsa_commcell, self.client)
            self.auto_vsa_instance = AutoVSAVSInstance(self.auto_vsa_client,
                                                       self.agent, self.instance)
            self.auto_vsa_backupset = AutoVSABackupset(self.auto_vsa_instance, self.backupset)
            self.auto_vsa_subclient = AutoVSASubclient(self.auto_vsa_backupset, self.subclient)

            _ = self.tc_utils.initialize(self)

        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    def run(self):
        """Runs the testcase in order"""
        try:
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_page.select_hypervisor(self.tcinputs["ClientName"])
            self.admin_console.select_configuration_tab()

            # Configure VM Provision Options
            self.hypervisor_details.configure_vm_provisioning(self.vm_provisioning_options, is_autoscale=True)

            # Validate VM Provision
            self.auto_scale_obj = AutoScaleValidation(self.tc_utils.sub_client_obj)
            self.auto_scale_obj.is_tenant = True
            self.auto_scale_obj.validate_auto_scale_settings(self.vm_provisioning_options)

            # Backup Job
            try:
                backup_option = OptionsHelper.BackupOptions(self.auto_vsa_subclient)
                backup_option.backup_type = 'FULL'
                self.auto_scale_obj.start_backup_job(backup_option)
                suspend_resume = False
                while not self.auto_scale_obj.backup_job.is_finished:
                    time.sleep(180)
                    self.auto_scale_jobs = self.vsa_commcell.get_vm_management_jobs(
                        self.auto_scale_obj.backup_job.job_id)
                    if self.auto_scale_jobs:
                        self.log.info(
                            f"VMManagement jobs {self.auto_scale_jobs} have been "
                            f"started by Backup Job  {self.auto_scale_obj.backup_job.job_id}. "
                            f"Waiting for jobs to complete.")

                        if self.auto_scale_obj.wait_for_vm_management_child_jobs_to_complete():
                            self.log.info(
                                f"VM Management Jobs {self.auto_scale_jobs} completed. Waiting for backup job to "
                                f"complete")
                            # VMManagement jobs have completed, now pause and resume the backup job
                            if not suspend_resume:
                                self.auto_scale_obj.backup_job.pause(True)
                                self.log.info(f"Backup Job {self.auto_scale_obj.backup_job.job_id} paused")
                                self.auto_scale_obj.backup_job.resume(True)
                                self.log.info(f"Backup Job {self.auto_scale_obj.backup_job.job_id} resumed")
                                suspend_resume = True

                        else:
                            raise Exception("One or more VMManagement jobs failed. Please check logs for more info.")
                    else:
                        self.log.info(
                            f"No VMManagement job has been started by Backup Job  {self.auto_scale_obj.backup_job.job_id}. "
                            f"Will retry after 3 minutes.")

                if not self.auto_scale_jobs:
                    raise Exception(f"No Auto-Scale job has been started by Backup Job "
                                    f"{self.auto_scale_obj.backup_job.job_id}")

                self.log.info("Backup completed. starting validation")

                auto_scale_utils_obj = self.auto_scale_obj
                auto_scale_utils_obj.post_backup_validation()
                if auto_scale_utils_obj.validator_error_string:
                    raise Exception("Error while performing post backup validation : {0}".format(
                        auto_scale_utils_obj.validator_error_string))
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        decorative_log("Tear Down Started")
        self.browser.close()
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
