from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.license import LicenseDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.License import License
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = " This test case will validate basics of 'License page' on AdminConsole "
        self.browser = None
        self.driver = None
        self.adminconsole = None
        self.adminpage = None
        self.lic_object = None
        self.machine = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.adminconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                    self.inputJSONnode['commcell']['commcellPassword'])
            self.adminconsole.navigator.navigate_to_license()
            self.lic_object = License(self.adminconsole)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def validate_details(self):
        """ Validates the details on the License page """
        license_mode_mapper = {"EVALUATION": 1000, "PRODUCTION": 1002, "DR_PRODUCTION": 1004}
        lic_response = LicenseDetails(self.commcell)
        details = self.lic_object.get_license_details()
        list_response = []
        list_response.append(lic_response.commcell_id)
        list_response.append(lic_response.cs_hostname)
        list_response.append(lic_response.license_ipaddress)
        list_response.append(lic_response.oem_name)
        list_response.append(lic_response.license_mode)
        list_response.append(lic_response.serial_number)
        list_response.append(lic_response.registration_code)
        if not int(lic_response.expiry_date) == 0:
            list_response.append(datetime.fromtimestamp
                                 (int(lic_response.expiry_date)).strftime("%b %d, %Y").replace(" 0", " "))
        if 'License has expired.' in details.keys():
            list_details = [value for key, value in details.items()][:-1]
        else:
            list_details = [value for key, value in details.items()]
        list_details[4] = license_mode_mapper[list_details[4].split()[0]]

        def signed_hex(n):
            return (n & 0x7fffffff) | -(n & 0x80000000)
        list_details[0] = signed_hex(int(list_details[0], 16))
        string = 'To order an additional license, send email to prodreg@commvault.com'
        if string in list_details:
            list_details.remove(string)
        if list_details == list_response:
            self.log.info("Details validated successfully")
            return

    def run(self):
        try:
            self.init_tc()
            self.validate_details()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
