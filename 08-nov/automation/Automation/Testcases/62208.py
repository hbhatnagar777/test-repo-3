from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.NetworkLoggerHelper import NetworkLogger
from Web.AdminConsole.Helper.NetworkLoggerHelper import AutoMR
import os
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
import time


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center : Performance testing of different screens using the nwLogger"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {

        }
        self.driver = None
        self.nlogger_page = None
        self.adminconsole_page = None
        self.per_helper_obj = None
        self.auto_mr_obj = None


    def set_registry_keys(self, user):
        """
        function to set registry keys in the remote CS machine

        :return: None
        """
        self.remote_mac_obj = Machine(machine_name=self.commcell.commserv_name, commcell_object=self.commcell)
        count = 0
        self.base_path = self.remote_mac_obj.get_registry_value("Base", "dGALAXYHOME")
        cache_path = os.path.join(self.base_path, 'Log Files', 'cache')
        if not self.remote_mac_obj.check_registry_exists("WebConsole",
                                                         "cacheDbLocation"):
            self.remote_mac_obj.create_registry("WebConsole",
                                                "cacheDbLocation", cache_path)
            self.log.info("Added cacheDbLocation")
            count += 1
        if not self.remote_mac_obj.check_registry_exists("WebConsole",
                                                         "debugModeUsers"):

            self.remote_mac_obj.create_registry("WebConsole",
                                                "debugModeUsers", user)
            self.log.info("Added debugModeUsers")
            count += 1
        else:
            username = self.remote_mac_obj.get_registry_value("WebConsole",
                                                              "debugModeUsers")
            if user != username:
                self.remote_mac_obj.create_registry("WebConsole",
                                                    "debugModeUsers", user)
                self.log.info("Added debugModeUsers")
                count += 1
        if count > 0:
            cs = self.commcell.clients.get(self.commcell.commserv_name)
            cs.restart_service("GxTomcatInstance001")

            time.sleep(300)

    def navigate_to_cc(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        hostname = self.tcinputs.get('webconsoleHostname', self.commcell.webconsole_hostname)
        self.admin_console = AdminConsole(self.browser, hostname)
        username = self.tcinputs.get('commcellUsername', self.inputJSONnode['commcell']['commcellUsername'])
        password = self.tcinputs.get('commcellPassword', self.inputJSONnode['commcell']['commcellPassword'])
        self.tcinputs["username"] = username
        user_id = self.commcell.users.get(username).user_id
        self.tcinputs["user_id"] = user_id
        self.admin_console.login(username=username,
                                 password=password, stay_logged_in=True)
        browser_stats_for_login = self.admin_console.login_stats + self.browser.get_browser_networkstats()
        self.driver = self.browser.driver
        login_time = self.admin_console.end_time_load - self.admin_console.start_time_load
        self.per_helper_obj = NetworkLogger(self.commcell, self.admin_console,
                                            self.tcinputs.get("email", self.inputJSONnode["email"]["receiver"]),
                                            self.browser, self.tcinputs)
        self.admin_console.clear_perfstats()
        self.per_helper_obj.record_load_time("LOGIN", login_time, browser_stats_for_login)

    def run(self):
        try:
            if self.tcinputs.get("setKeys"):
                self.set_registry_keys(
                    self.tcinputs.get('commcellUsername', self.inputJSONnode['commcell']['commcellUsername']))
            self.navigate_to_cc()
            if self.tcinputs.get("loop_twice"):
                value, exception = self.per_helper_obj.navigate_to_screens(record=False)
                self.per_helper_obj.clear_stats()
                if not value:
                    raise Exception(exception)
            value, exception = self.per_helper_obj.navigate_to_screens(record=True)
            mr_details = self.per_helper_obj.report_generator()
            if self.tcinputs.get("createMR") and len(mr_details) != 0:
                self.auto_mr_obj = AutoMR(self.commcell, self.admin_console, self.browser,self.tcinputs)
                self.auto_mr_obj.create_mrs(mr_details)
            self.per_helper_obj.create_graphs()
            self.per_helper_obj.mail_reports()
            if not value:
                raise Exception(exception)

        except Exception as e:
            raise Exception(e)
        finally:
            self.admin_console.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
