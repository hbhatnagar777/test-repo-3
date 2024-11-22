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

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    tear_down()                             --  tear down function of this test case

Job Selection Params (Optional):
    - job_id    (int)   -   id of job to test on (will resubmit if required)
                            default: latest resubmit-able successful job from job history with below params
    - app_id    (int)   -   if not job id given, you can give app id of any subclient to use to run backup job
                            default: None
    - automation_lag (int) -Only jobs above this duration will be selected for test (in seconds)
                            default: 120
    - size_threshold (int)- Only jobs larger than this size wil be selected for test (in MB)
                            default: 500 MB
    - job_filters (str) -   comma separated job types/filters to use while selecting job (when job id is not given)
                            default: None (any non-admin job will be used, DDB, Backup, Restore etc)

Testcase Params (Optional):
    - ui_delay  (int)   -   max acceptable time delay between API response and UI page updation (in seconds)
                            default: 30
    - reload    (bool)  -   will reload the jobs grid before validating job if True
                            default: False
    - redirect_exclusions   (str)   -   comma separated action links from jobs that can be ignored if greyed/missing
                                        example: any from below 6 strings
                                            Restore, View logs, Send logs, View job details, Job link, View failed items
                                        default: 'all' , missing redirect links won't be reported but misleading ones
                                                         will always be caught
    - use_csv   (bool)  -   will use export csv to read table data quickly if True, else read from page elements
                            default: True
                            (applicable only in testcases where table size is very large)
    - workflow  (str)   -   name of a workflow to use for executing multiple jobs at once
                            default: None, assumes multiple jobs suspended in active jobs page
                            (applicable only in testcases where multiple active jobs are required)
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.jobs_helper import JobsHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.jobs_helper = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "Functional test cases for Command Center - Active Jobs Page"
        self.tcinputs = {}

    def setup(self):
        """Initial configuration for the test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.jobs_helper = JobsHelper(admin_console=self.admin_console, commcell=self.commcell, **self.tcinputs)

    def run(self):
        """Run function of this test case"""
        try:
            self.jobs_helper.setup_active_jobs()
            job_id = self.jobs_helper.run_and_validate(reload=self.tcinputs.get('reload', False))
            self.jobs_helper.suspend_and_validate()
            self.jobs_helper.validate_redirects(job_id, exclusions=self.tcinputs.get('redirect_exclusions', 'all'))
            self.jobs_helper.resume_and_validate()
            self.jobs_helper.kill_and_validate()
            if bool(self.tcinputs.get('resubmit', False)):
                self.jobs_helper.resubmit_and_validate(self.jobs_helper.job.job_id)
            else:
                self.log.info("Resubmit test skipped")
        except Exception as exp:
            self.jobs_helper.clean_up()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            raise exp

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin_console.logout()
        self.browser.close()
