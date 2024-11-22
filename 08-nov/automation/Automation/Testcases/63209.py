# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies that browse request is audited.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    open_audit_trail()          --  Navigates to the report page and opens the audit trail report

    wait()                      --  Wait for some time and refreshes the report page

    random_text()               --  Returns a random text for the browse/find operation

    verify_audit()              --  Verifies the audit list like number of audits and the content of the last audit

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_random_string

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import Browser

from Web.AdminConsole.adminconsole import AdminConsole

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.Custom import viewer

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that browse request is audited.

        Steps:
            1) Create a backupset, subclient and run a backup job
            2) Do a browse, find from backupset and subclient levels
            3) Verify the details like username, operation type and other entity names in the audited data
            4) Run synthetic full backup job
            5) Verify browse request is not audited
            6) Login as another company user (tenant admin)
            7) Verify the previous browse requests are not seen for that user in the audit report

    """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Audit trail of browse requests'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None,
            'CompanyUser': None,
            'CompanyPassword': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

        self.browser = None
        self.admin_console = None
        self.navigator = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        rand_id = get_random_string(5)
        self.backupset = self.idx_tc.create_backupset(f'{self.id}_audit_{rand_id}', for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name=f'{self.id}_sc1',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login()

        self.navigator = self.admin_console.navigator

    @test_step
    def open_audit_trail(self):
        """Navigates to the report page and opens the audit trail report"""

        navigator = self.admin_console.navigator
        navigator.navigate_to_reports()

        self.report = Report(self.admin_console)
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("Audit trail")

        self.viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable('')
        self.viewer.associate_component(self.table)

    def run(self):
        """Contains the core testcase logic"""

        admin_user = self.inputJSONnode['commcell']['commcellUsername']

        self.idx_tc.run_backup_sequence(
            self.subclient, ['new', 'full'], verify_backup=False
        )

        self.open_audit_trail()

        text = self.random_text('path')
        self.log.info('***** Doing Browse from Backupset for path [%s] *****', text)
        self.backupset.browse(path=text)
        self.wait()
        self.table.set_filter('Details', text)
        self.verify_audit(1, admin_user, 'browse', subclient=False)

        text = self.random_text('path')
        self.log.info('***** Doing Browse from Subclient for path [%s] *****', text)
        self.subclient.browse(path=text)
        self.wait()
        self.table.set_filter('Details', text)
        self.verify_audit(1, admin_user, 'browse')

        text = self.random_text('file_name')
        self.log.info('***** Doing Find from Subclient with file name [%s] *****', text)
        self.subclient.find(file_name=text)
        self.wait()
        self.table.set_filter('Details', text)
        self.verify_audit(1, admin_user, 'find')

        self.idx_tc.run_backup_sequence(
            self.subclient, ['incremental', 'synthetic_full'], verify_backup=False
        )

        self.log.info('***** Checking if synthetic full browse request is audited *****')
        self.wait()
        self.table.set_filter('Operation', 'Browse')
        self.table.set_filter('Details', self.backupset.name)
        self.verify_audit(3, admin_user, 'find')

        self.log.info('***** Verifying audit as another company user [%s] *****', text)
        self.log.info('***** Logging out *****')
        self.admin_console.logout()
        self.admin_console.login(
            username=self.tcinputs.get('CompanyUser'),
            password=self.tcinputs.get('CompanyPassword')
        )

        self.open_audit_trail()

        text = self.random_text('path')
        self.backupset.browse(path=text)
        self.wait()
        self.table.set_filter('Operation', 'Browse')
        self.table.set_filter('Details', self.backupset.name)
        self.verify_audit(0, self.tcinputs.get('CompanyUser'), subclient=False)

    def wait(self, secs=10):
        """Wait for some time and refreshes the report page"""
        time.sleep(secs)
        self.report.refresh()

    @staticmethod
    def random_text(text_for):
        """Returns a random text for the browse/find operation"""

        if text_for == 'path':
            return 'c:\\' + get_random_string(5)

        if text_for == 'file_name':
            return get_random_string(8)

    @test_step
    def verify_audit(self, expected_audits, username, op_type='', backupset=True, subclient=True):
        """Verifies the audit list like number of audits and the content of the last audit

            Args:
                expected_audits     (int)       --      The number of audits to seen in the table

                username            (str)       --      The expected username of the last audit

                op_type             (str)       --      The expected browse/find operation type of the last audit

                backupset           (bool)      --      Whether to verify backupset name or not

                subclient           (bool)      --      Whether to verify subclient name or not

        """

        rows = self.table.get_rows_from_table_data()
        self.log.info(rows)

        if len(rows) != expected_audits:
            raise Exception(
                f'Browse request not audited as expected. Expected [{expected_audits}] audit. Actual [{len(rows)}]'
            )
        self.log.info('Verified expected number [%s] of audits', expected_audits)

        if expected_audits == 0:
            return

        a_username = self.table.get_column_data('User')[0].lower()
        a_operation = self.table.get_column_data('Operation')[0].lower()
        a_details = self.table.get_column_data('Details')[0].lower()

        if a_username != username:
            raise Exception(f'Username incorrect in browse audit. Expected [{username}] Actual [{a_username}]')

        self.log.info('Verified username [%s] in audit details', a_username)

        if a_operation != 'Browse/Find Operation'.lower():
            raise Exception(f'Operation type is incorrect in browse audit. Actual [{a_operation}]')

        self.log.info('Verified operation column [%s] in audit details', a_operation)

        if self.client.name.lower() not in a_details:
            raise Exception(f'Client name not in audit. [{self.client.name}] Actual [{a_details}]')

        self.log.info('Verified client name [%s] in audit details', self.client.name)

        if backupset:
            if self.backupset.name.lower() not in a_details:
                raise Exception(f'Backupset name not in audit. [{self.backupset.name}] Actual [{a_details}]')

            self.log.info('Verified backupset name [%s] in audit details', self.backupset.name)

        if subclient:
            if self.subclient.name.lower() not in a_details:
                raise Exception(f'Subclient name not in audit. [{self.subclient.name}] Actual [{a_details}]')

            self.log.info('Verified subclient name [%s] in audit details', self.subclient.name)

        if op_type != '':
            if op_type.lower() not in a_details:
                raise Exception(f'Subclient name not in audit. [{op_type.lower()}] Actual [{a_details}]')

            self.log.info('Verified operation type [%s] in audit details', op_type.lower())

    def tear_down(self):
        """Tear down function"""

        if self.agent and self.backupset:
            try:
                self.agent.backupsets.delete(self.backupset.backupset_name)
                self.log.info('Deleted the backupset successfully')
            except Exception as e:
                self.log.error('Failed to delete backupset [%s]', e)

        if self.admin_console:
            try:
                AdminConsole.logout_silently(self.admin_console)
                Browser.close_silently(self.browser)
            except Exception as e:
                self.log.error('Failed to close browser window [%s]', e)
