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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from datetime import datetime
import email
from platform import platform
from random import randint
from Server.organizationhelper import OrganizationHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Testcase to populate companies, and create plans, servers, server groups, users and storage to it"
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.company_base_name = "Performance_company"
        self.base_email = "email@test.com"
        self.org_helper = None
        self.password = self.inputJSONnode['commcell']['commcellPassword']

    def run(self):
        """Run function of this test case"""
        try:
            
            n = 2
            for i in range(n):
                self.log.info(f"Creating company {i}")
                company_name = self.company_base_name + str(datetime.now())
                company_alias = "Alias" + company_name
                self.commcell.organizations.add(name = company_name,
                                                email = company_name+self.base_email,
                                                contact_name = self.company_base_name+" Admin",
                                                company_alias = company_alias)

                self.log.info(f"--------------------\n\t\t\tCreated company:\n\t\t\tCompany Name: {company_name}\n\t\t\tCompany Alias: {company_alias}\n")

                self.org_helper = OrganizationHelper(self.commcell, company_name)
                self.log.info("Sharing MSP storage with company")
                self.org_helper.share_random_msp_storage_with_company()
                
                self.commcell.switch_to_company(company_name)
                self.commcell.refresh()

                self.log.info("Creating plans for company with shared storage")
                entity_count = 5
                for i in range(entity_count):
                    try:
                        self.org_helper.create_plan_with_available_resource()
                    except Exception as exp:
                        self.log.info(f"Plan creation failed with {exp}! Moving on")

                self.log.info("Creating server groups for company")
                for i in range(entity_count):
                    try:
                        self.commcell.client_groups.add("Server Group " + str(datetime.now()))
                    except Exception as exp:
                        self.log.info(f"Server group creation failed with {exp}! Moving on")
                
                self.log.info("Creating users for company")
                for i in range(entity_count):
                    try:
                        self.commcell.users.add("company_user_" + str(datetime.now()),
                                            "company_user_" + str(datetime.now()),
                                            password=self.password)
                    except Exception as exp:
                        self.log.info(f"User creation failed with {exp}! Moving on")

                self.commcell.reset_company()

        except Exception as exp:
            handle_testcase_exception(self, exp)
