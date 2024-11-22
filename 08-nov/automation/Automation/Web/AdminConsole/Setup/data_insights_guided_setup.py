# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Data Insights in getting started page

DataInsights    :   This class provides methods for data insights setup completion

"""

from Web.Common.page_object import PageService
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.AdminConsolePages.Plans import Plans


class DataInsights(GettingStarted):

    def __init__(self, admin_console):
        """ Data Insights guided setup Class initialization """
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.__driver = self._admin_console.driver
        self.dc_plan = Plans(self._admin_console)

    @PageService()
    def configure_wizard_for_fso(
            self, dc_plan, index_server, index_dir=None, index_node=None, create_index_server=False):
        """ Method to configure FSO solution """
        self.dc_plan.create_data_classification_plan(
            dc_plan, index_server, target_app='fso', create_index_server=create_index_server, node_name=index_node,
            index_directory=index_dir, guided_setup=True
        )

    @PageService()
    def configure_wizard_for_sdg(
            self, dc_plan, index_server, index_dir=None, index_node=None,
            content_analyzer=None, create_index_server=False,
            classifier_list=None, entities=None, enable_ocr=False):
        """ Method to configure SDG solution """
        self.dc_plan.create_data_classification_plan(
            dc_plan, index_server, content_analyzer=content_analyzer, entities_list=entities,
            content_analysis=True, enable_ocr=enable_ocr, target_app='gdpr',
            create_index_server=create_index_server, node_name=index_node, index_directory=index_dir,
            classifier_list=classifier_list, guided_setup=True
        )

    @PageService()
    def configure_wizard_for_case_manager(
            self, dc_plan, index_server, index_dir=None, index_node=None,
            content_analyzer=None, create_index_server=False, content_analysis=False,
            classifier_list=None, entities=None, enable_ocr=False):
        """ Method to configure SDG solution """
        self.dc_plan.create_data_classification_plan(
            dc_plan, index_server, content_analyzer=content_analyzer, entities_list=entities,
            content_analysis=content_analysis, enable_ocr=enable_ocr, target_app='casemanager',
            create_index_server=create_index_server, node_name=index_node, index_directory=index_dir,
            classifier_list=classifier_list, guided_setup=True
        )
