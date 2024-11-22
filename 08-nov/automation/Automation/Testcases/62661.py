# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    run()                                   --  run function of this test case

Pre-requisites:
    - The CS must have more than 2 jobs in suspended state or atleast pass job_ids or app_ids tcinput
    - This testcase analyzes the suspended jobs and decides the test steps to perform
    - Thus, more the table data variation, more table features tested

Testcase Params:
    - skip_tests (str)  -   string with test names to skip or avoid...
                            Ex: "validate_search, validate_sorting, validate_filters, validate_views"
    - method_params (dict)- to pass method specific params to all above test methods of rtable_helper
    - ideal_view    (str) - view name of the view on which all sort, filter, search tests are to be tested
                            ideally one which has 1 or 2 pages of job history populated but not too many pages
"""

import json
import os.path
import threading
import traceback
import concurrent.futures

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.logger import get_custom_logger
from Web.AdminConsole.Helper.jobs_helper import JobsHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.skip_tests = None
        self.jobs_helper = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "Functional test cases for Command Center - Job history Page"
        self.tcinputs = {}
        self.error_tracking = {}
        self.ideal_view = "Last week"  # todo: determine this properly, may change setup to setup

    def run_method_thread(self, method):
        """
        Worker thread to run the table validation methods parallely
        """
        browser = None
        admin_console = None
        log_filename = f'62661_{method}'
        log_filepath = os.path.join(constants.LOG_DIR, log_filename)
        try:
            browser = BrowserFactory().create_browser_object()
            browser.open()
            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                password=self._inputJSONnode['commcell']['commcellPassword'])
            jobs_helper = JobsHelper(admin_console=admin_console, commcell=self.commcell, **self.tcinputs)
            jobs_helper.setup_jobs_history(view=self.ideal_view)
            rt_helper = jobs_helper.job_history_table_helper
            rt_helper.log = get_custom_logger(log_filename, log_filepath, msg_prefix='')
            rt_helper.setup_table_columns_as_specified()

            self.log.info(f" * * * * STARTING TEST {method} [ID: {threading.get_ident()}] * * * * ")
            getattr(rt_helper, method)(**(self.tcinputs.get('method_params') or {}))
            self.error_tracking[method] = 'PASSED'
            self.log.info(f" * * * * PASSED TEST {method} * * * * ")
            try:
                os.remove(log_filepath)
            except:
                pass

        except Exception as exp:
            self.log.error(f" * * * * FAILED TEST {method} * * * * ")
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            self.status = constants.FAILED
            self.error_tracking[method] = 'FAILED'

        finally:
            AdminConsole.logout_silently(admin_console)
            Browser.close_silently(browser)

    def run(self):
        """Run function of this test case"""
        self.ideal_view = self.tcinputs.get('ideal_view') or self.ideal_view
        max_threads = int(self.tcinputs.get('max_threads') or 4)
        futures = []

        try:
            self.jobs_helper = JobsHelper(commcell=self.commcell, **self.tcinputs)
            self.jobs_helper.start_blackout_window()

            methods = ['validate_search', 'validate_sorting', 'validate_filters', 'validate_views']
            # todo: add redirections validation, and system default views

            with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
                for validation_method in methods:
                    if validation_method in self.tcinputs.get('skip_tests', ''):
                        self.log.info(f" * * * * SKIPPING TEST {validation_method} * * * * ")
                        self.error_tracking[validation_method] = 'SKIPPED'
                        continue
                    futures.append(executor.submit(self.run_method_thread, validation_method))
                concurrent.futures.wait(futures)
            self.result_string = json.dumps(self.error_tracking, indent=4)

        finally:
            if self.jobs_helper:
                self.jobs_helper.delete_blackout_window()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
