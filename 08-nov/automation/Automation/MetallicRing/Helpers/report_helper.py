# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for performing reports related operations in Metallic Ring

    ReportsRingHelper:

        __init__()                              --  Initializes Reports Ring Helper

        start_task                              --  Starts the reports related tasks for metallic ring

        enable_cloud_metrics                    --  Sets the cloud metrics url

        enable_private_metrics                  --  Sets the remote metrics url

        import_report                           --  Imports the report definition


"""
import xml.etree.cElementTree as ETree
from AutomationUtils.config import get_config
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from Web.API.cc import Reports
from cvpysdk.metricsreport import PrivateMetrics, CloudMetrics

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_METRICS_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.metrics_commcell


class ReportsRingHelper(BaseRingHelper):
    """ contains helper class for performing reports related operations in Metallic Ring"""

    def __init__(self, ring_commcell, username, password):
        super().__init__(ring_commcell)
        self.username = username
        self.password = password

    def start_task(self):
        """Starts the reports related tasks for metallic ring"""
        try:
            self.log.info("Starting Report helper task")
            self.enable_cloud_metrics()
            metric_url = _METRICS_CONFIG.dev_metrics
            self.enable_private_metrics(metric_url, port=443, protocol=cs.HTTPS_PROTOCOL)
            self.import_report()
            self.log.info("All Report helper related tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute report helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def enable_cloud_metrics(self):
        """Sets the cloud metrics url"""
        self.log.info("Request received to enable cloud metrics")
        cloud_metrics = CloudMetrics(self.commcell)
        cloud_metrics.enable_metrics()
        cloud_metrics.enable_all_services()
        cloud_metrics.save_config()
        self.log.info("Cloud metrics on the commcell is enabled")

    def enable_private_metrics(self, private_metrics_url, port=80, protocol=cs.HTTP_PROTOCOL):
        """
        Sets the private metrics url
        Args:
             private_metrics_url(str)   -   Url for private metrics reporting
             port(int)                  -   Port for private metrics
             protocol(str)              -   Protocol to use
        """
        self.log.info(f"Request received to enable private metrics. Private metrics URL [{private_metrics_url}]")
        private_metrics = PrivateMetrics(self.commcell)
        private_metrics.enable_metrics()
        private_metrics.enable_all_services()
        private_metrics.update_url(private_metrics_url, port=port, protocol=protocol)
        private_metrics.enable_chargeback(daily=True)
        private_metrics.save_config()
        self.log.info("Private metrics on the commcell is enabled")

    def import_report(self):
        """Imports a report with given definition"""
        self.log.info("Request received to import reports needed for metallic ring config")
        rpt_api = Reports(
            machine=self.commcell.webconsole_hostname,
            username=self.username, password=self.password)
        for report_dict in cs.REPORT_DICT_LIST:
            self.log.info(f"Following report is being imported - [{report_dict[cs.REPORT_NAME]}]")
            report_name = report_dict[cs.REPORT_NAME]
            report_xml_path = report_dict[cs.REPORT_XML]
            xml_tree = ETree.parse(report_xml_path)
            root = xml_tree.getroot()
            for page in root.iter(GeneralConstants.XML_REPORT_PAGE):
                page_name = page.find(GeneralConstants.XML_REPORT_PAGE_NAME).text
                self.log.info(f"Going to update Report's Page : {page_name}")
            xml_tree.write(report_xml_path)
            self.log.info("Xml updated correctly")
            rpt_api.import_custom_report_xml(rpt_path=report_xml_path)
            self.log.info(f"[{report_name}] - Import successful for Report xml : {report_xml_path}")
