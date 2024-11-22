# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" This testcase is to validate the creation of dedupe and non dedupe azure cloud storage only via CC

TestCase: Class for executing this test case

    __init__()      --  Initializes test case class object

    init_tc()       -- Initial configuration for the test case

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    create_cloud_storage() -- creates a new cloud storage

    validate_cloud_storage_deletion() -- validates the deletion of cloud storage

    validate_cloud_storage_creation() -- validates the creation of cloud storage

    cleanup()       -- Cleans Up the Entities created in the TC

Sample Input JSON:
    {
      "ClientName": Name of the Client (str),
      "MediaAgent": Name of the mediaAgent (str),
      "CloudContainer": Name of the cloud container (str),
      "StorageClass": - Access tier of the container (str)
                    Refer https://documentation.commvault.com/v11/essential/supported_cloud_storage_products.html
      "region": Name of the geographical region for storage (str)
      "accountName" : name of the storage account (str)
      "CloudCredentials1": Name of the cloud credentials for dedup cloud storage(str)
                            authType-"Access key and Account name"
      "accessKeyId" : access key for storage account ("Access key and Account name" - if cred not saved, mandatory)
      "CloudCredentials2": Name of the cloud credentials for non dedup cloud storage(str)
                            authType- "IAM AD application"
      "tenantId" :  tenant ID of the Azure application ("IAM AD application"- if cred not saved, mandatory)
      "application Id" : application Id of the application ("IAM AD application"- if cred not saved, mandatory)
      "application secret" : secret value for the created secret ("IAM AD application"- if cred not saved, mandatory)
      "cloud_dedup_path" : Cloud Ddb location for unix MA
                        (required - if the MA provided is Unix/Linux, else optional)

      *****In case of Unix/Linux MA, provide LVM enabled dedup paths*****
    }

Steps:

    1) Add dedupe Cloud storage (azure) - Use "Access key and Account name" auth type.
    2) Add non dedupe Cloud storage (azure) - Use "IAM AD authentication" (RBAC) auth type.
    3) Delete both storages

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()

        self.name = 'MM Smoke Test - CC - Azure Cloud Storage Creation'
        self.mm_helper = None
        self.cloud_storage_name1 = None
        self.cloud_storage_name2 = None
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.client_machine = None
        self.ma_machine = None
        self.path = None
        self.cloud_ddb_location1 = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent": None,
            "CloudContainer": None,
            "StorageClass": None,
            "region": None,
            "accountName": None,
            "CloudCredentials1": None,
            "CloudCredentials2": None,
        }
        self.res_string = ""
        self.dedup_provided = False
        self.cred_details2 = {}
        self.cred_details1 = {}
        self.cloudServer = "blob.core.windows.net"
        self.cloudType = "Microsoft Azure Storage"
        self.Authentication1 = "Access key and Account name"
        self.Authentication2 = "IAM AD application"

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Setup function of this test case"""

        self.init_tc()
        self.cloud_storage_name1 = f"Cloud1-{self.id}"
        self.cloud_storage_name2 = f"Cloud2-{self.id}"
        self.mm_helper = MMHelper(self)
        self.storage_helper = StorageMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])

        if self.tcinputs.get('cloud_dedup_path'):
            self.dedup_provided = True

        if "unix" in self.ma_machine.os_info.lower():
            if self.dedup_provided:
                self.log.info('Unix/Linux MA provided, assigning user defined dedup locations')
                self.cloud_ddb_location1 = self.tcinputs['cloud_dedup_path']
            else:
                self.log.error(
                    f"LVM enabled dedup path must be an input for Unix MA {self.tcinputs['MediaAgent']}")
                Browser.close_silently(self.browser)
                raise Exception(
                    f"Please provide LVM enabled dedup path as input for Unix MA {self.tcinputs['MediaAgent']}")
        else:
            if self.dedup_provided:
                self.log.info('Windows MA provided, assigning user defined dedup locations')
                self.cloud_ddb_location1 = self.tcinputs['cloud_dedup_path']
            else:
                self.log.info('Windows MA provided, creating dedup locations')
                ma_drive = options_selector.get_drive(self.ma_machine)
                if ma_drive is None:
                    Browser.close_silently(self.browser)
                    raise Exception("No free space for hosting ddb and mount paths")
                self.log.info('selected drive: %s', ma_drive)
                self.path = self.ma_machine.join_path(ma_drive, f"Smoke_Test_{self.id}")
                self.cloud_ddb_location1 = self.ma_machine.join_path(self.path, 'Cloud_DDB1')

        self.log.info('Ddb location for Cloud: %s', self.cloud_ddb_location1)

    def cleanup(self):
        """Cleans Up the Entities created in the TC"""

        try:
            self.log.info("****************************** Cleanup Started ******************************")

            if self.storage_helper.has_cloud_storage(self.cloud_storage_name1):
                self.log.info(f"Deleting cloud storage {self.cloud_storage_name1}")
                self.storage_helper.delete_cloud_storage(self.cloud_storage_name1)
                self.validate_cloud_storage_deletion(name=self.cloud_storage_name1)

            if self.storage_helper.has_cloud_storage(self.cloud_storage_name2):
                self.log.info(f"Deleting cloud storage {self.cloud_storage_name2}")
                self.storage_helper.delete_cloud_storage(self.cloud_storage_name2)
                self.validate_cloud_storage_deletion(name=self.cloud_storage_name2)
            self.log.info('****************************** Cleanup Completed ******************************')

        except Exception as exe:
            self.res_string += f'Error in Cleanup Reason: {exe} \n'
            self.status = constants.FAILED
            self.log.error(f'Error in Cleanup Reason: {exe}')

    def validate_cloud_storage_deletion(self, name):
        """Validates if storage is deleted or not

            Args:
                name - name of the storage whose deletion needs to be validated

        """

        try:
            exist = self.storage_helper.has_cloud_storage(name)
            if not exist:
                self.log.info(f'Cloud storage {name} does not exist on CC')
            else:
                raise Exception(f'Cloud storage {name} is not deleted, visible on CC')

        except Exception as exp:
            self.res_string += f'Error in validating deletion of cloud storage: {exp} \n'
            self.status = constants.FAILED

    def validate_cloud_storage_creation(self, name):
        """Validates if storage is created or not

            Args:
                name - name of the storage whose creation needs to be validated

        """

        try:
            exist = self.storage_helper.has_cloud_storage(name)
            if exist:
                self.log.info(f'Created cloud storage {name} is being shown on web page')
            else:
                raise Exception(f'Created cloud storage {name} is not displayed on web page')

        except Exception as exp:
            self.res_string += f'Error in validating creation of cloud storage: {exp} \n'
            self.status = constants.FAILED

    def create_cloud_storage(self, storage_name, auth_type=None, dedup_loc=None, cred_name=None, cred_details=None):
        """Creates a new cloud storage

            Args:
                storage_name - name of the storage

                auth_type - authentication type to be used

                dedup_loc - ddb path (provide in case of dedupe only)

                cred_name - name of the credentials to be used while creating storage (if needed)

                cred_details - credential details to be saved (in case, credentials not saved already)

        """

        try:
            self.log.info(f'Creating cloud storage {storage_name}')
            ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name
            self.storage_helper.add_cloud_storage(cloud_storage_name=storage_name, media_agent=ma_name,
                                                  cloud_type=self.cloudType,
                                                  server_host=self.cloudServer,
                                                  auth_type=auth_type,
                                                  container=self.tcinputs['CloudContainer'],
                                                  storage_class=self.tcinputs["StorageClass"],
                                                  region=self.tcinputs["region"],
                                                  saved_credential_name=cred_name,
                                                  deduplication_db_location=dedup_loc, cred_details=cred_details)
            self.validate_cloud_storage_creation(name=storage_name)

        except Exception as exp:
            self.res_string += f'Error in creating cloud storage: {exp} \n'
            self.status = constants.FAILED

    def run(self):
        """Run Function of this case"""

        try:

            self.cleanup()

            if self.tcinputs.get("accountName"):
                self.cred_details1["accountName"] = self.tcinputs["accountName"]
            if self.tcinputs.get("accessKeyId"):
                self.cred_details1["accessKeyId"] = self.tcinputs["accessKeyId"]
            self.log.info(self.cred_details1)

            self.log.info(f"****Creating dedupe cloud storage using {self.Authentication1}****")
            self.create_cloud_storage(storage_name=self.cloud_storage_name1, dedup_loc=self.cloud_ddb_location1,
                                      auth_type=self.Authentication1, cred_details=self.cred_details1,
                                      cred_name=self.tcinputs['CloudCredentials1'])

            if self.tcinputs.get("accountName"):
                self.cred_details2["accountName"] = self.tcinputs["accountName"]
            if self.tcinputs.get("tenantId"):
                self.cred_details2["tenantId"] = self.tcinputs["tenantId"]
            if self.tcinputs.get("applicationId"):
                self.cred_details2["applicationId"] = self.tcinputs["applicationId"]
            if self.tcinputs.get("applicationSecret"):
                self.cred_details2["applicationSecret"] = self.tcinputs["applicationSecret"]
            self.log.info(self.cred_details2)

            self.log.info(f"****Creating non dedupe cloud storage using {self.Authentication2}****")
            self.create_cloud_storage(storage_name=self.cloud_storage_name2, auth_type=self.Authentication2,
                                      cred_details=self.cred_details2, cred_name=self.tcinputs['CloudCredentials2'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            if not self.res_string:
                self.res_string = 'Success'
            self.log.info(f'Result of this TestCase: {self.res_string}')
            Browser.close_silently(self.browser)
