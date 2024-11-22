
"""
Contains all the Custom Reports' API
"""

from urllib.parse import quote as url_encode

from AutomationUtils import config
from AutomationUtils.logger import get_log
from Web.Common.exceptions import CVWebAPIException
from Web.WebConsole.API.cvsessions import CVSession
from Web.WebConsole.API.cvsessions import WebConsoleSession

_CONSTANTS = config.get_config()
_LOG = get_log()


class CustomReports:
    """
    Interacts with CustomReports's API
    """
    def __init__(self, cv_session):
        """
        Args:
            cv_session (CVSession): Any CVSession implementation
        """
        self._session = cv_session.session
        if isinstance(cv_session, WebConsoleSession):
            self._base_url = cv_session.cre_api_url
        else:
            self._base_url = cv_session.base_url

    @property
    def session(self):
        """Session used by custom reports"""
        return self._session

    def _base_request(
            self, method, suffix_url, payload="",
            response_type="application/json", content_type="application/json"):
        """
        Provides the API interface to the CRE's API on webconsole

        Args:
            method (self.session.METHOD): METHOD can be any of GET/PUT/POST/DELETE
        """
        url = self._base_url + url_encode(str(suffix_url))
        self.session.headers["Content-Type"] = content_type
        self.session.headers["Accept"] = response_type

        if payload != "":
            resp = method(url, str(payload))
        else:
            resp = method(url)
        resp.raise_for_status()
        return resp

    def save_report_definition(self, report_defi):
        """
        Args:
            report_defi (dict): Has to be a JSON representation of the
                report definition, return type of the
                `get_report_definition_by_name` can be directly used here
        """
        _LOG.info("API Trying to save report")
        self._base_request(self.session.put, "reports", payload=str(report_defi))

    def update_report_definition(self, rpt_name, new_defi):
        """Update any report with the given definition

        Args:
            rpt_name (str): Name of the report you are updating
            new_defi (dict): Dictionary representation of the report
                definition.
        """
        url = "reports"
        try:
            _LOG.info("API Updating [%s] definition" % rpt_name)
            old_defi = self.get_report_definition_by_name(rpt_name)
            new_defi["report"]["customReportId"] = old_defi["report"]["customReportId"]
            self._base_request(self.session.put, url, payload=str(new_defi))
        except Exception as e:
            raise CVWebAPIException(
                "Unable to update [%s]'s definition"
                % rpt_name, self._base_url + url) from e

    def get_all_installed_reports(self):
        """Retrieves the metadata for all the reports installed
        as a dictionary with `reportId`, `reportName`, `description`,
        `version`, `guid`, `revision` and a few other keys
        """
        url = "reports"
        try:
            _LOG.info("API Returning all the installed reports")
            response = self._base_request(self.session.get, url)
            resp_json = response.json()
            assert "reports" in resp_json.keys(), resp_json.text
            return resp_json["reports"]
        except Exception as e:
            raise CVWebAPIException(
                "Unable to retrieve reports", self._base_url + url) from e

    def get_report_definition_by_id(self, report_id):
        """Returns the report definition

        Args:
            report_id (int): ID of the report
        """
        try:
            _LOG.info("API Retrieving report by ID [%s]" % str(report_id))
            response = self._base_request(self.session.get, str(report_id))
            return response.json()
        except Exception as e:
            raise CVWebAPIException(
                "Unable to retrieve report with ID [%s]"
                % report_id, self._base_url + str(report_id)) from e

    def get_report_definition_by_name(self, report_name, suppress=False):
        """Used to return the report definition when searched with name

        Args:
            report_name (str): Name of the custom report
            suppress (bool): Set it to true when you don't want any exception
                to be raised
        """
        url = "reports/name:" + report_name
        try:
            resp = self._base_request(self.session.get, url)
            resp_json = resp.json()
            assert "report" in resp_json.keys(), resp.text
            return resp_json
        except Exception as e:
            if suppress is False:
                raise CVWebAPIException(
                    "Unable to retrieve report [%s]" % report_name,
                    self._base_url + url) from e

    def delete_custom_report_by_name(self, report_name, suppress=False):
        """Delete the custom report using the report name

        Args:
            report_name (str): name of the report
            suppress (bool): Set it to true when you don't want any exception
                to be raised
        """
        url = ""
        try:
            _LOG.info("API Deleting report by name [%s]" % report_name)
            report_defi = self.get_report_definition_by_name(report_name)
            url = "reports/" + str(report_defi["report"]["customReportId"])
            resp = self._base_request(self.session.delete, url)
            return resp.json()["queryId"]
        except Exception as e:
            _LOG.warning("API Unable to delete custom report [%s]; "
                         "error [%s]" % (report_name, str(e)))
            if suppress is False:
                raise CVWebAPIException(
                    "Unable to delete report [%s]" % report_name,
                    self._base_url + url) from e


def get_custom_reports_api(machine, port=80, protocol="http",
                           username=_CONSTANTS.ADMIN_USERNAME,
                           password=_CONSTANTS.ADMIN_PASSWORD,
                           proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
                           proxy_port=_CONSTANTS.HttpProxy.PORT):
    """Get custom report api with all defaults"""
    _LOG.info("API Creating WebConsole session for CustomReports on [%s]" % machine)
    session = WebConsoleSession(
        machine, port=port, protocol=protocol,
        proxy_machine=proxy_machine, proxy_port=proxy_port)
    session.login(username, password)
    return CustomReports(session)
