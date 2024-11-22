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
    __init__()                          --  initialize TestCase class

    setup()                             --  sets up the variables required for running the testcase

    run()                               --  run function of this test case

    validate_no_subscription()          --  validates tenant with no risk analysis subscription

    validate_sub_with_no_bkp()          --  validates risk analysis tenant with active subscription but no O365 backups

    validate_active_subscription()      --  validates risk analysis tenant with active subscription and valid O365 backups

    validate_configure_service()        --  Validates Service Catalog's Configure option

    validate_manage_service()           --  Validate Service Catalog's Manage option

    tear_down()                         --  tears down the onedrive entities created for running the testcase

    is_test_step_complete()             --  checks if a test step is complete

    set_test_step_complete()            --  Sets the progress with a give test step value

    __init_command_center()             --  Initializes service catalog screen

    __get_risk_subscription_type()      --  Gets Subscription Type

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from dynamicindex.utils import constants as cs
from dynamicindex.utils.constants import set_step_complete, is_step_complete, RAServiceCatalogSteps as rsc
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, RiskAnalysisType, RiskAnalysisSubType
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Basic acceptance of Sensitive Data Governance for backed up OneDrive users whose data " \
                    "is not content indexed"
        self.tcinputs = {
            'TenantWithoutSubscription': None,
            'TenantWithSubcriptionNoBackup': None,
            'TenantWithSubscription': None,
            'TenantAdmin': None,
            'TenantPassword': None
        }
        # Test Case constants
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.service_catalog = None
        self.tenant_admin = None
        self.tenant_password = None
        self.tenant_without_subscription = None
        self.tenant_with_subscription_no_backup = None
        self.tenant_with_subscription = None
        self.test_case_error = None
        self.rehydrator = None
        self.test_progress = None
        self.error_dict = {}

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.rehydrator = Rehydrator(self.id)
            self.test_progress = self.rehydrator.bucket(cs.BUCKET_TEST_PROGRESS)
            self.test_progress.get(default=0)
            self.tenant_admin = self.tcinputs.get('TenantAdmin')
            self.tenant_password = self.tcinputs.get('TenantPassword')
            self.tenant_without_subscription = self.tcinputs.get('TenantWithoutSubscription')
            self.tenant_with_subscription_no_backup = self.tcinputs.get('TenantWithSubcriptionNoBackup')
            self.tenant_with_subscription = self.tcinputs.get('TenantWithSubscription')
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.inputJSONnode["commcell"]["commcellPassword"])
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def is_test_step_complete(self, step_enum):
        """
        checks if a test step is complete
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        Returns:
            bool                        --  Returns true if step is complete else false
        """
        return is_step_complete(self.test_progress, step_enum.value)

    def set_test_step_complete(self, step_enum):
        """
        Sets the progress with a give test step value
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        """
        set_step_complete(self.test_progress, step_enum.value)

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting test case run")
            self.validate_no_subscription()
            self.validate_sub_with_no_bkp()
            self.validate_active_subscription()
            if not self.is_test_step_complete(rsc.VALIDATE_RA_OD_CONFIGURE):
                self.validate_configure_service(RiskAnalysisType.ONEDRIVE)
                self.set_test_step_complete(rsc.VALIDATE_RA_OD_CONFIGURE)
            else:
                self.log.info(f"{rsc.VALIDATE_RA_OD_CONFIGURE.name} step complete. Not starting it")
            if not self.is_test_step_complete(rsc.VALIDATE_RA_EXCH_CONFIGURE):
                self.validate_configure_service(RiskAnalysisType.EXCHANGE)
                self.set_test_step_complete(rsc.VALIDATE_RA_EXCH_CONFIGURE)
            else:
                self.log.info(f"{rsc.VALIDATE_RA_EXCH_CONFIGURE.name} step complete. Not starting it")
            self.validate_manage_service()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    @test_step
    def validate_no_subscription(self):
        """
        validates tenant with no risk analysis subscription
        """
        if not self.is_test_step_complete(rsc.VALIDATE_TENANT_WO_SUB):
            self.log.info("Validating RA for tenant with no subscription")
            username = f"{self.tenant_without_subscription}\\{self.tenant_admin}"
            self.__init_command_center(username, self.tenant_password)
            sub_type = self.__get_risk_subscription_type()
            if not sub_type == RiskAnalysisSubType.NO_SUBSCRIPTION:
                raise Exception(f"Tenant with no subscription returned a different subscription type [{sub_type}]")
            self.log.info("Validated RA for tenant with no subscription")
            self.set_test_step_complete(rsc.VALIDATE_TENANT_WO_SUB)
        else:
            self.log.info(f"{rsc.VALIDATE_TENANT_WO_SUB.name} step complete. Not starting it")

    @test_step
    def validate_sub_with_no_bkp(self):
        """
        validates risk analysis tenant with active subscription but no O365 backups
        """
        if not self.is_test_step_complete(rsc.VALIDATE_TENANT_W_SUB_NO_BKP):
            self.log.info("Validating RA for tenant with valid subscription and no M365 backup")
            username = f"{self.tenant_with_subscription_no_backup}\\{self.tenant_admin}"
            self.__init_command_center(username, self.tenant_password)
            sub_type = self.__get_risk_subscription_type()
            if not sub_type == RiskAnalysisSubType.SUBSCRIPTION_AND_NO_BACKUP:
                raise Exception(f"Tenant with subscription and no backup returned a different subscription type [{sub_type}]")
            self.log.info("Validated RA for tenant with valid subscription")
            self.set_test_step_complete(rsc.VALIDATE_TENANT_W_SUB_NO_BKP)
        else:
            self.log.info(f"{rsc.VALIDATE_TENANT_W_SUB_NO_BKP.name} step complete. Not starting it")

    @test_step
    def validate_active_subscription(self):
        """
        validates risk analysis tenant with active subscription and valid O365 backups
        """
        username = f"{self.tenant_with_subscription}\\{self.tenant_admin}"
        if not self.is_test_step_complete(rsc.VALIDATE_TENANT_W_SUB):
            self.log.info("Validating RA for tenant with valid subscription and backup")
            self.__init_command_center(username, self.tenant_password)
            sub_type = self.__get_risk_subscription_type()
            if not sub_type == RiskAnalysisSubType.SUBSCRIPTION_AND_BACKUP:
                raise Exception(f"Tenant with subscription and no backup returned a different subscription type [{sub_type}]")
            self.log.info("Validated RA for tenant with valid subscription and backup")
            self.set_test_step_complete(rsc.VALIDATE_TENANT_W_SUB)
        else:
            self.__init_command_center(username, self.tenant_password)
            self.log.info(f"{rsc.VALIDATE_TENANT_W_SUB.name} step complete. Not starting it")

    @test_step
    def validate_configure_service(self, app_type):
        """
        Validates Service Catalog's Configure option
        Args:
            app_type(RiskAnalysisType)       --  Type of App to configure
        """
        self.log.info(f"Validating RA Configure option for AppType [{app_type.value}]")
        self.navigator.navigate_to_service_catalogue()
        self.service_catalog = ServiceCatalogue(self.admin_console, HubServices.risk_analysis, app_type)
        self.service_catalog.configure_risk_analysis()
        self.log.info("RA configure option validated")

    @test_step
    def validate_manage_service(self):
        """
        Validate Service Catalog's Manage option
        """
        if not self.is_test_step_complete(rsc.VALIDATE_RA_MANAGE):
            self.log.info("Validating Manage RA for tenant with valid subscription and backup")
            self.navigator.navigate_to_service_catalogue()
            self.service_catalog = ServiceCatalogue(self.admin_console, HubServices.risk_analysis)
            self.service_catalog.manage_risk_analysis()
            self.log.info("Validated Manage RA for tenant with valid subscription and backup")
            self.set_test_step_complete(rsc.VALIDATE_RA_MANAGE)
        else:
            self.log.info(f"{rsc.VALIDATE_RA_MANAGE.name} step complete. Not starting it")

    def __init_command_center(self, username, password):
        """
        Initializes service catalog screen
        Args:
            username(str)       --  Tenant admin username
            password(str)       --  Tenant admin password
        """
        AdminConsole.logout_silently(self.admin_console)
        self.admin_console.wait_for_completion()
        self.admin_console.login(username=username,
                                 password=password)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()

    def __get_risk_subscription_type(self):
        """
        Gets Subscription Type
        Returns:
            enum                --  Subscription type enum
        """
        self.service_catalog = ServiceCatalogue(self.admin_console, HubServices.risk_analysis)
        sub_type = self.service_catalog.get_risk_subscription_type()
        return sub_type

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.rehydrator.cleanup()
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
