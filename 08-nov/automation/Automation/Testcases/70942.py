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

import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.mongodb_helper import MongoDBHelper
from Server.organizationhelper import OrganizationHelper

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
        self.name = "Company details caching validations"
        self.tcinputs = {
            "mongo_password": ""
        }
        self.MONGO_DB_NAME = "CommcellEntityCache"
        self.COMPANY_DETAILS_CACHE_COLLECTION = "CompanyDetails"

    def setup(self):
        """Setup function of this test case."""
        self.default_webserver_name, self.default_webserver_hostname = MongoDBHelper.get_default_webserver(self.csdb)
        
        self.mongo_util = MongoDBHelper(
            self.commcell, 
            self.default_webserver_hostname, 
            self.tcinputs["mongo_password"]
        ).mongodb
        
        self.collection = self.mongo_util.collection_object(
            self.MONGO_DB_NAME, 
            self.COMPANY_DETAILS_CACHE_COLLECTION
        )

    def run(self):
        """Run function of this test case."""
        retries = 3
        attempt_count = 0
        
        while retries > 0:
            try:
                self.execute_testcase()
                break
            except Exception as exp:
                self.log.error('Failed to execute test case with error: %s', exp)
                retries -= 1
                attempt_count += 1
                if retries == 0:
                    self.result_string = str(exp)
                    self.status = constants.FAILED
                    raise

        self.status = constants.PASSED
        self.result_string = "All validations passed successfully!"
        
        if attempt_count > 0:
            self.result_string = f"{self.result_string} (Attempted {attempt_count} times)"

    def teardown(self):
        """Tear down function of this test case."""
        OrganizationHelper(self.commcell).cleanup_orgs(
            marker=f'TestCompanyDetailsCache_{self.id}'
        )

    def execute_testcase(self):
        """Execute the test case."""
        # Create a company and validate the presence of company details cache
        company_name = f"TestCompanyDetailsCache_{self.id}_{random.randint(1, 1000)}"
        self.company = OrganizationHelper(self.commcell).create(name=company_name)
        self.document_query = {"_id": str(self.company.organization_id)}

        self.log.info(
            "While creating company via SDK, we already make GET ORG api call.. "
            "lets check if company details are cached on first api call.."
        )
        self.validate_company_cache_presence()

        # Delete company from the cache and check if it gets re-cached on next api call
        self.log.info("Delete company from the cache and check if it gets re-cached on next api call..")
        self.mongo_util.delete_document(self.collection, self.document_query)
        self.company.refresh()  # Not hard refresh, normal GET API call
        self.validate_company_cache_presence()

        # Corrupt the cache and check if it gets corrected on performing hard refresh
        self.log.info("Corrupt the cache and check if it gets corrected on performing hard refresh..")
        self.corrupt_company_cache()
        self.company.refresh()  # get the latest company details

        if self.company.organization_name.lower() == company_name.lower():
            raise Exception("Company details were not corrupted properly! API call returned correct company name.")

        self.company.refresh(hardRefresh=True)  # Hard refresh
        self.validate_company_cache_presence()
        
        # Edit the company and check if cache is updated
        self.log.info("Edit the company and check if cache is updated..")
        self.company.organization_name = f"{self.company.organization_name}_Updated"
        # sleep(5) # if we don't sleep, sometimes we might get error saying "Company details were not cached"
        self.company.refresh() # cache gets populate with this call
        self.validate_company_cache_presence()

        # Delete the company and check if cache is deleted
        self.log.info("Delete the company and check if cache is deleted..")
        self.commcell.organizations.refresh()
        self.commcell.organizations.delete(name=self.company.organization_name)
        document = self.mongo_util.get_document(self.collection, self.document_query)
        if document:
            raise Exception("Company details cache was not deleted!")

        self.log.info("All validations passed successfully!")

    def validate_company_cache_presence(self):
        """Validate the presence of company details cache."""
        document = self.mongo_util.get_document(self.collection, self.document_query)

        if not document:
            raise Exception("Company details were not cached!")

        company_name_from_cache = document.get("organizationInfo", {}).get("organization", {}).get("connectName", "")
        if company_name_from_cache.lower() != self.company.organization_name.lower():
            raise Exception(
                f"Cache Found but Company details are not matching!. "
                f"Expected: {self.company.organization_name}, Actual: {company_name_from_cache}"
            )

        self.log.info("Company details are cached successfully!")

    def corrupt_company_cache(self):
        """Corrupt the company details cache."""
        random_company_name = f"CorruptedName{random.randint(1, 1000)}"
        self.log.info(f"Updating company name in cache to corrupt it.. : [{random_company_name}]")

        update = {"$set": {"organizationInfo.organization.connectName": random_company_name}}
        self.mongo_util.update_document(self.collection, self.document_query, update)

        updated_document = self.mongo_util.get_document(self.collection, self.document_query)
        company_name_from_cache = updated_document.get("organizationInfo", {}).get("organization", {}).get("connectName", "")

        if company_name_from_cache.lower() != random_company_name.lower():
            raise Exception(
                f"Failed to corrupt the cache. Expected: {random_company_name}, Actual: {company_name_from_cache}"
            )

        self.log.info(
            f"Cache is corrupted successfully! Company name in cache: {company_name_from_cache} "
            f"but actual: {self.company.organization_name}"
        )
