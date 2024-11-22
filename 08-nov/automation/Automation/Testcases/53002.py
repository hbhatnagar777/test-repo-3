# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Checks if a query set with unpermitted characters in its name."""
from Web.ediscovery.enduser.setspecific.querysetoperations import QuerysetOperations as QuerySet
from dynamicindex.utils.constants import DELETE_SET
from dynamicindex.utils.constants import APPTYPE_ALL as ATYPE
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test to verify if a query set with unpermitted characters in its name."""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "test_querysetcreate_alphanumeric"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SEARCHENGINE
        self.feature = self.features_list.CONTENTINDEXING
        self.show_to_user = True
        self.set_config_values = None
        self.general_config_values = None

    def init_tc(self):
        """Initializes this test case."""
        self.general_config_values = config.get_config().Ediscovery.EnduserSite
        self.set_config_values = config.get_config().Ediscovery.EnduserSite.Queryset

    def test_querysetcreate_alphanumeric(self):
        """Creates a query set with unpermitted characters in its name."""
        username = self.set_config_values.USERNAME
        password = self.set_config_values.PASSWORD
        search_keyword = self.set_config_values.SEARCH_KEYWORD
        searchengine = self.general_config_values.SEARCHENGINE
        queryset = QuerySet()

        queryset.ini.login(username, password)
        setname, _ = queryset.create_set(
            search_keyword,
            searchengine,
            ATYPE, True)
        queryset.delete_set(
            setname, DELETE_SET)
        queryset.ini.logout()
        del queryset

    def run(self):
        try:
            self.init_tc()
            self.test_querysetcreate_alphanumeric()
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception occurred while executing this test case.")
