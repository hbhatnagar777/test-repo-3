
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" This file contains helper functions for custom reports related operations like import/export/delete reports

    Reports:

        __init__()                          --      Initialise the Reports class object

        export_report()                     --      exports report as pdf/html and downloads it to controller machine

        import_custom_report_xml()          --      imports custom reports into the commcell

        delete_custom_report()              --      deletes the custom report


"""
import os
from AutomationUtils.logger import get_log
from Web.Common.exceptions import CVWebAPIException


class Reports:

    """APIs available on webconsole"""

    def __init__(self, webconsole_session):
        """Session is created and csrf token is extracted

        Args:
             webconsole_session (WebConsole): Instance of WebConsole
        """
        self._webconsole_session = webconsole_session
        self._session = webconsole_session.session
        self._csrf = webconsole_session.csrf
        self._log = get_log()

    def export_report(self, report_id, export_type, folder_path, file_prefix="Automation_Exported", filters=None):
        """ Exports the reports in html/pdf file

        Args:

            report_id       (str)       --  report id

            export_type     (str)       --  export type (pdf/html)

            folder_path     (str)       --  folder path where exported file will be saved

            file_prefix     (str)       --  string which needs to be prefixed in export file name

            filters         (str)       --  custom reports filter to be applied in export url (Default - None)

                    Example for Filter panel
                            Format: <component ID>.filter.include.<Fieldname>=<Fieldvalue>
                            Usage : AutomationFilters.filter.include.CSVersion-0=11.21.3

        Returns:

            str     --  Exported file path in the controller

        Raises:

            Exception:

                    if failed to export the report

                    if failed to download the report

        """
        url = f"{self._webconsole_session.base_url}reports/exp.do?orientation=landscape&width=1200" \
              f"&exportType={export_type}&viewportWidth=1600&csrf={self._csrf}"
        report_url = f"{self._webconsole_session.base_url}reportsplus/reportViewer.jsp?reportId={report_id}" \
                     f"&exportType={export_type}&allDataSets=true&pageSize=-1&cacheId=undefined"
        if filters is not None:
            self._log.info(f"Applying filters to the Url : {filters}")
            report_url = f"{report_url}&{filters}"
        payload = {
            'url': report_url,
            'filePrefix': file_prefix,
            'type': 'report',
            'directDownload': False
        }
        self._log.info(f"Calling Export Url : {url} with payload : {payload}")
        resp = self._session.post(url, data=payload)
        resp.raise_for_status()
        remote_file_name = resp.content.decode('utf-8')
        if remote_file_name is None:
            raise Exception("Export operation failed. Please check")
        self._log.info(f"Exported file name on web server : {remote_file_name}")
        download_url = f"{self._webconsole_session.base_url}server/doDownload?type=report&fileName={remote_file_name}"
        self._log.info(f"Calling Download Url : {download_url}")
        resp = self._session.get(download_url)
        resp.raise_for_status()
        content = resp.content.decode('utf-8')
        if content is None:
            raise Exception("Download operation failed. Please check")
        download_path = f"{folder_path}{os.sep}{remote_file_name}"
        file = open(download_path, 'w')
        file.write(content)
        file.close()
        self._log.info(f"Downloaded report successfully. Report file path on controller :  {download_path}")
        return download_path

    def import_custom_report_xml(self, rpt_path):
        """Imports the Custom Report into the webconsole

        Args:
            rpt_path (str): Complete path of the xml file

        Returns:
            set: (name of custom report, id of custom report)
        """

        url = (
            self._webconsole_session.base_url +
            "server/uploadAndInstallCustomReport.do?csrf=" +
            self._csrf
        )
        try:
            self._log.info(
                "API - Importing custom report; [POST %s]" % (
                    url
                )
            )
            files = {"file": open(rpt_path, "rb")}
            resp = self._session.post(url, files=files)
            resp.raise_for_status()
            resp_json = resp.json()["imported"][0]
            assert "name" in resp_json.keys(), resp.text
            return resp_json['name'], resp_json['id']
        except Exception as e:
            raise CVWebAPIException(
                "Custom Report import failed", url
            ) from e

    def delete_custom_report(self, name, id_, suppress=False):
        """Delete custom report by name"""
        self._log.info(
            "API - Deleting report Report Name [%s]; Report ID [%s]",
            name,
            id_
        )
        try:
            resp = self._session.post(
                self._webconsole_session.base_url +
                "reportsplus/deleteCustomReport.do",
                data={"reportId": id_, "reportName": name}
            )
            resp.raise_for_status()
            expected_msg = "Report %s deleted successfully." % name
            error_msg = "Something went wrong while deleting report [%s]" % resp.text
            assert expected_msg == resp.text, error_msg
        except Exception as excp:
            error_msg = "Unable to delete report,  ID [%s], Name [%s]" % (id_, name)
            if not suppress:
                raise CVWebAPIException(error_msg) from excp
            else:
                self._log.warning(error_msg)
