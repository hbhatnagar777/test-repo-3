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

    setup()         --  sets up the variables required for running the testcase

    run_tile_test() --  opens browser, inits commcell_helper object and runs one tile test from CommcellHelper

    run()           --  run function of this test case, concurrently runs the run_tile_test for different tiles

Pre-requisites (optional):
    - Email settings without authentication is preferred (to test edit and restore original settings)
    - Security association must exist for at least one user or group other than master

tcinputs (optional):
    - tiles_to_avoid    (str)       -   CommcellHelper test method names to avoid testing
                                        example: 'test_general_tile, test_email_tile'
                                        default: None
    - maximum_threads   (str/int)   -   number of threads to test the tiles concurrently
                                        example: 4 
                                        [Note: 1 will avoid parallel execution but greatly increase runtime]
                                        default: 8
"""
import concurrent.futures
import inspect
import json
import threading
import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.commcell_helper import CommcellHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Basic Acceptance test for commcell page"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.max_threads = 8
        self.methods_to_avoid = ''
        self.name = "Basic Acceptance test for commcell page"
        self.error_tracking = {}
        self.lock = threading.Lock()

    def setup(self):
        self.methods_to_avoid = self.tcinputs.get('tiles_to_avoid', '')
        self.max_threads = int(self.tcinputs.get('maximum_threads', 8))

    def run_tile_test(self, test_method):
        ch, browser, admin_console = None, None, None
        try:
            browser = BrowserFactory().create_browser_object(name="User Browser")
            browser.open()
            with self.lock:
                # admin console init needs lock to avoid race conditions on reading config file
                for attempt in range(5):  # attempt 5 times to avoid file reading errors
                    try:
                        admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
                        break
                    except Exception as exp:
                        if attempt == 4:
                            raise exp
            admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                password=self._inputJSONnode['commcell']['commcellPassword'])
            admin_console.navigator.navigate_to_commcell()
            ch = CommcellHelper(admin_console, self.commcell)
            test_errors = getattr(ch, test_method)()
            if not test_errors:
                test_errors = []
        except Exception as exp:
            test_errors = [str(exp), traceback.format_exc()]
        finally:
            if ch:
                cleanup_errors = ch.clean_up()
            if admin_console:
                AdminConsole.logout_silently(admin_console)
            if browser:
                Browser.close_silently(browser)
            with self.lock:
                self.error_tracking[test_method] = test_errors + [] if not ch else cleanup_errors

    def run(self):
        futures = []
        result = {}

        with concurrent.futures.ThreadPoolExecutor(self.max_threads) as executor:
            for helper_method_name, helper_method_obj in inspect.getmembers(CommcellHelper):
                if helper_method_name.startswith('test_') and helper_method_name.endswith('_tile'):
                    result[helper_method_name] = 'FAILED IN BROWSER SETUP'
                    if helper_method_name.lower() in self.methods_to_avoid.lower():
                        self.log.info(f"** AVOIDING TEST -> {helper_method_name} **")
                        result[helper_method_name] = 'SKIPPED'
                        continue
                    futures.append(executor.submit(self.run_tile_test, helper_method_name))
            concurrent.futures.wait(futures)

        self.status = constants.PASSED
        self.log.info("****** COMMCELL PAGE TEST COMPLETED SUMMARY ******")
        for helper_method, errors in self.error_tracking.items():
            if not errors:
                result[helper_method] = 'PASSED'
                self.log.info(f"{helper_method} = PASSED!")
            else:
                self.log.error(f"{helper_method} = FAILED!")
                self.status = constants.FAILED
                for error in errors:
                    self.log.error(error)
                result[helper_method] = ["{:.40}".format(error) for error in errors]
            self.log.info("--------------------------------------------------")

        self.result_string = json.dumps(result, indent=2)
