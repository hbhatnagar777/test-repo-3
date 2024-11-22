
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This module contains all the core reports API on custom reports"""


from requests.exceptions import HTTPError

from Web.Common.exceptions import (
    CVWebAPIException,
    CVNotFound
)
from ._base import CustomReportsAPI


class Reports(CustomReportsAPI):
    """
    Interacts with Reports's API
    """

    @property
    def _base_report_url(self):
        return super()._base_url + "reports/"

    def delete_custom_report_by_name(self, report_name, suppress=False):
        """Delete the custom report using the report name

        Args:
            report_name (str): name of the report
            suppress (bool): Set it to true when you don't want any exception
                to be raised if report does not exist
        """
        report_defi = self.get_report_definition_by_name(report_name, suppress)
        if report_defi:
            url = self._base_report_url + str(report_defi["report"]["customReportId"])
            self._base_request(self.session.delete, url, desc="Delete report; ")

    def save_report_definition(self, report_defi):
        """
        Args:
            report_defi (dict): Has to be a JSON representation of the
                report definition, return type of the `get_report_definition_by_name`
                can be directly used here
        """
        self._base_request(
            self.session.put,
            self._base_report_url,
            payload=str(report_defi),
            desc="Save report"
        )

    def update_report_definition(self, rpt_name, new_defi):
        """Update any report with the given definition

        Args:
            rpt_name (str): Name of the report you are updating
            new_defi (dict): Dictionary representation of the report
                definition.
        """
        try:
            old_defi = self.get_report_definition_by_name(rpt_name)
            new_defi["report"]["customReportId"] = old_defi["report"]["customReportId"]
            self.save_report_definition(new_defi)
        except Exception as e:
            raise CVWebAPIException(
                f"Unable to update [{rpt_name}]'s definition",
                self._base_report_url
            ) from e

    def get_all_installed_reports(self, metadata=False):
        """Retrieves the metadata for all the reports installed
        as a dictionary with `reportId`, `reportName`, `description`,
        `version`, `guid`, `revision` and a few other keys
        """
        resp_txt = None
        try:
            response = self._base_request(
                self.session.get,
                self._base_report_url,
                desc="Retrieve all installed reports"
            )
            resp_txt = response.text
            reports = response.json()["reports"]
            if metadata:
                return reports
            else:
                return [report.get("reportName") for report in reports]
        except Exception as e:
            raise CVWebAPIException(
                msg="Unable to retrieve reports",
                url=self._base_report_url,
                response_text=resp_txt
            ) from e

    def get_report_definition_by_id(self, report_id):
        """Returns the report definitions

        Args:
            report_id (int): ID of the report
        """
        resp_txt = None
        url = self._base_report_url + "/" + str(report_id)
        try:
            response = self._base_request(
                self.session.get, url, desc="Retrieve report by ID "
            )
            resp_txt = response.text
            return response.json()
        except Exception as e:
            raise CVWebAPIException(
                msg="Unable to retrieve report with ID [%s]" % report_id,
                url=url + str(report_id),
                response_text=resp_txt
            ) from e

    def get_report_definition_by_name(self, report_name, suppress=False):
        """Used to return the report definition when searched with name

        Args:
            report_name (str): Name of the custom report
            suppress (bool): Set it to true when you don't want any exception
                to be raised
        """
        url = f"{self._base_report_url}name:{report_name}?includeDrafts=true"
        resp_txt = None
        try:
            resp = self._base_request(
                self.session.get, url, desc="Retrieve report by name"
            )
            resp_txt = resp.text
            resp_json = resp.json()
            assert "report" in resp_json.keys()
            return resp_json
        except (AssertionError, HTTPError) as e:
            if suppress:
                return {}
            raise CVNotFound(
                msg="Unable to fetch report [%s]" % report_name,
                url=url,
                response_text=resp_txt
            ) from e

        except Exception as e:
            raise CVWebAPIException(
                msg=f"Something went wrong while retrieving report [{report_name}]",
                url=url,
                response_text=resp_txt
            ) from e
