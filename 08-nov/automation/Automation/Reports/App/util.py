# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Apps util file"""

import os

from AutomationUtils import constants
from AutomationUtils.config import get_config
from Reports.storeutils import StoreUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import (
    CVWebAPIException,
    CVTestStepFailure
)


class AppUtils(TestCaseUtils):

    def __init__(self, testcase_obj):
        super().__init__(testcase_obj)
        self.testcase_obj = testcase_obj
        self.store_util = StoreUtils(self.testcase_obj)

    @property
    def config(self):
        return AppUtils.get_config()

    @classmethod
    def get_config(cls):
        return get_config(
            json_path=os.path.join(
                constants.AUTOMATION_DIRECTORY,
                "Reports",
                "App",
                "app_config.json"
            )
        )

    def is_app_installed(self, name):
        """Is app installed"""
        app = self.store_util.cre_api.execute_sql(
            f"""
            SELECT name
            FROM Store_App
            WHERE name LIKE '{name}'
            """,
            desc=f"Check if app [{name}] is installed on DB"
        )
        return len(app) == 1

    def verify_if_workflows_exists(self, workflows):
        """Verify if workflow exists"""
        list(map(self.store_util.has_workflow, workflows))

    def verify_if_tools_exists(self, tools):
        """Verify if tool exists"""
        list(map(self.store_util.validate_if_tool_exists, tools))

    def verify_if_alerts_exists(self, alerts):
        """Verify if tool exists"""
        list(map(self.store_util.verify_if_alert_exists, alerts))

    def verify_if_reports_exists(self, reports):
        """Verify if report exists"""
        try:
            list(map(
                self.store_util.cre_api.get_report_definition_by_name,
                reports
            ))
        except CVWebAPIException as e:
            raise CVTestStepFailure(
                f"Unable to find report [{e.url}]"
            ) from e

    def verify_if_app_is_installed(self, app_name):
        """Validate if app is installed"""
        if self.is_app_installed(app_name) is False:
            raise CVTestStepFailure(
                f"Unable to find app [{app_name}] inside Store_App table"
            )

    def handle_testcase_exception(self, excp):
        """Handle testcase exception"""
        self.store_util.handle_testcase_exception(excp)
