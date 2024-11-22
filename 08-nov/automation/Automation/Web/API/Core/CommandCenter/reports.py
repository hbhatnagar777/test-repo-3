# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from os import path

from Web.Common.exceptions import CVWebAPIException
from AutomationUtils.logger import get_log


class Reports:

    def __init__(self, session):
        self._cc_url = session.cc_url
        self._session = session.session
        self._LOG = get_log()

    def get_reports(self):
        """
        Gets report
        """
        try:
            self._LOG.info(f"Getting report info")
            resp = self._session.get(
                f"{self._cc_url}reportsList.do?tags=&includeMetricsReports=false"
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as err:
            raise CVWebAPIException("Unable to import app") from err

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
        url = self._cc_url + f"proxy/exp.do"

        report_url = f"/#/reportDetails?reportId={report_id}&app=ADMIN_CONSOLE&isAdminconsoleReport=true" \
                     f"&exportType={export_type}&allDataSets=true&pageSize=-1&viewportWidth=1600"

        if filters is not None:
            self._LOG.info(f"Applying filters to the Url : {filters}")
            report_url = f"{report_url}&{filters}"

        payload = {
            'orientation': 'portrait',
            'exportType': export_type,
            'isRelative': True,
            'url': report_url,
            'filePrefix': file_prefix,
            'type': 'report',
            'directDownload': True
        }

        self._LOG.info(f"Calling Export Url : {url} with payload : {payload}")
        resp = self._session.get(url, params=payload)
        resp.raise_for_status()

        download_path = path.join(folder_path, f"{file_prefix}.{export_type}")
        file = open(download_path, 'wb')
        file.write(resp.content)
        file.close()
        self._LOG.info(f"Downloaded report successfully. Report file path on controller :  {download_path}")
        return download_path

    def import_custom_report_xml(self, rpt_path):
        """Imports the Custom Report into the webconsole

        Args:
            rpt_path (str): Complete path of the xml file

        Returns:
            set: (name of custom report, id of custom report)
        """

        url = self._cc_url + "proxy/uploadAndInstallCustomReport.do"

        try:
            self._LOG.info(
                "API - Importing custom report; [POST %s]" % url
            )
            files = {"file": open(rpt_path, "rb")}
            resp = self._session.post(url, files=files)
            resp.raise_for_status()
            resp_json = resp.json()["successList"][0]
            assert "customReportName" in resp_json.keys(), resp.text
            return resp_json['customReportName'], resp_json['customReportId']
        except Exception as e:
            raise CVWebAPIException(
                "Custom Report import failed", url
            ) from e

    def delete_custom_report(self, name, id_, suppress=False):
        """Delete custom report by name"""
        self._LOG.info(
            "API - Deleting report Report Name [%s]; Report ID [%s]",
            name,
            id_
        )
        try:
            resp = self._session.post(
                self._cc_url + "deleteCustomReport.do",
                data={"reportId": id_, "reportName": name}
            )
            resp.raise_for_status()
            expected_msg = "Report %s deleted successfully." % name
            error_msg = "Something went wrong while deleting report [%s]" % resp.text
            assert expected_msg == resp.text, error_msg
        except Exception as excp:
            error_msg = "Unable to delete report, ID [%s], Name [%s]" % (id_, name)
            if not suppress:
                raise CVWebAPIException(error_msg) from excp
            else:
                self._LOG.warning(error_msg)
