# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.maintenance import DRBackupDaily
from Web.AdminConsole.Reports.health import Health
from Web.AdminConsole.Reports.health_tiles import GenericTile, DRBackup
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Reports.utils import TestCaseUtils
from cvpysdk.metricsreport import PrivateMetrics
from Web.Common.exceptions import CVException
import time


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.metrics = None
        self.manage_reports = None
        self.navigator = None
        self.health = None
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.dr_backup_page = None
        self.name = "Validate Disaster Recovery status on health report"
        self.tcinputs = {
            "network_share_path": None,
            "network_share_username": None,
            "network_share_password": None,
            "local_drive": None,
            "cloud_library": None
        }

    def setup(self):
        self.utils = TestCaseUtils(self)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.health = Health(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.manage_reports = ManageReport(self.admin_console)
        self.metrics = PrivateMetrics(self.commcell)

    def verify_security_assessment_on_health_report(self, expected_status, current_config):
        """Verifies DRBackup status on security assessment report"""
        self.navigator.navigate_to_metrics()
        self.manage_reports.access_commcell_health(self.commcell.commserv_name)
        sa_tile = GenericTile(self.admin_console, 'Security Assessment')
        sa_tile.access_view_details()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Platform Security")
        report_viewer.associate_component(table_obj)
        data = table_obj.get_table_data()
        self.log.info(f"security assessment report data : {data}")
        idx = data['Parameter'].index('Disaster Recovery Backup')
        status = data['Status'][idx]
        if status != expected_status:
            raise CVException(f"Security assessment report in health report is showing DR Backup status\n"
                              f"{status} but the expected status is {expected_status} when configured to "
                              f"{",".join(current_config)}")

        # Checking case when all the parameter remarks are same in security assessment report
        if len(set(data['Status'])) == 1 or len(set(data['Remarks'])) == 1:
            raise CVException("Security assessment report is showing same remarks and\
             status for all parameters. Something is wrong, please check")

    def verify_disaster_recovery_on_health_report(self, expected_status, current_config):
        """Verifies DRBackup status on DRBackup tile on health report"""
        self.navigator.navigate_to_metrics()
        self.manage_reports.access_commcell_health(self.commcell.commserv_name)
        dr_tile = DRBackup(self.admin_console)
        status = dr_tile.get_health_status()

        if status != expected_status:
            raise CVException(f"Health report is showing DR Backup status\n"
                              f"{status} but the expected status is {expected_status} when configured to "
                              f"{",".join(current_config)}")
        destinations = dr_tile.get_path().lower()

        for dest in current_config:
            if dest.lower() not in destinations:
                raise CVException(f"Health report is showing DR Backup destination as\n"
                                  f"{destinations} but current configuration is {",".join(current_config)}")

        if expected_status.lower() == "critcal" or expected_status.lower() == "warning":
            displayed_remark = dr_tile.get_remark()
            self.log.info(f"displayed remark : {displayed_remark}")
            if "recommended to run DR backup every 24 hours".lower() not in displayed_remark.lower():
                raise CVException("DR remark when status is critical/warning is not showing expected message")

        dr_tile.access_view_details()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Summary")
        report_viewer.associate_component(table_obj)
        data = table_obj.get_table_data()
        self.log.info(f"DR backup details report data : {data}")
        status = data['Status'][0]

        if status != expected_status:
            raise CVException(f"dr details report in health report is showing DR Backup status\n"
                              f"{status} but the expected status is {expected_status} when configured to "
                              f"{",".join(current_config)}")

    def upload_metrics(self):
        """click metrics upload and waits until its done"""
        self.log.info("Metrics upload initiated")
        self.metrics.enable_audit()
        self.metrics.enable_activity()
        self.metrics.upload_now()
        self.metrics.wait_for_uploadnow_completion(upload_timeout=500)
        time.sleep(120)
        self.log.info("Metrics upload complete")

    def verify_status(self, expected_status: str, current_config: list):
        """This method calls other internal methods to verify status at different places"""
        self.upload_metrics()
        self.verify_disaster_recovery_on_health_report(expected_status, current_config)
        self.verify_security_assessment_on_health_report(expected_status, current_config)

    def get_dr_edit_dict(self, retains=5, cvcloud=True, othercloud=True, local=True, network=False, **kwargs):
        """Returns a dict of required inputs to edit dr destinations"""

        dr_settings = {
            "retain": retains,
            "metallic": {"turn_on": cvcloud},
            "cloud_library": {
                "turn_on": othercloud,
                "cloud_library_name": self.tcinputs["cloud_library"],
            },
        }

        if local:
            dr_settings["local_drive"] = self.tcinputs["local_drive"]

        if network:
            dr_settings["network_share"] = {
                "path": self.tcinputs["network_share_path"],
                "username": self.tcinputs["network_share_username"],
                "password": self.tcinputs["network_share_password"],
            }
        return dr_settings

    def verify(self, **kwargs):
        """Verifies the dr status at health/security assessment report with given destinations"""
        self.navigator.navigate_to_maintenance()
        self.dr_backup_page.access_dr_backup()
        self.dr_backup_page.edit(
            self.get_dr_edit_dict(**kwargs)
        )
        current_config = []
        if kwargs['local']:
            current_config.append('Local')
        elif kwargs['network']:
            current_config.append('UNC')
        if kwargs['cvcloud'] or kwargs['othercloud']:
            current_config.append('Cloud')
        self.verify_status(expected_status=kwargs["expected_status"], current_config=current_config)

    def run(self):
        """Run function of this test case"""
        try:
            self.dr_backup_page = DRBackupDaily(self.admin_console)

            self.log.info("Validating DR Backup status when configured only to UNC path")
            self.verify(local=False, network=True, cvcloud=False, othercloud=False, expected_status="Critical")

            self.log.info("Validating DR Backup status when configured to UNC path along with commvault cloud")
            self.verify(local=False, network=True, cvcloud=True, othercloud=False, expected_status="Good")

            self.log.info('Validating DR status "warning" when retains set to 1 even when destination is cloud & local')
            self.verify(retains=1, local=True, network=False, cvcloud=True, othercloud=False, expected_status="Warning")

            self.log.info("Validating DR Backup status when configured to UNC path along with other cloud library")
            self.verify(local=False, network=True, cvcloud=False, othercloud=True, expected_status="Good")

            self.log.info('Validating DR status "warning" when retains set to 1 even when destination is cloud & UNC')
            self.verify(retains=1, local=False, network=True, cvcloud=True, othercloud=False, expected_status="Warning")

            self.log.info("Validating DR Backup status when configured to UNC path along with both clouds")
            self.verify(local=False, network=True, cvcloud=True, othercloud=True, expected_status="Good")

            self.log.info('Validating DR status when retains set to 1 even when destination is only Local')
            self.verify(retains=1, local=True, network=False, cvcloud=False, othercloud=False,
                        expected_status="Critical")

            self.log.info("Validating DR Backup status when configured to local path along with other commvault cloud")
            self.verify(local=True, network=False, cvcloud=True, othercloud=False, expected_status="Good")

            self.log.info('Validating DR status when retains set to 1 when destination is only UNC')
            self.verify(retains=1, local=False, network=True, cvcloud=False, othercloud=False,
                        expected_status="Critical")

            self.log.info("Validating DR Backup status when configured to local path along with other cloud library")
            self.verify(local=True, network=False, cvcloud=True, othercloud=True, expected_status="Good")

            self.log.info("Validating DR Backup status when configured only to local path")
            self.verify(local=True, network=False, cvcloud=False, othercloud=False, expected_status="Critical")

            self.log.info("Validating DR Backup status when configured to local path along with both clouds")
            self.verify(local=True, network=False, cvcloud=True, othercloud=True, expected_status="Good")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
