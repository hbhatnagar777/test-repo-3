# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    run()                   --  Main function for this testcase

    create_company()        --  Creates company on the commcell

    create_user()           --  Creates Tenant admin user


TestCase Inputs:
    {
       
        "cloud_webconsole_hostname" : str     -   Cloud webconsole hostname
        "cloud_admin"               : str     -   Cloud CS master group username
        "cloud_admin_password"      : str     -   Cloud CS master group user's password
    }

"""

from datetime import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.metallichelper import MetallicHelper
from Web.Common.page_object import TestStep
from Server.Security.userhelper import UserHelper
from SErver.organizationhelper import OrganizationHelper


class TestCase(CVTestCase):
    """ CLass to validate basic acceptance cases for Neo"""
    test_step = TestStep()

    def __init__(self):
        """ init method"""
        super(TestCase, self).__init__()
        self.name = "Neo acceptance case"
        self.metallic_obj = None
        self.tcinputs = {
            "cloud_webconsole_hostname": None,
            "cloud_admin": None,
            "cloud_admin_password": None
        }

    def init_tc(self):
        """ Initial configuration for the test case."""
        self.metallic_obj = Commcell(self.tcinputs['cloud_webconsole_hostname'],
                                     commcell_username=self.tcinputs['cloud_admin'],
                                     commcell_password=self.tcinputs['cloud_admin_password'])

    def create_company(self, commcell_obj):
        """
        Adds organisation
        Args:
            commcell_obj (object)   : commcell object of the commcell where company needs to be created
         """
        self.orghelper = OrganizationHelper(commcell_obj)
        self.company_name = "Company" + "_" + str(datetime.today().microsecond)
        contact_name = "User" + str(datetime.today().microsecond)
        self.log.info("Creating company with name: " + self.company_name)
        self.orghelper.create(name=self.company_name,
        email=contact_name + '@cv.in', 
        contact_name=contact_name, 
        company_alias=self.company_name)

    def create_user(self, commcell_obj, company):
        """ 
        Creating a Tenant admin user for an organisation
        Args:
            commcell_obj (object)   : commcell object of the commcell where user needs to be created
            company (str)           : Name of the company where Tenant admin user has to be created
        """
        self.userhelper = UserHelper(commcell_obj)
        self.userhelper.create_user(company + "\\TA",
                      company + "TA@cv.in",
                      password=self.tcinputs['cloud_admin_password'],
                      local_usergroups=[company + "\\" + "Tenant Admin"])
        self.log.info("Created Tenant Admin user in above company")

    def run(self):
        self.init_tc()
        self.helper = MetallicHelper(self.commcell)
        self.helper.add_CloudServiceUrl('http://' + self.tcinputs['cloud_webconsole_hostname'] + '/webconsole')
        self.helper.add_enableCompanyLinking(True)

        self.create_company(self.commcell)
        self.onprem_company = self.company_name
        self.create_user(self.commcell, self.onprem_company)

        self.create_company(self.metallic_obj)
        self.cloud_company = self.company_name
        self.create_user(self.metallic_obj, self.cloud_company)

        onprem_ta_user_obj = Commcell(self.commcell.webconsole_hostname,
                                      self.onprem_company + "\\TA",
                                      self.tcinputs['cloud_admin_password'])

        self.helper2 = MetallicHelper(onprem_ta_user_obj)

        self.helper.metallic_linking(self.tcinputs['cloud_webconsole_hostname'],
                                     self.cloud_company + "\\TA",
                                     self.tcinputs['cloud_admin_password'],
                                     self.onprem_company)

        self.metallic_helper_obj = MetallicHelper(self.metallic_obj)

        self.helper.validate_linking(self.cloud_company, self.metallic_helper_obj, True, True, self.onprem_company,
                                    self.helper2)

        self.helper2.is_switcher_available(self.tcinputs['cloud_webconsole_hostname'])

        self.helper2.metallic_nav()

        self.helper.get_completed_solutions(True, onprem_ta_user_obj, self.onprem_company)

        self.helper2.metallic_unlink()

        self.helper.validate_linking(self.cloud_company, self.metallic_helper_obj, False, True, self.onprem_company,
                                     self.helper2)

        self.log.info("3. Done!")

