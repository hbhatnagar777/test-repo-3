#!/usr/bin/python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.entity_manager import EntityManager
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for drop down component"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = \
            'Basic Integration test case for drop down component in AdminConsole Automation'
        self.browser = None
        self.admin_console = None
        self.entity_name = None
        self.entity_sensitivity = None
        self.entity_parent = None
        self.entity_keywords = None
        self.__navigator = None
        self.__entity_manager = None
        self.__app = None
        self.tcinputs = {
            'entity_sensitivity': None,
            'entity_parent': None,
            'entity_keywords': None,
        }

    def init_tc(self):
        """ initial setup for this test case """

        self.entity_name = '{}_entity'.format(self.id)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.__entity_manager = EntityManager(self.admin_console)
        self.__app = GovernanceApps(self.admin_console)
        self.__navigator = self.admin_console.navigator
        self.entity_keywords = self.tcinputs['entity_keywords']
        self.entity_parent = self.tcinputs['entity_parent']
        self.entity_sensitivity = self.tcinputs['entity_sensitivity']

    def add_entity(self):
        """ Method to perform single & multi select validation by creating an entity in entity
        manager """
        keywords = self.entity_keywords.split(',')
        self.__navigator.navigate_to_governance_apps()
        self.__app.select_entity_manager()
        self.__entity_manager.add_custom_entity(self.entity_name,
                                                self.entity_sensitivity, None,
                                                parent_entity=self.entity_parent, keywords=keywords)
        self.__entity_manager.select_entity(self.entity_name)

    def cleanup(self):
        """ Clean up entity created. """
        self.__navigator.navigate_to_governance_apps()
        self.__app.select_entity_manager()
        self.__entity_manager.entity_action(self.entity_name,
                                            action='Delete')

    def run(self):
        """ Main function for test case execution """
        try:
            self.init_tc()
            self.add_entity()
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
