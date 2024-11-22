# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    tear_down()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from VirtualServer.VSAUtils import OptionsHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Metallic.hubutils import HubManagement
import time, os
import datetime
from cvpysdk.commcell import Commcell
from cvpysdk.organization import Organization


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic basic acceptance test for Nutanix-AHV"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.unique_param = None
        self.company_prefix = "VSA-Automation-Nutanix-"

    def create_tenant(self):
        """
        Create a new tenant for the automation
        """
        date_info = datetime.datetime.now()
        self.company_name = date_info.strftime(self.company_prefix + "%d-%B-%H-%M")
        self.unique_param = date_info.strftime("%d-%B-%H-%M")
        user_firstname = "VSA" + str(int(time.time()))
        user_lastname = "user"
        user_email = user_firstname + user_lastname + '@domain.com'
        user_phonenumber = '00000000'
        user_country = self.tcinputs.get("UserCountry", "United States")
        self.log.info(f"Creating Tenant with Company name {self.company_name}")
        # Create a tenant and get password that is returned
        self.cs_user = self.hub_management.create_tenant(
            company_name=self.company_name,
            email=user_email,
            first_name=user_firstname,
            last_name=user_lastname,
            phone_number=user_phonenumber,
            country=user_country
        )

    def setup(self):
        try:
            if not self.unique_param:
                date_info = datetime.datetime.now()
                self.unique_param = date_info.strftime("%d-%B-%H-%M")
            self.tcinputs['storagePath'] += self.unique_param
            self.tcinputs['optNewPlan'] += self.unique_param
            self.tcinputs['newStorageName'] += self.unique_param
            self.tcinputs['hypCredentialName'] += self.unique_param
            self.tcinputs['hyp_client_name'] += self.unique_param
            self.tcinputs['SubclientName'] += self.unique_param
            decorative_log("Initializing browser objects")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            download_path = os.path.join(constants.TEMP_DIR, CCVMKubernetesTypes.nutanix.split()[0])
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            self.browser.set_downloads_dir(download_path)
            self.browser.open()
            self.hub_management = HubManagement(
                testcase_instance=self,
                commcell=self.commcell.webconsole_hostname
            )
            company_list = []
            for comp in company_list:
                self.hub_management.deactivate_tenant(tenant_name=comp)
                self.hub_management.delete_tenant(tenant_name=comp)
            self.hub_management.cleanup_tenants(filter=self.company_prefix)
            self.create_tenant()
            # self.company_name = 'VSA-Automation-Nutanix-12-February-01-50'
            # self.cs_user = 'VSA-Automation-Nutanix-12-February-01-50\\uat'
            decorative_log("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.cs_user,
                                     self.inputJSONnode['commcell']['commcellPassword']
                                     )
            metallic_ring_info = {
                "commcell": self.inputJSONnode['commcell']["webconsoleHostname"],
                "user": self.inputJSONnode['commcell']['commcellUsername'],
                "password": self.inputJSONnode['commcell']['commcellPassword']
            }
            cs_creds = {}
            self.commcell = Commcell(self.commcell.webconsole_hostname, self.cs_user,
                                     self.inputJSONnode['commcell']['commcellPassword'])
            cs_creds['commcell'] = self.commcell
            cs_creds['user'] = self.cs_user
            cs_creds['password'] = self.inputJSONnode['commcell']['commcellPassword']
            import base64
            cs_creds['encrypted_password'] = base64.b64encode(cs_creds['password'].encode('ascii')).decode('utf-8')
            self.vsa_metallic_helper = VSAMetallicHelper.getInstance(self.admin_console, self.tcinputs, cs_creds)
            self.vsa_metallic_helper.organization = Organization(self.commcell, self.company_name)
            self.vsa_metallic_helper.hub = True
            try:
                self.cleanup_access_nodes()
            except Exception as exp:
                self.log.exception(exp)
            try:
                self.vsa_metallic_helper.configure_metallic()
                # pass
            except Exception as exp:
                self.log.exception(exp)
                handle_testcase_exception(self, exp)
                raise Exception(exp)

            hyp_client = self.tcinputs['hyp_client_name']
            self.tcinputs['ClientName'] = hyp_client
            self.reinitialize_testcase_info()
            decorative_log("Creating an object for Virtual Server helper")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb,
                                                     **{'is_metallic': True, "metallic_ring_info": metallic_ring_info})
            self.vsa_obj.is_metallic = True
            self.vsa_obj.is_cloud = False
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.restore_network = self.tcinputs['network']
            self.vsa_obj.storage_container = self.tcinputs['storageContainer']
            self.vsa_obj.restore_proxy_input = self.tcinputs['restoreProxy']
            self.vsa_obj.auto_vsa_subclient = subclient_initialize(self, **{'is_metallic': True,
                                                                            "metallic_ring_info": metallic_ring_info})
            self.vsa_obj.testcase_obj = self
        except Exception as exp:
            if self.browser:
                Browser.close_silently(self.browser)
            self.log.exception(exp)
            handle_testcase_exception(self, exp)
            if self.vsa_metallic_helper:
                self.vsa_metallic_helper.resetInstance()
            raise Exception(exp)

    def run(self):
        """Main function for test case execution"""

        try:
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log("Performing full VM restore from subclient level")
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)

    def cleanup_access_nodes(self):
        """
        cleans up the instance on the access_nodes
        """
        access_node_details = {
            'name': self.vsa_metallic_helper.metallic_options.backup_gatewayname,
            'username': self.vsa_metallic_helper.metallic_options.remote_username,
            'password': self.vsa_metallic_helper.metallic_options.remote_userpassword
        }
        self.vsa_metallic_helper.cleanup_metallic_instance_on_client(machine_details=access_node_details)

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
            if self.status == constants.PASSED:
                self.cleanup_access_nodes()
                self.hub_management.deactivate_tenant(self.company_name)
                self.hub_management.delete_tenant(self.company_name)
        except Exception as exp:
            self.log.exception(exp)
        finally:
            if self.vsa_metallic_helper:
                self.vsa_metallic_helper.resetInstance()
