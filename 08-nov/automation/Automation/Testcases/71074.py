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

    tear_down()     --  tear down function of this test case

Note: Please install pymailtm module before running the case. (temporary use case)

"""

import os
import time
import random
import string
import pymailtm.pymailtm
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from cvpysdk.commcell import Commcell
from cvpysdk.organization import Organization
from CVTrials import saas_trial
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import subclient_initialize
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from Web.Common.exceptions import CVTestStepFailure
from Metallic.hubutils import HubManagement
from Server.Security.userhelper import UserHelper


class TestCase(CVTestCase):
    """Class for registering commvault trial package"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Saas trial - Complete on-boarding validation"
        self.helper_api = None
        self.helper_ui = None
        self.browser = None
        self.company_name = None
        self.tenant_user = None
        self.unique_param = None
        self.email = None
        self.mail_box = None
        self.config = None
        self.account = None
        self.hub_management = None
        self.admin_console = None
        self.vsa_obj = None
        self.vsa_metallic_helper = None
        self.user_helper = None
        self.reset_password_mail = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.helper_api = saas_trial.SaasTrial(lh_env=self.config.Cloud.host_name,
                                               user=self.config.Cloud.username,
                                               password=self.config.Cloud.password)
        self.helper_ui = saas_trial.SaasTrialUI(url=self.tcinputs['trial_url'])
        self.user_helper = UserHelper(commcell=self.commcell)

        self.hub_management = HubManagement(
            testcase_instance=self,
            commcell=self.commcell.webconsole_hostname
        )
        unique_suffix = ''.join(random.choices(string.ascii_lowercase, k=7))
        self.company_name = f'saas-trial-automation-{unique_suffix}'

        self.log.info('Generating temporary email account...')
        self.initialize_mail_account()
        if not self.email:
            raise Exception("Failed to Create temporary email. Testcase Failed to proceed!")
        self.log.info(f'Email account generated : {self.email}')

        # to be added : instead of third party module, use exchange mailbox to generate emails

        self.tenant_user = r"%s\%s" % (self.company_name, self.email.split("@")[0])

    def run(self):
        """Main function for test case execution"""
        try:
            # Step: 1 :: Register the trial customer with the temp email and onboard the company and tenant
            self.log.info(f'Onboarding test company user with name : {self.company_name} and email : {self.email}...')
            self.onboard_company()

            # step: 2 :: using resetTenantPassword WF reset the password for the tenant admin
            self.log.info(f'resetting password for the new tenant admin {self.tenant_user} of the company '
                          f'{self.company_name}')
            self.user_helper.reset_tenant_admin_password(user_name=self.tenant_user,
                                                         mail_content=self.reset_password_mail,
                                                         password=self.config.Metallic.tenant_password)

            # step: 3 :: Login to Metallic ring and configure virtualization workload
            self.log.info(f'Performing login to metallic ring and configuring virtualization client..')
            self.configure_virtualization()

            # step: 4 :: run backup and restore for the configured VM
            self.log.info("Performing Backup for the Hypervisor...")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
            self.log.info("Backup Successful!")

            self.log.info("Performing Restore for the Hypervisor...")
            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.full_vm_restore()

            self.log.info("Restore Successful!")

        except Exception as exp:
            raise handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.cleanup()
        # To close the browser
        Browser.close_silently(self.browser)

    def initialize_mail_account(self, retries=5, delay=5):
        """Initializes the mail account with retry logic in case of network errors."""
        attempt = 0
        while attempt < retries:
            try:
                self.log.info(f'Trying temp email generation. Attempt : {attempt} ')
                self.mail_box = pymailtm.MailTm()
                self.account = self.mail_box.get_account()
                self.email = self.account.address
                break
            except Exception as e:
                attempt += 1
                self.log.warning(f"Attempt {attempt}/{retries} failed with error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
        else:
            raise Exception("All attempts to initialize the mail account failed.")

    def configure_virtualization(self):
        try:
            self.log.info("Trying login to metallic ring with tenant admin user..")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            download_path = os.path.join(constants.TEMP_DIR, CCVMKubernetesTypes.vmware.split()[0])
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            self.browser.set_downloads_dir(download_path)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tenant_user, self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Successfully logged in!")

            self.log.info(f"creating a temporary commcell object with MSP user "
                          f"{self.inputJSONnode['commcell']['commcellUsername']} for validations")
            metallic_ring_info = {
                "commcell": self.inputJSONnode['commcell']["webconsoleHostname"],
                "user": self.inputJSONnode['commcell']['commcellUsername'],
                "password": self.inputJSONnode['commcell']['commcellPassword']
            }

            self.log.info("Initializing VSA metallic helper to configure virtualizaation workload..")
            cs_creds = {}
            self.commcell = Commcell(self.commcell.webconsole_hostname, self.tenant_user,
                                     self.inputJSONnode['commcell']['commcellPassword'])
            cs_creds['commcell'] = self.commcell
            cs_creds['user'] = self.tenant_user
            cs_creds['password'] = self.inputJSONnode['commcell']['commcellPassword']
            self.vsa_metallic_helper = VSAMetallicHelper.getInstance(admin_console=self.admin_console,
                                                                     tcinputs=self.tcinputs,
                                                                     company=self.company_name,
                                                                     commcell_info=cs_creds)
            self.vsa_metallic_helper.hub = True
            self.vsa_metallic_helper.organization = Organization(self.commcell, self.company_name)

            self.vsa_metallic_helper.metallic_options.access_node_os = self.tcinputs['access_node_os']
            if self.vsa_metallic_helper.metallic_options.access_node_os == 'unix':
                self.vsa_metallic_helper.metallic_options.install_through_authcode = True
                self.vsa_metallic_helper.metallic_options.backup_gatewayname = self.tcinputs['lin_backup_gatewayname']
                self.vsa_metallic_helper.metallic_options.remote_username = self.tcinputs.get('lin_remote_username',
                                                                                              'root')
                self.vsa_metallic_helper.metallic_options.remote_userpassword = self.tcinputs['lin_remote_userpassword']
                self.vsa_metallic_helper.metallic_options.storage_backup_gateway = self.tcinputs[
                    'lin_backup_gatewayname']
                self.vsa_metallic_helper.metallic_options.storage_path = self.tcinputs['lin_storagePath']
                self.vsa_metallic_helper.metallic_options.testcase = self
            else:
                self.vsa_metallic_helper.metallic_options.storage_backup_gateway = (
                    self.vsa_metallic_helper.metallic_options.backup_gatewayname.split('.'))[0]

            self.vsa_metallic_helper.metallic_options.skip_cloud_storage = True

            if not self.unique_param:
                self.unique_param = self.company_name[15:]
            self.vsa_metallic_helper.metallic_options.unique_param = self.unique_param
            self.vsa_metallic_helper.metallic_options.new_storage_name = (
                    self.vsa_metallic_helper.metallic_options.new_storage_name + self.unique_param)
            self.vsa_metallic_helper.metallic_options.hyp_client_name = (
                    self.vsa_metallic_helper.metallic_options.hyp_client_name + self.unique_param)
            self.vsa_metallic_helper.metallic_options.opt_new_plan = (
                    self.vsa_metallic_helper.metallic_options.opt_new_plan + self.unique_param)
            self.vsa_metallic_helper.metallic_options.hyp_credential_name = (
                    self.vsa_metallic_helper.metallic_options.hyp_credential_name + self.unique_param)
            self.vsa_metallic_helper.metallic_options.storage_path = (
                    self.vsa_metallic_helper.metallic_options.storage_path + self.unique_param)
            self.log.info("successfully initialized the helper")

            self.log.info("Starting configuration of Virtualization workload...")
            try:
                self.admin_console.navigator.navigate_to_service_catalogue()
                self.vsa_metallic_helper.configure_metallic()
            except Exception as exp:
                self.log.exception(exp)
                handle_testcase_exception(self, exp)
                raise Exception(exp)
            self.log.info("Successfully configured Virtualization workload!")

            self.log.info("Creating an object for Virtual Server helper...")
            self.tcinputs['ClientName'] = self.vsa_metallic_helper.metallic_options.hyp_client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb,
                                                     **{"metallic_ring_info": metallic_ring_info, "is_metallic": True})
            self.vsa_obj.is_metallic = True
            self.vsa_obj.is_cloud = False
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.restore_proxy_input = None
            self.vsa_obj.auto_vsa_subclient = subclient_initialize(self, **{'is_metallic': True,
                                                                            "metallic_ring_info": metallic_ring_info})
            self.vsa_obj.testcase_obj = self
        except Exception as exp:
            if self.browser:
                Browser.close_silently(self.browser)
                self.log.exception(exp)
                handle_testcase_exception(self, exp)

    def onboard_company(self):
        """method to onboard a trial customer's company"""
        try:
            # Registration and onboarding of the company through LH API
            api_inputs = {
                "companyName": self.company_name,
                "email": self.email,
                "title": "Engineer",
                "firstName": "Saas",
                "lastName": "automation",
                "phone": "870-516-4882",
                "country": "Canada",
                "state": "Quebec",
                "optInForContact": True,
                "utmCampaign": "amer_hybrid-cloud",
                "utmContent": "video",
                "utmMedium": "paidsocial",
                "utmSource": "linkedin",
                "utmTerm": "cv-",
                "trialInterest": [
                    "Metallic Salesforce", "Metallic Database"]
            }
            self.log.info('Onboarding trial customer using API...')
            self.tenant_user = self.helper_api.onboard_user(api_inputs)

            # Registration and on-boarding of the company through UI (pre-production URL)
            # self.log.info(f'On-boarding trial customer using UI {self.tcinputs["trial_url"]}...')
            # self.tenant_user = self.helper_ui.register_to_start_trial(email=self.email, company=self.company_name)

            if not self.tenant_user:
                raise Exception('Failed to onboard the Company.')

            self.log.info(f"Successfully onboarded company! Tenant admin user name : {self.tenant_user}")

            # Mailbox validation
            self.log.info("Starting Mailbox Validation for successful onboarding /Reset password link email..")
            subject = "Welcome to Commvault Cloud!"
            if not self.__check_for_email(subject=subject):
                raise Exception(f'Failed to find the email with subject {subject}')

            self.log.info('Mailbox Validation Successful!')

        except Exception as err:
            raise CVTestStepFailure(err)

    def __check_for_email(self, subject, timeout=300, interval=30):
        """
        Check for an email with a specific subject.
        """
        end_time = time.time() + timeout

        while time.time() < end_time:
            # Fetch messages from the mailbox
            messages = self.account.get_messages()

            for message in messages:
                if message.subject == subject:
                    self.reset_password_mail = message.text
                    return True
            self.log.info(f"Mail not received yet! sleeping for {interval} seconds")
            time.sleep(interval)

        return False

    def cleanup(self):
        """Method to clean up virtualization entities"""
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
        if self.status == constants.PASSED:
            if self.vsa_metallic_helper.metallic_options.access_node_os == 'windows':
                access_node_details = {
                    'name': self.vsa_metallic_helper.metallic_options.backup_gatewayname,
                    'username': self.vsa_metallic_helper.metallic_options.remote_username,
                    'password': self.vsa_metallic_helper.metallic_options.remote_userpassword
                }
                self.vsa_metallic_helper.cleanup_metallic_instance_on_client(machine_details=access_node_details)
            else:
                self.log.info('Cleaning up the backup gateway proxy...')
                if self.vsa_metallic_helper.metallic_options.deploy_helper:
                    self.vsa_metallic_helper.metallic_options.deploy_helper.hvobj.VMs[
                        self.vsa_metallic_helper.metallic_options.storage_backup_gateway].delete_vm()
            self.log.info('Deleting the tenant and the company...')
            self.hub_management.deactivate_tenant(self.company_name)
            self.hub_management.delete_tenant(self.company_name)
