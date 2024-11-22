# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

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
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Metallic.hubutils import HubManagement
import time
import datetime
from cvpysdk.commcell import Commcell
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
import json


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Azure backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic basic acceptance test for Azure"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.company_prefix = "VSA-Automation-Azure-"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.unique_param = None
        self.utils = TestCaseUtils(self)

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
            decorative_log("Initializing browser objects")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.hub_management = HubManagement(
                testcase_instance=self,
                commcell=self.commcell.webconsole_hostname
            )
            self.hub_management.cleanup_tenants(filter=self.company_prefix)
            company_list = []
            for comp in company_list:
                self.hub_management.deactivate_tenant(tenant_name=comp)
                self.hub_management.delete_tenant(tenant_name=comp)
            self.tcinputs['RestoreOptions'] = json.loads(self.tcinputs['RestoreOptions'])
            if self.tcinputs['existingHypervisor'] == "false" or self.tcinputs['existingHypervisor'] == "False":
                self.tcinputs['existingHypervisor'] = False
            if self.tcinputs['snapBackup'] == "false" or self.tcinputs['snapRestore'] == "false":
                self.tcinputs['snapBackup'] = False
                self.tcinputs['snapRestore'] = False
            self.create_tenant()
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
            commcell_info = {}
            self.commcell = Commcell(self.commcell.webconsole_hostname, self.cs_user,
                                     self.inputJSONnode['commcell']['commcellPassword'])
            commcell_info['commcell'] = self.commcell
            commcell_info['user'] = self.cs_user
            commcell_info['password'] = self.inputJSONnode['commcell']['commcellPassword']
            import base64
            commcell_info['encrypted_password'] = base64.b64encode(commcell_info['password'].encode('ascii')).decode(
                'utf-8')
            self.vsa_metallic_helper = VSAMetallicHelper.getInstance(self.admin_console, tcinputs=self.tcinputs,
                                                                     commcell_info=commcell_info)
            if not self.unique_param:
                self.unique_param = self.company_name[len(self.company_prefix):]
            self.vsa_metallic_helper.metallic_options.BYOS = False
            self.vsa_metallic_helper.metallic_options.unique_param = self.unique_param
            self.vsa_metallic_helper.metallic_options.hyp_client_name = self.vsa_metallic_helper.metallic_options.hyp_client_name + self.unique_param
            self.vsa_metallic_helper.metallic_options.opt_new_plan = self.vsa_metallic_helper.metallic_options.opt_new_plan + self.unique_param
            self.vsa_metallic_helper.metallic_options.hyp_credential_name = self.vsa_metallic_helper.metallic_options.hyp_credential_name + self.unique_param

            self.vsa_metallic_helper.hub = True
            try:
                self.vsa_metallic_helper.configure_metallic()
                pass
            except Exception as exp:
                if self.browser:
                    Browser.close_silently(self.browser)
                self.log.exception(exp)
                handle_testcase_exception(self, exp)
                raise Exception(exp)

            self.tcinputs['ClientName'] = self.vsa_metallic_helper.metallic_options.hyp_client_name
            self.reinitialize_testcase_info()
            decorative_log("Creating an object for Virtual Server helper")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb,
                                                     **{"metallic_ring_info": metallic_ring_info, 'is_metallic':True, "BYOS":False})
            self.vsa_obj.is_metallic = True
            self.vsa_obj.is_cloud = True
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.restore_proxy_input = None
            self.vsa_obj.auto_vsa_subclient = subclient_initialize(self, **{'is_metallic': True,
                                                                            "metallic_ring_info": metallic_ring_info,
                                                                            "BYOS": False})

            self.vsa_obj.testcase_obj = self
            self.utils.copy_config_options(self.vsa_obj, "RestoreOptions")
        except Exception as exp:
            if self.browser:
                Browser.close_silently(self.browser)
            handle_testcase_exception(self, exp)
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
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
            if self.status == constants.PASSED:
                self.hub_management.deactivate_tenant(self.company_name)
                self.hub_management.delete_tenant(self.company_name)
        except Exception as exp:
            self.log.exception(exp)
        finally:
            if self.vsa_metallic_helper:
                self.vsa_metallic_helper.resetInstance()
