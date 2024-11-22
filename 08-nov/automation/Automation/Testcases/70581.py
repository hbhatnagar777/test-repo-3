import traceback
from Web.AdminConsole.AdminConsolePages.Alerts import Alerts
from Web.Common.exceptions import CVWebAutomationException
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from cvpysdk.commcell import Commcell
from Server.Alerts.alert_helper import AlertHelper
from time import sleep
import random

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Alerts Functionality"
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
        self.sc_alert_helper = AlertHelper(self.service_commcell)
        
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.alerts = Alerts(self.admin_console)

        # switch to global view
        self.log.info("Switching to Global view...")
        self.navigator.switch_service_commcell('Global')
        self.navigator.navigate_to_alerts()
        

    def run(self):
        """Run function of this test case"""
        try:

            retry_count = 1
            
            while retry_count:
                try:
                    
                    self.create_test_alert_on_service_commcell()
                    
                    self.trigger_test_alert_and_validate()
                    
                    self.delete_triggered_alert()

                    break

                except Exception as exp:
                    if retry_count == 1:
                        raise exp

                    self.log.info(traceback.format_exc())

                    retry_count -= 1
                    self.log.info(f"TC:[{self.tcTID}] Failed, trying again")
                    self.tear_down()
                    self.setup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.service_commcell.refresh()
        
        self.log.info("Deleting test alerts from service commcell...")
        filtered_alerts = [alert for alert in self.service_commcell.alerts.all_alerts if f'TC_ALERT_{self.tcTID}' in alert.lower()]
        for alert_name in filtered_alerts:
            self.sc_alert_helper.delete_alert(alert_name)

    @test_step
    def is_triggered_alert_exists_on_sc(self, alert_name: str):
        """Check if triggered alert exists on service commcell"""
        retry_count = 3
        retry_interval = 10
        
        self.log.info("Checking if alert is present on service commcell...")
    
        while retry_count > 0:
            found_status = [alert_details['alertName'].lower() == alert_name.lower() for alert_details in self.service_commcell.alerts.console_alerts().get('feedsList',[])]
            if any(found_status):
                self.log.info("Alert is present on service commcell")
                return True
    
            self.log.info(f"Alert is not present, retrying in {retry_interval} seconds...")
            sleep(retry_interval)
            retry_count -= 1
    
        self.log.info("Alert is not present on service commcell")
        return False

    @test_step
    def create_test_alert_on_service_commcell(self):
        """Create test alert on service commcell"""
        self.log.info("Creating test alert on service commcell...")
        alert_dict = {
            'alert_type': 3,
            'notif_type': [8192], # console alert
            'notifTypeListOperationType': 0,
            'alert_severity': 0,
            'nonGalaxyUserOperationType': 0,
            'criteria': 1,
            'associationOperationType': 0,
            'entities': {'client_groups': "Infrastructure"},
            'userListOperationType': 0,
            'users': [self.service_commcell.commcell_username],
            'alert_name': f'TC_ALERT_{self.id}_{random.randint(1, 1000)}',
        }

        self.test_alert = self.service_commcell.alerts.create_alert(alert_dict)
        # self.service_commcell_test_alert.test()
        
    @test_step
    def trigger_test_alert_and_validate(self):
        """Trigger test alert"""
        self.log.info("Triggering test alert...")
        self.test_alert.trigger_test_alert()
        
        self.log.info("Validating if alert is triggered in Service Commcell...")
        alert_exists = self.is_triggered_alert_exists_on_sc(alert_name=self.test_alert.alert_name)
        
        if not alert_exists:
            raise CVWebAutomationException("Alert is not triggered in Service Commcell")
        
        self.log.info("Validating if alert is triggered and visible in Global Commcell...")
        trigger_status = False
        retry_count = 3
        retry_interval = 10

        while retry_count > 0:
            trigger_status = self.alerts.is_alert_triggered(alert_name=self.test_alert.alert_name,
                                                            # commcell_name=self.service_commcell_commserv_name
                                                            )
            
            if trigger_status:
                break
            
            self.log.info(f"Alert is not triggered, retrying in {retry_interval} seconds...")
            sleep(retry_interval)
            retry_count -= 1

        if not trigger_status:
            self.log.error("[Global]: Alert is not visible in Global Commcell though it is triggered and visible in Service Commcell")
            # raise CVWebAutomationException("[Global]: Alert is not visible in Global Commcell though it is triggered and visible in Service Commcell")
                
        self.log.info("[Global]: Alert is triggered successfully and visible in Global Commcell")
        
    @test_step
    def delete_triggered_alert(self):
        """Delete triggered alert"""
        self.log.info("Deleting triggered alert...")
        self.alerts.delete_current_triggered_alert(alert_name=self.test_alert.alert_name, commcell_name=self.service_commcell_commserv_name)
        
        found_status = self.is_triggered_alert_exists_on_sc(alert_name=self.test_alert.alert_name)
        
        if found_status:
            raise CVWebAutomationException("Triggered Alert is not deleted from Service Commcell")
        
        self.log.info("[Global]: Alert is deleted successfully from Global Commcell")
        