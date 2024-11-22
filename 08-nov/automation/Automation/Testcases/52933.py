# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
#

""""
TestCase to validate Metrics Client Group selection for Collection.
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils import config
from AutomationUtils.machine import Machine

from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Troubleshooting.troubleshoot import Troubleshoot
from Web.WebConsole.Reports.Troubleshooting.wia import RemoteWia, ConfigurationTypes, SendTrace

from Reports.metricsutils import MetricsServer

from cvpysdk.commcell import Commcell
from cvpysdk.license import LicenseDetails
from cvpysdk.schedules import Schedules

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate WIA via Cloud Troubleshooting request"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "WIA via Cloud Troubleshooting request"
        self.private_metrics = None
        self.tcinputs = {
            "commcell_name": None
        }
        self.browser = None
        self.webconsole = None
        self.metrics_server = None
        self.troubleshoot = None
        self.r_wia = None
        self.p_commcell = None
        self.utils = TestCaseUtils(self)
        self.schd_obj = None

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.metrics_server = MetricsServer(
            self.commcell.commserv_hostname,
            metrics_commcell_user=self.inputJSONnode['commcell']["commcellUsername"],
            metrics_commcell_pwd=self.inputJSONnode['commcell']["commcellPassword"]
                                           )
        self.p_commcell = Commcell(self.tcinputs['commcell_name'],
                                   _CONSTANTS.ADMIN_USERNAME,
                                   _CONSTANTS.ADMIN_PASSWORD
                                   )

    def init_webconsole(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.commserv_name)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_troubleshooting()
            self.troubleshoot = Troubleshoot(self.webconsole)
            self.r_wia = RemoteWia(self.webconsole)
            self.troubleshoot.access_commcell(self.tcinputs['commcell_name'])
            self.troubleshoot.access_remote_wia()

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def check_trace_started(self):
        """Verify if trace started in participating CommCell"""
        query = """SELECT sj.job_id,run_requested_date
        FROM msdb.dbo.sysjobactivity AS sja
        INNER JOIN msdb.dbo.sysjobs AS sj ON sja.job_id = sj.job_id
        WHERE sja.start_execution_date IS NOT NULL
        AND sj.name = 'WIA_TracerJob'
        AND sja.run_requested_date >  DATEADD(mi,-70,GETUTCDATE())"""
        csdb = CommServDatabase(self.p_commcell)
        csdb.execute(query)
        rows = len(csdb.rows)
        if rows == 0:
            raise CVTestStepFailure("WIA trace not started in CommCell")
        elif rows != 1:
            raise CVTestStepFailure("Expected [1] WIA trace in CommCell"
                                    " But found [%d] Trace" % rows
                                    )
        self.log.info('WIA Trace successfully started in CommCell')

    @test_step
    def submit_wia(self):
        """Submit WIA remote request"""
        self.r_wia.set_wia_configuration(ConfigurationTypes.type1.value)
        self.r_wia.set_send_trace_days(SendTrace.interval2.value)
        self.troubleshoot.submit()
        if self.troubleshoot.is_request_submit_success() is False:
            raise CVTestStepFailure("Wia Request submission failed didnt receive Request "
                                    "submit success message"
                                    )
        self.log.info('WIA request submitted from cloud')
        self.troubleshoot.go_back_to_submit_request()

    @test_step
    def check_req_created(self):
        """check request xml created in scripts directory"""
        self.log.info('Wait for 1 minute for xml creation in script folder')
        from time import sleep
        sleep(60)
        license_info = LicenseDetails(self.p_commcell)
        commcell_id = hex(license_info.commcell_id).split('x')[1].upper()
        if self.metrics_server.is_wia_troubleshoot_xml_exist(commcell_id,
                                                             self.p_commcell.commserv_guid
                                                             ) is False:
            raise CVTestStepFailure("Wia Request xml not found in troubelshooting folder"
                                    )
        self.log.info('WIA request created in cloud')

    @test_step
    def check_schedule_created(self):
        """Check WIA send log schedule is created"""
        query = """
        SELECT value FROM GXGlobalParam 
        WHERE name LIKE 'CommservSurveyWIAScheduleIDList'
        """
        csdb = CommServDatabase(self.p_commcell)
        csdb.execute(query)
        rows = len(csdb.rows)
        if rows == 0:
            raise CVTestStepFailure(
                "WIA schedule not found in gxglobalparam "
                "CommservSurveyLastTroubleshootingXmlRequestId"
            )
        self.schd_obj = Schedules(self.p_commcell)
        wia_schedule = self.schd_obj.get(schedule_id=int(csdb.rows[0][0].split(',')[-1]))
        if 'CloudWIAJob' in wia_schedule.schedule_name:
            self.log.info(f'Wia schedule [{wia_schedule.schedule_name}] found')
        return wia_schedule.schedule_name

    def cleanup(self, schedule_name):
        """delete send log schedule and stop wia trace"""
        self.log.info('Cleanup: delete send log schedule and stop wia trace')
        self.schd_obj.delete(schedule_name=schedule_name)
        mc_obj = Machine(self.p_commcell.commserv_name, self.p_commcell)
        mc_obj.execute_command(r"dbmaintenance -stopwiatracer")

    def run(self):
        try:
            self.init_webconsole()
            self.submit_wia()
            self.check_req_created()
            self.check_trace_started()
            schedule_name = self.check_schedule_created()
            self.cleanup(schedule_name)
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
