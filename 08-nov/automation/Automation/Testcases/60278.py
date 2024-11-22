# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Main file for executing this test case

Metrics Report : Verify Health Tiles loaded properly

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                    --  initialize TestCase class
    init_tc()                                     --  Initialize pre-requisites
    verify_links()                                --  verify health report document links
    verify_details                                --  verify health report tile detail pages
    run()                                         --  run function of this test case
Input Example:

    "testCases":
            {

            }


"""
import time
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAutomationException
)
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator

from Web.WebConsole.Reports.Metrics.health import Health
from Web.WebConsole.Reports.Metrics.health_tiles import GenericTile

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger

from Reports.utils import TestCaseUtils




class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """

    def __init__(self):
        super().__init__()
        self.name = "Metrics Report : Verify Doc Links loaded properly"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.log = None
        self.navigator: Navigator = None
        self.utils = TestCaseUtils(self)
        self.health = None
        self.notifications = None

    def _init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.log = logger.getLog()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_commcell_dashboard(self.commcell.commserv_name)
            self.navigator.goto_health_report()
            self.health = Health(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def verify_links(self):
        """
        Verify for proper links
        """
        self.log.info('Checking links for each tile')
        driver = self.webconsole.browser.driver
        url = driver.current_url

        links = []
        links = self.health.get_remark_links()

        self.log.info("Links found" + str(links))

        for link in links:
            driver.get(link)
            time.sleep(3)
            if driver.title == '404':
                self.log.info(f'Page {link} cannot be found')
                raise Exception(f'Page {link} cannot be found')
            xpaths = [f"//*[contains(text(), \"Sorry, we couldn't find what you are looking for.\")][not(self::script)]", f"//*[contains(text(), 'No Data Available.')][not(self::script)]"]
            element = []
            for xpath in xpaths:
                try:
                    element.extend(driver.find_elements(By.XPATH, xpath))
                    self.log.info(element)
                except Exception as e:
                    self.log.info('checking for %s failed' % xpath)
                    self.log.info(e)

        driver.get(url)

    def check_notification_error(self):
        """Check for any notification errors if exists"""
        error_found = False
        self.notifications = self.webconsole.get_all_unread_notifications()
        if self.notifications:  # once the notifications are found clear the
            # notifications for next report
            msg = 'Report does not exist or you do not have permissions to view it.'
            if self.notifications[0] == msg:
                error_found = True
        return error_found

    def verify_details(self):
        """
        Verify for proper view details
        """
        self.log.info('Checking details for each tile')
        driver = self.webconsole.browser.driver
        main_window = driver.current_window_handle

        no_view_details = []
        no_data = []
        for tile_name in self.health.get_visible_tiles():
            tile = GenericTile(self.webconsole, tile_name)
            self.webconsole.clear_all_notifications()
            tile.access_view_details()
            self.log.info(driver.title)
            if self.check_notification_error():
                raise CVTestStepFailure(
                    f" Table [{tile_name}] is missing details table"
                )
            """Check that tile has data in view details"""
            table = []
            try:
                table.extend(driver.find_elements(By.XPATH, f"//table//tbody"))
                self.log.info('tables: ' + str(len(table)))
            except Exception as e:
                self.log.info('no tables were found')
                self.log.info(e)

            if len(table) > 0:
                driver.close()
                driver.switch_to.window(main_window)
            time.sleep(1)

        self.log.info('no view details: ' + str(no_view_details))
        self.log.info('missing data: ' + str(no_data))

    def run(self):
        try:
            self._init_tc()
            self.verify_links()
            self.verify_details()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
