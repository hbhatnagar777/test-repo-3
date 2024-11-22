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
    """ CLass to validate basic acceptance cases for Loopy"""
    test_step = TestStep()

    def __init__(self):
        """ init method"""
        super(TestCase, self).__init__()
        self.name = "Loopy acceptance case"
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
        self.log.info(self.company_name)
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

    def run(self):
        self.init_tc()
        self.helper = MetallicHelper(self.commcell)
        self.helper.add_CloudServiceUrl('http://' + self.tcinputs['cloud_webconsole_hostname'] + '/webconsole')
        self.helper.add_enableCompanyLinking(False)
        self.create_company(self.metallic_obj)
        self.cloud_company = self.company_name
        self.create_user(self.metallic_obj, self.cloud_company)

        self.helper.metallic_linking(self.tcinputs['cloud_webconsole_hostname'],
                                     self.cloud_company + "\\TA",
                                     self.tcinputs['cloud_admin_password'])

        self.metallic_helper_obj = MetallicHelper(self.metallic_obj)

        self.helper.validate_linking(self.cloud_company, self.metallic_helper_obj, True, False)

        self.helper.is_switcher_available(self.tcinputs['cloud_webconsole_hostname'])

        self.helper.metallic_nav()
        try:
            self.helper.get_completed_solutions()
        except:
            self.log.info("get_completed_solutions Failed")

        self.helper.metallic_unlink()
        self.helper.validate_linking(self.cloud_company, self.metallic_helper_obj,
                                     is_linking=False,
                                     is_company_to_company_linking=False)
        self.log.info("3. Done!")
