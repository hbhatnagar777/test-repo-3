from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep

from AutomationUtils import database_helper
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
import inspect

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[CC Acceptance] Identity servers: CRUD operations on Identity servers page"
        self.tcinputs = {
            "domain_name" : "",
            "netbios_name" : "",
            "username" : "",
            "password" : ""
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.indentity_server_helper = IdentityServersMain(admin_console= self.admin_console, commcell=self.commcell,csdb=self.csdb)
        
    def run(self):
        """Run function of this test case"""
        try:
            functions = [
                function_obj
                for function_name, function_obj in inspect.getmembers(
                    object=self.indentity_server_helper
                )
                if function_name.startswith('validate_listing_')
            ]
            tries = 3
            while tries and functions:
                failed_functions = list(functions)
                self.commcell.domains.refresh()
                for function in failed_functions:
                    try:
                        self.log.info(f'Validating : {function.__name__}')
                        if 'creation' in function.__name__:
                            if self.commcell.domains.has_domain(self.tcinputs['netbios_name']):
                                self.commcell.domains.delete(self.tcinputs['netbios_name'])
                            function(self.tcinputs)
                        elif 'deletion' in function.__name__:
                            if not self.commcell.domains.has_domain(self.tcinputs['netbios_name']):
                                self.commcell.domains.add(domain_name=self.tcinputs['domain_name'], netbios_name=self.tcinputs['netbios_name'], 
                                    user_name= self.tcinputs['username'], password= self.tcinputs['password'], company_id= 0)
                            function(self.tcinputs['netbios_name'])
                        else:
                            function()
                        functions.remove(function)
                        self.log.info(f'Validation done for : {function.__name__}')
                    except Exception as err:
                        handle_testcase_exception(self, err)
                        self.log.info(f'[Exception] in [{function.__name__}]: [{err}]')
                tries -= 1
                self.log.info(f'Tries Left : {tries}')
                self.admin_console.refresh_page()

            if functions:
                failed_functions = [function.__name__ for function in functions]
                raise Exception(f'Validation failed for : {failed_functions}')

            self.status = constants.PASSED
            self.result_string = ''
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
