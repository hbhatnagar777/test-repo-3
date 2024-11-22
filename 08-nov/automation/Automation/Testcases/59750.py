# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

APIs being validated inside collection file:
    GET /company/{{organizationId}}/associatedentities

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- function to call helper function for executing collection file using newman
"""
from queue import Queue
from threading import Thread

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI.restapihelper import RESTAPIHelper
from Server.organizationhelper import OrganizationHelper
from Server.serverhelper import ServerTestCases
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing AssociatedEntities REST API for a company"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Companies - Associated entities count"
        self.laptop = None
        self.tcinputs = {
            "machine_host": None,
            "machine_username": None,
            "machine_password": None,
            "machine_host_laptop": None,
            "machine_username_laptop": None,
            "machine_password_laptop": None
        }


    def setup(self):
        """Setup function of this test case"""
        self.config_json = get_config()
        self.password = self.config_json.MSPCompany.tenant_password
        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password=self.password,
                                                                     to_password=self.password)
        self.company_name = self.infos['company_name']
        self.ta_commcell = self.infos['ta_loginobj']

        self.machine_name = self.config_json.Install.windows_client.machine_host if not self.tcinputs else \
            self.tcinputs['machine_host']
        self.machine_username = self.config_json.Install.windows_client.machine_username if not self.tcinputs else \
            self.tcinputs['machine_username']
        self.machine_password = self.config_json.Install.windows_client.machine_password if not self.tcinputs else \
            self.tcinputs['machine_password']

        self.machine_name_laptop = self.tcinputs['machine_host_laptop']
        self.machine_username_laptop = self.tcinputs['machine_username_laptop']
        self.machine_password_laptop = self.tcinputs['machine_password_laptop']

        self.org_helper = OrganizationHelper(commcell=self.commcell, company=self.company_name)
        self.ta_org_helper = OrganizationHelper(self.ta_commcell, company=self.company_name)

        self.uninstall_and_install_laptop()

        self.uninstall_and_install_fs_client()

    def uninstall_and_install_laptop(self):
        """Uninstalls and Re-Installs"""
        try:
            value = {
                'os': 'WINDOWS',
                'machine_hostname': self.machine_name_laptop,
                'machine_username': self.machine_username_laptop,
                'machine_password': self.machine_password_laptop
            }
            self.org_helper.uninstall_client(client_name=self.machine_name_laptop)
            self.ta_org_helper.install_laptop_client(value)
            self.log.info('Laptop Installation Finished!')
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_laptop] : {err}')

    def uninstall_and_install_fs_client(self):
        """Uninstalls and Re-Installs"""
        try:
            self.org_helper.uninstall_client(client_name=self.machine_name)
            self.ta_org_helper.install_client(hostname=self.machine_name,
                                              username=self.machine_username,
                                              password=self.machine_password)
            self.log.info('FS Client Installation Finished!')
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_fs_client] : {err}')

    def run(self):
        """Main function for test case execution"""
        try:
            api_count = self.org_helper.associated_entities_count()
            DB_count = self.org_helper.get_company_entities()
            if api_count != DB_count:
                raise Exception(f"Entities count from API: {api_count} is not same as from DB: {DB_count}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.infos:
            self.commcell.users.delete(user_name=self.infos['to_name'], new_user='admin')
            msp_orghelper_obj = OrganizationHelper(self.commcell, self.company_name)
            msp_orghelper_obj.delete_company(wait=True)
