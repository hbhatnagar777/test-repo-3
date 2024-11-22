import traceback, random
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.service_commcell import ServiceCommcell

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Service Commcells Functionality"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            "ServiceCommcellHostName": "",
            "ServiceCommcellUserName": "",
            "ServiceCommcellPassword": ""
        }

    def setup(self):
        """Setup function of this test case"""
        # connect to service commcell
        self.service_commcell = Commcell(self.tcinputs["ServiceCommcellHostName"],
                                         self.tcinputs["ServiceCommcellUserName"],
                                         self.tcinputs["ServiceCommcellPassword"])
        self.service_commcell_commserv_name = self.service_commcell.commserv_name
        
        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        # switch to global view
        self.log.info("Switching to Global view...")
        self.navigator.switch_service_commcell('Global')

        # required objects
        self.__service_commcell = ServiceCommcell(self.admin_console)

        # deregister service commcell if already registered
        self.navigator.navigate_to_service_commcell()

        if self.__service_commcell.is_service_commcell_exists(self.service_commcell_commserv_name):
            self.log.info("Service Commcell already registered, deregistering it...")
            self.deregister_service_commcell()

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 5
            
            while retry_count:
                try:
                    
                    self.register_service_commcell_with_invalid_credentials()

                    self.register_service_commcell()

                    self.associate_user_to_service_commcell()

                    self.disassociate_user_from_service_commcell()

                    self.refresh_service_commcell()

                    self.deregister_service_commcell()

                    break

                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())

                    retry_count -= 1
                    self.log.info("TC Failed, trying again")
                    self.tear_down()
                    self.setup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def register_service_commcell_with_invalid_credentials(self):
        """Method to register service commcell with invalid credentials"""
        self.navigator.navigate_to_service_commcell()
        try:
            self.__service_commcell.register_commcell(self.service_commcell.commserv_hostname, 
                                                    self.tcinputs['ServiceCommcellUserName'], 
                                                    'invalidpassword',
                                                    False)
        except Exception as exp:
            self.log.info(f"Exception: {exp}")
            self.log.info("As Expected, Service Commcell failed to register with invalid credentials")
        else:
            raise CVWebAutomationException("Service Commcell registered with invalid credentials")

    @test_step
    def register_service_commcell(self):
        """Method to register service commcell"""
        self.navigator.navigate_to_service_commcell()

        self.__service_commcell.register_commcell(self.service_commcell.commserv_hostname, 
                                                  self.tcinputs['ServiceCommcellUserName'], 
                                                  self.tcinputs['ServiceCommcellPassword'],
                                                  False)
        
        if not self.__service_commcell.is_service_commcell_exists(self.service_commcell_commserv_name):
            raise CVWebAutomationException("Service Commcell failed to register")
        
        self.log.info("Service Commcell registered successfully")

        # validate if sync status is successfull
        sync_status = self.__service_commcell.get_service_commcell_sync_status(self.service_commcell_commserv_name)

        if sync_status != 'Successful':
            raise CVWebAutomationException(f"Sync status is not successful - {sync_status}")
        
        self.log.info("Sync status is successful")
       
    @test_step
    def associate_user_to_service_commcell(self):
        """Method to associate user to service commcell"""
        self.navigator.navigate_to_service_commcell()

        # create new user to associate with service commcell
        self.user_name = f"testuser{random.randint(1, 1000)}"
        self.commcell.users.add(self.user_name, f"{self.user_name}@{self.user_name}.com", password=self.inputJSONnode['commcell']['commcellPassword'])
        self.log.info(f"User {self.user_name} created at global commcell")

        # add user association to service commcell
        self.__service_commcell.add_entity_association(entity=self.user_name,
                                                       commcells=[self.service_commcell_commserv_name])

    @test_step
    def disassociate_user_from_service_commcell(self):
        """Method to disassociate user from service commcell"""
        self.navigator.navigate_to_service_commcell()
        self.__service_commcell.delete_entity_association(entity=self.user_name)

    @test_step
    def refresh_service_commcell(self):
        """Method to refresh service commcell"""
        self.navigator.navigate_to_service_commcell()
        self.__service_commcell.refresh_registered_commcell(self.service_commcell_commserv_name)

        sync_status = self.__service_commcell.get_service_commcell_sync_status(self.service_commcell_commserv_name)

        if sync_status != 'Successful':
            raise CVWebAutomationException(f"Sync status is not successful - {sync_status}")

    @test_step
    def deregister_service_commcell(self):
        """Method to deregister service commcell"""
        self.navigator.navigate_to_service_commcell()
        self.__service_commcell.delete_registered_commcell(self.service_commcell_commserv_name, True)

        if self.__service_commcell.is_service_commcell_exists(self.service_commcell_commserv_name):
            raise CVWebAutomationException("Service Commcell failed to deregister")
        
        self.log.info("Service Commcell deregistered successfully")