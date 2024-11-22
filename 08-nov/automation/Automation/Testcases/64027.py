from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Metallic.MirageHelper import MirageCCHelper, MirageApiHelper
from cvpysdk.commcell import Commcell
from random import randint
from Server.organizationhelper import OrganizationHelper
from AutomationUtils.config import get_config

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Mirage]: Metallic only user flow"
        self.tcinputs = {
        }
        self.metallic_commcell = None

    def setup(self):
        """Setup function of this test case"""
        self.config = get_config().GCM
        self.metallic_ring = self.config.RING
        self.metric_commcell = self.config.METALLIC_METRICS

        self.metallic_password = self.metallic_ring.metallic_ring_password
        self.metallic_commcell = Commcell(self.metallic_ring.metallic_ring_hostname, self.metallic_ring.metallic_ring_username, self.metallic_password, verify_ssl=False)
        self.wf_commcell       = Commcell(self.metric_commcell.metrics_hostname, self.metric_commcell.metrics_username, self.metric_commcell.metrics_password, verify_ssl=False)
        self.mirage_api_helper = MirageApiHelper(self.metallic_commcell)

        # create company at metallic side using workflow
        self.create_tenant()

        # login as tenant admin
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.metallic_commcell.webconsole_hostname)
        self.admin_console.login(self.company_tenant_admin, self.metallic_password)
        # self.admin_console.driver.implicitly_wait(30)
        self.navigator = self.admin_console.navigator


        self.mirage_cc_helper = MirageCCHelper(self.admin_console, self.commcell)
        self.navigator.navigate_to_service_catalogue()

    def run(self):
        """Run function of this test case"""
        try:
            # Validate cloud command panel visibility from Service Catalog
            self.mirage_cc_helper.go_to_metallic_cloud_command()
            self.admin_console.wait_for_completion()

            current_page_url = self.admin_console.current_url()
            if 'cloudCommand' not in current_page_url:
                raise CVTestStepFailure(f'Clicking on cloud command from Service Catalog side didnt take the user to cloud command. Current Page URL: {current_page_url}')

            dashboards = self.mirage_cc_helper.available_dashboards()
            self.log.info(f'Available dashboards for metallic user => {dashboards}')

            if 'Platform Score' in dashboards:
                raise CVTestStepFailure(f'Metallic tenant admin can see Platform Score dashboard. Dashboards => {dashboards}')

            if ('Data Protection Score' not in dashboards) or ('Security Posture Score' not in dashboards):
                raise CVTestStepFailure(f'Metallic tenant admin is not seeing Data protection and Security posture dashboard. Dashboards => {dashboards}')

            if self.mirage_cc_helper.is_switcher_available():
                raise CVTestStepFailure('Commcell switcher available for Metallic only user!')

            self.navigator.navigate_to_service_catalogue()

            current_page_url = self.admin_console.current_url()
            if 'serviceCatalogV2' not in current_page_url:
                raise CVTestStepFailure(f'Clicking on service catalog breadcrumb didnt redirect to the new service catalog page : {current_page_url}')

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        if self.metallic_commcell:
            OrganizationHelper(self.metallic_commcell).cleanup_orgs(marker='Mirage')

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.ring_name = self.metallic_commcell.webconsole_hostname.split('.')[0].upper()
        self.tenant_name = f'MirageMetallicOnly{randint(0,100000)}'
        workflow_inputs = {
            "firstname": "MetallicOnly",
            "lastname": "MirageUser",
            "company_name": self.tenant_name,
            "phone": "000000000",
            "commcell": self.ring_name,
            "email": f"mirageuser{randint(1, 10000)}@metalliconly{randint(1, 10000)}.com"
        }
        self.mirage_api_helper.create_metallic_tenant(self.wf_commcell, workflow_inputs)

        self.log.info('Changing password for tenant admin..')
        self.company_tenant_admin = f"{workflow_inputs['company_name']}\\{workflow_inputs['email'].split('@')[0]}"
        self.metallic_commcell.users.refresh()
        self.metallic_commcell.users.get(self.company_tenant_admin).update_user_password(
            self.metallic_password, self.metallic_password)
        self.log.info(f'Successfully reset the password for user => {self.company_tenant_admin}')
